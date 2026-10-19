"""Perfiles de escritorio: guardan y recuperan de un golpe el fondo de cada pantalla y sus ajustes.

Un perfil ("Trabajo", "Juego", "Batería"...) recuerda, por pantalla, el wallpaper asignado, el audio, el
escalado, la velocidad y la rotación (activa/intervalo/orden), más los fotogramas por segundo. No guarda las
listas de rotación: al aplicar un perfil se conservan las listas actuales."""
import copy
import os
import subprocess
import time

from . import config

MAX_NAME = 40
ROTATION_KEYS = ("enabled", "interval_minutes", "mode")


def profiles_file():
    return os.path.join(config.CONF_DIR, "profiles.json")


def _lock():
    return config.FileLock(os.path.join(config.CONF_DIR, "profiles.lock"))


def clean_name(name):
    name = " ".join(str(name or "").split())
    if not name:
        raise ValueError("Escribe un nombre para el perfil.")
    if len(name) > MAX_NAME:
        raise ValueError(f"El nombre es demasiado largo (máximo {MAX_NAME} caracteres).")
    return name


def load_profiles():
    data = config.load_json(profiles_file(), {})
    return {k: v for k, v in data.items() if isinstance(v, dict)} if isinstance(data, dict) else {}


def capture(monitors):
    """Estado actual de `monitors` como perfil."""
    assignments = config.load_json(config.CURRENT_FILE, {})
    playlists = config.load_playlists()
    pick = lambda data: {m: copy.deepcopy(data[m]) for m in monitors if isinstance(data.get(m), dict)}
    return {
        "saved_at": int(time.time()),
        "assignments": {m: assignments[m] for m in monitors if isinstance(assignments.get(m), str)},
        "audio": pick(config.load_audio()),
        "scaling": {m: v for m, v in config.load_scaling().items() if m in monitors and isinstance(v, str)},
        "speed": {m: v for m, v in config.load_speed().items() if m in monitors and isinstance(v, (int, float))},
        "rotation": {m: {k: playlists[m][k] for k in ROTATION_KEYS if k in playlists[m]}
                     for m in monitors if isinstance(playlists.get(m), dict)},
        "fps": config.load_fps(),
    }


def save_profile(name, monitors):
    name = clean_name(name)
    with _lock():
        data = load_profiles()
        data[name] = capture(monitors)
        config.atomic_write_json(profiles_file(), data)
    return name


def delete_profile(name):
    with _lock():
        data = load_profiles()
        if data.pop(name, None) is not None:
            config.atomic_write_json(profiles_file(), data)
            return True
    return False


def _merge(load, save, saved, monitors):
    current = load()
    for monitor in monitors:
        if monitor in saved:
            current[monitor] = saved[monitor]
    save(current)


def apply_profile(name, monitors, installed_ids, apply_fn=None, now=None):
    """Aplica el perfil `name` a las pantallas conectadas (`monitors`). `installed_ids`: ids de wallpapers
    instalados. Devuelve (True, [pantallas con fondo cambiado], [avisos]) o (False, [], [motivo])."""
    profile = load_profiles().get(name)
    if not profile:
        return False, [], [f"No existe el perfil «{name}»."]
    now = time.time() if now is None else now
    notes = []
    _merge(config.load_audio, config.save_audio, profile.get("audio", {}), monitors)
    _merge(config.load_scaling, config.save_scaling, profile.get("scaling", {}), monitors)
    _merge(config.load_speed, config.save_speed, profile.get("speed", {}), monitors)
    if profile.get("fps") in config.FPS_OPTIONS:
        config.set_fps(profile["fps"])

    assignments = []
    for monitor in monitors:
        wid = profile.get("assignments", {}).get(monitor)
        if not wid:
            continue
        if wid not in installed_ids:
            notes.append(f"{monitor}: el wallpaper {wid} ya no está instalado.")
            continue
        assignments.append((monitor, wid))

    with config.FileLock(config.PLAYLISTS_LOCK):
        playlists = config.load_playlists()
        for monitor, saved in profile.get("rotation", {}).items():
            if monitor not in monitors:
                continue
            entry = playlists.setdefault(monitor, {"items": [], "current_index": 0, "last_switch": 0})
            if not isinstance(entry, dict):
                continue
            for key in ROTATION_KEYS:
                if key in saved:
                    entry[key] = saved[key]
            assigned = dict(assignments).get(monitor)
            if assigned in entry.get("items", []):
                entry["current_index"] = entry["items"].index(assigned)
            entry["last_switch"] = now   # la cuenta atrás de la rotación empieza ahora
            entry.pop("bag", None)
        config.atomic_write_json(config.PLAYLISTS_FILE, playlists)

    if assignments:
        run = apply_fn or (lambda pairs: subprocess.Popen(
            [config.APPLY_SCRIPT, *[f"{m}={w}" for m, w in pairs]], stdin=subprocess.DEVNULL))
        run(assignments)
    return True, [m for m, _w in assignments], notes
