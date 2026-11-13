#!/usr/bin/env python3
"""METER (apply after meter_defect_dev.py): shallow SAMF column tracer change, into tm_x:
 tm_x(80+n): sum over columns of sum_k dellae*xmb*dt2*1000*del*g... i.e. before positivity rescaling (Pa m2)
 tm_x(90+n): sum over columns of sum_k (new_qtr - qtr)*delp*garea at the end (Pa m2)
Usage: meter_shal_diag.py <tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF/samfshalcnv.f"
s = f.read_text()
reps = [("               ctr(i,k,n) = ctr(i,k,n) + dellae(i,k,n) * xmb(i) * dt2\n",
         "               ctr(i,k,n) = ctr(i,k,n) + dellae(i,k,n) * xmb(i) * dt2\n"
         "               if (n <= 10) tm_x(80+n) = tm_x(80+n) + dellae(i,k,n)\n"
         "     &           * xmb(i) * dt2 * real(delp(i,k), kind=conv_wp)\n"
         "     &           * real(garea(i), kind=conv_wp)\n"),
        ("      dqtr  = real((new_qtr - real(qtr, kind=conv_wp)) / real(delt,\n",
         "      do n = 1, min(ntr,10)\n"
         "        do k = 1, km\n"
         "          do i = 1, im\n"
         "            tm_x(90+n) = tm_x(90+n) + (new_qtr(i,k,n+2)\n"
         "     &        - real(qtr(i,k,n+2), kind=conv_wp))\n"
         "     &        * real(delp(i,k), kind=conv_wp)\n"
         "     &        * real(garea(i), kind=conv_wp)\n"
         "          enddo\n"
         "        enddo\n"
         "      enddo\n"
         "      dqtr  = real((new_qtr - real(qtr, kind=conv_wp)) / real(delt,\n")]
for a, b in reps:
    if s.count(a) != 1:
        sys.exit(f"ABORT {s.count(a)} {a[:60]!r}")
    s = s.replace(a, b)
f.write_text(s)
print("shallow diag meter", f)
