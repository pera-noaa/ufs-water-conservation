#!/usr/bin/env python3
"""trdyn ICs from the tracer agent's six-tracer IC (read-only): adds pt_cplume (= pt_plume, chemistry-type plume).
usage: make_ic.py <src dir> <dst dir> <mode>; mode m: pt_udry as in src (moist 1e-6*(1-sum water));
mode d: pt_udry = 1e-6 as float64 (a dry mixing ratio, for dry_tracer_ic). Other tracers are copied unchanged."""
import sys, numpy as np, netCDF4 as nc
src, dst, mode = sys.argv[1], sys.argv[2], sys.argv[3]
assert mode in ('m', 'd')
for t in range(1, 7):
    fi = f'{src}/gfs_data.tile{t}.nc'; fo = f'{dst}/gfs_data.tile{t}.nc'
    with nc.Dataset(fi) as a, nc.Dataset(fo, 'w', format=a.data_model) as b:
        b.setncatts(a.__dict__)
        for n, d in a.dimensions.items():
            b.createDimension(n, None if d.isunlimited() else len(d))
        for n, v in a.variables.items():
            dd = 'f8' if (n == 'pt_udry' and mode == 'd') else v.datatype
            o = b.createVariable(n, dd, v.dimensions)
            o.setncatts(v.__dict__)
            x = v[:]
            if n == 'pt_udry' and mode == 'd':
                x = np.full(x.shape, 1e-6, dtype='f8')
            o[:] = x
        v = a['pt_plume']
        o = b.createVariable('pt_cplume', v.datatype, v.dimensions); o.setncatts(v.__dict__); o[:] = v[:]
    with nc.Dataset(fo) as b:
        u = b['pt_udry'][:]
        print(t, mode, 'pt_udry min/max', float(u.min()), float(u.max()), 'pt_cplume max', float(b['pt_cplume'][:].max()))
