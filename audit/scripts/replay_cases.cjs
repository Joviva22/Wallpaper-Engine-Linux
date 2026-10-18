// Prueba lógica del wrapper extraído. Las API nativas se simulan: no sustituye QuickJS.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
const base = __dirname;
const input = JSON.parse(fs.readFileSync(path.join(base, 'cases.json'), 'utf8'));
const results = [];
for (const item of input.cases) {
  const variants = {};
  for (const proposed of [false, true]) {
    const layers = {discription2: {text: 'Original'}};
    const nativeScene = {getLayer(name) {assert.equal(this, nativeScene); return layers[name];}};
    const sandbox = {__textLayers: {}, __layerSeedProps: {}, __layerSeedText: 'Initial',
      __sceneCtx: {time: 2, dt: 1/60, fps: 60}, thisScene: nativeScene,
      engine: proposed ? {userProperties: {name: 'Test'}, frametime: 1/60, time: 2} : {frametime: 1/60}};
    if (proposed) sandbox.Vec3 = class Vec3 {constructor(x,y,z) {Object.assign(this, {x,y,z});}};
    let code = item.wrapper;
    if (proposed) {
      code = code.replace(/  var thisScene = \{[\s\S]*?\n  \};/, '  var thisScene = globalThis.thisScene;');
      code = code.replace(/  var engine = \{[\s\S]*?\n  \};/, '  var engine = globalThis.engine;');
    }
    const context = vm.createContext(sandbox, {codeGeneration: {strings: false, wasm: false}});
    let error = null;
    try {
      vm.runInContext(code, context, {timeout: 200});
      vm.runInContext('__textLayers[1]._tick();', context, {timeout: 200});
    } catch (err) {error = `${err.name}: ${err.message}`;}
    variants[proposed ? 'proposed_with_mock_api' : 'current_wrapper'] = {error};
    if (proposed) assert.equal(error, null, item.id);
    else assert.ok(error, item.id);
  }
  results.push({id: item.id, object: item.object, reason: item.reason, ...variants});
}
const report = {scope: 'Wrapper C++ extraído + Node VM. Propuesta con API simulada; no está instalada ni valida adaptadores C++/QuickJS.', results};
fs.writeFileSync(path.join(base, 'replay_results.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
