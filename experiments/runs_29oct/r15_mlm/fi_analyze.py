# fi_analyze.py <runs dir> : PREREG §2 forecast impact of the #404 fix. Δ = F − G; noise Δ_m = G_m − G (consv_te 0.999…0.990)
# beyond noise iff |Δ| > max_m |Δ_m| (false rate 1/11); also |Δ|/σ_n with σ_n the rms of Δ_m
import sys, os, json
import numpy as np
from netCDF4 import Dataset
R = sys.argv[1]
NOISE = [f"G_0.{1000 - m:03d}" for m in range(1, 11)]
SFC = {"precip (last 6 h)": "prate_ave", "precipitable water": "pwat", "2-m T": "tmp2m", "PBL height": "hpbl", "low cloud": "tcdc_avelcl"}

def load(run):
    s = Dataset(os.path.join(R, run, "sfcf024.nc")); a = Dataset(os.path.join(R, run, "atmf024.nc"))
    lat = np.asarray(s["lat"][:], float)
    w = np.cos(np.deg2rad(lat)); w = w / w.sum()
    out = {k: float((np.asarray(s[v][0], float) * w).sum()) for k, v in SFC.items()}
    out["_3d"] = {v: np.asarray(a[v][0], float) for v in ("tmp", "spfh")}
    out["_w"] = w
    return out

runs = ["F", "G"] + NOISE
D = {r: load(r) for r in runs}
G = D["G"]
def rms3(x, v): return float(np.sqrt((((x["_3d"][v] - G["_3d"][v]) ** 2).mean(axis=0) * G["_w"]).sum()))
res = {}
for k in list(SFC) + ["3-D T rms (K)", "3-D q rms (kg/kg)"]:
    if k.startswith("3-D"):
        v = "tmp" if " T " in k else "spfh"
        dF = rms3(D["F"], v); dn = [rms3(D[m], v) for m in NOISE]
        sig = float(np.sqrt(np.mean(np.square(dn))))
        res[k] = dict(F=dF, noise_max=max(dn), beyond=bool(dF > max(dn)), ratio=dF / sig)
    else:
        dF = D["F"][k] - G[k]; dn = [D[m][k] - G[k] for m in NOISE]
        sig = float(np.sqrt(np.mean(np.square(dn))))
        res[k] = dict(G=G[k], dF=dF, noise_maxabs=max(abs(x) for x in dn), beyond=bool(abs(dF) > max(abs(x) for x in dn)), ratio=abs(dF) / sig)
json.dump(res, open(os.path.join(R, "fi_result.json"), "w"), indent=1)
for k, v in res.items():
    print(f"{k:22s} " + "  ".join(f"{a}={b:.4g}" if isinstance(b, float) else f"{a}={b}" for a, b in v.items()))
