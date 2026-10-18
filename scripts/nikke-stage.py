#!/usr/bin/env python3
"""Nikke Stage: un wallpaper web propio que muestra hasta 4 personajes de Nikke a la vez,
elegidos entre los que tengas instalados (sin limite de ranuras ni de catalogo).

El wallpaper es codigo de este proyecto (wallpapers/nikke-stage/). Los personajes son los packs
gratuitos de github.com/I6RaVeN9I/nikke-wallpaper-packs (modelos de Nikke-db, activos de SHIFT UP,
contenido de fans para uso personal). Para dibujarlos usa los reproductores Spine que ya traen los
wallpapers de Nikke del Workshop (hay que estar suscrito a alguno); no se copian al repositorio.

Uso:
    scripts/nikke-stage.py add c010 Makima c195   # descarga e instala (por codigo o por nombre)
    scripts/nikke-stage.py search rapi            # busca codigos por nombre
    scripts/nikke-stage.py list                   # personajes instalados
    scripts/nikke-stage.py remove c800
    scripts/nikke-stage.py install                # (re)instala el wallpaper y sus propiedades
    scripts/nikke-stage.py background system      # fondo = el del escritorio (por defecto); o una RUTA; o none
Tambien se gestiona desde Elegir Fondo (Acciones > Nikke Stage: personajes), con buscador y boton
de descarga. Despues aplica "Nikke Stage" y en Personalizar elige el personaje de cada hueco, su
posicion, tamano, altura, espejo y mas. Requiere el motor parcheado (patches/0005 y 0009).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wpelib import nikke_stage, nikke_voices  # noqa: E402
from wpelib.l2d_pack import PackError  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("add", "remove", "list", "install", "search", "background", "voices", "voices-remove"))
    parser.add_argument("codes", nargs="*")
    args = parser.parse_args()
    if args.command == "list":
        for code, entry in sorted(nikke_stage.read_manifest()["characters"].items()):
            print(f"{code}  {entry.get('name', code)}  (Spine {entry.get('version')})")
        return
    if args.command == "background":
        what = args.codes[0] if args.codes else "system"
        if what == "none":
            nikke_stage.clear_background()
            print("Fondo de imagen quitado (se usa el color de fondo).")
        else:
            source = nikke_stage.detect_system_wallpaper() if what == "system" else what
            if not source:
                raise PackError("No pude detectar el fondo del sistema; indica una imagen: background RUTA.")
            print(f"Fondo: {nikke_stage.set_background(source)} (de {source})")
        target = nikke_stage.install_wallpaper()
    elif args.command == "voices":
        # voices CODE [jp|en|cn]: descarga solo las voces de ese personaje (unos MB), no el zip entero
        if not args.codes:
            parser.error("uso: voices CODIGO [jp|en|cn]")
        code = nikke_stage.normalize_code(args.codes[0])
        lang = args.codes[1] if len(args.codes) > 1 else None
        langs = [lang] if lang else nikke_voices.languages_with_voices(code)
        if not langs:
            raise PackError(f"{code} no tiene voces publicadas.")
        for language in langs[:1] if not lang else langs:
            files = nikke_voices.download_voices(code, language, progress=print)
            print(f"{code}: {len(files)} voces ({language}).")
        target = nikke_stage.install_wallpaper()
    elif args.command == "voices-remove":
        for code in args.codes:
            nikke_voices.remove_voices(code)
        target = nikke_stage.install_wallpaper()
    elif args.command == "install":
        target = nikke_stage.install_wallpaper()
    elif not args.codes:
        parser.error("indica al menos un personaje (codigo o nombre)")
    elif args.command == "search":
        found = nikke_stage.search(" ".join(args.codes))
        for code, name in found[:40]:
            print(f"{code}  {name}")
        if not found:
            print("Sin resultados.")
        return
    elif args.command == "add":
        target = nikke_stage.add(args.codes, progress=print)
    else:
        target = nikke_stage.remove(args.codes)
    print(f"Wallpaper instalado en {target}")
    print("Reaplicalo desde Elegir Fondo (Nikke Stage) y usa Personalizar para elegir personajes.")


if __name__ == "__main__":
    try:
        main()
    except PackError as error:
        sys.exit(str(error))
