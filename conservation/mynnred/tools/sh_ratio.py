#!/usr/bin/env python3
"""mynnred: 04 check, SH-weighted ratio applied/reported = exner1*cp/cpm = exner1/(1+0.84 q1). usage: sh_ratio.py <run> <grid dir>"""
import sys
import numpy as np
from netCDF4 import Dataset
run, gdir = sys.argv[1:3]
num = den = 0.0
for t in range(1, 7):
    with Dataset(f"{gdir}/C96_grid.tile{t}.nc") as g:
        s = np.asarray(g.variables["area"][:], dtype="f8")
    a = s[0::2, 0::2] + s[1::2, 0::2] + s[0::2, 1::2] + s[1::2, 1::2]
    for fh in (6, 12, 18, 24):
        with Dataset(f"{run}/sfcf{fh:03d}.tile{t}.nc") as d:
            sh = np.asarray(d.variables["shtfl_ave"][0], dtype="f8")
        with Dataset(f"{run}/atmf{fh:03d}.tile{t}.nc") as d:
            ps = np.asarray(d.variables["pressfc"][0], dtype="f8")
            q1 = np.asarray(d.variables["spfh"][0, -1], dtype="f8")
            dp1 = np.asarray(d.variables["dpres"][0, -1], dtype="f8")
        ex1 = ((ps - 0.5 * dp1) / 1e5) ** (287.05 / 1004.6)
        num += np.sum(a * sh * ex1 / (1 + 0.84 * q1)); den += np.sum(a * sh)
print(f"SH-weighted applied/reported = {num/den:.5f}")
