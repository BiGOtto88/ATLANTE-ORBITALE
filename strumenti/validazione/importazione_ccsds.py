"""Prova dell'importazione CCSDS: effemeridi OEM della ISS scritte da qui in EME2000, TEME e ITRF (python-sgp4 + ERFA, indipendenti dalla
pagina), caricate nella pagina; posizioni interpolate dalla pagina in istanti fuori griglia confrontate con la verità calcolata qui.
Poi AEM (quaternioni, versione 1 FIRST/A2B e B2A, versione 2 LAST, angoli di Eulero ZYX) e OMM (KVN, JSON, CSV) ricostruito dai TLE."""
import sys, math, json, numpy as np, erfa
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent))
from shot import serve
from playwright.sync_api import sync_playwright
from sgp4.api import Satrec, WGS72
L1='1 25544U 98067A   26317.54875000  .00012000  00000+0  21000-3 0  9990'
L2='2 25544  51.6320 270.4000 0007300  26.6000 333.5000 15.50000000 10000'
def ck(l):
    s=sum(int(c) if c.isdigit() else (1 if c=='-' else 0) for c in l[:68]); return l[:68]+str(s%10)
L1,L2=ck(L1),ck(L2); S=Satrec.twoline2rv(L1,L2)
T0=S.jdsatepoch+S.jdsatepochF   # start at the TLE epoch, UTC
T0MS=round((T0-2440587.5)*864e5)   # whole milliseconds
JD=lambda ms: 2440587.5+ms/864e5
def teme(jd):
    # jd given as UTC ms since 1970 when large (exact arithmetic for the file epochs), or as a Julian date
    if jd>1e11: e,r,v=S.sgp4(2440587.5,jd/864e5)
    else: e,r,v=S.sgp4(jd,0.0)
    return np.array(r),np.array(v)
def gmst82(jd):
    t=(jd-2451545.0)/36525; g=67310.54841+(876600*3600+8640184.812866)*t+0.093104*t*t-6.2e-6*t**3; return math.radians((g%86400)/240)
def teme_to_j2000(jd,r,v):
    # TEME → TOD: rotation by the equation of the equinoxes (IAU 1994 in ERFA's 2000B nutation: use ee00b); TOD → J2000 with the NPB matrix (2000B)
    tt=jd+(37+32.184)/86400; ee=erfa.ee00b(2400000.5,tt-2400000.5); c,s=math.cos(ee),math.sin(ee)
    Rz=np.array([[c,-s,0],[s,c,0],[0,0,1]])   # TOD = Rz(-ee)·TEME? TEME x axis is the mean equinox: TOD components = R3(-ee) r
    rt,vt=Rz@r,Rz@v; N=erfa.pnm00b(2400000.5,tt-2400000.5); return N.T@rt,N.T@vt
def teme_to_itrf(jd,r,v):
    th=gmst82(jd); c,s=math.cos(th),math.sin(th); R=np.array([[c,s,0],[-s,c,0],[0,0,1]]); w=np.array([0,0,7.2921158553e-5]); rp=R@r; return rp,R@v-np.cross(w,rp)
def iso(jd):
    return erfa.d2dtf('UTC',6,jd,0.0)
def fmt_ep(jd):
    import datetime
    if jd>1e11: t=datetime.datetime(1970,1,1)+datetime.timedelta(milliseconds=jd); return t.strftime('%Y-%m-%dT%H:%M:%S.%f')
    y,mo,d,f=erfa.d2dtf('UTC',6,jd,0.0); return '%04d-%02d-%02dT%02d:%02d:%02d.%06d'%(y,mo,d,f[0],f[1],f[2],f[3])
def oem(frame,conv,step=60,n=360,interp='HERMITE',deg=5):
    out=['CCSDS_OEM_VERS = 2.0','CREATION_DATE = 2026-11-14T00:00:00','ORIGINATOR = PROVA','','META_START','OBJECT_NAME = ISS (ZARYA)','OBJECT_ID = 1998-067A','CENTER_NAME = EARTH','REF_FRAME = '+frame,'TIME_SYSTEM = UTC',
         'START_TIME = '+fmt_ep(T0),'STOP_TIME = '+fmt_ep(T0+(n-1)*step/86400),'INTERPOLATION = '+interp,'INTERPOLATION_DEGREE = %d'%deg,'META_STOP','']
    for k in range(n):
        ms=T0MS+k*step*1000; r,v=teme(ms); r,v=conv(JD(ms),r,v); out.append(fmt_ep(ms)+' '+' '.join('%.9f'%x for x in list(r)+list(v)))
    return '\n'.join(out)+'\n'
cases=[('EME2000',teme_to_j2000),('TEME',lambda jd,r,v:(r,v)),('ITRF2014',teme_to_itrf)]
serve()
with sync_playwright() as pw:
    br=pw.chromium.launch(args=['--use-gl=swiftshader']); pg=br.new_page(); pg.goto('http://127.0.0.1:8765/index.html#it'); pg.wait_for_function('window.atlante && !!atlante.ephAt && atlante.sats.length>1000',timeout=90000)
    rng=np.random.default_rng(1)
    for frame,conv in cases:
        txt=oem(frame,conv); pg.evaluate('([t,n])=>atlante.loadCcsds(t,n,"OEM")',[txt,'iss_'+frame+'.oem']); worst=0
        ts=T0MS+rng.uniform(1000,358*60000,40)
        res=pg.evaluate('([T])=>{ const p=atlante.imported[atlante.imported.length-1]; return T.map(ms=>{ const o=[0,0,0], v=[0,0,0]; atlante.ephAt(p,ms,o,v); return o.concat(v); }); }',[list(ts)])
        for ms,q in zip(ts,res):
            r,v=teme(ms); r,v=teme_to_j2000(JD(ms),r,v); worst=max(worst,np.linalg.norm(np.array(q[:3])-r)*1000)
        print('OEM %-8s: 40 istanti fuori griglia, scarto massimo di posizione %.3f m'%(frame,worst))
    # Hermite on data whose velocities are the exact derivative of the positions (two-body orbit, Kepler's equation here):
    # SGP4's velocity is not exactly the derivative of its own position (about 1 cm/s), which limits the case above
    mu=398600.4418; a=6800.0; e=0.01; n_=math.sqrt(mu/a**3)
    def kep(tsec):
        M=n_*tsec; E=M
        for _ in range(30): E-= (E-e*math.sin(E)-M)/(1-e*math.cos(E))
        r=a*(1-e*math.cos(E)); x=a*(math.cos(E)-e); y=a*math.sqrt(1-e*e)*math.sin(E); vx=-math.sqrt(mu*a)/r*math.sin(E); vy=math.sqrt(mu*a)/r*math.sqrt(1-e*e)*math.cos(E)
        ci,si=math.cos(0.9),math.sin(0.9); return np.array([x,y*ci,y*si]),np.array([vx,vy*ci,vy*si])
    lines=['CCSDS_OEM_VERS = 2.0','CREATION_DATE = 2026-11-14T00:00:00','ORIGINATOR = PROVA','META_START','OBJECT_NAME = KEPLERO','OBJECT_ID = PROVA','CENTER_NAME = EARTH','REF_FRAME = EME2000','TIME_SYSTEM = UTC','START_TIME = '+fmt_ep(T0MS),'STOP_TIME = '+fmt_ep(T0MS+359*60000),'META_STOP']
    for k in range(360):
        r,v=kep(k*60.0); lines.append(fmt_ep(T0MS+k*60000)+' '+' '.join('%.9f'%x for x in list(r)+list(v)))
    pg.evaluate('([t,n])=>atlante.loadCcsds(t,n,"OEM")',['\n'.join(lines)+'\n','kepler.oem'])
    res=pg.evaluate('([T])=>{ const p=atlante.imported[atlante.imported.length-1]; return T.map(ms=>{ const o=[0,0,0], v=[0,0,0]; atlante.ephAt(p,ms,o,v); return o.concat(v); }); }',[list(ts)])
    print('OEM a due corpi, Hermite grado 5 (predefinito): scarto massimo di posizione %.2e m, di velocità %.2e m/s'%(max(np.linalg.norm(np.array(q[:3])-kep((ms-T0MS)/1000)[0])*1000 for ms,q in zip(ts,res)),max(np.linalg.norm(np.array(q[3:])-kep((ms-T0MS)/1000)[1])*1000 for ms,q in zip(ts,res))))
    # Lagrange of degree 7 on the EME2000 file
    txt=oem('EME2000',teme_to_j2000,interp='LAGRANGE',deg=7); pg.evaluate('([t,n])=>atlante.loadCcsds(t,n,"OEM")',[txt,'iss_lag.oem'])
    res=pg.evaluate('([T])=>{ const p=atlante.imported[atlante.imported.length-1]; return T.map(ms=>{ const o=[0,0,0]; atlante.ephAt(p,ms,o,null); return o; }); }',[list(ts)])
    print('OEM Lagrange grado 7: scarto massimo %.3f m'%max(np.linalg.norm(np.array(q)-teme_to_j2000(JD(ms),*teme(ms))[0])*1000 for ms,q in zip(ts,res)))
    # AEM: an attitude known here (rotation of 30° about (1,2,3) w.r.t. EME2000, body ← EME2000), written in four ways
    ax=np.array([1,2,3.]); ax/=np.linalg.norm(ax); th=math.radians(30); qv=ax*math.sin(th/2); qs=math.cos(th/2)
    def dcm(q,s):   # passive (body ← ref), scalar s, vector q
        x,y,z=q; w=s; return np.array([[1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w)],[2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w)],[2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y)]])
    Aref=dcm(qv,qs)
    ep1,ep2=fmt_ep(T0),fmt_ep(T0+600/86400)
    def aem(vers,lines,extra):
        return '\n'.join(['CCSDS_AEM_VERS = '+vers,'CREATION_DATE = 2026-11-14T00:00:00','ORIGINATOR = PROVA','META_START','OBJECT_NAME = ISS (ZARYA)','OBJECT_ID = 1998-067A','CENTER_NAME = EARTH']+extra+['TIME_SYSTEM = UTC','START_TIME = '+ep1,'STOP_TIME = '+ep2,'META_STOP']+(['DATA_START'] if vers.startswith('2') else [])+lines+(['DATA_STOP'] if vers.startswith('2') else []))+'\n'
    q1=[qs,*qv]; q2=[*qv,qs]; qi=[qs,*(-qv)]
    # Euler ZYX (v2): body = R_X(a3) R_Y(a2) R_Z(a1) ref
    R=Aref; a2=-math.asin(R[0,2]); a1=math.atan2(R[0,1],R[0,0]); a3=math.atan2(R[1,2],R[2,2])
    files={'v1 FIRST A2B':aem('1.0',[e+' '+' '.join('%.12f'%x for x in q1) for e in (ep1,ep2)],['REF_FRAME_A = EME2000','REF_FRAME_B = SC_BODY_1','ATTITUDE_DIR = A2B','ATTITUDE_TYPE = QUATERNION','QUATERNION_TYPE = FIRST']),
           'v1 FIRST B2A':aem('1.0',[e+' '+' '.join('%.12f'%x for x in qi) for e in (ep1,ep2)],['REF_FRAME_A = EME2000','REF_FRAME_B = SC_BODY_1','ATTITUDE_DIR = B2A','ATTITUDE_TYPE = QUATERNION','QUATERNION_TYPE = FIRST']),
           'v2 LAST':aem('2.0',[e+' '+' '.join('%.12f'%x for x in q2) for e in (ep1,ep2)],['REF_FRAME_A = EME2000','REF_FRAME_B = SC_BODY_1','ATTITUDE_TYPE = QUATERNION']),
           'v2 EULER ZYX':aem('2.0',[e+' '+' '.join('%.12f'%math.degrees(x) for x in (a1,a2,a3)) for e in (ep1,ep2)],['REF_FRAME_A = EME2000','REF_FRAME_B = SC_BODY_1','ATTITUDE_TYPE = EULER_ANGLE','EULER_ROT_SEQ = ZYX'])}
    pg.evaluate('n=>atlante.select(n)',25544)
    for k,t in files.items():
        pg.evaluate('([t,n])=>atlante.loadCcsds(t,n,"AEM")',[t,k+'.aem'])
        A=pg.evaluate('([jd])=>{ const A=new Float64Array(9); atlante.aemAt(atlante.attFile,(jd-2440587.5)*864e5,A); return Array.from(A); }',[T0+300/86400])
        err=np.degrees(np.arccos(max(-1,min(1,(np.trace(np.array(A).reshape(3,3)@Aref.T)-1)/2))))
        print('AEM %-14s: scarto d\'assetto %.2e°'%(k,err))
    # OMM round trip: the TLE above → OMM (KVN, JSON, CSV) → TLE rebuilt by the page
    omm={'OBJECT_NAME':'ISS (ZARYA)','OBJECT_ID':'1998-067A','EPOCH':fmt_ep(T0),'MEAN_MOTION':'15.50000000','ECCENTRICITY':'.0007300','INCLINATION':'51.6320','RA_OF_ASC_NODE':'270.4000','ARG_OF_PERICENTER':'26.6000','MEAN_ANOMALY':'333.5000','EPHEMERIS_TYPE':'0','CLASSIFICATION_TYPE':'U','NORAD_CAT_ID':'25544','ELEMENT_SET_NO':'999','REV_AT_EPOCH':'1000','BSTAR':'.00021','MEAN_MOTION_DOT':'.00012','MEAN_MOTION_DDOT':'0','MEAN_ELEMENT_THEORY':'SGP4'}
    tle=pg.evaluate('o=>atlante.ommToTle(o)',omm).split('\n')
    S2=Satrec.twoline2rv(tle[1],tle[2]); d=max(np.linalg.norm(np.array(S.sgp4(T0+k/24,0)[1])-np.array(S2.sgp4(T0+k/24,0)[1])) for k in range(48))*1000
    print('OMM → TLE: righe\n  '+tle[1]+'\n  '+tle[2]+'\n  posizioni SGP4 rispetto al TLE originale per 2 giorni: scarto massimo %.3f m'%d)
    br.close()
