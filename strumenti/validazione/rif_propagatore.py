#!/usr/bin/env python3
"""Riferimento indipendente per il propagatore numerico di Keplario.

Stessi modelli fisici, scritti con librerie diverse da quelle della pagina:
  - gravità della Terra EGM2008: pyshtools (SHTOOLS, MakeGravGridPoint), non il codice della pagina;
  - rotazione della Terra: ERFA (IAU 2006/2000A, matrice GCRS→ITRS con c2t06a, UT1 = UTC, moto del polo nullo);
  - effemeridi di Sole, Luna e pianeti: JPL DE421 (jplephem), non Astronomy Engine;
  - densità: NRLMSISE-00 di pymsis; integratore: SciPy DOP853 con tolleranze strette.
La relatività (termine di Schwarzschild, IERS 2010 eq. 10.12), le maree solide (IERS 2010 eq. 6.6, gradi 2) e l'ombra conica
sono riscritte qui da capo seguendo le stesse formule pubblicate.

Uso:  python3 rif_propagatore.py casi.json uscita.json [--tabelle tabelle.json]
casi.json:  [{nome, epoca (ISO UTC), y0 [km, km/s, EQJ], durata_s, passo_uscita_s, N, terzi: [...], rel, maree, srp: {CrAm}|null, drag: {CdAm, f107, f107a, ap}|null}]
--tabelle scrive anche le effemeridi DE421 e la rotazione ERFA campionate come le vuole il motore della pagina,
così la stessa propagazione si può rifare nel motore con gli stessi dati d'ingresso (controllo dell'implementazione).
"""
import json, sys, base64, pathlib
import numpy as np, erfa, pyshtools as pysh
from jplephem.spk import SPK
from scipy.integrate import solve_ivp

RADICE = pathlib.Path(__file__).resolve().parent.parent.parent
BSP = sys.argv[sys.argv.index('--bsp') + 1] if '--bsp' in sys.argv else '/tmp/gmat/application/data/planetary_ephem/spk/de421.bsp'
kern = SPK.open(BSP)
GM = dict(sun=132712440041.279, moon=4902.800118, venus=324858.592, mars=42828.374857, jupiter=126686531.9, saturn=37931206.2, mercury=22031.8686)
NAIF = dict(sun=10, mercury=1, venus=2, mars=4, jupiter=5, saturn=6)
AU = 149597870.7; CL = 299792.458; P1AU = 4.54e-6; R_SUN = 695700.0


def campo():
    j = json.load(open(RADICE / 'data/gravita_terra.json'))
    v = np.frombuffer(base64.b64decode(j['dati']), '<f8'); N = j['grado']
    cilm = np.zeros((2, N + 1, N + 1)); i = 0
    for n in range(N + 1):
        for m in range(n + 1):
            cilm[0, n, m] = v[2 * i]; cilm[1, n, m] = v[2 * i + 1]; i += 1
    return cilm, j['gm_km3s2'], j['raggio_km']


CILM, GM_E, R_E = campo()


def tempi(jd_utc):
    tai1, tai2 = erfa.utctai(jd_utc, 0.0)
    tt1, tt2 = erfa.taitt(tai1, tai2)
    return tt1, tt2


def pos_geo(k, tt1, tt2):
    """posizione geocentrica, km, ICRF (DE421; TDB ≈ TT)"""
    jd = tt1 + tt2
    e = kern[3, 399].compute(jd) + kern[0, 3].compute(jd)
    if k == 'moon':
        return kern[3, 301].compute(jd) - kern[3, 399].compute(jd)
    if k == 'sun':
        return kern[0, 10].compute(jd) - e
    return kern[0, NAIF[k]].compute(jd) - e


def c2t(jd_utc):
    tt1, tt2 = tempi(jd_utc)
    return erfa.c2t06a(tt1, tt2, jd_utc, 0.0, 0.0, 0.0)   # UT1 = UTC, moto del polo nullo


def frazione_luce(r_sc, r_corpo, R, s_sole):
    """frazione del disco solare visibile (ombra conica), scritta da capo: area dell'intersezione di due dischi"""
    d = r_sc - r_corpo; s = s_sole - r_sc
    a = np.arcsin(min(1, R_SUN / np.linalg.norm(s))); b = np.arcsin(min(1, R / np.linalg.norm(d)))
    c = np.arccos(np.clip(np.dot(-d, s) / (np.linalg.norm(d) * np.linalg.norm(s)), -1, 1))
    if c >= a + b: return 1.0
    if c <= abs(a - b):
        return 0.0 if b >= a else 1 - (b / a) ** 2
    x = (c * c + a * a - b * b) / (2 * c); y = np.sqrt(max(0.0, a * a - x * x))
    area = a * a * np.arccos(np.clip(x / a, -1, 1)) + b * b * np.arccos(np.clip((c - x) / b, -1, 1)) - c * y
    return 1 - area / (np.pi * a * a)


def maree(Rm, tt1, tt2, jd_utc):
    """ΔC̄2m, ΔS̄2m (IERS 2010 eq. 6.6, numeri di Love anelastici della tabella 6.3)"""
    k = [(0.30190, 0.0), (0.29830, -0.00144), (0.30102, -0.00130)]
    dC = np.zeros(3); dS = np.zeros(3)
    for b in ('moon', 'sun'):
        p = Rm @ pos_geo(b, tt1, tt2); r = np.linalg.norm(p); lat = np.arcsin(p[2] / r); lon = np.arctan2(p[1], p[0])
        f = GM[b] / GM_E * (R_E / r) ** 3
        P = pysh.legendre.PlmBar(2, np.sin(lat))   # P̄lm normalizzate 4π, indice l(l+1)/2 + m
        Pn = [P[3 + m] for m in range(3)]
        for m in range(3):
            dC[m] += f / 5 * Pn[m] * (k[m][0] * np.cos(m * lon) + k[m][1] * np.sin(m * lon))
            dS[m] += f / 5 * Pn[m] * (k[m][0] * np.sin(m * lon) - k[m][1] * np.cos(m * lon))
    return dC, dS


def accel_caso(caso):
    import datetime
    ep = datetime.datetime.fromisoformat(caso['epoca'].replace('Z', '+00:00'))
    jd0 = 2440587.5 + ep.timestamp() / 86400
    N = caso['N']; cil = CILM[:, :N + 1, :N + 1].copy(); cil[0, 0, 0] = 0
    terzi = caso.get('terzi', [])
    if caso.get('drag'):
        import pymsis

    def f(t, y):
        r = y[:3]; v = y[3:]; jd = jd0 + t / 86400; tt1, tt2 = tempi(jd)
        rn = np.linalg.norm(r); a = -GM_E * r / rn ** 3
        Rm = c2t(jd)
        if N >= 2:
            cl = cil
            if caso.get('maree'):
                cl = cil.copy(); dC, dS = maree(Rm, tt1, tt2, jd)
                for m in range(3): cl[0, 2, m] += dC[m]; cl[1, 2, m] += dS[m]
            p = Rm @ r; rr = np.linalg.norm(p); lat = np.degrees(np.arcsin(p[2] / rr)); lon = np.degrees(np.arctan2(p[1], p[0]))
            g = pysh.gravmag.MakeGravGridPoint(cl, GM_E * 1e9, R_E * 1e3, rr * 1e3, lat, lon, lmax=N)
            th = np.radians(90 - lat); la = np.radians(lon)
            rh = np.array([np.sin(th) * np.cos(la), np.sin(th) * np.sin(la), np.cos(th)])
            tth = np.array([np.cos(th) * np.cos(la), np.cos(th) * np.sin(la), -np.sin(th)]); ph = np.array([-np.sin(la), np.cos(la), 0])
            a = a + Rm.T @ ((g[0] * rh + g[1] * tth + g[2] * ph) / 1e3)
        for b in terzi:
            s = pos_geo(b, tt1, tt2); d = s - r
            a = a + GM[b] * (d / np.linalg.norm(d) ** 3 - s / np.linalg.norm(s) ** 3)
        if caso.get('rel'):
            v2 = v @ v; a = a + GM_E / (CL ** 2 * rn ** 3) * ((4 * GM_E / rn - v2) * r + 4 * (r @ v) * v)
        if caso.get('srp'):
            s = pos_geo('sun', tt1, tt2); lit = frazione_luce(r, np.zeros(3), 6378.137, s)
            lit = min(lit, frazione_luce(r, pos_geo('moon', tt1, tt2), 1737.4, s))
            u = (s - r) / np.linalg.norm(s - r); P = P1AU * (AU / np.linalg.norm(s - r)) ** 2 * lit
            a = a - P * caso['srp']['CrAm'] / 1000 * u
        if caso.get('drag'):
            D = caso['drag']; p = Rm @ r
            lon, lat, h = erfa.gc2gd(1, p * 1000)
            import datetime as dt
            when = np.datetime64(int(round((jd - 2440587.5) * 86400e6)), 'us')
            rho = pymsis.calculate(when, np.degrees(lon), np.degrees(lat), h / 1000, f107s=[D['f107']], f107as=[D['f107a']], aps=[[D['ap']] * 7], version=0).ravel()[0]
            w = np.array([0, 0, 7.2921159e-5]); wz = Rm.T @ w     # asse di rotazione in GCRS
            vr = v - np.cross(wz, r); vm = np.linalg.norm(vr)
            a = a - 0.5 * rho * D['CdAm'] * vm * 1000 * vr
        return np.concatenate([v, a])
    return f, jd0


def tabelle(caso):
    """effemeridi DE421 e rotazione ERFA campionate per il motore della pagina"""
    import datetime
    ep = datetime.datetime.fromisoformat(caso['epoca'].replace('Z', '+00:00')); jd0 = 2440587.5 + ep.timestamp() / 86400
    out = {'terzi': {}, 'pn': None, 'th': None}
    for b in caso.get('terzi', []) + ['sun']:
        h = 10800.0 if b == 'moon' else 86400.0; lo = -3 * 3600 - h; n = int(np.ceil((caso['durata_s'] + 3 * 3600 - lo) / h)) + 4
        d = [list(pos_geo(b, *tempi(jd0 + (lo + i * h) / 86400))) for i in range(n)]
        out['terzi'][b] = {'t0': lo, 'h': h, 'n': n, 'm': 3, 'd': sum(d, [])}
    h = 43200.0; lo = -3 * 3600 - h; n = int(np.ceil((caso['durata_s'] + 3 * 3600 - lo) / h)) + 4
    pn = []; th = []; W = 7.2921158553e-5; prev = None
    for i in range(n):
        jd = jd0 + (lo + i * h) / 86400; tt1, tt2 = tempi(jd)
        npb = erfa.pnm06a(tt1, tt2)              # GCRS → vero equatore e equinozio della data
        g = erfa.gst06a(jd, 0.0, tt1, tt2)       # tempo siderale apparente di Greenwich
        if prev is not None:
            g += np.round((prev + W * h - g) / (2 * np.pi)) * 2 * np.pi   # svolge l'angolo: avanza di circa W·h
        prev = g
        pn += list(npb.ravel()); th.append(g - W * i * h)
    out['pn'] = {'t0': lo, 'h': h, 'n': n, 'm': 9, 'd': pn}; out['th'] = {'t0': lo, 'h': h, 'n': n, 'm': 1, 'd': th, 'lin': [W]}
    return out


def main():
    casi = json.load(open(sys.argv[1])); res = {}; tab = {}
    for caso in casi:
        f, jd0 = accel_caso(caso)
        te = np.arange(0, caso['durata_s'] + 1e-9, caso['passo_uscita_s'])
        sol = solve_ivp(f, (0, caso['durata_s']), np.array(caso['y0'], float), method='DOP853', rtol=1e-13, atol=1e-10, t_eval=te)
        res[caso['nome']] = {'t': sol.t.tolist(), 'y': sol.y.T.tolist(), 'nfev': int(sol.nfev)}
        print('%-28s %6d valutazioni, stato finale %s' % (caso['nome'], sol.nfev, np.round(sol.y[:3, -1], 4)))
        if '--tabelle' in sys.argv: tab[caso['nome']] = tabelle(caso)
    json.dump(res, open(sys.argv[2], 'w'))
    if '--tabelle' in sys.argv: json.dump(tab, open(sys.argv[sys.argv.index('--tabelle') + 1], 'w'))


if __name__ == '__main__':
    main()
