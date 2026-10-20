#!/usr/bin/env python3
"""Range of pt_umoist (moist) and of its dry ratio q/(1-sum water) at f000 and <fh>, with location/level of extremes.
usage: umoist_frame.py <run> <fh> [var]"""
import sys, numpy as np, netCDF4 as nc
r, fh = sys.argv[1], sys.argv[2]; v = sys.argv[3] if len(sys.argv) > 3 else 'pt_umoist'
W = ['spfh', 'clwmr', 'icmr', 'rwmr', 'snmr', 'grle']
for h in ('000', fh):
    qs, cs, info = [], [], []
    for t in range(1, 7):
        d = nc.Dataset(f'{r}/atmf{h}.tile{t}.nc')
        q = d[v][0].astype('f8'); w = sum(d[x][0].astype('f8') for x in W)
        c = q / (1 - w)
        qs.append(q); cs.append(c)
        for arr, nm in ((q, 'q'), (c, 'c')):
            for f in (np.argmin, np.argmax):
                k, j, i = np.unravel_index(f(arr), arr.shape)
                info.append((nm, f.__name__, arr[k, j, i], t, k, float(d['grid_yt'][j, i]),
                             float(d['grid_xt'][j, i]), float(d['pfull'][k])))
    q = np.concatenate([x.ravel() for x in qs]); c = np.concatenate([x.ravel() for x in cs])
    print(f'f{h}: {v} moist min/max {q.min():.4e} {q.max():.4e} | dry ratio min/max {c.min():.4e} {c.max():.4e}'
          f' | frac cells moist outside +-1%: {np.mean(np.abs(q/1e-6-1) > 0.01):.2e}  dry outside [0.99,1.05]: {np.mean((c/1e-6 < 0.99) | (c/1e-6 > 1.05)):.2e}')
    for nm in ('q', 'c'):
        for fn in ('argmin', 'argmax'):
            best = [x for x in info if x[0] == nm and x[1] == fn]
            b = min(best, key=lambda x: x[2]) if fn == 'argmin' else max(best, key=lambda x: x[2])
            print(f'   {nm} {fn[3:]}: {b[2]:.4e} tile {b[3]} lev {b[4]} (p {b[7]:.1f} hPa) lat {b[5]:.1f} lon {b[6]:.1f}')
