#!/usr/bin/env python3
"""Quick checks on EBD/EBX: fv_update_phys IE+PE vs intended heating; fixer residual vs intended correction.
Usage: eb_check.py <out>"""
import sys
from collections import defaultdict
EBD = defaultdict(dict); EBX = {}
for line in open(sys.argv[1], errors="ignore"):
    w = line.split()
    if w and w[0].endswith(":") and w[0][:-1].isdigit():
        w = w[1:]
    if not w:
        continue
    if w[0] == "EBD":
        EBD[int(w[1])][int(w[2])] = [float(x) for x in w[3:15]]
    elif w[0] == "EBX":
        EBX[int(w[1])] = [float(x) for x in w[2:10]]
A, dt = 5.10064e14, 720.0
f = lambda x: x / (A * dt)
TE = lambda v: v[0] + v[1] + v[2] + v[3]
print("step  updIEPE-intended  rel   | fixerwin  fixer_intended  rel | sg(TE_A)")
for s in sorted(EBD):
    d = EBD[s]
    if 9 not in d or s not in EBX:
        continue
    u = d[6][0] + d[6][1] - d[5][0] - d[5][1]
    it = EBX[s][3]
    fw = TE(d[9]) - TE(d[7])
    fi = EBX[s][1]
    sg = sum(d[3][i] for i in (0, 1, 3, 4)) - sum(d[2][i] for i in (0, 1, 3, 4))
    if s % 10 == 0 or s < 4:
        print(f"{s:4d} {f(u - it):+.3e} {(u - it) / it:+.2e} | {f(fw):+.3e} {f(fi):+.3e} {fw / fi:+.2e} | {f(sg):+.3e}")
