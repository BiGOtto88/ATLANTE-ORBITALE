#!/usr/bin/env node
/* Prove automatiche del motore di calcolo di Atlante Orbitale (il blocco <script id="motore"> di index.html).
   Girano senza browser, con Node 18 o più recente, e senza rete. Le esegue il flusso GitHub «Verifica» a ogni modifica.

   Uso:  node strumenti/prove/prova_motore.js [index.html] [--rif uscita_riferimento.json]
   Con --rif confronta il propagatore anche con il riferimento indipendente appena ricalcolato in Python
   (strumenti/validazione/rif_propagatore.py: SHTOOLS, ERFA, DE421, SciPy); senza, usa quello salvato nel repository.

   Ogni prova stampa il valore ottenuto e la tolleranza; il programma esce con codice 1 se anche una sola non passa. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const RADICE = path.resolve(__dirname, '..', '..');
const args = process.argv.slice(2), pagina = args.find(a => !a.startsWith('--') && a.endsWith('.html')) || path.join(RADICE, 'index.html');
const iRif = args.indexOf('--rif'), fileRif = iRif >= 0 ? args[iRif + 1] : path.join(RADICE, 'strumenti/validazione/propagatore/rif.json');
const VAL = path.join(RADICE, 'strumenti/validazione/propagatore');

// ---- motore e Astronomy Engine in un contesto isolato
const html = fs.readFileSync(pagina, 'utf8'), a = html.indexOf('<script id="motore">'), b = html.indexOf('</script>', a);
if (a < 0) { console.error('Nella pagina non trovo il blocco <script id="motore">'); process.exit(1); }
const ctx = { console, Math, Date, Float64Array, Float32Array, Uint8Array, Array, Object, JSON, Error, isFinite, Infinity, NaN, window: {} };
vm.createContext(ctx);
vm.runInContext(html.slice(a + '<script id="motore">'.length, b) + ';this.Motore=Motore;', ctx);
vm.runInContext(fs.readFileSync(path.join(RADICE, 'vendor/astronomy.browser.min.js'), 'utf8'), ctx);
const M = ctx.Motore, A = ctx.window.Astronomy || ctx.Astronomy;
const BODIES = { sun: { gm: 132712440041.279, R: 695700, ab: 'Sun' }, mercury: { gm: 22031.8686, R: 2439.7, ab: 'Mercury' }, venus: { gm: 324858.592, R: 6051.8, ab: 'Venus' }, earth: { gm: 398600.4418, R: 6378.137, ab: 'Earth' },
  moon: { gm: 4902.800118, R: 1737.4, ab: 'Moon' }, mars: { gm: 42828.374857, R: 3396.19, ab: 'Mars' }, jupiter: { gm: 126686531.9, R: 71492, ab: 'Jupiter' }, saturn: { gm: 37931206.2, R: 60268, ab: 'Saturn' } };
function campo(k) { const j = JSON.parse(fs.readFileSync(path.join(RADICE, 'data', 'gravita_' + k + '.json'), 'utf8')), u = Buffer.from(j.dati, 'base64'), v = new Float64Array(u.buffer, u.byteOffset, u.length / 8), L = v.length / 2, C = new Float64Array(L), S = new Float64Array(L);
  for (let i = 0; i < L; i++) { C[i] = v[2 * i]; S[i] = v[2 * i + 1]; } return { gm: j.gm_km3s2, R: j.raggio_km, N: j.grado, C, S }; }

const esiti = [];
function prova(nome, valore, limite, unita, extra) { const ok = isFinite(valore) && valore <= limite; esiti.push(ok); console.log((ok ? 'ok    ' : 'NO    ') + nome.padEnd(64) + String(Number(valore.toPrecision(3))).padStart(11) + ' ' + (unita || '').padEnd(6) + ' (limite ' + limite + ')' + (extra ? '  ' + extra : '')); }
const hyp = (x, y, z) => Math.sqrt(x * x + y * y + z * z);

// ---- 1. armoniche sferiche contro SHTOOLS
{ const R = JSON.parse(fs.readFileSync(path.join(VAL, 'sh_riferimento.json'), 'utf8')).punti, F = {}; let peg = 0;
  for (const p of R) { const f = F[p.corpo] || (F[p.corpo] = campo(p.corpo)), la = p.lat * Math.PI / 180, lo = p.lon * Math.PI / 180, o = [0, 0, 0];
    M.shAcc(f, p.r * Math.cos(la) * Math.cos(lo), p.r * Math.cos(la) * Math.sin(lo), p.r * Math.sin(la), p.N, p.N, o);
    peg = Math.max(peg, hyp(o[0] - p.acc_kms2[0], o[1] - p.acc_kms2[1], o[2] - p.acc_kms2[2]) / hyp(...p.acc_kms2)); }
  prova('gravità: EGM2008, GRGM900C, GMM-2B, MGNP180U contro SHTOOLS (40 punti)', peg, 1e-11, 'relat.'); }

// ---- 2. propagatore contro il riferimento indipendente (stessi casi di strumenti/validazione/propagatore/casi.json)
{ const casi = JSON.parse(fs.readFileSync(path.join(VAL, 'casi.json'), 'utf8')), rif = JSON.parse(fs.readFileSync(fileRif, 'utf8')), tab = JSON.parse(fs.readFileSync(path.join(VAL, 'tab.json'), 'utf8')), F = campo('terra');
  for (const c of casi) for (const src of ['de421', 'app']) { const R = rif[c.nome]; if (!R) continue;
    const J = M.build(A, { c: 'earth', epochMs: Date.parse(c.epoca), durS: c.durata_s, bodies: BODIES, field: F, N: c.N, M: c.N, third: c.terzi, rel: c.rel, tide: c.maree,
      srp: c.srp ? { on: true, mode: 'ball', CrAm: c.srp.CrAm } : { on: false }, drag: c.drag ? { on: true, mode: 'ball', A: c.drag.CdAm / 2.2 * 100, m: 100, cd: 2.2 } : { on: false }, alb: { on: false } });
    if (c.drag) J.drag.swConst = { f107: c.drag.f107, f107a: c.drag.f107a, ap: c.drag.ap };
    if (src === 'de421') { const T = tab[c.nome]; for (const th of J.third) { const s = T.terzi[th.k]; th.tab = { t0: s.t0, h: s.h, n: s.n, m: 3, d: Float64Array.from(s.d) }; }
      J.occ = [{ tab: null, R: 6378.137 }]; const mo = J.third.find(x => x.k === 'moon'); if (mo) J.occ.push({ tab: mo.tab, R: 1737.4 });
      J.rot = { kind: 'earth', pn: Object.assign({}, T.pn, { d: Float64Array.from(T.pn.d) }), th: Object.assign({}, T.th, { d: Float64Array.from(T.th.d) }) }; }
    const P = M.newProp({ force: J, y0: c.y0, t1: c.durata_s, rtol: 1e-13, atol: 1e-10, out: c.passo_uscita_s }); M.runProp(P, 1e9);
    let mx = 0; for (let i = 0; i < R.t.length; i++) { const y = P.out.y[i], z = R.y[i]; mx = Math.max(mx, hyp(y[0] - z[0], y[1] - z[1], y[2] - z[2]) * 1000); }
    prova('orbita ' + c.nome + (src === 'de421' ? ', stessi dati d\'ingresso' : ', effemeridi della pagina'), mx, src === 'de421' ? 3 : 5, 'm', c.durata_s / 86400 + ' giorni'); } }

// ---- 3. Lambert (Izzo) richiuso con la propagazione a due corpi, ed esempio 5.2 di Curtis
{ let seed = 7, peg = 0, n = 0; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }, mu = 398600.4418;
  for (let k = 0; k < 2000; k++) { const r1 = [0, 0, 0].map(() => (rnd() * 2 - 1) * 20000), r2 = [0, 0, 0].map(() => (rnd() * 2 - 1) * 40000); if (hyp(...r1) < 6600 || hyp(...r2) < 6600) continue;
    const Mr = k % 4 === 0 ? 1 : 0, tof = Mr * 30000 + 500 + rnd() * 60000, L = M.lambert(mu, r1, r2, tof, Mr, rnd() > 0.3, rnd() > 0.5); if (!L) continue;
    const y = M.kepProp(mu, r1, L.v1, tof); peg = Math.max(peg, hyp(y[0] - r2[0], y[1] - r2[1], y[2] - r2[2])); n++; }
  prova('Lambert: arrivo nel punto richiesto (' + n + ' casi casuali, 0 e 1 giro)', peg * 1000, 1, 'm');
  const L = M.lambert(398600, [5000, 10000, 2100], [-14600, 2500, 7000], 3600, 0, true, true), att = [-5.9925, 1.9254, 3.2456];
  prova('Lambert: esempio 5.2 di Curtis (v1 = −5,9925 1,9254 3,2456 km/s)', hyp(L.v1[0] - att[0], L.v1[1] - att[1], L.v1[2] - att[2]), 1e-3, 'km/s'); }

// ---- 4. vita orbitale: metodo a inviluppo contro Cowell (orbita a 260 km, attività solare fissa)
{ const F = campo('terra'), ep = Date.UTC(2026, 10, 14), a0 = 6378.137 + 260, inc = 51.6 * Math.PI / 180, v = Math.sqrt(F.gm / a0), y0 = [a0, 0, 0, 0, v * Math.cos(inc), v * Math.sin(inc)];
  const mk = () => { const J = M.build(A, { c: 'earth', epochMs: ep, durS: 40 * 86400, bodies: BODIES, field: F, N: 8, M: 0, third: ['sun', 'moon'], srp: { on: true, mode: 'ball', CrAm: 0.012 }, drag: { on: true, mode: 'ball', A: 2, m: 200, cd: 2.2 }, alb: { on: false } }); J.drag.swConst = { f107: 150, f107a: 150, ap: 12 }; return J; };
  const P = M.newProp({ force: mk(), y0, t1: 40 * 86400, rtol: 1e-11, atol: 1e-8, out: 3600, stopAlt: 120 }); M.runProp(P, 1e9);
  const E = M.newEnv({ force: mk(), y0, tEnd: 40 * 86400, floor: 120, rtol: 1e-10, atol: 1e-7, dp: 0.004 }); M.runEnv(E, 1e9);
  const tc = P.out.t[P.out.t.length - 1]; prova('vita orbitale a 260 km: inviluppo contro Cowell', Math.abs(E.t - tc) / tc * 100, 0.5, '%', (tc / 86400).toFixed(2) + ' giorni con Cowell'); }

// ---- 5. assetto: conservazione del momento angolare e coerenza del filtro MEKF
{ const mu = 398600.4418, a = 6778, n = Math.sqrt(mu / a ** 3), T = 2 * Math.PI / n, inc = 51.6 * Math.PI / 180;
  const env = (dist) => { const h = 10, N = Math.ceil(T * 1.2 / h) + 8, d = new Float64Array(N * 24);
    for (let k = 0; k < N; k++) { const t = -2 * h + k * h, u = n * t, r = [a * Math.cos(u), a * Math.sin(u) * Math.cos(inc), a * Math.sin(u) * Math.sin(inc)], v = [-a * n * Math.sin(u), a * n * Math.cos(u) * Math.cos(inc), a * n * Math.cos(u) * Math.sin(inc)], rh = r.map(x => x / a);
      const B0 = 3e-5 * Math.pow(6371 / a, 3), B = [0, 1, 2].map(i => dist ? B0 * (-3 * rh[2] * rh[i] + (i === 2 ? 1 : 0)) : 0), g = mu / a ** 3, G = dist ? [g * (3 * rh[0] * rh[0] - 1), 3 * g * rh[0] * rh[1], 3 * g * rh[0] * rh[2], g * (3 * rh[1] * rh[1] - 1), 3 * g * rh[1] * rh[2], g * (3 * rh[2] * rh[2] - 1)] : [0, 0, 0, 0, 0, 0];
      d.set([...r, ...v, ...B, 1, 0, 0, dist ? 4.5e-6 : 0, 0, 0, ...v.map(x => x * 1000), ...G], k * 24); } return { t0: -2 * h, h, n: N, m: 24, d }; };
  const J = [1200, 15, -8, 15, 1500, 4, -8, 4, 900], Ji = (() => { const [a1, b1, c1, d1, e1, f1, g1, h1, i1] = J, A1 = e1 * i1 - f1 * h1, B1 = -(d1 * i1 - f1 * g1), C1 = d1 * h1 - e1 * g1, det = a1 * A1 + b1 * B1 + c1 * C1;
    return [A1 / det, -(b1 * i1 - c1 * h1) / det, (b1 * f1 - c1 * e1) / det, B1 / det, (a1 * i1 - c1 * g1) / det, -(a1 * f1 - c1 * d1) / det, C1 / det, -(a1 * h1 - b1 * g1) / det, (a1 * e1 - b1 * d1) / det]; })();
  const be = 54.7356 * Math.PI / 180, W = [45, 135, 225, 315].map(al => [Math.sin(be) * Math.cos(al * Math.PI / 180), Math.sin(be) * Math.sin(al * Math.PI / 180), Math.cos(be)]);
  const faces = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]].map((nn, i) => ({ n: nn, A: 4, r: nn.map(x => x + (i === 0 ? 0.05 : 0)), rs: 0.3, rd: 0.1 }));
  const base = dist => ({ dt: 0.1, dur: dist ? T : 600, J, Ji, W, hmax: 4, tmax: 0.05, mmax: dist ? 30 : 0, kdump: 2 * n, wn: 0.15, z: 0.9, mode: 'nadir', err0: 3 * Math.PI / 180, know0: 0.5 * Math.PI / 180,
    sens: dist ? { arw: 3.1623e-7, rrw: 3.1623e-10, b0: [0.1, -0.1, 0.05].map(x => x * Math.PI / 180 / 3600), st: 10 / 206265, stDt: 1, mag: 100e-9 } : { arw: 0, rrw: 0, b0: [0, 0, 0], st: 1e-9, stDt: 1, mag: 0 },
    sc: { cd: 2.2, rs: 0.3, faces, mdip: dist ? [0.1, 0.1, 0.1] : [0, 0, 0], e: null }, env: env(dist), logDt: 10, settle: 600, seed: 3 });
  const H = (q, w, h) => { const Am = M.qA(q, new Float64Array(9)), Hb = [0, 1, 2].map(i => J[3 * i] * w[0] + J[3 * i + 1] * w[1] + J[3 * i + 2] * w[2]); h.forEach((x, k) => { for (let i = 0; i < 3; i++) Hb[i] += W[k][i] * x; }); return [0, 1, 2].map(j => Am[j] * Hb[0] + Am[3 + j] * Hb[1] + Am[6 + j] * Hb[2]); };
  const r0 = M.adcsJob(base(false)), h0 = H(r0.q[0], r0.w[0], r0.h[0]), h1 = H(r0.q[r0.q.length - 1], r0.w[r0.w.length - 1], r0.h[r0.h.length - 1]);
  prova('assetto: momento angolare totale senza coppie esterne (manovra di 3°)', hyp(h0[0] - h1[0], h0[1] - h1[1], h0[2] - h1[2]) / hyp(...h0), 1e-10, 'relat.');
  const r1 = M.adcsJob(base(true)); prova('assetto: errori di stima MEKF fuori da 3σ (un\'orbita con disturbi)', 100 - r1.in3 / r1.n3 * 100, 3, '%');
  const tail = r1.err.slice(Math.floor(r1.err.length / 2)), rms = Math.sqrt(tail.reduce((s, x) => s + x * x, 0) / tail.length) * 206265; prova('assetto: puntamento RMS nella seconda metà dell\'orbita', rms, 10, '″'); }

// ---- 6. elementi orbitali: andata e ritorno
{ let peg = 0, seed = 3; const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  for (let k = 0; k < 500; k++) { const y = [(rnd() * 2 - 1) * 9000, (rnd() * 2 - 1) * 9000, (rnd() * 2 - 1) * 9000 + 7000, (rnd() * 2 - 1) * 5, (rnd() * 2 - 1) * 5, (rnd() * 2 - 1) * 5 + 2]; const m = M.cart2mee(398600, y), z = M.mee2cart(398600, m, new Float64Array(6));
    peg = Math.max(peg, hyp(y[0] - z[0], y[1] - z[1], y[2] - z[2]) / hyp(y[0], y[1], y[2])); }
  prova('elementi equinoziali: andata e ritorno su 500 stati', peg, 1e-10, 'relat.'); }

const ko = esiti.filter(x => !x).length;
console.log('\n' + (ko ? ko + ' prove su ' + esiti.length + ' NON superate.' : 'Tutte le ' + esiti.length + ' prove superate.'));
process.exit(ko ? 1 : 0);
