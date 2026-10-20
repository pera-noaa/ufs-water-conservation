#!/usr/bin/env python3
"""T1: TEMPO's semi-Lagrangian sedimentation tests qpi(k) > 0 where Juang and Hong (2010), and Thompson's copy, test
qpi(k) < 0, so it keeps exactly the parabolas with a negative edge; their negative interpolated values are then clipped
by max(xr, limit), which creates water (3e-4 of the precipitation per call in a unit test of the routine; the fixed
test conserves to rounding). Since TEMPO v3.0.0 (e41f020). Usage: python3 fix_tempo_semi_lagrangian.py <TEMPO checkout>"""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "src/module_mp_tempo_main.F90"
s = f.read_text()
old = "        if(qpi(k) > 0._wp .or. qmi(k) < 0._wp) then\n"
if s.count(old) != 1:
    sys.exit(f"ABORT T1: expected 1 match, found {s.count(old)}")
s = s.replace(old, "        ! fall back to piecewise constant if either edge value is negative\n"
                   "        if(qpi(k) < 0._wp .or. qmi(k) < 0._wp) then\n")
f.write_text(s)
print(f"patched {f.relative_to(f.parents[1])}: T1")
