"""dpres-weighted global means of history fields (unweighted by area: cubed-sphere cells ~equal; for ensemble spread only).
usage: global_means.py <fhr> <run> [run...]"""
import sys, numpy as np, netCDF4 as nc
fh, runs = sys.argv[1], sys.argv[2:]
vs = ['tmp', 'spfh', 'clwmr', 'pt_cnv', 'pt_ghg']
print('run'.ljust(8) + ''.join(v.rjust(22) for v in vs + ['ps']))
for r in runs:
    acc = {v: 0. for v in vs}; m = 0.; ps = 0.
    for t in range(1, 7):
        with nc.Dataset(f'{r}/atmf{fh}.tile{t}.nc') as a:
            dp = a['dpres'][0].astype('f8'); m += dp.sum(); ps += a['pressfc'][0].astype('f8').mean() / 6
            for v in vs:
                acc[v] += (a[v][0].astype('f8') * dp).sum()
    print(r.ljust(8) + ''.join(f'{acc[v]/m:22.14e}' for v in vs) + f'{ps:22.14e}')
