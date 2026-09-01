/* ============================================================
   SPECIALTY CLUB — CINEMATIC SCROLL STORY
   01 Navigation treatment
   03 Scroll story engine (scroll-progress driven; scrubs both ways)
   04 Can visual (one continuous object; transform-only motion)
   10 Reduced motion guard
   ------------------------------------------------------------
   SWAP POINT: replace specialty-club-sleek-can.png with any
   transparent PNG/WebP. For a future GLB: replace the contents
   of #canStage with a <canvas>, feed the same `current` progress
   value into a Three.js scene — keyframes below become camera
   moves. Nothing else changes.
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 01 NAVIGATION: transparent -> blurred after scroll */
  var nav = document.querySelector('nav');
  function navState() {
    if (!nav) return;
    if (window.scrollY > 40) nav.classList.add('nav-scrolled');
    else nav.classList.remove('nav-scrolled');
  }
  window.addEventListener('scroll', navState, { passive: true });
  navState();

  /* ---------- 10 REDUCED MOTION: static presentation, bail out */
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.documentElement.classList.add('rm');
    return;
  }

  var story = document.querySelector('.story');
  var canStage = document.getElementById('canStage');
  var can = document.getElementById('canBox');
  if (!story || !can) return;
  var scenes = Array.prototype.slice.call(story.querySelectorAll('.scene'));

  /* ---------- helpers */
  function clamp(v, a, b) { return Math.min(b, Math.max(a, v)); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function ease(t) { return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; }
  function seg(p, a, b) { return ease(clamp((p - a) / (b - a), 0, 1)); }

  /* ---------- 04 CAN KEYFRAMES (p, x vw, y vh, scale, rotate deg)
     0.00-0.20 hero: centered-right, calm
     0.20-0.45 formulation: drifts right, grows, +rotation
     0.45-0.70 production: crosses left for a cinematic close-up crop
     0.70-0.90 pulls back toward center-right
     0.90-1.00 settles small and hands off to page content        */
  var K = [
    { p: 0.00, x: 22, y: 0, s: 1.00, r: 0 },
    { p: 0.20, x: 22, y: 0, s: 1.03, r: 2 },
    { p: 0.45, x: 27, y: 2, s: 1.18, r: 8 },
    { p: 0.70, x: -12, y: 3, s: 1.48, r: -6 },
    { p: 0.90, x: 11, y: 1, s: 1.10, r: 2 },
    { p: 1.00, x: 0, y: 7, s: 0.60, r: 0 }
  ];
  function canState(p) {
    var i = 0;
    while (i < K.length - 2 && p > K[i + 1].p) i++;
    var a = K[i], b = K[i + 1];
    var t = ease(clamp((p - a.p) / (b.p - a.p), 0, 1));
    return { x: lerp(a.x, b.x, t), y: lerp(a.y, b.y, t), s: lerp(a.s, b.s, t), r: lerp(a.r, b.r, t) };
  }

  /* ---------- 03 SCENE WINDOWS [start, end] of scroll progress */
  var W = [[0.00, 0.185], [0.205, 0.45], [0.47, 0.71], [0.735, 0.965]];
  var FEATHER = 0.055;
  function sceneV(p, a, b) {
    var lead = a <= 0 ? 1 : clamp((p - a) / FEATHER, 0, 1);
    var tail = clamp((b - p) / FEATHER, 0, 1);
    return Math.min(lead, tail);
  }

  /* ---------- responsiveness: damp motion on smaller screens */
  var xf = 1, sf = 1;
  function onResize() {
    var w = window.innerWidth;
    xf = w < 760 ? 0.32 : (w < 1024 ? 0.68 : 1);   /* horizontal travel */
    sf = w < 760 ? 0.72 : 1;                        /* scale amplitude  */
  }
  window.addEventListener('resize', onResize, { passive: true });
  onResize();

  /* ---------- progress: 0..1 across the pinned story */
  function progress() {
    var r = story.getBoundingClientRect();
    var total = story.offsetHeight - window.innerHeight;
    return total > 0 ? clamp(-r.top / total, 0, 1) : 0;
  }
  var current = progress();

  /* ---------- render loop: smooth-follow, transform/opacity only */
  var hidden = false;
  document.addEventListener('visibilitychange', function () { hidden = document.hidden; });
  function frame(ts) {
    if (!hidden) {
      current = lerp(current, progress(), 0.16);
      var p = current;
      var st = canState(p);
      /* idle float: subtle, settles as the story ends */
      var settle = 1 - seg(p, 0.85, 1);
      var idleY = Math.sin(ts / 1100) * 7 * settle;
      var idleR = Math.sin(ts / 1700) * 0.6 * settle;
      can.style.transform =
        'translate(-50%, -50%)' +
        ' translate3d(' + (st.x * xf) + 'vw, calc(' + st.y + 'vh + ' + idleY.toFixed(2) + 'px), 0)' +
        ' rotate(' + (st.r * xf + idleR).toFixed(2) + 'deg)' +
        ' scale(' + (1 + (st.s - 1) * sf).toFixed(3) + ')';
      canStage.style.opacity = (1 - seg(p, 0.94, 1)).toFixed(3);

      for (var i = 0; i < scenes.length; i++) {
        var v = sceneV(p, W[i][0], W[i][1]);
        scenes[i].style.opacity = v.toFixed(3);
        scenes[i].style.transform = 'translate3d(0,' + ((1 - v) * 28).toFixed(1) + 'px,0)';
        scenes[i].style.pointerEvents = v > 0.5 ? 'auto' : 'none';
      }
    }
    window.requestAnimationFrame(frame);
  }
  window.requestAnimationFrame(frame);
})();
