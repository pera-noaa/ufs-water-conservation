#!/usr/bin/env python3
"""Global burden sum(q*delp*area)/g of tracers in a run's final RESTART (6 tiles), area from INPUT/C96_grid.tile*.nc.
usage: burden.py <run> <restart prefix e.g. 20210323.060000.> <var,...>  -> prints burdens; compare runs offline."""
import sys, numpy as np, netCDF4 as nc
r, pre, vs = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
out = {}
for t in range(1, 7):
    with nc.Dataset(f'{r}/INPUT/C96_grid.tile{t}.nc') as g:
        a = g['area'][:].astype('f8'); A = a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
    with nc.Dataset(f'{r}/RESTART/{pre}fv_core.res.tile{t}.nc') as c, nc.Dataset(f'{r}/RESTART/{pre}fv_tracer.res.tile{t}.nc') as d:
        dp = c['delp'][:].astype('f8')[0]
        for v in vs:
            out[v] = out.get(v, 0.) + (d[v][:].astype('f8')[0] * dp * A[None]).sum() / 9.80665
print(r, ' '.join(f'{v}={out[v]:.10e}' for v in vs))
