# Elegir Fondo · Wallpaper Engine para Linux

Aplicación GTK3 para gestionar fondos de pantalla de Wallpaper Engine en Linux.
Utiliza [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine)
para reproducir los fondos y permite elegir uno distinto para cada monitor.

El repositorio se llama **Wallpaper-Engine-Linux**. Los comandos conservan el
nombre `wallpaperengine-picker` y el lanzador del escritorio aparece como
**Elegir Fondo (Wallpaper Engine)**.

## Funciones

- Biblioteca con búsqueda, filtros, favoritos, recientes y fondos ocultos.
- Miniaturas panorámicas 16:9, con relleno difuminado que conserva la vista previa completa.
- Asignación por monitor, vista previa y personalización de las opciones del fondo.
- Escalado, audio, volumen y velocidad agrupados en **Reproducción**.
- Velocidades ×1, ×1,5, ×2, ×3 y ×4 para escenas y vídeos con el motor parcheado.
- Búsqueda en Steam Workshop y descarga mediante `steamcmd`.
- Rotación automática por monitor, icono de bandeja y restauración al iniciar sesión.
- Detección de fallos y reparaciones de incompatibilidades conocidas, con copia del original.

La compatibilidad depende del motor y del contenido de cada fondo. Que una escena
arranque no garantiza que todas sus luces, scripts o efectos funcionen como en Windows.

## Requisitos

Necesitas Python 3, GTK3 con PyGObject, Pillow, Steam y el motor
`linux-wallpaperengine`. Para reproducir los fondos hacen falta los recursos de
**Wallpaper Engine**, instalado en Steam (aplicación `431960`), y contenido descargado
del Workshop. La descarga integrada necesita además `steamcmd`; la búsqueda requiere
una clave de la Steam Web API.

El instalador contempla estas dependencias según el gestor de paquetes:

| Componente | Arch/CachyOS | Debian/Ubuntu | Fedora | openSUSE |
|---|---|---|---|---|
| Python y GTK3 | `python`, `python-gobject`, `gtk3` | `python3`, `python3-gi`, `gir1.2-gtk-3.0` | `python3`, `python3-gobject`, `gtk3` | `python3`, `python3-gobject`, `typelib-1_0-Gtk-3_0`, `gtk3` |
| Miniaturas | `python-pillow` | `python3-pil` | `python3-pillow` | `python3-Pillow` |
| JSON | `jq` | `jq` | `jq` | `jq` |
| Detección de monitores | `xorg-xrandr` | `x11-xserver-utils` | `xorg-x11-server-utils` | `xrandr` |
| Steam | `steam` | `steam` | `steam` | `steam` |

Los nombres son los que utiliza [install.sh](install.sh); la disponibilidad depende
de los repositorios habilitados. El entorno de referencia es CachyOS/Arch con KDE Plasma
y Wayland. Las demás distribuciones requieren comprobar sus dependencias y el motor.

En Arch, el instalador puede obtener `linux-wallpaperengine-git` y `steamcmd` desde AUR
mediante `paru` o `yay`. En otras distribuciones debes preparar el motor antes de ejecutar
el instalador. En Debian/Ubuntu, el intento de instalar `steamcmd` también puede modificar
la arquitectura y los repositorios mediante `sudo`. En Fedora/openSUSE, prepara `steamcmd`
por separado si quieres usar la descarga integrada.

## Instalación

```bash
git clone https://github.com/Joviva22/Wallpaper-Engine-Linux.git ~/wallpaperengine-picker
cd ~/wallpaperengine-picker
./install.sh
```

El instalador comprueba las dependencias, detecta la biblioteca de Steam y crea:

- Los comandos `wallpaperengine-picker`, `wallpaperengine-apply`,
  `wallpaperengine-rotate`, `wallpaperengine-tray` y `wallpaperengine-autostart`
  en `~/.local/bin` mediante enlaces al repositorio.
- El lanzador **Elegir Fondo (Wallpaper Engine)** en el menú de aplicaciones.
- Entradas de inicio automático para restaurar los fondos, gestionar la rotación
  y mostrar el icono de bandeja.

En una terminal interactiva pide confirmación antes de sus comandos con `sudo`.
`./install.sh --yes` omite esa confirmación; no elimina los requisitos del sistema.

Comprueba que `~/.local/bin` esté en tu `PATH`. Para la sesión actual:

```bash
export PATH="$HOME/.local/bin:$PATH"
wallpaperengine-picker
```

Los enlaces apuntan a esta carpeta: consérvala después de instalar.

### Motor parcheado

Los parches incluidos corrigen el renderizado de fondos web y añaden `--speed`
para escenas y vídeos. Para compilar e instalar el motor en tu carpeta de usuario:

```bash
./scripts/build-engine.sh
```

Necesitas las herramientas y dependencias de desarrollo del motor. El script descarga
sus fuentes y CEF, aplica [patches/](patches/) e instala el resultado en
`~/.local/opt/linux-wallpaperengine`, sin sustituir el paquete del sistema.
La primera compilación puede tardar y requiere espacio para fuentes y dependencias.
Utiliza un clon de compilación dedicado: el script restablece su fuente al commit base.

La aplicación prefiere ese motor local cuando existe. Si solo tienes el motor local y
`install.sh` no lo encuentra, añade su lanzador al `PATH` antes de instalar:

```bash
export PATH="$HOME/.local/opt/linux-wallpaperengine/bin:$PATH"
./install.sh
```

El selector de velocidad se desactiva cuando el motor disponible no anuncia `--speed`.
Los parches de este repositorio no representan soporte completo de todas las funciones
de Wallpaper Engine; consulta [Compatibilidad y reparaciones](#compatibilidad-y-reparaciones).

### Actualización y desinstalación

Para actualizar una copia sin cambios locales pendientes:

```bash
cd ~/wallpaperengine-picker
git pull
```

Después cierra y vuelve a abrir la aplicación. Los enlaces siguen apuntando al repositorio,
así que normalmente no necesitas reinstalar. Los cambios del motor requieren recompilarlo.

```bash
./uninstall.sh
```

La desinstalación quita los enlaces, el lanzador y las entradas de inicio automático,
y trata de detener los procesos de la aplicación. Conserva la configuración, la caché,
los fondos, el repositorio y el motor local. `./uninstall.sh --purge` también borra
la configuración y la caché de esta aplicación.

## Uso

Abre **Elegir Fondo (Wallpaper Engine)** desde el menú o ejecuta:

```bash
wallpaperengine-picker
```

1. Selecciona el monitor en la barra lateral o en **Monitor activo**.
2. Busca un fondo en la biblioteca.
3. Haz doble clic para aplicarlo, o usa **Asignar** en su panel de detalle.
4. Abre **Reproducción** para ajustar escalado, audio, volumen o velocidad del monitor activo.

Cada monitor utiliza su propio proceso del motor. Cambiar un fondo reinicia el proceso
de ese monitor, sin reiniciar los de las demás pantallas.

### Biblioteca y controles

La barra lateral ofrece **Biblioteca**, **Favoritos**, **Recientes**, **Animados**,
**Ocultos**, **Workshop**, los monitores y **Ajustes**.

- **Animados** filtra los tipos Vídeo y Web. Una escena puede tener movimiento y no aparecer
  en esa pestaña: su tipo no indica de forma fiable si está animada.
- **Filtros** combina etiquetas, clasificación de contenido y tipo. Las etiquetas deben
  coincidir todas; basta con coincidir con una de las clasificaciones seleccionadas.
- El corazón marca un favorito. La insignia de asignación identifica el fondo del monitor activo.
- Al seleccionar una tarjeta se abre el panel de detalle, con vista previa, información,
  **Personalizar** y otras acciones.
- El clic derecho o el botón `…` permiten asignar a otro monitor, añadir a la rotación,
  ocultar o desuscribirse. La barra inferior reúne las acciones en lote y **Actualizar**.

| Atajo | Acción |
|---|---|
| `Ctrl+F` o `Ctrl+K` | Activar el buscador |
| `Esc` | Vaciar la búsqueda si tiene texto |
| `Supr` | Ocultar la selección |

### Personalización, reproducción y rotación

**Personalizar** muestra las propiedades que define el autor del fondo: colores, texto,
interruptores, valores numéricos y listas. Las propiedades ligadas a la visibilidad de capas
se agrupan en **CAPAS** cuando se pueden identificar. Los cambios se guardan por fondo
y se pasan al motor; las interacciones y sus límites dependen de la escena y del motor.

En **Reproducción**, **Rellenar** recorta para ocupar la pantalla, **Ajustar** conserva
el encuadre completo y **Estirar** adapta la imagen a sus dimensiones. También puedes usar
el modo predeterminado de la escena. Estos ajustes se guardan por monitor.

El audio está silenciado por defecto. El altavoz y el volumen controlan el sonido generado
por el fondo. El análisis del audio del sistema utilizado por visualizadores es independiente,
aunque la reacción efectiva depende del soporte del motor y del efecto.

**Velocidad** ofrece ×1, ×1,5, ×2, ×3 y ×4 con el motor parcheado. Cambia la reproducción
del vídeo o el reloj de la escena; no garantiza que todos los subsistemas de una escena
se aceleren del mismo modo.

En **Rotación**, elige un monitor, añade y ordena sus fondos, activa la rotación y ajusta
el intervalo. El servicio en segundo plano revisa las listas cada 30 segundos.
Asignar manualmente un fondo desactiva la rotación de ese monitor. La selección automática
excluye fondos ocultos, fallos conocidos y fondos web.

El icono de bandeja permite abrir la aplicación, elegir fondos aleatorios y pausar o
reanudar la rotación. Su visibilidad depende del escritorio y del soporte de indicadores.

### Fondos ocultos y eliminación

Puedes proteger **Ocultos** y **Mostrar ocultos** con una contraseña desde **Ajustes**.
Se guarda mediante PBKDF2-HMAC-SHA256 con una sal aleatoria; los archivos de los fondos
no se cifran. Es una barrera de acceso dentro de la interfaz.

**Desuscribirse** elimina el contenido local del fondo. Para cancelar también la suscripción
de tu cuenta, completa la operación en Steam mediante la opción de abrir su página.
Borrar solo la copia local no cancela por sí mismo la suscripción del servidor.

### Steam Workshop

Desde **Workshop** puedes buscar, filtrar y marcar favoritos. Para buscar mediante la API,
configura tu clave cuando la aplicación la solicite. Puedes obtenerla en
[Steam Web API Key](https://steamcommunity.com/dev/apikey).
La clave se guarda en `config.json`, con permisos restringidos; no la compartas en capturas
ni en registros públicos.

**Descargar** utiliza `steamcmd` con acceso anónimo. Si un contenido rechaza esa descarga,
usa **Ir a Steam** para suscribirte con tu cuenta y después pulsa **Actualizar**.
Sin clave de API puedes utilizar la opción de abrir el Workshop en Steam.

### Fondos web

Están desactivados por defecto. La aplicación exige permiso explícito antes de ejecutar
su HTML y JavaScript y permite revocarlo desde el menú de acciones en lote.
El motor puede ejecutar CEF sin sandbox; utiliza fondos de confianza.
La rotación y la selección aleatoria excluyen los fondos web incluso cuando están permitidos.

## Compatibilidad y reparaciones

La aplicación registra los arranques fallidos y las terminaciones inesperadas del motor.
Una marca de **Fallo conocido** identifica esos casos; no detecta por sí sola todos los
problemas visuales o de scripts de una escena que sigue ejecutándose.

El panel de detalle ofrece **Reparar fallo conocido** cuando corresponde. El menú `⋮`
incluye **Reparar toda la biblioteca**. El reparador reconoce, entre otros casos:

- Formatos incompatibles de propiedades y del `padding` de texto.
- Determinados recursos de efectos interactivos que faltan o necesitan adaptación.
- Versiones conocidas de shaders de barras de audio, onda, FXAA, osciloscopio,
  coordenadas y movimiento de ojos.

Las correcciones de shaders comprueban el nombre del recurso y su SHA256. Se reutilizan
entre fondos que contienen la misma versión conocida, aunque cambie el ID del efecto.
Una versión distinta necesita revisión antes de modificarla.

Antes de modificar un paquete o proyecto se guarda `scene.pkg.bak_original` o
`project.json.bak_original`; una copia ya existente se conserva. Las escrituras son
atómicas y las reparaciones se coordinan mediante locks. Vuelve a aplicar el fondo
para cargar los recursos corregidos.

Una reparación no certifica que todo el fondo funcione. Quedan casos que necesitan cambios
del motor: luces, texturas configurables, funciones de SceneScript y algunas escenas con
proyección incompatible. No se sustituyen recursos arbitrariamente para ocultar esos fallos.

Puedes consultar [el informe de shaders](audit/compatibility/SHADERS.md) y
[los casos de scripts](audit/scripts/README.md) para ver las comprobaciones realizadas,
las limitaciones y los fallos pendientes. Los informes describen la versión probada;
no garantizan el resultado de cualquier fondo o versión futura.

## Configuración y registros

Los datos se guardan en `~/.config/wallpaperengine-picker/`:

| Archivo | Contenido |
|---|---|
| `config.json` | Biblioteca de Steam, clave de API y permiso `allow_web` |
| `current.json` | Fondo asignado a cada monitor |
| `scaling.json`, `audio.json`, `speed.json` | Ajustes de reproducción por monitor |
| `properties.json` | Personalización guardada por fondo |
| `favorites.json`, `recents.json` | Favoritos e historial reciente |
| `hidden.json`, `hidden_lock.json` | Fondos ocultos y protección de su acceso |
| `ui_state.json` | Estado de la ventana, filtros y selección de monitor |
| `playlists.json`, `rotation_paused` | Listas y pausa de la rotación |
| `known_bad.json` | Fallos detectados del motor |
| `wallpaperengine_PANTALLA.log` | Registro del motor de cada monitor |
| `pid_PANTALLA.pid`, `status_PANTALLA.json` | Proceso y estado de aplicación por monitor |

Los registros del motor tienen un tamaño acotado y se rotan. Las miniaturas se guardan
en `~/.cache/wallpaperengine-picker/` y se regeneran cuando hace falta.
Si la biblioteca detectada no es la correcta, revisa `steam_library` en `config.json`.

## Desarrollo y pruebas

La aplicación está en [wpelib/](wpelib/); [bin/](bin/) contiene los lanzadores.
[tests/](tests/) reúne las pruebas y [audit/](audit/) los diagnósticos reproducibles.

Desde la raíz del repositorio:

```bash
python3 -W error::ResourceWarning -m unittest discover -s tests -t .
```

Las pruebas usan configuración temporal. Algunas necesitan abrir un servidor HTTP local;
los ensayos gráficos y del motor requieren una sesión gráfica y se ejecutan por separado.

## Licencia

La licencia declarada de este proyecto es MIT. El motor tiene su propia licencia;
los fondos del Workshop pertenecen a sus respectivos autores.
