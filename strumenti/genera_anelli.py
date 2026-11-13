#!/usr/bin/env python3
"""Genera tex/ring.png: profilo radiale degli anelli principali di Saturno (opera originale di questo progetto, nessun file di terzi).

La striscia (1024 x 8 pixel, RGBA) va dal bordo interno dell'anello C (74 500 km) al bordo esterno dell'anello F (140 200 km),
lo stesso intervallo usato dalla pagina. Confini e lacune sono quelli noti dalla letteratura (raggi in migliaia di km dal centro di Saturno):
anello C 74,5-92,0; anello B 92,0-117,5; divisione di Cassini 117,5-122,2; anello A 122,2-136,8; lacuna di Encke a 133,4; anello F a 140,2.
Le sfumature sono una rappresentazione, non una mappa fotometrica.
Uso: python3 strumenti/genera_anelli.py tex/ring.png"""
import sys, random, math
from PIL import Image

RI, RO, W, H = 74.5, 140.2, 1024, 8
rnd = random.Random(7)                        # seme fisso: il file esce sempre uguale
# (r0, r1, alfa, colore)
FASCE = [(74.5, 92.0, 0.20, (128, 118, 108)), (92.0, 99.0, 0.70, (190, 168, 138)), (99.0, 117.5, 0.92, (214, 192, 156)),
         (117.5, 122.2, 0.07, (150, 140, 128)), (122.2, 133.2, 0.62, (196, 178, 148)), (133.6, 136.8, 0.55, (186, 168, 140)),
         (136.8, 139.9, 0.03, (150, 140, 128)), (139.9, 140.2, 0.50, (200, 184, 154))]
fine = [rnd.uniform(-1, 1) for _ in range(W)]
liscia = [sum(fine[max(0, i - 2):i + 3]) / len(fine[max(0, i - 2):i + 3]) for i in range(W)]   # variazione fine a piccola scala
im = Image.new('RGBA', (W, H))
for x in range(W):
    r = RI + (RO - RI) * x / (W - 1)
    a, c = 0.03, (150, 140, 128)
    for r0, r1, aa, cc in FASCE:
        if r0 <= r < r1:
            a, c = aa, cc
            # transizioni dolci ai bordi di ogni fascia (circa 0,4 migliaia di km)
            d = min(r - r0, r1 - r) / 0.4
            if d < 1: a = aa * (0.25 + 0.75 * max(d, 0))
            break
    if abs(r - 133.4) < 0.17: a *= 0.12                     # lacuna di Encke
    a = min(1.0, max(0.0, a * (1 + 0.16 * liscia[x] * (1 if a > 0.3 else 0.4))))
    sh = 1 + 0.05 * liscia[x]
    px = (min(255, int(c[0] * sh)), min(255, int(c[1] * sh)), min(255, int(c[2] * sh)), int(255 * a))
    for y in range(H): im.putpixel((x, y), px)
im.save(sys.argv[1] if len(sys.argv) > 1 else 'ring.png', optimize=True)
