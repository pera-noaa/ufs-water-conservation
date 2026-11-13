"""Locate extremes of tracers in atmf files. usage: locate_max.py <rundir> <fhr> var [var...]"""
import sys, numpy as np, netCDF4 as nc
d, fh, vs = sys.argv[1], sys.argv[2], sys.argv[3:]
for v in vs:
    best = []
    for t in range(1, 7):
        with nc.Dataset(f'{d}/atmf{fh}.tile{t}.nc') as a:
            x = a[v][0].astype('f8')
            for idx in np.argsort(x.ravel())[-3:]:
                k, j, i = np.unravel_index(idx, x.shape)
                best.append((x[k, j, i], t, k, j, i, float(a['grid_xt'][j, i]),
                             float(a['grid_yt'][j, i]), float(a['pfull'][k])))
            n = (x > 1.5e-6).sum() if 'umoist' in v else 0
            if n: print(f'  {v} tile{t}: {n} cells > 1.5e-6, levels {sorted(set(np.where(x > 1.5e-6)[0].tolist()))[:20]}')
    best.sort(reverse=True)
    for b in best[:6]:
        print(v, 'val %.4e tile %d k %d j %d i %d lon %.1f lat %.1f pfull %.2f' % b)
