#!/usr/bin/env python3
"""Land meter table (instrument_land14.py 'EMLAND kdt v(8)' lines). Usage: land14_table.py <out>
Noah-MP soil columns, all metered steps: precipitation-phase agreement with the host (frozen received prcp*fpice vs host
srflag*P) and Noah-MP's own water balance errwat (end - begin storage - (P - ET - R)*dt, mm per column-step)."""
import sys
v, w = {}, {}
for line in open(sys.argv[1], errors="replace"):
    if "EMLAND " in line:
        p = line[line.index("EMLAND "):].split()
        v[int(p[1])] = [float(x) for x in p[2:10]]
    if "EMLAND2 " in line:
        p = line[line.index("EMLAND2 "):].split()
        w[int(p[1])] = [float(x) for x in p[2:8]]
s = [sum(x[i] for x in v.values()) for i in range(8)]
print(f"# {sys.argv[1]}: {len(v)} steps")
print(f"soil column-steps with precipitation           {s[0]:.0f}  (with convective precipitation {s[4]:.0f})")
print(f"phase: columns where frozen received != host   {s[3]:.0f}  ({100 * (1 - s[3] / s[0]) if s[0] else 0:.4f} % agree)")
print(f"phase: sum|frozen received - host frozen| / sum host frozen = {s[1] / s[2] if s[2] else 0:.3e}")
print(f"water: soil column-steps {s[7]:.0f}; errwat sum {s[5]:+.3e} mm, sum|errwat| {s[6]:.3e} mm, "
      f"mean|errwat| {s[6] / s[7] if s[7] else 0:.3e} mm per column-step")
if w:
    t = [sum(x[i] for x in w.values()) for i in range(5)]
    mx = max(x[5] for x in w.values())
    print(f"phase: columns differing > 1e-6 P {t[0]:.0f}, > 1e-3 P {t[1]:.0f}; max |frozen diff|/P {mx:.3e}")
    print(f"precip: sum|Noah-MP prcp - host P| / sum host P = {t[2] / t[3] if t[3] else 0:.3e}; columns differing > 1e-9 P {t[4]:.0f}")
