import sys, math, json; sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent))
from shot import serve
from playwright.sync_api import sync_playwright
from sgp4.api import Satrec
T0=1794697200000
def sun_eq(jd):  # Astronomical Almanac low-precision Sun, mean equator & equinox of date (~0.01°)
    n=jd-2451545.0; L=math.radians((280.460+0.9856474*n)%360); g=math.radians((357.528+0.9856003*n)%360)
    lam=L+math.radians(1.915)*math.sin(g)+math.radians(0.020)*math.sin(2*g); eps=math.radians(23.439-0.0000004*n)
    return [math.cos(lam),math.cos(eps)*math.sin(lam),math.sin(eps)*math.sin(lam)]
serve()
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-gl=swiftshader']); pg=b.new_page()
    pg.goto('http://127.0.0.1:8765/index.html#it'); pg.wait_for_function('window.atlante && atlante.sats && atlante.sats.length>1000',timeout=90000)
    pg.click('#btnPlay'); pg.evaluate('t=>atlante.setTime(t)',T0)
    for nid in [25544,41038,40296]:
        pg.evaluate('n=>atlante.select(n)',nid); pg.evaluate("atlante.setTab('dati')"); pg.wait_for_timeout(200); tle=pg.inner_text('#tleTxt').split('\n')
        B=pg.evaluate('atlante.betaYear(60)'); s=Satrec.twoline2rv(tle[1].strip(),tle[2].strip()); worst=0
        for d,bv in zip(B['t'],B['b']):
            jd=T0/86400000+2440587.5+d; e,r,v=s.sgp4(jd,0); h=[r[1]*v[2]-r[2]*v[1],r[2]*v[0]-r[0]*v[2],r[0]*v[1]-r[1]*v[0]]; hm=math.sqrt(sum(x*x for x in h)); u=sun_eq(jd)
            ref=math.degrees(math.asin(sum(a*c for a,c in zip(h,u))/hm)); worst=max(worst,abs(bv-ref))
        print(nid,tle[0].strip(),'days',len(B['t']),'max |Δβ| = %.4f°'%worst)
    b.close()
