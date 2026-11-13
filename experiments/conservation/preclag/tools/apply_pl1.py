#!/usr/bin/env python3
"""apply_pl1.py <ufs-weather-model> : PL1 (sfc_precip_t1_carry). The surfaces book step N's precipitation (tprcp,
srflag, used at step N+1) at the lowest-layer T the atmosphere exported it at, T1(N) = Statein%tgrs(:,1) of step N,
instead of step N+1's T1. GFS_MP_generic_post stores T1(N) in Sfcprop%tprcp_t1 with tprcp; Noah-MP soil and glacier
and sfc_sice use it in their EP1 (sfc_precip_enthalpy) precipitation enthalpy; phy_data restart carries it.
Default off; off passes the step's own T1, i.e. the same values as before. Every anchor must match exactly once."""
import sys
import pathlib

W = pathlib.Path(sys.argv[1]) / "UFSATM/ccpp"
NE = "physics/physics/Interstitials/UFS_SCM_NEPTUNE"
NM = "physics/physics/SFC_Models/Land/Noahmp"
SI = "physics/physics/SFC_Models/SeaIce/CICE"
edits = {}


def rep(rel, old, new):
    edits.setdefault(rel, []).append((old, new))


def app(rel, text):
    edits.setdefault(rel, []).append((None, text))


FLAG_META = """[sfc_precip_t1_carry]
  standard_name = flag_for_surface_precipitation_at_fallout_temperature
  long_name = flag: surfaces book precipitation at the lowest-layer T of the step it fell
  units = flag
  dimensions = ()
  type = logical
  intent = in
  optional = True
"""
FIELD_META = """[tprcp_t1]
  standard_name = air_temperature_at_surface_adjacent_layer_at_precipitation_fallout
  long_name = lowest-layer T at the start of the physics step whose precipitation tprcp holds
  units = K
  dimensions = (horizontal_loop_extent)
  type = real
  kind = kind_phys
  intent = {intent}
  optional = True
"""

# ---- GFS_typedefs
T = "data/GFS_typedefs.F90"
rep(T, "    real (kind=kind_phys), pointer :: srflag (:)   => null()  !< sfc_fld%srflag - snow/rain flag for precipitation\n",
    "    real (kind=kind_phys), pointer :: srflag (:)   => null()  !< sfc_fld%srflag - snow/rain flag for precipitation\n"
    "    real (kind=kind_phys), pointer :: tprcp_t1 (:) => null()  !< lowest-layer T of the step tprcp fell in (pl1)\n")
rep(T, "    allocate (Sfcprop%srflag (IM))\n", "    allocate (Sfcprop%srflag (IM))\n    allocate (Sfcprop%tprcp_t1 (IM))\n")
rep(T, "    Sfcprop%srflag = clear_val\n", "    Sfcprop%srflag = clear_val\n    Sfcprop%tprcp_t1 = clear_val\n")
rep(T, "    logical              :: noahmp_pore_air    !< flag: Noah-MP soil pores keep the air heat when water moves\n",
    "    logical              :: noahmp_pore_air    !< flag: Noah-MP soil pores keep the air heat when water moves\n"
    "    logical              :: sfc_precip_t1_carry !< flag: surfaces book precipitation at the T1 of the step it fell (pl1)\n")
rep(T, "    logical              :: noahmp_pore_air    = .false.\n",
    "    logical              :: noahmp_pore_air    = .false.\n    logical              :: sfc_precip_t1_carry = .false.\n")
rep(T, "                               sfc_precip_enthalpy, lw_sfc_return, noahmp_pore_air,         &\n",
    "                               sfc_precip_enthalpy, lw_sfc_return, noahmp_pore_air,         &\n"
    "                               sfc_precip_t1_carry,                                         &\n")
rep(T, "    Model%noahmp_pore_air = noahmp_pore_air\n",
    "    Model%noahmp_pore_air = noahmp_pore_air\n    Model%sfc_precip_t1_carry = sfc_precip_t1_carry\n")
rep(T, "        print *, ' noahmp_pore_air : ', Model%noahmp_pore_air\n",
    "        print *, ' noahmp_pore_air : ', Model%noahmp_pore_air\n"
    "        print *, ' sfc_precip_t1_carry : ', Model%sfc_precip_t1_carry\n")
T = "data/GFS_typedefs.meta"
rep(T, "[srflag]\n  standard_name = precipitation_type\n",
    FIELD_META.replace("horizontal_loop_extent", "horizontal_dimension").replace("  intent = {intent}\n  optional = True\n", "")
    + "[srflag]\n  standard_name = precipitation_type\n")
rep(T, "[noahmp_fwet_opt]\n  standard_name = control_for_noahmp_canopy_wetted_fraction\n",
    FLAG_META.replace("  intent = in\n  optional = True\n", "")
    + "[noahmp_fwet_opt]\n  standard_name = control_for_noahmp_canopy_wetted_fraction\n")

# ---- phy_data restart
T = "driver/GFS_restart.F90"
rep(T, "    if (Model%rrfs_sd) then\n       num2d = num2d + 6\n    endif\n",
    "    if (Model%rrfs_sd) then\n       num2d = num2d + 6\n    endif\n"
    "    if (Model%sfc_precip_t1_carry) then\n       num2d = num2d + 1\n    endif\n")
rep(T, "      Restart(idx)%data%var2 => Coupling%rrfs_hwp_ave(:)\n    endif\n",
    "      Restart(idx)%data%var2 => Coupling%rrfs_hwp_ave(:)\n    endif\n"
    "    ! pl1: T1 of the step whose precipitation tprcp holds\n"
    "    if (Model%sfc_precip_t1_carry) then\n"
    "      idx = idx + 1\n"
    "      Restart(idx)%name = 'sfc_precip_t1'\n"
    "      Restart(idx)%axes = 2\n"
    "      Restart(idx)%data%var2 => Sfcprop%tprcp_t1(:)\n"
    "    endif\n")

# ---- GFS_MP_generic_post: store T1(N) with tprcp
T = f"{NE}/GFS_MP_generic_post.F90"
rep(T, "precip_phase_host, con_hfus, con_cp, sfc_precip_enthalpy, con_cliq, tgrs)\n",
    "precip_phase_host, con_hfus, con_cp, sfc_precip_enthalpy, con_cliq, tgrs, &\n"
    "        sfc_precip_t1_carry, tprcp_t1)\n")
rep(T, "      real(kind=kind_phys)                                   :: lfph\n",
    "      real(kind=kind_phys)                                   :: lfph\n"
    "      logical, optional,                       intent(in)    :: sfc_precip_t1_carry\n"
    "      real(kind=kind_phys), dimension(:), optional, intent(inout) :: tprcp_t1\n")
rep(T, "      if_save_fields: if (lssav) then\n",
    "      ! pl1: the surfaces book tprcp next step at the T1 it left the atmosphere at\n"
    "      if (present(sfc_precip_t1_carry) .and. present(tprcp_t1) .and. present(tgrs)) then\n"
    "        if (sfc_precip_t1_carry) then\n"
    "          do i = 1, im\n"
    "            tprcp_t1(i) = tgrs(i,1)\n"
    "          enddo\n"
    "        endif\n"
    "      endif\n\n"
    "      if_save_fields: if (lssav) then\n")
app(f"{NE}/GFS_MP_generic_post.meta", FLAG_META + FIELD_META.format(intent="inout"))

# ---- Noah-MP driver
T = f"{NM}/noahmpdrv.F90"
rep(T, "      sfc_precip_enthalpy, lw_sfc_return, noahmp_pore_air, ulw_lnd_rad, sfcdlw_rad &\n",
    "      sfc_precip_enthalpy, lw_sfc_return, noahmp_pore_air, ulw_lnd_rad, sfcdlw_rad, &\n"
    "      sfc_precip_t1_carry, tprcp_t1                                               &\n")
rep(T, "  real(kind=kind_phys) :: lwref\n",
    "  real(kind=kind_phys) :: lwref\n"
    "  logical, optional, intent(in) :: sfc_precip_t1_carry\n"
    "  real(kind=kind_phys), dimension(:), optional, intent(in) :: tprcp_t1\n"
    "  logical :: ptc\n"
    "  real(kind=kind_phys) :: tpr\n")
rep(T, "  call noahmp_options_energy2(epd, aird, 1972.0_kind_phys)   ! FV3's c_ice (frame F)\n",
    "  call noahmp_options_energy2(epd, aird, 1972.0_kind_phys)   ! FV3's c_ice (frame F)\n"
    "  ptc = .false.\n"
    "  if (present(sfc_precip_t1_carry)) ptc = sfc_precip_t1_carry .and. present(tprcp_t1)\n")
rep(T, "      hev = 0.\n      lwref = -1.e20\n",
    "      hev = 0.\n"
    "      tpr = temperature_forcing   ! pl1: precipitation temperature\n"
    "      if (ptc) then\n"
    "        if (tprcp_t1(i) > 0.) tpr = tprcp_t1(i)\n"
    "      endif\n"
    "      lwref = -1.e20\n")
rep(T, "          lwnet_ref=lwref, hevap=hev)\n", "          lwnet_ref=lwref, hevap=hev, tprec=tpr)\n")
rep(T, "          fpcv_host=fpcvh, sw_target=swt, hevap=hev, lwnet_ref=lwref)\n",
    "          fpcv_host=fpcvh, sw_target=swt, hevap=hev, lwnet_ref=lwref, tprec=tpr)\n")
app(f"{NM}/noahmpdrv.meta", FLAG_META + FIELD_META.format(intent="in"))

# ---- Noah-MP soil
T = f"{NM}/module_sf_noahmplsm.F90"
rep(T, "                   ,errmsg, errflg, fpcv_host, sw_target, hevap, lwnet_ref, hprec_out, hlw_out)\n",
    "                   ,errmsg, errflg, fpcv_host, sw_target, hevap, lwnet_ref, hprec_out, hlw_out, tprec)\n")
rep(T, "  real (kind=kind_phys), optional, intent(out) :: hlw_out   !< lw2 heat kept by the top layer (j/m2)\n",
    "  real (kind=kind_phys), optional, intent(out) :: hlw_out   !< lw2 heat kept by the top layer (j/m2)\n"
    "  real (kind=kind_phys), optional, intent(in)  :: tprec     !< precipitation temperature (k), pl1\n"
    "  real (kind=kind_phys)              :: tprc\n")
rep(T, "     dqp = 0.\n     if (opt_ep) then\n"
       "        dqp = (rain*cl_f*(sfctmp - tfrz) + snow*(ci_f*(sfctmp - t0_f) - cl_f*(tfrz - t0_f)) - pah)*dt - hprec\n",
    "     dqp = 0.\n     if (opt_ep) then\n"
    "        tprc = sfctmp\n"
    "        if (present(tprec)) tprc = tprec\n"
    "        dqp = (rain*cl_f*(tprc - tfrz) + snow*(ci_f*(tprc - t0_f) - cl_f*(tfrz - t0_f)) - pah)*dt - hprec\n")

# ---- Noah-MP glacier
T = f"{NM}/module_sf_noahmp_glacier.F90"
rep(T, "errmsg    ,errflg, fpice_host, sw_target, lwnet_ref, hevap, hprec_out, hlw_out) \n",
    "errmsg    ,errflg, fpice_host, sw_target, lwnet_ref, hevap, hprec_out, hlw_out, tprec) \n")
rep(T, "  real (kind=kind_phys), optional                 , intent(out)   :: hlw_out    !< lw2 heat kept (j/m2)\n",
    "  real (kind=kind_phys), optional                 , intent(out)   :: hlw_out    !< lw2 heat kept (j/m2)\n"
    "  real (kind=kind_phys), optional                 , intent(in)    :: tprec      !< precipitation temperature (k), pl1\n"
    "  real (kind=kind_phys)                                           :: tprc\n")
rep(T, "     if (opt_ep_gla) then\n"
       "        dqp = (prcp*(1.-fpice)*cl_f_gla*(sfctmp - tfrz) &\n"
       "            + prcp*fpice*(ci_f_gla*(sfctmp - t0_f_gla) - cl_f_gla*(tfrz - t0_f_gla)))*dt - hprg\n",
    "     if (opt_ep_gla) then\n"
    "        tprc = sfctmp\n"
    "        if (present(tprec)) tprc = tprec\n"
    "        dqp = (prcp*(1.-fpice)*cl_f_gla*(tprc - tfrz) &\n"
    "            + prcp*fpice*(ci_f_gla*(tprc - t0_f_gla) - cl_f_gla*(tfrz - t0_f_gla)))*dt - hprg\n")

# ---- sea ice
T = f"{SI}/sfc_sice.f"
rep(T, "     &       adjsfculw_ice, sfc_precip_enthalpy, con_hfus, con_cliq\n",
    "     &       adjsfculw_ice, sfc_precip_enthalpy, con_hfus, con_cliq,\n"
    "     &       sfc_precip_t1_carry, tprcp_t1\n")
rep(T, "      real (kind=kind_phys) :: snowm(im), dqp, e1, e1x, b1x, tc1\n",
    "      real (kind=kind_phys) :: snowm(im), dqp, e1, e1x, b1x, tc1\n"
    "      logical, optional, intent(in) :: sfc_precip_t1_carry\n"
    "      real (kind=kind_phys), optional, intent(in) :: tprcp_t1(:)\n"
    "      real (kind=kind_phys) :: tprc\n")
rep(T, "          dqp = snowm(i)*(1972.0_kind_phys*(t1(i) - t0c) - con_hfus\n",
    "          tprc = t1(i)\n"
    "          if (present(sfc_precip_t1_carry) .and. present(tprcp_t1)) then\n"
    "            if (sfc_precip_t1_carry .and. tprcp_t1(i) > zero)\n"
    "     &        tprc = tprcp_t1(i)\n"
    "          endif\n"
    "          dqp = snowm(i)*(1972.0_kind_phys*(tprc - t0c) - con_hfus\n")
app(f"{SI}/sfc_sice.meta", FLAG_META + FIELD_META.format(intent="in"))

out = {}
for rel, ops in edits.items():
    p = W / rel
    assert p.exists() and not p.is_symlink(), p
    s = p.read_text()
    for old, new in ops:
        if old is None:
            s = s.rstrip("\n") + "\n" + new
            continue
        n = s.count(old)
        assert n == 1, (rel, n, old[:80])
        s = s.replace(old, new)
        if rel.endswith(".f"):
            for ln in new.split("\n"):
                assert ln[:1] in ("!", "c", "C") or len(ln) <= 72, ln
    out[p] = (rel, len(ops), s)
for p, (rel, n, s) in out.items():
    p.write_text(s)
    print("edited", rel, n)
