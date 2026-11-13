#!/usr/bin/env python3
"""Surface energy meters, round 3 (ensfc2). Apply after instrument_es_sfc{,2}, es_static, es_icefix, instrument_es_sfc{3,4,5},
apply_sfc_fixes, apply_bugfix, apply_options (and D3A). Replaces round-2 layers 6 and 7 (which anchored on the round-2
switch code). esnb 120 -> 220, esng 220 -> 420.

Soil columns (x txl, esb(4) == 1), J m-2 per call:
  esl(41:43) aquifer exchange / subsurface runoff / watmin moves at layer T (as layer 6)  -> esb(121:123) -> esg(221:223)
  esl(44)    pore air displaced by the groundwater step, cpair*(-dtheta)*dz*(T-tfrz)        -> esg(224)
  esl(51)    soilwater boundary water at layer T  sum c_w bnd_k (T_k - tfrz)                -> esg(261)
  esl(52)    groundwater boundary water at layer T                                          -> esg(262)
  esl(53)    pore air displaced, soilwater + groundwater                                    -> esg(263)
  esl(54)    infiltration at its source T (rain tg, melt/drip tfrz) minus at layer-1 T     -> esg(264)
  esl(55)    internal (inter-layer) term, stock bookkeeping sum c_w I_k (T_k - tfrz)        -> esg(265)
  esl(56)    AD1 heat (computed), esl(57) AD1 heat applied, esl(58) bottom imbalance (kg)   -> esg(266:268)
  esl(59)    pore air displaced, soilwater part                                             -> esg(269)
  esl(60)    EV1 frame-F evaporation enthalpy mismatch x dt                                 -> esg(270)
  driver: esb(161) convective precip x dt, esb(162) of it T1-snow/host-rain, esb(163) T1-rain/host-snow,
          esb(164) 1 if convective precip, esb(165) 1 if the rules disagree                 -> esg(281:285)
  SW (as layer 6): A radiation-time albedo esb(131), B current albedo esb(132), flag esb(133) -> esg(231:236)
Frame-F statistics (as layer 7)  esb(134:140) -> esg(237:243).
Cells (x area, W m-2 not J): composites_post LW1/EV1 block: applied heating esb(171), LW part esb(172), land/ice/water
  booked net-up LW x frac esb(173:175), radiation-time net-up esb(176), EV1 part esb(177)    -> esg(301:307)
MP_generic_post: hfus x host-frozen convective mass esg(207), mass esg(208), PH1 heating applied (J) esg(209).
Usage: instrument_es2_r3.py <ufs-weather-model>"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
itl = root / "Interstitials/UFS_SCM_NEPTUNE"
emc = itl / "energy_meter_common.F90"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
nst = root / "SFC_Layer/UFS/sfc_nst.f90"
mpp = itl / "GFS_MP_generic_post.F90"
mppm = itl / "GFS_MP_generic_post.meta"
cpo = itl / "GFS_surface_composites_post.F90"
edits = {}


def get(p):
    return edits.get(p) or p.read_text()


def sub(path, old, new, after=None):
    s = get(path)
    if after is not None:
        if s.count(after) != 1:
            sys.exit(f"ABORT {path.name}: anchor count {s.count(after)}: {after.strip()[:70]!r}")
        i = s.index(after)
        j = s.find(old, i)
        if j < 0:
            sys.exit(f"ABORT {path.name}: {old.strip()[:70]!r} not after anchor")
        edits[path] = s[:j] + new + s[j + len(old):]
        return
    if s.count(old) != 1:
        sys.exit(f"ABORT {path.name}: {s.count(old)} matches: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def pre(path, a, t, **kw):
    sub(path, a, t + a, **kw)


def post(path, a, t, **kw):
    sub(path, a, a + t, **kw)


# ---------------------------------------------------------------- storage and accumulation
sub(emc, "esnb = 120, esng = 220\n", "esnb = 220, esng = 420\n")
pre(emc, "    esg(161:169) = esg(161:169) + a*emf(4:12, jj)\n",
    "    if (esb(4, i) == 1.d0) then\n"
    "       esg(221:230) = esg(221:230) + wl*esb(121:130, i)\n"
    "       esg(261:280) = esg(261:280) + wl*esb(141:160, i)\n"
    "       esg(281:290) = esg(281:290) + wl*esb(161:170, i)\n"
    "    endif\n"
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
    "    esg(237:239) = esg(237:239) + wl*esb(134:136, i)\n"
    "    esg(240:241) = esg(240:241) + wi*esb(137:138, i)\n"
    "    esg(242:243) = esg(242:243) + wo*esb(139:140, i)\n"
    "    esg(301:310) = esg(301:310) + a*esb(171:180, i)\n")

# ---------------------------------------------------------------- Noah-MP soil
sub(lsm, "  real(kind=8), public, save :: esl(40) = 0.d0\n", "  real(kind=8), public, save :: esl(80) = 0.d0\n")
GW = "  subroutine groundwater(parameters,nsnow  ,nsoil  ,dt     ,sice   ,zsoil  , & !in\n"
post(lsm, "         mliq(nsoil) = mliq(nsoil) - qin * dt        ! [mm]\n",
     "         esl(41) = esl(41) - cwat/1000.*qin*dt*(stc(nsoil)-tfrz)\n", after=GW)
post(lsm, "         mliq(nsoil) = mliq(nsoil) + max(0.,(wa - 5000.))\n",
     "         esl(41) = esl(41) + cwat/1000.*max(0.,(wa - 5000.))*(stc(nsoil)-tfrz)\n", after=GW)
post(lsm, "         mliq(iz) = mliq(iz) - qdis*dt*hk(iz)*dzmm(iz)/wtsub\n",
     "         esl(42) = esl(42) - cwat/1000.*qdis*dt*hk(iz)*dzmm(iz)/wtsub*(stc(iz)-tfrz)\n", after=GW)
post(lsm, "          mliq(iz+1) = mliq(iz+1) - xs\n",
     "          esl(43) = esl(43) + cwat/1000.*xs*(stc(iz)-stc(iz+1))\n", after=GW)
post(lsm, "        wa       = wa - xs\n", "        esl(41) = esl(41) + cwat/1000.*xs*(stc(nsoil)-tfrz)\n", after=GW)
# water(): soilwater / groundwater split
post(lsm, "  real (kind=kind_phys)                                           :: rsat0, qthru, qcold, qinfl, qinfh, tsbot\n",
     "  real (kind=kind_phys)                                           :: es_sh1(nsoil)\n")
post(lsm, "                                                    + qsnbot*(tsbot - stc(1)))\n",
     "       do iz = 1, nsoil\n"
     "          esl(51) = esl(51) + cwk*bnd(iz)*(stc(iz)-tfrz)\n"
     "          esl(59) = esl(59) - cpair*(sh2o(iz)-sh2o0(iz))*dzsnso(iz)*(stc(iz)-tfrz)\n"
     "          es_sh1(iz) = sh2o(iz)\n"
     "       enddo\n"
     "       esl(54) = esl(54) + qinfh\n")
post(lsm, "       dflx = dflx - ((sh2o(nsoil) - sh2o0(nsoil))*dzsnso(nsoil)*1000. - bnd(nsoil))  ! 0 if all is booked\n",
     "       do iz = 1, nsoil\n"
     "          esl(52) = esl(52) + cwk*bnd(iz)*(stc(iz)-tfrz)\n"
     "          esl(53) = esl(53) - cpair*(sh2o(iz)-sh2o0(iz))*dzsnso(iz)*(stc(iz)-tfrz)\n"
     "          esl(44) = esl(44) - cpair*(sh2o(iz)-es_sh1(iz))*dzsnso(iz)*(stc(iz)-tfrz)\n"
     "          esl(55) = esl(55) + cwk*((sh2o(iz)-sh2o0(iz))*dzsnso(iz)*1000. - bnd(iz))*(stc(iz)-tfrz)\n"
     "          esl(56) = esl(56) + qadv(iz)\n"
     "          if (opt_adv) esl(57) = esl(57) + qadv(iz)\n"
     "       enddo\n"
     "       esl(52) = esl(52) - esl(51)\n"
     "       esl(58) = esl(58) + dflx\n")
post(lsm, "     if (present(hevap)) hevap = hev\n", "     esl(60) = hev*dt\n")

# ---------------------------------------------------------------- driver
post(drv, "        esb(110:119,i) = esl(31:40)\n", "        esb(121:130,i) = esl(41:50)\n        esb(141:160,i) = esl(51:70)\n")
post(drv, "              > 0.5*precip_convective) fpcvh = 1.\n        endif\n",
     "        ! meter: host (srflag) vs sfctmp < tfrz decision for convective precipitation\n"
     "        if (precip_convective > 0.) then\n"
     "          esb(161,i) = precip_convective*delt\n"
     "          esb(164,i) = 1.d0\n"
     "          if (srflag(i)*precipitation_forcing - (precip_snow + precip_graupel + precip_hail) &\n"
     "              > 0.5*precip_convective) then\n"
     "            if (temperature_forcing >= 273.16d0) then\n"
     "              esb(163,i) = precip_convective*delt\n"
     "              esb(165,i) = 1.d0\n"
     "            endif\n"
     "          else\n"
     "            if (temperature_forcing < 273.16d0) then\n"
     "              esb(162,i) = precip_convective*delt\n"
     "              esb(165,i) = 1.d0\n"
     "            endif\n"
     "          endif\n"
     "        endif\n")
post(drv, "      esb(57,i) = 1000.d0*tprcp(i)*srflag(i)\n",
     "      if (present(albdvis_rad) .and. vegetation_category /= isice_table) then\n"
     "        if (albdvis_rad(i) >= 0.) then\n"
     "          esb(131,i) = (adjvisbmd(i)*(1.-albdvis_rad(i)) + adjvisdfd(i)*(1.-albivis_rad(i)) &\n"
     "                      + adjnirbmd(i)*(1.-albdnir_rad(i)) + adjnirdfd(i)*(1.-albinir_rad(i)))*delt\n"
     "          esb(132,i) = (adjvisbmd(i)*(1.-albedo_direct(1)) + adjvisdfd(i)*(1.-albedo_diffuse(1)) &\n"
     "                      + adjnirbmd(i)*(1.-albedo_direct(2)) + adjnirdfd(i)*(1.-albedo_diffuse(2)))*delt\n"
     "          esb(133,i) = 1.d0\n"
     "        endif\n"
     "      endif\n"
     "      if (vegetation_category == isice_table) then\n"
     "        esb(134,i) = edir(i)*delt*(temperature_ground - 273.15d0)\n"
     "      else\n"
     "        esb(134,i) = ((ecan(i) + etran(i))*(temperature_leaf - 273.15d0) &\n"
     "                     + edir(i)*(temperature_ground - 273.15d0))*delt\n"
     "      endif\n"
     "      esb(135,i) = (ecan(i) + etran(i) + edir(i))*delt*(temperature_forcing - 273.15d0)\n"
     "      esb(136,i) = precipitation_forcing*delt*(temperature_forcing - 273.15d0)\n")
# frame-F statistics, ice and open water (layer 7)
post(ice, "          esb(78,i) = sfcnsw(i)*delt\n",
     "          esb(137,i) = evapi(i)/hvap*delt*(tice(i) - 273.15d0)\n"
     "          esb(138,i) = evapi(i)/hvap*delt*(t1(i) - 273.15d0)\n")
post(nst, "          esb(101,i) = sfcemis(i)*sbc*tskin(i)**4*timestep\n",
     "          esb(139,i) = evap(i)/hvap*timestep*(tskin(i) - 273.15d0)\n"
     "          esb(140,i) = evap(i)/hvap*timestep*(t1(i) - 273.15d0)\n")

# ---------------------------------------------------------------- composites_post LW1 / EV1 block
post(cpo, "            qsfc_heat = qsfc_heat - (sfculw_rad(i) - sfcdlw_rad(i))\n",
     "            esb(172,i) = qsfc_heat\n"
     "            esb(173,i) = txl*(adjsfculw_land(i) - adjsfcdlw(i))\n"
     "            esb(174,i) = txi*(adjsfculw_ice(i) - adjsfcdlw(i))\n"
     "            esb(175,i) = txo*(adjsfculw_water(i) - adjsfcdlw(i))\n"
     "            esb(176,i) = sfculw_rad(i) - sfcdlw_rad(i)\n")
post(cpo, "          if (eve .and. dry(i)) qsfc_heat = qsfc_heat + txl*hflx_evap_enth(i)\n",
     "          if (eve .and. dry(i)) esb(177,i) = txl*hflx_evap_enth(i)\n"
     "          esb(171,i) = qsfc_heat\n")

# ---------------------------------------------------------------- MP_generic_post: host-frozen convective precipitation
post(mpp, "      use calpreciptype_mod, only: calpreciptype\n", "      use energy_meter_common, only: esg\n")
sub(mpp, "precip_phase_host, con_hfus, con_cp", "precip_phase_host, con_hfus, con_cp, garea")
post(mpp, "      real(kind=kind_phys),                    intent(in)    :: con_hfus, con_cp\n",
     "      real(kind=kind_phys), dimension(:), optional, intent(in) :: garea\n")
post(mpp, "*rhowater*csnow*con_g / (con_cp*(prsi(i,1)-prsi(i,2)))\n            endif\n",
     "            if (present(garea) .and. csnow > zero) then\n"
     "              esg(207) = esg(207) + garea(i)*3.3358d5*rhowater*csnow\n"
     "              esg(208) = esg(208) + garea(i)*rhowater*csnow\n"
     "              if (present(precip_phase_host)) then\n"
     "                if (precip_phase_host) esg(209) = esg(209) + garea(i)*lfph*rhowater*csnow\n"
     "              endif\n"
     "            endif\n")
s = get(mppm)
edits[mppm] = (s if s.endswith("\n") else s + "\n") + (
    "[garea]\n  standard_name = cell_area\n  long_name = grid cell area\n  units = m2\n"
    "  dimensions = (horizontal_loop_extent)\n  type = real\n  kind = kind_phys\n  intent = in\n  optional = True\n")

for p, s in edits.items():
    p.write_text(s)
    print("instrumented", p.name)
