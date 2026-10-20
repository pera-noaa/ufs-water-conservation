#!/usr/bin/env python3
"""Compare two runs' history files: per variable, max |diff|, rms diff, and difference of area means.
Usage: cmp_runs.py <runA> <runB> <fhr...>   (atmfFFF/sfcfFFF tile1-6)"""
import sys
import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]
VARS = {"atm": ["tmp", "spfh", "ugrd", "vgrd", "dpres", "clwmr", "icmr", "rwmr", "snmr", "grle", "delz"],
        "sfc": ["tmpsfc", "prate_ave", "lhtfl_ave", "shtfl_ave", "pressfc", "dswrf_ave", "ulwrf_ave"]}
for fh in sys.argv[3:]:
    for kind, vs in VARS.items():
        for v in vs:
            mx, ss, n, da = 0.0, 0.0, 0, 0.0
            ok = True
            for t in range(1, 7):
                try:
                    x = Dataset(f"{a}/{kind}f{int(fh):03d}.tile{t}.nc").variables[v][:].astype(np.float64)
                    y = Dataset(f"{b}/{kind}f{int(fh):03d}.tile{t}.nc").variables[v][:].astype(np.float64)
                except (KeyError, OSError):
                    ok = False
                    break
                d = y - x
                mx = max(mx, float(np.abs(d).max()))
                ss += float((d * d).sum())
                n += d.size
                da += float(d.mean())
            if ok:
                print(f"f{fh} {v:10s} max|d| {mx:.3e}  rms {np.sqrt(ss / n):.3e}  mean d {da / 6:+.3e}")
