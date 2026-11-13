#!/usr/bin/env python3
"""Bitwise comparison of two runs' <file> (default atmf024) over 6 tiles, every variable.
usage: cmp_atmf.py <runA> <runB> [file stem]"""
import sys, numpy as np, netCDF4 as nc
a, b = sys.argv[1], sys.argv[2]; st = sys.argv[3] if len(sys.argv) > 3 else 'atmf024'
res = {}
for t in range(1, 7):
    with nc.Dataset(f'{a}/{st}.tile{t}.nc') as A, nc.Dataset(f'{b}/{st}.tile{t}.nc') as B:
        for v in A.variables:
            if v not in B.variables or A[v].ndim < 2 or A[v].dtype.kind not in 'fiu':
                continue
            x = A[v][:]; y = B[v][:]
            x = np.asarray(x, dtype='f8'); y = np.asarray(y, dtype='f8')
            nd = int(np.sum(x != y)); md = float(np.max(np.abs(x - y))) if nd else 0.0
            r = res.setdefault(v, [0, 0.0, 0]); r[0] += nd; r[1] = max(r[1], md); r[2] += x.size
same = [v for v, r in res.items() if r[0] == 0]; diff = {v: r for v, r in res.items() if r[0]}
print(f'{st}: {len(same)} variables bit-identical, {len(diff)} differ')
for v, r in sorted(diff.items()):
    print(f'  DIFF {v}: {r[0]} of {r[2]} values, max|d| {r[1]:.3e}')
