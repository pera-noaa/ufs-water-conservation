# q_stats.py <run dir>... : SAMF event statistics from the dbg4 prints, crash status, mean precipitation
import sys, re
import numpy as np
from netCDF4 import Dataset
def prate(d):
    try:
        with Dataset(d + "/sfcf006.nc") as nc:
            lat = np.asarray(nc.variables["lat"][:], dtype=float); a = np.asarray(nc.variables["prate_ave"][0], dtype=float) * 86400
            w = np.cos(np.deg2rad(lat)); w = np.broadcast_to(w[:, None], a.shape) if w.ndim == 1 else w
            return np.sum(a * w) / np.sum(w)
    except Exception:
        return float("nan")
print(f"{'run':>18} {'end':>3} {'crash':>5} | {'deep':>5} {'cfl>1':>5} {'cfl>5':>5} {'>10K':>4} {'maxdT':>6} {'maxcfl':>6} {'medTKE':>6} | {'tkeCap':>6} {'maxTKE':>7} | {'shal':>4} {'s>1':>4} {'smaxdT':>6} {'tksCap':>6} | {'prate':>7}")
for d in sys.argv[1:]:
    deep, shal, tke, tks = [], [], [], []
    end = crash = 0
    with open(d + "/out", errors="replace") as f:
        for line in f:
            if "DBG" not in line:
                if re.search(r"PROGRAM ufs +HAS ENDED", line): end = 1
                continue
            s = re.sub(r"^\s*\d+:\s*", "", line).split()
            try:
                if s[0] == "DBGSAMF": deep.append([float(x) for x in s[7:16]])
                elif s[0] == "DBGSHAL": shal.append([float(x) for x in s[6:15]])
                elif s[0] == "DBGTKE": tke.append(float(s[5]))
                elif s[0] == "DBGTKS": tks.append(float(s[5]))
            except (ValueError, IndexError):
                pass
    try:
        crash = int(any("FATAL" in l for l in open(d + "/err", errors="replace")))
    except OSError:
        pass
    D = np.array(deep) if deep else np.zeros((0, 9)); S = np.array(shal) if shal else np.zeros((0, 9))
    dT, cfl, tk = (D[:, 0], D[:, 4], D[:, 7]) if len(D) else (np.zeros(0),) * 3
    sdT, scfl = (S[:, 0], S[:, 4]) if len(S) else (np.zeros(0),) * 2
    mx = lambda a: float(np.max(np.abs(a))) if len(a) else 0.0
    print(f"{d.rstrip('/').split('/')[-1]:>18} {end:>3} {crash:>5} | {len(D):>5} {int((cfl>1.0001).sum()):>5} {int((cfl>5).sum()):>5} {int((np.abs(dT)>10).sum()):>4} {mx(dT):6.1f} {mx(cfl):6.1f} {float(np.median(tk)) if len(tk) else 0:6.1f} | {len(tke):>6} {max(tke) if tke else 0:7.1f} | {len(S):>4} {int((scfl>1.0001).sum()):>4} {mx(sdT):6.1f} {len(tks):>6} | {prate(d):7.4f}")
