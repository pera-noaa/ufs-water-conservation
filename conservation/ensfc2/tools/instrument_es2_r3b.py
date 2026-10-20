#!/usr/bin/env python3
"""Surface energy meters, round 3b (after instrument_es2_r3.py): water content of evaporated ice, soil columns, J m-2:
  esl(61) snow / soil-ice sublimation content (hsnow, relative to tfrz)        -> esg(271)
  esl(62) frozen-ground evaporation content (ice at stc(1), deficit as liquid) -> esg(272)
Usage: instrument_es2_r3b.py <ufs-weather-model>"""
import sys
from pathlib import Path

lsm = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = lsm.read_text()
a1 = "   hevap = hevap + (qsnsub - qsnfro)*hvt1 + hsnow/dt\n"
a2 = "      hevap = hevap + (qseva - qsdew)*(hvt1 + cik*(stc(1)-tfrz)) + edef*(cwk - cik)*(stc(1)-tfrz)\n"
for a in (a1, a2):
    if s.count(a) != 1:
        sys.exit(f"ABORT: {a.strip()[:60]!r}")
s = s.replace(a1, a1 + "   esl(61) = esl(61) + hsnow\n")
s = s.replace(a2, a2 + "      esl(62) = esl(62) + ((qseva - qsdew)*cik + edef*(cwk - cik))*(stc(1)-tfrz)*dt\n")
lsm.write_text(s)
print("instrumented", lsm.name)
