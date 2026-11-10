"""
Crea le due immagini della schermata della busta (carta invecchiata e ceralacca)
calcolando luci, rilievi e texture. Si lancia solo se si vuole cambiarle:
    python crea_asset.py
Scrive: assets/busta.webp  e  assets/cera.webp
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

CARTELLA = os.path.dirname(os.path.abspath(__file__))
USCITA = os.path.join(CARTELLA, "assets")
os.makedirs(USCITA, exist_ok=True)


def fractal(shape, sigmas, pesi, seed):
    r = np.random.default_rng(seed)
    out = np.zeros(shape)
    for s, w in zip(sigmas, pesi):
        n = ndi.gaussian_filter(r.standard_normal(shape), s, mode="wrap")
        n /= n.std() + 1e-9
        out += w * n
    return out / sum(pesi)


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# =====================================================================
#  BUSTA (carta invecchiata)  1000 x 740   (corrisponde a 320 x 236 unita')
# =====================================================================
def crea_busta():
    W, H, SS = 1000, 740, 3
    X0, X1, Y0, Y1 = 31, 969, 62, 656
    PUNTA = (500, 456)
    CENTRO = (500, 400)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)

    def maschera(disegna):
        im = Image.new("L", (W * SS, H * SS), 0)
        disegna(ImageDraw.Draw(im))
        return np.asarray(im.resize((W, H), Image.LANCZOS), dtype=float) / 255

    body = maschera(lambda d: d.rounded_rectangle([X0 * SS, Y0 * SS, X1 * SS, Y1 * SS], radius=26 * SS, fill=255))
    poly = lambda pts: maschera(lambda d: d.polygon([(x * SS, y * SS) for x, y in pts], fill=255))
    flap = poly([(X0, Y0 - 2), (X1, Y0 - 2), PUNTA]) * body
    left = poly([(X0, Y0), CENTRO, (X0, Y1)]) * body * (1 - flap)
    right = poly([(X1, Y0), CENTRO, (X1, Y1)]) * body * (1 - flap)
    bott = poly([(X0, Y1), CENTRO, (X1, Y1)]) * body * (1 - flap)

    # --- carta di base con macchie, grana e fibre
    base = np.array([238.0, 223.0, 187.0])
    stain = fractal((H, W), [150, 70, 28, 9], [1.0, .8, .6, .35], 11)
    grana = ndi.gaussian_filter(np.random.default_rng(3).standard_normal((H, W)), .7)
    grana /= grana.std()
    col = base[None, None, :] * (1 + 0.05 * stain)[..., None]
    pos = np.clip(stain, 0, None)
    col[..., 1] *= 1 - 0.025 * pos
    col[..., 2] *= 1 - 0.075 * pos
    col *= (1 + 0.018 * grana)[..., None]

    fib = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fib)
    r = np.random.default_rng(5)
    for _ in range(2600):
        x, y = r.uniform(0, W), r.uniform(0, H)
        a = r.uniform(0, 6.28)
        l = r.uniform(6, 26)
        fd.line([(x, y), (x + np.cos(a) * l, y + np.sin(a) * l + r.uniform(-3, 3))], fill=int(r.uniform(40, 120)), width=1)
    fib = ndi.gaussian_filter(np.asarray(fib, dtype=float) / 255, .6)
    col *= (1 - 0.06 * fib)[..., None]

    # --- luci diverse sui pannelli
    luce = np.ones((H, W))
    luce += left * (-0.045 + 0.06 * (xx - X0) / 470)
    luce += right * (-0.11 + 0.05 * (X1 - xx) / 470)
    luce += bott * (0.035 - 0.08 * (yy - 400) / 256)
    luce += flap * (0.07 - 0.13 * (yy - Y0) / 394)
    col *= luce[..., None]

    # --- pieghe sotto il lembo
    def linea(pts, spess, off=(0, 0)):
        im = Image.new("L", (W * SS, H * SS), 0)
        ImageDraw.Draw(im).line([((x + off[0]) * SS, (y + off[1]) * SS) for x, y in pts], fill=255, width=int(spess * SS))
        return np.asarray(im.resize((W, H), Image.LANCZOS), dtype=float) / 255

    for pts in ([(X0, Y1), CENTRO], [(X1, Y1), CENTRO]):
        scura = ndi.gaussian_filter(linea(pts, 3.5), 1.6)
        chiara = ndi.gaussian_filter(linea(pts, 3.0, (2, 4.5)), 1.4)
        col *= (1 - 0.34 * scura * (1 - flap))[..., None]
        col += 255 * (0.13 * chiara * (1 - flap))[..., None]
    # bordo del lembo: riga scura + riflesso interno
    for pts in ([(X0, Y0), PUNTA], [(X1, Y0), PUNTA]):
        scura = ndi.gaussian_filter(linea(pts, 3.2), 1.3)
        chiara = ndi.gaussian_filter(linea(pts, 3.0, (0 if pts[0][0] < 500 else 0, -5)), 1.5)
        col *= (1 - 0.30 * scura)[..., None]
        col += 255 * (0.16 * chiara * flap)[..., None]

    # --- ombra del lembo sul corpo
    sh = np.roll(flap, 26, axis=0)
    sh = ndi.gaussian_filter(sh, 18)
    col *= (1 - 0.72 * sh * (1 - flap) * body)[..., None]
    # ombra morbida appena sotto i fianchi del lembo
    sh2 = ndi.gaussian_filter(np.roll(flap, 7, axis=0), 5)
    col *= (1 - 0.25 * sh2 * (1 - flap) * body)[..., None]

    # --- invecchiamento: bordi ingialliti, macchie, aloni, graffi
    dist = ndi.distance_transform_edt(body > 0.5)
    rumore = fractal((H, W), [40, 14, 5], [1, .8, .5], 21)
    e = np.exp(-dist / 60.0) * (0.75 + 0.25 * rumore)
    tint = np.array([176.0, 130.0, 78.0])
    a = np.clip(0.38 * e, 0, 0.6)[..., None]
    col = col * (1 - a) + tint * a * 0.92
    # macchie di umidita'
    rr = np.random.default_rng(9)
    for _ in range(16):
        cx, cy = rr.uniform(X0 + 30, X1 - 30), rr.uniform(Y0 + 30, Y1 - 30)
        rad = rr.uniform(8, 34)
        g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rad ** 2)))
        al = rr.uniform(.07, .2) * g * (0.6 + 0.4 * rumore)
        col = col * (1 - al[..., None]) + np.array([150, 104, 58.0]) * al[..., None]
    # un alone circolare, come di una tazza
    ring = np.exp(-(((np.hypot(xx - 770, yy - 520) - 82) ** 2) / (2 * 3.2 ** 2)))
    ring = ndi.gaussian_filter(ring, 1.5) * (0.5 + 0.5 * rumore) * flap.clip(0, 0) + ndi.gaussian_filter(ring, 1.5) * 0
    # sporco in basso
    col *= (1 - 0.10 * smooth(yy, 520, 656) * (0.7 + 0.3 * rumore) * body)[..., None]
    # graffi chiari sui bordi
    scuff = fractal((H, W), [2.2, 1.0], [1, 1], 33)
    mask_s = ((scuff > 1.45) & (dist < 16)).astype(float)
    mask_s = ndi.gaussian_filter(mask_s, .8)
    col += 255 * (0.12 * mask_s)[..., None]

    # --- bordo decorativo a inchiostro (rosso e verde), consumato
    def contorno(pts, spess, ss=SS):
        im = Image.new("L", (W * ss, H * ss), 0)
        ImageDraw.Draw(im).line([(x * ss, y * ss) for x, y in pts + [pts[0]]], fill=255, width=int(spess * ss), joint="curve")
        return np.asarray(im.resize((W, H), Image.LANCZOS), dtype=float) / 255

    def rettangolo(inset, spess):
        return contorno([(X0 + inset, Y0 + inset), (X1 - inset, Y0 + inset), (X1 - inset, Y1 - inset), (X0 + inset, Y1 - inset)], spess)

    G = ((X0 + X1 + PUNTA[0]) / 3, (Y0 + Y0 + PUNTA[1]) / 3)

    def triangolo(k, spess):
        pts = [(G[0] + (px - G[0]) * k, G[1] + (py - G[1]) * k) for px, py in [(X0, Y0), (X1, Y0), PUNTA]]
        return contorno(pts, spess)

    corpo_ink = (rettangolo(30, 3.4), rettangolo(41, 1.7))
    lembo_ink = (triangolo(.90, 3.4), triangolo(.845, 1.7))
    usura = np.clip(0.55 + 0.6 * fractal((H, W), [3, 1.2], [1, 1], 41), 0, 1)
    rosso = np.array([158.0, 38.0, 48.0])
    verde = np.array([42.0, 98.0, 70.0])
    for (m_r, m_v), regione in ((corpo_ink, (1 - flap) * body), (lembo_ink, flap)):
        for m, c, op in ((m_r, rosso, .62), (m_v, verde, .55)):
            al = (m * regione * usura * op)[..., None]
            col = col * (1 - al) + c * al

    # --- bordo dello spessore della carta
    spess = smooth(3.0 - dist, 0, 3.0)
    col *= (1 - 0.16 * spess)[..., None]
    col += 255 * (0.10 * smooth(dist, 0, 2.2) * (1 - smooth(dist, 2.2, 4.5)) * (yy < 330))[..., None]

    # --- alone leggero ai bordi esterni (vignettatura)
    vig = 1 - 0.07 * smooth(np.hypot((xx - 500) / 520, (yy - 360) / 340), .6, 1.15)
    col *= vig[..., None]

    rgb = np.clip(col, 0, 255).astype(np.uint8)
    alpha = np.clip(body * 255, 0, 255).astype(np.uint8)
    out = np.dstack([rgb, alpha])
    Image.fromarray(out, "RGBA").save(os.path.join(USCITA, "busta.webp"), quality=90, method=6)
    print("busta.webp", os.path.getsize(os.path.join(USCITA, "busta.webp")) // 1024, "KB")


# =====================================================================
#  CERALACCA  420 x 420 (disegnata a 840 e ridotta)
# =====================================================================
def crea_cera():
    S = 840
    CX, CY = 420, 400
    R0 = 282
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    r = np.random.default_rng(14)

    # sagoma irregolare, come cera sciolta
    ang = np.arctan2(yy - CY, xx - CX)
    rad = np.hypot(xx - CX, yy - CY)
    raggio = R0 * (1 + 0.040 * np.sin(3 * ang + 1.1) + 0.028 * np.sin(5 * ang + 2.3) + 0.018 * np.sin(8 * ang + 0.4) + 0.012 * np.sin(13 * ang + 3.0))
    # qualche sbavatura piu' marcata
    for a0, w, d in ((-0.6, .35, 22), (2.4, .30, 18), (0.9, .25, -10), (-2.3, .3, 14)):
        da = np.angle(np.exp(1j * (ang - a0)))
        raggio += d * np.exp(-(da / w) ** 2)
    m = (rad < raggio).astype(float)

    # goccia che cola
    gocc = Image.new("L", (S, S), 0)
    gd = ImageDraw.Draw(gocc)
    gd.polygon([(CX + 50, CY + 200), (CX + 130, CY + 200), (CX + 122, CY + 345), (CX + 92, CY + 372), (CX + 62, CY + 345)], fill=255)
    gd.ellipse([CX + 55, CY + 318, CX + 129, CY + 392], fill=255)
    gocc = ndi.gaussian_filter(np.asarray(gocc, dtype=float) / 255, 7)
    m = np.clip(np.maximum(m, ndi.gaussian_filter(np.where(gocc > .5, 1.0, 0.0), 1.3)), 0, 1)
    m = ndi.gaussian_filter(m, 1.2)
    mask_bin = m > 0.5

    # altezza: bordo arrotondato
    dist = ndi.distance_transform_edt(mask_bin)
    h = np.tanh(dist / 34.0)
    h += 0.10 * ndi.gaussian_filter(r.standard_normal((S, S)), 14) / 0.02 * 0.02

    # disco incassato + cordolo
    Ri = 0.66 * R0
    disco = ndi.gaussian_filter((np.hypot(xx - CX, yy - CY) < Ri).astype(float), 3.5)
    cord = ndi.gaussian_filter(((np.hypot(xx - CX, yy - CY) > Ri - 4) & (np.hypot(xx - CX, yy - CY) < Ri + 16)).astype(float), 5)
    h = h - 0.62 * disco + 0.20 * cord

    # stella in rilievo
    def stella(cx, cy, R1, R2, punte=4):
        pts = []
        for i in range(punte * 2):
            a = -np.pi / 2 + i * np.pi / punte
            rr_ = R1 if i % 2 == 0 else R2
            pts.append((cx + np.cos(a) * rr_, cy + np.sin(a) * rr_))
        im = Image.new("L", (S, S), 0)
        ImageDraw.Draw(im).polygon(pts, fill=255)
        return np.asarray(im, dtype=float) / 255
    st = ndi.gaussian_filter(stella(CX, CY, 150, 36), 3.6)
    st2 = ndi.gaussian_filter(stella(CX, CY, 78, 30, 4) if False else np.zeros((S, S)), 1)
    h += 0.50 * st

    # perline attorno
    pe = Image.new("L", (S, S), 0)
    pd = ImageDraw.Draw(pe)
    for i in range(26):
        a = i / 26 * 6.2832
        x, y = CX + np.cos(a) * Ri * 0.84, CY + np.sin(a) * Ri * 0.84
        pd.ellipse([x - 8.5, y - 8.5, x + 8.5, y + 8.5], fill=255)
    pe = ndi.gaussian_filter(np.asarray(pe, dtype=float) / 255, 2.2)
    h += 0.22 * pe

    # piccole imperfezioni della cera
    h += 0.020 * fractal((S, S), [18, 6, 2.2], [1, .8, .5], 61)

    # normali e illuminazione
    hs = ndi.gaussian_filter(h, 1.1)
    gy, gx = np.gradient(hs)
    k = 34.0
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(hs)
    nl = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    nx, ny, nz = nx / nl, ny / nl, nz / nl
    L = np.array([-0.48, -0.56, 0.68])
    L /= np.linalg.norm(L)
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    Hh = L + np.array([0, 0, 1.0])
    Hh /= np.linalg.norm(Hh)
    nh = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1)
    spec = nh ** 70 * 0.95 + nh ** 14 * 0.16
    # occlusione ambientale dai dislivelli
    ao = np.clip(0.80 + 2.2 * (hs - ndi.gaussian_filter(hs, 22)), 0.55, 1.10)

    base = np.array([176.0, 20.0, 38.0])
    prof = np.array([112.0, 8.0, 24.0])
    t = np.clip(diff, 0, 1)[..., None]
    col = (prof * (1 - t) + base * t * 1.12) * (0.30 + 0.78 * t) * 1.0
    col = col * ao[..., None]
    # sottili variazioni di colore nella cera
    var = fractal((S, S), [30, 9], [1, .7], 71)
    col[..., 0] *= (1 + 0.06 * var)
    col[..., 1] *= (1 + 0.20 * var)
    # luce che attraversa la cera ai bordi sottili (sembra piu' calda)
    sottile = (1 - np.clip(dist / 26, 0, 1)) * mask_bin
    col += np.array([60.0, 6.0, 8.0]) * sottile[..., None] * 0.6
    col += np.array([255.0, 214.0, 218.0]) * spec[..., None] * mask_bin[..., None]
    col = np.clip(col, 0, 255)

    # ombra morbida sotto il sigillo
    ombra = ndi.gaussian_filter(np.roll(np.roll(m, 20, axis=0), 12, axis=1), 18) * 0.62
    a_out = np.clip(m + (1 - m) * ombra, 0, 1)
    rgb = np.where(a_out[..., None] > 1e-4, (col * m[..., None]) / np.maximum(a_out[..., None], 1e-4), 0)

    out = np.dstack([np.clip(rgb, 0, 255), a_out * 255]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA").resize((S // 2, S // 2), Image.LANCZOS)
    img.save(os.path.join(USCITA, "cera.webp"), quality=92, method=6)
    print("cera.webp", os.path.getsize(os.path.join(USCITA, "cera.webp")) // 1024, "KB")


if __name__ == "__main__":
    crea_busta()
    crea_cera()
