# Segundo lote de compatibilidad de shaders

Revisión de 400 carpetas, 239 paquetes y 2.908 entradas de shaders (860 combinaciones de ruta y hash). El inventario estático final marca 27 variantes candidatas; son indicios, no 27 errores de ejecución certificados.

## Cambios aplicados

**19 fondos adicionales; 32 recursos de shader corregidos.** Las reglas verifican SHA256 y nombre de recurso bajo shaders/workshop/<id>/effects/, independientemente del ID del fondo o del efecto.

- Barras de audio: segunda versión del vertex y dos variantes del fragmento; mismo #endif huérfano y escritura sobre entradas.
- Onda y osciloscopio: coordenadas mutables y máscara escalar; userBalance y lowBalanceMultipier se calculan al entrar en main porque dependen de uniforms.
- Movimiento de ojos: se elimina el #endif huérfano y se usan las componentes xy de transformedCursorPosition.
- Reutilización de test_shader.frag ya verificado en Demon Queen bajo otros IDs de efecto.

Cada paquete conserva scene.pkg.bak_original; los backups preexistentes se preservan. Comprobada idempotencia. En 2919854127 también se normalizaron dos campos padding mediante la reparación existente, indicado en el informe. No se cambió la asignación del escritorio, project.json ni sus propiedades. Se crearon los locks habituales de reparación.

| Fondo | Recursos corregidos |
|---|---|
| 2407172811 | Simple_Audio_Bars.vert, Simple_Audio_Bars.frag |
| 2919854127 | test_shader.frag |
| 2973821653 | test_shader.frag |
| 3001442160 | test_shader.frag |
| 3086490516 | test_shader.frag |
| 3151551777 | Simple_Audio_Bars.frag, Simple_Audio_Bars.vert |
| 3208556055 | sine_wave.frag, audio_responsive_oscilloscope.frag |
| 3211109911 | test_shader.frag |
| 3477054430 | test_shader.frag |
| 3526096300 | Simple_Audio_Bars.frag, Simple_Audio_Bars.vert |
| 3535044281 | Simple_Audio_Bars.vert, Simple_Audio_Bars.frag, iris_movement__.vert |
| 3561551763 | test_shader.frag |
| 3563096027 | Simple_Audio_Bars.vert, Simple_Audio_Bars.frag |
| 3576436521 | test_shader.frag |
| 3590434671 | iris_movement__.vert |
| 3611439897 | Simple_Audio_Bars.vert, Simple_Audio_Bars.frag |
| 3637044670 | Simple_Audio_Bars.frag, Simple_Audio_Bars.vert, Simple_Audio_Bars.frag, Simple_Audio_Bars.vert |
| 3684060242 | Simple_Audio_Bars.vert, Simple_Audio_Bars.frag |
| 3701356561 | Simple_Audio_Bars.vert, Simple_Audio_Bars.frag |

## Evidencias y límites

- 98 pruebas pasan con ResourceWarning como error.
- Preprocesador: las siete variantes vertex con directivas sobrantes fallan antes y pasan después (algunas versiones se repiten en varios fondos). Resultado en shader_preprocessor_verification.json.
- Motor real en copias: 3208556055 pierde los errores de objetos 330, 295 y 203; 3535044281 y 3590434671 pierden los errores de movimiento de ojos en objetos 21 y 17. Copias reparadas de 2407172811 y 3151551777 sin errores GLSL. En estos dos los originales tampoco mostraron errores durante el ensayo: el recurso afectado no necesariamente estaba activo.
- No se ejecutaron los 19 fondos reparados individualmente: las versiones idénticas se reutilizan por hash. Esto certifica las correcciones descritas, no equivalencia visual completa, reacción al audio ni soporte de todas las funciones del fondo.
- Chromatic aberration, old film, cutout vignette y lens flare no mostraron errores GLSL en los representantes probados. No se modificaron por el mero hallazgo estático.
- Quedan problemas de SceneScript: Vec3 no definido y TypeError en 3208556055; acceso a name de objeto indefinido en 2947399331. Comunicados a Claude, junto a luces y texturas configurables ya pendientes.

## Reproducción

`python3 audit/compatibility/scan_shaders.py` realiza solo lectura; ejecutarlo de nuevo después de reparar produce un inventario distinto. El JSON guardado aquí corresponde a la revisión previa a aplicar este lote.

`WPE_REPAIR_REPORT=shader_batch_verification.json python3 audit/compatibility/verify_repairs.py 2407172811 3151551777 3208556055 3535044281 3590434671` comprueba copias, usando backups para el caso original. Necesita una sesión gráfica.

`python3 audit/compatibility/apply_shader_batch.py` enumera recursos reconocidos; `--apply` realiza las reparaciones con backup. applied_shader_batch.json conserva hashes de antes/después y de las copias originales.
