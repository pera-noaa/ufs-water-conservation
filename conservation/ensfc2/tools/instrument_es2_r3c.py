#!/usr/bin/env python3
"""Surface energy meters, round 3c: precipitation stored in existing snow layers at the layer T (soil columns, J m-2):
  esl(63) snowfall added to the top snow layer, cice/denice m (T - tfrz) -> esg(273)
  esl(64) rain added to the top snow layer,  cwat/denh2o m (T - tfrz)   -> esg(274)
Usage: instrument_es2_r3c.py <ufs-weather-model>"""
import sys
from pathlib import Path
lsm = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = lsm.read_text()
a1 = "         snice(isnow+1)  = snice(isnow+1)   + qsnow   * dt\n"
a2 = "         snliq(isnow+1) = snliq(isnow+1) + qrain * dt\n"
for a in (a1, a2):
    if s.count(a) != 1:
        sys.exit(f"ABORT {a.strip()!r}")
s = s.replace(a1, a1 + "         esl(63) = esl(63) + cice/denice*qsnow*dt*(stc(isnow+1)-tfrz)\n")
s = s.replace(a2, a2 + "         esl(64) = esl(64) + cwat/denh2o*qrain*dt*(stc(isnow+1)-tfrz)\n")
lsm.write_text(s)
print("instrumented", lsm.name)
