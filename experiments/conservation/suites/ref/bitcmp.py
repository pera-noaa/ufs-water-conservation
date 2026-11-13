#!/usr/bin/env python3
"""Bit-for-bit comparison of every variable in atmfHHH/sfcfHHH.tileN.nc between two run dirs.
Usage: bitcmp.py <dirA> <dirB>   prints per file the number of differing variables and the max |diff|."""
import glob, os, sys
import numpy as np
from netCDF4 import Dataset
a, b = sys.argv[1:3]
nf = ndiff = 0
for fa in sorted(glob.glob(f"{a}/atmf0??.tile?.nc") + glob.glob(f"{a}/sfcf0??.tile?.nc")):
    fb = f"{b}/{os.path.basename(fa)}"
    if not os.path.exists(fb):
        print("MISSING", fb); ndiff += 1; continue
    A, B = Dataset(fa), Dataset(fb)
    bad = []
    for v in A.variables:
        x, y = np.asarray(A[v][:]), np.asarray(B[v][:])
        if x.shape != y.shape or not np.array_equal(x, y, equal_nan=(x.dtype.kind == "f")):
            bad.append((v, (float(np.nanmax(np.abs(x.astype(float) - y.astype(float)))) if x.dtype.kind in "fiu" else "non-numeric") if x.shape == y.shape else -1))
    nf += 1
    if bad:
        ndiff += 1
        print(os.path.basename(fa), len(bad), "vars differ, e.g.", bad[:3])
print(f"{nf} files compared, {ndiff} differ")
