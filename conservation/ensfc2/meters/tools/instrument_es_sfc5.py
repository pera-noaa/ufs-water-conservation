#!/usr/bin/env python3
"""Surface energy meters, fifth layer: where the ice-cell LH/SH hand-off differs (apply after instrument_es_sfc4.py).
esng 200 -> 220. Ice-containing cells only:
  esg(201) composite evap (kinematic) x ice rho x hvap x dt      esg(202) PBL dqsfc1 x dt
  esg(203) txi x evap_ice (kinematic, in composite) x rho x hvap x dt   esg(204) txi x ice LH booked (W m-2) x dt
  esg(205) composite hflx x ice rho x cp x dt                   esg(206) PBL dtsfc1 x dt
Usage: instrument_es_sfc5.py <ufs-weather-model>"""
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
emc = root / "Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
cmp_ = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.F90"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    if s.count(old) != 1:
        sys.exit(f"ABORT {path.name}: {s.count(old)} matches: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, old + new) if new.startswith("\n") is False and False else s.replace(old, new)


sub(emc, "  integer, parameter, public :: esnb = 120, esng = 200\n", "  integer, parameter, public :: esnb = 120, esng = 220\n")
sub(emc, "    if (esb(2, i) > 0.d0) esg(160) = esg(160) + a*dl\n",
    "    if (esb(2, i) > 0.d0) esg(160) = esg(160) + a*dl\n"
    "    if (esb(2, i) > 0.d0 .and. esb(108, i) > 0.d0) then\n"
    "       esg(201) = esg(201) + a*esb(103, i)*esb(108, i)*2.5d6*esb(109, i)\n"
    "       esg(202) = esg(202) + a*emf(9, jj)\n"
    "       esg(203) = esg(203) + a*esb(104, i)*esb(108, i)*2.5d6*esb(109, i)\n"
    "       esg(204) = esg(204) + a*esb(2, i)*esb(74, i)\n"
    "       esg(205) = esg(205) + a*esb(105, i)*esb(108, i)*1004.6d0*esb(109, i)\n"
    "       esg(206) = esg(206) + a*emf(8, jj)\n"
    "    endif\n")
sub(cmp_, "          hflx(i)   = txl*hflx_lnd(i)  + txi*hflx_ice(i)  + txo*hflx_wat(i)\n",
    "          hflx(i)   = txl*hflx_lnd(i)  + txi*hflx_ice(i)  + txo*hflx_wat(i)\n"
    "          esb(103,i) = evap(i)\n          esb(104,i) = txi*evap_ice(i)\n          esb(105,i) = hflx(i)\n")
sub(ice, "          evapi(i) = evapi(i) * tem * hvapi\n",
    "          evapi(i) = evapi(i) * tem * hvapi\n"
    "          esb(108,i) = rho(i)\n          esb(109,i) = delt\n")
for p, s in edits.items():
    p.write_text(s)
    print("instrumented", p.name)
