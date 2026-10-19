"""Limpieza de espacio: borra solo lo que la app puede volver a generar.

Nunca toca: los wallpapers, las copias `scene.pkg.bak_original` de las reparaciones, los personajes y voces
descargados de Nikke Stage ni su base de datos (IndexedDB), ni la configuracion. Cada categoria lista rutas
concretas dentro de las carpetas de la app; los enlaces simbolicos se borran como enlaces, sin seguirlos."""
import fcntl
import glob
import os
import shutil
from dataclasses import dataclass, field

from . import config

CACHE_ROOT = os.path.expanduser("~/.cache/wallpaperengine-picker")
STAGE_ID = "9100000001"
# partes del perfil web de Nikke Stage que son puro cache HTTP/GPU; IndexedDB y Local Storage no se tocan
STAGE_CACHE_DIRS = ("Cache", "Code Cache", "GPUCache", "DawnCache", "GrShaderCache", "ShaderCache")


@dataclass
class Category:
    key: str
    label: str
    note: str
    paths: list = field(default_factory=list)
    default: bool = True
    blocked: str = ""
    size: int = 0


def _size(path):
    try:
        if os.path.islink(path) or os.path.isfile(path):
            return os.lstat(path).st_size
        total = 0
        for root, dirs, files in os.walk(path):
            for name in files + dirs:
                try:
                    total += os.lstat(os.path.join(root, name)).st_size
                except OSError:
                    pass
        return total
    except OSError:
        return 0


def _lock_is_free(path):
    try:
        fd = os.open(path, os.O_RDWR)
    except OSError:
        return False
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False
    finally:
        os.close(fd)


def _stage_running():
    """True si Nikke Stage esta en marcha en alguna pantalla (su cache esta en uso)."""
    for path in glob.glob(os.path.join(config.CONF_DIR, "pid_*.pid")):
        screen = os.path.basename(path)[4:-4]
        if config.load_json(config.CURRENT_FILE, {}).get(screen) != STAGE_ID:
            continue
        try:
            with open(path) as f:
                os.kill(int(f.read().strip()), 0)
            return True
        except (OSError, ValueError):
            continue
    return False


def scan():
    """Categorias con su tamaño actual (solo las que tienen algo que borrar)."""
    conf = config.CONF_DIR
    cats = [
        Category("old_thumbs", "Miniaturas de versiones antiguas",
                 "Carpetas de miniaturas de versiones anteriores de la app; ya no se usan.",
                 [p for p in glob.glob(os.path.join(CACHE_ROOT, "thumbs_v*")) + glob.glob(os.path.join(CACHE_ROOT, "workshop_thumbs*"))
                  if os.path.abspath(p) not in (os.path.abspath(config.CACHE_DIR), os.path.abspath(config.WORKSHOP_THUMB_CACHE))]),
        Category("thumbs", "Miniaturas actuales",
                 "Se vuelven a crear al abrir la app (la primera vez tarda un poco).",
                 [config.CACHE_DIR, config.WORKSHOP_THUMB_CACHE], default=False),
        Category("old_logs", "Copias antiguas de los registros del motor",
                 "Los `.log.1` rotados; solo sirven para diagnóstico de fallos viejos.",
                 glob.glob(os.path.join(conf, "wallpaperengine_*.log.1"))),
        Category("logs", "Registros actuales del motor",
                 "Se pierde el contexto de los últimos errores (el panel de Diagnóstico quedaría vacío).",
                 glob.glob(os.path.join(conf, "wallpaperengine_*.log")), default=False),
        Category("locks", "Archivos de bloqueo de reparaciones",
                 "Restos `repair_*.lock` que nadie está usando.",
                 [p for p in glob.glob(os.path.join(conf, "repair_*.lock")) if _lock_is_free(p)]),
    ]
    stage_cache = [os.path.join(CACHE_ROOT, "cef", STAGE_ID, "Default", d) for d in STAGE_CACHE_DIRS]
    stage_cache.append(os.path.join(CACHE_ROOT, "cef", STAGE_ID, "component_crx_cache"))
    stage = Category("stage_cache", "Caché web de Nikke Stage",
                     "Caché de red/GPU del navegador interno. Se conservan los personajes y voces descargados.",
                     [p for p in stage_cache if os.path.lexists(p)])
    if _stage_running():
        stage.blocked = "Nikke Stage está en marcha: cambia de fondo para poder limpiarla."
    cats.append(stage)
    result = []
    for cat in cats:
        cat.paths = [p for p in cat.paths if os.path.lexists(p)]
        cat.size = sum(_size(p) for p in cat.paths)
        if cat.paths:
            result.append(cat)
    return result


def _allowed(path):
    path = os.path.abspath(path)
    return any(path == root or path.startswith(root + os.sep)
               for root in (os.path.abspath(CACHE_ROOT), os.path.abspath(config.CONF_DIR)))


def clean(categories):
    """Borra las categorias dadas (objetos de scan()). Devuelve (bytes liberados, errores)."""
    freed, errors = 0, []
    for cat in categories:
        if cat.blocked:
            errors.append(f"{cat.label}: {cat.blocked}")
            continue
        for path in cat.paths:
            if not _allowed(path):
                errors.append(f"{path}: fuera de las carpetas de la app, no se toca")
                continue
            size = _size(path)
            try:
                if os.path.islink(path) or os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                freed += size
            except OSError as exc:
                errors.append(f"{path}: {exc}")
    return freed, errors


def human(size):
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
