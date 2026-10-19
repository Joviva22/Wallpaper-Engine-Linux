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


def _default_apply(screen, wid):
    return subprocess.run(
        [config.APPLY_SCRIPT, f'{screen}={wid}'], stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25).returncode == 0


def _paused():
    return os.path.exists(os.path.join(config.CONF_DIR, 'rotation_paused'))


def pick(items, index, allowed, direction=1):
    """Indice del siguiente (direction=1) o anterior (-1) fondo de `items` que esté en `allowed`, o None."""
    for step in range(1, len(items) + 1):
        candidate = (index + direction * step) % len(items)
        wid = items[candidate]
        if isinstance(wid, str) and wid in allowed:
            return candidate
    return None


def tick(now=None, apply_fn=None):
    now = time.time() if now is None else now
    if _paused():
        return
    allowed = eligible_ids()
    apply_fn = apply_fn or _default_apply
    # La decisión, aplicación aceptada y progreso usan el mismo lock que la GUI.
    with config.FileLock(config.PLAYLISTS_LOCK):
        playlists = config.load_playlists()
        changed = False
        for screen, entry in playlists.items():
            if not isinstance(entry, dict) or entry.get('enabled') is not True:
                continue
            if _paused():
                break
            items = entry.get('items')
            if not isinstance(items, list) or not items:
                continue
            interval = max(1, number(entry.get('interval_minutes'), 30)) * 60
            if now - number(entry.get('last_switch'), 0) < interval:
                continue
            next_index = pick(items, int(number(entry.get('current_index'), 0)), allowed)
            if next_index is None:
                continue
            try:
                accepted = apply_fn(screen, items[next_index])
            except (OSError, subprocess.TimeoutExpired):
                accepted = False
            if accepted:
                entry.update(current_index=next_index, last_switch=now)
                changed = True
        if changed:
            config.atomic_write_json(config.PLAYLISTS_FILE, playlists)


def status(screen, now=None, allowed=None):
    """Estado de la rotación de una pantalla para mostrarlo en la interfaz.

    Devuelve un dict con: enabled, paused, items (total), playable (los que rotarán), current (id o None),
    next (id o None), seconds_left (hasta el próximo cambio, o None si no hay)."""
    now = time.time() if now is None else now
    allowed = eligible_ids() if allowed is None else allowed
    entry = config.load_playlists().get(screen)
    entry = entry if isinstance(entry, dict) else {}
    items = [w for w in entry.get('items', []) if isinstance(w, str)]
    index = int(number(entry.get('current_index'), 0))
    info = {'enabled': entry.get('enabled') is True, 'paused': _paused(), 'items': len(items),
            'playable': sum(1 for w in items if w in allowed), 'current': None, 'next': None, 'seconds_left': None}
    if not items:
        return info
    info['current'] = items[index % len(items)]
    nxt = pick(items, index, allowed)
    info['next'] = items[nxt] if nxt is not None else None
    if info['enabled'] and not info['paused'] and info['next']:
        interval = max(1, number(entry.get('interval_minutes'), 30)) * 60
        info['seconds_left'] = max(0, int(number(entry.get('last_switch'), 0) + interval - now))
    return info


def step(screen, direction=1, now=None, apply_fn=None):
    """Pasa ya al siguiente (1) o al anterior (-1) fondo de la lista, aunque la rotación esté desactivada o en
    pausa, y reinicia la cuenta atrás. Devuelve (True, id) o (False, motivo)."""
    now = time.time() if now is None else now
    apply_fn = apply_fn or _default_apply
    allowed = eligible_ids()
    with config.FileLock(config.PLAYLISTS_LOCK):
        playlists = config.load_playlists()
        entry = playlists.get(screen)
        items = entry.get('items') if isinstance(entry, dict) else None
        if not isinstance(items, list) or not items:
            return False, 'La lista de rotación está vacía.'
        target = pick(items, int(number(entry.get('current_index'), 0)), allowed, 1 if direction >= 0 else -1)
        if target is None:
            return False, 'Ningún fondo de la lista puede rotar (ocultos, con fallo o web desactivado).'
        try:
            accepted = apply_fn(screen, items[target])
        except (OSError, subprocess.TimeoutExpired):
            accepted = False
        if not accepted:
            return False, 'No se pudo aplicar el fondo.'
        entry.update(current_index=target, last_switch=now)
        config.atomic_write_json(config.PLAYLISTS_FILE, playlists)
        return True, items[target]


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
