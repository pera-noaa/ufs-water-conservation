#!/usr/bin/env python3
"""TOPT gate table. usage: topt_table.py <ref run> <ctl1:ctlc999 pair> <run> ...   (run dirs under cwd)
Per run: energy rows from eb_table.py (W m-2, 24 h means) and f24 differences vs <ref> (T rms K, ps rms Pa, LH rms
W m-2), with the ctlc999 noise control (same differences, <ctlc999> vs its own consv_te=1 twin = <ref>)."""
import sys
import subprocess
import os
import numpy as np
from netCDF4 import Dataset

B = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
ref, ctl, runs = sys.argv[1], sys.argv[2], sys.argv[3:]
ROWS = {"2->3 dcyc2t3": "rad", "4->5 PBL": "PBL", "5->6 GWD": "GWD", "ALL physics": "phys",
        " coupling: E_D(6)-E_D(4) - dE_P": "cpl", "residual total": "resid"}


def energy(run):
    if not os.path.exists(f"{run}/out"):
        return {}
    txt = subprocess.run([PY, "-I", f"{B}/eb_table.py", f"{run}/out"], capture_output=True, text=True).stdout
    r = {}
    for line in txt.splitlines():
        for k, nm in ROWS.items():
            if line.startswith(k):
                if "r=dE-F" in line:
                    r[nm] = float(line.split("r=dE-F")[1].split()[0])
                else:
                    r[nm] = float(line.split()[-1])
    return r


def diff(a, b):
    out = []
    for kind, v in (("atm", "tmp"), ("sfc", "pressfc"), ("sfc", "lhtfl_ave")):
        ss, n = 0.0, 0
        try:
            for t in range(1, 7):
                x = Dataset(f"{a}/{kind}f024.tile{t}.nc")[v][:].astype(np.float64)
                y = Dataset(f"{b}/{kind}f024.tile{t}.nc")[v][:].astype(np.float64)
                ss += float(((y - x) ** 2).sum()); n += x.size
            out.append(np.sqrt(ss / n))
        except (OSError, KeyError, IndexError):
            out.append(float("nan"))
    return out


print("run          rad r        PBL r        GWD r        phys r       coupling     RESIDUAL   | f24 vs ref: T rms  ps rms  LH rms")
c1, c2 = ctl.split(":")
for run in [ref, ctl] + runs:
    e = energy(run if run != ctl else c2)
    d = diff(c1, c2) if run == ctl else (diff(ref, run) if run != ref else [0.0, 0.0, 0.0])
    print(f"{run:12s} " + " ".join(f"{e.get(k, float('nan')):+.4e}" for k in ("rad", "PBL", "GWD", "phys", "cpl", "resid"))
          + f" | {d[0]:.4f} {d[1]:.3f} {d[2]:.3f}")
