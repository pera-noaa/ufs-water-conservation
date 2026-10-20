#!/usr/bin/env python3
"""M2: Thompson counts every sedimentation flux out of the lowest layer as surface precipitation (rain, ice, snow,
graupel), instead of only when the water left in that layer exceeds R1*1000 (v1 snapshot and ufs/dev layouts).
Usage: python3 apply_thompson_m2_patch.py <dir containing physics/MP>
The flux sed_x(kts) always leaves the column; below the threshold it was deleted, a one-signed loss found by the
double-precision physics meter (instrument_wb_ep.py) after all other fixes. Exactly four sites must match."""
import re
import sys
from pathlib import Path

f90 = Path(sys.argv[1]) / "physics/MP/Thompson/module_mp_thompson.F90"
s = f90.read_text()
# v1: one-line continuation with R1*1000.; ufs/dev: block if with R1*rr_min
v1 = re.compile(r"\n( *)if \(r([risg])\(kts\)\.gt\.R1\*1000\.\) &\n *(ppt\w+ = ppt\w+ \+ sed_\2\(kts\)\*DT\*onstep\(\d\))\n")
up = re.compile(r"\n( *)if \(r([risg])\(kts\)\.gt\.R1\*rr_min\) then\n *(ppt\w+ = ppt\w+ \+ sed_\2\(kts\)\*DT\*onstep\(\d\))\n *endif *\n")
n1, n2 = len(v1.findall(s)), len(up.findall(s))
if (n1, n2) not in ((4, 0), (0, 4)):
    sys.exit(f"ABORT: expected 4 threshold sites in one form, found {n1} (v1) and {n2} (ufs/dev)")
n = 4
rep = lambda m: f"\n{m.group(1)}! all of the flux out of the lowest layer reaches the surface\n{m.group(1)}{m.group(3)}\n"
s = (v1 if n1 else up).sub(rep, s)
f90.write_text(s)
print(f"patched {f90.name} (M2: {n} surface precipitation thresholds removed)")
