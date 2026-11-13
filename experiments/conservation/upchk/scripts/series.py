#!/usr/bin/env python3
"""series.py <out> : per step, PBL water residual (EMS seg 4) vs MLM water and smoothing water (UCM), kg per step."""
import sys
E, M = {}, {}
for l in open(sys.argv[1], errors="ignore"):
    w = l.split()
    if w and w[0].endswith(":"):
        w = w[1:]
    if len(w) > 3 and w[0] == "EMS" and w[2] == "4":
        E[int(w[1])] = float(w[11])
    if len(w) > 3 and w[0] == "UCM":
        M[int(w[1])] = [float(x) for x in w[2:18]]
ks = sorted(k for k in E if k in M)
dt = 720.0
a = [E[k] for k in ks]; b = [M[k][1] * dt for k in ks]; c = [M[k][7] * dt for k in ks]
n = len(ks); ma, mb = sum(a) / n, sum(b) / n
cov = sum((x - ma) * (y - mb) for x, y in zip(a, b)); va = sum((x - ma) ** 2 for x in a); vb = sum((y - mb) ** 2 for y in b)
print(f"steps {n}; sum PBL water r {sum(a):+.4e} kg; sum MLM W {sum(b):+.4e}; sum smoothing W {sum(c):+.4e}; corr {cov / (va * vb) ** .5 if va and vb else 0:+.3f}")
for k in ks[:: max(1, n // 12)]:
    print(f"{k:4d} PBLr {E[k]:+.4e} MLM_W {M[k][1] * dt:+.4e} smooth_W {M[k][7] * dt:+.4e} act {M[k][13]:.3e}")
