#!/usr/bin/env python3
"""Converte i modelli del campo di gravità nei file data/gravita_<corpo>.json usati dal propagatore numerico.

Coefficienti completamente normalizzati C̄nm, S̄nm, troncati al grado indicato. Nel file JSON sono in base64
(Float64, little endian), alternati C, S, nell'ordine n = 0…N, m = 0…n (indice n(n+1)/2 + m).

Fonti (file originali nella cartella indicata con --sorgenti):
  Terra   EGM2008 (NGA; Pavlis et al. 2012), tide-free, troncato a 120 × 120   EGM2008_120.gfc  (formato ICGEM)
  Luna    GRGM900C (GRAIL, NASA GSFC; Lemoine et al. 2014), assi principali, troncato a 100 × 100   grgm900c.cof  (formato GMAT)
  Marte   GMM-2B (NASA GSFC; Lemoine et al. 2001), 80 × 80                    GMM2B.cof
  Venere  MGNP180U (Magellan, NASA JPL; Konopliv et al. 1999), 70 × 70        MGNP180U.cof

Uso:  python3 strumenti/gravita/converti_campi.py --sorgenti CARTELLA
"""
import argparse, base64, json, pathlib, re, struct

RADICE = pathlib.Path(__file__).resolve().parent.parent.parent
NUM = re.compile(r'[-+]?\d+\.\d*(?:[eEdD][-+]?\d+)?')

CAMPI = {
    'terra': dict(file='EGM2008_120.gfc', N=120, nome='EGM2008', formato='icgem',
                  fonte='EGM2008, National Geospatial-Intelligence Agency (Pavlis, Holmes, Kenyon, Factor, J. Geophys. Res. 117, B04406, 2012); sistema tide-free',
                  assi='ITRF (terrestre)'),
    'luna': dict(file='grgm900c.cof', N=100, nome='GRGM900C', formato='gmat',
                 fonte='GRGM900C, missione GRAIL, NASA Goddard (Lemoine et al., Geophys. Res. Lett. 41, 2014), dal Planetary Data System',
                 assi='assi principali di inerzia della Luna (DE430 PA)'),
    'marte': dict(file='GMM2B.cof', N=80, nome='GMM-2B', formato='gmat',
                  fonte='GMM-2B, Mars Global Surveyor, NASA Goddard (Lemoine et al., J. Geophys. Res. 106, 2001), dal Planetary Data System',
                  assi='IAU 2000 di Marte'),
    'venere': dict(file='MGNP180U.cof', N=70, nome='MGNP180U', formato='gmat',
                   fonte='MGNP180U, Magellan e Pioneer Venus Orbiter, NASA JPL (Konopliv, Banerdt, Sjogren, Icarus 139, 1999), dal Planetary Data System',
                   assi='IAU di Venere'),
}


def leggi(percorso, formato, N):
    C, S, gm, R = {}, {}, None, None
    for riga in percorso.read_text(encoding='latin1').splitlines():
        if formato == 'icgem':
            if riga.startswith('earth_gravity_constant'):
                gm = float(riga.split()[1].replace('D', 'E')) / 1e9
            elif riga.startswith('radius'):
                R = float(riga.split()[1].replace('D', 'E')) / 1e3
            elif riga.startswith('gfc'):
                p = riga.split()
                n, m = int(p[1]), int(p[2])
                if n <= N:
                    C[n, m] = float(p[3].replace('D', 'E').replace('d', 'E'))
                    S[n, m] = float(p[4].replace('D', 'E').replace('d', 'E'))
        else:
            if riga.startswith('POTFIELD'):
                v = NUM.findall(riga[16:])
                gm, R = float(v[0]) / 1e9, float(v[1]) / 1e3
            elif riga.startswith('RECOEF'):
                n, m = int(riga[6:11]), int(riga[11:14])
                v = NUM.findall(riga[14:])
                if n <= N:
                    C[n, m] = float(v[0])
                    S[n, m] = float(v[1]) if len(v) > 1 else 0.0
    C[0, 0] = 1.0
    return C, S, gm, R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sorgenti', required=True)
    a = ap.parse_args()
    for chiave, d in CAMPI.items():
        C, S, gm, R = leggi(pathlib.Path(a.sorgenti) / d['file'], d['formato'], d['N'])
        N = d['N']
        mancano = [(n, m) for n in range(2, N + 1) for m in range(n + 1) if (n, m) not in C]
        if mancano:
            raise SystemExit('%s: mancano %d coefficienti, per esempio %s' % (chiave, len(mancano), mancano[:3]))
        val = []
        for n in range(N + 1):
            for m in range(n + 1):
                val += [C.get((n, m), 0.0), S.get((n, m), 0.0)]
        dati = base64.b64encode(struct.pack('<%dd' % len(val), *val)).decode()
        out = dict(modello=d['nome'], fonte=d['fonte'], assi=d['assi'], gm_km3s2=gm, raggio_km=R, grado=N,
                   normalizzazione='completa (4π)', ordine='n = 0…N, m = 0…n; C e S alternati', dati=dati)
        f = RADICE / 'data' / ('gravita_%s.json' % chiave)
        f.write_text(json.dumps(out, ensure_ascii=False), encoding='utf-8')
        print('%-7s %-9s grado %3d  GM %.6f km³/s²  R %.4f km  C20 %.12e  -> %s (%d kB)' % (chiave, d['nome'], N, gm, R, C[2, 0], f.name, f.stat().st_size // 1024))


if __name__ == '__main__':
    main()
