#!/usr/bin/env python3
"""Uniform-dry check on native restart files: fv_tracer.res(.nest02).tileN.nc + fv_core.res(...) delp.
dev = q/(1-sum water)/1e-6 - 1 (dry-mass weighted rms, max) for the listed tracers; moist tracers: q/1e-6 - 1.
usage: uni_rst.py <tracer,...> <prefix e.g. RUN/RESTART/20230224.030000.> <tile tags e.g. tile1,...|nest02.tile7>"""
import sys, numpy as np, netCDF4 as nc
trs = sys.argv[1].split(','); pre = sys.argv[2]; tags = sys.argv[3].split(',')
W = ['sphum', 'liq_wat', 'ice_wat', 'rainwat', 'snowwat', 'graupel']
acc = {t: [0., 0., 0., None] for t in trs}
for tg in tags:
    with nc.Dataset(f'{pre}fv_tracer.res.{tg}.nc') as d, nc.Dataset(f'{pre}fv_core.res.{tg}.nc') as c:
        w = sum(d[v][:].astype('f8') for v in W if v in d.variables)
        D = c['delp'][:].astype('f8') * (1 - w)
        for t in trs:
            q = d[t][:].astype('f8')
            dev = (q / 1e-6 - 1) if 'moist' in t else (q / (1 - w) / 1e-6 - 1)
            a = acc[t]; a[0] += (D * dev**2).sum(); a[1] += D.sum()
            m = float(np.abs(dev).max())
            if m > a[2]:
                a[2] = m; a[3] = (tg, np.unravel_index(np.abs(dev).argmax(), dev.shape))
        dt = d['pt_udry'].dtype
for t, a in acc.items():
    print(f'{t:16s} rms {np.sqrt(a[0]/a[1]):.3e}  max {a[2]:.3e} at {a[3]}  [{tags[0]}.., file dtype {dt}]')
