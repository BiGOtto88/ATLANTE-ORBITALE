/* Keplario · laboratorio: funzioni comuni a tutte le pagine di calcolo.
   K.bar(...)       barra in alto con Cielo, le sei materie e la lingua
   K.en, K.t(it,en) lingua (stessa scelta dell'app: #en/#it, ?lang=, localStorage «atlante-lingua», lingua del browser)
   K.num(id)        legge un campo: null se vuoto, NaN se non è un numero (accetta virgola, spazi, 1e-3, −)
   K.fmt, K.sig     numeri all'italiana o all'inglese (spazio per le migliaia)
   K.der(id, x)     mostra in verde, dentro un campo lasciato vuoto, il valore che la pagina ha ricavato
   K.rows(el, ...)  righe di risultati; K.msg(el, testo) avvisi
   K.live(el, fn)   ricalcola a ogni modifica; K.keep(ids) ricorda i dati nell'indirizzo (#a=…&e=…)
   K.sat(el, fn)    «parti da un satellite reale»: cerca nel catalogo data/active.txt e dà gli elementi medi del TLE
   K.earth(THREE)   Terra realistica (giorno, notte, riflesso del mare, nuvole, atmosfera)
   K.chart(el, ...) grafico a linee con assi, legenda e lettura al passaggio del puntatore */
'use strict';
const K = (() => {
  const $ = id => typeof id === 'string' ? document.getElementById(id) : id;

  /* ---------- lingua ---------- */
  const lang = (() => {
    const h = (location.hash || '').slice(1);
    if (h === 'en' || h === 'it') return h;
    const q = (location.search.match(/[?&]lang=(en|it)\b/) || [])[1]; if (q) return q;
    try { const s = localStorage.getItem('atlante-lingua'); if (s === 'en' || s === 'it') return s; } catch (e) {}
    return /^it\b/i.test(navigator.language || 'it') ? 'it' : 'en';
  })();
  const en = lang === 'en';
  const t = (it, e) => en ? e : it;
  function applyLang(root) {
    document.documentElement.lang = lang;
    if (!en) return;
    (root || document).querySelectorAll('[data-en]').forEach(el => { el.innerHTML = el.getAttribute('data-en'); });
    for (const a of ['title', 'aria-label', 'placeholder', 'content', 'alt'])
      (root || document).querySelectorAll('[data-en-' + a + ']').forEach(el => el.setAttribute(a, el.getAttribute('data-en-' + a)));
  }

  /* ---------- barra in alto ---------- */
  const SUBJ = [
    ['orbite', 'Orbite e manovre', 'Orbits and manoeuvres'],
    ['assetto', 'Assetto e controllo', 'Attitude and control'],
    ['propulsione', 'Propulsione e lanciatori', 'Propulsion and launchers'],
    ['strutture', 'Strutture e materiali', 'Structures and materials'],
    ['comunicazioni', 'Comunicazioni e navigazione', 'Communications and navigation'],
    ['sistemi', 'Sistemi e missione', 'Systems and mission'],
  ];
  const sky = () => en ? 'en/' : './';
  function bar(cur) {
    const satQ = (location.search.match(/[?&](sat=\d+)/) || [])[1], q = satQ ? '?' + satQ : '';
    const h = document.createElement('header'); h.className = 'kb';
    h.innerHTML = '<div class="kb-in"><a class="kb-home" href="' + sky() + '">Keplario</a>' +
      '<a class="kb-sky" href="' + sky() + '#cielo">' + t('Cielo', 'Sky') + '</a><span class="kb-sep" aria-hidden="true"></span>' +
      '<nav class="kb-nav" aria-label="' + t('Laboratorio', 'Lab') + '">' +
      SUBJ.map(s => '<a href="' + s[0] + '.html' + q + '"' + (s[0] === cur ? ' aria-current="page"' : '') + '>' + (en ? s[2] : s[1]) + '</a>').join('') +
      '</nav><button class="btn sm kb-lang" type="button" title="' + (en ? 'Italiano' : 'English') + '">' + (en ? 'IT' : 'EN') + '</button></div>';
    document.body.prepend(h);
    h.querySelector('.kb-lang').onclick = () => {
      try { localStorage.setItem('atlante-lingua', en ? 'it' : 'en'); } catch (e) {}
      const u = new URL(location.href); u.searchParams.delete('lang'); if (u.hash === '#en' || u.hash === '#it') u.hash = '';
      location.replace(u.href);
    };
    const cn = h.querySelector('[aria-current=page]'); if (cn && cn.scrollIntoView) setTimeout(() => cn.scrollIntoView({ block: 'nearest', inline: 'center' }), 0);
    const f = document.createElement('footer'); f.className = 'foot';
    f.innerHTML = '<span>' + t('Strumento didattico: non usarlo per operazioni di volo.', 'A learning tool: not for flight operations.') + '</span>' +
      '<a href="' + sky() + '">' + t('Torna al cielo', 'Back to the sky') + '</a><a href="LICENZE.txt">' + t('Licenze', 'Licences') + '</a>';
    document.body.append(f);
  }
  function init(cur) { applyLang(); bar(cur); }

  /* ---------- numeri ---------- */
  function num(id) {
    const el = $(id); if (!el) return null;
    let v = String(el.value).trim(); if (v === '') return null;
    v = v.replace(/[\s  ']/g, '').replace(/−/g, '-').replace(/[×x]10\^?/i, 'e');
    // separatore decimale: con punto e virgola insieme vale l'ultimo dei due (1.234,5 e 1,234.5);
    // da soli, un punto o una virgola sono decimali (0.366 e 0,366); ripetuti sono migliaia (1.234.567)
    const dot = v.lastIndexOf('.'), com = v.lastIndexOf(',');
    if (dot >= 0 && com >= 0) v = dot > com ? v.replace(/,/g, '') : v.replace(/\./g, '').replace(',', '.');
    else if ((v.match(/\./g) || []).length > 1) v = v.replace(/\./g, '');
    else if ((v.match(/,/g) || []).length > 1) v = v.replace(/,/g, '');
    else v = v.replace(',', '.');
    const x = Number(v); return Number.isFinite(x) ? x : NaN;
  }
  const DEC = en ? '.' : ',';
  function group(s) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
  function fmt(x, d) {
    if (x == null || !Number.isFinite(x)) return '—';
    d = d == null ? 2 : d;
    let s = Math.abs(x).toFixed(d); const p = s.split('.');
    const neg = x < 0 && Number(s) !== 0;
    return (neg ? '−' : '') + group(p[0]) + (p[1] ? DEC + p[1] : '');
  }
  const SUP = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };
  function sig(x, n) {     // n cifre significative; potenze di dieci fuori da 10⁻³…10⁷
    if (x == null || !Number.isFinite(x)) return '—';
    n = n || 4; if (x === 0) return '0';
    const ax = Math.abs(x), e = Math.floor(Math.log10(ax));
    if (e < -3 || e > 7) {
      const m = x / Math.pow(10, e);
      return fmt(m, n - 1).replace(new RegExp('\\' + DEC + '?0+$'), '') + '·10' + String(e).split('').map(c => SUP[c]).join('');
    }
    return fmt(x, Math.max(0, n - 1 - e));
  }
  const plain = (x, d) => (x == null || !Number.isFinite(x)) ? '' : fmt(x, d).replace(/ /g, ' ');

  /* ---------- campi ricavati e campi in conflitto ---------- */
  function der(id, x, d) {
    const el = $(id); if (!el) return;
    if (el.dataset.ph === undefined) el.dataset.ph = el.placeholder || '';
    if (el.value.trim() !== '') return;
    const ok = x != null && Number.isFinite(x);
    el.placeholder = ok ? (typeof d === 'string' ? d : (d == null ? sig(x, 5) : plain(x, d))) : el.dataset.ph;
    el.classList.toggle('der', ok);
  }
  function clear(scope) {
    (scope ? $(scope) : document).querySelectorAll('input').forEach(el => {
      if (el.dataset.ph !== undefined) el.placeholder = el.dataset.ph;
      el.classList.remove('der', 'bad');
    });
  }
  function bad(id, on) { const el = $(id); if (el) el.classList.toggle('bad', on !== false); }
  const given = id => { const el = $(id); return !!el && el.value.trim() !== ''; };

  /* ---------- risultati e avvisi ---------- */
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  // voce: ['#', 'Titolo'] oppure [etichetta, valore, unità, nota, classe]  (valore già formattato)
  function rows(el, list) {
    $(el).innerHTML = list.filter(Boolean).map(r => r[0] === '#' ? '<h3>' + r[1] + '</h3>' :
      '<div class="row' + (r[4] ? ' ' + r[4] : '') + '"><span>' + r[0] + '</span><span class="v">' + r[1] + (r[2] ? '<small>' + r[2] + '</small>' : '') + '</span>' +
      (r[3] ? '<span class="n">' + r[3] + '</span>' : '') + '</div>').join('');
  }
  function msg(el, text, kind) { $(el).innerHTML = text ? '<p class="msg' + (kind ? ' ' + kind : '') + '">' + text + '</p>' : ''; }

  /* ---------- ricalcolo e memoria nell'indirizzo ---------- */
  function live(scope, fn, ms) {
    let tm = 0; const go = () => { clearTimeout(tm); tm = setTimeout(fn, ms == null ? 160 : ms); };
    $(scope).addEventListener('input', go); $(scope).addEventListener('change', go); return go;
  }
  let keepIds = [], keepExtra = {};
  function keep(ids, extra) {          // salva i campi compilati nell'indirizzo, così il calcolo si può condividere
    keepIds = ids; keepExtra = extra || {};
    const h = (location.hash || '').slice(1);
    if (h && h.includes('=')) {
      const p = new URLSearchParams(h);
      ids.forEach(id => { const el = $(id); if (!el || !p.has(id)) return; if (el.type === 'checkbox') el.checked = p.get(id) === '1'; else el.value = p.get(id); });
      return p;
    }
    return null;
  }
  function save(extra) {
    const p = new URLSearchParams();
    Object.entries(Object.assign({}, keepExtra, extra || {})).forEach(([k, v]) => { if (v != null && v !== '') p.set(k, v); });
    keepIds.forEach(id => { const el = $(id); if (!el) return; if (el.type === 'checkbox') { if (el.checked) p.set(id, '1'); } else if (el.value.trim() !== '') p.set(id, el.value.trim()); });
    const s = p.toString(); try { history.replaceState(null, '', location.pathname + location.search + (s ? '#' + s : '')); } catch (e) {}
  }
  function fill(map) { Object.entries(map).forEach(([id, v]) => { const el = $(id); if (!el) return; if (el.type === 'checkbox') el.checked = !!v; else el.value = v; }); }
  function wipe(scope) { $(scope).querySelectorAll('input:not([type=checkbox]):not([type=range]):not([data-keep])').forEach(el => { el.value = ''; }); clear(scope); }

  /* ---------- costanti e utilità di meccanica orbitale ---------- */
  const MU = 398600.4418, RE = 6378.137, J2 = 1.08262668e-3, D2R = Math.PI / 180, G0 = 9.80665, OMEGA_E = 7.2921159e-5;
  function kepler(M, e) { let E = e < 0.8 ? M : Math.PI; for (let k = 0; k < 50; k++) { const d = (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E)); E -= d; if (Math.abs(d) < 1e-13) break; } return E; }
  function nuFromM(M, e) { const E = kepler(((M % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI), e); return 2 * Math.atan2(Math.sqrt(1 + e) * Math.sin(E / 2), Math.sqrt(1 - e) * Math.cos(E / 2)); }
  function gmst(date) {   // tempo siderale medio di Greenwich, rad (IAU 1982)
    const jd = date.getTime() / 86400000 + 2440587.5, T = (jd - 2451545) / 36525;
    let s = 67310.54841 + (876600 * 3600 + 8640184.812866) * T + 0.093104 * T * T - 6.2e-6 * T * T * T;
    return ((s % 86400 + 86400) % 86400) / 86400 * 2 * Math.PI;
  }
  // perifocale → inerziale (ECI). Angoli in radianti.
  function pqw2eci(x, y, i, raan, argp) {
    const cw = Math.cos(argp), sw = Math.sin(argp), ci = Math.cos(i), si = Math.sin(i), co = Math.cos(raan), so = Math.sin(raan);
    const x1 = x * cw - y * sw, y1 = x * sw + y * cw, y2 = y1 * ci, z2 = y1 * si;
    return [x1 * co - y2 * so, x1 * so + y2 * co, z2];
  }

  /* ---------- satelliti reali dal catalogo dell'app ---------- */
  let CAT = null;
  function catalog() {
    if (CAT) return CAT;
    CAT = fetch('data/active.txt').then(r => { if (!r.ok) throw new Error('catalogo'); return r.text(); }).then(txt => {
      const L = txt.split(/\r?\n/), out = [];
      for (let k = 0; k < L.length - 2; k++) {
        if (L[k + 1].startsWith('1 ') && L[k + 2].startsWith('2 ') && !L[k].startsWith('1 ') && !L[k].startsWith('2 ')) {
          out.push({ name: L[k].trim().replace(/^0 /, ''), l1: L[k + 1], l2: L[k + 2], norad: +L[k + 1].slice(2, 7) }); k += 2;
        }
      }
      return out;
    });
    CAT.catch(() => { CAT = null; });
    return CAT;
  }
  function elements(s) {   // elementi medi del TLE (non osculanti): bastano per i calcoli del laboratorio
    const l1 = s.l1, l2 = s.l2;
    const i = +l2.slice(8, 16), raan = +l2.slice(17, 25), e = +('0.' + l2.slice(26, 33).trim()), argp = +l2.slice(34, 42), M = +l2.slice(43, 51), nrev = +l2.slice(52, 63);
    const yy = +l1.slice(18, 20), day = +l1.slice(20, 32), year = yy < 57 ? 2000 + yy : 1900 + yy;
    const epoch = new Date(Date.UTC(year, 0, 1) + (day - 1) * 86400000);
    const n = nrev * 2 * Math.PI / 86400, a = Math.cbrt(MU / (n * n));
    const nu = nuFromM(M * D2R, e) / D2R;
    return { name: s.name, norad: s.norad, i, raan, e, argp, M, nu: (nu + 360) % 360, a, n, revDay: nrev, epoch, hp: a * (1 - e) - RE, ha: a * (1 + e) - RE, T: 2 * Math.PI / n };
  }
  const POP = [25544, 20580, 48274, 40697, 41866, 49260, 43013, 39084];
  let satN = 0;
  function sat(host, onPick) {
    host = $(host); host.classList.add('sat'); const id = 'sat' + (++satN);
    host.innerHTML = '<label class="vh" for="' + id + 'Q">' + t('Cerca un satellite', 'Search for a satellite') + '</label>' +
      '<input id="' + id + 'Q" type="search" autocomplete="off" spellcheck="false" placeholder="' + t('Nome o numero NORAD, es. ISS', 'Name or NORAD number, e.g. ISS') + '" role="combobox" aria-expanded="false" aria-controls="' + id + 'L">' +
      '<ul id="' + id + 'L" role="listbox" hidden></ul><p class="satnote">' + t('Oppure inserisci i tuoi numeri qui sotto.', 'Or type your own numbers below.') + '</p>';
    const q = host.querySelector('input'), ul = host.querySelector('ul'), note = host.querySelector('.satnote');
    let list = [], sel = -1;
    const close = () => { ul.hidden = true; q.setAttribute('aria-expanded', 'false'); sel = -1; };
    const draw = () => {
      ul.innerHTML = list.map((s, k) => '<li role="option" id="' + id + 'O' + k + '" aria-selected="' + (k === sel) + '" data-k="' + k + '"><span>' + esc(s.name) + '</span><small>' + s.norad + '</small></li>').join('');
      ul.hidden = !list.length; q.setAttribute('aria-expanded', String(!!list.length));
      if (sel >= 0) q.setAttribute('aria-activedescendant', id + 'O' + sel); else q.removeAttribute('aria-activedescendant');
    };
    const search = () => catalog().then(cat => {
      const v = q.value.trim().toLowerCase();
      if (!v) list = POP.map(n => cat.find(s => s.norad === n)).filter(Boolean);
      else if (/^\d+$/.test(v)) list = cat.filter(s => String(s.norad).startsWith(v)).slice(0, 12);
      else { const a = cat.filter(s => s.name.toLowerCase().startsWith(v)), b = cat.filter(s => !s.name.toLowerCase().startsWith(v) && s.name.toLowerCase().includes(v)); list = a.concat(b).slice(0, 12); }
      sel = -1; draw();
    }).catch(() => { note.textContent = t('Catalogo non disponibile: inserisci i dati a mano.', 'Catalogue not available: type the data by hand.'); });
    const pick = s => {
      close(); q.value = s.name; const el = elements(s);
      note.innerHTML = t('Elementi medi del TLE del ', 'Mean TLE elements, epoch ') + el.epoch.toISOString().slice(0, 16).replace('T', ' ') + ' UTC · <a href="' + sky() + '#sat-' + s.norad + '">' + t('vedilo nel cielo', 'see it in the sky') + '</a>';
      onPick(el);
    };
    q.addEventListener('focus', search); q.addEventListener('input', search);
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { sel = Math.min(list.length - 1, sel + 1); draw(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { sel = Math.max(0, sel - 1); draw(); e.preventDefault(); }
      else if (e.key === 'Enter') { if (list[sel >= 0 ? sel : 0]) pick(list[sel >= 0 ? sel : 0]); e.preventDefault(); }
      else if (e.key === 'Escape') close();
    });
    ul.addEventListener('mousedown', e => { const li = e.target.closest('li'); if (li) { e.preventDefault(); pick(list[+li.dataset.k]); } });
    q.addEventListener('blur', () => setTimeout(close, 120));
    // ?sat=25544 nell'indirizzo (arriva dalla scheda di un satellite nel cielo)
    const want = +((location.search.match(/[?&]sat=(\d+)/) || [])[1] || 0);
    if (want) catalog().then(cat => { const s = cat.find(x => x.norad === want); if (s) pick(s); }).catch(() => {});
    return { pick };
  }

  /* ---------- Terra realistica (three.js r128) ---------- */
  function earth(THREE, R, opt) {
    R = R || 1; opt = opt || {};
    const TL = new THREE.TextureLoader(), tx = n => { const x = TL.load('tex/' + n + '.jpg'); x.anisotropy = 8; return x; };
    const sun = (opt.sun || new THREE.Vector3(5, 2.5, 4)).clone().normalize();
    const g = new THREE.Group();
    const mat = new THREE.ShaderMaterial({
      uniforms: { day: { value: tx('day') }, night: { value: tx('night') }, spec: { value: tx('spec') }, sun: { value: sun } },
      vertexShader: 'varying vec2 vUv; varying vec3 vN; varying vec3 vV; void main(){ vUv=uv; vN=normalize(normalMatrix*normal); vec4 mv=modelViewMatrix*vec4(position,1.); vV=normalize(-mv.xyz); gl_Position=projectionMatrix*mv; }',
      fragmentShader: 'uniform sampler2D day,night,spec; uniform vec3 sun; varying vec2 vUv; varying vec3 vN; varying vec3 vV; void main(){ vec3 n=normalize(vN); vec3 L=normalize((viewMatrix*vec4(sun,0.)).xyz); float d=dot(n,L); float k=smoothstep(-0.12,0.18,d); vec3 dc=texture2D(day,vUv).rgb; vec3 nc=texture2D(night,vUv).rgb*1.4; vec3 c=mix(nc,dc*(0.25+0.95*max(d,0.)),k); float sp=texture2D(spec,vUv).r; vec3 h=normalize(L+vV); c+=sp*pow(max(dot(n,h),0.),48.)*0.45*k; float f=pow(1.-max(dot(n,vV),0.),3.); c+=vec3(.25,.5,1.)*f*0.3*(0.2+k); gl_FragColor=vec4(c,1.); }'
    });
    const ball = new THREE.Mesh(new THREE.SphereGeometry(R, 128, 96), mat); g.add(ball);
    const cm = new THREE.MeshPhongMaterial({ transparent: true, opacity: 0.5, depthWrite: false });
    TL.load('tex/clouds.jpg', x => { cm.alphaMap = x; cm.needsUpdate = true; });
    const clouds = new THREE.Mesh(new THREE.SphereGeometry(R * 1.008, 96, 72), cm); g.add(clouds);
    const atm = new THREE.Mesh(new THREE.SphereGeometry(R * 1.08, 64, 48), new THREE.ShaderMaterial({
      transparent: true, side: THREE.BackSide, depthWrite: false, blending: THREE.AdditiveBlending,
      vertexShader: 'varying vec3 vN; void main(){ vN=normalize(normalMatrix*normal); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.); }',
      fragmentShader: 'varying vec3 vN; void main(){ float i=pow(0.72-dot(vN,vec3(0.,0.,1.)),3.); gl_FragColor=vec4(.3,.55,1.,1.)*i*0.42; }'
    }));
    g.add(atm);
    return { group: g, ball, clouds, setSun(v) { mat.uniforms.sun.value.copy(v).normalize(); } };
  }
  function stars(THREE, n, r) {
    n = n || 1400; r = r || 80;
    const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    for (let k = 0; k < n; k++) {
      const u = Math.random() * 2 - 1, a = Math.random() * 6.283, s = Math.sqrt(1 - u * u), rr = r * (1 + Math.random() * 0.4);
      pos.set([rr * s * Math.cos(a), rr * u, rr * s * Math.sin(a)], k * 3);
      const b = 0.45 + Math.random() * 0.55; col.set([b, b, b * (0.92 + Math.random() * 0.12)], k * 3);
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    return new THREE.Points(g, new THREE.PointsMaterial({ size: r * 0.0018, vertexColors: true, transparent: true, opacity: 0.9, depthWrite: false }));
  }
  // ECI (km) → coordinate three.js con l'asse y in alto e il raggio terrestre come unità
  const v3 = (THREE, p, unit) => new THREE.Vector3(p[0] / (unit || RE), p[2] / (unit || RE), -p[1] / (unit || RE));
  // scena pronta: renderer, camera, controlli, ridimensionamento, ciclo di disegno che si ferma fuori dallo schermo
  function scene3(THREE, host, opt) {
    host = $(host); opt = opt || {};
    const cv = document.createElement('canvas'); host.prepend(cv);
    const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(opt.fov || 38, 1, 0.01, 2000);
    scene.add(new THREE.AmbientLight(0x8a8a9a, opt.ambient == null ? 0.9 : opt.ambient));
    const light = new THREE.DirectionalLight(0xfff1e0, 1.5); light.position.set(5, 2.5, 4); scene.add(light);
    let controls = null;
    if (THREE.OrbitControls && opt.controls !== false) { controls = new THREE.OrbitControls(camera, cv); controls.enableDamping = true; controls.dampingFactor = 0.08; controls.enablePan = false; }
    const size = () => { const w = host.clientWidth, h = host.clientHeight; if (!w || !h) return; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); };
    if (window.ResizeObserver) new ResizeObserver(size).observe(host); else addEventListener('resize', size);
    size();
    let vis = true, hooks = [];
    if (window.IntersectionObserver) new IntersectionObserver(es => { vis = es[0].isIntersecting; }).observe(host);
    let last = performance.now();
    (function loop(now) {
      requestAnimationFrame(loop);
      if (!vis || document.hidden) { last = now; return; }
      const dt = Math.min(0.1, (now - last) / 1000); last = now;
      hooks.forEach(f => f(dt, now));
      if (controls) controls.update();
      renderer.render(scene, camera);
    })(last);
    return { THREE, renderer, scene, camera, controls, light, cv, size, onFrame(f) { hooks.push(f); } };
  }
  const has3D = () => { try { const c = document.createElement('canvas'); return !!(window.WebGLRenderingContext && (c.getContext('webgl') || c.getContext('experimental-webgl'))); } catch (e) { return false; } };

  /* ---------- grafici a linee ---------- */
  const C = { cy: '#35d4f2', gr: '#58e07f', vi: '#a995ff', ic: '#cfe3f5', am: '#ffb224', tx3: '#85919d' };
  function ticks(lo, hi, n) {
    if (!(hi > lo)) { hi = lo + 1; }
    const span = hi - lo, step0 = span / (n || 5), mag = Math.pow(10, Math.floor(Math.log10(step0))), r = step0 / mag;
    const step = (r < 1.5 ? 1 : r < 3 ? 2 : r < 7 ? 5 : 10) * mag, out = [];
    for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) out.push(Math.abs(v) < step * 1e-9 ? 0 : v);
    return { out, step };
  }
  function tickFmt(v, step) { const d = Math.max(0, -Math.floor(Math.log10(step) + 1e-9)); return Math.abs(v) >= 1e6 || (Math.abs(v) < 1e-3 && v !== 0) ? sig(v, 2) : fmt(v, Math.min(d, 6)); }
  // o = { title, x: [...], series: [{ name, y: [...], color, dash }], xLabel, yLabel, yFmt(v), xFmt(v), marks: [{ x, label }], yMin, yMax, h }
  function chart(host, o) {
    host = $(host); host.classList.add('chart');
    const draw = () => {
      const W = Math.max(280, host.clientWidth - 16), H = o.h || 230, L = 56, Rm = 14, T = 10, B = 34;
      const xs = o.x, all = [];
      o.series.forEach(s => s.y.forEach(v => { if (Number.isFinite(v)) all.push(v); }));
      let y0 = o.yMin != null ? o.yMin : Math.min(...all), y1 = o.yMax != null ? o.yMax : Math.max(...all);
      if (y0 === y1) { y0 -= 1; y1 += 1; }
      const pad = (y1 - y0) * 0.06; if (o.yMin == null) y0 -= pad; if (o.yMax == null) y1 += pad;
      const x0 = xs[0], x1 = xs[xs.length - 1];
      const X = v => L + (v - x0) / (x1 - x0 || 1) * (W - L - Rm), Y = v => T + (1 - (v - y0) / (y1 - y0)) * (H - T - B);
      const ty = ticks(y0, y1, 5), tx = ticks(x0, x1, Math.max(3, Math.floor(W / 110)));
      let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img" aria-label="' + esc(o.title || '') + '">';
      ty.out.forEach(v => { if (v < y0 || v > y1) return; s += '<line class="gd" x1="' + L + '" x2="' + (W - Rm) + '" y1="' + Y(v) + '" y2="' + Y(v) + '"/><text x="' + (L - 6) + '" y="' + (Y(v) + 4) + '" text-anchor="end">' + (o.yFmt ? o.yFmt(v) : tickFmt(v, ty.step)) + '</text>'; });
      tx.out.forEach(v => { if (v < x0 || v > x1) return; s += '<line class="gd" y1="' + T + '" y2="' + (H - B) + '" x1="' + X(v) + '" x2="' + X(v) + '" opacity=".6"/><text x="' + X(v) + '" y="' + (H - B + 15) + '" text-anchor="middle">' + (o.xFmt ? o.xFmt(v) : tickFmt(v, tx.step)) + '</text>'; });
      s += '<line class="ax" x1="' + L + '" x2="' + (W - Rm) + '" y1="' + (H - B) + '" y2="' + (H - B) + '"/>';
      if (o.xLabel) s += '<text x="' + (W - Rm) + '" y="' + (H - 4) + '" text-anchor="end">' + esc(o.xLabel) + '</text>';
      if (o.yLabel) s += '<text x="' + 4 + '" y="' + (T + 2) + '" text-anchor="start" dominant-baseline="hanging" opacity="0">' + '</text>';
      (o.marks || []).forEach(m => { if (m.x < x0 || m.x > x1) return; s += '<line x1="' + X(m.x) + '" x2="' + X(m.x) + '" y1="' + T + '" y2="' + (H - B) + '" stroke="' + (m.color || C.tx3) + '" stroke-dasharray="3 3"/><text x="' + (X(m.x) + 4) + '" y="' + (T + 11) + '" style="fill:' + (m.color || C.tx3) + '">' + esc(m.label || '') + '</text>'; });
      (o.bands || []).forEach(b => { s += '<rect x="' + X(b.x0) + '" width="' + Math.max(0, X(b.x1) - X(b.x0)) + '" y="' + T + '" height="' + (H - T - B) + '" fill="' + (b.color || '#fff') + '" opacity="' + (b.op || 0.06) + '"/>'; });
      o.series.forEach(se => {
        let d = '', pen = false;
        se.y.forEach((v, k) => { if (!Number.isFinite(v)) { pen = false; return; } d += (pen ? 'L' : 'M') + X(xs[k]).toFixed(1) + ' ' + Y(Math.max(y0, Math.min(y1, v))).toFixed(1); pen = true; });
        s += '<path d="' + d + '" fill="none" stroke="' + (se.color || C.cy) + '" stroke-width="2" stroke-linejoin="round"' + (se.dash ? ' stroke-dasharray="5 4"' : '') + '/>';
      });
      s += '<line class="hx" y1="' + T + '" y2="' + (H - B) + '" stroke="' + C.ic + '" stroke-opacity=".5" visibility="hidden"/>';
      o.series.forEach((se, k) => { s += '<circle data-k="' + k + '" r="4" fill="' + (se.color || C.cy) + '" stroke="#000" stroke-width="2" visibility="hidden"/>'; });
      s += '<rect x="' + L + '" y="' + T + '" width="' + (W - L - Rm) + '" height="' + (H - T - B) + '" fill="transparent" style="cursor:crosshair"/></svg>';
      const head = '<div class="ttl"><b>' + esc(o.title || '') + '</b>' + (o.yLabel ? '<span>' + esc(o.yLabel) + '</span>' : '') +
        (o.series.length > 1 ? o.series.map(se => '<span style="color:' + (se.color || C.cy) + '"><i></i><span style="color:var(--tx2)">' + esc(se.name) + '</span></span>').join('') : '') + '</div>';
      host.innerHTML = head + s + '<div class="tip" hidden></div>';
      const svg = host.querySelector('svg'), tip = host.querySelector('.tip'), hx = svg.querySelector('.hx'), dots = svg.querySelectorAll('circle'), hit = svg.querySelector('rect:last-of-type');
      const show = ev => {
        const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) * W / r.width;
        const xv = x0 + (px - L) / (W - L - Rm) * (x1 - x0);
        let k = 0, best = Infinity; xs.forEach((v, j) => { const d = Math.abs(v - xv); if (d < best) { best = d; k = j; } });
        hx.setAttribute('x1', X(xs[k])); hx.setAttribute('x2', X(xs[k])); hx.setAttribute('visibility', 'visible');
        let html = '<span style="color:var(--tx2)">' + (o.xName ? esc(o.xName) + ' ' : '') + (o.xFmt ? o.xFmt(xs[k]) : sig(xs[k], 4)) + '</span>';
        o.series.forEach((se, j) => { const v = se.y[k]; const c = dots[j]; if (Number.isFinite(v)) { c.setAttribute('cx', X(xs[k])); c.setAttribute('cy', Y(Math.max(y0, Math.min(y1, v)))); c.setAttribute('visibility', 'visible'); } else c.setAttribute('visibility', 'hidden');
          html += '<span style="color:' + (se.color || C.cy) + '">' + (o.series.length > 1 ? esc(se.name) + ' ' : '') + (o.yFmt ? o.yFmt(v) : sig(v, 4)) + (o.unit ? ' ' + esc(o.unit) : '') + '</span>'; });
        tip.innerHTML = html; tip.hidden = false;
        const hr = host.getBoundingClientRect(), tw = tip.offsetWidth, cx = ev.clientX - hr.left;
        tip.style.left = Math.min(hr.width - tw - 6, Math.max(6, cx + 12)) + 'px'; tip.style.top = (ev.clientY - hr.top - 46) + 'px';
      };
      const hide = () => { tip.hidden = true; hx.setAttribute('visibility', 'hidden'); dots.forEach(c => c.setAttribute('visibility', 'hidden')); };
      hit.addEventListener('pointermove', show); hit.addEventListener('pointerdown', show); hit.addEventListener('pointerleave', hide);
    };
    draw();
    if (!host._ro && window.ResizeObserver) { let w = host.clientWidth; host._ro = new ResizeObserver(() => { if (host._draw && Math.abs(host.clientWidth - w) > 4) { w = host.clientWidth; host._draw(); } }); host._ro.observe(host); }
    host._draw = draw;
  }

  function unchart(host) { host = $(host); if (!host) return; host._draw = null; host.innerHTML = ''; }   // toglie un grafico (non si ridisegna più)

  /* ---------- salvare i risultati ---------- */
  function csv(name, head, data) {
    const sep = en ? ',' : ';', dec = v => typeof v === 'number' ? (en ? String(v) : String(v).replace('.', ',')) : '"' + String(v).replace(/"/g, '""') + '"';
    const txt = [head.map(dec).join(sep)].concat(data.map(r => r.map(dec).join(sep))).join('\r\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿' + txt], { type: 'text/csv' })); a.download = name; document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }

  /* ---------- schede di modo ---------- */
  function tabs(host, onChange) {     // <div class="seg" role="tablist"><button role="tab" data-m="..." aria-controls="...">
    host = $(host); const bs = [...host.querySelectorAll('[role=tab]')];
    const set = m => { bs.forEach(b => { const on = b.dataset.m === m; b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1; const p = $(b.getAttribute('aria-controls')); if (p) p.hidden = !on; }); onChange && onChange(m); };
    host.addEventListener('click', e => { const b = e.target.closest('[role=tab]'); if (b) set(b.dataset.m); });
    host.addEventListener('keydown', e => { const k = bs.indexOf(document.activeElement); if (k < 0) return; let j = k; if (e.key === 'ArrowRight') j = (k + 1) % bs.length; else if (e.key === 'ArrowLeft') j = (k - 1 + bs.length) % bs.length; else return; bs[j].focus(); set(bs[j].dataset.m); e.preventDefault(); });
    return { set, get: () => (bs.find(b => b.getAttribute('aria-selected') === 'true') || bs[0]).dataset.m };
  }

  return { $, lang, en, t, init, applyLang, SUBJ, sky, num, fmt, sig, plain, der, clear, bad, given, esc, rows, msg, live, keep, save, fill, wipe,
    MU, RE, J2, D2R, G0, OMEGA_E, kepler, nuFromM, gmst, pqw2eci, catalog, elements, sat, earth, stars, v3, scene3, has3D, C, chart, unchart, ticks, csv, tabs };
})();
