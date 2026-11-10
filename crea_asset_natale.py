"""
Crea le immagini decorative natalizie (ghirlanda, lucine, palline, rami di abete)
calcolando ago per ago luci, ombre, brina e riflessi.
    python crea_asset_natale.py
Scrive nella cartella assets/:
    ghirlanda.webp + ghirlanda.js   (festone ripetibile + posizione delle lucine)
    palla-rossa/oro/verde/perla.webp (palline da appendere)
    ramo.webp                        (ramo di abete con bacche e pigna, angolo in basso a sinistra)
"""
import os, math, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

CARTELLA = os.path.dirname(os.path.abspath(__file__))
USCITA = os.path.join(CARTELLA, "assets")
os.makedirs(USCITA, exist_ok=True)

LUCE = np.array([-0.5, -0.85])
LUCE = LUCE / np.linalg.norm(LUCE)

VERDI = [(7, 34, 26), (14, 66, 46), (24, 100, 66), (52, 140, 92), (112, 190, 128)]


def fractal(shape, sigmas, pesi, seed):
    r = np.random.default_rng(seed)
    out = np.zeros(shape)
    for sg, w in zip(sigmas, pesi):
        n = ndi.gaussian_filter(r.standard_normal(shape), sg, mode="wrap")
        n /= n.std() + 1e-9
        out += w * n
    return out / sum(pesi)


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def colore_verde(t):
    t = max(0.0, min(0.999, t)) * (len(VERDI) - 1)
    i = int(t)
    return lerp(VERDI[i], VERDI[i + 1], t - i)


def norm3(v):
    v = np.array(v, dtype=float)
    return v / np.linalg.norm(v)


# =====================================================================
#   SFERE LUCIDE (palline, bacche)
# =====================================================================
def sfera(r, base, metallo=False, lucido=1.0, motivo=None, margine=4):
    n = int(2 * r + 2 * margine)
    cx = cy = n / 2.0
    yy, xx = np.mgrid[0:n, 0:n].astype(float)
    nx, ny = (xx - cx) / r, (yy - cy) / r
    rr = np.sqrt(nx ** 2 + ny ** 2)
    alpha = np.clip((1 - rr) * r + 0.5, 0, 1)
    nz = np.sqrt(np.clip(1 - rr ** 2, 0, 1))
    L = norm3([-0.5, -0.6, 0.62])
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    rx, ry, rz = 2 * nz * nx, 2 * nz * ny, 2 * nz * nz - 1
    su = np.clip(0.5 - 0.5 * ry, 0, 1)            # 1 = cielo (in alto), 0 = terra
    b = np.array(base, dtype=float)
    cielo = np.array([235.0, 242.0, 255.0])
    terra = np.array([40.0, 30.0, 26.0])
    env = terra[None, None, :] * (1 - su[..., None]) + cielo[None, None, :] * su[..., None]
    if metallo:
        env = env * 0.55 + b[None, None, :] * 0.95
        env = np.clip(env, 0, 255)
    fres = 0.10 + 0.90 * (1 - nz) ** 4
    rif = (0.78 if metallo else 0.30) * lucido * (0.45 + 0.55 * fres) if metallo else 0.28 * lucido * fres + 0.05
    col = b[None, None, :] * (0.20 + 0.92 * diff)[..., None]
    if metallo:
        col = b[None, None, :] * (0.25 + 0.55 * diff)[..., None]
    col = col * (1 - rif[..., None]) + env * rif[..., None]
    # riflesso della finestra
    w = np.exp(-(((rx + 0.40) / 0.17) ** 2 + ((ry + 0.52) / 0.11) ** 2))
    w2 = np.exp(-(((rx - 0.45) / 0.10) ** 2 + ((ry - 0.50) / 0.07) ** 2)) * 0.5
    col += 255 * (w * 0.95 * lucido + w2 * 0.5 * lucido)[..., None]
    col += 255 * (np.exp(-(((nx + 0.42) / 0.055) ** 2 + ((ny + 0.50) / 0.055) ** 2)) * 0.9 * lucido)[..., None]
    if motivo is not None:
        m, c = motivo(nx, ny, nz)
        col = col * (1 - m[..., None]) + (np.array(c, dtype=float)[None, None, :] * (0.35 + 0.8 * diff)[..., None]) * m[..., None] + 255 * (w * 0.5 * m)[..., None]
    col = np.clip(col, 0, 255)
    out = np.dstack([col, alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def motivo_fascia(c1, c2):
    def f(nx, ny, nz):
        m1 = (np.abs(ny + 0.05) < 0.07).astype(float) * (nz > .1)
        m2 = ((np.abs(ny + 0.30) < 0.03) | (np.abs(ny - 0.20) < 0.03)).astype(float) * (nz > .1)
        m = np.clip(m1 + m2, 0, 1)
        return ndi.gaussian_filter(m, .7), c1
    return f


def motivo_puntini(colore, seed=3, n=46):
    def f(nx, ny, nz):
        r = np.random.default_rng(seed)
        m = np.zeros_like(nx)
        for _ in range(n):
            a, b = r.uniform(-.8, .8, 2)
            if a * a + b * b > .62:
                continue
            m += np.exp(-(((nx - a) ** 2 + (ny - b) ** 2) / (2 * .02 ** 2)))
        return np.clip(m, 0, 1), colore
    return f


def motivo_losanghe(colore):
    def f(nx, ny, nz):
        u = (nx + ny) * 5.0
        v = (nx - ny) * 5.0
        m = ((np.abs(np.sin(u * math.pi)) > .93) | (np.abs(np.sin(v * math.pi)) > .93)).astype(float) * (nz > .15)
        return ndi.gaussian_filter(m, .6) * 0.8, colore
    return f


def pallina(r, base, nome, metallo=False, motivo=None):
    S = 2
    sp = sfera(r * S, base, metallo=metallo, motivo=motivo)
    # cappuccio e gancio
    larg = int(2 * r * S + 8 * S)
    cap_h = int(r * 0.34 * S)
    gancio_h = int(r * 0.62 * S)
    tot = gancio_h + cap_h + sp.size[1] - int(r * 0.06 * S)
    tela = Image.new("RGBA", (sp.size[0], tot), (0, 0, 0, 0))
    cx = sp.size[0] // 2
    ys = gancio_h + cap_h - int(r * 0.06 * S)
    tela.alpha_composite(sp, (0, ys))
    # cappuccio dorato (cilindro con costolature)
    cw = int(r * 0.62 * S)
    cap = np.zeros((cap_h, cw, 4))
    xs = np.linspace(-1, 1, cw)[None, :].repeat(cap_h, 0)
    ysv = np.linspace(0, 1, cap_h)[:, None].repeat(cw, 1)
    sh = np.sqrt(np.clip(1 - xs ** 2, 0, 1))
    oro = np.array([226.0, 178.0, 78.0])
    g = oro[None, None, :] * (0.32 + 0.8 * (sh * 0.7 + 0.3 * np.clip(-xs * .8 + .35, 0, 1)))[..., None]
    g += 255 * (np.exp(-(((xs + .42) / .12) ** 2)) * 0.55)[..., None]
    g *= (1 - 0.18 * (np.sin(ysv * math.pi * 7) > .3))[..., None]
    cap[..., :3] = np.clip(g, 0, 255)
    cap[..., 3] = 255 * np.clip((1 - np.abs(xs)) * cw * .5 + .5, 0, 1)
    capim = Image.fromarray(cap.astype(np.uint8), "RGBA")
    tela.alpha_composite(capim, (cx - cw // 2, gancio_h))
    # gancio ad anello
    d = ImageDraw.Draw(tela)
    rr = int(r * 0.22 * S)
    for k, col in ((5.0, (110, 78, 24, 255)), (3.0, (232, 190, 96, 255)), (1.2, (255, 238, 180, 255))):
        d.ellipse([cx - rr, gancio_h - rr * 1.6, cx + rr, gancio_h + rr * 0.35], outline=col, width=max(1, int(k * S / 2)))
    d.line([(cx, 0), (cx, gancio_h - rr * 1.6)], fill=(232, 190, 96, 255), width=max(1, int(1.5 * S)))
    out = tela.resize((tela.size[0] // S, tela.size[1] // S), Image.LANCZOS)
    out.save(os.path.join(USCITA, nome), quality=92, method=6)
    return out.size


# =====================================================================
#   AGHI DI ABETE
# =====================================================================
class Pennello:
    def __init__(self, W, H, S=2, brillo=0.0):
        self.W, self.H, self.S = W, H, S
        self.brillo = brillo
        self.aghi = []        # (z, x, y, ang, L, w, t)
        self.steli = []       # liste di punti
        self.neve = []        # (x, y, r)
        self.punti = []       # punti utili per le decorazioni

    def ago(self, x, y, a, L, w, z):
        self.aghi.append((z, x, y, a, L, w))

    def disegna(self, rng, wrap=0):
        S = self.S
        im = Image.new("RGBA", (self.W * S, self.H * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # steli
        for pts, sp in self.steli:
            for off in ((0,) if not wrap else (-wrap, 0, wrap)):
                for (x1, y1), (x2, y2), s in zip(pts[:-1], pts[1:], sp):
                    d.line([((x1 + off) * S, y1 * S), ((x2 + off) * S, y2 * S)], fill=(52, 36, 24, 255), width=max(1, int(s * S)))
        self.aghi.sort(key=lambda a: a[0])
        for z, x, y, a, L, w in self.aghi:
            dx, dy = math.cos(a), math.sin(a)
            lit = 0.5 + 0.5 * (dx * LUCE[0] + dy * LUCE[1])
            t = lit * 0.52 + z * 0.50 - 0.22 + self.brillo + rng.normal(0, 0.05)
            c1 = colore_verde(t - 0.10)
            c2 = colore_verde(t + 0.16)
            # punta leggermente piegata verso il basso (gravita')
            tx, ty = x + dx * L, y + dy * L + L * 0.12
            mx, my = x + dx * L * 0.52, y + dy * L * 0.52 + L * 0.03
            px, py = -dy, dx
            for off in ((0,) if not wrap else (-wrap, 0, wrap)):
                ox = off
                base = [((x + px * w + ox) * S, (y + py * w) * S), ((x - px * w + ox) * S, (y - py * w) * S),
                        ((mx - px * w * .55 + ox) * S, (my - py * w * .55) * S), ((tx + ox) * S, ty * S),
                        ((mx + px * w * .55 + ox) * S, (my + py * w * .55) * S)]
                d.polygon(base, fill=tuple(int(v) for v in c1) + (255,))
                tip = [((mx + px * w * .55 + ox) * S, (my + py * w * .55) * S), ((mx - px * w * .55 + ox) * S, (my - py * w * .55) * S), ((tx + ox) * S, ty * S)]
                d.polygon(tip, fill=tuple(int(v) for v in c2) + (255,))
        arr = np.array(im, dtype=float)
        al = arr[..., 3] / 255.0
        ao = ndi.gaussian_filter(al, 16 * S)
        ao2 = ndi.gaussian_filter(al, 5 * S)
        arr[..., :3] *= (1 - 0.42 * ao - 0.18 * ao2)[..., None]
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def abete(P, rng, x, y, ang, lung, nl, prof=0, curva=0.0, wrap=False):
    passo = max(1.4, nl * 0.046)
    n = int(lung / passo)
    px, py = x, y
    fase = rng.uniform(0, 6)
    pts, sp = [(px, py)], []
    for i in range(n):
        t = i / n
        a = ang + curva * t + 0.13 * math.sin(t * 3.4 + fase)
        px += math.cos(a) * passo
        py += math.sin(a) * passo
        pts.append((px, py))
        sp.append(max(1.4, nl * 0.09 * (1 - t) * (2.4 - prof)))
        P.punti.append((px, py, a, t, prof))
        L = nl * (1 - 0.60 * t) * (0.82 + 0.32 * rng.random())
        w = max(1.0, nl * 0.050 * (1 - 0.30 * t))
        for lato in (-1, 1):
            for k in range(4):
                na = a + lato * (0.95 + 0.50 * rng.random() - 0.38 * t) + (0.0, 0.18, -0.12, 0.30)[k] * (-lato)
                P.ago(px, py, na, L * (1.0, 0.82, 0.66, 0.50)[k] * (0.9 + 0.2 * rng.random()), w, rng.random())
        if prof < 2 and i % max(6, int(n / (12 - 4 * prof))) == int(fase) % 5 + 2 and 0.10 < t < 0.88:
            s = 1 if (i // 7) % 2 else -1
            abete(P, rng, px, py, a + s * (0.78 + 0.25 * rng.random()), lung * (0.36 - 0.06 * prof), nl * 0.86, prof + 1, s * 0.25, wrap)
    P.steli.append((pts, sp))


def neve_su(P, rng, im, prob, forza=1.0, wrap=0, W=0):
    """brina: puntini bianchi sulle punte degli aghi rivolte verso l'alto"""
    S = P.S
    nv = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(nv)
    for z, x, y, a, L, w in P.aghi:
        if rng.random() > prob:
            continue
        dx, dy = math.cos(a), math.sin(a)
        if dy > 0.25:     # solo aghi che puntano in su o di lato
            continue
        tx, ty = x + dx * L * 0.82, y + dy * L * 0.82 + L * 0.10
        r = max(1.0, w * 1.5)
        for off in ((0,) if not wrap else (-wrap, 0, wrap)):
            d.ellipse([(tx + off - r * 1.3) * S, (ty - r) * S, (tx + off + r * 1.3) * S, (ty + r * .8) * S], fill=(232, 243, 250, int(220 * forza)))
    nv = nv.filter(ImageFilter.GaussianBlur(0.5 * S))
    im.alpha_composite(nv)


# =====================================================================
#   LUCINE
# =====================================================================
def lampadina(colore, w=44, h=80):
    S = 3
    W, H = w * S, h * S
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    cx = W / 2
    col = np.array(colore, dtype=float)
    # presa (metallo scuro con anelli)
    pres_h = int(H * 0.26)
    # profilo ovale a goccia per il vetro
    y0 = pres_h * 0.85
    hh = H - y0
    t = np.clip((yy - y0) / hh, 0, 1)
    prof = (W * 0.46) * np.sin(np.pi * np.clip(t, 0, 1) ** 0.72) ** 0.85
    prof = np.where(t < 0.04, W * 0.20, prof)
    dist = np.abs(xx - cx)
    in_v = (dist <= prof) & (yy >= y0)
    nxv = np.where(prof > 1, (xx - cx) / np.maximum(prof, 1), 0)
    nzv = np.sqrt(np.clip(1 - nxv ** 2, 0, 1))
    nyv = (t - 0.45) * 1.1
    L = norm3([-0.5, -0.5, 0.7])
    diff = np.clip(nxv * L[0] + nyv * L[1] + nzv * L[2], 0, 1)
    nucleo = np.exp(-(((xx - cx) / (W * 0.20)) ** 2 + ((yy - (y0 + hh * 0.42)) / (hh * 0.28)) ** 2))
    vetro = col[None, None, :] * (0.50 + 0.55 * diff)[..., None]
    vetro = vetro * (0.55 + 0.45 * nzv)[..., None]
    vetro += (np.array([255, 245, 220.0]) * 0.8)[None, None, :] * (nucleo * 0.7)[..., None]
    vetro += 255 * (np.exp(-(((xx - (cx - W * 0.20)) / (W * 0.055)) ** 2 + ((yy - (y0 + hh * 0.38)) / (hh * 0.20)) ** 2)) * 0.8)[..., None]
    alpha = np.clip((prof - dist) * 1.2 + 0.5, 0, 1) * (yy >= y0)
    # presa
    sx = np.abs(xx - cx)
    in_p = (sx <= W * 0.20) & (yy < y0 + 3 * S)
    shp = np.sqrt(np.clip(1 - (sx / (W * 0.20)) ** 2, 0, 1))
    met = np.array([84.0, 84.0, 90.0])[None, None, :] * (0.25 + 0.9 * shp)[..., None]
    anelli = (np.sin(yy / S * 1.9) > 0.35) & in_p
    met = met * np.where(anelli, 0.55, 1.0)[..., None]
    met += 255 * (np.exp(-(((xx - (cx - W * 0.09)) / (W * 0.03)) ** 2)) * 0.5)[..., None]
    rgb = np.where(in_p[..., None], met, vetro)
    a = np.where(in_p, 1.0, alpha)
    out = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    return Image.fromarray(out, "RGBA").resize((w, h), Image.LANCZOS)


# =====================================================================
#   PIGNE, AGRIFOGLIO
# =====================================================================
def pigna(lung, larg, seed=5):
    S = 2
    r = np.random.default_rng(seed)
    W, H = int((lung + 20) * S), int((larg + 20) * S)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = H / 2
    righe = 15
    elementi = []
    for i in range(righe):
        t = i / (righe - 1)
        wd = larg * 0.5 * (math.sin(math.pi * (0.12 + 0.88 * t)) ** 0.65) * (1.0 - 0.1 * t)
        xx = (10 + lung * (1 - t) * 0.98) * S
        n = 6
        for k in range(n):
            ang = (k / n - 0.5) * 2.6 + r.normal(0, 0.06)
            yy = cy + math.sin(ang) * wd * S
            cz = math.cos(ang)
            elementi.append((cz, xx, yy, wd * S, t, ang))
    elementi.sort(key=lambda e: e[0])
    for cz, xx, yy, wd, t, ang in elementi:
        sw, sh = lung * 0.20 * S, larg * 0.22 * S
        lit = 0.45 + 0.55 * (-math.sin(ang) * 0.9 + 0.1)
        base = np.array([116.0, 76.0, 44.0]) * (0.45 + 0.8 * lit * (0.55 + 0.45 * cz))
        for k, f in ((0, 0.55), (1, 0.85), (2, 1.0)):
            col = tuple(int(min(255, v * f)) for v in base)
            d.ellipse([xx - sw * (1 - 0.2 * k), yy - sh * (1 - 0.22 * k), xx + sw * (1 - 0.2 * k), yy + sh * (1 - 0.22 * k)], fill=col + (255,))
        d.arc([xx - sw, yy - sh, xx + sw, yy + sh], 200, 340, fill=(200, 150, 96, 200), width=max(1, S))
    return im.resize((W // S, H // S), Image.LANCZOS)


def agrifoglio(lung, seed=1):
    S = 3
    r = np.random.default_rng(seed)
    W, H = int(lung * 1.2 * S), int(lung * 0.7 * S)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 6 * S, H / 2
    n = 36
    # contorno ondulato con punte
    sup, inf = [], []
    for i in range(n + 1):
        t = i / n
        hw = lung * 0.30 * math.sin(math.pi * t ** 0.9) * (1 + 0.18 * (abs((t * 6) % 2 - 1) - 0.5) * 2)
        x = cx + t * lung * S
        sup.append((x, cy - hw * S))
        inf.append((x, cy + hw * S))
    poly = sup + inf[::-1]
    d.polygon(poly, fill=(8, 46, 30, 255))
    # metà superiore piu' chiara (luce)
    d.polygon(sup + [(cx + lung * S, cy), (cx, cy)], fill=(20, 84, 48, 255))
    d.line([(cx, cy), (cx + lung * S * 0.97, cy)], fill=(86, 150, 96, 255), width=int(1.4 * S))
    for i in range(3, n - 4, 4):
        x = cx + i / n * lung * S
        hw = lung * 0.26 * S * math.sin(math.pi * (i / n))
        d.line([(x, cy), (x + 0.20 * lung * S / 4, cy - hw * .82)], fill=(52, 112, 70, 255), width=int(1 * S))
        d.line([(x, cy), (x + 0.20 * lung * S / 4, cy + hw * .82)], fill=(24, 84, 48, 255), width=int(1 * S))
    d.line(sup, fill=(96, 160, 104, 255), width=int(1.0 * S))
    return im.resize((W // S, H // S), Image.LANCZOS)


def ruota(im, gradi, centro=None):
    return im.rotate(gradi, expand=True, resample=Image.BICUBIC, center=centro)


def incolla(tela, spr, x, y, grad=0):
    if grad:
        spr = ruota(spr, grad)
    tela.alpha_composite(spr, (int(x - spr.size[0] / 2), int(y - spr.size[1] / 2)))


def bacche(tela, x, y, S, r=7, n=3, seed=1):
    rr = np.random.default_rng(seed)
    sp = sfera(r * S, (196, 18, 34), lucido=1.0)
    for k in range(n):
        a = k / n * 6.28 + rr.uniform(0, 1)
        incolla(tela, sp, x + math.cos(a) * r * S * 0.9, y + math.sin(a) * r * S * 0.9)
    return tela


# =====================================================================
#   GHIRLANDA (festone ripetibile)
# =====================================================================
def crea_ghirlanda():
    K = 1.5                       # fattore per schermi ad alta definizione
    W0, H0 = 620, 205
    W, H = int(W0 * K), int(H0 * K)
    S = 2
    rng = np.random.default_rng(31)
    y0, sag = 30 * K, 62 * K
    P = Pennello(W, H, S, brillo=0.12)

    def yv(x):
        u = (x % W) / W
        return y0 + 4 * sag * u * (1 - u)

    def tang(x):
        u = (x % W) / W
        return 4 * sag * (1 - 2 * u) / W

    nl = 36 * K
    passo = 0.7 * K
    x = 0.0
    while x < W:
        yc = yv(x)
        a = math.atan2(tang(x), 1)
        for lato in (-1, 1):
            for k in range(4):
                na = a + lato * (1.0 + 0.5 * rng.random()) + (0.0, 0.18, -0.12, 0.30)[k] * (-lato)
                L = nl * (0.6 + 0.6 * rng.random()) * (1, 0.82, 0.66, 0.5)[k]
                P.ago(x, yc, na, L, max(1.2, 1.5 * K), rng.random())
        x += passo
    # stelo (filo scuro) lungo il festone
    xs = np.arange(0, W + 1, 4.0)
    P.steli.append(([(float(xx), float(yv(xx))) for xx in xs], [3.0 * K] * (len(xs) - 1)))
    im = P.disegna(rng, wrap=W)
    pass

    # decorazioni naturali: bacche e pigne piccole
    for t_, sd in ((0.10, 1), (0.58, 2), (0.86, 3)):
        xx = t_ * W
        bacche(im, xx * S, (yv(xx) + 7 * K) * S, S, r=int(5.0 * K), n=3, seed=sd)
    # lucine
    lamp_info = []
    cols = [(255, 78, 90), (255, 206, 84), (112, 226, 160), (112, 184, 255), (255, 232, 190)]
    m = 4
    for j in range(m):
        t_ = (j + 0.5) / m
        xx = t_ * W
        if 0.05 < t_ % 1 < 0.95:
            pass
        yy = yv(xx)
        col = cols[j % 5]
        sp = lampadina(col, int(40 * K / 1.2), int(76 * K / 1.2)).resize((int(40 * K), int(76 * K)), Image.LANCZOS) if False else lampadina(col, int(38 * K), int(70 * K))
        spS = sp.resize((sp.size[0] * S, sp.size[1] * S), Image.LANCZOS)
        # ombra della lampadina sul fogliame
        im.alpha_composite(spS, (int((xx - sp.size[0] / 2) * S), int((yy + 4 * K) * S)))
        lamp_info.append({"x": xx / W, "y": (yy + 4 * K + sp.size[1] * 0.60) / H, "c": "#%02x%02x%02x" % col})
    out = im.resize((W, H), Image.LANCZOS)
    out.save(os.path.join(USCITA, "ghirlanda.webp"), quality=90, method=6)
    meta = {"w": W, "h": H, "y0": y0 / H, "sag": sag / H, "lampadine": lamp_info}
    with open(os.path.join(USCITA, "ghirlanda.js"), "w", encoding="utf-8") as f:
        f.write("window.GHIRLANDA=" + json.dumps(meta) + ";")
    print("ghirlanda", out.size, os.path.getsize(os.path.join(USCITA, "ghirlanda.webp")) // 1024, "KB")


# =====================================================================
#   PALLINE
# =====================================================================
def crea_palline():
    r = 46
    pallina(r, (176, 14, 32), "palla-rossa.webp", motivo=motivo_fascia((250, 224, 150), None))
    pallina(r, (240, 190, 70), "palla-oro.webp", metallo=True, motivo=motivo_losanghe((255, 236, 170)))
    pallina(r, (22, 104, 74), "palla-verde.webp", motivo=motivo_puntini((255, 244, 210), 7))
    pallina(r, (246, 240, 224), "palla-perla.webp", motivo=motivo_fascia((190, 30, 48), None))
    print("palline ok")


# =====================================================================
#   RAMO DI ABETE (angolo in basso a sinistra)
# =====================================================================
def crea_ramo():
    W, H = 800, 640
    S = 2
    rng = np.random.default_rng(77)
    P = Pennello(W, H, S, brillo=0.07)
    ox, oy = -30, H + 30
    nl = 46
    rami = ((-10, 640), (-24, 780), (-40, 700), (-56, 620), (-74, 520))
    for ang, lung in rami:
        abete(P, rng, ox, oy, math.radians(ang), lung, nl, 0, rng.uniform(-.12, .12))
    im = P.disegna(rng)

    def pos(bi, t):
        ang, lung = rami[bi]
        return ox + math.cos(math.radians(ang)) * lung * t, oy + math.sin(math.radians(ang)) * lung * t

    # agrifoglio con bacche
    for bi, t, grad, lung_f, sd in ((4, .60, 60, 92, 3), (0, .58, 20, 88, 4), (2, .84, 40, 84, 5), (3, .42, 70, 80, 6)):
        x, y = pos(bi, t)
        for k, g in enumerate((grad, grad - 70)):
            ag = agrifoglio(lung_f, seed=sd + k)
            agS = ag.resize((ag.size[0] * S, ag.size[1] * S), Image.LANCZOS)
            incolla(im, agS, (x + 30) * S, (y - 6) * S, g)
        bacche(im, x * S, y * S + 6 * S, S, r=10, n=4, seed=sd + 7)
    # palline appoggiate tra i rami
    for bi, t, r, base, metallo, mot in ((2, .60, 38, (176, 14, 32), False, motivo_fascia((250, 224, 150), None)),
                                        (3, .70, 32, (240, 190, 70), True, motivo_losanghe((255, 236, 170))),
                                        (1, .78, 30, (22, 104, 74), False, motivo_puntini((255, 244, 210), 7))):
        x, y = pos(bi, t)
        sp = sfera(r * S, base, metallo=metallo, motivo=mot)
        incolla(im, sp, x * S, y * S + 8 * S)
    out = im.resize((W, H), Image.LANCZOS)
    out.save(os.path.join(USCITA, "ramo.webp"), quality=90, method=6)
    print("ramo", out.size, os.path.getsize(os.path.join(USCITA, "ramo.webp")) // 1024, "KB")


# =====================================================================
#   PUPAZZI DI NEVE
# =====================================================================
class Tela:
    """accumulatore RGBA (alfa premoltiplicata) per comporre i pezzi"""
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.rgb = np.zeros((H, W, 3))
        self.a = np.zeros((H, W))

    def sopra(self, rgb, a):
        self.rgb = rgb * a[..., None] + self.rgb * (1 - a[..., None])
        self.a = a + self.a * (1 - a)

    def immagine(self):
        al = np.maximum(self.a, 1e-4)[..., None]
        out = np.dstack([np.clip(self.rgb / al, 0, 255), self.a * 255]).astype(np.uint8)
        return Image.fromarray(out, "RGBA")


def maschera_pil(W, H, disegna, ss=3):
    im = Image.new("L", (W * ss, H * ss), 0)
    disegna(ImageDraw.Draw(im), ss)
    return np.asarray(im.resize((W, H), Image.LANCZOS), dtype=float) / 255


def ombreggia(mask, colmap, sigma=7, k=26, spec=0.45, forma=60, rugosita=None):
    h = ndi.gaussian_filter(mask, sigma)
    if rugosita is not None:
        h = h + rugosita
    gy, gx = np.gradient(ndi.gaussian_filter(h, 1.0))
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(h)
    nl = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    nx, ny, nz = nx / nl, ny / nl, nz / nl
    L = norm3([-0.5, -0.6, 0.62])
    diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    Hh = norm3(L + np.array([0, 0, 1.0]))
    sp = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1) ** forma * spec
    rgb = colmap * (0.30 + 0.85 * diff)[..., None] + 255 * sp[..., None]
    return np.clip(rgb, 0, 255), mask


def sfera_neve(W, H, cx, cy, r, seed):
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    nx, ny = (xx - cx) / r, (yy - cy) / r
    rr = np.sqrt(nx ** 2 + ny ** 2)
    al = np.clip((1 - rr) * r + 0.5, 0, 1)
    nz = np.sqrt(np.clip(1 - rr ** 2, 0, 1))
    bump = fractal((H, W), [5, 2.2, 1.0], [1, .7, .5], seed) * 0.05
    gy, gx = np.gradient(bump)
    nxx, nyy, nzz = nx - gx * 6, ny - gy * 6, nz
    nn = np.sqrt(nxx ** 2 + nyy ** 2 + nzz ** 2) + 1e-6
    nxx, nyy, nzz = nxx / nn, nyy / nn, nzz / nn
    L = norm3([-0.5, -0.6, 0.62])
    diff = np.clip(nxx * L[0] + nyy * L[1] + nzz * L[2], 0, 1)
    luce = np.array([252.0, 252.0, 255.0])
    ombra = np.array([150.0, 172.0, 220.0])
    t = diff ** 0.8
    rgb = ombra[None, None, :] * (1 - t[..., None]) + luce[None, None, :] * t[..., None]
    rim = (1 - nz) ** 2.2
    rgb += np.array([-10.0, 6.0, 22.0]) * rim[..., None] * 0.6
    sp = np.random.default_rng(seed + 5).random((H, W)) > 0.9965
    rgb += 70 * (ndi.gaussian_filter(sp.astype(float), .7) * 3)[..., None]
    return np.clip(rgb, 0, 255), al


def pezzo_sfera(tela, W, H, cx, cy, r, colore, lucido=1.0):
    s_ = sfera(r, colore, lucido=lucido)
    a = np.array(s_, dtype=float)
    ox, oy = int(cx - s_.size[0] // 2), int(cy - s_.size[1] // 2)
    lr = np.zeros((H, W, 3))
    la = np.zeros((H, W))
    lr[oy:oy + s_.size[1], ox:ox + s_.size[0]] = a[..., :3]
    la[oy:oy + s_.size[1], ox:ox + s_.size[0]] = a[..., 3] / 255
    tela.sopra(lr, la)


def crea_pupazzo(nome, stile):
    W, H = 700, 900
    tela = Tela(W, H)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)

    # cumulo di neve e ombra a terra
    mound = maschera_pil(W, H, lambda d, s: d.ellipse([60 * s, 800 * s, 640 * s, 905 * s], fill=255))
    mound = ndi.gaussian_filter(mound, 14)
    sfum = np.clip((yy - 800) / 110.0, 0, 1)
    colm = np.array([248.0, 251.0, 255.0])[None, None, :] * (1 - 0.18 * sfum)[..., None] + np.array([190.0, 208.0, 240.0])[None, None, :] * (0.18 * sfum)[..., None]
    tela.sopra(colm, mound * 0.97)
    ombra = ndi.gaussian_filter(maschera_pil(W, H, lambda d, s: d.ellipse([170 * s, 820 * s, 560 * s, 880 * s], fill=255)), 14) * 0.45
    tela.sopra(np.ones((H, W, 3)) * np.array([90.0, 110.0, 160.0]), ombra)

    # tre sfere di neve
    for cx, cy, r, sd in ((350, 712, 152, 1), (350, 525, 114, 2), (350, 372, 84, 3)):
        rgb, al = sfera_neve(W, H, cx, cy, r, sd)
        tela.sopra(rgb, al)
        ao = ndi.gaussian_filter(((np.abs(np.hypot(xx - cx, yy - cy) - r) < 3) & (yy < cy - r * 0.2)).astype(float), 4) * 0.30
        tela.sopra(np.ones((H, W, 3)) * np.array([120.0, 140.0, 190.0]), ao * tela.a)

    # braccia (rametti)
    def ramo(d, s, pts, spess):
        d.line([(x * s, y * s) for x, y in pts], fill=255, width=int(spess * s), joint="curve")

    def braccia(d, s):
        ramo(d, s, [(268, 500), (190, 470), (112, 408)], 13)
        ramo(d, s, [(150, 440), (128, 470)], 8)
        ramo(d, s, [(135, 424), (92, 408)], 7)
        ramo(d, s, [(432, 500), (520, 478), (600, 420)], 13)
        ramo(d, s, [(560, 448), (590, 478)], 8)
        ramo(d, s, [(572, 436), (620, 440)], 7)

    bracc = maschera_pil(W, H, braccia)
    leg = np.ones((H, W, 3)) * np.array([104.0, 70.0, 42.0])
    leg *= (1 + 0.25 * fractal((H, W), [1.5, .8], [1, 1], 9))[..., None]
    tela.sopra(*ombreggia(bracc, leg, sigma=3, k=14, spec=0.15))

    # bottoni di carbone
    for by in (480, 530, 580):
        pezzo_sfera(tela, W, H, 350, by, 11, (28, 26, 30), 0.9)

    # sciarpa
    if stile == "cilindro":
        c1, c2 = np.array([186.0, 24.0, 40.0]), np.array([246.0, 240.0, 228.0])
    else:
        c1, c2 = np.array([26.0, 112.0, 80.0]), np.array([246.0, 240.0, 228.0])

    def sciarpa(d, s):
        d.pieslice([232 * s, 408 * s, 468 * s, 500 * s], 0, 180, fill=255)
        d.rectangle([248 * s, 452 * s, 452 * s, 458 * s], fill=255)

    sc = maschera_pil(W, H, sciarpa)
    coda = maschera_pil(W, H, lambda d, s: d.polygon([(398 * s, 470 * s), (448 * s, 462 * s), (470 * s, 590 * s), (418 * s, 600 * s)], fill=255))
    sc = np.clip(sc + coda, 0, 1)
    strisce = (np.sin((xx * 0.5 + yy * 0.05) / 4.2) > 0.1).astype(float)
    strisce_c = (np.sin((yy * 0.5) / 4.2) > 0.1).astype(float)
    mix = np.where((coda > 0.5)[..., None], (c1 * strisce_c[..., None] + c2 * (1 - strisce_c[..., None])), (c1 * strisce[..., None] + c2 * (1 - strisce[..., None])))
    maglia = 0.012 * np.sin(xx * 1.4) * np.sin(yy * 1.4)
    tela.sopra(*ombreggia(sc, mix, sigma=5, k=22, spec=0.1, rugosita=maglia))

    # naso a carota
    nas = maschera_pil(W, H, lambda d, s: d.polygon([(338 * s, 366 * s), (338 * s, 386 * s), (452 * s, 394 * s)], fill=255))
    carota = np.ones((H, W, 3)) * np.array([250.0, 120.0, 24.0])
    carota *= (1 - 0.14 * (np.sin(xx / 5.0) > 0.4))[..., None]
    tela.sopra(*ombreggia(nas, carota, sigma=3.2, k=30, spec=0.25))

    # occhi, sorriso, guance
    for ex, ey in ((314, 346), (386, 346)):
        pezzo_sfera(tela, W, H, ex, ey, 10, (22, 20, 24), 1.0)
    for i in range(7):
        t = i / 6
        pezzo_sfera(tela, W, H, 350 + (t - 0.5) * 100, 404 + 22 * math.sin(math.pi * t) - 2, 5.5, (30, 28, 32), 0.8)
    for gx_ in (292, 408):
        g = ndi.gaussian_filter(maschera_pil(W, H, lambda d, s: d.ellipse([(gx_ - 18) * s, 372 * s, (gx_ + 18) * s, 394 * s], fill=255)), 7) * 0.45
        tela.sopra(np.ones((H, W, 3)) * np.array([255.0, 120.0, 130.0]), g)

    # cappello
    if stile == "cilindro":
        falda = maschera_pil(W, H, lambda d, s: d.ellipse([250 * s, 292 * s, 450 * s, 332 * s], fill=255))

        def corona_(d, s):
            d.rectangle([278 * s, 190 * s, 422 * s, 312 * s], fill=255)
            d.ellipse([278 * s, 178 * s, 422 * s, 204 * s], fill=255)
            d.ellipse([278 * s, 298 * s, 422 * s, 326 * s], fill=255)

        corona = maschera_pil(W, H, corona_)
        nero = np.ones((H, W, 3)) * np.array([30.0, 28.0, 34.0])
        tela.sopra(*ombreggia(falda, nero, sigma=4, k=18, spec=0.5, forma=40))
        tela.sopra(*ombreggia(corona, nero, sigma=9, k=16, spec=0.55, forma=40))
        fascia = maschera_pil(W, H, lambda d, s: d.rectangle([278 * s, 270 * s, 422 * s, 298 * s], fill=255)) * (corona > 0.5)
        tela.sopra(*ombreggia(fascia, np.ones((H, W, 3)) * np.array([176.0, 24.0, 40.0]), sigma=3, k=14, spec=0.3))
        for bx in (396, 408):
            pezzo_sfera(tela, W, H, bx, 282, 7, (200, 18, 34), 1.0)
    else:
        def cupola_(d, s):
            d.pieslice([262 * s, 270 * s, 438 * s, 400 * s], 180, 360, fill=255)
            d.rectangle([262 * s, 330 * s, 438 * s, 352 * s], fill=255)

        cupola = np.clip(maschera_pil(W, H, cupola_), 0, 1) * (yy < 356)
        righe = (np.sin((xx - 350) / 5.5) > -0.15).astype(float)
        cl = np.array([176.0, 24.0, 40.0])
        bi = np.array([246.0, 240.0, 228.0])
        colm = cl[None, None, :] * righe[..., None] + bi[None, None, :] * (1 - righe[..., None])
        colm = np.where((yy > 328)[..., None], bi[None, None, :], colm)
        maglia2 = 0.012 * np.sin(xx * 1.3) * np.sin(yy * 1.3)
        tela.sopra(*ombreggia(cupola, colm, sigma=7, k=22, spec=0.1, rugosita=maglia2))
        pr, pa = sfera_neve(W, H, 350, 262, 26, 21)
        tela.sopra(pr, pa)

    return tela.immagine().resize((W // 2, H // 2), Image.LANCZOS)


def crea_pupazzi():
    for nome, stile in (("pupazzo-sx.webp", "cilindro"), ("pupazzo-dx.webp", "cuffia")):
        im = crea_pupazzo(nome, stile)
        im = im.crop(im.getbbox())
        im.save(os.path.join(USCITA, nome), quality=92, method=6)
        print(nome, im.size, os.path.getsize(os.path.join(USCITA, nome)) // 1024, "KB")


if __name__ == "__main__":
    import sys
    cosa = sys.argv[1:] or ["palline", "ghirlanda", "ramo", "pupazzi"]
    if "palline" in cosa:
        crea_palline()
    if "ghirlanda" in cosa:
        crea_ghirlanda()
    if "ramo" in cosa:
        crea_ramo()
    if "pupazzi" in cosa:
        crea_pupazzi()
