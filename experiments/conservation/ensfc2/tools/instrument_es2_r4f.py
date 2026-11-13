#!/usr/bin/env python3
"""Round 4f: per-column R_E (energy-step residual, J m-2) printed when |R_E| > 1e-3:
'ESE kdt i R_E dHs dHl ssoil*dt eflxb*dt' plus, from phasechange, the layer index and state of the first layer where
the KF1 remainder or the snow tfrz reset loses heat (esl(73:76)). Usage: instrument_es2_r4f.py <tree>"""
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
emc = root / "Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = emc.read_text()
a = "    if (esb(4, i) == 1.d0) esg(321:330) = esg(321:330) + wl*esb(191:200, i)\n"
assert s.count(a) == 1
s = s.replace(a, a + "    if (esb(4, i) == 1.d0) then\n"
              "       d1 = esb(27,i) + esb(28,i) - esb(51,i) - esb(36,i)\n"
              "       if (abs(d1) > 1.d-3) write(*,'(a,i6,i5,9es24.16)') 'ESE ', eskdt, i, d1, esb(27,i), esb(28,i), &\n"
              "            esb(51,i), esb(36,i), esb(197:200,i)\n"
              "    endif\n")
emc.write_text(s)
t = lsm.read_text()
# phasechange: record heat lost by the snow tfrz reset and the isnow==0 snow melt branch
a1 = "               if (mliq(j)*mice(j)>0.) stc(j) = tfrz\n"
assert t.count(a1) == 1
t = t.replace(a1, "               if (mliq(j)*mice(j)>0.) esl(73) = esl(73) + (stc(j)-tfrz)/fact(j)*dt\n" + a1)
a2 = "        heatr  = hm(1) - hfus*(temp1-sneqv)/dt  \n"
if t.count(a2) == 1:
    t = t.replace(a2, a2 + "        esl(74) = esl(74) + heatr*dt\n")
a3 = "              xm(1) = 0.\n              hm(1) = 0.\n"
if t.count(a3) == 1:
    t = t.replace(a3, "              esl(75) = esl(75) + hm(1)*dt\n" + a3)
lsm.write_text(t)
print("instrumented")
