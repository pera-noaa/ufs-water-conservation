#!/usr/bin/env python3
"""Diagnostic for the WBL errwat meter (apply after instrument_wb_land.py): print the water-balance terms of columns
whose Noah-MP errwat exceeds 0.5 mm in a step (first 40 per rank), and accumulate errwat by surface kind:
  WBL(10) = unweighted sum of errwat over glacier columns. Usage: python3 instrument_wb_landx.py <ufs_model.fd>"""
import sys
from pathlib import Path

drv = Path(sys.argv[1]) / "FV3/ccpp/physics/physics/SFC_Models/Land/Noahmp/noahmpdrv.F90"
s = drv.read_text()
old = "      wbl_tp(i) = 1000.0d0*tprcp(i)/delt\n"
new = (old +
       "      if ( vegetation_category == isice_table ) wbl(10) = wbl(10) + wbl_ew(i)\n"
       "      if (abs(wbl_ew(i)) > 0.5d0 .and. wbl_nx < 40) then\n"
       "        wbl_nx = wbl_nx + 1\n"
       "        write(*,'(a,i6,i5,i4,9es12.4)') 'WBLX ', itime, i, vegetation_category, wbl_ew(i), wbl_pr(i)*delt, &\n"
       "          wbl_et(i), runoff_surface*delt, runoff_baseflow*delt, canopy_ice+canopy_liquid, snow_water_equiv, &\n"
       "          aquifer_water, sum(soil_moisture_vol(1:4)*(/0.1d0,0.3d0,0.6d0,1.0d0/))*1000.d0\n"
       "      endif\n")
assert s.count(old) == 1, "anchor"
s = s.replace(old, new)
old2 = "      integer, public, save :: wbl_kdt = -1\n"
assert s.count(old2) == 1, "anchor2"
s = s.replace(old2, old2 + "      integer, save :: wbl_nx = 0\n")
drv.write_text(s)
print("instrumented", drv)
