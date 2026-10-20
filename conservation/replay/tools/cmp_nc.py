#!/usr/bin/env python3
"""cmp_nc.py <runA> <runB> <glob>... : bitwise comparison of netCDF outputs of two run dirs (paths relative to the run
dir, e.g. 'atmf024.tile*.nc' 'RESTART/*.nc' 'RESTART/*.res'). Per file: byte-identical, or else every variable's raw
values (no masking/scaling, NaN bit patterns included) compared as bytes. Prints per-pattern counts and any differing
variable; exit 1 if any file or variable differs or is missing."""
import glob
import os
import sys

import numpy as np
from netCDF4 import Dataset

a, b, pats = sys.argv[1], sys.argv[2], sys.argv[3:]
bad = 0
for pat in pats:
    fa = sorted(glob.glob(os.path.join(a, pat)))
    nbyte = nvar = 0
    if not fa:
        print(f"{pat}: NO FILES in {a}")
        bad += 1
        continue
    for f in fa:
        g = os.path.join(b, os.path.relpath(f, a))
        if not os.path.exists(g):
            print(f"  missing in B: {os.path.relpath(f, a)}")
            bad += 1
            continue
        if open(f, "rb").read() == open(g, "rb").read():
            nbyte += 1
            continue
        if not f.endswith(".nc"):
            print(f"  DIFFERS (text/binary): {os.path.relpath(f, a)}")
            bad += 1
            continue
        da, db = Dataset(f), Dataset(g)
        da.set_auto_maskandscale(False)
        db.set_auto_maskandscale(False)
        va, vb = set(da.variables), set(db.variables)
        if va != vb:
            print(f"  variable sets differ: {os.path.relpath(f, a)} {sorted(va ^ vb)[:5]}")
            bad += 1
        diff = [v for v in sorted(va & vb)
                if np.asarray(da.variables[v][:]).tobytes() != np.asarray(db.variables[v][:]).tobytes()]
        if diff:
            print(f"  DIFFERS {os.path.relpath(f, a)}: {len(diff)} of {len(va)} variables, e.g. {diff[:5]}")
            bad += 1
        else:
            nvar += 1
    print(f"{pat}: {len(fa)} files; byte-identical {nbyte}, all variables bitwise (metadata differs) {nvar}")
print("BITWISE IDENTICAL" if not bad else f"DIFFERENT ({bad})")
sys.exit(1 if bad else 0)
