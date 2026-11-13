# q_pr_ens.py A B: per-member global-mean precipitation (parent grid, area weighted) of run sets A and B (globs),
# last 3-h bucket and whole-run mean (mean of all prate_ave buckets); B-A in %, member SD and SE (paired by suffix and unpaired)
import sys, glob, re
import numpy as np
from netCDF4 import Dataset
def gm(f):
    with Dataset(f) as nc:
        lat = np.ma.asarray(nc.variables["lat" if "lat" in nc.variables else "grid_yt"][:]).astype(float)
        a = np.ma.masked_invalid(np.ma.asarray(nc.variables["prate_ave"][0]).astype(float)) * 86400
        w = np.cos(np.deg2rad(lat)); w = np.broadcast_to(w[:, None], a.shape) if w.ndim == 1 else w
        w = np.ma.masked_array(w, mask=np.ma.getmaskarray(a))
        return float(np.ma.sum(a * w) / np.ma.sum(w))
def run(d):
    fs = [f for f in sorted(glob.glob(d + "/sfcf[0-9][0-9][0-9].nc")) if not f.endswith("000.nc")]
    v = [gm(f) for f in fs]
    return (v[-1], float(np.mean(v)), len(v)) if v else None
def ens(pat):
    r = {}
    for d in sorted(glob.glob(pat)):
        x = run(d)
        if x: r[re.sub(r".*_[cL]", "", d)] = x
    return r
A, B = ens(sys.argv[1]), ens(sys.argv[2])
for j, nm in ((0, "last 3 h"), (1, "run mean")):
    a = np.array([v[j] for v in A.values()]); b = np.array([v[j] for v in B.values()])
    k = sorted(set(A) & set(B)); dp = np.array([B[m][j] - A[m][j] for m in k])
    am = a.mean()
    print(f"{nm:9s} nA={len(a)} nB={len(b)} buckets={sorted({v[2] for v in A.values()})} A={am:.4f} B={b.mean():.4f} "
          f"d={100*(b.mean()/am-1):+.2f}% SE_unpaired={100*np.sqrt(a.var(ddof=1)/len(a)+b.var(ddof=1)/len(b))/am:.2f}% "
          f"paired d={100*dp.mean()/am:+.2f}% SE={100*dp.std(ddof=1)/np.sqrt(len(dp))/am:.2f}% memberSD_A={100*a.std(ddof=1)/am:.2f}%")
