#!/usr/bin/env python3
"""F3 meter (instrumentation only; needs tm_meter.F90 with tm_x and post_tx.py's TX print).
Per call of samfdeepcnv (slots 1-8) / samfshalcnv (slots 11-18), chemical tracers n = 1, 2:
  b+n   : sum area*dM/g, dM = sum_k (new_qtr - qtr)*delp   (atmospheric change by the scheme)
  b+2+n : sum area*sum_k wet_dep/g                       (booked deposition, final)
  b+5   : sum over columns and n of area*|dM + D|/g      (column residual, absolute)
  b+6   : borrowing events with wet_dep < deficit (else-branch); b+7: events with wet_dep >= deficit
  b+8   : sum area*wet_dep/g at stake in else-branch events
Works on the unfixed and the fixed scheme (anchors common to both).
usage: meter_f3.py <ufs-weather-model tree>"""
import sys
from pathlib import Path

SAMF = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF"


def rep(path, pairs):
    s = path.read_text()
    for a, b in pairs:
        n = s.count(a)
        if n != 1:
            sys.exit(f"ABORT {path.name}: {n} x {a[:70]!r}")
        s = s.replace(a, b)
    path.write_text(s)
    print("metered", path)


def end_block(b):
    return (f"!  F3 METER\n"
            f"      if (do_aerosols) then\n"
            f"        do n = 1, min(ntc,2)\n"
            f"          kk = n + itc - 1\n"
            f"          do i = 1, im\n"
            f"            tm_a = 0.d0\n"
            f"            tm_b = 0.d0\n"
            f"            do k = 1, km\n"
            f"              tm_a = tm_a + dble(new_qtr(i,k,kk)\n"
            f"     &             - real(qtr(i,k,kk), kind=conv_wp)) * delp(i,k)\n"
            f"              tm_b = tm_b + dble(wet_dep(i,k,n))\n"
            f"            enddo\n"
            f"            tm_x({b}+n) = tm_x({b}+n) + garea(i)*tm_a/grav\n"
            f"            tm_x({b}+2+n) = tm_x({b}+2+n) + garea(i)*tm_b/grav\n"
            f"            tm_x({b}+5) = tm_x({b}+5)\n"
            f"     &                + garea(i)*abs(tm_a+tm_b)/grav\n"
            f"          enddo\n"
            f"        enddo\n"
            f"      endif\n")


def borrow(b):
    return ("                    tem = -new_qtr(i,k,kk) * dp\n"
            "!  F3 METER\n"
            "                    if (wet_dep(i,k,n) >= tem) then\n"
            f"                      tm_x({b+7}) = tm_x({b+7}) + 1.d0\n"
            "                    else\n"
            f"                      tm_x({b+6}) = tm_x({b+6}) + 1.d0\n"
            f"                      tm_x({b+8}) = tm_x({b+8})\n"
            "     &                  + garea(i)*dble(wet_dep(i,k,n))/grav\n"
            "                    endif\n")


DECL = "      real(kind=kind_phys), dimension(:), intent(in) :: fscav\n"
TEN = "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n"
USE = "      use funcphys , only : fpvs\n"
for f, b in (("samfdeepcnv.f", 0), ("samfshalcnv.f", 10)):
    rep(SAMF / f, [(USE, USE + "      use tm_meter, only : tm_x\n"),
                   (DECL, DECL + "      real(8) tm_a, tm_b\n"),
                   ("                    tem = -new_qtr(i,k,kk) * dp\n", borrow(b)),
                   (TEN, end_block(b) + TEN)])
