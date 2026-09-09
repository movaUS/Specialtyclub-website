# Specialty Club — can turntable handoff

## What exists

A 36-frame product turntable of the 12 oz can, scrubbed to scroll position
inside a pinned section, styled to the ORYZO reference. Built from a single flat
product photo plus the supplied label artwork — no 3D engine at runtime.

- `can-turntable.js` — the component. No dependencies, ~5 KB unminified.
- 72 WebP frames — 1.05 MB at 1x, 2.51 MB at 2x. Tier chosen automatically from
  pixel density and connection.
- Loading is lazy: first paint waits only on the poster image. Frames start when
  the section nears the viewport or the browser goes idle, arriving in a spread
  order so coarse scrubbing works before the last frame lands.

The can holds a pose per section and turns between them, rather than spinning at
a constant rate. The three printed panels sit at 0° and ±127.25° on the wrap:

| Section | Panel shown | Angle |
| --- | --- | --- |
| Formulation | Front lockup | 0° |
| Production | Benefits column | −127° |
| Packaging | Nutrition Facts | −233° |
| Finished | Front lockup | −360° |

Drag and arrow keys also rotate it. Reduced-motion unpins the section and stacks
the steps. With JavaScript off, the poster image stays.

---

## Blocker: the frames 404

Confirmed live — `specialtyclub.com/seq/1x/can_00.webp` returns Vercel's
NOT_FOUND. The files were never included in the deployment. The code is fine.

**Fix, three steps:**

1. Copy the `public` folder from `specialtyclub-DEPLOY-ASSETS.zip` into the repo
   root. It must end up as `public/seq/1x/…`, `public/seq/2x/…`, plus the two
   poster files.
2. Make the paths absolute — leading slash:
   ```js
   src: (i, tier) => `/seq/${tier}/can_${String(i).padStart(2, '0')}.webp`
   ```
   and `<img src="/can-poster.png">`. Without the slash the path resolves
   against the current route, so `/process` becomes `/process/seq/…`.
3. Deploy, then load `specialtyclub.com/seq/1x/can_00.webp` directly. It must
   show a black can.

**Two things that will silently break it again:**

- Do not run `public/seq` through an image optimiser. Some pipelines strip alpha
  from WebP, which puts a grey box behind the can. Mark it pass-through.
- Do not route the poster through `next/image`. The script needs the plain
  `<img>` element it replaces.

Other broken images on the site — including the "DATE CODING · WINSTON-SALEM"
photo, which is not from this package — suggest the same asset-pipeline problem
site-wide, not something specific to the turntable.

---

## Logo

**The supplied logo is black artwork on transparency, so it is effectively
invisible on the `#100904` background.** Cream versions are supplied in
`specialtyclub-logo.zip`.

**`specialty-club-mark-web.svg` does not contain the "SPECIALTY CLUB"
wordmark** — only the arcs, the SC monogram and the leaf. Just the 1600px PNG
has the full lockup. Worth requesting a corrected SVG from whoever produced it.

On making it bigger: **use the SVG mark, not the full lockup, in the header.** At
44–48px the curved wordmark renders about 5px tall and turns into a grey smudge,
so the logo would look worse the larger it gets. The mark alone stays crisp.

```css
.site-header__logo { height: 44px; width: auto; display: block; }
@media (max-width: 700px) { .site-header__logo { height: 34px; } }
```

Check the nav row padding afterwards if it was built around a 32px logo.

The leaf green `#1A852E` is a cool saturated green in a warm cream-and-ember
palette and reads as foreign on the dark canvas. All-cream and cream-with-ember-
leaf versions are both supplied — a brand call, not a technical one. The green
still works on packaging and light-background print.

---

## Decisions already made

- **The can no longer matches the original hero mockup.** The label artwork is
  20% larger, angularly, than what the mockup applied — the two were never the
  same can. Registration now locks to the printed circumference, so the wordmark
  reads noticeably larger. This was accepted deliberately.
- **Source artwork is 182dpi** (1446px around), about 82% of what the can needs,
  so the front is upscaled ~23%. The Nutrition panel stays legible at 2x. Vector
  or 300dpi art would sharpen it if it ever becomes available.

---

## Open items

1. **Copy is placeholder.** Formats, minimums, lead times and the line "each
   batch is assayed before it fills" are invented. Replace with real capability.
2. **Compliance review needed.** The product declares CBD 40mg / THC 10mg, and
   the Nutrition panel is now a featured pose rather than hidden on the back.
   State advertising rules for hemp-derived THC beverages cover age-gating,
   health claims and ad placement. "Zero sugar" and "keto friendly" beside a
   cannabinoid panel is the combination that draws scrutiny.
3. **Section count.** Site alt text mentions five stages; the sequence is built
   around four poses, and there are only three printed panels to rest on. A
   fifth stop would land on blank sleeve.
4. **Halyard Display Variable is not loaded** — falls back to Inter. Add the
   Typekit kit and `--font-display` picks it up with no other change.
5. **The lid tab is static** and does not rotate. Accepted for V1; more
   noticeable on the dark canvas because the rim light draws the eye to the lid.

---

## Files

| Archive | Contents |
| --- | --- |
| `specialtyclub-DEPLOY-ASSETS.zip` | **Start here.** Only what ships: `public/` folder, the component, and setup instructions. |
| `specialtyclub-turntable.zip` | Full package — demo page, documentation, and the frame-generation pipeline. |
| `specialtyclub-logo.zip` | Cream logo variants for the dark background, with usage notes. |
