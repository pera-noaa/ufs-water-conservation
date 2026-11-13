# q_sig.py: per-set member statistics from the q_stats tables (largest step, precipitation), and exact tests
import sys, re, math
from itertools import combinations
rows = {}
for p in sys.argv[1:]:
    for l in open(p):
        f = l.split()
        if len(f) < 20 or not f[0].startswith("q_") or f[1] not in "01": continue
        m = re.match(r"q_(.+)_c\d+$", f[0])
        if not m: continue
        rows.setdefault(m.group(1), {})[f[0]] = (int(f[1]), int(f[2]), float(f[8]), float(f[-1]), float(f[9]))
def fisher_one_sided(a, n1, b, n2):  # P(X >= a) for crashes a of n1 vs b of n2 under the hypergeometric null
    t = a + b; N = n1 + n2
    return sum(math.comb(n1, k) * math.comb(n2, t - k) for k in range(a, min(n1, t) + 1)) / math.comb(N, t)
for k in ("dev", "devP", "t1a", "devA", "t1aA", "devD", "t1aD", "devC", "t1aC", "devT", "t1aT", "devE", "t1aE"):
    if k not in rows: continue
    v = list(rows[k].values()); n = len(v); cr = sum(x[1] for x in v)
    fin = [x for x in v if x[0] == 1]
    mx = sorted(x[2] for x in fin); mc = sorted(x[4] for x in fin); pr = [x[3] for x in fin if not math.isnan(x[3])]
    mean = sum(pr) / len(pr) if pr else float("nan"); sd = (sum((x - mean) ** 2 for x in pr) / (len(pr) - 1)) ** 0.5 if len(pr) > 1 else 0
    print(f"{k:5s} n {n:2d} crashed {cr} | largest step per finished member: min {mx[0]:5.1f} median {mx[len(mx)//2]:5.1f} max {mx[-1]:5.1f} K, CFL median {mc[len(mc)//2]:4.1f} max {mc[-1]:4.1f} | prate mean {mean:.4f} sd {sd:.4f} range {min(pr):.4f}-{max(pr):.4f}")
print("Fisher one-sided, 3/20 vs 0/20:", round(fisher_one_sided(3, 20, 0, 20), 3), "; 3/20 vs 0/80:", round(fisher_one_sided(3, 20, 0, 80), 4))
print("P(0 of 20 | rate 3/20):", round((17/20) ** 20, 4))
