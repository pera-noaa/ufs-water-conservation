#!/usr/bin/env python3
"""Uniform-dry check on history files (float32): c = q/(1 - sum water), dev = c/1e-6 - 1, dpres*(1-w)-weighted rms and
max|dev| per tracer; also dev of the moist uniform tracers (q/1e-6 - 1). usage: uni_check.py <tracer,...> <file> [file ...]"""
import sys, numpy as np, netCDF4 as nc
trs = sys.argv[1].split(','); files = sys.argv[2:]
W = ['spfh', 'clwmr', 'icmr', 'rwmr', 'snmr', 'grle']
acc = {t: [0., 0., 0.] for t in trs}
for f in files:
    with nc.Dataset(f) as d:
        w = sum(d[v][:].astype('f8') for v in W if v in d.variables)
        dp = d['dpres'][:].astype('f8'); D = dp * (1 - w)
        for t in trs:
            if t not in d.variables:
                continue
            q = d[t][:].astype('f8')
            dev = (q / 1e-6 - 1) if 'moist' in t else (q / (1 - w) / 1e-6 - 1)
            a = acc[t]; a[0] += (D * dev**2).sum(); a[1] += D.sum(); a[2] = max(a[2], float(np.abs(dev).max()))
for t, a in acc.items():
    if a[1] > 0:
        print(f'{t:16s} rms {np.sqrt(a[0]/a[1]):.3e}  max {a[2]:.3e}   ({files[0].split("/")[-2]}/{files[0].split("/")[-1]}...)')
