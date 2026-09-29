/* Unicornext — le champ de points « sonar » (voir DESIGN.md, section 7).
 *
 * Port sans dépendance du composant React SonarGrid : une grille de points décorative qui répond
 * par des anneaux qui s'étendent. Un anneau part de temps en temps de lui-même, et un clic n'importe
 * où en lance un autre. Le canvas est fixe derrière toute l'app. Il se met en veille quand aucun
 * anneau n'est vivant, quand l'onglet est caché, et n'affiche qu'une grille immobile si le système
 * demande moins de mouvement.
 *
 * Ce script est exécuté dans la page de Streamlit (voir ui.sonar_html) : il ne doit être lancé
 * qu'une fois, d'où la garde ci-dessous. La couleur vient du CSS (`color` de #unicornext-sonar).
 */
(function () {
  if (window.__unicornextSonar) return;

  var OPTS = { spacing: 26, dotRadius: 1.3, baseOpacity: 0.2, pingEvery: 3.2, speed: 260, ringWidth: 90, amplitude: 2.2, maxRings: 5 };
  var PING_AREA = [0.15, 0.2, 0.85, 0.8];   // où naissent les anneaux spontanés : [x0, y0, x1, y1] en fractions
  var MAX_DPR = 2;
  var TAU = Math.PI * 2;

  var canvas = document.createElement("canvas");
  canvas.id = "unicornext-sonar";
  canvas.setAttribute("aria-hidden", "true");
  document.body.appendChild(canvas);
  var ctx = canvas.getContext("2d");
  if (!ctx) return;

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var width = 0, height = 0, raf = 0, timer = 0, stroke = "", seeded = false;
  var rings = [];
  var nextPing = performance.now() + OPTS.pingEvery * 1000;

  function readColor() { stroke = getComputedStyle(canvas).color; }

  function addRing(x, y, born) {
    readColor();
    rings.push({ x: x, y: y, born: born });
    while (rings.length > OPTS.maxRings) rings.shift();
  }

  function draw(now) {
    var o = OPTS;
    var lifetime = (Math.hypot(width, height) + o.ringWidth) / o.speed;     // secondes avant qu'un anneau sorte du cadre
    rings = rings.filter(function (r) { return (now - r.born) / 1000 < lifetime; });
    var live = rings.map(function (r) {
      var age = (now - r.born) / 1000;
      var radius = age * o.speed;
      return { x: r.x, y: r.y, radius: radius, reach: radius + o.ringWidth, fade: 1 - age / lifetime };
    });

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = stroke;

    var cols = Math.ceil(width / o.spacing) + 1;
    var rows = Math.ceil(height / o.spacing) + 1;
    var offsetX = (width - (cols - 1) * o.spacing) / 2;
    var offsetY = (height - (rows - 1) * o.spacing) / 2;

    // Passe 1 : tous les points au repos, en un seul tracé et un seul remplissage.
    var hot = [];
    ctx.globalAlpha = o.baseOpacity;
    ctx.beginPath();
    for (var i = 0; i < cols; i++) {
      var cx = offsetX + i * o.spacing;
      for (var j = 0; j < rows; j++) {
        var cy = offsetY + j * o.spacing;
        var energy = 0;
        for (var n = 0; n < live.length; n++) {
          var r = live[n];
          if (Math.abs(cx - r.x) > r.reach || Math.abs(cy - r.y) > r.reach) continue;
          var dist = Math.abs(Math.hypot(cx - r.x, cy - r.y) - r.radius);
          if (dist >= o.ringWidth) continue;
          var t = 1 - dist / o.ringWidth;
          var k = t * t * (3 - 2 * t) * r.fade;                                // lissage, qui s'éteint avec l'âge
          if (k > energy) energy = k;
        }
        if (energy < 0.01) {
          ctx.moveTo(cx + o.dotRadius, cy);
          ctx.arc(cx, cy, o.dotRadius, 0, TAU);
        } else {
          hot.push(cx, cy, energy);
        }
      }
    }
    ctx.fill();

    // Passe 2 : seuls les points sur un front d'onde ont leur propre opacité et leur propre rayon.
    for (var h = 0; h < hot.length; h += 3) {
      var e = hot[h + 2];
      ctx.globalAlpha = o.baseOpacity + (1 - o.baseOpacity) * e;
      ctx.beginPath();
      ctx.arc(hot[h], hot[h + 1], o.dotRadius * (1 + o.amplitude * e), 0, TAU);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  function resize() {
    width = Math.max(1, window.innerWidth);
    height = Math.max(1, window.innerHeight);
    var dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (!seeded) {
      // Un anneau déjà en cours au premier affichage : on voit l'idée tout de suite.
      seeded = true;
      if (!reduce.matches) addRing(width * (PING_AREA[0] + (PING_AREA[2] - PING_AREA[0]) * 0.68),
                                   height * (PING_AREA[1] + (PING_AREA[3] - PING_AREA[1]) * 0.34), performance.now() - 500);
    }
    draw(performance.now());
  }

  function scheduleIdle(delay) {
    window.clearTimeout(timer);
    timer = window.setTimeout(function () { tick(performance.now()); }, Math.max(16, delay));
  }

  function tick(now) {
    raf = 0;
    if (document.hidden) return;
    if (reduce.matches) { rings = []; draw(now); return; }
    if (now >= nextPing) {
      addRing(width * (PING_AREA[0] + Math.random() * (PING_AREA[2] - PING_AREA[0])),
              height * (PING_AREA[1] + Math.random() * (PING_AREA[3] - PING_AREA[1])), now);
      nextPing = now + OPTS.pingEvery * 1000;
    }
    draw(now);
    if (rings.length > 0) raf = requestAnimationFrame(tick);
    else scheduleIdle(nextPing - now);
  }

  function wake() {
    if (!raf) { window.clearTimeout(timer); raf = requestAnimationFrame(tick); }
  }

  function onDown(e) {
    if (reduce.matches || (e.pointerType === "mouse" && e.button !== 0)) return;
    addRing(e.clientX, e.clientY, performance.now());
    wake();
  }
  function onVisibility() { if (!document.hidden) wake(); }

  readColor();
  resize();
  window.addEventListener("resize", resize);
  document.addEventListener("pointerdown", onDown, { passive: true });
  document.addEventListener("visibilitychange", onVisibility);
  reduce.addEventListener("change", wake);
  wake();

  window.__unicornextSonar = {
    destroy: function () {
      window.removeEventListener("resize", resize);
      document.removeEventListener("pointerdown", onDown);
      document.removeEventListener("visibilitychange", onVisibility);
      reduce.removeEventListener("change", wake);
      cancelAnimationFrame(raf);
      window.clearTimeout(timer);
      canvas.remove();
      delete window.__unicornextSonar;
    },
  };
})();
