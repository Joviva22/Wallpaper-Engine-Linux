"""Auditoría de solo lectura de proyectos locales y logs, sin importar la app."""
import collections
import datetime
import json
import pathlib
import re
import struct
import sys

HOME = pathlib.Path.home()
CONF = HOME / '.config/wallpaperengine-picker'
REPO = pathlib.Path(__file__).resolve().parents[1]
lib = pathlib.Path(json.loads((CONF / 'config.json').read_text())['steam_library'])
root = lib / 'steamapps/workshop/content/431960'
sys.path.insert(0, str(REPO))
from wpelib.classify import classify_project

def resolve_project(wid):
    folder = root / wid
    try:
        return json.loads((folder / 'project.json').read_text()), [p.name for p in folder.iterdir()]
    except (OSError, ValueError):
        return None
assets = lib / 'steamapps/common/wallpaper_engine/assets'


def pkg_index(path, scene_name="scene.json"):
    duplicates = []
    size = path.stat().st_size
    with path.open('rb') as f:
        def u32():
            b = f.read(4)
            if len(b) != 4:
                raise ValueError('tabla truncada')
            return struct.unpack('<I', b)[0]
        hlen = u32()
        if hlen > 128:
            raise ValueError('cabecera excesiva')
        if not f.read(hlen).startswith(b'PKGV'):
            raise ValueError('cabecera no PKGV')
        count = u32()
        if count > 100000:
            raise ValueError('demasiadas entradas')
        entries = {}
        for _ in range(count):
            n = u32()
            if n > 16384:
                raise ValueError('nombre excesivo')
            b = f.read(n)
            if len(b) != n:
                raise ValueError('nombre truncado')
            name = b.decode('utf-8')
            off, length = u32(), u32()
            if name in entries:
                duplicates.append(name)
            entries[name] = (off, length)
        start = f.tell()
        for name, (off, length) in entries.items():
            if start + off + length > size:
                raise ValueError('entrada fuera del archivo: ' + name)
        scene = None
        if scene_name in entries:
            off, length = entries[scene_name]
            if length > 32 * 1024 * 1024:
                raise ValueError('scene.json excede límite de auditoría de 32 MiB')
            f.seek(start + off)
            scene = json.loads(f.read(length))
        return entries, scene, duplicates


LOG_RULES = [
 ('LOG_JSON', r'type_error\.302|Combo property must have|Property must have a value'),
 ('LOG_SHADER', r'GLSL .*Failed|Failed to setup object|compilation errors|error: syntax error'),
 ('LOG_WEB_SYMBOL', r'close symbol missing'),
 ('LOG_ABORT', r'terminate called|pure virtual method called|Segmentation fault|Aborted \(core'),
 ('LOG_LIGHT', r'Light objects are not supported|VolumeLight objects are not supported'),
 ('LOG_OBJECT', r'Unknown object type'),
 ('LOG_RESOURCE', r'Cannot (find file|resolve user texture|load particle|load texture)|[Ff]ile.*not found'),
 ('LOG_DBUS', r'DBus error:'),
 ('LOG_AV_SYNC', r'Audio/Video desynchronisation'),
 ('LOG_DECODER', r'Cannot load libcuda|Could not dynamically load CUDA|Failed setup for format vulkan|VK_KHR_video_decode_queue'),
 ('LOG_EGL_FALLBACK', r'Failed to initialize GLEW, but continuing with EGL context'),
 ('LOG_WAYLAND', r'Fullscreen detection not supported'),
]
LOG_RULES = [(code, re.compile(pattern)) for code, pattern in LOG_RULES]
logdata = collections.defaultdict(dict)
unassigned = collections.Counter()
if '--reuse-logs' in sys.argv:
    previous = json.loads((REPO / 'audit/wallpapers.json').read_text())
    logdata.update({row['id']: row['logs'] for row in previous['rows']})
    unassigned.update(previous['unassigned_log_lines'])
else:
    for log in sorted(CONF.glob('wallpaperengine_*.log*')):
        if not log.is_file():
            continue
        wid = None
        with log.open(errors='replace') as f:
            for num, line in enumerate(f, 1):
                if line.startswith('Running with:'):
                    m = re.search(r'/431960/(\d+)(?:\s|$)', line)
                    wid = m.group(1) if m else None
                for code, pattern in LOG_RULES:
                    if not pattern.search(line):
                        continue
                    if not wid:
                        unassigned[code] += 1
                        continue
                    data = logdata[wid].setdefault(code, {'count': 0, 'samples': []})
                    data['count'] += 1
                    if len(data['samples']) < 3:
                        data['samples'].append({'file': log.name, 'line': num, 'text': line.strip()[:500]})
rows = []
for folder in sorted(root.iterdir()):
    if not folder.is_dir():
        continue
    row = {'id': folder.name, 'title': folder.name, 'type': 'unknown', 'findings': [], 'logs': logdata.get(folder.name, {})}
    rows.append(row)
    def add(code, detail):
        row['findings'].append({'code': code, 'detail': detail})
    try:
        project = json.loads((folder / 'project.json').read_text(encoding='utf-8'))
        if not isinstance(project, dict):
            raise ValueError('project.json no es objeto')
    except Exception as e:
        add('PROJECT_INVALID', str(e)); continue
    row['title'] = project.get('title', folder.name)
    if not isinstance(row['title'], str):
        add('TITLE_INVALID', repr(row['title'])); row['title'] = str(row['title'])
    info = classify_project(folder.name, project, [p.name for p in folder.iterdir()], resolve=resolve_project)
    row['type'] = info['type'].lower()
    row['preset'] = info['preset']
    row['dependency'] = info['dependency']
    if row['preset'] and resolve_project(row['dependency']) is None:
        add('PRESET_PARENT_MISSING', row['dependency'])
    for key in ['file', 'preview']:
        value = project.get(key)
        if key == 'file' and row['preset'] and not value:
            continue
        if not isinstance(value, str) or not value:
            add('META_PATH_INVALID', key + ': ' + repr(value))
        elif not (folder / value).exists() and not (key == 'file' and (folder / pathlib.Path(value).with_suffix('.pkg')).is_file()):
            add('FILE_MISSING', key + ': ' + value)
    general = project.get('general') or {}
    if not isinstance(general, dict):
        add('PROPERTIES_INVALID', 'general no es objeto'); general = {}
    props = general.get('properties') or {}
    if not isinstance(props, dict):
        add('PROPERTIES_INVALID', 'properties no es objeto'); props = {}
    for name, prop in props.items():
        if not isinstance(prop, dict):
            add('PROPERTIES_INVALID', name); continue
        if prop.get('type') == 'combo':
            if 'value' not in prop:
                add('COMBO_VALUE_MISSING', name)
            elif isinstance(prop['value'], bool) or not isinstance(prop['value'], (str, int, float)):
                add('COMBO_VALUE_TYPE', name + ': ' + repr(prop['value']))
            options = prop.get('options')
            if not isinstance(options, list):
                add('COMBO_OPTIONS_INVALID', name)
            else:
                for opt in options:
                    if isinstance(opt, dict) and ('value' not in opt or 'label' not in opt or isinstance(opt.get('value'), bool)):
                        add('COMBO_OPTIONS_INVALID', name + ': ' + repr(opt))
    if row['type'] == 'web':
        add('WEB_BACKEND_RISK', 'Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto')
    names = {}
    scene = None
    try:
        scene_name = project.get('file') if isinstance(project.get('file'), str) else 'scene.json'
        pkg_path = folder / pathlib.Path(scene_name).with_suffix('.pkg')
        if pkg_path.is_file() and row['type'] == 'scene':
            names, scene, duplicates = pkg_index(pkg_path, scene_name)
            for name in duplicates:
                add('PKG_DUPLICATE_ENTRY', name)
            row['pkg_entries'] = len(names)
            if scene is None and row['type'] == 'scene' and not (folder / scene_name).is_file():
                add('SCENE_MISSING', 'scene.json no está en paquete ni en carpeta')
        if row['type'] == 'scene' and (folder / scene_name).is_file():
            scene = json.loads((folder / scene_name).read_text())
        if scene is not None:
            if not isinstance(scene, dict) or not isinstance(scene.get('objects', []), list):
                raise ValueError('estructura de escena inválida')
            row['objects'] = len(scene.get('objects', []))
            for obj in scene.get('objects', []):
                if not isinstance(obj, dict):
                    add('OBJECT_INVALID', repr(obj)[:100]); continue
                label = str(obj.get('id', '?')) + ' ' + str(obj.get('name', ''))
                if 'text' in obj and isinstance(obj.get('padding'), str):
                    add('TEXT_PADDING_STRING', label + ': ' + obj['padding'])
                if 'light' in obj:
                    add('LIGHT_UNSUPPORTED', label)
                if 'shape' in obj:
                    add('VOLUME_LIGHT_UNSUPPORTED', label)
                for effect in obj.get('effects', []) or []:
                    if not isinstance(effect, dict):
                        continue
                    ref = effect.get('file')
                    if isinstance(ref, str) and ref not in names and not (folder / ref).is_file() and not (assets / ref).is_file():
                        add('EFFECT_REF_UNRESOLVED', label + ': ' + ref)
    except Exception as e:
        add('SCENE_OR_PKG_INVALID', str(e))
    if row['type'] not in ('scene', 'web', 'video'):
        add('TYPE_UNRECOGNIZED', row['type'])

result = {'date': datetime.datetime.now().astimezone().isoformat(), 'library': str(root), 'count': len(rows), 'type_counts': dict(collections.Counter(r['type'] for r in rows)), 'rows': rows, 'historical_ids_not_installed': sorted(set(logdata) - {r['id'] for r in rows}), 'unassigned_log_lines': dict(unassigned)}
(REPO / 'audit/wallpapers.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('Fondos:', len(rows), 'Tipos:', result['type_counts'])
for code in sorted({f['code'] for r in rows for f in r['findings']}):
    affected = [r for r in rows if any(f['code'] == code for f in r['findings'])]
    print(code, len(affected), 'fondos;', sum(f['code'] == code for r in rows for f in r['findings']), 'casos')
for code, _ in LOG_RULES:
    affected = [r for r in rows if code in r['logs']]
    if affected:
        print(code, len(affected), 'fondos con evidencia histórica')
