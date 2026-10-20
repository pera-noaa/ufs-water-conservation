#!/usr/bin/env python3
"""Report the instrument_wb_negr_floor.py slots (WBT 86..88) next to the rain exit negatives (50, 55), cumulative at the last kdt.
Usage: python3 instrument_wb_negr_report.py <RUNDIR> [...]  (several run dirs: one line each)"""
import re
import sys
from collections import defaultdict

import numpy as np


def last(rd):
    d, pend = defaultdict(dict), {}
    for line in open(f"{rd}/out", errors="replace"):
        mm = re.match(r"\s*(\d+): (.*)\n?$", line)
        if not mm:
            continue
        r, txt = int(mm.group(1)), mm.group(2)
        if r in pend:
            txt = pend.pop(r) + txt
        elif txt.startswith("WBT ") and len(txt) == 1024:
            pend[r] = txt
            continue
        w = re.match(r"WBT\s+(\d+)\s+(.*)", txt)
        if w:
            d[int(w.group(1))][r] = np.array([float(x) for x in w.group(2).split()])
    k = max(d)
    a = np.array(list(d[k].values()))
    return k, a.shape[0], a.sum(0), a[:, 68].max()


for rd in sys.argv[1:]:
    k, nr, t, mx = last(rd)
    ncol = t[11] / k
    w = lambda i: t[i - 1] / ncol
    line = (f"{rd}: kdt {k} ranks {nr}; qr exit neg {w(50):.4e} kg/m2 in {t[54]:.0f} layers; qg {w(52):.4e}; qi {w(49):.4e};"
            f" qs {w(51):.4e}; slot9 {w(9):.4e}; max exit neg {mx:.3e} kg/kg")
    if len(t) >= 88:
        line += (f"\n   floored-at-sed-start: {w(86):.4e} kg/m2 ({w(86) / w(50) * 100 if w(50) else 0:.2f}%) in {t[86]:.0f}"
                 f" layers, {t[87]:.0f} with deficit <= R1")
    print(line)
