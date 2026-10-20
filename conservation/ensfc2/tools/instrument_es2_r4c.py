#!/usr/bin/env python3
"""Round 4c: replace the ESR print of instrument_es2_r4b.py by a full per-column breakdown (only |r| > 100 J m-2):
'ESR kdt i r dH B bnd(4) evc(2) pst(3) E19 d65 d66 EP LW2 AIR seg(10)'. Usage: instrument_es2_r4c.py <tree>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
s = p.read_text()
a = s[s.index("       if (abs(d2) > 1.d0) write(*,'(a,i6,i5,20es12.4)') 'ESR ', eskdt, i, d2, esb(41,i), &\n"):]
a = a[:a.index("    endif\n")]
b = ("       if (abs(d2) > 1.d2) write(*,'(a,i6,i5,33es11.3)') 'ESR ', eskdt, i, d2, esb(6,i), esb(6,i)-d1, &\n"
     "            esb(141:144,i), esb(151:152,i), esb(153:154,i), esb(47,i), esb(41,i), esb(155:156,i), &\n"
     "            esb(191:192,i), esb(195,i), esb(110:119,i)\n")
if s.count(a) != 1:
    sys.exit("ABORT")
p.write_text(s.replace(a, b))
print("instrumented", p.name)
