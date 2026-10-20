"""Copy gfs_data.tile*.nc adding two passive tracers: pt_u (uniform moist mixing ratio 1e-6) and pt_s (structured,
1e-6*S with S as in conservation/tracer/scripts/make_ic.py).  usage: make_ic2.py <src INPUT dir> <dst dir>"""
import sys, numpy as np, netCDF4 as nc
src, dst = sys.argv[1], sys.argv[2]
WAT = ['sphum', 'liq_wat', 'ice_wat', 'rainwat', 'snowwat', 'graupel']
for t in range(1, 7):
    fi = f'{src}/gfs_data.tile{t}.nc'; fo = f'{dst}/gfs_data.tile{t}.nc'
    with nc.Dataset(fi) as a:
        dp = a['delp'][:].astype('f8'); zh = a['zh'][:].astype('f8'); ps = a['ps'][:].astype('f8')
        lon = np.deg2rad(a['geolon'][:].astype('f8')); lat = np.deg2rad(a['geolat'][:].astype('f8'))
        w = {v: a[v][:].astype('f8') for v in WAT}
    assert zh[0].mean() > zh[-1].mean(), 'expected top-first IC levels'
    ptop = ps - dp.sum(axis=0)
    pint = ptop[None] + np.concatenate([np.zeros_like(ps)[None], np.cumsum(dp, axis=0)], axis=0)
    p = 0.5 * (pint[:-1] + pint[1:]); x = p / ps[None]
    lat3 = np.broadcast_to(lat, p.shape); lon3 = np.broadcast_to(lon, p.shape)
    ptrop = 10000. + 20000. * np.sin(lat3) ** 2
    cond = sum(w[v] for v in WAT[1:])
    S = (2.0 + 0.5 * (1 + np.tanh((x - 0.85) / 0.03)) - 0.6 * 0.5 * (1 + np.tanh((ptrop - p) / (0.1 * ptrop)))
         + 0.5 * np.sin(3 * lon3) * np.cos(lat3) ** 2 + 0.4 * np.tanh(np.rad2deg(lat3) / 5.)
         + 1.5 * np.minimum(1., cond / 1e-4) + 0.5 * np.minimum(1., np.maximum(w['sphum'], 0.) / 0.015))
    fields = {'pt_u': np.full_like(S, 1e-6), 'pt_s': 1e-6 * S}
    with nc.Dataset(fi) as a, nc.Dataset(fo, 'w', format=a.data_model) as b:
        b.setncatts(a.__dict__)
        for n, d in a.dimensions.items():
            b.createDimension(n, None if d.isunlimited() else len(d))
        for n, v in a.variables.items():
            o = b.createVariable(n, v.datatype, v.dimensions); o.setncatts(v.__dict__); o[:] = v[:]
        for n, f in fields.items():
            o = b.createVariable(n, 'f4', ('lev', 'lat', 'lon')); o.setncatts({'coordinates': 'geolon geolat'})
            o[:] = f.astype('f4')
    print(t, ' '.join(f'{n}:{f.min():.3e}/{f.max():.3e}' for n, f in fields.items()))
