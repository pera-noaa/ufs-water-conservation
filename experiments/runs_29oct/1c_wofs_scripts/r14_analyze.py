# r14_analyze.py <runs root> <test> : pre-registered estimators E1-E4 and gates G0-G3 for CP1/FV2 on one WoFS test
# runs: <root>/<test>/<label>/{phyf006.nc,dynf006.nc,r14_meter.*.bin,out}
import sys, os, glob, json
import numpy as np
from netCDF4 import Dataset
from scipy.spatial import cKDTree
root, test = sys.argv[1], sys.argv[2]
D = os.path.join(root, test)
DOSES = {"a-2": -2, "a-1": -1, "a+1": 1, "a+2": 2}
NOISE = {f"n{s}{k}": (1 if s == "+" else -1) * k for k in range(1, 6) for s in "+-"}
NSTEP, EPS32 = 600, float(np.finfo(np.float32).eps)
NF = 9   # meter fields: m ml h hl dev r1 e1 ma ha

def load(lab):
    d = os.path.join(D, lab)
    with Dataset(os.path.join(d, "phyf006.nc")) as nc:
        p = np.asarray(nc.variables["prate_ave"][0], dtype=float)
        lat = np.asarray(nc.variables["lat"][:], dtype=float); lon = np.asarray(nc.variables["lon"][:], dtype=float)
    with Dataset(os.path.join(d, "dynf006.nc")) as nc:
        t = np.asarray(nc.variables["tmp"][0], dtype=float)
    return dict(p=p, t=t, lat=lat, lon=lon)

def meter(lab):
    fs = sorted(glob.glob(os.path.join(D, lab, "r14_meter.*.bin")))
    out = dict(nfile=len(fs), nstep=set(), lon=[], lat=[], f=[[] for _ in range(NF)])
    for f in fs:
        b = open(f, "rb").read()
        h = np.frombuffer(b[:24], dtype=np.int32); isc, iec, jsc, jec, n, l0 = h
        ni, nj = iec - isc + 1, jec - jsc + 1; c = ni * nj
        a = np.frombuffer(b[24:], dtype=np.float64)
        if a.size != c * (2 + NF): raise SystemExit(f"GATE meter size {f}")
        out["nstep"].add(int(n)); out["lon"].append(a[:c]); out["lat"].append(a[c:2 * c])
        for q in range(NF): out["f"][q].append(a[(2 + q) * c:(3 + q) * c])
    out["lon"] = np.concatenate(out["lon"]); out["lat"] = np.concatenate(out["lat"])
    out["f"] = [np.concatenate(x) for x in out["f"]]
    return out

def wmean(x, lat):
    w = np.cos(np.deg2rad(lat)); return float(np.sum(x * w) / np.sum(w))

labs = ["c0", "c0r", "fv2"] + list(DOSES) + list(NOISE)
R = {l: load(l) for l in labs}
c = R["c0"]; P0 = wmean(c["p"], c["lat"])
dP = {l: 100 * (wmean(R[l]["p"], c["lat"]) - P0) / P0 for l in labs}
trms = {l: float(np.sqrt(np.mean((R[l]["t"] - c["t"]) ** 2))) for l in labs}
res = dict(test=test, P0=P0, dP=dP, trms=trms, gates={}, est={})
G = res["gates"]

# G0 reproducibility; known-bad: a one-ulp member must not be bitwise
G["G0_c0r_bitwise"] = bool(np.array_equal(R["c0r"]["p"], c["p"]) and np.array_equal(R["c0r"]["t"], c["t"]))
G["G0_kb_n+1_differs"] = not (np.array_equal(R["n+1"]["p"], c["p"]) and np.array_equal(R["n+1"]["t"], c["t"]))
G["G0_kb_fv2_differs"] = not (np.array_equal(R["fv2"]["p"], c["p"]) and np.array_equal(R["fv2"]["t"], c["t"]))

# G1 consumer: switches reach the line they act on (max |f14 - 1| per run), every PE wrote at step 600
M = {l: meter(l) for l in labs}
mx = {l: float(M[l]["f"][4].max()) for l in labs}
G["G1_nfile"] = sorted({M[l]["nfile"] for l in labs}); G["G1_nstep"] = sorted(set().union(*[M[l]["nstep"] for l in labs]))
G["G1_maxdev"] = mx
ok = mx["c0"] == 0.0 and mx["c0r"] == 0.0 and mx["fv2"] == 0.0
ok &= all(abs(mx[l] - abs(k) * EPS32) <= 1e-6 * abs(k) * EPS32 for l, k in NOISE.items())
ok &= all(mx[l] > 1e-4 for l in DOSES)
G["G1_consumer_ok"] = bool(ok); G["G1_nstep_ok"] = G["G1_nstep"] == [NSTEP]

# G2 meter identity at step 1: e1(a) - e1(c0) = a * r1(c0); known-bad: a=+2 against 1 * r1 must fail
r1 = M["c0"]["f"][5]; sc = np.max(np.abs(r1))
def ident(lab, a): return float(np.max(np.abs(M[lab]["f"][6] - M["c0"]["f"][6] - a * r1)) / sc)
G["G2_a+1"] = ident("a+1", 1); G["G2_a-2"] = ident("a-2", -2); G["G2_kb_a+2_as_1"] = ident("a+2", 1)
G["G2_ok"] = G["G2_a+1"] < 1e-6 and G["G2_a-2"] < 1e-6 and G["G2_kb_a+2_as_1"] > 0.5

# meter summary (c0; cells ~ equal area on the 3-km ESG grid, unweighted means)
m = M["c0"]["f"]; T6, T1 = NSTEP * 36.0, 100 * 36.0
res["meter"] = dict(R_6h_Wm2=float(m[0].mean() / T6), R_last_Wm2=float(m[1].mean() / T1), H_6h_Wm2=float(m[2].mean() / T6),
                    absR_6h_Wm2=float(m[7].mean() / T6), absH_6h_Wm2=float(m[8].mean() / T6),
                    absR_over_absH=float(m[7].sum() / m[8].sum()), R1_max_Jm2=float(sc))

# noise scale
nz = np.array([dP[l] for l in NOISE]); sig = float(np.sqrt(np.mean(nz ** 2)))
res["est"]["sigma_n"] = sig; res["est"]["noise_dP"] = {l: dP[l] for l in NOISE}
res["est"]["noise_trms_max"] = max(trms[l] for l in NOISE)

# E1 size
res["est"]["E1_dP_a+1"] = dP["a+1"]; res["est"]["E1_ratio"] = abs(dP["a+1"]) / sig

# E2 dose response through the origin; null = the same estimator on noise members relabelled as doses
def dose(pairs):
    a = np.array([v for _, v in pairs], float); y = np.array([dP[l] for l, _ in pairs])
    S = float(np.sum(a * y) / np.sum(a * a)); se = sig / np.sqrt(np.sum(a * a))
    r = float(np.sqrt(np.mean((y - S * a) ** 2)))
    d = dict((l, v) for l, v in pairs); m1 = [l for l in d if d[l] == -1][0]; p1 = [l for l in d if d[l] == 1][0]
    return dict(S=S, z=S / se, resid=r, resid_over_sig=r / sig, opp_sign=bool(np.sign(dP[m1]) != np.sign(dP[p1])))
e2 = dose(list(DOSES.items()))
e2["pass"] = bool(abs(e2["z"]) >= 3 and e2["resid"] <= 2 * sig and e2["opp_sign"])
res["est"]["E2"] = e2
for nm, pl in {"null12": [("n-2", -2), ("n-1", -1), ("n+1", 1), ("n+2", 2)],
               "null34": [("n-4", -2), ("n-3", -1), ("n+3", 1), ("n+4", 2)]}.items():
    e = dose(pl); e["pass"] = bool(abs(e["z"]) >= 3 and e["resid"] <= 2 * sig and e["opp_sign"]); res["est"]["E2_" + nm] = e
G["G3_E2_null_fails"] = not res["est"]["E2_null12"]["pass"] and not res["est"]["E2_null34"]["pass"]

# E3 co-location on 15x15-cell (45 km) boxes: dP box sums vs box sums of the last-hour restored term (c0 meter)
lat, lon = c["lat"], c["lon"]
def xyz(la, lo): return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
tree = cKDTree(xyz(np.deg2rad(lat.ravel()), np.deg2rad(lon.ravel())))
dist, idx = tree.query(xyz(M["c0"]["lat"], M["c0"]["lon"]))
B = 15; ny, nx = lat.shape; nby, nbx = ny // B, nx // B
jj, ii = np.unravel_index(idx, lat.shape); keep = (jj < nby * B) & (ii < nbx * B)
bid = (jj // B) * nbx + ii // B
def mbox(v): return np.bincount(bid[keep], weights=v[keep], minlength=nby * nbx)
Rb = mbox(M["c0"]["f"][1]); Rb6 = mbox(M["c0"]["f"][0])
def pbox(lab):
    d = (R[lab]["p"] - c["p"])[:nby * B, :nbx * B]; return d.reshape(nby, B, nbx, B).sum(axis=(1, 3)).ravel()
def rho(lab, s=1, Rv=Rb): return float(np.corrcoef(s * pbox(lab), Rv)[0, 1])
rn = {l: rho(l) for l in NOISE}; mxn = max(abs(v) for v in rn.values())
rd = {l: rho(l, np.sign(a)) for l, a in DOSES.items()}; rbar = float(np.mean(list(rd.values())))
e3 = dict(nbox=nby * nbx, map_maxdist_km=float(dist.max() * 6371.0), rho_noise=rn, max_abs_rho_noise=mxn,
          rho_dose_signed=rd, rho_bar_dose=rbar, rho_a1=rd["a+1"],
          rho_a1_6h=rho("a+1", 1, Rb6), rho_noise_6h_maxabs=max(abs(rho(l, 1, Rb6)) for l in NOISE))
e3["pass"] = bool(rd["a+1"] > mxn and rbar > mxn)
pn = {"n-2": -1, "n-1": -1, "n+1": 1, "n+2": 1}
rbar_null = float(np.mean([rho(l, s) for l, s in pn.items()]))
mx_rest = max(abs(rn[l]) for l in NOISE if l not in pn)
e3["null_rho_bar"] = rbar_null; e3["null_max_rest"] = mx_rest; e3["null_pass"] = bool(rbar_null > mx_rest)
res["est"]["E3"] = e3; G["G3_E3_null_fails"] = not e3["null_pass"]

# E4 FV2 within noise; known-bad: the same test on a=+2 must fail
def e4(lab): return bool(abs(dP[lab]) <= 2 * sig and trms[lab] <= res["est"]["noise_trms_max"])
res["est"]["E4"] = dict(dP=dP["fv2"], ratio=abs(dP["fv2"]) / sig, trms=trms["fv2"], pass_=e4("fv2"), kb_a2_pass=e4("a+2"))
G["G3_E4_kb_fails"] = not e4("a+2")
json.dump(res, open(os.path.join(root, f"r14_result_{test}.json"), "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
