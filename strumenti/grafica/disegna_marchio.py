"""Draws Keplario's cover image (icone/anteprima.jpg, 1200×630) and app icons (icone/icona*.svg/png).

The mark is Kepler's second law, computed, not sketched: an orbit with e = 0.62 drawn as dots at equal time steps
(close together at apocentre, far apart at pericentre), the central body at the focus, and two sectors swept in the
same time (1/12 of the period), one at pericentre and one at apocentre, with equal areas.

Needs Playwright with Chromium (to turn SVG with the B612 font into PNG) and Pillow.
    python3 strumenti/grafica/disegna_marchio.py
"""
import math, pathlib, random
from playwright.sync_api import sync_playwright
from PIL import Image

RADICE = pathlib.Path(__file__).resolve().parents[2]
ICONE = RADICE / 'icone'
E = 0.62
CY, MG, AM, TX, TX2, BG = '#35d4f2', '#ff62d4', '#ffb224', '#e6eaee', '#9aa5b1', '#05070a'


def kepler_E(M, e):
    x = M if e < 0.8 else math.pi
    for _ in range(50):
        x -= (x - e * math.sin(x) - M) / (1 - e * math.cos(x))
    return x


def orbita(cx, cy, a, rot, e=E):
    """Points of the orbit as a function of mean anomaly; the focus (central body) and helpers, in pixels."""
    b, c = a * math.sqrt(1 - e * e), a * e
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    def P(M):
        Ea = kepler_E(M, e)
        x, y = a * math.cos(Ea), b * math.sin(Ea)          # centred on the ellipse centre, pericentre towards +x
        return cx + x * cr - y * sr, cy + x * sr + y * cr
    fx, fy = cx + c * cr, cy + c * sr                     # focus near the pericentre
    return P, (fx, fy), b


def settore(P, F, M0, M1, n=60):
    pts = [P(M0 + (M1 - M0) * k / n) for k in range(n + 1)]
    return 'M%.1f %.1f ' % F + ' '.join('L%.1f %.1f' % p for p in pts) + ' Z'


def area(P, F, M0, M1, n=4000):
    s, prev = 0.0, P(M0)
    for k in range(1, n + 1):
        q = P(M0 + (M1 - M0) * k / n)
        s += 0.5 * abs((prev[0] - F[0]) * (q[1] - F[1]) - (q[0] - F[0]) * (prev[1] - F[1])); prev = q
    return s


def marchio(cx, cy, a, rot, scala=1.0, punti=48, etichette=False):
    P, F, b = orbita(cx, cy, a, rot)
    dM = 2 * math.pi / 12
    s = []
    s.append('<path d="%s" fill="%s" fill-opacity=".26" stroke="%s" stroke-width="%.1f"/>' % (settore(P, F, -dM / 2, dM / 2), CY, CY, 1.6 * scala))
    s.append('<path d="%s" fill="%s" fill-opacity=".26" stroke="%s" stroke-width="%.1f"/>' % (settore(P, F, math.pi - dM / 2, math.pi + dM / 2), MG, MG, 1.6 * scala))
    ell = ' '.join(('M' if k == 0 else 'L') + '%.1f %.1f' % P(2 * math.pi * k / 400) for k in range(401))
    s.append('<path d="%s" fill="none" stroke="%s" stroke-opacity=".35" stroke-width="%.1f"/>' % (ell, TX, 1.2 * scala))
    for k in range(punti):                                 # equal time steps
        x, y = P(2 * math.pi * k / punti)
        s.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x, y, 3.2 * scala, TX))
    s.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity=".18"/>' % (F[0], F[1], 26 * scala, AM))
    s.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (F[0], F[1], 11 * scala, AM))
    if etichette:
        A1, A2 = area(P, F, -dM / 2, dM / 2), area(P, F, math.pi - dM / 2, math.pi + dM / 2)
        assert abs(A1 / A2 - 1) < 1e-3, (A1, A2)
        p1, p2 = P(0), P(math.pi)
        s.append('<text x="%.0f" y="%.0f" class="m" fill="%s">A₁</text>' % (p1[0] + 16, p1[1] + 6, CY))
        s.append('<text x="%.0f" y="%.0f" class="m" fill="%s" text-anchor="end">A₂</text>' % (p2[0] - 16, p2[1] + 6, MG))
    return '\n'.join(s)


def font_css(relativo=False):
    # in the saved SVG the fonts are the site's own files; for drawing they are embedded, so the browser does not need to read files
    import base64
    u = (lambda n: '../fonts/' + n) if relativo else (lambda n: 'data:font/woff2;base64,' + base64.b64encode((RADICE / 'fonts' / n).read_bytes()).decode())
    return ('@font-face{font-family:B612;font-weight:700;src:url(%s)}'
            '@font-face{font-family:B612;font-weight:400;src:url(%s)}'
            '@font-face{font-family:B612M;src:url(%s)}' % (u('b612-latin-700-normal.woff2'), u('b612-latin-400-normal.woff2'), u('b612-mono-latin-400-normal.woff2')))


def copertina(relativo=False):
    W, H = 1200, 630
    rnd = random.Random(7)
    stelle = ''.join('<circle cx="%.1f" cy="%.1f" r="%.2f" fill="#fff" opacity="%.2f"/>' % (rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.4, 1.3), rnd.uniform(0.15, 0.6)) for _ in range(140))
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">
<style>%s .t{font-family:B612;font-weight:700} .r{font-family:B612} .m{font-family:B612M;font-size:20px}</style>
<rect width="%d" height="%d" fill="%s"/>%s
<g>%s</g>
<text x="76" y="262" class="t" font-size="94" letter-spacing="7" fill="%s">KEPLARIO</text>
<rect x="82" y="292" width="88" height="4" fill="%s"/>
<text x="80" y="348" class="r" font-size="34" fill="%s">il planetario delle orbite</text>
<text x="80" y="390" class="r" font-size="25" fill="%s">the orbit planetarium</text>
<text x="80" y="548" class="m" fill="%s">satelliti · sonde · missioni — scala e tempo reali</text>
<text x="80" y="578" class="m" fill="#6a7582">aree uguali in tempi uguali (Keplero, 1609)</text>
</svg>''' % (W, H, W, H, font_css(relativo), W, H, BG, stelle, marchio(935, 318, 225, -16, 1.0, 48, True), TX, CY, TX, TX2, TX2)


def icona(maschera=False, piccola=False):
    k = 0.78 if maschera else 0.92                      # maskable icons keep the drawing inside the central 80 %
    if piccola:                                         # 32 px: no time dots, a thicker orbit
        return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
<rect width="512" height="512" fill="#080a0d"/>%s</svg>''' % marchio(256, 256, 226, -16, 6.0, 0).replace('stroke-opacity=".35"', 'stroke-opacity=".9"')
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
<rect width="512" height="512" fill="#080a0d"/>
<g transform="translate(256 256) scale(%.3f) translate(-256 -256)">%s</g>
</svg>''' % (k, marchio(256, 256, 214, -16, 2.6, 16))


def rendi(svg, png, w, h):
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': w, 'height': h})
        pg.set_content('<html><body style="margin:0;background:#000">%s</body></html>' % svg.replace('width="512" height="512"', 'width="%d" height="%d"' % (w, h)))
        pg.evaluate('document.fonts.ready.then(()=>1)'); pg.wait_for_timeout(300)
        pg.screenshot(path=str(png), clip={'x': 0, 'y': 0, 'width': w, 'height': h})
        b.close()


def main():
    c = copertina()
    (ICONE / 'copertina.svg').write_text(copertina(True), encoding='utf-8')   # sorgente modificabile, con i caratteri del sito
    tmp = ICONE / '_copertina.png'
    rendi(c, tmp, 1200, 630)
    Image.open(tmp).convert('RGB').save(ICONE / 'anteprima.jpg', quality=90, optimize=True, progressive=True)
    tmp.unlink()
    i, im = icona(), icona(True)
    (ICONE / 'icona.svg').write_text(i, encoding='utf-8')
    for n in (180, 192, 512):
        rendi(i, ICONE / ('icona-%d.png' % n), n, n)
    rendi(icona(piccola=True), ICONE / 'icona-32.png', 32, 32)
    rendi(im, ICONE / 'icona-maschera-512.png', 512, 512)
    print('Scritti icone/anteprima.jpg, copertina.svg, icona.svg e le icone PNG.')


if __name__ == '__main__':
    main()
