"""Tracer mass from history output two ways: the trap (sum q*dpres) and the correct total-mass thickness
(sum q*dpres/(1-sum cond)). usage: may_trap.py <run dir> <tracer> ; area from INPUT/C96_grid.tile*.nc"""
import sys, math, numpy as np, netCDF4 as nc
d, tr = sys.argv[1], sys.argv[2]
area = []
for t in range(1, 7):
    with nc.Dataset(f'{d}/INPUT/C96_grid.tile{t}.nc') as g:
        a = g['area'][:].astype('f8'); area.append(a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])
COND = ['clwmr', 'icmr', 'rwmr', 'snmr', 'grle']
res = {}
for fh in ['000', '006', '012', '018', '024']:
    trap = []; good = []
    for t in range(1, 7):
        with nc.Dataset(f'{d}/atmf{fh}.tile{t}.nc') as a:
            q = a[tr][0].astype('f8'); dp = a['dpres'][0].astype('f8')
            c = sum(a[v][0].astype('f8') for v in COND)
        trap.append((q * dp * area[t - 1]).ravel()); good.append((q * dp / (1 - c) * area[t - 1]).ravel())
    res[fh] = (math.fsum(np.concatenate(trap)) / 9.80665, math.fsum(np.concatenate(good)) / 9.80665)
t0, g0 = res['000']
print(f'{tr}: relative change from f000   trap(sum q*dpres)   correct(sum q*dpres/(1-cond))')
for fh, (t, g) in res.items():
    print(f'  f{fh}  {t/t0-1:+.3e}  {g/g0-1:+.3e}')
