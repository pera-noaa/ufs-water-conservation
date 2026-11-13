#!/usr/bin/env python3
"""Coupling-write budget in the frame of report.md, from a run's stdout ('out'): EBQ (coupling meter),
EBD/EBX (dycore meters), EMS (physics meter), EMK (Thompson per process).
Usage: cpl_table.py <out> [dt=720]   All terms global-mean W m-2 over the metered steps."""
import sys
from collections import defaultdict

out = sys.argv[1]
dt = float(sys.argv[2]) if len(sys.argv) > 2 else 720.0
EBQ, EBX, EMK, EMC = {}, {}, defaultdict(dict), {}
EBD, EMS = defaultdict(dict), defaultdict(dict)
lines = open(out, errors="ignore").read().split("\n")
strip = lambda l: l.split(":", 1)[1] if l.strip()[:1].isdigit() and ":" in l[:8] else l
merged = []
i = 0
while i < len(lines):
    l = lines[i]
    if " EBQ " in l[:12] and len(l.split()) < 49 and i + 1 < len(lines):
        l = l + strip(lines[i + 1])[1:]  # stdout record wrapped at 1024 characters, mid-number
        i += 1
    merged.append(l)
    i += 1
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
        elif w[0] == "EBX":
            EBX[int(w[1])] = [float(x) for x in w[2:10]]
        elif w[0] == "EMS":
            EMS[int(w[1])][int(w[2])] = [float(x) for x in w[3:13]]
        elif w[0] == "EMC":
            EMC[int(w[1])] = [float(x) for x in w[2:6]]
        elif w[0] == "EMK":
            EMK[int(w[1])][int(w[2])] = [float(x) for x in w[3:9]]
    except (ValueError, IndexError):
        pass

g, cp, rv, cpv, cvv, cl, ci, hv, hf, T0 = 9.80665, 1004.6, 461.5, 1846.0, 3 * 461.5, 4185.5, 1972.0, 2.5e6, 3.3358e5, 273.15
Lv00 = hv - (cpv - cl) * T0
Li00 = hf - (cl - ci) * T0
steps = sorted(s for s in EBQ if s in EBD and 4 in EBD[s] and 6 in EBD[s])
n = len(steps)
A = EBQ[steps[0]][33]
W = lambda x: x / (A * dt * n)
NQ = len(EBQ[steps[0]])
q = [sum(EBQ[s][i] for s in steps) / g for i in range(NQ)]  # J (Pa*J/kg*m2 / g), kg for water rows
x = lambda i: q[i - 1]


def TE(v):
    return v[0] + v[1] + v[2] + v[3]


def EF(v):  # frame F: FV3 TE + Kirchhoff latent terms (Lv00, Li00)
    return TE(v) + Lv00 * v[5] - Li00 * v[7]


D2F = x(1) + x(2) + x(3) + (Lv00 - hv) * x(4) + (hf - Li00) * x(6)
DEF = cpv * x(10) + (Lv00 - hv) * x(9) - cl * x(11) - ci * x(12) - (hf - Li00) * x(8) + x(13)
S, Sx, FW, PE, K = x(16), x(17), x(14), x(15), x(3)
Srem = S - Sx
rows = [
    ("D2 in frame F: write, sum dm_w*(e_w^F(T,phi,K) - e_w^P)", D2F),
    ("(a) DEF: boundary enthalpy E*(h_v(T1)+phis) - P*(h_w(T1)+phis), minus physics-frame booking", DEF),
    ("(b) PE_rel: sum dm*(phi - phis)  [water PE created/destroyed by the write]", PE),
    ("    of which downward net flux (precipitation; Pauluis heating missing)", -x(29)),
    ("    of which upward net flux (vapour lifted; PE given for free)", -x(30)),
    ("(b) FW: -Rv*sum dmv*T  [vapour mass written at fixed volume]", FW),
    ("(b) S_cross: water crossing interfaces keeps no heat exchange (c_l/c_i down, cp_v up)", Sx),
    ("    downward part / upward part", None),
    ("(b) K: sum dm*KA", K),
    ("(p) S_rem = S - S_cross: physics latent heats vs Kirchhoff L(T)", Srem),
    ("identity D2F - (DEF+S+FW+PE+K)", D2F - (DEF + S + FW + PE + K)),
]
print(f"# {out}: {n} steps, area {A:.6e}; W m-2")
for lab, v in rows:
    if v is None:
        print(f"  {lab:86s} {W(x(27)):+.5e} / {W(x(28)):+.5e}")
    else:
        print(f"  {lab:86s} {W(v):+.5e}")
print(f"  S_cross with c_liq for all downward flux (alternative)                                 {W(x(26)):+.5e}")
print(f"  fix components: sum qpe {W(x(18)):+.5e} qfw {W(x(19)):+.5e} qse {W(x(20)):+.5e} applied {W(x(24)):+.5e}")
print(f"  layer sum|q|:   qpe {W(x(21)):.5e} qfw {W(x(22)):.5e} qse {W(x(23)):.5e}")
print(f"  column sum|.|:  PE_rel {W(x(31)):.5e} FW {W(x(32)):.5e} S_cross {W(x(33)):.5e}")
if NQ >= 46:
    print(f"  gross PE release by precipitation: deep {W(x(35)):+.5e} shallow {W(x(36)):+.5e} Thompson liq {W(x(37)):+.5e} "
          f"ice {W(x(38)):+.5e}  total {W(x(35)+x(36)+x(37)+x(38)):+.5e}; residual flux {W(x(39)):+.5e}; sum {W(sum(x(i) for i in range(35,40))):+.5e} (= -PE_rel)")
    print(f"  S_cross parts: liquid precip {W(x(40)):+.5e} ice precip {W(x(41)):+.5e} residual (cp_v) {W(x(42)):+.5e}")
    print(f"  surface precipitation from exported fluxes {W(x(43)):.5e} vs diag {W(x(7)+x(8)):.5e} kg m-2 s-1")
    print(f"  D11 interface: E*(cp_v-c_l)*(Tskin-T0) {W(x(44)):+.5e}  E*cp_v*(Tskin-T1) {W(x(45)):+.5e}  E-weighted Tskin-T1 {x(46)/max(x(9),1e-30):+.3f} K")
print(f"  water kg m-2 s-1: dWv {W(x(4)):+.4e} dWl {W(x(5)):+.4e} dWi {W(x(6)):+.4e} P_liq {W(x(7)):.4e} "
      f"P_ice {W(x(8)):.4e} E {W(x(9)):.4e}")

# independent checks against the dycore meter (eb_state) and closure
c = defaultdict(float)
for s in steps:
    d = EBD[s]
    c["IE write (eb_state 5-4) - W_IE"] += (d[5][0] - d[4][0]) - EBQ[s][0] / g
    c["PE write (eb_state 5-4) - W_PE"] += (d[5][1] - d[4][1]) - EBQ[s][1] / g
    c["KD write (eb_state 5-4)"] += d[5][2] - d[4][2]
    c["KA*m write (eb_state 5-4, slot 5 KA) - W_K"] += (d[5][4] - d[4][4]) - EBQ[s][2] / g
    c["injected (eb_state 6-5 IE+PE) - (phys heating + applied q)"] += (d[6][0] + d[6][1] - d[5][0] - d[5][1]) \
        - (EBQ[s][24] + EBQ[s][23]) / g
    c["EBX4 intended - (phys heating + applied q)"] += EBX[s][3] - (EBQ[s][24] + EBQ[s][23]) / g if s in EBX else 0.0
    c["dKD+dKW in fv_update_phys (D7 + physics dK)"] += d[6][2] + d[6][3] - d[5][2] - d[5][3]
    # thermodynamic coupling residual in frame F, eb_state for the state, meter for physics heating and frame terms
    tf = lambda v: v[0] + v[1] + Lv00 * v[5] - Li00 * v[7]
    c["R_thermo = T_F(6)-T_F(4) - phys(heat+hvap*dWv-hfus*dWi) - DEF - S_rem"] += \
        tf(d[6]) - tf(d[4]) - EBQ[s][24] / g - hv * EBQ[s][3] / g + hf * EBQ[s][5] / g
print("\n## checks (W m-2)")
c["R_thermo = T_F(6)-T_F(4) - phys(heat+hvap*dWv-hfus*dWi) - DEF - S_rem"] -= DEF + Srem
for k, v in c.items():
    print(f"  {k:86s} {W(v):+.5e}")
print(f"  {'expected R_thermo = PE_rel + FW + S_cross + applied':86s} {W(PE + FW + Sx + x(24)):+.5e}")

if EMC:
    ks = sorted(EMC)
    v = [sum(EMC[s][i] for s in ks) / (A * dt * len(ks)) for i in range(4)]
    print(f"\n## SAMF Kirchhoff gap (hvap - L_v(T))*C, {len(ks)} steps, W m-2: deep {v[0]:+.5e} (sum|.| {v[1]:.4e})  "
          f"shallow {v[2]:+.5e} (sum|.| {v[3]:.4e})")

if EMK:
    ks = [s for s in sorted(EMK) if len(EMK[s]) == 7]
    m = len(ks)
    names = {1: "cloud cond/evap", 2: "rain evaporation", 3: "deposition/sublimation", 4: "freezing/riming",
             5: "melting", 6: "clean-up with vapour", 7: "-"}
    print(f"\n## Thompson per process vs Kirchhoff L_F(T), {m} steps, W m-2: heat  gap  sum|gap|  heat(220-250K) "
          f"gap(220-250K)  gap/heat(220-250K)  dm(kg m-2 s-1)")
    tot = [0.0] * 6
    for p in range(1, 8):
        v = [sum(EMK[s][p][i] for s in ks) / (A * dt * m) for i in range(6)]
        tot = [a + b for a, b in zip(tot, v)]
        r = v[4] / v[3] if v[3] else float("nan")
        print(f"  {p} {names[p]:24s} " + " ".join(f"{y:+.4e}" for y in v[:5]) + f" {r:+.3e} {v[5]:+.3e}")
    print(f"  {'all':26s} " + " ".join(f"{y:+.4e}" for y in tot[:5]))
