"""cnv_s18_check.py <hafs_exp dir>: the q_*_S reruns (24 h, history at 18 and 24 h) against the q_*_L runs they copy:
every variable of sfcf024.nc and sfc.nest02.f024.nc must be bit-identical where the L run reached 24 h, and every S run
must have its 18 h files. Exit 1 otherwise."""
import glob
import os
import sys
import numpy as np
import netCDF4

H = sys.argv[1]
bad = 0
for g in ("devP2", "devF", "devB", "devP2ps", "devFps", "devBps"):
    for s in sorted(glob.glob(f"{H}/q_{g}_S*")):
        v = s.rsplit("_S", 1)[1]
        L = f"{H}/q_{g}_L{v}"
        miss = [f for f in ("sfcf018.nc", "sfc.nest02.f018.nc") if not os.path.exists(f"{s}/{f}")]
        res = []
        for f in ("sfcf024.nc", "sfc.nest02.f024.nc"):
            if not os.path.exists(f"{L}/{f}"):
                res.append(f"{f}: L run stopped before 24 h"); continue
            if not os.path.exists(f"{s}/{f}"):
                res.append(f"{f}: MISSING in S"); bad += 1; continue
            with netCDF4.Dataset(f"{L}/{f}") as a, netCDF4.Dataset(f"{s}/{f}") as b:
                nd = [k for k in a.variables if k not in ("time",) and a[k].dtype.kind == "f"
                      and not np.array_equal(np.ma.filled(a[k][:], -1e34), np.ma.filled(b[k][:], -1e34))]
            res.append(f"{f}: {'bit-identical' if not nd else 'DIFFER ' + ','.join(nd[:5])}")
            bad += bool(nd)
        bad += bool(miss)
        print(os.path.basename(s), "MISSING 18 h " + ",".join(miss) if miss else "18 h ok", "|", "; ".join(res))
print("FAIL" if bad else "PASS", bad)
sys.exit(1 if bad else 0)
