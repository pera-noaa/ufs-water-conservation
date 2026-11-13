#!/usr/bin/env python3
"""One-line impact summary of run B vs run A at f024 (C96 cells near-equal: unweighted means).
Usage: impact2.py <runA> <runB> [label]"""
import sys
import numpy as np
from netCDF4 import Dataset
a, b = sys.argv[1], sys.argv[2]
lab = sys.argv[3] if len(sys.argv) > 3 else b.rstrip("/").split("/")[-1]
def ld(r, k, v):
    return np.concatenate([Dataset(f"{r}/{k}f024.tile{t}.nc").variables[v][:].astype(np.float64).ravel() for t in range(1, 7)])
land = ld(a, "sfc", "land") == 1
ice = ld(a, "sfc", "icec") > 0
dT = ld(b, "atm", "tmp") - ld(a, "atm", "tmp")
out = [f"{lab:8s} T rms {np.sqrt((dT*dT).mean()):.3f} mean {dT.mean():+.1e}"]
for v, m, nm in [("tmp2m", land, "t2m_L"), ("tmpsfc", land, "tsfc_L"), ("lhtfl_ave", land, "LH_L"), ("shtfl_ave", land, "SH_L"),
                 ("uswrf_ave", land, "uSW_L"), ("ulwrf_ave", land, "uLW_L"), ("soilt1", land, "soilt1_L"), ("icetk", ice, "icetk_I"),
                 ("prate_ave", np.ones_like(land), "prate")]:
    d = (ld(b, "sfc", v) - ld(a, "sfc", v))[m]
    sc = 86400.0 if v == "prate_ave" else 1.0
    out.append(f"{nm} {d.mean()*sc:+.3f}/{np.sqrt((d*d).mean())*sc:.3f}")
print("  ".join(out))
