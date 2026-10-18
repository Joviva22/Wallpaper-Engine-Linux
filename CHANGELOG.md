# Cambios

Registro de cambios del proyecto. El repositorio todavía no tiene versiones etiquetadas;
las entradas se agrupan por fecha hasta que se publique la primera (`v0.1.0`).

## 2026-10-18

### Corregido
- Los archivos de estado se escriben de forma atómica (archivo temporal + `rename`, permisos
  600) y los JSON ilegibles se apartan como `.corrupt` en vez de sobrescribirse.
- Los registros del motor se rotan; la configuración queda en `700`/`600`.
- Instancia única para el demonio de rotación y la bandeja; el lock de instancia ya no se
  hereda a los procesos hijos.
- `playlists.json` se guarda bajo un lock compartido con el demonio, conservando su progreso.
- `wallpaperengine-apply` pasa de bash a Python (`wpelib/apply.py`): vigilante por pantalla,
  detección de fallos fiable y reparación automática de wallpapers con el bug conocido de
  `scene.json`.
- Reparaciones serializadas por wallpaper, con copias de seguridad atómicas.
- Normalización de propiedades `combo`/`slider` inválidas en `project.json` (arreglaba dos
  wallpapers web que se cerraban al arrancar).
- Validación de id y nombre de pantalla en `apply`; descargas de miniaturas con límite de
  tiempo y tamaño; la API key no aparece en los mensajes de error.
- La velocidad `--speed` solo se usa si el motor la soporta.

### Añadido
- Clasificación de wallpapers (`wpelib/classify.py`): tipo, clasificación y etiquetas
  normalizados, herencia en presets y filtro «Tipo» en la interfaz.
- Motor parcheado (`patches/`, `scripts/build-engine.sh`): corrige los wallpapers web en
  negro (#629 upstream) y añade `--speed` para escenas y vídeo.
- Motor parcheado: propiedades de usuario para wallpapers web (arregla el fondo de los Nikke) y mejoras de SceneScript en textos (`patches/0004`, `0005`).
- Luces de escena en el motor parcheado (`patches/0003`): puntuales, focos y direccionales.
- Wallpapers web desactivados por defecto, con confirmación explícita (`allow_web`).
- `uninstall.sh`; `install.sh` pide confirmación antes de usar `sudo`.
- Pruebas automáticas (`python3 -m unittest discover -s tests -t .`).

### Cambiado
- El repositorio pasa a llamarse `Wallpaper-Engine-Linux` en GitHub.
