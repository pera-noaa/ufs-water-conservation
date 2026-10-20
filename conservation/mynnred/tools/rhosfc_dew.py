#!/usr/bin/env python3
"""mynnred: independent estimate of 01(a) rhosfc/rho1 - 1 (E-weighted) and 01(b) dew/E from history output.
usage: rhosfc_dew.py <run> <gridINPUTdir>
rho1 = p1/(Rd*T1*(1+0.608 q1)), p1 ~ ps - dpres1/2 ; rhosfc = ps/(Rd*(T1 + 0.608 q1)) (the code's typo).
E from lhtfl_ave (6-h means, fh 6..24); dew = the downward part."""
import sys
import numpy as np
from netCDF4 import Dataset

run, gdir = sys.argv[1:3]
area = []
for t in range(1, 7):
    with Dataset(f"{gdir}/C96_grid.tile{t}.nc") as g:
        s = np.asarray(g.variables["area"][:], dtype="f8")
    area.append(s[0::2, 0::2] + s[1::2, 0::2] + s[0::2, 1::2] + s[1::2, 1::2])
area = np.stack(area)
num = den = dew = 0.0
for fh in (6, 12, 18, 24):
    for t in range(1, 7):
        with Dataset(f"{run}/sfcf{fh:03d}.tile{t}.nc") as d:
            lh = np.asarray(d.variables["lhtfl_ave"][0], dtype="f8")
        with Dataset(f"{run}/atmf{fh:03d}.tile{t}.nc") as d:
            ps = np.asarray(d.variables["pressfc"][0], dtype="f8")
            # lowest model level = last index (pfull top-down)
            T1 = np.asarray(d.variables["tmp"][0, -1], dtype="f8")
            q1 = np.asarray(d.variables["spfh"][0, -1], dtype="f8")
            dp1 = np.asarray(d.variables["dpres"][0, -1], dtype="f8")
        p1 = ps - 0.5 * dp1
        r = (ps / (T1 + 0.608 * q1)) / (p1 / (T1 * (1 + 0.608 * q1)))
        a = area[t - 1]
        num += np.sum(a * lh * (r - 1)); den += np.sum(a * lh); dew += np.sum(a * np.maximum(0.0, -lh))
print(f"E-weighted rhosfc/rho1 - 1 = {num/den*100:.3f} %   dew (downward LH) / net E = {dew/den*100:.3f} %")
