"""Fondos permitidos para cambios automáticos (bandeja y rotación)."""
from . import config


def eligible_ids():
    hidden = config.load_hidden_ids()
    broken = config.load_known_bad()
    items = config.load_wallpapers()
    web_allowed = config.web_wallpapers_allowed()
    allowed = set()
    for item in items:
        wid = item['id']
        dependency = item.get('dependency')
        if not wid.isdigit() or wid in hidden or wid in broken:
            continue
        if dependency and (dependency in hidden or dependency in broken):
            continue
        # Los fondos web solo entran si el usuario los ha permitido (el motor parcheado ya los renderiza).
        # Los presets necesitan resolver también sus overrides antes de aplicarlos.
        kinds = ('Scene', 'Video', 'Web') if web_allowed else ('Scene', 'Video')
        if item['type'] not in kinds or item.get('preset'):
            continue
        allowed.add(wid)
    return allowed
