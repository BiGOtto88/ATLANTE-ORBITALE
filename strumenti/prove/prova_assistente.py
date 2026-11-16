#!/usr/bin/env python3
"""Prova degli strumenti dell'assistente, senza modello e senza rete: un modello finto chiede ogni strumento e si controllano i risultati.
Uso: python3 strumenti/prove/prova_assistente.py [cartella_del_sito]   (richiede Playwright con Chromium)"""
import json, pathlib, re, subprocess, sys, time
from playwright.sync_api import sync_playwright

RADICE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
PORTA = 8791
srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORTA), '-d', str(RADICE)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
ok = True
def verifica(nome, cond, dettaglio=''):
    global ok; ok &= bool(cond); print(('ok    ' if cond else 'ERRORE'), nome, dettaglio)

try:
    # i nomi degli strumenti nel servizio e nella pagina coincidono
    nomi_w = re.findall(r"\{ name: '([a-z_0-9]+)', description", (RADICE / 'assistente/worker.js').read_text())
    pagina = (RADICE / 'sorgente/pagina-sorgente.html').read_text()
    blocco = re.search(r'const AS_TOOLS=\{(.*?)\};', pagina, re.S).group(1)
    nomi_p = re.findall(r'([a-z_0-9]+):as[A-Za-z0-9]+', blocco)
    verifica('nomi degli strumenti uguali nel servizio e nella pagina', sorted(nomi_w) == sorted(nomi_p), str(sorted(set(nomi_w) ^ set(nomi_p))))
    chiamate = [('calc', {'expression': 'sqrt(mu_earth/(11376^3))*2*pi'}),
        ('kepler_to_state', dict(a_km=11376, e=0.4178, i_deg=66, raan_deg=40, argp_deg=20, nu_deg=23)),
        ('propagate', dict(a_km=11376, e=0.4178, i_deg=66, raan_deg=40, argp_deg=20, nu_deg=23, duration_days=4, model='both')),
        ('repeat_ground_track', dict(k=4, m=3, e=0.4178, i_deg=66)),
        ('find_objects', {'query': 'ISS'}), ('object_status', {'norad': 25544}),
        ('passes', dict(norad=25544, lat_deg=45.4642, lon_deg=9.19, days=3)), ('ground_track_map', dict(norad=20580, hours=6)),
        ('diagram', {'name': 'keplerian_elements'}), ('diagram', {'name': 'orbit_regimes'}), ('snapshot_3d', {}),
        ('show_in_3d', {'norad': 25544}), ('calc', {'expression': 'process.exit()'}), ('inventato', {})]
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 900}); err = []; pg.on('pageerror', lambda e: err.append(str(e)))
        pg.goto('http://localhost:%d/index.html' % PORTA); pg.wait_for_timeout(4000)
        pg.evaluate("document.getElementById('btnAsk').hidden=false;document.getElementById('tabAsk').hidden=false"); pg.click('#btnAsk'); pg.wait_for_timeout(400)
        pg.evaluate("""calls=>{ const A=window.atlante.AS; let n=0; A.mock=async()=>{ n++; if(n===1) return {stop_reason:'tool_use',content:calls.map((c,i)=>({type:'tool_use',id:'t'+i,name:c[0],input:c[1]}))}; return {stop_reason:'end_turn',content:[{type:'text',text:'fine'}]}; }; }""", chiamate)
        pg.fill('#asIn', 'prova'); pg.click('#asGo'); pg.wait_for_timeout(7000)
        R = pg.evaluate("window.atlante.AS.msgs.filter(m=>Array.isArray(m.content)&&m.content[0]&&m.content[0].type==='tool_result').flatMap(m=>m.content.map(r=>({e:!!r.is_error,c:r.content})))")
        verifica('il ciclo si chiude e risponde', not pg.evaluate("window.atlante.AS.busy") and len(R) == len(chiamate))
        J = [json.loads(r['c']) if r['c'].startswith('{') else {} for r in R]
        verifica('stato cartesiano', abs(J[1]['position_km'][0] - 2590.338) < 1e-3 and J[1]['check_max_error'] < 1e-9)
        verifica('J2 dopo 4 giorni', abs(J[2]['with_j2']['lat_deg'] + 37.4920) < 5e-4 and abs(J[2]['with_j2']['lon_deg'] + 127.1008) < 5e-4, '(riferimento scipy DOP853)')
        verifica('due corpi dopo 4 giorni', abs(J[2]['two_body']['lat_deg'] + 39.8758) < 5e-4)
        verifica('traccia ripetuta', abs(J[3]['keplerian']['a_km'] - 34805.755) < 5e-3 and abs(J[3]['with_j2']['a_km'] - 34804.162) < 5e-3)
        verifica('ricerca e stato di un satellite', J[4]['matches'][0]['norad'] == 25544 and 300 < J[5]['altitude_km'] < 500)
        verifica('passaggi', J[6]['count'] > 0 and all(0 <= x['az_max_deg'] <= 360 for x in J[6]['passes']))
        verifica('figure nella chat (2 mappe, 2 schemi, 1 vista 3D)', pg.evaluate("document.querySelectorAll('.asfig').length") == 5, str(pg.evaluate("document.querySelectorAll('.asfig').length")))
        verifica('un\'espressione non ammessa viene rifiutata', R[12]['e'] and 'not allowed' in R[12]['c'])
        verifica('uno strumento inventato viene rifiutato', R[13]['e'])
        verifica('nessun errore nella pagina', not err, str(err[:2]))
        # secondo percorso: nell'artifact è la pagina stessa a chiamare il modello di chi guarda con gli strumenti (capacità «sample»); qui con una funzione finta
        pg2 = b.new_page(viewport={'width': 1280, 'height': 900}); err2 = []; pg2.on('pageerror', lambda e: err2.append(str(e)))
        pg2.goto('http://localhost:%d/index.html' % PORTA); pg2.wait_for_timeout(4000)
        pg2.evaluate("document.getElementById('btnAsk').hidden=false;document.getElementById('tabAsk').hidden=false"); pg2.click('#btnAsk'); pg2.wait_for_timeout(400)
        pg2.evaluate("""calls=>{ const A=window.atlante.AS; window.__sin=null; const f=async(input,o)=>{ window.__sin=input; const out=[]; for(const c of calls){ const t=o.tools.find(x=>x.name===c[0]); try{ out.push(await t.execute(c[1],{signal:new AbortController().signal})); }catch(e){ out.push('ERR '+e.message); } } window.__sout=out; o.onText({text:'ok **fine**'}); return {text:'ok **fine**',truncated:false}; }; f.limits=async()=>({tools:{maxCount:20}}); A.sample=f; }""", chiamate)
        pg2.fill('#asIn', 'prova due'); pg2.click('#asGo'); pg2.wait_for_timeout(7000)
        out = pg2.evaluate("window.__sout"); entrata = pg2.evaluate("window.__sin")
        verifica('percorso artifact: tutti gli strumenti eseguiti', out is not None and len(out) == len(chiamate))
        verifica('percorso artifact: risultati uguali', out and abs(json.loads(out[2])['with_j2']['lat_deg'] + 37.4920) < 5e-4 and out[12].startswith('ERR') and out[13].startswith('ERR'))
        verifica('percorso artifact: istruzioni e domanda nell\'ingresso', entrata and entrata[0]['role'] == 'user' and 'Keplario' in entrata[0]['content'] and entrata[-1]['content'] == 'prova due')
        verifica('percorso artifact: figure e testo nella chat', pg2.evaluate("document.querySelectorAll('.asfig').length") == 5 and 'fine' in pg2.inner_text('#asLog'))
        verifica('percorso artifact: nessun errore nella pagina', not err2, str(err2[:2]))
        # terzo percorso: informazioni esterne (CelesTrak, Wikipedia) simulate intercettando le richieste; il TLE è quello della ISS con un altro numero NORAD
        testo = (RADICE / 'data/active.txt').read_text().split('\n'); k = next(i for i, r in enumerate(testo) if r.startswith('ISS (ZARYA)'))
        def chk(r): return str(sum(int(c) if c.isdigit() else (1 if c == '-' else 0) for c in r[:68]) % 10)
        l1 = testo[k + 1][:2] + '03509' + testo[k + 1][7:68]; l2 = testo[k + 2][:2] + '03509' + testo[k + 2][7:68]
        tle = 'COSMOS 249 DEB (PROVA)\n' + l1 + chk(l1) + '\n' + l2 + chk(l2) + '\n'; cors = {'access-control-allow-origin': '*'}
        pg.close(); pg2.close()   # le pagine già provate occupano il processore
        ctx3 = b.new_context(viewport={'width': 1280, 'height': 900}); pg3 = ctx3.new_page(); err3 = []; pg3.on('pageerror', lambda e: err3.append(str(e)))
        ctx3.route('https://celestrak.org/NORAD/elements/gp.php?**', lambda r: r.fulfill(status=200, headers=cors, body=tle if 'CATNR=3509' in r.request.url else 'No GP data found'))
        ctx3.route('https://en.wikipedia.org/**', lambda r: r.fulfill(status=200, headers=cors, content_type='application/json', body='{"title":"Prova","extract":"testo"}'))
        pg3.goto('http://localhost:%d/index.html' % PORTA); pg3.wait_for_timeout(4000)
        pg3.evaluate("document.getElementById('btnAsk').hidden=false;document.getElementById('tabAsk').hidden=false"); pg3.click('#btnAsk'); pg3.wait_for_timeout(400)
        est = [('fetch_tle', {'catnr': 3509}), ('find_objects', {'query': '3509'}), ('object_status', {'norad': 3509}), ('show_in_3d', {'norad': 3509}),
               ('web_fetch', {'url': 'https://en.wikipedia.org/api/rest_v1/page/summary/Prova'}), ('web_fetch', {'url': 'https://example.com/'}), ('fetch_tle', {'catnr': 99999}), ('web_fetch', {'url': 'http://celestrak.org/x'})]
        pg3.evaluate("""calls=>{ const A=window.atlante.AS; let n=0; A.mock=async()=>{ n++; if(n===1) return {stop_reason:'tool_use',content:calls.map((c,i)=>({type:'tool_use',id:'e'+i,name:c[0],input:c[1]}))}; return {stop_reason:'end_turn',content:[{type:'text',text:'fine'}]}; }; }""", est)
        n0 = pg3.evaluate("window.atlante.sats.length"); pg3.fill('#asIn', 'prova tre'); pg3.click('#asGo'); pg3.wait_for_timeout(1500)
        for _ in range(40):
            if not pg3.evaluate("window.atlante.AS.busy"): break
            pg3.wait_for_timeout(1000)
        R3 = pg3.evaluate("window.atlante.AS.msgs.filter(m=>Array.isArray(m.content)&&m.content[0]&&m.content[0].type==='tool_result').flatMap(m=>m.content.map(r=>({e:!!r.is_error,c:r.content})))")
        verifica('esterno: tutte le chiamate eseguite', len(R3) == len(est), str(len(R3)))
        J3 = [json.loads(r['c']) if r['c'].startswith('{') else {} for r in R3]
        verifica('esterno: il TLE entra nel catalogo', J3[0].get('added_or_updated') == [3509] and pg3.evaluate("window.atlante.sats.length") == n0 + 1)
        verifica('esterno: l\'oggetto aggiunto si trova e ha uno stato', J3[1]['matches'][0]['norad'] == 3509 and J3[1]['matches'][0].get('added_this_session') and 300 < J3[2]['altitude_km'] < 500)
        verifica('esterno: si mostra nel 3D', J3[3].get('shown', '').startswith('COSMOS 249'))
        verifica('esterno: pagina Wikipedia letta', 'testo' in R3[4]['c'])
        verifica('esterno: host non ammesso rifiutato', R3[5]['e'] and 'not allowed' in R3[5]['c'])
        verifica('esterno: oggetto senza dati', J3[6].get('found') is False)
        verifica('esterno: http rifiutato', R3[7]['e'])
        verifica('esterno: nessun errore nella pagina', not err3, str(err3[:2]))
        # quarto percorso: Horizons e Space-Track tramite il servizio (simulato); la pagina riceve il servizio con la meta tag
        pg3.close(); ctx3.close()
        ctx4 = b.new_context(viewport={'width': 1280, 'height': 900}); pg4 = ctx4.new_page(); err4 = []; pg4.on('pageerror', lambda e: err4.append(str(e)))
        def pagina_con_servizio(r):
            resp = r.fetch(); r.fulfill(response=resp, body=re.sub(r'<meta name="assistente" content="[^"]*">', '<meta name="assistente" content="https://servizio.prova/">', resp.text()))
        ctx4.route('http://localhost:%d/index.html' % PORTA, pagina_con_servizio)
        ctx4.route('https://ssd.jpl.nasa.gov/**', lambda r: r.abort())   # Horizons non raggiungibile dal browser: si deve usare il servizio
        hz = '{"result":"header\\n$$SOE\\n2460745.500694444, A.D. 2025-Mar-10 00:01:00.0000, -4000.5, 5000.25, 3000.75, -3.5, -4.25, 5.125,\\n2460745.501388889, A.D. 2025-Mar-10 00:02:00.0000, 1, 2, 3, 4, 5, 6,\\n$$EOE\\nfooter"}'
        def servizio(r):
            if r.request.method == 'OPTIONS': return r.fulfill(status=204, headers={'access-control-allow-origin': '*', 'access-control-allow-headers': 'content-type'})
            q = json.loads(r.request.post_data); h = {'access-control-allow-origin': '*', 'content-type': 'application/json'}
            if 'messages' in q: return r.fulfill(status=502, headers=h, body=json.dumps({'error': 'upstream', 'status': 404, 'detail': 'modello prova'}))
            if q['proxy'] == 'horizons': return r.fulfill(status=200, headers=h, body=json.dumps({'status': 200, 'text': hz}))
            return r.fulfill(status=200, headers=h, body=json.dumps({'before': tle.replace('03509', '04242'), 'after': ''}) if q['norad'] == 4242 else json.dumps({'before': '', 'after': ''}))
        ctx4.route('https://servizio.prova/', servizio)
        pg4.goto('http://localhost:%d/index.html' % PORTA); pg4.wait_for_timeout(4000)
        pg4.evaluate("document.getElementById('btnAsk').hidden=false;document.getElementById('tabAsk').hidden=false"); pg4.click('#btnAsk'); pg4.wait_for_timeout(400)
        T4 = '2025-03-10T00:01:00Z'
        est4 = [('horizons_state', {'command': '3509', 'time_utc': T4}), ('horizons_state', {'command': "x'&y", 'time_utc': T4}),
                ('spacetrack_tle', {'norad': 4242, 'time_utc': T4}), ('spacetrack_tle', {'norad': 4243, 'time_utc': T4}),
                ('object_status', {'norad': 4242, 'time_utc': T4}), ('show_in_3d', {'norad': 4242, 'time_utc': T4}), ('object_status', {'norad': 4242, 'time_utc': 'ieri'})]
        pg4.evaluate("calls=>{ const A=window.atlante.AS; let n=0; A.mock=async()=>{ n++; if(n===1) return {stop_reason:'tool_use',content:calls.map((c,i)=>({type:'tool_use',id:'h'+i,name:c[0],input:c[1]}))}; return {stop_reason:'end_turn',content:[{type:'text',text:'fatto'}]}; }; }", est4)
        pg4.fill('#asIn', 'prova quattro'); pg4.click('#asGo'); pg4.wait_for_timeout(1500)
        for _ in range(40):
            if not pg4.evaluate("window.atlante.AS.busy"): break
            pg4.wait_for_timeout(1000)
        R4 = pg4.evaluate("window.atlante.AS.msgs.filter(m=>Array.isArray(m.content)&&m.content[0]&&m.content[0].type==='tool_result').flatMap(m=>m.content.map(r=>({e:!!r.is_error,c:r.content})))")
        verifica('storico: tutte le chiamate eseguite', len(R4) == len(est4), str(len(R4)))
        J4 = [json.loads(r['c']) if r['c'].startswith('{') else {} for r in R4]
        verifica('horizons: stato letto tramite il servizio', J4[0].get('via') == 'service' and J4[0].get('position_km') == [-4000.5, 5000.25, 3000.75] and J4[0].get('velocity_kms') == [-3.5, -4.25, 5.125], str(R4[0]['c'][:160]))
        verifica('horizons: elementi osculatori presenti', 'a_km' in J4[0].get('osculating_elements', {}))
        verifica('horizons: comando non valido rifiutato', R4[1]['e'])
        verifica('spacetrack: TLE storico propagato', J4[2].get('norad') == 4242 and 300 < J4[2].get('altitude_km', 0) < 500 and J4[2].get('added_to_catalogue') is True, str(R4[2]['c'][:200]))
        verifica('spacetrack: oggetto senza dati', J4[3].get('found') is False)
        verifica('storico: object_status a un istante passato', J4[4].get('time_utc', '').startswith('2025-03-10T00:01') and J4[4].get('altitude_km'), str(R4[4]['c'][:120]))
        verifica("storico: show_in_3d sposta l'orologio", J4[5].get('clock_utc', '').startswith('2025-03-10T00:01'), str(R4[5]['c'][:120]))
        verifica('storico: data non valida rifiutata', R4[6]['e'])
        pg4.evaluate("window.atlante.AS.mock=null"); pg4.fill('#asIn', 'errore'); pg4.click('#asGo'); pg4.wait_for_timeout(2500)
        T5 = pg4.evaluate("document.getElementById('asLog').innerText")
        verifica('errore del servizio: il pannello mostra il codice', 'HTTP 502' in T5 and 'servizio.prova' in T5 and 'upstream' in T5 and '404' in T5 and 'modello prova' in T5, T5[-160:])
        verifica('storico: nessun errore nella pagina', not err4, str(err4[:2]))
        b.close()
finally:
    srv.terminate()
sys.exit(0 if ok else 1)
