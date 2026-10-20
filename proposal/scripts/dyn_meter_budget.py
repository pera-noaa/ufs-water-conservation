#!/usr/bin/env python3
"""Split R_dyn (= snapshot dW - physics meter) into dycore pieces with the WBD meters (instrument_wb_dyn.py).
Usage: python3 dyn_meter_budget.py <RUNDIR> [<RUNDIR> ...]     (WB_WINDOW, WB_END as elsewhere; WB_SERIES=N prints
       the per-step pieces for steps 2..N as well)
Per window, kg/m2 (each meter normalised by its own model area):
  fvdyn = fv_dynamics, of which negadj = neg_adj3 | sgz = fv_subgrid_z | upd = fv_update_phys | gaps = (7)+(8), must be 0
  handoff = physics-update write (4) - physics meter, of which fill = fill_gfs (6)
  sum = fvdyn + sgz + upd + gaps + handoff, which must equal R_dyn = dW(snapshots) - physics meter."""
import glob
import os
import re
import sys
from collections import defaultdict

import numpy as np
from netCDF4 import Dataset

WIN, END = int(os.environ.get("WB_WINDOW", 6)), int(os.environ.get("WB_END", 24))
SERIES = int(os.environ.get("WB_SERIES", 0))
G = 9.80665
SP = ["spfh", "clwmr", "icmr", "rwmr", "snmr", "grle"]
# output dpres is delp*(1 - condensate), the physics' dry+vapour thickness (fv_nggps_diag.F90, GFS_PHYS); q is per total mass


def v(d, name):
    return np.asarray(d[name][:], float).squeeze()


def meters(rd, tag, ncol):
    acc, nr = defaultdict(lambda: np.zeros(ncol)), defaultdict(int)
    pat = re.compile(rf"\s*\d+:\s+{tag}\s+(\d+)\s+(.*)")
    for line in open(f"{rd}/out", errors="replace"):
        m = pat.match(line)
        if m:
            vals = [float(x) for x in m.group(2).split()]
            if len(vals) != ncol:
                sys.exit(f"ABORT: {tag} line with {len(vals)} values, expected {ncol}: {line.strip()[:80]}")
            acc[int(m.group(1))] += np.array(vals)
            nr[int(m.group(1))] += 1
    if not acc or len(set(nr.values())) != 1:
        sys.exit(f"ABORT: {tag} lines missing or unequal rank counts in {rd}/out")
    return acc


def run(rd):
    A = {}
    for t in range(1, 7):
        g = glob.glob(f"{rd}/INPUT/C*_grid.tile{t}.nc")
        a = v(Dataset(g[0]), "area")
        A[t] = a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
    atot = sum(a.sum() for a in A.values())
    dt = int(re.search(r"dt_atmos\s*[:=]\s*(\d+)", open(f"{rd}/model_configure").read()).group(1))
    wbp, wbd = meters(rd, "WBP", 3), meters(rd, "WBD", 9)
    kp = max(wbp)
    a_p = wbp[kp][2] / kp
    a_d = wbd[1][8]

    def W(fh):
        s = 0.0
        for t in range(1, 7):
            d = Dataset(f"{rd}/atmf{fh:03d}.tile{t}.nc")
            s += ((sum(v(d, k) for k in SP) * v(d, "dpres") / (1.0 - sum(v(d, k) for k in SP[1:]))).sum(0) / G * A[t]).sum()
        return s / atot

    def pieces(k0, k1):
        d = (wbd[k1] - wbd[k0]) / a_d
        M = (wbp[k1][0] - wbp[k0][0]) / a_p
        return M, d[0], d[1], d[2], d[4], d[6] + d[7], d[3] - M, d[5]

    print(f"\n### {rd}  (area: physics {a_p:.6e}, dycore {a_d:.6e}, grid {atot:.6e} m2)")
    print("window  |  R_dyn      fvdyn     (negadj)   sgz       upd       gaps      handoff   (fill)   | sum - R_dyn")
    for fh in range(WIN, END + 1, WIN):
        k0, k1 = max(1, (fh - WIN) * 3600 // dt), fh * 3600 // dt
        M, fvd, neg, sgz, upd, gaps, hand, fill = pieces(k0, k1)
        rdyn = W(fh) - W(fh - WIN) - M
        tot = fvd + sgz + upd + gaps + hand
        print(f"{fh-WIN:3d}-{fh:3d} | {rdyn:+.6f} {fvd:+.6f} ({neg:+.6f}) {sgz:+.6f} {upd:+.6f} {gaps:+.6f} "
              f"{hand:+.6f} ({fill:+.6f}) | {tot-rdyn:+.1e}")
    if SERIES:
        print("step |  fvdyn      (negadj)   sgz        upd        handoff    (fill)     physics")
        for k in range(2, SERIES + 1):
            M, fvd, neg, sgz, upd, gaps, hand, fill = pieces(k - 1, k)
            print(f"{k:4d} | {fvd:+.3e} ({neg:+.3e}) {sgz:+.3e} {upd:+.3e} {hand:+.3e} ({fill:+.3e}) {M:+.3e}")


for rd in sys.argv[1:]:
    run(rd)
