# Keplario: sito autonomo e app installabile

Keplario, il planetario delle orbite (in inglese *the orbit planetarium*): il nome unisce Keplero e «planetario».
Fino al 15 novembre 2026 il progetto si chiamava Atlante Orbitale.

Questa cartella è il sito completo. Non dipende da altri servizi per funzionare:
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

1. Crea un repository su GitHub (per esempio `keplario`). Con un account gratuito deve essere pubblico.
2. Carica **il contenuto** di questa cartella nel ramo `main`, compresa la cartella nascosta `.github`.
3. Nel repository apri **Settings → Pages** e alla voce **Source** scegli **GitHub Actions**.
4. Apri la scheda **Actions**, scegli «Aggiorna i dati e pubblica il sito» e premi **Run workflow**.
5. Dopo un paio di minuti il sito è all'indirizzo `https://TUO-NOME.github.io/keplario/` (in inglese `…/keplario/en/`).

Da quel momento il flusso riparte da solo ogni giorno alle 04:23 UTC e a ogni modifica che carichi.

## Nome del repository

**Il repository si chiama `KEPLARIO` e resta così**: il sito è già nei motori di ricerca a questo indirizzo (GitHub Pages distingue le maiuscole) e `SITO` in `strumenti/costruisci_sito.py` è `https://ottonspace.github.io/KEPLARIO/`. Rinominarlo farebbe perdere l'indirizzo indicizzato. Il resto di questa sezione vale solo se un giorno cambierai nome.

### Come cambiare nome al repository

Il repository esistente si rinomina senza perdere nulla: **Settings → General → Repository name** → `keplario` → **Rename**.
GitHub reindirizza da solo il vecchio indirizzo del repository, ma **non** quello del sito: dopo il cambio il sito è a
`https://ottonspace.github.io/KEPLARIO/` e il vecchio `…/ATLANTE-ORBITALE/` smette di funzionare. Poiché il sito non era ancora
nei motori di ricerca, conviene farlo adesso. Poi riavvia il flusso (Actions → «Aggiorna i dati e pubblica il sito» → Run workflow).
Se preferisci tenere il vecchio nome del repository, rimetti il vecchio indirizzo nella variabile `SITO` di `strumenti/costruisci_sito.py`.

## Italiano e inglese

La pagina si apre in inglese per chi ha il browser in un'altra lingua e in italiano per chi lo ha in italiano; il pulsante EN/IT
in alto cambia lingua e la ricorda. Per i motori di ricerca ci sono due indirizzi, `…/keplario/` (italiano) e `…/keplario/en/`
(inglese, stessa pagina con titolo e descrizione in inglese), collegati fra loro e tutti e due nella `sitemap.xml`; anche
`?lang=en` alla fine dell'indirizzo apre la versione inglese.

## Farlo trovare su Google e Bing

Un sito nuovo non compare subito nelle ricerche: i motori lo trovano seguendo i link da altri siti, e senza
nessun link possono passare settimane. Per accelerare (gratis, una volta sola):

1. **Google Search Console** (https://search.google.com/search-console): «Aggiungi proprietà» → tipo **Prefisso URL** →
   `https://ottonspace.github.io/KEPLARIO/`. Come verifica scegli **File HTML**: scarica il file che ti dà
   (si chiama `google` seguito da lettere e numeri, `.html`), caricalo nella cartella principale del repository e aspetta
   che il flusso «Aggiorna i dati e pubblica il sito» finisca (scheda Actions); poi torna su Search Console e premi **Verifica**.
   Verificato il sito, apri **Sitemap** e invia `sitemap.xml`; poi in **Controllo URL** incolla l'indirizzo del sito
   e premi **Richiedi indicizzazione**.
2. **Bing Webmaster Tools** (https://www.bing.com/webmasters): «Importa da Google Search Console», così non serve rifare la verifica.
   Bing fornisce i risultati anche a DuckDuckGo, Yahoo ed Ecosia.
3. Metti il link al sito dove capita: profilo GitHub (campo «Website» del repository), LinkedIn, forum, pagina del corso.
   Ogni link da un sito già noto aiuta.

Il sito ha già quello che serve ai motori: titolo e descrizione, indirizzo canonico, `sitemap.xml`, dati strutturati
schema.org (WebApplication) e un'immagine di anteprima (`icone/anteprima.jpg`) per i link condivisi.
L'indirizzo del sito è scritto in `strumenti/costruisci_sito.py` (variabile `SITO`): se cambia, aggiornalo lì e riconverti.
Un dominio tutto tuo (per esempio `keplario.com` o `keplario.it`, una decina di euro all'anno; controlla che sia libero) si collega a GitHub Pages da
**Settings → Pages → Custom domain** e rende il nome più facile da ricordare, ma non è necessario per comparire nelle ricerche.

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

Il codice dell'app è uno solo: `sorgente/pagina-sorgente.html`, la stessa pagina pubblicata come
anteprima incorporata. `index.html` si ricava da quella e non va modificato a mano.

```
python3 strumenti/costruisci_sito.py sorgente/pagina-sorgente.html
```

Lo strumento aggiunge la testata del sito e punta le librerie alle copie in `vendor/`.
Dopo una modifica alla pagina: salva la pagina aggiornata in `sorgente/`, lancia il comando
qui sopra e carica il risultato su GitHub; il flusso ripubblica il sito.

Prove automatiche, da lanciare dopo aver toccato gli strumenti o la pagina:

```
python3 strumenti/prove/prova_sonde.py                 # formule e strumento delle sonde, senza rete
python3 strumenti/prove/prova_sito.py . /tmp/schermate # il sito in un browser, con e senza rete (serve Playwright)
python3 strumenti/prove/prova_migliorie.py . /tmp/schermate # pagina Percorso, controllo PD e B-dot, margini ADCS (serve Playwright)
python3 strumenti/prove/prova_disturbi.py . /tmp/schermate  # disturbi ricalcolati a parte, IGRF, ombra, lancio reale (servono anche numpy e ppigrf)
python3 strumenti/prove/prova_forme.py . /tmp/schermate     # forme reali: camera vicina a più veicoli (serve Playwright)
node strumenti/prove/prova_motore.js                        # motore di calcolo: gravità, orbite, vita orbitale, Lambert, ADCS (serve solo Node)
```

Il flusso **Verifica dei modelli** (`.github/workflows/verifica.yml`) esegue `prova_motore.js` a ogni modifica e ogni lunedì,
e in più ricalcola il riferimento indipendente in Python (SHTOOLS, ERFA, effemeridi JPL DE421, SciPy) per confrontarlo con
il motore della pagina. Anche il flusso di pubblicazione esegue `prova_motore.js`: se una prova non passa, il sito non viene
ripubblicato e resta in linea l'ultima versione verificata. I risultati dei confronti sono in `VALIDAZIONE.md`.

## Strumenti di ingegneria

Nella scheda Ingegneria ci sono anche **Progetto orbita** (angolo β per un anno, traccia a terra che si ripete con J₂, orbita congelata con J₂ e J₃), **Sensori** (accecamento di star tracker e sensori d'orizzonte da Sole, Terra e Luna, con mappa del cielo in assi corpo) e, nella pagina ADCS, **saturazione delle ruote e scarico magnetico** su un giorno; nella pagina Termica i casi caldo e freddo dell'anno.


La scheda **Ingegneria** di ogni satellite, sonda o progetto raccoglie:

- **Propagatore**: integrazione numerica dell'orbita (Dormand–Prince 8(5,3)) con gravità in armoniche sferiche (EGM2008 fino a 120×120,
  GRGM900C per la Luna, GMM-2B per Marte, MGNP180U per Venere), terzi corpi, radiazione solare sulla forma vera, luce e calore del pianeta,
  resistenza NRLMSISE-00, relatività e maree solide; risultati in CSV e nei formati CCSDS OEM e OPM.
- **Manovre**: trasferimenti di Lambert verso un altro oggetto, finestre interplanetarie (C₃), mantenimento dell'orbita (resistenza,
  geostazionaria nord-sud ed est-ovest), fine vita (abbassamento del pericentro con la vita residua numerica, orbita cimitero IADC).
- **ADCS**: simulazione ad anello chiuso con quattro ruote di reazione, magnetotorquer, sensori con rumore e filtro MEKF; quaternioni in AEM.
- **Potenza**, **Termica**, **Collegamenti** (stazioni ESTRACK, DSN, NEN e italiane, bilancio di collegamento e Doppler) e, per i satelliti,
  **Congiunzioni** con il resto del catalogo.

I calcoli lunghi girano in un Web Worker, così la vista resta fluida anche sul telefono. Il motore è un blocco a sé nella pagina
(`<script id="motore">`): non tocca il DOM e si prova anche fuori dal browser. La pagina Evoluzione usa per la vita orbitale lo stesso
motore (metodo numerico a inviluppo); il vecchio metodo a elementi medi resta come opzione rapida.

## File CCSDS

Trascina un file sulla vista 3D (o caricalo dal pannello Dati):

- **OEM** (effemeride, KVN o XML): diventa un oggetto da guardare, con l'orbita disegnata dai suoi stati; terne EME2000, ICRF, GCRF, TEME, TOD, ITRF (per la Terra), tempi UTC, TAI, TT, TDB, GPS; interpolazione di Hermite o di Lagrange come indicato nel file. Se è un satellite del catalogo (stesso designatore, numero o nome), la pagina Fonte mostra la differenza con SGP4.
- **AEM** (assetto, versione 1 e 2, quaternioni o angoli di Eulero della versione 2): si applica all'oggetto scelto; pulsante «AEM» nella pagina Assetto.
- **OPM** (uno stato): diventa una missione del progettista.
- **OMM** (elementi medi, KVN, XML, JSON o CSV come li dà CelesTrak): sostituisce il catalogo, anche con numeri oltre 99 999.

Gli oggetti importati restano finché la pagina è aperta.

## Cosa c'è nella cartella

```
index.html              la pagina del sito (generata)
en/index.html           la stessa pagina in inglese, per i motori di ricerca (generata)
manifest.webmanifest    nome, icone e colori dell'app installata
sw.js                   tiene una copia del sito sul dispositivo per l'uso senza rete
data/                   satelliti, lanci, sonde, stelle, attività solare, campi di gravità, campo crostale di Marte, luoghi (citta.txt)
tex/                    texture di Terra, Luna, Sole e pianeti (Solar System Scope, CC BY 4.0); CREDITI.txt
modelli/                forme reali: modelli 3D dei veicoli (NASA 3D Resources), già in metri e negli assi dell'app; CREDITI.txt
vendor/                 three.js r128, satellite.js 5.0.0, Astronomy Engine 2.1.19
fonts/                  carattere B612
icone/                  marchio, icone dell'app e immagine di copertina (copertina.svg → anteprima.jpg)
LICENSE                 licenza MIT del codice dell'app
sorgente/               la pagina sorgente dell'app
assistente/             il servizio dell'assistente (worker.js) e le istruzioni per attivarlo
sitemap.xml             l'elenco delle pagine per i motori di ricerca (generato dalla conversione)
strumenti/              aggiornamento dei dati, conversione della pagina, prove
.github/workflows/      aggiornamento giornaliero e pubblicazione su GitHub Pages
LICENZE.txt             fonti, crediti e licenze di tutto ciò che il sito contiene (librerie, carattere, texture, modelli, dati)
```

## Licenze e crediti

Il sito è pronto da pubblicare sul piano legale: ogni componente ha la sua fonte e la sua licenza, annotate in questa cartella.

| Cosa | Licenza | Dove |
| --- | --- | --- |
| Codice dell'app (pagina, service worker, strumenti, icone e copertina, anelli di Saturno) | MIT, Copyright (c) 2026 Davide Ottoninuoto | `LICENSE` |
| three.js, satellite.js, Astronomy Engine | MIT | `LICENZE.txt` sezioni 2 e 11, intestazioni dentro `vendor/` |
| Carattere B612 | SIL Open Font License 1.1 | `fonts/OFL.txt`, `LICENZE.txt` sezioni 3 e 12 |
| Texture dei pianeti | CC BY 4.0, Solar System Scope (attribuzione obbligatoria) | `tex/CREDITI.txt`, `LICENZE.txt` sezioni 4 e 13 |
| Modelli 3D dei veicoli | NASA 3D Resources: di norma senza diritto d'autore negli USA; insegne NASA escluse | `modelli/CREDITI.txt`, `LICENZE.txt` sezione 5 |
| TLE e lanci, effemeridi, stelle, campo IGRF, campi di gravità | dati pubblici, con la fonte da citare | `LICENZE.txt` sezione 6 |
| Luoghi della pagina Passaggi (`data/citta.txt`) | GeoNames, CC BY 4.0 (attribuzione obbligatoria) | `LICENZE.txt` sezioni 6 e 13 |

La pagina cita le fonti nel pannello **Dati** e rimanda a `LICENZE.txt`; il flusso di pubblicazione copia `LICENSE` e
`LICENZE.txt` nel sito, perché le licenze devono accompagnare i file distribuiti. Se cambi il tuo nome come titolare o la licenza del
codice, correggi `LICENSE`, la sezione 1 e la sezione 10 di `LICENZE.txt` e la riga iniziale di `strumenti/costruisci_sito.py`.

Quando aggiungi qualcosa (un modello, una texture, una libreria, una nuova fonte dati): annota fonte, autore, licenza e modifiche
in `LICENZE.txt` e nel `CREDITI.txt` della cartella, **prima** di pubblicare. Non aggiungere materiale di cui non conosci la licenza.
Le texture si rigenerano o si sostituiscono solo con file la cui licenza permette la ridistribuzione; gli anelli di Saturno si
ricreano con `python3 strumenti/genera_anelli.py tex/ring.png`, il marchio, le icone e la copertina con
`python3 strumenti/grafica/disegna_marchio.py`, l'elenco dei luoghi con `python3 strumenti/citta/genera_citta.py`.

Il sito è uno strumento didattico: posizioni e orbite non vanno usate per operazioni di volo (avviso in `LICENZE.txt`, sezione 9).
Ricorda che con un account GitHub gratuito il repository di GitHub Pages è pubblico: il codice sarà visibile a tutti, con la licenza MIT.

## Scheda di presentazione (testo per i motori di ricerca)
In `sorgente/pagina-sorgente.html` il blocco `<section id="about">` contiene il testo che Google legge e che i nuovi visitatori vedono alla prima apertura (italiano e inglese, ciascuno tra i marcatori `<!--L:it-->…<!--/L-->` e `<!--L:en-->…<!--/L-->`). Per cambiarlo si modifica lì e si rigenera con `python3 strumenti/costruisci_sito.py sorgente/pagina-sorgente.html`: `index.html` tiene il blocco italiano, `en/index.html` quello inglese. I visitatori che tornano e i link a una scena (`#sat-…`, `#sonda-…`) non vedono la scheda; il pulsante **Info** la riapre. Da tastiera: frecce per ruotare la vista, + e − per lo zoom, spazio per la pausa.

