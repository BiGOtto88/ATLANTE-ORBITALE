"""Writes data/citta.txt, the list of places for the «Passaggi» page search.

Source: GeoNames (www.geonames.org, CC BY 4.0) through the Python package geonamescache (MIT), which ships the GeoNames
"cities15000" table. Kept: every city above 30 000 inhabitants and every Italian city above 15 000, minus administrative
sub-districts. One line per place, most populous first: name;country code;latitude;longitude[;other names separated by |].
The other names are the usual Italian forms of well-known cities (Roma, Londra, Monaco di Baviera...), so that both
spellings are found.

    pip install geonamescache
    python3 strumenti/citta/genera_citta.py
"""
import pathlib, unicodedata
import geonamescache

RADICE = pathlib.Path(__file__).resolve().parents[2]
ITALIANO = {  # (GeoNames name, country): Italian names
    ('Rome','IT'):'Roma', ('Milan','IT'):'Milano', ('Naples','IT'):'Napoli', ('Turin','IT'):'Torino', ('Genoa','IT'):'Genova',
    ('Florence','IT'):'Firenze', ('Padua','IT'):'Padova', ('Venice','IT'):'Venezia', ('Mantua','IT'):'Mantova', ("Reggio nell'Emilia",'IT'):'Reggio Emilia',
    ('London','GB'):'Londra', ('Edinburgh','GB'):'Edimburgo', ('Paris','FR'):'Parigi', ('Marseille','FR'):'Marsiglia', ('Lyon','FR'):'Lione',
    ('Nice','FR'):'Nizza', ('Toulouse','FR'):'Tolosa', ('Strasbourg','FR'):'Strasburgo', ('Moscow','RU'):'Mosca', ('Saint Petersburg','RU'):'San Pietroburgo',
    ('Beijing','CN'):'Pechino', ('Munich','DE'):'Monaco di Baviera', ('Berlin','DE'):'Berlino', ('Hamburg','DE'):'Amburgo', ('Köln','DE'):'Colonia',
    ('Frankfurt am Main','DE'):'Francoforte', ('Nuremberg','DE'):'Norimberga', ('Dresden','DE'):'Dresda', ('Lisbon','PT'):'Lisbona', ('Warsaw','PL'):'Varsavia',
    ('Kraków','PL'):'Cracovia', ('Prague','CZ'):'Praga', ('Athens','GR'):'Atene', ('Brussels','BE'):'Bruxelles', ('Antwerp','BE'):'Anversa',
    ('The Hague','NL'):"L'Aia", ('Geneva','CH'):'Ginevra', ('Zürich','CH'):'Zurigo', ('Basel','CH'):'Basilea', ('Bern','CH'):'Berna', ('Luzern','CH'):'Lucerna',
    ('Salzburg','AT'):'Salisburgo', ('Cairo','EG'):'Il Cairo', ('Mexico City','MX'):'Città del Messico', ('Copenhagen','DK'):'Copenaghen',
    ('Stockholm','SE'):'Stoccolma', ('New Delhi','IN'):'Nuova Delhi', ('Sevilla','ES'):'Siviglia', ('Barcelona','ES'):'Barcellona', ('Zaragoza','ES'):'Saragozza',
    ('Bucharest','RO'):'Bucarest', ('Belgrade','RS'):'Belgrado', ('Jerusalem','IL'):'Gerusalemme', ('Algiers','DZ'):'Algeri', ('Tunis','TN'):'Tunisi',
    ('Dublin','IE'):'Dublino', ('Kyiv','UA'):'Kiev', ('Ljubljana','SI'):'Lubiana', ('Zagreb','HR'):'Zagabria', ('Split','HR'):'Spalato', ('Rijeka','HR'):'Fiume',
    ('Havana','CU'):"L'Avana", ('São Paulo','BR'):'San Paolo', ('Philadelphia','US'):'Filadelfia', ('Cape Town','ZA'):'Città del Capo', ('Tehran','IR'):'Teheran',
    ('Damascus','SY'):'Damasco', ('Makkah','SA'):'La Mecca', ('Vienna','AT'):'Wien', ('Moscow','RU'):'Mosca', ('Seoul','KR'):'Seul', ('Istanbul','TR'):'Costantinopoli',
}
SALTA = ('circoiscrizione', 'circoscrizione', 'municipio ')

def piatto(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

def main():
    cc = geonamescache.GeonamesCache().get_cities().values()
    sel = [v for v in cc if (v['population'] >= 30000 or v['countrycode'] == 'IT') and not piatto(v['name']).startswith(SALTA)]
    sel.sort(key=lambda v: -v['population'])
    usati, righe = set(), []
    chiavi = {(piatto(n), c): it for (n, c), it in ITALIANO.items()}
    for v in sel:
        k = (piatto(v['name']), v['countrycode'])
        alt = chiavi.get(k) if k not in usati else None
        if alt: usati.add(k)
        righe.append('%s;%s;%.3f;%.3f%s' % (v['name'].replace(';', ','), v['countrycode'], v['latitude'], v['longitude'], (';' + alt) if alt else ''))
    mancano = [n for (n, c) in ITALIANO if (piatto(n), c) not in usati]
    if mancano: print('Nomi italiani senza città corrispondente:', ', '.join(mancano))
    (RADICE / 'data' / 'citta.txt').write_text('\n'.join(righe) + '\n', encoding='utf-8')
    print('Scritto data/citta.txt: %d luoghi' % len(righe))

if __name__ == '__main__':
    main()
