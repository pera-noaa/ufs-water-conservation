"""D1 offline replay: apply dyn_core's non-hydrostatic heat-block arithmetic to a real restart state and
measure the IE (= TE, delz/u/v/w fixed) change with FV3's own T diagnosis (L2E entry) and cvm (moist_cv nwat=6).
usage: d1_replay.py <RESTART file prefix, e.g. RESTART/20210323.060000.> [tile]"""
import sys
import numpy as np
from netCDF4 import Dataset

rdgas, rvgas, cp_air, grav = 287.05, 461.50, 1004.6, 9.80665
zvir = rvgas / rdgas - 1.
cv_air = cp_air - rdgas
cv_vap, c_ice, c_liq = 3. * rvgas, 1972., 4.1855e3
rdg = -rdgas / grav

rd = sys.argv[1]; tile = sys.argv[2] if len(sys.argv) > 2 else '1'
c = Dataset(f'{rd}fv_core.res.tile{tile}.nc'); t = Dataset(f'{rd}fv_tracer.res.tile{tile}.nc')
g = lambda d, v: np.asarray(d.variables[v][0], dtype=np.float64)
T, delp, delz = g(c, 'T'), g(c, 'delp'), g(c, 'DZ')
qv = g(t, 'sphum'); ql = g(t, 'liq_wat') + g(t, 'rainwat'); qs = g(t, 'ice_wat') + g(t, 'snowwat') + g(t, 'graupel')
qc = ql + qs
cvm = (1. - (qv + qc)) * cv_air + qv * cv_vap + ql * c_liq + qs * c_ice
cappa = rdgas / (rdgas + cvm / (1. + zvir * qv))
fac = (1. + zvir * qv) * (1. - qc)

# pt as dyn_core holds it (fv_dynamics conversion), then dyn_core's own pkz recomputation (self-test)
pkz0 = np.exp(cappa * np.log(rdg * delp * T * fac / delz))
pt = T * fac / pkz0
pkz = np.exp(cappa / (1. - cappa) * np.log(rdg * delp / delz * pt))
print(f'self-test pkz(dyn_core) vs pkz(fv_dynamics): max rel diff {np.max(np.abs(pkz / pkz0 - 1.)):.2e}')

def l2e_T(p):  # fv_mapz L2E entry (kord_tm<0, non-hydrostatic, MOIST_CAPPA): theta_v -> T_dens, then / fac
    return p * np.exp(cappa / (1. - cappa) * np.log(rdg * delp / delz * p)) / fac

w = delp  # mass weight
for h_K in (0.001, 0.01, 0.1):        # heat per unit mass expressed as K at cv_air: h = h_K*cv_air J/kg
    h = h_K * cv_air
    dtmp = h / cv_air                 # = heat_source/(cv_air*delp)
    pt_orig = pt + dtmp / pkz         # dyn_core, unfixed
    r_orig = cvm * (l2e_T(pt_orig) - T) / h
    dT = h / cvm                      # fix (bit 1)
    pt_fix = pt * np.exp((1. - cappa) * np.log(1. + dT / T))
    r_fix = cvm * (l2e_T(pt_fix) - T) / h
    pt_cp = pt + (h / cp_air) / pkz   # alternative one-word fix: cp_air instead of cv_air
    r_cp = cvm * (l2e_T(pt_cp) - T) / h
    pred = (rdgas + cvm / (1. + zvir * qv)) / (cv_air * (1. - qc))   # linear theory for r_orig
    for nm, r in (('orig', r_orig), ('fix', r_fix), ('cp_air', r_cp)):
        print(f'h={h_K:5.3f} K  {nm:6s} dTE/heat: mass-mean {np.sum(r*w)/np.sum(w):.6f}  min {r.min():.6f}  max {r.max():.6f}')
    print(f'h={h_K:5.3f} K  linear theory (R+cvm/(1+zvir qv))/(cv_air(1-qc)): mass-mean {np.sum(pred*w)/np.sum(w):.6f}'
          f'  max|orig-theory| {np.max(np.abs(r_orig-pred)):.2e}')
print(f'dry cp/cv = {cp_air/cv_air:.6f}')
