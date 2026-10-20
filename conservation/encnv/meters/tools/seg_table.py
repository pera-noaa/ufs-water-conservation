#!/usr/bin/env python3
"""Segment residuals (EMS) for GWD/deep/shallow/all physics and the GWD split (EMG), W m-2 over the run.
Usage: seg_table.py <out> [dt=720]"""
import sys
from collections import defaultdict

out = sys.argv[1]
dt = float(sys.argv[2]) if len(sys.argv) > 2 else 720.0
EMS, EMG, A = defaultdict(dict), {}, None
for line in open(out, errors="ignore"):
    w = line.split()
    if w and w[0].endswith(":") and w[0][:-1].isdigit():
        w = w[1:]
    try:
        if w and w[0] == "EMS":
            EMS[int(w[1])][int(w[2])] = [float(x) for x in w[3:13]]
        elif w and w[0] == "EMG":
            EMG[int(w[1])] = [float(x) for x in w[2:10]]
        elif w and w[0] == "EMF" and A is None:
            A = float(w[13])
    except (ValueError, IndexError):
        pass
ks = sorted(EMS)
n = len(ks)
f = 1.0 / (A * dt * n)
print(f"# {out}: {n} EMS steps, {len(EMG)} EMG steps, area {A:.6e}")
for s, name in ((5, "GWD"), (7, "SAMF deep"), (8, "SAMF shallow"), (12, "ALL physics")):
    r = sum(EMS[k][s][0] - EMS[k][s][6] for k in ks)
    dk = sum(EMS[k][s][4] for k in ks)
    dcpt = sum(EMS[k][s][1] for k in ks)
    ab = sum(EMS[k][s][7] for k in ks)
    mx = max(abs(EMS[k][s][0] - EMS[k][s][6]) for k in ks) / (A * dt)
    print(f"{name:14s} r {r*f:+.6e}  dcpT {dcpt*f:+.6e}  dK {dk*f:+.6e}  sum|r| {ab*f:.4e}  max|r| per step {mx:.3e}")
if EMG:
    lab = ["e1 dK(Xe;gw)", "e2 dK(X0;gsl)", "e3 dK(X0;ngw)", "e4 H gsl", "e5 H ngw", "e6 x pending",
           "e7 x gsl.ngw", "e8 sum|H_gsl+dK_gsl| layers"]
    m = len(EMG)
    g = 1.0 / (A * dt * m)
    tot = [sum(EMG[k][i] for k in EMG) * g for i in range(8)]
    for l, v in zip(lab, tot):
        print(f"  {l:30s} {v:+.6e}")
    print(f"  identity e1-(e2+e3+e6+e7)      {tot[0]-(tot[1]+tot[2]+tot[5]+tot[6]):+.3e}")
    print(f"  GSL own   e2+e4                {tot[1]+tot[3]:+.6e}")
    print(f"  NGW own   e3+e5                {tot[2]+tot[4]:+.6e}")
    print(f"  segment   e1+e4+e5             {tot[0]+tot[3]+tot[4]:+.6e}")
    print(f"  max per step |e2+e4|           {max(abs(v[1]+v[3]) for v in EMG.values())/(A*dt):.3e}")
