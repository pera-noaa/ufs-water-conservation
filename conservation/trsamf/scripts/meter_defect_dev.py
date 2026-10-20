#!/usr/bin/env python3
"""METER (develop SAMF only, i.e. without SA1; apply after instrument_tm.py + post_tx.py): column tracer-mass change
from the cloud-base TVD inconsistency, per tracer, into tm_x (Pa m2 per step, summed over ranks):
 deep    tm_x(4(n-1)+c): c=1 kb face, limiter phi=0 (local extremum); c=2 kb face, phi>0; c=3/4 same at jmin
         tm_x(40+n): gross cloud-base gradient term xmb*dt*g*area*eta(kb)*|ctr(kb)-ctr(kb+1)|/2
 shallow tm_x(60+2(n-1)+c): c=1 kb face phi=0, c=2 phi>0
Defect per column = xmb*dt*[eta(kb)*(ctro(kb)-tem1(kb)) + edto*etad(jmin)*(ctro(jmin)-tem1(jmin))] (deep),
counted only for columns whose tracer update is kept (deep: cnvflg and rn>0). Usage: meter_defect_dev.py <tree>"""
import sys
from pathlib import Path
d = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF"
def edit(f, reps):
    for a, b in reps:
        for ln in b.splitlines():
            if len(ln) > 72 and not ln.lstrip().startswith('!'):
                sys.exit(f"ABORT line > 72 cols: {ln!r}")
    s = f.read_text()
    for a, b in reps:
        if s.count(a) != 1:
            sys.exit(f"ABORT {f.name}: {s.count(a)} matches {a[:70]!r}")
        s = s.replace(a, b)
    f.write_text(s)
ACC_D = """      do i = 1, im
        if (cnvflg(i) .and. real(rn(i), kind=conv_wp) > 0.0_conv_wp)
     &  then
          tem = xmb(i) * dt2 * real(grav, kind=conv_wp)
     &        * real(garea(i), kind=conv_wp)
          do n = 1, min(ntr,10)
            do tm_c = 1, 4
              tm_x(4*(n-1)+tm_c) = tm_x(4*(n-1)+tm_c)
     &                           + tem*tm_dd(i,n,tm_c)
            enddo
            tm_x(40+n) = tm_x(40+n) + tem*tm_gk(i,n)
          enddo
        endif
      enddo
"""
edit(d / "samfdeepcnv.f", [
    ("      use tm_meter, only : tm_cfl_deep\n", "      use tm_meter, only : tm_cfl_deep\n      use tm_meter, only : tm_x\n"),
    ("      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n",
     "      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n"
     "      real(kind=conv_wp) tm_dd(im,ntr,4), tm_gk(im,ntr)\n      integer tm_c\n"),
    ("      do n=1,ntr\n!\n        flxtvd = 0.0_conv_wp\n",
     "      tm_dd = 0.0_conv_wp\n      tm_gk = 0.0_conv_wp\n      do n=1,ntr\n!\n        flxtvd = 0.0_conv_wp\n"),
    ("              if(k == jmin(i)) then\n                dp = 1000.0_conv_wp * del(i,k+1)\n"
     "                dellae(i,k+1,n) = dellae(i,k+1,n) - edto(i)\n",
     "              tm_c = 2\n"
     "              if (tem /= 0.0_conv_wp .and. phkp == 0.0_conv_wp)\n"
     "     &          tm_c = 1\n"
     "              if(k == kb(i)) then\n"
     "                tm_dd(i,n,tm_c) = eta(i,k) * (ctro(i,k,n) - tem1)\n"
     "                tm_gk(i,n) = eta(i,k) * 0.5_conv_wp *\n"
     "     &                       abs(ctr(i,k,n) - ctr(i,k+1,n))\n"
     "              endif\n"
     "              if(k == jmin(i)) tm_dd(i,n,2+tm_c) = edto(i) *\n"
     "     &            etad(i,k) * (ctro(i,k,n) - tem1)\n"
     "              if(k == jmin(i)) then\n                dp = 1000.0_conv_wp * del(i,k+1)\n"
     "                dellae(i,k+1,n) = dellae(i,k+1,n) - edto(i)\n"),
    ("      dqtr  = real((new_qtr - real(qtr, kind=conv_wp)) / real(delt,\n",
     ACC_D + "      dqtr  = real((new_qtr - real(qtr, kind=conv_wp)) / real(delt,\n")])
ACC_S = """      do i = 1, im
        if (cnvflg(i)) then
          tem = xmb(i) * dt2 * real(grav, kind=conv_wp)
     &        * real(garea(i), kind=conv_wp)
          do n = 1, min(ntr,10)
            do tm_c = 1, 2
              tm_x(60+2*(n-1)+tm_c) = tm_x(60+2*(n-1)+tm_c)
     &                              + tem*tm_ds(i,n,tm_c)
            enddo
          enddo
        endif
      enddo
"""
edit(d / "samfshalcnv.f", [
    ("      implicit none\n", "      use tm_meter, only : tm_x\n      implicit none\n"),
    ("      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n",
     "      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n"
     "      real(kind=conv_wp) tm_ds(im,ntr,2)\n      integer tm_c\n"),
    ("      do n=1,ntr\n!\n        flxtvd = 0.0_conv_wp\n",
     "      tm_ds = 0.0_conv_wp\n      do n=1,ntr\n!\n        flxtvd = 0.0_conv_wp\n"),
    ("                flxtvd(i,k) = eta(i,k) * tem1\n",
     "                flxtvd(i,k) = eta(i,k) * tem1\n"
     "                if(k == kb(i)) then\n"
     "                  tm_c = 2\n"
     "                  if (phkp == 0.0_conv_wp) tm_c = 1\n"
     "                  tm_ds(i,n,tm_c) = eta(i,k)*(ctro(i,k,n) - tem1)\n"
     "                endif\n"),
    ("      dqtr  = real((new_qtr - real(qtr, kind=conv_wp)) / real(delt,\n",
     ACC_S + "      dqtr  = real((new_qtr - real(qtr, kind=conv_wp)) / real(delt,\n")])
print("defect meter", d)
