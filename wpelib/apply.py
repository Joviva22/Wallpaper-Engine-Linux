"""Aplica wallpapers de Wallpaper Engine, uno por pantalla, cada uno en su PROPIO
proceso de linux-wallpaperengine. Asi, si el motor crashea al renderizar un wallpaper
concreto (ocurre con algunas escenas rotas/incompatibles), solo se cae esa pantalla y
no las demas.

Por cada pantalla se lanza un proceso "vigilante" desacoplado (fork + setsid) que:
  1. toma un lock exclusivo por pantalla,
  2. mata el motor anterior de esa pantalla,
  3. lanza el motor nuevo como hijo directo y escribe su PID en pid_PANTALLA.pid,
  4. suelta el lock y espera a que el motor termine para decidir si fue un crash
     (y apuntarlo en known_bad.json) o un cambio deliberado de wallpaper.

Uso: wallpaperengine-apply PANTALLA=ID [PANTALLA=ID ...]"""
import json
import os
import re
import signal
import subprocess
import sys
import time

from . import config
from .config import FileLock, atomic_write_json, load_json

MAX_LOG_BYTES = 5 * 1024 * 1024
CRASH_LOG_PATTERN = re.compile(r"terminate called|Segmentation fault|Aborted \(core dumped\)")
# Terminaciones por senal que NO son un crash del motor (parada o cambio deliberado).
NON_CRASH_SIGNALS = {signal.SIGTERM, signal.SIGKILL, signal.SIGINT, signal.SIGHUP}
ID_RE = re.compile(r"^[0-9]+$")
SCREEN_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _path(name):
    return os.path.join(config.CONF_DIR, name)


def pid_file(screen):
    return _path(f"pid_{screen}.pid")


def log_file(screen):
    return _path(f"wallpaperengine_{screen}.log")


_Lock = FileLock


# ---------------------------------------------------------------------------
# Argumentos del motor
# ---------------------------------------------------------------------------

def scaling_for(screen):
    mode = config.load_scaling().get(screen, config.DEFAULT_SCALING)
    return mode if mode in config.SCALING_MODES else config.DEFAULT_SCALING


def audio_args(screen):
    """Silenciado por defecto; --volume N si el usuario activo el audio en esa
    pantalla. --silent y --volume son mutuamente excluyentes para el motor."""
    conf = config.load_audio().get(screen)
    if isinstance(conf, dict) and conf.get("muted", True) is False:
        return ["--volume", str(conf.get("volume", config.DEFAULT_VOLUME))]
    return ["--silent"]


def property_args(wid):
    props = config.load_properties().get(wid)
    args = []
    if isinstance(props, dict):
        for key, value in props.items():
            text = value if isinstance(value, str) else json.dumps(value)
            args += ["--set-property", f"{key}={text}"]
    return args


def speed_args(screen):
    """--speed solo existe en un linux-wallpaperengine parcheado: un motor sin el
    flag abortaria con "argumento desconocido", asi que se omite si no esta."""
    speed = config.load_speed().get(screen, 1.0)
    if isinstance(speed, (int, float)) and not isinstance(speed, bool) and speed != 1 \
            and config.engine_supports_speed():
        return ["--speed", str(speed)]
    return []


def engine_command(screen, wid):
    return [
        "linux-wallpaperengine", "--assets-dir", config.ASSETS_DIR, "--fps", "30",
        "--screen-root", screen, "--bg", os.path.join(config.WORKSHOP_DIR, wid),
        "--scaling", scaling_for(screen), "--clamp", "border",
        *audio_args(screen), *property_args(wid), *speed_args(screen),
    ]


# ---------------------------------------------------------------------------
# Vigilancia del motor y known_bad.json
# ---------------------------------------------------------------------------

def _read_pid(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def _is_engine(pid):
    """Evita matar a un proceso ajeno si el PID guardado fue reutilizado."""
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return b"linux-wallpaperengine" in f.read()
    except OSError:
        return False


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def stop_previous(screen):
    pidfile = pid_file(screen)
    old = _read_pid(pidfile)
    # Se invalida el pidfile ANTES de matar: asi el vigilante del proceso viejo ve que
    # fue reemplazado a proposito y no lo toma por un crash.
    with open(pidfile, "w") as f:
        f.write("")
    if old is None or not _is_engine(old):
        return
    try:
        os.kill(old, signal.SIGTERM)
    except ProcessLookupError:
        return
    for _ in range(20):
        if not _alive(old):
            return
        time.sleep(0.1)
    try:
        os.kill(old, signal.SIGKILL)
    except ProcessLookupError:
        pass


def returncode_is_crash(returncode):
    """Popen devuelve -N si murio por la senal N; un 128+N positivo es lo que
    reporta un shell. Parada/cambio deliberado (TERM/KILL/INT/HUP) no cuenta."""
    if returncode < 0:
        return -returncode not in NON_CRASH_SIGNALS
    if returncode >= 128:
        return (returncode - 128) not in NON_CRASH_SIGNALS
    return False


def log_has_crash(logfile, offset):
    try:
        with open(logfile, "rb") as f:
            f.seek(offset)
            text = f.read().decode("utf-8", errors="replace")
    except OSError:
        return False
    return bool(CRASH_LOG_PATTERN.search(text))


def record_result(screen, wid, crashed):
    from datetime import datetime
    with _Lock(_path("known_bad.lock")):
        current = load_json(config.KNOWN_BAD_FILE, {})
        if crashed:
            current[wid] = {"screen": screen, "detected_at": datetime.now().astimezone().isoformat(timespec="seconds")}
        else:
            current.pop(wid, None)
        atomic_write_json(config.KNOWN_BAD_FILE, current)


def watch(screen, wid, proc, logfile, log_offset):
    returncode = proc.wait()
    if _read_pid(pid_file(screen)) != proc.pid:
        return  # alguien (otra llamada a apply) lo reemplazo a proposito
    crashed = returncode_is_crash(returncode) or log_has_crash(logfile, log_offset)
    record_result(screen, wid, crashed)


def restart_screen(screen, wid):
    """Cuerpo del vigilante de una pantalla. Corre en un proceso desacoplado."""
    logfile = log_file(screen)
    lock = _Lock(_path(f"lock_{screen}.lock"))
    lock.__enter__()
    try:
        # Sin el lock, dos llamadas casi simultaneas para la misma pantalla podian leer
        # el mismo pidfile "viejo" y acabar con varios motores vivos a la vez.
        stop_previous(screen)

        # Rotar el log si supera 5 MB (se conserva uno anterior como .1).
        try:
            if os.path.getsize(logfile) > MAX_LOG_BYTES:
                os.replace(logfile, logfile + ".1")
        except OSError:
            pass
        try:
            log_offset = os.path.getsize(logfile)
        except OSError:
            log_offset = 0

        cmd = engine_command(screen, wid)
        with open(logfile, "ab") as log:
            try:
                proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log,
                                        stderr=subprocess.STDOUT)
            except OSError as e:
                log.write(f"No se pudo lanzar linux-wallpaperengine: {e}\n".encode())
                return
        with open(pid_file(screen), "w") as f:
            f.write(str(proc.pid))
    finally:
        lock.release()

    # Fuera del lock: esperar puede tardar indefinidamente.
    watch(screen, wid, proc, logfile, log_offset)


def _detach_and_run(screen, wid):
    pid = os.fork()
    if pid:
        return
    try:
        os.setsid()
        devnull = os.open(os.devnull, os.O_RDWR)
        for fd in (0, 1, 2):
            os.dup2(devnull, fd)
        restart_screen(screen, wid)
    except BaseException:
        import traceback
        try:
            with open(log_file(screen), "a") as f:
                traceback.print_exc(file=f)
        except OSError:
            pass
    finally:
        os._exit(0)


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def parse_pairs(argv):
    """Valida los argumentos PANTALLA=ID. Devuelve (pares, error)."""
    pairs = []
    for arg in argv:
        screen, sep, wid = arg.partition("=")
        if not sep or not screen or not wid:
            return None, f"Formato invalido: '{arg}' (usa PANTALLA=ID)"
        if not ID_RE.match(wid):
            return None, f"ID invalido: '{wid}' (solo digitos)"
        if not SCREEN_RE.match(screen):
            return None, f"Nombre de pantalla invalido: '{screen}'"
        if not os.path.isdir(os.path.join(config.WORKSHOP_DIR, wid)):
            return None, f"No existe el wallpaper con id {wid} en {config.WORKSHOP_DIR}"
        pairs.append((screen, wid))
    return pairs, None


def save_assignments(pairs):
    """Mezcla con lo guardado (para no perder pantallas no mencionadas)."""
    with _Lock(_path("current.lock")):
        current = load_json(config.CURRENT_FILE, {})
        current.update(dict(pairs))
        atomic_write_json(config.CURRENT_FILE, current)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    os.umask(0o077)
    if not argv:
        print("Uso: wallpaperengine-apply PANTALLA=ID [PANTALLA=ID ...]", file=sys.stderr)
        return 1
    pairs, error = parse_pairs(argv)
    if error:
        print(error, file=sys.stderr)
        return 1
    os.makedirs(config.CONF_DIR, exist_ok=True)
    for screen, wid in pairs:
        print(f"  {screen} -> {wid}", flush=True)
        _detach_and_run(screen, wid)
    save_assignments(pairs)
    return 0
