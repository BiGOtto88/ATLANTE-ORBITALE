#!/usr/bin/env python3
"""Aggiorna data/probes.json: le orbite delle sonde oltre l'orbita terrestre, da JPL Horizons.

Per ogni sonda chiede a Horizons posizione e velocità (terna ICRF, tempi TDB) e le riduce
alla forma che la pagina sa propagare da sola:

  tipo "fit"  orbiter attorno a Luna, Marte, Giove: elementi medi nel piano equatoriale del corpo,
              con deriva lineare di nodo e pericentro e moto medio con termine quadratico;
  tipo "kep"  sonde in orbita attorno al Sole: elementi kepleriani a tratti; un tratto nuovo
              comincia quando quello prima si scosta troppo dalle effemeridi (sorvoli, spinta continua);
  tipo "L"    veicoli ai punti di Lagrange Sole-Terra: nessun dato, la pagina li disegna sul punto.

Una sonda che Horizons non restituisce (o restituisce con un nome inatteso) conserva i dati
che aveva: il file viene riscritto solo con ciò che è stato verificato.

Uso:   python3 strumenti/aggiorna_sonde.py              (dalla cartella del sito)
       python3 strumenti/aggiorna_sonde.py --solo LRO,MRO --prova
       python3 strumenti/aggiorna_sonde.py --in-linea https://utente.github.io/atlante
Con --in-linea i "dati di prima" sono quelli del sito già pubblicato, se più recenti di quelli nella cartella.
Serve solo Python 3, senza librerie aggiuntive.
Esce con 0 se almeno una sonda è stata aggiornata, con 1 se Horizons non ha dato nulla.
"""
import argparse, datetime, json, math, pathlib, re, sys, time, urllib.parse, urllib.request

RADICE = pathlib.Path(__file__).resolve().parent.parent
API = 'https://ssd.jpl.nasa.gov/api/horizons.api'
AGENTE = 'keplario/1.0 (aggiornamento giornaliero delle sonde)'
D2R, R2D, TAU = math.pi / 180, 180 / math.pi, 2 * math.pi

# Costanti uguali a quelle della pagina (tabella BDEF di index.html): se cambiano lì, vanno cambiate qui.
GM = {'sun': 132712440041.279, 'mercury': 22031.8686, 'venus': 324858.592, 'earth': 398600.4418, 'moon': 4902.800118,
      'mars': 42828.374857, 'jupiter': 126686531.9, 'saturn': 37931206.2, 'uranus': 5793951.3, 'neptune': 6835099.5}
POLO = {'mercury': (281.0103, 61.4155), 'venus': (272.76, 67.16), 'moon': (269.9949, 66.5392), 'mars': (317.681, 52.887),
        'jupiter': (268.057, 64.495), 'saturn': (40.589, 83.537), 'uranus': (257.311, -15.175), 'neptune': (299.36, 43.46)}
CENTRO = {'sun': '500@10', 'mercury': '500@199', 'venus': '500@299', 'earth': '500@399', 'moon': '500@301',
          'mars': '500@499', 'jupiter': '500@599', 'saturn': '500@699', 'uranus': '500@799', 'neptune': '500@899'}
SFERA = {'mercury': 1.1e5, 'venus': 6.2e5, 'mars': 5.8e5, 'jupiter': 4.8e7, 'saturn': 5.5e7}   # sfera d'influenza, km

# Sonde: sigla usata dalla pagina, numero Horizons, tipo, corpo centrale, parola attesa nel nome restituito.
# Per aggiungerne una: una riga qui e la sua scheda in PINFO dentro index.html.
SONDE = [
    dict(id='LRO', cmd='-85', tipo='fit', c='moon', nome=r'Lunar Reconnaissance|LRO'),
    dict(id='CH2', cmd='-152', tipo='fit', c='moon', nome=r'Chandrayaan'),
    dict(id='KPLO', cmd='-155', tipo='fit', c='moon', nome=r'KPLO|Danuri|Korea'),
    dict(id='ARTP1', cmd='-192', tipo='fit', c='moon', nome=r'ARTEMIS|THEMIS'),
    dict(id='ARTP2', cmd='-193', tipo='fit', c='moon', nome=r'ARTEMIS|THEMIS'),
    dict(id='MRO', cmd='-74', tipo='fit', c='mars', nome=r'Mars Reconnaissance|MRO'),
    dict(id='ODY', cmd='-53', tipo='fit', c='mars', nome=r'Odyssey'),
    dict(id='MEX', cmd='-41', tipo='fit', c='mars', nome=r'Mars Express|MEX'),
    dict(id='TGO', cmd='-143', tipo='fit', c='mars', nome=r'Trace Gas|ExoMars|TGO'),
    dict(id='HOPE', cmd='-62', tipo='fit', c='mars', nome=r'Hope|Emirates|EMM|Amal'),
    dict(id='JUNO', cmd='-61', tipo='fit', c='jupiter', nome=r'Juno'),
    dict(id='PSP', cmd='-96', tipo='kep', nome=r'Parker'),
    dict(id='SOLO', cmd='-144', tipo='kep', nome=r'Solar Orbiter|SolO'),
    dict(id='STA', cmd='-234', tipo='kep', nome=r'STEREO'),
    dict(id='JUICE', cmd='-28', tipo='kep', nome=r'JUICE|Jupiter Icy'),
    dict(id='CLIPPER', cmd='-159', tipo='kep', nome=r'Clipper'),
    dict(id='PSYCHE', cmd='-255', tipo='kep', nome=r'Psyche'),
    dict(id='LUCY', cmd='-49', tipo='kep', nome=r'Lucy'),
    dict(id='HERA', cmd='-91', tipo='kep', nome=r'Hera'),
    dict(id='APEX', cmd='-64', tipo='kep', nome=r'OSIRIS|APEX'),
    dict(id='HAY2', cmd='-37', tipo='kep', nome=r'Hayabusa'),
    dict(id='VGR1', cmd='-31', tipo='kep', nome=r'Voyager 1'),
    dict(id='VGR2', cmd='-32', tipo='kep', nome=r'Voyager 2'),
    dict(id='NH', cmd='-98', tipo='kep', nome=r'New Horizons'),
    dict(id='BEPI', cmd='-121', tipo='kep', nome=r'Bepi', cattura='mercury'),   # dopo l'inserimento in orbita i tratti sono attorno a Mercurio
    dict(id='SOHO', tipo='L', punto=1), dict(id='ACE', tipo='L', punto=1), dict(id='DSCOVR', tipo='L', punto=1),
    dict(id='ADITYA', tipo='L', punto=1), dict(id='JWST', tipo='L', punto=2), dict(id='EUCLID', tipo='L', punto=2),
]

GIORNI_ORBITER, GIORNI_CROCIERA = 90, 180     # quanto in avanti si guarda
CAMPIONI_MAX = 4000                           # campioni per richiesta
TOLL_FIT = 0.05                               # scarto ammesso per un orbiter, in frazioni del semiasse maggiore
SCARTO_MAX = 0.2                              # oltre questo scarto il risultato si butta e restano i dati di prima
TOLL_SOLE, TOLL_PIANETA = 2e-4, 0.02          # scarto ammesso per un tratto kepleriano, in frazioni della distanza
TRATTI_MAX = 60                               # per ciascuna fase (attorno al Sole, attorno al pianeta)


# ---------------------------------------------------------------- Horizons

class FineEffemeridi(Exception):
    """Horizons non ha effemeridi oltre (o prima di) un certo istante."""
    def __init__(self, jd, dopo):
        super().__init__(('dopo' if dopo else 'prima di') + ' JD %.4f' % jd)
        self.jd, self.dopo = jd, dopo


MESI = {m: i + 1 for i, m in enumerate('JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split())}


def jd_di(anno, mese, giorno, ore=0.0):
    a = (14 - mese) // 12
    y, m = anno + 4800 - a, mese + 12 * a - 3
    return giorno + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045 - 0.5 + ore / 24


def data_di(jd):
    """JD -> (anno, mese, giorno, ore, minuti), arrotondato al minuto."""
    z = int(math.floor(jd + 0.5 + 0.5 / 1440))
    f = jd + 0.5 + 0.5 / 1440 - z
    a = z + 32044
    b = (4 * a + 3) // 146097
    c = a - 146097 * b // 4
    d = (4 * c + 3) // 1461
    e = c - 1461 * d // 4
    m = (5 * e + 2) // 153
    minuti = int(f * 1440)
    return 100 * b + d - 4800 + m // 10, m + 3 - 12 * (m // 10), e - (153 * m + 2) // 5 + 1, minuti // 60, minuti % 60


def testo_data(jd):
    return '%04d-%02d-%02d %02d:%02d' % data_di(jd)


def leggi_risposta(testo):
    """Estrae nome del bersaglio e righe (jd, x, y, z, vx, vy, vz) da una risposta di Horizons in formato CSV."""
    if '$$SOE' not in testo:
        m = re.search(r'No ephemeris for target .*? (after|prior to) A\.D\. (\d{4})-([A-Za-z]{3})-(\d{2}) (\d{2}):(\d{2}):(\d{2})', testo)
        if m:
            jd = jd_di(int(m.group(2)), MESI[m.group(3).upper()], int(m.group(4)), int(m.group(5)) + int(m.group(6)) / 60 + int(m.group(7)) / 3600)
            raise FineEffemeridi(jd, m.group(1) == 'after')
        riga = next((r.strip() for r in testo.splitlines() if r.strip() and not r.startswith(('API', '*'))), '')
        raise RuntimeError('risposta senza tabella: ' + riga[:160])
    m = re.search(r'Target body name:\s*(.*?)\s*(\{|$)', testo, re.M)
    nome = m.group(1).strip() if m else ''
    righe = []
    for r in testo.split('$$SOE', 1)[1].split('$$EOE', 1)[0].splitlines():
        p = [x.strip() for x in r.split(',')]
        if len(p) < 8:
            continue
        try:
            righe.append((float(p[0]),) + tuple(float(x) for x in p[2:8]))
        except ValueError:
            continue
    if not righe:
        raise RuntimeError('tabella vuota')
    return nome, righe


def interroga(cmd, centro, jd_inizio, jd_fine, passo_min):
    """Vettori di stato della sonda rispetto al centro di un corpo: km e km/s, assi ICRF, tempi TDB."""
    par = {'format': 'text', 'COMMAND': "'%s'" % cmd, 'OBJ_DATA': 'NO', 'MAKE_EPHEM': 'YES', 'EPHEM_TYPE': 'VECTORS',
           'CENTER': "'%s'" % CENTRO[centro], 'REF_PLANE': 'FRAME', 'REF_SYSTEM': 'ICRF', 'OUT_UNITS': 'KM-S',
           'VEC_TABLE': '2', 'VEC_CORR': 'NONE', 'VEC_LABELS': 'NO', 'CSV_FORMAT': 'YES',
           'START_TIME': "'%s'" % testo_data(jd_inizio), 'STOP_TIME': "'%s'" % testo_data(jd_fine), 'STEP_SIZE': "'%d m'" % passo_min}
    url = API + '?' + urllib.parse.urlencode(par, quote_via=urllib.parse.quote)
    ultimo = None
    for n in range(3):
        try:
            rich = urllib.request.Request(url, headers={'User-Agent': AGENTE})
            with urllib.request.urlopen(rich, timeout=120) as r:
                testo = r.read().decode('utf-8', 'replace')
            time.sleep(0.5)                    # Horizons chiede di non sovrapporre le richieste
            return leggi_risposta(testo)
        except (FineEffemeridi, RuntimeError):
            raise
        except Exception as e:
            ultimo = e
            time.sleep(4 * (n + 1))
    raise RuntimeError('Horizons non raggiungibile: %s' % ultimo)


def campioni(sonda, centro, t0, fine, passo_min):
    """Come interroga, ma si ferma dove finiscono le effemeridi e controlla che il bersaglio sia quello atteso."""
    try:
        nome, righe = interroga(sonda['cmd'], centro, t0, fine, passo_min)
    except FineEffemeridi as e:
        if not e.dopo or e.jd - t0 < 2:
            raise RuntimeError('effemeridi non disponibili per questo periodo (%s)' % e)
        fine = e.jd - 10 / 1440
        nome, righe = interroga(sonda['cmd'], centro, t0, fine, passo_min)
    if not re.search(sonda['nome'], nome, re.I):
        raise RuntimeError('Horizons ha restituito «%s», non la sonda attesa' % nome)
    return righe


# ---------------------------------------------------------------- meccanica orbitale (stesse formule della pagina)

def base_corpo(corpo):
    """Terna equatoriale del corpo in componenti ICRF: Z sul polo, X sul nodo con l'equatore celeste."""
    ra, de = POLO[corpo][0] * D2R, POLO[corpo][1] * D2R
    Z = (math.cos(de) * math.cos(ra), math.cos(de) * math.sin(ra), math.sin(de))
    l = math.hypot(Z[0], Z[1])
    X = (-Z[1] / l, Z[0] / l, 0.0)
    Y = (Z[1] * X[2] - Z[2] * X[1], Z[2] * X[0] - Z[0] * X[2], Z[0] * X[1] - Z[1] * X[0])
    return X, Y, Z


def in_base(B, v):
    return tuple(B[k][0] * v[0] + B[k][1] * v[1] + B[k][2] * v[2] for k in range(3))


def da_base(B, v):
    return tuple(B[0][j] * v[0] + B[1][j] * v[1] + B[2][j] * v[2] for j in range(3))


def kepler_e(M, e):
    M = M % TAU
    E = M if e < 0.8 else math.pi
    for _ in range(60):
        d = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        E -= d
        if abs(d) < 1e-13:
            break
    return E


def kepler_h(M, e):
    H = math.asinh(M / e)
    for _ in range(80):
        d = (e * math.sinh(H) - H - M) / (e * math.cosh(H) - 1)
        H -= d
        if abs(d) < 1e-13:
            break
    return H


def perifocale(q, e, M):
    if e < 1:
        a, E = q / (1 - e), kepler_e(M, e)
        return a * (math.cos(E) - e), a * math.sqrt(1 - e * e) * math.sin(E)
    a, H = q / (e - 1), kepler_h(M, e)
    return a * (e - math.cosh(H)), a * math.sqrt(e * e - 1) * math.sinh(H)


def ruota(x, y, i, O, w):
    cO, sO, cw, sw, ci, si = math.cos(O), math.sin(O), math.cos(w), math.sin(w), math.cos(i), math.sin(i)
    return (x * (cO * cw - sO * sw * ci) - y * (cO * sw + sO * cw * ci),
            x * (sO * cw + cO * sw * ci) + y * (-sO * sw + cO * cw * ci),
            x * sw * si + y * cw * si)


def elementi(r, v, mu):
    """Elementi classici da posizione e velocità; angoli in radianti. Per l'iperbole a è negativo."""
    rm, vm = math.sqrt(sum(x * x for x in r)), math.sqrt(sum(x * x for x in v))
    rv = r[0] * v[0] + r[1] * v[1] + r[2] * v[2]
    h = (r[1] * v[2] - r[2] * v[1], r[2] * v[0] - r[0] * v[2], r[0] * v[1] - r[1] * v[0])
    hm = math.sqrt(sum(x * x for x in h))
    nx, ny = -h[1], h[0]
    nm = math.hypot(nx, ny)
    c1 = vm * vm - mu / rm
    ev = tuple((c1 * r[k] - rv * v[k]) / mu for k in range(3))
    e = math.sqrt(sum(x * x for x in ev))
    a = -mu / (2 * (vm * vm / 2 - mu / rm))
    ac = lambda x: math.acos(max(-1.0, min(1.0, x)))
    i = ac(h[2] / hm)
    O = ac(nx / nm) if nm > 1e-12 * hm else 0.0
    if ny < 0:
        O = TAU - O
    w = ac((nx * ev[0] + ny * ev[1]) / (nm * e)) if nm > 1e-12 * hm and e > 1e-12 else 0.0
    if ev[2] < 0:
        w = TAU - w
    nu = ac((ev[0] * r[0] + ev[1] * r[1] + ev[2] * r[2]) / (e * rm)) if e > 1e-12 else 0.0
    if rv < 0:
        nu = TAU - nu
    if e < 1:
        E = 2 * math.atan2(math.sqrt(1 - e) * math.sin(nu / 2), math.sqrt(1 + e) * math.cos(nu / 2))
        M = E - e * math.sin(E)
    else:
        H = 2 * math.atanh(max(-0.999999999999, min(0.999999999999, math.sqrt((e - 1) / (e + 1)) * math.tan(nu / 2))))
        M = e * math.sinh(H) - H
    return dict(a=a, e=e, i=i, O=O, w=w, nu=nu, M=M, rm=rm)


def avvolgi(x):
    """Riporta un angolo in radianti fra -pi e pi."""
    return (x + math.pi) % TAU - math.pi


def posizione_fit(p, jt):
    """Posizione ICRF rispetto al corpo, come la calcola la pagina per il tipo "fit"."""
    tau = jt - p['t0']
    Om, w = (p['om'][0] + p['om'][1] * tau) * D2R, (p['w'][0] + p['w'][1] * tau) * D2R
    u = (p['u'][0] + p['u'][1] * tau + p['u'][2] * tau * tau) * D2R
    x, y = perifocale(p['a'] * (1 - p['e']), p['e'], u - w)
    return da_base(base_corpo(p['c']), ruota(x, y, p['i'] * D2R, Om, w))


def posizione_kep(tratto, jt):
    """Posizione ICRF rispetto al corpo del tratto, come la calcola la pagina per il tipo "kep"."""
    k = tratto['k']
    a = abs(k[0] / (1 - k[1]))
    n = math.sqrt(GM[tratto['c']] / (a * a * a))
    x, y = perifocale(k[0], k[1], n * (jt - k[5]) * 86400)
    return ruota(x, y, k[2] * D2R, k[3] * D2R, k[4] * D2R)


def tratto_per(seg, jt):
    s = seg[0]
    for g in seg:
        if g['frm'] <= jt:
            s = g
        else:
            break
    return s


def cifre(x, n=9):
    return float('%.*g' % (n, x))


# ---------------------------------------------------------------- minimi quadrati (polinomi di grado 1 o 2)

def polinomio(t, y, grado):
    n = grado + 1
    A = [[sum(ti ** (r + c) for ti in t) for c in range(n)] for r in range(n)]
    b = [sum(yi * ti ** r for ti, yi in zip(t, y)) for r in range(n)]
    for i in range(n):                                   # eliminazione di Gauss con scambio di righe
        p = max(range(i, n), key=lambda r: abs(A[r][i]))
        A[i], A[p], b[i], b[p] = A[p], A[i], b[p], b[i]
        for r in range(i + 1, n):
            f = A[r][i] / A[i][i]
            for c in range(i, n):
                A[r][c] -= f * A[i][c]
            b[r] -= f * b[i]
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (b[i] - sum(A[i][c] * x[c] for c in range(i + 1, n))) / A[i][i]
    return x


# ---------------------------------------------------------------- orbiter: tipo "fit"

def adatta(corpo, righe, t0):
    """Elementi medi con derive, da campioni (jd, r, v) ICRF rispetto al corpo. Restituisce (voce, scarto massimo / a)."""
    mu, B = GM[corpo], base_corpo(corpo)
    el = [elementi(in_base(B, r[1:4]), in_base(B, r[4:7]), mu) for r in righe]
    if any(not (0 <= x['e'] < 1) for x in el):
        raise RuntimeError('orbita aperta rispetto a ' + corpo)
    t = [r[0] - t0 for r in righe]
    N = len(el)
    a, e, i = sum(x['a'] for x in el) / N, sum(x['e'] for x in el) / N, sum(x['i'] for x in el) / N
    n0 = math.sqrt(mu / a ** 3) * 86400                  # rad al giorno
    Om, u = [el[0]['O']], [el[0]['w'] + el[0]['M']]
    for k in range(1, N):
        Om.append(Om[-1] + avvolgi(el[k]['O'] - Om[-1]))
        previsto = u[-1] + n0 * (t[k] - t[k - 1])       # l'argomento di latitudine medio avanza quasi a velocità costante
        u.append(previsto + avvolgi(el[k]['w'] + el[k]['M'] - previsto))
    # Eccentricità e pericentro: su orbite quasi circolari i valori istantanei oscillano molto lungo ogni giro,
    # quindi si media il vettore eccentricità (e·cos ω, e·sin ω) su circa tre giri prima di ricavarli.
    passo = (t[-1] - t[0]) / (N - 1)
    meta = max(6, int(math.ceil(1.5 * (TAU / n0) / passo)))
    sx, sy = [0.0], [0.0]
    for x in el:
        sx.append(sx[-1] + x['e'] * math.cos(x['w']))
        sy.append(sy[-1] + x['e'] * math.sin(x['w']))
    tw, w, es = [], [], []
    for k in range(N):
        m = min(meta, k, N - 1 - k)
        if m < meta // 2 and N > 4 * meta:
            continue                                     # ai bordi la media copre troppo poco
        mx, my = (sx[k + m + 1] - sx[k - m]) / (2 * m + 1), (sy[k + m + 1] - sy[k - m]) / (2 * m + 1)
        ang = math.atan2(my, mx)
        tw.append(t[k]); es.append(math.hypot(mx, my)); w.append(ang if not w else w[-1] + avvolgi(ang - w[-1]))
    e = sum(es) / len(es)
    cO, cw, cu = polinomio(t, Om, 1), polinomio(tw, w, 1), polinomio(t, u, 2)
    giri = math.floor(cu[0] / TAU)
    voce = dict(c=corpo, type='fit', t0=t0, until=righe[-1][0], a=cifre(a), e=cifre(e), i=cifre(i * R2D),
                om=[cifre((cO[0] % TAU) * R2D), cifre(cO[1] * R2D)], w=[cifre(cw[0] * R2D), cifre(cw[1] * R2D)],
                u=[cifre((cu[0] - giri * TAU) * R2D), cifre(cu[1] * R2D), cifre(cu[2] * R2D)])
    peggio = 0.0
    for r in righe:
        p = posizione_fit(voce, r[0])
        peggio = max(peggio, math.dist(p, r[1:4]) / a)
    return voce, peggio


def orbiter(sonda, t0):
    corpo = sonda['c']
    primo = campioni(sonda, corpo, t0, t0 + 1 / 24, 30)
    e0 = elementi(primo[0][1:4], primo[0][4:7], GM[corpo])
    if not (e0['a'] > 0):
        raise RuntimeError('orbita aperta rispetto a ' + corpo)
    periodo_min = TAU * math.sqrt(e0['a'] ** 3 / GM[corpo]) / 60
    passo = int(max(5, min(360, periodo_min / 40), math.ceil(GIORNI_ORBITER * 1440 / CAMPIONI_MAX)))
    righe = campioni(sonda, corpo, t0, t0 + GIORNI_ORBITER, passo)
    durata = righe[-1][0] - t0
    # Scarto di fondo: quello che resta su pochi giri, dovuto alle oscillazioni che il modello non descrive.
    breve = min(durata, max(3.0, 3 * periodo_min / 1440))
    _, fondo = adatta(corpo, [r for r in righe if r[0] - t0 <= breve + 1e-9], t0)
    soglia = max(TOLL_FIT, 2 * fondo)
    while True:                                          # se l'orbita cambia troppo, si accorcia la finestra finché il modello la segue
        finestra = [r for r in righe if r[0] - t0 <= durata + 1e-9]
        voce, scarto = adatta(corpo, finestra, t0)
        if scarto <= soglia or durata <= 5:
            break
        durata = max(5.0, durata / 2)
    if scarto > SCARTO_MAX:
        raise RuntimeError('il modello non segue le effemeridi (scarto %.0f%% del semiasse)' % (100 * scarto))
    voce = dict(id=sonda['id'], **voce)
    return voce, 'finestra %.0f giorni, scarto massimo %.1f%% del semiasse' % (durata, 100 * scarto)


# ---------------------------------------------------------------- crociera: tipo "kep"

def kepleriani(riga, corpo):
    """[q, e, i, Ω, ω (gradi, assi ICRF), Tp (JD TDB)] dallo stato a un istante."""
    mu = GM[corpo]
    x = elementi(riga[1:4], riga[4:7], mu)
    n = math.sqrt(mu / abs(x['a']) ** 3) * 86400         # rad al giorno
    M = avvolgi(x['M']) if x['e'] < 1 else x['M']
    return [cifre(x['a'] * (1 - x['e'])), cifre(x['e']), cifre(x['i'] * R2D), cifre(x['O'] * R2D), cifre(x['w'] * R2D), cifre(riga[0] - M / n, 12)]


def spezza(righe, corpo, toll, minimo_km):
    """Divide i campioni in tratti kepleriani: ogni tratto usa gli elementi osculanti al suo istante centrale."""
    tratti, s, N = [], 0, len(righe)
    while s < N - 1:
        e = N - 1
        while True:
            k = kepleriani(righe[(s + e) // 2], corpo)
            tr = dict(frm=righe[s][0], c=corpo, k=k)
            ok = all(math.dist(posizione_kep(tr, r[0]), r[1:4]) <= max(minimo_km, toll * math.sqrt(sum(x * x for x in r[1:4]))) for r in righe[s:e + 1])
            if ok or e <= s + 1:
                break
            e = s + max(1, (e - s) // 2)
        tratti.append(tr)
        s = e
    return tratti


def spezza_entro(righe, corpo, toll, minimo_km):
    for _ in range(4):                                   # troppi tratti: si allarga la tolleranza
        tratti = spezza(righe, corpo, toll, minimo_km)
        if len(tratti) <= TRATTI_MAX:
            return tratti
        toll, minimo_km = toll * 3, minimo_km * 3
    # ancora troppi (orbita che cambia di continuo): tratti di uguale durata, ciascuno con gli elementi del suo istante centrale
    N = len(righe)
    lungo = -(-(N - 1) // TRATTI_MAX)
    return [dict(frm=righe[s][0], c=corpo, k=kepleriani(righe[min(N - 1, s + lungo // 2)], corpo)) for s in range(0, N - 1, lungo)]


def crociera(sonda, t0):
    righe = campioni(sonda, 'sun', t0, t0 + GIORNI_CROCIERA, 360)
    fine = righe[-1][0]
    tratti, nota = [], ''
    pianeta = sonda.get('cattura')
    vicino = []
    if pianeta:
        passo = int(max(30, math.ceil((fine - t0) * 1440 / CAMPIONI_MAX)))
        vicino = campioni(sonda, pianeta, t0, fine, passo)
        mu, legato = GM[pianeta], len(vicino)
        for k in reversed(range(len(vicino))):           # da quale campione in poi resta legata al pianeta
            r, v = vicino[k][1:4], vicino[k][4:7]
            rm = math.sqrt(sum(x * x for x in r))
            if sum(x * x for x in v) / 2 - mu / rm < 0 and rm < SFERA[pianeta]:
                legato = k
            else:
                break
        vicino = vicino[legato:]
    if len(vicino) >= 2:
        t_catt = vicino[0][0]
        prima = [r for r in righe if r[0] < t_catt]
        if len(prima) >= 2:
            tratti = spezza_entro(prima, 'sun', TOLL_SOLE, 2000.0)
        tratti += spezza_entro(vicino, pianeta, TOLL_PIANETA, 50.0)
        fine = vicino[-1][0]
        nota = ', in orbita attorno a %s dal JD %.2f' % (pianeta, t_catt)
    else:
        tratti = spezza_entro(righe, 'sun', TOLL_SOLE, 2000.0)
    tratti[0]['frm'] = 0
    voce = dict(id=sonda['id'], type='kep', until=fine, seg=tratti)
    return voce, '%d tratt%s fino al JD %.1f%s' % (len(tratti), 'o' if len(tratti) == 1 else 'i', fine, nota)


# ---------------------------------------------------------------- programma

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--file', default=str(RADICE / 'data' / 'probes.json'), help='file da aggiornare (predefinito: data/probes.json del sito)')
    ap.add_argument('--solo', default='', help='sigle da aggiornare, separate da virgola (predefinito: tutte)')
    ap.add_argument('--prova', action='store_true', help='calcola e stampa, ma non scrive il file')
    ap.add_argument('--in-linea', default='', metavar='INDIRIZZO', help='indirizzo del sito già pubblicato, da cui riprendere i dati se più recenti')
    arg = ap.parse_args()
    percorso = pathlib.Path(arg.file)
    try:
        doc = json.loads(percorso.read_text(encoding='utf-8'))
    except Exception:
        doc = {}
    if arg.in_linea:
        try:
            rich = urllib.request.Request(arg.in_linea.rstrip('/') + '/data/probes.json', headers={'User-Agent': AGENTE})
            with urllib.request.urlopen(rich, timeout=60) as r:
                linea = json.loads(r.read().decode('utf-8'))
            if isinstance(linea.get('probes'), list) and str(linea.get('generated', '')) > str(doc.get('generated', '')):
                doc = linea
                if not arg.prova:
                    percorso.write_text(json.dumps(doc, separators=(',', ':')) + '\n', encoding='utf-8')
                print('Riprese dal sito in linea le sonde del', doc['generated'])
        except Exception as e:
            print('Sito in linea: nessun dato delle sonde da riprendere (%s)' % e)
    vecchie = {p['id']: p for p in doc.get('probes', []) if isinstance(p, dict) and 'id' in p}
    solo = {s.strip().upper() for s in arg.solo.split(',') if s.strip()}
    oggi = datetime.datetime.now(datetime.timezone.utc)
    t0 = jd_di(oggi.year, oggi.month, oggi.day)          # mezzanotte di oggi
    nuove, riuscite, fallite = [], 0, 0
    for s in SONDE:
        if s['tipo'] == 'L':
            nuove.append(dict(id=s['id'], type='L', point=s['punto']))
            continue
        if solo and s['id'] not in solo:
            if s['id'] in vecchie:
                nuove.append(vecchie[s['id']])
            continue
        try:
            voce, nota = (orbiter if s['tipo'] == 'fit' else crociera)(s, t0)
            nuove.append(voce)
            riuscite += 1
            print('%-8s aggiornata: %s' % (s['id'], nota))
        except Exception as e:
            fallite += 1
            if s['id'] in vecchie:
                nuove.append(vecchie[s['id']])
            print('%-8s NON aggiornata (%s): %s' % (s['id'], 'restano i dati di prima' if s['id'] in vecchie else 'nessun dato', e))
    note = {s['id'] for s in SONDE}
    nuove += [p for i, p in vecchie.items() if i not in note]      # voci aggiunte a mano nel file: restano
    print('%d sonde aggiornate, %d non aggiornate.' % (riuscite, fallite))
    if not riuscite:
        print('Horizons non ha dato nulla di utilizzabile: il file resta come è.')
        return 1
    if arg.prova:
        return 0
    doc = {'generated': '%04d-%02d-%02d' % (oggi.year, oggi.month, oggi.day), 'source': 'JPL Horizons',
           'frame': 'ICRF; type fit: body equator of date, node from ICRF equator; times TDB', 'probes': nuove}
    percorso.write_text(json.dumps(doc, separators=(',', ':')) + '\n', encoding='utf-8')
    print('Scritto', percorso)
    return 0


if __name__ == '__main__':
    sys.exit(main())
