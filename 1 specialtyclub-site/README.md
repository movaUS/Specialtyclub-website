# Specialty Club — pinned turntable, ORYZO treatment

The 36-frame turntable from V1, re-graded for the warm-dark canvas and set in a
pinned scroll section where the can stays centred while the copy changes around
it. The rotation system itself is unchanged.

```
index.html            the pinned reveal section
can-turntable.js      component, no dependencies, ~5 KB unminified
can-poster.webp/.png  frame 0, the no-JavaScript fallback
seq/1x/can_NN.webp    294 × 692    1.05 MB total  (30 KB/frame)
seq/2x/can_NN.webp    588 × 1384   2.51 MB total  (71 KB/frame)
pipeline/             frame generation, plus the source wrap artwork
```

## Source artwork

The label is the supplied 360° wrap (`pipeline/die_line_SP_black_can.png`),
mapped at printed proportions. Three things had to be handled.

**The wrap and the original hero photo are different cans.** The lockup covers
134° of arc in the artwork but only 111° on the photographed can, and the
proportions disagree by 10.6% — the photo's label area is 1.470 wide-to-tall
against the sleeve's 202/152 = 1.329. The photo was a generic mockup with the
art dropped on at whatever size looked right.

Registration therefore locks to the **circumference**, so the artwork keeps its
printed proportions, and the wordmark is aligned to the height it sat at in the
photo. What gets cropped is the sleeve's blank top and bottom margin, which is
the correct thing to lose. **The can now reads with a noticeably larger
wordmark than the original hero image** — this was accepted deliberately.

**The wrap arrived with fake lighting painted into it.** Background ran 7 to 110
across a single row, near-constant down each column: vertical gradient bands
simulating a cylinder. Left in, you would get lighting twice — painted
highlights rotating with the label while the real highlight stayed put.
`step5_flatten.py` keys the ink against a backdrop estimated from the
artwork-free top and bottom margins and rebuilds it as flat ink on true black.
The Nutrition Facts box needed care: it is a flat black panel sitting *over* the
gradient, which the keying handles by treating its interior as background.

**Resolution is 1446px around, roughly 182dpi.** That is 82% of what the can
needs, so the front is upscaled about 23%. The panel stays legible at 2x — see
`preview.gif` — but higher-resolution or vector artwork would sharpen the
wordmark if it ever becomes available.

## The grading pass

Frames are rendered neutral, then graded for the warm-dark canvas. The
photographic lighting was built for white seamless: two specular bands and a
core sitting at level 6–8, below Walnut Shadow at 9.7. Ungraded, the can reads
as a cold hole. `step7_relight_art.py` applies a warm tint toward the printed
cream `(1.00, 0.945, 0.872)`, a warm rim over the outer 16% of the radius
weighted to the upper right, and a +5 ambient floor. All screen-space, so they
stay locked while the label rotates underneath.

## Section behaviour

- `460vh` wrapper, `100vh` sticky stage. Rotation is scrubbed directly to
  scroll position — no timed autoplay anywhere.
- The can **settles into a pose per section** rather than spinning at a constant
  rate, matching the way the ORYZO coaster changes orientation between
  sections. Four rests across one continuous 360° in a single direction:

  | Section | Panel | Angle | Frame |
  | --- | --- | --- | --- |
  | Formulation | Front lockup | 0° | 0 |
  | Production | Benefits column | −127° | −12.7 |
  | Packaging | Nutrition Facts | −233° | −23.3 |
  | Finished | Front lockup | −360° | −36 |

  The three printed panels sit at 0° and ±127.25° on the wrap, measured from
  the artwork. Frame granularity is 10°, so the two side panels land about 2.8°
  off centre — not perceptible. Rotation runs in one direction throughout.

  Configured through the `stops` option; each entry is a scroll position, a
  frame, and a `hold` half-width for the plateau. Transitions ease in and out.
  Still a pure function of scroll, never a timer. Omit `stops` to get the
  constant-rate spin back.
- Four steps — formulation, production, packaging, finished — crossfade as
  overlays over the same three-column grid, so heading and body stay one block
  in the markup and survive the reduced-motion and mobile reflows.
- The step index sits bottom-left on dashed hairlines. It marks position in the
  sequence, which is structural, not decorative.
- Drag and arrow keys still rotate the can. The copy overlays are
  `pointer-events: none` so they never intercept the grab.

## Loading

First paint waits on nothing but the poster. `preload: 1` fetches only frame 0;
the remaining 35 start when the section comes within 200px of the viewport or
when the browser goes idle, whichever lands first.

They arrive in a spread order — every ninth frame, then every sixth, then the
gaps — so coarse scrubbing works long before the last frame is in. Any frame
not yet present draws the nearest one that is. Four requests run in parallel.

Tier is chosen from pixel density and connection: 2x on high-density displays,
1x when `Save-Data` is set or the connection reports 2G or 3G.

## Token conformance

| Token | Value | Used for |
| --- | --- | --- |
| Walnut Shadow | `#100904` | page canvas, both sections |
| Warm Cream | `#ffedd7` | all text |
| Cork Border | `#40372e` | dashed dividers, step index, spec rows |
| Driftwood | `#6c5f51` | muted labels, right-edge serial |
| Ember | `#dc5000` | the contact link only |
| Bark Brown | `#382416` | selection highlight |

Type is uppercase weight 500 throughout, with weight 400 mixed case reserved
for the 29px body copy. Line-height is 0.9 on display and heading sizes. No
shadows, no solid dividers, no centred body copy, no filled CTA.

**Halyard Display Variable is not loaded.** The stack falls to Inter, the
documented structural substitute. If you have the Typekit kit, add it and the
`--font-display` variable picks it up with no other change.

## Open items

**The lid tab is static.** Accepted for V1. More noticeable on the dark canvas
than on white, because the rim light draws the eye to the lid. Watch it in
testing; the fix is to cut the tab out and rotate it on its own ellipse.

**Copy is placeholder.** Written to the manufacturing story rather than as
consumer advertising, but the specifics — minimums, lead times, assay practice
— are invented. In particular "each batch is assayed before it fills" is a
factual claim about your process; confirm it before publishing.

**This is a hemp product.** The panel declares CBD 40mg and THC 10mg.
Advertising rules for hemp-derived THC beverages vary by state and cover
age-gating, health claims and where ads may run. The combination of "zero
sugar" and "keto friendly" beside a cannabinoid panel is the kind of thing that
attracts attention. Get the site copy through compliance review before launch.

**Halyard Display Variable is not loaded.** The stack falls back to Inter, the
documented substitute. Add the Typekit kit and `--font-display` picks it up.

## Regenerating

```bash
python3 pipeline/step1_analyze.py       # geometry + shading field from the photo
python3 pipeline/step5_flatten.py       # strip painted shading from the wrap
python3 pipeline/step6_render_art.py    # map artwork to the cylinder, 36 frames
python3 pipeline/step7_relight_art.py   # warm grade + rim for the dark canvas
```

To swap in new artwork, replace `pipeline/die_line_SP_black_can.png` and re-run
from step 5. If the lockup moves, update `LOCK_X` / `LOCK_Y` in step 6 — they
are the wordmark's centre in the flat, and everything registers off them.

Step 7's constants are the ones to tune if the canvas colour changes: `WARM`,
`TINT`, `RIM_R` / `RIM_L`, and `LIFT`. Set `TINT` and `LIFT` to 0 to get neutral
frames back for a light-background context.
