#!/usr/bin/env python3
"""Report the WBB write-back meters of instrument_wbb.py per step, per species group and region, against PTM slot 10.
Usage: python3 instrument_wbb_report.py <RUNDIR> [<RUNDIR> ...]"""
import re
import sys
from collections import defaultdict

import numpy as np

GRP = {1: "trpa", 2: "trpb", 3: "sphum", 4: "water"}
REG = {1: "top 40 layers", 2: "below", 0: "all"}


def read(rd, tag, nkey, nv):
    acc, cnt = defaultdict(lambda: np.zeros(nv)), defaultdict(int)
    pat = re.compile(rf"\s*\d+:\s+{tag}\s+" + r"\s+".join([r"(\d+)"] * nkey) + r"\s+(.*)")
    for ln in open(f"{rd}/out", errors="replace"):
        m = pat.match(ln)
        if m:
            k = tuple(int(m.group(i + 1)) for i in range(nkey))
            acc[k] += np.array([float(x) for x in m.group(nkey + 1).split()])
            cnt[k] += 1
    nr = max(cnt.values())
    return {k: v for k, v in acc.items() if cnt[k] == nr}, nr


for rd in sys.argv[1:]:
    W, nr = read(rd, "WBB", 3, 12)
    P, _ = read(rd, "PTM", 2, 15)
    steps = sorted({k[0] for k in W})
    print(f"\n### {rd}: {len(steps)} steps on {nr} ranks; per-step values / per-step target (sum qwat)")
    for m in (1, 2, 3, 4):
        for r in (1, 2, 0):
            rr = (1, 2) if r == 0 else (r,)
            cum = np.array([sum(W[(s, m, x)] for x in rr) for s in steps])
            d = np.diff(np.r_[np.zeros((1, 12)), cum], axis=0)
            t = d[:, 0]
            f = lambda c: d[:, c] / t
            e = f(1)
            line = (f"  {GRP[m]:5s} {REG[r]:13s} err {e.mean():+.3e} sd {e.std():.1e} pos {np.mean(e > 0):4.0%} |"
                    f" delp-store {f(2).mean():+.2e} q-store {f(3).mean():+.2e} dry(r4) {f(4).mean():+.2e} |"
                    f" fixB {f(5).mean():+.3e} (pos {np.mean(f(5) > 0):4.0%}) fixC {f(6).mean():+.3e} |"
                    f" |err| {f(7).mean():.2e} fixB {f(8).mean():.2e} | cells -/+ {d[:,9].sum()/d[:,9:11].sum():.4f}"
                    f" | sum(delp-q0x)/target {f(11).mean():+.2e}")
            print(line)
        if m <= 2:
            ptm = np.array([P[(s, m)][9] for s in steps])
            dp = np.diff(np.r_[0.0, ptm])
            tot = np.diff(np.r_[0.0, np.array([sum(W[(s, m, x)][1] for x in (1, 2)) for s in steps])])
            tg = np.diff(np.r_[0.0, np.array([sum(W[(s, m, x)][0] for x in (1, 2)) for s in steps])])
            print(f"  {GRP[m]:5s} check: PTM write back / target {np.mean(dp/tg):+.3e};  max|PTM(10) - WBB err| / target"
                  f" {np.max(np.abs(dp - tot)/tg):.1e}")
