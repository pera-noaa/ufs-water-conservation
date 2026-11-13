#!/usr/bin/env python3
"""Surface energy meters, seventh layer (after instrument_es_sfc6.py): what frame F (encpl) needs from the surfaces.
E-weighted evaporating-surface and lowest-layer temperatures, kg m-2 K relative to T0 = 273.15:
  land  sum E_k (T_k - T0) esg(237) [canopy evaporation and transpiration at tv, ground at tg; glacier at tg],
        E (T1 - T0) esg(238), precipitation P (T1 - T0) esg(239)  (x txl)
  ice   E (tice - T0) esg(240), E (T1 - T0) esg(241)  (x txi);  water E (tskin - T0) esg(242), E (T1 - T0) esg(243)
Usage: instrument_es_sfc7.py <ufs-weather-model>"""
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
emc = root / "Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
nst = root / "SFC_Layer/UFS/sfc_nst.f90"
edits = {}


def post(path, a, t):
    s = edits.get(path) or path.read_text()
    if s.count(a) != 1:
        sys.exit(f"ABORT {path.name}: {s.count(a)} matches: {a.strip()[:70]!r}")
    edits[path] = s.replace(a, a + t)


post(emc, "    if (esb(4, i) == 1.d0) esg(221:230) = esg(221:230) + wl*esb(121:130, i)\n",
     "    esg(237:239) = esg(237:239) + wl*esb(134:136, i)\n"
     "    esg(240:241) = esg(240:241) + wi*esb(137:138, i)\n"
     "    esg(242:243) = esg(242:243) + wo*esb(139:140, i)\n")
post(drv, "      esb(57,i) = 1000.d0*tprcp(i)*srflag(i)\n",
     "      if (vegetation_category == isice_table) then\n"
     "        esb(134,i) = edir(i)*delt*(temperature_ground - 273.15d0)\n"
     "      else\n"
     "        esb(134,i) = ((ecan(i) + etran(i))*(temperature_leaf - 273.15d0) &\n"
     "                     + edir(i)*(temperature_ground - 273.15d0))*delt\n"
     "      endif\n"
     "      esb(135,i) = (ecan(i) + etran(i) + edir(i))*delt*(temperature_forcing - 273.15d0)\n"
     "      esb(136,i) = precipitation_forcing*delt*(temperature_forcing - 273.15d0)\n")
post(ice, "          esb(78,i) = sfcnsw(i)*delt\n",
     "          esb(137,i) = evapi(i)/hvap*delt*(tice(i) - 273.15d0)\n"
     "          esb(138,i) = evapi(i)/hvap*delt*(t1(i) - 273.15d0)\n")
post(nst, "          esb(101,i) = sfcemis(i)*sbc*tskin(i)**4*timestep\n",
     "          esb(139,i) = evap(i)/hvap*timestep*(tskin(i) - 273.15d0)\n"
     "          esb(140,i) = evap(i)/hvap*timestep*(t1(i) - 273.15d0)\n")
for p, s in edits.items():
    p.write_text(s)
    print("instrumented", p.name)
