"""Reproduce el #endif huérfano sin renderizar ni modificar el wallpaper original."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

home = Path.home()
work = Path(tempfile.mkdtemp(prefix='wpe-shader-probe-'))
os.environ['HOME'] = str(work)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wpelib.repair import _unpack
library = home / '.local/share/Steam'
package = library / 'steamapps/workshop/content/431960/3789816832/scene.pkg'
if package.with_name('scene.pkg.bak_original').is_file():
    package = package.with_name('scene.pkg.bak_original')
_, _, files = _unpack(package)
name = 'shaders/workshop/3577773857/effects/Simple_Audio_Bars.vert'
raw = files[name]
assert hashlib.sha256(raw).hexdigest() == '0608e9e36f29234827179234ab8186e389dbff043df8ed80386a1fb14bb274fe'
lines = raw.decode().splitlines(keepends=True)
assert lines[69].strip() == '#endif'
header = '#version 120\n#extension GL_GOOGLE_include_directive : require\n'
variants = {'original': ''.join(lines), 'without_orphan_endif': ''.join(lines[:69] + lines[70:])}
glslang = home / 'build/lwe/build/output/glslang'
include = library / 'steamapps/common/wallpaper_engine/assets/shaders'
results = {}
for label, text in variants.items():
    path = work / (label + '.vert')
    path.write_text(header + text)
    run = subprocess.run([str(glslang), '-E', '-S', 'vert', '-I' + str(include), str(path)],
                         capture_output=True, text=True, timeout=20)
    results[label] = {'returncode': run.returncode, 'errors': run.stderr[-3000:]}
results['scope'] = 'Solo preprocesador; no valida el aspecto visual ni todos los shaders del efecto.'
results['original_unchanged'] = hashlib.sha256(_unpack(package)[2][name]).hexdigest() == hashlib.sha256(raw).hexdigest()
Path(__file__).with_name('audio_shader_probe.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(results, ensure_ascii=False, indent=2))
