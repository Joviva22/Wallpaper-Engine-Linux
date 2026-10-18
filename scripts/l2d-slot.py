#!/usr/bin/env python3
"""Cambia el personaje de las ranuras del wallpaper "Ultimate L2D Player - Demo".

La demo admite dos ranuras (image/slot_1 e image/slot_2) con UN personaje cada una.
Este script descarga el pack gratuito de un personaje (de los lanzamientos de
github.com/I6RaVeN9I/nikke-wallpaper-packs), lo valida, lo extrae y lo deja en la ranura
elegida sustituyendo el que hubiera. No modifica el codigo del wallpaper.

Uso:
    scripts/l2d-slot.py --slot 1 c010        # instala Rapi en la ranura 1
    scripts/l2d-slot.py --list               # muestra lo que hay en cada ranura
    scripts/l2d-slot.py --clear 2            # vacia la ranura 2

Los codigos (c010, c195_01...) son los de Nikke-db: https://nikke-db.pages.dev
Los modelos son contenido de fans con activos de SHIFT UP Corp.
"""
import argparse
import io
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

WALLPAPER_ID = "3792173227"
RELEASE_URL = "https://github.com/I6RaVeN9I/nikke-wallpaper-packs/releases/download/v1.0/{code}.zip"
CODE_RE = re.compile(r"^c\d{3,4}(_\d{2})?$")
ALLOWED_EXTENSIONS = {".atlas", ".png", ".skel", ".json"}
MAX_ZIP_BYTES = 60 * 1024 * 1024
MAX_UNPACKED_BYTES = 120 * 1024 * 1024


def find_wallpaper_dir(override=None):
    if override:
        return override
    candidates = []
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from wpelib import config
        candidates.append(config.WORKSHOP_DIR)
    except Exception:
        pass
    home = os.path.expanduser("~")
    candidates += [
        os.path.join(home, ".local/share/Steam/steamapps/workshop/content/431960"),
        os.path.join(home, ".steam/steam/steamapps/workshop/content/431960"),
    ]
    for base in candidates:
        path = os.path.join(base, WALLPAPER_ID)
        if os.path.isdir(path):
            return path
    sys.exit(f"No encuentro el wallpaper {WALLPAPER_ID}. Suscribete a el en el Workshop o usa --wallpaper-dir.")


def slot_dir(wallpaper, slot):
    # En Linux importa la mayuscula: el wallpaper pide `slot_N` en minuscula, aunque el paquete
    # trae `Slot_1` (hecho en Windows).
    return os.path.join(wallpaper, "image", f"slot_{slot}")


def characters_in(path):
    if not os.path.isdir(path):
        return []
    return sorted(n for n in os.listdir(path)
                  if CODE_RE.match(n) and os.path.isdir(os.path.join(path, n)))


def download(code):
    url = RELEASE_URL.format(code=code)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read(MAX_ZIP_BYTES + 1)
    except urllib.error.HTTPError as e:
        sys.exit(f"No existe el pack {code} ({e.code}). Comprueba el codigo en Nikke-db.")
    except OSError as e:
        sys.exit(f"No se pudo descargar {url}: {e}")
    if len(data) > MAX_ZIP_BYTES:
        sys.exit(f"{code}.zip supera {MAX_ZIP_BYTES // 1048576} MB: no es un pack de personaje normal.")
    return data


def extract_safely(data, code, dest):
    """Extrae solo archivos del pack (atlas/png/skel/json) dentro de `dest`/code, con rutas
    normalizadas (los zips traen barras de Windows) y sin salirse de la carpeta."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        sys.exit("El archivo descargado no es un zip valido.")
    total = 0
    files = 0
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        if info.is_dir():
            continue
        parts = name.split("/")
        if name.startswith("/") or ".." in parts or parts[0] != code:
            sys.exit(f"El zip contiene una ruta inesperada ({info.filename!r}); no lo instalo.")
        if os.path.splitext(name)[1].lower() not in ALLOWED_EXTENSIONS:
            sys.exit(f"El zip contiene un tipo de archivo inesperado ({info.filename!r}); no lo instalo.")
        total += info.file_size
        if total > MAX_UNPACKED_BYTES:
            sys.exit("El pack descomprimido es demasiado grande; no lo instalo.")
        target = os.path.join(dest, *parts)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with archive.open(info) as src, open(target, "wb") as out:
            shutil.copyfileobj(src, out)
        files += 1
    if not os.path.isfile(os.path.join(dest, code, f"{code}_00.skel")):
        sys.exit(f"El pack no contiene {code}_00.skel; no parece un personaje valido.")
    return files


def install(wallpaper, slot, code):
    data = download(code)
    with tempfile.TemporaryDirectory(prefix="l2d-slot-") as tmp:
        files = extract_safely(data, code, tmp)
        target = slot_dir(wallpaper, slot)
        os.makedirs(target, exist_ok=True)
        # Una sola carpeta de personaje por ranura (con mas, el wallpaper no carga ninguna).
        for old in characters_in(target):
            shutil.rmtree(os.path.join(target, old))
        shutil.copytree(os.path.join(tmp, code), os.path.join(target, code))
    print(f"{code} instalado en la ranura {slot} ({files} archivos): {os.path.join(target, code)}")
    print("Abre los ajustes del wallpaper y elige esa ranura (Slot/Loadout) para verlo.")
    print("Nota: Steam puede borrar estos archivos cuando actualice el wallpaper.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("code", nargs="?", help="codigo del personaje, p.ej. c010")
    parser.add_argument("--slot", type=int, choices=(1, 2), default=1, help="ranura de destino (1 o 2)")
    parser.add_argument("--list", action="store_true", help="muestra el contenido de las ranuras")
    parser.add_argument("--clear", type=int, choices=(1, 2), help="vacia una ranura")
    parser.add_argument("--wallpaper-dir", help="carpeta del wallpaper (por defecto, se detecta)")
    args = parser.parse_args()

    wallpaper = find_wallpaper_dir(args.wallpaper_dir)
    if args.list:
        for slot in (1, 2):
            chars = characters_in(slot_dir(wallpaper, slot))
            print(f"slot_{slot}: {', '.join(chars) if chars else '(vacia)'}")
        return
    if args.clear:
        target = slot_dir(wallpaper, args.clear)
        for old in characters_in(target):
            shutil.rmtree(os.path.join(target, old))
        print(f"Ranura {args.clear} vaciada.")
        return
    if not args.code:
        parser.error("indica un codigo de personaje, --list o --clear")
    if not CODE_RE.match(args.code):
        sys.exit(f"Codigo no valido: {args.code!r} (formato c010 o c010_02).")
    install(wallpaper, args.slot, args.code)


if __name__ == "__main__":
    main()
