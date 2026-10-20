#!/usr/bin/env python3
"""TEST ONLY (T1 causal test): replace SAMF deep's single explicit tracer update by Courant-limited sub-steps
(tm_meter.tm_samf_substep). Apply after instrument_tm.py. Usage: testhook_samf_substep.py <tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF/samfdeepcnv.f"
s = f.read_text()
a = "      use tm_meter, only : tm_cfl_deep\n"
b = "      if (.not.hwrf_samfdeep) then\n       indx = ntk - 2\n       do n = 1, ntr\n"
for x in (a, b):
    if s.count(x) != 1:
        sys.exit(f"ABORT {s.count(x)} {x!r}")
s = s.replace(a, "      use tm_meter, only : tm_cfl_deep, tm_samf_substep\n")
s = s.replace(b, "      if (.not.hwrf_samfdeep) call tm_samf_substep(im,km,ntr,cnvflg,\n"
                 "     &   kb,jmin,ktcon,kmax,eta,etad,edto,ecko,ercko,ecdo,ctr,del,\n"
                 "     &   xmb,dt2,dellae,real(grav,kind=conv_wp))\n" + b)
f.write_text(s)
print("SAMF substep test hook", f)
