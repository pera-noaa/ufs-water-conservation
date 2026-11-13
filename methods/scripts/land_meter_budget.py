#!/usr/bin/env python3
"""Land <-> atmosphere water hand-off per window from the WBL meters (instrument_wb_land.py), exact.
Usage: python3 land_meter_budget.py <RUNDIR> [<RUNDIR> ...]     (WB_WINDOW, WB_END as elsewhere)
Global-mean kg/m2 per window (steps k0+1..k1; atmfHHH is after step HHH*3600/dt, atmf000 after step 1), and % of global P:
  ET      Noah-MP evapotranspiration debited from the land
  evap    = atmosphere receives - land debits (the hand-off fix D targets), split into
            conv  = what noahmpdrv hands over - land debits (its latent-heat -> water conversion) and
            rho   = atmosphere receives - what noahmpdrv hands over (rho_a of the PBL vs Noah-MP's density)
  prcp    = precipitation Noah-MP used - precipitation the host handed it (same steps)
  lag     = precipitation handed in the window - precipitation the atmosphere removed over land in the window
            (Noah-MP gets each step's precipitation one step later; nets to zero over a run)
  errwat  = Noah-MP's own water-balance error (land storage change - (P - ET - runoff))
  pbl     = water satmedmfvdifq adds / water it books - 1 (all surfaces, unweighted)
Positive = water created."""
import glob
import os
import re
import sys
from collections import defaultdict

import numpy as np
from netCDF4 import Dataset

WIN, END = int(os.environ.get("WB_WINDOW", 6)), int(os.environ.get("WB_END", 24))


def lines(rd, tag, ncol):
    acc, nr = defaultdict(lambda: np.zeros(ncol)), defaultdict(int)
    for line in open(f"{rd}/out", errors="replace"):
        m = re.match(rf"\s*\d+:\s+{tag}\s+(\d+)\s+(.*)", line)
        if m:
            vals = [float(x) for x in m.group(2).split()]
            if len(vals) != ncol:
                sys.exit(f"ABORT: {tag} line with {len(vals)} values: {line.strip()[:80]}")
            acc[int(m.group(1))] += np.array(vals)
            nr[int(m.group(1))] += 1
    if not acc or len(set(nr.values())) != 1:
        sys.exit(f"ABORT: {tag} lines missing or unequal rank counts in {rd}/out")
    return acc


def run(rd):
    A = {}
    for t in range(1, 7):
        a = np.asarray(Dataset(glob.glob(f"{rd}/INPUT/C*_grid.tile{t}.nc")[0])["area"][:], float)
        A[t] = a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
    atot = sum(a.sum() for a in A.values())
    dt = int(re.search(r"dt_atmos\s*[:=]\s*(\d+)", open(f"{rd}/model_configure").read()).group(1))
    wbp, wbl = lines(rd, "WBP", 3), lines(rd, "WBL", 10)
    kp = max(wbp)
    ag = wbp[kp][2] / kp                       # model global area
    kl = max(wbl)
    print(f"\n### {rd}  (land fraction {wbl[kl][6]/kl/ag:.4f}; WBL steps {min(wbl)}-{kl})")
    print("window |   ET      | evap        (conv       rho)       | prcp        lag        | errwat     | "
          "%P: evap    prcp    errwat | pbl")
    for fh in range(WIN, END + 1, WIN):
        k0, k1 = max(1, (fh - WIN) * 3600 // dt), fh * 3600 // dt
        d = (wbl[k1] - wbl[k0]) / ag
        P = sum((np.asarray(Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc")["prateb_ave"][:], float).squeeze() * A[t]).sum()
                for t in range(1, 7)) / atot * WIN * 3600
        evap, conv, rho = d[1] - d[0], d[2] - d[0], d[1] - d[2]
        prcp = d[3] - d[4]
        lag = (d[4] - (wbl[k1 + 1][4] - wbl[k0 + 1][4]) / ag) if (k1 + 1) in wbl else float("nan")
        pbl = d[7] / d[8] - 1
        print(f"{fh-WIN:3d}-{fh:3d} | {d[0]:.6f} | {evap:+.2e} ({conv:+.2e} {rho:+.2e}) | {prcp:+.2e} {lag:+.2e} | "
              f"{d[5]:+.2e} | {100*evap/P:+.4f} {100*prcp/P:+.4f} {100*d[5]/P:+.4f} | {pbl:+.1e}")


for rd in sys.argv[1:]:
    run(rd)
