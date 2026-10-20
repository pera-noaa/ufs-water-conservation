#!/usr/bin/env python3
"""apply_e1.py <ufs-weather-model> : E.1 sea spray behind gfs_physics_nml nst_spray_opt (default 0 = explicit, stock).
1 = backward Euler of the spray exchange with the lowest layer, linearised in t1 and q1 (qs(t1) by its slope): the
spray fluxes are those of the layer state at the end of the step under the spray alone. sfc_nst.f90 and sfc_ocean.F
(same code). New scheme arguments: nst_spray_opt, the interface pressures (lowest layer mass) and gravity; sfc_ocean also
the time step."""
import sys
from pathlib import Path

T = Path(sys.argv[1])
P = T / "UFSATM/ccpp/physics/physics"
D = T / "UFSATM/ccpp/data"


def sub(path, old, new, count=1):
    s = path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: anchor found {n}x (want {count}):\n{old[:200]}")
    path.write_text(s.replace(old, new))


META = """[nst_spray_opt]
  standard_name = control_for_sea_spray_time_integration
  long_name = sea spray: 0 explicit, 1 backward Euler with the lowest layer
  units = index
  dimensions = ()
  type = integer
  intent = in
[prsi]
  standard_name = air_pressure_at_interface
  long_name = air pressure at model layer interfaces
  units = Pa
  dimensions = (horizontal_loop_extent,vertical_interface_dimension)
  type = real
  kind = kind_phys
  intent = in
[con_g]
  standard_name = gravitational_acceleration
  long_name = gravitational acceleration
  units = m s-2
  dimensions = ()
  type = real
  kind = kind_phys
  intent = in
"""

# ---- sfc_nst.f90 (free form)
f = P / "SFC_Layer/UFS/sfc_nst.f90"
sub(f, "       q1, tref, cm, ch, lseaspray, fm, fm10,                     &\n",
    "       q1, tref, cm, ch, lseaspray, fm, fm10,                     &\n"
    "       nst_spray_opt, prsi, con_g,                                 &\n")
sub(f, "    ! For sea spray effect\n    logical, intent(in) :: lseaspray\n",
    "    ! For sea spray effect\n    logical, intent(in) :: lseaspray\n"
    "    integer, intent(in) :: nst_spray_opt   ! 0 explicit, 1 backward Euler with the lowest layer\n"
    "    real (kind=kind_phys), dimension(:,:), intent(in) :: prsi\n"
    "    real (kind=kind_phys), intent(in) :: con_g\n")
sub(f, "    real (kind=kind_phys) :: windrel\n",
    "    real (kind=kind_phys) :: windrel\n"
    "    real (kind=kind_phys) :: ca, cb, dqs, at, aq, a11, a12, a21, a22, r1, r2, det, dts, dqv\n")
IMP = """          if (nst_spray_opt == 1) then
             ! backward Euler: spray fluxes of the lowest layer's end-of-step state under the spray alone
             ca = conlf * (ws10**5.4) * ru10 * bb1 * rho_a(i) * hvap   ! W m-2 per unit saturation deficit
             cb = consf * (ws10**3.4) * ru10 * rho_a(i) * cp           ! W m-2 K-1
             tem = fpvs(t1(i) + 0.05_kp)
             dqs = eps * tem / (prsl1(i) + epsm1 * tem)
             tem = fpvs(t1(i) - 0.05_kp)
             dqs = (dqs - eps * tem / (prsl1(i) + epsm1 * tem)) * 10._kp   ! d qs / d t1
             at = timestep * con_g / (cp * (prsi(i,1) - prsi(i,2)))
             aq = timestep * con_g / (hvap * (prsi(i,1) - prsi(i,2)))
             ptem = alps - gams
             a11 = one + at * (bets * cb + ptem * ca * dqs)
             a12 = - at * ptem * ca
             a21 = - aq * alps * ca * dqs
             a22 = one + aq * alps * ca
             r1 = at * (bets * cb * (tskin(i) - t1(i)) - ptem * ca * (qss1 - q0(i)))
             r2 = aq * alps * ca * (qss1 - q0(i))
             det = a11 * a22 - a12 * a21
             dts = (r1 * a22 - a12 * r2) / det
             dqv = (a11 * r2 - a21 * r1) / det
             evaps = ca * (qss1 + dqs * dts - q0(i) - dqv)
          endif
"""
sub(f, "          evaps = evaps * rho_a(i) * hvap * (qss1 - q0(i))\n          evap(i) = evap(i) + alps * evaps\n",
    "          evaps = evaps * rho_a(i) * hvap * (qss1 - q0(i))\n" + IMP + "          evap(i) = evap(i) + alps * evaps\n")
sub(f, "          hflxs = hflxs * rho_a(i) * cp * (tskin(i) - t1(i))\n",
    "          hflxs = hflxs * rho_a(i) * cp * (tskin(i) - t1(i))\n"
    "          if (nst_spray_opt == 1) hflxs = cb * (tskin(i) - t1(i) - dts)\n")
sub(P / "SFC_Layer/UFS/sfc_nst.meta", "[fm]\n  standard_name = Monin_Obukhov_similarity_function_for_momentum_over_water\n",
    META + "[fm]\n  standard_name = Monin_Obukhov_similarity_function_for_momentum_over_water\n")

# ---- sfc_ocean.F (fixed form, same spray code; needs the time step too)
g = P / "SFC_Models/Ocean/UFS/sfc_ocean.F"
sub(g, "     &       tskin, cm, ch, lseaspray, fm, fm10,                        &\n",
    "     &       tskin, cm, ch, lseaspray, fm, fm10,                        &\n"
    "     &       nst_spray_opt, prsi, con_g, timestep,                       &\n")
sub(g, "      logical, intent(in) :: lseaspray\n",
    "      logical, intent(in) :: lseaspray\n"
    "      integer, intent(in) :: nst_spray_opt\n"
    "      real (kind=kind_phys), dimension(:,:), intent(in) :: prsi\n"
    "      real (kind=kind_phys), intent(in) :: con_g, timestep\n")
s = g.read_text()
a = "     &                         bb1, hflxs, evaps, ptem\n"
if s.count(a) != 1:
    sys.exit("ABORT sfc_ocean locals")
g.write_text(s.replace(a, a + "      real (kind=kind_phys) :: ca, cb, dqs, at, aq, a11, a12, a21, a22,  &\n"
                             "     &                         r1, r2, det, dts, dqv, tes\n"))
IMPF = """          if (nst_spray_opt == 1) then
!  backward Euler: spray fluxes of the lowest layer's end-of-step
!  state under the spray alone
            ca = conlf * (ws10**5.4) * ru10 * bb1 * rho(i) * hvap
            cb = consf * (ws10**3.4) * ru10 * rho(i) * cp
            tes = fpvs(t1(i) + 0.05_kind_phys)
            dqs = eps * tes / (prsl1(i) + epsm1 * tes)
            tes = fpvs(t1(i) - 0.05_kind_phys)
            dqs = (dqs - eps * tes / (prsl1(i) + epsm1 * tes))           &
     &          * 10.0_kind_phys
            at = timestep * con_g / (cp * (prsi(i,1) - prsi(i,2)))
            aq = timestep * con_g / (hvap * (prsi(i,1) - prsi(i,2)))
            ptem = alps - gams
            a11 = 1.0_kind_phys + at * (bets * cb + ptem * ca * dqs)
            a12 = - at * ptem * ca
            a21 = - aq * alps * ca * dqs
            a22 = 1.0_kind_phys + aq * alps * ca
            r1 = at * (bets*cb*(tskin(i) - t1(i))                       &
     &               - ptem*ca*(qss1 - q0(i)))
            r2 = aq * alps * ca * (qss1 - q0(i))
            det = a11 * a22 - a12 * a21
            dts = (r1 * a22 - a12 * r2) / det
            dqv = (a11 * r2 - a21 * r1) / det
            evaps = ca * (qss1 + dqs * dts - q0(i) - dqv)
          endif
"""
sub(g, "          evaps = evaps * rho(i) * hvap * (qss1 - q0(i))\n          evap(i) = evap(i) + alps * evaps\n",
    "          evaps = evaps * rho(i) * hvap * (qss1 - q0(i))\n" + IMPF + "          evap(i) = evap(i) + alps * evaps\n")
sub(g, "          hflxs = hflxs * rho(i) * cp * (tskin(i) - t1(i))\n",
    "          hflxs = hflxs * rho(i) * cp * (tskin(i) - t1(i))\n"
    "          if (nst_spray_opt == 1) hflxs = cb * (tskin(i) - t1(i) - dts)\n")
om = P / "SFC_Models/Ocean/UFS/sfc_ocean.meta"
sub(om, "[fm]\n  standard_name = Monin_Obukhov_similarity_function_for_momentum_over_water\n",
    META + "[timestep]\n  standard_name = timestep_for_physics\n  long_name = physics timestep\n  units = s\n"
           "  dimensions = ()\n  type = real\n  kind = kind_phys\n  intent = in\n"
           "[fm]\n  standard_name = Monin_Obukhov_similarity_function_for_momentum_over_water\n")

td = D / "GFS_typedefs.F90"
sub(td, "    logical              :: lseaspray       !< flag for sea spray parameterization\n",
    "    logical              :: lseaspray       !< flag for sea spray parameterization\n"
    "    integer              :: nst_spray_opt   !< sea spray time integration: 0 explicit, 1 backward Euler with the lowest layer\n")
sub(td, "    logical              :: lseaspray      = .false.                  !< flag for sea spray parameterization\n",
    "    logical              :: lseaspray      = .false.                  !< flag for sea spray parameterization\n"
    "    integer              :: nst_spray_opt  = 0\n")
sub(td, "lheatstrg, lseaspray, cnvcld,", "lheatstrg, lseaspray, nst_spray_opt, cnvcld,")
sub(td, "    Model%lseaspray         = lseaspray\n",
    "    Model%lseaspray         = lseaspray\n    Model%nst_spray_opt     = nst_spray_opt\n")
sub(td, "      print *, ' lseaspray         : ', Model%lseaspray\n",
    "      print *, ' lseaspray         : ', Model%lseaspray\n"
    "      print *, ' nst_spray_opt     : ', Model%nst_spray_opt\n")
tm = D / "GFS_typedefs.meta"
s = tm.read_text()
a = "[lseaspray]\n"
if s.count(a) != 1:
    sys.exit("ABORT typedefs meta lseaspray")
tm.write_text(s.replace(a, "[nst_spray_opt]\n  standard_name = control_for_sea_spray_time_integration\n"
                           "  long_name = sea spray: 0 explicit, 1 backward Euler with the lowest layer\n"
                           "  units = index\n  dimensions = ()\n  type = integer\n" + a))
print("E1 applied", T)
