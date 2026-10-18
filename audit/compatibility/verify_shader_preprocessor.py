"""Confirma directivas desequilibradas y su reparación, sin modificar paquetes."""
import json
from pathlib import Path
import subprocess
from scan_shaders import home, root, settings, shaders, repair
import tempfile

inventory = json.loads(Path(__file__).with_name('shader_inventory.json').read_text())
glslang = home / 'build/lwe/build/output/glslang'
include = Path(settings['steam_library']) / 'steamapps/common/wallpaper_engine/assets/shaders'
work = Path(tempfile.mkdtemp(prefix='wpe-shader-preprocess-'))
results = []
for item in inventory['candidates']:
    if not any(f['code'] == 'ORPHAN_ENDIF' for f in item['findings']):
        continue
    pkg = root / item['ids'][0] / 'scene.pkg'
    backup = pkg.with_name('scene.pkg.bak_original')
    raw = dict(shaders(backup if backup.is_file() else pkg))[item['shader']]
    files = {item['shader']: raw}
    repaired = repair._fix_audio_bars_shader(files) or repair._fix_iris_movement_shader(files)
    result = {'shader': item['shader'], 'sha256': item['sha256'], 'ids': item['ids'], 'repair_available': repaired}
    for label, text in [('original', raw), ('repaired', files[item['shader']])]:
        if label == 'repaired' and not repaired:
            continue
        path = work / (label + '.vert')
        path.write_bytes(b'#version 120\n#extension GL_GOOGLE_include_directive : require\n' + text)
        proc = subprocess.run([str(glslang), '-E', '-S', 'vert', '-I' + str(include), str(path)],
                              capture_output=True, text=True, timeout=20)
        result[label] = {'returncode': proc.returncode, 'stderr': proc.stderr[-1500:]}
    if repaired:
        assert result['original']['returncode'] != 0 and result['repaired']['returncode'] == 0, result
    results.append(result)
Path(__file__).with_name('shader_preprocessor_verification.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(results, ensure_ascii=False, indent=2))
