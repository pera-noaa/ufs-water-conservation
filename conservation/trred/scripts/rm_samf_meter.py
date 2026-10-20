#!/usr/bin/env python3
"""32-bit SAMF build: drop the diagnostic tm_cfl_deep call (real(8) dummies) from samfdeepcnv.f; TM slot meters stay.
usage: rm_samf_meter.py <tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF/samfdeepcnv.f"
s = f.read_text()
for old in ("      use tm_meter, only : tm_cfl_deep\n",
            "      call tm_cfl_deep(im,km,cnvflg,kb,jmin,ktcon,eta,etad,edto,\n     &     xmb,del,dt2)\n"):
    if s.count(old) != 1:
        sys.exit(f"ABORT {s.count(old)} {old!r}")
    s = s.replace(old, "")
assert "tm_" not in s, [l for l in s.splitlines() if "tm_" in l][:3]
f.write_text(s)
print("RM_OK")
