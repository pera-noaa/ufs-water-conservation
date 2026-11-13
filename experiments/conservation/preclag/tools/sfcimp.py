#!/usr/bin/env python3
"""sfcimp.py <ctl> <exp> [fh=24] : exp - ctl at sfcf<fh>, mean / rms over land (land == 1), sea ice (land == 2) and
open water (land == 0) for surface fields a precipitation-temperature change can reach. Missing fields are skipped."""
import sys
import numpy as np
from netCDF4 import Dataset
a, b = sys.argv[1:3]
fh = int(sys.argv[3]) if len(sys.argv) > 3 else 24


def ld(r, v):
    return np.concatenate([Dataset(f"{r}/sfcf{fh:03d}.tile{t}.nc").variables[v][:].astype(float).ravel() for t in range(1, 7)])


lm = ld(a, "land")
for v in ("tmp2m", "lhtfl_ave", "shtfl_ave", "tmpsfc", "soilt1", "weasd", "snod", "icetk", "tisfc"):
    try:
        d = ld(b, v) - ld(a, v)
    except (KeyError, IndexError):
        continue
    row = []
    for name, k in (("land", 1), ("ice", 2), ("water", 0)):
        m = lm == k
        if m.any():
            row.append(f"{name} {d[m].mean():+.3e}/{np.sqrt((d[m] ** 2).mean()):.3e}")
    print(f"{v:10s} " + " | ".join(row))
