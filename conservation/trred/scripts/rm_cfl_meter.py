#!/usr/bin/env python3
"""32-bit SAMF build of the fxf (env-switched) tree: drop only the tm_cfl_deep call (real(8) dummies); tm_x counters stay.
usage: rm_cfl_meter.py <tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF/samfdeepcnv.f"
s = f.read_text()
for old in ("      use tm_meter, only : tm_cfl_deep\n",
            "      call tm_cfl_deep(im,km,cnvflg,kb,jmin,ktcon,eta,etad,edto,\n     &     xmb,del,dt2)\n"):
    if s.count(old) != 1:
        sys.exit(f"ABORT {s.count(old)} {old!r}")
    s = s.replace(old, "")
f.write_text(s)
print("RM_OK")
