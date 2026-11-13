#!/usr/bin/env python3
"""Run-to-run differences at hour <fh>, in ppm-equivalent of a 400 ppm CO2 scaling.
usage: compare_ppm.py <run A> <run B> <fh>
For each tracer: scale s = 400 ppm / (dpres-weighted global mean of A's field); prints dpres-weighted rms and max |B-A|*s.
Also: identity of tmp, spfh, clwmr, dpres, pressfc, ugrd (bitwise), and pt_udry dry-ratio spread in A and B:
c = q/(1 - sum water), dev = c/1e-6 - 1, dry-mass-weighted rms and max |dev| (and ppm-eq = dev*400)."""
import sys, numpy as np, netCDF4 as nc
a, b, fh = sys.argv[1:4]
TR = ['pt_cnv', 'pt_plume', 'pt_umoist', 'pt_ghg', 'pt_udry', 'pt_dyn_nopbl']
W = ['spfh', 'clwmr', 'icmr', 'rwmr', 'snmr', 'grle']
def load(r, v):
    return np.concatenate([nc.Dataset(f'{r}/atmf{fh}.tile{t}.nc')[v][:].astype('f8').ravel() for t in range(1, 7)])
dpA = load(a, 'dpres')
for v in ['tmp', 'spfh', 'clwmr', 'dpres', 'ugrd', 'pressfc']:
    x, y = load(a, v), load(b, v)
    d = y - x
    print(f'{v:9s} identical={bool((d == 0).all())}  max|diff| {abs(d).max():.3e}  rms {np.sqrt((d**2).mean()):.3e}')
for v in TR:
    try:
        x, y = load(a, v), load(b, v)
    except (KeyError, IndexError):
        continue
    mean = (x * dpA).sum() / dpA.sum()
    s = 400. / mean if mean != 0 else 0.
    d = (y - x) * s
    print(f'{v:13s} meanA {mean:.4e}  rms diff {np.sqrt((d**2*dpA).sum()/dpA.sum()):.3e} ppm-eq  max {abs(d).max():.3e} ppm-eq'
          f'  minA/maxA {x.min()/mean:.4f}/{x.max()/mean:.4f}  minB/maxB {y.min()/mean:.4f}/{y.max()/mean:.4f}')
for r in (a, b):
    q = load(r, 'pt_udry'); w = sum(load(r, v) for v in W); dp = load(r, 'dpres')
    D = dp * (1 - w); dev = q / (1 - w) / 1e-6 - 1
    print(f'pt_udry dry ratio {r.split("/")[-1]:8s}: rms dev {np.sqrt((D*dev**2).sum()/D.sum()):.3e} '
          f'({400*np.sqrt((D*dev**2).sum()/D.sum()):.3f} ppm)  max|dev| {abs(dev).max():.3e} ({400*abs(dev).max():.2f} ppm)'
          f'  [history is float32: resolution ~6e-8]')
