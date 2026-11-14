# Script di verifica usato per VALIDAZIONE.md (i percorsi /tmp sono quelli della prova: adattali).
import numpy as np, pymsis, json, subprocess, datetime as dt
rng=np.random.default_rng(3); n=300
doy=rng.integers(1,366,n); sec=rng.uniform(0,86400,n); alt=rng.uniform(80,1000,n); lat=rng.uniform(-89,89,n); lon=rng.uniform(-180,180,n)
f107=rng.uniform(65,250,n); f107a=f107+rng.uniform(-20,20,n); ap=rng.uniform(0,80,n)
ref=[]
for i in range(n):
    d=np.datetime64('2023-01-01')+np.timedelta64(int(doy[i])-1,'D')+np.timedelta64(int(sec[i]*1e6),'us')
    out=pymsis.calculate(d,lon[i],lat[i],alt[i],f107s=[f107[i]],f107as=[f107a[i]],aps=[[ap[i]]*7],version=0)
    ref.append(float(np.squeeze(out)[pymsis.Variable.MASS_DENSITY]))
inp=[[int(doy[i]),float(int(sec[i]*1e6)/1e6),float(alt[i]),float(lat[i]),float(lon[i]),float(f107a[i]),float(f107[i]),float(ap[i])] for i in range(n)]
js=subprocess.run(['node','-e',"const M=require('./msis.js'); const I=JSON.parse(require('fs').readFileSync(0)); console.log(JSON.stringify(I.map(a=>{const o=M.run(...a); return [o.d[5]*1000, M.gtd7?0:0];})))"],input=json.dumps(inp),capture_output=True,text=True)
mine=[r[0] for r in json.loads(js.stdout)]
bad=[i for i,m in enumerate(mine) if m is None]
print('NaN cases',len(bad), [inp[i] for i in bad[:3]])
mine=[m if m is not None else float('nan') for m in mine]
rel=np.abs(np.array(mine)-np.array(ref))/np.array(ref)
rel=rel[~np.isnan(rel)]
print('max rel diff gtd7d vs pymsis v0:',rel.max(),' median',np.median(rel))
i=int(rel.argmax()); print(inp[i], mine[i], ref[i])
