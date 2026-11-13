#!/usr/bin/env python3
"""Defect D size: vapour the host adds over land (LH/2.5e6) minus water Noah-MP debits (hvap 2.5104e6, hsub 2.844e6).
Usage: python3 noahmp_qfx_excess.py <RUNDIR>
Uses sfcfHHH.tileN.nc: evbs_ave, evcw_ave, trans_ave, sbsno_ave (W/m2), lhtfl_ave, prateb_ave, land. Snow sublimation
(sbsno) is taken at hsub, the rest at hvap (lower bound: Noah-MP uses hsub for ALL ground/canopy/transpiration
fluxes when tg/tv < tfrz). Upper bound: every flux at hsub where tmpsfc < 273.15 K at both window ends.
Prints per 6-h window: global-mean excess (kg/m2) and as % of global P; and land LH-components / lhtfl_ave."""
import sys
import numpy as np
from netCDF4 import Dataset

HOST, HVAP, HSUB, DT = 2.5e6, 2.5104e6, 2.844e6, 6 * 3600.0
rd = sys.argv[1]


def area(t):
    a = np.asarray(Dataset(f"{rd}/INPUT/C96_grid.tile{t}.nc")["area"][:], float)
    return a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]


A = {t: area(t) for t in range(1, 7)}
atot = sum(a.sum() for a in A.values())
print(f"{rd}\nwindow | excess kg/m2 lo..hi     | excess/P lo..hi   | comp/lhtfl(land) | sbsno share of land LH")
for fh in (6, 12, 18, 24):
    ex = exh = p = comp = lh = sb = 0.0
    for t in range(1, 7):
        d = Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc")
        g = lambda n: np.ma.filled(np.ma.masked_invalid(np.ma.asarray(d[n][:], float)), 0.0).squeeze()
        land = g("land") == 1
        for n in ("evbs_ave", "evcw_ave", "trans_ave", "sbsno_ave", "lhtfl_ave"):
            land &= np.abs(g(n)) < 1e10
        evbs, evcw, tr, sbs = g("evbs_ave"), g("evcw_ave"), g("trans_ave"), g("sbsno_ave")
        tot = evbs + evcw + tr
        debit = (evbs - sbs) / HVAP + sbs / HSUB + (evcw + tr) / HVAP
        a = A[t] * land
        ex += ((tot / HOST - debit) * a).sum() * DT
        cold = (g("tmpsfc") < 273.15) & (np.asarray(Dataset(f"{rd}/sfcf{fh-6:03d}.tile{t}.nc")["tmpsfc"][:], float).squeeze() < 273.15)
        exh += ((tot / HOST - np.where(cold, tot / HSUB, debit)) * a).sum() * DT
        comp += (tot * a).sum()
        lh += (g("lhtfl_ave") * a).sum()
        sb += (sbs * a).sum()
        p += (g("prateb_ave") * A[t]).sum() * DT
    print(f"{fh-6:2d}-{fh:2d}  | {ex/atot:+.6f}..{exh/atot:+.6f} | {100*ex/p:+.3f}..{100*exh/p:+.3f}% | {comp/lh:.4f}           | {sb/comp:.3f}")
