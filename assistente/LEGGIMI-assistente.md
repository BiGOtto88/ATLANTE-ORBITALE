# Assistente di Keplario: come attivarlo

L'assistente risponde a domande libere. Capisce la richiesta, sceglie da solo quali calcoli fare (stato di un'orbita, propagazione con J2, traccia a terra, passaggi sopra un luogo, ricerca di un satellite, disegni) e li fa con il motore dell'app, poi risponde. Il modello di intelligenza artificiale gira su un servizio esterno, quindi serve un piccolo intermediario che tiene nascosta la chiave. Finché non lo attivi, il pulsante «Assistente» non compare sul sito.

## Costi e sicurezza

- Ogni domanda usa l'API di Anthropic e la paga chi possiede la chiave (tu). Il modello è scelto nel file `worker.js` (`claude-haiku-5-5`, il più economico).
- Prima di tutto, nella console di Anthropic imposta un **limite di spesa mensile** sulla chiave o sull'area di lavoro.
- La chiave non sta mai nella pagina: sta solo nell'intermediario (segreto di Cloudflare).
- Il servizio risponde solo al sito indicato in `ALLOWED_ORIGIN`, accetta richieste piccole, e con l'archivio `LIMITS` limita le domande per persona (60 al giorno) e in totale (1500 al giorno). I numeri si cambiano con `DAILY_PER_IP` e `DAILY_TOTAL`.
- Le domande degli utenti passano da Cloudflare e da Anthropic. Il pannello lo dice agli utenti.

## Passi (circa 15 minuti, piano gratuito di Cloudflare)

1. Crea un account su cloudflare.com e una chiave API sulla console di Anthropic (console.anthropic.com).
2. Cloudflare → **Workers & Pages** → **Create** → **Create Worker**, nome `keplario-assistente` → **Deploy**.
3. **Edit code**: cancella il testo, incolla tutto il contenuto di `assistente/worker.js`, **Deploy**.
4. **Settings → Variables and Secrets**, aggiungi:
   - `ANTHROPIC_API_KEY` come **Secret**, con la tua chiave;
   - `ALLOWED_ORIGIN` come testo: `https://bigotto88.github.io` (senza barra finale e senza `/keplario`; se il nome utente GitHub cambia, cambia anche questo).
5. Per i limiti: **Storage & Databases → KV** → crea un archivio, poi nel Worker **Settings → Bindings → Add → KV namespace**, nome della variabile `LIMITS`.
6. Copia l'indirizzo del Worker (finisce con `.workers.dev`).
7. Mettilo nel sito, in uno di questi due modi:
   - scrivilo nella riga `ASSISTENTE = ''` di `strumenti/costruisci_sito.py` e riconverti la pagina (comando in `LEGGIMI.md`);
   - oppure apri `index.html` e `en/index.html` su GitHub e metti l'indirizzo nel tag `<meta name="assistente" content="…">`.
8. Ricarica il sito due volte: compare il pulsante «Assistente». Fai una domanda di prova.

Per provare in locale senza `ALLOWED_ORIGIN` del sito, nel Worker aggiungi la variabile `ALLOW_LOCALHOST` = `1` e apri la pagina da `http://localhost:8000`.

## Cosa sa fare e cosa no

Strumenti (definiti in `worker.js`, eseguiti dalla pagina in `sorgente/pagina-sorgente.html`): `calc`, `kepler_to_state`, `propagate`, `repeat_ground_track`, `find_objects`, `object_status`, `passes`, `ground_track_map`, `show_in_3d`, `snapshot_3d`, `diagram`, più `fetch_tle`, `web_fetch`, `horizons_state` e `spacetrack_tle` (questi quattro solo sul sito vero). I numeri vengono da questi calcoli e non dalla memoria del modello. Se un'informazione non è raggiungibile (internet, dati in tempo reale), lo dice.

Prova automatica degli strumenti, senza modello e senza costi: `python3 strumenti/prove/prova_assistente.py .`

Se cambi un nome o un parametro di uno strumento, cambialo sia in `worker.js` sia nella pagina: la prova controlla che i nomi coincidano.

## Storico di oggetti rientrati (facoltativo)

`horizons_state` dà posizione e velocità esatte di un oggetto a un istante (JPL Horizons, senza account). Se il browser non riesce a raggiungere Horizons, la richiesta passa dal Worker.

`spacetrack_tle` cerca in Space-Track il TLE storico più vicino all'istante (funziona anche per oggetti già rientrati). Serve il tuo account gratuito di Space-Track, che resta solo nel Worker:

1. Nel Worker: Settings → Variables and Secrets → Add.
2. Tipo **Secret**, nome `SPACETRACK_USER`, valore l'e-mail dell'account.
3. Tipo **Secret**, nome `SPACETRACK_PASS`, valore la password.
4. Deploy. Le credenziali non compaiono nel sito, nella pagina né nel repository.

Senza questi due segreti `spacetrack_tle` risponde che Space-Track non è configurato e l'assistente passa a Horizons. Space-Track limita le richieste (circa 30 al minuto): il limite giornaliero del Worker le tiene ampiamente sotto.

## Nell'artifact di Claude

Nell'artifact l'assistente non usa il servizio: è la pagina stessa a chiamare Claude con gli stessi strumenti (capacità «sample» dell'artifact), sull'account di chi guarda, e chiede il consenso alla prima domanda. Il pulsante compare da solo, senza indirizzo.

## Se modifichi gli strumenti

Le istruzioni e le definizioni degli strumenti stanno in `worker.js`. Dopo ogni modifica lancia `python3 strumenti/sincronizza_assistente.py` (le copia nella pagina) e poi riconverti la pagina con `costruisci_sito.py`.
