#!/usr/bin/env python3
"""Forecast impact of run B vs run A: T by pressure band (max|d|, rms, mean d), ps, precip, LH (6 tiles, cell means).
Usage: impact.py <runA> <runB> <fhr> [dt_s]   with dt_s, T rows are also given as K/day = d/dt_s*86400 (step-1 use)"""
import sys
import numpy as np
from netCDF4 import Dataset

a, b, fh = sys.argv[1], sys.argv[2], int(sys.argv[3])
dts = float(sys.argv[4]) if len(sys.argv) > 4 else None
BANDS = [(1100, 500), (500, 200), (200, 50), (50, 1), (1, 0)]


def load(run, kind, v):
    return np.concatenate([Dataset(f"{run}/{kind}f{fh:03d}.tile{t}.nc").variables[v][:].astype(np.float64)[0]
                           for t in range(1, 7)], axis=-1)


p = Dataset(f"{a}/atmf{fh:03d}.tile1.nc").variables["pfull"][:]
d = load(b, "atm", "tmp") - load(a, "atm", "tmp")
for hi, lo in BANDS:
    k = (p <= hi) & (p > lo)
    x = d[k]
    s = f"f{fh:03d} T {hi:5d}-{lo:4d} hPa  max|d| {np.abs(x).max():.3e}  rms {np.sqrt((x*x).mean()):.3e}  mean {x.mean():+.3e} K"
    if dts:
        s += f"  | max {np.abs(x).max()/dts*86400:.3e} mean {x.mean()/dts*86400:+.3e} K/day"
    print(s)
kmax = int(np.unravel_index(np.abs(d).argmax(), d.shape)[0])
print(f"f{fh:03d} T all levels rms {np.sqrt((d*d).mean()):.3e}  max at level {kmax} ({p[kmax]:.1f} hPa)")
for kind, v, u in (("sfc", "pressfc", "Pa"), ("sfc", "prate_ave", "mm/day"), ("sfc", "lhtfl_ave", "W m-2")):
    try:
        x = load(b, kind, v) - load(a, kind, v)
        xa = load(a, kind, v)
    except (KeyError, OSError):
        continue
    f = 86400.0 if v == "prate_ave" else 1.0
    print(f"f{fh:03d} {v:10s} max|d| {np.abs(x).max()*f:.3e}  rms {np.sqrt((x*x).mean())*f:.3e}  mean d {x.mean()*f:+.3e}"
          f"  (mean A {xa.mean()*f:.4e}) {u}")
