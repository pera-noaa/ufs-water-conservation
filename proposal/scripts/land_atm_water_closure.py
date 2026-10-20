#!/usr/bin/env python3
"""Land-atmosphere water hand-off (defect D): vapour the atmosphere receives over land vs water Noah-MP removes.
Usage: python3 land_atm_water_closure.py <MASK_RUNDIR> <RUNDIR> [<RUNDIR> ...]
Per 6-h window, global-mean kg/m2 and % of global P (prateb_ave):
  gap  = lhtfl_ave/2.5e6 (host evap, what satmedmfvdifq adds) - Noah-MP debit, debit = (evbs-sbsno)/hvap +
         sbsno/hsub + (evcw+trans)/hvap with Noah-MP's hvap 2.5104e6, hsub 2.844e6 (frozen ground/canopy outside the
         snowpack is taken at hvap, so the debit is an upper bound and the gap a lower bound);
  land = land storage budget dS - (P - E) + d(runoff) with S = soilm + weasd + cnwat, E = lhtfl_ave/2.5e6
         (aquifer storage is not output, so this carries the aquifer change; watr_acc is a 6-h bucket).
Cells: land == 1 and, in MASK_RUNDIR's 0-6 h file, Noah-MP latent-heat components within 5 % of lhtfl_ave (drops
lake/fractional cells where lhtfl is not the Noah-MP flux). The same cells are used for every run."""
import sys
import numpy as np
from netCDF4 import Dataset

HOST, HVAP, HSUB, DT = 2.5e6, 2.5104e6, 2.844e6, 6 * 3600.0
mask_rd, rds = sys.argv[1], sys.argv[2:]


def get(d, n):
    return np.ma.filled(np.ma.masked_invalid(np.ma.asarray(d[n][:], float)), np.nan).squeeze()


def area(rd, t):
    a = np.asarray(Dataset(f"{rd}/INPUT/C96_grid.tile{t}.nc")["area"][:], float)
    return a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]


A = {t: area(mask_rd, t) for t in range(1, 7)}
atot = sum(a.sum() for a in A.values())
M = {}
for t in range(1, 7):
    d = Dataset(f"{mask_rd}/sfcf006.tile{t}.nc")
    tot = get(d, "evbs_ave") + get(d, "evcw_ave") + get(d, "trans_ave")
    lh = get(d, "lhtfl_ave")
    with np.errstate(invalid="ignore", divide="ignore"):
        ok = (get(d, "land") == 1) & np.isfinite(tot) & (np.abs(tot) < 1e10) & (np.abs(tot / lh - 1) < 0.05)
    M[t] = ok
print(f"cells: {sum(m.sum() for m in M.values())} land cells, mask from {mask_rd}")

for rd in rds:
    print(f"\n{rd}\nwindow | gap kg/m2  gap/P    | land-budget kg/m2  /P     | P_land share")
    for fh in (6, 12, 18, 24):
        gap = land = p = pl = 0.0
        for t in range(1, 7):
            d1, d0 = Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc"), Dataset(f"{rd}/sfcf{fh-6:03d}.tile{t}.nc")
            m, a = M[t], A[t]
            evbs, evcw, tr, sbs = (get(d1, n) for n in ("evbs_ave", "evcw_ave", "trans_ave", "sbsno_ave"))
            e_atm = get(d1, "lhtfl_ave") / HOST
            debit = (evbs - sbs) / HVAP + sbs / HSUB + (evcw + tr) / HVAP
            prc = get(d1, "prateb_ave")
            gap += np.nansum(((e_atm - debit) * a)[m]) * DT
            stor = lambda d: get(d, "soilm") + get(d, "weasd") + get(d, "cnwat")
            # watr_acc is a 6-h bucket; sfcf000 is after step 1, so the first bucket starts at its value
            dro = get(d1, "watr_acc") - (get(d0, "watr_acc") if fh == 6 else 0.0)
            land += np.nansum(((stor(d1) - stor(d0)) - (prc - e_atm) * DT + dro)[m] * a[m])
            p += np.nansum(prc * a) * DT
            pl += np.nansum((prc * a)[m]) * DT
        print(f"{fh-6:2d}-{fh:2d}  | {gap/atot:+.6f}  {100*gap/p:+.3f}% | {land/atot:+.6f}        {100*land/p:+.3f}% | {pl/p:.3f}")
