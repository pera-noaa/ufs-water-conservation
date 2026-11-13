#!/usr/bin/env python3
"""Trace Noah-MP's own water-balance residual (soil points) by surface state and size (diagnostic builds only; apply
after instrument_wb_land.py). Usage: python3 instrument_wb_noahmpx.py <ufs_model.fd>
In noahmp_sflx, after Noah-MP's error check, errwat (mm per step) is accumulated by state, unweighted over columns:
  WBE | 1/2 count/sum layered snow (isnow < 0) | 3/4 thin snow (isnow = 0, sneqv > 0 at start or end) | 5/6 no snow,
      frozen soil | 7/8 no snow, unfrozen | 9-12 counts and 13-16 sums for |errwat| in [0,1e-6), [1e-6,1e-4),
      [1e-4,1e-2), [1e-2,inf)
printed at finalize; and the first 4 columns per rank with |errwat| > 1e-4 mm are printed with every storage term:
  WBX isnow vegtyp max(sice) zwt | errwat d_canopy d_snow d_aquifer d_soil | P ecan etran edir runsrf runsub (mm)"""
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


sub(lsm, "  real(kind=8), public, save :: wbl_errwat = 0.d0, wbl_prcp = 0.d0\n",
    "  real(kind=8), public, save :: wbl_errwat = 0.d0, wbl_prcp = 0.d0\n"
    "  real(kind=8), public, save :: wbe(16) = 0.d0\n"
    "  real(kind=8), save :: wbx_c0, wbx_s0, wbx_a0, wbx_m0\n"
    "  integer, save :: wbx_n = 0\n")
sub(lsm, "     if(ist == 1) then\n     beg_wb = canliq + canice + sneqv + wa\n",
    "     wbx_c0 = canliq + canice\n     wbx_s0 = sneqv\n     wbx_a0 = wa\n"
    "     wbx_m0 = 1000.d0*sum(smc(1:nsoil)*dzsnso(1:nsoil))\n"
    "     if(ist == 1) then\n     beg_wb = canliq + canice + sneqv + wa\n")
CALL_END = ("                 pahv   ,pahg   ,pahb   ,canhs,errmsg, errflg)   !in ( except errwat [out] and errmsg, errflg [inout] )\n"
            "#else\n"
            "                 pahv   ,pahg   ,pahb,   canhs )   !in ( except errwat, which is out )\n"
            "#endif\n")
sub(lsm, CALL_END, CALL_END +
    "     if (ist == 1) then\n"
    "       if (isnow < 0) then\n"
    "         wbe(1) = wbe(1) + 1.d0; wbe(2) = wbe(2) + errwat\n"
    "       else if (sneqv > 0. .or. wbx_s0 > 0.d0) then\n"
    "         wbe(3) = wbe(3) + 1.d0; wbe(4) = wbe(4) + errwat\n"
    "       else if (maxval(sice(1:nsoil)) > 0.) then\n"
    "         wbe(5) = wbe(5) + 1.d0; wbe(6) = wbe(6) + errwat\n"
    "       else\n"
    "         wbe(7) = wbe(7) + 1.d0; wbe(8) = wbe(8) + errwat\n"
    "       endif\n"
    "       if (abs(errwat) < 1.e-6) then\n"
    "         wbe(9) = wbe(9) + 1.d0; wbe(13) = wbe(13) + errwat\n"
    "       else if (abs(errwat) < 1.e-4) then\n"
    "         wbe(10) = wbe(10) + 1.d0; wbe(14) = wbe(14) + errwat\n"
    "       else if (abs(errwat) < 1.e-2) then\n"
    "         wbe(11) = wbe(11) + 1.d0; wbe(15) = wbe(15) + errwat\n"
    "       else\n"
    "         wbe(12) = wbe(12) + 1.d0; wbe(16) = wbe(16) + errwat\n"
    "       endif\n"
    "       if (abs(errwat) > 1.e-4 .and. wbx_n < 4) then\n"
    "         wbx_n = wbx_n + 1\n"
    "         write(*,'(a,2i4,2es11.3,11es12.4)') 'WBX ', isnow, vegtyp, maxval(sice(1:nsoil)), zwt, errwat, &\n"
    "           canliq+canice-wbx_c0, sneqv-wbx_s0, wa-wbx_a0, 1000.d0*sum(smc(1:nsoil)*dzsnso(1:nsoil))-wbx_m0, &\n"
    "           prcp*dt, ecan*dt, etran*dt, edir*dt, runsrf*dt, runsub*dt\n"
    "       endif\n"
    "     endif\n")
sub(mpt, "         use noahmpdrv, only: wbl, wbl_kdt, wbn\n",
    "         use noahmpdrv, only: wbl, wbl_kdt, wbn\n         use module_sf_noahmplsm, only: wbe\n")
sub(mpt, "         write(*,'(a,i7,26es24.15)') 'WBN ', wbl_kdt, wbn\n",
    "         write(*,'(a,i7,26es24.15)') 'WBN ', wbl_kdt, wbn\n"
    "         write(*,'(a,16es24.15)') 'WBE ', wbe\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBE").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
