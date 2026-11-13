#!/usr/bin/env python3
"""Surface energy meters, round 4b (after instrument_es2_r4.py):
  glacier esgl(19) sublimated snow content hsng (j/m2) -> esg(317)
  soil columns: per-call closure R_final4 (es2_check.py formula) printed when |r| > 1 J m-2 as
  'ESR kdt i r E19 pst EP LW2 AIR R_P R_E R_S seg31..40(sensible) seg-latents' for localisation.
Usage: instrument_es2_r4b.py <ufs-weather-model>"""
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
emc = root / "Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
edits = {}
def sub(p, a, b):
    s = edits.get(p) or p.read_text()
    if s.count(a) != 1:
        sys.exit(f"ABORT {p.name}: {s.count(a)} {a.strip()[:60]!r}")
    edits[p] = s.replace(a, b)
sub(gla, "     esgl(18) = hprg\n", "     esgl(18) = hprg\n     esgl(19) = hsng\n")
sub(emc, "    if (esb(4, i) == 1.d0) esg(321:330) = esg(321:330) + wl*esb(191:200, i)\n",
    "    if (esb(4, i) == 1.d0) esg(321:330) = esg(321:330) + wl*esb(191:200, i)\n"
    "    if (esb(4, i) == 1.d0) then\n"
    "       d1 = esb(6,i) - (esb(8,i) - esb(9,i) - esb(10,i) - esb(11,i) + esb(12,i) + esb(36,i) + esb(46,i) &\n"
    "            - 3.3358d5*esb(17,i) + 3.3358d5*(esb(44,i) + esb(45,i)))\n"
    "       d2 = d1 - (esb(141,i)+esb(142,i)+esb(143,i)+esb(144,i)) + (esb(151,i)+esb(152,i)) &\n"
    "            - (esb(153,i)+esb(154,i)+esb(47,i)) - esb(41,i) + esb(155,i) + esb(156,i) &\n"
    "            - esb(191,i) - esb(192,i) - esb(195,i)\n"
    "       if (abs(d2) > 1.d0) write(*,'(a,i6,i5,20es12.4)') 'ESR ', eskdt, i, d2, esb(41,i), &\n"
    "            esb(153,i)+esb(154,i)+esb(47,i), esb(191,i), esb(192,i), esb(195,i), &\n"
    "            esb(25,i)+esb(26,i)+3.3358d5*esb(50,i), esb(27,i)+esb(28,i)-esb(51,i)-esb(36,i), &\n"
    "            -esb(33,i)-esb(35,i), esb(110:119,i)\n"
    "    endif\n")
for p, s in edits.items():
    p.write_text(s)
    print("instrumented", p.name)
