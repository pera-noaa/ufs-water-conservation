# q_step.py <label> <run dir>...: per-step size of the dbg4 events pooled over members (is the heating per step set by
# dt, as a physical rate would be, or fixed by the CFL limit?): events per member, |dT| percentiles, CFL, xmb at xmbmax
import sys, re
import numpy as np
lab, runs = sys.argv[1], sys.argv[2:]
dT, cfl, lim, n = [], [], 0, 0
for d in runs:
    try:
        f = open(d + "/out", errors="replace")
    except OSError:
        continue
    n += 1
    for line in f:
        if "DBGSAMF" not in line:
            continue
        s = re.sub(r"^\s*\d+:\s*", "", line).split()
        try:
            t, x, xm, c = float(s[7]), float(s[9]), float(s[10]), float(s[11])
        except (ValueError, IndexError):
            continue
        dT.append(abs(t)); cfl.append(c); lim += abs(x - xm) <= 1e-3 * xm
a = np.array(dT); c = np.array(cfl)
p = lambda v, q: float(np.percentile(v, q)) if len(v) else 0.0
print(f"{lab:10s} members {n:2d} events/member {len(a)/max(n,1):8.0f} | |dT| K p50 {p(a,50):5.1f} p90 {p(a,90):5.1f} p99 {p(a,99):5.1f} max {a.max() if len(a) else 0:5.1f} | CFL p50 {p(c,50):4.2f} max {c.max() if len(c) else 0:4.2f} | xmb=xmbmax {lim/max(len(a),1):.0%}")
