#!/usr/bin/env python3
"""Offline estimate of MYNN's surface-vapour-flux excess: mynn_tendencies applies rhosfc*qfx/rho1 per unit area, not qfx.
rhosfc = psfc/(Rd*(T1 + p608*q1)) [module_bl_mynn.F90 L4137], rho1 = prsl1/(Rd*T1*(1+p608*q1)) [mynnedmf_wrapper.F90 L610].
Per window: X = sum_col E_col*(rhosfc/rho1 - 1)*area / area_tot, factor averaged over the window's two snapshots.
Also prints the layer-1 mass ratio g*rho1*|delz1|/delp1 (E-weighted). Usage: mynn_rhosfc_offline.py <rundir>"""
import glob, sys
import numpy as np
from netCDF4 import Dataset
rd = sys.argv[1]; G, HVAP, FV, RD = 9.80665, 2.5e6, 0.60776, 287.05
def v(d, n): return np.asarray(d[n][:], float).squeeze()
A = {}
for t in range(1, 7):
    a = v(Dataset(glob.glob(f"{rd}/INPUT/C*_grid.tile{t}.nc")[0]), "area")
    A[t] = a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
atot = sum(a.sum() for a in A.values())
def fac(fh, t):
    d = Dataset(f"{rd}/atmf{fh:03d}.tile{t}.nc")
    ps = v(d, "pressfc"); T = v(d, "tmp")[-1]; q = v(d, "spfh")[-1]
    cond = sum(v(d, k)[-1] for k in ("clwmr", "icmr", "rwmr", "snmr", "grle"))
    dp = v(d, "dpres")[-1] / (1 - cond)
    prsl = dp / np.log(ps / (ps - dp))
    rho1 = prsl / (RD * T * (1 + FV * q)); rhosfc = ps / (RD * (T + FV * q))
    return rhosfc / rho1 - 1, G * rho1 * abs(v(d, "delz")[-1]) / dp - 1
print("window | E (kg/m2) | X=excess (kg/m2) | X/E | E-weighted (rhosfc/rho1-1) | E-wtd (g rho1 dz1/delp1 - 1)")
for fh in range(6, 25, 6):
    E = X = M = 0.0
    for t in range(1, 7):
        e = v(Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc"), "lhtfl_ave") / HVAP * 6 * 3600
        f0, m0 = fac(fh - 6, t); f1, m1 = fac(fh, t)
        E += (e * A[t]).sum(); X += (e * 0.5 * (f0 + f1) * A[t]).sum(); M += (e * 0.5 * (m0 + m1) * A[t]).sum()
    print(f"{fh-6:3d}-{fh:3d} | {E/atot:.5f} | {X/atot:+.5f} | {100*X/E:+.3f}% | {X/E:+.5f} | {M/E:+.5f}")
