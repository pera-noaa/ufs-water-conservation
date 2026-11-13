#!/usr/bin/env python3
"""Round 4e: snow-bottom outflow content (internal snow -> soil, or runoff at the bottom snow layer T):
esl(72) = c_w qsnbot dt (tsbot - tfrz) -> esb(196) -> esg(326). The round-3 booking counted the infiltrated part as a soil
import; the correct column booking is only the runoff part as an export, i.e. booked - esl(72).
Usage: instrument_es2_r4e.py <tree>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = p.read_text()
a = "                                                    + qsnbot*(tsbot - stc(1)))\n"
if s.count(a) != 1:
    sys.exit("ABORT")
p.write_text(s.replace(a, a + "       esl(72) = esl(72) + cwk*qsnbot*dt*(tsbot - tfrz)\n"))
print("instrumented", p.name)
