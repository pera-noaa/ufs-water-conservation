#!/usr/bin/env python3
"""Report the instrument_wb_neg_stages.py meters (WBT 33..77) per species and stage. Usage: python3 instrument_wb_neg_report.py <RUNDIR> [kdt ... | --fix]
Sums the per-rank cumulative WBT lines (slot 69 is a max); kg/m2 values are divided by the columns per step (slot 12/kdt),
so they are global unweighted per-column totals through kdt; --fix writes <RUNDIR>/rejoined/out for wb_meter_report_ups.py. 'window' rows are the difference between consecutive kdt."""
import re
import sys
from collections import defaultdict

import numpy as np

SP = ("qc", "qi", "qr", "qs", "qg")
rd = sys.argv[1]
# srun splits records longer than 1024 bytes into labelled chunks: rejoin per rank (the WBT record is 1321 bytes)
d = defaultdict(dict)
pend, lines = {}, []
for line in open(f"{rd}/out", errors="replace"):
    mm = re.match(r"(\s*(\d+): )(.*)\n?$", line)
    if not mm:
        lines.append(line)
        continue
    r, txt = int(mm.group(2)), mm.group(3)
    if r in pend:
        txt = pend.pop(r) + txt
    elif txt.startswith("WBT ") and len(txt) == 1024:
        pend[r] = txt
        continue
    lines.append(f"{mm.group(1)}{txt}\n")
    w = re.match(r"WBT\s+(\d+)\s+(.*)", txt)
    if w:
        d[int(w.group(1))][r] = np.array([float(x) for x in w.group(2).split()])
if len(sys.argv) > 2 and sys.argv[2] == "--fix":
    import os
    os.makedirs(f"{rd}/rejoined", exist_ok=True)
    open(f"{rd}/rejoined/out", "w").writelines(lines)
    sys.exit(f"wrote {rd}/rejoined/out")
ks = sorted(d)
DTA = float(re.search(r"dt_atmos:\s*(\S+)", open(f"{rd}/model_configure").read()).group(1))
ranks = max(len(v) for v in d.values())
at = [int(x) for x in sys.argv[2:]] or [1, ks[-1]]


def tot(k):
    a = np.array(list(d[k].values()))
    if len(a) != ranks:
        sys.exit(f"kdt {k}: {len(a)}/{ranks} ranks")
    s = a.sum(0)
    s[68] = a[:, 68].max()
    return s


def show(label, t, k, ncol):
    w = lambda i: t[i - 1] / ncol
    print(f"## {label}  (cols/step {ncol:.0f}; slot 9 {w(9):.4e}; column-steps with an exit negative {t[67]:.0f}"
          f" = {t[67] / (ncol * k) * 100 if k else 0:.3f}% of column-steps)")
    print(f"   {'sp':3s} {'srcsink':>11s} {'cond/evap':>11s} {'sediment':>11s} {'melt/frz':>11s} {'EXIT':>11s}"
          f" {'n layers':>12s} {'k=kts':>11s} {'T>=T0':>11s} {'<500m':>11s}")
    for j, q in enumerate(SP):
        A, B, C, D = w(33 + j), w(38 + j), w(43 + j), w(48 + j)
        print(f"   {q:3s} {A:11.3e} {B - A:+11.3e} {C - B:+11.3e} {D - C:+11.3e} {D:11.3e} {t[52 + j]:12.0f}"
              f" {w(58 + j):11.3e} {w(63 + j):11.3e} {w(71 + j):11.3e}")
    print(f"   cloud-sed layers with vtck*DT > dz: {t[69]:.0f}; overshoot (vt*DT/dz-1)*rc*dz {w(77):.3e};"
          f" cloud-sed surface flux {w(76) * DTA:.3e}; max exit negative so far {t[68]:.3e} kg/kg")
    if len(t) >= 85:
        print(f"   prg_rcs < 0 after the diff-03 closure: {w(78) * DTA:.3e} kg/m2 in {t[78]:.0f} layers;"
              f" exit negatives < -1e-9 kg/kg (layers) " + " ".join(f"{q} {t[79 + j]:.0f}" for j, q in enumerate(SP))
              + f"; qc exit negatives over land {w(85):.3e}")


prev, pk = None, 0
for k in at:
    t = tot(k)
    ncol = t[11] / k
    show(f"{rd}  kdt {k} cumulative", t, k, ncol)
    if prev is not None:
        dt = t - prev
        dt[68] = t[68]
        show(f"window kdt {pk + 1}-{k}", dt, k - pk, ncol)
    prev, pk = t, k
