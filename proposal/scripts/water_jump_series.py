#!/usr/bin/env python3
"""Cold-start water jump: global total water W(t) - W(0) + P(0,t) - E(0,t) at every output time in the first bucket.
Usage: python3 water_jump_series.py <RUNDIR>
Needs atmf*.tileN.nc / sfcf*.tileN.nc at fractional hours (output_fh 0 0.2 ... 6) and fhzero >= the last time, so
prateb_ave and lhtfl_ave average from 0 to t. W uses the six water species times dpres/(1 - condensate): output dpres is the dry+vapour thickness."""
import glob
import re
import sys
import numpy as np
from netCDF4 import Dataset

G, HVAP = 9.80665, 2.5e6
SP = ["spfh", "clwmr", "icmr", "rwmr", "snmr", "grle"]
rd = sys.argv[1]


def area(t):
    a = np.asarray(Dataset(f"{rd}/INPUT/C96_grid.tile{t}.nc")["area"][:], float)
    return a[0::2, 0::2] + a[1::2, 0::2] + a[1::2, 1::2] + a[0::2, 1::2]


A = {t: area(t) for t in range(1, 7)}
atot = sum(a.sum() for a in A.values())
tags = sorted({re.sub(r"\.tile\d\.nc$", "", f.split("/atmf")[-1]) for f in glob.glob(f"{rd}/atmf*.tile1.nc")})


def hours(tag):
    m = re.match(r"(\d+)(?:-(\d+))?(?:-(\d+))?", tag)
    return int(m[1]) + int(m[2] or 0) / 60 + int(m[3] or 0) / 3600


rows = []
for tag in sorted(tags, key=hours):
    h = hours(tag)
    w = pe = 0.0
    for t in range(1, 7):
        d = Dataset(f"{rd}/atmf{tag}.tile{t}.nc")
        q = sum(np.asarray(d[s][:], float).squeeze() for s in SP if s in d.variables)
        cond = q - np.asarray(d[SP[0]][:], float).squeeze()
        w += ((q * np.asarray(d["dpres"][:], float).squeeze() / (1.0 - cond)).sum(0) / G * A[t]).sum()
        if h > 0:
            s = Dataset(f"{rd}/sfcf{tag}.tile{t}.nc")
            p = np.asarray(s["prateb_ave"][:], float).squeeze()
            e = np.asarray(s["lhtfl_ave"][:], float).squeeze() / HVAP
            pe += ((p - e) * A[t]).sum() * h * 3600
    rows.append((h, w / atot, pe / atot))
w0 = rows[0][1]
print(f"{rd}\n hour  | W-W0     | P-E cum  | residual (W-W0+P-E)")
for h, w, pe in rows:
    print(f"{h:5.2f}  | {w-w0:+.5f} | {pe:+.5f} | {w-w0+pe:+.5f}")
