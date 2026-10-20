#!/usr/bin/env python3
"""Item 3: signal of arm B (o3/TKE also sub-stepped) vs arm A, against member spread.
usage: noise.py <rtdir> <file stem atmf024> <members e.g. 0,3,4,5>"""
import sys, numpy as np, netCDF4 as nc
rt, st, mem = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
VARS = ['tmp', 'spfh', 'clwmr', 'icmr', 'rwmr', 'snmr', 'grle', 'o3mr', 'ugrd', 'pressfc']
def load(run):
    out = {}
    lat = []; dp = []
    for t in range(1, 7):
        with nc.Dataset(f'{rt}/{run}/{st}.tile{t}.nc') as f:
            if t == 1:
                have = [v for v in VARS + ['sgs_tke'] if v in f.variables]
            lat.append(np.asarray(f['grid_yt'][:], 'f8'))
            dp.append(np.asarray(f['dpres'][0], 'f8'))
            for v in have:
                out.setdefault(v, []).append(np.asarray(f[v][0], 'f8'))
    lat = np.stack(lat); dp = np.stack(dp)
    return {v: np.stack(x) for v, x in out.items()}, lat, dp
data = {}
for arm in 'AB':
    for m in mem:
        data[arm + m] = load(f'n{arm}{m}')
lat = data['A' + mem[0]][1]
bins = np.digitize(lat, np.arange(-90, 91, 10))
def gm(Q, dp):
    if Q.ndim == 4:
        return np.sum(Q * dp) / np.sum(dp)
    return Q.mean()
def zm(Q, dp):
    """zonal (10 deg) x 4 layer-band dp-weighted means"""
    if Q.ndim == 3:
        return np.array([Q[bins == b].mean() for b in range(1, 19)])
    nk = Q.shape[1]; bands = np.array_split(np.arange(nk), 4)
    r = []
    for bd in bands:
        q = np.sum(Q[:, bd] * dp[:, bd], axis=1) / np.sum(dp[:, bd], axis=1)
        r.append([q[bins == b].mean() for b in range(1, 19)])
    return np.array(r)
for v in data['A' + mem[0]][0]:
    g = {k: gm(x[0][v], x[2]) for k, x in data.items()}
    dA = np.array([g['A' + m] for m in mem]); dB = np.array([g['B' + m] for m in mem])
    d = dB - dA
    sA = dA.std(ddof=1)
    tst = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)) + 1e-300)
    print(f'{v:8s} global mean A {dA.mean():.6e}  B-A paired: mean {d.mean():+.3e} (rel {d.mean()/dA.mean():+.2e}) sd {d.std(ddof=1):.2e} '
          f'| member spread sd(A) {sA:.2e} sd(B) {dB.std(ddof=1):.2e} | paired t {tst:+.2f}')
    z = {k: zm(x[0][v], x[2]) for k, x in data.items()}
    zA = np.array([z['A' + m] for m in mem]); zB = np.array([z['B' + m] for m in mem])
    zd = zB - zA
    sd_noise = zA.std(axis=0, ddof=1)
    t = zd.mean(0) / (zd.std(0, ddof=1) / np.sqrt(len(mem)) + 1e-300)
    out = np.abs(zd.mean(0)) > 2 * sd_noise
    print(f'         zonal cells {t.size}: |mean(B-A)| > 2 sd(A members) in {out.sum()}; |paired t| > 3.18 (p<.05, 3 dof) in {np.sum(np.abs(t) > 3.18)}; '
          f'max |mean d|/sd_noise {np.max(np.abs(zd.mean(0))/(sd_noise+1e-300)):.2f}; max |mean d| {np.max(np.abs(zd.mean(0))):.3e} where t>3.18 {np.max(np.abs(zd.mean(0))*(np.abs(t)>3.18)):.3e}; typical member sd {np.median(sd_noise):.3e}')
