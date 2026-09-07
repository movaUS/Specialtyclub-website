/*
 * can-turntable.js — scroll- and drag-scrubbed image sequence on <canvas>.
 * No dependencies. ~4 KB unminified.
 *
 *   CanTurntable.mount(document.querySelector('.turntable'), {
 *     frames: 36,
 *     src: (i, tier) => `seq/${tier}/can_${String(i).padStart(2, '0')}.webp`
 *   });
 *
 * Degradation, in order: no JS -> the <img> already in the markup stays put.
 * No canvas -> same. Reduced motion -> scroll scrubbing is off, drag and
 * arrow keys still work. Slow link or Save-Data -> half-resolution tier.
 */
(function (global) {
  'use strict';

  var raf = global.requestAnimationFrame || function (f) { return setTimeout(f, 16); };

  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  function pickTier(opts) {
    if (opts.tier) return opts.tier;
    var c = navigator.connection || {};
    if (c.saveData) return '1x';
    if (/^(slow-)?2g$/.test(c.effectiveType || '')) return '1x';
    if (c.effectiveType === '3g') return '1x';
    return (global.devicePixelRatio || 1) >= 1.5 ? '2x' : '1x';
  }

  function mount(root, opts) {
    opts = opts || {};
    var N = opts.frames || 36;
    var spins = opts.spins == null ? 1 : opts.spins;
    var dir = opts.direction == null ? 1 : opts.direction;
    var stops = opts.stops && opts.stops.length > 1 ? opts.stops : null;
    var stage = root.querySelector('[data-turntable-stage]') || root;   // sticky, drives scroll math
    var mount = root.querySelector('[data-turntable-mount]') || stage;   // sized box the canvas fills
    var poster = root.querySelector('[data-turntable-poster]');

    var canvas = document.createElement('canvas');
    var ctx = canvas.getContext && canvas.getContext('2d');
    if (!ctx) return null;                       // leaves the poster <img> alone

    canvas.className = 'turntable__canvas';
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('tabindex', '0');
    canvas.setAttribute('aria-label',
      opts.label || 'Product can. Drag left or right, or use the arrow keys, to rotate.');

    var tier = pickTier(opts);
    var shots = new Array(N);
    var got = 0, ready = false;
    var offset = 0, scrollFrame = 0, drawn = -1, visible = true;
    var reduce = global.matchMedia &&
      global.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------------------------------------------------------- loading --
       First paint must not wait on the sequence. Only `preload` frames are
       fetched eagerly (default: just frame 0, which matches the poster). The
       rest start when the section nears the viewport or the browser goes idle,
       whichever happens first, and arrive in a spread-out order so scrubbing
       coarsely works long before the last frame lands. */
    var eager = opts.preload == null ? 1 : opts.preload;
    var failed = 0;
    var concurrency = opts.concurrency || 4;
    var started = false;

    function load(i) {
      if (shots[i]) return Promise.resolve();
      return new Promise(function (res) {
        var img = new Image();
        img.decoding = 'async';
        img.onload = function () {
          if (global.createImageBitmap) {
            createImageBitmap(img).then(function (b) { shots[i] = b; res(); },
                                        function () { shots[i] = img; res(); });
          } else { shots[i] = img; res(); }
        };
        img.onerror = function () { failed++; res(); };
        img.src = opts.src(i, tier);
      }).then(function () {
        got++;
        if (opts.onProgress) opts.onProgress(got / N);
        schedule();
      });
    }

    // Spread order: coarse ring first, then progressively fill the gaps.
    function spreadOrder() {
      var seen = {}, order = [];
      for (var step = Math.max(1, N >> 2); step >= 1; step >>= 1) {
        for (var i = 0; i < N; i += step) {
          if (!seen[i]) { seen[i] = 1; order.push(i); }
        }
        if (step === 1) break;
      }
      for (var j = 0; j < N; j++) if (!seen[j]) order.push(j);
      return order;
    }

    function pool(list) {
      var next = 0;
      function worker() {
        if (next >= list.length) return Promise.resolve();
        return load(list[next++]).then(worker);
      }
      var runners = [];
      for (var w = 0; w < Math.min(concurrency, list.length); w++) runners.push(worker());
      return Promise.all(runners);
    }

    function begin() {
      if (started) return;
      started = true;
      var order = spreadOrder().filter(function (i) { return !shots[i]; });
      pool(order).then(function () {
        if (!anyLoaded()) {
          root.setAttribute('data-failed', '');
          if (opts.onError) opts.onError(failed, N);
          return;
        }
        if (!ready) {                       // frame 0 failed but others arrived
          ready = true;
          root.setAttribute('data-ready', '');
          if (poster) poster.setAttribute('aria-hidden', 'true');
        }
        root.setAttribute('data-complete', '');
        if (opts.onReady) opts.onReady();
      });
    }

    var first = [];
    for (var e = 0; e < eager; e++) first.push(Math.round(e * N / eager) % N);
    function anyLoaded() {
      for (var q = 0; q < N; q++) if (shots[q]) return true;
      return false;
    }

    pool(first).then(function () {
      if (!anyLoaded()) {
        // Every requested frame 404'd or failed to decode. Leave the poster in
        // place rather than swapping in an empty canvas.
        root.setAttribute('data-failed', '');
        if (opts.onError) opts.onError(failed, N);
        return;
      }
      ready = true;
      root.setAttribute('data-ready', '');
      if (poster) poster.setAttribute('aria-hidden', 'true');
      schedule();
    });

    if (global.requestIdleCallback) requestIdleCallback(begin, { timeout: 2500 });
    else setTimeout(begin, 1200);

    function nearest(i) {
      if (shots[i]) return shots[i];
      for (var d = 1; d <= N >> 1; d++) {
        if (shots[(i - d + N) % N]) return shots[(i - d + N) % N];
        if (shots[(i + d) % N]) return shots[(i + d) % N];
      }
      return null;
    }

    /* ----------------------------------------------------------- sizing -- */
    var cssW = 0, cssH = 0;
    function resize() {
      var r = mount.getBoundingClientRect();
      var dpr = clamp(global.devicePixelRatio || 1, 1, 2);
      if (!r.width || !r.height) return;
      cssW = r.width; cssH = r.height;
      canvas.width = Math.round(r.width * dpr);
      canvas.height = Math.round(r.height * dpr);
      canvas.style.width = r.width + 'px';
      canvas.style.height = r.height + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      drawn = -1;
      schedule();
    }

    /* ------------------------------------------------------------- draw -- */
    var queued = false;
    function schedule() {
      if (queued) return;
      queued = true;
      raf(function () { queued = false; draw(); });
    }

    function currentFrame() {
      var f = Math.round(scrollFrame + offset);
      return ((f % N) + N) % N;
    }

    /* Optional pose stops. Instead of a constant spin, the can settles at a
       defined angle for each section and turns during the transitions — the
       object holds still while its copy is being read. Still a pure function
       of scroll position, never a timer.

         stops: [{ at: 0.125, frame: 0, hold: 0.06 }, …]
           at    scroll progress, 0-1, where this pose is centred
           frame frame index; may exceed `frames` to keep turning one way
           hold  half-width of the plateau, in scroll progress */
    function easeInOut(t) {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    function frameFromStops(p) {
      var last = stops.length - 1;
      if (p <= stops[0].at) return stops[0].frame;
      for (var i = 0; i < last; i++) {
        var a = stops[i], b = stops[i + 1];
        var aEnd = a.at + (a.hold || 0);
        var bStart = b.at - (b.hold || 0);
        if (p <= aEnd) return a.frame;
        if (p < bStart) {
          var t = (p - aEnd) / Math.max(bStart - aEnd, 1e-6);
          return a.frame + (b.frame - a.frame) * easeInOut(clamp(t, 0, 1));
        }
      }
      return stops[last].frame;
    }

    function draw() {
      if (!ready || !visible || !cssW) return;
      var f = currentFrame();
      if (f === drawn) return;
      var img = nearest(f);
      if (!img) return;
      drawn = f;

      var iw = img.width, ih = img.height;
      var s = Math.min(cssW / iw, cssH / ih);
      var w = iw * s, h = ih * s;
      ctx.clearRect(0, 0, cssW, cssH);
      ctx.drawImage(img, (cssW - w) / 2, (cssH - h) / 2, w, h);
      if (opts.onFrame) opts.onFrame(f, N);
    }

    /* ----------------------------------------------------------- scroll --
       The sequence is driven by how far the tall wrapper has travelled past
       the sticky stage, which is what makes it feel welded to the page. */
    function onScroll() {
      if (reduce) return;
      var r = root.getBoundingClientRect();
      var span = root.offsetHeight - stage.offsetHeight;
      if (span <= 0) return;
      var p = clamp(-r.top / span, 0, 1);
      scrollFrame = stops ? dir * frameFromStops(p) : dir * p * N * spins;
      if (opts.onScrub) opts.onScrub(p);
      schedule();
    }

    /* ------------------------------------------------------- drag + keys -- */
    var dragging = false, lastX = 0, moved = 0;
    var perFrame = 14;                       // px of travel per frame

    canvas.addEventListener('pointerdown', function (e) {
      dragging = true; moved = 0; lastX = e.clientX;
      try { canvas.setPointerCapture(e.pointerId); } catch (err) {}
      root.setAttribute('data-dragging', '');
    });
    canvas.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var dx = e.clientX - lastX;
      moved += Math.abs(dx);
      lastX = e.clientX;
      offset += dir * dx / perFrame;
      if (moved > 6) e.preventDefault();
      schedule();
    });
    function endDrag(e) {
      if (!dragging) return;
      dragging = false;
      try { canvas.releasePointerCapture(e.pointerId); } catch (err) {}
      root.removeAttribute('data-dragging');
    }
    canvas.addEventListener('pointerup', endDrag);
    canvas.addEventListener('pointercancel', endDrag);
    canvas.style.touchAction = 'pan-y';

    canvas.addEventListener('keydown', function (e) {
      var k = e.key;
      if (k === 'ArrowLeft' || k === 'ArrowRight') {
        offset += (k === 'ArrowLeft' ? -1 : 1);
        schedule();
        e.preventDefault();
      }
    });

    /* ---------------------------------------------------------- observers -- */
    if (global.IntersectionObserver) {
      new IntersectionObserver(function (es) {
        visible = es[0].isIntersecting;
        if (visible) { begin(); schedule(); }
      }, { rootMargin: '200px' }).observe(root);
    }
    if (global.ResizeObserver) new ResizeObserver(resize).observe(mount);
    else global.addEventListener('resize', resize);

    global.addEventListener('scroll', onScroll, { passive: true });

    mount.appendChild(canvas);
    resize();
    onScroll();

    return {
      canvas: canvas,
      rotateTo: function (f) { offset = f - scrollFrame; schedule(); },
      destroy: function () {
        global.removeEventListener('scroll', onScroll);
        canvas.remove();
      }
    };
  }

  global.CanTurntable = { mount: mount };
})(window);
