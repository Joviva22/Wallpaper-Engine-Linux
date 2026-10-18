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
Despues, en Elegir Fondo, aplica "Nikke Stage" y en Personalizar elige el personaje de cada
hueco, su posicion, tamano, altura, espejo y cuanto laten con la musica. Requiere el motor parcheado (patches/0005 y 0009).
"""
import argparse
import importlib.util
import json
import os
import shutil
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(REPO, "wallpapers", "nikke-stage")
WALLPAPER_ID = "9100000001"
L2D_INDEX_URL = "https://raw.githubusercontent.com/Nikke-db/Nikke-db.github.io/main/js/json/l2d.json"
SLOTS = 4
RUNTIME_FILES = ("spine-player.js", "spine-player4.1.js", "spine-player.css")
DEFAULT_X = {1: 50, 2: 25, 3: 75, 4: 10}


def _load_slot_module():
    spec = importlib.util.spec_from_file_location("l2d_slot", os.path.join(REPO, "scripts", "l2d-slot.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


slotlib = _load_slot_module()


def config_files():
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "wallpaperengine-picker", "web_css", "files", "stage")


def workshop_dir():
    try:
        sys.path.insert(0, REPO)
        from wpelib import config
        if os.path.isdir(config.WORKSHOP_DIR):
            return config.WORKSHOP_DIR
    except Exception:
        pass
    for path in ("~/.local/share/Steam/steamapps/workshop/content/431960",
                 "~/.steam/steam/steamapps/workshop/content/431960"):
        full = os.path.expanduser(path)
        if os.path.isdir(full):
            return full
    sys.exit("No encuentro la carpeta del Workshop de Wallpaper Engine (431960).")


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
    import re
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
    sys.exit("Necesito los reproductores Spine de un wallpaper de Nikke del Workshop (spine-player.js y "
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
    properties["bounce"] = {"order": order, "text": "Latido con la musica (%)", "type": "slider",
                            "min": 0, "max": 30, "step": 1, "value": 0}
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


def install_wallpaper():
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
    print(f"Wallpaper instalado en {target}")
    print("Reaplicalo desde Elegir Fondo (Nikke Stage) y usa Personalizar para elegir personajes.")


def resolve(query, index):
    """Convierte un nombre ('Makima') en codigo ('c800'); los codigos validos pasan tal cual."""
    if slotlib.CODE_RE.match(query):
        return query
    needle = query.strip().lower()
    exact = [i for i, e in index.items() if str(e.get("name", "")).lower() == needle and slotlib.CODE_RE.match(str(i))]
    if len(exact) == 1:
        return exact[0]
    partial = [i for i, e in index.items() if needle in str(e.get("name", "")).lower() and slotlib.CODE_RE.match(str(i))]
    if len(partial) == 1:
        return partial[0]
    if not partial and not exact:
        sys.exit(f"No encuentro ningun personaje que se llame {query!r}. Prueba 'search {query}'.")
    options = ", ".join(f"{i} ({index[i].get('name')})" for i in (exact or partial)[:12])
    sys.exit(f"{query!r} es ambiguo: {options}. Usa el codigo.")


def search(query):
    index = l2d_index()
    needle = query.strip().lower()
    found = [(i, e.get("name", "")) for i, e in sorted(index.items(), key=lambda kv: str(kv[0]))
             if slotlib.CODE_RE.match(str(i)) and needle in str(e.get("name", "")).lower()]
    for code, name in found[:40]:
        print(f"{code}  {name}")
    if not found:
        print("Sin resultados.")


def add(codes):
    index = l2d_index()
    manifest = read_manifest()
    codes = [resolve(c, index) for c in codes]
    for code in codes:
        data = slotlib.download(code)
        dest = os.path.join(config_files(), "characters")
        os.makedirs(dest, exist_ok=True)
        import tempfile
        with tempfile.TemporaryDirectory(prefix="nikke-stage-") as tmp:
            files = slotlib.extract_safely(data, code, tmp)
            final = os.path.join(dest, code)
            if os.path.isdir(final):
                shutil.rmtree(final)
            shutil.copytree(os.path.join(tmp, code), final)
        info = index.get(code, {})
        manifest["characters"][code] = {"name": info.get("name", code), "version": skeleton_version(code)}
        print(f"{code} ({manifest['characters'][code]['name']}): {files} archivos")
    write_manifest(manifest)
    install_wallpaper()


def remove(codes):
    manifest = read_manifest()
    for code in codes:
        if code in manifest["characters"]:
            del manifest["characters"][code]
        shutil.rmtree(os.path.join(config_files(), "characters", code), ignore_errors=True)
    write_manifest(manifest)
    install_wallpaper()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("add", "remove", "list", "install", "search"))
    parser.add_argument("codes", nargs="*")
    args = parser.parse_args()
    if args.command == "list":
        for code, entry in sorted(read_manifest()["characters"].items()):
            print(f"{code}  {entry.get('name', code)}  (Spine {entry.get('version')})")
    elif args.command == "install":
        install_wallpaper()
    elif not args.codes:
        parser.error("indica al menos un personaje (codigo o nombre)")
    elif args.command == "search":
        search(" ".join(args.codes))
    elif args.command == "add":
        add(args.codes)
    else:
        remove(args.codes)


if __name__ == "__main__":
    main()
