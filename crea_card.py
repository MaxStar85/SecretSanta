"""
Crea la 'card di partecipazione' di ognuno (anteprima del link su WhatsApp):
assets/card-<nome>.jpg  (1200 x 630).
Sulla card c'e' solo il ritratto di chi riceve il link: NON rivela nessun abbinamento.
Si rilancia solo se si cambia grafica:   python crea_card.py
"""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage as ndi

CARTELLA = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(CARTELLA, "assets")
F = os.path.join(CARTELLA, "foto")
W, H = 1200, 630
NOMI = ["Massimo", "Cristiana", "Giorgia", "Lorenzo", "Luca", "Laura", "Ivo", "Maria Elena", "Francesca"]
FONT = r"C:\Windows\Fonts"


def slug(n):
    return n.lower().replace(" ", "-")


def font(nome, size):
    return ImageFont.truetype(os.path.join(FONT, nome), size)


def apri(nome):
    return Image.open(os.path.join(A, nome)).convert("RGBA")


def sfondo():
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    t = yy / H
    top = np.array([14.0, 62.0, 48.0])
    bot = np.array([6.0, 30.0, 24.0])
    col = top[None, None, :] * (1 - t[..., None]) + bot[None, None, :] * t[..., None]
    # bagliore caldo in alto al centro e rosso scuro in basso
    g = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - 40) / 260) ** 2))
    col += np.array([60.0, 55.0, 25.0])[None, None, :] * g[..., None] * 0.55
    r = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - H) / 200) ** 2))
    col += np.array([40.0, 8.0, 14.0])[None, None, :] * r[..., None]
    vig = 1 - 0.30 * np.clip(np.hypot((xx - W / 2) / (W * .62), (yy - H / 2) / (H * .75)) - .45, 0, 1)
    col *= vig[..., None]
    im = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # neve sfocata
    rng = np.random.default_rng(4)
    nv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(nv)
    for _ in range(70):
        x, y, r_ = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 7)
        d.ellipse([x - r_, y - r_, x + r_, y + r_], fill=(255, 255, 255, int(rng.uniform(50, 150))))
    im.alpha_composite(nv.filter(ImageFilter.GaussianBlur(1.6)))
    return im


def testo_spaziato(d, xy, testo, fnt, fill, tracking):
    x, y = xy
    for ch in testo:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + tracking


def larghezza_spaziata(d, testo, fnt, tracking):
    return sum(d.textlength(c, font=fnt) + tracking for c in testo) - tracking


def testo_oro(im, centro, testo, fnt, tracking=0, glow=True):
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    w = int(larghezza_spaziata(d0, testo, fnt, tracking)) + 40
    h = int(fnt.size * 1.6)
    m = Image.new("L", (w, h), 0)
    testo_spaziato(ImageDraw.Draw(m), (20, int(fnt.size * 0.18)), testo, fnt, 255, tracking)
    a = np.asarray(m, dtype=float) / 255
    yy = np.linspace(0, 1, h)[:, None]
    c1, c2, c3 = np.array([255.0, 238.0, 190.0]), np.array([236.0, 198.0, 118.0]), np.array([170.0, 124.0, 44.0])
    col = np.where(yy < 0.55, c1 + (c2 - c1) * (yy / 0.55), c2 + (c3 - c2) * ((yy - 0.55) / 0.45))
    rgba = np.dstack([np.repeat(col[:, None, :], w, 1), a * 255]).astype(np.uint8)
    t = Image.fromarray(rgba, "RGBA")
    x0, y0 = int(centro[0] - w / 2), int(centro[1] - h / 2)
    if glow:
        gl = Image.new("RGBA", (w, h), (255, 220, 130, 0))
        gl.putalpha(m.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.55)))
        im.alpha_composite(gl, (x0, y0))
    im.alpha_composite(t, (x0, y0))


def testo_semplice(im, centro, parti, ombra=True):
    """parti = [(testo, font, colore)] sulla stessa riga, centrate"""
    d = ImageDraw.Draw(im)
    tot = sum(d.textlength(t, font=f) for t, f, c in parti)
    x = centro[0] - tot / 2
    for t, f, c in parti:
        if ombra:
            d.text((x + 2, centro[1] + 3), t, font=f, fill=(0, 0, 0, 150), anchor="ls")
        d.text((x, centro[1]), t, font=f, fill=c, anchor="ls")
        x += d.textlength(t, font=f)


def ghirlanda(im):
    g = apri("ghirlanda.webp")
    meta = json.loads(open(os.path.join(A, "ghirlanda.js"), encoding="utf-8").read().split("=", 1)[1].rstrip(";\n "))
    gh = 150
    tw = int(gh * g.size[0] / g.size[1])
    gs = g.resize((tw, gh), Image.LANCZOS)
    off = int((W / 2) % tw)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(-1, W // tw + 2):
        x0 = off + i * tw
        lay.alpha_composite(gs, (x0, 0)) if x0 >= 0 else lay.paste(gs, (x0, 0), gs)
        for l in meta["lampadine"]:
            cx, cy = x0 + l["x"] * tw, l["y"] * gh
            r = int(gh * 0.30)
            c = tuple(int(l["c"][k:k + 2], 16) for k in (1, 3, 5))
            gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c + (170,))
    glow = glow.filter(ImageFilter.GaussianBlur(11))
    im.alpha_composite(glow)
    im.alpha_composite(lay)
    # palline alle giunture
    nomi = ["rossa", "oro", "verde", "perla"]
    n = 0
    for i in range(-1, W // tw + 2):
        x = off + i * tw
        if x < 40 or x > W - 40:
            continue
        sp = apri("palla-%s.webp" % nomi[n % 4])
        w = int(gh * 0.60)
        sp = sp.resize((w, int(w * sp.size[1] / sp.size[0])), Image.LANCZOS)
        im.alpha_composite(sp, (int(x - w / 2), int(meta["y0"] * gh - 8)))
        n += 1


def suolo_e_pupazzi(im):
    # pupazzi (statici: braccia alzate leggermente)
    for lato, x_c in (("sx", 78), ("dx", W - 78)):
        liv = {k: apri("pupazzo-%s-%s.webp" % (lato, k)) for k in ("bsx", "bdx", "corpo", "occhi", "coda")}
        liv["bsx"] = liv["bsx"].rotate(-9, resample=Image.BICUBIC)
        liv["bdx"] = liv["bdx"].rotate(9, resample=Image.BICUBIC)
        w0, h0 = liv["corpo"].size
        hh = 190
        ww = int(hh * w0 / h0)
        fig = Image.new("RGBA", (w0, h0), (0, 0, 0, 0))
        for k in ("bsx", "bdx", "corpo", "occhi", "coda"):
            fig.alpha_composite(liv[k])
        fig = fig.resize((ww, hh), Image.LANCZOS)
        im.alpha_composite(fig, (int(x_c - ww / 2), H - hh - 16))
    s = apri("suolo.webp")
    sh = 82
    sw = int(sh * s.size[0] / s.size[1])
    ss = s.resize((sw, sh), Image.LANCZOS)
    for x in range(0, W, sw):
        im.alpha_composite(ss, (x, H - sh))


def ritratto(im, nome, centro, d):
    foto = Image.open(os.path.join(F, slug(nome) + ".jpg")).convert("RGB").resize((d, d), Image.LANCZOS)
    S = 3
    m = Image.new("L", (d * S, d * S), 0)
    ImageDraw.Draw(m).ellipse([0, 0, d * S - 1, d * S - 1], fill=255)
    m = m.resize((d, d), Image.LANCZOS)
    # anello dorato (gradiente conico) + alone
    R = d // 2 + 12
    yy, xx = np.mgrid[0:2 * R, 0:2 * R].astype(float)
    ang = np.arctan2(yy - R, xx - R)
    t = (np.sin(ang * 2 + 0.5) * 0.5 + 0.5)
    c_lo, c_hi = np.array([169.0, 124.0, 44.0]), np.array([255.0, 238.0, 190.0])
    col = c_lo[None, None, :] * (1 - t[..., None]) + c_hi[None, None, :] * t[..., None]
    rr = np.hypot(xx - R, yy - R)
    a = np.clip(R - rr, 0, 1)
    ring = Image.fromarray(np.dstack([col, a * 255]).astype(np.uint8), "RGBA")
    halo = Image.new("RGBA", (2 * R + 80, 2 * R + 80), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse([40, 40, 2 * R + 40, 2 * R + 40], fill=(255, 210, 120, 120))
    halo = halo.filter(ImageFilter.GaussianBlur(20))
    sh = Image.new("RGBA", halo.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([40, 52, 2 * R + 40, 2 * R + 52], fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    cx, cy = centro
    im.alpha_composite(sh, (cx - R - 40, cy - R - 40))
    im.alpha_composite(halo, (cx - R - 40, cy - R - 40))
    im.alpha_composite(ring, (cx - R, cy - R))
    im.paste(foto, (cx - d // 2, cy - d // 2), m)


def busta(im, centro, larg):
    b = apri("busta.webp")
    sc = larg / b.size[0]
    bw, bh = int(b.size[0] * sc), int(b.size[1] * sc)
    b = b.resize((bw, bh), Image.LANCZOS)
    cx, cy = centro
    x0, y0 = int(cx - bw / 2), int(cy - bh / 2)
    sh = Image.new("RGBA", (bw + 120, bh + 120), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([60, 78, bw + 60, bh + 70], radius=20, fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    im.alpha_composite(sh, (x0 - 60, y0 - 60))
    im.alpha_composite(b, (x0, y0))
    # ceralacca sulla punta del lembo (500, 456 su 1000 x 740)
    c = apri("cera.webp")
    cw = int(150 / 320 * bw)
    c = c.resize((cw, int(cw * c.size[1] / c.size[0])), Image.LANCZOS)
    px, py = x0 + 500 * sc, y0 + 456 * sc
    im.alpha_composite(c, (int(px - 0.5 * cw), int(py - 0.476 * c.size[1])))


def crea(nome):
    im = sfondo()
    ghirlanda(im)
    suolo_e_pupazzi(im)
    testo_oro(im, (W / 2, 166), "NATALE IN FAMIGLIA", font("pala.ttf", 23), tracking=9, glow=False)
    testo_oro(im, (W / 2, 232), "Secret Santa", font("palab.ttf", 76), tracking=3)
    ritratto(im, nome, (350, 380), 190)
    busta(im, (790, 380), 330)
    testo_semplice(im, (W / 2, 536), [(nome + ", ", font("georgiai.ttf", 40), (255, 246, 222, 255)),
                                       ("c'è una busta per te", font("georgiai.ttf", 40), (240, 205, 128, 255))])
    out = os.path.join(A, "card-%s.jpg" % slug(nome))
    im.convert("RGB").save(out, quality=88, optimize=True)
    print(os.path.basename(out), os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    import sys
    for n in (sys.argv[1:] or NOMI):
        crea(n)
