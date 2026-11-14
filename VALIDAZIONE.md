# Atlante Orbitale: verifica dei modelli

Questo file raccoglie i confronti fatti fra i calcoli della pagina e strumenti indipendenti, con i numeri ottenuti. Gli script sono in `strumenti/validazione/`. I calcoli della pagina sono stati eseguiti nel browser (Chromium) sulla pagina stessa, con un aggancio di prova che espone le funzioni interne (`window.__dbg`); i dati d'ingresso dei confronti con Basilisk escono dalla pagina, così i due programmi lavorano sugli stessi numeri.

Verifica del 14 novembre 2026, sulla versione con atmosfera NRLMSISE-00, forme vere, evoluzione orbitale e passaggi; aggiornata lo stesso giorno con gli strumenti di ingegneria (propagatore numerico, manovre, ADCS ad anello chiuso, potenza, termica, collegamenti, congiunzioni, messaggi CCSDS). Le prove del motore di calcolo si rifanno da sole a ogni modifica: `strumenti/prove/prova_motore.js` e il flusso GitHub «Verifica dei modelli» (`.github/workflows/verifica.yml`), che ricalcola anche il riferimento indipendente in Python.

## In breve

| Cosa | Riferimento | Scarto massimo |
|---|---|---|
| Orbita bassa per 1 giorno con J₂, J₃, J₄ | Basilisk 2.12, RK4 a 1 s | 0,14 m in posizione, 0,15 mm/s in velocità |
| Coppia da gradiente di gravità, inerzia piena | Basilisk `GravityGradientEffector` | 7·10⁻¹⁶ (relativo) |
| Forza e coppia di resistenza su facce piane | Basilisk `FacetDragDynamicEffector` | 2·10⁻¹⁵ |
| Forza e coppia di radiazione su facce piane | Basilisk `FacetSRPDynamicEffector` | 9·10⁻¹¹ |
| Densità NRLMSISE-00 (300 casi a caso) | pymsis 0.13 (versione 00) | 5,2·10⁻⁵ |
| Densità nella pagina, dalla posizione TEME | pymsis 0.13 | 4,0·10⁻⁵ |
| Accelerazione zonale J₂–J₄ | gradiente numerico del potenziale | 3·10⁻⁹ |
| Superfici esposte dei modelli 3D | tracciamento di raggi con Embree (trimesh) | forze < 1 %, centro di pressione entro 3 cm |
| Evoluzione mediata delle orbite | integrazione diretta (Cowell) con le stesse forze | vedi tabella sotto |
| Passaggi visibili da Roma | Skyfield 1.55 | 0,5 s sugli orari, 0,003° sull'elevazione, visibilità 21 su 21 |
| Gravità in armoniche sferiche (EGM2008 120×120, GRGM900C, GMM-2B, MGNP180U) | SHTOOLS 4.14 (pyshtools) | 7·10⁻¹⁵ (relativo) |
| Propagatore numerico, 5 orbite da 1 a 3 giorni, stessi dati d'ingresso | riferimento indipendente in Python (SHTOOLS, ERFA, DE421, SciPy DOP853) | da 0,7 mm a 1,0 m |
| Propagatore numerico con le effemeridi della pagina | stesso riferimento con DE421 ed ERFA | da 0,17 a 0,77 m |
| Vita orbitale con il metodo a inviluppo, 4 casi da 7 giorni a 3 anni | integrazione diretta (Cowell) giro per giro | da 0,03 % a 0,22 % sulla data di rientro |
| Problema di Lambert (Izzo), 1 722 casi casuali | propagazione a due corpi dell'arco trovato | 1,7 mm all'arrivo |
| Lambert, esempio 5.2 di Curtis | soluzione pubblicata | 5·10⁻⁵ km/s |
| Simulazione ADCS senza coppie esterne | conservazione del momento angolare | 8·10⁻¹⁵ (relativo) |
| Filtro MEKF, un'orbita con disturbi | coerenza statistica (errori entro 3σ) | 99,9 % (atteso 99,7 %) |
| Fattori di vista lastra–pianeta | formule analitiche | esatto al nadir, 0,19 % di lato |
| Messaggi OEM e OPM | lettura con la libreria `beyond` 0.9 | letti senza errori, stato identico |

Le verifiche precedenti (campi magnetici in armoniche sferiche contro un calcolo indipendente in Python, scarto ≤ 10⁻⁹; disco di corrente contro il pacchetto `con2020`, 10⁻¹⁴; tensore del gradiente di gravità con J₂ e terzi corpi contro le differenze finite, 10⁻¹⁰) restano valide.

## 1. Confronto con Basilisk

[Basilisk](https://hanspeterschaub.info/basilisk/) è il simulatore di dinamica spaziale dell'AVS Lab (University of Colorado), usato in missioni reali. Script: `basilisk_confronto.py` (Basilisk), `casi_pagina.js` (pagina), `confronta_basilisk.py` (confronto). Ingressi in `casi_basilisk.json`, uscite in `uscita_basilisk.json`, scarti in `risultati_basilisk.json`.

**Orbita.** Orbita circolare a 420 km inclinata di 51,6°, un giorno. Basilisk usa il suo modello in armoniche sferiche con i soli coefficienti zonali C̄₂₀, C̄₃₀, C̄₄₀ ricavati dagli stessi J₂, J₃, J₄ (EGM2008) e il suo integratore RK4 a 1 s; la pagina usa `zonalAcc` e `evoCowell` (RK4, 1 s). Dopo 24 ore le posizioni differiscono di 0,14 m: l'accelerazione e l'integrazione coincidono.

**Gradiente di gravità.** Tre posizioni (orbita bassa sull'asse x, orbita bassa generica, geostazionaria) e tre assetti generici, inerzia con termini fuori diagonale. Le coppie coincidono alla precisione di macchina. Nella pagina il tensore Γ comprende anche J₂ e le maree di Sole e Luna; qui il confronto è fatto con la sola massa puntiforme, come in Basilisk.

**Facce piane.** Il veicolo schematico della pagina (classe «Minisatellite»: parallelepipedo e due ali, 10 facce con i loro centri rispetto al baricentro) in tre assetti, con tre direzioni del moto e del Sole. Resistenza: forza e coppia coincidono alla precisione di macchina. Radiazione: coincidono a 10⁻¹⁰, dopo aver diviso per la pressione solare di ciascun programma (Basilisk usa 1 368 W/m² a 1 AU, la pagina 1 361 W/m²: la differenza dello 0,5 % è solo nella costante).

## 2. Atmosfera terrestre NRLMSISE-00

La pagina contiene una traduzione in JavaScript della versione in C di NRLMSISE-00 di D. Brodowski. Confronto con `pymsis` 0.13 (codice Fortran ufficiale, versione 00, Ap giornaliero): 300 casi a caso fra 0 e 1 000 km, tutte le latitudini, longitudini, ore e stagioni, F10.7 fra 65 e 300 e Ap fra 0 e 200. Scarto massimo sulla densità totale 5,2·10⁻⁵, nessun valore non numerico (`msis_pymsis.py`). Il caso di prova della distribuzione C (giorno 172, 29 000 s, 400 km, 60° N, 70° O) dà le densità e le temperature pubblicate cifra per cifra.

Nella pagina la densità parte dalla posizione in TEME: latitudine, longitudine e quota geodetiche WGS-84, ora solare locale, indici del giorno dal file `data/meteo_spaziale.json`. Su 60 punti a caso fra il 2000 e il 2026 lo scarto rispetto a pymsis con gli stessi indici è 4,0·10⁻⁵.

Indici: F10.7 del giorno precedente, media di 81 giorni centrata e Ap giornaliero dai file CelesTrak (misure NRCan e GFZ, previsioni NOAA/SWPC). Oltre le previsioni mensili si usa un ciclo solare medio di 11 anni con F10.7 fra 70 e 190. Questa è la fonte d'errore più grande per la vita orbitale: fra minimo e massimo del ciclo la densità a 400 km cambia di un fattore 5–10.

## 3. Superfici esposte e autoschermatura

Per ogni modello 3D lo script `strumenti/modelli/superfici.mjs` rasterizza la forma lungo 25 × 48 direzioni con un buffer di profondità (768 × 768 punti per direzione, un punto a caso dentro ogni pixel per non avere errori sistematici sui bordi allineati alla griglia). Controlli:

- un cubo di 2 m con una piastra di 1 m² davanti a una faccia: area proiettata 4,002 m² contro 4 m² esatti, ombra della piastra corretta;
- ISS, Hubble e GOES contro il tracciamento di raggi indipendente con Embree (`raggi_superfici.py`, 640 000 raggi per direzione) in cinque direzioni fuori griglia: area proiettata entro lo 0,8 %, forza di radiazione entro l'1 %; coppie entro il 3 % per Hubble e GOES; per la ISS, quasi simmetrica, la coppia è un piccolo residuo di bracci grandi e lo scarto va letto come spostamento del centro di pressione: al più 3 cm su 109 m (lo stesso tracciamento di raggi, ripetuto con più raggi, oscilla di quasi altrettanto).

Limite noto: pannelli e antenne restano nella posizione del file NASA. I pannelli veri inseguono il Sole; per questo l'evoluzione orbitale propone come area di resistenza la media su tutte le direzioni.

## 4. Evoluzione orbitale mediata contro integrazione diretta

L'evoluzione a lungo termine integra gli elementi equinoziali medi con le equazioni di Gauss mediate su un giro (quadratura numerica con la perturbazione completa in ogni punto). Il controllo è l'integrazione diretta delle equazioni del moto (Cowell, RK4) con esattamente le stesse accelerazioni; dalla traiettoria diretta si ricavano gli elementi medi con una media mobile di un periodo (`evoluzione_cowell.py`).

| Caso | Durata | Grandezza | Diretta | Mediata |
|---|---|---|---|---|
| Orbita bassa 420 km, 51,6°, drag MSIS (C<sub>D</sub>A/m = 0,033 m²/kg) | 30 giorni | Δa | −8,62 km | −8,26 km |
| | | e finale | 0,00160 | 0,00158 |
| | | ΔΩ | −148,34° | −148,12° |
| Molniya, e = 0,72, 63,4°, Sole e Luna | 60 giorni | Δe | +0,00350 | +0,00348 |
| | | Δi | +0,0327° | +0,0326° |
| | | ΔΩ | −7,86° | −7,91° |
| Luna, 100 km polare, Terra e Sole | 60 giorni | Δe | +0,00041 | +0,00039 |
| | | Δi | +0,0902° | +0,0898° |
| | | Δω | −39,68° | −39,68° |
| Geostazionaria con pressione di radiazione alta | 180 giorni | Δe | +0,00679 | +0,00679 |
| | | Δi | +0,4224° | +0,4228° |
| Marte 300 km polare, drag | 30 giorni | Δa | −0,56 km | −0,62 km |
| | | ΔΩ | +17,47° | +17,68° |
| Giove, a = 5 milioni di km, e = 0,1, 20°: Sole e satelliti galileiani come anelli | 300 giorni | Δe | −0,00111 | −0,00113 |
| | | Δi | +0,0277° | +0,0277° |
| | | ΔΩ | −0,260° | −0,261° |
| Giove, a = 200 000 km, dentro l'orbita di Io: J₂, satelliti fermi nel giro | 20 giorni | ΔΩ | −29,13° | −28,90° |
| | | Δω | +46,24° | +45,89° |

Nella prima e nell'ultima riga la propagazione mediata parte dagli elementi medi ricavati dalla traiettoria diretta. Il decadimento per resistenza differisce del 4 % in orbita terrestre bassa e del 12 % su Marte: la media al primo ordine non vede le oscillazioni di corto periodo della quota, che con un'atmosfera esponenziale contano un poco. Le derive di nodo, apsidi, inclinazione ed eccentricità da gravità, terzi corpi e radiazione coincidono entro l'1 %. Attorno a Giove i satelliti galileiani più veloci del veicolo sono sostituiti dal loro anello di massa mediato sull'orbita (doppia media), quelli più lenti restano fermi durante il giro come il Sole; l'integrazione diretta li tiene sempre nella posizione vera. La doppia media non vale vicino alle risonanze con i satelliti (periodi in rapporto semplice).

Esempio: la ISS senza manovre (TLE del 14 novembre 2026, 420 km, 420 t, area media del modello 1 725 m², C<sub>D</sub> = 2,2) rientra dopo circa 3,9 anni, nel 2030, attraversando il minimo solare (metodo numerico della sezione 7: 3,83 anni, 12 settembre 2030; metodo rapido: 3,91 anni); con l'area lungo la traccia e i pannelli fissi (544 m²) la durata sale a più di 9 anni. Il valore reale dipende soprattutto dall'orientamento dei pannelli e dall'attività solare.

## 5. Passaggi visibili

Confronto con Skyfield 1.55 (`passaggi_skyfield.py`) per la ISS e per Hubble, da Roma (41,9° N, 12,5° E, 50 m), elevazione minima 10°, tre giorni dal 14 novembre 2026, stessi TLE. Tutti i 21 passaggi coincidono: inizio e fine entro 0,46 s, istante del massimo entro 0,15 s, elevazione massima entro 0,003°. La visibilità a occhio nudo (satellite illuminato con il Sole almeno 6° sotto l'orizzonte), calcolata da Skyfield con le effemeridi DE421 ogni 10 s, coincide in 21 casi su 21.


## 6. Propagatore numerico

Il propagatore della scheda Ingegneria integra le equazioni del moto di Cowell in assi J2000 con Dormand–Prince 8(5,3) (coefficienti come in SciPy) e uscite per interpolazione di Hermite di quinto grado. Il motore di calcolo è un blocco di codice separato (`<script id="motore">`) che gira in un Web Worker o, se il browser non lo permette, sulla pagina a piccoli passi.

**Gravità.** Coefficienti completamente normalizzati: EGM2008 (NGA) fino a 120, GRGM900C (GRAIL) fino a 100, GMM-2B (Marte) fino a 80, MGNP180U (Venere) fino a 70, nei file `data/gravita_*.json` (`strumenti/gravita/converti_campi.py`). Ricorrenza di Legendre per colonne su P̄/cos φ, senza singolarità ai poli. Confronto con `MakeGravGridPoint` di SHTOOLS su 40 punti a caso dei quattro corpi e gradi fra 8 e 120: scarto massimo 7·10⁻¹⁵ relativo. Vicino ai poli (oltre 89,99°) è SHTOOLS a perdere cifre (divisione per sin θ); la pagina resta continua fino al polo.

**Orbite.** Il riferimento è scritto da capo con librerie diverse (`rif_propagatore.py`): gravità con SHTOOLS, rotazione terrestre IAU 2006/2000A con ERFA (`c2t06a`), effemeridi JPL DE421 con `jplephem`, densità con `pymsis`, integratore DOP853 di SciPy con tolleranza 10⁻¹³; relatività, maree solide (IERS 2010, eq. 6.6) e ombra conica riscritte dalle formule pubblicate. Casi in `strumenti/validazione/propagatore/casi.json`, partenza 14 novembre 2026:

| Caso | Durata | Stessi dati d'ingresso | Effemeridi e rotazione della pagina |
|---|---|---|---|
| Orbita bassa 400 km, 51,6°, EGM2008 70×70, Sole, Luna, relatività, maree | 1 giorno | 0,06 m | 0,17 m |
| Orbita bassa 400 km, EGM2008 120×120, Sole, Luna, Venere, Marte, Giove, Saturno | 1 giorno | 0,34 m | 0,77 m |
| Orbita bassa 300 km eliosincrona, 20×20, resistenza NRLMSISE-00 e radiazione con ombra | 1 giorno | 1,0 m | 0,29 m |
| GPS, 26 560 km, 12×12, Sole, Luna, Giove, radiazione | 2 giorni | 0,20 m | 0,76 m |
| Geostazionaria, 8×8, Sole, Luna, radiazione | 3 giorni | 0,7 mm | 0,67 m |

«Stessi dati d'ingresso»: il motore della pagina riceve le effemeridi DE421 e la rotazione ERFA campionate dal riferimento, così resta solo la differenza di implementazione. Nel caso con resistenza il metro di scarto viene dalla differenza fra la traduzione in JavaScript di NRLMSISE-00 e pymsis (5·10⁻⁵ sulla densità, su un decadimento di circa 150 km lungo la traccia in un giorno). Con le effemeridi e la rotazione della pagina (Astronomy Engine) lo scarto resta sotto il metro dopo uno–tre giorni.

**Stato iniziale dei satelliti.** SGP4 dà la posizione in TEME; la pagina la porta al vero equatore della data con l'equazione degli equinozi (tempo siderale apparente meno quello medio) e poi a J2000 con precessione e nutazione. L'incertezza del TLE (da centinaia di metri a qualche chilometro) resta: per la ISS il propagatore numerico e SGP4 si allontanano di circa 5 km in 6 ore, che è la differenza fra i due modelli, non un errore del calcolo.

## 7. Vita orbitale con il metodo a inviluppo

Nella pagina Evoluzione il metodo numerico (predefinito) segue l'orbita un giro alla volta con il modello completo e salta molti giri insieme sulla sequenza dei passaggi al nodo ascendente (envelope following, Petzold 1981). La pendenza della sequenza è la differenza centrale fra un giro in avanti e uno all'indietro, presi a un quarto di giorno di distanza perché gli effetti legati alla rotazione terrestre (termini in longitudine dell'atmosfera) si compensino; negli ultimi 40 km i giri sono seguiti uno per uno fino alla caduta a 120 km.

Confronto con l'integrazione diretta di tutti i giri, stesso modello (EGM2008 zonale fino al grado 8, Sole, Luna, radiazione, NRLMSISE-00 con gli indici di `data/meteo_spaziale.json`), orbite circolari a 51,6° dal 14 novembre 2026 (`strumenti/validazione/propagatore/inviluppo_vs_cowell.json`):

| Quota iniziale | C<sub>D</sub>A/m | Cowell | Inviluppo | Scarto | Tempo (Cowell → inviluppo) |
|---|---|---|---|---|---|
| 260 km | 0,022 m²/kg | 7,07 giorni | 7,08 giorni | +0,16 % | 4,5 s → 0,7 s |
| 330 km | 0,022 m²/kg | 44,43 giorni | 44,46 giorni | +0,06 % | 25 s → 2,3 s |
| 400 km | 0,040 m²/kg | 117,64 giorni | 117,68 giorni | +0,03 % | 59 s → 4,9 s |
| 415 km (come la ISS) | 0,0084 m²/kg | 1 125,9 giorni | 1 128,4 giorni | +0,22 % | 541 s → 43 s |

Il metodo a elementi medi della sezione 4 resta disponibile come «rapido»: sbaglia il decadimento del 4–12 % perché non vede le oscillazioni di corto periodo della quota. Due errori trovati e corretti durante questa verifica: la differenza in avanti (un giro solo) dava la pendenza mezzo giro più tardi, con l'1,7 % di rientro anticipato; con la stessa fase della rotazione terrestre a ogni passo l'atmosfera veniva campionata sempre alla stessa longitudine (aliasing). Le prove sono in `strumenti/prove/prova_motore.js`.

## 8. Manovre

**Lambert.** Algoritmo di Izzo (2015), zero o più giri, rami destro e sinistro. Su 1 722 casi casuali (0 e 1 giro, prograde e retrograde) l'arco trovato, propagato con le variabili universali, arriva entro 1,7 mm dal punto richiesto. Esempio 5.2 di Curtis (r₁ = 5 000, 10 000, 2 100 km; r₂ = −14 600, 2 500, 7 000 km; 1 ora): v₁ entro 5·10⁻⁵ km/s dal valore pubblicato. La propagazione a variabili universali usa l'iterazione di Laguerre–Conway: con Newton, per orbite quasi radiali (pericentro di 90 km e semiasse di 12 000 km) non convergeva.

**Finestre interplanetarie.** C₃ da Lambert eliocentrico fra le posizioni vere dei pianeti (Astronomy Engine). Per Marte il minimo della griglia di questa verifica cade alla fine di novembre 2028 con C₃ = 9,0 km²/s², durata 312 giorni, iniezione da 300 km di 3,61 km/s.

**Mantenimento.** In orbita geostazionaria la deriva dell'inclinazione viene dalla pendenza media su un anno di propagazione numerica: per GOES-16 0,92°/anno, dentro l'intervallo noto 0,75–0,95°/anno (massimo quando il nodo dell'orbita lunare è vicino all'equinozio di primavera, come nel 2024–2026). Su 30 giorni la stima saliva a 1,2°/anno per il termine semestrale del Sole: per questo si usa l'anno intero. Lo scarico della resistenza in orbita bassa è l'integrale della decelerazione su un giro con NRLMSISE-00.

## 9. Simulazione ADCS ad anello chiuso

Corpo rigido con quattro ruote a piramide (54,74°), magnetotorquer, giroscopio con rumore d'angolo e di velocità, sensore stellare, magnetometro e filtro MEKF (Lefferts, Markley e Shuster 1982; Markley e Crassidis 2014). Prove su un'orbita bassa sintetica con gravità, campo dipolare e radiazione:

- senza coppie esterne, con una manovra di 3°: il momento angolare totale nello spazio (corpo più ruote) resta costante a 8·10⁻¹⁵;
- con i disturbi, sensore stellare da 10″ a 1 Hz e giroscopio σ<sub>v</sub> = 3,2·10⁻⁷ rad/√s, σ<sub>u</sub> = 3,2·10⁻¹⁰ rad/s^1,5 (i valori dell'esempio di Markley e Crassidis): errore di stima 1,3″, deviazione standard del filtro 0,9″ per asse, 99,9 % degli errori entro 3σ; puntamento vero 1,8″ RMS nella seconda metà dell'orbita;
- un errore di segno nella legge di scarico (m = k (B × h) invece di m = k (h × B)/|B|²) faceva crescere il momento delle ruote invece di scaricarlo: corretto, ora il momento resta vicino a zero.

## 10. Potenza, termica, collegamenti

**Termica.** I flussi di albedo e infrarosso si integrano sull'angolo solido del disco del pianeta visto dalla faccia (F = (1/π)∫cos θ dΩ), con ogni raggio portato fino alla superficie per l'altezza del Sole e la temperatura locale. Fattore di vista di una lastra rivolta al nadir: uguale a (R/r)² alla precisione di macchina; lastra perpendicolare al nadir: scarto 0,19 % dalla formula analitica, da 1,05 a 4 raggi. Una prima versione, che integrava sulla calotta del pianeta, sbagliava del 2–3 % in orbita bassa.

**Collegamenti.** Il bilancio coincide con il calcolo a mano: a 1 000 km in banda X (8,45 GHz) perdita nello spazio libero 170,98 dB, antenna di 11 m con efficienza 0,6 57,55 dBi, C/N₀ 106,36 dB·Hz con 10 W e 6 dBi a bordo. Le stazioni ESTRACK, DSN, NEN e italiane hanno coordinate arrotondate a circa 100 m.

**Potenza.** Ombra e penombra coniche come nella pagina Disturbi, distanza vera dal Sole; dimensionamento con il metodo di SMAD (P<sub>sa</sub> = (P<sub>e</sub>T<sub>e</sub>/X<sub>e</sub> + P<sub>d</sub>T<sub>d</sub>/X<sub>d</sub>)/T<sub>d</sub>).

## 11. Congiunzioni e formati

**Congiunzioni.** SGP4 per tutti gli oggetti con la fascia di quote compatibile, distanza ogni 20 s, minimo esatto con la sezione aurea. Per la ISS: 1 039 oggetti esaminati in 6,5 s (6,2 milioni di posizioni). I moduli della ISS (catalogati come oggetti separati, sempre a distanza zero) sono riconosciuti ed esclusi. Non si calcola una probabilità di collisione: i TLE non hanno covarianza.

**CCSDS.** OEM 2.0 (efemeridi), OPM 2.0 (stato e parametri del veicolo) e AEM 1.0 (quaternioni della simulazione ADCS), in KVN, assi EME2000. OEM e OPM esportati dalla pagina sono letti dalla libreria indipendente `beyond` 0.9 senza errori e con lo stesso stato.

## 12. Computer e smartphone

Tutti i calcoli lunghi (propagazione, vita orbitale, simulazione ADCS, congiunzioni) girano in un Web Worker: in Chrome con lo schermo di un iPhone 13 emulato (390 × 844, tocco) il codice della pagina occupa il 4 % del tempo anche durante un calcolo; il resto è il disegno della scena. Sui dispositivi lenti la risoluzione scende a passi (supersampling spento, poi fino a 0,6 della densità dello schermo) finché un fotogramma non dura meno di 30 ms. Safari e iPhone veri non si possono provare in questo ambiente: WebKit non era scaricabile.

## 13. Limiti

- Gli elementi TLE e SGP4 hanno errori di qualche chilometro dopo pochi giorni dall'epoca; i passaggi si spostano di conseguenza.
- L'evoluzione orbitale non modella manovre, le lune di Saturno, Urano e Nettuno, variazioni d'assetto nel tempo; il metodo rapido a elementi medi non vede nemmeno risonanze e armoniche tesserali.
- Il propagatore trascura UT1 − UTC e il moto del polo (alcuni metri sulla rotazione terrestre), le maree oceaniche, la pressione di radiazione terrestre come sorgente estesa e le accelerazioni da manovre non pianificate. La Luna usa l'orientamento IAU con coefficienti GRGM900C riferiti agli assi principali (0,02° di differenza).
- La simulazione ADCS non modella vibrazioni, flessibilità, ritardi di calcolo e quantizzazione dei sensori; le ruote sono ideali entro i limiti di coppia e momento.
- Il modello termico ha un nodo per faccia e uno interno: serve per un primo dimensionamento, non sostituisce un modello termico dettagliato.
- Le atmosfere di Venere, Marte e dei giganti sono profili medi senza dipendenza dall'ora e dal ciclo solare.
- La magnitudine dei passaggi è una stima da sfera diffusa, utile per confronti relativi.
- Atlante Orbitale è uno strumento didattico: non va usato per operazioni di volo.

## 14. Elementi orbitali della pagina Orbita (14 nov 2026)

Prova: `strumenti/prove/prova_elementi.py` (pagina vera in Chromium, istante fisso, confronto con python-sgp4 2.27).

| Satellite | Orbita | Osculanti: scarto massimo | Medi SGP4: scarto massimo |
|---|---|---|---|
| ISS (25544) | bassa | a 0,05 km, angoli 1·10⁻⁴° | a 0,005 km, angoli 2·10⁻⁴° |
| GOES 16 (41866) | geostazionaria, risonanza a 1 giorno | a 0,02 km | a 0,04 km, angoli 2·10⁻⁴° |
| POLAR (23802) | molto ellittica, spazio profondo | a 0,015 km | a 0,007 km, e 5·10⁻⁷ |
| MERIDIAN 7 (40296) | Molniya, risonanza a 12 ore | a 0,02 km | a 0,05 km, angoli 5·10⁻⁴° |
| YAOGAN-29 (41038) | eliosincrona quasi circolare | a 0,002 km | a 0,04 km |

Gli scarti sono quelli dell'arrotondamento a video. Errori trovati e corretti:

- **Elementi medi fermi all'epoca del TLE.** Prima si mostravano Ω, ω, M, a ed e del TLE senza portarli all'istante simulato: con un TLE di un giorno e mezzo il nodo della ISS era sbagliato di 13,8°, l'argomento del pericentro di 10°, l'anomalia di 47°; per POLAR le quote di 22 km. Ora sono gli elementi medi di SGP4 all'istante simulato (`sgp4Mean`: parte secolare e resistenza di SGP4, termini secolari e risonanze dello spazio profondo, come in satellite.js).
- **Punti di Lagrange.** La velocità era calcolata per differenze finite con tempi arrotondati al millisecondo: gli elementi oscillavano di decine di migliaia di km fra un fotogramma e l'altro e il propagatore numerico partiva con un errore di velocità fino a 1,5 m/s. Ora posizione e velocità sono analitiche, sulla retta Sole–baricentro Terra-Luna. Anche lo stato usato da assetto e disturbi delle sonde usa la velocità analitica del modello, non più le differenze finite.
- **Stato → elementi nel progetto di missione.** Con orbite equatoriali o circolari nodo e pericentro non sono definiti e venivano posti a 0, perdendo la posizione lungo l'orbita. Ora l'angolo va nell'argomento di latitudine o nella longitudine vera: andata e ritorno stato → elementi → stato con scarto relativo massimo 1,4·10⁻¹⁰ su 2 000 stati a caso.
- **Angoli a 360°.** Un angolo di 359,9999° appariva come 360,000; ora è 0,000.
- **Missione dall'orbita di un satellite.** Prima usava gli elementi osculanti, con un periodo sbagliato fino a qualche decimo di minuto per le orbite basse; ora usa gli elementi medi SGP4 dell'istante simulato, coerenti con il modello del progetto (kepleriano con J2 secolare).

Pagina Stato (quota geodetica, latitudine, longitudine, velocità, raggio, angolo di volo): uguale a un calcolo indipendente (python-sgp4, GMST IAU 1982, WGS84) a tutte le cifre mostrate per gli stessi quattro tipi di orbita.

## 15. Simulazione animata del percorso (14 nov 2026)

- **Finestre di lancio** (Strumenti): il viaggio della casella scelta (all'inizio il minimo di C₃; tocca un'altra casella per cambiarlo) visto dal polo nord dell'eclittica. Pianeti sulle orbite vere delle effemeridi, sonda sull'arco di Lambert propagato con il problema dei due corpi (stesse posizione e velocità iniziali dei numeri mostrati: l'arco parte dal pianeta di partenza e arriva su quello di arrivo).
- **Percorso** (satelliti, sonde e missioni): ogni tratto (parcheggio, trasferimento, orbita finale) è una conica percorsa con la legge oraria di Keplero, con le stesse ipotesi dei numeri della pagina (manovre impulsive; per la Luna Hohmann fino alla sua distanza; per i pianeti orbite circolari e complanari e partenza alla prossima finestra). Per i satelliti il percorso parte dall'orbita media SGP4.
- Etichette delle date nella mappa delle finestre: giorno e mese se le partenze coprono fino a 200 giorni, mese e anno intero altrimenti (prima «nov 26» voleva dire novembre 2026 ma si leggeva come 26 novembre).
