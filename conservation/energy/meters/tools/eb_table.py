#!/usr/bin/env python3
"""Energy meter tables from a run's stdout ('out'): EBD/EBX (dycore, coupling) and EMS/EMF (physics).
Usage: eb_table.py <out> [dt=720] [--steps]   All terms as global-mean W m-2 averaged over the run
(sum over steps / (area * total time)); --steps prints per-step series of selected terms."""
import sys
from collections import defaultdict

out = sys.argv[1]
dt = 720.0
EBD = defaultdict(dict)
EBX = {}
EMS = defaultdict(dict)
EMF = {}
EBC = None
for line in open(out, errors="ignore"):
    w = line.split()
    if w and w[0].endswith(":") and w[0][:-1].isdigit():
        w = w[1:]
    if not w:
        continue
    try:
        if w[0] == "EBD":
            EBD[int(w[1])][int(w[2])] = [float(x) for x in w[3:15]]
        elif w[0] == "EBX":
            EBX[int(w[1])] = [float(x) for x in w[2:10]]
        elif w[0] == "EMS":
            EMS[int(w[1])][int(w[2])] = [float(x) for x in w[3:13]]
        elif w[0] == "EMF":
            EMF[int(w[1])] = [float(x) for x in w[2:14]]
        elif w[0] == "EBC":
            EBC = [float(x) for x in w[1:10]]
    except (ValueError, IndexError):
        pass

A = 5.10064e14
if EMF:
    A = next(iter(EMF.values()))[11]
cp, rd, rv, g, hlv, hlf, cpv, cl, ci = EBC if EBC else (1004.6, 287.05, 461.5, 9.80665, 2.5e6, 3.3358e5, 1846, 4185.5, 1972)
steps = sorted(EBD)
print(f"# file {out}  steps EBD {len(steps)} ({steps[0] if steps else '-'}..{steps[-1] if steps else '-'})  "
      f"EMS {len(EMS)}  area {A:.6e}  constants cp={cp} hlv={hlv} hlf={hlf} cpv={cpv} cl={cl} ci={ci}")


def TE(v):
    return v[0] + v[1] + v[2] + v[3]


def EP(v):  # physics-frame energy of the dycore state
    return v[9] + hlv * v[5] - hlf * v[7] + v[10]


def wm2(x, n):
    return x / (A * dt * n)


# ---- dycore and coupling, per-step differences
terms = defaultdict(float)
nst = 0
for s in steps:
    d = EBD[s]
    if not all(k in d for k in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)):
        continue
    nst += 1
    terms["dyc: te0 point - atmos_dyn start (TE)"] += TE(d[7]) - TE(d[1])
    terms["dyc: Rayleigh_Super (TE)"] += TE(d[8]) - TE(d[7])
    terms["dyc: dyn_core+tracers+remap+fixer (TE, 8->9)"] += TE(d[9]) - TE(d[8])
    terms["dyc: fixer window total te0->after fix (TE, 7->9)"] += TE(d[9]) - TE(d[7])
    terms["dyc: neg_adj3 (TE)"] += TE(d[10]) - TE(d[9])
    terms["dyc: end fv_dynamics -> after p_split (TE)"] += TE(d[2]) - TE(d[10])
    terms["dyc: fv_subgrid_z (TE)"] += TE(d[3]) - TE(d[2])
    terms["dyc: fv_subgrid_z (IE+PE+KW+KA, A-grid KE)"] += d[3][0] + d[3][1] + d[3][3] + d[3][4] - (d[2][0] + d[2][1] + d[2][3] + d[2][4])
    terms["dyc: fv_subgrid_z dKA"] += d[3][4] - d[2][4]
    terms["dyc: fv_subgrid_z dIE+dPE"] += d[3][0] + d[3][1] - d[2][0] - d[2][1]
    terms["dyc: fv_subgrid_z dKW"] += d[3][3] - d[2][3]
    terms["cpl: dyn end -> state_update start (TE)"] += TE(d[4]) - TE(d[3])
    terms["cpl: delp/q write (TE)"] += TE(d[5]) - TE(d[4])
    terms["cpl: delp/q write: IE"] += d[5][0] - d[4][0]
    terms["cpl: delp/q write: PE"] += d[5][1] - d[4][1]
    terms["cpl: delp/q write: KD"] += d[5][2] - d[4][2]
    terms["cpl: delp/q write: mass (kg, as W m-2 x1)"] += d[5][8] - d[4][8]
    terms["cpl: fv_update_phys (TE)"] += TE(d[6]) - TE(d[5])
    terms["cpl: fv_update_phys IE+PE"] += d[6][0] + d[6][1] - d[5][0] - d[5][1]
    terms["cpl: fv_update_phys KD"] += d[6][2] - d[5][2]
    terms["cpl: fv_update_phys KA"] += d[6][4] - d[5][4]
    if s in EBX:
        terms["cpl: intended heating sum cp_air t_dt dt delp/g"] += EBX[s][3]
        terms["dyc: fixer intended (consv*sum(te0-te))"] += EBX[s][1]
        terms["dyc: E_Flux (W m-2, summed)"] += EBX[s][2] * A * dt
        terms["dyc: te0 (g_sum) - TE(slot7)"] += EBX[s][0] - TE(d[7])
    if s + 1 in EBD and 1 in EBD[s + 1]:
        terms["gap: step end -> next atmos_dyn start (TE)"] += TE(EBD[s + 1][1]) - TE(d[6])
    terms["water: delp/q write dWv"] += d[5][5] - d[4][5]
    terms["water: delp/q write dWl"] += d[5][6] - d[4][6]
    terms["water: delp/q write dWi"] += d[5][7] - d[4][7]
print(f"\n## dycore and coupling ({nst} steps), global mean W m-2 (water rows kg m-2 s-1)")
for k, v in terms.items():
    print(f"{k:58s} {wm2(v, nst):+.6e}")

# ---- physics segments
segname = {1: "1->2 interstitial_1..composites_pre", 2: "2->3 dcyc2t3 (radiation)", 3: "3->4 surface loop..sfc_diag_post",
           4: "4->5 PBL (sfc_generic_post..PBL_post)", 5: "5->6 GWD (+apply)", 6: "6->7 photochem",
           7: "7->8 SAMF deep", 8: "8->9 SAMF shallow", 9: "9->10 interst_4, cnvc90", 10: "10->11 Thompson+MP_post",
           11: "11->12 maximum_hourly..physics_post", 12: "ALL physics 1->12"}
ks = sorted(EMS)
if ks:
    acc = defaultdict(lambda: [0.0] * 10)
    for k in ks:
        for s, v in EMS[k].items():
            acc[s] = [a + b for a, b in zip(acc[s], v)]
    n = len(ks)
    print(f"\n## physics frame, {n} steps, W m-2: dE  dcpT  dLvq  d(-Lf qi)  dK | dW(kg m-2 s-1)  F  sum|r|  dW-Wflux")
    for s in range(1, 13):
        v = acc[s]
        print(f"{segname[s]:40s} " + " ".join(f"{wm2(x, n):+.4e}" for x in v[:5]) + f" | {wm2(v[5], n):+.3e} "
              + f"{wm2(v[6], n):+.4e} {wm2(v[7], n):.4e} {wm2(v[8], n):+.3e} | r=dE-F {wm2(v[0] - v[6], n):+.6e} | dE* {wm2(v[9], n):+.4e} gap {wm2(v[9] - v[0], n):+.4e}")
    f = [0.0] * 12
    for k in ks:
        if k in EMF:
            f = [a + b for a, b in zip(f, EMF[k])]
    lab = ["E_phys(probe1) J", "W(probe1) kg", "SWnet TOA*xmu", "-OLR", "SWnet sfc*xmu (rad)", "LWnet sfc (rad, down)",
           "adjsfcnsw", "adjsfcdlw", "SH (dtsfc1)", "LH (dqsfc1)", "precip kg", "area"]
    print("\n## physics extras (W m-2 means except first two, per-step means)")
    for i, l in enumerate(lab[:11]):
        val = f[i] / n / A if i < 2 else wm2(f[i], n)
        print(f"{l:28s} {val:+.6e}")

if "--steps" in sys.argv:
    print("\n## per step: kstep TE(1) fixerwindow(7->9) sgz cpl_write cpl_upd intended  EP(4)  E_phys(probe1, from EMF)")
    for s in steps:
        d = EBD[s]
        if 9 not in d:
            continue
        ep1 = EMF.get(s, [float('nan')])[0]
        print(f"{s:4d} {TE(d[1]):.16e} {wm2(TE(d[9]) - TE(d[7]), 1):+.4e} {wm2(TE(d[3]) - TE(d[2]), 1):+.4e} "
              f"{wm2(TE(d[5]) - TE(d[4]), 1):+.4e} {wm2(TE(d[6]) - TE(d[5]), 1):+.4e} "
              f"{wm2(EBX.get(s, [0] * 4)[3], 1):+.4e} {EP(d[4]):.16e} {ep1:.16e}")

# ---- global budget in the frame E_D = TE + hlv*Wv - hlf*Wi (physics latent constants on the FV3 TE)
if ks and steps:
    ED = lambda v: TE(v) + hlv * v[5] - hlf * v[7]
    tot = defaultdict(float)
    nb = 0
    for s in ks:
        if s not in EBD or 6 not in EBD[s] or 12 not in EMS[s]:
            continue
        d, m = EBD[s], EMS[s]
        nb += 1
        F = m[12][6]
        dEP = m[12][0]
        tot["E_D(end) - E_D(start of step)"] += ED(d[6]) - ED(d[1])
        tot["boundary flux F (rad TOA-sfc + SH + LH + hfus*P_ice)"] += F
        tot["residual total"] += ED(d[6]) - ED(d[1]) - F
        tot[" dycore: fixer window (7->9)"] += ED(d[9]) - ED(d[7])
        tot[" dycore: other dyn (1->7, 9->3)"] += ED(d[7]) - ED(d[1]) + ED(d[3]) - ED(d[9])
        tot[" physics: dE_P - F (sum of schemes)"] += dEP - F
        tot[" coupling: E_D(6)-E_D(4) - dE_P"] += ED(d[6]) - ED(d[4]) - dEP
        tot["   coupling: delp/q write dTE"] += TE(d[5]) - TE(d[4])
        tot["   coupling: heating injected - phys dcpT (= C1 + D7 heat when on)"] += (d[6][0] + d[6][1] - d[5][0] - d[5][1]) - m[12][1]
        tot["   coupling: dKD+dKW - phys dK"] += (d[6][2] + d[6][3] - d[5][2] - d[5][3]) - m[12][4]
        tot["   KE+heating closure (D7 exact => equals C1 heating; 0 if C1 off)"] += (
            (d[6][0] + d[6][1] + d[6][2] + d[6][3] - d[5][0] - d[5][1] - d[5][2] - d[5][3]) - m[12][1] - m[12][4]
            + ED(d[3]) - ED(d[2]))
        tot["   water write dTE + C1 heating (derived above): D2 after C1"] += (TE(d[5]) - TE(d[4])
            + (d[6][0] + d[6][1] + d[6][2] + d[6][3] - d[5][0] - d[5][1] - d[5][2] - d[5][3]) - m[12][1] - m[12][4]
            + ED(d[3]) - ED(d[2]))
        tot["   check: latent terms dycore - physics"] += (hlv * (d[6][5] - d[4][5]) - hlf * (d[6][7] - d[4][7])) - (m[12][2] + m[12][3])
        tot["   check: E_P(probe1) - E_P(dycore slot 4)"] += EMF[s][0] - EP(d[4]) if s in EMF else 0.0
    print(f"\n## global budget, frame E_D = TE + hlv*Wv - hlf*Wi, {nb} steps, W m-2")
    for k, v in tot.items():
        print(f"{k:58s} {wm2(v, nb):+.6e}")
