"""Descarga y validacion de los packs gratuitos de personajes de Nikke
(github.com/I6RaVeN9I/nikke-wallpaper-packs, modelos de Nikke-db, contenido de fans con
activos de SHIFT UP). Compartido por scripts/l2d-slot.py, scripts/nikke-stage.py y la ventana
de personajes de Nikke Stage."""
import io
import os
import re
import shutil
import urllib.error
import urllib.request
import zipfile

class PackError(Exception):
    """Error legible para el usuario al descargar o validar un pack."""


RELEASE_URL = "https://github.com/I6RaVeN9I/nikke-wallpaper-packs/releases/download/v1.0/{code}.zip"
CODE_RE = re.compile(r"^c\d{3,4}(_\d{2})?$")
ALLOWED_EXTENSIONS = {".atlas", ".png", ".skel", ".json"}
MAX_ZIP_BYTES = 60 * 1024 * 1024
MAX_UNPACKED_BYTES = 120 * 1024 * 1024


def download(code):
    url = RELEASE_URL.format(code=code)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read(MAX_ZIP_BYTES + 1)
    except urllib.error.HTTPError as e:
        raise PackError(f"No existe el pack {code} ({e.code}). Comprueba el codigo en Nikke-db.")
    except OSError as e:
        raise PackError(f"No se pudo descargar {url}: {e}")
    if len(data) > MAX_ZIP_BYTES:
        raise PackError(f"{code}.zip supera {MAX_ZIP_BYTES // 1048576} MB: no es un pack de personaje normal.")
    return data


def extract_safely(data, code, dest):
    """Extrae solo archivos del pack (atlas/png/skel/json) dentro de `dest`/code, con rutas
    normalizadas (los zips traen barras de Windows) y sin salirse de la carpeta."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise PackError("El archivo descargado no es un zip valido.")
    total = 0
    files = 0
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        if info.is_dir():
            continue
        parts = name.split("/")
        if name.startswith("/") or ".." in parts or parts[0] != code:
            raise PackError(f"El zip contiene una ruta inesperada ({info.filename!r}); no lo instalo.")
        if os.path.splitext(name)[1].lower() not in ALLOWED_EXTENSIONS:
            raise PackError(f"El zip contiene un tipo de archivo inesperado ({info.filename!r}); no lo instalo.")
        total += info.file_size
        if total > MAX_UNPACKED_BYTES:
            raise PackError("El pack descomprimido es demasiado grande; no lo instalo.")
        target = os.path.join(dest, *parts)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with archive.open(info) as src, open(target, "wb") as out:
            shutil.copyfileobj(src, out)
        files += 1
    if not os.path.isfile(os.path.join(dest, code, f"{code}_00.skel")):
        raise PackError(f"El pack no contiene {code}_00.skel; no parece un personaje valido.")
    return files
