#!/usr/bin/env python3
"""Run-to-run tracer differences at hour <fh> in ppm-equivalent of 400 ppm (scale = 400 / A's dp-weighted mean), as
trsamf/compare_ppm.py plus pt_cplume and dry-ratio extrema (c = q/(1 - sum water), relative to A's mean dry ratio).
usage: cmp_dyn.py <run A> <run B> <fh>   (history is float32)"""
import sys, numpy as np, netCDF4 as nc
a, b, fh = sys.argv[1:4]
TR = ['pt_cnv', 'pt_umoist', 'pt_ghg', 'pt_udry', 'pt_cplume', 'pt_plume']
W = ['spfh', 'clwmr', 'icmr', 'rwmr', 'snmr', 'grle']
def load(r, v):
    return np.concatenate([nc.Dataset(f'{r}/atmf{fh}.tile{t}.nc')[v][:].astype('f8').ravel() for t in range(1, 7)])
dpA = load(a, 'dpres')
for v in ['tmp', 'spfh', 'clwmr', 'dpres', 'ugrd', 'pressfc']:
    d = load(b, v) - load(a, v)
    print(f'{v:9s} identical={bool((d == 0).all())}  max|diff| {abs(d).max():.3e}')
wA = sum(load(a, v) for v in W); wB = sum(load(b, v) for v in W)
for v in TR:
    try:
        x, y = load(a, v), load(b, v)
    except (KeyError, IndexError):
        continue
    mean = (x * dpA).sum() / dpA.sum(); s = 400. / mean if mean else 0.
    d = (y - x) * s
    cx, cy = x / (1 - wA), y / (1 - wB); cm = (cx * dpA * (1 - wA)).sum() / (dpA * (1 - wA)).sum()
    print(f'{v:10s} rms {np.sqrt((d**2*dpA).sum()/dpA.sum()):.3e} max {abs(d).max():.3e} ppm-eq | dry ratio/mean A {cx.min()/cm:.5f}..{cx.max()/cm:.5f}'
          f' B {cy.min()/cm:.5f}..{cy.max()/cm:.5f} | q<0 A {int((x<0).sum())} B {int((y<0).sum())}')
