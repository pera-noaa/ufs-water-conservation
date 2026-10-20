#!/usr/bin/env python3
"""Emulate atmosphere_state_update's 32-bit physics->dycore tracer write-back in numpy on one atmf tile and report its mass bias.
Usage: python3 fix_writeback_emulate.py <atmfHHH.tileN.nc> [perturb]   (perturb: relative physics change applied to water and tracers)"""
import sys

import numpy as np
from netCDF4 import Dataset

f32, f64 = np.float32, np.float64
d = Dataset(sys.argv[1])
pert = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
W = ["spfh", "clwmr", "icmr", "rwmr", "snmr", "grle"]
T = ["trpa", "trpb"]
g = lambda v: np.asarray(d[v][:]).squeeze().astype(f32)          # (k top->bottom, y, x), float32 as the dycore holds it
dp4 = g("dpres")
q4 = {v: g(v) for v in W + T}
# statein (real*8): tracer mass, dry+vapour thickness, GFS mixing ratio
m = {v: f64(q4[v]) * f64(dp4) for v in W + T}
s = f64(dp4) - sum(m[v] for v in W[1:])
ptop = 0.999                                                       # value immaterial: prsi rounding is real*8
prsi = ptop + np.cumsum(s, axis=0)                                 # top -> bottom, interface below layer k
prsi_top = np.concatenate([np.full((1,) + s.shape[1:], ptop), prsi[:-1]])
dpp = prsi - prsi_top                                              # prsi(k)-prsi(k+1) in GFS order
qgrs = {v: m[v] / s for v in W + T}
rng = np.random.default_rng(1)
gq0 = {v: qgrs[v] * (1.0 + pert * rng.standard_normal(qgrs[v].shape)) for v in W + T}
# write-back, as in the source: qwat real*8, dry part real*4, q0 real*8, delp and q stored real*4
qwat = {v: dpp * gq0[v] for v in W + T}
qt = sum(qwat[v] for v in W)
sw4 = np.zeros_like(dp4)
for v in W:                                                        # Fortran sum(): sequential real*4
    sw4 = f32(sw4 + q4[v])
dry4 = f32(dp4 * f32(f32(1.0) - sw4))
q0 = f64(dry4) + qt
dpn = f32(q0)
for v in T + ["spfh"]:
    qn = f32(qwat[v] / q0)
    tgt = qwat[v].sum()
    err = f64(qn) * f64(dpn) - qwat[v]
    eq = (f64(qn) - qwat[v] / q0) * q0
    ed = f64(qn) * (f64(dpn) - q0)
    eb = f64(f32(qwat[v] / f64(dpn))) * f64(dpn) - qwat[v]                       # fix B: divide by the stored delp
    q0c = f64(dp4) * (1.0 - sum(f64(q4[w]) for w in W)) + qt                      # fix C: real*8 dry mass
    ec = f64(f32(qwat[v] / q0c)) * f64(f32(q0c)) - qwat[v]
    top = qwat[v][:40].sum()
    print(f"{v:6s} rel err {err.sum()/tgt:+.3e} (top40 {err[:40].sum()/tgt:+.3e})  q-round {eq.sum()/tgt:+.3e}"
          f"  delp-round {ed.sum()/tgt:+.3e}  fixB {eb.sum()/tgt:+.3e}  fixC {ec.sum()/tgt:+.3e}"
          f"  |err| {np.abs(err).sum()/tgt:.2e} |fixB| {np.abs(eb).sum()/tgt:.2e}  cells |fixB|>|err| {np.mean(np.abs(eb)>np.abs(err)*(1+1e-12)):.1e}"
          f"  top40 mass share {top/tgt:.3f}")
wt = sum(f64(f32(qwat[v] / q0)) for v in W) * f64(dpn)
print(f"water  rel err {(wt.sum()-qt.sum())/qt.sum():+.3e};  dry mass rel change {((f64(dpn)-qt).sum()-(f64(dp4)-sum(m[v] for v in W)).sum())/f64(dp4).sum():+.3e}")
