#!/usr/bin/env python3
"""Scarica da CelesTrak gli indici di attività solare e geomagnetica (SW-All.csv) e scrive data/meteo_spaziale.json,
usato dal modello di atmosfera NRLMSISE-00 dell'app.

Per ogni giorno dal 1° gennaio 2000: flusso solare F10.7 osservato (sfu), la sua media su 81 giorni centrata, Ap giornaliero;
poi le previsioni giornaliere (45 giorni) e mensili (fino a una ventina d'anni) pubblicate da CelesTrak.
Fonte: CelesTrak, T.S. Kelso, «Space Weather Data», https://celestrak.org/SpaceData/ (dati NOAA/SWPC, GFZ Potsdam, NRCan).

Uso:   python3 strumenti/aggiorna_meteo_spaziale.py                 (dalla cartella del sito; scarica e riscrive il file)
       python3 strumenti/aggiorna_meteo_spaziale.py --file SW-All.txt [SW-Last5Years.txt ...]
                                                   (copie locali, formato .csv o .txt di CelesTrak; i file successivi aggiornano i precedenti)
Serve solo Python 3, senza librerie aggiuntive. Una richiesta al giorno, come chiede CelesTrak.
"""
import csv, datetime as dt, io, json, pathlib, sys, urllib.request

RADICE = pathlib.Path(__file__).resolve().parent.parent
URL = 'https://celestrak.org/SpaceData/SW-All.csv'
INIZIO = dt.date(2000, 1, 1)

def jd(d):
    return (d - dt.date(2000, 1, 1)).days + 2451544.5   # giorno civile alle 0h UT

def leggi_csv(testo):
    giorni, mesi = {}, []
    for r in csv.DictReader(io.StringIO(testo)):
        d = dt.date.fromisoformat(r['DATE'])
        tipo = (r.get('F10.7_DATA_TYPE') or '').strip()
        def num(k):
            v = (r.get(k) or '').strip()
            return float(v) if v else None
        f, c, ap = num('F10.7_OBS'), num('F10.7_OBS_CENTER81'), num('AP_AVG')
        if tipo == 'PRM':
            if f is not None: mesi.append((d, f, c if c is not None else f))
        elif f is not None:
            giorni[d] = (f, c if c is not None else f, ap, 'P' if tipo == 'PRD' else 'O')
    return giorni, mesi

def leggi_txt(testo):
    giorni, mesi, sez = {}, [], None
    for riga in testo.splitlines():
        if riga.startswith('BEGIN '): sez = riga.split()[1]; continue
        if riga.startswith('END '): sez = None; continue
        if not sez or not riga.strip() or riga.startswith('#'): continue
        d = dt.date(int(riga[0:4]), int(riga[5:7]), int(riga[8:10]))
        campo = lambda a, b: float(riga[a:b]) if riga[a:b].strip() else None
        if sez == 'MONTHLY_PREDICTED':
            f, c = campo(112, 118), campo(118, 124)       # F10.7 osservato e media centrata su 81 giorni
            if f is not None: mesi.append((d, f, c if c is not None else f))
        elif sez in ('OBSERVED', 'DAILY_PREDICTED'):
            ap, f, c = campo(79, 83), campo(112, 118), campo(118, 124)
            if f is not None: giorni[d] = (f, c if c is not None else f, ap, 'O' if sez == 'OBSERVED' else 'P')
    return giorni, mesi

def scrivi(giorni, mesi, fonte):
    d0 = max(INIZIO, min(giorni)); ultimo = max(giorni)
    F, C, A = [], [], []; n_oss = 0; d = d0; prec = None
    while d <= ultimo:
        v = giorni.get(d) or prec
        F.append(round(v[0], 1)); C.append(round(v[1], 1)); A.append(round(v[2] if v[2] is not None else 12))
        if v[3] == 'O' and d in giorni: n_oss = len(F)
        prec = v; d += dt.timedelta(days=1)
    M = [[jd(m[0]), round(m[1], 1), round(m[2], 1)] for m in mesi if m[0] > ultimo]
    out = {'fonte': 'CelesTrak, Space Weather Data (NOAA/SWPC, GFZ, NRCan): ' + fonte, 'aggiornato': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
           'jd0': jd(d0), 'osservati': n_oss, 'f107': F, 'f107c81': C, 'ap': A, 'mensili': M,
           'nota': 'f107: flusso solare a 10,7 cm osservato (sfu); f107c81: media su 81 giorni centrata; ap: Ap giornaliero. '
                   'I primi «osservati» giorni sono misure, gli altri previsioni giornaliere; «mensili»: [JD, F10.7, media 81 giorni] previsti.'}
    p = RADICE / 'data' / 'meteo_spaziale.json'
    p.write_text(json.dumps(out, separators=(',', ':')))
    print('Scritto', p, '-', len(F), 'giorni da', d0, 'a', ultimo, '(osservati', n_oss, '),', len(M), 'mesi previsti')

if __name__ == '__main__':
    if '--file' in sys.argv:
        nomi = sys.argv[sys.argv.index('--file') + 1:]; testi = [pathlib.Path(f).read_text() for f in nomi]; fonte = ', '.join(pathlib.Path(f).name for f in nomi)
    else:
        req = urllib.request.Request(URL, headers={'User-Agent': 'AtlanteOrbitale/1.0 (aggiornamento giornaliero, GitHub Actions)'})
        testi = [urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')]; fonte = URL
    giorni, mesi = {}, []
    for testo in testi:
        g, m = (leggi_csv(testo) if testo.lstrip().startswith('DATE') else leggi_txt(testo))
        oss = max((d for d, v in g.items() if v[3] == 'O'), default=None)
        giorni = {d: v for d, v in giorni.items() if oss is None or d <= oss or v[3] == 'O'}   # le previsioni vecchie lasciano il posto alle misure
        giorni.update(g); mesi = m or mesi
    if len(giorni) < 1000: sys.exit('Dati di meteo spaziale incompleti: file non aggiornato.')
    scrivi(giorni, mesi, fonte)
