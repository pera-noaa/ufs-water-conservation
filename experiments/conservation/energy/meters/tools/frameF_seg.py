#!/usr/bin/env python3
"""Per-segment frame-F table from meter v2 (EMS with 14 values): r_P (physics frame), r_F (frame F, water at step-initial
T, boundary water enthalpy at T1), S_cross of the segment (encpl speciation), gap = r_F - S_cross.
Usage: frameF_seg.py <out> [dt=720]   W m-2 global means."""
import sys
from collections import defaultdict
out = sys.argv[1]
dt = float(sys.argv[2]) if len(sys.argv) > 2 else 720.0
EMS, EMF = defaultdict(dict), {}
for line in open(out, errors="ignore"):
    w = line.split()
    if w and w[0].endswith(":") and w[0][:-1].isdigit():
        w = w[1:]
    if len(w) < 3:
        continue
    try:
        if w[0] == "EMS" and len(w) >= 17:
            EMS[int(w[1])][int(w[2])] = [float(x) for x in w[3:17]]
        elif w[0] == "EMF":
            EMF[int(w[1])] = [float(x) for x in w[2:14]]
    except ValueError:
        pass
ks = sorted(k for k in EMS if 12 in EMS[k])
n = len(ks)
A = EMF[ks[0]][11]
W = lambda x: x / (A * dt * n)
name = {1: "1->2 interst_1..composites_pre", 2: "2->3 radiation", 3: "3->4 surface loop", 4: "4->5 PBL", 5: "5->6 GWD",
        6: "6->7 photochem", 7: "7->8 SAMF deep", 8: "8->9 SAMF shallow", 9: "9->10 interst_4", 10: "10->11 Thompson",
        11: "11->12 post", 12: "ALL physics"}
print(f"# {out}: {n} steps; W m-2:  r_P   r_F   S_cross   gap=r_F-S_cross   sum|gap|")
for s in range(1, 13):
    v = [sum(EMS[k][s][i] for k in ks) for i in range(14)]
    rP = v[0] - v[6]
    print(f"{name[s]:34s} {W(rP):+.6e} {W(v[10]):+.6e} {W(v[12]):+.6e} {W(v[10]-v[12]):+.6e} {W(v[13]):.3e}")
