#!/usr/bin/env python3
"""Land water meter for NOAA-EMC/noahmp's CCPP driver (diagnostic builds only): per soil column and call, storage
S = canliq + canice + sneqv + wa + sum(smc*dz)*1000 before and after noahmp_sflx, against
(precipitation as Noah-MP sums it, prcpconv + prcpnonc + prcpshcv, - canopy evaporation - transpiration - soil evaporation - surface runoff - baseflow)*dt. Each
noahmpdrv_run call prints the increments of this call on its rank:
  WBLND ncol  sum(res)  sum|res|  sum(P*dt)  loop-iterations  land-points  glacier-points   (mm, unweighted)
so the run totals are the sums over all WBLND lines. Usage: python3 instrument_noahmp_emc_meter.py <noahmp checkout>"""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "drivers/ccpp/noahmpdrv.F90"
s = f.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


s = one(s, "  integer    :: iopt_gla  = 2 ! option for glacier treatment\n",
        "  integer    :: iopt_gla  = 2 ! option for glacier treatment\n"
        "  real (kind=kind_phys) :: wbm_s0, wbm_s1, wbm_r, wbm(3), wbm_dz\n  integer :: wbm_n, wbm_k, wbm_c(3)\n", "locals")
s = one(s, "  do i = 1, im\n\n    if (flag_iter(i) .and. dry(i)) then\n",
        "  wbm = 0.0; wbm_n = 0; wbm_c = 0\n  do i = 1, im\n    wbm_c(1) = wbm_c(1) + 1\n\n    if (flag_iter(i) .and. dry(i)) then\n"
        "      wbm_c(2) = wbm_c(2) + 1\n", "loop start")
a = s.index("        call noahmp_sflx (parameters")
anchor = "        latent_heat_total  = latent_heat_canopy + latent_heat_ground + transpiration_heat\n"
if s.count(anchor) != 1 or s.index(anchor) < a:
    sys.exit("ABORT: statement after the noahmp_sflx call")
e = s.index(anchor)  # first statement after the call (which ends inside #ifdef CCPP blocks)
before = ("        wbm_s0 = canopy_liquid + canopy_ice + snow_water_equiv + aquifer_water\n"
          "        do wbm_k = 1, nsoil\n"
          "          wbm_dz = -soil_interface_depth(wbm_k)\n"
          "          if (wbm_k > 1) wbm_dz = soil_interface_depth(wbm_k-1) - soil_interface_depth(wbm_k)\n"
          "          wbm_s0 = wbm_s0 + soil_moisture_vol(wbm_k)*wbm_dz*1000.0\n"
          "        end do\n")
after = ("        wbm_s1 = canopy_liquid + canopy_ice + snow_water_equiv + aquifer_water\n"
         "        do wbm_k = 1, nsoil\n"
         "          wbm_dz = -soil_interface_depth(wbm_k)\n"
         "          if (wbm_k > 1) wbm_dz = soil_interface_depth(wbm_k-1) - soil_interface_depth(wbm_k)\n"
         "          wbm_s1 = wbm_s1 + soil_moisture_vol(wbm_k)*wbm_dz*1000.0\n"
         "        end do\n"
         "        wbm_r = wbm_s1 - wbm_s0 - (precip_convective + precip_non_convective + precip_sh_convective - evaporation_canopy - transpiration &\n"
         "                - evaporation_soil - runoff_surface - runoff_baseflow)*delt\n"
         "        wbm(1) = wbm(1) + wbm_r; wbm(2) = wbm(2) + abs(wbm_r)\n"
         "        wbm(3) = wbm(3) + (precip_convective + precip_non_convective + precip_sh_convective)*delt; wbm_n = wbm_n + 1\n")
s = s[:a] + before + s[a:e] + after + s[e:]
s = one(s, "  end do ! im loop\n", "  end do ! im loop\n  write(*,'(a,i8,3es22.13,3i8)') 'WBLND ', wbm_n, wbm, wbm_c\n", "print")
s = one(s, "        call noahmp_glacier (", "        wbm_c(3) = wbm_c(3) + 1\n        call noahmp_glacier (", "glacier count")
f.write_text(s)
print(f"instrumented {f.name}: WBLND meter")
