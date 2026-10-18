"""Nikke Stage: logica compartida por scripts/nikke-stage.py y la ventana de personajes de la app.

Gestiona los personajes instalados (packs gratuitos de nikke-wallpaper-packs), el manifiesto que lee
el wallpaper y la generacion del propio wallpaper en la carpeta del Workshop (id 9100000001)."""
import json
import os
import re
import shutil
import tempfile
import urllib.request

from . import l2d_pack
from .l2d_pack import PackError

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(REPO, "wallpapers", "nikke-stage")
WALLPAPER_ID = "9100000001"
L2D_INDEX_URL = "https://raw.githubusercontent.com/Nikke-db/Nikke-db.github.io/main/js/json/l2d.json"
SLOTS = 4
RUNTIME_FILES = ("spine-player.js", "spine-player4.1.js", "spine-player.css")
DEFAULT_X = {1: 50, 2: 25, 3: 75, 4: 10}


def config_files():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "wallpaperengine-picker", "web_css", "files", "stage")


def workshop_dir():
    try:
        from . import config
        if os.path.isdir(config.WORKSHOP_DIR):
            return config.WORKSHOP_DIR
    except Exception:
        pass
    for path in ("~/.local/share/Steam/steamapps/workshop/content/431960",
                 "~/.steam/steam/steamapps/workshop/content/431960"):
        full = os.path.expanduser(path)
        if os.path.isdir(full):
            return full
    raise PackError("No encuentro la carpeta del Workshop de Wallpaper Engine (431960).")


def read_manifest():
    path = os.path.join(config_files(), "characters.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data.get("characters"), dict):
            return data
    except (OSError, ValueError):
        pass
    return {"characters": {}}


def write_manifest(manifest):
    os.makedirs(config_files(), exist_ok=True)
    with open(os.path.join(config_files(), "characters.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def l2d_index():
    """Nombres y version de Spine de cada codigo (Nikke-db). Sin red, se usa el codigo como nombre."""
    cache = os.path.join(config_files(), "l2d_index.json")
    try:
        with urllib.request.urlopen(L2D_INDEX_URL, timeout=20) as resp:
            data = json.loads(resp.read(5 * 1024 * 1024))
        os.makedirs(config_files(), exist_ok=True)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except (OSError, ValueError):
        try:
            with open(cache, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = []
    return {item.get("id"): item for item in data if isinstance(item, dict)}


def skeleton_version(code):
    """Version de Spine del esqueleto binario (cabecera del .skel): '4.1' o '4.0'.
    Los esqueletos 4.1 necesitan el reproductor spine-player4.1.js; el resto, spine-player.js."""
    path = os.path.join(config_files(), "characters", code, f"{code}_00.skel")
    try:
        with open(path, "rb") as f:
            head = f.read(96)
    except OSError:
        return "4.0"
    match = re.search(rb"(\d)\.(\d)\.\d+", head)
    return "4.1" if match and match.group(1) == b"4" and match.group(2) == b"1" else "4.0"


def find_runtime_dir(workshop):
    for entry in sorted(os.listdir(workshop)):
        folder = os.path.join(workshop, entry)
        if entry != WALLPAPER_ID and all(os.path.isfile(os.path.join(folder, n)) for n in RUNTIME_FILES):
            return folder
    raise PackError("Necesito los reproductores Spine de un wallpaper de Nikke del Workshop (spine-player.js y "
             "spine-player4.1.js). Suscribete a cualquiera, por ejemplo 'Nikke Alice Wonderland Bunny'.")


def build_properties(manifest):
    options = [{"label": "(ninguno)", "value": "none"}]
    for code, entry in sorted(manifest["characters"].items()):
        options.append({"label": f"{entry.get('name', code)} ({code})", "value": code})
    codes = [o["value"] for o in options]
    properties = {}
    order = 0
    for i in range(1, SLOTS + 1):
        default = codes[i] if i < len(codes) else "none"
        order += 1
        properties[f"char{i}"] = {"order": order, "text": f"Personaje {i}", "type": "combo",
                                  "value": default, "options": options}
        order += 1
        properties[f"x{i}"] = {"order": order, "text": f"Posicion horizontal {i} (%)", "type": "slider",
                               "min": 0, "max": 100, "step": 1, "value": DEFAULT_X[i]}
        order += 1
        properties[f"scale{i}"] = {"order": order, "text": f"Tamano {i} (%)", "type": "slider",
                                   "min": 20, "max": 150, "step": 1, "value": 90}
        order += 1
        properties[f"y{i}"] = {"order": order, "text": f"Altura {i} (%)", "type": "slider",
                               "min": -30, "max": 60, "step": 1, "value": 0}
        order += 1
        properties[f"flip{i}"] = {"order": order, "text": f"Espejo {i}", "type": "bool", "value": False}
    order += 1
    properties["autospread"] = {"order": order, "text": "Repartir los personajes automaticamente", "type": "bool", "value": True}
    order += 1
    properties["speed"] = {"order": order, "text": "Velocidad de animacion (%)", "type": "slider",
                           "min": 25, "max": 300, "step": 5, "value": 100}
    order += 1
    properties["reactevery"] = {"order": order, "text": "Reaccion automatica cada (segundos, 0 = no)", "type": "slider",
                                "min": 0, "max": 120, "step": 5, "value": 0}
    order += 1
    properties["bounce"] = {"order": order, "text": "Latido con la musica (%)", "type": "slider",
                            "min": 0, "max": 30, "step": 1, "value": 0}
    order += 1
    properties["bgimage"] = {"order": order, "text": "Usar la imagen de fondo (la del sistema)", "type": "bool", "value": True}
    order += 1
    properties["bgcolor"] = {"order": order, "text": "Color de fondo", "type": "color", "value": "0.047 0.063 0.086"}
    return properties


def make_preview(path):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    image = Image.new("RGB", (512, 512), (12, 16, 22))
    draw = ImageDraw.Draw(image)
    for i in range(4):
        x = 90 + i * 110
        draw.rounded_rectangle((x - 40, 140, x + 40, 440), 30, outline=(90, 220, 170), width=4)
    draw.text((150, 60), "NIKKE STAGE", fill=(230, 240, 235))
    image.save(path)
    return True


BACKGROUND_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
MAX_BACKGROUND_BYTES = 40 * 1024 * 1024


def detect_system_wallpaper():
    """Ruta del fondo de escritorio actual (KDE Plasma) o None. Lee la configuracion de Plasma, que
    guarda la imagen de cada escritorio en `Image=`; se usa la ultima que exista."""
    config_file = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                               "plasma-org.kde.plasma.desktop-appletsrc")
    try:
        with open(config_file, encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    found = None
    in_wallpaper = False
    for line in lines:
        if line.startswith("["):
            in_wallpaper = "[Wallpaper][org.kde.image]" in line
        elif in_wallpaper and line.startswith("Image="):
            value = line[len("Image="):].strip()
            if value.startswith("file://"):
                value = urllib.request.url2pathname(value[len("file://"):])
            if os.path.isfile(value) and os.path.splitext(value)[1].lower() in BACKGROUND_EXTENSIONS:
                found = value
    return found


def set_background(path):
    """Copia `path` como fondo de Nikke Stage (files/stage/background.<ext>) y lo anota en el manifiesto."""
    path = os.path.expanduser(path)
    extension = os.path.splitext(path)[1].lower()
    if not os.path.isfile(path) or extension not in BACKGROUND_EXTENSIONS:
        raise PackError(f"Necesito una imagen existente ({', '.join(sorted(BACKGROUND_EXTENSIONS))}).")
    if os.path.getsize(path) > MAX_BACKGROUND_BYTES:
        raise PackError("La imagen pesa demasiado (maximo 40 MB).")
    os.makedirs(config_files(), exist_ok=True)
    manifest = read_manifest()
    old = manifest.get("background")
    name = f"background{extension}"
    shutil.copyfile(path, os.path.join(config_files(), name))
    if old and old != name:
        try:
            os.remove(os.path.join(config_files(), old))
        except OSError:
            pass
    manifest["background"] = name
    write_manifest(manifest)
    return name


def clear_background():
    manifest = read_manifest()
    old = manifest.pop("background", None)
    manifest["background_disabled"] = True
    if old:
        try:
            os.remove(os.path.join(config_files(), old))
        except OSError:
            pass
    write_manifest(manifest)


def ensure_default_background():
    """Primera instalacion: usa el fondo del sistema como fondo base, salvo que el usuario ya haya
    elegido uno (o lo haya quitado a proposito)."""
    manifest = read_manifest()
    if manifest.get("background") or manifest.get("background_disabled"):
        return manifest.get("background")
    system = detect_system_wallpaper()
    if system:
        try:
            return set_background(system)
        except PackError:
            return None
    return None


def install_wallpaper():
    ensure_default_background()
    workshop = workshop_dir()
    runtime = find_runtime_dir(workshop)
    target = os.path.join(workshop, WALLPAPER_ID)
    os.makedirs(target, exist_ok=True)
    for name in ("index.html", "stage.js", "style.css"):
        shutil.copyfile(os.path.join(SOURCE_DIR, name), os.path.join(target, name))
    for name in RUNTIME_FILES:
        shutil.copyfile(os.path.join(runtime, name), os.path.join(target, name))
    manifest = read_manifest()
    project = {
        "title": "Nikke Stage",
        "workshopid": WALLPAPER_ID,
        "type": "web",
        "file": "index.html",
        "tags": ["Anime"],
        "contentrating": "Everyone",
        "description": "Hasta 4 personajes de Nikke a la vez, a tu eleccion. Wallpaper propio (Elegir Fondo).",
        "general": {"properties": build_properties(manifest), "supportsaudioprocessing": True},
    }
    if make_preview(os.path.join(target, "preview.png")):
        project["preview"] = "preview.png"
    with open(os.path.join(target, "project.json"), "w", encoding="utf-8") as f:
        json.dump(project, f, indent=2, ensure_ascii=False)
    return target


def normalize_code(text):
    """Acepta variantes habituales de un codigo ('C080_1', 'c80', ' c010 ') y devuelve el canonico
    ('c080_01', 'c080', 'c010'), o None si no parece un codigo."""
    match = re.fullmatch(r"c(\d{1,4})(?:_(\d{1,2}))?", text.strip().lower())
    if not match:
        return None
    number = match.group(1).zfill(3)
    return f"c{number}" + (f"_{match.group(2).zfill(2)}" if match.group(2) else "")


def resolve(query, index):
    """Convierte un nombre ('Makima') en codigo ('c800'); los codigos (incluso mal escritos, como
    'c080_1') se normalizan."""
    code = normalize_code(query)
    if code and l2d_pack.CODE_RE.match(code):
        return code
    if l2d_pack.CODE_RE.match(query):
        return query
    needle = query.strip().lower()
    exact = [i for i, e in index.items() if str(e.get("name", "")).lower() == needle and l2d_pack.CODE_RE.match(str(i))]
    if len(exact) == 1:
        return exact[0]
    partial = [i for i, e in index.items() if needle in str(e.get("name", "")).lower() and l2d_pack.CODE_RE.match(str(i))]
    if len(partial) == 1:
        return partial[0]
    if not partial and not exact:
        raise PackError(f"No encuentro ningun personaje que se llame {query!r}. Prueba 'search {query}'.")
    options = ", ".join(f"{i} ({index[i].get('name')})" for i in (exact or partial)[:12])
    raise PackError(f"{query!r} es ambiguo: {options}. Usa el codigo.")


def search(query, index=None):
    """[(codigo, nombre)] de los personajes del catalogo cuyo nombre contiene `query`."""
    index = l2d_index() if index is None else index
    needle = query.strip().lower()
    return [(i, e.get("name", "")) for i, e in sorted(index.items(), key=lambda kv: str(kv[0]))
            if l2d_pack.CODE_RE.match(str(i)) and needle in str(e.get("name", "")).lower()]


PACKS_API = "https://api.github.com/repos/I6RaVeN9I/nikke-wallpaper-packs/releases/tags/v1.0"


def available_packs():
    """Codigos con pack descargable en la release del repositorio de packs (o None si no se puede saber).
    Se guarda en cache por si GitHub no responde."""
    cache = os.path.join(config_files(), "packs_available.json")
    try:
        with urllib.request.urlopen(PACKS_API, timeout=20) as resp:
            data = json.loads(resp.read(10 * 1024 * 1024))
        names = sorted(a["name"][:-4] for a in data.get("assets", []) if str(a.get("name", "")).endswith(".zip"))
        os.makedirs(config_files(), exist_ok=True)
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(names, f)
        return set(names)
    except (OSError, ValueError, KeyError, TypeError):
        try:
            with open(cache, encoding="utf-8") as f:
                return set(json.load(f))
        except (OSError, ValueError):
            return None


def catalog(index=None, packs=None):
    """Catalogo [(codigo, nombre, instalado, disponible)]: los personajes de Nikke-db mas los packs que solo
    existen en el repositorio (sin nombre). `disponible` es False si no hay pack gratuito (None = se desconoce)."""
    index = l2d_index() if index is None else index
    packs = available_packs() if packs is None else packs
    installed = read_manifest()["characters"]
    rows = {}
    for code, entry in index.items():
        if l2d_pack.CODE_RE.match(str(code)):
            rows[code] = (code, entry.get("name", code), code in installed, None if packs is None else code in packs)
    for code in sorted(packs or ()):
        if code not in rows and l2d_pack.CODE_RE.match(code):
            rows[code] = (code, code, code in installed, True)
    return [rows[c] for c in sorted(rows)]


def add(codes, progress=None):
    """Descarga e instala personajes. `progress(mensaje)` recibe el avance (para consola o GUI)."""
    report = progress or (lambda message: None)
    index = l2d_index()
    manifest = read_manifest()
    codes = [resolve(c, index) for c in codes]
    for code in codes:
        report(f"Descargando {code}...")
        try:
            data = l2d_pack.download(code)
        except PackError as error:
            if "404" in str(error):
                raise PackError(f"{code} no tiene pack gratuito en nikke-wallpaper-packs, asi que no se puede descargar.") from error
            raise
        dest = os.path.join(config_files(), "characters")
        os.makedirs(dest, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="nikke-stage-") as tmp:
            files = l2d_pack.extract_safely(data, code, tmp)
            final = os.path.join(dest, code)
            if os.path.isdir(final):
                shutil.rmtree(final)
            shutil.copytree(os.path.join(tmp, code), final)
        info = index.get(code, {})
        manifest["characters"][code] = {"name": info.get("name", code), "version": skeleton_version(code)}
        report(f"{code} ({manifest['characters'][code]['name']}): {files} archivos")
        write_manifest(manifest)
    return install_wallpaper()


def remove(codes):
    manifest = read_manifest()
    for code in codes:
        if code in manifest["characters"]:
            del manifest["characters"][code]
        shutil.rmtree(os.path.join(config_files(), "characters", code), ignore_errors=True)
    write_manifest(manifest)
    return install_wallpaper()
