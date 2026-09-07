# Handoff

A 36-frame product turntable for the Specialty Club can, scrubbed to scroll
position inside a pinned section. Everything needed is in this folder. Read
`README.md` for how it was built; this file covers integration only.

## Integrate

| File | Where it goes |
| --- | --- |
| `can-turntable.js` | Site JS. No dependencies, no build step required. |
| `index.html` | **Reference implementation, not a page.** Lift the markup, CSS and init call into the site's framework. |
| `seq/1x/`, `seq/2x/` | Static assets, served as-is. |
| `can-poster.webp`, `can-poster.png` | Static assets. The poster is the no-JavaScript fallback. |
| `pipeline/` | Build tooling. Keep in the repo, **do not deploy.** |
| `preview.gif` | Reference only. Not for production. |

## If the can does not appear

The component now leaves the poster image in place when frames fail to load, and
puts `data-failed` on the root element. If you see that attribute, or the poster
itself shows alt text, the assets are not reachable — the code is fine.

Open DevTools, Network tab, reload, and read the URL of the failed request. Then:

- **Path resolves against the route.** `src` returns `seq/1x/can_00.webp`, which
  is relative. On a framework route like `/process` that becomes
  `/process/seq/…`. Fix: put the folders under `public/` and return a leading
  slash — `/seq/1x/can_00.webp`.
- **Assets never deployed.** Check `seq/` is committed and present in the build
  output, not filtered by `.gitignore`, LFS, or an asset allowlist. It is 36
  files per tier, 72 total.
- **Optimizer rejected them.** Some pipelines refuse or rewrite WebP with alpha.
  Mark `seq/` pass-through.

Fastest single check: open `https://yourdomain/seq/1x/can_00.webp` directly. If
that 404s it is deployment or path, never the component.

## Three things not to break

**1. Don't re-optimize `seq/`.** If the asset pipeline runs images through a
compressor, it may strip alpha or recompress the WebPs. The can would get a hard
edge or a grey box behind it. Mark the folder pass-through.

**2. Keep the three data attributes.** The component finds its elements by
these, not by class name, so the classes can be renamed freely:

- `data-turntable-stage` — the sticky element. Scroll progress is measured as
  how far the outer wrapper travels past it.
- `data-turntable-mount` — the sized box the canvas fills. Give it the can's
  294 × 692 aspect ratio.
- `data-turntable-poster` — the still image. Must exist in the markup before JS
  runs, or the no-JS case has no hero.

**3. Keep the wrapper taller than the stage.** The wrapper is `460vh`, the
sticky stage is `100vh`. Scroll progress is
`(wrapperHeight − stageHeight)`; if a framework collapses the wrapper to the
stage height, that span is zero and the can stops rotating. This is the most
likely way integration breaks.

## Init

```js
CanTurntable.mount(document.getElementById('reveal'), {
  frames: 36,
  spins: 1,
  preload: 1,
  src: (i, tier) => `seq/${tier}/can_${String(i).padStart(2, '0')}.webp`,
  onScrub: (p) => { /* drives the four copy steps */ }
});
```

Options, callbacks and the returned handle are documented in `README.md`.
Nothing needs configuring for the default behaviour.

## What the frames already account for

The frames are graded for the `#100904` canvas — warm tint, a warm rim at the
silhouette, and an ambient floor. This was necessary, not cosmetic: the source
was lit for white seamless and its dark core sits at level 6–8, below the
Walnut Shadow background at 9.7. Ungraded, the can reads as a cold hole.

So: **don't apply CSS filters, blend modes or opacity to the canvas**, and don't
place the can on a different background colour without re-running
`pipeline/step4_relight.py` with the new value. The grading is baked to one
specific canvas colour.

## Behaviour to preserve in QA

- Scroll-scrubbed only. No timed autoplay.
- The can holds a pose through each section and turns between them (`stops` in
  the init call). It should be visibly still while copy is being read.
- Drag and left/right arrow keys rotate the can. The copy overlays are
  `pointer-events: none` so they don't intercept the grab.
- `prefers-reduced-motion` unpins the section and stacks the four steps. Drag
  and keyboard still work, because those answer a user action.
- With JS disabled the poster stays and the page keeps a correct hero.
- `Save-Data`, 2G or 3G force the 1x tier regardless of screen density.

## Outstanding before launch

1. **Artwork is now the real 360° wrap**, registered to printed proportions.
   The wordmark reads larger than in the original hero mockup — that change was
   accepted deliberately. Source art is 182dpi; vector or 300dpi would sharpen
   the front if it becomes available.
2. **Lid tab is static.** Accepted for V1. It is more noticeable on the dark
   canvas than on white, because the rim light draws the eye to the lid. Watch
   it in testing.
3. **Spec copy is placeholder.** Formats, minimums and lead times are invented.
   Replace with real capability before this is customer-facing.
4. **Halyard Display Variable is not loaded.** The stack falls back to Inter,
   the documented substitute. Add the Typekit kit and `--font-display` picks it
   up with no other change.

## Questions

Anything about the geometry, the grading, or regenerating the frames for a
different can or a different background colour — ask before changing the
pipeline constants. They were fitted to this specific photograph.
