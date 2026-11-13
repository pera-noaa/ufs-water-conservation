#!/usr/bin/env python3
"""Exact physics/dynamics split of the global water budget from the in-model whole-physics meter (instrument_wb_phys.py).
Usage: python3 phys_meter_budget.py <RUNDIR> [<RUNDIR> ...]     (WB_WINDOW, WB_END as in water_budget_by_scheme.py)
Reads the srun-labelled 'N: WBP kdt sum(dW*area) sum(dW) sum(area)' lines from RUNDIR/out, sums them over ranks at
each kdt, and per window (snapshot atmfHHH = after step HHH*3600/dt; atmf000 = after step 1) prints, in kg/m2:
  M = water the physics added (meter), dW = snapshot change, E, P (buckets), and
  R_phys = M - (E - P), R_dyn = dW - M (dynamics + physics->dynamics coupling), R_total = dW - (E - P).
Area weights are the model's own cell areas (the meter's sum(area)/kdt); the snapshot side uses INPUT/C*_grid areas
and the two totals are printed so a mismatch is visible."""
import glob
import os
import re
import sys
from collections import defaultdict

import numpy as np
from netCDF4 import Dataset

WIN, END = int(os.environ.get("WB_WINDOW", 6)), int(os.environ.get("WB_END", 24))
G, HVAP = 9.80665, 2.5e6
SP = ["spfh", "clwmr", "icmr", "rwmr", "snmr", "grle"]
# output dpres is delp*(1 - condensate), the physics' dry+vapour thickness (fv_nggps_diag.F90, GFS_PHYS); q is per total mass


def v(d, name):
    return np.asarray(d[name][:], float).squeeze()


def run(rd):
    A = {}
    for t in range(1, 7):
        g = glob.glob(f"{rd}/INPUT/C*_grid.tile{t}.nc")
        if len(g) != 1:
            sys.exit(f"ABORT: expected one INPUT/C*_grid.tile{t}.nc in {rd}, found {g}")
        a = v(Dataset(g[0]), "area")
        A[t] = a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
    atot = sum(a.sum() for a in A.values())
    m = re.search(r"dt_atmos\s*[:=]\s*(\d+)", open(f"{rd}/model_configure").read())
    dt = int(m.group(1))

    wbp, nr = defaultdict(lambda: np.zeros(3)), defaultdict(int)
    for line in open(f"{rd}/out", errors="replace"):
        mm = re.match(r"\s*\d+:\s+WBP\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if mm:
            k = int(mm.group(1))
            wbp[k] += np.array([float(x) for x in mm.group(2, 3, 4)])
            nr[k] += 1
    if not wbp:
        sys.exit(f"ABORT: no WBP lines in {rd}/out")
    ranks = set(nr.values())
    if len(ranks) != 1:
        sys.exit(f"ABORT: unequal rank counts per kdt: {sorted(ranks)}")
    kmax = max(wbp)
    amodel = wbp[kmax][2] / kmax

    def W(fh):
        s = 0.0
        for t in range(1, 7):
            d = Dataset(f"{rd}/atmf{fh:03d}.tile{t}.nc")
            s += ((sum(v(d, k) for k in SP) * v(d, "dpres") / (1.0 - sum(v(d, k) for k in SP[1:]))).sum(0) / G * A[t]).sum()
        return s / atot

    def sfc(fh, name):
        return sum((v(Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc"), name) * A[t]).sum() for t in range(1, 7)) / atot * WIN * 3600

    def step(fh):
        return max(1, fh * 3600 // dt)

    print(f"\n### {rd}  (ranks {ranks.pop()}, dt {dt} s, steps 1-{kmax}; area model {amodel:.6e} grid {atot:.6e} m2)")
    print("window |  M        dW       E        P       | R_phys    R_dyn     R_total  | R_phys/P R_dyn/P R_tot/P")
    for fh in range(WIN, END + 1, WIN):
        k0, k1 = step(fh - WIN), step(fh)
        if k0 not in wbp or k1 not in wbp:
            sys.exit(f"ABORT: meter has no kdt {k0} or {k1}")
        M = (wbp[k1][0] - wbp[k0][0]) / amodel
        dW = W(fh) - W(fh - WIN)
        E, P = sfc(fh, "lhtfl_ave") / HVAP, sfc(fh, "prateb_ave")
        rp, rd_, rt = M - (E - P), dW - M, dW - (E - P)
        print(f"{fh-WIN:3d}-{fh:3d} | {M:+.5f} {dW:+.5f} {E:.5f} {P:.5f} | {rp:+.6f} {rd_:+.6f} {rt:+.6f} | "
              f"{100*rp/P:+.3f}% {100*rd_/P:+.3f}% {100*rt/P:+.3f}%")


for rd in sys.argv[1:]:
    run(rd)
