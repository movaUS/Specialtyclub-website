"""Step 1: cylinder geometry, clean shading field, ink-coverage decomposition.

The source is a mockup render: cream ink is uniformly lit while the black body
carries the cylinder gradient plus narrow specular ridges. We factor the label
into   pixel = k*INK + (1-k)*shade(x,y)   and keep k as the rotatable artwork.
Only the band that actually holds artwork is rebuilt; lid, shoulder and base
stay untouched.
"""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, binary_dilation, percentile_filter, zoom

CX, R = 543.0, 283.0
EA, EB = 5.588, 0.009150        # ellipse amplitude vs label height (perspective)
YS_TOP, YS_BOT = 215.0, 1318.0  # rebuilt band, in label space

im = Image.open("/mnt/user-data/uploads/HERO_CAN.png").convert("RGBA")
arr = np.array(im).astype(np.float64)
rgb, alpha = arr[..., :3], arr[..., 3] / 255.0
H, W, _ = rgb.shape
lum = rgb.mean(2)
mask = alpha > 0.5

xg = np.arange(W)[None, :].astype(float)
yg = np.arange(H)[:, None].astype(float)
sn = (xg - CX) / R
cs = np.sqrt(np.clip(1 - np.clip(sn, -1, 1) ** 2, 0, 1))
Ys = (yg - EA * cs) / (1.0 + EB * cs)

inband = mask & (Ys >= YS_TOP) & (Ys <= YS_BOT) & (np.abs(sn) < 0.999)
print("band px:", inband.sum(), " holes in band rows:",
      int(sum(1 for y in range(H) if inband[y].sum() and
              (np.diff(np.where(inband[y])[0]) > 1).any())))

# ---------------------------------------------------------------- ink & INK
ext = lum.copy()
for y in range(H):
    xb = np.where(inband[y])[0]
    if len(xb) < 8:
        continue
    ext[y, :xb.min()] = ext[y, xb.min()]
    ext[y, xb.max() + 1:] = ext[y, xb.max()]

DS = 4
bs = percentile_filter(ext[::DS, ::DS], 30, size=(1, 39), mode="nearest")
base = zoom(bs, (H / bs.shape[0], W / bs.shape[1]), order=1)[:H, :W]
base = gaussian_filter(base, 6)

# Specular ridges peak near 152; cream ink sits at 230-255.
ink = inband & (lum > 160) & ((lum - base) > 40)
INK = np.array([np.percentile(rgb[..., c][ink & (lum > 190)], 60) for c in range(3)])
print("INK", INK.round(1), " ink px", int(ink.sum()))

# -------------------------------------------- shading from ink-free rows only
ink_wide = binary_dilation(ink, np.ones((5, 5), bool))
core = inband & (np.abs(sn) < 0.93)
row_ink = (ink_wide & core).sum(1) / np.maximum(core.sum(1), 1)
clean = (row_ink < 0.010) & (core.sum(1) > 200)
ci = np.where(clean)[0]
print("clean rows:", len(ci), "span", ci.min(), ci.max(), "maxgap", int(np.diff(ci).max()))

prof = np.zeros((H, W, 3))
for y in ci:
    xb = np.where(inband[y])[0]
    row = rgb[y].copy()
    row[:xb.min()] = row[xb.min()]
    row[xb.max() + 1:] = row[xb.max()]
    prof[y] = row
for c in range(3):
    prof[..., c] = np.stack(
        [np.interp(np.arange(H), ci, prof[ci, x, c]) for x in range(W)], axis=1)

shade = np.dstack([gaussian_filter(prof[..., c], (30, 7)) for c in range(3)])
shade = np.maximum(shade, 2.0)
REF = np.array([np.median(shade[inband][:, c]) for c in range(3)])
print("REF", REF.round(2))

# --------------------------------------------------------------- coverage k
sl = shade.mean(2)
k = np.clip((lum - sl) / np.maximum(INK.mean() - sl, 1.0), 0.0, 1.0)
k = np.clip((k - 0.10) / 0.90, 0.0, 1.0)      # kill low-level sheen residue
k[~inband] = 0.0

rec = shade * (1 - k[..., None]) + INK * k[..., None]
err = np.abs(rec - rgb).mean(2)[inband]
print("recompose err  p50 %.2f  p95 %.2f  p99.9 %.2f" % tuple(np.percentile(err, [50, 95, 99.9])))

np.savez_compressed("geom.npz", shade=shade.astype(np.float32), k=k.astype(np.float32),
                    inband=inband, mask=mask, alpha=alpha.astype(np.float32),
                    rgb=rgb.astype(np.float32), REF=REF, INK=INK)
Image.fromarray(np.clip(shade, 0, 255).astype(np.uint8)).save("dbg_shade.png")
Image.fromarray((k * 255).astype(np.uint8)).save("dbg_k.png")
Image.fromarray(np.clip(rec, 0, 255).astype(np.uint8)).save("dbg_recompose.png")
