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
import json
import os
import shutil
import struct

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
    tmp = path + ".tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(out)
            f.flush()
            os.fsync(f.fileno())
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


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


def attempt_repair(wid):
    """Intenta reparar el scene.pkg de un wallpaper aplicando los patrones de
    incompatibilidad conocidos. Guarda SIEMPRE una copia del .pkg original la
    primera vez (scene.pkg.bak_original) antes de tocar nada. Devuelve
    (huboCambios: bool, mensaje: str)."""
    folder = os.path.join(WORKSHOP_DIR, wid)
    pkg_path = os.path.join(folder, "scene.pkg")
    if not os.path.isfile(pkg_path):
        return False, "Este wallpaper no usa scene.pkg (no hay nada que reparar)."

    try:
        header, entries, raw_by_name = _unpack(pkg_path)
        if "scene.json" not in raw_by_name:
            return False, "scene.pkg no contiene scene.json."
        scene = json.loads(raw_by_name["scene.json"].decode("utf-8"))
    except Exception as e:
        return False, f"No se pudo leer scene.pkg: {e}"

    fixed = _fix_vector_padding(scene)
    injected = _inject_missing_vendor_effects(scene, entries, raw_by_name)
    xray_fixed = _fix_broken_xray_shader(raw_by_name)

    if not fixed and not injected and not xray_fixed:
        return False, "No se encontro ninguna incompatibilidad conocida en este wallpaper."

    backup_path = pkg_path + ".bak_original"
    if not os.path.isfile(backup_path):
        shutil.copy2(pkg_path, backup_path)

    raw_by_name["scene.json"] = json.dumps(scene, indent=4).encode("utf-8")
    try:
        _repack(pkg_path, header, entries, raw_by_name)
    except Exception as e:
        return False, f"Fallo al reescribir scene.pkg: {e}"

    parts = []
    if fixed:
        parts.append(f"{fixed} campo(s) 'padding' corregidos")
    if injected:
        parts.append(f"efectos anadidos: {', '.join(injected)}")
    if xray_fixed:
        parts.append("shader xray sustituido por la version que reacciona al raton")
    return True, f"Reparado: {'; '.join(parts)} (backup en scene.pkg.bak_original)."


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
    repaired = []
    for i, wid in enumerate(ids):
        if progress_callback:
            progress_callback(i, len(ids), wid)
        ok, _msg = attempt_repair(wid)
        if ok:
            repaired.append(wid)
    return repaired, len(ids)
