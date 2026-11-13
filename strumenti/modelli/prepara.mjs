// Prepara i modelli NASA per l'app: toglie la compressione Draco, porta il modello in metri e negli assi corpo dell'app
// (z = dimensione maggiore, dove stanno le ali; y = intermedia; x = minore), centra, alleggerisce, e scrive un .glb.
import { NodeIO, getBounds } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, weld, simplify, quantize, textureCompress } from '@gltf-transform/functions';
import { MeshoptSimplifier } from 'meshoptimizer';
import draco3d from 'draco3d';
import sharp from 'sharp';
import fs from 'fs';
const [, , DA, A, ELENCO] = process.argv;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'draco3d.decoder': await draco3d.createDecoderModule() });
await MeshoptSimplifier.ready;
const solo = process.argv[5] ? process.argv[5].split(',') : null, tutte = JSON.parse(fs.readFileSync(ELENCO, 'utf8')), voci = solo ? Object.fromEntries(Object.entries(tutte).filter(([k]) => solo.includes(k))) : tutte;
let esito = {}; try { esito = JSON.parse(fs.readFileSync(`${A}/esito.json`, 'utf8')); } catch (e) {}
const tris = root => { let t = 0; for (const m of root.listMeshes()) for (const p of m.listPrimitives()) { const i = p.getIndices(); t += (i ? i.getCount() : p.getAttribute('POSITION').getCount()) / 3; } return Math.round(t); };
for (const [chiave, v] of Object.entries(voci)) {
  try {
    const doc = await io.read(`${DA}/${v.file}.glb`), root = doc.getRoot();
    for (const e of root.listExtensionsUsed()) if (e.extensionName === 'KHR_draco_mesh_compression') e.dispose();
    if (v.togli) for (const nd of root.listNodes()) if (v.togli.includes(nd.getName())) nd.dispose();   // pezzi staccati dal veicolo nel file originale (ISS: 7 dischi a ~80 m dalla stazione)
    const scena = root.getDefaultScene() || root.listScenes()[0], b = getBounds(scena), dim = b.max.map((x, i) => x - b.min[i]), c = b.min.map((x, i) => (x + b.max[i]) / 2);
    const ord = [0, 1, 2].sort((i, j) => dim[i] - dim[j]), s = v.max ? v.max / Math.max(...dim) : 1;        // ord = [minore, intermedia, maggiore]
    const P = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]; P[0][ord[0]] = 1; P[1][ord[1]] = 1; P[2][ord[2]] = 1;
    const det = P[0][0] * (P[1][1] * P[2][2] - P[1][2] * P[2][1]) - P[0][1] * (P[1][0] * P[2][2] - P[1][2] * P[2][0]) + P[0][2] * (P[1][0] * P[2][1] - P[1][1] * P[2][0]);
    if (det < 0) P[1][ord[1]] = -1;                       // rotazione propria: niente immagini speculari, le scritte restano leggibili
    if (v.gira) for (const r of v.gira) for (let k = 0; k < 3; k++) P[r][k] = -P[r][k];                    // ribalta due assi (mezzo giro) dove serve
    const M = new Array(16).fill(0); for (let r = 0; r < 3; r++) { let t = 0; for (let k = 0; k < 3; k++) { M[k * 4 + r] = s * P[r][k]; t -= s * P[r][k] * c[k]; } M[12 + r] = t; } M[15] = 1;
    const corpo = doc.createNode('corpo').setMatrix(M); for (const n of scena.listChildren()) { scena.removeChild(n); corpo.addChild(n); } scena.addChild(corpo);
    if (v.piatto) for (const m of root.listMeshes()) for (const pr of m.listPrimitives()) pr.setAttribute('NORMAL', null);      // facce piane: i vertici si possono unire e il file si riduce molto
    const prima = tris(root); await doc.transform(dedup(), prune(), weld());
    if (prima > v.tri) await doc.transform(simplify({ simplifier: MeshoptSimplifier, ratio: v.tri / prima, error: v.err || 0.003 }));
    if (root.listTextures().length) await doc.transform(textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [1024, 1024] }));
    await doc.transform(prune(), quantize());
    await io.write(`${A}/${chiave}.glb`, doc);
    const d2 = dim.map(x => x * s).sort((a, b) => a - b);
    esito[chiave] = { tri: tris(root), da: prima, kB: Math.round(fs.statSync(`${A}/${chiave}.glb`).size / 1024), x: +d2[0].toFixed(2), y: +d2[1].toFixed(2), z: +d2[2].toFixed(2), tex: root.listTextures().length };
    console.log(chiave.padEnd(10), JSON.stringify(esito[chiave]));
  } catch (e) { console.log(chiave.padEnd(10), 'ERRORE', String(e).slice(0, 160)); }
}
fs.writeFileSync(`${A}/esito.json`, JSON.stringify(esito));
