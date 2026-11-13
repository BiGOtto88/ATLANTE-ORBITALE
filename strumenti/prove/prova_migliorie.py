#!/usr/bin/env python3
"""Prova delle migliorie: numeri della pagina Percorso contro valori calcolati a parte, leggi di controllo, margini ADCS."""
import json, math, subprocess, sys, time, pathlib
from playwright.sync_api import sync_playwright

SITO = pathlib.Path(sys.argv[1]).resolve(); OUT = pathlib.Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
URL = 'http://localhost:8781/'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8781', '--bind', '127.0.0.1'], cwd=SITO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
MU, RE, AU, MUS = 398600.4418, 6378.137, 149597870.7, 132712440041.279
R = {}
def vv(mu, r, a): return math.sqrt(mu * (2 / r - 1 / a))
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = br.new_context(viewport={'width': 1440, 'height': 900}, locale='it-IT'); err = []
        ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(URL) else r.abort())
        pg = ctx.new_page(); pg.on('pageerror', lambda e: err.append('pageerror: ' + str(e))); pg.on('console', lambda m: err.append(m.text) if m.type == 'error' else None)
        pg.goto(URL); pg.wait_for_function('window.atlante && atlante.state().N>0 && atlante.state().P>0', timeout=90000)
        ev = pg.evaluate
        # ---- 1. GTO + apogeo da Kourou e da Cape Canaveral
        r0, rg = RE + 200, 42164.17
        for nome, lat in (('kourou', 5.24), ('canaveral', 28.5)):
            t = ev('atlante.twoBurn(%r,%r,%r,%r,%r)' % (MU, r0, rg, rg, math.radians(lat)))
            at = (r0 + rg) / 2; vc, v1, v2, vf = math.sqrt(MU / r0), vv(MU, r0, at), vv(MU, rg, at), math.sqrt(MU / rg)
            tutto_apogeo = (v1 - vc) + math.sqrt(v2 * v2 + vf * vf - 2 * v2 * vf * math.cos(math.radians(lat)))
            R['GEO da ' + nome] = dict(d1=round(t['d1'], 4), d2=round(t['d2'], 4), tot=round(t['d1'] + t['d2'], 4), ripartizione_gradi=round(math.degrees(t['split']), 2), ore=round(t['tof'] / 3600, 3),
                                       atteso_d1_senza_piano=round(v1 - vc, 4), atteso_tot_tutto_all_apogeo=round(tutto_apogeo, 4))
            assert t['d1'] + t['d2'] <= tutto_apogeo + 1e-9 and t['d1'] + t['d2'] > tutto_apogeo - 0.05
        # ---- 2. Hohmann LEO 200 -> 700 km, senza cambio di piano
        t = ev('atlante.twoBurn(%r,%r,%r,%r,0)' % (MU, r0, RE + 700, RE + 700)); at = (r0 + RE + 700) / 2
        att = (vv(MU, r0, at) - math.sqrt(MU / r0)) + (math.sqrt(MU / (RE + 700)) - vv(MU, RE + 700, at))
        R['LEO 200 -> 700'] = dict(tot=round(t['d1'] + t['d2'], 5), atteso=round(att, 5)); assert abs(t['d1'] + t['d2'] - att) < 1e-9
        # discesa: da 200 km a un'orbita 150 x 180 km, e orbita a cavallo 150 x 400
        for rp, ra in ((RE + 150, RE + 180), (RE + 150, RE + 400)):
            t = ev('atlante.twoBurn(%r,%r,%r,%r,0)' % (MU, r0, rp, ra)); far = ra if r0 <= ra else rp; near = rp if far == ra else ra; at = (r0 + far) / 2
            att = abs(vv(MU, r0, at) - math.sqrt(MU / r0)) + abs(vv(MU, far, (rp + ra) / 2) - vv(MU, far, at))
            R['caso %d x %d' % (rp - RE, ra - RE)] = dict(tot=round(t['d1'] + t['d2'], 5), atteso=round(att, 5)); assert abs(t['d1'] + t['d2'] - att) < 1e-9
        # ---- 3. Marte
        h = ev('atlante.helioHohmann("mars")'); r2 = (MUS * (686.98 * 86400 / (2 * math.pi)) ** 2) ** (1 / 3); at = (AU + r2) / 2
        R['Marte'] = dict(vinf_partenza=round(h['vinf1'], 3), atteso1=round(vv(MUS, AU, at) - math.sqrt(MUS / AU), 3), vinf_arrivo=round(h['vinf2'], 3), atteso2=round(math.sqrt(MUS / r2) - vv(MUS, r2, at), 3),
                          giorni=round(h['tof'] / 86400, 1), sinodico_giorni=round(h['syn'] / 86400, 1), prossima_finestra=ev('new Date(atlante.state().simMs+%r*1000).toISOString().slice(0,10)' % h['wait']))
        assert abs(h['vinf1'] - (vv(MUS, AU, at) - math.sqrt(MUS / AU))) < 1e-6 and abs(h['tof'] / 86400 - 258.9) < 1.0 and abs(h['syn'] / 86400 - 779.9) < 1.0
        # la finestra: all'istante trovato Marte deve precedere la Terra dell'angolo di fase richiesto (verifica con le effemeridi vere)
        R['Marte']['fase_alla_finestra_gradi'] = ev('''(()=>{ const A=window.Astronomy, t=A.MakeTime(new Date(atlante.state().simMs+%r*1000)), e=A.HelioVector(A.Body.Earth,t), m=A.HelioVector(A.Body.Mars,t);
            const ec=v=>{ const c=Math.cos(23.4392911*Math.PI/180), s=Math.sin(23.4392911*Math.PI/180); return Math.atan2(v.y*c+v.z*s,v.x); }; return (((ec(m)-ec(e))*180/Math.PI)%%360+360)%%360; })()''' % h['wait'])
        R['Marte']['fase_richiesta_gradi'] = round(180 - 360 / 686.98 * h['tof'] / 86400, 2)
        p = ev('(()=>{ const P=atlante.transferPlan("mars",3396.19+300,3396.19+300,1.6); return {dv:P.dv,d:P.steps.map(s=>s[2])}; })()')
        d1 = math.sqrt(h['vinf1'] ** 2 + 2 * MU / r0) - math.sqrt(MU / r0); mum = 42828.374857; rp = 3396.19 + 300; d2 = math.sqrt(h['vinf2'] ** 2 + 2 * mum / rp) - math.sqrt(mum / rp)
        R['Marte, orbita 300 km'] = dict(iniezione=round(p['d'][1], 3), atteso=round(d1, 3), cattura=round(p['d'][2], 3), atteso_cattura=round(d2, 3)); assert abs(p['d'][1] - d1) < 1e-6 and abs(p['d'][2] - d2) < 1e-6
        # ---- 4. Luna, orbita polare a 100 km
        p = ev('(()=>{ const P=atlante.transferPlan("moon",1837.4,1837.4,1.57); return {d:P.steps.map(s=>s[2]),tof:P.tof}; })()')
        R['Luna 100 km'] = dict(iniezione=round(p['d'][1], 3), cattura=round(p['d'][2], 3), giorni=round(p['tof'] / 86400, 2)); assert 3.05 < p['d'][1] < 3.2 and 0.75 < p['d'][2] < 0.95
        # ---- 5. occasioni di lancio: all'istante trovato il sito sta nel piano dell'orbita della ISS
        ev('atlante.select(25544)'); time.sleep(1.5)
        R['ISS, sito nel piano'] = ev('''(()=>{ const a=atlante, k=a.sats.findIndex(s=>s.norad===25544), st=a.state(), rec=a.sats[k].rec, pv=satellite.sgp4(rec,(a.jdOf(st.simMs)-rec.jdsatepoch)*1440);
            const el=a.elementsFromState([pv.position.x,pv.position.y,pv.position.z],[pv.velocity.x,pv.velocity.y,pv.velocity.z],398600.4418), n=[Math.sin(el.i)*Math.sin(el.raan),-Math.sin(el.i)*Math.cos(el.raan),Math.cos(el.i)];
            a.SITE.lat=28.5; a.SITE.lon=-80.6;
            return a.planePasses(el,st.simMs).map(w=>{ const lst=satellite.gstime(a.jdOf(w[0]))+a.SITE.lon*Math.PI/180, la=a.SITE.lat*Math.PI/180, s=[Math.cos(la)*Math.cos(lst),Math.cos(la)*Math.sin(lst),Math.sin(la)];
              return {tra_ore:+((w[0]-st.simMs)/3.6e6).toFixed(2), azimut:+(w[1]*180/Math.PI).toFixed(1), fuori_piano_gradi:+(Math.asin(s[0]*n[0]+s[1]*n[1]+s[2]*n[2])*180/Math.PI).toFixed(3)}; }); })()''')
        assert all(abs(w['fuori_piano_gradi']) < 0.05 for w in R['ISS, sito nel piano']) and len(R['ISS, sito nel piano']) == 2
        ev('atlante.SITE.lat=5.24; atlante.SITE.lon=-52.77')
        # ---- 6. pagina Percorso per oggetti diversi
        def percorso(sel, attesa=2.0):
            ev(sel); ev('atlante.setTab("percorso")'); time.sleep(attesa); return ev('document.getElementById("tOut").innerText')
        t = percorso('atlante.select(25544)'); R['testo ISS'] = t[:520]; pg.screenshot(path=str(OUT / '1-percorso-iss.png'))
        R['schede'] = ev('[...document.querySelectorAll(".tabs button")].map(b=>b.textContent)')
        t = percorso('atlante.select(41866)', 3.0); R['testo GOES-16'] = [l for l in t.split('\n') if 'Δv' in l or 'cambio di piano' in l][:6]; pg.screenshot(path=str(OUT / '2-percorso-geo.png'))
        t = percorso('atlante.probe("MRO")'); R['testo MRO'] = [l for l in t.split('\n') if 'Δv' in l or 'finestra' in l.lower() or 'giorni' in l][:8]
        t = percorso('atlante.probe("JWST")'); R['testo JWST'] = t[:200]
        t = percorso('atlante.probe("VGR1")'); R['testo Voyager 1'] = t[:160]
        t = percorso('atlante.probe("PSP")'); R['testo Parker'] = [l for l in t.split('\n') if 'Δv' in l or 'AU' in l][:5]
        t = percorso('atlante.probe("LRO")'); R['testo LRO'] = [l for l in t.split('\n') if 'Δv' in l][:4]
        # cambio del sito dalla pagina
        ev('atlante.select(41866)'); ev('atlante.setTab("percorso")'); time.sleep(1)
        pg.select_option('#tSite', 'baikonur'); time.sleep(0.5); t = ev('document.getElementById("tOut").innerText'); R['GOES da Bajkonur'] = [l for l in t.split('\n') if 'Δv totale' in l or 'cambio di piano' in l or l.strip().endswith('km/s')][:4]
        pg.select_option('#tSite', 'kourou'); time.sleep(0.3)
        R['impostazioni salvate'] = ev('localStorage.getItem("atlante-percorso")')
        # ---- 7. missione nuova: margini ADCS
        ev('atlante.goto("earth")'); time.sleep(0.5); pg.click('#btnNewDes'); time.sleep(1.5)
        R['schede progetto'] = ev('[...document.querySelectorAll(".tabs button")].map(b=>b.textContent)')
        ev('atlante.setTab("adcs")'); time.sleep(2.5); a2 = ev('document.getElementById("adcs").innerText')
        pg.fill('#gM', '4'); pg.dispatch_event('#gM', 'change'); time.sleep(2.0); a4 = ev('document.getElementById("adcs").innerText')
        def riga(t, chiave): return next((l for l in t.split('\n') if chiave in l), '')
        R['ADCS margine 2'] = riga(a2, 'dipolo ≥'); R['ADCS margine 4'] = riga(a4, 'dipolo ≥'); R['ADCS perché'] = riga(a4, 'Il dipolo vale')[60:230]
        assert R['ADCS margine 2'] != R['ADCS margine 4'] and 'margine 4 sui disturbi' in a4 and 'margine 2 sui disturbi' in a2
        t = percorso('void 0'); R['testo missione SSO'] = [l for l in t.split('\n') if 'Δv' in l or 'azimut' in l.lower()][:6]; pg.screenshot(path=str(OUT / '3-percorso-missione.png'))
        # ---- 8. controllo PD: parte da 5 gradi di errore
        ev('atlante.select(40697)'); ev('atlante.setTab("assetto")'); time.sleep(1); pg.click('#amP'); pg.click('#btnFaster'); pg.click('#btnFaster'); time.sleep(0.3)
        e0 = ev('document.getElementById("aErr").textContent'); time.sleep(9)
        R['PD'] = dict(errore_iniziale=e0, errore_dopo=ev('document.getElementById("aErr").textContent'), coppia=ev('document.getElementById("aTc").textContent'), ruote=ev('document.getElementById("aHw").textContent'),
                       trascorsi_s=None, nota=ev('document.getElementById("cNote").textContent')[:150], modo=ev('atlante.att.mode'))
        pg.screenshot(path=str(OUT / '4-assetto-pd.png'))
        assert float(R['PD']['errore_dopo'].replace(',', '.').replace('−', '-')) < 0.5
        # ---- 9. B-dot: parte con 2 gradi al secondo per asse
        for i in range(3): pg.fill('#aW%d' % i, '0.3'); pg.dispatch_event('#aW%d' % i, 'change')
        pg.click('#amB'); time.sleep(0.5); w0 = ev('Math.hypot(...atlante.att.w)*180/Math.PI'); pg.click('#btnFaster'); time.sleep(12)
        R['B-dot'] = dict(omega_iniziale=round(w0, 3), omega_dopo=round(ev('Math.hypot(...atlante.att.w)*180/Math.PI'), 4), velocita=ev('document.getElementById("speed").textContent'), saturo=ev('atlante.att.sat'), k=ev('atlante.att.ctl.kb'), mmax=ev('atlante.att.ctl.mmax'))
        print(json.dumps({k: R[k] for k in ('PD', 'B-dot')}, indent=1, ensure_ascii=False)); sys.stdout.flush()
        assert R['B-dot']['omega_dopo'] < 0.85 * R['B-dot']['omega_iniziale']      # quanto scende dipende da quanti secondi simulati entrano nella prova
        for i in range(3): pg.fill('#aW%d' % i, '0'); pg.dispatch_event('#aW%d' % i, 'change')
        # telefono: nessuno scorrimento orizzontale con la pagina Percorso aperta
        tel = br.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale='it-IT')
        tel.route('**/*', lambda r: r.continue_() if r.request.url.startswith(URL) else r.abort()); p2 = tel.new_page(); p2.goto(URL)
        p2.wait_for_function('window.atlante && atlante.state().N>0', timeout=90000); p2.evaluate('atlante.select(25544)'); p2.evaluate('atlante.setTab("percorso")'); time.sleep(2.5)
        p2.screenshot(path=str(OUT / '5-telefono-percorso.png')); R['telefono'] = p2.evaluate('[document.documentElement.scrollWidth,innerWidth]')
        R['errori'] = err[:10]
        br.close()
finally:
    srv.terminate()
print(json.dumps(R, indent=1, ensure_ascii=False))
