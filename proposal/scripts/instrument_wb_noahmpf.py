#!/usr/bin/env python3
"""Split Noah-MP's steady water-balance residual by where it arises in noahmp_sflx (diagnostic builds only; apply after
instrument_wb_noahmpx.py). Usage: python3 instrument_wb_noahmpf.py <ufs_model.fd>
Soil points, steps > 1. Storage S = canliq + canice + sneqv + wa + sum(smc*dz)*1000 (+ ponding at water() entry):
  A = S at water() entry - S at the start (energy, phenology, the sice rebuild; no fluxes are applied there)
  B = S after water() - S at water() entry - (prcp - ecan - etran - edir - runsrf - runsub)*dt
  D = sum(max(sh2o - smc, 0)*dz)*1000 at water() entry (liquid above total: created when smc is rebuilt as sh2o + sice)
WBF | for categories layered snow, thin snow, frozen soil, unfrozen (4 x): sum A, sum B, sum D   (12 values, mm)
and the first 4 columns per rank with |A| or |B| > 1e-5 mm:
WBY isnow vegtyp | A B D | ponding at entry, sneqv at start and end, prcp, ecan, etran, edir, runsrf, runsub (mm)"""
import sys
from pathlib import Path

lsm = Path(sys.argv[1]) / "FV3/ccpp/physics/physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
mpt = Path(sys.argv[1]) / "FV3/ccpp/physics/physics/MP/Thompson/mp_thompson.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


STOR = "canliq + canice + sneqv + wa + 1000.d0*sum(smc(1:nsoil)*dzsnso(1:nsoil))"
# after the wbe declaration (with or without instrument_wb_noahmph.py's wbk)
s0 = edits.get(lsm) or lsm.read_text()
i = s0.index("  real(kind=8), public, save :: wbe(16) = 0.d0")
j = s0.index("\n", i) + 1
edits[lsm] = s0[:j] + ("  real(kind=8), public, save :: wbf(12) = 0.d0\n"
                       "  real(kind=8), save :: wbf_se, wbf_sx, wbf_d, wbf_pe\n"
                       "  integer, save :: wby_n = 0, wbf_c\n") + s0[j:]
sub(lsm, "    sice(:) = max(0.0, smc(:) - sh2o(:))   \n",
    "    sice(:) = max(0.0, smc(:) - sh2o(:))   \n"
    f"    wbf_se = {STOR} + ponding\n"
    "    wbf_pe = ponding\n"
    "    wbf_d = 1000.d0*sum(max(sh2o(1:nsoil) - smc(1:nsoil), 0.)*dzsnso(1:nsoil))\n")
sub(lsm, "     call error (parameters,swdown ,fsa    ,fsr    ,fira   ,fsh    ,fcev   , & !in\n",
    f"     wbf_sx = {STOR}\n"
    "     call error (parameters,swdown ,fsa    ,fsr    ,fira   ,fsh    ,fcev   , & !in\n")
sub(lsm, "     if (ist == 1 .and. itime > 1) then\n       if (isnow < 0) then\n",
    "     if (ist == 1 .and. itime > 1) then\n"
    "       if (isnow < 0) then\n         wbf_c = 0\n"
    "       else if (sneqv > 0. .or. wbx_s0 > 0.d0) then\n         wbf_c = 3\n"
    "       else if (maxval(sice(1:nsoil)) > 0.) then\n         wbf_c = 6\n"
    "       else\n         wbf_c = 9\n       endif\n"
    "       wbf(wbf_c+1) = wbf(wbf_c+1) + (wbf_se - (wbx_c0 + wbx_s0 + wbx_a0 + wbx_m0))\n"
    "       wbf(wbf_c+2) = wbf(wbf_c+2) + (wbf_sx - wbf_se - (prcp - ecan - etran - edir - runsrf - runsub)*dt)\n"
    "       wbf(wbf_c+3) = wbf(wbf_c+3) + wbf_d\n"
    "       if ((abs(wbf_se - (wbx_c0 + wbx_s0 + wbx_a0 + wbx_m0)) > 1.e-5 .or. &\n"
    "            abs(wbf_sx - wbf_se - (prcp - ecan - etran - edir - runsrf - runsub)*dt) > 1.e-5) .and. wby_n < 4) then\n"
    "         wby_n = wby_n + 1\n"
    "         write(*,'(a,2i4,12es12.4)') 'WBY ', isnow, vegtyp, wbf_se - (wbx_c0 + wbx_s0 + wbx_a0 + wbx_m0), &\n"
    "           wbf_sx - wbf_se - (prcp - ecan - etran - edir - runsrf - runsub)*dt, wbf_d, wbf_pe, wbx_s0, sneqv, &\n"
    "           prcp*dt, ecan*dt, etran*dt, edir*dt, runsrf*dt, runsub*dt\n"
    "       endif\n"
    "       if (isnow < 0) then\n")
sub(mpt, "         use module_sf_noahmplsm, only: wbe", "         use module_sf_noahmplsm, only: wbf\n         use module_sf_noahmplsm, only: wbe")
sub(mpt, "         write(*,'(a,16es24.15)') 'WBE ', wbe\n",
    "         write(*,'(a,16es24.15)') 'WBE ', wbe\n         write(*,'(a,12es24.15)') 'WBF ', wbf\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBF").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.name}")
