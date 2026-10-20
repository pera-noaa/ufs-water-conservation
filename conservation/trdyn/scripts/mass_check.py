#!/usr/bin/env python3
"""Global tracer mass sum(q*dpres*area) from native-tile history (float32), relative change between two hours.
area from INPUT/C96_grid.tile*.nc (supergrid, 2x2 blocks). usage: mass_check.py <run dir> <tracer,...> <h0> <h1>"""
import sys, numpy as np, netCDF4 as nc
r, trs, h0, h1 = sys.argv[1], sys.argv[2].split(','), sys.argv[3], sys.argv[4]
A = []
for t in range(1, 7):
    with nc.Dataset(f'{r}/INPUT/C96_grid.tile{t}.nc') as g:
        a = g['area'][:].astype('f8'); A.append(a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])
def mass(h, v):
    m = 0.
    for t in range(1, 7):
        with nc.Dataset(f'{r}/atmf{h}.tile{t}.nc') as d:
            q = d[v][:].astype('f8')[0]; dp = d['dpres'][:].astype('f8')[0]
            m += (q * dp * A[t-1][None]).sum()
    return m
for v in trs:
    m0, m1 = mass(h0, v), mass(h1, v)
    print(f'{r.split("/")[-1]:5s} {v:12s} mass {h0}->{h1} rel change {(m1-m0)/m0:+.3e}')
