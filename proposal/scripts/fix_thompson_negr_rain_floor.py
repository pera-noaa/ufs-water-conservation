#!/usr/bin/env python3
"""Thompson sedi_semi rain: layers held at the R1 floor enter semi_lagrange_sedim with their actual rain, so M5 cannot transport the floor as mass.
Usage: python3 fix_thompson_negr_rain_floor.py <ufs-weather-model | module_mp_thompson.F90> [--graupel]
Before the rain substep loop, rr(k) <= R1 is reset to (qr1d + qrten*DT)*rho, the state qrten is accounted against.
--graupel applies the same to rg before the graupel substep loop (same mechanism, not separately tested).
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

p = Path(sys.argv[1])
m = p if p.suffix == ".F90" else p / "UFSATM/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90"
s = m.read_text()


def sub(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {m.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    s = s.replace(old, new)


loop = ("            dtcfl = dt/niter\n"
        "            do n = 1, niter\n"
        "               rr_tmp(:) = rr(:)\n")
sub(loop,
    "            dtcfl = dt/niter\n"
    "            ! floored layers carry their actual rain, so the R1 floor is not sedimented as mass\n"
    "            do k = kts, kte\n"
    "               if (rr(k) .le. R1) rr(k) = (qr1d(k) + qrten(k)*DT)*rho(k)\n"
    "            enddo\n"
    "            do n = 1, niter\n"
    "               rr_tmp(:) = rr(:)\n")
if "--graupel" in sys.argv[2:]:
    gloop = ("            dtcfl = dt/niter\n\n"
             "            do n = 1, niter\n"
             "               rg_tmp(:) = rg(:)\n")
    sub(gloop,
        "            dtcfl = dt/niter\n"
        "            ! floored layers carry their actual graupel, so the R1 floor is not sedimented as mass\n"
        "            do k = kts, kte\n"
        "               if (rg(k) .le. R1) rg(k) = (qg1d(k) + qgten(k)*DT)*rho(k)\n"
        "            enddo\n\n"
        "            do n = 1, niter\n"
        "               rg_tmp(:) = rg(:)\n")
m.with_suffix(m.suffix + ".preNEGR").write_text(m.read_text())
m.write_text(s)
print(f"patched {m}")
