"""Tables from the suites meter (SMS/SMT/SMX lines in <run>/out).
usage: analyze_sm.py <run dir> [kdt0 kdt1]   (steps kdt0..kdt1 inclusive; default all printed steps)
Water: kg m-2 global mean over the window, and per-step max |r|/scale; energy: W m-2; tracer: fraction of mass."""
import sys
from collections import defaultdict
from pathlib import Path

run = Path(sys.argv[1])
SEG = {8: ["rad+sfc (no F)", "MYNN-EDMF", "GWD", "phot+SAMF deep", "intst4+cnvc90", "MP (Thompson)", "post"],
       9: ["rad+sfc (no F)", "PBL (satmedmfvdifq)", "GWD", "phot+SAMF deep", "SAMF shallow", "intst4+cnvc90",
           "MP (GFDL v3)", "post"],
       10: ["rad+sfc (no F)", "MYNN-EDMF", "GWD", "phot+intst3", "GF (+DCNV post)", "intst4", "cnvc90",
            "MP (Thompson)", "post"]}
sms, smt, smx = defaultdict(dict), {}, {}
for line in open(run / "out", errors="ignore"):
    if line.startswith("SMS "):
        p = line.split()
        sms[int(p[1])][int(p[2])] = [float(x) for x in p[3:]]
    elif line.startswith("SMT "):
        p = line.split()
        smt[int(p[1])] = [float(x) for x in p[2:]]
    elif line.startswith("SMX "):
        p = line.split()
        smx[int(p[1])] = [float(x) for x in p[2:]]
ks = sorted(sms)
if len(sys.argv) > 3:
    ks = [k for k in ks if int(sys.argv[2]) <= k <= int(sys.argv[3])]
nseg = max(sms[ks[0]]) - 1
np_ = nseg
names = SEG.get(np_, [f"s{i}" for i in range(1, np_)]) + ["PHYSICS (p1->end)", "DYN+coupling"]
area = smt[ks[0]][3]
dt = {8: 720., 9: 720., 10: 300.}.get(np_, 720.)
T = len(ks) * dt
tu0, ts0 = smt[ks[0]][1], smt[ks[0]][2]
print(f"run {run.name}: steps {ks[0]}..{ks[-1]} ({len(ks)}), {T/3600:.2f} h, area {area:.6e}")
print(f"W0 {smt[ks[0]][0]/area:.6f} kg/m2  Tu0 {tu0/area:.6e}  Ts0 {ts0/area:.6e}")
for k in (ks[0], ks[-1]):
    print(f"  SMT kdt {k}: W {smt[k][0]/area:.12f}  Tu/Tu0-1 {smt[k][1]/tu0-1:.3e}  Ts/Ts0-1 {smt[k][2]/ts0-1:.3e}")
hdr = (f"{'segment':22s} {'dW':>12s} {'flux':>12s} {'rW':>12s} {'rW/|flux|':>10s} {'sum|rWc|':>10s} "
       f"{'maxstep|rW|':>11s} {'rE_P':>11s} {'F_P':>9s} {'dKE':>10s} {'rE_F':>11s} {'dTu/Tu0':>10s} {'dTs/Ts0':>10s} {'dDevU':>9s} {'-Lf*dWi':>9s} {'dWv':>10s}")
print("water kg/m2 per window (global mean); energy W/m2; tracers fraction of initial mass")
print(hdr)
for s in range(1, np_ + 2):
    nv = len(sms[ks[0]][s]) if s in sms[ks[0]] else 14
    v = [sum(sms[k][s][i] for k in ks if s in sms[k]) for i in range(nv)] + [0.] * (16 - nv)
    mx = max(abs(sms[k][s][2]) for k in ks if s in sms[k]) / area
    fl = v[1] / area
    rel = v[2] / v[1] if v[1] != 0 else float("nan")
    print(f"{names[s-1]:22s} {v[0]/area:12.5e} {fl:12.5e} {v[2]/area:12.4e} {rel:10.2e} {v[3]/area:10.3e} "
          f"{mx:11.3e} {v[6]/area/T:11.4e} {v[5]/area/T:9.3f} {v[7]/area/T:10.3e} {v[10]/area/T:11.4e} "
          f"{v[11]/tu0:10.2e} {v[12]/ts0:10.2e} {v[13]/area:9.2e} {-v[14]/area/T*334000.:9.3f} {v[15]/area:10.3e}")
if smx:
    nx = min(len(v) for v in smx.values()); x = [sum(smx[k][i] for k in ks if k in smx) / area if i < nx else 0. for i in range(48)]
    print("SMX (kg/m2 or J/m2 per window, global mean; counts area-weighted /area):")
    lab = {1: "MYNN E reported", 2: "MYNN E before clip", 3: "MYNN sfc water solved", 4: "MYNN rho1*flqv*dt",
           5: "MYNN dW rho*dz pre-mc", 6: "MYNN dW rho*dz post-mc", 7: "MYNN dW host of tend", 8: "MYNN dew-limiter cut",
           9: "MYNN SH reported J", 10: "MYNN SH solved J", 11: "MYNN host cp*dT J", 12: "MYNN clip events",
           13: "GF raincv sh-only", 14: "GF raincv deep", 15: "GF raincv other", 16: "GF prets sh-only",
           17: "GF prets deep cols", 18: "GF pret deep", 19: "GF pretm", 20: "GF cond floor (mr)", 21: "GF qv floor n",
           22: "GF class sum", 23: "GF dW host sh-only", 24: "GF dW host deep", 25: "GF dW host other", 26: "GFsh own-frame dW", 27: "GFsh own pre*dt",
           28: "GFDL dW scheme frame", 29: "GFDL P raw (+water0)", 30: "GFDL P booked", 31: "GFDL water0",
           32: "GFDL dW host frame", 33: "MYNN diss heat J", 34: "MYNN cp*exner*dthl J", 35: "MYNN tcd J", 36: "MYNN sub+det J", 37: "MYNN MF explicit J", 38: "MYNN implicit op J", 39: "MYNN implicit op no-exner", 40: "MYNN mcheck thl heat J", 41: "MYNN mcheck cond fill", 42: "GF closure moist cols", 43: "GF closure water cut", 44: "GFDL frame-F gap J", 45: "GFDL own-frame gap J", 46: "MYNN E ideal-gas rho", 47: "GFDL frame-F gap +PE J", 48: "GFDL own gap +PE J"}
    for i in range(48):
        if x[i] != 0 or (i + 1) in lab:
            if x[i] != 0:
                print(f"  x{i+1:02d} {lab.get(i+1, ''):24s} {x[i]: .6e}")
    d = lambda a, b: x[a-1] - x[b-1]
    print("  diffs: x07-x05 (host vs rho*dz frame) %.6e | x05-x03 (dW rho*dz - sfc solved) %.6e | x03-x01 %.6e | x06-x05 (moisture_check) %.6e"
          % (d(7, 5), d(5, 3), d(3, 1), d(6, 5)))
    print("  MYNN thl-energy gap x34-x10-x33-x35-x36 = %.6e J/m2 (%.3e W/m2); GFDL x44 %.4e x47 %.4e W/m2"
          % (x[33]-x[9]-x[32]-x[34]-x[35], (x[33]-x[9]-x[32]-x[34]-x[35])/T, x[43]/T, x[46]/T))
