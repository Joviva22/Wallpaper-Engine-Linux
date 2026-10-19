"""Rotación coordinada con la GUI y con la selección automática compartida."""
import math
import os
import random
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


HISTORY_LIMIT = 30
MODES = ("order", "random")


def _history(entry):
    return [w for w in entry.get('history', []) if isinstance(w, str)] if isinstance(entry.get('history'), list) else []


def choose(entry, allowed, direction=1, rnd=random):
    """Decide a qué fondo pasar. Devuelve (indice, id, bolsa_restante) o None.

    - En orden: el siguiente/anterior de la lista que pueda rotar.
    - Aleatorio (mode="random"): sin repetir hasta haber pasado por todos (`bag` guarda los que faltan en
      la ronda) y sin repetir nunca el actual en el cambio de una ronda a otra.
    - Hacia atrás en aleatorio: vuelve por el historial real, no por la lista."""
    items = entry.get('items')
    if not isinstance(items, list) or not items:
        return None
    index = int(number(entry.get('current_index'), 0)) % len(items)
    current = items[index]
    if entry.get('mode') == 'random':
        if direction < 0:
            for wid in reversed(_history(entry)[:-1]):
                if wid in allowed and wid in items:
                    return items.index(wid), wid, None
        else:
            playable = list(dict.fromkeys(w for w in items if isinstance(w, str) and w in allowed))
            if not playable:
                return None
            bag = [w for w in entry.get('bag', []) if w in playable and w != current]
            if not bag:
                bag = [w for w in playable if w != current] or playable
            wid = rnd.choice(bag)
            return items.index(wid), wid, [w for w in bag if w != wid]
    target = pick(items, index, allowed, 1 if direction >= 0 else -1)
    return None if target is None else (target, items[target], None)


def commit(entry, index, wid, now, direction=1, bag=None):
    """Apunta un cambio aceptado: índice, hora, historial (con el actual al final) y bolsa de la ronda."""
    history = _history(entry)
    if direction < 0 and wid in history[:-1]:
        # se vuelve atrás por el historial: se descarta lo posterior a ese fondo
        history = history[:len(history) - 1 - history[:-1][::-1].index(wid)]
    else:
        history.append(wid)
    entry.update(current_index=index, last_switch=now, history=history[-HISTORY_LIMIT:])
    if bag is not None:
        entry['bag'] = bag


def tick(now=None, apply_fn=None, rnd=random):
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
            if not isinstance(entry.get('items'), list) or not entry['items']:
                continue
            interval = max(1, number(entry.get('interval_minutes'), 30)) * 60
            if now - number(entry.get('last_switch'), 0) < interval:
                continue
            target = choose(entry, allowed, 1, rnd)
            if target is None:
                continue
            try:
                accepted = apply_fn(screen, target[1])
            except (OSError, subprocess.TimeoutExpired):
                accepted = False
            if accepted:
                commit(entry, target[0], target[1], now, 1, target[2])
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
    info = {'mode': 'random' if entry.get('mode') == 'random' else 'order', 'history': _history(entry)[-6:],
            'enabled': entry.get('enabled') is True, 'paused': _paused(), 'items': len(items),
            'playable': sum(1 for w in items if w in allowed), 'current': None, 'next': None, 'seconds_left': None}
    if not items:
        return info
    info['can_rotate'] = False
    info['current'] = items[index % len(items)]
    # En aleatorio el siguiente no se conoce hasta que toca: solo se sabe si hay alguno que pueda salir.
    nxt = pick(items, index, allowed)
    info['next'] = None if nxt is None else (None if info['mode'] == 'random' else items[nxt])
    info['can_rotate'] = nxt is not None
    if info['enabled'] and not info['paused'] and info['can_rotate']:
        interval = max(1, number(entry.get('interval_minutes'), 30)) * 60
        info['seconds_left'] = max(0, int(number(entry.get('last_switch'), 0) + interval - now))
    return info


def step(screen, direction=1, now=None, apply_fn=None, rnd=random):
    """Pasa ya al siguiente (1) o al anterior (-1) fondo, aunque la rotación esté desactivada o en pausa, y
    reinicia la cuenta atrás. Devuelve (True, id) o (False, motivo)."""
    now = time.time() if now is None else now
    apply_fn = apply_fn or _default_apply
    allowed = eligible_ids()
    direction = 1 if direction >= 0 else -1
    with config.FileLock(config.PLAYLISTS_LOCK):
        playlists = config.load_playlists()
        entry = playlists.get(screen)
        items = entry.get('items') if isinstance(entry, dict) else None
        if not isinstance(items, list) or not items:
            return False, 'La lista de rotación está vacía.'
        target = choose(entry, allowed, direction, rnd)
        if target is None:
            return False, 'Ningún fondo de la lista puede rotar (ocultos, con fallo o web desactivado).'
        try:
            accepted = apply_fn(screen, target[1])
        except (OSError, subprocess.TimeoutExpired):
            accepted = False
        if not accepted:
            return False, 'No se pudo aplicar el fondo.'
        commit(entry, target[0], target[1], now, direction, target[2])
        config.atomic_write_json(config.PLAYLISTS_FILE, playlists)
        return True, target[1]


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
