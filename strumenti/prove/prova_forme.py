#!/usr/bin/env python3
"""Prova delle forme reali: avvicina la camera a più veicoli e controlla che il modello 3D venga caricato e disegnato.
Uso: python3 strumenti/prove/prova_forme.py . /tmp/schermate      (serve Playwright)"""
import json, subprocess, sys, time, pathlib
from playwright.sync_api import sync_playwright

SITO = pathlib.Path(sys.argv[1]).resolve(); OUT = pathlib.Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
URL = 'http://localhost:8785/'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8785', '--bind', '127.0.0.1'], cwd=SITO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
R = {}
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        ctx = br.new_context(viewport={'width': 1280, 'height': 800}, locale='it-IT'); err = []; esterni = []
        ctx.route('**/*', lambda r: r.continue_() if r.request.url.startswith(URL) else (esterni.append(r.request.url), r.abort()))
        pg = ctx.new_page(); pg.on('pageerror', lambda e: err.append('pageerror: ' + str(e))); pg.on('console', lambda m: err.append(m.text[:200]) if m.type == 'error' else None)
        pg.goto(URL); pg.wait_for_function('window.atlante && atlante.state().N>0 && atlante.state().P>0', timeout=90000)
        ev = pg.evaluate
        casi = [('iss', 'atlante.select(25544)', True), ('hubble', 'atlante.select(20580)', True), ('goes', 'atlante.select(41866)', True), ('landsat9', 'atlante.select(49260)', True), ('jwst', 'atlante.probe("JWST")', True),
                ('juno', 'atlante.probe("JUNO")', True), ('mro', 'atlante.probe("MRO")', True), ('voyager', 'atlante.probe("VGR1")', True), ('starlink', 'atlante.select(atlante.sats.find(s=>/^STARLINK/.test(s.name)).norad)', False)]
        for nome, sel, reale in casi:
            ev(sel); time.sleep(1.2); pg.click('#btnNear')
            if reale: pg.wait_for_function('atlante.near.real!==""', timeout=30000)
            time.sleep(3.0); n = ev('atlante.near'); st = ev('atlante.state()')
            R[nome] = dict(vicino=n['on'], modello=n['real'], dimensione_m=round(n['size'] / 0.62, 1) if n['real'] else None, distanza_m=round(ev('(()=>{ const s=atlante.state(); return 0; })()') or 0, 1), segue=st['follow'], didascalia=ev('document.querySelector("#inset .it").textContent'))
            assert n['on'] and st['follow'] and (bool(n['real']) == reale), (nome, n)
            # il veicolo deve stare davvero nella scena ravvicinata, non solo nel riquadro dell'assetto
            R[nome]['disegnato'] = ev('atlante.near.drawn'); assert R[nome]['disegnato'] > 0, nome
            pg.screenshot(path=str(OUT / ('%s.png' % nome)))
        # con la rotella ci si allontana e ci si riavvicina restando sul veicolo
        ev('atlante.select(25544)'); time.sleep(1); pg.click('#btnNear'); time.sleep(2.5); pg.mouse.move(640, 400)
        for _ in range(12): pg.mouse.wheel(0, 300); time.sleep(0.05)
        time.sleep(0.8); R['dopo la rotella indietro'] = ev('atlante.near.on')
        for _ in range(40): pg.mouse.wheel(0, -300); time.sleep(0.03)
        time.sleep(0.8); R['dopo la rotella avanti'] = ev('atlante.near.on'); assert R['dopo la rotella avanti']
        pg.click('#btnBody'); time.sleep(2.0); R['tornando alla vista del pianeta'] = ev('atlante.near.on'); assert not R['tornando alla vista del pianeta']
        R['modelli caricati'] = ev('atlante.near.loaded'); R['richieste esterne'] = sorted(set(esterni)); R['errori'] = err[:8]
        br.close()
finally:
    srv.terminate()
print(json.dumps(R, indent=1, ensure_ascii=False))
