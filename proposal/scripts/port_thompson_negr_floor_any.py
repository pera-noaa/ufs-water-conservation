#!/usr/bin/env python3
"""M5's floor start (as fix_thompson_negr_rain_floor.py --graupel) for any CCPP Thompson copy, matched by pattern so the
copy's own indentation is kept: before the semi-Lagrangian rain and graupel substep loops, layers at or below R1 are reset
to (q1d + qten*DT)*rho, so the R1 floor is not sedimented as mass. Aborts unless each anchor matches once.
Usage: python3 port_thompson_negr_floor_any.py <module_mp_thompson.F90>"""
import re
import sys
from pathlib import Path

m = Path(sys.argv[1])
s = m.read_text()
if "floored layers carry" in s:
    sys.exit("ABORT: already has the floor start")
for sp, q in (("rr", "qr"), ("rg", "qg")):
    pat = re.compile(rf"\n( *)dtcfl = dt/niter\n(\n?)( *)do n = 1, niter\n( *){sp}_tmp\(:\) = {sp}\(:\)\n")
    found = pat.findall(s)
    if len(found) != 1:
        sys.exit(f"ABORT {sp}: expected 1 match, found {len(found)}")
    word = "rain" if sp == "rr" else "graupel"

    def rep(mm):
        i = mm.group(1)
        return (f"\n{i}dtcfl = dt/niter\n{i}! floored layers carry their actual {word}, so the R1 floor is not sedimented as mass\n"
                f"{i}do k = kts, kte\n{i}   if ({sp}(k) .le. R1) {sp}(k) = ({q}1d(k) + {q}ten(k)*DT)*rho(k)\n{i}enddo\n"
                f"{mm.group(2)}{mm.group(3)}do n = 1, niter\n{mm.group(4)}{sp}_tmp(:) = {sp}(:)\n")
    s = pat.sub(rep, s)
m.write_text(s)
print(f"patched {m} (floor start: rain and graupel)")
