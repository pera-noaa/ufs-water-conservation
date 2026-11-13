#!/usr/bin/env python3
"""Raw ESG sums (W m-2 global, or kg m-2 s-1 for masses) by index. Usage: es_raw.py <out> <i0> <i1> [dt]"""
import sys
from collections import defaultdict
fn, i0, i1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
dt = float(sys.argv[4]) if len(sys.argv) > 4 else 720.0
st = defaultdict(lambda: [0.0] * 261)
for line in open(fn, errors="replace"):
    if "ESG " not in line:
        continue
    p = line[line.index("ESG "):].split()
    k, s = int(p[1]), int(p[2])
    for j, v in enumerate(p[3:13]):
        st[k][10 * (s - 1) + j + 1] = float(v)
ks = sorted(st)
A = sum(st[k][170] for k in ks) / len(ks)
for i in range(i0, i1 + 1):
    print(f"{i:4d} {sum(st[k][i] for k in ks) / (A * len(ks) * dt):+.6e}")
