#!/usr/bin/env python3
"""PBL segment (EMS s=4) components vs fluxes. usage: ems_seg.py <out> [dt=720]"""
import sys
from collections import defaultdict
out = sys.argv[1]
dt = float(sys.argv[2]) if len(sys.argv) > 2 else 720.0
EMS, EMF = defaultdict(dict), {}
for line in open(out, errors="ignore"):
    w = line.split()
    if w and w[0].endswith(":"):
        w = w[1:]
    if len(w) > 3 and w[0] == "EMS":
        EMS[int(w[1])][int(w[2])] = [float(x) for x in w[3:13]]
    elif len(w) > 3 and w[0] == "EMF":
        EMF[int(w[1])] = [float(x) for x in w[2:14]]
ks = sorted(EMF)
A = EMF[ks[0]][11]
n = len(ks)
c = [sum(EMS[k][4][j] for k in ks) / (n * A * dt) for j in range(10)]
f = [sum(EMF[k][j] for k in ks) / (n * A * dt) for j in range(12)]
print("PBL segment dE, cpT, hvap*qv, -hfus*qi, K:", " ".join(f"{x:+.6f}" for x in c[:5]))
print("F (EMS), dtsfc (EMF 9), dqsfc (EMF 10):", f"{c[6]:+.6f} {f[8]:+.6f} {f[9]:+.6f}")
print("cpT - dtsfc:", f"{c[1] - f[8]:+.6f}", " hvap*qv - dqsfc:", f"{c[2] - f[9]:+.6f}")
