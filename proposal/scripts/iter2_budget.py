#!/usr/bin/env python3
"""Defect E per window from the WBQ meter (instrument_wb_iter2.py): water the second surface iteration adds to Noah-MP
land that the atmosphere never exchanged. Usage: python3 iter2_budget.py <RUNDIR>. Global-mean kg/m2 and % of global P."""
import glob, re, sys
from collections import defaultdict
import numpy as np
from netCDF4 import Dataset

rd = sys.argv[1]
q, p = defaultdict(lambda: np.zeros(4)), defaultdict(float)
for line in open(f"{rd}/out", errors="replace"):
    m = re.match(r"\s*\d+:\s+(WBQ|WBP)\s+(\d+)\s+(.*)", line)
    if m and m.group(1) == "WBQ":
        q[int(m.group(2))] += np.array([float(x) for x in m.group(3).split()])
    elif m:
        p[int(m.group(2))] += float(m.group(3).split()[2])
kp = max(p); ag = p[kp] / kp
A = {}
for t in range(1, 7):
    a = np.asarray(Dataset(glob.glob(f"{rd}/INPUT/C*_grid.tile{t}.nc")[0])["area"][:], float)
    A[t] = a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
at = sum(a.sum() for a in A.values())
print(f"### {rd}\nwindow | P again   ET again  R again  | net land gain (P-ET-R) | % of global P | land area recomputed (fraction of land, per step)")
for fh in (6, 12, 18, 24):
    k0, k1 = max(1, (fh - 6) * 5), fh * 5
    d = (q[k1] - q[k0]) / ag
    P = sum((np.asarray(Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc")["prateb_ave"][:], float).squeeze() * A[t]).sum() for t in range(1, 7)) / at * 21600
    land = 0.2762 * (k1 - k0)
    print(f"{fh-6:3d}-{fh:3d} | {d[0]:.6f} {d[1]:.6f} {d[2]:.6f} | {d[0]-d[1]-d[2]:+.6f} | {100*(d[0]-d[1]-d[2])/P:+.4f} | {d[3]/land:.4f}")
