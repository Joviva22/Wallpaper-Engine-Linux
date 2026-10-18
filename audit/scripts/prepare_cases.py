"""Extrae casos reales y el wrapper C++ actual, sin modificar fondos ni motor."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

home = Path.home()
settings = json.loads((home / '.config/wallpaperengine-picker/config.json').read_text())
root = Path(settings['steam_library']) / 'steamapps/workshop/content/431960'
os.environ['HOME'] = tempfile.mkdtemp(prefix='wpe-script-cases-')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wpelib.repair import _unpack

source_path = home / 'build/lwe/src/WallpaperEngine/Scripting/ScriptEngine.cpp'
source = source_path.read_text()
start = source.index('std::ostringstream wrapper;')
block = source[start:source.index('const std::string evalScript', start)]
tokens = re.findall(r'<<\s*("(?:\\.|[^"\\])*"|id\b|body\b)', block)
assert tokens and tokens.count('body') == 1
cases = []
for wid, oid, reason in [('3088099655', 97, 'thisScene.getLayer oculto por shim local'),
                         ('2947399331', 349, 'engine.userProperties ausente en shim y EngineObject'),
                         ('3208556055', 608, 'Vec3 no publicado como constructor global')]:
    scene = json.loads(_unpack(root / wid / 'scene.pkg')[2]['scene.json'])
    obj = next(o for o in scene['objects'] if o['id'] == oid)
    script = obj['text']['script']
    body = script.replace("'use strict';", '').replace('"use strict";', '').replace('export ', '')
    wrapper = ''.join(body if token == 'body' else '1' if token == 'id' else json.loads(token) for token in tokens)
    cases.append({'id': wid, 'object': oid, 'name': obj['name'], 'reason': reason,
                  'script_sha256': hashlib.sha256(script.encode()).hexdigest(), 'wrapper': wrapper})
base = Path(__file__).parent
(base / 'cases.json').write_text(json.dumps({'source': str(source_path),
    'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'cases': cases}, ensure_ascii=False, indent=2) + '\n')
print(f'{len(cases)} casos extraídos del wrapper actual.')
