#!/usr/bin/env python3
"""Do 3-D dtend diagnostics and 2-D surface diagnostics sit in the same columns? Per-column PBL residual
C_pbl - E should be ~0 everywhere if they do. Also tries simple index transforms to find a mapping that zeroes it.
Usage: python3 column_mapping_check.py <RUNDIR> <end_fh>"""
import sys
import numpy as np
from netCDF4 import Dataset

rd, fh = sys.argv[1], int(sys.argv[2])
G, HVAP, DT = 9.80665, 2.5e6, 6 * 3600.0
SPN = ["qv", "liq_wat", "ice_wat", "rainwat", "snowwat", "graupel"]
COND = ["clwmr", "icmr", "rwmr", "snmr", "grle"]


def v(d, n):
    return np.asarray(d[n][:], float).squeeze()


for t in (1, 3):
    d0, d1 = Dataset(f"{rd}/atmf{fh-6:03d}.tile{t}.nc"), Dataset(f"{rd}/atmf{fh:03d}.tile{t}.nc")
    dpp = 0.5 * sum(v(d, "dpres") for d in (d0, d1))  # output dpres is already the physics (dry+vapour) thickness
    s = Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc")
    Cpbl = sum((v(s, f"dtend_{sp}_pbl") * DT * dpp).sum(0) / G for sp in SPN)
    Cpbl_flat = sum((v(s, f"dtend_{sp}_pbl") * DT).sum(0) for sp in SPN)  # mapping-independent of dp
    E = v(s, "lhtfl_ave") / HVAP * DT
    r = Cpbl - E
    print(f"tile {t}: E mean {E.mean():.4f}  C_pbl mean {Cpbl.mean():.4f}  per-column |C_pbl-E|: median {np.median(np.abs(r)):.2e}"
          f" p99 {np.percentile(np.abs(r), 99):.2e} max {np.abs(r).max():.2e};  corr(C_pbl,E)={np.corrcoef(Cpbl.ravel(), E.ravel())[0,1]:.4f}")
    for name, f in [("transpose", lambda a: a.T), ("flipud", np.flipud), ("fliplr", np.fliplr), ("rot90", np.rot90)]:
        print(f"    corr with E after {name:9s}: {np.corrcoef(f(Cpbl).ravel(), E.ravel())[0,1]:.4f}")
    # microphysics, same column test
    Cmp = sum((v(s, f"dtend_{sp}_mp") * DT * dpp).sum(0) / G for sp in SPN)
    Pls = (v(s, "prateb_ave") - v(s, "cpratb_ave")) * DT
    print(f"    MP: corr(-C_mp, Pls)={np.corrcoef(-Cmp.ravel(), Pls.ravel())[0,1]:.4f}; per-column |C_mp+Pls| median {np.median(np.abs(Cmp+Pls)):.2e} p99 {np.percentile(np.abs(Cmp+Pls),99):.2e}")
    hi = Pls > 1.0
    print(f"    MP in columns with Pls>1 kg/m2 ({hi.sum()}): mean -C_mp {(-Cmp[hi]).mean():.3f}, mean Pls {Pls[hi].mean():.3f}")

print("\nper-column split test (all tiles):")
acc = {k: [] for k in ["rphys", "rcnv", "rmp", "A", "P"]}
for t in range(1, 7):
    a = np.asarray(Dataset(f"{rd}/INPUT/C96_grid.tile{t}.nc")["area"][:], float)
    A = a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
    d0, d1 = Dataset(f"{rd}/atmf{fh-6:03d}.tile{t}.nc"), Dataset(f"{rd}/atmf{fh:03d}.tile{t}.nc")
    dpp = 0.5 * sum(v(d, "dpres") for d in (d0, d1))  # output dpres is already the physics (dry+vapour) thickness
    s = Dataset(f"{rd}/sfcf{fh:03d}.tile{t}.nc")
    col = lambda names: sum((v(s, n) * DT * dpp).sum(0) / G for n in names if n in s.variables)
    Cphys = col([f"dtend_{sp}_phys" for sp in SPN])
    Ccnv = col(["dtend_qv_deepcnv", "dtend_qv_shalcnv"] + [f"dtend_{sp}_cnvtrans" for sp in SPN[1:]])
    Cmp = col([f"dtend_{sp}_mp" for sp in SPN])
    E = v(s, "lhtfl_ave") / HVAP * DT
    P, Pc = v(s, "prateb_ave") * DT, v(s, "cpratb_ave") * DT
    acc["rphys"].append(Cphys - (E - P)); acc["rcnv"].append(Ccnv + Pc); acc["rmp"].append(Cmp + P - Pc); acc["A"].append(A); acc["P"].append(P)
c = {k: np.concatenate([x.ravel() for x in vals]) for k, vals in acc.items()}
for k in ["rphys", "rcnv", "rmp"]:
    print(f"  {k}: global {(c[k]*c['A']).sum()/c['A'].sum():+.5f}  per-column |.| median {np.median(np.abs(c[k])):.2e} p99 {np.percentile(np.abs(c[k]),99):.2e} max {np.abs(c[k]).max():.2e}")
print(f"  corr(rcnv, rmp) = {np.corrcoef(c['rcnv'], c['rmp'])[0,1]:.4f};  regression slope rmp on rcnv = {np.polyfit(c['rcnv'], c['rmp'], 1)[0]:.3f}")
