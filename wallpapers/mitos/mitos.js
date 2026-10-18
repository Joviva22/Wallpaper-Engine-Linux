// Mitos en blanco y negro: Inazuma, Grecia, Grand Blue y mitologia nordica, dibujados en codigo (arte original,
// sin imagenes externas). Cada escena tiene una parte estatica (se pinta una vez en una capa) y otra animada.
(function () {
  'use strict';

  var SCENES = ['inazuma', 'grecia', 'grandblue', 'nordica'];
  var CAPTIONS = { inazuma: 'Inazuma Eleven', grecia: 'Ελλάς', grandblue: 'Grand Blue', nordica: 'Miðgarðr' };
  var props = { scene: 'auto', seconds: 45, grain: 12, contrast: 110, parallax: true, caption: true, particles: 100, fps: 30 };

  var canvas = document.getElementById('view');
  var ctx = canvas.getContext('2d');
  var grain = document.getElementById('grain');
  var caption = document.getElementById('caption');
  var W = 0, H = 0;
  var layers = {};          // scene -> cached static canvas
  var current = 0, next = -1, fade = 0, sceneTime = 0;
  var pointer = { x: 0, y: 0, sx: 0, sy: 0 };
  var lastFrame = 0;

  // ------------------------------------------------------------------ helpers
  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function gray(v, a) { v = Math.round(Math.max(0, Math.min(255, v))); return 'rgba(' + v + ',' + v + ',' + v + ',' + (a === undefined ? 1 : a) + ')'; }

  function vgrad(c, h, stops) {
    var g = c.createLinearGradient(0, 0, 0, h);
    stops.forEach(function (s) { g.addColorStop(s[0], gray(s[1])); });
    return g;
  }

  // silueta de montanas: `amp` es la altura maxima en pixeles sobre la linea y
  function ridge(c, w, y, amp, rough, seed, fill, step) {
    var r = rng(seed), pts = [], n = Math.ceil(w / (step || 40)) + 2, v = 0, max = 0.001;
    for (var i = 0; i < n; i++) { v += (r() - 0.5) * rough; v *= 0.93; pts.push(Math.abs(v)); max = Math.max(max, Math.abs(v)); }
    c.beginPath(); c.moveTo(0, c.canvas.height);
    for (var j = 0; j < n; j++) c.lineTo(j * (step || 40), y - pts[j] / max * amp);
    c.lineTo(w, c.canvas.height); c.closePath(); c.fillStyle = fill; c.fill();
  }

  function blob(c, x, y, rx, ry, alpha, v) {
    var g = c.createRadialGradient(x, y, 0, x, y, rx);
    g.addColorStop(0, gray(v, alpha)); g.addColorStop(1, gray(v, 0));
    c.save(); c.translate(0, y); c.scale(1, ry / rx); c.translate(0, -y);
    c.fillStyle = g; c.beginPath(); c.arc(x, y, rx, 0, 6.2832); c.fill(); c.restore();
  }

  function moon(c, x, y, r, seed) {
    var g = c.createRadialGradient(x, y, r * 0.2, x, y, r * 3);
    g.addColorStop(0, gray(255, 0.35)); g.addColorStop(1, gray(255, 0));
    c.fillStyle = g; c.beginPath(); c.arc(x, y, r * 3, 0, 6.2832); c.fill();
    c.fillStyle = gray(240); c.beginPath(); c.arc(x, y, r, 0, 6.2832); c.fill();
    var q = rng(seed);
    for (var i = 0; i < 14; i++) {
      var a = q() * 6.2832, d = Math.sqrt(q()) * r * 0.85;
      c.fillStyle = gray(190 + q() * 25, 0.55);
      c.beginPath(); c.arc(x + Math.cos(a) * d, y + Math.sin(a) * d, r * (0.05 + q() * 0.12), 0, 6.2832); c.fill();
    }
  }

  function stars(c, w, h, n, seed, maxY) {
    var q = rng(seed);
    for (var i = 0; i < n; i++) {
      c.fillStyle = gray(200 + q() * 55, 0.3 + q() * 0.7);
      var s = q() < 0.06 ? 2.2 : 1;
      c.fillRect(q() * w, q() * h * maxY, s, s);
    }
  }

  function wrap(v, m) { return ((v % m) + m) % m; }

  // ------------------------------------------------------------------ INAZUMA ELEVEN
  // Estadio de noche: focos, grada, campo, un emblema de rayo y un delantero rematando una bola de energia.
  function bolt(c, x, y, s, v, alpha) {
    c.fillStyle = gray(v, alpha); c.beginPath();
    c.moveTo(x + s * 0.12, y - s * 0.62); c.lineTo(x - s * 0.34, y + s * 0.06); c.lineTo(x - s * 0.04, y + s * 0.06);
    c.lineTo(x - s * 0.16, y + s * 0.62); c.lineTo(x + s * 0.36, y - s * 0.1); c.lineTo(x + s * 0.05, y - s * 0.1); c.closePath(); c.fill();
  }

  function ball(c, x, y, r, spin) {
    var g = c.createRadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r);
    g.addColorStop(0, gray(255)); g.addColorStop(1, gray(175));
    c.fillStyle = g; c.beginPath(); c.arc(x, y, r, 0, 6.2832); c.fill();
    c.save(); c.translate(x, y); c.rotate(spin); c.fillStyle = gray(15);
    function penta(px, py, pr) { c.beginPath(); for (var i = 0; i < 5; i++) { var a = i * 1.2566 - 1.5708; var xx = px + Math.cos(a) * pr, yy = py + Math.sin(a) * pr; if (i) c.lineTo(xx, yy); else c.moveTo(xx, yy); } c.closePath(); c.fill(); }
    penta(0, 0, r * 0.34);
    for (var k = 0; k < 5; k++) { var a = k * 1.2566 - 1.5708; penta(Math.cos(a) * r * 0.82, Math.sin(a) * r * 0.82, r * 0.2); }
    c.restore();
    c.strokeStyle = gray(10); c.lineWidth = Math.max(1.5, r * 0.06); c.beginPath(); c.arc(x, y, r, 0, 6.2832); c.stroke();
  }

  function limb(c, ax, ay, bx, by, cx, cy, w) {
    c.lineWidth = w; c.lineCap = 'round'; c.lineJoin = 'round'; c.beginPath(); c.moveTo(ax, ay); c.lineTo(bx, by); c.lineTo(cx, cy); c.stroke();
  }

  // delantero en remate acrobatico (silueta): u = altura del jugador
  function striker(c, x, y, u) {
    c.strokeStyle = gray(2); c.fillStyle = gray(2);
    // tronco inclinado hacia atras
    c.lineWidth = u * 0.17; c.lineCap = 'round';
    c.beginPath(); c.moveTo(x - u * 0.08, y - u * 0.5); c.lineTo(x + u * 0.04, y - u * 0.1); c.stroke();
    c.beginPath(); c.arc(x - u * 0.2, y - u * 0.58, u * 0.085, 0, 6.2832); c.fill();              // cabeza
    limb(c, x - u * 0.05, y - u * 0.46, x - u * 0.28, y - u * 0.36, x - u * 0.44, y - u * 0.44, u * 0.06);  // brazos
    limb(c, x - u * 0.03, y - u * 0.44, x + u * 0.2, y - u * 0.48, x + u * 0.3, y - u * 0.62, u * 0.06);
    limb(c, x + u * 0.04, y - u * 0.1, x + u * 0.28, y - u * 0.3, x + u * 0.58, y - u * 0.5, u * 0.085);    // pierna de remate
    limb(c, x + u * 0.02, y - u * 0.08, x - u * 0.16, y + u * 0.2, x - u * 0.1, y + u * 0.52, u * 0.085);   // pierna de apoyo
  }

  function inazumaStatic(c, w, h) {
    c.fillStyle = vgrad(c, h, [[0, 6], [0.45, 40], [0.62, 90], [1, 20]]); c.fillRect(0, 0, w, h);
    stars(c, w, h, 90, 11, 0.35);
    var hy = h * 0.6;                                           // horizonte de la grada
    // focos
    [0.08, 0.3, 0.7, 0.92].forEach(function (fx, i) {
      var x = w * fx, y = h * (0.16 + (i % 2) * 0.03);
      var cone = c.createLinearGradient(0, y, 0, hy);
      cone.addColorStop(0, gray(255, 0.28)); cone.addColorStop(1, gray(255, 0));
      c.fillStyle = cone; c.beginPath(); c.moveTo(x - 14, y); c.lineTo(x + 14, y); c.lineTo(x + (fx < 0.5 ? 1 : -1) * w * 0.1 + 200, hy); c.lineTo(x + (fx < 0.5 ? 1 : -1) * w * 0.1 - 200, hy); c.closePath(); c.fill();
      c.fillStyle = gray(3); c.fillRect(x - 3, y, 6, hy - y);
      c.fillRect(x - 46, y - 22, 92, 26);
      c.fillStyle = gray(255); for (var l = 0; l < 6; l++) c.fillRect(x - 40 + l * 15, y - 17, 11, 16);
      blob(c, x, y - 8, 120, 120, 0.55, 255);
    });
    // emblema: circulo con rayo
    var ex = w * 0.5, ey = h * 0.36, er = h * 0.27;
    blob(c, ex, ey, er * 2, er * 2, 0.5, 255);
    c.fillStyle = gray(8, 0.82); c.beginPath(); c.arc(ex, ey, er, 0, 6.2832); c.fill();
    c.strokeStyle = gray(245); c.lineWidth = er * 0.05; c.beginPath(); c.arc(ex, ey, er, 0, 6.2832); c.stroke();
    c.lineWidth = er * 0.02; c.beginPath(); c.arc(ex, ey, er * 0.9, 0, 6.2832); c.stroke();
    bolt(c, ex, ey, er * 1.55, 250, 0.95);
    // grada: filas de siluetas de publico
    var q = rng(19);
    for (var row = 0; row < 3; row++) {
      var y0 = hy - row * h * 0.035 - h * 0.01; c.fillStyle = gray(30 - row * 9);
      c.fillRect(0, y0, w, h * 0.05);
      for (var x = -10; x < w + 10; x += 9 + q() * 6) { c.beginPath(); c.arc(x, y0 + q() * 3, 5 + q() * 2, 0, 6.2832); c.fill(); }
    }
    c.fillStyle = gray(4); c.fillRect(0, hy + h * 0.02, w, h * 0.012);      // valla
    // campo con franjas en perspectiva
    var fy = hy + h * 0.032;
    for (var i = 0; i < 9; i++) {
      var y1 = fy + (h - fy) * Math.pow(i / 9, 1.7), y2 = fy + (h - fy) * Math.pow((i + 1) / 9, 1.7);
      c.fillStyle = gray(i % 2 ? 46 : 62); c.fillRect(0, y1, w, y2 - y1 + 1);
    }
    c.strokeStyle = gray(235, 0.85); c.lineWidth = 3;
    c.beginPath(); c.ellipse(w * 0.5, h * 0.9, w * 0.2, h * 0.07, 0, 0, 6.2832); c.stroke();
    c.beginPath(); c.moveTo(0, h * 0.96); c.lineTo(w, h * 0.96); c.stroke();
    // porteria lejana
    var gx = w * 0.82, gy = fy + h * 0.015;
    c.strokeStyle = gray(240); c.lineWidth = 3; c.strokeRect(gx, gy - h * 0.06, w * 0.1, h * 0.06);
    c.strokeStyle = gray(240, 0.4); c.lineWidth = 1; c.beginPath();
    for (var k = 1; k < 8; k++) { c.moveTo(gx + w * 0.1 * k / 8, gy - h * 0.06); c.lineTo(gx + w * 0.1 * k / 8, gy); }
    for (var m = 1; m < 4; m++) { c.moveTo(gx, gy - h * 0.06 * m / 4); c.lineTo(gx + w * 0.1, gy - h * 0.06 * m / 4); }
    c.stroke();
    // jugador
    striker(c, w * 0.44, h * 0.66, h * 0.4);
  }

  var storm = { next: 1.5, bolt: null, age: 9 };
  function makeBolt(x0, y0, x1, y1) {
    var segs = [], q = Math.random, steps = 14;
    var px = x0, py = y0;
    for (var i = 1; i <= steps; i++) {
      var t = i / steps, nx = x0 + (x1 - x0) * t + (q() - 0.5) * 90 * (1 - t * 0.5), ny = y0 + (y1 - y0) * t;
      segs.push([px, py, nx, ny, 3 * (1 - t * 0.4)]);
      if (q() < 0.3) segs.push([nx, ny, nx + (q() - 0.5) * 140, ny + 50 + q() * 70, 1.5]);
      px = nx; py = ny;
    }
    return segs;
  }

  function inazumaDynamic(c, w, h, t, dt, quality) {
    var bx = w * 0.6 + Math.sin(t * 0.9) * w * 0.012, by = h * 0.4 + Math.sin(t * 1.3) * h * 0.012, br = h * 0.052;
    // espiral de energia alrededor del balon
    c.save(); c.globalCompositeOperation = 'lighter';
    for (var arm = 0; arm < 3; arm++) {
      c.beginPath();
      for (var i = 0; i < 60; i++) {
        var a = i * 0.28 + t * 3 + arm * 2.0944, r = br * (1.3 + i * 0.07);
        var x = bx + Math.cos(a) * r, y = by + Math.sin(a) * r * 0.55;
        if (i) c.lineTo(x, y); else c.moveTo(x, y);
      }
      c.strokeStyle = gray(255, 0.35); c.lineWidth = 3; c.stroke();
    }
    blob(c, bx, by, br * 5, br * 5, 0.6, 255);
    c.restore();
    // estela: bola -> jugador
    var g = c.createLinearGradient(w * 0.57, h * 0.46, bx, by); g.addColorStop(0, gray(255, 0)); g.addColorStop(1, gray(255, 0.4));
    c.strokeStyle = g; c.lineWidth = br * 0.8; c.lineCap = 'round'; c.beginPath(); c.moveTo(w * 0.57, h * 0.46); c.lineTo(bx - br, by + br * 0.5); c.stroke();
    ball(c, bx, by, br, t * 4);
    // rayos que salen del balon
    storm.next -= dt; storm.age += dt;
    if (storm.next <= 0) {
      var ang = Math.random() * 6.2832, len = h * (0.25 + Math.random() * 0.3);
      storm.bolt = makeBolt(bx, by, bx + Math.cos(ang) * len, by + Math.sin(ang) * len * 0.8); storm.age = 0; storm.next = 0.6 + Math.random() * 1.8;
    }
    if (storm.bolt && storm.age < 0.3) {
      var life = 1 - storm.age / 0.3, flick = Math.sin(storm.age * 90) > -0.3 ? 1 : 0.4;
      c.fillStyle = gray(255, 0.1 * life * flick); c.fillRect(0, 0, w, h);
      c.shadowColor = '#fff'; c.shadowBlur = 22; c.lineCap = 'round';
      storm.bolt.forEach(function (s) { c.strokeStyle = gray(255, flick); c.lineWidth = s[4] * (0.6 + life); c.beginPath(); c.moveTo(s[0], s[1]); c.lineTo(s[2], s[3]); c.stroke(); });
      c.shadowBlur = 0;
    }
    // chispas y polvo de cesped
    var n = Math.round(60 * quality);
    for (var p = 0; p < n; p++) {
      var r1 = rng(p * 71 + 5)(), r2 = rng(p * 19 + 11)();
      var age = wrap(t * (0.25 + r1 * 0.3) + r2, 1);
      var px = bx + Math.cos(p * 2.3) * br * (1 + age * 9), py = by + Math.sin(p * 2.3) * br * (1 + age * 6);
      c.fillStyle = gray(255, (1 - age) * 0.9); c.fillRect(px, py, 2 + r1 * 2, 2 + r1 * 2);
    }
    for (var d = 0; d < 30 * quality; d++) {
      var rr = rng(d * 7 + 2)(), dx = wrap(rr * w + t * (15 + rr * 20), w), dy = h * (0.7 + rng(d * 3 + 8)() * 0.28) - Math.abs(Math.sin(t + d)) * 14;
      c.fillStyle = gray(240, 0.25); c.beginPath(); c.arc(dx, dy, 1.2 + rr * 1.6, 0, 6.2832); c.fill();
    }
  }

  // ------------------------------------------------------------------ GRECIA
  function column(c, x, base, top, w) {
    var g = c.createLinearGradient(x - w / 2, 0, x + w / 2, 0);
    g.addColorStop(0, gray(150)); g.addColorStop(0.35, gray(250)); g.addColorStop(1, gray(120));
    c.fillStyle = g; c.fillRect(x - w / 2, top, w, base - top);
    c.fillStyle = gray(235); c.fillRect(x - w * 0.62, top - w * 0.2, w * 1.24, w * 0.2);   // capitel
    c.fillStyle = gray(215); c.fillRect(x - w * 0.52, top - w * 0.34, w * 1.04, w * 0.14);
    c.strokeStyle = gray(90, 0.55); c.lineWidth = 1;
    for (var i = 1; i < 6; i++) { var fx = x - w / 2 + w * i / 6; c.beginPath(); c.moveTo(fx, top); c.lineTo(fx, base); c.stroke(); }
  }

  function meander(c, x0, y, w, size, v) {
    c.strokeStyle = gray(v); c.lineWidth = Math.max(2, size * 0.14); c.lineJoin = 'miter'; c.beginPath();
    var n = Math.ceil(w / (size * 2));
    for (var i = 0; i < n; i++) {
      var x = x0 + i * size * 2;
      c.moveTo(x, y + size); c.lineTo(x, y); c.lineTo(x + size * 1.5, y); c.lineTo(x + size * 1.5, y + size * 0.75);
      c.lineTo(x + size * 0.5, y + size * 0.75); c.lineTo(x + size * 0.5, y + size * 0.3); c.lineTo(x + size, y + size * 0.3);
      c.moveTo(x + size * 1.5, y + size); c.lineTo(x + size * 2, y + size);
    }
    c.stroke();
  }

  function laurel(c, x, y, r, count, v) {
    c.fillStyle = gray(v);
    for (var side = -1; side <= 1; side += 2) {
      for (var i = 0; i < count; i++) {
        var a = Math.PI / 2 + side * (0.25 + i * (Math.PI * 1.55 / count) / 2);
        var px = x + Math.cos(a) * r, py = y + Math.sin(a) * r;
        c.save(); c.translate(px, py); c.rotate(a + side * 0.9);
        c.beginPath(); c.ellipse(0, 0, r * 0.14, r * 0.05, 0, 0, 6.2832); c.fill(); c.restore();
      }
    }
  }

  function grecaStatic(c, w, h) {
    c.fillStyle = vgrad(c, h, [[0, 150], [0.5, 215], [1, 250]]); c.fillRect(0, 0, w, h);
    var sx = w * 0.5, sy = h * 0.34, sr = h * 0.17;
    var rg = c.createRadialGradient(sx, sy, sr * 0.5, sx, sy, sr * 4);
    rg.addColorStop(0, gray(255, 0.9)); rg.addColorStop(1, gray(255, 0)); c.fillStyle = rg; c.fillRect(0, 0, w, h);
    c.fillStyle = gray(255); c.beginPath(); c.arc(sx, sy, sr, 0, 6.2832); c.fill();
    c.strokeStyle = gray(40, 0.8); c.lineWidth = 3; c.beginPath(); c.arc(sx, sy, sr * 1.12, 0, 6.2832); c.stroke();
    laurel(c, sx, sy, sr * 1.25, 14, 30);
    ridge(c, w, h * 0.72, h * 0.14, 20, 41, gray(125), 46);
    // templo
    var base = h * 0.84, colW = w * 0.032, n = 8, left = w * 0.2, right = w * 0.8, top = h * 0.42;
    var sh = h * 0.012;
    for (var s = 0; s < 3; s++) { c.fillStyle = gray(235 - s * 18); c.fillRect(left - w * 0.03 - s * w * 0.014, base + s * sh, (right - left) + w * 0.06 + s * w * 0.028, sh + 1); }
    for (var i = 0; i < n; i++) column(c, left + (right - left) * i / (n - 1), base, top, colW);
    c.fillStyle = gray(228); c.fillRect(left - w * 0.025, top - colW * 0.9, right - left + w * 0.05, colW * 0.56);
    meander(c, left - w * 0.02, top - colW * 0.82, right - left + w * 0.04, colW * 0.24, 40);
    c.fillStyle = gray(246); c.beginPath(); c.moveTo(left - w * 0.035, top - colW * 0.9); c.lineTo(sx, top - h * 0.17); c.lineTo(right + w * 0.035, top - colW * 0.9); c.closePath(); c.fill();
    c.strokeStyle = gray(60); c.lineWidth = 3; c.stroke();
    c.fillStyle = gray(205); c.beginPath(); c.moveTo(left + w * 0.04, top - colW * 1.1); c.lineTo(sx, top - h * 0.14); c.lineTo(right - w * 0.04, top - colW * 1.1); c.closePath(); c.fill();
    // suelo y friso
    c.fillStyle = gray(18); c.fillRect(0, base + sh * 3, w, h);
    meander(c, 0, h * 0.94, w, h * 0.035, 235);
    // olivo
    var ox = w * 0.9, oy = base; c.fillStyle = gray(12); c.fillRect(ox - 6, oy - h * 0.2, 12, h * 0.2);
    var q = rng(77); for (var k = 0; k < 40; k++) blob(c, ox + (q() - 0.5) * w * 0.1, oy - h * 0.22 - q() * h * 0.1, w * 0.04, h * 0.03, 0.9, 12);
  }

  function grecaDynamic(c, w, h, t, dt, quality) {
    for (var i = 0; i < 5; i++) {
      var x = wrap(i * w * 0.36 + t * (5 + i * 1.6), w * 1.5) - w * 0.25, y = h * (0.1 + (i % 3) * 0.12);
      blob(c, x, y, w * 0.2, h * 0.05, 0.75, 255);
    }
    // rayos de sol
    c.save(); c.translate(w * 0.5, h * 0.34); c.globalCompositeOperation = 'lighter';
    for (var r = 0; r < 12; r++) {
      var a = r * 0.5236 + t * 0.02;
      c.fillStyle = gray(255, 0.035); c.beginPath(); c.moveTo(0, 0); c.lineTo(Math.cos(a - 0.05) * w, Math.sin(a - 0.05) * w); c.lineTo(Math.cos(a + 0.05) * w, Math.sin(a + 0.05) * w); c.closePath(); c.fill();
    }
    c.restore();
    // aves
    c.strokeStyle = gray(20); c.lineWidth = 2;
    for (var b = 0; b < 7; b++) {
      var bx = wrap(b * w * 0.17 + t * (30 + b * 3), w * 1.2) - w * 0.1, by = h * (0.2 + (b % 4) * 0.045) + Math.sin(t + b) * 8, f = Math.sin(t * 5 + b) * 5;
      c.beginPath(); c.moveTo(bx - 12, by - f); c.quadraticCurveTo(bx - 5, by - 6, bx, by); c.quadraticCurveTo(bx + 5, by - 6, bx + 12, by - f); c.stroke();
    }
    // polvo dorado (en gris) y hojas
    var n = Math.round(40 * quality);
    for (var p = 0; p < n; p++) {
      var rr = rng(p * 53 + 9)();
      var px = wrap(rr * w + t * (8 + rr * 10), w), py = wrap(rng(p * 17 + 5)() * h - t * (6 + rr * 8), h);
      c.fillStyle = gray(255, 0.35 + 0.3 * Math.sin(t + p)); c.beginPath(); c.arc(px, py, 1 + rr * 2, 0, 6.2832); c.fill();
    }
  }

  // ------------------------------------------------------------------ GRAND BLUE
  function diver(c, x, y, s, t) {
    c.save(); c.translate(x, y); c.rotate(-0.25 + Math.sin(t * 0.6) * 0.04); c.scale(s, s);
    c.fillStyle = gray(4);
    c.beginPath(); c.ellipse(0, 0, 70, 22, 0, 0, 6.2832); c.fill();                  // torso
    c.beginPath(); c.arc(78, -4, 17, 0, 6.2832); c.fill();                            // cabeza
    c.fillStyle = gray(215, 0.8); c.beginPath(); c.ellipse(86, -6, 9, 7, 0.2, 0, 6.2832); c.fill(); // mascara
    c.fillStyle = gray(4); c.beginPath(); c.roundRect ? c.roundRect(-45, -38, 70, 22, 11) : c.rect(-45, -38, 70, 22); c.fill(); // botella
    c.lineCap = 'round'; c.strokeStyle = gray(4); c.lineWidth = 12;
    var kick = Math.sin(t * 2) * 9;
    c.beginPath(); c.moveTo(-60, 4); c.lineTo(-130, 18 + kick); c.stroke();            // piernas
    c.beginPath(); c.moveTo(-60, -2); c.lineTo(-128, -8 - kick); c.stroke();
    c.beginPath(); c.moveTo(-128, 18 + kick); c.lineTo(-170, 34 + kick * 1.4); c.lineTo(-166, 6 + kick); c.closePath(); c.fill(); // aletas
    c.beginPath(); c.moveTo(-126, -8 - kick); c.lineTo(-166, -26 - kick * 1.4); c.lineTo(-170, 2 - kick); c.closePath(); c.fill();
    c.beginPath(); c.moveTo(48, 6); c.lineTo(108, 34); c.stroke();                      // brazo
    c.restore();
  }

  function grandStatic(c, w, h) {
    c.fillStyle = vgrad(c, h, [[0, 235], [0.2, 165], [0.6, 70], [1, 14]]); c.fillRect(0, 0, w, h);
    // lecho marino y rocas
    ridge(c, w, h * 0.9, h * 0.1, 24, 61, gray(16), 36);
    ridge(c, w, h * 0.97, h * 0.07, 20, 62, gray(4), 30);
    // coral
    var q = rng(66);
    for (var i = 0; i < 26; i++) {
      var x = q() * w, y = h * (0.9 + q() * 0.08), len = h * (0.04 + q() * 0.08);
      c.strokeStyle = gray(6); c.lineWidth = 3 + q() * 5; c.lineCap = 'round';
      for (var b = -1; b <= 1; b++) { c.beginPath(); c.moveTo(x, y); c.quadraticCurveTo(x + b * len * 0.5, y - len * 0.6, x + b * len * 0.9, y - len); c.stroke(); }
    }
  }

  function grandDynamic(c, w, h, t, dt, quality) {
    // rayos desde la superficie
    c.save(); c.globalCompositeOperation = 'lighter';
    for (var r = 0; r < 9; r++) {
      var x0 = w * (r / 8) + Math.sin(t * 0.3 + r) * 30, wd = w * 0.03, slant = w * 0.12;
      var g = c.createLinearGradient(0, 0, 0, h * 0.85); g.addColorStop(0, gray(255, 0.22)); g.addColorStop(1, gray(255, 0));
      c.fillStyle = g; c.beginPath(); c.moveTo(x0, 0); c.lineTo(x0 + wd, 0); c.lineTo(x0 + wd * 2.5 - slant, h * 0.85); c.lineTo(x0 - wd * 1.5 - slant, h * 0.85); c.closePath(); c.fill();
    }
    c.restore();
    // superficie
    c.fillStyle = gray(250); c.beginPath(); c.moveTo(0, 0); 
    for (var x = 0; x <= w; x += 12) c.lineTo(x, h * 0.04 + Math.sin(x * 0.012 + t * 1.4) * 8 + Math.sin(x * 0.03 - t * 2) * 3);
    c.lineTo(w, 0); c.closePath(); c.fill();
    // algas
    for (var k = 0; k < 18; k++) {
      var kx = rng(k * 29 + 4)() * w, kh = h * (0.12 + rng(k * 5 + 1)() * 0.12);
      c.strokeStyle = gray(5); c.lineWidth = 5; c.lineCap = 'round'; c.beginPath(); c.moveTo(kx, h * 0.95);
      c.bezierCurveTo(kx + Math.sin(t + k) * 25, h * 0.95 - kh * 0.4, kx - Math.sin(t * 0.8 + k) * 25, h * 0.95 - kh * 0.7, kx + Math.sin(t * 1.1 + k) * 18, h * 0.95 - kh); c.stroke();
    }
    // cardumen
    for (var f = 0; f < 36; f++) {
      var fr = rng(f * 41 + 3)(), fx = wrap(fr * w * 1.2 + t * (50 + fr * 25), w * 1.3) - w * 0.15, fy = h * (0.3 + 0.18 * Math.sin(f * 0.7 + t * 0.4) + (f % 3) * 0.04);
      c.fillStyle = gray(8 + fr * 30, 0.9); c.beginPath(); c.ellipse(fx, fy, 10, 4, 0, 0, 6.2832); c.fill();
      c.beginPath(); c.moveTo(fx - 9, fy); c.lineTo(fx - 17, fy - 5 + Math.sin(t * 10 + f) * 2); c.lineTo(fx - 17, fy + 5); c.fill();
    }
    // buceador y burbujas
    var dx = w * 0.42 + Math.sin(t * 0.25) * w * 0.04, dy = h * 0.5 + Math.sin(t * 0.5) * h * 0.015;
    diver(c, dx, dy, h / 600, t);
    c.strokeStyle = gray(240, 0.8); c.lineWidth = 1.5;
    var nb = Math.round(34 * quality);
    for (var b = 0; b < nb; b++) {
      var age = wrap(t * 0.35 + b / nb, 1), bx = dx + (h / 600) * 90 + Math.sin(age * 14 + b) * 14 * age + (b % 5) * 4, by = dy - age * h * 0.6;
      c.beginPath(); c.arc(bx, by, 2 + (b % 4) * 1.5 * age, 0, 6.2832); c.stroke();
    }
  }

  // ------------------------------------------------------------------ MITOLOGIA NORDICA
  var RUNES = [
    [[0.3, 0, 0.3, 1], [0.3, 0.35, 0.8, 0.1], [0.3, 0.65, 0.8, 0.4]],              // fehu
    [[0.2, 1, 0.2, 0], [0.2, 0, 0.8, 0.3], [0.8, 0.3, 0.8, 1]],                      // uruz
    [[0.3, 0, 0.3, 1], [0.3, 0.25, 0.8, 0.5], [0.8, 0.5, 0.3, 0.75]],               // thurisaz
    [[0.3, 0, 0.3, 1], [0.3, 0.1, 0.8, 0.35], [0.3, 0.4, 0.8, 0.65]],               // ansuz
    [[0.3, 0, 0.3, 1], [0.3, 0, 0.8, 0.25], [0.8, 0.25, 0.3, 0.5], [0.3, 0.5, 0.8, 1]], // raidho
    [[0.75, 0.2, 0.25, 0.5], [0.25, 0.5, 0.75, 0.8]],                                // kenaz
    [[0.2, 0.1, 0.8, 0.9], [0.8, 0.1, 0.2, 0.9]],                                    // gebo
    [[0.3, 0, 0.3, 1], [0.3, 0, 0.75, 0.2], [0.75, 0.2, 0.3, 0.4]],                 // wunjo
    [[0.2, 0, 0.2, 1], [0.8, 0, 0.8, 1], [0.2, 0.35, 0.8, 0.65]],                   // hagalaz
    [[0.5, 0, 0.5, 1], [0.2, 0.3, 0.8, 0.6]],                                        // nauthiz
    [[0.5, 0, 0.5, 1]],                                                              // isa
    [[0.5, 0, 0.5, 1], [0.5, 0.2, 0.9, 0.5], [0.5, 0.5, 0.1, 0.8]]                  // sowilo-ish
  ];

  function drawRune(c, n, x, y, s, alpha) {
    c.strokeStyle = gray(245, alpha); c.lineWidth = Math.max(1.5, s * 0.08); c.lineCap = 'round';
    RUNES[n % RUNES.length].forEach(function (l) { c.beginPath(); c.moveTo(x + l[0] * s, y + l[1] * s * 1.4); c.lineTo(x + l[2] * s, y + l[3] * s * 1.4); c.stroke(); });
  }

  function valknut(c, x, y, r, v, alpha) {
    c.strokeStyle = gray(v, alpha); c.lineWidth = Math.max(2, r * 0.07); c.lineJoin = 'round';
    for (var i = 0; i < 3; i++) {
      var a = i * 2.0944 - 1.5708, cx = x + Math.cos(a) * r * 0.5, cy = y + Math.sin(a) * r * 0.5;
      c.beginPath();
      for (var k = 0; k < 3; k++) { var b = a + Math.PI + k * 2.0944 + 0.52; var px = cx + Math.cos(b) * r * 0.8, py = cy + Math.sin(b) * r * 0.8; if (k) c.lineTo(px, py); else c.moveTo(px, py); }
      c.closePath(); c.stroke();
    }
  }

  function longship(c, x, y, s) {
    c.fillStyle = gray(3); c.beginPath();
    c.moveTo(x - s * 0.5, y - s * 0.12);
    c.quadraticCurveTo(x - s * 0.52, y - s * 0.3, x - s * 0.42, y - s * 0.38);          // proa dragon
    c.quadraticCurveTo(x - s * 0.38, y - s * 0.32, x - s * 0.4, y - s * 0.26);
    c.quadraticCurveTo(x - s * 0.3, y + s * 0.02, x - s * 0.12, y + s * 0.07);
    c.lineTo(x + s * 0.28, y + s * 0.07);
    c.quadraticCurveTo(x + s * 0.46, y, x + s * 0.5, y - s * 0.22);                       // popa
    c.quadraticCurveTo(x + s * 0.4, y - s * 0.06, x + s * 0.3, y - s * 0.08);
    c.lineTo(x - s * 0.4, y - s * 0.1); c.closePath(); c.fill();
    c.fillRect(x - s * 0.02, y - s * 0.62, s * 0.014, s * 0.56);                          // mastil
    c.beginPath(); c.moveTo(x - s * 0.01, y - s * 0.6); c.quadraticCurveTo(x + s * 0.28, y - s * 0.5, x + s * 0.3, y - s * 0.16);
    c.lineTo(x - s * 0.01, y - s * 0.18); c.closePath(); c.fill();
    c.strokeStyle = gray(200, 0.5); c.lineWidth = 2; c.beginPath(); c.moveTo(x + s * 0.02, y - s * 0.52); c.lineTo(x + s * 0.28, y - s * 0.46); c.moveTo(x + s * 0.02, y - s * 0.4); c.lineTo(x + s * 0.28, y - s * 0.36); c.stroke();
  }

  function yggdrasil(c, x, base, size) {
    var q = rng(88); c.strokeStyle = gray(2); c.fillStyle = gray(2); c.lineCap = 'round';
    function branch(bx, by, ang, len, wd, d) {
      if (d > 6 || len < size * 0.015) return;
      var ex = bx + Math.sin(ang) * len, ey = by - Math.cos(ang) * len;
      c.lineWidth = wd; c.beginPath(); c.moveTo(bx, by); c.quadraticCurveTo((bx + ex) / 2 + (q() - 0.5) * len * 0.2, (by + ey) / 2, ex, ey); c.stroke();
      if (d >= 4) { c.beginPath(); c.arc(ex, ey, size * 0.008 + q() * size * 0.012, 0, 6.2832); c.fill(); }
      var n = d < 2 ? 3 : 2;
      for (var i = 0; i < n; i++) branch(ex, ey, ang + (q() - 0.5) * 1.3 + (i - (n - 1) / 2) * 0.45, len * (0.68 + q() * 0.12), wd * 0.68, d + 1);
    }
    branch(x, base, 0, size * 0.34, size * 0.06, 0);
    branch(x, base, -0.35, size * 0.26, size * 0.04, 1);
    branch(x, base, 0.35, size * 0.26, size * 0.04, 1);
    for (var r = -3; r <= 3; r++) {     // raices
      c.lineWidth = size * 0.028; c.beginPath(); c.moveTo(x, base - 6); c.quadraticCurveTo(x + r * size * 0.08, base + size * 0.05, x + r * size * 0.2, base + size * 0.14); c.stroke();
    }
  }

  function nordicaStatic(c, w, h) {
    c.fillStyle = vgrad(c, h, [[0, 4], [0.55, 55], [0.8, 120], [1, 70]]); c.fillRect(0, 0, w, h);
    stars(c, w, h, 260, 91, 0.6);
    moon(c, w * 0.9, h * 0.2, h * 0.07, 13);
    valknut(c, w * 0.16, h * 0.2, h * 0.09, 220, 0.55);
    blob(c, w * 0.7, h * 0.74, w * 0.5, h * 0.3, 0.5, 255);
    ridge(c, w, h * 0.8, h * 0.3, 34, 92, gray(60), 30);
    ridge(c, w, h * 0.8, h * 0.16, 34, 93, gray(24), 34);
    // mar
    var sea = vgrad(c, h, [[0, 60], [1, 6]]); c.fillStyle = sea; c.fillRect(0, h * 0.8, w, h * 0.2);
    c.strokeStyle = gray(240, 0.3); c.lineWidth = 1.5; var q = rng(94);
    for (var i = 0; i < 60; i++) { var x = q() * w, y = h * (0.81 + q() * 0.18), l = 20 + q() * 90; c.beginPath(); c.moveTo(x, y); c.lineTo(x + l, y); c.stroke(); }
    longship(c, w * 0.22, h * 0.84, h * 0.34);
    yggdrasil(c, w * 0.64, h * 0.82, h * 0.82);
      }

  function nordicaDynamic(c, w, h, t, dt, quality) {
    // aurora
    c.save(); c.globalCompositeOperation = 'lighter';
    for (var b = 0; b < 3; b++) {
      c.beginPath(); c.moveTo(0, h * (0.22 + b * 0.06));
      for (var x = 0; x <= w; x += 20) c.lineTo(x, h * (0.2 + b * 0.07) + Math.sin(x * 0.004 + t * (0.35 + b * 0.1) + b) * h * 0.06 + Math.sin(x * 0.011 - t * 0.5) * h * 0.015);
      for (var x2 = w; x2 >= 0; x2 -= 20) c.lineTo(x2, h * (0.38 + b * 0.07) + Math.sin(x2 * 0.003 - t * 0.3 + b) * h * 0.05);
      c.closePath();
      var g = c.createLinearGradient(0, h * 0.15, 0, h * 0.55); g.addColorStop(0, gray(255, 0.0)); g.addColorStop(0.3, gray(255, 0.12 - b * 0.025)); g.addColorStop(1, gray(255, 0));
      c.fillStyle = g; c.fill();
    }
    c.restore();
    // runas flotantes
    for (var r = 0; r < 9; r++) {
      var rx = w * (0.08 + r * 0.105) + Math.sin(t * 0.3 + r) * 14, ry = h * (0.38 + (r % 3) * 0.06) + Math.sin(t * 0.5 + r * 1.7) * 12;
      drawRune(c, r * 5 + 1, rx, ry, h * 0.034, 0.35 + 0.35 * Math.sin(t * 0.8 + r * 2));
    }
    // nieve
    var n = Math.round(120 * quality);
    for (var p = 0; p < n; p++) {
      var rr = rng(p * 61 + 7)(), px = wrap(rr * w + Math.sin(t * 0.6 + p) * 24 - t * 10, w), py = wrap(rng(p * 23 + 3)() * h + t * (22 + rr * 38), h);
      c.fillStyle = gray(255, 0.4 + rr * 0.5); c.beginPath(); c.arc(px, py, 0.8 + rr * 2.1, 0, 6.2832); c.fill();
    }
  }

  var SCENE_DEFS = {
    inazuma: { build: inazumaStatic, draw: inazumaDynamic },
    grecia: { build: grecaStatic, draw: grecaDynamic },
    grandblue: { build: grandStatic, draw: grandDynamic },
    nordica: { build: nordicaStatic, draw: nordicaDynamic }
  };

  // ------------------------------------------------------------------ engine
  function layer(name) {
    if (!layers[name]) {
      var c = document.createElement('canvas'); c.width = W; c.height = H;
      SCENE_DEFS[name].build(c.getContext('2d'), W, H);
      layers[name] = c;
    }
    return layers[name];
  }

  function renderScene(c, name, t, dt) {
    var quality = props.particles / 100;
    var ox = props.parallax ? -pointer.sx * 14 : 0, oy = props.parallax ? -pointer.sy * 8 : 0;
    c.save(); c.translate(W / 2 + ox, H / 2 + oy); c.scale(1.04, 1.04); c.translate(-W / 2, -H / 2);
    c.drawImage(layer(name), 0, 0); c.restore();
    SCENE_DEFS[name].draw(c, W, H, t, dt, quality);
    // vineta
    var v = c.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.05);
    v.addColorStop(0, gray(0, 0)); v.addColorStop(1, gray(0, 0.55)); c.fillStyle = v; c.fillRect(0, 0, W, H);
  }

  var offscreen = document.createElement('canvas');

  function sceneName(index) { return SCENES[wrap(index, SCENES.length)]; }

  function showCaption() {
    caption.classList.remove('show');
    if (!props.caption) return;
    setTimeout(function () { caption.textContent = CAPTIONS[sceneName(current)]; caption.classList.add('show'); }, 300);
  }

  function goTo(index) {
    if (index === current || next !== -1) return;
    next = wrap(index, SCENES.length); fade = 0;
  }

  function frame(now) {
    requestAnimationFrame(frame);
    var interval = 1000 / Math.max(10, props.fps);
    if (now - lastFrame < interval - 2) return;
    var dt = Math.min(0.1, (now - lastFrame) / 1000 || 0.033); lastFrame = now;
    sceneTime += dt;
    pointer.sx += (pointer.x - pointer.sx) * 0.05; pointer.sy += (pointer.y - pointer.sy) * 0.05;

    if (props.scene === 'auto') {
      if (next === -1 && sceneTime > props.seconds) goTo(current + 1);
    } else {
      var wanted = SCENES.indexOf(props.scene);
      if (wanted !== -1 && wanted !== current && next === -1) goTo(wanted);
    }

    renderScene(ctx, sceneName(current), now / 1000, dt);
    if (next !== -1) {
      fade += dt / 1.6;
      offscreen.width = W; offscreen.height = H;
      renderScene(offscreen.getContext('2d'), sceneName(next), now / 1000, dt);
      // fundido a negro en el centro de la transicion: mas elegante en blanco y negro
      var k = Math.min(1, fade);
      ctx.globalAlpha = k < 0.5 ? 0 : (k - 0.5) * 2; ctx.drawImage(offscreen, 0, 0); ctx.globalAlpha = 1;
      ctx.fillStyle = gray(0, k < 0.5 ? k * 2 : (1 - k) * 2); ctx.fillRect(0, 0, W, H);
      if (fade >= 1) { current = next; next = -1; sceneTime = 0; showCaption(); }
    }
  }

  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W; canvas.height = H;
    layers = {};
  }

  function makeGrain() {
    var g = document.createElement('canvas'); g.width = g.height = 128;
    var gc = g.getContext('2d'), img = gc.createImageData(128, 128), r = rng(5);
    for (var i = 0; i < img.data.length; i += 4) { var v = r() * 255; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255; }
    gc.putImageData(img, 0, 0);
    grain.style.backgroundImage = 'url(' + g.toDataURL() + ')';
    setInterval(function () { grain.style.backgroundPosition = Math.floor(Math.random() * 128) + 'px ' + Math.floor(Math.random() * 128) + 'px'; }, 90);
  }

  function applyProps() {
    grain.style.opacity = String(props.grain / 100);
    canvas.style.filter = 'contrast(' + props.contrast + '%)';
    if (!props.caption) caption.classList.remove('show'); else caption.classList.add('show');
  }

  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', function (e) { pointer.x = e.clientX / W - 0.5; pointer.y = e.clientY / H - 0.5; });
  window.addEventListener('click', function () { if (props.scene === 'auto') goTo(current + 1); });
  window.wallpaperPropertyListener = {
    applyUserProperties: function (p) {
      Object.keys(p || {}).forEach(function (k) {
        var v = p[k] && p[k].value !== undefined ? p[k].value : p[k];
        props[k] = v;
      });
      props.seconds = Math.max(5, Number(props.seconds) || 45);
      applyProps();
    }
  };
  window.mitos = { goTo: goTo, props: props, scenes: SCENES };

  resize(); makeGrain(); applyProps(); showCaption();
  requestAnimationFrame(frame);
})();
