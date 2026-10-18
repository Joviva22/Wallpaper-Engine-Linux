"""Propiedades personalizables por wallpaper (el equivalente a la pestana
'Customize' de Wallpaper Engine en Windows). linux-wallpaperengine expone
--list-properties para volcar las propiedades de un fondo (tipo, etiqueta,
valor actual, y min/max/step o lista de opciones segun el tipo) y
--set-property clave=valor para sobreescribirlas al lanzarlo."""
import subprocess

from .config import ASSETS_DIR, WORKSHOP_DIR, engine_executable


def list_properties(wid, timeout=8):
    """Ejecuta --list-properties sobre un wallpaper y devuelve una lista de dicts:
    {key, type, label, value, min, max, step, options: [(idx, label), ...]}.
    Los tipos posibles son: boolean, slider, combo, color, textinput.
    Devuelve [] si el wallpaper no existe o el motor no responde (p.ej. si crashea)."""
    folder = f"{WORKSHOP_DIR}/{wid}"
    try:
        result = subprocess.run(
            [engine_executable(), "--assets-dir", ASSETS_DIR, "--bg", folder, "--list-properties"],
            capture_output=True, text=True, timeout=timeout,
        )
    except Exception:
        return []

    lines = result.stdout.splitlines()
    props = []
    current = None
    in_values = False

    for line in lines:
        if line.startswith(("Running with:", "Using wallpaper engine's assets")):
            continue
        if not line.strip():
            in_values = False
            continue

        header = line if line == line.lstrip() else None
        if header and " - " in header:
            if current:
                props.append(current)
            key, _, ptype = header.partition(" - ")
            current = {"key": key.strip(), "type": ptype.strip(), "label": key.strip(),
                       "value": "", "min": None, "max": None, "step": None, "options": []}
            in_values = False
            continue

        if current is None:
            continue

        stripped = line.strip()
        if stripped.startswith("Text:"):
            current["label"] = stripped[len("Text:"):].strip()
        elif stripped.startswith("Value:"):
            current["value"] = stripped[len("Value:"):].strip()
        elif stripped.startswith("Min:"):
            current["min"] = stripped[len("Min:"):].strip()
        elif stripped.startswith("Max:"):
            current["max"] = stripped[len("Max:"):].strip()
        elif stripped.startswith("Step:"):
            current["step"] = stripped[len("Step:"):].strip()
        elif stripped.startswith("Values:"):
            in_values = True
        elif in_values and "=" in stripped:
            idx, _, label = stripped.partition("=")
            current["options"].append((idx.strip(), label.strip()))

    if current:
        props.append(current)

    return props


def list_layer_properties(wid):
    """Detecta que propiedades controlan la VISIBILIDAD de una o mas capas
    concretas de la escena, a diferencia del resto de propiedades (color,
    tamano...) que no fijan ninguna capa. Wallpaper Engine liga la visibilidad
    de un objeto a una propiedad personalizable de dos formas distintas:

    1. "visible": {"user": "clave", "value": true|false} — un interruptor on/off
       normal (propiedad tipo boolean). Visto en el "xray" de Eclipse
       (front_sync_1/front_sync_2) y en variantes dia/noche.
    2. "visible": {"user": {"condition": "N", "name": "clave"}, "value": bool} —
       la capa solo se muestra cuando una propiedad tipo COMBO vale exactamente
       la opcion N. Varias capas distintas pueden compartir la misma propiedad
       combo, cada una ligada a una opcion diferente (p.ej. nieve/cerezo/lluvia
       seleccionadas por un unico combo de "estacion").

    Devuelve una lista de dicts. Los del tipo 1: {"kind": "toggle", "key",
    "label", "value", "layer_names"}. Los del tipo 2 se agrupan por combo:
    {"kind": "combo", "key", "label", "current_value",
     "options": [{"condition", "option_label", "layer_names"}, ...]}."""
    import json
    import os

    from .repair import _unpack

    pkg_path = os.path.join(WORKSHOP_DIR, wid, "scene.pkg")
    if not os.path.isfile(pkg_path):
        return []
    try:
        _, _, raw_by_name = _unpack(pkg_path)
        scene = json.loads(raw_by_name["scene.json"].decode("utf-8"))
    except Exception:
        return []

    toggle_keys = {}
    combo_conditions = {}  # propkey -> { condition: [layer_names] }
    for obj in scene.get("objects", []):
        vis = obj.get("visible")
        if not isinstance(vis, dict) or "user" not in vis:
            continue
        name = obj.get("name") or f"id {obj.get('id')}"
        user = vis["user"]
        if isinstance(user, str):
            toggle_keys.setdefault(user, []).append(name)
        elif isinstance(user, dict) and "name" in user and "condition" in user:
            key = user["name"]
            condition = str(user["condition"])
            combo_conditions.setdefault(key, {}).setdefault(condition, []).append(name)

    if not toggle_keys and not combo_conditions:
        return []

    props_by_key = {p["key"]: p for p in list_properties(wid)}
    result = []

    for key, names in toggle_keys.items():
        prop = props_by_key.get(key)
        if not prop or prop["type"] != "boolean":
            continue  # solo tiene sentido "fijar" capas ligadas a un interruptor on/off
        result.append({"kind": "toggle", "key": key, "label": prop["label"],
                        "value": prop["value"], "layer_names": names})

    for key, conditions in combo_conditions.items():
        prop = props_by_key.get(key)
        if not prop or prop["type"] != "combo":
            continue
        option_labels = dict(prop["options"])  # idx -> label del combo
        options = []
        for condition, names in conditions.items():
            options.append({
                "condition": condition,
                "option_label": option_labels.get(condition, condition),
                "layer_names": names,
            })
        options.sort(key=lambda o: o["condition"])
        result.append({"kind": "combo", "key": key, "label": prop["label"],
                        "current_value": prop["value"], "options": options})

    return result


def build_property_args(wid, overrides):
    """Convierte { propkey: valor } (guardado en properties.json) en una lista
    plana ['--set-property', 'clave=valor', ...] para linux-wallpaperengine."""
    args = []
    for key, value in overrides.get(wid, {}).items():
        args.append("--set-property")
        args.append(f"{key}={value}")
    return args
