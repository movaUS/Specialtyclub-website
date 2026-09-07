"""Step 6: build the RGB label texture from the real wrap and render 36 frames.

Registration is locked to the circumference so the artwork keeps its printed
proportions, then the wordmark is aligned to the height it sits at in the
photograph. The mockup can is 10.6% wider-to-taller than the 202x152 sleeve,
so the sleeve's blank top and bottom margins are what gets cropped.
"""
import numpy as np, os, time
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter1d, binary_dilation

CX, R = 543.0, 283.0
EA, EB = 5.588, 0.009150
YS_TOP, YS_BOT = 215.0, 1318.0
TU, TV = 1792, 1216
NFRAMES, LEVELS = 36, 6
GAMMA = 0.70                     # ink falloff; background stays physical

FLAT_W, FLAT_H = 1446, 1088
CIRC = 2 * np.pi * R             # 1778 px around
SCALE = CIRC / FLAT_W            # 1.2296 can px per flat px
LOCK_X, LOCK_Y = 721.0, 417.0    # SPECIALTY centre in the flat
A_YS = 105.0                     # art top, in label space

d = np.load("geom.npz")
shade = d["shade"].astype(np.float64)
k_src = d["k"].astype(np.float64)
inband, alpha = d["inband"], d["alpha"].astype(np.float64)
rgb = d["rgb"].astype(np.float64)
INK, REF = d["INK"].astype(np.float64), d["REF"].astype(np.float64)
H, W = k_src.shape

# ------------------------------------------------------- texture from flat
flat = np.load("flat_art.npy").astype(np.float64)
tex_h = int(round(FLAT_H * SCALE / (YS_BOT - YS_TOP) * TV))
img = Image.fromarray(np.clip(flat, 0, 255).astype(np.uint8)).resize((TU, tex_h), Image.LANCZOS)
art = np.array(img).astype(np.float64)

tex = np.tile(REF, (TV, TU, 1))
row0 = (A_YS - YS_TOP) / (YS_BOT - YS_TOP) * TV      # where the art top lands
for iv in range(TV):
    s = int(round(iv - row0))
    if 0 <= s < tex_h:
        tex[iv] = art[s]

shift = int(round(TU / 2 - LOCK_X * TU / FLAT_W))
tex = np.roll(tex, shift, axis=1)
print("texture %s  art rows %d  vshift %.1f  hshift %d" % (tex.shape, tex_h, row0, shift))

cov = np.clip((tex.mean(2) - REF.mean()) / (245.0 - REF.mean()), 0, 1)

mips = np.zeros((LEVELS, TV, TU, 3), np.float32)
mips[0] = tex
for l in range(1, LEVELS):
    for c in range(3):
        mips[l, ..., c] = gaussian_filter1d(tex[..., c], 0.5 * (2 ** l), axis=1, mode="wrap")
covm = np.zeros((LEVELS, TV, TU), np.float32)
covm[0] = cov
for l in range(1, LEVELS):
    covm[l] = gaussian_filter1d(cov, 0.5 * (2 ** l), axis=1, mode="wrap")

# --------------------------------------------------------- screen geometry
ys_i, xs_i = np.nonzero(inband)
sn = np.clip((xs_i - CX) / R, -0.999999, 0.999999)
th = np.arcsin(sn); cth = np.cos(th)
Ysv = (ys_i - EA * cth) / (1.0 + EB * cth)
vv = (Ysv - YS_TOP) / (YS_BOT - YS_TOP)
ok = (vv >= 0) & (vv <= 1)
ys_i, xs_i, th, vv = ys_i[ok], xs_i[ok], th[ok], vv[ok]
vpix = vv * (TV - 1)

t_lo = np.arcsin(np.clip((xs_i - 0.5 - CX) / R, -1, 1))
t_hi = np.arcsin(np.clip((xs_i + 0.5 - CX) / R, -1, 1))
lod = np.clip(np.log2(np.maximum(np.abs(t_hi - t_lo) / (2 * np.pi) * TU, 1e-3)), 0, LEVELS - 1.001)
l0 = np.floor(lod).astype(int); lf = lod - l0

shade_px = shade[ys_i, xs_i]
illum = shade_px / REF

rec0 = shade * (1 - k_src[..., None]) + INK * k_src[..., None]
gf = np.clip(rgb - rec0, -10, 10)
inkd = binary_dilation(k_src > 0.04, np.ones((11, 11), bool))
for y in range(H):
    b = inband[y]
    if b.sum() < 12: continue
    bad = inkd[y] & b; good = b & ~bad
    if good.sum() < 12 or not bad.any(): continue
    gx, bx = np.where(good)[0], np.where(bad)[0]
    for c in range(3):
        gf[y, bx, c] = np.interp(bx, gx, gf[y, gx, c])
grain = gf[ys_i, xs_i]

os.makedirs("frames_art", exist_ok=True)
t0 = time.time()
for f in range(NFRAMES):
    phi = 2 * np.pi * f / NFRAMES
    u = ((th + phi) / (2 * np.pi) + 0.5) % 1.0 * TU

    val = np.zeros((len(u), 3)); cvv = np.zeros(len(u))
    for l in range(LEVELS):
        m = l0 == l
        if not m.any(): continue
        co = np.vstack([vpix[m], u[m]])
        w = lf[m]
        for c in range(3):
            a1 = map_coordinates(mips[l, ..., c], co, order=1, mode="grid-wrap")
            b1 = a1 if l + 1 >= LEVELS else map_coordinates(mips[l + 1, ..., c], co, order=1, mode="grid-wrap")
            val[m, c] = a1 * (1 - w) + b1 * w
        a2 = map_coordinates(covm[l], co, order=1, mode="grid-wrap")
        b2 = a2 if l + 1 >= LEVELS else map_coordinates(covm[l + 1], co, order=1, mode="grid-wrap")
        cvv[m] = a2 * (1 - w) + b2 * w
    cvv = np.clip(cvv, 0, 1)[:, None]

    eff = illum * (1 - cvv) + np.power(np.clip(illum, 0, None), GAMMA) * cvv
    px = val * eff + grain * (1 - cvv)

    out = rgb.copy()
    out[ys_i, xs_i] = px
    out = np.clip(out, 0, 255)
    Image.fromarray(np.dstack([out, alpha * 255]).astype(np.uint8), "RGBA").save(
        "frames_art/raw_%02d.png" % f)
    if f % 12 == 0: print("  frame %2d  %.1fs" % (f, time.time() - t0))

print("rendered in %.1fs" % (time.time() - t0))
