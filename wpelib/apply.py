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
import math
import os
import re
import signal
import resource
import select
import uuid
import subprocess
import sys
import threading
import time

from . import config
from .config import FileLock, atomic_write_json, load_json
from .engine_log import append_bounded, capture

MAX_LOG_BYTES = 5 * 1024 * 1024
# Segundos que un fondo debe seguir vivo para considerarlo "el ultimo que funcionaba" de su pantalla.
STABLE_SECONDS = 15
# Firmas de errores de datos de escena/proyecto que repair.py sabe corregir.
REPAIRABLE_LOG_PATTERN = re.compile(
    r"type_error\.302|Combo property must have a value|Projection must have (?:a )?(?:width|height)",
    re.IGNORECASE,
)
CRASH_LOG_PATTERN = re.compile(r"terminate called|Segmentation fault|Aborted \(core dumped\)|pure virtual method called")
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
    if isinstance(speed, (int, float)) and not isinstance(speed, bool) and math.isfinite(speed) and 0.25 <= speed <= 4 and speed != 1 \
            and config.engine_supports_speed():
        return ["--speed", str(speed)]
    return []


def project_type(wid):
    from .classify import classify_project

    def resolve(item):
        folder = os.path.join(config.WORKSHOP_DIR, item)
        if not os.path.isfile(os.path.join(folder, "project.json")):
            return None
        try:
            return load_json(os.path.join(folder, "project.json"), {}), os.listdir(folder)
        except OSError:
            return None

    project = resolve(wid)
    if not project:
        return ""
    kind = classify_project(wid, project[0], project[1], resolve=resolve)['type'].lower()
    return kind if kind in ("web", "video", "scene") else ""


def web_block_reason(wid):
    if project_type(wid) == "web" and not config.web_wallpapers_allowed():
        return "Los fondos web están desactivados. Permítelos explícitamente desde Elegir Fondo antes de aplicarlos."
    return ""


def find_libcef():
    """Ruta de libcef.so junto al motor instalado (o None). El paquete instala un
    wrapper en /usr/bin que hace `cd <dir>`; si no, se prueba junto al binario."""
    import shutil
    exe = shutil.which(config.engine_executable())
    candidates = [config.PATCHED_ENGINE_DIR]
    if exe:
        try:
            with open(exe, encoding="utf-8", errors="ignore") as f:
                m = re.search(r"^cd\s+(\S+?);", f.read(4096), re.M)
            if m:
                candidates.append(m.group(1).strip("\"'"))
        except OSError:
            pass
        candidates.append(os.path.dirname(os.path.realpath(exe)))
    candidates.append("/opt/linux-wallpaperengine")
    for d in candidates:
        path = os.path.join(d, "libcef.so")
        if os.path.isfile(path):
            return path
    return None


def engine_env(wid):
    """Entorno del motor. Los wallpapers de tipo web necesitan libcef.so cargado ANTES
    que libc (LD_PRELOAD); si no, el motor muere al arrancar con SIGTRAP y el mensaje
    "close symbol missing" (Almamu/linux-wallpaperengine#628). Solo se precarga para
    wallpapers web, porque libcef.so pesa ~230 MB."""
    env = os.environ.copy()
    if project_type(wid) == "web":
        libcef = find_libcef()
        if libcef:
            env["LD_PRELOAD"] = libcef + (os.pathsep + env["LD_PRELOAD"] if env.get("LD_PRELOAD") else "")
    return env


def engine_command(screen, wid):
    return [
        config.engine_executable(), "--assets-dir", config.ASSETS_DIR, "--fps", "30",
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
    return returncode != 0


def _log_text(logfile, offset):
    try:
        with open(logfile, "rb") as f:
            f.seek(offset)
            return f.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def log_has_crash(logfile, offset):
    return bool(CRASH_LOG_PATTERN.search(_log_text(logfile, offset)))


def log_is_repairable(logfile, offset):
    return bool(REPAIRABLE_LOG_PATTERN.search(_log_text(logfile, offset)))


def record_result(screen, wid, crashed, returncode=None, detail=""):
    from datetime import datetime
    with _Lock(_path("known_bad.lock")):
        current = load_json(config.KNOWN_BAD_FILE, {})
        if crashed:
            current[wid] = {"screen": screen, "detected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                            "returncode": returncode, "detail": detail[-4000:]}
        else:
            current.pop(wid, None)
        atomic_write_json(config.KNOWN_BAD_FILE, current)


def try_auto_repair(wid, logfile, log_offset, repairable=None):
    """Si el crash tiene la firma de un bug de formato que repair.py sabe corregir,
    lo repara (con backup scene.pkg.bak_original). Devuelve True si cambio algo."""
    if not (log_is_repairable(logfile, log_offset) if repairable is None else repairable):
        return False
    from . import repair
    changed, message = repair.attempt_repair(wid)
    append_bounded(logfile, f"[wallpaperengine-picker] auto-reparacion de {wid}: {message}\n".encode(), MAX_LOG_BYTES)
    return changed


def write_status(screen, wid, state, detail="", returncode=None, **extra):
    atomic_write_json(_path(f"status_{screen}.json"), {
        "id": wid, "state": state, "detail": detail.replace("\x00", "")[-4000:],
        "returncode": returncode, "token": uuid.uuid4().hex, **extra,
    })


def last_good_file():
    return _path("last_good.json")


def get_last_good(screen):
    """Ultimo wallpaper que estuvo STABLE_SECONDS funcionando en esa pantalla (o None)."""
    value = load_json(last_good_file(), {}).get(screen)
    return value if isinstance(value, str) and ID_RE.match(value) else None


def mark_last_good(screen, wid):
    with _Lock(_path("last_good.lock")):
        data = load_json(last_good_file(), {})
        data[screen] = wid
        atomic_write_json(last_good_file(), data)


def disable_core_dumps():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def watch(screen, wid, proc, logfile, log_offset, allow_repair=True,
          evidence=None, on_started=None, fallback=True):
    returncode = proc.wait()
    with _Lock(_path(f"lock_{screen}.lock")):
        if _read_pid(pid_file(screen)) != proc.pid:
            if on_started:
                on_started(False, "La selección fue reemplazada por otra.")
            return
    crashed = returncode_is_crash(returncode) or (
        evidence['crashed'] if evidence is not None else log_has_crash(logfile, log_offset))
    repairable = evidence['repairable'] if evidence is not None else None
    if crashed and allow_repair and try_auto_repair(wid, logfile, log_offset, repairable):
        restart_screen(screen, wid, allow_repair=False, on_started=on_started, expected_pid=proc.pid,
                       fallback=fallback)
        return
    detail = evidence['tail'] if evidence is not None else _log_text(logfile, log_offset)[-4000:]
    good = get_last_good(screen) if (crashed and fallback) else None
    if good == wid or (good and not os.path.isdir(os.path.join(config.WORKSHOP_DIR, good))):
        good = None
    with _Lock(_path(f"lock_{screen}.lock")):
        # Revalidar tras una reparación/lectura: no pisar el estado de otro motor.
        if _read_pid(pid_file(screen)) != proc.pid:
            if on_started:
                on_started(False, "La selección fue reemplazada por otra.")
            return
        record_result(screen, wid, crashed, returncode, detail)
        state = "failed" if crashed else "stopped"
        message = f"El motor terminó con código {returncode}. " + detail
        if not good:
            write_status(screen, wid, state, message, returncode)
    if good:
        # El fondo nuevo fallo: se avisa de por que y se restaura el ultimo que funcionaba. El estado
        # "rolled_back" lo escribe el relanzamiento cuando el fondo anterior ya esta en marcha.
        if on_started:
            on_started(False, message + f"\nSe restaura el fondo anterior ({good}).")
        restart_screen(screen, good, allow_repair=False, fallback=False, rollback=(wid, message, returncode))
        return
    if on_started:
        on_started(False, message)


def restart_screen(screen, wid, allow_repair=True, on_started=None, expected_pid=None, fallback=True, rollback=None):
    """Lanza el motor, confirma que permanece vivo y recoge su salida hasta el final."""
    reason = web_block_reason(wid)
    if reason:
        write_status(screen, wid, "blocked", reason)
        if on_started:
            on_started(False, reason)
        return
    logfile = log_file(screen)
    with _Lock(_path(f"lock_{screen}.lock")):
        if expected_pid is not None and _read_pid(pid_file(screen)) != expected_pid:
            if on_started:
                on_started(False, "La selección fue reemplazada durante la reparación.")
            return
        stop_previous(screen)
        # Se conserva la rotación inicial para logs antiguos de tamaño excesivo.
        if os.path.exists(logfile) and os.path.getsize(logfile) >= MAX_LOG_BYTES:
            os.replace(logfile, logfile + ".1")
        append_bounded(logfile, f"[picker] Inicio {screen}={wid}\n".encode(), MAX_LOG_BYTES)
        try:
            proc = subprocess.Popen(engine_command(screen, wid), stdin=subprocess.DEVNULL,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    env=engine_env(wid), preexec_fn=disable_core_dumps)
        except OSError as exc:
            detail = f"No se pudo lanzar linux-wallpaperengine: {exc}"
            append_bounded(logfile, (detail + "\n").encode(), MAX_LOG_BYTES)
            record_result(screen, wid, True, None, detail)
            write_status(screen, wid, "failed", detail)
            if on_started:
                on_started(False, detail)
            return
        with open(pid_file(screen), "w") as f:
            f.write(str(proc.pid))

    def ready():
        with _Lock(_path(f"lock_{screen}.lock")):
            if _read_pid(pid_file(screen)) != proc.pid:
                return
            save_assignments([(screen, wid)])
            if rollback:
                failed_id, reason, failed_code = rollback
                write_status(screen, wid, "rolled_back", reason, failed_code, failed_id=failed_id)
            else:
                write_status(screen, wid, "running")
            if on_started:
                on_started(True, "")

        def confirm_stable():
            # Solo cuenta como "ultimo que funcionaba" si sigue vivo tras STABLE_SECONDS.
            if proc.poll() is None and _read_pid(pid_file(screen)) == proc.pid:
                mark_last_good(screen, wid)

        timer = threading.Timer(STABLE_SECONDS, confirm_stable)
        timer.daemon = True
        timer.start()

    evidence = capture(proc, logfile, MAX_LOG_BYTES, CRASH_LOG_PATTERN,
                       REPAIRABLE_LOG_PATTERN, ready)
    watch(screen, wid, proc, logfile, 0, allow_repair, evidence, on_started, fallback)


def _detach_and_run(screen, wid):
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid:
        os.close(write_fd)
        try:
            if not select.select([read_fd], [], [], 20)[0]:
                return False, "No se recibió confirmación de arranque a tiempo."
            payload = json.loads(os.read(read_fd, 8192).decode())
            return payload['ok'], payload['detail']
        except (ValueError, OSError, KeyError):
            return False, "El vigilante terminó sin confirmar el arranque."
        finally:
            os.close(read_fd)
    os.close(read_fd)
    sent = False

    def report(ok, detail):
        nonlocal sent
        if sent:
            return
        sent = True
        try:
            os.write(write_fd, json.dumps({"ok": ok, "detail": detail[-800:]}, ensure_ascii=False).encode())
        except OSError:
            pass
        finally:
            os.close(write_fd)

    try:
        os.setsid()
        devnull = os.open(os.devnull, os.O_RDWR)
        for fd in (0, 1, 2):
            os.dup2(devnull, fd)
        os.close(devnull)
        restart_screen(screen, wid, on_started=report)
    except BaseException as exc:
        report(False, f"Error del vigilante: {exc}")
    finally:
        report(False, "El motor terminó antes de confirmar el arranque.")
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
    for screen, wid in pairs:
        reason = web_block_reason(wid)
        if reason:
            write_status(screen, wid, "blocked", reason)
            print(f"{screen}: {reason}", file=sys.stderr)
            return 1
    os.makedirs(config.CONF_DIR, exist_ok=True)
    success = True
    for screen, wid in pairs:
        print(f"  {screen} -> {wid}", flush=True)
        ok, detail = _detach_and_run(screen, wid)
        if not ok:
            success = False
            print(f"{screen}: {detail}", file=sys.stderr)
    return 0 if success else 1
