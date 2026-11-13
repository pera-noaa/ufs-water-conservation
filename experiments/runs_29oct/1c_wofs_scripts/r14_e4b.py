# r14_e4b.py <runs root> <test> : pre-registered E4b (PREREG_E4b.md) for FV2 against a 50-member noise ensemble
import sys, os, glob, json
import numpy as np
from netCDF4 import Dataset
from scipy.stats import mannwhitneyu
root, test = sys.argv[1], sys.argv[2]
D = os.path.join(root, test)
NOISE = {f"n{s}{k}": (1 if s == "+" else -1) * k for k in range(1, 26) for s in "+-"}
OLD = [l for l, k in NOISE.items() if abs(k) <= 5]
NEW = [l for l, k in NOISE.items() if abs(k) >= 6]
DOSES = {"a-2": -2, "a-1": -1, "a+1": 1, "a+2": 2}
NSTEP, EPS32 = 600, float(np.finfo(np.float32).eps)

def load(lab):
    d = os.path.join(D, lab)
    with Dataset(os.path.join(d, "phyf006.nc")) as nc:
        p = np.asarray(nc.variables["prate_ave"][0], dtype=float); lat = np.asarray(nc.variables["lat"][:], dtype=float)
    with Dataset(os.path.join(d, "dynf006.nc")) as nc:
        t = np.asarray(nc.variables["tmp"][0], dtype=float)
    return dict(p=p, t=t, lat=lat)

def meter_dev(lab):   # max |f - 1| (field 4) and the set of steps written, over all PE files
    fs = sorted(glob.glob(os.path.join(D, lab, "r14_meter.*.bin"))); mx, st = 0.0, set()
    for f in fs:
        b = open(f, "rb").read(); h = np.frombuffer(b[:24], dtype=np.int32); c = (h[1] - h[0] + 1) * (h[3] - h[2] + 1)
        a = np.frombuffer(b[24:], dtype=np.float64); mx = max(mx, float(a[6 * c:7 * c].max())); st.add(int(h[4]))
    return mx, st, len(fs)

def wmean(x, lat):
    w = np.cos(np.deg2rad(lat)); return float(np.sum(x * w) / np.sum(w))

labs = ["c0", "fv2"] + list(DOSES) + list(NOISE)
R = {l: load(l) for l in labs}
c = R["c0"]; P0 = wmean(c["p"], c["lat"])
dP = {l: 100 * (wmean(R[l]["p"], c["lat"]) - P0) / P0 for l in labs}
trms = {l: float(np.sqrt(np.mean((R[l]["t"] - c["t"]) ** 2))) for l in labs}
res = dict(test=test, N=len(NOISE), dP=dP, trms=trms, gates={}, est={})
G, E = res["gates"], res["est"]

# G0 every new run finished
G["G0_rc"] = {l: open(os.path.join(D, l, "rc")).read().strip() for l in NEW}
G["G0_ok"] = all(v == "rc=0" for v in G["G0_rc"].values())
# G1 consumer on the new members; known-bad: c0
md = {l: meter_dev(l) for l in NEW + ["c0"]}
G["G1_ok"] = bool(all(abs(md[l][0] - abs(NOISE[l]) * EPS32) <= 1e-6 * abs(NOISE[l]) * EPS32 and md[l][1] == {NSTEP} for l in NEW))
G["G1_nfile"] = sorted({md[l][2] for l in NEW}); G["G1_kb_c0_fails"] = md["c0"][0] == 0.0

def e4b(lab, pool):
    nz = np.array([dP[l] for l in pool]); s = float(np.sqrt(np.mean(nz ** 2)))
    m = int(sum(trms[l] >= trms[lab] for l in pool)); p = (1 + m) / (len(pool) + 1)
    leg1, leg2 = abs(dP[lab]) <= 2 * s, p > 0.05
    return dict(dP=dP[lab], sigma=s, ratio=abs(dP[lab]) / s, trms=trms[lab], m=m, p=p, leg1=bool(leg1), leg2=bool(leg2), pass_=bool(leg1 and leg2))

pool = list(NOISE)
E["sigma_50"] = e4b("fv2", pool)["sigma"]
E["E4b_fv2"] = e4b("fv2", pool)
E["E4b_kb_a+2"] = e4b("a+2", pool); G["G3_power_ok"] = not E["E4b_kb_a+2"]["pass_"]
E["E4b_a+1_reported"] = e4b("a+1", pool)
# legacy E4 on the original 10
s10 = float(np.sqrt(np.mean(np.array([dP[l] for l in OLD]) ** 2)))
E["E4_legacy10"] = dict(sigma=s10, pass_=bool(abs(dP["fv2"]) <= 2 * s10 and trms["fv2"] <= max(trms[l] for l in OLD)))
# leave-one-out null
loo = {l: e4b(l, [q for q in pool if q != l]) for l in pool}
E["null_fail_frac"] = float(np.mean([not v["pass_"] for v in loo.values()]))
E["null_fail_leg2_frac"] = float(np.mean([not v["leg2"] for v in loo.values()]))
G["G3_null_ok"] = E["null_fail_frac"] <= 0.15
# exchangeability, reported
E["exch"] = dict(trms_median_old=float(np.median([trms[l] for l in OLD])), trms_median_new=float(np.median([trms[l] for l in NEW])),
                 trms_mw_p=float(mannwhitneyu([trms[l] for l in OLD], [trms[l] for l in NEW]).pvalue),
                 absdP_median_old=float(np.median([abs(dP[l]) for l in OLD])), absdP_median_new=float(np.median([abs(dP[l]) for l in NEW])),
                 absdP_mw_p=float(mannwhitneyu([abs(dP[l]) for l in OLD], [abs(dP[l]) for l in NEW]).pvalue))
# CP1 E2 slope with sigma_50, reported
a = np.array(list(DOSES.values()), float); y = np.array([dP[l] for l in DOSES])
S = float(np.sum(a * y) / np.sum(a * a)); E["E2_S"] = S; E["E2_z_sigma50"] = S / (E["sigma_50"] / np.sqrt(np.sum(a * a)))
res["verdict_ok"] = bool(G["G0_ok"] and G["G1_ok"] and G["G1_kb_c0_fails"] and G["G3_power_ok"] and G["G3_null_ok"])
json.dump(res, open(os.path.join(root, f"r14_e4b_{test}.json"), "w"), indent=1, default=float)
print(json.dumps({k: v for k, v in res.items() if k not in ("dP", "trms")}, indent=1, default=float))
