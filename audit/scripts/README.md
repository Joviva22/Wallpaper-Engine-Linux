# Regresión de scripts de texto

Se han aislado tres fallos de scripts reales. Los fondos y el motor no se han modificado.

| Fondo | Objeto | Causa identificada |
|---|---|---|
| Terminal `3088099655` | 97 (`cd`) | El `thisScene` local de `registerTextLayer` oculta el objeto global y no tiene `getLayer`. |
| `2947399331` | 349 (`Clock`) | El `engine` local no tiene `userProperties`. El EngineObject global tampoco implementa actualmente esa propiedad. |
| `3208556055` | 608 (`ACTIVE: Packet Loss`) | Se crean vectores con `new Vec3`, pero el constructor no está publicado globalmente. |

`prepare_cases.py` extrae el wrapper JavaScript directamente de `ScriptEngine.cpp` y los scripts reales de `scene.pkg`. Guarda el hash de la fuente y de cada script. `replay_cases.cjs` reproduce los tres errores en una VM Node con tiempo limitado.

```bash
python3 audit/scripts/prepare_cases.py
node audit/scripts/replay_cases.cjs
```

La segunda variante del ensayo sustituye los shims locales por los objetos globales y simula las API pendientes. Los tres casos pasan así. **Es una prueba lógica de la causa y del contrato necesario, no una reparación instalada ni una validación de los adaptadores C++/QuickJS.**

## Integración recomendada para Claude

1. Evitar que el wrapper de textos oculte `globalThis.thisScene`/`engine`. Conservar los aliases de tiempo existentes sin perder métodos y getters nativos. No usar simplemente `Object.create(nativeObject)` para métodos que necesitan el receptor nativo (`get_layer` recupera el objeto opaco desde `this`).
2. Publicar `engine.userProperties` con los valores efectivos de las propiedades, incluidas las personalizaciones del usuario. Añadir el cambio de propiedades si el motor lo soporta; devolver un objeto vacío solo escondería el error.
3. En VectorAdapter, publicar el constructor `Vec2/Vec3/Vec4` en el objeto global antes de liberar la referencia local `ctor`. Ya se construyen los prototipos, pero el constructor se libera sin publicarlo globalmente. Verificar construcción, operaciones, valores de retorno y liberación de referencias con QuickJS real.
4. Implementar `engine.registerAudioBuffers` y su actualización con datos de AudioContext. El EngineObject actual no lo implementa; quitar el shim no basta para los textos de audio. No devolver buffers permanentemente a cero como supuesto arreglo.
5. Verificar `thisLayer`: el wrapper actual es un objeto independiente con solo `text`. Escribir `visible`/`color` desde los scripts no implica actualizar la capa renderizada. Usar un enlace con la capa real y conservar el contrato `update(value)`.
6. Completar los logs de excepciones con ID/nombre de capa y stack. Ahora varios fondos producen la misma línea `layer.update: TypeError` sin señalar el origen.

Verificación pendiente: ejecutar estos tres contratos en QuickJS y después los fondos originales con el motor compilado, comprobando también el resultado visual. Las fuentes del motor y sus parches siguen reservados a Claude.
