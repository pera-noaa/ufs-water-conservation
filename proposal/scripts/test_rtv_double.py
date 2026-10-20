#!/usr/bin/env python3
"""Diagnostic test only: compute rTv in the FV3 driver's physics state (atmosphere.F90) with double-precision gas
constants equal to the physics' con_rd and con_rv, instead of the dycore's rdgas and zvir (single precision in a
32-bit build). Usage: python3 test_rtv_double.py <ufs_model.fd>"""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "FV3/atmos_cubed_sphere/driver/fvGFS/atmosphere.F90"
s = f.read_text()
old = "           rTv = rdgas*IPD_Data(nb)%Statein%tgrs(i,k)*(1.+zvir*qgrs_rad)\n"
new = ("           rTv = 2.8705e+2_kind_phys*IPD_Data(nb)%Statein%tgrs(i,k)                  &\n"
       "               *(1.+(4.6150e+2_kind_phys/2.8705e+2_kind_phys-1.)*qgrs_rad)\n")
if s.count(old) != 1:
    sys.exit(f"ABORT: rTv line found {s.count(old)} times")
f.write_text(s.replace(old, new))
print(f"patched {f.name} (rTv in double, physics constants)")
