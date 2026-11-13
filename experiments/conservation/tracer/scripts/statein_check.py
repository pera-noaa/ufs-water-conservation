"""Offline replica of atmos_phys_driver_statein's tracer conversion on a double-precision restart, to explain
the dyn->phys mass error. usage: statein_check.py <RESTART dir> <prefix e.g. 20210323.060000.> [tracer=pt_cnv]
Unweighted by area (mechanism check). Prints relative J-I with prsl (base) and with prsi differences (FV2), and
the base error split by whether the column-layer condensate mass is below half an ulp of the interface pressure."""
import sys, math, numpy as np, netCDF4 as nc
d, pre = sys.argv[1], sys.argv[2]; tr = sys.argv[3] if len(sys.argv) > 3 else 'pt_cnv'
COND = ['liq_wat', 'ice_wat', 'rainwat', 'snowwat', 'graupel']
with nc.Dataset(f'{d}/{pre}fv_core.res.nc') as a:
    ptop = float(a['ak'][:].ravel()[0])
tot = {'I': [], 'base': [], 'fv2': [], 'base_tinycond': [], 'base_nocond': [], 'base_bigcond': []}
for t in range(1, 7):
    with nc.Dataset(f'{d}/{pre}fv_core.res.tile{t}.nc') as a:
        delp = a['delp'][0].astype('f8')
    with nc.Dataset(f'{d}/{pre}fv_tracer.res.tile{t}.nc') as a:
        q = a[tr][0].astype('f8'); c = {v: a[v][0].astype('f8') for v in COND}
    assert delp.dtype == np.float64
    x = q * delp                              # qgrs = q * prsl(=delp)
    prsl = delp.copy()
    cm = np.zeros_like(delp)
    for v in COND:
        qc = c[v] * delp
        prsl = prsl - qc
        cm = cm + qc
    P = np.full(delp.shape[1:], ptop)
    jb = np.empty_like(x); jf = np.empty_like(x); half_ulp = np.empty_like(x)
    for k in range(delp.shape[0]):            # top -> bottom, as the flip_vc loop k=npz..1
        Pn = P + prsl[k]
        dp = Pn - P
        jb[k] = (x[k] / prsl[k]) * dp
        jf[k] = (x[k] / dp) * dp
        half_ulp[k] = np.spacing(Pn) / 2
        P = Pn
    eb = jb - x; ef = jf - x
    tot['I'].append(x.ravel()); tot['base'].append(eb.ravel()); tot['fv2'].append(ef.ravel())
    tot['base_nocond'].append(np.where(cm == 0, eb, 0).ravel())
    tot['base_tinycond'].append(np.where((cm > 0) & (cm < half_ulp), eb, 0).ravel())
    tot['base_bigcond'].append(np.where(cm >= half_ulp, eb, 0).ravel())
I = math.fsum(np.concatenate(tot['I']))
for k in ['base', 'fv2', 'base_nocond', 'base_tinycond', 'base_bigcond']:
    v = np.concatenate(tot[k])
    print(f'{k:14s} (J-I)/I = {math.fsum(v)/I:+.3e}   cells nonzero {np.count_nonzero(v):9d}  positive {int((v>0).sum()):9d}')
cm_all = None
