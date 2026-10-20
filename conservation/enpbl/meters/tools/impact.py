#!/usr/bin/env python3
"""Forecast impact of a run vs a reference, next to a noise control, by land/sea x day/night.
usage: impact.py <ref run> <test run> <control run> [start UTC hour, default from model_configure]
Area weights and longitude from INPUT/C96_grid.tile*.nc. Local solar time = UTC + lon/15;
day = LST 08-16, night = LST 20-04 (others count only in 'all'). Means are area-weighted.
Prints for each fh: mean(test-ref) and mean(ctl-ref) per category, and rms over all cells."""
import sys
import numpy as np
from netCDF4 import Dataset

ref, tst, ctl = sys.argv[1:4]
start = None
if len(sys.argv) > 4:
    start = float(sys.argv[4])
else:
    for line in open(f"{ref}/model_configure"):
        if line.startswith("start_hour"):
            start = float(line.split(":")[1])
FH = [6, 12, 18, 24]
area, lon = [], []
for t in range(1, 7):
    g = Dataset(f"{ref}/INPUT/C96_grid.tile{t}.nc")
    a = g.variables["area"][:].astype(np.float64)
    area.append(a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])
    lon.append(g.variables["x"][:][1::2, 1::2].astype(np.float64))
area, lon = np.stack(area), np.stack(lon)


def read(run, kind, fh, v):
    return np.stack([Dataset(f"{run}/{kind}f{fh:03d}.tile{t}.nc").variables[v][:].astype(np.float64)[0]
                     for t in range(1, 7)])


land = read(ref, "sfc", 0, "land")
CATS = ["all", "land-day", "land-night", "sea-day", "sea-night"]


def masks(fh, avg):
    utc = (start + fh - (3.0 if avg else 0.0)) % 24.0
    lst = (utc + lon / 15.0) % 24.0
    day = (lst >= 8) & (lst <= 16)
    night = (lst >= 20) | (lst <= 4)
    lnd = land == 1
    return {"all": np.ones_like(lnd), "land-day": lnd & day, "land-night": lnd & night,
            "sea-day": ~lnd & day, "sea-night": ~lnd & night}


def wmean(x, m):
    w = area * m
    return float((x * w).sum() / w.sum())


SFC = {"tmp2m": "K", "hpbl": "m", "spd10m": "m/s", "shtfl_ave": "W/m2", "lhtfl_ave": "W/m2", "tmpsfc": "K"}


def sfcvar(run, fh, v):
    if v == "spd10m":
        return np.hypot(read(run, "sfc", fh, "ugrd10m"), read(run, "sfc", fh, "vgrd10m"))
    return read(run, "sfc", fh, v)


print(f"# ref {ref}\n# test {tst}\n# ctl {ctl}\n# start_hour {start}")
acc = {}
for v, u in SFC.items():
    print(f"\n## {v} [{u}]  per fh: test-ref | ctl-ref   (mean by category; rms all)")
    for fh in FH:
        R = sfcvar(ref, fh, v)
        dT, dC = sfcvar(tst, fh, v) - R, sfcvar(ctl, fh, v) - R
        M = masks(fh, v.endswith("_ave"))
        row = []
        for c in CATS:
            a, b = wmean(dT, M[c]), wmean(dC, M[c])
            acc.setdefault((v, c), []).append((a, b))
            row.append(f"{c} {a:+.3e}|{b:+.3e}")
        rt, rc = np.sqrt(wmean(dT**2, M["all"])), np.sqrt(wmean(dC**2, M["all"]))
        print(f"f{fh:03d} " + "  ".join(row) + f"  rms {rt:.3e}|{rc:.3e}")
print("\n## mean over fh 6-24 (test-ref | ctl-ref)")
for v in SFC:
    print(f"{v:10s} " + "  ".join(f"{c} {np.mean([x[0] for x in acc[(v, c)]]):+.3e}|"
                                  f"{np.mean([x[1] for x in acc[(v, c)]]):+.3e}" for c in CATS))

# PBL temperature profile: bottom 25 levels, mean over fh 6-24
NL = 25
print(f"\n## tmp, bottom {NL} levels (1 = lowest), mean over fh 6-24: test-ref | ctl-ref [K]; mean height [m]")
prof = {c: np.zeros((NL, 2)) for c in CATS}
z = np.zeros(NL)
for fh in FH:
    R = read(ref, "atm", fh, "tmp")[:, ::-1][:, :NL]
    dT = read(tst, "atm", fh, "tmp")[:, ::-1][:, :NL] - R
    dC = read(ctl, "atm", fh, "tmp")[:, ::-1][:, :NL] - R
    dz = -read(ref, "atm", fh, "delz")[:, ::-1][:, :NL]
    zc = np.cumsum(dz, axis=1) - 0.5 * dz
    M = masks(fh, False)
    for k in range(NL):
        z[k] += wmean(zc[:, k], M["all"]) / len(FH)
        for c in CATS:
            prof[c][k] += np.array([wmean(dT[:, k], M[c]), wmean(dC[:, k], M[c])]) / len(FH)
print("k   z(m)  " + "  ".join(f"{c:>21s}" for c in CATS))
for k in range(NL):
    print(f"{k+1:2d} {z[k]:6.0f}  " + "  ".join(f"{prof[c][k,0]:+.2e}|{prof[c][k,1]:+.2e}" for c in CATS))
