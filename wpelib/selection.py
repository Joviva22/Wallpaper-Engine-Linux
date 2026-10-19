"""Fondos permitidos para cambios automáticos (bandeja y rotación)."""
from . import config


def ineligible_reasons():
    """{id: motivo} de cada wallpaper instalado que NO puede entrar en una rotación o en el aleatorio."""
    hidden = config.load_hidden_ids()
    broken = config.load_known_bad()
    web_allowed = config.web_wallpapers_allowed()
    items = config.load_wallpapers()
    reasons = {}
    for item in items:
        wid = item['id']
        dependency = item.get('dependency')
        if not wid.isdigit():
            reasons[wid] = 'id no válido'
        elif wid in hidden:
            reasons[wid] = 'está oculto'
        elif wid in broken:
            reasons[wid] = 'está marcado como fallo conocido'
        elif dependency and (dependency in hidden or dependency in broken):
            reasons[wid] = 'depende de un fondo oculto o con fallo'
        elif item.get('preset'):
            # Los presets necesitan resolver también sus overrides antes de aplicarlos.
            reasons[wid] = 'es un preset'
        elif item['type'] == 'Web' and not web_allowed:
            reasons[wid] = 'los fondos web están desactivados'
        elif item['type'] not in ('Scene', 'Video', 'Web'):
            reasons[wid] = 'tipo no soportado'
    return reasons, {item['id'] for item in items}


def eligible_ids():
    reasons, installed = ineligible_reasons()
    return installed - set(reasons)


def playlist_problems(ids):
    """{id: motivo} de los fondos de `ids` que la rotación se saltará."""
    reasons, installed = ineligible_reasons()
    return {wid: ('no está instalado' if wid not in installed else reasons[wid])
            for wid in ids if wid not in installed or wid in reasons}
