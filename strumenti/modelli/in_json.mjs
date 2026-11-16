// Scrive ogni modello .glb come un unico file JSON (glTF con i dati incorporati in base64): è il formato che il visualizzatore integrato sa servire.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import fs from 'fs';
const [, , DA, A] = process.argv, io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
fs.mkdirSync(A, { recursive: true }); let tot = 0;
for (const f of fs.readdirSync(DA).filter(f => f.endsWith('.glb')).sort()) {
  const doc = await io.read(`${DA}/${f}`), { json, resources } = await io.writeJSON(doc, { basename: f.replace('.glb', '') });
  const dato = (uri, tipo) => `data:${tipo};base64,` + Buffer.from(resources[uri]).toString('base64');
  for (const b of json.buffers || []) if (b.uri && resources[b.uri]) b.uri = dato(b.uri, 'application/octet-stream');
  for (const im of json.images || []) if (im.uri && resources[im.uri]) im.uri = dato(im.uri, im.mimeType || (im.uri.endsWith('.webp') ? 'image/webp' : im.uri.endsWith('.png') ? 'image/png' : 'image/jpeg'));
  const out = JSON.stringify(json); fs.writeFileSync(`${A}/${f.replace('.glb', '.json')}`, out); tot += out.length;
}
console.log('scritti', fs.readdirSync(A).length, 'file,', (tot / 1048576).toFixed(1), 'MB');
