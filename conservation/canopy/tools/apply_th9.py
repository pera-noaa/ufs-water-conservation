#!/usr/bin/env python3
"""apply_th9.py <ufs-weather-model> : TH9 behind gfs_physics_nml thompson_sed_actual (default .false.): flux-form
sedimentation moves the layers' actual rain/ice/snow/graupel, not the R1 placeholder (held TH9, switched)."""
import sys
from pathlib import Path

T = Path(sys.argv[1])
M = T / "UFSATM/ccpp/physics/physics/MP/Thompson"
D = T / "UFSATM/ccpp/data"


def sub(path, old, new, count=1):
    s = path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: anchor found {n}x (want {count}):\n{old[:200]}")
    path.write_text(s.replace(old, new))


mod = M / "module_mp_thompson.F90"
sub(mod, "   logical                      :: thompson_kirchhoff = .false.\n",
    "   logical                      :: thompson_kirchhoff = .false.\n"
    "!..thompson_sed_actual: floored layers sediment their actual mass, not the R1 placeholder\n"
    "   logical                      :: thompson_sed_actual = .false.\n")
sub(mod, "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n",
    "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon, sfloor\n")
sub(mod, "      if (ANY(L_qr .eqv. .true.)) then\n         nstep = nint(1./onstep(1))\n\n         if(.not. sedi_semi) then\n",
    "      sfloor = R1\n      if (thompson_sed_actual) sfloor = 0._wp\n"
    "      if (ANY(L_qr .eqv. .true.)) then\n         nstep = nint(1./onstep(1))\n\n         if(.not. sedi_semi) then\n"
    "            if (thompson_sed_actual) then  ! the R1 placeholder is not sedimented as mass\n"
    "               do k = kts, kte\n"
    "                  if (rr(k) .le. R1) rr(k) = max(0._wp, (qr1d(k) + qrten(k)*DT)*rho(k))\n"
    "               enddo\n            endif\n")
for sp, q, n in (("i", "qi", 2), ("s", "qs", 3)):
    sub(mod, f"      if (ANY(L_q{sp} .eqv. .true.)) then\n         nstep = nint(1./onstep({n}))\n         do n = 1, nstep\n",
        f"      if (ANY(L_q{sp} .eqv. .true.)) then\n         nstep = nint(1./onstep({n}))\n"
        f"         if (thompson_sed_actual) then  ! the R1 placeholder is not sedimented as mass\n"
        f"            do k = kts, kte\n"
        f"               if (r{sp}(k) .le. R1) r{sp}(k) = max(0._wp, ({q}1d(k) + {q}ten(k)*DT)*rho(k))\n"
        f"            enddo\n         endif\n         do n = 1, nstep\n")
sub(mod, "      if (ANY(L_qg .eqv. .true.)) then\n         nstep = nint(1./onstep(4))\n         if(.not. sedi_semi) then \n",
    "      if (ANY(L_qg .eqv. .true.)) then\n         nstep = nint(1./onstep(4))\n         if(.not. sedi_semi) then \n"
    "            if (thompson_sed_actual) then  ! the R1 placeholder is not sedimented as mass\n"
    "               do k = kts, kte\n"
    "                  if (rg(k) .le. R1) rg(k) = max(0._wp, (qg1d(k) + qgten(k)*DT)*rho(k))\n"
    "               enddo\n            endif\n")
for sp in "risg":
    sub(mod, f"r{sp}(k) = max(R1, r{sp}(k) ", f"r{sp}(k) = max(sfloor, r{sp}(k) ", 2)

if "--module-only" in sys.argv:
    sys.exit(print("TH9 module only", T))
drv = M / "mp_thompson.F90"
sub(drv, "                                  is_initialized, kirchhoff, errmsg, errflg)\n",
    "                                  is_initialized, kirchhoff, sed_actual, errmsg, errflg)\n")
sub(drv, "lvap0, lfus, thompson_kirchhoff\n", "lvap0, lfus, thompson_kirchhoff, thompson_sed_actual\n")
sub(drv, "         logical,                   intent(in   ) :: kirchhoff\n",
    "         logical,                   intent(in   ) :: kirchhoff\n"
    "         logical,                   intent(in   ) :: sed_actual\n")
sub(drv, "         thompson_kirchhoff = kirchhoff\n",
    "         thompson_kirchhoff = kirchhoff\n         thompson_sed_actual = sed_actual\n")
meta = M / "mp_thompson.meta"
sub(meta, "[kirchhoff]\n  standard_name = flag_for_thompson_kirchhoff_latent_heat\n",
    "[sed_actual]\n  standard_name = flag_for_thompson_sedimenting_actual_mass\n"
    "  long_name = flag: Thompson flux-form sedimentation moves actual mass, not the R1 placeholder\n"
    "  units = flag\n  dimensions = ()\n  type = logical\n  intent = in\n"
    "[kirchhoff]\n  standard_name = flag_for_thompson_kirchhoff_latent_heat\n")

td = D / "GFS_typedefs.F90"
sub(td, "    logical              :: thompson_kirchhoff !<",
    "    logical              :: thompson_sed_actual !< Thompson sedimentation moves actual mass, not the R1 placeholder\n"
    "    logical              :: thompson_kirchhoff !<")
sub(td, "    logical              :: thompson_kirchhoff = .false.        !<",
    "    logical              :: thompson_sed_actual = .false.\n"
    "    logical              :: thompson_kirchhoff = .false.        !<")
sub(td, "                               sedi_semi, decfl, thompson_kirchhoff, samf_kirchhoff, thompson_frame_heat,                   &\n",
    "                               sedi_semi, decfl, thompson_kirchhoff, samf_kirchhoff, thompson_frame_heat,                   &\n"
    "                               thompson_sed_actual,                                                                         &\n")
sub(td, "    Model%thompson_kirchhoff = thompson_kirchhoff\n",
    "    Model%thompson_kirchhoff = thompson_kirchhoff\n    Model%thompson_sed_actual = thompson_sed_actual\n")
sub(td, "        print *, ' thompson_kirchhoff: ', Model%thompson_kirchhoff\n",
    "        print *, ' thompson_kirchhoff: ', Model%thompson_kirchhoff\n"
    "        print *, ' thompson_sed_actual: ', Model%thompson_sed_actual\n")
tm = D / "GFS_typedefs.meta"
sub(tm, "[thompson_kirchhoff]\n  standard_name = flag_for_thompson_kirchhoff_latent_heat\n",
    "[thompson_sed_actual]\n  standard_name = flag_for_thompson_sedimenting_actual_mass\n"
    "  long_name = flag: Thompson flux-form sedimentation moves actual mass, not the R1 placeholder\n"
    "  units = flag\n  dimensions = ()\n  type = logical\n"
    "[thompson_kirchhoff]\n  standard_name = flag_for_thompson_kirchhoff_latent_heat\n")
print("TH9 applied", T)
