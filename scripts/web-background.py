#!/usr/bin/env python3
"""Pone una imagen propia como fondo de un wallpaper web, sin tocar sus archivos.

Escribe una hoja de estilos de usuario en ~/.config/wallpaperengine-picker/web_css/ que el
motor parcheado (patches/0009) inyecta en la pagina al cargarla, y copia la imagen a
web_css/files/ (servida como <wallpaper>/__user/<nombre>). Funciona con los wallpapers web
que dejan ver el fondo de la pagina (p.ej. el reproductor L2D y los Nikke); los que dibujan
su propio fondo opaco encima no se veran afectados.

Uso:
    scripts/web-background.py --id 3792173227 ~/Imagenes/fondo.jpg
    scripts/web-background.py --all ~/Imagenes/fondo.jpg      # todos los wallpapers web
    scripts/web-background.py --id 3792173227 --color '#101820'
    scripts/web-background.py --id 3792173227 --clear
Reaplica el wallpaper para ver el cambio.
"""
import argparse
import os
import re
import shutil
import sys

ALLOWED = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
MAX_BYTES = 40 * 1024 * 1024


def config_dir():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "wallpaperengine-picker", "web_css")


def css_path(target):
    return os.path.join(config_dir(), f"{target}.css")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image", nargs="?", help="imagen de fondo")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="id del wallpaper (carpeta del Workshop)")
    group.add_argument("--all", action="store_true", help="aplicar a todos los wallpapers web")
    parser.add_argument("--color", help="usar un color en vez de una imagen (p.ej. '#101820')")
    parser.add_argument("--clear", action="store_true", help="quitar el fondo personalizado")
    parser.add_argument("--fit", choices=("cover", "contain", "stretch"), default="cover",
                        help="como ajustar la imagen (por defecto cover)")
    args = parser.parse_args()

    target = "all" if args.all else args.id
    if not re.fullmatch(r"all|\d+", target):
        sys.exit("El id debe ser numerico.")
    path = css_path(target)

    if args.clear:
        if os.path.exists(path):
            os.remove(path)
        print(f"Fondo personalizado de {target} eliminado.")
        return

    os.makedirs(os.path.join(config_dir(), "files"), exist_ok=True)
    if args.color:
        if not re.fullmatch(r"#[0-9a-fA-F]{3,8}|[a-zA-Z]{3,20}", args.color):
            sys.exit("Color no valido (usa #rrggbb o un nombre de color).")
        rule = f"background: {args.color} !important;"
    else:
        if not args.image:
            parser.error("indica una imagen, --color o --clear")
        source = os.path.expanduser(args.image)
        ext = os.path.splitext(source)[1].lower()
        if ext not in ALLOWED or not os.path.isfile(source):
            sys.exit(f"Necesito un archivo de imagen existente ({', '.join(sorted(ALLOWED))}).")
        if os.path.getsize(source) > MAX_BYTES:
            sys.exit("La imagen pesa demasiado (maximo 40 MB).")
        name = f"bg_{target}{ext}"
        shutil.copyfile(source, os.path.join(config_dir(), "files", name))
        size = {"cover": "cover", "contain": "contain", "stretch": "100% 100%"}[args.fit]
        rule = f'background: url("__user/{name}") center / {size} no-repeat !important;'

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"/* generado por scripts/web-background.py */\nhtml, body {{ {rule} }}\n")
    print(f"Fondo guardado para {target}: {path}")
    print("Reaplica el wallpaper para verlo (requiere el motor parcheado, patches/0009).")


if __name__ == "__main__":
    main()
