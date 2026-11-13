#!/usr/bin/env python3
"""mynnred: area-weighted 24 h impact of run B vs A, against a noise pair (NB - NA), on the C96 tiles.
usage: impact_aw.py <runA> <runB> <noiseA> <noiseB> <gridINPUTdir>
T: area- and dp-weighted (delp from dpres if present, else level mean); others area-weighted. Also rms ratios."""
import sys
import numpy as np
from netCDF4 import Dataset

a, b, na, nb, gdir = sys.argv[1:6]
area = []
for t in range(1, 7):
    with Dataset(f"{gdir}/C96_grid.tile{t}.nc") as g:
        s = np.asarray(g.variables["area"][:], dtype="f8")
    area.append(s[0::2, 0::2] + s[1::2, 0::2] + s[0::2, 1::2] + s[1::2, 1::2])
area = np.stack(area)  # (6, 96, 96)
W = area / area.sum()


def load(r, kind, v):
    out = []
    for t in range(1, 7):
        with Dataset(f"{r}/{kind}f024.tile{t}.nc") as d:
            if v not in d.variables:
                return None
            out.append(np.asarray(d.variables[v][0], dtype="f8"))
    return np.stack(out)


F = [("atm", "tmp"), ("atm", "spfh"), ("sfc", "pressfc"), ("sfc", "prate_ave"), ("sfc", "lhtfl_ave"),
     ("sfc", "shtfl_ave"), ("sfc", "tmp2m"), ("sfc", "pwat")]
print(f"{'field':10s} {'aw mean B-A':>12s} {'aw mean NB-NA':>13s} {'aw rms B-A':>11s} {'aw rms N':>11s} {'ratio':>6s}")
for kind, v in F:
    xa, xb, ya, yb = (load(r, kind, v) for r in (a, b, na, nb))
    if xa is None:
        continue
    if xa.ndim == 4:  # (tile, lev, y, x)
        dp = load(a, "atm", "dpres")
        w = (W[:, None] * dp) / np.sum(W[:, None] * dp) if dp is not None else np.broadcast_to(W[:, None], xa.shape) / xa.shape[1]
    else:
        w = W
    d1, d2 = xb - xa, yb - ya
    m1, m2 = np.sum(w * d1), np.sum(w * d2)
    r1, r2 = np.sqrt(np.sum(w * d1**2)), np.sqrt(np.sum(w * d2**2))
    print(f"{v:10s} {m1:+12.4e} {m2:+13.4e} {r1:11.4e} {r2:11.4e} {r1/r2:6.2f}")
