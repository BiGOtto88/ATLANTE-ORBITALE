"""Prova degli elementi orbitali mostrati nella pagina Orbita: python3 strumenti/prove/prova_elementi.py 25544,41866,23802 [osc|mean]
Serve il sito sulla porta 8765 (python -m http.server dalla cartella del sito), apre la pagina in Chromium (playwright) a un istante fisso
e confronta gli elementi osculanti (stato SGP4 → elementi) e medi (am, em, im, Om, om, mm, nm di python-sgp4) con quelli mostrati.
Reads the Orbit page for a set of satellites in the browser at a fixed simulated instant and checks it against python-sgp4."""
import sys, json, math, subprocess, socket, time, pathlib
def serve():
    s=socket.socket()
    if s.connect_ex(('127.0.0.1',8765))!=0:
        subprocess.Popen([sys.executable,'-m','http.server','8765','--bind','127.0.0.1'],cwd=str(pathlib.Path(__file__).resolve().parents[2]),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(0.8)
    s.close()
from playwright.sync_api import sync_playwright
from sgp4.api import Satrec, jday
MU=398600.4418; RE=6378.137
T0=1794697200000  # fixed simulated instant (ms)
def num(t):
    t=t.replace('−','-').replace(' ','').replace(' ','').replace(',','.')
    try: return float(t)
    except: return float('nan')
def elems(r,v):
    rm=math.sqrt(sum(x*x for x in r)); vm=math.sqrt(sum(x*x for x in v)); rv=sum(a*b for a,b in zip(r,v))
    h=[r[1]*v[2]-r[2]*v[1],r[2]*v[0]-r[0]*v[2],r[0]*v[1]-r[1]*v[0]]; hm=math.sqrt(sum(x*x for x in h))
    n=[-h[1],h[0],0]; nm=math.hypot(n[0],n[1]); c1=vm*vm-MU/rm
    ev=[(c1*r[k]-rv*v[k])/MU for k in range(3)]; e=math.sqrt(sum(x*x for x in ev)); a=1/(2/rm-vm*vm/MU)
    i=math.degrees(math.acos(h[2]/hm)); O=math.degrees(math.atan2(h[0],-h[1]))%360
    w=math.degrees(math.acos(max(-1,min(1,(n[0]*ev[0]+n[1]*ev[1])/(nm*e))))); w= 360-w if ev[2]<0 else w
    nu=math.degrees(math.acos(max(-1,min(1,sum(a_*b for a_,b in zip(ev,r))/(e*rm))))); nu=360-nu if rv<0 else nu
    return dict(a=a,e=e,i=i,O=O,w=w,nu=nu,T=2*math.pi*math.sqrt(a**3/MU)/60,hp=a*(1-e)-RE,ha=a*(1+e)-RE,h=hm)
IDS=[int(x) for x in sys.argv[1].split(',')]; mode=sys.argv[2] if len(sys.argv)>2 else 'osc'
serve()
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-gl=swiftshader']); pg=b.new_page(viewport={'width':1440,'height':900})
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto('http://127.0.0.1:8765/index.html#it'); pg.wait_for_function('window.atlante && atlante.sats && atlante.sats.length>1000',timeout=90000)
    pg.click('#btnPlay'); pg.evaluate('t=>atlante.setTime(t)',T0); pg.wait_for_timeout(300)
    for nid in IDS:
        ok=pg.evaluate('n=>{atlante.select(n); return atlante.state().sel===n}',nid)
        if not ok: print(nid,'not in catalog'); continue
        pg.evaluate("atlante.setTab('dati')"); pg.wait_for_timeout(250); tle=pg.inner_text('#tleTxt').split('\n')
        pg.evaluate("atlante.setTab('orbita')"); pg.wait_for_timeout(250)
        if mode=='mean': pg.click('#segMean'); pg.wait_for_timeout(300)
        else: pg.click('#segOsc'); pg.wait_for_timeout(300)
        d={k:pg.inner_text('#'+k) for k in ['eA','eE','eI','eO','eW','eNu','eT','eHp','eHa','eX','eAnomL']}
        unitT=pg.evaluate("document.getElementById('eT').nextElementSibling.textContent")
        s=Satrec.twoline2rv(tle[1].strip(),tle[2].strip())
        jd=T0/86400000+2440587.5; err,r,v=s.sgp4(jd,0.0)
        if mode=='osc':
            E=elems(r,v); ref=dict(eA=E['a'],eE=E['e'],eI=E['i'],eO=E['O'],eW=E['w'],eNu=E['nu'],eT=E['T'],eHp=E['hp'],eHa=E['ha'],eX=E['h'])
        else:
            xke=60/math.sqrt(6378.135**3/398600.8); a=s.am*6378.135
            ref=dict(eA=a,eE=s.em,eI=math.degrees(s.im),eO=math.degrees(s.Om)%360,eW=math.degrees(s.om)%360,eNu=math.degrees(s.mm)%360,eT=2*math.pi/s.nm,eHp=a*(1-s.em)-RE,eHa=a*(1+s.em)-RE)
        out=[]
        for k,rv_ in ref.items():
            got=num(d[k]); 
            if k=='eT' and unitT!='min': got=got*(1440 if unitT=='giorni' else 1)
            diff=got-rv_
            if k in ('eO','eW','eNu'): diff=(diff+180)%360-180
            out.append('%s %s/%s(%.3g)'%(k,d[k],('%.6g'%rv_),diff))
        print(nid,tle[0].strip(),'|',d['eAnomL'],'\n   ',' '.join(out))
    for e in errs: print('ERR',e)
    b.close()
