"""Copy gfs_data.tile*.nc from <src> to <dst>, multiplying temperature by (1 + amp*N(0,1)) (seeded).
usage: perturb_ic.py <src dir> <dst dir> <seed> [amp=1e-7]"""
import sys, shutil, numpy as np, netCDF4 as nc
src, dst, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]); amp = float(sys.argv[4]) if len(sys.argv) > 4 else 1e-7
rng = np.random.default_rng(seed)
for t in range(1, 7):
    f = f'{dst}/gfs_data.tile{t}.nc'
    shutil.copy(f'{src}/gfs_data.tile{t}.nc', f)
    with nc.Dataset(f, 'a') as a:
        x = a['t'][:].astype('f8')
        y = (x * (1. + amp * rng.standard_normal(x.shape))).astype('f4')
        a['t'][:] = y
        print(t, 'changed cells', int((y != x.astype('f4')).sum()), 'of', x.size)
