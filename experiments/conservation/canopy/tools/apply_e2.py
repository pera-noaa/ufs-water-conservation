#!/usr/bin/env python3
"""apply_e2.py <ufs-weather-model> : E.2 Noah-MP canopy wetted fraction, gfs_physics_nml noahmp_fwet_opt (default 0).
  0 stock: any canopy ice sets fwet from the ice alone; 1 each phase's fill fraction weighted by its mass;
  2 the larger fill fraction; 3 the phase with more mass (NCAR Noah-MP v5 CanopyHydrologyMod).
Edits precip_heat and canwater (CCPP Noah-MP and, if present, the NOAA-EMC/noahmp copy: setter only, no host plumbing),
noahmpdrv.F90/.meta, GFS_typedefs.F90/.meta. Every anchor must match exactly once (or the stated count)."""
import sys
from pathlib import Path

T = Path(sys.argv[1])
P = T / "UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp"
D = T / "UFSATM/ccpp/data"


def sub(path, old, new, count=1):
    s = path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: anchor found {n}x (want {count}):\n{old[:200]}")
    path.write_text(s.replace(old, new))


FWET_OLD = """      if(canice.gt.0.) then
           fwet = max(0.,canice) / max(maxsno,1.e-06)
      else
           fwet = max(0.,canliq) / max(maxliq,1.e-06)
      endif
      fwet = min(fwet, 1.) ** 0.667
"""
FWET_NEW = """      if(canice.gt.0.) then
           fwet = max(0.,canice) / max(maxsno,1.e-06)
      else
           fwet = max(0.,canliq) / max(maxliq,1.e-06)
      endif
      if (opt_fwt /= 0) fwet = canopy_wetfrac(canliq, canice, maxliq, maxsno)  ! trace ice does not hide the liquid
      fwet = min(fwet, 1.) ** 0.667
"""
FUNC = """
  !> canopy wetted fraction rule (gfs_physics_nml noahmp_fwet_opt); 0 = stock: any ice sets fwet from the ice alone
  subroutine noahmp_options_fwet(fwt)
    integer, intent(in) :: fwt
    opt_fwt = fwt
  end subroutine noahmp_options_fwet

  !> fill fraction of a canopy holding both phases, before the 0.667 power (opt_fwt 1-3)
  pure function canopy_wetfrac(canliq, canice, maxliq, maxsno) result(fw)
    real (kind=kind_phys), intent(in) :: canliq, canice, maxliq, maxsno
    real (kind=kind_phys) :: fw, wl, wi, fl, fi
    wl = max(0.,canliq)
    wi = max(0.,canice)
    fl = min(wl / max(maxliq,1.e-06), 1.)
    fi = min(wi / max(maxsno,1.e-06), 1.)
    select case (opt_fwt)
    case (1)       ! each phase's fill fraction weighted by its share of the canopy water
      fw = 0.
      if (wl + wi > 0.) fw = (wl*fl + wi*fi) / (wl + wi)
    case (2)       ! the larger fill fraction
      fw = max(fl, fi)
    case default   ! 3: the phase with more mass (NCAR Noah-MP v5 CanopyHydrologyMod)
      fw = fl
      if (wi > 0. .and. wi >= wl) fw = fi
    end select
  end function canopy_wetfrac
"""


def lsm(path, ccpp):
    if ccpp:
        sub(path, "  logical, save :: opt_adv = .false.  ! soil water moved between layers carries its sensible heat\n",
            "  logical, save :: opt_adv = .false.  ! soil water moved between layers carries its sensible heat\n"
            "  integer, save :: opt_fwt = 0        ! canopy wetted fraction rule (noahmp_options_fwet)\n")
        sub(path, "  public  :: noahmp_options_energy\n",
            "  public  :: noahmp_options_energy\n  public  :: noahmp_options_fwet\n")
        sub(path, "  end subroutine noahmp_options_energy\n", "  end subroutine noahmp_options_energy\n" + FUNC)
    else:  # NOAA-EMC/noahmp: module default 0; a land-component host sets it with noahmp_options_fwet
        sub(path, "  public  :: noahmp_sflx\n", "  public  :: noahmp_sflx\n  public  :: noahmp_options_fwet\n")
        sub(path, "  public  :: psi_init\n",
            "  public  :: psi_init\n  integer, save :: opt_fwt = 0        ! canopy wetted fraction rule (noahmp_options_fwet)\n")
        s = path.read_text()
        a = "contains\n"
        i = s.index(a)
        path.write_text(s[:i + len(a)] + FUNC + s[i + len(a):])
    sub(path, FWET_OLD, FWET_NEW, 2)


lsm(P / "module_sf_noahmplsm.F90", True)
emc = T / "NOAHMP-interface/noahmp/src/module_sf_noahmplsm.F90"
if emc.exists():
    lsm(emc, False)

drv = P / "noahmpdrv.F90"
if drv.read_text().count("      hflx_evap_enth, con_cliq, con_cvap, con_t0c                                &\n") == 1:
    sub(drv, "      hflx_evap_enth, con_cliq, con_cvap, con_t0c                                &\n",
        "      hflx_evap_enth, con_cliq, con_cvap, con_t0c, noahmp_fwet_opt               &\n")
else:  # other trees (ensfc2 round 4) carry more arguments after con_t0c
    sub(drv, "      hflx_evap_enth, con_cliq, con_cvap, con_t0c,",
        "      hflx_evap_enth, noahmp_fwet_opt, con_cliq, con_cvap, con_t0c,")
sub(drv, "  integer, optional, intent(in) :: noahmp_canopy_heat\n",
    "  integer, optional, intent(in) :: noahmp_canopy_heat\n"
    "  integer, optional, intent(in) :: noahmp_fwet_opt  ! canopy wetted fraction rule (0 stock)\n")
sub(drv, "  call noahmp_options_energy(opt_cnh_d, kir_d, adv_d, con_cliq, con_cvap, con_t0c)\n",
    "  call noahmp_options_energy(opt_cnh_d, kir_d, adv_d, con_cliq, con_cvap, con_t0c)\n"
    "  if (present(noahmp_fwet_opt)) then\n    call noahmp_options_fwet(noahmp_fwet_opt)\n"
    "  else\n    call noahmp_options_fwet(0)\n  endif\n")
meta = P / "noahmpdrv.meta"
s = meta.read_text()
tail = "[con_t0c]\n  standard_name = temperature_at_zero_celsius\n"
if s.rfind("[ccpp-arg-table]\n  name = noahmpdrv_run") < 0 or s.rfind("[ccpp-arg-table]") != s.rfind("[ccpp-arg-table]\n  name = noahmpdrv_run"):
    sys.exit("ABORT noahmpdrv.meta: the last table is not noahmpdrv_run")
meta.write_text(s.rstrip("\n") + "\n[noahmp_fwet_opt]\n  standard_name = control_for_noahmp_canopy_wetted_fraction\n"
                "  long_name = Noah-MP canopy wetted fraction rule\n  units = index\n  dimensions = ()\n"
                "  type = integer\n  intent = in\n  optional = True\n")

td = D / "GFS_typedefs.F90"
sub(td, "    integer              :: noahmp_canopy_heat !",
    "    integer              :: noahmp_fwet_opt    !< Noah-MP canopy wetted fraction: 0 stock, 1 mass-weighted, 2 larger, 3 dominant phase\n"
    "    integer              :: noahmp_canopy_heat !")
sub(td, "    integer              :: noahmp_canopy_heat = 0\n",
    "    integer              :: noahmp_canopy_heat = 0\n    integer              :: noahmp_fwet_opt    = 0\n")
sub(td, "                               noahmp_kirchhoff,                                            &\n",
    "                               noahmp_kirchhoff, noahmp_fwet_opt,                           &\n")
sub(td, "    Model%noahmp_kirchhoff = noahmp_kirchhoff\n",
    "    Model%noahmp_kirchhoff = noahmp_kirchhoff\n    Model%noahmp_fwet_opt = noahmp_fwet_opt\n")
sub(td, "        print *, ' noahmp_kirchhoff : ', Model%noahmp_kirchhoff\n",
    "        print *, ' noahmp_kirchhoff : ', Model%noahmp_kirchhoff\n"
    "        print *, ' noahmp_fwet_opt : ', Model%noahmp_fwet_opt\n")
tm = D / "GFS_typedefs.meta"
sub(tm, "[noahmp_kirchhoff]\n  standard_name = flag_for_noahmp_kirchhoff_consistent_phase_change\n"
        "  long_name = flag: Noah-MP phase change with L_f(T) consistent with its heat capacities\n"
        "  units = flag\n  dimensions = ()\n  type = logical\n",
    "[noahmp_kirchhoff]\n  standard_name = flag_for_noahmp_kirchhoff_consistent_phase_change\n"
    "  long_name = flag: Noah-MP phase change with L_f(T) consistent with its heat capacities\n"
    "  units = flag\n  dimensions = ()\n  type = logical\n"
    "[noahmp_fwet_opt]\n  standard_name = control_for_noahmp_canopy_wetted_fraction\n"
    "  long_name = Noah-MP canopy wetted fraction rule\n  units = index\n  dimensions = ()\n  type = integer\n")
print("E2 applied", T)
