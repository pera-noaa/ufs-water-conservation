#!/usr/bin/env python3
"""Round 4d: the ESR breakdown at full precision (es24.16), |r| > 100 J m-2. Usage: instrument_es2_r4d.py <tree>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
s = p.read_text()
a = "write(*,'(a,i6,i5,33es11.3)') 'ESR '"
if s.count(a) != 1:
    sys.exit("ABORT")
p.write_text(s.replace(a, "write(*,'(a,i6,i5,33es24.16)') 'ESR '"))
print("instrumented", p.name)
