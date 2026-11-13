#!/usr/bin/env python3
"""Per-scheme global water budget from dtend diagnostics on native cubed-sphere tiles (any resolution), per window (WB_WINDOW hours, default 6, to WB_END, default 24).
Usage: python3 water_budget_by_scheme.py <RUNDIR> [<RUNDIR> ...]
Needs atmfHHH.tileN.nc (dpres + 6 species), sfcfHHH.tileN.nc (dtend_* 3-D tendencies, prateb_ave, cpratb_ave,
lhtfl_ave), INPUT/C<res>_grid.tileN.nc. FV3 writes gfs_phys 3-D diagnostics to the sfcf files.
Convection = dtend_qv_deepcnv + dtend_qv_shalcnv + condensate dtend_*_cnvtrans (detrainment and transport).
Output dpres is delp*(1 - condensate), the physics' dry+vapour thickness, while q is per total mass: W uses
dpres/(1 - condensate), and physics tendencies are integrated with dpres itself, averaged over the window's two snapshots. Fields the model never fills are taken as zero and listed. kg/m2 per window."""
import glob
import os
import re
import sys
import numpy as np
from netCDF4 import Dataset

# window length and end (hours); WB_BUCKET (default WB_WINDOW) must equal fhzero and divide the window, and every
# bucket end must be an output time. Each bucket's tendency is integrated with that bucket's own mean thickness.
WIN, END = int(os.environ.get("WB_WINDOW", 6)), int(os.environ.get("WB_END", 24))
BK = int(os.environ.get("WB_BUCKET", WIN))
# WB_THICK (hours, multiple of WB_BUCKET, divides WB_WINDOW): interval whose end-point mean thickness weights the
# tendencies; for convergence tests of that approximation only
TK = int(os.environ.get("WB_THICK", BK))
if WIN % BK or TK % BK or WIN % TK:
    sys.exit(f"ABORT: need WB_BUCKET={BK} | WB_THICK={TK} | WB_WINDOW={WIN}")
G, HVAP, DT = 9.80665, 2.5e6, BK * 3600.0
SP = {"spfh": "qv", "clwmr": "liq_wat", "icmr": "ice_wat", "rwmr": "rainwat", "snmr": "snowwat", "grle": "graupel"}
COND = ["clwmr", "icmr", "rwmr", "snmr", "grle"]
GROUPS = {
    "pbl": [f"dtend_{s}_pbl" for s in SP.values()],
    "cnv": ["dtend_qv_deepcnv", "dtend_qv_shalcnv"] + [f"dtend_{s}_cnvtrans" for s in SP.values() if s != "qv"],
    "mp": [f"dtend_{s}_mp" for s in SP.values()],
    "phys": [f"dtend_{s}_phys" for s in SP.values()],
}


def area(rd, t):
    g = glob.glob(f"{rd}/INPUT/C*_grid.tile{t}.nc")
    if len(g) != 1:
        sys.exit(f"ABORT: expected one INPUT/C*_grid.tile{t}.nc in {rd}, found {g}")
    a = np.asarray(Dataset(g[0])["area"][:], float)
    if os.environ.get("WB_UNWEIGHTED"):  # every column counts once, as the Thompson column and driver meters do (the physics meter is area-weighted)
        a = np.ones_like(a)
    return a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]


def v(d, name):
    return np.asarray(d[name][:], float).squeeze()


def run(rd):
    A = {t: area(rd, t) for t in range(1, 7)}
    atot = sum(a.sum() for a in A.values())
    missing, present, nonzero = set(), set(), set()
    # the bucket fields reset every fhzero hours; a different WB_BUCKET would silently mis-sum P and E
    fz = re.search(r"^\s*fhzero\s*=\s*([0-9.]+)", open(f"{rd}/input.nml").read(), re.M)
    if fz and abs(float(fz.group(1)) - BK) > 1e-6:
        sys.exit(f"ABORT {rd}: fhzero = {fz.group(1)} but WB_BUCKET = {BK}")

    def W(fh):
        s = 0.0
        for t in range(1, 7):
            d = Dataset(f"{rd}/atmf{fh:03d}.tile{t}.nc")
            s += ((sum(v(d, k) for k in SP) * v(d, "dpres") / (1.0 - sum(v(d, k) for k in COND))).sum(0) / G * A[t]).sum()
        return s / atot

    def dp_phys(fh, t):
        d = Dataset(f"{rd}/atmf{fh:03d}.tile{t}.nc")
        # output dpres is delp*(1 - condensate), the physics' dry+vapour thickness (fv_nggps_diag.F90, GFS_PHYS); q is per total mass
        return v(d, "dpres")

    def sfc(fh, name, scale=1.0):
        return sum((v(Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc"), name) * A[t]).sum() for t in range(1, 7)) / atot * scale * DT

    print(f"\n### {rd}")
    print("window |  dW     | E       P       Pconv   | R_pbl    R_cnv    R_mp     R_other  | R_phys   R_dyn    R_total  | R_tot/P | R_cnv/Pc | R_mp/Pls")
    tot = np.zeros(7)
    for fh in range(WIN, END + 1, WIN):
        C = dict.fromkeys(GROUPS, 0.0)
        for b in range(fh - WIN + BK, fh + 1, BK):
            for t in range(1, 7):
                t0 = b - BK - (b - BK - (fh - WIN)) % TK
                dpp = 0.5 * (dp_phys(t0, t) + dp_phys(t0 + TK, t))
                d = Dataset(f"{rd}/sfcf{b:03d}.tile{t}.nc")
                for g, names in GROUPS.items():
                    for n in names:
                        if n not in d.variables:
                            missing.add(n)
                            continue
                        present.add(n)
                        if np.any(v(d, n)):
                            nonzero.add(n)
                        C[g] += ((v(d, n) * DT * dpp).sum(0) / G * A[t]).sum()
        C = {g: c / atot for g, c in C.items()}
        dW = W(fh) - W(fh - WIN)
        # bucket precipitation (reset every fhzero); prate_ave/cprat_ave average since forecast start
        bks = range(fh - WIN + BK, fh + 1, BK)
        E = sum(sfc(b, "lhtfl_ave", 1 / HVAP) for b in bks)
        P, Pc = sum(sfc(b, "prateb_ave") for b in bks), sum(sfc(b, "cpratb_ave") for b in bks)
        r_pbl = C["pbl"] - E
        r_cnv = C["cnv"] + Pc
        r_mp = C["mp"] + (P - Pc)
        r_oth = C["phys"] - (C["pbl"] + C["cnv"] + C["mp"])
        r_phys = C["phys"] - (E - P)
        r_dyn = dW - C["phys"]
        r_tot = dW - (E - P)
        row = np.array([r_pbl, r_cnv, r_mp, r_oth, r_phys, r_dyn, r_tot])
        tot += row
        print(f"{fh-WIN:3d}-{fh:3d} | {dW:+.4f} | {E:.5f} {P:.5f} {Pc:.5f} | " + " ".join(f"{x:+.5f}" for x in row[:4])
              + " | " + " ".join(f"{x:+.5f}" for x in row[4:])
              + f" | {100*r_tot/P:+.2f}% | {100*r_cnv/Pc:+.2f}% | {100*r_mp/(P-Pc):+.2f}%")
    print("sum                                         | " + " ".join(f"{x:+.5f}" for x in tot[:4]) + " | "
          + " ".join(f"{x:+.5f}" for x in tot[4:]))
    print("not in output (taken as 0):", " ".join(sorted(missing)) or "none")
    zero = present - nonzero
    if zero:
        print("in output but identically zero:", " ".join(sorted(zero)),
              "(with SAMF the cnvtrans fields are never filled, so R_cnv carries the split's bias)")


for rd in sys.argv[1:]:
    run(rd)
