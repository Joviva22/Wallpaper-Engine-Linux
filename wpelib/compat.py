"""Estado de compatibilidad de cada wallpaper: Funciona / Falla / Bloqueado / Sin probar.

Fuente: `known_bad.json` (fallos del motor), el historial `compat.json` (ultimo resultado de una aplicacion
o de una prueba en ventana) y el permiso para fondos web. El ultimo resultado manda: un fondo que fallo
pero luego estuvo funcionando 15 s (o se reparo) deja de figurar como fallo."""
import os
from datetime import datetime

from . import config
from .config import FileLock, atomic_write_json, load_json

OK, FAILED, BLOCKED, UNTESTED = "ok", "failed", "blocked", "untested"
LABELS = {OK: "✓ Funciona", FAILED: "⚠ Falla", BLOCKED: "🔒 Web desactivado", UNTESTED: "Sin probar"}


def history_file():
    return os.path.join(config.CONF_DIR, "compat.json")


def load_history():
    data = load_json(history_file(), {})
    return data if isinstance(data, dict) else {}


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def record(wid, ok, detail="", source="apply"):
    """Apunta el ultimo resultado de `wid`. `source`: "apply" (fondo real) o "preview" (ventana de prueba)."""
    with FileLock(os.path.join(config.CONF_DIR, "compat.lock")):
        data = load_history()
        data[wid] = {"state": OK if ok else FAILED, "at": _now(), "source": source, "detail": detail[-600:]}
        atomic_write_json(history_file(), data)


def clear(wid):
    with FileLock(os.path.join(config.CONF_DIR, "compat.lock")):
        data = load_history()
        if data.pop(wid, None) is not None:
            atomic_write_json(history_file(), data)


def _first_line(text):
    for line in (text or "").splitlines():
        if line.strip():
            return line.strip()[:160]
    return ""


def _date(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return ""


def status(item, known_bad, history, web_allowed):
    """(estado, etiqueta, explicacion) de un wallpaper de load_wallpapers()."""
    wid = item["id"]
    if wid in known_bad:
        entry = known_bad[wid] if isinstance(known_bad[wid], dict) else {}
        reason = _first_line(entry.get("detail")) or f"el motor terminó con código {entry.get('returncode')}"
        when = _date(entry.get("detected_at"))
        return FAILED, LABELS[FAILED], f"Falló{' el ' + when if when else ''}: {reason}"
    if item.get("type") == "Web" and not web_allowed:
        return BLOCKED, LABELS[BLOCKED], "Los fondos web están desactivados; permítelos desde Elegir Fondo."
    entry = history.get(wid)
    if isinstance(entry, dict):
        when = _date(entry.get("at"))
        how = "en una prueba" if entry.get("source") == "preview" else "como fondo"
        if entry.get("state") == OK:
            return OK, LABELS[OK], f"Funcionó {how} el {when}."
        if entry.get("state") == FAILED:
            reason = _first_line(entry.get("detail")) or "el motor falló"
            return FAILED, LABELS[FAILED], f"Falló {how} el {when}: {reason}"
    return UNTESTED, LABELS[UNTESTED], "Aún no se ha probado en este equipo."
