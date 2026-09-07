"""Step 4: grade the sequence for the warm-dark (ORYZO) canvas.

The source was lit for white seamless: neutral greys, two specular bands, and
a core that sits *below* Walnut Shadow in level. Three corrections, all in
screen space so they stay locked while the label rotates:
  1. warm tint toward the can's own cream (251,237,220)
  2. a warm rim at the silhouette, weighted to the upper right
  3. a small ambient lift so the dark core doesn't punch a hole in the void
"""
import numpy as np, os
from PIL import Image
from scipy.ndimage import uniform_filter1d

BG = np.array([16, 9, 4], float)          # #100904
WARM = np.array([1.00, 0.945, 0.872])     # matches the cream ink's own ratio
TINT = 0.85                               # how far to push toward warm
RIM_R, RIM_L = 46.0, 26.0                 # rim strength, right lit harder
RIM_W = 0.16                              # rim falloff width, fraction of radius
LIFT = 5.0                                # ambient floor above the void

src = np.array(Image.open("frames_art/raw_00.png").convert("RGBA"))
H, W, _ = src.shape

# silhouette centre + radius per row (static across the sequence)
al0 = src[..., 3] / 255.0
cx = np.zeros(H); rr = np.zeros(H); ok = np.zeros(H, bool)
for y in range(H):
    xs = np.where(al0[y] > 0.5)[0]
    if len(xs) > 8:
        cx[y] = (xs.min() + xs.max()) / 2.0
        rr[y] = (xs.max() - xs.min()) / 2.0
        ok[y] = True
idx = np.where(ok)[0]
cx = uniform_filter1d(np.interp(np.arange(H), idx, cx[idx]), 9)
rr = uniform_filter1d(np.interp(np.arange(H), idx, rr[idx]), 9)

xg = np.arange(W)[None, :].astype(float)
s = (xg - cx[:, None]) / np.maximum(rr[:, None], 1.0)
s = np.clip(s, -1, 1)

# rim: rises over the outer RIM_W of the radius on each side
right = np.clip((s - (1 - RIM_W)) / RIM_W, 0, 1) ** 1.5
left = np.clip((-s - (1 - RIM_W)) / RIM_W, 0, 1) ** 1.7

# light sits high and to the right, so the rim fades toward the base
top, bot = idx.min(), idx.max()
vfade = 1.0 - 0.45 * np.clip((np.arange(H) - top) / (bot - top), 0, 1)
rim = (right * RIM_R + left * RIM_L) * vfade[:, None]

os.makedirs("frames_artlit", exist_ok=True)
for f in range(36):
    a = np.array(Image.open("frames_art/raw_%02d.png" % f).convert("RGBA")).astype(float)
    rgb, alpha = a[..., :3], a[..., 3:4] / 255.0

    lum = rgb.mean(2, keepdims=True)
    rgb = rgb * (1 - TINT) + lum * WARM * TINT          # warm grade

    inside = (alpha[..., 0] > 0.02)
    rgb[inside] += LIFT * WARM                          # ambient floor

    # screen-blend the rim so the metal and specular bands don't clip
    add = rim[..., None] * WARM
    rgb = rgb + add * (1.0 - np.clip(rgb / 255.0, 0, 1))
    rgb = np.clip(rgb, 0, 255)

    out = np.dstack([rgb, alpha * 255]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save("frames_artlit/lit_%02d.png" % f)

print("graded 36 frames")

# proof sheet on the real canvas colour
sheet = Image.new("RGB", (5 * 190, 470), tuple(BG.astype(int)))
for i, f in enumerate([0, 5, 10, 15, 20]):
    im = Image.open("frames_artlit/lit_%02d.png" % f).convert("RGBA")
    bg = Image.new("RGBA", im.size, tuple(BG.astype(int)) + (255,))
    bg.alpha_composite(im)
    bg = bg.convert("RGB"); bg.thumbnail((175, 450))
    sheet.paste(bg, (i * 190 + 10, 10))
sheet.save("tn_lit.png")
