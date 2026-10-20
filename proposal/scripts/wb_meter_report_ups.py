#!/usr/bin/env python3
"""Physics closure (WBP/WBQ) and Thompson stage split (WBT) from the upstream meters (instrument_wb_*_ups.py).
Usage: python3 wb_meter_report_ups.py <RUNDIR> [<RUNDIR> ...]     (env WB_AT="30 120": the steps to report)
Sums the srun-labelled lines over ranks at each kdt (all cumulative through kdt; one line per rank and kdt is kept).
R = dW - (E_add + H - P) as an area mean (kg/m2; v1's ep_meter_budget.py definition). WBT slots are global means per
column (unweighted, kg/m2): the sum over columns and steps divided by the columns per step."""
import os
import re
import sys
from collections import defaultdict

import numpy as np

NAMES = {1: "entry stage", 3: "source/sink", 4: "cond/evap", 5: "sedimentation", 6: "final stage", 7: "TOTAL",
         8: "qv floor at exit", 9: "negatives before exit exchange", 10: "tiny positives before exit exchange",
         11: "entry: 0<q<=R1 zeroed (loss)", 13: "entry: q<0 zeroed (source)", 14: "sed rain", 15: "sed cloud",
         16: "sed ice", 17: "sed snow", 18: "sed graupel", 19: "melt/freeze block", 20: "SL floor raise (source)",
         21: "SL inputs <= R1 excluded (loss)", 22: "SL transport non-conservation",
         26: "entry tiny loss qc", 27: "entry tiny loss qi", 28: "entry tiny loss qr", 29: "entry tiny loss qs",
         30: "entry tiny loss qg", 31: "rain overwrite: remainder deleted (loss)"}


def load(rd):
    d = defaultdict(dict)
    for line in open(f"{rd}/out", errors="replace"):
        mm = re.match(r"\s*(\d+):\s+(WBP|WBQ|WBT)\s+(\d+)\s+(.*)", line)
        if mm:
            d[(mm.group(2), int(mm.group(3)))][int(mm.group(1))] = np.array([float(x) for x in mm.group(4).split()])
    return d


def tot(d, tag, k):
    v = d.get((tag, k))
    if not v:
        return None, 0
    a = np.array(list(v.values()))
    s = a.sum(0)
    if tag == "WBQ":
        s[5] = a[:, 5].max()
    if tag == "WBT":
        s[24] = a[:, 24].max()
    return s, len(v)


def run(rd):
    d = load(rd)
    ks = sorted({k for (t, k) in d if t == "WBP"})
    if not ks:
        sys.exit(f"ABORT {rd}: no WBP lines")
    ranks = max(len(d[("WBP", k)]) for k in ks)
    at = [int(x) for x in os.environ.get("WB_AT", "30 60 90 120").split()]
    at = [k for k in at if k in ks] or [ks[-1]]
    p1, _ = tot(d, "WBP", ks[0])
    print(f"### {rd}  (ranks {ranks}, steps {ks[0]}-{ks[-1]})")
    for k in at:
        p, n1 = tot(d, "WBP", k)
        q, n2 = tot(d, "WBQ", k)
        t, n3 = tot(d, "WBT", k)
        if min(n1, n2, n3) != ranks:
            print(f"  kdt {k}: incomplete ({n1}, {n2}, {n3} ranks)")
            continue
        a = p[2] / k
        R = (p[0] - (q[0] + q[3] - q[2])) / a
        ncol = t[11] / k
        print(f"  kdt {k:4d}: R {R:+.3e} kg/m2 (sum of column R {q[6]/a:+.3e}); P {q[2]/a:.4e}; "
              f"max |R| column {q[5]:.3e}; sum |R| {q[4]/a:.3e}; E_add-E_book {(q[0]-q[1])/a:+.2e}")
        print(f"            WBT per column (cols/step {ncol:.0f}); max |col total| {t[24]:.3e}; "
              f"entry tiny zeroings {t[22]:.0f}; no_micro cols {t[23]/k:.0f}/step")
        if len(t) > 31:
            print(f"            rain qrten overwrites {t[31]/k:.0f}/step")
        for i in sorted(n for n in NAMES if n <= len(t)):
            print(f"      {i:2d} {NAMES[i]:38s} {t[i-1]/ncol:+.4e}")
        print(f"         check 1+3+4+5+6 = {(t[0]+t[2]+t[3]+t[4]+t[5])/ncol:+.4e};  14..19 = {t[13:19].sum()/ncol:+.4e};"
              f"  SL 20-21+22 = {(t[19]-t[20]+t[21])/ncol:+.4e};  13-11 = {(t[12]-t[10])/ncol:+.4e}")


for rd in sys.argv[1:]:
    run(rd)
