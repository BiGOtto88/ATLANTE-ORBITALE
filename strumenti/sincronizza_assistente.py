#!/usr/bin/env python3
"""Copia le istruzioni e le definizioni degli strumenti dell'assistente da assistente/worker.js nella pagina sorgente
(il blocco tra /*ASDEFS*/ e /*/ASDEFS*/), così il servizio e l'artifact usano gli stessi testi.
Uso: python3 strumenti/sincronizza_assistente.py   (poi riconverti la pagina con costruisci_sito.py)"""
import json, pathlib, re, subprocess, sys
R = pathlib.Path(__file__).resolve().parent.parent
w = (R / 'assistente/worker.js').read_text()
corpo = re.sub(r'export default \{[\s\S]*$', '', w)
js = "const vm=require('vm');const o=vm.runInNewContext(process.argv[1]+';({SYSTEM,TOOLS})');console.log(JSON.stringify(o))"
o = json.loads(subprocess.run(['node', '-e', js, corpo], capture_output=True, text=True, check=True).stdout)
bloc = '/*ASDEFS*/const AS_SYS=%s;\nconst AS_DEFS=%s;/*/ASDEFS*/' % (json.dumps(o['SYSTEM'], ensure_ascii=False), json.dumps(o['TOOLS'], ensure_ascii=False))
P = R / 'sorgente/pagina-sorgente.html'; s = P.read_text()
n = re.subn(r'/\*ASDEFS\*/[\s\S]*?/\*/ASDEFS\*/', lambda m: bloc, s)
if n[1] != 1: sys.exit('blocco /*ASDEFS*/ non trovato')
P.write_text(n[0]); print('Sincronizzato: %d strumenti' % len(o['TOOLS']))
