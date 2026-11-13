#!/usr/bin/env python3
"""mynnred: sum the per-rank moisture_check fill statistics. usage: agg_stats.py <rundir> <steps per day>"""
import sys, glob
import numpy as np
CP, XLV, XLF = 1004.6, 2.5e6, 3.3358e5
I = np.zeros(6); S = np.zeros(8)
fs = sorted(glob.glob(f"{sys.argv[1]}/mynnred_stats_*.txt")); spd = float(sys.argv[2])
for f in fs:
    v = open(f).read().split("\n")[1].split()
    I += np.array(v[:6], float); S += np.array(v[6:], float)
n = I[0]
print(f"ranks {len(fs)}  column-steps {n:.0f}  with fill c/i/s/v: {I[1]/n:.3f}/{I[2]/n:.3f}/{I[3]/n:.3f}/{I[4]/n:.3f}  input negatives {I[5]/n:.3g}")
print("column-mean fill (kg m-2 day-1): c %.4e i %.4e s %.4e v %.4e" % tuple(S[:4] / n * spd))
print("thl heat from moisture_check cp*sum(m*exner*dthl) %.4e W m-2 ; L*fill %.4e W m-2 ; ratio %.12f" %
      (CP * S[4] / n * spd / 86400, (XLV * S[0] + (XLV + XLF) * (S[1] + S[2])) / n * spd / 86400,
       CP * S[4] / (XLV * S[0] + (XLV + XLF) * (S[1] + S[2]))))
print("mean column rho*dz %.2f kg m-2, mean sum(MYNN delp)/g %.2f kg m-2" % (S[6] / n, S[7] / n / 9.80665))
