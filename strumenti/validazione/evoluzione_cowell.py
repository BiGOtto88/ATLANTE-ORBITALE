# Script di verifica usato per VALIDAZIONE.md (i percorsi /tmp sono quelli della prova: adattali).
import json, numpy as np
d=json.load(open('/tmp/evo_cmp.json'))
def osc(mu,y):
    r=np.array(y[1:4]); v=np.array(y[4:7]); h=np.cross(r,v); rm=np.linalg.norm(r); ev=np.cross(v,h)/mu-r/rm; e=np.linalg.norm(ev)
    a=1/(2/rm-v@v/mu); i=np.arccos(h[2]/np.linalg.norm(h)); n=np.array([-h[1],h[0],0]); O=np.arctan2(n[1],n[0])
    w=np.arctan2(np.dot(np.cross(n/np.linalg.norm(n),ev),h/np.linalg.norm(h)),np.dot(n/np.linalg.norm(n),ev))
    return a,e,i,O,w
for k,v in d.items():
    mu=v['mu']; C=np.array(v['cow']); t=C[:,0]; E=np.array([osc(mu,y) for y in C])
    a,e,i,O,w=E.T; f=e*np.cos(w+O); g=e*np.sin(w+O); T=2*np.pi*np.sqrt(np.mean(a)**3/mu)/86400
    # running mean over one orbit
    def rm(x):
        out=np.empty_like(x); 
        for j in range(len(t)):
            m=np.abs(t-t[j])<=T/2; out[j]=x[m].mean()
        return out
    am, fm, gm, im = rm(a), rm(f), rm(g), rm(i); Om=np.unwrap(O); Om=rm(Om); em=np.hypot(fm,gm); wm=np.unwrap(np.arctan2(gm,fm))-Om
    sel=(t-t[0]>T)&(t[-1]-t>T)
    A=v['avg']; ta=np.array(A['t']); 
    def ip(x): return np.interp(t[sel],ta,np.array(x))
    aa,ea,ia=ip(A['a']),ip(A['e']),ip(A['i']); Oa=np.interp(t[sel],ta,np.unwrap(A['O'])); wa=np.interp(t[sel],ta,np.unwrap(A['w']))
    j0=0; j1=-1; tt=t[sel]
    print('== %s  (avg %.1f s, %d steps; cowell %.1f s) end=%s'%(k,v['tA']/1000,v['steps'],v['tC']/1000,v['end']))
    print('  span days %.1f  T %.3f d'%(tt[j1]-tt[j0],T))
    print('  Δa   cowell %+.4f  avg %+.4f km'%(am[sel][j1]-am[sel][j0], aa[j1]-aa[j0]))
    print('  Δe   cowell %+.6f  avg %+.6f'%(em[sel][j1]-em[sel][j0], ea[j1]-ea[j0]))
    print('  Δi   cowell %+.5f  avg %+.5f deg'%(np.degrees(im[sel][j1]-im[sel][j0]), np.degrees(ia[j1]-ia[j0])))
    print('  ΔΩ   cowell %+.4f  avg %+.4f deg'%(np.degrees(Om[sel][j1]-Om[sel][j0]), np.degrees(Oa[j1]-Oa[j0])))
    print('  Δω   cowell %+.4f  avg %+.4f deg'%(np.degrees(wm[sel][j1]-wm[sel][j0]), np.degrees(wa[j1]-wa[j0])))
print()
for k,v in d.items():
    mu=v['mu']; C=np.array(v['cow']); t=C[:,0]; E=np.array([osc(mu,y) for y in C]); a=E[:,0]; T=2*np.pi*np.sqrt(np.mean(a)**3/mu)/86400
    m=(t-t[0])<=T; print(k,'mean a first orbit (cowell) %.3f  avg start %.3f  diff %.3f km'%(a[m].mean(), v['avg']['a'][0], a[m].mean()-v['avg']['a'][0]))
