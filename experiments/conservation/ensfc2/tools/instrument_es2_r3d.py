#!/usr/bin/env python3
"""Surface energy meters, round 3d: ice that was not there (soil columns, J m-2, hfus x mass taken from liquid instead):
  esl(65) frozen-ground evaporation in water() (NM11 returns the heat)       -> esg(275)
  esl(66) snow/soil-ice sublimation in snowh2o (no heat returned)            -> esg(276)
Usage: instrument_es2_r3d.py <ufs-weather-model>"""
import sys
from pathlib import Path
lsm = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = lsm.read_text()
a = "         lheat = lheat - hfus*sice(1)*dzsnso(1)*1000.   ! the missing ice came from the liquid\n"
if s.count(a) != 1:
    sys.exit("ABORT nm11 anchor")
s = s.replace(a, "         esl(65) = esl(65) - hfus*sice(1)*dzsnso(1)*1000.\n" + a)
i = s.index("  subroutine snowh2o (")
j = s.index("  end subroutine snowh2o", i)
blk = s[i:j]
b = "         sh2o(1) = sh2o(1) + sice(1)\n"
n = blk.count(b)
if n != 2:
    sys.exit(f"ABORT snowh2o deficit anchors {n}")
blk = blk.replace(b, "         esl(66) = esl(66) - hfus*sice(1)*dzsnso(1)*1000.\n" + b)
s = s[:i] + blk + s[j:]
lsm.write_text(s)
print("instrumented", lsm.name)
