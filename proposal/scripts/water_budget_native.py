#!/usr/bin/env python3
"""Global water budget on native C96 tiles: dW (6 species, sum q*dpres/g) vs (E - P)*6h per 6-h window.
Usage: python3 water_budget_native.py <RUNDIR>   (needs sfcfHHH.tileN.nc, atmfHHH.tileN.nc, INPUT/C96_grid.tileN.nc)"""
import sys
import numpy as np
from netCDF4 import Dataset

RD = sys.argv[1]
G, HVAP, DT = 9.80665, 2.5e6, 6 * 3600.0
SPECIES = ["spfh", "clwmr", "icmr", "rwmr", "snmr", "grle"]


def area(t):
    a = np.asarray(Dataset(f"{RD}/INPUT/C96_grid.tile{t}.nc")["area"][:], float)
    return a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]


A = {t: area(t) for t in range(1, 7)}
ATOT = sum(a.sum() for a in A.values())


def gmean2d(fh, var, scale=1.0):
    s = 0.0
    for t in range(1, 7):
        x = np.asarray(Dataset(f"{RD}/sfcf{fh:03d}.tile{t}.nc")[var][:], float).squeeze()
        s += (x * A[t]).sum()
    return s / ATOT * scale


def water(fh):
    s = 0.0
    for t in range(1, 7):
        d = Dataset(f"{RD}/atmf{fh:03d}.tile{t}.nc")
        dp = np.asarray(d["dpres"][:], float).squeeze()
        q = sum(np.asarray(d[v][:], float).squeeze() for v in SPECIES)
        # output dpres is delp*(1 - condensate), the physics' dry+vapour thickness (fv_nggps_diag.F90, GFS_PHYS); q is per total mass
        dp = dp / (1.0 - (q - np.asarray(d[SPECIES[0]][:], float).squeeze()))
        s += ((q * dp).sum(axis=0) / G * A[t]).sum()
    return s / ATOT


print(f"earth area check: {ATOT:.6e} m2 (4*pi*R^2 = {4*np.pi*6.371e6**2:.6e})")
W = {fh: water(fh) for fh in (0, 6, 12, 18, 24)}
print("fh   W_native(kg/m2)")
for fh, w in W.items():
    print(f"{fh:3d}  {w:.6f}")
print("window   P*6h      E*6h      (E-P)*6h   dW        residual  resid/P")
for fh in (6, 12, 18, 24):
    P = gmean2d(fh, "prateb_ave") * DT  # bucket; prate_ave averages since forecast start
    E = gmean2d(fh, "lhtfl_ave", 1.0 / HVAP) * DT
    dW = W[fh] - W[fh - 6]
    r = dW - (E - P)
    print(f"{fh-6:2d}-{fh:2d}   {P:.5f}  {E:.5f}  {E-P:+.5f}  {dW:+.5f}  {r:+.5f}  {100*r/P:+.2f}%")
