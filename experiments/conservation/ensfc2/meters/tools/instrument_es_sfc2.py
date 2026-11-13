#!/usr/bin/env python3
"""Surface energy meters, second layer (apply after instrument_es_sfc.py):
  - Noah-MP water(): heat content after canwater, snowwater, the NM11 heat return, soilwater, groundwater
    (esl(31:40) -> esb(110:119) -> esg(181:190), soil columns)
  - storage change between calls (previous call's end vs this call's start): soil total esg(191), soil latent
    esg(192), sea ice esg(193), glacier total esg(180)
  - hand-off by surface type vs the cell's atmosphere-side flux: SW land/ice/water esg(194/195/199),
    LW land/ice/water esg(196/197/198)
Usage: instrument_es_sfc2.py <ufs-weather-model>"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
itl = root / "Interstitials/UFS_SCM_NEPTUNE"
emc = itl / "energy_meter_common.F90"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def pre(path, anchor, text):
    sub(path, anchor, text + anchor)


def post(path, anchor, text):
    sub(path, anchor, anchor + text)


# energy_meter_common: previous-call storage per column, extra sums
post(emc, "  integer, save :: eskdt = -1\n",
     "  real(kind=8), save :: esph(emnc) = -1.d34, espl(emnc) = 0.d0, espi(emnc) = -1.d34\n")
pre(emc, "    esb(6, i) = esb(7, i) - esb(6, i)\n",
    "    if (esb(4, i) > 0.d0) then\n"
    "       if (esph(jj) > -1.d33) then\n"
    "          if (esb(4, i) == 1.d0) then\n"
    "             esg(191) = esg(191) + wl*(esb(6, i) - esph(jj))\n"
    "             esg(192) = esg(192) + wl*(esb(58, i) - espl(jj))\n"
    "          else\n"
    "             esg(180) = esg(180) + wl*(esb(6, i) - esph(jj))\n"
    "          endif\n"
    "       endif\n"
    "       esph(jj) = esb(7, i)\n"
    "       espl(jj) = esb(59, i)\n"
    "    endif\n"
    "    if (esb(60, i) > 0.d0) then\n"
    "       if (espi(jj) > -1.d33) esg(193) = esg(193) + wi*(esb(61, i) - espi(jj))\n"
    "       espi(jj) = esb(62, i)\n"
    "    endif\n"
    "    if (esb(4, i) == 1.d0) esg(181:190) = esg(181:190) + wl*esb(110:119, i)\n"
    "    esg(194) = esg(194) + wl*(esb(8, i) - emf(6, jj))\n"
    "    esg(195) = esg(195) + wi*(esb(81, i) - emf(6, jj))\n"
    "    esg(196) = esg(196) + wl*(-esb(9, i) - emf(5, jj))\n"
    "    esg(197) = esg(197) + wi*(esb(82, i) - emf(5, jj))\n"
    "    esg(198) = esg(198) + wo*(esb(94, i) - esb(101, i) - emf(5, jj))\n"
    "    esg(199) = esg(199) + wo*(esb(90, i) - emf(6, jj))\n")

# Noah-MP water() sub-segments (smc is stale inside water(): heat content from sh2o + sice)
sub(lsm, "  real(kind=8), public, save :: esl(30) = 0.d0\n",
    "  real(kind=8), public, save :: esl(40) = 0.d0\n  real(kind=8), save :: es_ws = 0.d0, es_wl = 0.d0\n")
DECL = ("    type (noahmp_parameters), intent(in) :: parameters\n"
        "    integer, intent(in) :: k, nsnow, nsoil, isnow\n"
        "    real(kind=kind_phys), intent(in) :: stc(-nsnow+1:nsoil), dzsnso(-nsnow+1:nsoil), snice(-nsnow+1:0), &\n"
        "                                        snliq(-nsnow+1:0), sh2o(nsoil), sice(nsoil), sneqv, canice\n")
WARGS = "parameters, nsnow, nsoil, isnow, stc, dzsnso, snice, snliq, sh2o, sice, sneqv, canice"
pre(lsm, "  subroutine noahmp_sflx (parameters, &\n",
    f"  subroutine es_segw(k, {WARGS})\n" + DECL +
    "    real(kind=8) :: hs, hl\n"
    "    call es_hland(parameters, nsnow, nsoil, isnow, stc, dzsnso, snice, snliq, sh2o + sice, sh2o, sneqv, &\n"
    "                  canice, hs, hl)\n"
    "    esl(k) = hs - es_ws\n    esl(k+1) = hl - es_wl\n    es_ws = hs\n    es_wl = hl\n"
    "  end subroutine es_segw\n")
pre(lsm, "   etrani(1:nsoil) = 0.\n", "   es_ws = es_hs\n   es_wl = es_hl\n")
pre(lsm, "     qsnsub = 0.\n", f"   call es_segw(31, {WARGS})\n")
pre(lsm, "   esl(23) = (qsnsub - qsnfro)*dt\n", f"   call es_segw(33, {WARGS})\n")
pre(lsm, "    qinsur = (ponding+ponding1+ponding2)/dt * 0.001\n", f"   call es_segw(35, {WARGS})\n")
pre(lsm, "          call groundwater (parameters,nsnow  ,nsoil  ,dt     ,sice   ,zsoil  , & !in\n",
    f"          call es_segw(37, {WARGS})\n")
pre(lsm, "    runsub       = runsub + snoflow         !mm/s\n", f"   call es_segw(39, {WARGS})\n")

# driver: latent part at start and end, water() sub-segments
post(drv, "      es_h0 = es_hs + es_hl\n", "      esb(58,i) = es_hl\n")
post(drv, "      esb(7,i) = es_hs + es_hl\n", "      esb(59,i) = es_hl\n")
post(drv, "        esb(23:52,i) = esl(1:30)\n", "        esb(110:119,i) = esl(31:40)\n")

# sea ice: final-call SW and LW used
post(ice, "          esb(69,i) = esb(69,i) + sneti(i)*delt\n",
     "          esb(81,i) = sneti(i)*delt\n"
     "          esb(82,i) = (dlwflx(i) - sfcemis(i)*sbc*t12*t12\n"
     "     &      - 4.d0*sfcemis(i)*sbc*t12*es_t0(i)*tem)*delt\n")

for path, s in edits.items():
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
