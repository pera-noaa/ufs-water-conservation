#!/usr/bin/env python3
"""imp_land14.py <ctl> <exp> : canopy's imp24.py statistic (land == 1, mean of the four 6 h buckets of evcw, sbsno, lhtfl;
mean of the f06..f24 instants of tmp2m, spfh2m; exp - ctl as % of control, K for tmp2m, f24 in brackets) plus snow at
f24 on land: weasd (SWE), snod (depth), tsnowp (accumulated snowfall), snowc_ave (cover): mean difference, % of control."""
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
for v in ("weasd", "snod", "tsnowp", "snowc_ave"):
    c = ld(a, 24, v)[m]; e = ld(b, 24, v)[m]
    out.append(f"{v} {e.mean()-c.mean():+.3e} ({100*(e.mean()/c.mean()-1):+.3f}%, rms {np.sqrt(((e-c)**2).mean()):.2e})")
print(" | ".join(out))
