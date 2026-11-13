#!/usr/bin/env python3
"""imp24.py <ctl> <exp> : land (land==1) 0-24 h mean of the four 6 h buckets (evcw, sbsno, lhtfl) and the mean of the
f06..f24 instants (tmp2m, spfh2m), exp - ctl: % of control (K for tmp2m), plus the 18-24 h bucket / f24 value."""
import sys
import numpy as np
from netCDF4 import Dataset
a, b = sys.argv[1:3]
def ld(r, fh, v):
    return np.concatenate([Dataset(f"{r}/sfcf{fh:03d}.tile{t}.nc").variables[v][:].astype(float).ravel() for t in range(1, 7)])
m = ld(a, 24, "land") == 1
out = []
for v in ("evcw_ave", "sbsno_ave", "lhtfl_ave", "tmp2m", "spfh2m"):
    c = [ld(a, fh, v)[m].mean() for fh in (6, 12, 18, 24)]; e = [ld(b, fh, v)[m].mean() for fh in (6, 12, 18, 24)]
    if v == "tmp2m":
        out.append(f"{v} {np.mean(e)-np.mean(c):+.3f}K (f24 {e[3]-c[3]:+.3f})")
    else:
        out.append(f"{v} {100*(np.mean(e)/np.mean(c)-1):+.2f}% (f24 {100*(e[3]/c[3]-1):+.2f})")
print(" | ".join(out))
