#!/usr/bin/env python3
"""Bitwise gate: compare every numeric variable of atmf/sfcf <fhr> tiles (and RESTART *.nc at the end time if both have
them). Prints the number of differing variables and the largest |diff|. Usage: bitcmp.py <runA> <runB> [fhr=24]"""
import sys, glob, os
import numpy as np
from netCDF4 import Dataset
a, b = sys.argv[1], sys.argv[2]
fh = int(sys.argv[3]) if len(sys.argv) > 3 else 24
files = [f"atmf{fh:03d}.tile{t}.nc" for t in range(1, 7)] + [f"sfcf{fh:03d}.tile{t}.nc" for t in range(1, 7)]
ra = sorted(os.path.basename(f) for f in glob.glob(f"{a}/RESTART/2021*.nc"))
rb = set(os.path.basename(f) for f in glob.glob(f"{b}/RESTART/2021*.nc"))
files += [f"RESTART/{f}" for f in ra if f in rb]
ndiff, nvar, worst = 0, 0, (0.0, "")
for f in files:
    da, db = Dataset(f"{a}/{f}"), Dataset(f"{b}/{f}")
    for v in da.variables:
        x = da.variables[v][:]
        if x.dtype.kind not in "fiu" or v in ("time",):
            continue
        y = db.variables[v][:]
        nvar += 1
        d = np.max(np.abs(np.asarray(y, dtype=np.float64) - np.asarray(x, dtype=np.float64))) if x.size else 0.0
        if d > 0 or np.ma.count_masked(x) != np.ma.count_masked(y):
            ndiff += 1
            if d > worst[0]:
                worst = (d, f"{f}:{v}")
    da.close(); db.close()
print(f"{'BITWISE' if ndiff == 0 else 'DIFFER'}: {ndiff}/{nvar} variables differ over {len(files)} files; max|diff| {worst[0]:.3e} {worst[1]}")
