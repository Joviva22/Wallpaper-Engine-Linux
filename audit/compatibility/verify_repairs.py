"""Verifica reparaciones en copias; nunca escribe en la biblioteca real."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

real_home = Path.home()
work = Path(tempfile.mkdtemp(prefix='wpe-repairs-'))
os.environ['HOME'] = str(work)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wpelib import config, repair, apply
real_config = json.loads((real_home / '.config/wallpaperengine-picker/config.json').read_text())
steam = Path(real_config['steam_library']) / 'steamapps'
library = steam / 'workshop/content/431960'
repair.WORKSHOP_DIR = str(work / 'library')
engine = real_home / '.local/opt/linux-wallpaperengine/bin/linux-wallpaperengine'
assets = steam / 'common/wallpaper_engine/assets'
report = Path(__file__).with_name('repair_verification.json')
results = json.loads(report.read_text()) if report.exists() else {}
ids = sys.argv[1:] or ['3789816832', '3802742966', '3088099655', '3789790717']
for wid in ids:
    source = library / wid
    baseline_pkg = source / 'scene.pkg.bak_original'
    if not baseline_pkg.is_file():
        baseline_pkg = source / 'scene.pkg'
    folder = Path(repair.WORKSHOP_DIR) / wid
    folder.mkdir(parents=True)
    for entry in source.iterdir():
        if entry.name == 'scene.pkg.bak_original':
            continue
        if entry.name in ('scene.pkg', 'project.json'):
            shutil.copy2(baseline_pkg if entry.name == 'scene.pkg' else entry, folder / entry.name)
        else:
            (folder / entry.name).symlink_to(entry)
    original = hashlib.sha256((source / 'scene.pkg').read_bytes()).hexdigest()
    variants = ['original', 'repaired'] if wid in ('3789816832', '3802742966') else ['original']
    case = {}
    for variant in variants:
        if variant == 'repaired':
            ok, message = repair.attempt_repair(wid, fix_project=False)
            assert ok, message
            case['repair_message'] = message
            assert (folder / 'scene.pkg.bak_original').read_bytes() == baseline_pkg.read_bytes()
            assert not repair.attempt_repair(wid, fix_project=False)[0]
            case['backup_verified'] = True
            case['idempotent'] = True
        cmd = [str(engine), '--assets-dir', str(assets), '--window', '0x0x128x128',
               '--fps', '15', '--silent', str(folder)]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                preexec_fn=apply.disable_core_dumps)
        timed_out = False
        try:
            output, _ = proc.communicate(timeout=8)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.terminate()
            try:
                output, _ = proc.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill();output, _ = proc.communicate()
        log = output.decode(errors='replace')
        log_path = Path(__file__).with_name(f'{wid}_{variant}.log')
        log_path.write_text('\n'.join(line.rstrip() for line in log.splitlines()) + '\n')
        case[variant] = {'returncode': proc.returncode, 'running_at_timeout': timed_out,
                         'log': log_path.name,
                         'shader_errors': [line for line in log.splitlines() if 'Failed to setup object' in line or 'GLSL ' in line and 'parsing Failed' in line or 'error:' in line],
                         'diagnostics': [line for line in log.splitlines() if any(token in line.lower() for token in ['error', 'failed', 'cannot', 'not found'])][-35:]}
    case['original_unchanged'] = hashlib.sha256((source / 'scene.pkg').read_bytes()).hexdigest() == original
    assert case['original_unchanged']
    results[wid] = case
report = Path(__file__).with_name('repair_verification.json')
report.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(results, ensure_ascii=False, indent=2))

for wid in ids:
    if 'repaired' in results[wid]:
        log = Path(__file__).with_name(results[wid]['repaired']['log']).read_text()
        assert not any(token in log for token in ['Failed to setup object', 'parsing Failed', 'error:']), wid
