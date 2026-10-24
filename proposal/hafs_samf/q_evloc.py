# q_evloc.py <run dir>... : where the dbg4 events (|dT| > 4 K in one step) sit: layer relative to kb/kbcon/ktcon,
# heating or cooling, CFL and eta at the event, and the share at the lowest model layers.
import sys, re
import numpy as np
for d in sys.argv[1:]:
    E = []
    with open(d + "/out", errors="replace") as f:
        for line in f:
            if "DBGSAMF" not in line:
                continue
            s = re.sub(r"^\s*\d+:\s*", "", line).split()
            try:
                E.append([float(x) for x in s[2:16]])  # k kb kbcon jmin ktcon dT dq xmb xmbmax cfl eta del tke clamt
            except (ValueError, IndexError):
                pass
    E = np.array(E) if E else np.zeros((0, 14))
    k, kb, kbc, jmin, ktc, dT, dq, xmb, xmbmax, cfl, eta, dl = (E[:, i] for i in range(12))
    n = len(E)
    if n == 0:
        print(f"{d}: no events"); continue
    sub = (k < kbc) & (k >= kb); below_kb = k < kb; at = k == kbc; above = k > kbc
    print(f"{d.rstrip('/').split('/')[-1]}: {n} events | k<kb {int(below_kb.sum())} kb..kbcon-1 {int(sub.sum())} kbcon {int(at.sum())} above {int(above.sum())}"
          f" | heating {int((dT > 0).sum())} cooling {int((dT < 0).sum())} | k 1-2 {int((k <= 2).sum())} | xmb=xmbmax {int((np.abs(xmb - xmbmax) <= 1e-3 * xmbmax).sum())}"
          f" | CFL med {np.median(cfl):.2f} max {cfl.max():.1f} | eta max {eta.max():.2f} | kb med {np.median(kb):.0f} kbcon med {np.median(kbc):.0f}"
          f" | dT p50 {np.median(np.abs(dT)):.1f} p99 {np.percentile(np.abs(dT), 99):.1f}")
