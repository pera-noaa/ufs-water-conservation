#!/usr/bin/env python3
"""Lowest-layer profiles of a variable at the column of its 24 h extreme. usage: col_profile.py <run> <var> [nlev] [tile j i]"""
import sys, numpy as np, netCDF4 as nc
r, v = sys.argv[1], sys.argv[2]; nl = int(sys.argv[3]) if len(sys.argv) > 3 else 10
if len(sys.argv) > 6:
    t, j, i = map(int, sys.argv[4:7])
else:
    best = None
    for t in range(1, 7):
        a = nc.Dataset(f'{r}/atmf024.tile{t}.nc')[v][0].astype('f8')
        k, jj, ii = np.unravel_index(np.argmax(np.abs(a / np.mean(a) - 1)), a.shape)
        x = abs(a[k, jj, ii] / np.mean(a) - 1)
        if best is None or x > best[0]:
            best = (x, t, jj, ii)
    _, t, j, i = best
print(f'{r} {v} tile {t} j {j} i {i}; lowest {nl} layers (surface last), values / 1e-6 (tracers) ')
for h in ('000', '006', '012', '018', '024'):
    d = nc.Dataset(f'{r}/atmf{h}.tile{t}.nc')
    a = d[v][0, -nl:, j, i].astype('f8'); q = d['spfh'][0, -nl:, j, i].astype('f8'); dp = d['dpres'][0, -nl:, j, i]
    print(f' f{h} {v}: ' + ' '.join(f'{x/1e-6:7.4f}' for x in a) + '  | qv g/kg: ' + ' '.join(f'{x*1e3:5.2f}' for x in q[-3:])
          + '  dp: ' + ' '.join(f'{x:6.0f}' for x in dp[-3:]))
