// Toglie da un modello già preparato i nodi indicati e lo ricentra (stessi assi e stessa scala).
import { NodeIO, getBounds } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { prune } from '@gltf-transform/functions';
const [, , FILE, NOMI] = process.argv, togli = NOMI.split(','), io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(FILE), root = doc.getRoot(), scena = root.getDefaultScene() || root.listScenes()[0];
let n = 0; for (const nd of root.listNodes()) if (togli.includes(nd.getName())) { nd.dispose(); n++; }
await doc.transform(prune());
const b = getBounds(scena), c = b.min.map((x, i) => (x + b.max[i]) / 2), dim = b.max.map((x, i) => x - b.min[i]);
const corpo = scena.listChildren()[0], M = corpo.getMatrix().slice(); for (let r = 0; r < 3; r++) M[12 + r] -= c[r]; corpo.setMatrix(M);
await io.write(FILE, doc);
const b2 = getBounds(scena);
console.log('tolti', n, 'nodi; spostamento', c.map(x => x.toFixed(2)).join(' '), 'm; dimensioni', dim.map(x => x.toFixed(2)).join(' × '), 'm; nuovo centro', b2.min.map((x, i) => ((x + b2.max[i]) / 2).toFixed(3)).join(' '));
