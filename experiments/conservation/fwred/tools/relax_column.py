#!/usr/bin/env python3
"""Red-team check, independent of encpl/tools/column_fw.py: no energy-conservation shortcut.
1-D compressible Lagrangian column (layers = fixed mass, gas EOS p = (md Rd + mv Rv) T / dz, liquid has weight
but no volume), explicit acoustic integration with Rayleigh damping of w (damped KE optionally returned as heat).
Condense dm of vapour in layer k and compare the RELAXED temperature for:
  ISO : isobaric truth, layer enthalpy conserved with Kirchhoff-consistent h (h_v = cpv T + Lv00, h_l = cl T)
  CVL : fixed volume, internal-energy latent heat (u_v = cvv T + Lv00), then dynamic relaxation
  FV3 : fixed volume, physics heat hvap*dm (isobaric enthalpy latent heat) put into U, then dynamic relaxation
  FV3P: as FV3 but the vapour is removed from the layer (precipitated) at fixed dz; rain leaves (no PE/sensible terms)
  ISOP: isobaric truth for removal: layer loses dm carrying h_v(T) (vapour leaves with its enthalpy), heat hvap*dm
        minus ... -> see text; we compare FV3P against CVLP (removed vapour carries u_v, U gets L_e*dm) relaxed."""
import numpy as np, sys
g, Rd, Rv, cpd, cpv, cl, hv, T0 = 9.80665, 287.05, 461.5, 1004.6, 1846.0, 4185.5, 2.5e6, 273.15
cvd, cvv = cpd - Rd, cpv - Rv
Lv00 = hv - (cpv - cl) * T0
N, pt_, ps = 30, 2.0e4, 1.0e5
dpl = np.full(N, (ps - pt_) / N)
m = dpl / g                                            # layer total mass, top->bottom
k = 20
pmid0 = pt_ + np.cumsum(dpl) - dpl / 2
T = 288.0 - 6.5e-3 * 7000 * np.log(ps / pmid0) / np.log(2)  # rough profile
T = np.clip(T, 230, 300); T[k] = T0
qv = 0.01 * (pmid0 / ps) ** 3
mv = qv * m; ml = np.zeros(N); md = m - mv
ret = (sys.argv[1] if len(sys.argv) > 1 else "heat") == "heat"

def hydro(md, mv, ml, T):
    mm = md + mv + ml
    p = np.empty(N); p[0] = pt_ + g * mm[0] / 2
    for i in range(1, N): p[i] = p[i-1] + g * (mm[i-1] + mm[i]) / 2
    return p, (md * Rd + mv * Rv) * T / p

def relax(md, mv, ml, T, dz, nsteps=240000, dt=0.025, alpha=0.02):
    """interfaces zi[0]=top ... zi[N]=0 (ground). w at interfaces 0..N-1 (ground fixed)."""
    mm = md + mv + ml; nR = md * Rd + mv * Rv; cv = md * cvd + mv * cvv + ml * cl
    T = T.copy(); dz = dz.copy(); w = np.zeros(N)
    mi = np.empty(N); mi[0] = mm[0] / 2; mi[1:] = (mm[:-1] + mm[1:]) / 2   # interface masses
    def energy(T, dz, w):
        zi = np.concatenate([np.cumsum(dz[::-1])[::-1], [0.0]])
        zm = 0.5 * (zi[:-1] + zi[1:])
        return np.sum(cv * T) + np.sum(mm * g * zm) + 0.5 * np.sum(mi * w**2) + pt_ * zi[0]
    E0 = energy(T, dz, w)
    for it in range(nsteps):
        p = nR * T / dz
        pabove = np.concatenate([[pt_], p[:-1]])
        f = p - pabove - g * mi                       # net upward force on interface i (top of layer i)
        w += dt * f / mi
        ke0 = 0.5 * mi * w**2
        w *= (1 - alpha * dt)
        dke = ke0 - 0.5 * mi * w**2                  # dissipated KE
        # interface i is top of layer i and bottom of layer i-1
        wbot = np.concatenate([w[1:], [0.0]])
        ddz = dt * (w - wbot)
        T *= (dz / (dz + ddz)) ** (nR / cv)        # exact reversible adiabat at fixed composition
        dz += ddz
        if ret:                                      # return dissipated KE as heat (half to each adjacent layer)
            q = 0.5 * dke; T += q / cv; T[:-1] += q[1:] / cv[:-1]; T[0] += q[0] / cv[0]
    return T, dz, (energy(T, dz, w) - E0), np.max(abs(w))

p0, dz0 = hydro(md, mv, ml, T)
# sanity: the initial state is in discrete equilibrium
Tr, dzr, dE, wm = relax(md, mv, ml, T, dz0, nsteps=2000)
print(f"equilibrium check: max|dT|={np.max(abs(Tr-T)):.2e} K")
dm = 1e-3 * m[k]
mv1 = mv.copy(); mv1[k] -= dm; ml1 = ml.copy(); ml1[k] += dm
cvk1 = md[k] * cvd + mv1[k] * cvv + ml1[k] * cl
cpk1 = md[k] * cpd + mv1[k] * cpv + ml1[k] * cl
Lh = hv + (cpv - cl) * (T0 - T0)
Le = Lh - Rv * T0
# ISO: H = sum m h conserved at fixed p
T_iso = T0 + Lh * dm / cpk1
# CVL: U conserved at fixed volume -> U' = U0, composition changed
Tc = T.copy(); Tc[k] = T0 + Le * dm / cvk1
T_cvl, _, dE1, w1 = relax(md, mv1, ml1, Tc, dz0)
# FV3: pt += cp/cv * (hvap*dm/cp_phys) i.e. U gets hvap*dm
Tf = T.copy(); Tf[k] = T0 + hv * dm / cvk1
T_fv3, _, dE2, w2 = relax(md, mv1, ml1, Tf, dz0)
# FV3P: vapour removed at fixed dz, same physics heat hvap*dm into U of the remaining mass
cvk2 = md[k] * cvd + mv1[k] * cvv
Tp = T.copy(); Tp[k] = T0 + hv * dm / cvk2
T_fv3p, _, dE3, w3 = relax(md, mv1, ml, Tp, dz0)
# CVLP: vapour leaves at fixed volume carrying its enthalpy h_v (open system dU = -h_v dm_out), condensation
# heat is internal: equivalently liquid leaves carrying u_l=h_l (no volume) after condensing with L_e at fixed V
Tq = T.copy(); Tq[k] = T0 + Le * dm / cvk2      # U(remaining) = U0 - u_l*dm  (u_l=h_l: liquid leaves)
T_cvlp, _, dE4, w4 = relax(md, mv1, ml, Tq, dz0)
cpk2 = md[k] * cpd + mv1[k] * cpv
T_isop = T0 + Lh * dm / cpk2                      # isobaric: H(remaining) = H0 - h_l*dm
print(f"layer {k}: p={p0[k]:.0f} Pa, dm={dm:.4f} kg/m2, Rv*T0={Rv*T0:.4e} J/kg, damped KE returned as heat: {ret}")
print(f"energy drift (J/m2): CVL {dE1:.2e} FV3 {dE2:.2e} FV3P {dE3:.2e}; max|w| end {max(w1,w2,w3):.1e}")
d = lambda Tx: Tx - T0
print(f"liquid stays : ISO dT={T_iso-T0:.5f}  CVL relaxed dT={d(T_cvl[k]):.5f}  FV3 relaxed dT={d(T_fv3[k]):.5f}")
print(f"   FV3-CVL excess per kg condensed (H-equiv) = {(T_fv3[k]-T_cvl[k])*cpk1/dm:.4e} J/kg; "
      f"other layers max|FV3-CVL| {np.max(abs(np.delete(T_fv3-T_cvl,k))):.1e} K")
print(f"   CVL vs ISO: {(T_cvl[k]-T_iso)*cpk1/dm:+.3e} J/kg")
print(f"precip out   : ISOP dT={T_isop-T0:.5f}  CVLP relaxed dT={d(T_cvlp[k]):.5f}  FV3P relaxed dT={d(T_fv3p[k]):.5f}")
print(f"   FV3P-CVLP excess = {(T_fv3p[k]-T_cvlp[k])*cpk2/dm:.4e} J/kg; CVLP vs ISOP {(T_cvlp[k]-T_isop)*cpk2/dm:+.3e} J/kg")
