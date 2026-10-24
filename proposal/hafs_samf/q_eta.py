# q_eta.py <run dir>... : sub-cloud eta statistics from the dbgeta prints (DBGETA per column with eta > 1.2,
# DBGETN per call: convective columns, of those eta > 1.2, tkemean > tkcrt = 2, and with dbgeta2 sub-cloud eta <= 0
# and clamt at its cap).
# Check: below cloud base above 1 km, eta > 1 needs clamt > clam (tkemean > 0.35; clamt reaches clam + clamd = 0.13 at
# tkemean 0.65 and (1 + tkemean/2) clam above tkemean 2); any eta > 1.2 with tkemean <= 2 is listed.
import sys, re
import numpy as np
print(f"{'run':>16} {'columns':>9} {'eta>1.2':>8} {'tke>2':>8} {'eta<=0':>7} {'capped':>7} | {'eta>2':>6} {'eta>10':>6} {'maxeta':>8} | {'median tke':>10} {'clamt=1.5':>9} {'zkb km':>11} | {'eta>1.2 & tke<=2':>16}")
for d in sys.argv[1:]:
    nc = n12 = nt = 0
    nn = ncp = -1
    rows = []
    with open(d + "/out", errors="replace") as f:
        for line in f:
            if "DBGET" not in line:
                continue
            s = re.sub(r"^\s*\d+:\s*", "", line).split()
            try:
                if s[0] == "DBGETN":
                    nc += int(s[1]); n12 += int(s[2]); nt += int(s[3])
                    if len(s) > 5:
                        nn = max(nn, 0) + int(s[4]); ncp = max(ncp, 0) + int(s[5])
                elif s[0] == "DBGETA":
                    rows.append([float(x) for x in s[4:9]])
            except (ValueError, IndexError):
                pass
    R = np.array(rows) if rows else np.zeros((0, 5))
    eta, tke, clamt, zkb = R[:, 0], R[:, 1], R[:, 2], R[:, 3] / 1e3
    q = lambda a, p: float(np.percentile(a, p)) if len(a) else 0.0
    print(f"{d.rstrip('/').split('/')[-1]:>16} {nc:>9} {n12:>8} {nt:>8} {nn:>7} {ncp:>7} | {int((eta > 2).sum()):>6} {int((eta > 10).sum()):>6} {float(eta.max()) if len(eta) else 0:8.1f} |"
          f" {q(tke, 50):10.1f} {int((clamt > 1.499).sum()):>9} {q(zkb, 10):5.1f}-{q(zkb, 90):<5.1f} | {int(((eta > 1.2) & (tke <= 2.0)).sum()):>16}")
