/* Atlante Orbitale: service worker.
   Tiene una copia del sito sul dispositivo, così l'app si apre anche senza rete.

   - Pagina (index.html): prima la rete, la copia locale se la rete manca.
   - Dati che cambiano (data/active.txt, meta.json, probes.json, lanci.json, meteo_spaziale.json): prima la rete, la copia locale se la rete manca.
   - Tutto il resto (librerie, caratteri, texture, stelle, icone): subito la copia locale,
     che viene poi rinfrescata in sottofondo per l'apertura successiva. I modelli 3D (modelli/) si copiano
     al primo uso: senza rete si vedono quelli già aperti almeno una volta.

   Cambia VERSIONE solo per buttare via le copie vecchie (per esempio dopo aver tolto dei file). */
'use strict';

const VERSIONE = 'atlante-v1';
const BASE = new URL('./', self.location).href;          // cartella in cui vive il sito
const INDICE = new URL('index.html', BASE).href;

const FISSI = [
  'index.html', 'manifest.webmanifest', 'LICENZE.txt',
  'vendor/three.min.js', 'vendor/OrbitControls.js', 'vendor/LineSegmentsGeometry.js', 'vendor/LineGeometry.js',
  'vendor/LineMaterial.js', 'vendor/LineSegments2.js', 'vendor/Line2.js', 'vendor/GLTFLoader.js', 'vendor/satellite.min.js', 'vendor/astronomy.browser.min.js',
  'fonts/b612-latin-400-normal.woff2', 'fonts/b612-latin-700-normal.woff2',
  'fonts/b612-mono-latin-400-normal.woff2', 'fonts/b612-mono-latin-700-normal.woff2',
  'icone/icona.svg', 'icone/icona-32.png', 'icone/icona-180.png', 'icone/icona-192.png', 'icone/icona-512.png', 'icone/icona-maschera-512.png',
  'tex/day.jpg', 'tex/night.jpg', 'tex/spec.jpg', 'tex/clouds.jpg', 'tex/sun.jpg', 'tex/mercury.jpg', 'tex/venus.jpg', 'tex/moon.jpg',
  'tex/mars.jpg', 'tex/jupiter.jpg', 'tex/saturn.jpg', 'tex/ring.png', 'tex/uranus.jpg', 'tex/neptune.jpg',
  'data/stars.json', 'data/campo_marte.json',
];
const VARIABILI = ['data/meta.json', 'data/active.txt', 'data/probes.json', 'data/lanci.json', 'data/meteo_spaziale.json'];
const eVariabile = rel => VARIABILI.includes(rel);

const chiave = url => { const u = new URL(url); return u.origin + u.pathname; };   // senza ?query e #frammento

// Mette da parte una copia della risposta senza far aspettare la pagina: la scrittura prosegue in sottofondo.
function salva(ev, cache, url, risposta) {
  if (risposta && risposta.status === 200 && risposta.type === 'basic') {
    const scrittura = cache.put(chiave(url), risposta.clone()).catch(() => { /* spazio esaurito: si continua senza copia */ });
    if (ev) ev.waitUntil(scrittura);
  }
  return risposta;
}

self.addEventListener('install', ev => {
  ev.waitUntil((async () => {
    const cache = await caches.open(VERSIONE);
    // Un file che non si riesce a scaricare non blocca l'installazione: verrà copiato al primo uso.
    await Promise.all(FISSI.concat(VARIABILI).map(async rel => {
      const url = new URL(rel, BASE).href;
      try { const r = await fetch(url, { cache: 'no-cache' }); if (r.status === 200) await cache.put(chiave(url), r); } catch (e) {}
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', ev => {
  ev.waitUntil((async () => {
    for (const nome of await caches.keys()) if (nome.startsWith('atlante-') && nome !== VERSIONE) await caches.delete(nome);
    await self.clients.claim();
  })());
});

function conScadenza(promessa, ms) {
  return new Promise((ok, no) => { const t = setTimeout(() => no(new Error('tempo scaduto')), ms); promessa.then(v => { clearTimeout(t); ok(v); }, e => { clearTimeout(t); no(e); }); });
}

// Prima la rete; se manca o tarda troppo, la copia locale.
async function primaLaRete(ev, urlCopia, attesaMs) {
  const cache = await caches.open(VERSIONE);
  const inCopia = await cache.match(chiave(urlCopia));
  const rete = fetch(ev.request).then(r => salva(ev, cache, urlCopia, r));
  if (!inCopia) return rete;
  try { const r = await conScadenza(rete, attesaMs); if (r && r.ok) return r; } catch (e) { rete.catch(() => {}); }
  return inCopia;
}

// Subito la copia locale; in sottofondo se ne scarica una nuova per la prossima volta.
async function copiaPoiRete(ev) {
  const cache = await caches.open(VERSIONE), url = ev.request.url;
  const inCopia = await cache.match(chiave(url));
  const rete = fetch(ev.request).then(r => salva(ev, cache, url, r));
  if (inCopia) { ev.waitUntil(rete.catch(() => {})); return inCopia; }
  return rete;
}

self.addEventListener('fetch', ev => {
  const richiesta = ev.request;
  if (richiesta.method !== 'GET' || richiesta.headers.has('range')) return;
  if (!richiesta.url.startsWith(BASE)) return;                       // CelesTrak e ogni altro sito passano senza essere toccati
  const rel = new URL(richiesta.url).pathname.slice(new URL(BASE).pathname.length);
  if (richiesta.mode === 'navigate') {                               // apertura della pagina: l'unica è index.html
    if (rel === '' || rel === 'index.html') ev.respondWith(primaLaRete(ev, INDICE, 4000));
    return;
  }
  if (rel === 'sw.js') return;
  if (eVariabile(rel)) { ev.respondWith(primaLaRete(ev, richiesta.url, 12000)); return; }
  ev.respondWith(copiaPoiRete(ev));
});
