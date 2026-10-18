"""Prueba real de velocidad en una ventana pequeña y con HOME/Steam temporales.
No aplica fondos al escritorio ni modifica la biblioteca del usuario.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--speed', type=float, choices=[1.5, 2.0, 3.0, 4.0], default=2.0)
speed = parser.parse_args().speed
stem = 'speed' + f'{speed:g}'.replace('.', '_')
report_name = 'speed_verification.json' if speed == 2 else stem + '_verification.json'
real_home = Path.home()
prefix = real_home / '.local/opt/linux-wallpaperengine'
wrapper = prefix / 'bin/linux-wallpaperengine'
if not wrapper.is_file():
    raise SystemExit('El motor parcheado aún no está instalado.')
real_config = json.loads((real_home / '.config/wallpaperengine-picker/config.json').read_text())
assets = Path(real_config['steam_library']) / 'steamapps/common/wallpaper_engine/assets'
work = Path(tempfile.mkdtemp(prefix='wpe-speed-verify-'))
os.environ['HOME'] = str(work)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wpelib import config, apply
config.PATCHED_ENGINE_DIR = str(prefix)
config.PATCHED_ENGINE_WRAPPER = str(wrapper)
config.ASSETS_DIR = str(assets)
folder = Path(config.WORKSHOP_DIR) / '123'
folder.mkdir(parents=True)
config.atomic_write_json(str(folder / 'project.json'), {'title': 'Speed test', 'type': 'video', 'file': 'test.mp4'})
subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=128x128:rate=30',
                '-t', '3', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(folder / 'test.mp4')], check=True, timeout=30)
assert speed in config.SPEED_OPTIONS
config.save_speed({'TEST': speed})
assert config.engine_supports_speed(), 'El motor instalado no anuncia --speed'
cmd = apply.engine_command('TEST', '123')
assert cmd[0] == str(wrapper)
assert cmd[cmd.index('--speed') + 1] == str(speed)
index = cmd.index('--screen-root')
cmd[index:index+2] = ['--window', '0x0x128x128']
cmd += ['--screenshot', str(work / (stem + '.png')), '--screenshot-delay', '120']
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        env=apply.engine_env('123'), preexec_fn=apply.disable_core_dumps)
try:
    try:
        out, _ = proc.communicate(timeout=8)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            out, _ = proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
finally:
    if proc.poll() is None:
        proc.kill()
        proc.wait()
text = '\n'.join(line.rstrip() for line in out.decode(errors='replace').splitlines()) + '\n'
(work / (stem + '.log')).write_text(text)
result = {'selected_engine': cmd[0], 'speed_argument': str(speed),
          'mpv_verified_speed': f'Video playback speed: {speed:g}x' in text,
          'screenshot_exists': (work / (stem + '.png')).is_file(),
          'returncode': proc.returncode, 'artifacts': str(work)}
from PIL import Image, ImageStat
if result['screenshot_exists']:
    with Image.open(work / (stem + '.png')) as frame:
        result['screenshot_has_color'] = max(ImageStat.Stat(frame.convert('RGB')).mean) > 1
        result['screenshot_size'] = list(frame.size)
base = Path(__file__).parent
import shutil
for suffix in ['.log', '.png']:
    artifact = work / (stem + suffix)
    if artifact.exists():
        shutil.copy2(artifact, base / artifact.name)
result['evidence_log'] = stem + '.log'
result['evidence_screenshot'] = stem + '.png'
(base / report_name).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
if not result['mpv_verified_speed'] or not result.get('screenshot_has_color'):
    print(text[-3000:])
    raise SystemExit(1)
