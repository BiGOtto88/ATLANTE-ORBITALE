#!/usr/bin/env python3
"""Prova del sito autonomo in un browser reale: caricamento senza CDN, service worker, apertura senza rete, installabilità."""
import json, subprocess, sys, time, pathlib
from playwright.sync_api import sync_playwright

SITO = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
PORT = 8765
URL = f'http://localhost:{PORT}/'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=SITO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.0)
esito = {}
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = br.new_context(viewport={'width': 1440, 'height': 900}, locale='it-IT')
        esterni, errori, falliti = [], [], []
        def instrada(route):
            u = route.request.url
            if u.startswith(URL): route.continue_()
            else: esterni.append(u); route.abort()
        ctx.route('**/*', instrada)
        page = ctx.new_page()
        page.on('console', lambda m: errori.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errori.append('pageerror: ' + str(e)))
        page.on('requestfailed', lambda r: falliti.append(r.url))
        page.goto(URL)
        page.wait_for_function('window.atlante && atlante.state().N>0 && atlante.state().P>0', timeout=90000)
        esito['stato'] = page.evaluate('atlante.state()')
        esito['librerie'] = page.evaluate('[...document.scripts].filter(s=>s.src).map(s=>new URL(s.src).pathname)')
        page.evaluate('document.fonts.ready.then(()=>1)')
        esito['caratteri'] = page.evaluate('[...document.fonts].filter(f=>f.status==="loaded").map(f=>f.family+" "+f.weight)')
        esito['margine_body'] = page.evaluate('getComputedStyle(document.body).margin')
        esito['nascosti_visibili'] = page.evaluate('[...document.querySelectorAll("[hidden]")].filter(e=>getComputedStyle(e).display!=="none").map(e=>e.id||e.className)')
        esito['scorrimento'] = page.evaluate('[document.documentElement.scrollWidth,innerWidth,document.documentElement.scrollHeight,innerHeight]')
        esito['stamp'] = page.inner_text('#stamp')
        time.sleep(2.5)
        page.screenshot(path=str(OUT / '1-apertura.png'))
        page.evaluate('atlante.select(25544)'); time.sleep(3.5)
        page.screenshot(path=str(OUT / '2-iss.png'))
        esito['iss'] = page.evaluate('document.querySelector("#detail h2").textContent')
        page.evaluate('atlante.probe("MRO")'); time.sleep(3.5)
        page.screenshot(path=str(OUT / '3-mro.png'))
        esito['mro_quota'] = page.evaluate('document.getElementById("sAlt").textContent')
        # service worker
        page.evaluate('navigator.serviceWorker.ready.then(()=>1)')
        page.wait_for_function('navigator.serviceWorker.controller!==null', timeout=30000)
        time.sleep(2)
        esito['copie_locali'] = page.evaluate('caches.open("atlante-v1").then(c=>c.keys()).then(k=>k.map(r=>new URL(r.url).pathname).sort())')
        # installabilità (protocollo di Chrome)
        cdp = ctx.new_cdp_session(page)
        man = cdp.send('Page.getAppManifest')
        esito['manifest_url'] = man.get('url'); esito['manifest_errori'] = man.get('errors')
        try: esito['installabilita_errori'] = cdp.send('Page.getInstallabilityErrors').get('installabilityErrors')
        except Exception as e: esito['installabilita_errori'] = 'n/d: ' + str(e)[:80]
        # senza rete: ricarica
        ctx.set_offline(True)
        errori_prima = len(errori)
        page.reload()
        page.wait_for_function('window.atlante && atlante.state().N>0 && atlante.state().P>0', timeout=90000)
        time.sleep(3)
        esito['senza_rete'] = page.evaluate('atlante.state()')
        esito['senza_rete_stamp'] = page.inner_text('#stamp')
        esito['senza_rete_caratteri'] = page.evaluate('[...document.fonts].filter(f=>f.status==="loaded").length')
        page.screenshot(path=str(OUT / '4-senza-rete.png'))
        esito['errori_senza_rete'] = errori[errori_prima:]
        ctx.set_offline(False)
        # telefono
        tel = br.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale='it-IT')
        tel.route('**/*', instrada)
        p2 = tel.new_page(); p2.goto(URL)
        p2.wait_for_function('window.atlante && atlante.state().N>0', timeout=90000); time.sleep(3)
        p2.screenshot(path=str(OUT / '5-telefono.png'))
        esito['telefono_scorrimento'] = p2.evaluate('[document.documentElement.scrollWidth,innerWidth]')
        esito['richieste_esterne'] = sorted(set(esterni)); esito['errori_console'] = errori[:errori_prima][:12]; esito['richieste_fallite'] = [f for f in falliti if f.startswith(URL)][:12]
        br.close()
finally:
    srv.terminate()
print(json.dumps(esito, indent=1, ensure_ascii=False))
