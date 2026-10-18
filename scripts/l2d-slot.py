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
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wpelib import l2d_pack  # noqa: E402
from wpelib.l2d_pack import CODE_RE, PackError  # noqa: E402

WALLPAPER_ID = "3792173227"
def find_wallpaper_dir(override=None):
    if override:
        return override
    candidates = []
    try:
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


def install(wallpaper, slot, code):
    data = l2d_pack.download(code)
    with tempfile.TemporaryDirectory(prefix="l2d-slot-") as tmp:
        files = l2d_pack.extract_safely(data, code, tmp)
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
    try:
        main()
    except PackError as error:
        sys.exit(str(error))
