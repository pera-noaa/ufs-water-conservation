#!/usr/bin/env python3
"""Noah-MP land water balance by storage term, from the WBN meter (instrument_wb_noahmp.py).
Usage: python3 noahmp_balance.py <RUNDIR> [<RUNDIR> ...]     (WB_WINDOW, WB_END as elsewhere)
Mean per land column (mm) per window (steps k0+1..k1), for soil and glacier points:
  within calls: change of canopy, snow, soil, aquifer water from what the driver receives to what it returns;
                P, ET, R; residual = sum of changes - (P - ET - R); errwat (Noah-MP's own check, summed)
  between calls: what the next call receives minus what the previous call returned, per term (anything outside
                 Noah-MP that edits land water)."""
import os
import re
import sys
from collections import defaultdict

import numpy as np

WIN, END = int(os.environ.get("WB_WINDOW", 6)), int(os.environ.get("WB_END", 24))
TERMS = ["can", "snow", "soil", "aq"]


def run(rd):
    acc, nr = defaultdict(lambda: np.zeros(26)), defaultdict(int)
    for line in open(f"{rd}/out", errors="replace"):
        m = re.match(r"\s*\d+:\s+WBN\s+(\d+)\s+(.*)", line)
        if m:
            v = np.array([float(x) for x in m.group(2).split()])
            if v.size != 26:
                sys.exit(f"ABORT: WBN line with {v.size} values")
            acc[int(m.group(1))] += v
            nr[int(m.group(1))] += 1
    if not acc or len(set(nr.values())) != 1:
        sys.exit(f"ABORT: WBN lines missing or unequal rank counts in {rd}/out")
    W = {k: a.reshape(13, 2).T for k, a in acc.items()}  # Fortran wbn(2,13) -> [c][t]
    dt = int(re.search(r"dt_atmos\s*[:=]\s*(\d+)", open(f"{rd}/model_configure").read()).group(1))
    kmax = max(W)
    print(f"\n### {rd}  (steps {min(W)}-{kmax})")
    for c, name in ((0, "soil"), (1, "glacier")):
        ncol = (W[kmax][c][12] - W[kmax - 1][c][12])
        print(f"-- {name}: {ncol:.0f} columns; mm per column per window")
        print("window | within: d_can   d_snow   d_soil   d_aq    | P       ET      R      | resid    errwat  | "
              "between: can     snow     soil     aq")
        for fh in range(WIN, END + 1, WIN):
            k0, k1 = max(1, (fh - WIN) * 3600 // dt), min(fh * 3600 // dt, kmax)
            d = (W[k1][c] - W[k0][c]) / ncol
            within = [d[2 * j + 1] - d[2 * j] for j in range(4)]
            P, ET, R, ew = d[8], d[9], d[10], d[11]
            resid = sum(within) - (P - ET - R)
            # between: in(n+1) - out(n), n = k0..k1-1
            if k1 + 0 in W and k0 - 1 in W:
                between = [((W[k1][c][2 * j] - W[k0][c][2 * j]) - (W[k1 - 1][c][2 * j + 1] - W[k0 - 1][c][2 * j + 1])) / ncol
                           for j in range(4)]
            else:
                between = [float("nan")] * 4
            print(f"{fh-WIN:3d}-{fh:3d} | " + " ".join(f"{x:+.5f}" for x in within) +
                  f" | {P:.4f} {ET:.4f} {R:.4f} | {resid:+.5f} {ew:+.4f} | " + " ".join(f"{x:+.5f}" for x in between))


for rd in sys.argv[1:]:
    run(rd)
