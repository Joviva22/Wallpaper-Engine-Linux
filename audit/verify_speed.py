"""Prueba real de ×2 en una ventana pequeña y con HOME/Steam temporales.
No aplica fondos al escritorio ni modifica la biblioteca del usuario.
"""
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

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
config.save_speed({'TEST': 2.0})
assert config.engine_supports_speed(), 'El motor instalado no anuncia --speed'
cmd = apply.engine_command('TEST', '123')
assert cmd[0] == str(wrapper)
assert cmd[cmd.index('--speed') + 1] == '2.0'
index = cmd.index('--screen-root')
cmd[index:index+2] = ['--window', '0x0x128x128']
cmd += ['--screenshot', str(work / 'speed2.png'), '--screenshot-delay', '120']
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
text = out.decode(errors='replace')
(work / 'speed2.log').write_text(text)
result = {'selected_engine': cmd[0], 'speed_argument': '2.0',
          'mpv_verified_2x': 'Video playback speed: 2x' in text,
          'screenshot_exists': (work / 'speed2.png').is_file(),
          'returncode': proc.returncode, 'artifacts': str(work)}
(Path(__file__).with_name('speed_verification.json')).write_text(json.dumps(result, indent=2) + '\n')
from PIL import Image, ImageStat
if result['screenshot_exists']:
    with Image.open(work / 'speed2.png') as frame:
        result['screenshot_has_color'] = max(ImageStat.Stat(frame.convert('RGB')).mean) > 1
(Path(__file__).with_name('speed_verification.json')).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
if not result['mpv_verified_2x']:
    print(text[-3000:])
    raise SystemExit(1)
