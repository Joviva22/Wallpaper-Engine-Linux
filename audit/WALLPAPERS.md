# Inventario de errores de todos los wallpapers locales

Revisión: 2026-10-18T18:58:55.372091+02:00. Biblioteca: `/home/joviva/.local/share/Steam/steamapps/workshop/content/431960`.

Se revisaron **400 carpetas**: 253 scene, 116 video, 31 web.

La revisión lee `project.json`, la tabla y los límites de las entradas de `scene.pkg`, el JSON de escena, objetos de luz/texto, referencias de efectos y los logs conservados. Los vídeos se inspeccionaron con `ffprobe`. No se cambiaron fondos, paquetes ni configuración. No se aplicaron los 400 fondos al escritorio: los hallazgos estáticos describen incompatibilidades posibles o concretas de formato, mientras los logs son evidencia histórica y pueden corresponder a versiones anteriores del fondo o del motor. No detectar un error no garantiza aspecto visual correcto ni ausencia de errores de scripts.

**Vídeos:** 116 inspeccionados; 0 con error o sin pista; 0 con advertencias. Se comprobaron contenedor y pistas, sin decodificar cada fotograma.

## Distintos problemas detectados

| Código | Problema | Fondos afectados | Evidencia |
| --- | --- | ---: | --- |
| `COMBO_OPTIONS_INVALID` | Opciones de combo incompatibles | 1 | Archivos actuales |
| `COMBO_VALUE_MISSING` | Combo sin valor inicial | 1 | Archivos actuales |
| `COMBO_VALUE_TYPE` | Valor inicial de combo incompatible | 1 | Archivos actuales |
| `LIGHT_UNSUPPORTED` | Luz no implementada por el motor local examinado | 11 | Archivos actuales |
| `PKG_DUPLICATE_ENTRY` | Nombre duplicado en la tabla del paquete; advertencia de estructura | 1 | Archivos actuales |
| `TEXT_PADDING_STRING` | Padding de texto vectorial en cadena | 10 | Archivos actuales |
| `VOLUME_LIGHT_UNSUPPORTED` | VolumeLight/shape no implementado | 11 | Archivos actuales |
| `WEB_BACKEND_RISK` | Fondo web: riesgo de compatibilidad del backend | 31 | Archivos actuales |
| `LOG_ABORT` | Excepción fatal, abort o fallo de segmentación | 6 | Logs históricos |
| `LOG_AV_SYNC` | Desincronización de audio y vídeo | 6 | Logs históricos |
| `LOG_DBUS` | Errores DBus repetidos | 2 | Logs históricos |
| `LOG_DECODER` | Intentos de decodificación Vulkan/CUDA fallidos | 20 | Logs históricos |
| `LOG_EGL_FALLBACK` | Aviso GLEW: continúa con EGL | 52 | Logs históricos |
| `LOG_JSON` | Excepción de tipos JSON o propiedad obligatoria ausente | 5 | Logs históricos |
| `LOG_LIGHT` | Luces no soportadas en ejecución | 5 | Logs históricos |
| `LOG_OBJECT` | Tipo de objeto desconocido en ejecución | 8 | Logs históricos |
| `LOG_RESOURCE` | Recurso no encontrado/cargado en ejecución | 2 | Logs históricos |
| `LOG_SHADER` | Error de compilación/preparación de shader | 2 | Logs históricos |
| `LOG_WAYLAND` | Detección de pantalla completa no soportada | 52 | Logs históricos |
| `LOG_WEB_SYMBOL` | Símbolo close ausente al iniciar backend web | 2 | Logs históricos |

Interpretación: `WEB_BACKEND_RISK` no es un error individual demostrado. `LIGHT_UNSUPPORTED` y `VOLUME_LIGHT_UNSUPPORTED` implican pérdida visual, no necesariamente un cierre. Las referencias no resueltas requieren comprobar también recursos empaquetados globales o dependencias antes de declararlas ausentes. Los avisos de decodificador, EGL y pantalla completa pueden permitir que la reproducción continúe. Una entrada duplicada en el paquete no demuestra corrupción ni un cierre: debe comprobarse qué versión del recurso elige el motor. Las categorías pueden solaparse: un mismo fondo puede tener varios problemas.

Los valores numéricos de combo son admitidos por el parser local examinado; no se han clasificado como error por ser números. Los valores booleanos sí son incompatibles con su conversión a cadena.

## Inventario completo

| ID | Título | Tipo | Hallazgos en archivos actuales | Categorías en logs históricos |
| --- | --- | --- | --- | --- |
| 1081733658 | Customizable Module Visualizer | web | WEB_BACKEND_RISK | LOG_ABORT, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 1177044161 | Final Fantasy | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1190785367 | Cute Ctrl+Z | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1363762335 | Pixel Pokemon Center | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1364515189 | CPC Flag (Lighter) | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 1401506296 | FinalFantasyVII | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1415834125 | Anime Snow on a pink sunset · Enhanced Version [Animated] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1444006651 | Final_Fantasy | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1545463512 | Pokemon | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 1581782146 | Saber | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1653959255 | Cloud Final Fantasy | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1661372823 | 도기코기 DoggieCorgi | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1664802886 | Pokemon | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 1706318451 | PokemonSliver | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 1828698678 | Periodic Table of Elements *** 40 LANGUAGES *** | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 1863194499 | Youtube Originals | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 1880483129 | Monkey swinging | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2007119928 | pepeDD | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2058152721 | Final Fantasy VII REMAKE - Title Screen | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2063626406 | Cool Car | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2071322772 | Cs Go knife | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2079244403 | 高木さん 高木同学 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2083190909 | Aerith - Final Fantasy VII remake | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2134765860 | Bunk | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2138216783 | Grand Blue Chisa | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2148996556 | Inazuma Eleven Opening Remastered | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2167703666 | Pokémon Crystal - New Bark Town/Home | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 2168640648 | Pokemon Black / White 2 - Join Avenue | scene | Sin hallazgos en las comprobaciones realizadas | LOG_DBUS, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 2168669189 | Pokemon FireRed / LeafGreen - Berry Forest | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2168687397 | Pokemon Emerald - Route 110 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2172073471 | Pokemon HeartGold / SoulSilver - Olivine City | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 2176774204 | Mt. Silver / Pokemon Heartgold | scene | Sin hallazgos en las comprobaciones realizadas | LOG_DBUS, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 2196187716 | Game Room | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2207249535 | Batman - DC Superhero | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2226721636 | Shiba Ramen | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2243617023 | Pokemon ending kekkei sensen | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2252876329 | Arabic Monkey | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2269600861 | monkey with guts theme | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2292763401 | Bell Tower / Pokemon Heartgold | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2296269194 | CS:GO | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2325500626 | Dark Souls Bonfire (Pixel) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2338094750 | [4K] Uncharted 4 - 14 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2338271330 | Son Gohan Dragon Ball Z | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2361552760 | Hinata | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2374001373 | GalexY's Black Space Minimal | web (preset de 850923796) | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 2375127872 | MONKEY FRIDAY | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2390985336 | Cozy Room | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2401337013 | Pokemon Red.Blue | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2401343936 | Pokemon Emerald | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2401354577 | Pokemon Silver | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2407172811 | Pixel Art | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2407266684 | Hinata and Sakura | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2412448157 | Coding Desk | scene | Sin hallazgos en las comprobaciones realizadas | LOG_ABORT, LOG_EGL_FALLBACK, LOG_JSON, LOG_WAYLAND |
| 2413271262 | Hinata Hyuga B | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 2432343678 | 穗乃果 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2479655197 | Whatsapp Drip Car | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2491359038 | Checkbox | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 2497380788 | Berserk | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2497398215 | [PoPw0w] CS:GO Miami Seaside | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2497534036 | FFVII | scene (preset de 2058152721) | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2511404038 | Hinata and Sakura (Sakimichan) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2511542322 | Uncharted 4 Intro | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2547951752 | My dreams FFVII | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2595479020 | Welcome to the new world - Sword Art Online | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2597983718 | Fate/stay night - Rin Tohsaka | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2627236541 | Dragon Slayer | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2643966798 | OnePiece - Alone | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2668339466 | Pokemon Emerald - Bike Ride | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2670793861 | Hinata | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2675053693 | 明日方舟Q弹兔兔 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2707487062 | Gameboy Pokemon | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2711624818 | Inazuma Eleven [Opening Castellano] | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2719679317 | 勇者林克 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2751555951 | Uncharted Legacy of Thieves Collection | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2777464661 | AudiR8 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2790112285 | GigaChad - Can You Feel My Heart | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2791405268 | Cartoon Luffy Gear 5 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2794089817 | MiG-31 Blueprint 「AD」 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2795688676 | Fishing Shack | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2806956811 | Final Fantasy IX (ULTRAWIDE) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2809770238 | [The Legend of Zelda]林克与塞尔达 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2821185257 | F77-Cloud Strife | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2823563989 | Cairo القاهرة | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2828779339 | Nintendo 64 | scene | LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 2831090574 | Chisa Kotegawa - Grand blue (4K+Clock) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2836178866 | Grand Blue Diving Shop (Night Time) | scene | LIGHT_UNSUPPORTED | LOG_EGL_FALLBACK, LOG_LIGHT, LOG_OBJECT, LOG_WAYLAND |
| 2840380808 | Yelan Xray +18 -- Genshin Impact | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 2841805505 | Aerith's House (FFVII Remake) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2843745418 | [Cyberpunk]target lock | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2849102890 | Breaking Bad GTA Intro | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2853761842 | [桜都字幕组][ピンクパイナップル]オナホ教室 ～女子全員妊娠計画～ THE ANIMATION | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2853879719 | 妖精 (x-ray) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2854663557 | ankara messi chiquito | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2857866445 | Guts - Berserk | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2861218511 | hinata | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2861252650 | Uncharted 4 Libertalia | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2871680480 | Car Trip | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2872906858 | Cassette Deck (Media Integration) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2880212869 | 【治愈系】像素宝可梦 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2882091461 | [SFW] Uta (One Piece) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2884323042 | Monkey Ridin Through Los Santos | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2890473419 | 麻匪 肉肉的雷电将军 3D 21:9 16:9 | scene | LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 2891436791 | Cat | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 2896051050 | トロテム女仆掀裙 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2896906752 | Bocchi the Rock! · PA-san | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2898186348 | [Moon] Minimalist Wallpaper• | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2899111551 | AlonsoC15 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2899121554 | Pokémon Emerald "Remake" Title Screen. | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2899162907 | CRT Cat Tennis | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2909616963 | Afterglow | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2913091682 | Pokémon Emerald - waterfall. | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2914405895 | 你在盯着哪里看？ | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 2918233495 | Breakdancing Garfield Loop | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2919833032 | mclaren p1 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2919854127 | 麻匪 辉夜 AHEGAO | scene | TEXT_PADDING_STRING | Sin errores identificados en los logs conservados |
| 2924967442 | pera | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2925278995 | Chill Time🐟🐟🌛 (Day/Night) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2927180913 | Edge of Summer | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2932789245 | gohan | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2933386637 | chill ocean | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2935050550 | gohan goes to mcdonalds | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2935672880 | 搬电容的小女孩 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2937188619 | [4K] 櫻花和居 Sakura | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2937991140 | Berserk starboy | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2942588168 | Toyota AE86 Trueno Drift | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2943735921 | Pokemon bailando | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2944773634 | Blue Sky [4K] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2947302287 | Angled Waves | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2947399331 | Anime Console | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2947421643 | Obama prism (spinning) | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2948618803 | Chill'out Beach [4K] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2950411785 | Kingdom Hearts FF Style ( 1 Hour Music ) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2950724888 | IlloJuan Room | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2952104640 | Chill Mario | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2952891094 | 宝可梦 小智、伙伴们 再会-Pokemon Ash Ketchumand、Partners Goodbye(试作311) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2956113333 | DARK SOULS™ III • Soul of Cinder · Animated Wallpaper | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2957128564 | Chipset Inspection | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2958029534 | rainy weather x minecraft | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2961391230 | Bowser Singing Peaches- By Jack Black · Super Mario Bros Movie | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2962210602 | 本人的免责声明，请右键在创意工坊打开 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2962323917 | ⌜👽 DanDaDan 👽 - Momo Ayase - Customizable⌟ | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2963123096 | 宝可梦 穹顶之下小遥相遇烈空坐-Pokemon May Meeting Mega Rayquaza Under The Dome by乌列er （试作315） | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2963618194 | Just the two of us | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2964521946 | Chill campfire Real time day and night cycle [4k] by Becco38 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2967504743 | Ganon Rosario - Dale, Zelda, Dale | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2967540199 | [4k] Vegeta under the rain Chill hop music study/relax to meme by Becco38 | scene | LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 2971333726 | Floor796 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2971987338 | [8K HDR] Mazda Rx-7 KHYZYL SALEEM by Becco38 | scene | LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 2973197117 | John Cena -  Cupid | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2973821653 | Kılıçdaroğlu Erdoğan'a Padişah Dinletiyor | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2976330565 | The Legend of Zelda Tears of the Kingdom | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2976340420 | night in sinnoh | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2977682502 | 呀哈哈-烧冰3 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2980088441 | CodeTime | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2986283348 | Hercules n Wolfes (Audio Responsive) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2990989001 | Gamer Zone | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 2997198842 | 织梦勇者的海拉鲁冒险4k | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3001053327 | Chudbob Soypants | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3001442160 | 四百合两被撅 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3001696877 | 钢之炼金术师 爱德华 故乡的天空-FULLMETAL ALCHEMIST Edward The Hometown Sky（试作328） | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3002120692 | NieR: Automata · Android Machine Robot · eggloaf | scene | TEXT_PADDING_STRING | Sin errores identificados en los logs conservados |
| 3005232415 | Pessi | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3009576338 | Pixel Art | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3010544687 | Steel Ball Run | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3016113292 | 菲奥娜 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3020475064 | Daylight Rush | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3034976631 | Bocchi the Rock! Hitori Gotoh Pixel 4K | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3039335251 | Hinata interactive | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3042793806 | Fallen Tower | scene | LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3044903359 | STEEL BALL RUN | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3045152648 | cyberloft lofi | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3051217368 | CS签名静态 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3079014483 | 海贼王全员派对 ONE PIECE Party | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3085273166 | 9MM x LOLI SHIGURE UI | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3086490516 | CyberMySoul | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3088076273 | [4K] SSJ Son Goku · Dragon Ball | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3088099655 | terminal · world clock + countdown [4K] | scene | Sin hallazgos en las comprobaciones realizadas | LOG_ABORT, LOG_EGL_FALLBACK, LOG_JSON, LOG_OBJECT, LOG_RESOURCE, LOG_WAYLAND |
| 3090304160 | Кавасаки,Каго,Крико и Эстрипер | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3101250849 | lifecouldbemonke | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3103638245 | Lethal Company | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3118343745 | Los Pingüinos  Last Christmas | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3120693095 | OVA 妻に黙って即売会に行くんじゃなかった ＃2 [中文字幕]_4K | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3120907497 | Basketball_CS2 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3122339805 | Pixels | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3125045358 | Atreus studying-God of War Ragnarök | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3129248394 | Pixels of Autumn [S22 Ultra] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3130062296 | GTR R35 Japanese Convenience Store (raining) + Anime Girl Dancing | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3131759472 | Cave Hideout | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3134882598 | Jungle theme | scene (preset de 3122339805) | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3135364491 | Honda NSX / 5ENNA - Shigure Ui [God Requiem] dance (4k full HD) | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3135979670 | Minimalist Topographic · Clock | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3136351729 | ASCII Models (Donut, Earth, Skeleton, Heartbeat) | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3136497704 | Gengar | scene (preset de 3122339805) | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3136912260 | Dark PIxels | scene (preset de 3122339805) | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3137375751 | Astronaut in the light [4K / AUDIO] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3139337064 | Lain | scene (preset de 3122339805) | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3140830382 | Population Data | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3141421197 | GraspOfTheAbyss | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3143966504 | · Pokémon - Lake of Rage · [HD] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3147779403 | Evening Rain | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3150758651 | SHIGURE UI x RYAN GOSLING (9MM) | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3151551777 | Persona 3 Reload [4K + Day/Night cycle] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3155776049 | Pixel Desktop | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3158063102 | Circular Star [4K] | scene | LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3159551339 | made by هايلوكس :p | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3163137329 | PixeledDucky | scene (preset de 3122339805) | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3190459067 | Goku Cloud Artwork (Akira Toriyama Tribute in YT) | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3208556055 | Station | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3210875135 | After Sunset [4K] | scene | LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3211109911 | Timeless [Dante] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3216043609 | Cosecha propia de patacas | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3218303536 | Dark Mode Win XP Bliss | scene | TEXT_PADDING_STRING | Sin errores identificados en los logs conservados |
| 3223077541 | Circular Black Hole [4K] | scene | LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3235218034 | Haix CS:GO MEME | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3248239912 | Stardew Valley Dynamic Day/Night · 16:9 | scene | TEXT_PADDING_STRING | Sin errores identificados en los logs conservados |
| 3250755486 | cat eating a chips through the windows 7 wallpaper | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3252690481 | 租借女友/Xray/水原千鹤/七海麻美/更科瑠夏/樱泽墨/彼女、お借りします | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3280544405 | Miku x Shrek | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3290491250 | frieren | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3309685345 | NIKKE BEAUTY FULL SHOT メイデン | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3315123651 | 雏田Hyūga Hinata | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3348560292 | 【壁纸动态4K 30帧/毛主席】大海航行靠舵手，干革命靠毛泽东思想！ | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3356568449 | 白色后妈裙御姐3 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3359737479 | Nikke Alice Wonderland Bunny | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3360411320 | Nikke Dorothy Nastalgia | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3360824342 | Nikke Maiden Under the Sun | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3361204762 | Nikke Isabel Honeymoon Party | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3361248339 | Nikke Mihara | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3365280541 | SSJ2 Gohan Manga | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3367988661 | Floating Cat. | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3377132665 | Floating Ducks. | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3379659876 | persona4 x DANDADAN | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3379996991 | Winter Conch Street - SpongeBob SquarePants | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3386057440 | 山中井野-Xray | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3390481639 | Super Vegito Vs Buu Dragon Ball Manga Animation | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3392974377 | MiSide Mita 4k · Edited by CAMOTE | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3409406753 | makima black dress | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3409418483 | Dragon Ball Goku Vegeta | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3411438230 | YessirSupra goth girl | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3414455628 | [Final Fantasy] Cloud Strife | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3421299830 | Ellen Joe ZZZ | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3439838314 | Goku Black and White [ Remastered by Desktophut.com ] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3441187616 | Minecraft Overgrown Cabin 4K Upscale | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3441873795 | Swimming Kirby [4K] | scene | VOLUME_LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3453105223 | Brown Dust 2 Michaela Nun | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3455300199 | Girl · Dark Background · Dark & Colored Versions · 4K | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3456058351 | 甜蜜女友 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3466760845 | 八奈见杏菜 - “ 我发现了一家好店! ” - 8K 高清修复 @AaixolkerBM - Yanami Anna | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3468644034 | higashiyama kobeni-Ly0 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3469855069 | study mode stardew | scene (preset de 3248239912) | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3472940912 | -Tsukatsuki Rio [ blue archive ] - 4K | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3474622002 | Loki One Piece Manga | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3477054430 | Cat with headphones on the roof | scene | LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3478188957 | Dark18 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3478829647 | Dragon Ball Z - Gohan Definitivo | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3479671230 | Switzerland. | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3480108838 | Pokemon Diamond and Pearl - Credits | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3480803034 | cs夜行衣雨夜-蝴蝶刀检视 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3481819587 | Mount Fuji. Japan. | scene | VOLUME_LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3493061261 | Ultra Ego Vegeta Manga Edit by zenkai.rz | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3495414735 | Monkey D. Luffy – The Light in the Shadows | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3505410236 | Esdese-Ly0 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3509243656 | 三体实时演算 · Three-Body problem - SYKM | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3510151715 | Back and white #5 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3514942235 | Girl · Dark Background · Dark & Colored Versions · 4K | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3516882089 | A swaying ocean | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3526096300 | Custom Wii Home Menu - With Clickable Channels | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3527811827 | 【GrandBlue】碧蓝之海 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3528523036 | 胜利女神2K壁纸-Nikke Rapi: Red Hood Red Flavor | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3531878415 | Sledding Game | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3535044281 | [One Piece] Future Pirate King Ruffy | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3537671609 | // Handle_with_care_; PrintStream CS Aesthetics Tribute [4K / Clock] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3539544537 | NIKKE_拉毗 小红帽：红色风情 动态壁纸 (Japanese/English) | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3540080477 | 催眠致幻/Hypnotic hallucination | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3541112453 | Kuroha Moment鼠标垫 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3544530728 | 蜡笔小新-荷塘小憩 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3544784842 | bbno$ - mememe  MMV | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3546094127 | Evangelion · Asuka Langley · Minimalist | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3548242401 | NIKKE_米哈拉：羁绊锁链 动态壁纸 可交互 | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3550072279 | CHZZKMoca_Vacance2025 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3561551763 | Hoshimi Miyabi · Zenless Zone Zero · 4K | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3561824355 | GRASS 4K -terminal | scene (preset de 3088099655) | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3563096027 | Nissan GT-R R32 · 🆄🆆🆄 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3566329932 | Frieren · Sousou no Frieren [Media Visualizer, Clock, Calendar] | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3574952137 | Johnny Joestar Steel Ball Run Manga Animation | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3575806939 | Monster Energy | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3576436521 | Jesus Christ / JJBA Part 7 / JOJO | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3577490812 | Image_1759209041166（X-ray） | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3578485404 | 雪乃深冬-Ly0 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3580010980 | 放置天使Idle Angels | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3585875739 | Miku Monitoring | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3588579284 | 甜蜜女友3 柳木诗梦 高配版 支持147种立绘 配置不够不要用 语音触摸BETA版 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3590434671 | 135088483_p0 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3598619616 | LEON  VAM- Static Wallpaper X-Ray +18 1 | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3599477480 | Stellar Blade EVE Bunny 18+ [4k] | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3600129651 | Wilhelmina Iron Monarch 1 / Brown Dust 2, 브라운더스트2, ブラウンダスト2, 棕色塵埃2, 棕色尘埃2 | scene | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3610988025 | 日向雏田动态壁纸 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3611439897 | 碧蓝航线 五河琴里【普通版/语音/多功能壁纸】-B站慕慕慕慕斯小蛋糕1.0 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3612167681 | 暗黑御姐环绕动效 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3612171954 | 日向雏田环绕动效 | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3612647859 | 水上樂園女王 - 威廉明娜 / BrownDust2 / 棕色塵埃2 | video | Sin hallazgos en las comprobaciones realizadas | LOG_AV_SYNC, LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3614551199 | 泡在我家的辣妹-Ly0 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3615575163 | SCU/Minecraft-Smart-Desktop | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3620505517 | Chainsaw Man – The Movie: Reze Arc (drawn by maldo / dh lucky) | scene | VOLUME_LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3631139973 | Memento Mori - Death Calendar | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3637044670 | Gohan Beast (Shortcut, Media Info.) · 𝙎𝙚𝙮𝙪𝙡.𝙎𝙖𝙡𝙩𝙯 | scene | PKG_DUPLICATE_ENTRY | Sin errores identificados en los logs conservados |
| 3639101641 | 艾莲乔-绝区零 | scene | VOLUME_LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3641286571 | Iceland Highlands 4K | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3645032120 | 波雅汉库克动态壁纸 | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3653171633 | F1 Ferrari SF-26 | scene | VOLUME_LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3653991401 | 𝓓𝓪𝓻𝓴✝ | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3657975068 | [熟肉][中英字幕]神之款待：希芙的拥抱-Divine Hospitality Sif's Embrace-Dezmall | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3660392544 | Eve · Stellar Blade | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3662185984 | UFO ferry | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3672019557 | Dragon Ball Anniversary | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3675286485 | floor796 | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3678785889 | hinata , naruto | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3682112815 | Eclipse Date_looponly | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3682739600 | Pixar Cars [4K] | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3683255353 | horizon-sky-wanderer-moewalls-com | video | Sin hallazgos en las comprobaciones realizadas | LOG_AV_SYNC, LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3683975943 | 干到喷水还不满足 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3684018768 | Before the Road | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3684027780 | 双马尾御姐激情侍奉 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3684060242 | Grand Theft Auto V: Los Santos | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3684676180 | 邻居是喜欢榨精的痴女御姐 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3685196434 | 饥渴人妻上门求操 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3686017621 | 姐妹花抢鸡巴吃 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3686075716 | 男厕所束缚调教肉便器 | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3688319285 | 偷情寂寞人妻 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3691894727 | [afk] Girl ·AI Art·NSFW·18+·4K· //264 | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3692766662 | Landscape of Pywel (Crimson Desert) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3694299915 | not so goofy. | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3695981322 | Isabel Wedding Dress (4K) - Nikke Godess of Victory | scene | VOLUME_LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3696819731 | Wuhu Island | scene | LIGHT_UNSUPPORTED, TEXT_PADDING_STRING | Sin errores identificados en los logs conservados |
| 3697686181 | 调月莉音4K | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3698658890 | Go For It, Nakamura-kun!! Ending "Hatsukoi" (Episode 1) | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3700124511 | 终末地：帝江号 | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3701356561 | Lost Valley · northway. | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3704188417 | Milf 5-BigHip丨R18丨4K丨Black | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3710108798 | 碧蓝航线Azur Laneアズールレーン | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3721300967 | Komi-Shouko-By-Suna丨R18丨4K丨Black | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_OBJECT, LOG_WAYLAND |
| 3725287547 | boa hancock | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3737237256 | Fishing Frogs by Abi Toads | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3741334342 | Tayama/Yamada — 山田/田山 (4k) | scene | TEXT_PADDING_STRING, VOLUME_LIGHT_UNSUPPORTED | Sin errores identificados en los logs conservados |
| 3743866623 | 以撒盖小被 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3756621387 | 阿洛娜指纹识别2.0[网页版] | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3762254115 | 胜利女神NIKKE | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3772073136 | Terraria Goldfish Walker（1080p） | scene | Sin hallazgos en las comprobaciones realizadas | LOG_ABORT, LOG_DECODER, LOG_EGL_FALLBACK, LOG_JSON, LOG_WAYLAND |
| 3776653850 | Asuka Langley & Night bedroom — 惣流・アスカ・ラングレ | scene | VOLUME_LIGHT_UNSUPPORTED | LOG_ABORT, LOG_EGL_FALLBACK, LOG_JSON, LOG_LIGHT, LOG_OBJECT, LOG_WAYLAND |
| 3777008325 | MOMO | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3777338505 | M027 Reze and Power | scene | VOLUME_LIGHT_UNSUPPORTED | LOG_EGL_FALLBACK, LOG_LIGHT, LOG_OBJECT, LOG_WAYLAND |
| 3777601433 | DUAL - NSFW | scene | TEXT_PADDING_STRING | LOG_ABORT, LOG_JSON |
| 3777864954 | 绮梦晚夏奥奇传说 | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3779168864 | Spider-Man(噪点) | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3781595377 | 莫加多尔 · 共坠的渴慕（动态） | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3781607667 | Street Fighter 6 beach | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3781792400 | Blue Archive丨蔚蓝档案丨调月莉音丨Tsukatsuki Rio | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3783744288 | 香迪 · 魅惑的特调饮品 | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3783788697 | 华盛顿 · 夜间巡诊 | web | COMBO_VALUE_MISSING, WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3784286394 | 建武 · 妆点，只为今夜 | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3784961254 | 君主 · 海滩享受计划 | web | WEB_BACKEND_RISK | LOG_WEB_SYMBOL |
| 3785053191 | 约克城II · 交错的温柔时光 | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3785545617 | 圣路易斯 · 邮轮上的诱人午后 | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3786137579 | 碧蓝航线Azur Laneアズールレーン | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3789790717 | ANIME GIRL - SADAKO | scene | Sin hallazgos en las comprobaciones realizadas | LOG_AV_SYNC, LOG_DECODER, LOG_EGL_FALLBACK, LOG_OBJECT, LOG_RESOURCE, LOG_WAYLAND |
| 3789816832 | Nino Nakano, she is very flexible | scene | VOLUME_LIGHT_UNSUPPORTED | LOG_EGL_FALLBACK, LOG_LIGHT, LOG_OBJECT, LOG_SHADER, LOG_WAYLAND |
| 3791364468 | 148145549_p0 | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3792804757 | 耀佳音 Astra Yao 4k | video | Sin hallazgos en las comprobaciones realizadas | LOG_AV_SYNC, LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3792926059 | 蕾米埃尔 丹 Remielle Dan 绝区零 Zenless Zone Zero | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3793228943 | Ralph Lauren ART | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3794626785 | M069 frienre e fern | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3795054117 | [H69Verse]甘露寺蜜璃无限城 第二章 Mitsuri Infinitys Pleasure Castle | video | Sin hallazgos en las comprobaciones realizadas | LOG_AV_SYNC, LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3796799777 | 冬日街 | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3797025357 | M076 sexy police | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3798304439 | miku x teto face check | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3798592629 | 航天三小只（原作者抖音不吃锦鲤） | scene | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3799142774 | Rhine Lab · 莱茵生命交互桌面 · Interactive Desktop | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 3799669491 | 第七史诗 - 里安娜&路西艾拉 | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3800682327 | Minecraft Skydive Live Wallpaper | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3801244014 | Hinata Hyuga (2)丨4K丨DarK | scene | TEXT_PADDING_STRING | Sin errores identificados en los logs conservados |
| 3801329407 | Kafka - Honkai Star Rail 4K | scene | VOLUME_LIGHT_UNSUPPORTED | LOG_EGL_FALLBACK, LOG_LIGHT, LOG_OBJECT, LOG_WAYLAND |
| 3802067987 | 《螈版生存》动态壁纸（电脑端） | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3802401381 | nami sx -alexandr | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3802576044 | 交错战线 | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3802655120 | 鸣潮 - 爱弥斯 | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 3802742966 | Demon Queen [Dark Ritual] 4K Anime | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_SHADER, LOG_WAYLAND |
| 3803547930 | 海绵宝宝｜章鱼哥的上班日常 | scene | TEXT_PADDING_STRING | Sin errores identificados en los logs conservados |
| 3804035019 | Girl · Dark Background · Dark & Colored Versions · 4K | scene | TEXT_PADDING_STRING | Sin errores identificados en los logs conservados |
| 3816902511 | 废土骑行 · Wasteland Ride · 荒野の旅 | web | WEB_BACKEND_RISK | LOG_WEB_SYMBOL |
| 3817708280 | 小野寺小咲-Onodera kosaki | video | Sin hallazgos en las comprobaciones realizadas | LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3818461208 | Suspended Reverie | scene | Sin hallazgos en las comprobaciones realizadas | LOG_EGL_FALLBACK, LOG_WAYLAND |
| 3819090543 | 雏田-穿搭轮换 | video | Sin hallazgos en las comprobaciones realizadas | LOG_AV_SYNC, LOG_DECODER, LOG_EGL_FALLBACK, LOG_WAYLAND |
| 803212581 | Countdown Timer | web | WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 828722349 | Alps Mountains - Windy & Snowing | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 837562803 | Nisekoi (ニセコイ / 伪恋) NCED (Kosaki ver) 1080P | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 837581037 | Nisekoi (ニセコイ / 伪恋) NCOP1 1080P | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 837583600 | Nisekoi (ニセコイ / 伪恋) NCOP2 1080P | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 850923796 | Audio Scratchboard | web | COMBO_OPTIONS_INVALID, COMBO_VALUE_TYPE, WEB_BACKEND_RISK | Sin errores identificados en los logs conservados |
| 860024140 | Party Hard ! | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |
| 893871465 | CS:GO Russians player | video | Sin hallazgos en las comprobaciones realizadas | Sin errores identificados en los logs conservados |

## Detalle por fondo con hallazgos en archivos

### 1081733658 — Customizable Module Visualizer

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 1828698678 — Periodic Table of Elements *** 40 LANGUAGES ***

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 2374001373 — GalexY's Black Space Minimal

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 2491359038 — Checkbox

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 2828779339 — Nintendo 64

- **Luz no implementada por el motor local examinado** (1): 54 .

### 2836178866 — Grand Blue Diving Shop (Night Time)

- **Luz no implementada por el motor local examinado** (3): 65 ; 68 ; 69 .

### 2890473419 — 麻匪 肉肉的雷电将军 3D 21:9 16:9

- **Luz no implementada por el motor local examinado** (3): 19 ; 22 ; 26 s.

### 2919854127 — 麻匪 辉夜 AHEGAO

- **Padding de texto vectorial en cadena** (2): 50 文本层: 32.00000 32.00000; 63 文本层: 32.00000 32.00000.

### 2967540199 — [4k] Vegeta under the rain Chill hop music study/relax to meme by Becco38

- **Luz no implementada por el motor local examinado** (1): 329 .

### 2971987338 — [8K HDR] Mazda Rx-7 KHYZYL SALEEM by Becco38

- **Luz no implementada por el motor local examinado** (2): 64 circle; 112 anarchy.

### 3002120692 — NieR: Automata · Android Machine Robot · eggloaf

- **Padding de texto vectorial en cadena** (6): 251 text-shadow: 0.00000 0.00000; 113 text: 0.00000 0.00000; 202 time: 0.00000 0.00000; 225 date: 0.00000 0.00000; 120 media-name-shadow: 0.00000 0.00000; 144 media-name: 0.00000 0.00000.

### 3042793806 — Fallen Tower

- **Luz no implementada por el motor local examinado** (2): 330 Sky Light; 327 Sun Light.

### 3136351729 — ASCII Models (Donut, Earth, Skeleton, Heartbeat)

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3158063102 — Circular Star [4K]

- **Luz no implementada por el motor local examinado** (2): 9842 ; 402 .

### 3210875135 — After Sunset [4K]

- **Luz no implementada por el motor local examinado** (3): 101 ; 106 ; 107 .

### 3218303536 — Dark Mode Win XP Bliss

- **Padding de texto vectorial en cadena** (2): 2248 Time: 67.00000 67.00000; 2250 Date: 32.00000 32.00000.

### 3223077541 — Circular Black Hole [4K]

- **Luz no implementada por el motor local examinado** (3): 156 ; 2067 ; 61 .

### 3248239912 — Stardew Valley Dynamic Day/Night · 16:9

- **Padding de texto vectorial en cadena** (171): 259 Time: 32.00000 32.00000; 105 Time Bloom: 32.00000 32.00000; 124 Date: 32.00000 32.00000; 125 Date Bloom: 32.00000 32.00000; 1687 ClassicDate: 32.00000 32.00000; 1848 ClassicTime: 32.00000 32.00000; 525 Artist: 32.00000 32.00000; 496 ArtistBloom: 32.00000 32.00000; 524 Title: 32.00000 32.00000; 617 TitleBloom: 32.00000 32.00000; 526 Album: 32.00000 32.00000; 585 AlbumBloom: 32.00000 32.00000; 787 TimeRemaining: 32.00000 32.00000; 788 TimeRemainingBloom: 32.00000 32.00000; 866 SongLength: 32.00000 32.00000; 867 SongLengthBloom: 32.00000 32.00000; 1405 : 32.00000 32.00000; 1610 Main Text: 32.00000 32.00000; 2309 Other Info: 32.00000 32.00000; 2351 Page Number: 32.00000 32.00000; 2059 LABEL_UnsavedChanges1: 32.00000 32.00000; 1356 LABEL_Player: 32.00000 32.00000; 2879 LABEL_PlayerToggle: 32.00000 32.00000; 2718 LABEL_HatHair: 32.00000 32.00000; 1338 LABEL_Scale: 32.00000 32.00000; 1346 LABEL_Value: 32.00000 32.00000; 5183 LABEL_SkinColor: 32.00000 32.00000; 5191 LABEL_Value: 32.00000 32.00000; 5199 LABEL_Value: 32.00000 32.00000; 5207 LABEL_Value: 32.00000 32.00000; 5092 LABEL_EyeColor: 32.00000 32.00000; 5102 LABEL_Value: 32.00000 32.00000; 5110 LABEL_Value: 32.00000 32.00000; 5118 LABEL_Value: 32.00000 32.00000; 2366 LABEL_Hair: 32.00000 32.00000; 1783 LABEL_HairIndex: 32.00000 32.00000; 1739 LABEL_HairColor: 32.00000 32.00000; 1402 LABEL_Value: 32.00000 32.00000; 2127 LABEL_Value: 32.00000 32.00000; 1447 LABEL_Value: 32.00000 32.00000; 891 LABEL_Shirt: 32.00000 32.00000; 892 LABEL_ShirtIndex: 32.00000 32.00000; 893 LABEL_ShirtColor: 32.00000 32.00000; 902 LABEL_Value: 32.00000 32.00000; 919 LABEL_Value: 32.00000 32.00000; 929 LABEL_Value: 32.00000 32.00000; 1803 LABEL_Pants: 32.00000 32.00000; 1804 LABEL_PantsIndex: 32.00000 32.00000; 1805 LABEL_PantsColor: 32.00000 32.00000; 1813 LABEL_Value: 32.00000 32.00000; 1821 LABEL_Value: 32.00000 32.00000; 1829 LABEL_Value: 32.00000 32.00000; 1414 LABEL_Hat: 32.00000 32.00000; 1415 LABEL_HatIndex: 32.00000 32.00000; 1796 LABEL_ShoesColor: 32.00000 32.00000; 1825 LABEL_Value: 32.00000 32.00000; 1835 LABEL_Value: 32.00000 32.00000; 1843 LABEL_Value: 32.00000 32.00000; 1911 LABEL_Accessory: 32.00000 32.00000; 1912 LABEL_AccessoryIndex: 32.00000 32.00000; 1922 LABEL_ScreenHeight: 32.00000 32.00000; 1939 LABEL_Value: 32.00000 32.00000; 1795 LABEL_UnsavedChanges2: 32.00000 32.00000; 1909 LABEL_Player: 32.00000 32.00000; 1930 LABEL_PlayerToggle: 32.00000 32.00000; 1940 LABEL_HatHair: 32.00000 32.00000; 1948 LABEL_Scale: 32.00000 32.00000; 1956 LABEL_Value: 32.00000 32.00000; 1965 LABEL_SkinColor: 32.00000 32.00000; 1974 LABEL_Value: 32.00000 32.00000; 1983 LABEL_Value: 32.00000 32.00000; 1993 LABEL_Value: 32.00000 32.00000; 1996 LABEL_EyeColor: 32.00000 32.00000; 2006 LABEL_Value: 32.00000 32.00000; 2014 LABEL_Value: 32.00000 32.00000; 2022 LABEL_Value: 32.00000 32.00000; 2025 LABEL_Hair: 32.00000 32.00000; 2027 LABEL_HairIndex: 32.00000 32.00000; 2028 LABEL_HairColor: 32.00000 32.00000; 2039 LABEL_Value: 32.00000 32.00000; 2054 LABEL_Value: 32.00000 32.00000; 2065 LABEL_Value: 32.00000 32.00000; 2069 LABEL_Shirt: 32.00000 32.00000; 2071 LABEL_ShirtIndex: 32.00000 32.00000; 2072 LABEL_ShirtColor: 32.00000 32.00000; 2088 LABEL_Value: 32.00000 32.00000; 2098 LABEL_Value: 32.00000 32.00000; 2106 LABEL_Value: 32.00000 32.00000; 2109 LABEL_Pants: 32.00000 32.00000; 2110 LABEL_PantsIndex: 32.00000 32.00000; 2111 LABEL_PantsColor: 32.00000 32.00000; 2121 LABEL_Value: 32.00000 32.00000; 2130 LABEL_Value: 32.00000 32.00000; 2141 LABEL_Value: 32.00000 32.00000; 2144 LABEL_Hat: 32.00000 32.00000; 2145 LABEL_HatIndex: 32.00000 32.00000; 2149 LABEL_ShoesColor: 32.00000 32.00000; 2157 LABEL_Value: 32.00000 32.00000; 2165 LABEL_Value: 32.00000 32.00000; 2173 LABEL_Value: 32.00000 32.00000; 2177 LABEL_Accessory: 32.00000 32.00000; 2178 LABEL_AccessoryIndex: 32.00000 32.00000; 2183 LABEL_ScreenHeight: 32.00000 32.00000; 2192 LABEL_Value: 32.00000 32.00000; 1719 : 32.00000 32.00000; 2762 : 32.00000 32.00000; 2348 FPS Tracker: 32.00000 32.00000; 5083 LABEL_Latitude: 32.00000 32.00000; 5176 VALUE_Latitude: 32.00000 32.00000; 2840 LABEL_Longitude: 32.00000 32.00000; 2909 VALUE_Longitude: 32.00000 32.00000; 1626 LABEL_SaveDisclaimer: 32.00000 32.00000; 3368 LABEL_Number: 32.00000 32.00000; 3378 LABEL_Number: 32.00000 32.00000; 3386 LABEL_Number: 32.00000 32.00000; 3352 LABEL_Number: 32.00000 32.00000; 3148 LABEL_Number: 32.00000 32.00000; 3398 LABEL_Number: 32.00000 32.00000; 3408 LABEL_Number: 32.00000 32.00000; 3420 LABEL_Number: 32.00000 32.00000; 3428 LABEL_Number: 32.00000 32.00000; 4895 LABEL_Number: 32.00000 32.00000; 3518 LABEL_Period: 32.00000 32.00000; 2242 LABEL_Minus: 32.00000 32.00000; 3052 LABEL_Number: 32.00000 32.00000; 3054 LABEL_Number: 32.00000 32.00000; 3056 LABEL_Number: 32.00000 32.00000; 3058 LABEL_Number: 32.00000 32.00000; 3060 LABEL_Number: 32.00000 32.00000; 3062 LABEL_Number: 32.00000 32.00000; 3064 LABEL_Number: 32.00000 32.00000; 3066 LABEL_Number: 32.00000 32.00000; 3068 LABEL_Number: 32.00000 32.00000; 3070 LABEL_Number: 32.00000 32.00000; 3072 LABEL_Period: 32.00000 32.00000; 3074 LABEL_Minus: 32.00000 32.00000; 2225 Selected Crop Name: 32.00000 32.00000; 2763 WinLose Text: 32.00000 32.00000; 2448 Time Until Next Text: 32.00000 32.00000; 2712 Hover Crop Text: 32.00000 32.00000; 3221 G_GrowTime_1: 32.00000 32.00000; 3225 G_Price_1: 32.00000 32.00000; 3234 G_Regrows_1: 32.00000 32.00000; 3236 G_CropType_1: 32.00000 32.00000; 3296 G_GrowTime_2: 32.00000 32.00000; 3300 G_Price_2: 32.00000 32.00000; 3303 G_Regrows_2: 32.00000 32.00000; 3306 G_CropType_2: 32.00000 32.00000; 3358 G_GrowTime_3: 32.00000 32.00000; 3361 G_Price_3: 32.00000 32.00000; 3364 G_Regrows_3: 32.00000 32.00000; 3369 G_CropType_3: 32.00000 32.00000; 3415 G_GrowTime_4: 32.00000 32.00000; 3418 G_Price_4: 32.00000 32.00000; 3423 G_Regrows_4: 32.00000 32.00000; 3426 G_CropType_4: 32.00000 32.00000; 3466 G_GrowTime_5: 32.00000 32.00000; 3469 G_Price_5: 32.00000 32.00000; 3472 G_Regrows_5: 32.00000 32.00000; 3475 G_CropType_5: 32.00000 32.00000; 3519 G_GrowTime_6: 32.00000 32.00000; 3522 G_Price_6: 32.00000 32.00000; 3525 G_Regrows_6: 32.00000 32.00000; 3528 G_CropType_6: 32.00000 32.00000; 3567 Crop: 32.00000 32.00000; 3570 Growth: 32.00000 32.00000; 3572 Price: 32.00000 32.00000; 3574 Regrow: 32.00000 32.00000; 3576 Type: 32.00000 32.00000; 3578 Season: 32.00000 32.00000; 2478 InfoboxText: 32.00000 32.00000.

### 3359737479 — Nikke Alice Wonderland Bunny

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3360411320 — Nikke Dorothy Nastalgia

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3360824342 — Nikke Maiden Under the Sun

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3361204762 — Nikke Isabel Honeymoon Party

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3361248339 — Nikke Mihara

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3441873795 — Swimming Kirby [4K]

- **VolumeLight/shape no implementado** (1): 560 Light shafts - corner.

### 3477054430 — Cat with headphones on the roof

- **Luz no implementada por el motor local examinado** (4): 38 ; 59 ; 133 ; 124 .

### 3481819587 — Mount Fuji. Japan.

- **VolumeLight/shape no implementado** (1): 79 Rayons lumineux - coin.

### 3528523036 — 胜利女神2K壁纸-Nikke Rapi: Red Hood Red Flavor

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3539544537 — NIKKE_拉毗 小红帽：红色风情 动态壁纸 (Japanese/English)

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3548242401 — NIKKE_米哈拉：羁绊锁链 动态壁纸 可交互

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3615575163 — SCU/Minecraft-Smart-Desktop

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3620505517 — Chainsaw Man – The Movie: Reze Arc (drawn by maldo / dh lucky)

- **VolumeLight/shape no implementado** (1): 782 Light shafts - corner.

### 3631139973 — Memento Mori - Death Calendar

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3637044670 — Gohan Beast (Shortcut, Media Info.) · 𝙎𝙚𝙮𝙪𝙡.𝙎𝙖𝙡𝙩𝙯

- **Nombre duplicado en la tabla del paquete; advertencia de estructura** (1): fonts/workshop/3632410990/nasalization.otf.

### 3639101641 — 艾莲乔-绝区零

- **VolumeLight/shape no implementado** (1): 20 光束 - 角.

### 3653171633 — F1 Ferrari SF-26

- **VolumeLight/shape no implementado** (4): 128 V2 Light shafts - radial; 787 V2 Light shafts - radial; 193 V1 Light shafts - linear; 125 V1 Light shafts - linear.

### 3675286485 — floor796

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3695981322 — Isabel Wedding Dress (4K) - Nikke Godess of Victory

- **VolumeLight/shape no implementado** (1): 361 Light shafts - corner.

### 3696819731 — Wuhu Island

- **Luz no implementada por el motor local examinado** (3): 107 Scene Light; 742 Lighthouse Light; 1042 Plane Light.
- **Padding de texto vectorial en cadena** (4): 1476 Text Song: 64.00000 64.00000; 1540 Text Artist: 64.00000 64.00000; 1129 Time: 0.00000 0.00000; 1138 Date: 0.00000 0.00000.

### 3700124511 — 终末地：帝江号

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3741334342 — Tayama/Yamada — 山田/田山 (4k)

- **Padding de texto vectorial en cadena** (5): 331 Artist Shadow: 32.00000 32.00000; 342 Artist Title: 32.00000 32.00000; 345 Song Shadow: 32.00000 32.00000; 350 Song Title: 32.00000 32.00000; 565 Часы: 32.00000 32.00000.
- **VolumeLight/shape no implementado** (1): 247 Лучи света — линии.

### 3756621387 — 阿洛娜指纹识别2.0[网页版]

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3776653850 — Asuka Langley & Night bedroom — 惣流・アスカ・ラングレ

- **VolumeLight/shape no implementado** (1): 347 Лучи света — линии.

### 3777338505 — M027 Reze and Power

- **VolumeLight/shape no implementado** (2): 181 Eixos de luz - linear; 178 Eixos de luz - linear.

### 3777601433 — DUAL - NSFW

- **Padding de texto vectorial en cadena** (1): 35 D a y: 128.00000 128.00000.

### 3777864954 — 绮梦晚夏奥奇传说

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3781595377 — 莫加多尔 · 共坠的渴慕（动态）

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3783744288 — 香迪 · 魅惑的特调饮品

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3783788697 — 华盛顿 · 夜间巡诊

- **Combo sin valor inicial** (1): alignment.
- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3784286394 — 建武 · 妆点，只为今夜

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3784961254 — 君主 · 海滩享受计划

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3785053191 — 约克城II · 交错的温柔时光

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3785545617 — 圣路易斯 · 邮轮上的诱人午后

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3789816832 — Nino Nakano, she is very flexible

- **VolumeLight/shape no implementado** (2): 898 Eixos de luz - linear; 789 Eixos de luz - linear.

### 3796799777 — 冬日街

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3799142774 — Rhine Lab · 莱茵生命交互桌面 · Interactive Desktop

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 3801244014 — Hinata Hyuga (2)丨4K丨DarK

- **Padding de texto vectorial en cadena** (6): 1875 ™DAY DATE TIME: 32.00000 32.00000; 1876 ™Clock: 32.00000 32.00000; 1877 ™Date: 32.00000 32.00000; 1879 ➤Sound: 32.00000 32.00000; 1885 ➤Sound: 32.00000 32.00000; 1889 ➤Sound: 32.00000 32.00000.

### 3801329407 — Kafka - Honkai Star Rail 4K

- **VolumeLight/shape no implementado** (1): 88 Rayos de luz: esquina.

### 3803547930 — 海绵宝宝｜章鱼哥的上班日常

- **Padding de texto vectorial en cadena** (5): 188 时钟: 32.00000 32.00000; 191 秒钟: 32.00000 32.00000; 192 时段: 32.00000 32.00000; 193 日期: 32.00000 32.00000; 194 星期: 32.00000 32.00000.

### 3804035019 — Girl · Dark Background · Dark & Colored Versions · 4K

- **Padding de texto vectorial en cadena** (3): 363 Clock: 32.00000 32.00000; 372 D a y: 32.00000 32.00000; 378 Date: 32.00000 32.00000.

### 3816902511 — 废土骑行 · Wasteland Ride · 荒野の旅

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 803212581 — Countdown Timer

- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

### 850923796 — Audio Scratchboard

- **Opciones de combo incompatibles** (2): animateWhenSilent: {'label': 'Do Nothing', 'value': False}; animateWhenSilent: {'label': 'Animate', 'value': True}.
- **Valor inicial de combo incompatible** (1): animateWhenSilent: True.
- **Fondo web: riesgo de compatibilidad del backend** (1): Compatibilidad del backend web pendiente de prueba individual; no equivale a fallo demostrado de este proyecto.

## Evidencia histórica por fondo

Cada ejemplo conserva archivo, línea y mensaje. Las repeticiones cuentan líneas coincidentes, no número de caídas. El ID se atribuye al último `Running with:` del mismo log; con procesos que compartan el archivo esta atribución puede ser ambigua. Las líneas anteriores al primer arranque identificable no se atribuyen a ningún fondo.

### 1081733658 — Customizable Module Visualizer

- **Excepción fatal, abort o fallo de segmentación**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:969`: pure virtual method called
  - `wallpaperengine_eDP-1.log:970`: terminate called without an active exception
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:964`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:965`: Fullscreen detection not supported by your Wayland compositor

### 1364515189 — CPC Flag (Lighter)

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:973`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:974`: Fullscreen detection not supported by your Wayland compositor

### 1545463512 — Pokemon

- **Intentos de decodificación Vulkan/CUDA fallidos**: 7 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1659`: Cannot load libcuda.so.1
  - `wallpaperengine_HDMI-A-1.log:1661`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_HDMI-A-1.log:1662`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1657`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1658`: Fullscreen detection not supported by your Wayland compositor

### 1664802886 — Pokemon

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:681`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:682`: Fullscreen detection not supported by your Wayland compositor

### 1706318451 — PokemonSliver

- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:301`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:687`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:302`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:688`: Fullscreen detection not supported by your Wayland compositor

### 2167703666 — Pokémon Crystal - New Bark Town/Home

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1675`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1676`: Fullscreen detection not supported by your Wayland compositor

### 2168640648 — Pokemon Black / White 2 - Join Avenue

- **Errores DBus repetidos**: 35347 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2155`: DBus error: El objeto no existe en la ruta «/org/mpris/MediaPlayer2» (org.freedesktop.DBus.Error.UnknownMethod)
  - `wallpaperengine_eDP-1.log.1:2156`: DBus error: El objeto no existe en la ruta «/org/mpris/MediaPlayer2» (org.freedesktop.DBus.Error.UnknownMethod)
  - `wallpaperengine_eDP-1.log.1:2157`: DBus error: El objeto no existe en la ruta «/org/mpris/MediaPlayer2» (org.freedesktop.DBus.Error.UnknownMethod)
- **Aviso GLEW: continúa con EGL**: 4 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2146`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:2153`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:37504`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 4 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2147`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:2154`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:37505`: Fullscreen detection not supported by your Wayland compositor

### 2172073471 — Pokemon HeartGold / SoulSilver - Olivine City

- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1681`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_HDMI-A-1.log:1687`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1682`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_HDMI-A-1.log:1688`: Fullscreen detection not supported by your Wayland compositor

### 2176774204 — Mt. Silver / Pokemon Heartgold

- **Errores DBus repetidos**: 1089661 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:37571`: DBus error: Remote peer disconnected (org.freedesktop.DBus.Error.NoReply)
  - `wallpaperengine_eDP-1.log.1:37572`: DBus error: The name is not activatable (org.freedesktop.DBus.Error.ServiceUnknown)
  - `wallpaperengine_eDP-1.log.1:37573`: DBus error: The name is not activatable (org.freedesktop.DBus.Error.ServiceUnknown)
- **Aviso GLEW: continúa con EGL**: 7 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:37567`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:651601`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:651607`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 7 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:37568`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:651602`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:651608`: Fullscreen detection not supported by your Wayland compositor

### 2412448157 — Coding Desk

- **Excepción fatal, abort o fallo de segmentación**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:661`: terminate called after throwing an instance of 'nlohmann::json_abi_v3_11_3::detail::type_error'
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:666`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Excepción de tipos JSON o propiedad obligatoria ausente**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:662`: what():  [json.exception.type_error.302] type must be number, but is string
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:667`: Fullscreen detection not supported by your Wayland compositor

### 2413271262 — Hinata Hyuga B

- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:25`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:3`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:26`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:4`: Fullscreen detection not supported by your Wayland compositor

### 2836178866 — Grand Blue Diving Shop (Night Time)

- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:354`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1127324`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Luces no soportadas en ejecución**: 6 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:351`: Light objects are not supported yet
  - `wallpaperengine_eDP-1.log:352`: Light objects are not supported yet
  - `wallpaperengine_eDP-1.log:353`: Light objects are not supported yet
- **Tipo de objeto desconocido en ejecución**: 6 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:357`: Unknown object type, creating placeholder, empty object: 65
  - `wallpaperengine_eDP-1.log:358`: Unknown object type, creating placeholder, empty object: 68
  - `wallpaperengine_eDP-1.log:359`: Unknown object type, creating placeholder, empty object: 69
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:355`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1127325`: Fullscreen detection not supported by your Wayland compositor

### 2840380808 — Yelan Xray +18 -- Genshin Impact

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1127315`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1127316`: Fullscreen detection not supported by your Wayland compositor

### 2891436791 — Cat

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:344`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:345`: Fullscreen detection not supported by your Wayland compositor

### 2914405895 — 你在盯着哪里看？

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1127771`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1127772`: Fullscreen detection not supported by your Wayland compositor

### 3088099655 — terminal · world clock + countdown [4K]

- **Excepción fatal, abort o fallo de segmentación**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:386`: terminate called after throwing an instance of 'nlohmann::json_abi_v3_11_3::detail::type_error'
  - `wallpaperengine_eDP-1.log.1:1128148`: terminate called after throwing an instance of 'nlohmann::json_abi_v3_11_3::detail::type_error'
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:391`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Excepción de tipos JSON o propiedad obligatoria ausente**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:387`: what():  [json.exception.type_error.302] type must be number, but is string
  - `wallpaperengine_eDP-1.log.1:1128149`: what():  [json.exception.type_error.302] type must be number, but is string
- **Tipo de objeto desconocido en ejecución**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:394`: Unknown object type, creating placeholder, empty object: 72
- **Recurso no encontrado/cargado en ejecución**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:393`: Cannot resolve user texture image for pass filesystem error: Cannot find file: Success [image]
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:392`: Fullscreen detection not supported by your Wayland compositor

### 3577490812 — Image_1759209041166（X-ray）

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:9`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:10`: Fullscreen detection not supported by your Wayland compositor

### 3598619616 — LEON  VAM- Static Wallpaper X-Ray +18 1

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1522`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1523`: Fullscreen detection not supported by your Wayland compositor

### 3599477480 — Stellar Blade EVE Bunny 18+ [4k]

- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1654`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1130616`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1655`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1130617`: Fullscreen detection not supported by your Wayland compositor

### 3600129651 — Wilhelmina Iron Monarch 1 / Brown Dust 2, 브라운더스트2, ブラウンダスト2, 棕色塵埃2, 棕色尘埃2

- **Intentos de decodificación Vulkan/CUDA fallidos**: 14 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2082`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:2086`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log.1:2087`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2080`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1128301`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2081`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1128302`: Fullscreen detection not supported by your Wayland compositor

### 3612171954 — 日向雏田环绕动效

- **Intentos de decodificación Vulkan/CUDA fallidos**: 7 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1504`: Cannot load libcuda.so.1
  - `wallpaperengine_HDMI-A-1.log:1507`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_HDMI-A-1.log:1508`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1502`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1503`: Fullscreen detection not supported by your Wayland compositor

### 3612647859 — 水上樂園女王 - 威廉明娜 / BrownDust2 / 棕色塵埃2

- **Desincronización de audio y vídeo**: 4 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2119`: Audio/Video desynchronisation detected! Possible reasons include too slow
  - `wallpaperengine_eDP-1.log.1:37531`: Audio/Video desynchronisation detected! Possible reasons include too slow
  - `wallpaperengine_eDP-1.log.1:37539`: Audio/Video desynchronisation detected! Possible reasons include too slow
- **Intentos de decodificación Vulkan/CUDA fallidos**: 28 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:685`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log:689`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log:690`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 4 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:683`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:2102`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:37514`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 4 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:684`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:2103`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:37515`: Fullscreen detection not supported by your Wayland compositor

### 3645032120 — 波雅汉库克动态壁纸

- **Intentos de decodificación Vulkan/CUDA fallidos**: 7 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1564`: Cannot load libcuda.so.1
  - `wallpaperengine_HDMI-A-1.log:1567`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_HDMI-A-1.log:1568`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1562`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1563`: Fullscreen detection not supported by your Wayland compositor

### 3657975068 — [熟肉][中英字幕]神之款待：希芙的拥抱-Divine Hospitality Sif's Embrace-Dezmall

- **Intentos de decodificación Vulkan/CUDA fallidos**: 7 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1541`: Cannot load libcuda.so.1
  - `wallpaperengine_HDMI-A-1.log:1546`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_HDMI-A-1.log:1547`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1539`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1540`: Fullscreen detection not supported by your Wayland compositor

### 3660392544 — Eve · Stellar Blade

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1531`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1532`: Fullscreen detection not supported by your Wayland compositor

### 3683255353 — horizon-sky-wanderer-moewalls-com

- **Desincronización de audio y vídeo**: 27 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:36`: Audio/Video desynchronisation detected! Possible reasons include too slow
  - `wallpaperengine_eDP-1.log:42`: Audio/Video desynchronisation detected! Possible reasons include too slow
  - `wallpaperengine_eDP-1.log:48`: Audio/Video desynchronisation detected! Possible reasons include too slow
- **Intentos de decodificación Vulkan/CUDA fallidos**: 21 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:19`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log:24`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log:25`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 3 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:17`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log:154`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log:182`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 3 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:18`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log:155`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log:183`: Fullscreen detection not supported by your Wayland compositor

### 3686075716 — 男厕所束缚调教肉便器

- **Intentos de decodificación Vulkan/CUDA fallidos**: 7 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1481`: Cannot load libcuda.so.1
  - `wallpaperengine_HDMI-A-1.log:1486`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_HDMI-A-1.log:1487`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1479`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:1480`: Fullscreen detection not supported by your Wayland compositor

### 3721300967 — Komi-Shouko-By-Suna丨R18丨4K丨Black

- **Aviso GLEW: continúa con EGL**: 7 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:478`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_HDMI-A-1.log:487`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1131239`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Tipo de objeto desconocido en ejecución**: 130 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:480`: Unknown object type, creating placeholder, empty object: 25
  - `wallpaperengine_HDMI-A-1.log:489`: Unknown object type, creating placeholder, empty object: 25
  - `wallpaperengine_HDMI-A-1.log:493`: Unknown object type, creating placeholder, empty object: 410
- **Detección de pantalla completa no soportada**: 7 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:479`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_HDMI-A-1.log:488`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1131240`: Fullscreen detection not supported by your Wayland compositor

### 3762254115 — 胜利女神NIKKE

- **Intentos de decodificación Vulkan/CUDA fallidos**: 7 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1131222`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:1131224`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log.1:1131225`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1131220`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1131221`: Fullscreen detection not supported by your Wayland compositor

### 3772073136 — Terraria Goldfish Walker（1080p）

- **Excepción fatal, abort o fallo de segmentación**: 3 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:286`: terminate called after throwing an instance of 'nlohmann::json_abi_v3_11_3::detail::type_error'
  - `wallpaperengine_eDP-1.log.1:1132800`: terminate called after throwing an instance of 'nlohmann::json_abi_v3_11_3::detail::type_error'
  - `wallpaperengine_eDP-1.log.1:1132804`: terminate called after throwing an instance of 'nlohmann::json_abi_v3_11_3::detail::type_error'
- **Intentos de decodificación Vulkan/CUDA fallidos**: 14 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:293`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log:298`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log:299`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:291`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log:364`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Excepción de tipos JSON o propiedad obligatoria ausente**: 3 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:287`: what():  [json.exception.type_error.302] type must be number, but is string
  - `wallpaperengine_eDP-1.log.1:1132801`: what():  [json.exception.type_error.302] type must be number, but is string
  - `wallpaperengine_eDP-1.log.1:1132805`: what():  [json.exception.type_error.302] type must be number, but is string
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:292`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log:365`: Fullscreen detection not supported by your Wayland compositor

### 3776653850 — Asuka Langley & Night bedroom — 惣流・アスカ・ラングレ

- **Excepción fatal, abort o fallo de segmentación**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:705`: terminate called after throwing an instance of 'nlohmann::json_abi_v3_11_3::detail::type_error'
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:711`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Excepción de tipos JSON o propiedad obligatoria ausente**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:706`: what():  [json.exception.type_error.302] type must be number, but is string
- **Luces no soportadas en ejecución**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:704`: VolumeLight objects are not supported yet
  - `wallpaperengine_eDP-1.log:710`: VolumeLight objects are not supported yet
- **Tipo de objeto desconocido en ejecución**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:714`: Unknown object type, creating placeholder, empty object: 347
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:712`: Fullscreen detection not supported by your Wayland compositor

### 3777008325 — MOMO

- **Intentos de decodificación Vulkan/CUDA fallidos**: 14 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:5`: Cannot load libcuda.so.1
  - `wallpaperengine_HDMI-A-1.log:9`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_HDMI-A-1.log:10`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:3`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1131198`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:4`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1131199`: Fullscreen detection not supported by your Wayland compositor

### 3777338505 — M027 Reze and Power

- **Aviso GLEW: continúa con EGL**: 3 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:817`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:209`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:697`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Luces no soportadas en ejecución**: 6 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:815`: VolumeLight objects are not supported yet
  - `wallpaperengine_eDP-1.log:816`: VolumeLight objects are not supported yet
  - `wallpaperengine_eDP-1.log.1:207`: VolumeLight objects are not supported yet
- **Tipo de objeto desconocido en ejecución**: 6 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:823`: Unknown object type, creating placeholder, empty object: 181
  - `wallpaperengine_eDP-1.log:826`: Unknown object type, creating placeholder, empty object: 178
  - `wallpaperengine_eDP-1.log.1:215`: Unknown object type, creating placeholder, empty object: 181
- **Detección de pantalla completa no soportada**: 3 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:818`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:210`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:698`: Fullscreen detection not supported by your Wayland compositor

### 3777601433 — DUAL - NSFW

- **Excepción fatal, abort o fallo de segmentación**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2076`: terminate called after throwing an instance of 'nlohmann::json_abi_v3_11_3::detail::type_error'
  - `wallpaperengine_eDP-1.log.1:1131009`: terminate called after throwing an instance of 'nlohmann::json_abi_v3_11_3::detail::type_error'
- **Excepción de tipos JSON o propiedad obligatoria ausente**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2077`: what():  [json.exception.type_error.302] type must be number, but is string
  - `wallpaperengine_eDP-1.log.1:1131010`: what():  [json.exception.type_error.302] type must be number, but is string

### 3781792400 — Blue Archive丨蔚蓝档案丨调月莉音丨Tsukatsuki Rio

- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1646`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1131013`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1647`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1131014`: Fullscreen detection not supported by your Wayland compositor

### 3784961254 — 君主 · 海滩享受计划

- **Símbolo close ausente al iniciar backend web**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:2130`: close symbol missing

### 3786137579 — 碧蓝航线Azur Laneアズールレーン

- **Intentos de decodificación Vulkan/CUDA fallidos**: 14 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:225`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:227`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log.1:228`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:223`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1131021`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:224`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1131022`: Fullscreen detection not supported by your Wayland compositor

### 3789790717 — ANIME GIRL - SADAKO

- **Desincronización de audio y vídeo**: 4 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1214`: Audio/Video desynchronisation detected! Possible reasons include too slow
  - `wallpaperengine_eDP-1.log.1:1628`: Audio/Video desynchronisation detected! Possible reasons include too slow
  - `wallpaperengine_eDP-1.log.1:1127356`: Audio/Video desynchronisation detected! Possible reasons include too slow
- **Intentos de decodificación Vulkan/CUDA fallidos**: 46 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:713`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:715`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:720`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
- **Aviso GLEW: continúa con EGL**: 5 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:711`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:733`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1192`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Tipo de objeto desconocido en ejecución**: 4 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:752`: Unknown object type, creating placeholder, empty object: 159
  - `wallpaperengine_eDP-1.log.1:1211`: Unknown object type, creating placeholder, empty object: 159
  - `wallpaperengine_eDP-1.log.1:1127351`: Unknown object type, creating placeholder, empty object: 159
- **Recurso no encontrado/cargado en ejecución**: 5 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:719`: Cannot resolve user texture video for pass filesystem error: Cannot find file: Success [video]
  - `wallpaperengine_eDP-1.log.1:741`: Cannot resolve user texture video for pass filesystem error: Cannot find file: Success [video]
  - `wallpaperengine_eDP-1.log.1:1200`: Cannot resolve user texture video for pass filesystem error: Cannot find file: Success [video]
- **Detección de pantalla completa no soportada**: 5 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:712`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:734`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1193`: Fullscreen detection not supported by your Wayland compositor

### 3789816832 — Nino Nakano, she is very flexible

- **Aviso GLEW: continúa con EGL**: 4 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:248`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log:737`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log:777`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Luces no soportadas en ejecución**: 8 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:246`: VolumeLight objects are not supported yet
  - `wallpaperengine_eDP-1.log:247`: VolumeLight objects are not supported yet
  - `wallpaperengine_eDP-1.log:735`: VolumeLight objects are not supported yet
- **Tipo de objeto desconocido en ejecución**: 8 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:253`: Unknown object type, creating placeholder, empty object: 898
  - `wallpaperengine_eDP-1.log:281`: Unknown object type, creating placeholder, empty object: 789
  - `wallpaperengine_eDP-1.log:743`: Unknown object type, creating placeholder, empty object: 898
- **Error de compilación/preparación de shader**: 32 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:254`: GLSL vertex unit parsing Failed: ERROR: 0:157: '#endif' : mismatched statements
  - `wallpaperengine_eDP-1.log:256`: ERROR: 2 compilation errors.  No code generated.
  - `wallpaperengine_eDP-1.log:259`: 0:1(1): error: syntax error, unexpected end of file
- **Detección de pantalla completa no soportada**: 4 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:249`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log:738`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log:778`: Fullscreen detection not supported by your Wayland compositor

### 3791364468 — 148145549_p0

- **Aviso GLEW: continúa con EGL**: 3 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:720`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:2133`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:2138`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 3 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:721`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:2134`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:2139`: Fullscreen detection not supported by your Wayland compositor

### 3792804757 — 耀佳音 Astra Yao 4k

- **Desincronización de audio y vídeo**: 3 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:443`: Audio/Video desynchronisation detected! Possible reasons include too slow
  - `wallpaperengine_eDP-1.log.1:1131108`: Audio/Video desynchronisation detected! Possible reasons include too slow
  - `wallpaperengine_eDP-1.log.1:1131144`: Audio/Video desynchronisation detected! Possible reasons include too slow
- **Intentos de decodificación Vulkan/CUDA fallidos**: 21 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:427`: Cannot load libcuda.so.1
  - `wallpaperengine_HDMI-A-1.log:431`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_HDMI-A-1.log:432`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 3 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:425`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1131090`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1131126`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 3 líneas coincidentes.
  - `wallpaperengine_HDMI-A-1.log:426`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1131091`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1131127`: Fullscreen detection not supported by your Wayland compositor

### 3792926059 — 蕾米埃尔 丹 Remielle Dan 绝区零 Zenless Zone Zero

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1131083`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1131084`: Fullscreen detection not supported by your Wayland compositor

### 3793228943 — Ralph Lauren ART

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1132793`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1132794`: Fullscreen detection not supported by your Wayland compositor

### 3794626785 — M069 frienre e fern

- **Aviso GLEW: continúa con EGL**: 6 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:840`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:242`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1637`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 6 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:841`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:243`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1638`: Fullscreen detection not supported by your Wayland compositor

### 3795054117 — [H69Verse]甘露寺蜜璃无限城 第二章 Mitsuri Infinitys Pleasure Castle

- **Desincronización de audio y vídeo**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128222`: Audio/Video desynchronisation detected! Possible reasons include too slow
- **Intentos de decodificación Vulkan/CUDA fallidos**: 7 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128207`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:1128210`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log.1:1128211`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128205`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128206`: Fullscreen detection not supported by your Wayland compositor

### 3798304439 — miku x teto face check

- **Intentos de decodificación Vulkan/CUDA fallidos**: 14 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:851`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log:855`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log:856`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:849`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:251`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:850`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:252`: Fullscreen detection not supported by your Wayland compositor

### 3799669491 — 第七史诗 - 里安娜&路西艾拉

- **Intentos de decodificación Vulkan/CUDA fallidos**: 8 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:731`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:759`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:762`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:728`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:757`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:729`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:758`: Fullscreen detection not supported by your Wayland compositor

### 3801329407 — Kafka - Honkai Star Rail 4K

- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:832`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1184`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Luces no soportadas en ejecución**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:831`: VolumeLight objects are not supported yet
  - `wallpaperengine_eDP-1.log.1:1183`: VolumeLight objects are not supported yet
- **Tipo de objeto desconocido en ejecución**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:835`: Unknown object type, creating placeholder, empty object: 88
  - `wallpaperengine_eDP-1.log.1:1187`: Unknown object type, creating placeholder, empty object: 88
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:833`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1185`: Fullscreen detection not supported by your Wayland compositor

### 3802401381 — nami sx -alexandr

- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:676`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1128156`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:677`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1128157`: Fullscreen detection not supported by your Wayland compositor

### 3802576044 — 交错战线

- **Intentos de decodificación Vulkan/CUDA fallidos**: 7 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128188`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:1128190`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log.1:1128191`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128186`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128187`: Fullscreen detection not supported by your Wayland compositor

### 3802742966 — Demon Queen [Dark Ritual] 4K Anime

- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128323`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Error de compilación/preparación de shader**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128921`: Failed to setup object 717: 0:108(2): error: initializer of type vec4 cannot be assigned to variable of type vec2
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1128324`: Fullscreen detection not supported by your Wayland compositor

### 3816902511 — 废土骑行 · Wasteland Ride · 荒野の旅

- **Símbolo close ausente al iniciar backend web**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:314`: close symbol missing

### 3817708280 — 小野寺小咲-Onodera kosaki

- **Intentos de decodificación Vulkan/CUDA fallidos**: 7 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1132737`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log.1:1132739`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log.1:1132740`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1132735`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 1 líneas coincidentes.
  - `wallpaperengine_eDP-1.log.1:1132736`: Fullscreen detection not supported by your Wayland compositor

### 3818461208 — Suspended Reverie

- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:3`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1132808`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:4`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1132809`: Fullscreen detection not supported by your Wayland compositor

### 3819090543 — 雏田-穿搭轮换

- **Desincronización de audio y vídeo**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:334`: Audio/Video desynchronisation detected! Possible reasons include too slow
  - `wallpaperengine_eDP-1.log.1:1132771`: Audio/Video desynchronisation detected! Possible reasons include too slow
- **Intentos de decodificación Vulkan/CUDA fallidos**: 14 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:319`: Cannot load libcuda.so.1
  - `wallpaperengine_eDP-1.log:322`: [ffmpeg/video] h264: Device does not support the VK_KHR_video_decode_queue extension!
  - `wallpaperengine_eDP-1.log:323`: [ffmpeg/video] h264: Failed setup for format vulkan: hwaccel initialisation returned error.
- **Aviso GLEW: continúa con EGL**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:317`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
  - `wallpaperengine_eDP-1.log.1:1132754`: Failed to initialize GLEW, but continuing with EGL context: No GLX display
- **Detección de pantalla completa no soportada**: 2 líneas coincidentes.
  - `wallpaperengine_eDP-1.log:318`: Fullscreen detection not supported by your Wayland compositor
  - `wallpaperengine_eDP-1.log.1:1132755`: Fullscreen detection not supported by your Wayland compositor

## Límites y seguimiento

- No se compilaron todos los shaders ni se ejecutaron scripts web/SceneScript; esos errores requieren un ensayo por fondo con el motor y un registro independiente.
- La tabla de paquetes comprueba estructura y límites, pero no decodifica todas las texturas, sonidos ni modelos.
- Los presets válidos heredan el tipo de su dependencia y no se consideran incompletos por carecer de `type` o `file`. La inspección de sus recursos se recoge en la entrada del proyecto padre; no se ha probado individualmente la aplicación de cada preset.
- Comparar marcas de `known_bad.json` con resultados nuevos antes de retirar o añadir fallos conocidos.
- Datos completos: `wallpapers.json` y `videos.json`; scripts de lectura: `scan_wallpapers.py` y `probe_videos.py`.
