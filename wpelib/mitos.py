"""Instala el wallpaper propio "Mitos en blanco y negro" (Inazuma, Grecia, Grand Blue, mitologia nordica).

Es un wallpaper web sin dependencias: todo el arte se dibuja en codigo (canvas 2D), asi que no hay imagenes
ni personajes con licencia de terceros. Se copia a la carpeta del Workshop como un proyecto mas."""
import json
import os
import shutil

from . import nikke_stage

WALLPAPER_ID = "9100000002"
SOURCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wallpapers", "mitos")
FILES = ("index.html", "mitos.js", "style.css")

SCENE_OPTIONS = [
    {"label": "Cambiar sola", "value": "auto"},
    {"label": "Inazuma (tormenta, torii y petalos)", "value": "inazuma"},
    {"label": "Grecia (templo, sol y laurel)", "value": "grecia"},
    {"label": "Grand Blue (buceo)", "value": "grandblue"},
    {"label": "Mitologia nordica (Yggdrasil y aurora)", "value": "nordica"},
]


def properties():
    items = [
        ("scene", {"text": "Escena", "type": "combo", "value": "auto", "options": SCENE_OPTIONS}),
        ("seconds", {"text": "Segundos por escena (modo automatico)", "type": "slider", "min": 10, "max": 300, "step": 5, "value": 45}),
        ("particles", {"text": "Cantidad de lluvia, petalos, burbujas y nieve (%)", "type": "slider", "min": 0, "max": 100, "step": 5, "value": 100}),
        ("grain", {"text": "Grano de pelicula (%)", "type": "slider", "min": 0, "max": 40, "step": 1, "value": 12}),
        ("contrast", {"text": "Contraste (%)", "type": "slider", "min": 70, "max": 160, "step": 5, "value": 110}),
        ("parallax", {"text": "Movimiento con el raton", "type": "bool", "value": True}),
        ("caption", {"text": "Nombre de la escena", "type": "bool", "value": True}),
        ("fps", {"text": "Fotogramas por segundo", "type": "slider", "min": 15, "max": 60, "step": 5, "value": 30}),
    ]
    return {key: {"order": number, **value} for number, (key, value) in enumerate(items, 1)}


def make_preview(path):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    image = Image.new("L", (512, 512), 12)
    draw = ImageDraw.Draw(image)
    draw.ellipse((330, 60, 450, 180), fill=235)
    draw.polygon([(0, 512), (0, 330), (120, 290), (230, 350), (340, 300), (512, 380), (512, 512)], fill=40)
    draw.rectangle((60, 220, 70, 400), fill=4)
    draw.rectangle((150, 220, 160, 400), fill=4)
    draw.rectangle((50, 215, 170, 230), fill=4)
    image.convert("RGB").save(path)
    return True


def install_wallpaper():
    target = os.path.join(nikke_stage.workshop_dir(), WALLPAPER_ID)
    os.makedirs(target, exist_ok=True)
    for name in FILES:
        shutil.copyfile(os.path.join(SOURCE_DIR, name), os.path.join(target, name))
    project = {
        "title": "Mitos en blanco y negro",
        "workshopid": WALLPAPER_ID,
        "type": "web",
        "file": "index.html",
        "tags": ["Fantasy", "Abstract"],
        "contentrating": "Everyone",
        "description": "Inazuma, mitologia griega, Grand Blue y mitologia nordica en blanco y negro. Wallpaper propio (Elegir Fondo).",
        "general": {"properties": properties()},
    }
    if make_preview(os.path.join(target, "preview.png")):
        project["preview"] = "preview.png"
    with open(os.path.join(target, "project.json"), "w", encoding="utf-8") as f:
        json.dump(project, f, indent=2, ensure_ascii=False)
    return target
