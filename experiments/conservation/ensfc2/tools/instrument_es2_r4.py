#!/usr/bin/env python3
"""Surface energy meters, round 4 (after instrument_es2_r3*.py, on a tree with apply_bugfix_r4 + apply_options_r4).
Soil columns, J m-2 per call: esl(67) EP1 heat applied, esl(68) LW2 heat kept, esl(69) frame-F precipitation target,
  esl(70) stored precipitation content (hprec), esl(71) AIR1 heat kept                    -> esb(191:195) -> esg(321:325)
Glacier: esgl(13) sensible content change across the 600 mm reset (glacier flow), esgl(14) EP1 heat, esgl(15) LW2 heat,
  esgl(16) EV1 x dt, esgl(17) frame-F precipitation target, esgl(18) stored content    -> esb(181:186) -> esg(311:316)
Sea ice: esb(201) EP1 heat per ice area (J m-2)                                          -> esg(331)
Cells: esb(178) LW2 land part kept by the land (W m-2)                                    -> esg(308)
Usage: instrument_es2_r4.py <ufs-weather-model>"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
emc = root / "Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
cpo = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.F90"
edits = {}


def get(p):
    return edits.get(p) or p.read_text()


def sub(path, old, new, after=None, before=None):
    s = get(path)
    lo, hi = 0, len(s)
    if after is not None:
        if s.count(after) != 1:
            sys.exit(f"ABORT {path.name}: anchor count {s.count(after)}: {after.strip()[:60]!r}")
        lo = s.index(after)
    if before is not None:
        hi = s.index(before, lo)
    seg = s[lo:hi]
    if seg.count(old) != 1:
        sys.exit(f"ABORT {path.name}: {seg.count(old)} matches: {old.strip()[:70]!r}")
    edits[path] = s[:lo] + seg.replace(old, new) + s[hi:]


def pre(p, a, t, **kw):
    sub(p, a, t + a, **kw)


def post(p, a, t, **kw):
    sub(p, a, a + t, **kw)


pre(emc, "    esg(161:169) = esg(161:169) + a*emf(4:12, jj)\n",
    "    if (esb(4, i) == 1.d0) esg(321:330) = esg(321:330) + wl*esb(191:200, i)\n"
    "    if (esb(4, i) == 2.d0) esg(311:320) = esg(311:320) + wl*esb(181:190, i)\n"
    "    if (esb(60, i) > 0.d0) esg(331) = esg(331) + wi*esb(201, i)\n")
# cs1: the land heat content uses the per-mass snow heat capacity, as the model now does
sub(lsm, "       sv = min(1.d0, snice(iz)/(dzsnso(iz)*denice))\n       lv = min(1.d0 - sv, snliq(iz)/(dzsnso(iz)*denh2o))\n",
    "       sv = snice(iz)/(dzsnso(iz)*denice)\n       lv = snliq(iz)/(dzsnso(iz)*denh2o)\n")
# soil
post(lsm, "     if (present(hprec_out)) hprec_out = dqp\n",
     "     esl(67) = dqp\n     esl(68) = dqlw\n"
     "     esl(69) = (rain*cl_f*(sfctmp - tfrz) + snow*(ci_f*(sfctmp - t0_f) - cl_f*(tfrz - t0_f)))*dt\n"
     "     esl(70) = hprec\n")
WA = "  subroutine water (parameters,vegtyp ,nsnow  ,nsoil  ,imelt  ,dt     ,uu     , & !in\n"
sub(lsm, "          if (opt_air) qairh = cpair*(sh2o(iz) - sh2o0(iz))*dzsnso(iz)*(stc(iz) - tfrz)  ! air1: pore air heat kept\n",
    "          if (opt_air) qairh = cpair*(sh2o(iz) - sh2o0(iz))*dzsnso(iz)*(stc(iz) - tfrz)  ! air1: pore air heat kept\n"
    "          esl(71) = esl(71) + qairh\n", after=WA, before="  end subroutine water")
# glacier
sub(gla, "  real(kind=8), public, save :: esgl(12) = 0.d0\n", "  real(kind=8), public, save :: esgl(20) = 0.d0\n")
GL = "  subroutine noahmp_glacier (&\n"
post(gla, "     if (present(hprec_out)) hprec_out = dqp\n",
     "     esgl(14) = dqp\n     esgl(15) = dqlw\n"
     "     if (present(hevap)) esgl(16) = hevap*dt\n"
     "     esgl(17) = (prcp*(1.-fpice)*cl_f_gla*(sfctmp - tfrz) &\n"
     "              + prcp*fpice*(ci_f_gla*(sfctmp - t0_f_gla) - cl_f_gla*(tfrz - t0_f_gla)))*dt\n"
     "     esgl(18) = hprg\n", after=GL, before="  end subroutine noahmp_glacier")
SWG = "  subroutine snowwater_glacier (nsnow   ,nsoil   ,imelt    ,dt     ,sfctmp , & !in\n"
post(gla, "  real (kind=kind_phys)                                           :: hpf, hpr\n",
     "  real (kind=kind_phys)                                           :: es_h0\n", after=SWG,
     before="  end subroutine snowwater_glacier")
pre(gla, "!the reset below keeps 600 mm of ice: the liquid it removes leaves as surface runoff and\n",
    "   es_h0 = 0.d0\n"
    "   do iz = isnow+1, 0\n"
    "      es_h0 = es_h0 + snow_hcap_glacier(snice(iz), snliq(iz), dzsnso(iz))*(stc(iz) - tfrz)\n"
    "   enddo\n", after=SWG, before="  end subroutine snowwater_glacier")
pre(gla, "! sum up snow mass for layered snow\n",
    "   esgl(13) = -es_h0\n"
    "   do iz = isnow+1, 0\n"
    "      esgl(13) = esgl(13) + snow_hcap_glacier(snice(iz), snliq(iz), dzsnso(iz))*(stc(iz) - tfrz)\n"
    "   enddo\n", after=SWG, before="  end subroutine snowwater_glacier")
post(drv, "        esb(23:34,i) = esgl(1:12)\n", "        esb(181:188,i) = esgl(13:20)\n")
post(drv, "        esb(141:160,i) = esl(51:70)\n", "        esb(191:200,i) = esl(67:76)\n")
# sea ice
post(ice, "     &        - con_cliq*tfi_e + li_e)\n", "          esb(201,i) = dqp\n")
# composites
pre(cpo, "              if (ulw_lnd_rad(i) >= zero) qsfc_heat = qsfc_heat                                   &\n",
    "              if (ulw_lnd_rad(i) >= zero) esb(178,i) = txl*((adjsfculw_land(i) - adjsfcdlw(i))   &\n"
    "                - (ulw_lnd_rad(i) - sfcdlw_rad(i)))\n")
for p, s in edits.items():
    p.write_text(s)
    print("instrumented", p.name)
