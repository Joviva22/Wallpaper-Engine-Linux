"""Voces de los personajes de Nikke Stage.

Los packs de voces (nikke-wallpaper-packs, release "Audio") son tres zips enormes (jp 418 MB, en 1,7 GB,
cn 63 MB) con una carpeta por personaje. En vez de bajarlos enteros, se lee su directorio central con
peticiones HTTP por rango y solo se descargan los archivos del personaje elegido (unos 5-15 MB). Cada
archivo se valida (nombre, tamano) y se guarda en files/stage/voices/<idioma>/<codigo>/."""
import json
import os
import re
import struct
import time
import urllib.request
import zlib

from . import nikke_stage
from .l2d_pack import PackError

URL = "https://github.com/I6RaVeN9I/nikke-wallpaper-packs/releases/download/Audio/{lang}.zip"
LANGUAGES = ("jp", "en", "cn")
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+\.(wav|ogg)$")
MAX_FILE_BYTES = 40 * 1024 * 1024
MAX_CHARACTER_BYTES = 150 * 1024 * 1024
INDEX_MAX_AGE = 7 * 24 * 3600


def _range(url, start, end, timeout=60):
    request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.read(), resp.headers.get("Content-Range", "")
    except OSError as error:
        raise PackError(f"No se pudo leer {url}: {error}") from error


def _voices_dir():
    return os.path.join(nikke_stage.config_files(), "voices")


def _index_path(lang):
    return os.path.join(_voices_dir(), f"index_{lang}.json")


def read_central_directory(lang):
    """[(nombre, metodo, comprimido, tamano, offset)] de los archivos del zip de voces de `lang`."""
    if lang not in LANGUAGES:
        raise PackError(f"Idioma no valido: {lang!r} (usa {', '.join(LANGUAGES)}).")
    cache = _index_path(lang)
    try:
        if time.time() - os.path.getmtime(cache) < INDEX_MAX_AGE:
            with open(cache, encoding="utf-8") as f:
                return [tuple(e) for e in json.load(f)]
    except (OSError, ValueError):
        pass
    url = URL.format(lang=lang)
    _, content_range = _range(url, 0, 0)
    try:
        total = int(content_range.split("/")[1])
    except (IndexError, ValueError) as error:
        raise PackError("El servidor no admite lecturas parciales del zip de voces.") from error
    tail, _ = _range(url, max(0, total - 70000), total - 1)
    eocd = tail.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise PackError("No se encontro el directorio del zip de voces.")
    cd_size, cd_offset = struct.unpack("<II", tail[eocd + 12:eocd + 20])
    directory, _ = _range(url, cd_offset, cd_offset + cd_size - 1, timeout=120)
    entries, pos = [], 0
    while pos + 46 <= len(directory) and directory[pos:pos + 4] == b"PK\x01\x02":
        method = struct.unpack("<H", directory[pos + 10:pos + 12])[0]
        compressed, size = struct.unpack("<II", directory[pos + 20:pos + 28])
        name_len, extra_len, comment_len = struct.unpack("<HHH", directory[pos + 28:pos + 34])
        offset = struct.unpack("<I", directory[pos + 42:pos + 46])[0]
        name = directory[pos + 46:pos + 46 + name_len].decode("utf-8", errors="replace").replace("\\", "/")
        entries.append((name, method, compressed, size, offset))
        pos += 46 + name_len + extra_len + comment_len
    os.makedirs(_voices_dir(), exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(entries, f)
    return entries


def files_for(lang, code, entries=None):
    entries = read_central_directory(lang) if entries is None else entries
    prefix = f"{lang}/{code}/"
    return [e for e in entries if e[0].startswith(prefix) and NAME_RE.match(e[0][len(prefix):])]


def languages_with_voices(code):
    """Idiomas en los que `code` tiene voces. Sin red, lista vacia."""
    found = []
    for lang in LANGUAGES:
        try:
            if files_for(lang, code):
                found.append(lang)
        except PackError:
            continue
    return found


def _fetch_entry(lang, entry):
    name, method, compressed, size, offset = entry
    if size > MAX_FILE_BYTES or compressed > MAX_FILE_BYTES:
        raise PackError(f"{name} es demasiado grande.")
    url = URL.format(lang=lang)
    header, _ = _range(url, offset, offset + 29)
    if header[:4] != b"PK\x03\x04":
        raise PackError(f"Cabecera inesperada en {name}.")
    name_len, extra_len = struct.unpack("<HH", header[26:30])
    data, _ = _range(url, offset + 30 + name_len + extra_len, offset + 30 + name_len + extra_len + compressed - 1, timeout=120)
    if method == 8:
        data = zlib.decompressobj(-15).decompress(data, MAX_FILE_BYTES + 1)
    elif method != 0:
        raise PackError(f"Metodo de compresion no soportado en {name}.")
    if len(data) > MAX_FILE_BYTES:
        raise PackError(f"{name} es demasiado grande.")
    return data


def download_voices(code, lang, progress=None):
    """Descarga las voces de `code` en `lang`; devuelve la lista de archivos."""
    if not nikke_stage.l2d_pack.CODE_RE.match(code):
        raise PackError(f"Codigo no valido: {code!r}.")
    report = progress or (lambda message: None)
    entries = files_for(lang, code)
    if not entries:
        raise PackError(f"{code} no tiene voces en {lang}.")
    if sum(e[3] for e in entries) > MAX_CHARACTER_BYTES:
        raise PackError(f"Las voces de {code} superan {MAX_CHARACTER_BYTES // 1048576} MB.")
    folder = os.path.join(_voices_dir(), lang, code)
    os.makedirs(folder, exist_ok=True)
    saved = []
    for number, entry in enumerate(entries, 1):
        filename = entry[0].rsplit("/", 1)[-1]
        report(f"Voces {code} ({lang}): {number}/{len(entries)}")
        data = _fetch_entry(lang, entry)
        target = os.path.join(folder, filename)
        with open(target + ".part", "wb") as f:
            f.write(data)
        os.replace(target + ".part", target)
        saved.append(filename)
    manifest = nikke_stage.read_manifest()
    manifest.setdefault("voices", {}).setdefault(lang, {})[code] = sorted(saved)
    nikke_stage.write_manifest(manifest)
    return saved


def remove_voices(code, lang=None):
    import shutil
    manifest = nikke_stage.read_manifest()
    for language in ([lang] if lang else list(manifest.get("voices", {}))):
        shutil.rmtree(os.path.join(_voices_dir(), language, code), ignore_errors=True)
        manifest.get("voices", {}).get(language, {}).pop(code, None)
    nikke_stage.write_manifest(manifest)
