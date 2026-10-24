# q_w.py RUN...: SA1 water counter (DBGWD deep, DBGWS shallow; parent then nest: created, conv rain, |created| [kg])
# summed over the run, against parent total precipitation from the sfcf prate_ave buckets (fhzero = 3 h; whole run
# only if the buckets tile it, else "-")
import sys, glob, re
import numpy as np
from netCDF4 import Dataset
A = 4 * np.pi * 6.3712e6 ** 2
def ptot(d):
    fs = [f for f in sorted(glob.glob(d + "/sfcf[0-9][0-9][0-9].nc")) if not f.endswith("000.nc")]
    hs = [int(f[-6:-3]) for f in fs]
    if not hs or hs != list(range(3, 3 * len(hs) + 1, 3)): return float("nan"), hs
    s = 0.0
    for f in fs:
        with Dataset(f) as nc:
            lat = np.ma.asarray(nc.variables["lat" if "lat" in nc.variables else "grid_yt"][:]).astype(float)
            a = np.ma.masked_invalid(np.ma.asarray(nc.variables["prate_ave"][0]).astype(float))
            w = np.cos(np.deg2rad(lat)); w = np.broadcast_to(w[:, None], a.shape) if w.ndim == 1 else w
            w = np.ma.masked_array(w, mask=np.ma.getmaskarray(a))
            s += float(np.ma.sum(a * w) / np.ma.sum(w)) * A * 3 * 3600
    return s, hs
print(f"{'run':>18} {'lines':>6} | parent: {'Wdeep':>9} {'Wshal':>9} {'RCdeep':>9} {'RCshal':>9} {'Ptot':>9} | {'W/RC%':>6} {'W/P%':>6} {'RC/P%':>6} {'|W|/RC%':>7} | nest {'W/RC%':>6}")
for d in sys.argv[1:]:
    t = {"DBGWD": np.zeros(6), "DBGWS": np.zeros(6)}; nl = 0
    with open(d + "/out", errors="replace") as f:
        for line in f:
            m = re.search(r"(DBGW[DS])((?:\s+-?[0-9.]+E[-+][0-9]+){6})", line)
            if m: t[m.group(1)] += np.array(m.group(2).split(), float); nl += 1
    D, S = t["DBGWD"], t["DBGWS"]; W, RC = D[0] + S[0], D[1] + S[1]; P, hs = ptot(d)
    Wn, RCn = D[3] + S[3], D[4] + S[4]
    pct = lambda a, b: 100 * a / b if b else float("nan")
    print(f"{d.rstrip('/').split('/')[-1]:>18} {nl:>6} | {D[0]:9.3e} {S[0]:9.3e} {D[1]:9.3e} {S[1]:9.3e} {P:9.3e} | "
          f"{pct(W, RC):6.2f} {pct(W, P):6.2f} {pct(RC, P):6.1f} {pct(D[2] + S[2], RC):7.2f} | {pct(Wn, RCn):6.2f}")
