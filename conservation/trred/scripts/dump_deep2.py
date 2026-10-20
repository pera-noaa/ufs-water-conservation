#!/usr/bin/env python3
"""dump_deep.py fix-up: qcko/qcdo are recomputed by the closure's test state after dellaq; dump copies saved right
after dellaq is final instead. usage: dump_deep2.py <tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF/samfdeepcnv.f"
s = f.read_text()
def sub(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT {s.count(old)} {old[:70]!r}")
    return s.replace(old, new)
s = sub(s, "      real(kind=conv_wp) dmp_qoi(im,km)\n",
        "      real(kind=conv_wp) dmp_qoi(im,km), dmp_qcko(im,km),\n     &  dmp_qcdo(im,km)\n")
old = ("             dellaq(i,k) = dellaq(i,k) + (flxtvd(i,k) - flxtvd(i,k-1))\n"
       "     &                    * real(grav, kind=conv_wp)/dp\n          endif\n        enddo\n      enddo\n")
s = sub(s, old, old + "      dmp_qcko = qcko\n      dmp_qcdo = qcdo\n")
s = sub(s, "     &  xlamue,xlamud,zi,del,delp,c0t,q,q1,dmp_qoi,dellaq,qcko,\n     &  qrcko,qcdo,qrcdo,",
        "     &  xlamue,xlamud,zi,del,delp,c0t,q,q1,dmp_qoi,dellaq,dmp_qcko,\n     &  qrcko,dmp_qcdo,qrcdo,")
f.write_text(s)
print("DUMP2_OK")
