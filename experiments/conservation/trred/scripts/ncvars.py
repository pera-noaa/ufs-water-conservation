import sys, netCDF4 as nc
f = nc.Dataset(sys.argv[1])
print(' '.join(f'{v}{tuple(f[v].shape)}' for v in f.variables))
