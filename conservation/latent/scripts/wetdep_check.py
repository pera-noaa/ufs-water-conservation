#!/usr/bin/env python3
"""Exported bucket field vs in-model meter: sum over tiles/buckets of cnv_wetdep_<tr> * cell area against the TX deep +
shallow booked deposition. usage: wetdep_check.py <rundir> [fh list, default 6 12 18 24]"""
import sys
import re
import numpy as np
from netCDF4 import Dataset
rd = sys.argv[1]
fhs = [int(x) for x in sys.argv[2:]] or [6, 12, 18, 24]
area = []
for t in range(1, 7):
    a = Dataset(f"{rd}/INPUT/C96_grid.tile{t}.nc")["area"][:].astype(np.float64)
    area.append((a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]) * (6371200.0 / 6371000.0) ** 2)  # grid file R=6371.0 km, model 6371.2 km
TX = {}
for line in open(f"{rd}/out", errors="replace"):
    m = re.search(r"\bTX +(\d+ .*)$", line)
    if m:
        f = m.group(1).split(); TX[int(f[0])] = [float(x) for x in f[1:]]
nst = max(TX)
for n, tr in ((1, "pt_ghg"), (2, "pt_udry")):
    tot = 0.0
    per = []
    for fh in fhs:
        s = sum(float((Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc")[f"cnv_wetdep_{tr}"][0].astype(np.float64) * area[t - 1]).sum())
                for t in range(1, 7))
        per.append(s); tot += s
    d = sum(TX[s][2 + n - 1] + TX[s][12 + n - 1] for s in TX)
    k = nst // len(fhs)
    dper = [sum(TX[s][2 + n - 1] + TX[s][12 + n - 1] for s in TX if (i * k < s <= (i + 1) * k)) for i in range(len(fhs))]
    print(f"{tr}: exported sum {tot:.7e} kg, meter {d:.7e} kg, rel {(tot - d) / d:+.3e}; per bucket rel "
          + " ".join(f"{(a - b) / b:+.1e}" for a, b in zip(per, dper)))
