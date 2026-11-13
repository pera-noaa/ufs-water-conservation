"""Bitwise comparison of two runs: every numeric variable of the listed history stems (and RESTART if 'restart').
usage: cmp_bit.py <runA> <runB> [stem ...]   default stems: atmf024 sfcf024; files <stem>.nc or <stem>.tile{1..6}.nc"""
import sys, glob, os
import numpy as np
from netCDF4 import Dataset
a, b = sys.argv[1], sys.argv[2]
stems = sys.argv[3:] or ["atmf024", "sfcf024"]
for st in stems:
    if st == "restart":
        fa = sorted(f for f in glob.glob(f"{a}/RESTART/*.nc") if not os.path.basename(f).startswith("20210322.180000"))
    else:
        fa = sorted(glob.glob(f"{a}/{st}.nc") + glob.glob(f"{a}/{st}.tile*.nc"))
    nv = nd = 0; worst = []
    for f in fa:
        g = f.replace(a, b, 1)
        if not os.path.exists(g):
            nd += 1; worst.append((-2, os.path.basename(f), "MISSING")); continue
        with Dataset(f) as x, Dataset(g) as y:
            for v in x.variables:
                if x.variables[v].dtype.kind not in "fiu" or v not in y.variables:
                    continue
                nv += 1
                p, q = np.asarray(x.variables[v][:]), np.asarray(y.variables[v][:])
                if p.shape != q.shape or not np.array_equal(p, q, equal_nan=True):
                    nd += 1
                    d = float(np.nanmax(np.abs(p.astype('f8') - q.astype('f8')))) if p.shape == q.shape else -1
                    worst.append((d, os.path.basename(f), v))
    worst.sort(reverse=True)
    print(f"{st}: {nd} of {nv} variables differ ({len(fa)} files)" + ("" if not worst else "; largest: " +
          ", ".join(f"{fn}:{v} {d:.2e}" for d, fn, v in worst[:4])))
