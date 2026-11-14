# Script di verifica usato per VALIDAZIONE.md (i percorsi /tmp sono quelli della prova: adattali).
import numpy as np, trimesh, json, sys
def ref(k, dirs, N=800, rs=0.3, rd=0.1):
    V=np.fromfile('/tmp/tri_%s.bin'%k).reshape(-1,3,3); j=json.load(open('/home/claude/sito_zip/estratto/modelli/%s_sup.json'%k)); cm=np.array(j['centroide_m'])
    m=trimesh.Trimesh(vertices=V.reshape(-1,3), faces=np.arange(len(V)*3).reshape(-1,3), process=False); from trimesh.ray.ray_pyembree import RayMeshIntersector; m.ray=RayMeshIntersector(m)
    n=np.cross(V[:,1]-V[:,0],V[:,2]-V[:,0]); l=np.linalg.norm(n,axis=1); n=n/np.where(l>0,l,1)[:,None]
    R=np.linalg.norm(V.reshape(-1,3),axis=1).max()*1.001; out=[]
    rng=np.random.default_rng(1)
    for s in dirs:
        s=np.array(s,float); s/=np.linalg.norm(s); a=np.array([0,0,1.]) if abs(s[2])<0.9 else np.array([1.,0,0]); u=np.cross(a,s); u/=np.linalg.norm(u); w=np.cross(s,u)
        g=(np.arange(N)+rng.random((N,N)))/N*2*R-R; gy=((np.arange(N)[:,None]+rng.random((N,N)))/N*2*R-R)
        P=g.ravel()[:,None]*u+gy.ravel()[:,None]*w; O=P+2*R*s; D=np.tile(-s,(len(O),1)); dA=(2*R/N)**2
        idx=np.concatenate([m.ray.intersects_first(O[i:i+20000],D[i:i+20000]) for i in range(0,len(O),20000)]); h=idx>=0; t=idx[h]; nn=n[t].copy(); c=nn@s; nn[c<0]*=-1; c=np.abs(c)
        # hit point: O + τ(−s), plane n·(x−v0)=0
        v0=V[t,0]; tau=np.einsum('ij,ij->i',n[t],O[h]-v0)/np.einsum('ij,j->i',n[t],s); r=O[h]-tau[:,None]*s - cm
        A=h.sum()*dA
        F=-((1-rs)*A*s + (2*rs*c[:,None]*nn).sum(0)*dA + 2/3*rd*nn.sum(0)*dA)
        M=-((1-rs)*np.cross(r,np.tile(s,(len(r),1))).sum(0)*dA + 2*rs*(c[:,None]*np.cross(r,nn)).sum(0)*dA + 2/3*rd*np.cross(r,nn).sum(0)*dA)
        Md=-np.cross(r.sum(0)*dA, s)   # drag with q·CD = 1
        out.append(dict(s=s.tolist(),A=A,F=F.tolist(),M=M.tolist(),Md=Md.tolist()))
    return out
dirs=[[0.3,-0.5,0.81],[-0.7,0.2,-0.3],[1,0,0],[0.1,0.95,0.2],[-0.2,-0.4,0.9]]
res={k:ref(k,dirs) for k in sys.argv[1:]}
json.dump(res,open('/tmp/sup_ref.json','w'))
for k,v in res.items():
    for e in v: print(k, np.round(e['s'],2), 'A %.3f'%e['A'], 'F', np.round(e['F'],3), 'M', np.round(e['M'],3))
