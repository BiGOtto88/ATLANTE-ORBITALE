# Atlante Orbitale: sito autonomo e app installabile

Questa cartella è il sito completo. Non dipende da Claude né da altri servizi per funzionare:
librerie, caratteri, texture e dati sono tutti qui dentro. È un sito statico, quindi va bene
qualsiasi hosting; le istruzioni qui sotto usano GitHub Pages perché è gratuito e sa anche
aggiornare i dati da solo ogni giorno.

## Provarlo sul tuo computer

Serve Python 3. Dal terminale, dentro questa cartella:

```
python3 -m http.server 8000
```

poi apri `http://localhost:8000` nel browser. Aprire `index.html` con un doppio clic non basta:
il browser blocca la lettura dei file di dati se la pagina non arriva da un server.

## Pubblicarlo su GitHub Pages

1. Crea un repository su GitHub (per esempio `atlante-orbitale`). Con un account gratuito deve essere pubblico.
2. Carica **il contenuto** di questa cartella nel ramo `main`, compresa la cartella nascosta `.github`.
3. Nel repository apri **Settings → Pages** e alla voce **Source** scegli **GitHub Actions**.
4. Apri la scheda **Actions**, scegli «Aggiorna i dati e pubblica il sito» e premi **Run workflow**.
5. Dopo un paio di minuti il sito è all'indirizzo `https://TUO-NOME.github.io/atlante-orbitale/`.

Da quel momento il flusso riparte da solo ogni giorno alle 04:23 UTC e a ogni modifica che carichi.

## Installarlo come applicazione

Il sito pubblicato (o `localhost`) si installa come un'app, con la sua icona e la sua finestra:

- **Computer, Chrome o Edge:** pulsante **Installa** nella striscia in alto dell'app, oppure l'icona di installazione nella barra dell'indirizzo.
- **Android, Chrome:** pulsante **Installa**, oppure menu ⋮ → «Aggiungi a schermata Home».
- **iPhone e iPad, Safari:** Condividi → «Aggiungi alla schermata Home».
- **Mac, Safari:** File → «Aggiungi al Dock».

Dopo la prima apertura l'app parte anche senza rete, con gli ultimi dati scaricati. Le missioni
che progetti restano salvate nel browser del dispositivo su cui le hai create.

## Come si aggiornano i dati

| Dato | File | Fonte | Chi lo aggiorna |
| --- | --- | --- | --- |
| Satelliti terrestri | `data/active.txt`, `data/meta.json` | CelesTrak, con una copia su GitHub come riserva | `strumenti/aggiorna_tle.py`, ogni giorno |
| Data e sito reali dei lanci | `data/lanci.json` | catalogo SATCAT di CelesTrak | `strumenti/aggiorna_tle.py`, ogni giorno |
| Sonde oltre l'orbita terrestre | `data/probes.json` | JPL Horizons | `strumenti/aggiorna_sonde.py`, ogni giorno |
| Pianeti e lune | calcolati nella pagina | Astronomy Engine | niente da aggiornare |
| Stelle, texture | `data/stars.json`, `tex/` | fissi | niente da aggiornare |

Un file nuovo sostituisce quello vecchio solo se supera i controlli (formato, cifre di controllo
dei TLE, nome della sonda restituito da Horizons, scarto del modello dalle effemeridi). Se una
fonte non risponde, il sito resta con i dati di prima. Se il catalogo pubblicato ha più di 36 ore,
la pagina chiede i TLE direttamente a CelesTrak dal browser di chi la apre.

I due strumenti si possono lanciare anche a mano, dalla cartella del sito:

```
python3 strumenti/aggiorna_tle.py
python3 strumenti/aggiorna_sonde.py            # tutte le sonde, circa due minuti
python3 strumenti/aggiorna_sonde.py --solo MRO,JUNO --prova
```

Per aggiungere una sonda: una riga nella tabella `SONDE` di `strumenti/aggiorna_sonde.py`
(sigla, numero Horizons, tipo) e la sua scheda nella tabella `PINFO` della pagina.

## Forme reali dei veicoli

Avvicinando la camera a un veicolo (pulsante **Vicino**, oppure **Segui** e poi la rotella) si vede il suo modello 3D.
I modelli in `modelli/` vengono dalla raccolta pubblica NASA 3D Resources e coprono 33 veicoli: ISS, Hubble, James Webb,
Terra, Aqua, Aura, Landsat 8 e 9, Suomi NPP e NOAA-20, GOES, TDRS, Chandra, Fermi, GPM, ICESat-2, OCO-2, Sentinel-6,
GRACE-FO, SDO, THEMIS, Juno, MRO, LRO, Mars Odyssey, Parker Solar Probe, Voyager, OSIRIS-REx, SOHO, ACE, DSCOVR, STEREO
e altri. Gli altri satelliti restano con la forma schematica a parallelepipedo e due ali.

Per aggiungere un modello: scarica il file `.glb`, aggiungi una riga a `strumenti/modelli/elenco.json` (nome del file,
dimensione massima reale in metri, numero di triangoli da tenere) e lancia

```
cd strumenti/modelli
npm install @gltf-transform/core @gltf-transform/extensions @gltf-transform/functions meshoptimizer draco3d sharp
node prepara.mjs CARTELLA-DEI-GLB ../../modelli elenco.json
```

poi collega il modello al satellite nella tabella `REAL_SAT` (o `REAL_PROBE`) della pagina. Lo strumento porta il modello
in metri e lo orienta con il lato più lungo sull'asse z del corpo, dove stanno le ali; quale faccia guardi la Terra non
si ricava dal file, quindi può non coincidere con l'assetto di volo reale.

## Modificare l'app

Il codice dell'app è uno solo: `sorgente/pagina-claude.html`, la stessa pagina pubblicata come
artifact in Claude. `index.html` si ricava da quella e non va modificato a mano.

```
python3 strumenti/da_claude_a_sito.py sorgente/pagina-claude.html
```

Lo strumento aggiunge la testata del sito e punta le librerie alle copie in `vendor/`.
Dopo una modifica fatta con Claude: salva la pagina aggiornata in `sorgente/`, lancia il comando
qui sopra e carica il risultato su GitHub; il flusso ripubblica il sito.

Prove automatiche, da lanciare dopo aver toccato gli strumenti o la pagina:

```
python3 strumenti/prove/prova_sonde.py                 # formule e strumento delle sonde, senza rete
python3 strumenti/prove/prova_sito.py . /tmp/schermate # il sito in un browser, con e senza rete (serve Playwright)
python3 strumenti/prove/prova_migliorie.py . /tmp/schermate # pagina Percorso, controllo PD e B-dot, margini ADCS (serve Playwright)
python3 strumenti/prove/prova_disturbi.py . /tmp/schermate  # disturbi ricalcolati a parte, IGRF, ombra, lancio reale (servono anche numpy e ppigrf)
python3 strumenti/prove/prova_forme.py . /tmp/schermate     # forme reali: camera vicina a più veicoli (serve Playwright)
```

## Cosa c'è nella cartella

```
index.html              la pagina del sito (generata)
manifest.webmanifest    nome, icone e colori dell'app installata
sw.js                   tiene una copia del sito sul dispositivo per l'uso senza rete
data/                   satelliti, lanci, sonde, stelle
tex/                    texture di Terra, Luna, Sole e pianeti
modelli/                forme reali: modelli 3D dei veicoli (NASA 3D Resources), già in metri e negli assi dell'app
vendor/                 three.js r128, satellite.js 5.0.0, Astronomy Engine 2.1.19
fonts/                  carattere B612
icone/                  icona dell'app
sorgente/               la pagina sviluppata in Claude
strumenti/              aggiornamento dei dati, conversione della pagina, prove
.github/workflows/      aggiornamento giornaliero e pubblicazione su GitHub Pages
LICENZE.txt             licenze delle librerie e del carattere inclusi
```

## Prima di rendere pubblico il sito

- Le texture in `tex/` vengono dalle prime fasi del progetto e la loro provenienza non è annotata:
  controlla da dove arrivano e con quale licenza, e aggiungi il credito richiesto.
- I TLE sono dati pubblici di CelesTrak, le effemeridi delle sonde di JPL Horizons, le stelle dal
  catalogo Hipparcos: è buona norma citarli nella pagina o nel repository.
