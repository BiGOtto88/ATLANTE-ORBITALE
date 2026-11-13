#!/usr/bin/env python3
"""Prova dei disturbi: ogni coppia mostrata dalla pagina viene ricalcolata a parte, in Python, con le formule scritte da capo;
il campo magnetico è confrontato con la libreria ppigrf (IGRF-14), l'ombra con un'integrazione numerica del disco solare.
Controlla anche il riquadro «Lancio reale» della pagina Percorso.

Uso: python3 strumenti/prove/prova_disturbi.py . /tmp/schermate      (servono Playwright, numpy e ppigrf)"""
import datetime, json, math, subprocess, sys, time, pathlib
import numpy as np, ppigrf
from playwright.sync_api import sync_playwright

SITO = pathlib.Path(sys.argv[1]).resolve(); OUT = pathlib.Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
URL = 'http://localhost:8783/'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8783', '--bind', '127.0.0.1'], cwd=SITO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
RE, AU, C, WE = 6378.137, 149597870.7, 299792458.0, 7.2921159e-5
ATM = {700: (3.614e-14, 88.667), 800: (1.170e-14, 124.64), 400: (3.725e-12, 58.515), 450: (1.585e-12, 60.828), 500: (6.967e-13, 63.822), 600: (1.454e-13, 71.835), 350: (9.518e-12, 53.298)}   # Vallado, tab. 8-4
R = {}
LEGGI = '''(n=>{ const a=atlante, k=a.sats.findIndex(s=>s.norad===n), sc=a.scModel({t:'sat',i:k}), e=a.env, T=a.TQ, v=x=>Array.from(x);
  return {env:{mu:e.mu,r:v(e.r),v:v(e.v),sun:v(e.sun),dSun:e.dSun,P:e.P,lit:e.lit,Pir:e.Pir,Pal:e.Pal,nad:v(e.nad),B:v(e.B),rho:e.rho,vr:v(e.vr),alt:e.alt},
    A:v(a.att.A), L:v(a.att.L), J:v(sc.J), Ip:v(sc.Ip), cd:sc.cd, m:v(sc.mdip), faces:sc.faces.map(f=>({n:f.n,A:f.A,r:f.r,rs:f.rs,rd:f.rd})),
    T:{gg:v(T.gg),drag:v(T.drag),srp:v(T.srp),srpE:v(T.srpE),mag:v(T.mag),fDrag:v(T.fDrag),fRad:v(T.fRad)}, ms:a.state().simMs, gmst:satellite.gstime(a.jdOf(a.state().simMs)), perr:a.pErr(), mode:a.att.mode, nome:a.sats[k].name}; })'''


def radiazione(facce, u, P):
    F = np.zeros(3); M = np.zeros(3)
    for f in facce:
        n = np.array(f['n'], float); c = n @ u
        if c <= 0: continue
        Fi = -P * f['A'] * c * ((1 - f['rs']) * u + (2 * f['rs'] * c + 2 / 3 * f['rd']) * n)
        F += Fi; M += np.cross(np.array(f['r'], float), Fi)
    return F, M


def ricalcola(d):
    e = d['env']; A = np.array(d['A']).reshape(3, 3); J = np.array(d['J']).reshape(3, 3); r = np.array(e['r']); rm = np.linalg.norm(r)
    c = A @ r / rm; gg = 3 * e['mu'] / rm ** 3 * np.cross(c, J @ c)
    vb = A @ np.array(e['vr']); vm = np.linalg.norm(vb); u = vb / vm; Fd = np.zeros(3); Md = np.zeros(3)
    for f in d['faces']:
        n = np.array(f['n'], float); cc = n @ u
        if cc <= 0 or e['rho'] <= 0: continue
        Fi = -0.5 * e['rho'] * d['cd'] * f['A'] * cc * vm * vm * u; Fd += Fi; Md += np.cross(np.array(f['r'], float), Fi)
    Fs, Ms = radiazione(d['faces'], A @ np.array(e['sun']), e['P']) if e['P'] > 0 else (np.zeros(3), np.zeros(3))
    Fe, Me = radiazione(d['faces'], A @ np.array(e['nad']), e['Pir'] + e['Pal'])
    mag = np.cross(np.array(d['m']), A @ np.array(e['B']))
    return dict(gg=gg, drag=Md, srp=Ms + Me, srpE=Me, mag=mag, fDrag=Fd, fRad=Fs + Fe)


def ambiente(d):
    """Campo magnetico, densità, pressioni ricalcolati a parte dalla sola posizione e dall'istante."""
    e = d['env']; r = np.array(e['r']); v = np.array(e['v']); rm = np.linalg.norm(r); g = d['gmst']; cg, sg = math.cos(g), math.sin(g)
    x, y, z = cg * r[0] + sg * r[1], -sg * r[0] + cg * r[1], r[2]
    th, ph = math.degrees(math.acos(z / rm)), math.degrees(math.atan2(y, x))
    quando = datetime.datetime.fromtimestamp(d['ms'] / 1000, datetime.timezone.utc).replace(tzinfo=None)
    Br, Bt, Bp = [float(np.ravel(q)[0]) for q in ppigrf.igrf_gc(rm, th, ph, quando)]
    t, f = math.radians(th), math.radians(ph)
    be = np.array([Br * math.sin(t) * math.cos(f) + Bt * math.cos(t) * math.cos(f) - Bp * math.sin(f), Br * math.sin(t) * math.sin(f) + Bt * math.cos(t) * math.sin(f) + Bp * math.cos(f), Br * math.cos(t) - Bt * math.sin(t)]) * 1e-9
    B = np.array([cg * be[0] - sg * be[1], sg * be[0] + cg * be[1], be[2]])
    h = rm - RE; base = max(k for k in ATM if k <= h) if h >= 350 else None
    rho = ATM[base][0] * math.exp(-(h - base) / ATM[base][1]) if base and h < 900 else None
    vr = (v - np.cross([0, 0, WE], r)) * 1000
    ps = 1361 / C * (AU / e['dSun']) ** 2; cospsi = max(0.0, float(r @ np.array(e['sun'])) / rm)
    return dict(B=B, rho=rho, vr=vr, P=ps * e['lit'], Pir=237 / C * (RE / rm) ** 2, Pal=0.30 * ps * (RE / rm) ** 2 * cospsi)


def frazione_sole(a, b, c, n=700):
    """Parte del disco solare (raggio angolare a) non coperta dal disco del corpo (raggio b) a distanza angolare c: conteggio su griglia."""
    xs = np.linspace(-a, a, n); X, Y = np.meshgrid(xs, xs); dentro = X * X + Y * Y <= a * a
    return float(np.sum(dentro & ((X - c) ** 2 + Y * Y > b * b)) / np.sum(dentro))


try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = br.new_context(viewport={'width': 1440, 'height': 900}, locale='it-IT'); err = []
        ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(URL) else r.abort())
        pg = ctx.new_page(); pg.on('pageerror', lambda e: err.append('pageerror: ' + str(e))); pg.on('console', lambda m: err.append(m.text) if m.type == 'error' else None)
        pg.goto(URL); pg.wait_for_function('window.atlante && atlante.state().N>0 && atlante.state().P>0 && Object.keys(atlante.lanci).length>0', timeout=90000)
        ev = pg.evaluate
        # ---- 1. coppie ricalcolate a parte, per più satelliti e più assetti
        peggio = 0; tabella = []
        for norad in (40697, 25544, 20580, 41866, 39634):
            ev('atlante.select(%d)' % norad); ev('atlante.setTab("disturbi")'); time.sleep(1.2)
            for modo in ('amN', 'amI', 'amF'):
                ev('atlante.setTab("assetto")'); pg.click('#' + modo); ev('atlante.setTab("disturbi")'); time.sleep(0.7)
                d = ev(LEGGI + '(%d)' % norad); mio = ricalcola(d)
                for k, val in mio.items():
                    pag = np.array(d['T'][k]); scala = max(np.linalg.norm(val), np.linalg.norm(pag))
                    if scala > 0: peggio = max(peggio, np.linalg.norm(val - pag) / scala)
                amb = ambiente(d); e = d['env']
                sB = np.linalg.norm(amb['B'] - np.array(e['B'])) / np.linalg.norm(amb['B']); sV = np.linalg.norm(amb['vr'] - np.array(e['vr'])) / np.linalg.norm(amb['vr'])
                sP = [abs(amb[k] - e[k]) / max(amb[k], 1e-30) for k in ('P', 'Pir', 'Pal') if amb[k] > 0]
                sR = abs(amb['rho'] - e['rho']) / amb['rho'] if amb['rho'] else 0
                assert sB < 1e-4 and sV < 1e-9 and all(q < 1e-3 for q in sP) and sR < 1e-9, (norad, modo, sB, sV, sP, sR)
                if modo == 'amN':
                    T = d['T']; n3 = lambda q: float(np.linalg.norm(q)); rm = n3(e['r'])
                    assert n3(T['gg']) > 0 and n3(np.array(T['fDrag'])) >= 0
                    if e['rho'] > 0: assert float(np.array(T['fDrag']) @ (np.array(d['A']).reshape(3, 3) @ np.array(e['vr']))) < 0      # la resistenza si oppone al moto
                    tabella.append('%-14s quota %6.0f km · GG %.2e · drag %.2e · radiazione %.2e (Terra %.2e) · magnetica %.2e N·m · |B| %6.0f nT · ρ %.1e · luce %.2f · GG max 45° %.2e'
                                   % (d['nome'][:14], e['alt'], n3(T['gg']), n3(T['drag']), n3(T['srp']), n3(T['srpE']), n3(T['mag']), n3(e['B']) * 1e9, e['rho'], e['lit'], 1.5 * e['mu'] / rm ** 3 * (d['Ip'][2] - d['Ip'][0])))
                    # gradiente con il corpo fuori asse dell'errore di puntamento: confronto con la formula ai piccoli angoli
                    th = math.radians(d['perr']); A = np.array(d['A']).reshape(3, 3); L = np.array(d['L']).reshape(3, 3)
                    ang = math.degrees(math.acos(max(-1, min(1, (np.trace(A @ L.T) - 1) / 2)))); assert abs(ang - d['perr']) < 1e-6, ang
        R['coppie: scarto massimo fra pagina e ricalcolo'] = '%.1e' % peggio; assert peggio < 1e-9
        R['valori in assetto nadir con 1° di errore'] = tabella
        ev('atlante.setTab("assetto")'); pg.click('#amN')
        # ---- 2. profilo lungo l'orbita: il gradiente non è più nullo
        ev('atlante.select(40697)'); ev('atlante.setTab("disturbi")'); time.sleep(2.0)
        R['massimi sull\'orbita (drag, GG, radiazione, magnetica)'] = ['%.2e' % x for x in ev('atlante.prof.max')]; assert ev('atlante.prof.max[1]') > 0
        R['testo ambiente'] = ev('document.getElementById("dEnv").textContent'); R['righe'] = ev('["dF0","dF1","dF2","dF3"].map(i=>document.getElementById(i).textContent)')
        pg.screenshot(path=str(OUT / '1-disturbi.png'))
        # con errore di puntamento nullo e tensore diagonale il gradiente torna a zero: è la fisica, non un difetto
        ev('atlante.setTab("assetto")'); pg.fill('#aPe', '0'); pg.dispatch_event('#aPe', 'change'); ev('atlante.setTab("disturbi")'); time.sleep(0.8)
        R['GG con errore di puntamento 0°'] = ev('Math.hypot(...atlante.TQ.gg)'); assert R['GG con errore di puntamento 0°'] < 1e-15
        ev('atlante.setTab("assetto")'); pg.fill('#aPe', '1'); pg.dispatch_event('#aPe', 'change')
        # ---- 3. ombra e penombra contro l'integrazione numerica
        casi = []
        for rm, ang_fuori in ((7000.0, 0.0), (7000.0, None), (42164.0, None), (384400.0, None)):
            d = AU; a = math.asin(695700 / d); b = math.asin(RE / rm)
            for c in ([b + 2 * a] if ang_fuori == 0.0 else [b - 1.5 * a, b - 0.6 * a, b, b + 0.5 * a, b + 0.95 * a]):
                dd = -rm * math.cos(c)                                   # r·ŝ per una separazione angolare c fra centro del corpo e Sole
                pag = ev('atlante.sunFraction(%r,%r,%r,%r)' % (rm, dd, d, RE)); mio = frazione_sole(a, b, c)
                casi.append((rm, round(math.degrees(c - b) / math.degrees(a), 2), round(pag, 4), round(mio, 4))); assert abs(pag - mio) < 4e-3, casi[-1]
        R['ombra: (raggio km, distanza dal bordo in raggi solari, pagina, integrazione)'] = casi
        # ---- 4. missione di progetto: il gradiente entra nel bilancio ADCS
        ev('atlante.goto("earth")'); time.sleep(0.4); pg.click('#btnNewDes'); time.sleep(1.2); ev('atlante.setTab("adcs")'); time.sleep(2.5)
        t = ev('document.getElementById("adcs").innerText'); R['ADCS, riga del gradiente'] = next((l for l in t.replace('\n\n', '\n').split('\n') if l.startswith('Gradiente')), '')
        R['ADCS, valori'] = [l for l in t.split('\n') if 'N·m' in l][:5]
        # ---- 5. riquadro «Lancio reale»
        def lancio(sel):
            ev(sel); ev('atlante.setTab("percorso")'); time.sleep(2.0); return ev('document.getElementById("tOut").innerText')
        t = lancio('atlante.select(25544)'); R['ISS'] = t[:430]; R['ISS sito usato'] = ev('JSON.stringify(atlante.SITE)'); pg.screenshot(path=str(OUT / '2-lancio-iss.png'))
        assert 'Bajkonur' in t and 'Proton-K' in t and '20 nov 1998' in t and ev('atlante.SITE.real')
        t = lancio('atlante.select(41866)'); R['GOES-16'] = t[:330]; assert 'Cape Canaveral' in t and 'Atlas V 541' in t
        stl = ev('atlante.sats.find(s=>/^STARLINK/.test(s.name)).norad'); t = lancio('atlante.select(%d)' % stl); R['Starlink'] = t[:330]
        qual = ev('atlante.sats.find(s=>/^YAOGAN/.test(s.name)).norad'); t = lancio('atlante.select(%d)' % qual); R['senza profilo'] = t[:330]
        t = lancio('atlante.probe("MRO")'); R['MRO'] = t[:330]; assert 'Atlas V 401' in t and 'aerofrenaggio' in t
        t = lancio('atlante.probe("JWST")'); R['JWST'] = t[:260]; assert 'Kourou' in t
        R['oggetti con sito reale'] = ev('(()=>{ let n=0, senza=new Set(); for(let i=0;i<atlante.sats.length;i++){ const r=atlante.realLaunch({t:"sat",i}); if(r&&r.code) n++; } return n; })()')
        R['sigle di sito senza coordinate'] = ev('(()=>{ const s=new Set(Object.values(atlante.lanci).map(x=>x[1])); atlante.select(25544); return [...s].filter(k=>!document.body||false).length; })()')
        pg.select_option('#tSite', 'kourou'); time.sleep(0.6); R['ISS da Kourou'] = ev('JSON.stringify(atlante.SITE)'); pg.select_option('#tSite', 'reale'); time.sleep(0.6); R['ISS di nuovo dal sito reale'] = ev('atlante.SITE.name')
        ev('atlante.goto("earth")'); time.sleep(0.3); t = lancio('atlante.probe("D1")'); R['missione di progetto'] = t[:200]
        tel = br.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale='it-IT')
        tel.route('**/*', lambda r: r.continue_() if r.request.url.startswith(URL) else r.abort()); p2 = tel.new_page(); p2.goto(URL)
        p2.wait_for_function('window.atlante && atlante.state().N>0', timeout=90000); p2.evaluate('atlante.select(40697)'); p2.evaluate('atlante.setTab("disturbi")'); time.sleep(2.5)
        p2.screenshot(path=str(OUT / '3-telefono-disturbi.png'), full_page=False); R['telefono'] = p2.evaluate('[document.documentElement.scrollWidth,innerWidth]')
        R['errori'] = err[:10]
        br.close()
finally:
    srv.terminate()
print(json.dumps(R, indent=1, ensure_ascii=False))
