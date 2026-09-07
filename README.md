# Specialty Club — v2

Static site. No build step, no framework, no third-party runtime dependencies.
Drop the folder in as the Vercel Root Directory exactly as before.

## Deploy

Everything at the repo root is served as-is. `.vercelignore` keeps `pipeline/`
and the Python out of the deployment — it is build tooling, not site code.

The contact form still posts to Formspree `mdeokrgy` and still redirects to
`thanks.html`. Untouched.

## What changed

| | v1 | v2 |
| --- | --- | --- |
| Canvas | `#100904` walnut | `#0D0F11` steel |
| Text | `#ffedd7` cream | `#F2EDE4` warm off-white, 16.5:1 |
| Accent | `#dc5000` ember | `#4FA46E` leaf, 6.3:1 — passes AA for links |
| Type | Inter only | Space Grotesk / Inter / IBM Plex Mono, self-hosted |
| Can | 240px static PNG | 36-frame scroll-scrubbed turntable, five poses |
| Product proof | 8 low-res cards | 5 high-res cans, scroll-driven gallery |
| Line footage | none | two graded 9:16 clips, deferred |
| Capability copy | invented placeholders | real numbers throughout |

## The can

`seq/1x` and `seq/2x` are 36 frames rendered from `HERO_CAN_V2_.png` and graded
for the steel canvas. 2x (595 × 1442) is native resolution — the source render
supports no more, so do not upscale a 3x tier; it would add weight and no detail.

Rotation is one continuous 360° with five rests, scrubbed to scroll position.
Never a timer. Drag and arrow keys still rotate it.

| Stage | Panel | Frame |
| --- | --- | --- |
| Formulation | Front lockup | 0 |
| Co-packing | Three-quarter | −6.4 |
| Canning | Side panel | −12.7 |
| Packaging | Reverse panel | −23.3 |
| Design | Front lockup | −36 |

The grade is a split-tone: printed cream ink and metal stay warm, the black body
settles neutral-cool so it doesn't read brown against the steel canvas. The
ambient floor is +11 because the new canvas (level 15.0) is lighter than the old
one (9.7) — without it the can punches a hole in the page.

## Regenerating frames

```bash
cd pipeline
python3 step1_analyze.py        # geometry + shading, from HERO_CAN.png
python3 step5_flatten.py        # strip painted shading off the wrap
python3 step6_render_art.py     # 36 neutral frames
python3 step7_relight_steel.py  # split-tone grade for #0D0F11
```

Geometry constants are recalibrated for the V2 hero (`CX=512, R=289`). If the
canvas colour ever changes, `step7`'s `BG`, `SPLIT`, `LIFT` and `RIM_*` are the
knobs. New label artwork: replace `die_line_SP_black_can.png` and re-run from
step 5.

## Performance

First paint fetches ~195 KB: HTML, CSS, three woff2, the hero can and the
component. The hero can doubles as the turntable poster, so it is cached before
the sequence starts and is the LCP element (preloaded, `fetchpriority=high`).

The 36 frames start only when the section is within 200px or the browser goes
idle, and arrive in a spread order so coarse scrubbing works early. Both videos
carry `preload="none"` and get their `src` assigned by IntersectionObserver, so
they cannot delay first render. Tier is chosen from pixel density and
connection; `Save-Data` and 2G/3G get 1x.

## Accessibility

Reduced motion flattens the pinned section and the gallery into static stacked
layouts and stops scroll-scrubbing; drag and keyboard still work. No zoom lock.
A `<noscript>` block reveals everything if JS fails, so no content is trapped
behind an observer. Focus rings are visible and there is a skip link.

## Facts published

500,000 cans/week · 12 oz sleek, 12 oz standard, 19.2 oz · 10,000 per SKU ·
6–8 weeks concept to finished goods · nitrogen dosing on all lines ·
GMP-certified, NCDA&CS permitted, FDA registered · assayed each batch.

Every invented placeholder from the prototype is gone. If any line above is
wrong, it is wrong on a public page — check it.

## Open items

- **Brand green is provisional.** `#4FA46E` was chosen to clear 4.5:1 on the
  canvas. Send `LOGO_SC.pdf` and it gets retuned to the actual leaf; only the
  `--accent` token changes.
- **Logo is raster.** 150 × 162 PNG, used at 40px so it holds, but an SVG would
  be sharper in the footer and on retina.
- **Die-line is 1446px around (~182dpi)**, about 82% of what the can needs, so
  the front panel is upscaled ~23%. Vector artwork would sharpen the wordmark.
- **Lab photography is still AI-generated** and used only as heavily darkened
  atmosphere behind type in scene 02. Swap in real R&D photos when they arrive.
- **Line footage is handheld and vertical.** Held to 9:16 as specified. A locked
  landscape shot would open up a full-bleed desktop band that portrait cannot fill.
- **THC/CBD panel** is visible during rotation, as agreed. Revisit with
  compliance before any paid promotion.
