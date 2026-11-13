#!/usr/bin/env python3
"""Aggiorna il catalogo dei satelliti terrestri: data/active.txt, data/meta.json e data/lanci.json.

Scarica gli elementi TLE dei satelliti attivi da CelesTrak; se CelesTrak non risponde
ripiega su una copia pubblica ospitata su GitHub. Il file nuovo sostituisce quello
vecchio solo se supera i controlli (formato, cifre di controllo, numero di oggetti).

Uso:   python3 strumenti/aggiorna_tle.py            (dalla cartella del sito)
       python3 strumenti/aggiorna_tle.py --in-linea https://utente.github.io/atlante
Con --in-linea si parte dai dati del sito già pubblicato, se sono più recenti di quelli nella cartella:
così, quando le fonti non rispondono, resta in linea l'ultimo catalogo buono e non uno più vecchio.
Serve solo Python 3, senza librerie aggiuntive.
Esce con 0 se i dati sono aggiornati o già uguali, con 1 se nessuna fonte ha dato dati validi.

data/lanci.json riporta data e sito reali di ogni lancio (catalogo SATCAT di CelesTrak) per i satelliti
presenti in active.txt; se il SATCAT non si scarica, il file resta com'è.
"""
import argparse, csv, datetime, io, json, pathlib, re, sys, time, urllib.request

RADICE = pathlib.Path(__file__).resolve().parent.parent
AGENTE = 'atlante-orbitale/1.0 (aggiornamento giornaliero del catalogo)'
FONTI = [
    ('CelesTrak', 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'),
    ('CelesTrak (copia caelo-works/tle-mirror)', 'https://raw.githubusercontent.com/caelo-works/tle-mirror/main/tle/active.tle'),
]
MINIMO = 8000            # sotto questo numero di satelliti il file è di sicuro incompleto
FONTI_SATCAT = [
    ('CelesTrak', 'https://celestrak.org/pub/satcat.csv'),
    ('CelesTrak (copia caelo-works/tle-mirror)', 'https://raw.githubusercontent.com/caelo-works/tle-mirror/main/tle/satcat.csv'),
]


def scarica(url, tentativi=3):
    ultimo = None
    for n in range(tentativi):
        try:
            rich = urllib.request.Request(url, headers={'User-Agent': AGENTE, 'Accept': 'text/plain,*/*'})
            with urllib.request.urlopen(rich, timeout=90) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:                      # rete, 403, 5xx: si riprova con calma
            ultimo = e
            time.sleep(5 * (n + 1))
    raise ultimo


def cifra_ok(riga):
    """Cifra di controllo di una riga TLE: somma delle cifre, i segni meno valgono 1, modulo 10."""
    if len(riga) < 69 or not riga[68].isdigit():
        return False
    s = sum(int(c) if c.isdigit() else (1 if c == '-' else 0) for c in riga[:68])
    return s % 10 == int(riga[68])


def controlla(testo):
    """Restituisce (testo ripulito, numero di satelliti). Tiene solo le terne nome + riga 1 + riga 2 valide."""
    righe = [r.rstrip() for r in testo.replace('\r', '').split('\n')]
    fuori, n, scartati, i = [], 0, 0, 0
    while i < len(righe) - 1:
        a, b = righe[i], righe[i + 1]
        if a.startswith('1 ') and b.startswith('2 ') and len(a) >= 69 and len(b) >= 69:
            nome = righe[i - 1].strip() if i > 0 and righe[i - 1] and not righe[i - 1].startswith(('1 ', '2 ')) else ''
            if cifra_ok(a) and cifra_ok(b) and a[2:7] == b[2:7]:
                fuori += [nome or ('NORAD ' + a[2:7].strip()), a[:69], b[:69]]
                n += 1
            else:
                scartati += 1
            i += 2
        else:
            i += 1
    return '\n'.join(fuori) + '\n', n, scartati


def leggi_meta(f_meta):
    try:
        return json.loads(f_meta.read_text(encoding='utf-8'))
    except Exception:
        return {}


def riprendi(base, f_tle, f_meta):
    """Se il sito in linea ha un catalogo valido e più recente di quello locale, lo copia nella cartella."""
    try:
        meta = json.loads(scarica(base.rstrip('/') + '/data/meta.json', 1))
        if not str(meta.get('updated', '')) > str(leggi_meta(f_meta).get('updated', '')):
            return
        testo, n, scartati = controlla(scarica(base.rstrip('/') + '/data/active.txt', 1))
        if n < MINIMO or scartati > 0.02 * n:
            return
        f_tle.write_text(testo, encoding='utf-8')
        f_meta.write_text(json.dumps({'updated': meta['updated'], 'count': n, 'source': str(meta.get('source', ''))}, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'Ripreso dal sito in linea il catalogo del {meta["updated"]} ({n} satelliti)')
    except Exception as e:
        print(f'Sito in linea: nessun catalogo da riprendere ({e})')


def sigle_lanci(testo_tle):
    """Sigle dei lanci (anno-numero, per esempio 1998-067) dei satelliti di un file TLE."""
    lanci = set()
    for riga in testo_tle.split('\n'):
        m = re.match(r'^1 .{7}(\d\d)(\d{3})[A-Z]', riga)
        if m:
            anno = int(m.group(1))
            lanci.add('%d-%s' % ((2000 if anno < 57 else 1900) + anno, m.group(2)))
    return lanci


def aggiorna_lanci(dati):
    """Scrive data/lanci.json: sigla del lancio -> [data, sigla del sito], dal catalogo SATCAT."""
    f_tle, f_lanci = dati / 'active.txt', dati / 'lanci.json'
    if not f_tle.exists():
        return
    servono = sigle_lanci(f_tle.read_text(encoding='utf-8'))
    for nome, url in FONTI_SATCAT:
        try:
            righe = list(csv.DictReader(io.StringIO(scarica(url, 2))))
            lanci = {}
            for r in righe:
                sigla = (r.get('OBJECT_ID') or '')[:8]
                if sigla in servono and sigla not in lanci and re.match(r'^\d{4}-\d\d-\d\d$', r.get('LAUNCH_DATE') or ''):
                    lanci[sigla] = [r['LAUNCH_DATE'], (r.get('LAUNCH_SITE') or '').strip()]
        except Exception as e:
            print(f'Lanci, {nome}: non raggiungibile ({e})')
            continue
        if len(lanci) < 0.9 * len(servono):
            print(f'Lanci, {nome}: trovati solo {len(lanci)} lanci su {len(servono)}, scarto il file')
            continue
        lanci = dict(sorted(lanci.items()))
        try:
            if json.loads(f_lanci.read_text(encoding='utf-8')).get('l') == lanci:
                print(f'Lanci, {nome}: {len(lanci)} lanci, nessuna novità')
                return
        except Exception:
            pass
        adesso = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        f_lanci.write_text(json.dumps({'updated': adesso, 'source': 'SATCAT, ' + nome, 'l': lanci}, separators=(',', ':')) + '\n', encoding='utf-8')
        print(f'Lanci, {nome}: scritti data e sito di {len(lanci)} lanci')
        return
    print('Lanci: nessuna fonte disponibile, data/lanci.json resta com\'è.')


def main():
    esito = catalogo()
    try:
        ap = argparse.ArgumentParser(add_help=False)
        ap.add_argument('--cartella', default=str(RADICE / 'data'))
        aggiorna_lanci(pathlib.Path(ap.parse_known_args()[0].cartella))
    except Exception as e:                           # i dati di lancio non devono mai fermare l'aggiornamento dei TLE
        print(f'Lanci: non aggiornati ({e})')
    return esito


def catalogo():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--cartella', default=str(RADICE / 'data'), help='cartella dei dati (predefinita: data/ del sito)')
    ap.add_argument('--in-linea', default='', metavar='INDIRIZZO', help='indirizzo del sito già pubblicato, da cui riprendere i dati se più recenti')
    arg = ap.parse_args()
    dati = pathlib.Path(arg.cartella)
    dati.mkdir(parents=True, exist_ok=True)
    f_tle, f_meta = dati / 'active.txt', dati / 'meta.json'
    if arg.in_linea:
        riprendi(arg.in_linea, f_tle, f_meta)
    prima = leggi_meta(f_meta)
    soglia = max(MINIMO, int(0.6 * (prima.get('count') or 0)))

    for nome, url in FONTI:
        try:
            testo, n, scartati = controlla(scarica(url))
        except Exception as e:
            print(f'{nome}: non raggiungibile ({e})')
            continue
        if n < soglia:
            print(f'{nome}: solo {n} satelliti validi (ne servono almeno {soglia}), scarto il file')
            continue
        if scartati > 0.02 * n:
            print(f'{nome}: {scartati} terne con cifre di controllo sbagliate, scarto il file')
            continue
        vecchio = f_tle.read_text(encoding='utf-8') if f_tle.exists() else ''
        if testo == vecchio:
            print(f'{nome}: {n} satelliti, nessuna novità rispetto al file già presente')
            return 0
        adesso = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        dati.mkdir(parents=True, exist_ok=True)
        f_tle.write_text(testo, encoding='utf-8')
        f_meta.write_text(json.dumps({'updated': adesso, 'count': n, 'source': nome}, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'{nome}: {n} satelliti, catalogo aggiornato alle {adesso}')
        return 0
    print('Nessuna fonte ha dato un catalogo valido: i file esistenti restano come sono.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
