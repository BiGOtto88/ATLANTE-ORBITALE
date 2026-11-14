"""Confronto di Atlante Orbitale con Basilisk (AVS Lab, University of Colorado; licenza ISC).

Calcola con Basilisk 2.12 gli stessi casi che la pagina calcola nel browser e scrive basilisk.json:
  A. orbita bassa per un giorno con gravità della Terra fino a J4 (armoniche zonali EGM2008), integratore RK4 a 1 s;
  B. coppia da gradiente di gravità (GravityGradientEffector) con inerzia piena e assetto generico;
  C. forze e coppie di resistenza (FacetDragDynamicEffector) e di pressione di radiazione (FacetSRPDynamicEffector)
     su un veicolo a facce piane (parallelepipedo con due ali, come il modello schematico della pagina).
Uso:  python3 basilisk_confronto.py casi.json basilisk.json
casi.json viene dalla pagina (strumenti/validazione/casi_pagina.js), così i dati d'ingresso sono gli stessi."""
import json, sys, os, tempfile
import numpy as np
from Basilisk.simulation import spacecraft, GravityGradientEffector, facetDragDynamicEffector, facetSRPDynamicEffector
from Basilisk.utilities import SimulationBaseClass, macros, simIncludeGravBody, RigidBodyKinematics as rbk
from Basilisk.architecture import messaging

casi = json.load(open(sys.argv[1]))
out = {}

def sim_base(r, v, J, sigma, dt=1.0):
    S = SimulationBaseClass.SimBaseClass(); P = S.CreateNewProcess('p'); P.addTask(S.CreateNewTask('t', macros.sec2nano(dt)))
    sc = spacecraft.Spacecraft(); sc.ModelTag = 'sc'; sc.hub.mHub = 1000.0
    sc.hub.IHubPntBc_B = np.array(J).reshape(3, 3).tolist(); sc.hub.r_BcB_B = [[0.0], [0.0], [0.0]]
    sc.hub.r_CN_NInit = (np.array(r) * 1000).tolist(); sc.hub.v_CN_NInit = (np.array(v) * 1000).tolist()
    sc.hub.sigma_BNInit = [[sigma[0]], [sigma[1]], [sigma[2]]]; sc.hub.omega_BN_BInit = [[0.0], [0.0], [0.0]]
    S.AddModelToTask('t', sc)
    return S, sc

# ---- A. orbita con J2–J4 ----
A = casi['orbita']; mu = A['mu'] * 1e9; R = A['R'] * 1000
f = tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False)
f.write(f"{R},{mu},0,4,4,1,0,0\n")
C = {2: -A['J'][0] / np.sqrt(5), 3: -A['J'][1] / np.sqrt(7), 4: -A['J'][2] / 3.0}   # Jn → C̄n0 normalizzato
for n in range(0, 5):
    for m in range(0, n + 1):
        f.write(f"{n},{m},{(1.0 if (n, m) == (0, 0) else C.get(n, 0.0) if m == 0 else 0.0)},0,0,0\n")
f.close()
S, sc = sim_base(A['r'], A['v'], np.eye(3).ravel() * 100, [0, 0, 0], dt=1.0)
gf = simIncludeGravBody.gravBodyFactory(); earth = gf.createEarth(); earth.isCentralBody = True
earth.useSphericalHarmonicsGravityModel(f.name, 4); earth.mu = mu
gf.addBodiesTo(sc)
rec = sc.scStateOutMsg.recorder(macros.sec2nano(3600.0)); S.AddModelToTask('t', rec)
S.InitializeSimulation(); S.ConfigureStopTime(macros.sec2nano(A['giorni'] * 86400)); S.ExecuteSimulation()
out['orbita'] = {'t': (rec.times() * 1e-9).tolist(), 'r': (rec.r_BN_N / 1000).tolist(), 'v': (rec.v_BN_N / 1000).tolist()}
os.unlink(f.name)

# ---- B. gradiente di gravità ----
B = casi['gradiente']; out['gradiente'] = []
for c in B['casi']:
    S, sc = sim_base(c['r'], c['v'], B['J'], c['sigma'])
    gf = simIncludeGravBody.gravBodyFactory(); e = gf.createEarth(); e.isCentralBody = True; e.mu = B['mu'] * 1e9; gf.addBodiesTo(sc)
    gg = GravityGradientEffector.GravityGradientEffector(); gg.ModelTag = 'gg'; gg.addPlanetName(e.planetName); sc.addDynamicEffector(gg); S.AddModelToTask('t', gg)
    rec = gg.gravityGradientOutMsg.recorder(); S.AddModelToTask('t', rec)
    S.InitializeSimulation(); S.ConfigureStopTime(0); S.ExecuteSimulation()
    out['gradiente'].append(list(rec.gravityGradientTorque_B[-1]))

# ---- C. facce piane: resistenza e radiazione ----
Cc = casi['facce']; out['facce'] = []
for c in Cc['casi']:
    S, sc = sim_base(c['r'], c['v'], np.eye(3).ravel() * 100, c['sigma'])
    dr = facetDragDynamicEffector.FacetDragDynamicEffector(); dr.ModelTag = 'drag'
    for fc in Cc['faces']: dr.addFacet(fc['A'], Cc['cd'], fc['n'], fc['r'])
    atm = messaging.AtmoPropsMsgPayload(); atm.neutralDensity = c['rho']; am = messaging.AtmoPropsMsg().write(atm); dr.atmoDensInMsg.subscribeTo(am)
    sc.addDynamicEffector(dr); S.AddModelToTask('t', dr)
    sr = facetSRPDynamicEffector.FacetSRPDynamicEffector(); sr.ModelTag = 'srp'; sr.setNumFacets(len(Cc['faces'])); sr.setNumArticulatedFacets(0)
    for fc in Cc['faces']: sr.addFacet(fc['A'], np.eye(3).tolist(), fc['n'], [0.0, 0.0, 1.0] if abs(fc['n'][2]) < 0.9 else [1.0, 0.0, 0.0], fc['r'], fc['rd'], fc['rs'])
    sun = messaging.SpicePlanetStateMsgPayload(); sun.PositionVector = (np.array(c['sole']) * 1000).tolist(); sm = messaging.SpicePlanetStateMsg().write(sun); sr.sunInMsg.subscribeTo(sm)
    sc.addDynamicEffector(sr); S.AddModelToTask('t', sr)
    S.InitializeSimulation(); S.ConfigureStopTime(0); S.ExecuteSimulation()
    dr.computeForceTorque(0.0, 0.0); sr.computeForceTorque(0.0, 0.0)
    d = np.linalg.norm(np.array(c['sole']) * 1000 - np.array(c['r']) * 1000); AUm = 149597870693.0
    P = 1368.0 / 299792458.0 * (AUm / d) ** 2      # flusso solare usato da FacetSRPDynamicEffector (1368 W/m²), AU di Basilisk
    out['facce'].append({'Fdrag_B': list(np.array(dr.forceExternal_B).ravel()), 'Mdrag_B': list(np.array(dr.torqueExternalPntB_B).ravel()),
                         'Fsrp_B_su_P': list(np.array(sr.forceExternal_B).ravel() / P), 'Msrp_B_su_P': list(np.array(sr.torqueExternalPntB_B).ravel() / P)})
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print('scritto', sys.argv[2])
