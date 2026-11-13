#!/usr/bin/env python3
"""Where the added heating lands, from 'EMZ' lines (instrument_heat_profile.py v2).
Usage: heat_profile.py <run dir> [nsteps=100] [dt=720]
Per pressure band: global mass-weighted mean heating (K/day) of each term, its share of the term's total, and the
max local |dT/dt| (K/day).
Layer mass is the cell-mean dpres of atmf000 (the meter's c6 undercounts: samfdeepcnv returns early in blocks
without convection). Reads v1 (13 values) and v2 (23 values) EMZ lines."""
import sys
import numpy as np
from netCDF4 import Dataset

run = sys.argv[1]
ns = int(sys.argv[2]) if len(sys.argv) > 2 else 100
dt = float(sys.argv[3]) if len(sys.argv) > 3 else 720.0
cp, area = 1004.6, 5.100965e14
rows = {}
for line in open(f"{run}/out", errors="ignore"):
    w = line.split()
    if w and w[0].endswith(":") and w[0][:-1].isdigit():
        w = w[1:]
    if w and w[0] == "EMZ":
        v = [float(x) for x in w[2:]]
        if len(v) == 13:  # v1: c1..c8, x1..x5 -> v2 layout
            v = v[:8] + [0.0] * 6 + v[8:13] + [0.0] * 4
        rows[int(w[1])] = v[:23]
levs = len(rows)
z = np.array([rows[k] for k in range(1, levs + 1)])  # k = 1 bottom
pf = Dataset(f"{run}/atmf000.tile1.nc").variables["pfull"][:][::-1]  # bottom first
dp = np.mean([Dataset(f"{run}/atmf000.tile{t}.nc").variables["dpres"][0].mean(axis=(1, 2)) for t in range(1, 7)],
             axis=0)[::-1]
z[:, 5] = dp / 9.80665 * area * ns  # sum m*area over steps
terms = [("D3A deep", 0, 14), ("D3A shal", 1, 15), ("D3B deep", 2, 16), ("D3B shal", 3, 17), ("D4 GSL", 4, 18),
         ("NGW run", 8, 19), ("NGW -dK", 9, 20), ("D12 diag", 10, 21)]
W = lambda x: x / (area * dt * ns)
print(f"# {run}: {levs} levels, {ns} steps. Totals W m-2: " + "  ".join(f"{n} {W(z[:, c].sum()):+.4e}" for n, c, _ in terms))
print(f"# D3B layer<0 {W(z[:,6].sum()):+.4e}  D3B interface<0 {W(z[:,11].sum()):+.4e}  D3B layer-1 remainder "
      f"{W(z[:,12].sum()):+.3e}  D4 layer<0 {W(z[:,7].sum()):+.4e}")
for hi, lo in ((1100, 850), (850, 500), (500, 200), (200, 50), (50, 10), (10, 1), (1, 0.1), (0.1, 0)):
    k = (pf <= hi) & (pf > lo)
    m = z[k, 5].sum()
    s = f"{hi:6g}-{lo:<4g}hPa"
    for n, c, x in terms:
        s += f" | {n} {z[k, c].sum() / (cp * m) * 86400 / dt:+.2e} K/d mx {z[k, x].max():.1e}"
    print(s)
