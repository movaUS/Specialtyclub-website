"""Step 5: strip the painted-on cylinder shading from the supplied wrap.

The flat is opaque vector artwork sitting on a fake gradient backdrop. So the
backdrop is replaced outright rather than divided out: estimate it from the
artwork-free top and bottom margins, key the ink against it, and rebuild as
flat ink on the label's true black.
"""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d

FLAT = "flat_src.png"
REF = 26.48                      # label black in albedo terms, from step 1
INKREF = 245.0

a = np.array(Image.open(FLAT).convert("RGB")).astype(np.float64)
H, W, _ = a.shape
lum = a.mean(2)

# backdrop from the clear margins, interpolated down the label
top = np.median(a[10:75], axis=0)
bot = np.median(a[1010:1080], axis=0)
top = np.stack([gaussian_filter1d(top[:, c], 3) for c in range(3)], 1)
bot = np.stack([gaussian_filter1d(bot[:, c], 3) for c in range(3)], 1)
t = (np.arange(H) / (H - 1))[:, None, None]
S = top[None] * (1 - t) + bot[None] * t
Sl = S.mean(2)
print("backdrop range: %.1f .. %.1f" % (Sl.min(), Sl.max()))

# key the ink: opaque above a threshold, soft only at the antialiased edge
r = (lum - Sl) / np.maximum(INKREF - Sl, 1.0)
alpha = np.clip((r - 0.10) / 0.30, 0, 1)

# unmix so edge pixels don't carry the backdrop's brightness into the ink
af = np.maximum(alpha, 1e-3)[..., None]
ink = np.clip((a - S * (1 - af)) / af, 0, 255)

flat = REF * (1 - alpha[..., None]) + ink * alpha[..., None]
flat = np.clip(flat, 0, 255)

print("ink coverage %.4f   mean ink colour %s" % (
    (alpha > 0.5).mean(), ink[alpha > 0.8].mean(0).round(0)))

np.save("flat_art.npy", flat.astype(np.float32))
Image.fromarray(flat.astype(np.uint8)).save("dbg_flat.png")

# side-by-side proof
cmp = Image.new("RGB", (W, H // 2 + 8), (0, 0, 0))
cmp.paste(Image.fromarray(a.astype(np.uint8)).crop((0, 0, W, H // 4)), (0, 0))
cmp.paste(Image.fromarray(flat.astype(np.uint8)).crop((0, 0, W, H // 4)), (0, H // 4 + 8))
cmp.thumbnail((900, 900))
cmp.save("tn_flatten.png")
print("saved dbg_flat.png")
