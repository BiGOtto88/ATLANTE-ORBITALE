# Independent check of the limb search: brute-force ray casting on the WGS84 ellipsoid (+h) on a fine grid of directions near the limb,
# minimum angle between a boresight and the directions that hit; compared with the page's limbOf (180 azimuths, bisection).
import sys, json, math, numpy as np; sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parent))
from shot import serve
from playwright.sync_api import sync_playwright
RE=6378.137; F=1/298.257223563; RP=RE*(1-F)
cases=[([7000,0,0],[0,0,1],100),([0,-4000,5800],[0.3,0.8,0.52],100),([3000,3000,6000],[-0.2,0.9,0.1],40),([42164,0,0],[-0.98,0.17,0.05],0),([5000,-5000,1000],[0,0,-1],100)]
def brute(r,b,h):
    r=np.array(r,float); b=np.array(b,float); b/=np.linalg.norm(b); A=RE+h; C=RE*0.99664719+h  # page uses BODY.f = 0.99665 → C = R·f
    rm=np.linalg.norm(r); n=-r/rm; a=np.array([0,0,1.]) if abs(n[2])<0.9 else np.array([1,0,0.]); e1=np.cross(a,n); e1/=np.linalg.norm(e1); e2=np.cross(n,e1)
    rho=math.asin(min(1,max(A,C)/rm)); best=9e9
    phi=np.linspace(max(0,rho-0.05),min(math.pi/2,rho+0.02),1500); psi=np.linspace(0,2*math.pi,2880,endpoint=False)
    P,Q=np.meshgrid(phi,psi); d=(np.cos(P)[...,None]*n+np.sin(P)[...,None]*(np.cos(Q)[...,None]*e1+np.sin(Q)[...,None]*e2))
    p=r/np.array([A,A,C]); dd=d/np.array([A,A,C]); pd=(dd*p).sum(-1); disc=pd**2-(dd*dd).sum(-1)*((p*p).sum()-1); hit=(pd<0)&(disc>=0)
    ang=np.degrees(np.arccos(np.clip((d*b).sum(-1),-1,1))); bh=( (np.dot(b/np.array([A,A,C]),p))<0 ) and (np.dot(b/np.array([A,A,C]),p)**2-np.dot(b/np.array([A,A,C]),b/np.array([A,A,C]))*((p*p).sum()-1)>=0)
    return float(ang[hit].min()) if not bh else -1
serve()
with sync_playwright() as pw:
    br=pw.chromium.launch(args=['--use-gl=swiftshader']); pg=br.new_page(); pg.goto('http://127.0.0.1:8765/index.html#it'); pg.wait_for_function('window.atlante && !!atlante.limbOf && atlante.sats.length>1000',timeout=90000)
    for r,b,h in cases:
        js=pg.evaluate("([r,b,h])=>{ const L=atlante.limbOf('earth',r,h,[1,0,0]); const l=Math.hypot(...b), u=b.map(x=>x/l); let m=1e9; for(const q of L.limb){ const c=q.d[0]*u[0]+q.d[1]*u[1]+q.d[2]*u[2]; m=Math.min(m,Math.acos(Math.max(-1,Math.min(1,c)))*180/Math.PI); } return L.hit(u)?-1:m; }",[r,b,h])
        ref=brute(r,b,h); print(r,b,h,'pagina %.4f°  forza bruta %.4f°  scarto %.4f°'%(js,ref,js-ref))
    br.close()
