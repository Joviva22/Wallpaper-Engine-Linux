"""Genera el inventario legible a partir de las comprobaciones locales."""
import collections
import json
from pathlib import Path
base=Path(__file__).resolve().parent
r=json.loads((base/'wallpapers.json').read_text())
v=json.loads((base/'videos.json').read_text())
labels={
 'PRESET_PARENT_MISSING':'Preset con proyecto padre ausente',
 'PKG_DUPLICATE_ENTRY':'Nombre duplicado en la tabla del paquete; advertencia de estructura',
 'PROJECT_INVALID':'Proyecto ausente o JSON inválido',
 'TITLE_INVALID':'Título con tipo inválido',
 'META_PATH_INVALID':'Ruta principal o miniatura no declarada correctamente',
 'FILE_MISSING':'Archivo declarado ausente',
 'PROPERTIES_INVALID':'Estructura de propiedades inválida',
 'COMBO_VALUE_MISSING':'Combo sin valor inicial',
 'COMBO_VALUE_TYPE':'Valor inicial de combo incompatible',
 'COMBO_OPTIONS_INVALID':'Opciones de combo incompatibles',
 'WEB_BACKEND_RISK':'Fondo web: riesgo de compatibilidad del backend',
 'SCENE_MISSING':'Escena no encontrada',
 'TEXT_PADDING_STRING':'Padding de texto vectorial en cadena',
 'LIGHT_UNSUPPORTED':'Luz no implementada por el motor local examinado',
 'VOLUME_LIGHT_UNSUPPORTED':'VolumeLight/shape no implementado',
 'EFFECT_REF_UNRESOLVED':'Referencia de efecto no resuelta en paquete/carpeta/assets sueltos',
 'SCENE_OR_PKG_INVALID':'Escena o estructura del paquete inválida',
 'OBJECT_INVALID':'Objeto de escena inválido',
 'TYPE_UNRECOGNIZED':'Tipo ausente o no reconocido',
 'LOG_JSON':'Excepción de tipos JSON o propiedad obligatoria ausente',
 'LOG_SHADER':'Error de compilación/preparación de shader',
 'LOG_WEB_SYMBOL':'Símbolo close ausente al iniciar backend web',
 'LOG_ABORT':'Excepción fatal, abort o fallo de segmentación',
 'LOG_LIGHT':'Luces no soportadas en ejecución',
 'LOG_OBJECT':'Tipo de objeto desconocido en ejecución',
 'LOG_RESOURCE':'Recurso no encontrado/cargado en ejecución',
 'LOG_DBUS':'Errores DBus repetidos',
 'LOG_AV_SYNC':'Desincronización de audio y vídeo',
 'LOG_DECODER':'Intentos de decodificación Vulkan/CUDA fallidos',
 'LOG_EGL_FALLBACK':'Aviso GLEW: continúa con EGL',
 'LOG_WAYLAND':'Detección de pantalla completa no soportada',
}
def esc(s):return str(s).replace('|','·').replace('\n',' ').replace('\r',' ')
lines=['# Inventario de errores de todos los wallpapers locales','',f"Revisión: {r['date']}. Biblioteca: `{r['library']}`.",'',f"Se revisaron **{r['count']} carpetas**: "+', '.join(f'{n} {t}' for t,n in sorted(r['type_counts'].items()))+'.','',
'La revisión lee `project.json`, la tabla y los límites de las entradas de `scene.pkg`, el JSON de escena, objetos de luz/texto, referencias de efectos y los logs conservados. Los vídeos se inspeccionaron con `ffprobe`. No se cambiaron fondos, paquetes ni configuración. No se aplicaron los 400 fondos al escritorio: los hallazgos estáticos describen incompatibilidades posibles o concretas de formato, mientras los logs son evidencia histórica y pueden corresponder a versiones anteriores del fondo o del motor. No detectar un error no garantiza aspecto visual correcto ni ausencia de errores de scripts.','',
f"**Vídeos:** {len(v)} inspeccionados; {sum(bool(x.get('error') or x.get('returncode') or not x.get('has_video')) for x in v)} con error o sin pista; {sum(bool(x.get('stderr')) for x in v)} con advertencias. Se comprobaron contenedor y pistas, sin decodificar cada fotograma.",'',
'## Distintos problemas detectados','', '| Código | Problema | Fondos afectados | Evidencia |','| --- | --- | ---: | --- |']
counts=collections.Counter(code for row in r['rows'] for code in {f['code'] for f in row['findings']})
for code,n in sorted(counts.items()):
 lines.append(f'| `{code}` | {labels.get(code,code)} | {n} | Archivos actuales |')
logcounts=collections.Counter(code for row in r['rows'] for code in row['logs'])
for code,n in sorted(logcounts.items()):
 lines.append(f'| `{code}` | {labels.get(code,code)} | {n} | Logs históricos |')
lines += ['',
'Interpretación: `WEB_BACKEND_RISK` no es un error individual demostrado. `LIGHT_UNSUPPORTED` y `VOLUME_LIGHT_UNSUPPORTED` implican pérdida visual, no necesariamente un cierre. Las referencias no resueltas requieren comprobar también recursos empaquetados globales o dependencias antes de declararlas ausentes. Los avisos de decodificador, EGL y pantalla completa pueden permitir que la reproducción continúe. Una entrada duplicada en el paquete no demuestra corrupción ni un cierre: debe comprobarse qué versión del recurso elige el motor. Las categorías pueden solaparse: un mismo fondo puede tener varios problemas.',
'', 'Los valores numéricos de combo son admitidos por el parser local examinado; no se han clasificado como error por ser números. Los valores booleanos sí son incompatibles con su conversión a cadena.', '',
'## Inventario completo','', '| ID | Título | Tipo | Hallazgos en archivos actuales | Categorías en logs históricos |', '| --- | --- | --- | --- | --- |']
for row in r['rows']:
 codes=sorted({f['code'] for f in row['findings']})
 lines.append(f"| {row['id']} | {esc(row['title'])} | {esc(row['type']) + (' (preset de ' + row['dependency'] + ')' if row.get('preset') else '')} | {', '.join(codes) or 'Sin hallazgos en las comprobaciones realizadas'} | {', '.join(sorted(row['logs'])) or 'Sin errores identificados en los logs conservados'} |")
lines += ['', '## Detalle por fondo con hallazgos en archivos','']
for row in r['rows']:
 if not row['findings']:continue
 lines += [f"### {row['id']} — {esc(row['title'])}",'']
 grouped=collections.defaultdict(list)
 for f in row['findings']:grouped[f['code']].append(f['detail'])
 for code,details in sorted(grouped.items()):
  lines += [f"- **{labels.get(code,code)}** ({len(details)}): "+'; '.join(esc(d) for d in details)+'.']
 lines += ['']
lines += ['## Evidencia histórica por fondo','',
'Cada ejemplo conserva archivo, línea y mensaje. Las repeticiones cuentan líneas coincidentes, no número de caídas. El ID se atribuye al último `Running with:` del mismo log; con procesos que compartan el archivo esta atribución puede ser ambigua. Las líneas anteriores al primer arranque identificable no se atribuyen a ningún fondo.','']
for row in r['rows']:
 if not row['logs']:continue
 lines += [f"### {row['id']} — {esc(row['title'])}",'']
 for code,data in sorted(row['logs'].items()):
  lines += [f"- **{labels.get(code,code)}**: {data['count']} líneas coincidentes."]
  for sample in data['samples']:
   lines += [f"  - `{sample['file']}:{sample['line']}`: {esc(sample['text'])}"]
 lines += ['']
lines += ['## Límites y seguimiento','',
'- No se compilaron todos los shaders ni se ejecutaron scripts web/SceneScript; esos errores requieren un ensayo por fondo con el motor y un registro independiente.',
'- La tabla de paquetes comprueba estructura y límites, pero no decodifica todas las texturas, sonidos ni modelos.',
'- Los presets válidos heredan el tipo de su dependencia y no se consideran incompletos por carecer de `type` o `file`. La inspección de sus recursos se recoge en la entrada del proyecto padre; no se ha probado individualmente la aplicación de cada preset.',
'- Comparar marcas de `known_bad.json` con resultados nuevos antes de retirar o añadir fallos conocidos.',
'- Datos completos: `wallpapers.json` y `videos.json`; scripts de lectura: `scan_wallpapers.py` y `probe_videos.py`.','']
(base/'WALLPAPERS.md').write_text('\n'.join(lines),encoding='utf-8')
print('Informe generado:',base/'WALLPAPERS.md')
print('Categorías estáticas:',dict(counts))
print('Categorías históricas:',dict(logcounts))
