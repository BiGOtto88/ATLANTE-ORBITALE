# Assistente di Keplario: come attivarlo

L'assistente risponde a domande libere. Capisce la richiesta, sceglie da solo quali calcoli fare (stato di un'orbita, propagazione con J2, traccia a terra, passaggi sopra un luogo, ricerca di un satellite, disegni) e li fa con il motore dell'app, poi risponde. Il modello di intelligenza artificiale gira su un servizio esterno, quindi serve un piccolo intermediario che tiene nascosta la chiave. Finché non lo attivi, il pulsante «Assistente» non compare sul sito.

## Costi e sicurezza

- Ogni domanda usa l'API del modello scelto. Predefinito: **Google Gemini** (`gemini-3.5-flash-lite`, il più economico). In alternativa il modello di Anthropic (`claude-haiku-5-5`): basta cambiare la variabile `PROVIDER`. Nome del modello con la variabile `MODEL`: i nomi cambiano spesso, controllali su ai.google.dev/gemini-api/docs/models.
- **Gemini, piano gratuito:** esiste, con limiti di richieste al minuto e al giorno bassi, e Google può usare le domande per migliorare i propri prodotti. Con la fatturazione attivata (piano a pagamento) non le usa. Se vuoi più riservatezza, attiva la fatturazione e metti un limite di spesa.
- Prima di tutto, nella console del fornitore (Google AI Studio o Anthropic) imposta un **limite di spesa mensile**, o tieni bassi `DAILY_PER_IP` e `DAILY_TOTAL`.
- La chiave non sta mai nella pagina: sta solo nell'intermediario (segreto di Cloudflare).
- Il servizio risponde solo al sito indicato in `ALLOWED_ORIGIN`, accetta richieste piccole, e con l'archivio `LIMITS` limita le domande per persona (60 al giorno) e in totale (1500 al giorno). I numeri si cambiano con `DAILY_PER_IP` e `DAILY_TOTAL`.
- Le domande degli utenti passano da Cloudflare e da Anthropic. Il pannello lo dice agli utenti.

## Passi (circa 15 minuti, piano gratuito di Cloudflare)

1. Crea un account su cloudflare.com e una chiave API su Google AI Studio (aistudio.google.com → Get API key).
2. Cloudflare → **Workers & Pages** → **Create** → **Create Worker**, nome `keplario-assistente` → **Deploy**.
3. **Edit code**: cancella il testo, incolla tutto il contenuto di `assistente/worker.js`, **Deploy**.
4. **Settings → Variables and Secrets**, aggiungi:
   - `GEMINI_API_KEY` come **Secret**, con la chiave creata su aistudio.google.com (Get API key);
   - (solo se usi Claude al posto di Gemini) `ANTHROPIC_API_KEY` come **Secret**, e `PROVIDER` = `anthropic`;
   - `ALLOWED_ORIGIN` come testo: `https://ottonspace.github.io` (senza barra finale e senza `/keplario`; se il nome utente GitHub cambia, cambia anche questo).
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

Nell'artifact l'assistente non usa il servizio né Gemini: è la pagina stessa a chiamare il modello di chi guarda con gli stessi strumenti (capacità «sample» dell'artifact), sull'account di chi guarda, e chiede il consenso alla prima domanda. Il pulsante compare da solo, senza indirizzo.

## Provare il servizio senza rete

`node strumenti/prove/prova_worker.mjs .` simula le risposte di Gemini e di Anthropic e controlla che messaggi, strumenti e firme di ragionamento (richieste da Gemini 3) siano tradotti bene.

## Se modifichi gli strumenti

Le istruzioni e le definizioni degli strumenti stanno in `worker.js`. Dopo ogni modifica lancia `python3 strumenti/sincronizza_assistente.py` (le copia nella pagina) e poi riconverti la pagina con `costruisci_sito.py`.

## Velocità e consumo di token (novembre 2026)
Il servizio è stato alleggerito. Cosa fa ora, senza che tu debba cambiare niente nella pagina:
- **Ragionamento basso.** Con i modelli Gemini 3 il ragionamento è impostato su `low` (di solito era il tempo di attesa maggiore, e i token di ragionamento si pagano come quelli d'uscita). Per cambiarlo imposta la variabile `THINKING_LEVEL` (`minimal`, `low`, `medium`, `high`); con il valore `default` si lascia la scelta al modello.
- **Cronologia compatta.** Le chiamate e i risultati degli strumenti restano solo per la domanda in corso; delle domande precedenti si rimandano solo il testo tuo e quello delle risposte. I risultati degli strumenti sono tagliati a 3000 caratteri.
- **Istruzioni e strumenti più corti** (circa un quarto in meno) e contesto della pagina (orologio, oggetto scelto) in fondo alla domanda invece che nelle istruzioni: la parte fissa resta identica da una richiesta all'altra, e il fornitore può riusarla dalla cache (con Gemini la cache implicita sconta i token ripetuti).
- **Strumenti in parallelo.** L'assistente è istruito a chiamare insieme gli strumenti indipendenti, così servono meno giri.
- **Limiti.** Nel conto giornaliero (`DAILY_PER_IP`, `DAILY_TOTAL`) entra ora solo la domanda nuova, non i suoi passaggi di calcolo: prima una domanda con 5 passaggi ne consumava 5 e le scritture dell'archivio KV (1000 al giorno nel piano gratuito) finivano presto. I passaggi hanno un limite leggero di 60 al minuto per indirizzo.

Per applicare la nuova versione: Cloudflare → il tuo Worker → **Edit code** → incolla tutto `assistente/worker.js` → **Deploy**. Le variabili e i segreti restano quelli già impostati.

