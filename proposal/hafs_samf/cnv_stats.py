"""cnv_stats.py <hafs_exp dir> <out.npz>: hafs_global_1nest_atm convective precipitation (cprat_ave, run-mean since
start) for develop (P2), Han's xlamue floor (F) and 2a95266 (B), progsigma false and true, 10 x 48 h members each.
Per group, domain (glb 1 deg, nest 0.25 deg rotated) and hour (24, 48): member fields over the members that reached
that hour in all three groups of the progsigma set, plus per-member global means of convective and total rate."""
import glob
import os
import sys
import numpy as np
import netCDF4

H, out = sys.argv[1], sys.argv[2]
SETS = {"F": ("devP2", "devF", "devB"), "T": ("devP2ps", "devFps", "devBps")}
FILES = {"glb": "sfcf0%02d.nc", "nest": "sfc.nest02.f0%02d.nc"}
res = {}
for s, groups in SETS.items():
    for hr in (24, 48):
        mem = sorted({os.path.basename(d).split("_L")[1] for d in glob.glob(f"{H}/q_{groups[0]}_L*")})
        ok = [m for m in mem if all(os.path.exists(f"{H}/q_{g}_L{m}/{FILES['glb'] % hr}") for g in groups)]
        res[f"mem_{s}{hr}"] = np.array([int(m) for m in ok])
        for g in groups:
            for dom, pat in FILES.items():
                cp, tp = [], []
                for m in ok:
                    with netCDF4.Dataset(f"{H}/q_{g}_L{m}/{pat % hr}") as d:
                        cp.append(d["cprat_ave"][0].astype(np.float64) * 86400.0)
                        tp.append(d["prate_ave"][0].astype(np.float64) * 86400.0)
                        if f"lat_{dom}" not in res:
                            res[f"lat_{dom}"] = d["lat"][:].astype(np.float32)
                            res[f"lon_{dom}"] = d["lon"][:].astype(np.float32)
                            res[f"land_{dom}"] = d["land"][0].astype(np.int8)
                cp, tp = np.array(cp), np.array(tp)
                res[f"cp_{g}_{dom}_{hr}"] = cp.astype(np.float32)
                if dom == "glb":
                    w = np.cos(np.deg2rad(res["lat_glb"].astype(np.float64)))
                    assert w.shape == cp.shape[1:], w.shape
                    w /= w.sum()
                    res[f"gm_cp_{g}_{hr}"] = (cp * w).sum(axis=(1, 2))
                    res[f"gm_tp_{g}_{hr}"] = (tp * w).sum(axis=(1, 2))
                print(s, hr, g, dom, len(ok), "members", f"mean {cp.mean():.4f} mm/day")
np.savez_compressed(out, **res)
print("wrote", out, os.path.getsize(out))
