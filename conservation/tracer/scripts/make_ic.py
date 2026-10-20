"""Copy gfs_data.tile*.nc and add structured / uniform passive tracers (test ICs for tracer-mass conservation).
usage: make_ic.py <src INPUT dir> <dst INPUT dir>
Structured field S (dimensionless, mmr = 1e-6*S): sharp boundary-layer step, lat-dependent tropopause step,
zonal wave, sharp interhemispheric step, cloud/precip and humidity correlated parts. Plume: zero outside a
lat/lon/pressure box (exercises positivity machinery). Uniform moist: 1e-6. Uniform dry: 1e-6*(1-sum(water))."""
import sys, numpy as np, netCDF4 as nc
src, dst = sys.argv[1], sys.argv[2]
WAT = ['sphum', 'liq_wat', 'ice_wat', 'rainwat', 'snowwat', 'graupel']
COND = WAT[1:]
for t in range(1, 7):
    fi = f'{src}/gfs_data.tile{t}.nc'; fo = f'{dst}/gfs_data.tile{t}.nc'
    with nc.Dataset(fi) as a:
        dp = a['delp'][:].astype('f8'); zh = a['zh'][:].astype('f8'); ps = a['ps'][:].astype('f8')
        lon = np.deg2rad(a['geolon'][:].astype('f8')); lat = np.deg2rad(a['geolat'][:].astype('f8'))
        w = {v: a[v][:].astype('f8') for v in WAT}
    top_first = zh[0].mean() > zh[-1].mean()
    assert top_first, 'expected top-first IC levels'
    ptop = ps - dp.sum(axis=0)
    pint = ptop[None] + np.concatenate([np.zeros_like(ps)[None], np.cumsum(dp, axis=0)], axis=0)   # lev+1 interfaces, top first
    p = 0.5 * (pint[:-1] + pint[1:])
    x = p / ps[None]
    lat3 = np.broadcast_to(lat, p.shape); lon3 = np.broadcast_to(lon, p.shape)
    ptrop = 10000. + 20000. * np.sin(lat3) ** 2
    cond = sum(w[v] for v in COND)
    S = (2.0 + 1.0 * 0.5 * (1 + np.tanh((x - 0.85) / 0.03))
         - 0.6 * 0.5 * (1 + np.tanh((ptrop - p) / (0.1 * ptrop)))
         + 0.5 * np.sin(3 * lon3) * np.cos(lat3) ** 2
         + 0.4 * np.tanh(np.rad2deg(lat3) / 5.)
         + 1.5 * np.minimum(1., cond / 1e-4)
         + 0.5 * np.minimum(1., np.maximum(w['sphum'], 0.) / 0.015))
    plume = np.where((np.cos(lon3 - np.deg2rad(100.)) > 0.3) & (np.abs(np.rad2deg(lat3) - 10.) < 35.) & (x > 0.3),
                     (np.cos(lon3 - np.deg2rad(100.)) - 0.3) * np.minimum(1., (x - 0.3) / 0.2) * 3.0, 0.)
    fields = {'pt_dyn_nopbl': 1e-6 * S, 'pt_cnv': 1e-6 * S, 'pt_plume': 1e-6 * plume,
              'pt_umoist': np.full_like(S, 1e-6), 'pt_ghg': 1e-6 * S,
              'pt_udry': 1e-6 * (1. - sum(w[v] for v in WAT))}
    with nc.Dataset(fi) as a, nc.Dataset(fo, 'w', format=a.data_model) as b:
        b.setncatts(a.__dict__)
        for n, d in a.dimensions.items():
            b.createDimension(n, None if d.isunlimited() else len(d))
        for n, v in a.variables.items():
            o = b.createVariable(n, v.datatype, v.dimensions)
            o.setncatts(v.__dict__); o[:] = v[:]
        for n, f in fields.items():
            o = b.createVariable(n, 'f4', ('lev', 'lat', 'lon'))
            o.setncatts({'coordinates': 'geolon geolat'}); o[:] = f.astype('f4')
    print(t, ' '.join(f'{n}:{f.min():.3e}/{f.max():.3e}' for n, f in fields.items()))
