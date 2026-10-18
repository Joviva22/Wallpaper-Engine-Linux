"""Clasificacion de wallpapers a partir de su project.json: tipo, clasificacion de
contenido (rating) y etiquetas, normalizados y con respaldo cuando faltan datos.

project.json es heterogeneo en la practica: mayusculas inconsistentes, campos de
tipo incorrecto, "presets" que no traen tipo/etiquetas porque heredan de otro
wallpaper (campo `dependency`), y proyectos sin `contentrating` pero con
`ratingsex`/`ratingviolence`. Todo eso se resuelve aqui, sin tocar disco, para que
sea facil de probar."""
import os
import re

UNKNOWN = "Desconocido"
RATINGS = ("Everyone", "Questionable", "Mature")
_RATING_BY_LOWER = {r.lower(): r for r in RATINGS}

# Etiquetas oficiales del Workshop de Wallpaper Engine (con su capitalizacion).
KNOWN_TAGS = [
    "Abstract", "Animal", "Anime", "CGI", "Cartoon", "Cyberpunk", "Fantasy", "Game",
    "Landscape", "Memes", "Music", "Nature", "Pixel art", "Relaxing", "Retro",
    "Sci-Fi", "Sports", "Technology", "Television", "Unspecified", "Vehicle",
]
_TAG_BY_LOWER = {t.lower(): t for t in KNOWN_TAGS}

_VIDEO_EXT = {".mp4", ".webm", ".mkv", ".avi", ".mov", ".m4v", ".wmv", ".gif"}
_WEB_EXT = {".html", ".htm"}
_MAX_DEPTH = 3


def normalize_type(raw):
    """'scene'/'Scene'/' SCENE ' -> 'Scene'. Vacio o no-texto -> ''."""
    if isinstance(raw, str) and raw.strip():
        return raw.strip().capitalize()
    return ""


def infer_type(data, filenames):
    """Tipo deducido del archivo principal o del contenido de la carpeta, para
    proyectos que no declaran `type`. '' si no se puede saber."""
    main = data.get("file")
    if isinstance(main, str):
        ext = os.path.splitext(main.lower())[1]
        if ext in _WEB_EXT:
            return "Web"
        if ext in _VIDEO_EXT:
            return "Video"
        if ext in (".json", ".pkg"):
            return "Scene"
    names = {n.lower() for n in filenames}
    if "scene.pkg" in names:
        return "Scene"
    if "index.html" in names:
        return "Web"
    if any(os.path.splitext(n)[1] in _VIDEO_EXT for n in names):
        return "Video"
    return ""


def normalize_rating(raw):
    """Devuelve la clasificacion canonica o '' si no es una de las tres."""
    if isinstance(raw, str):
        return _RATING_BY_LOWER.get(raw.strip().lower(), "")
    return ""


def infer_rating(data):
    """Clasificacion deducida de ratingsex/ratingviolence cuando falta contentrating."""
    sex = str(data.get("ratingsex", "")).strip().lower()
    violence = str(data.get("ratingviolence", "")).strip().lower()
    if sex in ("adult", "full"):
        return "Mature"
    if sex == "mild" or violence in ("included", "mild", "full"):
        return "Questionable"
    if sex == "none" or violence == "none":
        return "Everyone"
    return ""


def normalize_tags(raw):
    """Lista de etiquetas sin vacias, sin duplicados (ignorando mayusculas) y con la
    capitalizacion oficial del Workshop cuando se conoce. Acepta str o lista."""
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    seen = set()
    out = []
    for tag in raw:
        if not isinstance(tag, str):
            continue
        tag = tag.strip()
        key = tag.lower()
        if not tag or key in seen:
            continue
        seen.add(key)
        out.append(_TAG_BY_LOWER.get(key, tag))
    return out


def _dependency_id(data):
    dep = data.get("dependency")
    if isinstance(dep, int) and not isinstance(dep, bool):
        dep = str(dep)
    if isinstance(dep, str) and re.fullmatch(r"\d+", dep.strip()):
        return dep.strip()
    return ""


def classify_project(entry, data, filenames=(), resolve=None, _depth=0):
    """Clasifica un proyecto. `entry` es el id (nombre de carpeta), `data` el
    project.json ya cargado, `filenames` los archivos de su carpeta y `resolve(dep_id)`
    devuelve (data, filenames) del proyecto del que depende o None.

    Devuelve {title, preview, type, rating, tags, preset, dependency}."""
    if not isinstance(data, dict):
        data = {}
    title = data.get("title")
    title = title.strip() if isinstance(title, str) and title.strip() else entry
    preview = data.get("preview")
    preview = preview if isinstance(preview, str) else ""

    wtype = normalize_type(data.get("type"))
    rating = normalize_rating(data.get("contentrating"))
    tags = normalize_tags(data.get("tags"))
    dependency = _dependency_id(data)
    preset = bool(dependency and (isinstance(data.get("preset"), dict) or not wtype))

    parent = None
    if dependency and resolve and _depth < _MAX_DEPTH and dependency != entry:
        resolved = resolve(dependency)
        if resolved:
            parent = classify_project(dependency, resolved[0], resolved[1], resolve, _depth + 1)

    if not wtype:
        wtype = (parent or {}).get("type") or infer_type(data, filenames)
    if not rating:
        rating = infer_rating(data) or (parent or {}).get("rating") or ""
    if not tags and parent:
        tags = list(parent["tags"])

    return {
        "title": title, "preview": preview, "type": wtype or UNKNOWN,
        "rating": rating or UNKNOWN, "tags": tags,
        "preset": preset, "dependency": dependency,
    }
