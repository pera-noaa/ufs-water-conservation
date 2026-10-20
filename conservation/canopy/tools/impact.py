#!/usr/bin/env python3
"""impact.py <ctl run> <exp run> <fh...> : forecast impact, exp - ctl, unweighted cell statistics over 6 tiles.
Global: atm tmp rms (all levels), pressfc rms, lhtfl_ave mean/rms. Land (land==1) and open water (land==0, icec==0):
per field  ctl mean | mean diff | % of ctl mean | rms diff. *_ave fields are means over the 6 h bucket ending at fh."""
import sys
import numpy as np
from netCDF4 import Dataset

a, b = sys.argv[1], sys.argv[2]
LAND = ["evcw_ave", "trans_ave", "sbsno_ave", "evbs_ave", "lhtfl_ave", "shtfl_ave", "tmp2m", "spfh2m", "cnwat", "tmpsfc"]
OCN = ["lhtfl_ave", "shtfl_ave", "tmp_hyblev1", "spfh_hyblev1", "prate_ave"]


def load(run, kind, fh, v):
    return np.concatenate([Dataset(f"{run}/{kind}f{fh:03d}.tile{t}.nc").variables[v][:].astype(np.float64).ravel()
                           for t in range(1, 7)])


for fh in map(int, sys.argv[3:]):
    x, y = load(a, "atm", fh, "tmp"), load(b, "atm", fh, "tmp")
    p, q = load(a, "sfc", fh, "pressfc"), load(b, "sfc", fh, "pressfc")
    l1, l2 = load(a, "sfc", fh, "lhtfl_ave"), load(b, "sfc", fh, "lhtfl_ave")
    print(f"f{fh:03d} GLOBAL T rms {np.sqrt(np.mean((y-x)**2)):.4f} K  ps rms {np.sqrt(np.mean((q-p)**2)):.3f} Pa  "
          f"LH mean {np.mean(l2-l1):+.4f} rms {np.sqrt(np.mean((l2-l1)**2)):.3f} W/m2")
    land = load(a, "sfc", fh, "land")
    ice = load(a, "sfc", fh, "icec")
    for name, m, vs in (("LAND", land == 1, LAND), ("OCEAN", (land == 0) & (ice <= 0), OCN)):
        for v in vs:
            try:
                u, w = load(a, "sfc", fh, v)[m], load(b, "sfc", fh, v)[m]
            except KeyError:
                continue
            c = np.mean(u); d = w - u
            pc = 100 * np.mean(d) / c if c != 0 else float("nan")
            print(f"f{fh:03d} {name:5s} {v:13s} ctl {c:+.4e}  d {np.mean(d):+.4e} ({pc:+.3f} %)  rms {np.sqrt(np.mean(d*d)):.4e}")
