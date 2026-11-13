#!/usr/bin/env python3
"""Report the WBB2 meters of instrument_wbb2.py (per-step means / per-step target from WBB slot 1, or cell fractions).
Usage: python3 instrument_wbb2_report.py <RUNDIR>"""
import re
import sys
from collections import defaultdict

import numpy as np


def read(rd, tag, nv):
    acc, cnt = defaultdict(lambda: np.zeros(nv)), defaultdict(int)
    pat = re.compile(rf"\s*\d+:\s+{tag}\s+(\d+)\s+(\d)\s+(\d)\s+(.*)")
    for ln in open(f"{rd}/out", errors="replace"):
        m = pat.match(ln)
        if m:
            k = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            acc[k] += np.array([float(x) for x in m.group(4).split()])
            cnt[k] += 1
    nr = max(cnt.values())
    return {k: v for k, v in acc.items() if cnt[k] == nr}


rd = sys.argv[1]
W, V = read(rd, "WBB", 12), read(rd, "WBB2", 10)
steps = sorted({k[0] for k in V})
ncell = {1: 40 * 6 * 96 * 96, 2: 87 * 6 * 96 * 96}
for m, nm in ((1, "trpa"), (2, "trpb")):
    for r, rn in ((1, "top 40 layers"), (2, "below")):
        w = np.diff(np.r_[np.zeros((1, 12)), [W[(s, m, r)] for s in steps]], axis=0)
        v = np.diff(np.r_[np.zeros((1, 10)), [V[(s, m, r)] for s in steps]], axis=0)
        t = w[:, 0]
        tm = lambda c: (v[:, c] / t).mean()
        print(f"{nm} {rn:13s} per step / target: current err {(w[:,1]/t).mean():+.3e} | fixC err {(w[:,6]/t).mean():+.3e} ="
              f" unrepresentable cells {tm(1):+.3e} + other cells {tm(2):+.3e} | physics change {tm(0):+.3e}")
        print(f"     cells: physics changed {v[:,4].mean()/ncell[r]:.3f}, of which unrepresentable {v[:,3].mean()/max(v[:,4].mean(),1):.3f};"
              f" physics-no-op cells {v[:,7].mean()/ncell[r]:.3f}: current err there {tm(5):+.3e}, fixC err there {tm(6):+.3e};"
              f" delp moved {v[:,8].mean()/ncell[r]:.3f} of cells, mass effect q_new*(delp_new-delp_old) {tm(9):+.3e}")
