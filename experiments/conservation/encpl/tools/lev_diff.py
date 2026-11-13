#!/usr/bin/env python3
"""Systematic vs noise: per model level, mean and rms of runB - runA for tmp (6 tiles, cell mean),
grouped in layer bands; plus means of selected 2-D fields.
Usage: lev_diff.py <runA> <runB> <fhr>"""
import sys
import numpy as np
from netCDF4 import Dataset

a, b, fh = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = []
for t in range(1, 7):
    x = Dataset(f"{a}/atmf{fh:03d}.tile{t}.nc").variables["tmp"][:].astype(np.float64)[0]
    y = Dataset(f"{b}/atmf{fh:03d}.tile{t}.nc").variables["tmp"][:].astype(np.float64)[0]
    d.append((y - x).reshape(x.shape[0], -1))
d = np.concatenate(d, axis=1)
nk = d.shape[0]
bands = [(0, 30), (30, 60), (60, 85), (85, 105), (105, 117), (117, nk)]
print(f"# {b} - {a}, atmf{fh:03d}, tmp, levels 0=top of {nk}")
for k0, k1 in bands:
    s = d[k0:k1]
    print(f"levels {k0:3d}-{k1 - 1:3d}: mean {s.mean():+.4e} K  rms {np.sqrt((s * s).mean()):.4e} K")
print(f"all: mean {d.mean():+.4e}  rms {np.sqrt((d * d).mean()):.4e}")
for v in ("prate_ave", "lhtfl_ave", "shtfl_ave", "tmp2m", "pressfc", "ulwrf_ave"):
    m, r, n = 0.0, 0.0, 0
    try:
        for t in range(1, 7):
            x = Dataset(f"{a}/sfcf{fh:03d}.tile{t}.nc").variables[v][:].astype(np.float64)
            y = Dataset(f"{b}/sfcf{fh:03d}.tile{t}.nc").variables[v][:].astype(np.float64)
            m += float((y - x).sum())
            r += float(((y - x) ** 2).sum())
            n += x.size
        print(f"{v:10s} mean d {m / n:+.4e}  rms {np.sqrt(r / n):.4e}")
    except (KeyError, OSError):
        pass
