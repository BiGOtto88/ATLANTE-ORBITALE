# Script di verifica usato per VALIDAZIONE.md (i percorsi /tmp sono quelli della prova: adattali).
import json,numpy as np
P=json.load(open('/tmp/val_page.json'))['pagina']; B=json.load(open('/tmp/basilisk.json')); res={}
# A
po=np.array(P['orbita']); br=np.array(B['orbita']['r']); bv=np.array(B['orbita']['v']); bt=np.array(B['orbita']['t'])
n=min(len(po),len(br)); dr=np.linalg.norm(po[:n,1:4]-br[:n],axis=1)*1000; dv=np.linalg.norm(po[:n,4:7]-bv[:n],axis=1)*1000
print('A orbit: times page(h)',np.round((po[:n,0]-po[0,0])*24,3)[[0,1,-1]],'bsk',bt[[0,1,n-1]]/3600)
print('A max |Δr| m %.4f  final %.4f ; max |Δv| mm/s %.4f'%(dr.max(),dr[-1],dv.max()*1000)); res['orbita']={'dr_max_m':dr.max(),'dr_fine_m':dr[-1],'dv_max_mm_s':dv.max()*1000}
# B
for i,(a,b) in enumerate(zip(P['gradiente'],B['gradiente'])):
    a=np.array(a); b=np.array(b); print('B gg case',i,a,b,'rel %.2e'%(np.linalg.norm(a-b)/np.linalg.norm(b)))
res['gradiente']=[float(np.linalg.norm(np.array(a)-np.array(b))/np.linalg.norm(b)) for a,b in zip(P['gradiente'],B['gradiente'])]
# C
res['facce']=[]
for i,(a,b) in enumerate(zip(P['facce'],B['facce'])):
    r={}
    for k in ['Fdrag_B','Mdrag_B','Fsrp_B_su_P','Msrp_B_su_P']:
        x=np.array(a[k]); y=np.array(b[k]); r[k]=float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30)); print('C',i,k,np.round(x,9),np.round(y,9),'rel %.2e'%r[k])
    res['facce'].append(r)
json.dump(res,open('/tmp/val_res.json','w'),indent=1)
