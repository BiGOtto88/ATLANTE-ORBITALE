# Independent check of the frozen-orbit formula: Cowell with J2+J3 zonal gravity (SciPy DOP853), orbit-averaged eccentricity vector
# (e cos ω, e sin ω) over many orbits; it circles around the frozen point, whose centre is fitted and compared with −(J3/2J2)(R/a) sin i.
import numpy as np, math
from scipy.integrate import solve_ivp
def run(mu,R,J2,J3,a,inc,e0,w0,days):
    def acc(t,y):
        x,yy,z=y[:3]; r2=x*x+yy*yy+z*z; r=math.sqrt(r2); zr=z/r; f=mu/r2/r
        k2=1.5*J2*(R/r)**2; ax=-f*x*(1-k2*(5*zr*zr-1)); ay=-f*yy*(1-k2*(5*zr*zr-1)); az=-f*z*(1-k2*(5*zr*zr-3))
        k3=0.5*J3*(R/r)**3; c=mu/r2/r  # J3 term: gradient of -mu J3 R^3 P3(z/r) / r^4 (Vallado, Fundamentals of Astrodynamics, sez. 8.6)
        ax+= c*x*k3*5*(7*zr**3-3*zr); ay+= c*yy*k3*5*(7*zr**3-3*zr); az+= c*k3*r*(35*zr**4-30*zr*zr+3)
        return [y[3],y[4],y[5],ax,ay,az]
    p=a*(1-e0*e0); nu=0.0; r=p/(1+e0); ci,si=math.cos(inc),math.sin(inc); cw,sw=math.cos(w0),math.sin(w0)
    P=np.array([cw,ci*sw,si*sw]); Q=np.array([-sw,ci*cw,si*cw]); vr=math.sqrt(mu/p)
    y0=np.concatenate([r*P, vr*(e0*Q+Q)])
    T=2*math.pi*math.sqrt(a**3/mu); N=int(days*86400/T)
    sol=solve_ivp(acc,[0,N*T],y0,method='DOP853',rtol=1e-11,atol=1e-9,t_eval=np.linspace(0,N*T,N*64+1))
    Y=sol.y.T; ev=[]
    for k in range(N):
        seg=Y[k*64:(k+1)*64]; E=[]
        for s in seg:
            rr=s[:3]; vv=s[3:]; h=np.cross(rr,vv); e=np.cross(vv,h)/mu-rr/np.linalg.norm(rr); nvec=np.cross([0,0,1],h); nvec/=np.linalg.norm(nvec); m=np.cross(h/np.linalg.norm(h),nvec)
            E.append([e@nvec,e@m])  # components in the node frame: e cos ω, e sin ω
        ev.append(np.mean(E,axis=0))
    ev=np.array(ev); A=np.c_[2*ev,np.ones(len(ev))]; b=(ev**2).sum(1); cx,cy,_=np.linalg.lstsq(A,b,rcond=None)[0]
    return cx,cy
for name,mu,R,J2,J3,a,inc in [('Terra 800 km i 98,6°',398600.4418,6378.1363,1.082626e-3,-2.532411e-6,6378.137+800,98.6),('Marte 400 km i 92°',42828.374857,3397.0,1.955454e-3,3.144981e-5,3397+400,92.0)]:
    cx,cy=run(mu,R,J2,J3,a,math.radians(inc),0.004,math.radians(90),260 if 'Terra' in name else 400)
    ef=-J3/(2*J2)*(R/a)*math.sin(math.radians(inc))
    print('%-22s formula e=%.6f ω=%s | numerico: centro (e cosω, e sinω) = (%.6f, %.6f)'%(name,abs(ef),'90°' if ef>0 else '270°',cx,cy))
