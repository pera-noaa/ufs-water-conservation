"""deepcnt.py RUN fh : columns with nonzero deep-convection qv tendency (dtend_qv_deepcnv) over 6 tiles."""
import sys, numpy as np, netCDF4 as nc
n = tot = 0
for t in range(1, 7):
    f = nc.Dataset(f"{sys.argv[1]}/sfcf{sys.argv[2]}.tile{t}.nc")
    v = np.ma.filled(f["dtend_qv_deepcnv"][:], 0.0)
    col = (v != 0).reshape(-1, v.shape[-2], v.shape[-1]).any(axis=0)
    n += int(col.sum()); tot += col.size
print(f"{sys.argv[1]}: deep-convective columns {n}/{tot}")
