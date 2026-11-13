#!/usr/bin/env python3
"""dsp_table.py <out> [dt=720] [k_split=2] : sa3dtke double-heating budget, global W m-2 per run.
PBL: EMS segment 4 (dE - F, dK) and UCM slots 17-20 (add_dspm.py); dycore: UCD lines (one per dyn_core call)."""
import sys
out = sys.argv[1]
dt = float(sys.argv[2]) if len(sys.argv) > 2 else 720.0
ks = int(sys.argv[3]) if len(sys.argv) > 3 else 2
E, F, M, D = {}, {}, {}, []
for l in open(out, errors="ignore"):
    w = l.split()
    if w and w[0].endswith(":") and w[0][:-1].isdigit():
        w = w[1:]
    try:
        if len(w) > 3 and w[0] == "EMS" and w[2] == "4":
            E[int(w[1])] = [float(x) for x in w[3:17]]
        elif len(w) > 2 and w[0] == "EMF":
            F[int(w[1])] = [float(x) for x in w[2:14]]
        elif len(w) > 2 and w[0] == "UCM":
            M[int(w[1])] = [float(x) for x in w[2:27]]
        elif len(w) == 5 and w[0] == "UCD":
            D.append([float(x) for x in w[1:5]])
    except ValueError:
        pass
st = sorted(k for k in E if k in M and k in F)
n = len(st)
A = F[st[0]][11]
W = lambda s: s / (A * n)               # rate sums (W per step) -> W m-2
WE = lambda s: s / (A * dt * n)         # energy sums (J per step) -> W m-2
res = WE(sum(E[k][0] - E[k][6] for k in st))
dK = WE(sum(E[k][4] for k in st))
a = W(sum(M[k][16] for k in st)); b = W(sum(M[k][17] for k in st))
c = W(sum(M[k][18] for k in st)); s = W(sum(M[k][19] for k in st))
T = len(D) / ks * dt
hn = sum(x[0] for x in D) / (A * T) if D else 0.0
ha = sum(x[1] for x in D) / (A * T) if D else 0.0
sdef = sum(x[2] for x in D); sdiv = sum(x[3] for x in D)
print(f"# {out}: {n} physics steps, {len(D)} UCD lines ({T / 3600:.2f} h), area {A:.6e}")
print(f"PBL residual dE-F (EMS seg 4)            {res:+.6e} W/m2")
print(f"(a) horizontal shear prod, as in prod     {a:+.6e} W/m2   (2*dku_h*def_2 would be {2 * a:+.6e})")
print(f"(b) vertical shear prod, as in prod       {b:+.6e} W/m2")
print(f"    surface-stress prod (k=1)             {s:+.6e} W/m2")
print(f"(c) dissipative heating dspfac*diss       {c:+.6e} W/m2")
if len(M[st[0]]) >= 25:
    print(f"(c') applied D1 heating sum m cp dspq        {W(sum(M[k][24] for k in st)):+.6e} W/m2")
print(f"(d) PBL KE change dK (EMS seg 4)          {dK:+.6e} W/m2")
print(f"    gate: (c) + (d) vs residual           {c + dK:+.6e} vs {res:+.6e}  (diff {res - c - dK:+.3e})")
print(f"dycore heat_source nominal / applied      {hn:+.6e} / {ha:+.6e} W/m2")
if len(M[st[0]]) >= 24:
    p1, p2, p3, sh = (W(sum(M[k][j] for k in st)) for j in (20, 21, 22, 23))
    print(f"(b-i) 2(dw/dz)^2 part                    {p1:+.6e} W/m2")
    print(f"(b-ii) (du/dz)^2+(dv/dz)^2 part           {p2:+.6e} W/m2")
    print(f"(b-iii) w-u cross part                    {p3:+.6e} W/m2")
    print(f"    gate: i+ii+iii vs (b)                 {p1 + p2 + p3:+.6e} vs {b:+.6e}  (diff {b - p1 - p2 - p3:+.3e})")
    print(f"shr2 shadow (PBL own shear, as if off)    {sh:+.6e} W/m2")
    print(f"(ii) - shr2 (level/timing/no dw2min)      {p2 - sh:+.6e} W/m2;  w part (i)+(iii) {p1 + p3:+.6e} W/m2")
print(f"divergent fraction of dku_h-weighted def_2 {sdiv / sdef if sdef else 0.0:.4e} -> (a)_div = {a * sdiv / sdef if sdef else 0.0:+.6e} W/m2")
