"""Rotación coordinada con la GUI y con la selección automática compartida."""
import math
import os
import subprocess
import time

from . import config
from .selection import eligible_ids


def number(value, default):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (ValueError, TypeError):
        return default


def tick(now=None, apply_fn=None):
    now = time.time() if now is None else now
    if os.path.exists(os.path.join(config.CONF_DIR, 'rotation_paused')):
        return
    allowed = eligible_ids()
    apply_fn = apply_fn or (lambda screen, wid: subprocess.run(
        [config.APPLY_SCRIPT, f'{screen}={wid}'], stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25).returncode == 0)
    # La decisión, aplicación aceptada y progreso usan el mismo lock que la GUI.
    with config.FileLock(config.PLAYLISTS_LOCK):
        playlists = config.load_playlists()
        changed = False
        for screen, entry in playlists.items():
            if not isinstance(entry, dict) or entry.get('enabled') is not True:
                continue
            if os.path.exists(os.path.join(config.CONF_DIR, 'rotation_paused')):
                break
            items = entry.get('items')
            if not isinstance(items, list) or not items:
                continue
            interval = max(1, number(entry.get('interval_minutes'), 30)) * 60
            if now - number(entry.get('last_switch'), 0) < interval:
                continue
            index = int(number(entry.get('current_index'), 0))
            for step in range(1, len(items) + 1):
                next_index = (index + step) % len(items)
                wid = items[next_index]
                if not isinstance(wid, str) or wid not in allowed:
                    continue
                try:
                    accepted = apply_fn(screen, wid)
                except (OSError, subprocess.TimeoutExpired):
                    accepted = False
                if accepted:
                    entry.update(current_index=next_index, last_switch=now)
                    changed = True
                break
        if changed:
            config.atomic_write_json(config.PLAYLISTS_FILE, playlists)


def main():
    os.umask(0o077)
    # Descriptor no heredable: los motores no retienen el lock de instancia única.
    fd = os.open(os.path.join(config.CONF_DIR, 'rotate.lock'), os.O_RDWR | os.O_CREAT, 0o600)
    import fcntl
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return
    try:
        while True:
            tick()
            time.sleep(30)
    finally:
        os.close(fd)
