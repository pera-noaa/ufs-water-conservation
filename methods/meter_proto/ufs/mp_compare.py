#!/usr/bin/env python3
"""Compare the budget-meter prototypes with each other and with the offline history budget.
Usage: mp_compare.py budget <RUNDIR> [...]      BUDGET lines vs the offline native-tile budget, per 6-h window
       mp_compare.py bitcmp <RUNDIR_A> <RUNDIR_B> [fh ...]   every variable of atmf/sfcf (6 tiles), bitwise
Offline budget: W = sum q*dpres/(1-condensate)/g over 6 species, E from lhtfl_ave/hvap, P from prateb_ave (buckets).
Window 0-6 h is skipped (atmf000 is written after step 1)."""
import re
import sys
import numpy as np
from netCDF4 import Dataset

G, HVAP, DT = 9.80665, 2.5e6, 6 * 3600.0
SPECIES = ["spfh", "clwmr", "icmr", "rwmr", "snmr", "grle"]


def offline(rd):
    def area(t):
        a = np.asarray(Dataset(f"{rd}/INPUT/C96_grid.tile{t}.nc")["area"][:], float)
        return a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
    A = {t: area(t) for t in range(1, 7)}
    at = sum(a.sum() for a in A.values())

    def g2(fh, var, s=1.0):
        return sum((np.asarray(Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc")[var][:], float).squeeze() * A[t]).sum()
                   for t in range(1, 7)) / at * s

    def w(fh):
        s = 0.0
        for t in range(1, 7):
            d = Dataset(f"{rd}/atmf{fh:03d}.tile{t}.nc")
            q = sum(np.asarray(d[v][:], float).squeeze() for v in SPECIES)
            dp = np.asarray(d["dpres"][:], float).squeeze()
            dp = dp / (1.0 - (q - np.asarray(d[SPECIES[0]][:], float).squeeze()))
            s += ((q * dp).sum(axis=0) / G * A[t]).sum()
        return s / at
    W = {fh: w(fh) for fh in (6, 12, 18, 24)}
    out = {}
    for fh in (12, 18, 24):
        P, E = g2(fh, "prateb_ave", DT), g2(fh, "lhtfl_ave", DT / HVAP)
        out[fh] = dict(dW=W[fh] - W[fh - 6], E=E, P=P, R=W[fh] - W[fh - 6] - (E - P))
    return out


def budget_lines(rd):
    b = {}
    for line in open(f"{rd}/out", errors="replace"):
        line = re.sub(r"^\s*\d+:\s*", "", line)
        if not line.startswith("BUDGET water"):
            continue
        p = line.split()
        fh, seg, vals = float(p[2]), p[3], [float(x) for x in p[4:9]]
        b.setdefault(round(fh), {})[seg] = vals
    return b


def budget(rds):
    for rd in rds:
        b, off = budget_lines(rd), offline(rd)
        print(f"== {rd}")
        print("window  A:phys res        A:nonphys res     A:H              A total+H         offline R        "
              "A-offline         B:samf res        C:fam_samf res    B-C              C sum - A dW")
        for fh in (12, 18, 24):
            if fh not in b:
                print(f"{fh-6:2d}-{fh:2d}  no BUDGET lines")
                continue
            x = b[fh]
            ap, an = x["A:physics"][2], x["A:non_physics"][2]
            h = x["A:E,Pconv,Pls,H"][3]
            tot = ap + an + h
            bs = x.get("B:samf", [np.nan] * 5)[2]
            cs = x.get("C:fam_samf", [np.nan] * 5)[2]
            cv = x.get("C:sum_vs_A", [np.nan] * 5)[2]
            print(f"{fh-6:2d}-{fh:2d}  {ap:+.6e}     {an:+.6e}     {h:+.6e}    {tot:+.6e}     {off[fh]['R']:+.6e}    "
                  f"{tot-off[fh]['R']:+.6e}     {bs:+.6e}     {cs:+.6e}     {bs-cs:+.3e}       {cv:+.3e}")
        print("window  family residuals (C): pbl, photochem, samf, mp, rest;  A E, Pconv, Pls (kg/m2 per window)")
        for fh in (12, 18, 24):
            if fh in b:
                x = b[fh]
                fam = [x.get(f"C:fam_{k}", [np.nan] * 5)[2] for k in ("pbl", "photochem", "samf", "mp", "rest")]
                e, pc, pl = x["A:E,Pconv,Pls,H"][:3]
                print(f"{fh-6:2d}-{fh:2d}  " + "  ".join(f"{v:+.4e}" for v in fam) +
                      f"   E {e:.5f} Pc {pc:.5f} Pl {pl:.5f}  samf/Pc {100*fam[2]/pc:+.4f}%  mp/Pl {100*fam[3]/pl:+.4f}%")


def bitcmp(a, b, fhs):
    nd = nv = 0
    for fh in fhs:
        for kind in ("atmf", "sfcf"):
            for t in range(1, 7):
                da, db = Dataset(f"{a}/{kind}{fh}.tile{t}.nc"), Dataset(f"{b}/{kind}{fh}.tile{t}.nc")
                for v in da.variables:
                    if v not in db.variables:
                        continue
                    x, y = np.asarray(da[v][:]), np.asarray(db[v][:])
                    nv += 1
                    if x.shape != y.shape or not np.array_equal(x, y, equal_nan=x.dtype.kind in "fc"):
                        nd += 1
                        print(f"DIFF {kind}{fh} tile{t} {v}")
    print(f"bitcmp {a} vs {b}: {nd} of {nv} variable-tiles differ")


if __name__ == "__main__":
    if sys.argv[1] == "budget":
        budget(sys.argv[2:])
    else:
        bitcmp(sys.argv[2], sys.argv[3], sys.argv[4:] or ["024"])
