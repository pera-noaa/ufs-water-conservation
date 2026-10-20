#!/usr/bin/env python3
"""FV2 candidate: in atmos_phys_driver_statein convert tracers to the physics basis with the same layer thickness
(prsi(k)-prsi(k+1)) that atmosphere_state_update uses to convert them back, so the round trip is exact to ~eps
instead of eps*p/dp. Usage: fix_FV2_statein_dp.py <ufs-weather-model tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90"
s = f.read_text()
reps = [("""           IPD_Statein%prsi(im,k)  = IPD_Statein%prsi(im,k+1) + IPD_Statein%prsl(im,k)
           IPD_Statein%prsik(im,k) = log( IPD_Statein%prsi(im,k) )
! Redefine mixing ratios for GFS == tracer_mass / (dry_air_mass + water_vapor_mass)
           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &
                                                   / IPD_Statein%prsl(im,k)
""", """           IPD_Statein%prsi(im,k)  = IPD_Statein%prsi(im,k+1) + IPD_Statein%prsl(im,k)
           IPD_Statein%prsik(im,k) = log( IPD_Statein%prsi(im,k) )
! Redefine mixing ratios for GFS == tracer_mass / (dry_air_mass + water_vapor_mass)
! (divide by the thickness atmosphere_state_update multiplies back by, so tracer mass round-trips exactly)
           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &
                                                   / (IPD_Statein%prsi(im,k) - IPD_Statein%prsi(im,k+1))
"""), ("""           IPD_Statein%prsi(im,k+1)  = IPD_Statein%prsi(im,k) + IPD_Statein%prsl(im,k)
           IPD_Statein%prsik(im,k) = log( IPD_Statein%prsi(im,k) )
! Redefine mixing ratios for GFS == tracer_mass / (dry_air_mass + water_vapor_mass)
           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &
                                           / IPD_Statein%prsl(im,k)
""", """           IPD_Statein%prsi(im,k+1)  = IPD_Statein%prsi(im,k) + IPD_Statein%prsl(im,k)
           IPD_Statein%prsik(im,k) = log( IPD_Statein%prsi(im,k) )
! Redefine mixing ratios for GFS == tracer_mass / (dry_air_mass + water_vapor_mass)
! (divide by the thickness atmosphere_state_update multiplies back by, so tracer mass round-trips exactly)
           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &
                                           / (IPD_Statein%prsi(im,k+1) - IPD_Statein%prsi(im,k))
""")]
for old, new in reps:
    if s.count(old) != 1:
        sys.exit(f"ABORT: {s.count(old)} matches")
    s = s.replace(old, new)
f.write_text(s)
print("FV2 applied", f)
