// Nikke Stage: up to four Nikke characters on screen at once, with an in-wallpaper settings panel.
// Own code. It uses the Spine web runtimes bundled by the installer (spine = 4.0, spine41 = 4.1).
// Characters come from two places: packs installed on disk (scripts/nikke-stage.py or the app window,
// listed in __user/stage/characters.json) and packs downloaded from this panel, which are kept in the
// browser's own IndexedDB (the engine keeps a profile for this wallpaper). Settings live in localStorage.
(function () {
  'use strict';

  var SLOT_COUNT = 4;
  var BASE = '__user/stage/';
  var RELEASE_URL = 'https://github.com/I6RaVeN9I/nikke-wallpaper-packs/releases/download/v1.0/';
  var INDEX_URL = 'https://raw.githubusercontent.com/Nikke-db/Nikke-db.github.io/main/js/json/l2d.json';
  var THUMB_URL = 'https://raw.githubusercontent.com/Nikke-db/Nikke-db.github.io/main/images/sprite/';
  var CODE_RE = /^c\d{3,4}(_\d{2})?$/;
  var ALLOWED_EXT = /\.(atlas|png|skel|json)$/i;
  var MAX_UNPACKED = 120 * 1024 * 1024;
  var STORE_KEY = 'nikkeStage.v1';
  var CATALOG_KEY = 'nikkeStage.catalog.v1';
  var SWATCHES = ['#0c1016', '#1b1f3b', '#2b1b3d', '#3d1b2b', '#12352f', '#3a2f12', '#f2f2f2', '#000000'];

  // ------------------------------------------------------------------ state
  var diskChars = {};        // code -> { name, version }   (installed on disk)
  var dbChars = {};          // code -> { name, version }   (downloaded in the panel, kept in IndexedDB)
  var packs = null;          // codes with a free pack in the repository (null = unknown)
  var catalog = [];          // [{ id, name }] from Nikke-db
  var packs = null;          // codes with a free pack in the release (null = unknown)
  var props = {};            // defaults delivered by the engine (Personalizar)
  var saved = null;          // { values, base } from localStorage
  var values = {};           // effective settings
  var slots = [];
  var level = 0;             // smoothed audio level
  var reactTimer = null;
  var saveTimer = null;
  var awakeTimer = null;
  var backgroundFile = null;  // image copied by the installer (the system wallpaper by default)
  var blobUrls = {};         // code -> { rawDataURIs }

  function $(id) { return document.getElementById(id); }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      if (key === 'class') node.className = attrs[key];
      else if (key === 'text') node.textContent = attrs[key];
      else if (key.slice(0, 2) === 'on') node.addEventListener(key.slice(2), attrs[key]);
      else node.setAttribute(key, attrs[key]);
    });
    (children || []).forEach(function (child) { if (child) node.appendChild(child); });
    return node;
  }

  // ------------------------------------------------------------------ defaults and settings
  function defaultValues() {
    var defaults = { bgimage: true, autospread: true, speed: 100, reactevery: 0, bounce: 0, labels: false, bgcolor: '#0c1016' };
    var xs = { 1: 50, 2: 25, 3: 75, 4: 10 };
    for (var i = 1; i <= SLOT_COUNT; i++) {
      defaults['char' + i] = 'none';
      defaults['x' + i] = xs[i];
      defaults['scale' + i] = 90;
      defaults['y' + i] = 0;
      defaults['flip' + i] = false;
      defaults['mode' + i] = 'main';
      defaults['anim' + i] = '';
      defaults['z' + i] = i;
    }
    return defaults;
  }

  function toHex(value) {
    // Wallpaper Engine colours are "r g b" in the 0..1 range; the panel uses #rrggbb
    if (typeof value === 'string' && value.charAt(0) === '#') return value;
    var parts = String(value || '').split(' ').map(Number);
    if (parts.length < 3 || parts.some(isNaN)) return null;
    return '#' + parts.slice(0, 3).map(function (c) {
      var hex = Math.max(0, Math.min(255, Math.round(c * 255))).toString(16);
      return hex.length < 2 ? '0' + hex : hex;
    }).join('');
  }

  function flatProps(raw) {
    var flat = {};
    Object.keys(raw || {}).forEach(function (key) {
      var value = raw[key] && raw[key].value;
      if (value === undefined) return;
      if (key === 'bgcolor') value = toHex(value);
      else if (typeof value === 'string' && value === 'true') value = true;
      else if (typeof value === 'string' && value === 'false') value = false;
      else if (/^(x|scale|y|z)\d$|^(speed|reactevery|bounce)$/.test(key)) value = Number(value);
      if (value !== null) flat[key] = value;
    });
    return flat;
  }

  function computeValues() {
    var flat = flatProps(props);
    var result = defaultValues();
    Object.keys(flat).forEach(function (key) { result[key] = flat[key]; });
    // saved panel settings win unless the same property was changed afterwards in Personalizar
    if (saved && saved.values) {
      Object.keys(saved.values).forEach(function (key) {
        var untouched = !saved.base || JSON.stringify(saved.base[key]) === JSON.stringify(flat[key]);
        if (untouched) result[key] = saved.values[key];
      });
    }
    return result;
  }

  function loadSaved() {
    try { saved = JSON.parse(localStorage.getItem(STORE_KEY) || 'null'); } catch (e) { saved = null; }
  }

  function scheduleSave() {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      try {
        localStorage.setItem(STORE_KEY, JSON.stringify({ values: values, base: flatProps(props) }));
        saved = { values: JSON.parse(JSON.stringify(values)), base: flatProps(props) };
      } catch (e) { console.error('cannot save settings: ' + e); }
    }, 400);
  }

  function setValue(key, value) {
    values[key] = value;
    scheduleSave();
    applyAll();
  }

  // ------------------------------------------------------------------ IndexedDB (downloaded packs)
  var dbPromise = null;
  function db() {
    if (!dbPromise) {
      dbPromise = new Promise(function (resolve, reject) {
        var request = indexedDB.open('nikke-stage', 1);
        request.onupgradeneeded = function () {
          request.result.createObjectStore('files');
          request.result.createObjectStore('meta');
        };
        request.onsuccess = function () { resolve(request.result); };
        request.onerror = function () { reject(request.error); };
      });
    }
    return dbPromise;
  }

  function idb(storeName, mode, action) {
    return db().then(function (database) {
      return new Promise(function (resolve, reject) {
        var tx = database.transaction(storeName, mode);
        var request = action(tx.objectStore(storeName));
        tx.oncomplete = function () { resolve(request && request.result); };
        tx.onerror = function () { reject(tx.error); };
      });
    });
  }

  function saveDbMeta() { return idb('meta', 'readwrite', function (s) { return s.put(dbChars, 'chars'); }); }

  // ------------------------------------------------------------------ zip reading (Windows zips, deflate)
  function inflateRaw(bytes) {
    var stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    return new Response(stream).arrayBuffer().then(function (buffer) { return new Uint8Array(buffer); });
  }

  function readZip(buffer) {
    var view = new DataView(buffer);
    var eocd = -1;
    for (var i = buffer.byteLength - 22; i >= Math.max(0, buffer.byteLength - 66000); i--) {
      if (view.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
    }
    if (eocd < 0) throw new Error('no es un zip valido');
    var count = view.getUint16(eocd + 10, true);
    var pos = view.getUint32(eocd + 16, true);
    var decoder = new TextDecoder();
    var entries = [];
    for (var n = 0; n < count; n++) {
      if (view.getUint32(pos, true) !== 0x02014b50) throw new Error('zip danado');
      var method = view.getUint16(pos + 10, true);
      var compressed = view.getUint32(pos + 20, true);
      var size = view.getUint32(pos + 24, true);
      var nameLen = view.getUint16(pos + 28, true);
      var extraLen = view.getUint16(pos + 30, true);
      var commentLen = view.getUint16(pos + 32, true);
      var local = view.getUint32(pos + 42, true);
      var name = decoder.decode(new Uint8Array(buffer, pos + 46, nameLen)).replace(/\\/g, '/');
      entries.push({ name: name, method: method, compressed: compressed, size: size, local: local });
      pos += 46 + nameLen + extraLen + commentLen;
    }
    return entries.filter(function (e) { return e.name.slice(-1) !== '/'; }).map(function (e) {
      var nameLen = view.getUint16(e.local + 26, true);
      var extraLen = view.getUint16(e.local + 28, true);
      var start = e.local + 30 + nameLen + extraLen;
      return { name: e.name, method: e.method, size: e.size, data: new Uint8Array(buffer, start, e.compressed) };
    });
  }

  // Packs that are not on disk are served from memory through a custom Spine Downloader: the skeleton and atlas bytes
  // are handed over directly (the stock rawDataURIs route decodes them with atob(), which garbles non-ASCII region
  // names such as the Korean ones in some packs), and only the PNG pages use blob: URLs.
  function memoryAssets() { return { bytes: {}, urls: {} }; }

  function addAsset(assets, path, bytes) {
    if (/\.png$/i.test(path)) assets.urls[path] = URL.createObjectURL(new Blob([bytes], { type: 'image/png' }));
    else assets.bytes[path] = bytes;
  }

  function makeDownloader(runtime, assets) {
    var downloader = new runtime.Downloader();
    Object.keys(assets.urls).forEach(function (path) { downloader.rawDataUris[path] = assets.urls[path]; });
    var decode = function (bytes) { return new TextDecoder().decode(bytes); };
    var plainText = downloader.downloadText.bind(downloader);
    var plainBinary = downloader.downloadBinary.bind(downloader);
    var plainJson = downloader.downloadJson.bind(downloader);
    downloader.downloadText = function (url, success, error) {
      if (assets.bytes[url]) success(decode(assets.bytes[url])); else plainText(url, success, error);
    };
    downloader.downloadBinary = function (url, success, error) {
      if (assets.bytes[url]) success(assets.bytes[url]); else plainBinary(url, success, error);
    };
    downloader.downloadJson = function (url, success, error) {
      if (assets.bytes[url]) { try { success(JSON.parse(decode(assets.bytes[url]))); } catch (e) { error(0, String(e)); } }
      else plainJson(url, success, error);
    };
    return downloader;
  }

  function skeletonVersion(bytes) {
    var head = '';
    for (var i = 0; i < Math.min(bytes.length, 96); i++) head += String.fromCharCode(bytes[i]);
    var match = head.match(/(\d)\.(\d)\.\d+/);
    return match && match[1] === '4' && match[2] === '1' ? '4.1' : '4.0';
  }

  function installPack(code, name, buffer) {
    var entries = readZip(buffer);
    var total = 0;
    var jobs = [];
    entries.forEach(function (entry) {
      var parts = entry.name.split('/');
      if (parts[0] !== code || parts.indexOf('..') !== -1 || !ALLOWED_EXT.test(entry.name)) {
        throw new Error('el pack contiene un archivo inesperado: ' + entry.name);
      }
      total += entry.size;
      if (total > MAX_UNPACKED) throw new Error('el pack es demasiado grande');
      // the main model plus the aim/ and cover/ poses
      var load = entry.method === 0 ? Promise.resolve(new Uint8Array(entry.data)) : inflateRaw(entry.data);
      jobs.push(load.then(function (bytes) { return { rel: parts.slice(1).join('/'), bytes: bytes }; }));
    });
    return Promise.all(jobs).then(function (files) {
      var skel = files.filter(function (f) { return f.rel === code + '_00.skel'; })[0];
      if (!skel) throw new Error('el pack no trae ' + code + '_00.skel');
      return Promise.all(files.map(function (f) {
        return idb('files', 'readwrite', function (s) { return s.put(new Blob([f.bytes]), code + '/' + f.rel); });
      })).then(function () {
        dbChars[code] = { name: name || code, version: skeletonVersion(skel.bytes) };
        delete blobUrls[code];
        return saveDbMeta();
      });
    });
  }

  function downloadPack(code, onProgress) {
    return fetch(RELEASE_URL + code + '.zip').then(function (response) {
      if (!response.ok) throw new Error('no existe el pack ' + code + ' (' + response.status + ')');
      var total = Number(response.headers.get('content-length')) || 0;
      var reader = response.body.getReader();
      var chunks = [];
      var received = 0;
      function pump() {
        return reader.read().then(function (result) {
          if (result.done) return;
          chunks.push(result.value);
          received += result.value.length;
          if (received > 60 * 1024 * 1024) throw new Error('el pack es demasiado grande');
          if (onProgress && total) onProgress(received / total);
          return pump();
        });
      }
      return pump().then(function () { return new Blob(chunks).arrayBuffer(); });
    });
  }

  function removePack(code) {
    return idb('files', 'readwrite', function (s) {
      return s.delete(IDBKeyRange.bound(code + '/', code + '/￿'));
    }).then(function () {
      delete dbChars[code];
      delete blobUrls[code];
      return saveDbMeta();
    });
  }

  function rawUrlsFor(code) {
    if (blobUrls[code]) return Promise.resolve(blobUrls[code]);
    var range = IDBKeyRange.bound(code + '/', code + '/\uffff');
    return Promise.all([idb('files', 'readonly', function (st) { return st.getAllKeys(range); }),
                        idb('files', 'readonly', function (st) { return st.getAll(range); })])
      .then(function (result) {
        var keys = result[0], blobs = result[1];
        return Promise.all(blobs.map(function (blob) { return blob.arrayBuffer(); })).then(function (buffers) {
          var assets = memoryAssets();
          keys.forEach(function (key, index) { addAsset(assets, 'db/' + key, new Uint8Array(buffers[index])); });
          blobUrls[code] = assets;
          return assets;
        });
      });
  }

  // ------------------------------------------------------------------ characters
  function allChars() {
    var merged = {};
    Object.keys(dbChars).forEach(function (code) { merged[code] = dbChars[code]; });
    Object.keys(diskChars).forEach(function (code) { merged[code] = diskChars[code]; });
    return merged;
  }

  function installedCodes() {
    return Object.keys(allChars()).sort();
  }

  function charName(code) {
    var entry = allChars()[code];
    if (entry && entry.name && entry.name !== code) return entry.name;
    var item = catalog.filter(function (c) { return c.id === code; })[0];
    return item ? item.name : code;
  }

  function thumbUrl(code) {
    var match = code.match(/^(c\d+)(?:_(\d\d))?$/);
    return match ? THUMB_URL + 'si_' + match[1] + (match[2] ? '_' + match[2] : '') + '_00_s.png' : '';
  }

  var MODES = [['main', 'Normal'], ['aim', 'Apuntando'], ['cover', 'Cobertura']];
  var MODE_DEFAULT_ANIM = { main: 'idle', aim: 'aim', cover: 'cover_idle' };
  var REACTION_RE = /(action|shy|angry|talk|special|hit|reload|stun|fire)/i;

  function modeFile(code, mode) {
    if (mode === 'aim') return 'aim/' + code + '_aim_00';
    if (mode === 'cover') return 'cover/' + code + '_cover_00';
    return code + '_00';
  }

  function runtimeFor(code) {
    var entry = allChars()[code];
    return entry && entry.version === '4.1' ? window.spine41 : window.spine;
  }

  // ------------------------------------------------------------------ stage (spine players)
  function createSlot(index) {
    var element = el('div', { class: 'slot', id: 'slot' + (index + 1) });
    element.style.transition = 'opacity 0.6s ease';
    element.style.opacity = '0';
    $('stage').appendChild(element);
    var slot = { index: index, element: element, code: null, loaded: null, player: null, token: 0, flip: false,
                 reactions: null, baseAnim: null, animations: [], loadedMode: 'main' };
    element.addEventListener('click', function () { if (!document.body.classList.contains('editing')) playReaction(slot); });
    element.addEventListener('mousedown', function (event) { startDrag(slot, event); });
    element.addEventListener('wheel', function (event) { wheelScale(slot, event); });
    return slot;
  }

  function destroyPlayer(slot) {
    slot.token++;
    if (slot.player) { try { slot.player.dispose(); } catch (e) { /* ignore */ } slot.player = null; }
    slot.element.innerHTML = '';
    slot.element.style.opacity = '0';
    slot.reactions = null;
  }

  function playReaction(slot) {
    if (!slot.player || !slot.reactions || !slot.reactions.length) return;
    playAnimation(slot, slot.reactions[Math.floor(Math.random() * slot.reactions.length)], false);
  }

  function scheduleReactions(seconds) {
    if (reactTimer) { clearInterval(reactTimer); reactTimer = null; }
    if (seconds > 0) {
      reactTimer = setInterval(function () {
        var ready = slots.filter(function (s) { return s.player && s.reactions && s.reactions.length; });
        if (ready.length) playReaction(ready[Math.floor(Math.random() * ready.length)]);
      }, seconds * 1000);
    }
  }

  // Creates a SpinePlayer in `container` for one character and calls onReady(player, idleName).
  // `raw` maps urls to in-memory blobs for packs that are not on disk.
  function spawnPlayer(container, code, mode, wantedAnimation, version, folder, raw, isCurrent, onReady, onFail) {
    var runtime = version === '4.1' ? window.spine41 : window.spine;
    if (!runtime || !runtime.SpinePlayer) { console.error('Spine runtime missing for ' + code); return; }
    function create(animation) {
      var config = {
        skelUrl: folder + modeFile(code, mode) + '.skel',
        atlasUrl: folder + modeFile(code, mode) + '.atlas',
        showControls: false,
        alpha: true,
        backgroundColor: '#00000000',
        // the modified spine-player.js bundled by the Nikke wallpapers has a plain zoom field (default 2, which
        // crops the character): framed height / canvas height fits the whole viewport on the canvas
        update: function (player) {
          if (!('nrb_zoom' in player) || !player.currentViewport || !player.canvas) return;
          var vp = player.currentViewport;
          var height = vp.height + vp.padTop + vp.padBottom;
          var width = vp.width + vp.padLeft + vp.padRight;
          player.nrb_zoom = Math.max(height / player.canvas.height, width / player.canvas.width) || 1;
        },
        success: function (player) {
          if (!isCurrent()) { try { player.dispose(); } catch (e) { /* ignore */ } return; }
          if ('nrb_zoom' in player) { player.anrb_posxa = 0; player.nrb_posy = 0; }
          onReady(player, animation);
        },
        error: function (player, message) {
          // the failed player keeps its render loop alive (and throwing) unless it is disposed
          try { if (player) player.dispose(); } catch (e) { /* ignore */ }
          if (animation && isCurrent()) {
            console.error('Cannot load ' + code + ' with ' + animation + ': ' + message + ' (retrying)');
            container.innerHTML = '';
            create(null);
          } else {
            console.error('Cannot load ' + code + ': ' + message);
            if (onFail && isCurrent()) onFail(message);
          }
        }
      };
      if (animation) config.animation = animation;
      if (raw) config.downloader = makeDownloader(runtime, raw);
      new runtime.SpinePlayer(container, config);
    }
    create(wantedAnimation || MODE_DEFAULT_ANIM[mode] || 'idle');
  }

  function loadCharacter(slot, code) {
    var i = slot.index + 1;
    var mode = values['mode' + i] || 'main';
    destroyPlayer(slot);
    slot.loaded = code;
    slot.loadedMode = mode;
    slot.animations = [];
    if (!code || code === 'none' || !allChars()[code]) return;
    var token = slot.token;
    var fromDisk = !!diskChars[code];

    (fromDisk ? Promise.resolve(null) : rawUrlsFor(code)).then(function (raw) {
      if (token !== slot.token) return;
      var folder = fromDisk ? BASE + 'characters/' + code + '/' : 'db/' + code + '/';
      spawnPlayer(slot.element, code, mode, values['anim' + i] || '', allChars()[code].version, folder, raw,
        function () { return token === slot.token; },
        function (player, animation) {
          slot.player = player;
          player.speed = values.speed / 100;
          var names = player.skeleton.data.animations.map(function (a) { return a.name; });
          slot.animations = names;
          slot.baseAnim = animation && names.indexOf(animation) !== -1 ? animation : names[0];
          slot.reactions = names.filter(function (n) { return REACTION_RE.test(n) && n !== slot.baseAnim; });
          slot.element.style.opacity = '1';
          refreshPanel();
        },
        function () {
          // this pack has no such pose: go back to the normal one
          if (mode !== 'main' && token === slot.token) {
            toast(charName(code) + ' no tiene la pose "' + mode + '"');
            values['mode' + i] = 'main';
            scheduleSave();
            slot.loaded = null;
            applyAll();
          }
        });
    }).catch(function (e) { console.error('load ' + code + ': ' + e); });
  }

  function playAnimation(slot, name, loop) {
    if (!slot.player || !slot.animations || slot.animations.indexOf(name) === -1) return false;
    slot.player.setAnimation(name, !!loop);
    if (!loop && slot.baseAnim) slot.player.addAnimation(slot.baseAnim, true, 0);
    return true;
  }

  function applyTransform(slot) {
    var pulse = 1 + (values.bounce / 100) * level;
    slot.element.style.transformOrigin = '50% 100%';
    slot.element.style.transform = 'scaleX(' + (slot.flip ? -1 : 1) + ') scale(' + pulse + ')';
  }

  function layout(slot) {
    var i = slot.index + 1;
    var height = window.innerHeight * values['scale' + i] / 100;
    var width = height * 0.75;
    var x = values['x' + i];
    if (values.autospread) {
      var visible = slots.filter(function (other) { return other.code && other.code !== 'none'; });
      var position = visible.indexOf(slot);
      if (position !== -1) x = (position + 1) * 100 / (visible.length + 1);
    }
    slot.element.style.height = height + 'px';
    slot.element.style.width = width + 'px';
    slot.element.style.left = (window.innerWidth * x / 100 - width / 2) + 'px';
    slot.element.style.bottom = (window.innerHeight * values['y' + i] / 100) + 'px';
    slot.flip = values['flip' + i] === true;
    slot.element.style.zIndex = String(values['z' + i]);
    slot.element.style.display = slot.code && slot.code !== 'none' ? 'block' : 'none';
    var tag = slot.element.querySelector('.name-tag');
    if (values.labels && slot.code && slot.code !== 'none') {
      if (!tag) { tag = el('div', { class: 'name-tag' }); slot.element.appendChild(tag); }
      tag.textContent = charName(slot.code);
    } else if (tag) {
      tag.remove();
    }
    applyTransform(slot);
  }

  function applyAll() {
    document.body.style.backgroundColor = values.bgcolor;
    if (backgroundFile && values.bgimage !== false) {
      document.body.style.backgroundImage = 'url("' + BASE + backgroundFile + '")';
      document.body.style.backgroundSize = 'cover';
      document.body.style.backgroundPosition = 'center';
      document.body.style.backgroundRepeat = 'no-repeat';
    } else {
      document.body.style.backgroundImage = 'none';
    }
    scheduleReactions(Number(values.reactevery));
    slots.forEach(function (slot) { slot.code = values['char' + (slot.index + 1)]; });
    slots.forEach(function (slot) {
      layout(slot);
      if (slot.code !== slot.loaded || (values['mode' + (slot.index + 1)] || 'main') !== slot.loadedMode) loadCharacter(slot, slot.code);
      if (slot.player) slot.player.speed = values.speed / 100;
    });
    refreshPanel();
  }

  // ------------------------------------------------------------------ editing on the stage (drag + wheel)
  var drag = null;
  function startDrag(slot, event) {
    if (!document.body.classList.contains('editing') || event.button > 0) return;
    drag = { slot: slot, startX: event.clientX, startY: event.clientY,
             x: values['x' + (slot.index + 1)], y: values['y' + (slot.index + 1)] };
    slot.element.classList.add('dragging');
    event.preventDefault();
  }
  window.addEventListener('mousemove', function (event) {
    wake();
    if (!drag) return;
    var i = drag.slot.index + 1;
    values.autospread = false;
    values['x' + i] = Math.max(0, Math.min(100, drag.x + (event.clientX - drag.startX) * 100 / window.innerWidth));
    values['y' + i] = Math.max(-30, Math.min(60, drag.y - (event.clientY - drag.startY) * 100 / window.innerHeight));
    layout(drag.slot);
  });
  window.addEventListener('mouseup', function () {
    if (!drag) return;
    drag.slot.element.classList.remove('dragging');
    drag = null;
    scheduleSave();
    refreshPanel();
  });
  function wheelScale(slot, event) {
    if (!document.body.classList.contains('editing')) return;
    var key = 'scale' + (slot.index + 1);
    values[key] = Math.max(20, Math.min(150, values[key] + (event.deltaY < 0 ? 4 : -4)));
    layout(slot);
    scheduleSave();
    refreshPanel();
    event.preventDefault();
  }

  // ------------------------------------------------------------------ panel UI
  var pageNodes = {};
  var slotCards = [];
  var pickerTarget = 0;

  function toast(message, ms) {
    var node = $('toast');
    node.textContent = message;
    node.classList.add('show');
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { node.classList.remove('show'); }, ms || 2600);
  }

  function wake() {
    document.body.classList.add('ui-awake');
    clearTimeout(awakeTimer);
    awakeTimer = setTimeout(function () { document.body.classList.remove('ui-awake'); }, 4000);
  }

  function slider(key, label, min, max, step, suffix) {
    var output = el('output');
    var input = el('input', { type: 'range', min: min, max: max, step: step });
    input.addEventListener('input', function () { setValue(key, Number(input.value)); });
    var row = el('div', { class: 'row' }, [el('label', { text: label }), input, output]);
    row.sync = function () { input.value = values[key]; output.textContent = Math.round(values[key]) + (suffix || ''); };
    return row;
  }

  function toggle(key, label) {
    var input = el('input', { type: 'checkbox' });
    input.addEventListener('change', function () { setValue(key, input.checked); });
    var row = el('div', { class: 'row' }, [el('label', { text: label }),
      el('label', { class: 'switch' }, [input, el('span')])]);
    row.sync = function () { input.checked = values[key] === true; };
    return row;
  }

  function buildSlotCard(index) {
    var i = index + 1;
    var avatar = el('div', { class: 'avatar', title: 'Cambiar personaje',
      onclick: function () { openPicker(index); } });
    var name = el('b');
    var detail = el('small');
    var clear = el('button', { class: 'btn', text: 'Quitar', onclick: function () { setValue('char' + i, 'none'); } });
    var head = el('div', { class: 'slot-head' }, [avatar, el('div', { class: 'slot-title' }, [name, detail]), clear]);
    var modeBar = el('div', { class: 'seg' }, MODES.map(function (m) {
      return el('button', { class: 'seg-btn', 'data-mode': m[0], text: m[1],
        onclick: function () { setValue('mode' + i, m[0]); setValue('anim' + i, ''); } });
    }));
    var animSelect = el('select', { class: 'select' });
    animSelect.addEventListener('change', function () { setValue('anim' + i, animSelect.value); });
    var slotObj = function () { return slots[index]; };
    var actions = el('div', { class: 'actions' }, [
      el('button', { class: 'btn', text: 'Reacción', onclick: function () { playReaction(slotObj()); } }),
      el('button', { class: 'btn', text: 'Recargar', 'data-act': 'reload', onclick: function () {
        var names = slotObj().animations.filter(function (n) { return /reload/i.test(n); });
        if (names.length) playAnimation(slotObj(), names[Math.floor(Math.random() * names.length)], false);
        else toast('Esta pose no tiene animación de recarga'); } }),
      el('button', { class: 'btn', text: 'Disparar', 'data-act': 'fire', onclick: function () {
        var names = slotObj().animations.filter(function (n) { return /fire|shot|attack/i.test(n); });
        if (names.length) playAnimation(slotObj(), names[0], false);
        else toast('Esta pose no tiene animación de disparo'); } }),
      el('button', { class: 'btn', text: '⬆ Delante', title: 'Traer al frente', onclick: function () {
        var top = -1e9; for (var n = 1; n <= SLOT_COUNT; n++) top = Math.max(top, values['z' + n]); setValue('z' + i, top + 1); } }),
      el('button', { class: 'btn', text: '⬇ Detrás', title: 'Enviar al fondo', onclick: function () {
        var low = 1e9; for (var n = 1; n <= SLOT_COUNT; n++) low = Math.min(low, values['z' + n]); setValue('z' + i, low - 1); } })]);
    var rows = [el('div', { class: 'row' }, [el('label', { text: 'Pose' }), modeBar]),
                el('div', { class: 'row' }, [el('label', { text: 'Animación' }), animSelect]),
                actions,
                slider('x' + i, 'Posición', 0, 100, 1, '%'), slider('scale' + i, 'Tamaño', 20, 150, 1, '%'),
                slider('y' + i, 'Altura', -30, 60, 1, '%'), toggle('flip' + i, 'Espejo')];
    rows[0].sync = function () {
      Array.prototype.forEach.call(modeBar.children, function (b) { b.classList.toggle('active', b.getAttribute('data-mode') === (values['mode' + i] || 'main')); });
    };
    rows[1].sync = function () {
      var current = values['anim' + i] || '';
      var names = slotObj() ? slotObj().animations : [];
      animSelect.innerHTML = '';
      animSelect.appendChild(el('option', { value: '', text: '(automática)' }));
      names.forEach(function (n) { animSelect.appendChild(el('option', { value: n, text: n })); });
      animSelect.value = current;
    };
    actions.sync = function () {
      var names = slotObj() ? slotObj().animations : [];
      actions.querySelector('[data-act=reload]').style.opacity = names.some(function (n) { return /reload/i.test(n); }) ? '1' : '0.45';
      actions.querySelector('[data-act=fire]').style.opacity = names.some(function (n) { return /fire|shot|attack/i.test(n); }) ? '1' : '0.45';
    };
    var title = el('h2', { class: 'fold', text: 'Hueco ' + i, onclick: function () { card.classList.toggle('open'); } });
    var card = el('div', { class: 'card slot-card' + (index === 0 ? ' open' : '') }, [title, head].concat(rows));
    card.sync = function () {
      var code = values['char' + i];
      var empty = !code || code === 'none';
      avatar.className = 'avatar' + (empty ? ' empty' : '');
      avatar.style.backgroundImage = empty ? 'none' : 'url("' + thumbUrl(code) + '")';
      avatar.textContent = empty ? '+' : '';
      name.textContent = empty ? 'Vacío' : charName(code);
      detail.textContent = empty ? 'Pulsa para elegir un personaje' : code;
      clear.style.display = empty ? 'none' : '';
      rows.forEach(function (row) { row.sync(); });
    };
    return card;
  }

  function buildScenePage() {
    var color = el('input', { type: 'color' });
    color.addEventListener('input', function () { setValue('bgcolor', color.value); });
    var swatches = el('div', { class: 'swatches' }, SWATCHES.map(function (hex) {
      var swatch = el('div', { class: 'swatch', title: hex, onclick: function () { setValue('bgcolor', hex); } });
      swatch.style.background = hex;
      return swatch;
    }));
    var rows = [toggle('bgimage', 'Imagen de fondo'), toggle('autospread', 'Repartir solos'), toggle('labels', 'Mostrar nombres'),
                slider('speed', 'Velocidad', 25, 300, 5, '%'), slider('reactevery', 'Reacción cada', 0, 120, 5, ' s'),
                slider('bounce', 'Latido (música)', 0, 30, 1, '%')];
    var reset = el('button', { class: 'btn danger', text: 'Restablecer ajustes', onclick: function () {
      var keep = {};
      for (var i = 1; i <= SLOT_COUNT; i++) keep['char' + i] = values['char' + i];
      values = defaultValues();
      Object.keys(keep).forEach(function (key) { values[key] = keep[key]; });
      scheduleSave(); applyAll(); toast('Ajustes restablecidos');
    } });
    var page = el('div', { class: 'page' }, [
      el('div', { class: 'card' }, [el('h2', { text: 'Animación' })].concat(rows)),
      el('div', { class: 'card' }, [el('h2', { text: 'Fondo' }),
        el('div', { class: 'row' }, [el('label', { text: 'Color' }), color]), swatches,
        el('p', { class: 'hint', text: 'La imagen es la del sistema por defecto; se cambia desde Elegir Fondo (Nikke Stage: personajes) o con scripts/nikke-stage.py background.' })]),
      el('div', { class: 'card' }, [el('h2', { text: 'Edición en pantalla' }),
        el('p', { class: 'hint', text: 'Con el panel abierto puedes arrastrar los personajes por la pantalla para moverlos (el tamaño se cambia con el deslizador de cada hueco).' }),
        reset])]);
    page.sync = function () { rows.forEach(function (row) { row.sync(); }); color.value = values.bgcolor; };
    return page;
  }

  function buildCharactersPage() {
    slotCards = [];
    for (var i = 0; i < SLOT_COUNT; i++) slotCards.push(buildSlotCard(i));
    var page = el('div', { class: 'page' }, [el('p', { class: 'hint',
      text: 'Elige hasta cuatro personajes. Pulsa la foto de cada hueco para cambiarlo o ve a "Catálogo" para descargar más.' })]
      .concat(slotCards));
    page.sync = function () { slotCards.forEach(function (card) { card.sync(); }); };
    return page;
  }

  // ---- catalogue
  var catalogGrid = null;
  var catalogSearch = null;
  var catalogCount = null;
  var catalogBusy = {};

  function makeTile(code, name, options) {
    var tile = el('div', { class: 'tile' + (options.selected ? ' selected' : ''), title: name + ' (' + code + ')',
      onclick: options.onclick });
    tile.style.backgroundImage = 'url("' + thumbUrl(code) + '")';
    tile.appendChild(el('div', { class: 'label', text: name }));
    if (options.badge) tile.appendChild(el('div', { class: 'badge' + (options.badgeClass ? ' ' + options.badgeClass : ''), text: options.badge }));
    return tile;
  }

  var CATALOG_PAGE = 20;
  var catalogPage = 0;
  var catalogLetter = '';      // '' = all; '#' = names not starting with a letter
  var catalogFilter = 'all';   // all | saved | missing | favs
  var showVariants = false;    // false: one tile per character, its outfits are reached from the preview
  var catalogNav = null;
  var catalogLetters = null;
  var catalogFilters = null;
  var favourites = {};
  var FAV_KEY = 'nikkeStage.favs.v1';

  try { favourites = JSON.parse(localStorage.getItem(FAV_KEY) || '{}') || {}; } catch (e) { favourites = {}; }
  function toggleFavourite(code) {
    if (favourites[code]) delete favourites[code]; else favourites[code] = 1;
    try { localStorage.setItem(FAV_KEY, JSON.stringify(favourites)); } catch (e) { /* ignore */ }
  }

  function baseOf(code) { return code.replace(/_\d\d$/, ''); }

  function allItems() {
    var base = catalog.length ? catalog : installedCodes().map(function (c) { return { id: c, name: charName(c) }; });
    if (!packs) return base;
    // packs that exist in the repository but have no entry (name) in Nikke-db: shown by code
    var known = {};
    base.forEach(function (item) { known[item.id] = true; });
    return base.concat(Object.keys(packs).filter(function (code) { return !known[code] && CODE_RE.test(code); })
      .map(function (code) { return { id: code, name: code, unnamed: true }; }));
  }

  function hasPack(code) { return !packs || !!packs[code] || !!allChars()[code]; }

  function variantsOf(code) {
    var base = baseOf(code);
    return allItems().filter(function (item) { return baseOf(item.id) === base && (hasPack(item.id) || item.id === code); });
  }

  function firstLetter(name) {
    var letter = String(name || '').trim().charAt(0).toUpperCase();
    return /[A-Z]/.test(letter) ? letter : '#';
  }

  function catalogItems(ignoreLetter) {
    var installed = allChars();
    var query = catalogSearch ? catalogSearch.value.trim().toLowerCase() : '';
    var items = allItems();
    var groups = {};
    items.forEach(function (item) { var base = baseOf(item.id); groups[base] = (groups[base] || 0) + 1; });
    return items.filter(function (item) {
      var isVariant = baseOf(item.id) !== item.id;
      if ((isVariant || item.unnamed) && !showVariants) return false;
      if (!ignoreLetter && catalogLetter && firstLetter(item.name) !== catalogLetter) return false;
      if (catalogFilter === 'saved' && !installed[item.id]) return false;
      if (catalogFilter === 'missing' && (installed[item.id] || !hasPack(item.id))) return false;
      if (catalogFilter === 'favs' && !favourites[item.id]) return false;
      return !query || item.id.toLowerCase().indexOf(query) !== -1 || String(item.name).toLowerCase().indexOf(query) !== -1;
    }).map(function (item) { item.extra = isBaseWithVariants(item, groups); return item; });
  }

  function isBaseWithVariants(item, groups) {
    return baseOf(item.id) === item.id && groups[item.id] > 1 && !showVariants ? groups[item.id] - 1 : 0;
  }

  function refreshCatalog() {
    if (!catalogGrid) return;
    var installed = allChars();
    var items = catalogItems(false);
    var pages = Math.max(1, Math.ceil(items.length / CATALOG_PAGE));
    catalogPage = Math.min(catalogPage, pages - 1);
    catalogGrid.innerHTML = '';
    catalogCount.textContent = items.length + ' personajes' + (catalog.length ? '' : ' (sin conexión)')
      + ' · ' + installedCodes().length + ' guardados';
    items.slice(catalogPage * CATALOG_PAGE, (catalogPage + 1) * CATALOG_PAGE).forEach(function (item) {
      var have = !!installed[item.id];
      var tile = makeTile(item.id, item.name, {
        badge: catalogBusy[item.id] ? Math.round(catalogBusy[item.id] * 100) + '%' : (have ? 'Guardado' : (!hasPack(item.id) ? 'Sin pack' : (favourites[item.id] ? '★' : 'Ver'))),
        badgeClass: have ? '' : (!hasPack(item.id) ? 'none' : 'get'),
        onclick: function () { openPreview(item.id, item.name); }
      });
      if (item.extra) tile.appendChild(el('div', { class: 'variants', text: '+' + item.extra }));
      if (favourites[item.id]) tile.classList.add('fav');
      if (!have && !hasPack(item.id)) tile.classList.add('nopack');
      if (catalogBusy[item.id]) tile.classList.add('busy');
      catalogGrid.appendChild(tile);
    });

    // pager: arrows + numbered pages so any page is one click away
    catalogNav.innerHTML = '';
    catalogNav.appendChild(el('button', { class: 'chip', text: '◀', disabled: catalogPage === 0 ? 'disabled' : null,
      onclick: function () { catalogPage = Math.max(0, catalogPage - 1); refreshCatalog(); } }));
    var first = Math.max(0, Math.min(catalogPage - 3, pages - 8));
    for (var p = first; p < Math.min(pages, first + 8); p++) {
      (function (number) {
        catalogNav.appendChild(el('button', { class: 'chip' + (number === catalogPage ? ' active' : ''), text: String(number + 1),
          onclick: function () { catalogPage = number; refreshCatalog(); } }));
      })(p);
    }
    catalogNav.appendChild(el('button', { class: 'chip', text: '▶', disabled: catalogPage >= pages - 1 ? 'disabled' : null,
      onclick: function () { catalogPage = Math.min(pages - 1, catalogPage + 1); refreshCatalog(); } }));

    // letters that have at least one result (ignoring the letter itself)
    var present = {};
    catalogItems(true).forEach(function (item) { present[firstLetter(item.name)] = true; });
    Array.prototype.forEach.call(catalogLetters.children, function (chip) {
      var letter = chip.getAttribute('data-letter');
      chip.style.display = letter && !present[letter] ? 'none' : '';
      chip.classList.toggle('active', letter === catalogLetter);
    });
    Array.prototype.forEach.call(catalogFilters.children, function (chip) {
      var key = chip.getAttribute('data-filter');
      chip.classList.toggle('active', key === 'variants' ? showVariants : key === catalogFilter);
    });
  }

  function download(code, name) {
    if (catalogBusy[code] !== undefined) return;
    catalogBusy[code] = 0.01;
    refreshCatalog();
    toast('Descargando ' + name + '...');
    downloadPack(code, function (fraction) { catalogBusy[code] = Math.max(0.01, fraction * 0.9); refreshCatalog(); })
      .then(function (buffer) { return installPack(code, name, buffer); })
      .then(function () {
        delete catalogBusy[code];
        toast(name + ' instalado');
        refreshCatalog();
        refreshPanel();
      })
      .catch(function (error) {
        delete catalogBusy[code];
        refreshCatalog();
        toast('No se pudo instalar ' + name + ': ' + (error.message || error), 5000);
      });
  }

  function offerRemove(code) {
    if (diskChars[code]) { toast(charName(code) + ' está instalado en disco (se quita desde la aplicación)'); return; }
    var inUse = slots.some(function (slot) { return slot.code === code; });
    if (inUse) { toast(charName(code) + ' se está usando en un hueco'); return; }
    if (!window.confirm || true) {
      // the page has no native dialogs in a wallpaper: a second click within 3 s confirms
      if (offerRemove.pending === code) {
        offerRemove.pending = null;
        removePack(code).then(function () { toast(charName(code) + ' eliminado'); refreshCatalog(); refreshPanel(); });
      } else {
        offerRemove.pending = code;
        toast('Pulsa otra vez para eliminar a ' + charName(code), 3000);
        setTimeout(function () { if (offerRemove.pending === code) offerRemove.pending = null; }, 3000);
      }
    }
  }

  function loadPacks() {
    var PACKS_KEY = 'nikkeStage.packs.v1';
    function use(names) {
      packs = {};
      names.forEach(function (name) { packs[name] = true; });
      refreshCatalog();
    }
    try {
      var cached = JSON.parse(localStorage.getItem(PACKS_KEY) || 'null');
      if (cached && cached.names) { use(cached.names); if (Date.now() - cached.t < 24 * 3600 * 1000) return; }
    } catch (e) { /* ignore */ }
    fetch('https://api.github.com/repos/I6RaVeN9I/nikke-wallpaper-packs/releases/tags/v1.0')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var names = (data.assets || []).map(function (a) { return a.name; })
          .filter(function (n) { return /\.zip$/.test(n); }).map(function (n) { return n.slice(0, -4); });
        if (!names.length) return;
        try { localStorage.setItem(PACKS_KEY, JSON.stringify({ t: Date.now(), names: names })); } catch (e) { /* ignore */ }
        use(names);
      }).catch(function (e) { console.error('packs: ' + e); });
  }

  function loadCatalog() {
    loadPacks();
    try {
      var cached = JSON.parse(localStorage.getItem(CATALOG_KEY) || 'null');
      if (cached && cached.items) { catalog = cached.items; refreshCatalog(); }
      if (cached && Date.now() - cached.t < 7 * 24 * 3600 * 1000) return;
    } catch (e) { /* ignore */ }
    fetch(INDEX_URL).then(function (r) { return r.json(); }).then(function (data) {
      catalog = data.filter(function (item) { return CODE_RE.test(item.id); })
        .map(function (item) { return { id: item.id, name: item.name }; });
      try { localStorage.setItem(CATALOG_KEY, JSON.stringify({ t: Date.now(), items: catalog })); } catch (e) { /* ignore */ }
      refreshCatalog();
    }).catch(function (e) { console.error('catalog: ' + e); });
  }

  function buildCatalogPage() {
    catalogSearch = el('input', { type: 'search', placeholder: 'Buscar (solo si llega el teclado)' });
    catalogSearch.addEventListener('input', function () { catalogPage = 0; refreshCatalog(); });
    catalogCount = el('div', { class: 'count' });
    catalogGrid = el('div', { class: 'grid compact' });
    catalogNav = el('div', { class: 'pager' });
    // the engine forwards the mouse but not the keyboard, so filtering and paging are done with buttons
    catalogLetters = el('div', { class: 'chips' }, [''].concat('ABCDEFGHIJKLMNOPQRSTUVWXYZ#'.split('')).map(function (letter) {
      return el('button', { class: 'chip', 'data-letter': letter, text: letter || 'A-Z',
        onclick: function () { catalogLetter = letter; catalogPage = 0; refreshCatalog(); } });
    }));
    catalogFilters = el('div', { class: 'chips' }, [['all', 'Todos'], ['favs', '★ Favoritos'], ['saved', 'Guardados'], ['missing', 'Sin descargar']]
      .map(function (f) {
        return el('button', { class: 'chip', 'data-filter': f[0], text: f[1],
          onclick: function () { catalogFilter = f[0]; catalogPage = 0; refreshCatalog(); } });
      }).concat([el('button', { class: 'chip', 'data-filter': 'variants', text: 'Con trajes',
        title: 'Mostrar también las variantes de cada personaje',
        onclick: function () { showVariants = !showVariants; catalogPage = 0; refreshCatalog(); } })]));
    var head = el('div', { class: 'sticky-head' }, [catalogNav, catalogCount]);
    var page = el('div', { class: 'page' }, [head, catalogFilters, catalogLetters, catalogSearch, catalogGrid]);
    page.sync = refreshCatalog;
    return page;
  }

  // ---- preview: see ANY character from the catalogue without installing it
  var preview = { code: null, name: '', player: null, token: 0, buffer: null, urls: [], info: null, mode: 'main' };

  function closePreview() {
    preview.token++;
    if (preview.player) { try { preview.player.dispose(); } catch (e) { /* ignore */ } preview.player = null; }
    preview.urls.forEach(function (url) { URL.revokeObjectURL(url); });
    preview.urls = [];
    preview.buffer = null;
    preview.code = null;
    $('preview-stage').innerHTML = '';
    document.body.classList.remove('previewing');
  }

  function previewActions() {
    var bar = $('preview-actions');
    bar.innerHTML = '';
    var code = preview.code;
    var installed = !!allChars()[code];
    var modes = el('div', { class: 'seg' }, MODES.map(function (m) {
      return el('button', { class: 'seg-btn' + (preview.mode === m[0] ? ' active' : ''), text: m[1],
        onclick: function () { preview.mode = m[0]; previewActions(); respawnPreview(); } });
    }));
    bar.appendChild(modes);
    var variants = variantsOf(code);
    if (variants.length > 1) {
      bar.appendChild(el('div', { class: 'chips' }, variants.map(function (variant) {
        return el('button', { class: 'chip' + (variant.id === code ? ' active' : ''), title: variant.name,
          text: variant.id === baseOf(variant.id) ? 'Base' : variant.id.slice(-2),
          onclick: function () { openPreview(variant.id, variant.name); } });
      })));
    }
    bar.appendChild(el('button', { class: 'btn', text: favourites[code] ? '★ Favorito' : '☆ Favorito', onclick: function () {
      toggleFavourite(code); previewActions(); refreshCatalog(); } }));
    if (!installed) {
      bar.appendChild(el('button', { class: 'btn primary', text: 'Guardar en mi colección', onclick: function () {
        if (!preview.buffer) return;
        installPack(code, preview.name, preview.buffer.slice(0)).then(function () {
          toast(preview.name + ' guardado'); refreshCatalog(); refreshPanel(); previewActions();
        }).catch(function (e) { toast('No se pudo guardar: ' + (e.message || e), 5000); });
      } }));
    }
    for (var i = 1; i <= SLOT_COUNT; i++) {
      (function (slotNumber) {
        bar.appendChild(el('button', { class: 'btn', text: 'Hueco ' + slotNumber, title: 'Ponerlo en el hueco ' + slotNumber,
          onclick: function () {
            var go = function () { setValue('char' + slotNumber, code); toast(preview.name + ' en el hueco ' + slotNumber); };
            if (allChars()[code]) { go(); return; }
            installPack(code, preview.name, preview.buffer.slice(0)).then(function () { refreshCatalog(); go(); previewActions(); })
              .catch(function (e) { toast('No se pudo guardar: ' + (e.message || e), 5000); });
          } }));
      })(i);
    }
    if (installed && dbChars[code] && !diskChars[code]) {
      bar.appendChild(el('button', { class: 'btn danger', text: 'Eliminar', onclick: function () {
        if (slots.some(function (slot) { return slot.code === code; })) { toast('Se está usando en un hueco'); return; }
        removePack(code).then(function () { toast(preview.name + ' eliminado'); refreshCatalog(); previewActions(); });
      } }));
    }
    bar.appendChild(el('button', { class: 'btn', text: 'Cerrar', onclick: closePreview }));
  }

  function openPreview(code, name) {
    if (!hasPack(code)) { toast((name || code) + ' no tiene pack gratuito en nikke-wallpaper-packs', 4000); return; }
    closePreview();
    preview.mode = 'main';
    preview.code = code;
    preview.name = name || charName(code);
    var token = ++preview.token;
    document.body.classList.add('previewing');
    $('preview-name').textContent = preview.name + '  ·  ' + code;
    $('preview-status').textContent = 'Cargando...';
    previewActions();
    var container = $('preview-stage');

    var source;
    if (diskChars[code]) {
      source = Promise.resolve({ version: diskChars[code].version, folder: BASE + 'characters/' + code + '/', raw: null });
    } else if (dbChars[code]) {
      source = rawUrlsFor(code).then(function (raw) { return { version: dbChars[code].version, folder: 'db/' + code + '/', raw: raw }; });
    } else {
      source = downloadPack(code, function (fraction) {
        if (token === preview.token) $('preview-status').textContent = 'Descargando ' + Math.round(fraction * 100) + '%';
      }).then(function (buffer) {
        preview.buffer = buffer;
        var raw = memoryAssets();
        var skelBytes = null;
        return Promise.all(readZip(buffer).map(function (entry) {
          var parts = entry.name.split('/');
          if (parts[0] !== code || parts.length < 2 || !ALLOWED_EXT.test(entry.name)) return null;
          var load = entry.method === 0 ? Promise.resolve(new Uint8Array(entry.data)) : inflateRaw(entry.data);
          return load.then(function (bytes) {
            var rel = parts.slice(1).join('/');
            if (rel === code + '_00.skel') skelBytes = bytes;
            addAsset(raw, 'pv/' + code + '/' + rel, bytes);
          });
        })).then(function () {
          if (!skelBytes) throw new Error('el pack no trae ' + code + '_00.skel');
          preview.urls = Object.keys(raw.urls).map(function (key) { return raw.urls[key]; });
          return { version: skeletonVersion(skelBytes), folder: 'pv/' + code + '/', raw: raw };
        });
      });
    }

    source.then(function (info) {
      if (token !== preview.token) return;
      preview.info = info;
      $('preview-status').textContent = '';
      previewActions();
      respawnPreview();
    }).catch(function (error) {
      if (token === preview.token) $('preview-status').textContent = 'No se pudo cargar: ' + (error.message || error);
    });
  }

  function respawnPreview() {
    if (!preview.info || !preview.code) return;
    var token = ++preview.token;
    var container = $('preview-stage');
    if (preview.player) { try { preview.player.dispose(); } catch (e) { /* ignore */ } preview.player = null; }
    container.innerHTML = '';
    var code = preview.code;
    spawnPlayer(container, code, preview.mode, '', preview.info.version, preview.info.folder, preview.info.raw,
      function () { return token === preview.token; },
      function (player, animation) {
        preview.player = player;
        var names = player.skeleton.data.animations.map(function (a) { return a.name; });
        var reactions = names.filter(function (n) { return REACTION_RE.test(n) && n !== animation; });
        container.onclick = function () {
          if (!reactions.length) return;
          player.setAnimation(reactions[Math.floor(Math.random() * reactions.length)], false);
          player.addAnimation(animation, true, 0);
        };
      },
      function () {
        if (preview.mode !== 'main' && token === preview.token) {
          toast('Este personaje no tiene esa pose');
          preview.mode = 'main';
          previewActions();
          respawnPreview();
        }
      });
  }

  // ---- picker (choose the character of a slot)
  function openPicker(index) {
    pickerTarget = index;
    pickerPage = 0;
    document.body.classList.add('picker-open');
    renderPicker();
  }

  var pickerPage = 0;
  var PICKER_PAGE = 14;

  function renderPicker() {
    var grid = $('picker-grid');
    grid.innerHTML = '';
    var current = values['char' + (pickerTarget + 1)];
    var codes = installedCodes();
    var pages = Math.max(1, Math.ceil(codes.length / PICKER_PAGE));
    pickerPage = Math.min(pickerPage, pages - 1);
    if (pickerPage === 0) {
      grid.appendChild(makeTile('c000', 'Vacío', { onclick: function () { choose('none'); } }));
      grid.lastChild.style.backgroundImage = 'none';
    }
    codes.slice(pickerPage * PICKER_PAGE, (pickerPage + 1) * PICKER_PAGE).forEach(function (code) {
      grid.appendChild(makeTile(code, charName(code), { selected: code === current, onclick: function () { choose(code); } }));
    });
    var nav = $('picker-nav');
    nav.innerHTML = '';
    nav.appendChild(el('button', { class: 'btn', text: '◀', disabled: pickerPage === 0 ? 'disabled' : null, onclick: function () { pickerPage--; renderPicker(); } }));
    nav.appendChild(el('span', { class: 'page-info', text: 'Página ' + (pickerPage + 1) + ' de ' + pages }));
    nav.appendChild(el('button', { class: 'btn', text: '▶', disabled: pickerPage >= pages - 1 ? 'disabled' : null, onclick: function () { pickerPage++; renderPicker(); } }));
    $('picker-title').textContent = 'Personaje del hueco ' + (pickerTarget + 1);
  }

  function choose(code) {
    document.body.classList.remove('picker-open');
    setValue('char' + (pickerTarget + 1), code);
  }

  // ---- panel shell
  function refreshPanel() {
    Object.keys(pageNodes).forEach(function (name) { if (pageNodes[name].sync) pageNodes[name].sync(); });
    if (document.body.classList.contains('picker-open')) renderPicker();
  }

  function showTab(name) {
    Object.keys(pageNodes).forEach(function (key) {
      pageNodes[key].classList.toggle('active', key === name);
      $('tab-' + key).classList.toggle('active', key === name);
    });
  }

  function setPanel(open) {
    document.body.classList.toggle('panel-open', open);
    document.body.classList.toggle('editing', open);
    if (!open) { document.body.classList.remove('picker-open'); closePreview(); }
    if (open) refreshPanel();
  }

  // the engine does not forward the mouse wheel: dragging an empty area of the panel scrolls it instead
  function makeDragScroll(box) {
    var state = null;
    box.addEventListener('mousedown', function (event) {
      if (event.target.closest('button, input, select, .tile, .swatch, .avatar, .fold, .chip')) return;
      state = { y: event.clientY, top: box.scrollTop };
    });
    window.addEventListener('mousemove', function (event) { if (state) box.scrollTop = state.top - (event.clientY - state.y); });
    window.addEventListener('mouseup', function () { state = null; });
  }

  function buildUI() {
    var tabs = [['chars', 'Personajes'], ['catalog', 'Catálogo'], ['scene', 'Escena']];
    pageNodes.chars = buildCharactersPage();
    pageNodes.catalog = buildCatalogPage();
    pageNodes.scene = buildScenePage();
    var tabBar = el('div', { class: 'tabs' }, tabs.map(function (t) {
      return el('button', { class: 'tab', id: 'tab-' + t[0], text: t[1], onclick: function () { showTab(t[0]); } });
    }));
    var pagesBox = el('div', { class: 'pages' }, [pageNodes.chars, pageNodes.catalog, pageNodes.scene]);
    makeDragScroll(pagesBox);
    var panel = el('div', { id: 'panel' }, [
      el('header', {}, [el('h1', {}, [document.createTextNode('Nikke '), el('span', { text: 'Stage' })]),
        el('button', { class: 'icon-btn', id: 'close', title: 'Cerrar', text: '✕', onclick: function () { setPanel(false); } })]),
      tabBar,
      pagesBox,
      el('div', { class: 'scroll-btns' }, [
        el('button', { class: 'icon-btn', title: 'Subir', text: '▲', onclick: function () { pagesBox.scrollBy({ top: -260, behavior: 'smooth' }); } }),
        el('button', { class: 'icon-btn', title: 'Bajar', text: '▼', onclick: function () { pagesBox.scrollBy({ top: 260, behavior: 'smooth' }); } })])]);
    var picker = el('div', { id: 'picker', onclick: function (event) { if (event.target === picker) document.body.classList.remove('picker-open'); } }, [
      el('div', { class: 'box' }, [el('h2', { id: 'picker-title' }), el('div', { class: 'grid', id: 'picker-grid' }), el('div', { class: 'pager', id: 'picker-nav' }),
        el('div', { class: 'row' }, [el('button', { class: 'btn primary', text: 'Descargar más personajes', onclick: function () {
          document.body.classList.remove('picker-open'); showTab('catalog'); } }),
          el('button', { class: 'btn', text: 'Cancelar', onclick: function () { document.body.classList.remove('picker-open'); } })])])]);
    document.body.appendChild(el('button', { id: 'gear', title: 'Ajustes de Nikke Stage', text: '⚙',
      onclick: function () { setPanel(!document.body.classList.contains('panel-open')); } }));
    document.body.appendChild(panel);
    document.body.appendChild(el('div', { id: 'preview' }, [el('div', { id: 'preview-stage' }),
      el('div', { id: 'preview-bar' }, [el('b', { id: 'preview-name' }), el('span', { id: 'preview-status' }), el('div', { id: 'preview-actions' })])]));
    document.body.appendChild(picker);
    document.body.appendChild(el('div', { id: 'toast' }));
    showTab(installedCodes().length ? 'chars' : 'catalog');
  }

  // ------------------------------------------------------------------ start
  function loadDiskManifest() {
    return fetch(BASE + 'characters.json').then(function (r) { return r.json(); })
      .then(function (data) { diskChars = data.characters || {}; backgroundFile = data.background || null; })
      .catch(function () { diskChars = {}; });
  }

  function loadDbChars() {
    return idb('meta', 'readonly', function (s) { return s.get('chars'); })
      .then(function (data) { dbChars = data || {}; })
      .catch(function (e) { console.error('indexedDB: ' + e); dbChars = {}; });
  }

  function chooseDefaults() {
    // first run with nothing chosen: put the first installed characters in the free slots
    var any = false;
    for (var i = 1; i <= SLOT_COUNT; i++) if (values['char' + i] !== 'none') any = true;
    if (any) return;
    var codes = installedCodes();
    for (var n = 0; n < Math.min(SLOT_COUNT, codes.length, 2); n++) values['char' + (n + 1)] = codes[n];
  }

  function start() {
    for (var i = 0; i < SLOT_COUNT; i++) slots.push(createSlot(i));
    loadSaved();
    values = computeValues();
    chooseDefaults();
    buildUI();
    applyAll();
    loadCatalog();
    window.addEventListener('resize', function () { slots.forEach(layout); });
    window.addEventListener('keydown', function (event) { if (event.key === 'Escape') setPanel(false); });
    window.wallpaperPropertyListener = {
      applyUserProperties: function (delivered) {
        Object.keys(delivered || {}).forEach(function (key) { props[key] = delivered[key]; });
        values = computeValues();
        applyAll();
      }
    };
    if (window.wallpaperRegisterAudioListener) {
      window.wallpaperRegisterAudioListener(function (data) {
        var sum = 0;
        for (var n = 0; n < 12; n++) sum += data[n] || 0;
        level += (Math.min(1, sum / 12) - level) * 0.35;
        if (values.bounce > 0) slots.forEach(applyTransform);
      });
    }
  }

  Promise.all([loadDiskManifest(), loadDbChars()]).then(start);
})();
