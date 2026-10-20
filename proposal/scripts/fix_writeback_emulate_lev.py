#!/usr/bin/env python3
"""Per-level breakdown of the emulated 32-bit write-back delp rounding (fix_writeback_emulate.py) on one atmf tile.
Usage: python3 fix_writeback_emulate_lev.py <atmfHHH.tileN.nc> [perturb]"""
import sys

import numpy as np
from netCDF4 import Dataset

f32, f64 = np.float32, np.float64
d = Dataset(sys.argv[1])
pert = float(sys.argv[2]) if len(sys.argv) > 2 else 1e-7
W = ["spfh", "clwmr", "icmr", "rwmr", "snmr", "grle"]
g = lambda v: np.asarray(d[v][:]).squeeze().astype(f32)
dp4 = g("dpres")
q4 = {v: g(v) for v in W + ["trpa", "trpb"]}
m = {v: f64(q4[v]) * f64(dp4) for v in q4}
s = f64(dp4) - sum(m[v] for v in W[1:])
qgrs = {v: m[v] / s for v in q4}
rng = np.random.default_rng(1)
gq0 = {v: qgrs[v] * (1.0 + pert * rng.standard_normal(s.shape)) for v in q4}
qwat = {v: s * gq0[v] for v in q4}
qt = sum(qwat[v] for v in W)
sw4 = np.zeros_like(dp4)
for v in W:
    sw4 = f32(sw4 + q4[v])
x4 = f32(f32(1.0) - sw4)
dry4 = f32(dp4 * x4)
q0 = f64(dry4) + qt
e2 = (f64(f32(q0)) - q0) / q0
exact_dry = f64(dp4) - sum(m[v] for v in W)
a = (f64(x4) - (1.0 - sum(f64(q4[v]) for v in W)))          # rounding of 1 - sum, absolute
b = (f64(dry4) - f64(dp4) * f64(x4)) / f64(dp4)              # rounding of the product, relative
ta = qwat["trpa"].sum()
print(" k   dp4(mean)    S(mean)    E[1-S round]  E[prod round]  E[e2]        trpa-weighted e2 contrib")
for k in range(0, dp4.shape[0], 1):
    c = (qwat["trpa"][k] * e2[k]).sum() / ta
    if k < 30 or k % 8 == 0 or abs(c) > 2e-11:
        print(f"{k:3d} {dp4[k].mean():11.4e} {sw4[k].mean():10.3e} {a[k].mean():+.3e}   {b[k].mean():+.3e}   {e2[k].mean():+.3e}  {c:+.3e}"
              f"  sd(dp4)/mean {dp4[k].std()/dp4[k].mean():.1e}")
print("total trpa", (qwat["trpa"] * e2).sum() / ta)
