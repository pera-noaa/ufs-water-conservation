#!/usr/bin/env python3
"""uc_table.py <run out> [dt=720] : 24-h budgets from the upchk run log.
EMS (physics energy meter v2, ported): per segment, energy residual dE - F (physics frame) and frame F, W m-2;
water residual dW - W_boundary, kg m-2 per run. UCT: tracer mass change per segment / initial mass, per run.
UCH (#403): horizontal-diffusion sums; UCM (#390): MLM column-integral sums. All global means over the steps present."""
import sys
from collections import defaultdict

out = sys.argv[1]
dt = float(sys.argv[2]) if len(sys.argv) > 2 else 720.0
EMS, EMF, UCT, UCH, UCM = defaultdict(dict), {}, defaultdict(dict), defaultdict(dict), {}
for line in open(out, errors="ignore"):
    w = line.split()
    if w and w[0].endswith(":") and w[0][:-1].isdigit():
        w = w[1:]
    if len(w) < 3:
        continue
    try:
        if w[0] == "EMS":
            EMS[int(w[1])][int(w[2])] = [float(x) for x in w[3:17]]
        elif w[0] == "EMF":
            EMF[int(w[1])] = [float(x) for x in w[2:14]]
        elif w[0] == "UCT":
            UCT[int(w[1])][int(w[2])] = [float(x) for x in w[3:8]]
        elif w[0] == "UCH":
            UCH[int(w[1])][int(w[2])] = [float(x) for x in w[3:8]]
        elif w[0] == "UCM":
            UCM[int(w[1])] = [float(x) for x in w[2:22]]
    except (ValueError, IndexError):
        pass
steps = sorted(s for s in EMS if 12 in EMS[s] and s in EMF)
if not steps:
    sys.exit(f"{out}: no EMS steps")
A = EMF[steps[0]][11]
n = len(steps)
print(f"# {out}: {n} steps (kdt {steps[0]}..{steps[-1]}), area {A:.6e} m2, dt {dt}")
SEG = {1: "sfc_pre", 2: "radiation", 3: "surface", 4: "PBL", 5: "GWD", 6: "photochem", 7: "SAMF deep",
       8: "SAMF shallow", 9: "cnvc90", 10: "microphysics", 11: "MP post", 12: "all physics"}
print(f"{'segment':14s} {'dE-F W/m2':>14s} {'frameF r W/m2':>14s} {'sum|r| W/m2':>12s} {'water r kg/m2':>14s} {'dK W/m2':>12s}")
for s in range(1, 13):
    e = sum(EMS[k][s][0] - EMS[k][s][6] for k in steps) / (A * dt * n)
    rf = sum(EMS[k][s][10] for k in steps) / (A * dt * n) if len(EMS[steps[0]][s]) > 10 else float('nan')  # v1 meter: no frame F
    ab = sum(EMS[k][s][7] for k in steps) / (A * dt * n)
    wr = sum(EMS[k][s][8] for k in steps) / A
    dk = sum(EMS[k][s][4] for k in steps) / (A * dt * n)
    print(f"{s:2d} {SEG[s]:11s} {e:+14.6e} {rf:+14.6e} {ab:12.4e} {wr:+14.6e} {dk:+12.4e}")
if UCT:
    ts = sorted(k for k in UCT if k in steps)
    print(f"# UCT tracer mass change per run / mass at first step ({len(ts)} steps)")
    print(f"{'n':>3s} {'M0 kg':>14s} {'PBL':>12s} {'GWD..photo':>12s} {'SAMF deep':>12s} {'SAMF shal':>12s}")
    for t in sorted(UCT[ts[0]]):
        m0 = UCT[ts[0]][t][0]
        r = [sum(UCT[k][t][j] for k in ts) / m0 if m0 else 0.0 for j in range(1, 5)]
        print(f"{t:3d} {m0:14.6e} " + " ".join(f"{x:+12.4e}" for x in r))
if UCH:
    hs = sorted(k for k in UCH if k in steps and any(abs(v[0]) > 0 for v in UCH[k].values()))
    print(f"# UCH horizontal diffusion ({len(hs)} steps with a nonzero term): n=0 T (J), n>=1 vdiff tracer (kg)")
    print(f"{'n':>3s} {'Smass/run':>14s} {'Smass/Gmass':>12s} {'Sarea/Garea':>12s} {'Smass/M0':>12s} {'W/m2 or kg/m2':>14s}")
    for t in sorted(UCH[hs[0]]) if hs else []:
        sm = sum(UCH[k][t][0] for k in hs)
        gm = sum(UCH[k][t][2] for k in hs)
        sa = sum(UCH[k][t][1] for k in hs)
        ga = sum(UCH[k][t][3] for k in hs)
        m0 = UCH[hs[0]][t][4]
        unit = sm / (A * dt * n) if t == 0 else sm / A
        print(f"{t:3d} {sm:+14.6e} {sm / gm if gm else 0:+12.4e} {sa / ga if ga else 0:+12.4e} "
              f"{sm / m0 if m0 else 0:+12.4e} {unit:+14.6e}")
if UCM:
    ms = sorted(k for k in UCM if k in steps)
    nv = len(UCM[ms[0]])
    v = [sum(UCM[k][j] for k in ms) for j in range(nv)]
    act = [UCM[k][13] for k in ms]
    print(f"# UCM MLM column integrals ({len(ms)} steps; active columns per step max {max(act):.0f}, mean {sum(act) / len(act):.1f})")
    lab = ["E mass-weighted W/m2", "W mass-weighted kg/m2/run", "gross |E| W/m2", "gross |W| kg/m2/run",
           "E dz-weighted (rel. to dz-gross)", "W dz-weighted", "smoothing E mass-w W/m2", "smoothing W kg/m2/run",
           "smoothing E dz-w (rel. to dz-gross)", "smoothing W dz-w", "momentum u (sum m du)", "momentum v",
           "KE rate sum m(u du + v dv) W/m2", "active area x steps", "dz-gross |E|", "sum cloud-base index",
           "whole satmedmfvdifq water gap kg/m2/run", "its gross kg/m2/run", "rain+graupel part kg/m2/run", "surface evap kg/m2/run"]
    conv = [1 / (A * n), dt / A, 1 / (A * n), dt / A, 1 / v[14] if v[14] else 0, 1.0, 1 / (A * n), dt / A,
            1 / v[14] if v[14] else 0, 1.0, 1.0, 1.0, 1 / (A * n), 1.0, 1.0, 1.0, dt / A, dt / A, dt / A, dt / A]
    for j in range(nv):
        print(f"  {j + 1:2d} {lab[j]:38s} {v[j] * conv[j]:+14.6e}")
