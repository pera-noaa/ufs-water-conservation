#!/usr/bin/env python3
"""Surface energy meters, sixth layer (after instrument_es_sfc5.py and apply_round2.py): esnb 140, esng 260.
  Noah-MP groundwater: aquifer exchange enthalpy at the bottom layer's T esl(41), subsurface-runoff enthalpy esl(42),
    water moved between layers by the watmin fix esl(43)  -> esb(121:123) -> esg(221:223) (soil)
  land SW: A = radiation-time albedo x the radiation's band fluxes esb(131), B = this step's Noah-MP albedo x band
    fluxes esb(132) -> esg(233), esg(234), Noah-MP fsa esg(235) (soil, x txl); land-only cells: A esg(231),
    atmosphere net SW esg(232), fsa esg(236)
  convective precipitation the host calls snow: hfus x mass esg(207), mass esg(208) (GFS_MP_generic_post)
Usage: instrument_es_sfc6.py <ufs-weather-model>"""
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
emc = root / "Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
mpp = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    if s.count(old) != 1:
        sys.exit(f"ABORT {path.name}: {s.count(old)} matches: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def post(path, a, t):
    sub(path, a, a + t)


sub(emc, "esnb = 120, esng = 220\n", "esnb = 140, esng = 260\n")
sub(emc, "    esg(161:169) = esg(161:169) + a*emf(4:12, jj)\n",
    "    if (esb(4, i) == 1.d0) esg(221:230) = esg(221:230) + wl*esb(121:130, i)\n"
    "    if (esb(133, i) > 0.d0) then\n"
    "       esg(233) = esg(233) + wl*esb(131, i)\n"
    "       esg(234) = esg(234) + wl*esb(132, i)\n"
    "       esg(235) = esg(235) + wl*esb(8, i)\n"
    "       if (esb(1, i) > 0.999d0) then\n"
    "          esg(231) = esg(231) + a*esb(131, i)\n"
    "          esg(232) = esg(232) + a*emf(6, jj)\n"
    "          esg(236) = esg(236) + a*esb(8, i)\n"
    "       endif\n"
    "    endif\n"
    "    esg(161:169) = esg(161:169) + a*emf(4:12, jj)\n")
sub(lsm, "  real(kind=8), public, save :: esl(40) = 0.d0\n", "  real(kind=8), public, save :: esl(50) = 0.d0\n")
post(lsm, "         mliq(nsoil) = mliq(nsoil) - qin * dt        ! [mm]\n",
     "         esl(41) = esl(41) - cwat/1000.*qin*dt*(stc(nsoil)-tfrz)\n")
post(lsm, "         mliq(nsoil) = mliq(nsoil) + max(0.,(wa - 5000.))\n",
     "         esl(41) = esl(41) + cwat/1000.*max(0.,(wa - 5000.))*(stc(nsoil)-tfrz)\n")
post(lsm, "         mliq(iz) = mliq(iz) - qdis*dt*hk(iz)*dzmm(iz)/wtsub\n",
     "         esl(42) = esl(42) - cwat/1000.*qdis*dt*hk(iz)*dzmm(iz)/wtsub*(stc(iz)-tfrz)\n")
t = edits.get(lsm) or lsm.read_text()
k = t.index("  subroutine groundwater(")
a = "          mliq(iz+1) = mliq(iz+1) - xs\n"
j = t.index(a, k)
edits[lsm] = t[:j] + a + "          esl(43) = esl(43) + cwat/1000.*xs*(stc(iz)-stc(iz+1))\n" + t[j + len(a):]
post(lsm, "        wa       = wa - xs\n", "        esl(41) = esl(41) + cwat/1000.*xs*(stc(nsoil)-tfrz)\n")
post(drv, "        esb(110:119,i) = esl(31:40)\n", "        esb(121:130,i) = esl(41:50)\n")
post(drv, "      esb(57,i) = 1000.d0*tprcp(i)*srflag(i)\n",
     "      if (swa >= 0.d0 .and. vegetation_category /= isice_table) then\n"
     "        esb(131,i) = swa*delt\n"
     "        esb(132,i) = (adjvisbmd(i)*(1.-albedo_direct(1)) + adjvisdfd(i)*(1.-albedo_diffuse(1)) &\n"
     "                    + adjnirbmd(i)*(1.-albedo_direct(2)) + adjnirdfd(i)*(1.-albedo_diffuse(2)))*delt\n"
     "        esb(133,i) = 1.d0\n"
     "      endif\n")
post(mpp, "      use calpreciptype_mod, only: calpreciptype\n", "      use energy_meter_common, only: esg\n")
post(mpp, "                                             / (con_cp*(prsi(i,1)-prsi(i,2)))\n            endif\n",
     "            if (present(garea) .and. csnow > zero) then\n"
     "              esg(207) = esg(207) + garea(i)*con_hfus*rhowater*csnow\n"
     "              esg(208) = esg(208) + garea(i)*rhowater*csnow\n"
     "            endif\n")
for p, s in edits.items():
    p.write_text(s)
    print("instrumented", p.name)
