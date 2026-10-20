"""Replicate FV3's cold-start water steps (external_ic get_nggps_ic + remap_scalar, data_source_fv3gfs) offline.
Usage: python3 coldstart_trace.py <RUNDIR>"""
import glob, sys
import numpy as np
from netCDF4 import Dataset
R = sys.argv[1]; g = 9.80665
SP = ["sphum", "liq_wat", "ice_wat", "rainwat", "snowwat", "graupel"]
vc = np.asarray(Dataset(f"{R}/INPUT/gfs_ctrl.nc")["vcoord"][:], float)   # (2, 129): ak0, bk0 (top->bottom?)
ak0, bk0 = vc[0], vc[1]
if ak0[0] < ak0[-1] and bk0[0] > bk0[-1]: pass
# order so index 0 is the model top
if bk0[0] > bk0[-1]: ak0, bk0 = ak0[::-1], bk0[::-1]
ak, bk = ak0[1:], bk0[1:]          # external_eta: model takes IC interfaces 2..km+1
tot = np.zeros(6); atot = 0.0; dps = 0.0
for t in range(1, 7):
    a = np.asarray(Dataset(glob.glob(f"{R}/INPUT/C*_grid.tile{t}.nc")[0])["area"][:], float)
    A = a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
    d = Dataset(f"{R}/INPUT/gfs_data.tile{t}.nc")
    ps0 = np.asarray(d["ps"][:], float); zh = np.asarray(d["zh"][:], float); delp = np.asarray(d["delp"][:], float)
    q = {s: np.asarray(d[s][:], float) for s in SP}
    phis = np.asarray(Dataset(f"{R}/INPUT/oro_data.tile{t}.nc")["orog_filt"][:], float) * g
    km = delp.shape[0]
    W0 = sum(q[s] * delp for s in SP).sum(0) / g                       # IC as stored
    pe0 = ak0[:, None, None] + bk0[:, None, None] * ps0                 # (km+1, ny, nx)
    W0b = sum(q[s] * np.diff(pe0, axis=0) for s in SP).sum(0) / g      # IC with delp from ak/bk/ps
    # surface pressure on model terrain: interpolate ln p vs gz, mirrored extension below the IC surface
    gz = zh * g; pn = np.log(pe0)
    k2 = max(10, km // 2)
    gze = np.concatenate([gz, 2 * gz[-1:] - gz[-2:-k2 - 1:-1]]); pne = np.concatenate([pn, 2 * pn[-1:] - pn[-2:-k2 - 1:-1]])
    ny, nx = ps0.shape; ps1 = np.empty_like(ps0)
    for j in range(ny):
        for i in range(nx):
            z, p = gze[:, j, i], pne[:, j, i]
            k = np.where((phis[j, i] <= z[:-1]) & (phis[j, i] >= z[1:]))[0][-1]
            ps1[j, i] = np.exp(p[k] + (p[k + 1] - p[k]) * (z[k] - phis[j, i]) / (z[k] - z[k + 1]))
    pe1 = ak[:, None, None] + bk[:, None, None] * ps1
    # conservative remap of each species from pe0 layers to pe1 layers (piecewise constant; constant extension at the bottom)
    def remap(qs):
        out = np.empty((pe1.shape[0] - 1, ny, nx))
        for j in range(ny):
            for i in range(nx):
                e0 = pe0[:, j, i]; e1 = pe1[:, j, i]; v = qs[:, j, i]
                cum = np.concatenate([[0], np.cumsum(v * np.diff(e0))])
                def C(p):
                    p = np.asarray(p)
                    c = np.interp(np.minimum(p, e0[-1]), e0, cum)
                    return c + np.maximum(p - e0[-1], 0) * v[-1]
                out[:, j, i] = np.diff(C(e1)) / np.diff(e1)
        return out
    qn = {s: remap(q[s]) for s in SP}
    dp2 = np.diff(pe1, axis=0)
    W1 = sum(qn[s] * dp2 for s in SP).sum(0) / g
    cond = sum(qn[s] for s in SP[1:])
    W2 = sum(qn[s] * dp2 / (1 - cond) for s in SP).sum(0) / g
    # contributions
    lost_top = sum(q[s][0] * np.diff(pe0, axis=0)[0] for s in SP) / g
    for n, x in enumerate([W0, W0b, W1, W2, lost_top, ps1 - ps0]):
        tot[n] += (x * A).sum()
    atot += A.sum()
tot /= atot
print(f"W_IC (q*delp as stored)        {tot[0]:.5f} kg/m2")
print(f"W_IC (delp from ak0,bk0,ps)    {tot[1]:.5f}  (diff {tot[1]-tot[0]:+.5f})")
print(f"after ps re-derivation + remap {tot[2]:.5f}  (step {tot[2]-tot[1]:+.5f}; top layer dropped {tot[4]:.2e}; mean ps change {tot[5]:+.3f} Pa)")
print(f"after delp/(1-condensate)      {tot[3]:.5f}  (step {tot[3]-tot[2]:+.5f})")
print(f"total initialisation change    {tot[3]-tot[0]:+.5f}  (model print: 24.0596 - W_IC)")
