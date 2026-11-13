#!/usr/bin/env python3
"""PBL TKE / KE budget from a run's stdout (EMT, EMP lines) plus the PBL-segment residual (EMS slot 4).
usage: pbl_table.py <out> [dt=720]   W m-2 = mean over metered steps of sum/area."""
import sys
from collections import defaultdict

out = sys.argv[1]
dt = float(sys.argv[2]) if len(sys.argv) > 2 else 720.0
EMT, EMP, EMS = {}, defaultdict(dict), defaultdict(dict)
for line in open(out, errors="ignore"):
    w = line.split()
    if w and w[0].endswith(":") and w[0][:-1].isdigit():
        w = w[1:]
    if not w:
        continue
    try:
        if w[0] == "EMT":
            EMT[int(w[1])] = [float(x) for x in w[2:26]]
        elif w[0] == "EMP":
            EMP[int(w[1])][int(w[2])] = [float(x) for x in w[3:15]]
        elif w[0] == "EMS":
            EMS[int(w[1])][int(w[2])] = [float(x) for x in w[3:13]]
    except (ValueError, IndexError):
        pass
st = sorted(EMT)
n = len(st)
A = EMT[st[-1]][23]  # first line holds two steps
# EMT line k holds PBL step k+1; the first line also holds step 1 (p12 skips its reduce at step 1)
m = [sum(EMT[s][j] for s in st) / ((n + 1) * A) for j in range(24)]
N = {1: "P_shear (incl. EDMF momentum terms)", 2: "  of which surface-layer term (k=1)", 3: "P_buoy", 4: "  P_buoy > 0 part",
     5: "TKE floor at entry (max(q,tkmin))", 6: "eps, mean over the 20 substeps", 7: "eps removed by the clip",
     8: "TKE floor in substeps (tkmnz)", 9: "eps of the last substep (heated)", 10: "dTKE/dt local (P - eps + floors)",
     11: "dTKE/dt transport (diffusion + MF + borrowing)", 14: "-dKE/dt momentum solve (total)",
     15: "  surface stress work, implicit (u_new)", 16: "  surface stress work, explicit (u_old)",
     17: "  sum of local -dKE < 0 (cooling in the KE form)", 18: "heat solve: sum cp dT m - dtsfc (closure)",
     19: "dissipative heating actually applied", 20: "B&B: sum of layer heating < 0",
     21: "B&B: sum of interface D < 0", 22: "B&B: interface D from EDMF mass-flux transfer",
     23: "B&B: sum of (D - D_MF) < 0 (diffusive part)"}
print(f"# {out}: {n + 1} PBL steps in {n} EMT lines ({st[0]}..{st[-1]}), area {A:.6e}")
for j in sorted(N):
    print(f"{j:2d} {N[j]:48s} {m[j-1]:+.6e}")
print(f"   TKE content in / out (J m-2, step means)      {m[11]:.6e} / {m[12]:.6e}")
c0, c1 = EMT[st[1]][11] / A, EMT[st[-1]][12] / A
print(f"   TKE content in (step {st[1]+1}) -> out (step {st[-1]+1}) (J m-2) {c0:.6e} -> {c1:.6e}"
      f"  = {(c1 - c0) / ((st[-1] - st[1] + 1) * dt):+.3e} W m-2")
print(f"   excess eps_last - (-dKE)                      {m[8] - m[13]:+.6e}")
print(f"   identity check local: P - eps_mean + floor_sub - dTKE_local = {m[0] + m[2] - m[5] + m[7] - m[9]:+.3e}")
ks = sorted(EMS)
if ks:
    r = [EMS[s][4][0] - EMS[s][4][6] for s in ks if 4 in EMS[s]]
    ab = [EMS[s][4][7] for s in ks if 4 in EMS[s]]
    print(f"   PBL segment (EMS s=4): r = {sum(r) / (len(r) * A * dt):+.6e} W m-2, sum|r| = {sum(ab) / (len(ab) * A * dt):.6e},"
          f" max|r_step| = {max(abs(x) for x in r) / (A * dt):.3e}  ({len(r)} steps)")
# heating profiles: 12 columns = [old eps | per-layer -dKE | B&B] x [land-day, sea-day, land-night, sea-night]
if EMP:
    ps = sorted(EMP)
    L = max(EMP[ps[0]])
    tot = [[sum(EMP[s][k][j] for s in ps) / ((len(ps) + 1) * A) for j in range(12)] for k in range(1, L + 1)]
    F, C = ["old", "perlayer", "BB"], ["land-day", "sea-day", "land-night", "sea-night"]
    print("\n# heating by form x category (W m-2 of global area)")
    for f in range(3):
        print(f"{F[f]:9s} " + "  ".join(f"{C[c]} {sum(t[4*f+c] for t in tot):+.4f}" for c in range(4))
              + f"  total {sum(sum(t[4*f:4*f+4]) for t in tot):+.4f}  sum(min(layer,0)) {sum(min(sum(t[4*f:4*f+4]),0) for t in tot):+.4f}")
    bands = [(1, 1), (2, 3), (4, 6), (7, 10), (11, 15), (16, 20), (21, 30), (31, 45), (46, L)]
    print("# band(k)  old  perlayer  BB  | BB by land-day sea-day land-night sea-night | old by same")
    for a, b in bands:
        t = [sum(tot[k - 1][j] for k in range(a, b + 1)) for j in range(12)]
        print(f"{a:3d}-{b:3d}  {sum(t[0:4]):+.4f} {sum(t[4:8]):+.4f} {sum(t[8:12]):+.4f} | "
              + " ".join(f"{x:+.4f}" for x in t[8:12]) + " | " + " ".join(f"{x:+.4f}" for x in t[0:4]))
