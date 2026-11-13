#!/usr/bin/env python3
"""1-D column: 1 g/kg of vapour condensed in one layer at T = T0 (Kirchhoff term zero), FV3 frame
E_F = sum m*(cvm*T + phi_mid) + Lv00*m_v, delz hydrostatic in FV3's form delz = -(Rm*T/g)*ln(pe_bot/pe_top),
Rm per total mass (condensate has no R). Every final state is hydrostatic with interface pressures fixed by
the masses; E_F is the quantity FV3's dynamics (+ consv_te fixer) conserves.
 (i)   physical, isobaric: closed column, E_F conserved -> solve T_k  [a: liquid stays; b: liquid falls out,
       leaving at the surface with c_l*T1 + phis, PE dissipated in the layers it crosses]
 (ii)  FV3 path: physics heats hvap*dm (cp_air*dT*m_p, CP1) into IE at fixed volume; write changes composition
       (a) or removes the vapour mass (b) at fixed delz; E_F after the write is conserved by the relaxation
       -> solve T_k of the relaxed hydrostatic column (b: same heat placement as (i) for PE/sensible)."""
import numpy as np
from scipy.optimize import brentq

g, Rd, Rv, cpd, cpv, cl, ci, hv, T0 = 9.80665, 287.05, 461.5, 1004.6, 1846.0, 4185.5, 1972.0, 2.5e6, 273.15
cvd, cvv = cpd - Rd, 3 * Rv
Lv00 = hv - (cpv - cl) * T0
N, ps, pt = 40, 1.0e5, 1.0e3
pe = np.linspace(pt, ps, N + 1)                       # interfaces, top -> bottom
dp = np.diff(pe)
T = 300.0 - 70.0 * (1 - (pe[:-1] + pe[1:]) / 2 / ps)  # K
k = int(np.argmin(abs((pe[:-1] + pe[1:]) / 2 - 7.5e4)))
qv = 0.012 * ((pe[:-1] + pe[1:]) / 2 / ps) ** 3
mt = dp / g
mv, ml, md = qv * mt, np.zeros(N), (1 - qv) * mt
T[k] = T0


def EF(md, mv, ml, T, phis=0.0):
    m = md + mv + ml
    pei = pt + np.concatenate([[0], np.cumsum(m * g)])
    Rm = (md * Rd + mv * Rv) / m
    dz = Rm * T / g * np.log(pei[1:] / pei[:-1])
    phib = phis + g * np.concatenate([np.cumsum(dz[::-1])[::-1], [0]])
    phim = 0.5 * (phib[:-1] + phib[1:])
    return float(np.sum(md * cvd * T + mv * cvv * T + ml * cl * T + m * phim + Lv00 * mv)), phim, dz


E0, phim0, dz0 = EF(md, mv, ml, T)
dm = 1e-3 * md[k]                                     # 1 g/kg (dry) condensed
print(f"layer {k}: p={(pe[k]+pe[k+1])/2:.0f} Pa T={T[k]} K m={mt[k]:.2f} kg/m2 dm={dm:.4f} kg/m2")
cpm = (md[k] * cpd + (mv[k] - dm) * cpv + dm * cl) / mt[k]


def solveT(E_target, md_, mv_, ml_, Tb):
    def f(x):
        TT = Tb.copy(); TT[k] = x
        return EF(md_, mv_, ml_, TT)[0] - E_target
    return brentq(f, 200, 400)


# (i)a physical, liquid stays
mv1, ml1 = mv.copy(), ml.copy(); mv1[k] -= dm; ml1[k] += dm
Ti = solveT(E0, md, mv1, ml1, T)
# (ii)a FV3: E after write = E0 + hvap*dm + composition change at fixed volume (phi, delz unchanged)
Ew = E0 + hv * dm + dm * (cl - cvv) * T[k] - Lv00 * dm
Tii = solveT(Ew, md, mv1, ml1, T)
Lh = hv + (cpv - cl) * (T[k] - T0)
print("(a) liquid stays in the layer")
print(f"  physical: dT={Ti-T0:+.5f} K -> heat (H-equivalent) {(Ti-T0)*mt[k]*cpm/dm:.6e} J/kg  (L_h(T)={Lh:.6e})")
print(f"  FV3     : dT={Tii-T0:+.5f} K -> {(Tii-T0)*mt[k]*cpm/dm:.6e} J/kg;  excess {(Tii-Ti)*mt[k]*cpm/dm:.6e} J/kg"
      f"  vs Rv*T = {Rv*T0:.6e}")
print(f"  E_F(write) - E_F(physical) = {(Ew-E0)/dm:.6e} J/kg")
# fixed-volume write with no relaxation: layer pressure drop vs hydrostatic
# (b) vapour removed (precipitated). Physical: E_F = E0 - dm*(cl*T1 + phis); heat for PE and sensible exchange
# is put in layer k too (both paths identical in placement), so the comparison isolates the latent/R_v term.
mv2 = mv.copy(); mv2[k] -= dm
T1 = T[-1]
Eb_phys = E0 - dm * (cl * T1 + 0.0)
Tb_i = solveT(Eb_phys, md, mv2, ml, T)
Ew2 = E0 + hv * dm - dm * (cvv * T[k] + Lv00 + phim0[k])            # FV3 write
Ew2_bits = Ew2 + dm * phim0[k] + dm * cl * (T[k] - T1)              # + PE bit + sensible bit (both into layer k here)
Tb_ii = solveT(Ew2, md, mv2, ml, T)
Tb_iib = solveT(Ew2_bits, md, mv2, ml, T)
print("(b) vapour condensed and precipitated out")
print(f"  physical: E_F change {(Eb_phys-E0)/dm:+.6e} J/kg   T_k {Tb_i:.5f}")
print(f"  FV3, no bits     : E_F change {(Ew2-E0)/dm:+.6e} J/kg T_k {Tb_ii:.5f}  excess vs physical {(Ew2-Eb_phys)/dm:+.6e}")
print(f"  FV3, PE+S bits   : excess {(Ew2_bits-Eb_phys)/dm:+.6e} J/kg (Rv*T={Rv*T0:.6e});  "
      f"+FW bit: {(Ew2_bits - Rv*T[k]*dm - Eb_phys)/dm:+.3e}")
# MPAS-style: internal-energy latent heat at fixed volume, then relaxation
Le = Lh - Rv * T[k]
Ew3 = E0 + Le * dm + dm * (cl - cvv) * T[k] - Lv00 * dm
print(f"  MPAS-style (L_h - Rv*T at fixed volume), liquid stays: E_F(write) - E_F(physical) = {(Ew3-E0)/dm:+.3e} J/kg")
