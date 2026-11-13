#!/usr/bin/env python3
"""Trasforma la pagina sviluppata in Claude (l'artifact) nella pagina del sito autonomo, index.html.

Il codice dell'app è uno solo. Le due versioni differiscono soltanto in due punti, che questo
strumento sistema da solo:

  1. la testata: il sito ha bisogno di una testata completa (lingua, manifest, icone, caratteri
     B612 inclusi), che nel visualizzatore di Claude viene aggiunta in automatico;
  2. le librerie: nel visualizzatore arrivano da un CDN, nel sito dalle copie in vendor/.

Uso:   python3 strumenti/da_claude_a_sito.py pagina-di-claude.html
       (dalla cartella del sito; riscrive index.html)

La pagina di Claude può essere sia il file sorgente pubblicato, sia la pagina salvata dal
visualizzatore con la sua prima riga di testata: lo strumento riconosce entrambi i casi.
Serve solo Python 3, senza librerie aggiuntive.
"""
import pathlib, re, sys

RADICE = pathlib.Path(__file__).resolve().parent.parent
RANGE_LATINO = ('U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,'
                'U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD')
CARATTERI = [('B612', 400, 'b612-latin-400-normal.woff2'), ('B612', 700, 'b612-latin-700-normal.woff2'),
             ('B612 Mono', 400, 'b612-mono-latin-400-normal.woff2'), ('B612 Mono', 700, 'b612-mono-latin-700-normal.woff2')]
DESCRIZIONE = ('Il sistema solare in scala reale, i satelliti attivi attorno alla Terra e le sonde in viaggio: '
               'orbita, assetto, disturbi e progetto di missione.')


def converti(pagina):
    avvisi = []
    # la pagina salvata dal visualizzatore comincia con una riga di testata e finisce con </body></html>: si tolgono
    if pagina.lstrip().lower().startswith('<!doctype'):
        riga, _, resto = pagina.lstrip().partition('\n')
        if not riga.rstrip().endswith('<body>'):
            raise SystemExit('Questa sembra già una pagina completa (forse index.html del sito), non la pagina di Claude.')
        pagina = re.sub(r'\s*</body>\s*</html>\s*$', '\n', resto)

    m = re.search(r'<title>(.*?)</title>', pagina, re.S)
    titolo = m.group(1).strip() if m else 'Atlante Orbitale'
    inizio = pagina.find('<style>')
    fine = pagina.find('</style>', inizio)
    if inizio < 0 or fine < 0:
        raise SystemExit('Non trovo il blocco <style> della pagina: il file non è quello atteso.')
    stile, corpo = pagina[inizio:fine + len('</style>')], pagina[fine + len('</style>'):].lstrip('\n')
    # quello che precede <style> (titolo, meta del visualizzatore, caratteri da Google) viene sostituito dalla testata del sito

    # librerie: dal CDN alle copie incluse
    def locale(m):
        nome = m.group(1).split('/')[-1].split('?')[0]
        if not (RADICE / 'vendor' / nome).exists():
            avvisi.append('manca vendor/%s: scarica %s e mettilo nella cartella vendor/' % (nome, m.group(1)))
        return '<script src="vendor/%s"></script>' % nome
    corpo, n = re.subn(r'<script\s+src="(https?://[^"]+\.js(?:\?[^"]*)?)"\s*>\s*</script>', locale, corpo)
    if re.search(r'(src|href)="https?://', corpo):
        avvisi.append('nel corpo della pagina restano riferimenti a file esterni: controlla le righe con src="http… o href="http…')

    facce = ''.join('@font-face{font-family:"%s";font-style:normal;font-weight:%d;font-display:swap;'
                    'src:url(fonts/%s) format("woff2");unicode-range:%s}\n' % (fam, peso, file, RANGE_LATINO)
                    for fam, peso, file in CARATTERI)
    testata = '''<!doctype html>
<!-- Atlante Orbitale. Copyright (c) 2026 Davide Ottoninuoto, licenza MIT (file LICENSE). Librerie, caratteri, texture, modelli 3D e dati di terzi:
     fonti e licenze in LICENZE.txt. -->
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>%s</title>
<!-- File generato da strumenti/da_claude_a_sito.py: le modifiche fatte qui a mano si perdono alla prossima conversione. -->
<meta name="description" content="%s">
<meta name="theme-color" content="#080a0d">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icone/icona.svg" type="image/svg+xml">
<link rel="icon" href="icone/icona-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="icone/icona-180.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Atlante">
<style>
/* Regole di base che il visualizzatore di Claude aggiunge da solo e su cui la pagina conta. */
:root{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
html{background:#000;scroll-padding-top:env(safe-area-inset-top,0px)}
body{margin:0;padding:0}
img{max-width:100%%}
[hidden]:not([hidden=until-found i]){display:none!important}
/* Carattere B612, incluso nel sito (SIL Open Font License) */
%s</style>
''' % (titolo, DESCRIZIONE, facce)
    return testata + stile + '\n</head>\n<body>\n' + corpo.rstrip() + '\n</body>\n</html>\n', n, avvisi


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    pagina = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
    sito, n, avvisi = converti(pagina)
    (RADICE / 'index.html').write_text(sito, encoding='utf-8')
    print('Scritto index.html (%d kB), %d librerie puntate a vendor/.' % (len(sito.encode()) // 1024, n))
    for a in avvisi:
        print('ATTENZIONE:', a)
    return 1 if avvisi else 0


if __name__ == '__main__':
    sys.exit(main())
