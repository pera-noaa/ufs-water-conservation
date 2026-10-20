"""24 h impact of run B vs A against the noise pair (A vs N): rms and mean of the difference per field.
usage: impact.py <runA> <runB> <noiseA> <noiseB> [fhr=24]   noise = noiseB - noiseA (the consv_te 0.999 pair)"""
import sys, glob
import numpy as np
from netCDF4 import Dataset
a, b, na, n = sys.argv[1:5]
fh = int(sys.argv[5]) if len(sys.argv) > 5 else 24
F = [("atm", "tmp", "T (K)"), ("atm", "spfh", "q (kg/kg)"), ("atm", "ugrd", "u (m/s)"), ("sfc", "pressfc", "ps (Pa)"),
     ("sfc", "prate_ave", "precip (kg/m2/s)"), ("sfc", "cpratb_ave", "conv precip bucket"), ("sfc", "lhtfl_ave", "LH (W/m2)"),
     ("sfc", "shtfl_ave", "SH (W/m2)"), ("sfc", "tmp2m", "T2m (K)"), ("sfc", "spfh2m", "q2m"), ("sfc", "pwat", "PW (kg/m2)"),
     ("sfc", "tmpsfc", "Tsfc (K)")]
def load(r, kind, v):
    fs = sorted(glob.glob(f"{r}/{kind}f{fh:03d}.nc") + glob.glob(f"{r}/{kind}f{fh:03d}.tile*.nc"))
    out = []
    for f in fs:
        with Dataset(f) as d:
            if v not in d.variables: return None
            out.append(np.asarray(d.variables[v][:], dtype='f8').ravel())
    return np.concatenate(out) if out else None
print(f"{'field':20s} {'rms B-A':>11s} {'rms N-A':>11s} {'ratio':>6s} {'mean B-A':>11s} {'mean N-A':>11s} {'mean A':>11s}")
for kind, v, lab in F:
    x, y, z, w = load(a, kind, v), load(b, kind, v), load(n, kind, v), load(na, kind, v)
    if x is None or y is None or z is None or w is None:
        continue
    d1, d2 = y - x, z - w
    r1, r2 = np.sqrt(np.mean(d1**2)), np.sqrt(np.mean(d2**2))
    print(f"{lab:20s} {r1:11.3e} {r2:11.3e} {r1/r2 if r2 else float('inf'):6.2f} {d1.mean():+11.3e} {d2.mean():+11.3e} {x.mean():11.4e}")
