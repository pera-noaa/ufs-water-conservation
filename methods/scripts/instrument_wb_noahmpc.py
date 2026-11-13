#!/usr/bin/env python3
"""Meter canwater's canopy truncation (canliq or canice <= 1e-6 mm set to 0) against Noah-MP's errwat (diagnostic
builds only; apply after instrument_wb_noahmpx.py, instrument_wb_noahmph.py and instrument_wb_noahmpf.py).
Usage: python3 instrument_wb_noahmpc.py <ufs_model.fd>
Soil points, steps > 1, by the WBE/WBF state groups g = layered snow, thin snow, frozen soil, unfrozen (4 x):
  WBC | count of column-steps with a truncation, sum of canliq deleted, sum of canice deleted, sum of
        (errwat + deleted)   (16 values, mm, unweighted over columns)
  WBD | counts and sums of (errwat + deleted) for |.| in [0,1e-10), [1e-10,1e-8), [1e-8,1e-6), [1e-6,inf)
and the first 4 columns per rank with |errwat + deleted| > 1e-9 mm:
  WBZ isnow vegtyp max(sice) zwt | errwat del_liq del_ice d_canopy d_snow d_aquifer d_soil | P ecan etran edir
      runsrf runsub (mm per step)"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
mpt = root / "MP/Thompson/mp_thompson.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


DEL = "(errwat + wbc_l + wbc_i)"
sub(lsm, "  real(kind=8), public, save :: wbe(16) = 0.d0, wbk(6) = 0.d0\n",
    "  real(kind=8), public, save :: wbe(16) = 0.d0, wbk(6) = 0.d0\n"
    "  real(kind=8), public, save :: wbc(16) = 0.d0, wbd(8) = 0.d0\n"
    "  real(kind=8), save :: wbc_l = 0.d0, wbc_i = 0.d0\n"
    "  integer, save :: wbz_n = 0, wbc_g\n")
sub(lsm, "     wbx_c0 = canliq + canice\n", "     wbc_l = 0.d0; wbc_i = 0.d0\n     wbx_c0 = canliq + canice\n")
sub(lsm, "       if(canliq <= 1.e-06) canliq = 0.0\n",
    "       if(canliq <= 1.e-06) wbc_l = wbc_l + canliq\n       if(canliq <= 1.e-06) canliq = 0.0\n")
sub(lsm, "      if(canice.le.1.e-6) canice = 0.\n",
    "      if(canice.le.1.e-6) wbc_i = wbc_i + canice\n      if(canice.le.1.e-6) canice = 0.\n")
WBE1 = "       if (isnow < 0) then\n         wbe(1) = wbe(1) + 1.d0; wbe(2) = wbe(2) + errwat\n"
sub(lsm, WBE1,
    "       wbc_g = 4*(wbf_c/3)\n"
    "       if (wbc_l + wbc_i > 0.d0) wbc(wbc_g+1) = wbc(wbc_g+1) + 1.d0\n"
    "       wbc(wbc_g+2) = wbc(wbc_g+2) + wbc_l\n"
    "       wbc(wbc_g+3) = wbc(wbc_g+3) + wbc_i\n"
    f"       wbc(wbc_g+4) = wbc(wbc_g+4) + {DEL}\n"
    f"       if (abs{DEL} < 1.d-10) then\n"
    f"         wbd(1) = wbd(1) + 1.d0; wbd(5) = wbd(5) + {DEL}\n"
    f"       else if (abs{DEL} < 1.d-8) then\n"
    f"         wbd(2) = wbd(2) + 1.d0; wbd(6) = wbd(6) + {DEL}\n"
    f"       else if (abs{DEL} < 1.d-6) then\n"
    f"         wbd(3) = wbd(3) + 1.d0; wbd(7) = wbd(7) + {DEL}\n"
    "       else\n"
    f"         wbd(4) = wbd(4) + 1.d0; wbd(8) = wbd(8) + {DEL}\n"
    "       endif\n"
    f"       if (abs{DEL} > 1.d-9 .and. wbz_n < 4) then\n"
    "         wbz_n = wbz_n + 1\n"
    "         write(*,'(a,2i4,2es11.3,13es12.4)') 'WBZ ', isnow, vegtyp, maxval(sice(1:nsoil)), zwt, errwat, &\n"
    "           wbc_l, wbc_i, canliq+canice-wbx_c0, sneqv-wbx_s0, wa-wbx_a0, &\n"
    "           1000.d0*sum(smc(1:nsoil)*dzsnso(1:nsoil))-wbx_m0, &\n"
    "           prcp*dt, ecan*dt, etran*dt, edir*dt, runsrf*dt, runsub*dt\n"
    "       endif\n" + WBE1)
sub(mpt, "         use module_sf_noahmplsm, only: wbe, wbk\n",
    "         use module_sf_noahmplsm, only: wbe, wbk\n         use module_sf_noahmplsm, only: wbc, wbd\n")
sub(mpt, "         write(*,'(a,6es24.15)') 'WBK ', wbk\n",
    "         write(*,'(a,6es24.15)') 'WBK ', wbk\n"
    "         write(*,'(a,16es24.15)') 'WBC ', wbc\n         write(*,'(a,8es24.15)') 'WBD ', wbd\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBC").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
