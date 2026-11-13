#!/usr/bin/env python3
"""Prove di strumenti/aggiorna_sonde.py senza rete.   Uso: python3 strumenti/prove/prova_sonde.py [SIGLA ...]

1. Le formule Python danno le stesse posizioni del codice JavaScript della pagina.
2. Con effemeridi generate dal modello pubblicato (data/probes.json) lo strumento ritrova le stesse orbite.
3. Con un'orbita integrata numericamente attorno a Marte (con J2) il modello adattato la segue
   e la precessione del nodo coincide con il valore teorico.
4. Lettura di una risposta di Horizons, compreso il messaggio di fine effemeridi.
"""
import json, math, pathlib, subprocess, sys, tempfile

SITO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(SITO / 'strumenti'))
import aggiorna_sonde as S

dati = json.loads((SITO / 'data' / 'probes.json').read_text())
per_id = {p['id']: p for p in dati['probes']}
T0 = next(p['t0'] for p in dati['probes'] if p['type'] == 'fit')      # istante da cui valgono i dati pubblicati


def modello(p, jt):
    if p['type'] == 'fit':
        return p['c'], S.posizione_fit(p, jt)
    tr = S.tratto_per(p['seg'], jt)
    return tr['c'], S.posizione_kep(tr, jt)


# ---- 1. confronto con il JavaScript della pagina
pagina = (SITO / 'index.html').read_text()
def blocco(nome):
    i = pagina.index('function ' + nome + '(')
    j = pagina.index('\n', i)
    if pagina[i:j].count('{') != pagina[i:j].count('}'):
        j = pagina.index('\n}\n', i) + 2
    return pagina[i:j]
js = '\n'.join(blocco(n) for n in ('keplerE', 'keplerH', 'perifocal', 'rotOrb'))
js = 'const TAU=2*Math.PI, D2R=Math.PI/180;\n' + js + '''
const fs=require('fs'), data=JSON.parse(fs.readFileSync(process.argv[2])), GM=JSON.parse(process.argv[3]), POLE=JSON.parse(process.argv[4]), T0=+process.argv[5];
function basis(c){ const ra=POLE[c][0]*D2R, de=POLE[c][1]*D2R, Z=[Math.cos(de)*Math.cos(ra),Math.cos(de)*Math.sin(ra),Math.sin(de)], l=Math.hypot(Z[0],Z[1]), X=[-Z[1]/l,Z[0]/l,0], Y=[Z[1]*X[2]-Z[2]*X[1],Z[2]*X[0]-Z[0]*X[2],Z[0]*X[1]-Z[1]*X[0]]; return [X,Y,Z]; }
const xy=[0,0], tB=[0,0,0], out=[];
for(const p of data.probes){ if(p.type==='L') continue; for(const d of [0.3,3.7,7.7,12.9]){ const jt=T0+d, o=[0,0,0]; let c;
  if(p.type==='fit'){ const tau=jt-p.t0, Om=(p.om[0]+p.om[1]*tau)*D2R, w=(p.w[0]+p.w[1]*tau)*D2R, u=(p.u[0]+p.u[1]*tau+p.u[2]*tau*tau)*D2R;
    perifocal(p.a*(1-p.e),p.e,u-w,xy); rotOrb(xy[0],xy[1],p.i*D2R,Om,w,tB); const B=basis(p.c);
    o[0]=B[0][0]*tB[0]+B[1][0]*tB[1]+B[2][0]*tB[2]; o[1]=B[0][1]*tB[0]+B[1][1]*tB[1]+B[2][1]*tB[2]; o[2]=B[0][2]*tB[0]+B[1][2]*tB[1]+B[2][2]*tB[2]; c=p.c; }
  else { let s=p.seg[0]; for(const g of p.seg){ if(g.frm<=jt) s=g; else break; }
    const k=s.k, a=Math.abs(k[0]/(1-k[1])), n=Math.sqrt(GM[s.c]/(a*a*a)); perifocal(k[0],k[1],n*(jt-k[5])*86400,xy); rotOrb(xy[0],xy[1],k[2]*D2R,k[3]*D2R,k[4]*D2R,o); c=s.c; }
  out.push([p.id,d,c,o]); } }
console.log(JSON.stringify(out));
'''
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
    f.write(js)
res = json.loads(subprocess.run(['node', f.name, str(SITO / 'data' / 'probes.json'), json.dumps(S.GM), json.dumps(S.POLO), repr(T0)], capture_output=True, text=True, check=True).stdout)
peggio = 0
for pid, d, c, o in res:
    c2, p2 = modello(per_id[pid], T0 + d)
    assert c == c2, (pid, c, c2)
    peggio = max(peggio, math.dist(o, p2) / max(1.0, math.sqrt(sum(x * x for x in o))))
print('1. Python = JavaScript della pagina: %d confronti, scarto relativo massimo %.1e' % (len(res), peggio))
assert peggio < 1e-9

# ---- 2. giro completo con effemeridi generate dal modello pubblicato
def finta_interroga(cmd, centro, jd0, jd1, passo_min):
    sonda = next(s for s in S.SONDE if s.get('cmd') == cmd)
    p = per_id[sonda['id']]
    if jd1 > p['until'] + 1e-6:
        raise S.FineEffemeridi(p['until'], True)
    righe, n, h = [], int(round((jd1 - jd0) * 1440 / passo_min)), 2e-6
    for k in range(n + 1):
        t = jd0 + k * passo_min / 1440
        c, r = modello(p, t)
        tr = S.tratto_per(p['seg'], t) if p['type'] == 'kep' else None
        f = (lambda tt: S.posizione_kep(tr, tt)) if tr else (lambda tt: S.posizione_fit(p, tt))
        a, b = f(t - h), f(t + h)
        v = [(b[i] - a[i]) / (2 * h * 86400) for i in range(3)]
        if c != centro:                                   # stato rispetto a un altro corpo: qui basta sapere che non è legata
            r, v = [1e9, 0, 0], [0, 50, 0]
        righe.append((t,) + tuple(r) + tuple(v))
    return sonda['nome'].split('|')[0].replace('\\', ''), righe
S.interroga = finta_interroga
S.time.sleep = lambda *_: None
for s in S.SONDE:
    if len(sys.argv) > 1 and s['id'] not in sys.argv[1:]:
        continue
    if s['tipo'] == 'L':
        continue
    voce, nota = (S.orbiter if s['tipo'] == 'fit' else S.crociera)(s, T0)
    vecchia, peggio, n = per_id[s['id']], 0, 0
    t = T0
    while t < min(voce['until'], vecchia['until']):
        c1, a = modello(vecchia, t); c2, b = modello(voce, t)
        scala = vecchia['a'] if vecchia['type'] == 'fit' else math.sqrt(sum(x * x for x in a))   # orbiter: rispetto al semiasse
        peggio = max(peggio, math.dist(a, b) / scala); n += 1
        t += 0.37
    stato = 'ok' if peggio < (2e-2 if s['tipo'] == 'fit' else 0.5 if s.get('cattura') else 5e-3) else 'DIVERSA'      # il modello pubblicato ha salti ai sorvoli: lì lo scarto è atteso
    print('2. %-8s %s · scarto relativo dal modello pubblicato %.1e su %d istanti · %s' % (s['id'], stato, peggio, n, nota))
    assert stato == 'ok', s['id']

# ---- 3. orbita integrata attorno a Marte con J2
mu, Rm, J2 = S.GM['mars'], 3396.19, 1.96045e-3
def acc(r):
    x, y, z = r; r2 = x * x + y * y + z * z; rm = math.sqrt(r2); k = 1.5 * J2 * mu * Rm * Rm / rm ** 5; q = 5 * z * z / r2
    return (-mu * x / rm ** 3 - k * x * (1 - q), -mu * y / rm ** 3 - k * y * (1 - q), -mu * z / rm ** 3 - k * z * (3 - q))
a0, e0, i0 = 3656.7, 0.009, 92.69 * S.D2R
x, y = S.perifocale(a0 * (1 - e0), e0, 0.4)
r = list(S.ruota(x, y, i0, 1.0, 4.68))
vx, vy = (lambda E: (-math.sqrt(mu * a0) / (a0 * (1 - e0 * math.cos(E))) * math.sin(E), math.sqrt(mu * a0) / (a0 * (1 - e0 * math.cos(E))) * math.sqrt(1 - e0 * e0) * math.cos(E)))(S.kepler_e(0.4, e0))
v = list(S.ruota(vx, vy, i0, 1.0, 4.68))
B, h, righe, passo, giorni = S.base_corpo('mars'), 20.0, [], 23, 30
for k in range(int(giorni * 86400 / h) + 1):
    if k % int(passo * 60 / h) == 0:
        righe.append((T0 + k * h / 86400,) + S.da_base(B, r) + S.da_base(B, v))
    def d(s): return s[3:], acc(s[:3])
    s0 = r + v
    k1 = d(s0); s1 = [s0[j] + h / 2 * (list(k1[0]) + list(k1[1]))[j] for j in range(6)]
    k2 = d(s1); s2 = [s0[j] + h / 2 * (list(k2[0]) + list(k2[1]))[j] for j in range(6)]
    k3 = d(s2); s3 = [s0[j] + h * (list(k3[0]) + list(k3[1]))[j] for j in range(6)]
    k4 = d(s3)
    for j in range(6):
        inc = h / 6 * ((list(k1[0]) + list(k1[1]))[j] + 2 * (list(k2[0]) + list(k2[1]))[j] + 2 * (list(k3[0]) + list(k3[1]))[j] + (list(k4[0]) + list(k4[1]))[j])
        if j < 3: r[j] += inc
        else: v[j - 3] += inc
voce, scarto = S.adatta('mars', righe, T0)
n = math.sqrt(mu / voce['a'] ** 3)
teorico = -1.5 * n * J2 * (Rm / (voce['a'] * (1 - voce['e'] ** 2))) ** 2 * math.cos(voce['i'] * S.D2R) * S.R2D * 86400
print('3. Marte con J2, %d giorni: scarto massimo %.2f%% del semiasse · deriva del nodo %.4f °/giorno, teoria %.4f' % (giorni, 100 * scarto, voce['om'][1], teorico))
assert scarto < 0.02 and abs(voce['om'][1] - teorico) < 0.03 * abs(teorico) + 0.002

# ---- 4. lettura delle risposte di Horizons
ok = '''API VERSION: 1.2
API SOURCE: NASA/JPL Horizons API

*******************************************************************************
Ephemeris / API_USER Thu Nov 12 08:00:00 2026 Pasadena, USA      / Horizons
*******************************************************************************
Target body name: Lunar Reconnaissance Orbiter (-85)  {source: LRO_merged}
Center body name: Moon (301)                      {source: LRO_merged}
*******************************************************************************
            JDTDB,            Calendar Date (TDB),                      X,                      Y,                      Z,                     VX,                     VY,                     VZ,
**************************************************************************************************************************************************************************************************
$$SOE
2461356.500000000, A.D. 2026-Nov-12 00:00:00.0000,  1.234567890123456E+03, -5.432109876543210E+02,  1.111111111111111E+03,  9.876543210987654E-01,  1.234567890123457E+00, -2.345678901234568E-01,
2461356.520833333, A.D. 2026-Nov-12 00:30:00.0000, -1.034567890123456E+03,  6.432109876543210E+02,  1.211111111111111E+03, -8.876543210987654E-01,  1.134567890123457E+00,  3.345678901234568E-01,
$$EOE
**************************************************************************************************************************************************************************************************
'''
nome, righe = S.leggi_risposta(ok)
assert nome == 'Lunar Reconnaissance Orbiter (-85)' and len(righe) == 2 and righe[1][0] == 2461356.520833333 and righe[0][3] == 1111.111111111111 and righe[1][6] == 0.3345678901234568
try:
    S.leggi_risposta('API VERSION: 1.2\nAPI SOURCE: NASA/JPL Horizons API\n\n No ephemeris for target "Mars Reconnaissance Orbiter" after A.D. 2026-NOV-28 12:00:00.0000 TDB\n')
    raise SystemExit('doveva segnalare la fine delle effemeridi')
except S.FineEffemeridi as e:
    assert e.dopo and abs(e.jd - 2461373.0) < 1e-9, e.jd
assert S.testo_data(2461356.5) == '2026-11-12 00:00' and S.testo_data(2461373.0 - 10 / 1440) == '2026-11-28 11:50' and abs(S.jd_di(2026, 11, 12) - 2461356.5) < 1e-9
print('4. Lettura delle risposte di Horizons e conversione delle date: ok')
