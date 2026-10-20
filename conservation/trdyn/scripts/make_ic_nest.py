#!/usr/bin/env python3
"""gnv1_nested IC with uniform-dry test tracers: copies gfs_data.tile1-6 and gfs_data.nest02.tile7 and adds
pt_udry and pt_udry_nopbl = 1e-6 (float64, dry mixing ratio for dry_tracer_ic) and pt_umoist_nopbl = 1e-6.
usage: make_ic_nest.py <src INPUT dir> <dst dir>"""
import sys, numpy as np, netCDF4 as nc
src, dst = sys.argv[1], sys.argv[2]
for t in [f'tile{i}' for i in range(1, 7)] + ['nest02.tile7']:
    fi = f'{src}/gfs_data.{t}.nc'; fo = f'{dst}/gfs_data.{t}.nc'
    with nc.Dataset(fi) as a, nc.Dataset(fo, 'w', format=a.data_model) as b:
        b.setncatts(a.__dict__)
        for n, d in a.dimensions.items():
            b.createDimension(n, None if d.isunlimited() else len(d))
        for n, v in a.variables.items():
            o = b.createVariable(n, v.datatype, v.dimensions); o.setncatts(v.__dict__); o[:] = v[:]
        ref = a['sphum']
        for n in ('pt_udry', 'pt_udry_nopbl', 'pt_umoist_nopbl'):
            o = b.createVariable(n, 'f8', ref.dimensions); o[:] = np.full(ref.shape, 1e-6)
    print(t, 'ok', a.data_model if False else '')
