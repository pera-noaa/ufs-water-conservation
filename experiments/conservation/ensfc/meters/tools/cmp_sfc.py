#!/usr/bin/env python3
"""Surface-field differences between two runs at one forecast hour, by surface mask (ice: icec>0 of run A;
land: land==1). Area weights = 1 (C96 cells near-equal). Usage: cmp_sfc.py <runA> <runB> <fhr>"""
import sys
import numpy as np
from netCDF4 import Dataset
a, b, fh = sys.argv[1], sys.argv[2], int(sys.argv[3])
V = ["icetk", "tisfc", "weasd", "tmpsfc", "tmp2m", "spfh2m", "shtfl_ave", "lhtfl_ave", "gflux_ave", "soilt1",
     "snod", "ulwrf_ave", "uswrf_ave", "prate_ave"]
def load(r, v):
    return np.concatenate([Dataset(f"{r}/sfcf{fh:03d}.tile{t}.nc").variables[v][:].astype(np.float64).ravel()
                           for t in range(1, 7)])
icec, land = load(a, "icec"), load(a, "land")
masks = {"ice": icec > 0, "land": land == 1, "all": np.ones_like(icec, bool)}
for v in V:
    try:
        x, y = load(a, v), load(b, v)
    except KeyError:
        continue
    d = y - x
    out = [f"{v:10s}"]
    for m, k in masks.items():
        dd = d[k]
        out.append(f"{m}: mean {dd.mean():+.3e} rms {np.sqrt((dd*dd).mean()):.3e}")
    print("  ".join(out))
