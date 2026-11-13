"""RMS / max |difference| of history fields between two runs. usage: compare_atmf.py <run A> <run B> <fhr> [vars...]"""
import sys, numpy as np, netCDF4 as nc
a, b, fh = sys.argv[1:4]
vs = sys.argv[4:] or ['tmp', 'spfh', 'clwmr', 'dpres', 'ugrd', 'pt_cnv', 'pt_ghg', 'pt_dyn_nopbl', 'pt_umoist']
for v in vs:
    s2 = n = 0; mx = 0.; ref = 0.; ident = True
    for t in range(1, 7):
        with nc.Dataset(f'{a}/atmf{fh}.tile{t}.nc') as A, nc.Dataset(f'{b}/atmf{fh}.tile{t}.nc') as B:
            x = A[v][:].astype('f8'); y = B[v][:].astype('f8')
        d = x - y; ident &= bool((d == 0).all())
        s2 += (d ** 2).sum(); n += d.size; mx = max(mx, abs(d).max()); ref += (x ** 2).sum()
    print(f'{v:14s} rms diff {np.sqrt(s2/n):.3e}  max {mx:.3e}  rms field {np.sqrt(ref/n):.3e}  identical={ident}')
