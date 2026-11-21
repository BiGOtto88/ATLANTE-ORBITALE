# Laboratorio di Keplario: come si fa una pagina

Keplario ha due posti:

- **Cielo** (`index.html`, `en/index.html`): i satelliti veri, in 3D, in tempo reale.
- **Laboratorio**: sei pagine di calcolo, una per materia. Ognuna parte dai numeri dell'utente oppure da un satellite reale.

| file | materia (it / en) |
|---|---|
| `orbite.html` | Orbite e manovre / Orbits and manoeuvres |
| `assetto.html` | Assetto e controllo / Attitude and control |
| `propulsione.html` | Propulsione e lanciatori / Propulsion and launchers |
| `strutture.html` | Strutture e materiali / Structures and materials |
| `comunicazioni.html` | Comunicazioni e navigazione / Communications and navigation |
| `sistemi.html` | Sistemi e missione / Systems and mission |

## File

- Sorgente di una pagina: `sorgente/laboratorio/<nome>.html`, con i segnaposto `<!--KIT:CSS-->` nel `<head>` e `<!--KIT:JS-->` prima dello script della pagina.
- Stile e funzioni comuni: `sorgente/laboratorio/kit.css` e `kit.js` (oggetto globale `K`, documentato in cima a `kit.js`). **Non modificarli**: se ti serve una funzione in più, scrivila nello script della tua pagina e segnalala nel resoconto finale.
- Pagina pubblicata: `python3 strumenti/costruisci_laboratorio.py <nome>` scrive `<nome>.html` nella radice con kit dentro.
- Esempio completo e funzionante: `sorgente/laboratorio/_modello.html` (orbita circolare). Parti da lì.
- Librerie disponibili in `vendor/`: `three.min.js` (r128), `OrbitControls.js`, `GLTFLoader.js`, `satellite.min.js`. Texture della Terra in `tex/` (usale con `K.earth`). Modelli NASA in `modelli/` (iss, hubble, jwst, juno .glb). Nessuna libreria da internet.

## Come deve funzionare una pagina

1. **Dai quello che sai, il resto lo ricava la pagina.** Niente bottone «Calcola»: si ricalcola a ogni modifica (`K.live`). I campi lasciati vuoti mostrano in verde il valore ricavato (`K.der`). Se l'utente dà dati in più che non tornano, il campo in conflitto si colora d'ambra (`K.bad`) e un messaggio dice quali numeri non tornano e quanto dovrebbero valere.
2. **Schede di modo** (`.seg`, `K.tabs`) per le parti diverse della materia, più una scheda finale «Come funziona» / «How it works» con formule, ipotesi, limiti e fonti (libri e norme: Curtis, Vallado, Wertz-Larson SMAD, Sutton, ECSS, NASA SP-8007…).
3. **Una vista che si capisce al volo** per ogni modo: 3D con `K.scene3` + `K.earth` quando c'è la Terra (Terra realistica, mai una sfera blu), oppure un disegno 2D in SVG/canvas fatto bene. Le cose si muovono solo se il movimento spiega qualcosa (un'orbita percorsa, un modo di vibrare, il propellente che finisce). Se WebGL manca (`K.has3D()`), la pagina funziona lo stesso.
4. **Risultati** con `K.rows`: etichetta, valore, unità, nota facoltativa (da cosa è ricavato). Il risultato principale con classe `key`. Grafici con `K.chart` (assi con unità, legenda se più serie, lettura al passaggio del puntatore).
5. **Compila un esempio** (dati realistici di un caso vero) e **Svuota**. I dati restano nell'indirizzo (`K.keep` + `K.save`) così il calcolo si può condividere.
6. **Satellite reale** (`K.sat`) dove l'orbita conta: compila i campi con gli elementi del TLE. Funziona anche con `?sat=25544` nell'indirizzo (arriva dalla scheda di un satellite nel Cielo).
7. **Prova interna**: una funzione `selfTest()` nello script confronta 2–4 casi con valori noti dei libri (tolleranza scritta) e scrive l'esito in console con `console.info('selfTest', …)`. Va chiamata solo con `?test` nell'indirizzo.

## Aspetto

- Colori (variabili in `kit.css`): fondo nero, pannelli `--pn`, linee sottili `--ln`. **Ciano** `--cy` = cose che si toccano e prima serie dei grafici. **Verde** `--gr` = valori calcolati. **Viola chiaro** `--vi` e **ghiaccio** `--ic` = seconda e terza serie. **Ambra** `--am` solo per avvisi. **Mai** rosso, magenta, giallo come decorazione, mai sfondi bianchi, mai sfumature, bagliori o ombre colorate.
- Carattere: B612 per tutto (anche i numeri). Testo in minuscolo normale: **niente MAIUSCOLE** su etichette o bottoni, niente spaziatura larga tra le lettere, niente etichette sopra i titoli.
- Angoli piccoli (6 px), niente pillole. Bottoni `.btn`; il bottone pieno `.btn.pri` al massimo uno per pagina.
- Una cosa memorabile per pagina (la vista), tutto il resto quieto.
- Deve funzionare bene a 390 px di larghezza (telefono) e a 1440 px.

## Scrittura

- Italiano come base, inglese con `data-en="…"` sullo stesso elemento (anche `data-en-aria-label`, `data-en-placeholder`, `data-en-content` per la descrizione). Nei testi creati da script: `K.t('italiano', 'English')`.
- Frasi corte, verbi semplici, si parla all'utente con il «tu». Dire cosa fa una cosa, non venderla.
- Vietati: «cruciale», «fondamentale», «nel panorama», «immergiamoci», «sbloccare», «rivoluzionario», «potente», «intuitivo», punti esclamativi, frasi motivazionali, riassunti finali.
- Niente università, corsi, esami o semestri: è uno strumento per chiunque.
- Messaggi d'errore: dicono cosa non va e come si sistema, con i numeri. Mai scuse.
- Numeri con `K.fmt` / `K.sig` (virgola in italiano, punto in inglese, spazio per le migliaia). Unità SI, gradi per gli angoli.

## Fisica

- Formule esatte e standard, niente stime inventate. Se un modello è semplificato, la scheda «Come funziona» lo dice (es. «Terra sferica», «ombra cilindrica»).
- Costanti in `K`: `MU` 398600.4418 km³/s², `RE` 6378.137 km, `J2`, `G0` 9.80665 m/s², `OMEGA_E`.
- Controlla sempre i casi limite (divisioni per zero, radici di numeri negativi, valori fuori dominio): mai `NaN` a schermo, al suo posto un messaggio.

## Head della pagina (SEO)

`<title>` sotto i 60 caratteri, `<meta name="description">` sotto i 155, `<link rel="canonical" href="https://ottonspace.github.io/KEPLARIO/<nome>.html">`, JSON-LD `WebApplication` come nel modello, un solo `<h1>`.

## Provare

```
cd /home/claude/repo
python3 strumenti/costruisci_laboratorio.py <nome>
python3 -m http.server <porta>          # la porta assegnata, in sottofondo
python3 /home/claude/shot_lab.py "http://localhost:<porta>/<nome>.html" /home/claude/audit/<nome>-d.png 1440 900
python3 /home/claude/shot_lab.py "http://localhost:<porta>/<nome>.html" /home/claude/audit/<nome>-m.png 390 844
python3 /home/claude/shot_lab.py "http://localhost:<porta>/<nome>.html?lang=en" /home/claude/audit/<nome>-en.png 1440 900 en-GB
```
Lo script stampa gli errori JavaScript: devono essere zero. Il sesto argomento facoltativo è codice JS da eseguire prima dello scatto (per esempio cliccare una scheda). Guarda le immagini e correggi quello che non va (testi tagliati, sovrapposizioni, campi troppo stretti, viste vuote).
