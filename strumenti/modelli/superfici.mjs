// Tabelle delle superfici esposte dei modelli 3D, per resistenza atmosferica e pressione di radiazione sulla forma vera.
// Per ogni direzione di provenienza ŝ (flusso solare, flusso d'aria, luce e calore del pianeta) su una griglia di 25 × 48 direzioni,
// il modello è rasterizzato in proiezione ortogonale lungo ŝ con un buffer di profondità: conta solo la prima superficie colpita,
// quindi le parti in ombra di altre parti (autoschermatura) non ricevono nulla. Per ogni pixel visibile, area proiettata dA, punto r
// (metri, assi corpo, origine del modello) e normale n̂ rivolta verso la sorgente, con c = n̂·ŝ, si accumulano
//   A = ΣdA, R0 = ΣdA r, N1 = ΣdA n̂, N2 = ΣdA c n̂, Q1 = ΣdA r×n̂, Q2 = ΣdA c r×n̂     (16 numeri per direzione)
// da cui, per un modello di superficie con riflessione speculare ρs e diffusa ρd (Wertz; Montenbruck e Gill 2000):
//   radiazione  F = −P [(1−ρs) A ŝ + 2ρs N2 + ⅔ρd N1],   M = −P [(1−ρs) R0×ŝ + 2ρs Q2 + ⅔ρd Q1]   (rispetto all'origine)
//   resistenza  F = −q CD A v̂,  M = −q CD R0×v̂  (ŝ = v̂, direzione del moto rispetto all'atmosfera)
// Uso:  NPIX=768 node superfici.mjs <cartella dei .glb> [chiave,chiave,...]     scrive <chiave>_sup.json accanto ai .glb (NPIX: punti per lato)
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import fs from 'fs';
const [, , DIR, SOLO] = process.argv, NT = 24, NP = 48, NPIX = +(process.env.NPIX || 512);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const chiavi = SOLO ? SOLO.split(',') : fs.readdirSync(DIR).filter(f => f.endsWith('.glb')).map(f => f.slice(0, -4));
function triangoli(doc) {
  const T = [];
  const visita = (nd) => {
    const mesh = nd.getMesh();
    if (mesh) { const W = nd.getWorldMatrix();
      for (const p of mesh.listPrimitives()) { if (p.getMode() !== 4) continue; const pos = p.getAttribute('POSITION'), ind = p.getIndices(), n = ind ? ind.getCount() : pos.getCount(), e = [0, 0, 0];
        const v = i => { pos.getElement(i, e); return [W[0] * e[0] + W[4] * e[1] + W[8] * e[2] + W[12], W[1] * e[0] + W[5] * e[1] + W[9] * e[2] + W[13], W[2] * e[0] + W[6] * e[1] + W[10] * e[2] + W[14]]; };
        for (let k = 0; k + 2 < n; k += 3) { const a = v(ind ? ind.getScalar(k) : k), b = v(ind ? ind.getScalar(k + 1) : k + 1), c = v(ind ? ind.getScalar(k + 2) : k + 2); T.push(...a, ...b, ...c); } } }
    for (const c of nd.listChildren()) visita(c); };
  const sc = doc.getRoot().getDefaultScene() || doc.getRoot().listScenes()[0];
  for (const n of sc.listChildren()) visita(n);
  return new Float64Array(T);
}
for (const k of chiavi) {
  const t0 = Date.now(), doc = await io.read(`${DIR}/${k}.glb`), V = triangoli(doc), nt = V.length / 9;
  // normali, aree, centroide delle superfici, raggio
  const Nn = new Float64Array(nt * 3), Ar = new Float64Array(nt); let S = 0, cx = 0, cy = 0, cz = 0, R = 0;
  const mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9];
  for (let t = 0; t < nt; t++) { const o = t * 9, ux = V[o + 3] - V[o], uy = V[o + 4] - V[o + 1], uz = V[o + 5] - V[o + 2], wx = V[o + 6] - V[o], wy = V[o + 7] - V[o + 1], wz = V[o + 8] - V[o + 2];
    let nx = uy * wz - uz * wy, ny = uz * wx - ux * wz, nz = ux * wy - uy * wx; const l = Math.hypot(nx, ny, nz); Ar[t] = l / 2; if (l > 0) { nx /= l; ny /= l; nz /= l; } Nn[t * 3] = nx; Nn[t * 3 + 1] = ny; Nn[t * 3 + 2] = nz;
    S += Ar[t]; cx += Ar[t] * (V[o] + V[o + 3] + V[o + 6]) / 3; cy += Ar[t] * (V[o + 1] + V[o + 4] + V[o + 7]) / 3; cz += Ar[t] * (V[o + 2] + V[o + 5] + V[o + 8]) / 3;
    for (let q = 0; q < 9; q += 3) { R = Math.max(R, Math.hypot(V[o + q], V[o + q + 1], V[o + q + 2])); for (let i = 0; i < 3; i++) { mn[i] = Math.min(mn[i], V[o + q + i]); mx[i] = Math.max(mx[i], V[o + q + i]); } } }
  R *= 1.001; const pix = 2 * R / NPIX, dA = pix * pix, Z = new Float32Array(NPIX * NPIX), ID = new Int32Array(NPIX * NPIX), P = new Float64Array(nt * 9);
  // un punto di campionamento a caso dentro ogni pixel (campionamento stratificato): i bordi allineati alla griglia, frequenti nei modelli,
  // non danno errori sistematici sull'area, che restano rumore piccolo e senza segno
  const JX = new Float32Array(NPIX * NPIX), JY = new Float32Array(NPIX * NPIX); let seme = 12345; const caso = () => (seme = (seme * 16807) % 2147483647) / 2147483647;
  for (let q = 0; q < NPIX * NPIX; q++) { JX[q] = caso(); JY[q] = caso(); }
  const out = new Float32Array((NT + 1) * NP * 16);
  for (let i = 0; i <= NT; i++) for (let j = 0; j < NP; j++) {
    const th = Math.PI * i / NT, ph = 2 * Math.PI * j / NP, sx = Math.sin(th) * Math.cos(ph), sy = Math.sin(th) * Math.sin(ph), sz = Math.cos(th);
    // base del piano immagine: u, w ⟂ ŝ
    let ax = Math.abs(sz) < 0.9 ? 0 : 1, ay = 0, az = Math.abs(sz) < 0.9 ? 1 : 0;
    let ux = ay * sz - az * sy, uy = az * sx - ax * sz, uz = ax * sy - ay * sx; const ul = Math.hypot(ux, uy, uz); ux /= ul; uy /= ul; uz /= ul;
    const wx = sy * uz - sz * uy, wy = sz * ux - sx * uz, wz = sx * uy - sy * ux;
    for (let q = 0; q < nt * 3; q++) { const x = V[q * 3], y = V[q * 3 + 1], z = V[q * 3 + 2]; P[q * 3] = (x * ux + y * uy + z * uz + R) / pix; P[q * 3 + 1] = (x * wx + y * wy + z * wz + R) / pix; P[q * 3 + 2] = x * sx + y * sy + z * sz; }
    Z.fill(-Infinity); ID.fill(-1);
    for (let t = 0; t < nt; t++) { const o = t * 9, x0 = P[o], y0 = P[o + 1], z0 = P[o + 2], x1 = P[o + 3], y1 = P[o + 4], z1 = P[o + 5], x2 = P[o + 6], y2 = P[o + 7], z2 = P[o + 8];
      const den = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0); if (Math.abs(den) < 1e-12) continue;
      const X0 = Math.max(0, Math.floor(Math.min(x0, x1, x2))), X1 = Math.min(NPIX - 1, Math.floor(Math.max(x0, x1, x2))), Y0 = Math.max(0, Math.floor(Math.min(y0, y1, y2))), Y1 = Math.min(NPIX - 1, Math.floor(Math.max(y0, y1, y2)));
      for (let py = Y0; py <= Y1; py++) for (let px = X0; px <= X1; px++) { const q = py * NPIX + px, X = px + JX[q], Y = py + JY[q];
        const b1 = ((X - x0) * (y2 - y0) - (x2 - x0) * (Y - y0)) / den, b2 = ((x1 - x0) * (Y - y0) - (X - x0) * (y1 - y0)) / den, b0 = 1 - b1 - b2;
        if (b0 < 0 || b1 < 0 || b2 < 0) continue; const z = b0 * z0 + b1 * z1 + b2 * z2; if (z > Z[q]) { Z[q] = z; ID[q] = t; } } }
    let A = 0, R0x = 0, R0y = 0, R0z = 0, N1x = 0, N1y = 0, N1z = 0, N2x = 0, N2y = 0, N2z = 0, Q1x = 0, Q1y = 0, Q1z = 0, Q2x = 0, Q2y = 0, Q2z = 0;
    for (let py = 0; py < NPIX; py++) for (let px = 0; px < NPIX; px++) { const q = py * NPIX + px, t = ID[q]; if (t < 0) continue;
      let nx = Nn[t * 3], ny = Nn[t * 3 + 1], nz = Nn[t * 3 + 2], c = nx * sx + ny * sy + nz * sz; if (c < 0) { nx = -nx; ny = -ny; nz = -nz; c = -c; }   // superfici a due facce: si usa quella rivolta alla sorgente
      const a = (px + JX[q]) * pix - R, b = (py + JY[q]) * pix - R, d = Z[q], rx = a * ux + b * wx + d * sx, ry = a * uy + b * wy + d * sy, rz = a * uz + b * wz + d * sz;
      const tx = ry * nz - rz * ny, ty = rz * nx - rx * nz, tz = rx * ny - ry * nx;
      A += dA; R0x += dA * rx; R0y += dA * ry; R0z += dA * rz; N1x += dA * nx; N1y += dA * ny; N1z += dA * nz; N2x += dA * c * nx; N2y += dA * c * ny; N2z += dA * c * nz;
      Q1x += dA * tx; Q1y += dA * ty; Q1z += dA * tz; Q2x += dA * c * tx; Q2y += dA * c * ty; Q2z += dA * c * tz; }
    out.set([A, R0x, R0y, R0z, N1x, N1y, N1z, N2x, N2y, N2z, Q1x, Q1y, Q1z, Q2x, Q2y, Q2z], (i * NP + j) * 16);
  }
  const f = v => +v.toPrecision(5);
  const res = { versione: 1, modello: k, nt: NT, np: NP, pixel_m: f(pix), triangoli: nt, area_m2: f(S), centroide_m: [f(cx / S), f(cy / S), f(cz / S)], dimensioni_m: [0, 1, 2].map(i => f(mx[i] - mn[i])),
    ordine: 'A,R0,N1,N2,Q1,Q2 (m², m³ per R0 e Q): righe θ = 0…180° da +z, colonne φ = 0…360° da +x verso +y', dati: Buffer.from(out.buffer).toString('base64') };
  fs.writeFileSync(`${DIR}/${k}_sup.json`, JSON.stringify(res));
  console.log(k.padEnd(10), nt, 'tri', 'area', f(S), 'pix', f(pix), 'A(+x)', f(out[(NT / 2 * NP) * 16]), 'A(+z)', f(out[0]), ((Date.now() - t0) / 1000).toFixed(1) + ' s');
}
