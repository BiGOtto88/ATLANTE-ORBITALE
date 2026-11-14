// Casi di confronto calcolati dalla pagina (da eseguire nella pagina di prova con l'aggancio window.__dbg, vedi VALIDAZIONE.md).
// Restituisce {casi, pagina}: casi va dato a basilisk_confronto.py, pagina sono i risultati della pagina sugli stessi dati.
(async ()=>{ const D=__dbg, d2r=Math.PI/180;
 const mrp2A=s=>{ const s2=s[0]*s[0]+s[1]*s[1]+s[2]*s[2], X=[[0,-s[2],s[1]],[s[2],0,-s[0]],[-s[1],s[0],0]], A=[], k=1/((1+s2)*(1+s2));
   for(let i=0;i<3;i++) for(let j=0;j<3;j++){ let x2=0; for(let q=0;q<3;q++) x2+=X[i][q]*X[q][j]; A.push((i===j?1:0)+k*(8*x2-4*(1-s2)*X[i][j])); } return A; };   // dcm_BN di Basilisk
 const casi={}, pag={};
 // A. orbita
 const r0=[6798.137,0,0], vc=Math.sqrt(398600.4418/6798.137), v0=[0,vc*Math.cos(51.6*d2r),vc*Math.sin(51.6*d2r)];
 casi.orbita={mu:398600.4418,R:6378.137,J:[1.08262668e-3,-2.53265649e-6,-1.61962159e-6],r:r0,v:v0,giorni:1};
 const fake={cd:2.2,m:100,rs:0.3,shape:null,faces:[{n:[1,0,0],A:1,rs:0.3,rd:0.1}]}, C=D.evoCtx('earth',2461358.5,fake,'free','mean'); C.th=[]; C.BA=0; C.CRA=0; C.mu=398600.4418; C.R=6378.137; C.J=casi.orbita.J;
 const t0=performance.now(); pag.orbita=D.evoCowell(C,r0,v0,2461358.5,1,1,3600); pag.orbita_ms=performance.now()-t0;
 // B. gradiente di gravità
 const J=[1200,-35,22,-35,900,18,22,18,1500]; casi.gradiente={J,mu:398600.4418,casi:[]}; pag.gradiente=[];
 const env=D.env, G=env.G, T={gg:[0,0,0],drag:[0,0,0],srp:[0,0,0],srpE:[0,0,0],mag:[0,0,0],tot:[0,0,0],fDrag:[0,0,0],fRad:[0,0,0]}, sc={J,faces:[],cd:2.2,rs:0.3,mdip:[0,0,0],shape:null};
 for(const [r,s] of [[[7000,0,0],[0.1,0.2,0.3]],[[-3000,5000,4000],[-0.4,0.1,0.25]],[[42164*0.6,42164*0.8,0],[0.05,-0.3,0.6]]]){
   casi.gradiente.casi.push({r,v:[0,7,0],sigma:s}); for(let i=0;i<9;i++) G[i]=0; D.addPoint(G,398600.4418,r[0],r[1],r[2]); G[3]=G[1]; G[6]=G[2]; G[7]=G[5];   // addPoint fills the upper triangle, as in gravGrad
   env.rho=0; env.P=0; env.Pir=0; env.Pal=0; env.hasB=false; D.torques(sc,mrp2A(s),T); pag.gradiente.push(T.gg.slice()); }
 // C. facce piane
 const box=D.scModel({t:'probe',p:{type:'des',cls:'mini',id:'val'}}), faces=box.faces.map(f=>({n:f.n,A:f.A,r:f.r,rs:f.rs,rd:f.rd}));
 casi.facce={cd:box.cd,faces,casi:[]}; pag.facce=[]; const sc2={J,faces:box.faces,cd:box.cd,rs:box.rs,mdip:[0,0,0],shape:null};
 for(const [v,s,sun] of [[[0,7.6,0.4],[0.1,-0.2,0.05],[1.2e8,8e7,3e7]],[[-5.2,4.1,2.8],[0.3,0.3,-0.2],[-9e7,1.1e8,4.5e7]],[[1.0,-7.3,1.5],[-0.15,0.05,0.4],[3e7,-1.4e8,-6e7]]]){
   const r=[6800,500,-300], rho=3e-12; casi.facce.casi.push({r,v,sigma:s,rho,sole:sun});
   for(let i=0;i<9;i++) G[i]=0; env.rho=rho; env.vr[0]=v[0]*1000; env.vr[1]=v[1]*1000; env.vr[2]=v[2]*1000;
   const d=Math.hypot(sun[0]-r[0],sun[1]-r[1],sun[2]-r[2]); env.sun[0]=(sun[0]-r[0])/d; env.sun[1]=(sun[1]-r[1])/d; env.sun[2]=(sun[2]-r[2])/d; env.P=1; env.Pir=0; env.Pal=0; env.hasB=false;
   D.torques(sc2,mrp2A(s),T); pag.facce.push({Fdrag_B:T.fDrag.slice(),Mdrag_B:T.drag.slice(),Fsrp_B_su_P:T.fRad.slice(),Msrp_B_su_P:T.srp.slice()}); }
 return {casi,pagina:pag}; })()
