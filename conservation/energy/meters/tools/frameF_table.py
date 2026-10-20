#!/usr/bin/env python3
"""Global 24 h budget in frame F (encpl report.md): E_F = FV3 TE + Lv00*Wv - Li00*Wi, boundary flux
F_F = rad(TOA - sfc) + SH + E*(h_v(T1)+phis) - P*(h_w(T1)+phis), from EBD/EBX (dycore), EMS (physics), EBQ (encpl
coupling meter). Usage: frameF_table.py <out> [dt=720] [--ep1]. W m-2, global mean over steps with all three meters.
--ep1 (sfc_precip_enthalpy on): PH1 convective snow leaves as ice at T1 in F_F (EML swap term), as the surface books it.
EML lines (meter EB_LAG=1): precipitation hand-off lag c_w P(N) (T1(N+1) - T1(N)), not part of the atmosphere budget."""
import sys
from collections import defaultdict

EP1 = "--ep1" in sys.argv
argv = [a for a in sys.argv if a != "--ep1"]
out = argv[1]
dt = float(argv[2]) if len(argv) > 2 else 720.0
g, cp, rv, cpv, cl, ci, hv, hf, T0 = 9.80665, 1004.6, 461.5, 1846.0, 4185.5, 1972.0, 2.5e6, 3.3358e5, 273.15
Lv00 = hv - (cpv - cl) * T0
Li00 = hf - (cl - ci) * T0
lines = open(out, errors="ignore").read().split("\n")
strip = lambda l: l.split(":", 1)[1] if l.strip()[:1].isdigit() and ":" in l[:8] else l
merged, i = [], 0
while i < len(lines):
    l = lines[i]
    if " EBQ " in l[:12] and len(l.split()) < 49 and i + 1 < len(lines):
        l = l + strip(lines[i + 1])[1:]
        i += 1
    merged.append(l)
    i += 1
EBQ, EBD, EMS, EML = {}, defaultdict(dict), defaultdict(dict), {}
for line in merged:
    w = line.split()
    if w and w[0].endswith(":") and w[0][:-1].isdigit():
        w = w[1:]
    if not w:
        continue
    try:
        if w[0] == "EBQ":
            EBQ[int(w[1])] = [float(x) for x in w[2:48]]
        elif w[0] == "EBD":
            EBD[int(w[1])][int(w[2])] = [float(x) for x in w[3:15]]
        elif w[0] == "EML":
            EML[int(w[1])] = [float(x) for x in w[2:10]]
        elif w[0] == "EMS":
            EMS[int(w[1])][int(w[2])] = [float(x) for x in w[3:13]]
    except (ValueError, IndexError):
        pass
steps = sorted(s for s in EBQ if s in EMS and 12 in EMS[s] and all(k in EBD.get(s, {}) for k in range(1, 11)))
n = len(steps)
A = EBQ[steps[0]][33]
W = lambda v: v / (A * dt * n)
TE = lambda v: v[0] + v[1] + v[2] + v[3]
EF = lambda v: TE(v) + Lv00 * v[5] - Li00 * v[7]
t = defaultdict(float)
for s in steps:
    d, m, q = EBD[s], EMS[s], [v / g for v in EBQ[s]]
    x = lambda i: q[i - 1]
    DEF = cpv * x(10) + (Lv00 - hv) * x(9) - cl * x(11) - ci * x(12) - (hf - Li00) * x(8) + x(13)
    Srem = x(16) - x(17)
    FP = m[12][6]
    dE = EF(d[6]) - EF(d[1])
    t["E_F(end) - E_F(start)"] += dE
    t["F_F = F_P + DEF (rad + SH + water boundary enthalpy)"] += FP + DEF
    t["RESIDUAL"] += dE - FP - DEF
    t[" dycore: fixer window"] += EF(d[9]) - EF(d[7])
    t[" dycore: other (fv_sg heat; its KE in coupling)"] += EF(d[7]) - EF(d[1]) + EF(d[3]) - EF(d[9])
    t[" physics: sum of scheme residuals r_P (physics frame)"] += m[12][0] - FP
    cF = EF(d[6]) - EF(d[4]) - m[12][0] - DEF
    t[" coupling in frame F: E_F(6)-E_F(4) - dE_P - DEF"] += cF
    t["   S_rem: physics latent heats vs Kirchhoff L(T)"] += Srem
    kin = d[6][2] + d[6][3] - d[4][2] - d[4][3] - m[12][4]
    t["   KE: write + update (KD+KW) - physics dK"] += kin
    t["   thermodynamic remainder (R_thermo) = coupling - S_rem - KE"] += cF - Srem - kin
    t["   applied C1 heating (encpl meter)"] += x(24)
    hand = m[3][0] - m[3][6]
    chem = m[6][0] - m[6][6]
    t["declared: surface hand-off heating (segment 3: ensfc2 LW1 + EV1, booked surface flux)"] += hand
    t["declared: h2ophys chemical water source S_chem = hvap*dWv"] += chem
    sw = EML[s][3] if s in EML else 0.0
    if EP1:
        t["declared: PH1 snow leaves as ice at T1 (in F_F with --ep1)"] += sw
    t["RESIDUAL net of the declared terms"] += dE - FP - DEF - hand - chem - (sw if EP1 else 0.0)
    if s in EML and len(EML[s]) >= 8:   # preclag meter v2: lag at probe 1 of N+1, as the surfaces will book it
        t["hand-off lag as the surfaces book it: c_w P(N)(T1_sfc - T1(N)), all surfaces"] += EML[s][0]
        t["  of which land (frland-weighted)"] += EML[s][1]
        t["  of which sea ice ((1-frland) fice)"] += EML[s][4]
        t["  lag if booked at T1(N+1) (pre-PL1 definition)"] += EML[s][5]
    elif s in EML:
        t["hand-off lag (not in atmosphere budget): c_w P(N)(T1(N+1)-T1(N)), all surfaces"] += EML[s][0]
        t["  of which land (frland-weighted)"] += EML[s][1]
        t["PH1 swap csnow (c_l - c_i)(T1 - T0) (diagnostic)"] += sw if not EP1 else 0.0
print(f"# {out}: {n} steps, frame F, W m-2")
for k, v in t.items():
    print(f"{k:66s} {W(v):+.6e}")
print("# note: RESIDUAL = dycore + r_P + coupling_F; r_P + S_rem is the scheme-vs-Kirchhoff remainder")
if EML and all(len(v) >= 8 for v in EML.values()):
    c7 = sum(v[6] for v in EML.values()); c8 = sum(v[7] for v in EML.values())
    print(f"# EML capacity check: sum|c tprcp(N+1 surface) - c P(N) (atmosphere)| / sum c P(N) = {c7 / c8 if c8 else 0.0:.3e}")
if EML:
    um = {k: int(v[2]) for k, v in EML.items() if v[2] > 0}
    print(f"# EML: {len(EML)} steps; unmatched columns (no previous step or remapped): {um if len(um) < 4 else str(len(um)) + ' steps'}")
