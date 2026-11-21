#!/usr/bin/env python3
"""Costruisce le pagine del laboratorio di Keplario.

Prende ogni sorgente/laboratorio/<nome>.html, mette kit.css e kit.js al posto dei segnaposto
<!--KIT:CSS--> e <!--KIT:JS--> e scrive <nome>.html nella radice del sito. Così ogni pagina pubblicata
è un file solo, che il flusso di GitHub copia insieme agli altri .html senza bisogno di cartelle nuove.

Uso (dalla cartella del sito):
    python3 strumenti/costruisci_laboratorio.py            tutte le pagine
    python3 strumenti/costruisci_laboratorio.py orbite      solo orbite.html
I file che iniziano con _ (per esempio _modello.html) sono esempi e non vengono pubblicati,
a meno di chiederli per nome.
"""
import pathlib
import sys

RADICE = pathlib.Path(__file__).resolve().parent.parent
SORGENTE = RADICE / 'sorgente' / 'laboratorio'


def costruisci(nome: str) -> pathlib.Path:
    src = SORGENTE / f'{nome}.html'
    testo = src.read_text(encoding='utf-8')
    for segnaposto in ('<!--KIT:CSS-->', '<!--KIT:JS-->'):
        if testo.count(segnaposto) != 1:
            raise SystemExit(f'{src.name}: serve esattamente un {segnaposto}')
    css = (SORGENTE / 'kit.css').read_text(encoding='utf-8')
    js = (SORGENTE / 'kit.js').read_text(encoding='utf-8')
    testo = testo.replace('<!--KIT:CSS-->', '<style>\n' + css + '</style>')
    testo = testo.replace('<!--KIT:JS-->', '<script>\n' + js + '</script>')
    out = RADICE / f'{nome}.html'          # _modello.html resta un esempio: non va caricato su GitHub
    out.write_text(testo, encoding='utf-8')
    return out


def main() -> None:
    nomi = sys.argv[1:] or sorted(p.stem for p in SORGENTE.glob('*.html') if not p.stem.startswith('_'))
    for nome in nomi:
        out = costruisci(nome)
        print(f'{out.relative_to(RADICE)}  {out.stat().st_size // 1024} kB')


if __name__ == '__main__':
    main()
