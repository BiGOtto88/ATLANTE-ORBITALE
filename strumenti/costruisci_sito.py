#!/usr/bin/env python3
"""Trasforma la pagina sorgente nella pagina del sito autonomo, index.html.

Il codice dell'app è uno solo. Le due versioni differiscono soltanto in due punti, che questo
strumento sistema da solo:

  1. la testata: il sito ha bisogno di una testata completa (lingua, manifest, icone, caratteri
     B612 inclusi), che nel visualizzatore integrato viene aggiunta in automatico;
  2. le librerie: nel visualizzatore arrivano da un CDN, nel sito dalle copie in vendor/.

Uso:   python3 strumenti/costruisci_sito.py pagina-sorgente.html
       (dalla cartella del sito; riscrive index.html)

La pagina sorgente può essere sia il file sorgente pubblicato, sia la pagina salvata dal
visualizzatore con la sua prima riga di testata: lo strumento riconosce entrambi i casi.
Serve solo Python 3, senza librerie aggiuntive.
"""
import datetime, json, pathlib, re, sys

RADICE = pathlib.Path(__file__).resolve().parent.parent
RANGE_LATINO = ('U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,'
                'U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD')
CARATTERI = [('B612', 400, 'b612-latin-400-normal.woff2'), ('B612', 700, 'b612-latin-700-normal.woff2'),
             ('B612 Mono', 400, 'b612-mono-latin-400-normal.woff2'), ('B612 Mono', 700, 'b612-mono-latin-700-normal.woff2')]
DESCRIZIONE = ('Satelliti e sonde in orbita in scala reale e in tempo reale: orbite, assetto, finestre di lancio e progetto di missione. Gratis, da computer e da telefono.')
DESCRIZIONE_EN = ('Satellites and probes in orbit at true scale and in real time: orbits, attitude, launch windows and mission design. Free, on computer and phone.')
# indirizzo pubblico del sito (GitHub Pages): serve ai motori di ricerca e alle anteprime dei link; cambialo se il sito si sposta
SITO = 'https://ottonspace.github.io/KEPLARIO/'
# Indirizzo del servizio dell'assistente (vedi assistente/LEGGIMI-assistente.md). Vuoto = assistente nascosto.
ASSISTENTE = 'https://keplario-assistente.davide-ottoninuoto.workers.dev'
SOTTOTITOLO = 'il planetario delle orbite'
SOTTOTITOLO_EN = 'the orbit planetarium'


def dati_strutturati(titolo, en=False):
    # schema.org WebApplication: dice ai motori di ricerca che cos'è il sito (nome, descrizione, gratuito, lingue)
    d = {'@context': 'https://schema.org', '@type': 'WebApplication', 'name': titolo, 'alternateName': ['Keplario', 'Atlante Orbitale'], 'url': SITO + ('en/' if en else ''),
         'description': DESCRIZIONE_EN if en else DESCRIZIONE, 'applicationCategory': 'EducationalApplication', 'operatingSystem': 'Any (web browser)' if en else 'Qualsiasi (browser)',
         'inLanguage': ['it', 'en'], 'isAccessibleForFree': True, 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'EUR'},
         'featureList': (['Orbit, position and speed of ~15,000 satellites', 'Solar-system probes with ground track', 'ISS and satellite passes over your location', 'Mission design: orbit, attitude, perturbations, power, links, launch windows'] if en else ['Orbita, posizione e velocità di oltre 15 000 satelliti', 'Sonde del sistema solare con traccia a terra', 'Passaggi della ISS e dei satelliti sopra il tuo luogo', 'Progetto di missione: orbita, assetto, disturbi, potenza, collegamenti, finestre di lancio']),
         'image': SITO + 'icone/anteprima.jpg', 'author': {'@type': 'Person', 'name': 'Davide Ottoninuoto'}}
    return json.dumps(d, ensure_ascii=False).replace('</', '<\\/')


def scrivi_sitemap(oggi):
    # sitemap.xml: le pagine da indicizzare (italiano e inglese, collegate fra loro), da indicare in Google Search Console e Bing Webmaster Tools
    alt = ('<xhtml:link rel="alternate" hreflang="it" href="%s"/><xhtml:link rel="alternate" hreflang="en" href="%sen/"/>'
           '<xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % (SITO, SITO, SITO))
    righe = ''.join('  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>daily</changefreq>%s</url>\n' % (u, oggi, alt) for u in (SITO, SITO + 'en/'))
    # pagine del laboratorio (una sola pagina per le due lingue: la lingua si sceglie nella pagina)
    lab = [n for n in ('orbite', 'assetto', 'propulsione', 'strutture', 'comunicazioni', 'sistemi') if (RADICE / (n + '.html')).exists()]
    righe += ''.join('  <url><loc>%s%s.html</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq></url>\n' % (SITO, n, oggi) for n in lab)
    (RADICE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                                        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + righe + '</urlset>\n', encoding='utf-8')


def converti(pagina):
    avvisi = []
    # la pagina salvata dal visualizzatore comincia con una riga di testata e finisce con </body></html>: si tolgono
    if pagina.lstrip().lower().startswith('<!doctype'):
        riga, _, resto = pagina.lstrip().partition('\n')
        if not riga.rstrip().endswith('<body>'):
            raise SystemExit('Questa sembra già una pagina completa (forse index.html del sito), non la pagina sorgente.')
        pagina = re.sub(r'\s*</body>\s*</html>\s*$', '\n', resto)

    m = re.search(r'<title>(.*?)</title>', pagina, re.S)
    titolo = m.group(1).strip() if m else 'Keplario'
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
    if re.search(r'src="https?://|<link[^>]+href="https?://', corpo):   # normal links (<a href>) to other sites are fine
        avvisi.append('nel corpo della pagina restano riferimenti a file esterni: controlla le righe con src="http… o href="http…')

    facce = ''.join('@font-face{font-family:"%s";font-style:normal;font-weight:%d;font-display:swap;'
                    'src:url(fonts/%s) format("woff2");unicode-range:%s}\n' % (fam, peso, file, RANGE_LATINO)
                    for fam, peso, file in CARATTERI)
    def testata(en):
        tit, sott, desc, url = titolo, (SOTTOTITOLO_EN if en else SOTTOTITOLO), (DESCRIZIONE_EN if en else DESCRIZIONE), SITO + ('en/' if en else '')
        return '''<!doctype html>
<!-- Keplario. Copyright (c) 2026 Davide Ottoninuoto, licenza MIT (file LICENSE). Librerie, caratteri, texture, modelli 3D e dati di terzi:
     fonti e licenze in LICENZE.txt. -->
<html lang="%s"%s>
<head>
<meta charset="utf-8">
%s<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>%s · %s</title>
<!-- File generato da strumenti/costruisci_sito.py: le modifiche fatte qui a mano si perdono alla prossima conversione. -->
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<link rel="alternate" hreflang="it" href="%s">
<link rel="alternate" hreflang="en" href="%sen/">
<link rel="alternate" hreflang="x-default" href="%s">
<meta name="robots" content="index,follow">
<meta property="og:type" content="website">
<meta property="og:site_name" content="%s">
<meta property="og:title" content="%s · %s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="%sicone/anteprima.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="%s">
<meta property="og:locale:alternate" content="%s">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">%s</script>
<meta name="theme-color" content="#080a0d">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icone/icona.svg" type="image/svg+xml">
<link rel="icon" href="icone/icona-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="icone/icona-180.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Keplario">
<style>
/* Regole di base che il visualizzatore integrato aggiunge da solo e su cui la pagina conta. */
:root{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
html{background:#000;scroll-padding-top:env(safe-area-inset-top,0px)}
body{margin:0;padding:0}
img{max-width:100%%}
[hidden]:not([hidden=until-found i]){display:none!important}
/* Carattere B612, incluso nel sito (SIL Open Font License) */
%s</style>
''' % ('en' if en else 'it', ' data-lang="en"' if en else '',
         # la pagina inglese vive in en/ ma usa i file della radice
         '<base href="../">\n' if en else '', tit, sott, desc, url, SITO, SITO, SITO, tit, tit, sott, desc, url, SITO,
         'en_GB' if en else 'it_IT', 'it_IT' if en else 'en_GB', dati_strutturati(tit, en), facce)
    def lingua(en):
        # il testo di presentazione c'è nelle due lingue: nella pagina si vede subito quello della lingua della pagina,
        # l'altro è nascosto (lo mostra la pagina se il visitatore usa l'altra lingua)
        c = corpo.replace('<!--L:it-->', '').replace('<!--L:en-->', '').replace('<!--/L-->', '')
        altra = 'it' if en else 'en'
        c = c.replace('<div class="al" data-l="%s">' % altra, '<div class="al" data-l="%s" hidden>' % altra)
        if en: c = c.replace('>Esplora il cielo</button>', '>Explore the sky</button>').replace('>Visita guidata · 6 tappe</button>', '>Guided tour · 6 stops</button>')
        return c
    fai = lambda en: testata(en).replace('<meta name="robots" content="index,follow">', '<meta name="robots" content="index,follow">\n<meta name="assistente" content="%s">' % ASSISTENTE, 1) + stile + '\n</head>\n<body>\n' + lingua(en).rstrip() + '\n</body>\n</html>\n'
    return fai(False), fai(True), n, avvisi


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    pagina = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
    sito, sito_en, n, avvisi = converti(pagina)
    (RADICE / 'index.html').write_text(sito, encoding='utf-8')
    (RADICE / 'en').mkdir(exist_ok=True)
    (RADICE / 'en' / 'index.html').write_text(sito_en, encoding='utf-8')   # stessa pagina, in inglese, per i motori di ricerca
    scrivi_sitemap(datetime.date.today().isoformat())
    print('Scritto index.html (%d kB), %d librerie puntate a vendor/.' % (len(sito.encode()) // 1024, n))
    for a in avvisi:
        print('ATTENZIONE:', a)
    return 1 if avvisi else 0


if __name__ == '__main__':
    sys.exit(main())
