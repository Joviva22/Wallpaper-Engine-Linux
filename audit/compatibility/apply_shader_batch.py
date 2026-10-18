"""Aplica el lote verificado. Sin --apply solo enumera los fondos candidatos."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wpelib import repair
from scan_shaders import shaders, root

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
base = Path(__file__).parent
inventory = json.loads((base / 'shader_inventory.json').read_text())
verification = json.loads((base / 'shader_batch_verification.json').read_text())
for case in verification.values():
    assert case['backup_verified'] and case['idempotent']
    assert case['repaired']['running_at_timeout'] and not case['repaired']['shader_errors']
# Revisar todos los paquetes: otro fondo puede reutilizar un recurso conocido
# sin presentar los demás patrones sospechosos del inventario.
ids = sorted(folder.name for folder in root.iterdir() if (folder / 'scene.pkg').is_file())
results = {}
for wid in ids:
    pkg = root / wid / 'scene.pkg'
    resources = dict(shaders(pkg))
    before_resources = dict(resources)
    changed = repair._fix_audio_bars_shader(resources)
    changed = repair._fix_iris_movement_shader(resources) or changed
    changed = bool(repair._fix_known_fragment_shaders(resources)) or changed
    if not changed:
        continue
    changed_names = [name for name in resources if resources[name] != before_resources[name]]
    print(wid, ', '.join(changed_names))
    if not args.apply:
        continue
    before = hashlib.sha256(pkg.read_bytes()).hexdigest()
    backup = pkg.with_name('scene.pkg.bak_original')
    backup_before = hashlib.sha256(backup.read_bytes()).hexdigest() if backup.exists() else before
    ok, message = repair.attempt_repair(wid, fix_project=False)
    assert ok, message
    assert hashlib.sha256(backup.read_bytes()).hexdigest() == backup_before
    assert not repair.attempt_repair(wid, fix_project=False)[0]
    results[wid] = {'message': message, 'resources': changed_names,
                    'before_sha256': before, 'after_sha256': hashlib.sha256(pkg.read_bytes()).hexdigest(),
                    'backup_sha256': backup_before}
if args.apply:
    (base / 'applied_shader_batch.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(f'Aplicados: {len(results)}; backups e idempotencia verificados.')
