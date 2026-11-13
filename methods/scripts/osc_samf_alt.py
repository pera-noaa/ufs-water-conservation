#!/usr/bin/env python3
"""Per-step SAMF deep and shallow changes to T and qv in layers 1-3 for one column, from instrument_wb_osc_meter.py OSM lines.
Usage: python3 osc_samf_alt.py <RUNDIR> LON LAT KDT_FROM KDT_TO
Deep = call 17 - call 16 (after GFS_DCNV_generic_post minus after get_phi_fv3), shallow = call 18 - call 17; kcnv after deep;
PBL (incl. surface fluxes) dT1 = dtdt*dtp after satmedmfvdifq minus before, for comparison."""
import re
import sys
from collections import defaultdict

rd, lon0, lat0, k0, k1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
lab = re.compile(r"^\s*\d+:\s*")
M = defaultdict(dict)
for line in open(f"{rd}/out", errors="replace"):
    if "OSM " not in line:
        continue
    f = lab.sub("", line).split()
    if f[0] == "OSM" and abs(float(f[3]) - lon0) < 0.01 and abs(float(f[4]) - lat0) < 0.01 and k0 <= int(f[1]) <= k1:
        M[int(f[1])][int(f[2])] = [float(x) for x in f[5:67]]
print(" kdt kcnv | deep dT1     dT2     dT3    dq1       dq2       dq3     | shal dT1    dT2     dT3    dq1       dq2       dq3     | PBL dT1")
for k in sorted(M):
    m = M[k]
    if not all(n in m for n in (11, 12, 16, 17, 18)):
        continue
    d = lambda a, b, i: m[b][i] - m[a][i]
    dp = [d(16, 17, 7 * j) for j in range(3)] + [d(16, 17, 7 * j + 1) for j in range(3)]
    sh = [d(17, 18, 7 * j) for j in range(3)] + [d(17, 18, 7 * j + 1) for j in range(3)]
    print(f"{k:4d} {m[17][61]:4.0f} | " + " ".join(f"{x:7.3f}" for x in dp[:3]) + " " + " ".join(f"{x:9.2e}" for x in dp[3:])
          + " | " + " ".join(f"{x:7.3f}" for x in sh[:3]) + " " + " ".join(f"{x:9.2e}" for x in sh[3:])
          + f" | {m[12][21] - m[11][21]:7.3f}")
