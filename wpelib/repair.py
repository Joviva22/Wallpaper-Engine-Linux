"""Reparacion de wallpapers que hacen crashear linux-wallpaperengine por
incompatibilidades conocidas del formato .pkg (ver known_bad.json).

El formato .pkg de Wallpaper Engine es:
  [4 bytes LE: longitud de cabecera]["PKGV"+version, esa longitud]
  [4 bytes LE: numero de entradas]
  Por entrada: [4 bytes LE longitud nombre][nombre utf-8][4 bytes LE offset][4 bytes LE longitud]
  (justo despues de la tabla de entradas empieza el bloque de datos; cada entrada
  vive en data_blob_start + offset, length bytes)

Bug confirmado (investigado con gdb sobre el binario real, ver sesion de depuracion
del wallpaper "Hinata Hyuga (2)", id 3801244014): WallpaperEngine::Data::Parsers::
ObjectParser::parseText() lee la propiedad "padding" de los objetos de texto como un
NUMERO simple, pero algunos wallpapers (creados con una version mas reciente/distinta
del editor de Windows) la guardan como vector-string de dos componentes
("32.00000 32.00000", horizontal y vertical) igual que "size" o "scale". Al llamar a
.get<double>() sobre ese string, nlohmann::json lanza type_error.302 y el proceso
muere. Wallpaper Engine en Windows sí soporta ambas formas; el port de Linux solo la
forma escalar. Confirmado con gdb + parcheando una copia aislada del wallpaper."""
import hashlib
import json
import os
import re
import shutil
import struct
import tempfile

from . import config
from .config import WORKSHOP_DIR

VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor_effects")

# Efectos "interactive" nativos del motor (xray, cursorripple...) cuyos shaders y
# materiales NO vienen instalados en los assets globales de linux-wallpaperengine
# (comprobado: a los 3 efectos del grupo "interactive" les faltan sus dependencias
# en ASSETS_DIR). La mayoria de wallpapers que los usan los empaquetan ellos mismos
# dentro de su propio scene.pkg (asi funcionan sin depender de assets globales), pero
# si alguno NO lo hace, el efecto simplemente no carga. Estas plantillas son los
# archivos REALES de Wallpaper Engine, extraidos de wallpapers del Workshop que si
# los traian consigo, y verificados en este sistema (compilan sin errores de GLSL,
# confirmado revisando el log de un proceso real en produccion para "xray" y con una
# prueba aislada para "cursorripple") — no son una reimplementacion propia.
VENDOR_EFFECTS = {
    "xray": {
        "ref": "effects/xray/effect.json",
        "marker": "shaders/effects/xray.frag",  # si esto YA existe, el wallpaper trae lo suyo
        "files": {
            "effects/xray/effect.json": "effect.json",
            "materials/effects/xray.json": "material.json",
            "shaders/effects/xray.frag": "shader.frag",
            "shaders/effects/xray.vert": "shader.vert",
        },
    },
    "cursorripple": {
        "ref": "effects/cursorripple/effect.json",
        "marker": "shaders/effects/cursorripple_combine.frag",
        "files": {
            "effects/cursorripple/effect.json": "effect.json",
            "materials/effects/cursorripple_apply_force.json": "material_apply_force.json",
            "materials/effects/cursorripple_simulate_force.json": "material_simulate_force.json",
            "materials/effects/cursorripple_combine.json": "material_combine.json",
            "shaders/effects/cursorripple_apply_force.frag": "apply_force.frag",
            "shaders/effects/cursorripple_apply_force.vert": "apply_force.vert",
            "shaders/effects/cursorripple_simulate_force.frag": "simulate_force.frag",
            "shaders/effects/cursorripple_simulate_force.vert": "simulate_force.vert",
            "shaders/effects/cursorripple_combine.frag": "combine.frag",
            "shaders/effects/cursorripple_combine.vert": "combine.vert",
        },
    },
}


def _unpack(path):
    with open(path, "rb") as f:
        data = f.read()
    pos = 0
    hdr_len = struct.unpack_from("<I", data, pos)[0]; pos += 4
    header = data[pos:pos + hdr_len]; pos += hdr_len
    entry_count = struct.unpack_from("<I", data, pos)[0]; pos += 4
    entries = []
    for _ in range(entry_count):
        name_len = struct.unpack_from("<I", data, pos)[0]; pos += 4
        name = data[pos:pos + name_len].decode("utf-8", errors="replace"); pos += name_len
        offset, length = struct.unpack_from("<II", data, pos); pos += 8
        entries.append((name, offset, length))
    blob_start = pos
    raw_by_name = {}
    for name, offset, length in entries:
        raw_by_name[name] = data[blob_start + offset: blob_start + offset + length]
    return header, entries, raw_by_name


def _repack(path, header, entries, raw_by_name):
    out = bytearray()
    out += struct.pack("<I", len(header))
    out += header
    out += struct.pack("<I", len(entries))

    new_offset = 0
    new_entries = []
    for name, _, _ in entries:
        raw = raw_by_name[name]
        new_entries.append((name, new_offset, len(raw)))
        new_offset += len(raw)

    for name, offset, length in new_entries:
        name_bytes = name.encode("utf-8")
        out += struct.pack("<I", len(name_bytes))
        out += name_bytes
        out += struct.pack("<II", offset, length)
    for name, _, _ in new_entries:
        out += raw_by_name[name]

    # A un temporal + rename atomico: un fallo a mitad de escritura no deja el
    # scene.pkg (que Steam puede no volver a descargar) a medias.
    # El temporal es exclusivo (mkstemp) para que dos escrituras nunca compartan nombre.
    _atomic_write_bytes(path, bytes(out))


def _atomic_write_bytes(path, data):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".repair-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        shutil.copymode(path, tmp) if os.path.exists(path) else os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _backup_once(path):
    """Copia `path` a `path.bak_original` SOLO si no existe ya. La copia se hace a un
    temporal y se renombra, para que un backup a medias nunca cuente como backup."""
    backup = path + ".bak_original"
    if os.path.isfile(backup):
        return
    with open(path, "rb") as f:
        _atomic_write_bytes(backup, f.read())


def _fix_vector_padding(scene):
    """El unico patron confirmado hasta ahora: 'padding' en objetos de texto
    guardado como vector-string en vez de numero. Se queda con la componente
    horizontal, que es la que linux-wallpaperengine espera."""
    fixed = 0
    for obj in scene.get("objects", []):
        if "text" in obj and isinstance(obj.get("padding"), str):
            parts = obj["padding"].split()
            if parts:
                try:
                    obj["padding"] = float(parts[0])
                    fixed += 1
                except ValueError:
                    pass
    return fixed


def _effect_file_refs(scene):
    """Devuelve el conjunto de rutas 'file' de todos los efectos usados en la
    escena (objects[].effects[].file), recorriendo tambien objetos anidados."""
    refs = set()
    for obj in scene.get("objects", []):
        for eff in obj.get("effects", []) or []:
            f = eff.get("file")
            if f:
                refs.add(f)
    return refs


def _inject_missing_vendor_effects(scene, entries, raw_by_name):
    """Si la escena usa un efecto nativo 'interactive' (xray, cursorripple) que
    en esta instalacion de linux-wallpaperengine no tiene sus dependencias
    globales (ver VENDOR_EFFECTS), pero el propio wallpaper TAMPOCO las trae
    empaquetadas, copia dentro del .pkg los archivos reales verificados en
    wpelib/vendor_effects/ para que el efecto funcione. Modifica `entries` y
    `raw_by_name` in-place. Devuelve la lista de nombres de efectos inyectados."""
    refs = _effect_file_refs(scene)
    existing_names = {n for n, _, _ in entries}
    injected = []
    for name, info in VENDOR_EFFECTS.items():
        if info["ref"] not in refs:
            continue
        if info["marker"] in raw_by_name:
            continue  # el wallpaper ya trae sus propios archivos, no tocar nada
        for pkg_name, template_file in info["files"].items():
            template_path = os.path.join(VENDOR_DIR, name, template_file)
            with open(template_path, "rb") as f:
                raw_by_name[pkg_name] = f.read()
            if pkg_name not in existing_names:
                entries.append((pkg_name, 0, 0))
                existing_names.add(pkg_name)
        injected.append(name)
    return injected


# Marcador del shader "xray" oficial ROTO: usa g_EffectTextureProjectionMatrixInverse
# para reproyectar la posicion del cursor, un uniform que no aparece en absoluto en el
# binario de linux-wallpaperengine (comprobado con `strings` sobre liblinux-wallpaperengine-lib.so),
# asi que se queda sin rellenar y el efecto no revela nada visible al mover el raton
# (confirmado en un wallpaper real: compila sin errores, pero no hay reaccion visual).
# El arreglo sustituye esa reproyeccion por comparacion directa en espacio UV (el mismo
# metodo, verificado con capturas reales, que usa el efecto "reveal_on_hover" propio de
# esta app) y se guarda ya corregido en wpelib/vendor_effects/xray/.
_BROKEN_XRAY_MARKER = b"g_EffectTextureProjectionMatrixInverse"


def _fix_broken_xray_shader(raw_by_name):
    """Si el wallpaper trae su propia copia (rota) del shader xray, la sustituye por
    la version corregida de la plantilla vendor. Devuelve True si se aplico."""
    frag_name = "shaders/effects/xray.frag"
    vert_name = "shaders/effects/xray.vert"
    if vert_name not in raw_by_name:
        return False
    if _BROKEN_XRAY_MARKER not in raw_by_name[vert_name]:
        return False  # no es la version rota (o ya esta arreglado)

    for pkg_name, template_file in VENDOR_EFFECTS["xray"]["files"].items():
        template_path = os.path.join(VENDOR_DIR, "xray", template_file)
        with open(template_path, "rb") as f:
            raw_by_name[pkg_name] = f.read()
    return True


_AUDIO_BARS_SHADER = "shaders/workshop/3577773857/effects/Simple_Audio_Bars.vert"
_AUDIO_BARS_BROKEN_SHA256 = "0608e9e36f29234827179234ab8186e389dbff043df8ed80386a1fb14bb274fe"


def _fix_audio_bars_shader(raw_by_name):
    """Elimina solo el #endif huérfano del recurso diagnosticado y verificado."""
    fixed = False
    hashes = {_AUDIO_BARS_BROKEN_SHA256,
              "c70a5978bff0a016a9dc4f77ede6327d06a776a74268b0d3eff2cd57f899ea3a"}
    for name, raw in list(raw_by_name.items()):
        if not re.fullmatch(r"shaders/workshop/\d+/effects/Simple_Audio_Bars\.vert", name):
            continue
        if hashlib.sha256(raw).hexdigest() not in hashes:
            continue
        lines = raw.splitlines(keepends=True)
        if len(lines) <= 69 or lines[69].strip() != b"#endif":
            continue
        raw_by_name[name] = b"".join(lines[:69] + lines[70:])
        fixed = True
    return fixed



_IRIS_BROKEN_SHA256 = "974eeb7fa6d8e923816d77c9cb9f5c91fcc50a403d23605c91b85ba7fe8c104e"


def _fix_iris_movement_shader(raw_by_name):
    """Corrige directiva y dimensiones UV de la versión conocida de iris."""
    fixed = False
    for name, raw in list(raw_by_name.items()):
        if not re.fullmatch(r"shaders/workshop/\d+/effects/iris_movement__\.vert", name):
            continue
        if hashlib.sha256(raw).hexdigest() != _IRIS_BROKEN_SHA256:
            continue
        lines = raw.splitlines(keepends=True)
        if len(lines) <= 92 or lines[92].strip() != b"#endif":
            continue
        new = b"".join(lines[:92] + lines[93:])
        new = new.replace(b"vec2 da = transformedCursorPosition *", b"vec2 da = transformedCursorPosition.xy *")
        raw_by_name[name] = new
        fixed = True
    return fixed


_KNOWN_FRAGMENT_HASHES = {
    "shaders/workshop/3577773857/effects/Simple_Audio_Bars.frag": "244821bc402ae08c2cef4a6b5e9e491343bbe0ec02b54e8cc6b69e974f8e374f",
    "shaders/workshop/3681571511/effects/fxaa.frag": "4aaa800c637f76ffd512963294d723086cd4e6e04dfcc35d038b8de794192608",
    "shaders/workshop/2844906964/effects/test_shader.frag": "683530058ca911911d5702699d9ad4f0a8cee7b4cb74f4ff953301f8bdbf0114",
    "shaders/workshop/3577773857/effects/sine_wave.frag": "f7c6acf28a9b8dacb938e9a94295dadb0e2b7faaa648ce49b7b53a9a496da486",
    "shaders/workshop/2799421411/effects/audio_responsive_oscilloscope.frag": "9acf31d49580b8b73d188bebe677a76921268c33230b2a9b5492ef437df976e7",
}


def _fix_known_fragment_shaders(raw_by_name):
    """Adapta únicamente las versiones diagnosticadas, sin alterar otros shaders."""
    fixed = []
    # Las mismas versiones aparecen bajo IDs distintos del efecto en Workshop.
    # Exigir nombre de recurso y hash permite reutilizarlas sin depender del fondo.
    accepted = {}
    for path, digest in _KNOWN_FRAGMENT_HASHES.items():
        accepted.setdefault(path.rsplit("/", 1)[-1], set()).add(digest)
    accepted.setdefault("Simple_Audio_Bars.frag", set()).update({
        "8993311eeb3ea2d5be6665b0947351859a2ba5e102a8db4a870d30d12d9fc9ef",
        "4fb5eed2c8bf8abbdd29403cc82bb743c5350a9d37ffec48ad2b8c7edd8b7278",
    })
    accepted.setdefault("sine_wave.frag", set()).add(
        "a4e8822e605698745ce06f4d014d4dd1a589af8cc76317f44ed1f4bb07071d5f")
    for name, raw in list(raw_by_name.items()):
        if not re.fullmatch(r"shaders/workshop/\d+/effects/[^/]+\.frag", name):
            continue
        if hashlib.sha256(raw).hexdigest() not in accepted.get(name.rsplit("/", 1)[-1], set()):
            continue
        if name.endswith(("Simple_Audio_Bars.frag", "sine_wave.frag")):
            # También las funciones auxiliares transforman coordenadas: usan una
            # variable global mutable, inicializada al entrar en main.
            new = re.sub(rb"\bv_TexCoord\b", b"audioCoord", raw)
            new = new.replace(b"varying vec2 audioCoord;",
                              b"varying vec2 v_TexCoord;\r\nvec2 audioCoord;")
            new = new.replace(b"void main() {",
                              b"void main() {\r\n    audioCoord = v_TexCoord.xy;", 1)
            if name.endswith("sine_wave.frag"):
                # La máscara calculada por pow es escalar y ApplyBlending exige float.
                new = new.replace(b"vec2 waveCoord = audioCoord;", b"float waveCoord = 0.0;")
        elif name.endswith("fxaa.frag"):
            # z/w siguen almacenando el tamaño del texel; solo xy es la posición UV.
            new = re.sub(rb"\bv_TexCoord(\s*[-+])", rb"v_TexCoord.xy\1", raw)
        elif name.endswith("audio_responsive_oscilloscope.frag"):
            assignments = []
            def defer_uniform_constant(match):
                kind, variable, expression = match.groups()
                assignments.append(variable + b" = " + expression + b";")
                return kind + b" " + variable + b";"
            new = re.sub(rb"const (vec2|float) (userBalance|lowBalanceMultipier) = ([^;]+);",
                         defer_uniform_constant, raw)
            new = new.replace(b"void main() {", b"void main() {\r\n    " + b"\r\n    ".join(assignments), 1)
        else:
            new = raw.replace(b"vec2 fragPos = v_TexCoord;", b"vec2 fragPos = v_TexCoord.xy;")
        if new != raw:
            raw_by_name[name] = new
            fixed.append(name.rsplit("/", 1)[-1])
    return fixed


def _combo_option_value(option):
    if isinstance(option, dict):
        return option.get("value")
    return option


def _as_text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def _numeric_text(value):
    """Si `value` es un texto numerico devuelve el numero (int o float), si no None."""
    if not isinstance(value, str):
        return None
    try:
        number = float(value.strip())
    except ValueError:
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return int(number) if number == int(number) and "." not in value and "e" not in value.lower() else number


def _fix_project_properties(data):
    """Normaliza propiedades de project.json (combo y slider) que linux-wallpaperengine no
    acepta (aborta con json type_error.302 o "Combo property must have a value"):
      - sin campo `value`: se rellena con la opcion indicada por `index`
      - `value` que no es texto (true, 1...): se convierte a texto
    y en los `slider`, valores numericos guardados como texto ("50" -> 50).
    Devuelve el numero de propiedades corregidas."""
    props = (data.get("general") or {}).get("properties") if isinstance(data, dict) else None
    if not isinstance(props, dict):
        return 0
    fixed = 0
    for prop in props.values():
        if isinstance(prop, dict) and prop.get("type") == "slider":
            # Los slider guardan a veces el numero como texto ("50"); el motor exige numero.
            for key in ("value", "min", "max", "step"):
                number = _numeric_text(prop.get(key))
                if number is not None:
                    prop[key] = number
                    fixed += 1
            continue
        if not isinstance(prop, dict) or prop.get("type") != "combo":
            continue
        # El motor lee tambien el `value` de cada opcion como texto.
        for option in prop.get("options") or []:
            if isinstance(option, dict) and "value" in option and not isinstance(option["value"], str):
                option["value"] = _as_text(option["value"])
                fixed += 1
        if "value" not in prop or prop["value"] is None:
            options = prop.get("options")
            index = prop.get("index", 0)
            if isinstance(options, list) and isinstance(index, int) and 0 <= index < len(options):
                value = _combo_option_value(options[index])
                if value is not None:
                    prop["value"] = _as_text(value)
                    fixed += 1
        elif not isinstance(prop["value"], str):
            prop["value"] = _as_text(prop["value"])
            fixed += 1
    return fixed


def _repair_project_json(folder):
    """Devuelve el numero de propiedades corregidas en project.json (0 si nada)."""
    path = os.path.join(folder, "project.json")
    if not os.path.isfile(path):
        return 0
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return 0
    fixed = _fix_project_properties(data)
    if fixed:
        _backup_once(path)
        _atomic_write_bytes(path, json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))
    return fixed


def attempt_repair(wid, fix_project=True):
    """Intenta reparar un wallpaper aplicando los patrones de incompatibilidad
    conocidos, en project.json (propiedades combo) y en scene.pkg. Guarda SIEMPRE una
    copia del original la primera vez (*.bak_original) antes de tocar nada. Es seguro
    llamarla a la vez desde varios procesos: se serializa por wallpaper con un lock.
    `fix_project=False` omite la normalizacion de project.json (solo se aplica a
    wallpapers que de verdad fallan, para no alterar los que ya funcionan).
    Devuelve (huboCambios: bool, mensaje: str)."""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(wid))
    with config.FileLock(os.path.join(config.CONF_DIR, f"repair_{safe}.lock")):
        return _attempt_repair_locked(wid, fix_project)


def _attempt_repair_locked(wid, fix_project=True):
    folder = os.path.join(WORKSHOP_DIR, wid)
    parts = []

    try:
        props_fixed = _repair_project_json(folder) if fix_project else 0
    except OSError as e:
        return False, f"No se pudo reescribir project.json: {e}"
    if props_fixed:
        parts.append(f"{props_fixed} propiedad(es) de project.json normalizadas")

    pkg_path = os.path.join(folder, "scene.pkg")
    if not os.path.isfile(pkg_path):
        if parts:
            return True, f"Reparado: {'; '.join(parts)} (backup en project.json.bak_original)."
        return False, "Este wallpaper no usa scene.pkg (no hay nada que reparar)."

    try:
        header, entries, raw_by_name = _unpack(pkg_path)
        if "scene.json" not in raw_by_name:
            return bool(parts), (f"Reparado: {'; '.join(parts)}." if parts else "scene.pkg no contiene scene.json.")
        scene = json.loads(raw_by_name["scene.json"].decode("utf-8"))
    except Exception as e:
        if parts:
            return True, f"Reparado: {'; '.join(parts)}. (scene.pkg no se pudo leer: {e})"
        return False, f"No se pudo leer scene.pkg: {e}"

    fixed = _fix_vector_padding(scene)
    injected = _inject_missing_vendor_effects(scene, entries, raw_by_name)
    xray_fixed = _fix_broken_xray_shader(raw_by_name)
    audio_bars_fixed = _fix_audio_bars_shader(raw_by_name)
    fragments_fixed = _fix_known_fragment_shaders(raw_by_name)
    iris_fixed = _fix_iris_movement_shader(raw_by_name)

    if not fixed and not injected and not xray_fixed and not audio_bars_fixed and not fragments_fixed and not iris_fixed:
        if parts:
            return True, f"Reparado: {'; '.join(parts)} (backup en project.json.bak_original)."
        return False, "No se encontro ninguna incompatibilidad conocida en este wallpaper."

    try:
        _backup_once(pkg_path)
    except OSError as e:
        return bool(parts), f"No se pudo guardar la copia original de scene.pkg: {e}"

    if fixed:
        raw_by_name["scene.json"] = json.dumps(scene, indent=4).encode("utf-8")
    try:
        _repack(pkg_path, header, entries, raw_by_name)
    except Exception as e:
        return bool(parts), f"Fallo al reescribir scene.pkg: {e}"

    if fixed:
        parts.append(f"{fixed} campo(s) 'padding' corregidos")
    if injected:
        parts.append(f"efectos anadidos: {', '.join(injected)}")
    if iris_fixed:
        parts.append("shader de movimiento de ojos corregido")
    if fragments_fixed:
        parts.append(f"shaders de fragmento corregidos: {', '.join(fragments_fixed)}")
    if audio_bars_fixed:
        parts.append("shader de barras de audio corregido (#endif sobrante)")
    if xray_fixed:
        parts.append("shader xray sustituido por la version que reacciona al raton")
    return True, f"Reparado: {'; '.join(parts)} (backup en *.bak_original)."


def scan_library_ids():
    """Ids de todos los wallpapers descargados localmente (tengan o no scene.pkg)."""
    if not os.path.isdir(WORKSHOP_DIR):
        return []
    return sorted(
        entry for entry in os.listdir(WORKSHOP_DIR)
        if os.path.isdir(os.path.join(WORKSHOP_DIR, entry))
    )


def attempt_repair_all(progress_callback=None):
    """Recorre TODA la biblioteca local (no solo los marcados en known_bad.json,
    por si alguno tiene el mismo patron y todavia no se ha probado) e intenta
    reparar cada uno con attempt_repair(). progress_callback(indice, total, wid),
    si se pasa, se llama antes de procesar cada wallpaper (util para una barra de
    progreso). Devuelve (lista_de_ids_reparados, total_revisados)."""
    ids = scan_library_ids()
    known_bad = config.load_known_bad()
    repaired = []
    for i, wid in enumerate(ids):
        if progress_callback:
            progress_callback(i, len(ids), wid)
        ok, _msg = attempt_repair(wid, fix_project=wid in known_bad)
        if ok:
            repaired.append(wid)
    return repaired, len(ids)
