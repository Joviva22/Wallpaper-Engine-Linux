// Nikke Stage: shows up to four Nikke characters at once, chosen from the installed packs.
// Own code; it only uses the Spine web runtimes bundled by the installer (spine = 4.0, spine41 = 4.1)
// and the free character packs managed by scripts/nikke-stage.py.
(function () {
  'use strict';

  var SLOT_COUNT = 4;
  var BASE = '__user/stage/';
  var manifest = { characters: {} };
  var slots = [];
  var latest = null;

  function cssColor(value) {
    // Wallpaper Engine colours are "r g b" in the 0..1 range
    var parts = String(value || '').split(' ').map(Number);
    if (parts.length < 3 || parts.some(isNaN)) return null;
    return 'rgb(' + parts.slice(0, 3).map(function (c) { return Math.round(c * 255); }).join(',') + ')';
  }

  function runtimeFor(code) {
    var entry = manifest.characters[code];
    return entry && entry.version === '4.1' ? window.spine41 : window.spine;
  }

  function prop(props, name, fallback) {
    return props && props[name] && props[name].value !== undefined ? props[name].value : fallback;
  }

  function createSlot(index) {
    var element = document.createElement('div');
    element.className = 'slot';
    element.id = 'slot' + (index + 1);
    document.getElementById('stage').appendChild(element);
    return { index: index, element: element, code: null, loaded: null, player: null, token: 0 };
  }

  function destroyPlayer(slot) {
    slot.token++;
    if (slot.player) {
      try { slot.player.dispose(); } catch (e) { /* ignore */ }
      slot.player = null;
    }
    slot.element.innerHTML = '';
  }

  function loadCharacter(slot, code) {
    destroyPlayer(slot);
    slot.code = code;
    slot.loaded = code;
    if (!code || code === 'none' || !manifest.characters[code]) return;

    var runtime = runtimeFor(code);
    if (!runtime || !runtime.SpinePlayer) {
      console.error('Spine runtime missing for ' + code);
      return;
    }

    var token = slot.token;
    var folder = BASE + 'characters/' + code + '/';

    // The player frames the camera on the animation it starts with; without naming one it uses the
    // first (often a tiny face animation) and the character is cropped. 'idle' shows the whole body.
    function create(animation) {
      var config = {
        skelUrl: folder + code + '_00.skel',
        atlasUrl: folder + code + '_00.atlas',
        showControls: false,
        alpha: true,
        backgroundColor: '#00000000',
        // In the modified spine-player.js the camera zoom is a plain field (default 2, which crops the
        // character): zoom = framed height / canvas height fits the whole viewport on the canvas.
        update: function (player) {
          if (!('nrb_zoom' in player) || !player.currentViewport || !player.canvas) return;
          var vp = player.currentViewport;
          var height = vp.height + vp.padTop + vp.padBottom;
          var width = vp.width + vp.padLeft + vp.padRight;
          player.nrb_zoom = Math.max(height / player.canvas.height, width / player.canvas.width) || 1;
        },
        success: function (player) {
          if (token !== slot.token) { try { player.dispose(); } catch (e) { /* ignore */ } return; }
          slot.player = player;
          // the spine-player.js bundled by the Nikke wallpapers is a modified build that zooms x2 by default
          if ('nrb_zoom' in player) { player.anrb_posxa = 0; player.nrb_posy = 0; }
          var names = player.skeleton.data.animations.map(function (a) { return a.name; });
          var reactions = names.filter(function (n) { return /^(action|shy|angry|talk|special)/.test(n); });
          // clicking the character plays a reaction and goes back to idle
          slot.element.onclick = function () {
            if (!reactions.length || !slot.player || !animation) return;
            var reaction = reactions[Math.floor(Math.random() * reactions.length)];
            slot.player.setAnimation(reaction, false);
            slot.player.addAnimation(animation, true, 0);
          };
        },
        error: function (player, message) {
          if (animation && token === slot.token) {
            console.error('Cannot load ' + code + ' with ' + animation + ': ' + message + ' (retrying)');
            destroyPlayer(slot);
            slot.token = token + 1;
            token = slot.token;
            create(null);
          } else {
            console.error('Cannot load ' + code + ': ' + message);
          }
        }
      };
      if (animation) config.animation = animation;
      new runtime.SpinePlayer(slot.element, config);
    }

    create('idle');
  }

  var bounce = 0;     // how much the characters pulse with the music (0..1)
  var level = 0;      // smoothed audio level (0..1)

  function applyTransform(slot) {
    var pulse = 1 + bounce * level;
    slot.element.style.transformOrigin = '50% 100%';
    slot.element.style.transform = 'scaleX(' + (slot.flip ? -1 : 1) + ') scale(' + pulse + ')';
  }

  function layout(slot, props) {
    var i = slot.index + 1;
    var scale = Number(prop(props, 'scale' + i, 90)) / 100;
    var x = Number(prop(props, 'x' + i, 50));
    var height = window.innerHeight * scale;
    var width = height * 0.75;
    slot.element.style.height = height + 'px';
    slot.element.style.width = width + 'px';
    slot.element.style.left = (window.innerWidth * x / 100 - width / 2) + 'px';
    // vertical offset as a percentage of the screen height (positive moves the character up)
    slot.element.style.bottom = (window.innerHeight * Number(prop(props, 'y' + i, 0)) / 100) + 'px';
    slot.flip = prop(props, 'flip' + i, false) === true || prop(props, 'flip' + i, false) === 'true';
    slot.element.style.display = slot.code && slot.code !== 'none' ? 'block' : 'none';
    applyTransform(slot);
  }

  function apply(props) {
    latest = props;
    bounce = Number(prop(props, 'bounce', 0)) / 100;
    var color = cssColor(prop(props, 'bgcolor', null));
    if (color) document.body.style.background = color;
    slots.forEach(function (slot) {
      var wanted = prop(props, 'char' + (slot.index + 1), 'none');
      // size the container first: the player measures it when it starts
      slot.code = wanted;
      layout(slot, props);
      if (wanted !== slot.loaded) loadCharacter(slot, wanted);
    });
  }

  function showHint() {
    var hasCharacters = Object.keys(manifest.characters || {}).length > 0;
    if (hasCharacters) return;
    var hint = document.createElement('div');
    hint.style.cssText = 'position:absolute;inset:0;display:flex;align-items:center;justify-content:center;'
      + 'color:#9fb3c8;font:20px sans-serif;text-align:center;padding:40px';
    hint.textContent = 'Nikke Stage: no hay personajes instalados. Ejecuta scripts/nikke-stage.py add c010 (por ejemplo).';
    document.body.appendChild(hint);
  }

  function start() {
    showHint();
    for (var i = 0; i < SLOT_COUNT; i++) slots.push(createSlot(i));
    window.addEventListener('resize', function () {
      slots.forEach(function (slot) { layout(slot, latest); });
    });
    window.wallpaperPropertyListener = { applyUserProperties: apply };
    // the characters pulse to the music: low bands drive a smoothed level used by applyTransform
    if (window.wallpaperRegisterAudioListener) {
      window.wallpaperRegisterAudioListener(function (data) {
        var sum = 0;
        for (var i = 0; i < 12; i++) sum += data[i] || 0;
        var target = Math.min(1, sum / 12);
        level += (target - level) * 0.35;
        if (bounce > 0) slots.forEach(applyTransform);
      });
    }
    // without the engine (or before it delivers the properties) show the first slot's default
    setTimeout(function () { if (!latest) apply({}); }, 3000);
  }

  fetch(BASE + 'characters.json')
    .then(function (response) { return response.json(); })
    .then(function (data) { manifest = data; })
    .catch(function (e) { console.error('characters.json: ' + e); })
    .then(start);
})();
