#!/usr/bin/env python3
"""Copy gfs_data*.nc from a run's INPUT (resolving links) to <dst> adding float64 test tracers = 1e-6.
usage: add_tracer_ic.py <run INPUT dir> <dst dir> <name,...>"""
import sys, glob, os, numpy as np, netCDF4 as nc
src, dst, names = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
for fi in sorted(glob.glob(f'{src}/gfs_data*.nc')):
    fo = f'{dst}/{os.path.basename(fi)}'
    with nc.Dataset(os.path.realpath(fi)) as a, nc.Dataset(fo, 'w', format=a.data_model) as b:
        b.setncatts(a.__dict__)
        for n, d in a.dimensions.items():
            b.createDimension(n, None if d.isunlimited() else len(d))
        for n, v in a.variables.items():
            o = b.createVariable(n, v.datatype, v.dimensions); o.setncatts(v.__dict__); o[:] = v[:]
        ref = a['sphum']
        for n in names:
            if n not in a.variables:
                o = b.createVariable(n, 'f8', ref.dimensions); o[:] = np.full(ref.shape, 1e-6)
    print(os.path.basename(fi), 'ok')
