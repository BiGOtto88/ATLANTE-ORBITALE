# Script di verifica usato per VALIDAZIONE.md (i percorsi /tmp sono quelli della prova: adattali).
import json, numpy as np, warnings; warnings.filterwarnings('ignore')
from skyfield.api import load, EarthSatellite, wgs84, Loader
from skyfield_data import get_skyfield_data_path
d=json.load(open('/tmp/pass_pg.json'))
L=Loader(get_skyfield_data_path()); eph=L('de421.bsp'); ts=load.timescale(builtin=True); obs=wgs84.latlon(41.9,12.5,elevation_m=50); sun=eph['sun']; earth=eph['earth']
mx={'r':0,'m':0,'s':0,'el':0}; visok=0; vistot=0
for no in ['25544','20580']:
    v=d[no]; sat=EarthSatellite(v['l1'],v['l2'],'x',ts); t0=ts.utc(1970,1,1,0,0,v['ms']/1000); t1=ts.utc(1970,1,1,0,0,v['ms']/1000+3*86400)
    t,ev=sat.find_events(obs,t0,t1,altitude_degrees=10.0); ps=[]; cur={}
    for ti,e in zip(t,ev):
        if e==0: cur={'rise':ti}
        elif e==1: cur['max']=ti
        else: cur['set']=ti; ps.append(cur); cur={}
    print(no,'page',len(v['list']),'skyfield',len(ps))
    for p,q in zip(v['list'],ps):
        tr=q['rise'].utc_datetime().timestamp(); tm=q['max'].utc_datetime().timestamp(); tset=q['set'].utc_datetime().timestamp()
        alt=(sat-obs).at(q['max']).altaz()[0].degrees
        # visibility by skyfield: sample every 10 s
        tt=ts.utc(1970,1,1,0,0,np.arange(tr,tset,10.0)); lit=sat.at(tt).is_sunlit(eph); sa=(earth+obs).at(tt).observe(sun).apparent().altaz()[0].degrees; vis=bool(np.any(lit&(sa<-6)))
        vistot+=1; visok+= (vis==p['vis'])
        for k,a,b in [('r',p['t0']/1000,tr),('m',p['tm']/1000,tm),('s',p['t1']/1000,tset)]: mx[k]=max(mx[k],abs(a-b))
        mx['el']=max(mx['el'],abs(p['el']-alt))
        print('  %s Δrise %+.2f s Δmax %+.2f s Δset %+.2f s el %.2f/%.2f vis %s/%s mag %s'%(q['rise'].utc_strftime('%m-%d %H:%M'),p['t0']/1000-tr,p['tm']/1000-tm,p['t1']/1000-tset,p['el'],alt,p['vis'],vis,p['mag']))
print('max diffs',mx,'visibility agreement %d/%d'%(visok,vistot))
