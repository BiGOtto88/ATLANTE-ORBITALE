// Prova del servizio (assistente/worker.js) senza rete: finge le risposte di Gemini e di Anthropic e controlla la traduzione dei messaggi.
// Uso: node strumenti/prove/prova_worker.mjs [cartella_del_sito]
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path';
const radice = path.resolve(process.argv[2] || '.');
const tmp = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'wk-')), 'worker.mjs');
fs.copyFileSync(path.join(radice, 'assistente/worker.js'), tmp);
const W = (await import(tmp)).default;
let ok = true; const verifica = (n, c, d = '') => { ok = ok && !!c; console.log(c ? 'ok    ' : 'ERRORE', n, d); };
const ORIGIN = 'https://prova.github.io';
let visto = null, risposta = null;
globalThis.fetch = async (url, init) => { visto = { url: String(url), init, body: JSON.parse(init.body) }; const r = risposta; return new Response(JSON.stringify(r.body), { status: r.status || 200 }); };
const chiama = (env, messages, extra = {}) => W.fetch(new Request('https://w.prova/', { method: 'POST', headers: { Origin: ORIGIN, 'content-type': 'application/json' }, body: JSON.stringify({ messages, lang: 'it', ctx: {}, ...extra }) }), { ALLOWED_ORIGIN: ORIGIN, ...env });
const G = { GEMINI_API_KEY: 'k-g' };

// 1) prima richiesta: testo dell'utente
risposta = { body: { candidates: [{ content: { parts: [{ thought: true, text: 'ragiono' }, { functionCall: { name: 'calc', args: { expression: '1+1' } }, thoughtSignature: 'SIG1' }, { functionCall: { name: 'find_objects', args: { query: 'ISS' } } }] } }] } };
let r = await chiama(G, [{ role: 'user', content: 'ciao' }]); let o = await r.json();
verifica('gemini: indirizzo, modello e chiave', visto.url.includes('/models/gemini-3.5-flash-lite:generateContent') && visto.init.headers['x-goog-api-key'] === 'k-g', visto.url);
verifica('gemini: istruzioni di sistema e domanda', visto.body.systemInstruction.parts[0].text.includes('Keplario') && visto.body.contents[0].role === 'user' && visto.body.contents[0].parts[0].text === 'ciao');
const dec = visto.body.tools[0].functionDeclarations;
verifica('gemini: tutti gli strumenti dichiarati', dec.length >= 15 && dec.every(d => d.name && d.description), String(dec.length));
verifica('gemini: strumento senza parametri senza schema', !dec.find(d => d.name === 'snapshot_3d').parameters);
verifica('gemini: schemi puliti', !JSON.stringify(dec).includes('additionalProperties') && dec.find(d => d.name === 'kepler_to_state').parameters.required.length === 6);
verifica('gemini: risposta tradotta (strumenti e firma, niente pensiero)', o.stop_reason === 'tool_use' && o.content.length === 2 && o.content[0].type === 'tool_use' && o.content[0].sig === 'SIG1' && o.content[1].sig === undefined && o.content[0].input.expression === '1+1', JSON.stringify(o).slice(0, 200));

// 2) ritorno degli esiti: nomi ricavati dagli id, firma rimandata
const asst = o.content; const turno2 = [{ role: 'user', content: 'ciao' }, { role: 'assistant', content: asst }, { role: 'user', content: [{ type: 'tool_result', tool_use_id: asst[0].id, content: '{"value":2}' }, { type: 'tool_result', tool_use_id: asst[1].id, content: 'testo non json', is_error: true }] }];
risposta = { body: { candidates: [{ content: { parts: [{ text: 'Fatto: 2', thoughtSignature: 'SIG2' }] } }] } };
r = await chiama(G, turno2); o = await r.json(); const c = visto.body.contents;
verifica('gemini: chiamata del modello con firma rimandata', c[1].role === 'model' && c[1].parts[0].functionCall.name === 'calc' && c[1].parts[0].thoughtSignature === 'SIG1' && !c[1].parts[1].thoughtSignature);
verifica('gemini: esiti come functionResponse con il nome giusto', c[2].role === 'user' && c[2].parts[0].functionResponse.name === 'calc' && c[2].parts[0].functionResponse.response.value === 2 && c[2].parts[1].functionResponse.name === 'find_objects' && c[2].parts[1].functionResponse.response.error === 'testo non json');
verifica('gemini: risposta finale di testo', o.stop_reason === 'end_turn' && o.content[0].text === 'Fatto: 2' && o.content[0].sig === 'SIG2');

// 3) casi limite
risposta = { status: 429, body: { error: 'quota' } }; r = await chiama(G, [{ role: 'user', content: 'x' }]);
verifica('gemini: troppe richieste → 429 limite', r.status === 429 && (await r.json()).error === 'limit');
risposta = { status: 400, body: { error: 'x' } }; r = await chiama(G, [{ role: 'user', content: 'x' }]);
verifica('gemini: altro errore → 502 senza dettagli', r.status === 502 && !(JSON.stringify(await r.json())).includes('x"'));
risposta = { body: { candidates: [], promptFeedback: { blockReason: 'SAFETY' } } }; r = await chiama(G, [{ role: 'user', content: 'x' }]); o = await r.json();
verifica('gemini: risposta bloccata → testo di cortesia', o.stop_reason === 'end_turn' && /Non riesco/.test(o.content[0].text));
risposta = { body: { candidates: [{ content: { parts: [{ text: 'ok' }] } }] } }; await chiama({ ...G, MODEL: 'gemini-x', THINKING_LEVEL: 'low' }, [{ role: 'user', content: 'x' }]);
verifica('gemini: MODEL e THINKING_LEVEL rispettati', visto.url.includes('gemini-x:') && visto.body.generationConfig.thinkingConfig.thinkingLevel === 'low');

// 4) scelta del fornitore e Anthropic invariato (firme tolte)
risposta = { body: { content: [{ type: 'text', text: 'ciao' }], stop_reason: 'end_turn' } };
r = await chiama({ ANTHROPIC_API_KEY: 'k-a' }, [{ role: 'user', content: 'a' }, { role: 'assistant', content: [{ type: 'text', text: 'b', sig: 'S' }] }, { role: 'user', content: 'c' }]);
verifica('anthropic: scelto se c\'è solo la sua chiave, firme tolte', visto.url.includes('api.anthropic.com') && !JSON.stringify(visto.body.messages).includes('"sig"') && r.status === 200);
await chiama({ ANTHROPIC_API_KEY: 'k-a', GEMINI_API_KEY: 'k-g', PROVIDER: 'anthropic' }, [{ role: 'user', content: 'a' }]);
verifica('PROVIDER=anthropic ha la precedenza', visto.url.includes('api.anthropic.com'));
risposta = { body: { candidates: [{ content: { parts: [{ text: 'ok' }] } }] } }; await chiama({ ANTHROPIC_API_KEY: 'k-a', GEMINI_API_KEY: 'k-g' }, [{ role: 'user', content: 'a' }]);
verifica('con entrambe le chiavi vince Gemini', visto.url.includes('googleapis'));
r = await chiama({}, [{ role: 'user', content: 'a' }]); verifica('senza chiavi: non configurato', r.status === 500);
r = await W.fetch(new Request('https://w.prova/', { method: 'POST', headers: { Origin: 'https://altro.it' }, body: '{}' }), { ALLOWED_ORIGIN: ORIGIN, ...G }); verifica('origine diversa rifiutata', r.status === 403);
process.exit(ok ? 0 : 1);
