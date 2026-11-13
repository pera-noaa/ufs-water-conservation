#!/usr/bin/env python3
"""Compare two runs' final RESTART fv_core/fv_tracer (6 tiles): per variable rms and max of B-A; for tracers also
relative rms of (B-A)/mean|A|. usage: cmp_rst.py <runA> <runB> [var,...]"""
import sys, glob, os, numpy as np, netCDF4 as nc
a, b = sys.argv[1], sys.argv[2]; want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
def files(r, st):
    fs = sorted(glob.glob(f'{r}/RESTART/*{st}.tile[1-6].nc')) or sorted(glob.glob(f'{r}/RESTART/{st}.tile[1-6].nc'))
    return [f for f in fs if '0000.' in os.path.basename(f) or not os.path.basename(f)[0].isdigit()][-6:]
for st in ('fv_core.res', 'fv_tracer.res'):
    fa, fb = files(a, st), files(b, st)
    with nc.Dataset(fa[0]) as d:
        vs = [v for v in d.variables if d[v].ndim >= 3 and d[v].dtype.kind == 'f']
    for v in vs:
        if want and v not in want:
            continue
        x = np.concatenate([nc.Dataset(f)[v][:].astype('f8').ravel() for f in fa])
        y = np.concatenate([nc.Dataset(f)[v][:].astype('f8').ravel() for f in fb])
        d = y - x; m = np.abs(x).mean()
        nd = int((d != 0).sum())
        print(f'{v:10s} ndiff {nd:9d}  rms {np.sqrt((d**2).mean()):.3e}  max {np.abs(d).max():.3e}  rel rms {np.sqrt((d**2).mean())/m if m else 0:.3e}')
