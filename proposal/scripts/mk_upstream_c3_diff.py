#!/usr/bin/env python3
"""Write fix C3 (sediment in the entry-density frame) into an upstream ccpp-physics module_mp_thompson.F90 in place.
Usage: python3 mk_upstream_c3_diff.py <module_mp_thompson.F90>   (ufs/dev layout: real(wp), RoverRv)"""
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()


def sub(s, old, new, count=1, start=0):
    n = s.count(old, start)
    if n != count:
        sys.exit(f"ABORT: expected {count}, found {n}: {old.strip()[:70]!r}")
    return s[:start] + s[start:].replace(old, new)


s = sub(s, "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR\n",
        "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n")
A = ("         qv(k) = max(1.E-10, qv1d(k) + DT*qvten(k))\n"
     "         rho(k) = RoverRv*pres(k) / (R*temp(k)*(qv(k)+RoverRv))\n"
     "         rhof(k) = SQRT(RHO_NOT/rho(k))\n")
s = sub(s, A, "         qv(k) = max(1.E-10, qv1d(k) + DT*qvten(k))\n"
              "         ! rho stays the entry density so sedimentation conserves the host's column mass\n"
              "         rhon = RoverRv*pres(k) / (R*temp(k)*(qv(k)+RoverRv))\n"
              "         rhof(k) = SQRT(RHO_NOT/rhon)\n")
i = s.index("         rhon = RoverRv")
s = s[:i] + s[i:].replace("         vsc2(k) = SQRT(rho(k)/visco(k))\n", "         vsc2(k) = SQRT(rhon/visco(k))\n", 1)
s = sub(s, "            temp(k) = t1d(k) + DT*tten(k)\n"
           "            rho(k) = RoverRv*pres(k) / (R*temp(k)*(qv(k)+RoverRv))\n",
        "            temp(k) = t1d(k) + DT*tten(k)\n", count=2)
f.write_text(s)
print(f"patched {f}")
