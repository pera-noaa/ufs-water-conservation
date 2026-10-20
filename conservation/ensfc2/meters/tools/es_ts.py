#!/usr/bin/env python3
"""Per-step ESG values (W m-2 global) for chosen indices. Usage: es_ts.py <out> <idx,idx,...> [kdt0 kdt1] [dt]"""
import sys
from collections import defaultdict
fn = sys.argv[1]
idx = [int(x) for x in sys.argv[2].split(",")]
k0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0
k1 = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
dt = float(sys.argv[5]) if len(sys.argv) > 5 else 720.0
st = defaultdict(lambda: [0.0] * 261)
for line in open(fn, errors="replace"):
    if "ESG " not in line:
        continue
    p = line[line.index("ESG "):].split()
    k, s = int(p[1]), int(p[2])
    for j, v in enumerate(p[3:13]):
        st[k][10 * (s - 1) + j + 1] = float(v)
for k in sorted(st):
    if k0 <= k <= k1:
        A = st[k][170]
        print(f"{k:4d} " + " ".join(f"{st[k][i] / (A * dt):+.4e}" for i in idx))
