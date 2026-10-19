"""Informe de diagnostico: lo que hace falta para entender por que un fondo no funciona, en texto plano.

Pensado para pegarlo en un issue: sustituye la carpeta personal por `~` y no incluye ninguna clave ni
configuracion privada, solo estados, rutas relativas y las ultimas lineas del registro del motor."""
import glob
import os
import subprocess
import time
from datetime import datetime

from . import compat, config, rotation
from .config import load_json

LOG_LINES = 25
BAD_LIMIT = 8


def _home(text):
    home = os.path.expanduser("~")
    return (text or "").replace(home, "~")


def _repo_version():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        out = subprocess.run(["git", "-C", root, "log", "-1", "--format=%h %cs"], capture_output=True, text=True,
                             timeout=5, stdin=subprocess.DEVNULL)
        return out.stdout.strip() or "desconocida"
    except (OSError, subprocess.SubprocessError):
        return "desconocida"


def _engine_info():
    exe = config.engine_executable()
    patched = os.path.join(config.PATCHED_ENGINE_DIR, "linux-wallpaperengine")
    info = [f"motor: {_home(exe)}" + (" (parcheado)" if os.path.exists(patched) and exe.startswith(config.PATCHED_ENGINE_DIR) else "")]
    try:
        stamp = datetime.fromtimestamp(os.path.getmtime(patched if os.path.exists(patched) else exe))
        info.append(f"compilado/instalado: {stamp:%Y-%m-%d %H:%M}")
    except OSError:
        pass
    patches = sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "patches", "*.patch")))
    info.append(f"parches en el repositorio: {len(patches)}")
    return info


def _tail(path, lines):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 16000))
            text = f.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    return [line for line in text.splitlines() if line.strip()][-lines:]


def _titles():
    try:
        return {item["id"]: item["title"] for item in config.load_wallpapers()}
    except Exception:
        return {}


def build_report(now=None):
    now = time.time() if now is None else now
    titles = _titles()
    name = lambda wid: f"{titles.get(wid, '?')} ({wid})" if wid else "-"
    out = [f"Informe de Elegir Fondo — {datetime.fromtimestamp(now):%Y-%m-%d %H:%M:%S}",
           f"version: {_repo_version()}", *_engine_info(),
           f"fondos web permitidos: {'si' if config.web_wallpapers_allowed() else 'no'}", ""]

    current = load_json(config.CURRENT_FILE, {})
    last_good = load_json(os.path.join(config.CONF_DIR, "last_good.json"), {})
    out.append("== Pantallas ==")
    screens = sorted(set(current) | set(last_good) | {os.path.basename(p)[7:-5] for p in
                                                      glob.glob(os.path.join(config.CONF_DIR, "status_*.json"))})
    for screen in screens:
        status = load_json(os.path.join(config.CONF_DIR, f"status_{screen}.json"), {})
        out.append(f"{screen}: asignado {name(current.get(screen))}")
        out.append(f"  ultimo que funcionaba: {name(last_good.get(screen))}")
        if status:
            out.append(f"  ultimo estado: {status.get('state')} ({name(status.get('id'))})")
            if status.get("failed_id"):
                out.append(f"  restaurado tras fallo de {name(status['failed_id'])}")
            detail = (status.get("detail") or "").strip()
            if detail and status.get("state") != "running":
                out.append("  motivo: " + _home(detail.splitlines()[-1][:300]))
        info = rotation.status(screen, now=now)
        if info["items"]:
            state = "pausada" if info["paused"] else ("activa" if info["enabled"] else "desactivada")
            out.append(f"  rotacion {state}: {info['playable']}/{info['items']} fondos pueden rotar; "
                       f"siguiente {name(info['next'])}")
    out.append("")

    bad = load_json(config.KNOWN_BAD_FILE, {})
    out.append(f"== Fallos conocidos ({len(bad)}) ==")
    recent = sorted(bad.items(), key=lambda kv: (kv[1] or {}).get("detected_at", ""), reverse=True)[:BAD_LIMIT]
    for wid, entry in recent:
        entry = entry if isinstance(entry, dict) else {}
        reason = next((l for l in reversed((entry.get("detail") or "").splitlines()) if l.strip()), "")
        out.append(f"{name(wid)}  {entry.get('detected_at', '')}  codigo {entry.get('returncode')}  {_home(reason)[:200]}")
    if len(bad) > len(recent):
        out.append(f"... y {len(bad) - len(recent)} mas")
    out.append("")

    history = compat.load_history()
    counts = {}
    for entry in history.values():
        counts[entry.get("state")] = counts.get(entry.get("state"), 0) + 1
    out.append(f"== Compatibilidad registrada == {counts or 'sin datos'}")
    out.append("")

    for screen in screens:
        lines = _tail(os.path.join(config.CONF_DIR, f"wallpaperengine_{screen}.log"), LOG_LINES)
        if lines:
            out.append(f"== Registro del motor en {screen} (ultimas {len(lines)} lineas) ==")
            out.extend(_home(line[:300]) for line in lines)
            out.append("")
    return "\n".join(out).rstrip() + "\n"
