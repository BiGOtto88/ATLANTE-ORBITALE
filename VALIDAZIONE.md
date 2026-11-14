# Atlante Orbitale: verifica dei modelli

Questo file raccoglie i confronti fatti fra i calcoli della pagina e strumenti indipendenti, con i numeri ottenuti. Gli script sono in `strumenti/validazione/`. I calcoli della pagina sono stati eseguiti nel browser (Chromium) sulla pagina stessa, con un aggancio di prova che espone le funzioni interne (`window.__dbg`); i dati d'ingresso dei confronti con Basilisk escono dalla pagina, così i due programmi lavorano sugli stessi numeri.

Verifica del 14 novembre 2026, sulla versione con atmosfera NRLMSISE-00, forme vere, evoluzione orbitale e passaggi.

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

Nella prima e nell'ultima riga la propagazione mediata parte dagli elementi medi ricavati dalla traiettoria diretta. Il decadimento per resistenza differisce del 4 % in orbita terrestre bassa e del 12 % su Marte: la media al primo ordine non vede le oscillazioni di corto periodo della quota, che con un'atmosfera esponenziale contano un poco. Le derive di nodo, apsidi, inclinazione ed eccentricità da gravità, terzi corpi e radiazione coincidono entro l'1 %.

Esempio: la ISS senza manovre (TLE del 14 novembre 2026, 420 km, 420 t, area media del modello 1 725 m², C<sub>D</sub> = 2,2) rientra dopo circa 3,9 anni, nel 2030, attraversando il minimo solare; con l'area lungo la traccia e i pannelli fissi (544 m²) la durata sale a più di 9 anni. Il valore reale dipende soprattutto dall'orientamento dei pannelli e dall'attività solare.

## 5. Passaggi visibili

Confronto con Skyfield 1.55 (`passaggi_skyfield.py`) per la ISS e per Hubble, da Roma (41,9° N, 12,5° E, 50 m), elevazione minima 10°, tre giorni dal 14 novembre 2026, stessi TLE. Tutti i 21 passaggi coincidono: inizio e fine entro 0,46 s, istante del massimo entro 0,15 s, elevazione massima entro 0,003°. La visibilità a occhio nudo (satellite illuminato con il Sole almeno 6° sotto l'orizzonte), calcolata da Skyfield con le effemeridi DE421 ogni 10 s, coincide in 21 casi su 21.

## 6. Limiti

- Gli elementi TLE e SGP4 hanno errori di qualche chilometro dopo pochi giorni dall'epoca; i passaggi si spostano di conseguenza.
- L'evoluzione orbitale non modella manovre, risonanze con la rotazione del corpo, armoniche tesserali, lune dei pianeti giganti come terzi corpi, variazioni d'assetto nel tempo.
- Le atmosfere di Venere, Marte e dei giganti sono profili medi senza dipendenza dall'ora e dal ciclo solare.
- La magnitudine dei passaggi è una stima da sfera diffusa, utile per confronti relativi.
- Atlante Orbitale è uno strumento didattico: non va usato per operazioni di volo.
