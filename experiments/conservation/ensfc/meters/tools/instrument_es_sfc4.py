#!/usr/bin/env python3
"""Surface energy meters, fourth layer: SH and LH hand-off by cell class (apply after instrument_es_sfc3.py).
Per cell, components' booked flux (txl*land + txi*ice + txo*water) minus what the PBL applied (dtsfc1, dqsfc1):
LH -> esg(154/155/156), SH -> esg(157/158/159) for land-only / water-only / mixed cells; esg(160) = ice-cell LH.
Usage: instrument_es_sfc4.py <ufs-weather-model>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
s = p.read_text()
anchor = "    esg(161:169) = esg(161:169) + a*emf(4:12, jj)\n"
if s.count(anchor) != 1:
    sys.exit("ABORT energy_meter_common.F90: anchor")
s = s.replace("    real(kind=8) :: wl, wi, wo, d1, d2\n", "    real(kind=8) :: wl, wi, wo, d1, d2, dl, dh\n")
s = s.replace(anchor,
    "    dl = esb(1, i)*2.5d6*esb(14, i) + esb(2, i)*esb(74, i) + esb(3, i)*esb(98, i) - emf(9, jj)\n"
    "    dh = esb(1, i)*esb(10, i) + esb(2, i)*esb(73, i) + esb(3, i)*esb(97, i) - emf(8, jj)\n"
    "    if (esb(1, i) > 0.999d0) then\n"
    "       esg(154) = esg(154) + a*dl\n       esg(157) = esg(157) + a*dh\n"
    "    else if (esb(3, i) > 0.999d0) then\n"
    "       esg(155) = esg(155) + a*dl\n       esg(158) = esg(158) + a*dh\n"
    "    else\n"
    "       esg(156) = esg(156) + a*dl\n       esg(159) = esg(159) + a*dh\n"
    "    endif\n"
    "    if (esb(2, i) > 0.d0) esg(160) = esg(160) + a*dl\n" + anchor)
p.write_text(s)
print("instrumented", p)
