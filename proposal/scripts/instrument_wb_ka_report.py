#!/usr/bin/env python3
"""Summarise instrument_wb_ka.py meter output (WKA per rank-step, WKE/WKC per column) from a run's 'out' file.
Usage: python3 instrument_wb_ka_report.py <RUNDIR> [LON LAT] [KDT_FROM KDT_TO]
Prints: global per-step series of fix A's cloud-base heating (sum and max |dTA| over all convecting columns, signed sum,
borrowing counts, max |SAMF dT| at kb and k=1, max T(1)); totals over the run; the steps with the largest max|dTA|; and,
for the column nearest LON LAT (default 73.262 -12.792), its entry state (WKE) and convection record (WKC) per step."""
import re
import sys
from collections import defaultdict

rd = sys.argv[1]
lon0, lat0 = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (73.262, -12.792)
k0, k1 = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 10**9)
lab = re.compile(r"^\s*\d+:\s*")
A = defaultdict(lambda: [0.0] * 12)
E, C = {}, {}
for line in open(f"{rd}/out", errors="replace"):
    line = lab.sub("", line)
    if line.startswith("WKA "):
        f = line.split()
        kdt, v = int(f[1]), [float(x) for x in f[2:14]]
        a = A[kdt]
        for j in (0, 1, 3, 4, 5, 6, 8):  # sums
            a[j] += v[j]
        for j in (2, 7, 9, 10, 11):      # maxima
            a[j] = max(a[j], v[j])
    elif line.startswith(("WKE ", "WKC ")):
        f = line.split()
        key = (int(f[1]), round(float(f[2]), 3), round(float(f[3]), 3))
        (E if f[0] == "WKE" else C)[key] = f[4:]
if not A:
    sys.exit("no WKA lines")
steps = sorted(A)
print(f"WKA: steps {steps[0]}..{steps[-1]} ({len(steps)}; each line is step kdt, summed over ranks)")
hdr = "  kdt  ncnv   sum|dTA|K  max|dTA|K   sumdTA_K  kb=1 qkb<0 borrow max|dTj|K sum|dqA|kg/m2 max|dTkb| max|dT1|  maxT1"
fmt = "{:5d} {:5.0f} {:11.4e} {:10.4e} {:10.3e} {:5.0f} {:5.0f} {:6.0f} {:9.3e} {:12.4e} {:9.3e} {:8.3e} {:7.2f}"
sel = [k for k in steps if k0 <= k <= k1]
print(hdr)
for k in (sel if len(sel) <= 400 else sel[:: max(1, len(sel) // 200)]):
    print(fmt.format(k, *A[k]))
tot = [sum(A[k][j] for k in steps) for j in range(12)]
print(f"TOTAL over {len(steps)} steps: convecting column-steps {tot[0]:.0f}, sum|dTA| {tot[1]:.4e} K, "
      f"mean|dTA| {tot[1] / max(tot[0], 1):.4e} K, signed mean {tot[3] / max(tot[0], 1):.4e} K, "
      f"max|dTA| {max(A[k][2] for k in steps):.4e} K, kb=1 fraction {tot[4] / max(tot[0], 1):.3f}, "
      f"q(kb)<0 column-steps {tot[5]:.0f}, borrowing column-steps {tot[6]:.0f}, max|dTj| {max(A[k][7] for k in steps):.3e} K, "
      f"sum|dqA| {tot[8]:.4e} kg/m2 (unweighted), max|SAMF dT1| {max(A[k][10] for k in steps):.3e} K, "
      f"max T1 {max(A[k][11] for k in steps):.2f} K")
print("largest max|dTA| steps:", ", ".join(f"{k}:{A[k][2]:.3g}K" for k in sorted(steps, key=lambda k: -A[k][2])[:10]))

pts = {(lo, la) for (_, lo, la) in list(E) + list(C)}
if pts:
    lo, la = min(pts, key=lambda p: (p[0] - lon0) ** 2 + (p[1] - lat0) ** 2)
    print(f"\ncolumn {lo:.3f} {la:.3f} (nearest to {lon0} {lat0}); dqA in kg/kg, dTA/dTkb/dT1 in K per step")
    print("  kdt  T1in     q1in      T2in     q2in    | kb jm kt  phkp    qo(kb)    tem1      q1kb      q1kb1     xmb"
          "       dqA        dTA       dTkb      dT1       qkbpost   T1out    dTj")
    ks = sorted({k for (k, a, b) in list(E) + list(C) if (a, b) == (lo, la) and k0 <= k <= k1})
    for k in ks:
        e = E.get((k, lo, la))
        c = C.get((k, lo, la))
        s = f"{k:5d} " + (f"{float(e[0]):7.2f} {float(e[1]):9.3e} {float(e[2]):7.2f} {float(e[3]):9.3e}" if e else " " * 35)
        if c:
            kb, jm, kt, ph = c[0], c[1], c[2], c[3]
            v = [float(x) for x in c[4:]]  # eta qo tem1 qkb qkb1 xmb dqA dTA dTkb dT1 qpost T1 q1 dTj rn
            s += (f" | {kb:>2} {jm:>2} {kt:>2} {float(ph):6.3f} {v[1]:9.3e} {v[2]:9.3e} {v[3]:9.3e} {v[4]:9.3e} {v[5]:9.3e}"
                  f" {v[6]:10.3e} {v[7]:9.3e} {v[8]:9.3e} {v[9]:9.3e} {v[10]:10.3e} {v[11]:7.2f} {v[13]:9.2e}")
        print(s)
hot = sorted({(k, a, b) for (k, a, b), e in E.items() if float(e[0]) > 320.})
if hot:
    print(f"\nWKE T(1) > 320 K: {len(hot)} column-steps; first: {hot[:5]}")
