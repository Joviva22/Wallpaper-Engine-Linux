# wallpaperengine-picker

Selector grafico de fondos de pantalla animados para Linux, basado en
[linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine), con:

- Interfaz con **sidebar + cuadricula + panel de detalle** (Biblioteca / Favoritos / Recientes
  / Animados / Workshop), miniaturas reales en formato cuadrado (1:1), y una tarjeta por wallpaper con
  favorito, insignias y acciones al pasar el raton.
- Asignacion de un wallpaper **distinto por cada monitor**, con vista previa grande, menu
  contextual, y atajos de teclado.
- Filtros combinables por titulo, etiqueta (Y) y clasificacion de contenido (O) — Everyone /
  Questionable / Mature.
- Busqueda y descarga de nuevos wallpapers **directamente desde el Workshop de Steam**, usando
  la Steam Web API y `steamcmd` (sin necesidad de abrir el cliente de Steam), con la misma
  interfaz de sidebar/cuadricula/detalle.
- Favoritos y "Recientes" (historial de lo ultimo aplicado), ocultar sin borrar, y
  desuscribirse (borra local + opcion de completar el unsubscribe real en Steam).
- Rotacion automatica de wallpapers por pantalla (con presets de intervalo, rellenar con
  favoritos, orden aleatorio) mediante un demonio en segundo plano.
- Icono de bandeja del sistema con accesos rapidos, y deteccion automatica de wallpapers que
  hacen crashear el motor.
- Autostart en KDE Plasma: recuerda la ultima configuracion por pantalla y la reaplica al
  iniciar sesion.

Probado en CachyOS/Arch Linux con KDE Plasma (Wayland) y una GPU NVIDIA. `install.sh` tambien
detecta e instala dependencias en Debian/Ubuntu (`apt`), Fedora (`dnf`) y openSUSE (`zypper`),
con una salvedad: el motor `linux-wallpaperengine` solo tiene paquete listo para instalar en
Arch (AUR); en el resto hay que compilarlo desde sus fuentes (ver enlace mas abajo) antes de
correr `install.sh`.

## Como funciona

`linux-wallpaperengine` es el motor que renderiza las escenas `.pkg`/`scene.json` del
Workshop de Wallpaper Engine (app de Steam `431960`). Este proyecto añade una interfaz
grafica (GTK3) alrededor de ese motor para:

1. Detectar automaticamente donde tienes instalada tu biblioteca de Steam (lee
   `libraryfolders.vdf`, igual que hace el propio Steam).
2. Listar los wallpapers que ya tienes descargados (suscritos via Steam) con sus miniaturas.
3. Permitirte asignar un wallpaper a cada monitor conectado y lanzarlos con un solo proceso
   de `linux-wallpaperengine`.
4. Opcionalmente, buscar mas wallpapers en el Workshop sin salir de la app y descargarlos con
   `steamcmd`.

## Requisitos

`install.sh` detecta tu gestor de paquetes (`pacman`, `apt`, `dnf` o `zypper`) e instala solo
lo que falte. Equivalencias por distro:

| Para que se usa | Arch (`pacman`/AUR) | Debian/Ubuntu (`apt`) | Fedora (`dnf`) | openSUSE (`zypper`) |
|---|---|---|---|---|
| Motor que renderiza los wallpapers | `linux-wallpaperengine-git` (AUR) | *sin paquete, compilar* | *sin paquete, compilar* | *sin paquete, compilar* |
| Cliente de Steam | `steam` | `steam` | `steam` | `steam` |
| Descargar del Workshop sin abrir Steam | `steamcmd` (AUR) | `steamcmd` | *sin paquete* | *sin paquete* |
| Interfaz grafica (GTK3 desde Python) | `python-gobject` `gtk3` | `python3-gi` `gir1.2-gtk-3.0` | `python3-gobject` `gtk3` | `python3-gobject` `typelib-1_0-Gtk-3_0` `gtk3` |
| Generar las miniaturas | `python-pillow` | `python3-pil` | `python3-pillow` | `python3-Pillow` |
| Manejo de JSON en los scripts de shell | `jq` | `jq` | `jq` | `jq` |
| Detectar monitores conectados | `xorg-xrandr` | `x11-xserver-utils` | `xorg-x11-server-utils` | `xrandr` |
| Icono de bandeja (opcional) | `libayatana-appindicator` | `gir1.2-ayatanaappindicator3-0.1` | `libappindicator-gtk3` | `typelib-1_0-AyatanaAppIndicator3-0_1` |

Fuera de Arch, `linux-wallpaperengine` no tiene paquete: compilalo desde
[sus fuentes](https://github.com/Almamu/linux-wallpaperengine) antes de correr `install.sh`
(y en Fedora/openSUSE lo mismo con `steamcmd`, ver
[SteamCMD](https://developer.valvesoftware.com/wiki/SteamCMD); sin el sigue funcionando la
opcion **"Abrir Workshop en Steam"** para suscribirte manualmente).

Ademas necesitas tener **Wallpaper Engine** (app 431960) instalada en Steam (es de pago,
~4€) y al menos un wallpaper suscrito desde el Workshop, o usar la busqueda integrada de
esta app para descargar uno.

## Estructura del proyecto

```
bin/
  wallpaperengine-picker       # lanzador delgado (resuelve el repo y llama a wpelib)
  wallpaperengine-apply        # aplica wallpapers, un proceso por pantalla
  wallpaperengine-rotate       # demonio de rotacion automatica
  wallpaperengine-tray         # icono de bandeja
  wallpaperengine-common.sh    # deteccion de la biblioteca de Steam (bash)
wpelib/                        # la app en Python, en modulos:
  config.py                    # config, deteccion de Steam, estado persistido
  steam_api.py                 # busqueda/descarga via Steam Web API + steamcmd
  ui.py                        # tema CSS y widgets reutilizables
  workshop_window.py           # ventana de busqueda del Workshop
  playlist_window.py           # ventana de listas de rotacion
  properties.py                # lee --list-properties de un wallpaper
  properties_window.py         # dialogo "Personalizar" (propiedades del wallpaper)
  repair.py                    # arregla incompatibilidades conocidas del .pkg
  vendor_effects/               # shaders reales de xray/cursorripple usados por repair.py
  main_window.py               # ventana principal
```

## Instalacion

```bash
git clone <url-de-este-repo> ~/wallpaperengine-picker
cd ~/wallpaperengine-picker
./install.sh
```

`install.sh`:

- Detecta tu gestor de paquetes (`pacman`, `apt`, `dnf` o `zypper`) e instala las
  dependencias que falten con el (pidiendo `sudo`); en Arch usa ademas `paru`/`yay` para lo
  que viene de AUR (`linux-wallpaperengine-git`, `steamcmd`).
- Detecta tu biblioteca de Steam (funciona aunque Wallpaper Engine todavia no este instalada
  ni tengas ningun wallpaper suscrito, siempre que Steam mismo ya se haya abierto una vez).
- Crea symlinks de `bin/wallpaperengine-apply` y `bin/wallpaperengine-picker` en
  `~/.local/bin` (asegurate de que este directorio este en tu `PATH`).
- Crea un lanzador en el menu de aplicaciones: **"Elegir Fondo (Wallpaper Engine)"**.
- Crea una entrada de autostart de KDE que reaplica la ultima configuracion al iniciar
  sesion (solo si ya has aplicado un wallpaper al menos una vez).

Para actualizar despues de hacer `git pull`, no hace falta reinstalar nada: los symlinks
apuntan al repo.

## Uso

Lanza la app desde el menu de aplicaciones ("Elegir Fondo (Wallpaper Engine)") o con:

```bash
wallpaperengine-picker
```

La ventana principal ("Fondos de pantalla") se organiza en tres zonas:

### Sidebar (izquierda)

- **Biblioteca / Favoritos / Recientes / Animados / Ocultos**: pestañas de navegacion.
  Biblioteca es la vista por defecto (todo lo descargado, sin lo oculto); Favoritos/Recientes/
  Animados tampoco muestran nunca los ocultos, ni siquiera si uno oculto esta marcado como
  favorito o es reciente; Animados filtra a wallpapers de tipo Video o Web (los unicos que
  Wallpaper Engine garantiza que se mueven — una escena "Scene" puede o no tener movimiento y
  no hay forma fiable de saberlo de antemano). Entrar en **Ocultos** pide la contraseña si hay
  una configurada (ver "Ocultos con contraseña" mas abajo).
- **Workshop**: abre la ventana de busqueda del Workshop (ver mas abajo).
- **Monitores**: lista de pantallas conectadas, cada una con el titulo del wallpaper que
  tiene puesto ahora mismo. Clicar una la marca como "pantalla activa" (a la que se aplicara
  el siguiente wallpaper que elijas); lo mismo hacen los chips "MONITOR ACTIVO" arriba del
  todo en el panel central. Junto a los chips hay un combo **"Escalado"** (Rellenar / Ajustar
  / Estirar / Por defecto de la escena) que se guarda por pantalla y reaplica el wallpaper
  actual al cambiarlo — usa "Ajustar" si un wallpaper concreto se ve recortado con "Rellenar".
- **Ajustes**: muestra la ruta detectada de tu biblioteca de Steam y donde se cachean las
  miniaturas, y da acceso a la contraseña de "Ocultos" (ver mas abajo).

### Panel central

- Buscador grande (`Ctrl+F` o `Ctrl+K` le da el foco, `Esc` lo vacia), un boton **"Filtros
  (N)"** que despliega etiquetas (deben coincidir todas) y clasificacion (basta una), y un
  combo de orden.
- Cada tarjeta muestra la miniatura en formato cuadrado (1:1), un corazon de favorito, una insignia si esta
  oculta o si crasheo el motor ("[⚠ Fallo conocido]"), y un check morado si es el wallpaper
  actual de la pantalla activa. Al pasar el raton aparecen botones de vista previa y asignar
  directamente sobre la miniatura; hay tambien un boton "..." que abre el mismo menu que el
  clic derecho (asignar a cada monitor, favorito, vista previa, anadir a rotacion,
  ocultar/mostrar, desuscribirse).
- Doble clic en una tarjeta la aplica de inmediato a la pantalla activa.
- Puedes seleccionar **varios wallpapers a la vez** (Ctrl+clic o arrastrando) y usar el menu
  de acciones en lote (icono "⋮" de la barra inferior) para ocultarlos/desuscribirlos juntos;
  `Supr` oculta la seleccion actual.
- Barra inferior: contador de resultados/seleccion, **"Mostrar ocultos"** (los incluye tambien
  dentro de "Biblioteca", ademas de en su propia pestaña — pide la contraseña igual que la
  pestaña "Ocultos" si hay una configurada), **"Rotacion"**, el menu de acciones en lote, y
  **"Actualizar"** (vuelve a leer la carpeta del Workshop, por si suscribiste algo nuevo desde
  Steam).

### Ocultos con contraseña

Puedes proteger el acceso a los wallpapers ocultos desde **Ajustes → "Proteger 'Ocultos' con
contraseña..."**. Una vez puesta, hace falta introducirla tanto para entrar en la pestaña
**Ocultos** como para activar la casilla **"Mostrar ocultos"** de la barra inferior — son los
dos unicos sitios desde los que se pueden ver, y ambos piden la contraseña por igual (si
solo se protegiera uno de los dos, el otro seria una forma trivial de saltarsela). Se pide
cada vez, en cada sesion de la app; no se guarda ni se recuerda un rato. Si cierras la
ventana estando en la pestaña Ocultos con contraseña puesta, al reabrir la app vuelve a
"Biblioteca" en vez de restaurar esa pestaña directamente, por el mismo motivo.

Se guarda con PBKDF2-HMAC-SHA256 + salt aleatorio en `hidden_lock.json` (permisos `0600`),
nunca la contraseña en texto plano; aun asi no es proteccion criptografica seria — quien
tenga acceso a tu carpeta de configuracion puede leer `hidden.json` directamente sin pasar
por la contraseña. Es una cortina simple para que nadie la vea de pasada, no un cifrado real.

### Panel de detalle (derecha)

Se despliega al seleccionar una tarjeta: vista previa grande, titulo, favorito, botones
"Asignar a `<pantalla activa>`" / "Vista previa" / "Anadir a rotacion" / "Personalizar" /
"Ocultar" / "Desuscribirse", y una seccion de informacion (tipo, categorias, clasificacion,
fecha de descarga) con las etiquetas del wallpaper debajo.

### Personalizar (propiedades del wallpaper)

Equivalente a la pestaña "Customize" de Wallpaper Engine en Windows: muchos wallpapers del
Workshop definen sus propias opciones (mostrar/ocultar un reloj, color de acento, velocidad
de una animacion, activar/desactivar reacciones al raton, texto personalizado...). El boton
"Personalizar" del panel de detalle lee esas opciones directamente del wallpaper con
`linux-wallpaperengine --list-properties` y las muestra como casillas, sliders, listas
desplegables, selector de color o campo de texto segun corresponda. Los cambios se guardan
por wallpaper en `properties.json` y se pasan al motor como `--set-property clave=valor` la
proxima vez que se aplica (si el wallpaper ya esta activo en alguna pantalla, se reaplica al
momento). No todos los wallpapers definen propiedades personalizables — si no tiene ninguna,
el dialogo lo indica. Que interaccion concreta hace cada propiedad (p.ej. si un elemento
desaparece al pasar el raton por encima) depende de como el autor haya diseñado la escena;
la app solo puede exponer y ajustar lo que el wallpaper ya trae definido, no añadir
comportamientos nuevos que no existan en el.

**Fijar una capa concreta.** Cuando un wallpaper tiene varias capas que se muestran/ocultan
segun una propiedad personalizable, el dialogo "Personalizar" las separa en una seccion
aparte, **CAPAS**, arriba del todo — son las mismas propiedades que antes aparecian
mezcladas con el resto, solo que agrupadas y explicadas para este caso de uso. Hay dos formas
en que Wallpaper Engine liga una capa a una propiedad, y la app soporta ambas:

- **Interruptor simple**: `"visible": {"user": "clave", "value": true|false}` — una casilla
  "Fijar siempre visible" (visto en los pares de video del efecto "xray" de Eclipse, o en
  variantes dia/noche que se activan con un booleano independiente por capa).
- **Grupo de opciones (combo)**: `"visible": {"user": {"condition": "N", "name": "clave"},
  ...}` — varias capas distintas comparten una unica propiedad tipo lista desplegable, cada
  una ligada a un valor concreto (p.ej. un wallpaper de Azur Lane con una propiedad "efecto
  climatico" que alterna entre capas de cerezo/nieve/lluvia/lluvia intensa). Estas se
  muestran como botones de opcion (radio): solo se puede fijar una a la vez, igual que
  decide el propio combo internamente.

Si dos capas son mutuamente excluyentes segun la logica interna del wallpaper (p.ej. un
script que solo deja una activa a la vez incluso si ambas casillas estan marcadas), fijar
ambas puede no comportarse como se espera — eso depende de como el autor programo esa logica,
no de la app.

### Buscar en el Workshop

La ventana de busqueda ("Workshop" en la sidebar) usa el mismo lenguaje visual: sidebar con
Etiquetas (deben coincidir todas), Clasificacion y Popularidad (Todo el tiempo / Hoy / Semana
/ Mes / Medio año / Año — mas votados o en tendencia segun la que elijas), un buscador grande
con paginacion junto a el, y una cuadricula de tarjetas identica a la de la biblioteca. El
tamaño del archivo y si ya lo tienes descargado se muestran como texto/insignia separados del
titulo (no mezclados como antes). Al seleccionar un resultado se abre el panel de detalle con
**"Ir a Steam"** (accion principal — deja que tu cuenta real se encargue, mas fiable) y
**"Descargar"** (usa `steamcmd` con login anonimo, ver mas abajo); tambien puedes marcar
resultados como favoritos antes de descargarlos. La pagina siguiente se precarga en segundo
plano para que "Pagina siguiente" sea practicamente instantaneo.

### Icono de bandeja

`wallpaperengine-tray` (autostart) añade un icono a la bandeja del sistema con accesos
rapidos sin abrir la ventana completa: wallpaper aleatorio por pantalla, pausar/reanudar la
rotacion automatica, y un enlace para abrir el selector completo. Usa
`libayatana-appindicator` si esta disponible; si no, cae a `Gtk.StatusIcon` (puede no
mostrarse en todos los escritorios).

### Desuscribirse y borrar

"Desuscribirse" borra el contenido local (y su cache de miniaturas) de los wallpapers
seleccionados y los quita de cualquier lista de rotacion. El login anonimo que usa la
descarga por API **no puede** desuscribir tu cuenta real de Steam (esa suscripcion vive en
el servidor, ligada a tu cuenta), asi que el dialogo te deja elegir "Borrar y abrir en
Steam" para completar el desuscribir de verdad alli si no quieres que se vuelva a
sincronizar mas adelante.

### Deteccion de wallpapers problematicos

Algunas escenas del Workshop hacen que `linux-wallpaperengine` termine con una excepcion
C++ no capturada (o un segfault) al intentar renderizarlas. Cada vez que se aplica un
wallpaper, `wallpaperengine-apply` vigila el proceso durante unos segundos: si muere con una
de esas señales tipicas, guarda el id en `known_bad.json` y la app lo marca como
"[⚠ Fallo conocido]" tanto en la lista local como en los resultados del Workshop. Si vuelves
a probar ese mismo id y esta vez no crashea, la marca se quita sola.

Cuando el wallpaper esta marcado, el panel de detalle muestra ademas un boton **"Reparar
fallo conocido"**. Investigando un caso real (crash con `[json.exception.type_error.302]
type must be number, but is string`, depurado con gdb hasta el codigo fuente de
`linux-wallpaperengine`) se confirmo que la causa era la propiedad `padding` de los objetos
de texto: algunos wallpapers la guardan como vector de dos componentes
(`"32.00000 32.00000"`, horizontal/vertical, igual que `scale` o `size`), pero el motor de
Linux solo soporta ahi un numero simple, y revienta al intentar leerla como tal. El boton
"Reparar" hace una copia de seguridad de `scene.pkg` (`scene.pkg.bak_original`, solo la
primera vez) y corrige ese campo en el sitio. No es un arreglo universal para cualquier
crash — solo cubre este patron concreto — pero cuando aplica, deja el wallpaper
utilizable sin depender de que el autor original lo actualice.

El menu de "Acciones en lote" (icono `⋮` de la barra inferior) tiene ademas **"Reparar
toda la biblioteca"**: revisa TODOS los wallpapers descargados (no solo los que ya se
hayan marcado como fallo conocido al intentarlos, por si alguno tiene el mismo problema y
todavia no se ha probado) y repara automaticamente los que encuentre, con el mismo
respaldo automatico por wallpaper. Se ejecuta en segundo plano (no bloquea la ventana) y
al terminar muestra cuantos de cuantos revisados se han corregido. Es la forma recomendada
de arreglar de golpe todos los wallpapers afectados por este patron concreto, incluidos los
que usan efectos interactivos con el raton o reactivos al audio — la reparacion no depende
del tipo de wallpaper, solo de si tiene ese campo mal formado.

Ademas, esta misma reparacion se intenta **automaticamente** justo despues de cada descarga
hecha desde la ventana "Workshop" de la app (antes de que llegues a probar el wallpaper por
primera vez), asi que en la mayoria de los casos ni siquiera hace falta ver el crash una vez
para que se corrija. Si el wallpaper ya se suscribio/descargo por fuera de la app (por
ejemplo, directamente desde el cliente de Steam), usa "Reparar toda la biblioteca" o el
boton individual "Reparar fallo conocido" tras el primer intento fallido.

**Efectos interactivos "xray" y "cursorripple" rotos por assets que faltan.** Estos dos
efectos nativos del motor (el genero "revelar al pasar el raton") pertenecen al grupo
"interactive" de Wallpaper Engine, y en esta version de `linux-wallpaperengine` para Linux
les faltan sus archivos (`materials/`, `shaders/*.frag/.vert`) en los assets globales del
motor — comprobado con los 3 efectos de ese grupo. La mayoria de wallpapers que los usan los
empaquetan ellos mismos dentro de su propio `scene.pkg` (asi no dependen de los assets
globales), pero si alguno no lo hace, falla con
`Cannot find requested file in any of the mountpoints: [...]xray.json`. El reparador
detecta esto (busca `effects/xray/effect.json` o `effects/cursorripple/effect.json`
referenciado en la escena sin sus shaders empaquetados) y copia dentro del `.pkg` los
archivos REALES de Wallpaper Engine — extraidos de wallpapers del Workshop que si los
traian consigo y verificados en este sistema (revisando el log de un proceso en produccion
real para "xray", y con una carga aislada para "cursorripple": ningun error de compilacion
GLSL) — guardados como plantilla en `wpelib/vendor_effects/`. No es una reimplementacion
propia del efecto, son los shaders originales del propio motor. Esta reparacion forma parte
del mismo `attempt_repair()`, asi que se aplica igual desde "Reparar fallo conocido",
"Reparar toda la biblioteca" y la reparacion automatica al descargar.

**Limitacion conocida sin arreglo todavia**: existe un segundo patron de incompatibilidad,
distinto al de `padding`, en el que `general.orthogonalprojection` viene como `null` en vez
de `{width, height}` (visto en "Wuhu Island" y "Cat with headphones on the roof" en pruebas
reales). A diferencia del bug de `padding`, rellenar ese campo con un valor por defecto evita
el error de carga pero **no** arregla el renderizado: la escena se queda en negro/gris,
probablemente porque esas escenas usan camara en perspectiva y no deberian depender de una
proyeccion ortografica en absoluto. Por eso este patron NO esta incluido en el reparador
automatico (daria una falsa sensacion de "arreglado" sin estarlo de verdad) — necesitaria
soporte real en el codigo del motor, no un parche de datos.

### Audio de los wallpapers

Por defecto los wallpapers se lanzan silenciados (mismo comportamiento que siempre ha
tenido la app). Cada pantalla tiene ahora, junto al combo "Escalado", un boton de altavoz y
un deslizador de volumen independientes: al activar el altavoz, esa pantalla deja de pasar
`--silent` al motor y pasa `--volume N` en su lugar, asi que el sonido o musica propios del
wallpaper (si los tiene) se reproducen. Los wallpapers con visualizador de audio (barras,
anillos que reaccionan a la musica...) reaccionan al audio del sistema independientemente de
si esa pantalla esta silenciada o no — `--silent` solo corta el sonido que el propio
wallpaper generaria, no la lectura del audio del sistema que usan esos efectos, que
`linux-wallpaperengine` controla con un flag totalmente distinto (`--no-audio-processing`)
que esta app nunca activa. El ajuste se guarda por pantalla en `audio.json`.

### Velocidad de reproduccion (x1.5 / x2 / x3 / x4)

Junto al combo "Escalado" y el control de audio hay un combo **"Velocidad"** para wallpapers
de video. Esto **no** es una funcion nativa de `linux-wallpaperengine` — el motor usa libmpv
para reproducir video pero nunca expone un flag para controlar su velocidad. Para poder
ofrecer esto se ha parcheado y recompilado el motor desde el codigo fuente
(github.com/Almamu/linux-wallpaperengine): se añadio un flag `--speed N` que llama a
`mpv_set_property(handle, "speed", MPV_FORMAT_DOUBLE, &N)`, siguiendo exactamente el mismo
patron que el motor ya usa para `--volume` (`GLPlayer::setVolume`). Verificado leyendo de
vuelta el valor con `mpv_get_property` en el propio proceso real: con `--speed 2.5` mpv
confirma internamente `speed=2.5`.

El binario y la libreria instalados en `/opt/linux-wallpaperengine/` fueron sustituidos por
esta version parcheada (con backup de los originales junto a ellos,
`*.bak_original`); si se reinstala el paquete `linux-wallpaperengine-git` de AUR, este flag
desaparecera hasta volver a aplicar el parche (el codigo fuente parcheado, con submodulos
inicializados, quedo clonado durante esta sesion). Como es un flag nuevo del motor y no algo
que dependa del wallpaper, solo tiene efecto en wallpapers de tipo Video (o con video
incrustado dentro de una escena); en un wallpaper sin ningun video no hace nada. El ajuste se
guarda por pantalla en `speed.json`, y solo se pasa `--speed` al motor cuando es distinto de
1.0 (por si en el futuro se reinstala una version del motor sin el parche, no romper el resto
de argumentos).

### Rotacion automatica de wallpapers

Cada pantalla puede tener, en vez de un unico wallpaper fijo, una lista de wallpapers que
van rotando solos cada cierto tiempo:

1. Pulsa **"Rotacion"** (barra inferior), elige la pantalla a configurar.
2. Anade wallpapers desde "Disponibles" a "Orden de rotacion" (boton "Anadir"), reordena con
   "Subir"/"Bajar" y quita los que no quieras con "Quitar". "Rellenar con favoritos" anade de
   golpe todo lo que tengas marcado con corazon; "Aleatorizar orden" baraja la lista actual.
3. Marca "Activar rotacion en esta pantalla" y ajusta el intervalo en minutos (o usa uno de
   los presets: 15 min / 30 min / 1 hora / 1 dia).
4. Pulsa "Guardar y aplicar": aplica el primer wallpaper de la lista de inmediato y guarda la
   configuracion en `~/.config/wallpaperengine-picker/playlists.json`.

Un demonio en segundo plano (`wallpaperengine-rotate`, instalado por `install.sh` como
autostart de KDE) revisa cada 30 segundos si toca avanzar alguna pantalla a su siguiente
wallpaper, asi que la rotacion sigue funcionando aunque cierres la ventana principal.
Asignar manualmente un wallpaper fijo a una pantalla (fuera de la ventana de rotacion)
desactiva automaticamente su rotacion, para que no se pisen entre si.

### Configurar la Steam Web API Key

La busqueda en el Workshop usa la API publica de Steam (`IPublishedFileService/QueryFiles`),
que requiere una API key gratuita asociada a tu cuenta. Si prefieres no configurarla, el
mismo dialogo que la pide tiene un boton **"Abrir Workshop en Steam"** que te lleva
directamente a la pagina del Workshop en Steam para buscar y suscribirte alli, sin usar la
API ni `steamcmd`.

1. Ve a <https://steamcommunity.com/dev/apikey> y genera una key (como dominio puedes poner
   `localhost`).
2. Pegala cuando la app te la pida al abrir "Workshop" desde la sidebar, **o** guardala tu
   mismo sin que pase por ningun chat/terminal compartido:

   ```bash
   mkdir -p ~/.config/wallpaperengine-picker
   python3 - <<'EOF'
   import json, os, getpass
   p = os.path.expanduser('~/.config/wallpaperengine-picker/config.json')
   cfg = json.load(open(p)) if os.path.exists(p) else {}
   cfg['steam_api_key'] = getpass.getpass('Pega tu Steam Web API Key: ').strip()
   json.dump(cfg, open(p, 'w'), indent=2)
   os.chmod(p, 0o600)
   print('Guardado.')
   EOF
   ```

La key se guarda en `~/.config/wallpaperengine-picker/config.json` (permisos `600`).

### Descarga via Workshop (como funciona por dentro)

La descarga usa `steamcmd` con login anonimo:

```bash
steamcmd +force_install_dir <tu_biblioteca_de_steam> \
         +login anonymous \
         +workshop_download_item 431960 <id_del_wallpaper> \
         +quit
```

Esto funciona para la mayoria del contenido del Workshop de Wallpaper Engine sin necesidad
de iniciar sesion con tu cuenta real. Si algun item en concreto no se puede descargar asi,
sigue pudiendo suscribirte a el desde el propio Steam (el boton "Actualizar" de la ventana
principal recogera cualquier wallpaper que hayas suscrito por ese medio).

## Configuracion

Todo el estado vive en `~/.config/wallpaperengine-picker/`:

- `config.json`: ruta detectada de tu biblioteca de Steam (`steam_library`) y tu API key
  (`steam_api_key`). Si tienes varias bibliotecas de Steam, edita `steam_library` a mano si
  la deteccion automatica elige la que no es.
- `current.json`: ultima asignacion aplicada, `{ "NOMBRE_PANTALLA": "id_wallpaper", ... }`.
  Es lo que usa el autostart para restaurar tu configuracion al iniciar sesion.
- `wallpaperengine_PANTALLA.log` y `pid_PANTALLA.pid` (uno por cada monitor): salida y PID del
  proceso `linux-wallpaperengine` de esa pantalla (util para ver por que un wallpaper concreto
  no carga o hace crashear el motor).
- `hidden.json`: lista de ids de wallpapers ocultos.
- `hidden_lock.json`: si existe, protege la pestaña "Ocultos" y la casilla "Mostrar ocultos"
  con contraseña — `{"salt": hex, "hash": hex}` (PBKDF2-HMAC-SHA256), nunca la contraseña en
  si. Sin este fichero, ninguno de los dos pide nada (comportamiento de siempre).
- `scaling.json`: modo de escalado por pantalla, `{ "PANTALLA": "fill"|"fit"|"stretch"|"default" }`
  ("fill", recorta para rellenar, si una pantalla no tiene entrada).
- `properties.json`: overrides guardados del panel "Personalizar", por wallpaper:
  `{ "id_wallpaper": { "clave_propiedad": "valor", ... } }`.
- `audio.json`: audio por pantalla, `{ "PANTALLA": {"muted": bool, "volume": 0-100} }`
  (silenciado si una pantalla no tiene entrada).
- `speed.json`: velocidad de reproduccion de video por pantalla, `{ "PANTALLA": 1.0-4.0 }`
  (1.0/normal si una pantalla no tiene entrada). Requiere el motor parcheado, ver la seccion
  "Velocidad de reproduccion" mas arriba.
- `favorites.json`: lista de ids marcados con favorito (compartida entre la biblioteca local
  y los resultados del Workshop).
- `recents.json`: ids aplicados recientemente, mas reciente primero (hasta 100), para la
  pestaña "Recientes".
- `ui_state.json`: pestaña, orden y filtro de clasificacion activos, y la pantalla activa —
  se restauran solos al reabrir la app.
- `playlists.json`: listas de rotacion por pantalla, `{ "PANTALLA": {"enabled": bool,
  "interval_minutes": N, "items": [id, ...], "current_index": N, "last_switch": epoch} }`.
  La edita la ventana "Rotacion..." y la lee el demonio `wallpaperengine-rotate`.
- `known_bad.json`: ids que hicieron crashear el motor, `{ "id": {"screen": ..., "detected_at":
  ...} }`. La escribe `wallpaperengine-apply`, la lee la app para marcarlos en la lista.
- `rotation_paused`: si existe (archivo vacio), el demonio de rotacion no avanza ninguna
  pantalla. Lo crea/borra el icono de bandeja al pulsar "Pausar/Reanudar rotacion".

Las miniaturas se cachean en `~/.cache/wallpaperengine-picker/` (se pueden borrar sin
problema, se regeneran solas).

## Notas y limitaciones

- Cada pantalla corre en su **propio proceso** `linux-wallpaperengine` (PID guardado en
  `~/.config/wallpaperengine-picker/pid_PANTALLA.pid`, log en `wallpaperengine_PANTALLA.log`).
  Esto aisla los fallos: algunas escenas del Workshop hacen crashear el motor (excepciones
  C++ no capturadas al parsear un `scene.json` incompatible); con procesos separados, solo se
  cae la pantalla afectada y las demas siguen funcionando. Cambiar el wallpaper de una
  pantalla solo reinicia el proceso de esa pantalla, sin tocar las demas.
- El reinicio del proceso de una pantalla esta protegido con `flock` por pantalla
  (`~/.config/wallpaperengine-picker/lock_PANTALLA.lock`). Sin esto, dos llamadas a
  `wallpaperengine-apply` casi simultaneas para la misma pantalla (p.ej. mover rapido el
  deslizador de volumen mientras la rotacion automatica tambien actua) podian leer el mismo
  PID "viejo" antes de que la otra lo actualizara y acabar con varios procesos
  `linux-wallpaperengine` vivos a la vez en la misma pantalla, agotando la VRAM
  (`CUDA_ERROR_OUT_OF_MEMORY`) — visto en produccion real, confirmado y corregido.
- La deteccion de crashes (`known_bad.json`) espera de verdad (`wait`) a que el proceso de
  cada pantalla termine y mira su codigo de salida real, en vez de solo buscar frases como
  "terminate called" en el log. Esto detecta tambien segfaults silenciosos que no imprimen
  ningun mensaje reconocible (visto en produccion: un wallpaper moria con
  `Segmentation fault` real, exit code 139, sin dejar ninguna traza de texto en el log, asi
  que el chequeo anterior nunca lo habria marcado). Un cambio deliberado de wallpaper mata al
  proceso viejo con `SIGTERM` (tambien un "codigo de salida por señal"), pero eso NO se marca
  como fallo — se distingue comprobando si el pidfile de esa pantalla sigue apuntando a ese
  proceso en el momento en que muere; si ya no coincide, fue un cambio a proposito.
- El escalado es configurable por pantalla (combo "Escalado", por defecto "Rellenar"); el
  `clamp` se deja fijo en `border` siempre. Si un wallpaper en concreto se ve mal incluso con
  "Ajustar", puede deberse a que la escena en si no esta pensada para tu resolucion/aspecto.
- Probado sobre Wayland (KWin) usando XWayland para `xrandr`; en un compositor puramente
  wlroots (Sway, Hyprland...) puedes pasar `--layer background` a `linux-wallpaperengine`
  directamente si lo necesitas (no expuesto aun en la interfaz).
- La pestaña "Animados" solo detecta tipos `Video`/`Web`; una escena `Scene` puede tener
  movimiento (parallax, particulas...) y no aparecera ahi porque `project.json` no expone
  ningun flag fiable de estatico/animado para ese tipo.
- No hay alternancia real cuadricula/lista, las etiquetas del panel de detalle son de solo
  lectura, y no se muestra la resolucion del wallpaper (Wallpaper Engine no la expone de
  forma fiable en `project.json`). La ventana no tiene una barra de titulo/logo propios;
  usa la del gestor de ventanas.

## Licencia

MIT. `linux-wallpaperengine` tiene su propia licencia (ver su repositorio); el contenido del
Workshop pertenece a sus respectivos autores.

## Tests

    python3 -m unittest discover -s tests -t .
