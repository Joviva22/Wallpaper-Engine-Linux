"""Configuracion, deteccion de la biblioteca de Steam y estado persistido en
disco: wallpapers ocultos, listas de rotacion, wallpapers con fallos
conocidos, y el escaneo de la biblioteca local ya descargada."""
import copy
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile

from PIL import Image

APPID = "431960"
CONF_DIR = os.path.expanduser("~/.config/wallpaperengine-picker")
CONFIG_FILE = os.path.join(CONF_DIR, "config.json")
CURRENT_FILE = os.path.join(CONF_DIR, "current.json")
HIDDEN_LOCK_FILE = os.path.join(CONF_DIR, "hidden_lock.json")
HIDDEN_FILE = os.path.join(CONF_DIR, "hidden.json")
FAVORITES_FILE = os.path.join(CONF_DIR, "favorites.json")
RECENTS_FILE = os.path.join(CONF_DIR, "recents.json")
UI_STATE_FILE = os.path.join(CONF_DIR, "ui_state.json")
PLAYLISTS_FILE = os.path.join(CONF_DIR, "playlists.json")
KNOWN_BAD_FILE = os.path.join(CONF_DIR, "known_bad.json")
SCALING_FILE = os.path.join(CONF_DIR, "scaling.json")
SCALING_MODES = ["fill", "fit", "stretch", "default"]
DEFAULT_SCALING = "fill"
PROPERTIES_FILE = os.path.join(CONF_DIR, "properties.json")
AUDIO_FILE = os.path.join(CONF_DIR, "audio.json")
DEFAULT_VOLUME = 50
SPEED_FILE = os.path.join(CONF_DIR, "speed.json")
SPEED_OPTIONS = [1.0, 1.5, 2.0, 3.0, 4.0]
DEFAULT_SPEED = 1.0
MAX_RECENTS = 100
CACHE_DIR = os.path.expanduser("~/.cache/wallpaperengine-picker/thumbs_v5")
WORKSHOP_THUMB_CACHE = os.path.expanduser("~/.cache/wallpaperengine-picker/workshop_thumbs")
APPLY_SCRIPT = os.path.expanduser("~/.local/bin/wallpaperengine-apply")
THUMB_SIZE = (320, 320)  # 1:1; debe coincidir con CARD_SIZE en wpelib/ui.py
DEFAULT_ID = "2168640648"
STEAM_API_QUERYFILES = "https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/"

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(WORKSHOP_THUMB_CACHE, exist_ok=True)
os.makedirs(CONF_DIR, exist_ok=True)


def atomic_write_json(path, data):
    """Escribe JSON a un temporal en el mismo directorio y lo renombra encima
    (os.replace es atomico): un crash o una escritura concurrente nunca deja
    el archivo a medias."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _id_set(data):
    if not isinstance(data, list):
        raise ValueError("se esperaba una lista")
    return set(data)


def load_json(path, default, convert=None):
    """Lee JSON de `path`. Si no existe, devuelve una copia de `default`. Si esta
    corrupto o no tiene la forma esperada, lo aparta como `path.corrupt` (en vez
    de dejar que el siguiente save_* lo sobrescriba y se pierdan los datos sin
    aviso) y devuelve `default`. `convert` (p.ej. set) valida/transforma."""
    if not os.path.isfile(path):
        return copy.deepcopy(default)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if convert is not None:
            data = convert(data)
        elif not isinstance(data, type(default)):
            raise ValueError("tipo inesperado")
        return data
    except OSError:
        return copy.deepcopy(default)
    except (ValueError, TypeError):  # incluye JSONDecodeError y UnicodeDecodeError
        try:
            os.replace(path, path + ".corrupt")
        except OSError:
            pass
        return copy.deepcopy(default)


# ---------------------------------------------------------------------------
# Configuracion y deteccion de la biblioteca de Steam
# ---------------------------------------------------------------------------

def parse_libraryfolders(vdf_path):
    paths = []
    try:
        with open(vdf_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for match in re.findall(r'"path"\s*"([^"]+)"', content):
            paths.append(match.replace("\\\\", "/"))
    except Exception:
        pass
    return paths


def detect_steam_library():
    candidates = [os.path.expanduser("~/.local/share/Steam"), os.path.expanduser("~/.steam/steam")]
    lib_paths = []
    for base in candidates:
        vdf = os.path.join(base, "steamapps", "libraryfolders.vdf")
        if os.path.isfile(vdf):
            lib_paths.append(base)
            lib_paths.extend(parse_libraryfolders(vdf))

    seen = []
    for p in lib_paths:
        if p not in seen:
            seen.append(p)

    for p in seen:
        if os.path.isdir(os.path.join(p, "steamapps", "workshop", "content", APPID)) or \
           os.path.isdir(os.path.join(p, "steamapps", "common", "wallpaper_engine")):
            return p

    return seen[0] if seen else os.path.expanduser("~/.local/share/Steam")


def load_config():
    cfg = load_json(CONFIG_FILE, {})
    changed = False
    if not cfg.get("steam_library") or not os.path.isdir(cfg.get("steam_library", "")):
        cfg["steam_library"] = detect_steam_library()
        changed = True
    if changed:
        save_config(cfg)
    return cfg


def save_config(cfg):
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(CONFIG_FILE, cfg)
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass


CONFIG = load_config()
STEAM_LIB = CONFIG["steam_library"]
WORKSHOP_DIR = os.path.join(STEAM_LIB, "steamapps", "workshop", "content", APPID)
ASSETS_DIR = os.path.join(STEAM_LIB, "steamapps", "common", "wallpaper_engine", "assets")


def detect_monitors():
    try:
        out = subprocess.check_output(["xrandr", "--listmonitors"], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []
    lines = out.strip().splitlines()[1:]
    return [line.split()[-1] for line in lines if line.strip()]


def load_current_assignments(monitors):
    assignments = load_json(CURRENT_FILE, {})
    for mon in monitors:
        assignments.setdefault(mon, DEFAULT_ID)
    return assignments


def load_known_bad():
    """Ids que hicieron crashear linux-wallpaperengine la ultima vez que se probaron
    (detectado por wallpaperengine-apply, ver known_bad.json)."""
    return load_json(KNOWN_BAD_FILE, {})


def load_hidden_ids():
    return load_json(HIDDEN_FILE, set(), _id_set)


def save_hidden_ids(ids):
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(HIDDEN_FILE, sorted(ids))


def has_hidden_password():
    return os.path.isfile(HIDDEN_LOCK_FILE)


def set_hidden_password(password):
    """Protege la pestaña 'Ocultos' con una contraseña. Se guarda con
    PBKDF2-HMAC-SHA256 + salt aleatorio, nunca en texto plano — no es proteccion
    criptografica de verdad (quien tenga acceso al disco puede leer hidden.json
    igualmente), solo evita que alguien la vea de pasada sin querer."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000).hex()
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(HIDDEN_LOCK_FILE, {"salt": salt, "hash": digest})
    try:
        os.chmod(HIDDEN_LOCK_FILE, 0o600)
    except OSError:
        pass


def clear_hidden_password():
    if os.path.isfile(HIDDEN_LOCK_FILE):
        os.remove(HIDDEN_LOCK_FILE)


def verify_hidden_password(password):
    if not os.path.isfile(HIDDEN_LOCK_FILE):
        return True
    try:
        with open(HIDDEN_LOCK_FILE, encoding="utf-8") as f:
            data = json.load(f)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(data["salt"]), 200_000
        ).hex()
        return secrets.compare_digest(digest, data["hash"])
    except Exception:
        return False


def load_favorite_ids():
    return load_json(FAVORITES_FILE, set(), _id_set)


def save_favorite_ids(ids):
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(FAVORITES_FILE, sorted(ids))


def load_recent_ids():
    """Devuelve los ids aplicados recientemente, mas reciente primero."""
    return load_json(RECENTS_FILE, [])


def record_recent(wid):
    recents = [r for r in load_recent_ids() if r != wid]
    recents.insert(0, wid)
    recents = recents[:MAX_RECENTS]
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(RECENTS_FILE, recents)
    return recents


def load_ui_state():
    return load_json(UI_STATE_FILE, {})


def save_ui_state(state):
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(UI_STATE_FILE, state)


def load_playlists():
    return load_json(PLAYLISTS_FILE, {})


def save_playlists(data):
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(PLAYLISTS_FILE, data)


def load_scaling():
    """Modo de escalado guardado por pantalla, { "PANTALLA": "fill"|"fit"|"stretch"|"default" }."""
    return load_json(SCALING_FILE, {})


def save_scaling(data):
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(SCALING_FILE, data)


def load_properties():
    """Overrides de propiedades personalizables guardados por wallpaper,
    { "wallpaper_id": { "propkey": "valor" } } (ver wpelib/properties.py)."""
    return load_json(PROPERTIES_FILE, {})


def save_properties(data):
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(PROPERTIES_FILE, data)


def load_audio():
    """Configuracion de audio guardada por pantalla,
    { "PANTALLA": {"muted": bool, "volume": 0-100} }. Silenciado por defecto
    (mismo comportamiento que antes de que esto existiera): --silent solo afecta
    al sonido PROPIO del wallpaper (video/musica incrustada), no a que reaccione
    al audio del sistema (eso lo controla --no-audio-processing, que esta app
    nunca pasa, asi que la reactividad al audio funciona independientemente de
    si esta silenciado o no)."""
    return load_json(AUDIO_FILE, {})


def save_audio(data):
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(AUDIO_FILE, data)


def load_speed():
    """Velocidad de reproduccion guardada por pantalla, { "PANTALLA": 1.0-4.0 }.
    Requiere el flag --speed de linux-wallpaperengine (anadido en esta sesion,
    parchea GLPlayer para llamar mpv_set_property(handle, "speed", ...) — solo
    afecta a wallpapers de tipo Video o con video incrustado; en una escena sin
    video no tiene ningun efecto. 1.0 (normal) si no hay nada guardado."""
    return load_json(SPEED_FILE, {})


def save_speed(data):
    os.makedirs(CONF_DIR, exist_ok=True)
    atomic_write_json(SPEED_FILE, data)


def unsubscribe_workshop_item(wid):
    """Borra el contenido local del wallpaper y lo quita de cualquier lista de
    rotacion. No es un unsubscribe real en Steam (eso requiere el cliente
    autenticado con tu cuenta); solo limpia lo que tenemos en disco/config."""
    folder = os.path.join(WORKSHOP_DIR, wid)
    if os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)

    thumb = os.path.join(CACHE_DIR, f"{wid}.png")
    if os.path.isfile(thumb):
        os.remove(thumb)

    playlists = load_playlists()
    changed = False
    for data in playlists.values():
        items = data.get("items", [])
        if wid in items:
            data["items"] = [i for i in items if i != wid]
            changed = True
    if changed:
        save_playlists(playlists)

    favorites = load_favorite_ids()
    if wid in favorites:
        favorites.discard(wid)
        save_favorite_ids(favorites)

    properties = load_properties()
    if wid in properties:
        del properties[wid]
        save_properties(properties)


def build_thumb(preview_path, dest_path):
    try:
        img = Image.open(preview_path)
        img = img.convert("RGB")
        img.thumbnail(THUMB_SIZE, Image.LANCZOS)
        canvas = Image.new("RGB", THUMB_SIZE, (30, 30, 30))
        x = (THUMB_SIZE[0] - img.width) // 2
        y = (THUMB_SIZE[1] - img.height) // 2
        canvas.paste(img, (x, y))
        canvas.save(dest_path, "PNG")
        return True
    except Exception:
        return False


def load_wallpapers():
    """Devuelve lista de dicts: id, title, thumb (ruta si ya esta en cache, si
    no None), preview_path (para generar la miniatura mas tarde en segundo
    plano), tags, rating, mtime, type. No genera miniaturas aqui (para no
    bloquear la interfaz la primera vez que aparecen wallpapers nuevos);
    eso lo hace el llamador con build_thumb() de forma progresiva."""
    items = []
    if not os.path.isdir(WORKSHOP_DIR):
        return items
    for entry in sorted(os.listdir(WORKSHOP_DIR)):
        folder = os.path.join(WORKSHOP_DIR, entry)
        project_path = os.path.join(folder, "project.json")
        if not os.path.isfile(project_path):
            continue
        try:
            with open(project_path, encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            title = data.get("title", entry)
            preview = data.get("preview", "")
            tags = data.get("tags", []) or []
            rating = data.get("contentrating", "Desconocido") or "Desconocido"
            wtype = data.get("type", "Desconocido") or "Desconocido"
        except Exception:
            title, preview, tags, rating, wtype = entry, "", [], "Desconocido", "Desconocido"

        # Wallpaper Engine no es consistente con las mayusculas de "type"
        # ("scene" vs "Scene", "video" vs "Video"...); lo normalizamos aqui
        # una sola vez para que todo el resto de la app compare de forma fiable.
        wtype = wtype.strip().capitalize() if isinstance(wtype, str) and wtype.strip() else "Desconocido"

        thumb_path = os.path.join(CACHE_DIR, f"{entry}.png")
        has_cached_thumb = os.path.isfile(thumb_path)
        preview_path = os.path.join(folder, preview) if preview else ""

        try:
            mtime = os.path.getmtime(folder)
        except OSError:
            mtime = 0

        items.append({
            "id": entry, "title": title,
            "thumb": thumb_path if has_cached_thumb else None,
            "preview_path": preview_path if os.path.isfile(preview_path) else None,
            "tags": tags, "rating": rating, "mtime": mtime, "type": wtype,
        })
    items.sort(key=lambda r: r["title"].lower())
    return items


SORT_OPTIONS = {
    "Mas reciente primero": lambda item: -item["mtime"],
    "Mas antiguo primero": lambda item: item["mtime"],
    "Titulo (A-Z)": lambda item: item["title"].lower(),
    "Titulo (Z-A)": lambda item: item["title"].lower(),
}
SORT_REVERSE = {"Titulo (Z-A)": True}
