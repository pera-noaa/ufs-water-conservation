#!/usr/bin/env python3
"""WRF Thompson microphysics water meter (diagnostic builds only). Around the CALL mp_gt_driver in
phys/module_microphysics_driver.F, per call and tile, sums over the tile's columns:
  host:     sum_k q_tot*rho*dz8w        (WRF's dry-air mass per layer, rho = 1/alt)
  thompson: sum_k q_tot*rho_t*dz8w      (rho_t = 0.622 p/(R T (qv+0.622)) at entry, Thompson's own density)
and prints  WBMP itimestep  ncol  host(after-before)+P  thompson(after-before)+P  P   (kg/m2 summed over columns; P from
RAINNCV, all grid-scale precipitation of the step). Usage: python3 instrument_wrf_mp_meter.py <WRF checkout>"""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "phys/module_microphysics_driver.F"
s = f.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


a = s.index("        CASE (THOMPSON)")
call = s.index("             CALL mp_gt_driver(", a)
# end of the call statement: first line after it that does not end with '&' and is not a preprocessor line
e = call
while True:
    nl = s.index("\n", e)
    line = s[e:nl]
    e = nl + 1
    if line.lstrip().startswith("#"):
        continue
    if not line.split("!")[0].rstrip().endswith("&"):  # ignore trailing comments
        break
before = (
    "             ! WBMP meter (diagnostic)\n"
    "             wbm_s0h = 0.d0; wbm_s0t = 0.d0\n"
    "             if (allocated(wbm_rt)) deallocate(wbm_rt)\n"
    "             allocate(wbm_rt(its:ite,kts:kte,jts:jte))\n"
    "             do j = jts, jte\n             do k = kts, kte\n             do i = its, ite\n"
    "               wbm_rt(i,k,j) = 0.622*p(i,k,j) &\n"
    "                 /(287.04*th(i,k,j)*pi_phy(i,k,j)*(max(1.e-10,qv_curr(i,k,j))+0.622))\n"
    "               wbm_q = qv_curr(i,k,j) + qc_curr(i,k,j) + qr_curr(i,k,j) &\n"
    "                     + qi_curr(i,k,j) + qs_curr(i,k,j) + qg_curr(i,k,j)\n"
    "               wbm_s0h = wbm_s0h + wbm_q*rho(i,k,j)*dz8w(i,k,j)\n"
    "               wbm_s0t = wbm_s0t + wbm_q*wbm_rt(i,k,j)*dz8w(i,k,j)\n"
    "             enddo\n             enddo\n             enddo\n")
after = (
    "             wbm_s1h = 0.d0; wbm_s1t = 0.d0; wbm_p = 0.d0\n"
    "             do j = jts, jte\n             do k = kts, kte\n             do i = its, ite\n"
    "               wbm_q = qv_curr(i,k,j) + qc_curr(i,k,j) + qr_curr(i,k,j) &\n"
    "                     + qi_curr(i,k,j) + qs_curr(i,k,j) + qg_curr(i,k,j)\n"
    "               wbm_s1h = wbm_s1h + wbm_q*rho(i,k,j)*dz8w(i,k,j)\n"
    "               wbm_s1t = wbm_s1t + wbm_q*wbm_rt(i,k,j)*dz8w(i,k,j)\n"
    "             enddo\n             enddo\n             enddo\n"
    "             do j = jts, jte\n             do i = its, ite\n               wbm_p = wbm_p + RAINNCV(i,j)\n"
    "             enddo\n             enddo\n"
    "             write(*,'(a,i8,i8,3es22.13)') 'WBMP ', itimestep, (ite-its+1)*(jte-jts+1), &\n"
    "               wbm_s1h - wbm_s0h + wbm_p, wbm_s1t - wbm_s0t + wbm_p, wbm_p\n")
s = s[:call] + before + s[call:e] + after + s[e:]
s = one(s, "  real, private, parameter :: NI_MIN = 1.E-6\nCONTAINS\n",
        "  real, private, parameter :: NI_MIN = 1.E-6\n  REAL(8), SAVE :: wbm_s0h, wbm_s0t, wbm_s1h, wbm_s1t, wbm_p, wbm_q\n"
        "  REAL, ALLOCATABLE, SAVE :: wbm_rt(:,:,:)\nCONTAINS\n", "module variables")
f.write_text(s)
print(f"instrumented {f.name}: WBMP meter")
