#!/usr/bin/env python3
"""spr.py <out> [--cells N] : sea-spray meter summary from 'SPR kdt lon lat ws10 lam t1 q1 tskin qss1 ex used hs' lines.
- per run: cell-steps with lam > 1, > 2, > 5; max lam; spray latent flux used vs explicit (sums over lam > 2 cell-steps)
- 2dt oscillation: per cell, the lowest-layer T1 series over consecutive steps; a flip is d1*d2 < 0 with both |d| > 0.5 K.
  Cells with >= 3 flips in a row are 'oscillating'; prints their count, the largest |dT1| and the N worst cells."""
import sys
from collections import defaultdict

fn = sys.argv[1]
ncell = int(sys.argv[sys.argv.index("--cells") + 1]) if "--cells" in sys.argv else 5
rec = {}
for line in open(fn, errors="replace"):
    i = line.find("SPR ")
    if i < 0:
        continue
    w = line[i:].split()
    if len(w) < 13:
        continue
    try:
        k = int(w[1]); lon, lat = float(w[2]), float(w[3]); v = [float(x) for x in w[4:13]]
    except ValueError:
        continue
    rec[(k, round(lon, 2), round(lat, 2))] = v   # last surface iteration wins
n1 = n2 = n5 = 0; lmax = (0.0, None); ex2 = us2 = 0.0
cells = defaultdict(dict)
for (k, lon, lat), v in rec.items():
    ws, lam, t1, q1, ts, qs, ex, us, hs = v
    n1 += 1; n2 += lam > 2; n5 += lam > 5
    if lam > lmax[0]:
        lmax = (lam, (k, lon, lat, ws))
    if lam > 2:
        ex2 += ex; us2 += us
    cells[(lon, lat)][k] = (t1, lam, ws, ts, ex, us)
print(f"{fn}: cell-steps lam>1 {n1}  >2 {n2}  >5 {n5}; max lam {lmax[0]:.2f} at kdt,lon,lat,ws10 {lmax[1]}")
if n2 and ex2 != 0:
    print(f"  lam>2 cell-steps: spray latent (before alps) explicit sum {ex2:.4e}, used sum {us2:.4e}, used/explicit {us2/ex2:.3f}")
osc = []
for c, s in cells.items():
    ks = sorted(s)
    best = run = 0; amp = 0.0
    for a, b, d in zip(ks, ks[1:], ks[2:]):
        if b != a + 1 or d != b + 1:
            run = 0; continue
        d1 = s[b][0] - s[a][0]; d2 = s[d][0] - s[b][0]
        if d1 * d2 < 0 and min(abs(d1), abs(d2)) > 0.5:
            run += 1; best = max(best, run); amp = max(amp, abs(d1), abs(d2))
        else:
            run = 0
    if best >= 3:
        osc.append((amp, best, c, max(x[1] for x in s.values()), max(x[2] for x in s.values())))
osc.sort(reverse=True)
print(f"  oscillating cells (>=3 consecutive 2dt flips of T1 > 0.5 K): {len(osc)}; largest |dT1| per step "
      f"{osc[0][0] if osc else 0:.2f} K")
for amp, best, c, lam, ws in osc[:ncell]:
    print(f"    cell {c}: max |dT1| {amp:.2f} K, flips in a row {best}, max lam {lam:.1f}, max ws10 {ws:.1f}")
