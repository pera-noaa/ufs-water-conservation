#!/usr/bin/env python3
"""Step-by-step double-precision closure of the physics' water from the WBQ meter (instrument_wb_ep.py) and WBP.
Usage: python3 ep_meter_budget.py <RUNDIR> [<RUNDIR> ...]
Sums the srun-labelled WBP and WBQ lines over ranks at each kdt (cumulative through kdt) and prints, as global means
(kg/m2, divided by the meter's own area per step): totals of dW, E_add, E_book, P, H; the global residual
R = dW - (E_add + H - P) per step (max |R_step|) and summed; the column-level sum |R| and max |R|; and E_add - E_book."""
import re
import sys
from collections import defaultdict

import numpy as np


def run(rd):
    acc = {"WBP": defaultdict(lambda: np.zeros(3)), "WBQ": defaultdict(lambda: np.zeros(7))}
    nr = {"WBP": defaultdict(int), "WBQ": defaultdict(int)}
    for line in open(f"{rd}/out", errors="replace"):
        m = re.match(r"\s*\d+:\s+(WBP|WBQ)\s+(\d+)\s+(.*)", line)
        if m:
            tag, k = m.group(1), int(m.group(2))
            v = np.array([float(x) for x in m.group(3).split()])
            if tag == "WBQ":
                acc[tag][k][:6] += np.r_[v[:5], 0.0]
                acc[tag][k][5] = max(acc[tag][k][5], v[5])
                acc[tag][k][6] += v[6]
            else:
                acc[tag][k] += v
            nr[tag][k] += 1
    ks = sorted(set(acc["WBP"]) & set(acc["WBQ"]))
    if not ks:
        sys.exit(f"ABORT {rd}: no WBP/WBQ lines")
    ranks = max(nr["WBQ"].values())
    ks = [k for k in ks if nr["WBQ"][k] == ranks and nr["WBP"][k] == ranks]
    # finalize prints repeat the last kdt: keep one value per kdt (the larger cumulative)
    p = np.array([acc["WBP"][k] for k in ks]) / np.array([[nr["WBP"][k] / ranks] for k in ks])
    q = np.array([acc["WBQ"][k] for k in ks])
    q[:, :5] /= np.array([[nr["WBQ"][k] / ranks] for k in ks])
    q[:, 6] /= np.array([nr["WBQ"][k] / ranks for k in ks])
    area_step = np.diff(np.r_[0.0, p[:, 2]])
    a = np.median(area_step[area_step > 0])
    dW, Ea, Eb, P, H, Rabs, Rcol = p[:, 0], q[:, 0], q[:, 1], q[:, 2], q[:, 3], q[:, 4], q[:, 6]
    R = dW - (Ea + H - P)
    Rs = np.diff(np.r_[0.0, R])
    print(f"### {rd}  (ranks {ranks}, steps {ks[0]}-{ks[-1]}, area per step {a:.6e} m2)")
    print(f"totals (kg/m2):  dW {dW[-1]/a:+.6e}  E_add {Ea[-1]/a:.6e}  P {P[-1]/a:.6e}  H {H[-1]/a:+.6e}")
    print(f"global residual R = dW - (E_add + H - P):  total {R[-1]/a:+.3e}  max |R| in one step {np.abs(Rs).max()/a:.3e}"
          f"  (sum of column R {Rcol[-1]/a:+.3e})")
    print(f"column level:  sum |R| {Rabs[-1]/a:.3e} kg/m2 (area mean, all steps)  max |R| in any column {q[:, 5].max():.3e} kg/m2")
    print(f"boundary layer, added - booked:  {(Ea[-1]-Eb[-1])/a:+.3e} kg/m2  ({(Ea[-1]-Eb[-1])/Eb[-1]:+.2e} of E)")


for rd in sys.argv[1:]:
    run(rd)
