#!/usr/bin/env python3
"""29-Oct runs: 24-h sums (kg/m2, area mean) of the EMS PBL-segment water residual (seg 4, emg(9)) and the
in-scheme uc_exit residual (UCM slot 17 = sum del/g*rtg_water - rho_a*evap, per second) times dt.
Usage: old_uc.py DT RUNDIR [...]"""
import re
import sys

dt = float(sys.argv[1])
for rd in sys.argv[2:]:
    ems4, ucm17, ucm20, ucm18, area = 0.0, 0.0, 0.0, 0.0, None
    for ln in open(f"{rd}/out", errors="replace"):
        ln = re.sub(r"^\s*\d+:\s*", "", ln)
        p = ln.split()
        if not p:
            continue
        if p[0] == "EMS" and p[2] == "4":
            ems4 += float(p[3 + 8])
        elif p[0] == "EMF":
            area = float(p[-1])
        elif p[0] == "UCM":
            v = [float(x) for x in p[2:]]
            ucm17 += v[16]; ucm18 += v[17]; ucm20 += v[19]
    print(f"{rd}: area {area:.6e}  EMS PBL water res {ems4/area:+.6e}  uc_exit res*dt {ucm17*dt/area:+.6e}  "
          f"gross*dt {ucm18*dt/area:+.6e}  rho*evap*dt {ucm20*dt/area:+.6e}")
