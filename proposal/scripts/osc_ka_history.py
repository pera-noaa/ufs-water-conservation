#!/usr/bin/env python3
"""Fix A's cloud-base heating dTA per column over steps K0..K1 from a metered-A run's 'out' (WKC/WKA lines of instrument_wb_ka.py).
Usage: python3 osc_ka_history.py <RUNDIR> [K0=1 K1=715]
Prints, for every column of the 71-76E, 15-9S box: convecting steps, mean |dTA|, max |dTA|, signed sum dTA (cumulative heating
at kb), the same for the last 100 steps; the 3x3 crash cluster (72.2-74.3E, 12.8-10.8S) flagged; the global per-column-step
mean |dTA| from WKA for comparison; and 50-step windows of the cluster's mean dTA against the rest of the box."""
import re
import sys
from collections import defaultdict

rd = sys.argv[1]
k0, k1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1, 715)
lab = re.compile(r"^\s*\d+:\s*")
col = defaultdict(list)          # (lon, lat) -> [(kdt, dTA, kb)]
gsum, gn, gmax = 0.0, 0.0, 0.0
for line in open(f"{rd}/out", errors="replace"):
    line = lab.sub("", line)
    if line.startswith("WKC "):
        f = line.split()
        k = int(f[1])
        if k0 <= k <= k1:
            col[(round(float(f[2]), 3), round(float(f[3]), 3))].append((k, float(f[15]), int(f[4])))
    elif line.startswith("WKA "):
        f = line.split()
        k = int(f[1])
        if k0 <= k <= k1:
            gn += float(f[2]); gsum += float(f[3]); gmax = max(gmax, float(f[4]))
box = {c: v for c, v in col.items() if 71 < c[0] < 76 and -15 < c[1] < -9}
clu = lambda c: 72.0 < c[0] < 74.5 and -13.0 < c[1] < -10.5
print(f"steps {k0}..{k1}; global mean |dTA| per convecting column-step {gsum / max(gn, 1):.4f} K, max {gmax:.3f} K")
print(f"{'lon':>8} {'lat':>8} {'ncnv':>5} {'mean|dTA|':>10} {'max|dTA|':>9} {'sum dTA':>9} {'n_last100':>9} {'sum_last100':>11} {'kb=1 frac':>9}")
rows = []
for c, v in box.items():
    a = [abs(x[1]) for x in v]
    last = [x[1] for x in v if x[0] > k1 - 100]
    rows.append((c, len(v), sum(a) / len(a), max(a), sum(x[1] for x in v), len(last), sum(last),
                 sum(1 for x in v if x[2] == 1) / len(v)))
rows.sort(key=lambda r: -r[4])
for i, r in enumerate(rows):
    c = r[0]
    print(f"{c[0]:8.3f} {c[1]:8.3f} {r[1]:5d} {r[2]:10.4f} {r[3]:9.3f} {r[4]:9.2f} {r[5]:9d} {r[6]:11.3f} {r[7]:9.2f}"
          f"{'  <- cluster' if clu(c) else ''}  rank {i + 1}/{len(rows)} by sum dTA")
cl = [r for r in rows if clu(r[0])]
ot = [r for r in rows if not clu(r[0])]
avg = lambda rs, j: sum(r[j] for r in rs) / max(len(rs), 1)
print(f"cluster ({len(cl)} cols): mean ncnv {avg(cl, 1):.0f}, mean|dTA| {avg(cl, 2):.4f}, sum dTA {avg(cl, 4):.2f} K; "
      f"rest of box ({len(ot)} cols): ncnv {avg(ot, 1):.0f}, mean|dTA| {avg(ot, 2):.4f}, sum dTA {avg(ot, 4):.2f} K")
print("50-step windows: summed dTA per column (cluster mean | rest-of-box mean)")
for w in range(k0, k1 + 1, 50):
    def s(rs):
        return sum(sum(x[1] for x in box[r[0]] if w <= x[0] < w + 50) for r in rs) / max(len(rs), 1)
    print(f"  {w:4d}-{min(w + 49, k1):4d}  {s(cl):8.3f} | {s(ot):8.3f}")
