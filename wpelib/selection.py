"""Fondos permitidos para cambios automáticos (bandeja y rotación)."""
from . import config


def eligible_ids():
    hidden = config.load_hidden_ids()
    broken = config.load_known_bad()
    items = config.load_wallpapers()
    allowed = set()
    for item in items:
        wid = item['id']
        dependency = item.get('dependency')
        if not wid.isdigit() or wid in hidden or wid in broken:
            continue
        if dependency and (dependency in hidden or dependency in broken):
            continue
        # El backend web instalado tiene un fallo de renderizado pendiente.
        # Los presets necesitan resolver también sus overrides antes de aplicarlos.
        if item['type'] not in ('Scene', 'Video') or item.get('preset'):
            continue
        allowed.add(wid)
    return allowed
