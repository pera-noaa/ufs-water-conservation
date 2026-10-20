#!/usr/bin/env python3
"""TEST HOOK (not a fix): env F3_NORTNP=1 skips SAMF's column positivity borrowing (rtnp) for chemical tracers in
samfdeepcnv/samfshalcnv, so negative chemical-tracer values reach the wet-deposition borrowing branch (both its
if- and else-cases). Default (unset) leaves the code path unchanged.
usage: testhook_f3_nortnp.py <ufs-weather-model tree>"""
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
    print("hooked", path)


DECL = "      real(kind=kind_phys), dimension(:), intent(in) :: fscav\n"
ENV = "        if (do_aerosols) do_aerosols = (ntr >= itc + ntc - 3)\n"
HOOKDECL = DECL + "      logical f3nortnp\n      character(len=8) f3env\n"
HOOKENV = (ENV + "        call get_environment_variable('F3_NORTNP', f3env)\n"
           "        f3nortnp = (f3env == '1')\n")
COND = "(rtnp(i) < 0.0_conv_wp .and. .not.\n     &         (f3nortnp .and. itc > 0 .and. n >= itc-2))"
rep(SAMF / "samfdeepcnv.f", [
    (DECL, HOOKDECL), (ENV, HOOKENV),
    ("              if(rtnp(i) < 0.0_conv_wp) then\n                if(tsump(i) > abs(tsumn(i))) then\n"
     "                  if(ctr(i,k,n)<0.0_conv_wp) ctr(i,k,n)=0.0_conv_wp\n",
     f"              if{COND} then\n                if(tsump(i) > abs(tsumn(i))) then\n"
     "                  if(ctr(i,k,n)<0.0_conv_wp) ctr(i,k,n)=0.0_conv_wp\n")])
rep(SAMF / "samfshalcnv.f", [
    (DECL, HOOKDECL), (ENV, HOOKENV),
    ("              if(rtnp(i) < 0.0_conv_wp) then\n                if(tsump(i) > abs(tsumn(i))) then\n"
     "                  if(ctr(i,k,n) < 0.0_conv_wp) ctr(i,k,n) = 0.0_conv_wp\n",
     f"              if{COND} then\n                if(tsump(i) > abs(tsumn(i))) then\n"
     "                  if(ctr(i,k,n) < 0.0_conv_wp) ctr(i,k,n) = 0.0_conv_wp\n")])
