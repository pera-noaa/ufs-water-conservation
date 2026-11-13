#!/usr/bin/env python3
"""Candidate energy fixes, applied by anchor substitution to a ufs-weather-model tree.
Usage: apply_fixes.py <ufs-weather-model> <fix id> [<fix id> ...]
  FX1  fv_mapz consv_te fixer: weight zsum1 by the heat capacity the correction is applied with
  SG1  fv_subgrid_z (non-hydrostatic): relax total energy te, not T, so the 2dz filter conserves it
  CP1  atmosphere_state_update: physics heating is per physics mass (prsi difference); scale t_dt to the new delp
  R1   dcyc2t3: radiative heating rates (per mass at the radiation call) rescaled to the current layer mass
  D7   fv_core_nml cpl_ke_heating (default .false.): heat, per D-grid cell, the KE the A-grid wind increments
       (fv_subgrid_z + physics) imply minus the KE their D-grid mapping realises
  D7S  fv_core_nml cpl_ke_smooth (default 0): passes of a conservative 5-point smoother applied to the D7 heating
       (per-area energy, flux form, exact global conservation) before it is applied; needs D7
  S1K  samf_kirchhoff (encpl S1) made exact in frame F: L at the step-initial T (tgrs) and the ice part of detrained
       condensate at L_f(T) (adds (c_l - c_i)(T - T0) to D3A's constant hfus)
  TFH  gfs_physics_nml thompson_frame_heat (default .false.): Thompson's heating replaced, per layer, by the frame-F latent
       heat of its net phase change (from its water budget and exported precipitation fluxes) at the step-initial T
  PBK  gfs_physics_nml pbl_kirchhoff (default .false.): satmedmfvdifq's condensate filler (vapour <-> cloud/rain water)
       at FV3's L_h(T) (T = PBL input = step-initial T) instead of hvap
  TH8  Thompson: count all sedimented mass at the surface (the R1*rr_min condition dropped precipitation whose mass had
       already left the lowest layer: a water leak, 6.6e-12 kg m-2 s-1, -5.6e-6 W m-2 in frame F)
  PBF  (with pbl_kirchhoff) satmedmfvdifq exports its liquid/ice condensate transport fluxes (Stateout pflx_pbll/pbli;
       filler phase change excluded) and cpl_water_energy bit 4 uses them (c_l/c_i by direction) instead of cp_v
  C8   cpl_water_energy bit 8 (on top of encpl 04/06): heat -dm*(KE_D + w^2/2) where the write adds/removes water mass
Every anchor must match the stated number of times; nothing is written unless all match."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/fv3/atmos_cubed_sphere/model"
ccpp = Path(sys.argv[1]) / "UFSATM/ccpp"
edits = {}


def suball(path, old, new):
    s = edits.get(path) or path.read_text()
    if s.count(old) < 1:
        sys.exit(f"ABORT {path.name}: no match: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


def sub(path, old, new, count=1, which=None):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    if which is None:
        edits[path] = s.replace(old, new)
    else:  # replace only occurrence number `which` (0-based)
        parts = s.split(old)
        edits[path] = old.join(parts[:which + 1]) + new + old.join(parts[which + 1:])


def fx1():
    p = root / "fv_mapz.F90"
    old = ("               zsum1(i,j) = zsum1(i,j) + pkz(i,j,k)*delp(i,j,k)\n"
           "            enddo\n         enddo\n         if ( hydrostatic ) then\n")
    new = ("               zsum1(i,j) = zsum1(i,j) + pkz(i,j,k)*delp(i,j,k)\n"
           "            enddo\n         enddo\n"
           "#if defined(MOIST_CAPPA) && defined(USE_COND) && !defined(MULTI_GASES)\n"
           "         if ( .not. hydrostatic ) then\n"
           "! weight as the correction is applied: pt+dtmp*pkz is divided by (1+r_vir*qv)*(1-qc) and heats cvm\n"
           "            do i=is,ie\n               zsum1(i,j) = 0.\n            enddo\n"
           "            do k=1,km\n"
           "               call moist_cv(is,ie,isd,ied,jsd,jed, km, j, k, nwat, sphum, liq_wat, rainwat,    &\n"
           "                             ice_wat, snowwat, graupel, hailwat, q, gz, cvm)\n"
           "               do i=is,ie\n"
           "                  zsum1(i,j) = zsum1(i,j) + cvm(i)*pkz(i,j,k)*delp(i,j,k)   &\n"
           "                             / (cv_air*(1.+r_vir*q(i,j,k,sphum))*(1.-gz(i)))\n"
           "               enddo\n            enddo\n         endif\n#endif\n"
           "         if ( hydrostatic ) then\n")
    sub(p, old, new, count=2, which=0)


def sg1():
    p = root / "fv_sg.F90"
    # keep the pre-mixing total energy of each layer (non-hydrostatic branch of the GFS_PHYS version)
    sub(p, "      real, dimension(is:ie,km):: u0, v0, w0, t0, hd, te, gz, tvm, pm, den\n",
        "      real, dimension(is:ie,km):: u0, v0, w0, t0, hd, te, gz, tvm, pm, den, te1\n", count=2, which=0)
    sub(p, "             hd(i,k) = cpm(i)*t0(i,k) + tmp\n             te(i,k) = cvm(i)*t0(i,k) + tmp\n",
        "             hd(i,k) = cpm(i)*t0(i,k) + tmp\n             te(i,k) = cvm(i)*t0(i,k) + tmp\n"
        "            te1(i,k) = te(i,k)\n", count=2, which=0)
    sub(p, "      real ri_ref, ri, pt1, pt2, ratio, tv, cv, tmp, q_liq, q_sol\n",
        "      real ri_ref, ri, pt1, pt2, ratio, tv, cv, tmp, q_liq, q_sol, cvx\n", count=2, which=0)
    sub(p, "!$OMP                                  tv,gz,hd,te,ratio,pt1,pt2,tv1,tv2,ri_ref, ri,mc,km1)\n",
        "!$OMP                                  tv,gz,hd,te,ratio,pt1,pt2,tv1,tv2,ri_ref, ri,mc,km1,te1,cvx)\n", count=2, which=0)
    # relax te with the other fields and diagnose T from it (heat capacity of the relaxed q)
    old = ("      do iq=1,nq\n         do k=1,kbot\n            do i=is,ie\n"
           "               q0(i,k,iq) = qa(i,j,k,iq) + (q0(i,k,iq) - qa(i,j,k,iq))*fra\n"
           "            enddo\n         enddo\n      enddo\n   endif\n")
    new = old[:-len("   endif\n")] + (
        "      if ( .not. hydrostatic .and. nwat == 6 ) then\n"
        "! T from the relaxed total energy, so the filter conserves cvm*T + gz + KE\n"
        "         do k=1,kbot\n            do i=is,ie\n"
        "               q_liq = q0(i,k,liq_wat) + q0(i,k,rainwat)\n"
        "               q_sol = q0(i,k,ice_wat) + q0(i,k,snowwat) + q0(i,k,graupel)\n"
        "               cvx = (1.-(q0(i,k,sphum)+q_liq+q_sol))*cv_air + q0(i,k,sphum)*cv_vap + q_liq*c_liq + q_sol*c_ice\n"
        "               t0(i,k) = (te1(i,k) + (te(i,k) - te1(i,k))*fra - gz(i,k)     &\n"
        "                       - 0.5*(u0(i,k)**2+v0(i,k)**2+w0(i,k)**2)) / cvx\n"
        "            enddo\n         enddo\n      endif\n   endif\n")
    sub(p, old, new, count=2, which=0)


def cp1():
    p = root.parent / "driver/UFS/atmosphere.F90"
    sub(p, "   real(kind=kind_phys):: rcp, q0, qwat(nq), qt, rdt\n",
        "   real(kind=kind_phys):: rcp, q0, qwat(nq), qt, rdt, qp\n")
    sub(p, "!$OMP             private (nb, blen, i, j, k, k1, ix, im, q0, qwat, qt, tracer_name)\n",
        "!$OMP             private (nb, blen, i, j, k, k1, ix, im, q0, qwat, qt, tracer_name, qp)\n")
    sub(p, "         t_dt(i,j,k1) = t_dt(i,j,k1) + (IPD_Stateout%gt0(im,k) - IPD_Statein%tgrs(im,k)) * rdt\n", "")
    sub(p, "         qwat(1:nq_adv) = q0*IPD_Stateout%gq0(im,k,1:nq_adv)\n",
        "         qwat(1:nq_adv) = q0*IPD_Stateout%gq0(im,k,1:nq_adv)\n         qp = q0\n")
    sub(p, "         Atm(n)%delp(i,j,k1) = q0\n",
        "         Atm(n)%delp(i,j,k1) = q0\n"
        "! physics heated its own layer mass qp (condensate excluded); fv_update_phys heats the new delp\n"
        "         t_dt(i,j,k1) = t_dt(i,j,k1) + (IPD_Stateout%gt0(im,k) - IPD_Statein%tgrs(im,k)) * rdt * qp / q0\n")


def r1():
    td = ccpp / "data/GFS_typedefs.F90"
    sub(td, "    real (kind=kind_phys), pointer :: htrlw (:,:)  => null()  !< hlw  total sky lw heating rate in k/sec\n",
        "    real (kind=kind_phys), pointer :: htrlw (:,:)  => null()  !< hlw  total sky lw heating rate in k/sec\n"
        "    real (kind=kind_phys), pointer :: dpsw  (:,:)  => null()  !< layer pressure thickness at the last sw call (Pa)\n"
        "    real (kind=kind_phys), pointer :: dplw  (:,:)  => null()  !< layer pressure thickness at the last lw call (Pa)\n")
    sub(td, "    allocate (Radtend%htrlw  (IM,Model%levs))\n",
        "    allocate (Radtend%htrlw  (IM,Model%levs))\n    allocate (Radtend%dpsw   (IM,Model%levs))\n"
        "    allocate (Radtend%dplw   (IM,Model%levs))\n")
    sub(td, "    Radtend%htrlw  = clear_val\n",
        "    Radtend%htrlw  = clear_val\n    Radtend%dpsw   = clear_val\n    Radtend%dplw   = clear_val\n")
    tm = ccpp / "data/GFS_typedefs.meta"
    old = ("[htrlw]\n  standard_name = tendency_of_air_temperature_due_to_longwave_heating_on_radiation_timestep\n"
           "  long_name = total sky lw heating rate\n  units = K s-1\n"
           "  dimensions = (horizontal_dimension,vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n")
    new = old + "".join(
        f"[{n}]\n  standard_name = air_pressure_difference_between_interfaces_on_{w}_radiation_timestep\n"
        f"  long_name = layer pressure thickness at the last {w} radiation call\n  units = Pa\n"
        "  dimensions = (horizontal_dimension,vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n"
        for n, w in (("dpsw", "sw"), ("dplw", "lw")))
    sub(tm, old, new)
    f = ccpp / "physics/physics/Interstitials/UFS_SCM_NEPTUNE/dcyc2t3.f"
    sub(f, "     &       ten_v, ten_q, errmsg,errflg)\n",
        "     &       ten_v, ten_q, lsswr, lslwr, dpsw, dplw, errmsg,errflg)\n")
    sub(f, "      real(kind=kind_phys), dimension(:,:), intent(in) :: p_lev\n",
        "      real(kind=kind_phys), dimension(:,:), intent(in) :: p_lev\n"
        "      logical, intent(in) :: lsswr, lslwr\n"
        "      real(kind=kind_phys), dimension(:,:), intent(inout) :: dpsw, dplw\n"
        "      real(kind=kind_phys) :: wsw(im,levs), wlw(im,levs)\n")
    sub(f, "      ten_q = 0.0\n      \n!     Vertical ordering?\n",
        "      ten_q = 0.0\n"
        "!  heating rates are per layer mass at the radiation call: rescale\n"
        "!  to the current mass so the column gets the flux divergence\n"
        "      do k = 1, levs\n        do i = 1, im\n"
        "          tem1 = abs(p_lev(i,k) - p_lev(i,k+1))\n"
        "          if (lsswr) dpsw(i,k) = tem1\n          if (lslwr) dplw(i,k) = tem1\n"
        "          wsw(i,k) = one\n          wlw(i,k) = one\n"
        "          if (dpsw(i,k) > zero) wsw(i,k) = dpsw(i,k) / tem1\n"
        "          if (dplw(i,k) > zero) wlw(i,k) = dplw(i,k) / tem1\n"
        "        enddo\n      enddo\n      \n!     Vertical ordering?\n")
    sub(f, "               ten_t(i,k) = swh(i,k)*xmu(i) +                           &\n"
           "     &              htrlw(i,k)*lfnc + (1.-lfnc)*hlw(i,k)\n",
        "               ten_t(i,k) = swh(i,k)*xmu(i)*wsw(i,k) +                  &\n"
        "     &              htrlw(i,k)*lfnc + (1.-lfnc)*hlw(i,k)*wlw(i,k)\n")
    sub(f, "               ten_t(i,k)  = swh(i,k)*xmu(i)  + hlw(i,k)\n",
        "               ten_t(i,k)  = swh(i,k)*xmu(i)*wsw(i,k)                   &\n"
        "     &                     + hlw(i,k)*wlw(i,k)\n")
    sub(f, "     &                               swh(i,k)*xmu(i))*deltim\n",
        "     &                               swh(i,k)*xmu(i)*wsw(i,k))*deltim\n")
    sub(f, "            dtend(:,:,idtend) = dtend(:,:,idtend) + hlw(:,:)*deltim\n",
        "            dtend(:,:,idtend) = dtend(:,:,idtend)                       &\n"
        "     &                          + hlw(:,:)*wlw(:,:)*deltim\n")
    sub(f, "     &                               + swh(i,k)*xmu(i)*deltim\n",
        "     &                               + swh(i,k)*xmu(i)*wsw(i,k)*deltim\n")
    m = ccpp / "physics/physics/Interstitials/UFS_SCM_NEPTUNE/dcyc2t3.meta"
    old = "[errmsg]\n"
    new = ("[lsswr]\n  standard_name = flag_for_calling_shortwave_radiation\n  long_name = logical flags for sw radiation calls\n"
           "  units = flag\n  dimensions = ()\n  type = logical\n  intent = in\n"
           "[lslwr]\n  standard_name = flag_for_calling_longwave_radiation\n  long_name = logical flags for lw radiation calls\n"
           "  units = flag\n  dimensions = ()\n  type = logical\n  intent = in\n"
           + "".join(f"[{n}]\n  standard_name = air_pressure_difference_between_interfaces_on_{w}_radiation_timestep\n"
                     f"  long_name = layer pressure thickness at the last {w} radiation call\n  units = Pa\n"
                     "  dimensions = (horizontal_loop_extent,vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n"
                     "  intent = inout\n" for n, w in (("dpsw", "sw"), ("dplw", "lw")))
           + "[errmsg]\n")
    sub(m, old, new, count=s_count(m, old), which=0)


def s_count(path, old):
    return (edits.get(path) or path.read_text()).count(old)


def d7():
    m = root
    sub(m / "fv_arrays.F90", "   real    :: consv_te = 0.   !< Fraction of total energy lost during the adiabatic integration\n",
        "   real    :: consv_te = 0.   !< Fraction of total energy lost during the adiabatic integration\n"
        "   logical :: cpl_ke_heating = .false. !< heat the KE mismatch of the A- to D-grid wind-increment mapping\n")
    c = m / "fv_control.F90"
    sub(c, "     real    , pointer :: consv_te\n", "     real    , pointer :: consv_te\n     logical , pointer :: cpl_ke_heating\n")
    sub(c, "       consv_te                      => Atm%flagstruct%consv_te\n",
        "       consv_te                      => Atm%flagstruct%consv_te\n"
        "       cpl_ke_heating                => Atm%flagstruct%cpl_ke_heating\n")
    sub(c, "            pass_full_omega_to_physics_in_non_hydrostatic_mode, ignore_rst_cksum\n",
        "            pass_full_omega_to_physics_in_non_hydrostatic_mode, ignore_rst_cksum, cpl_ke_heating\n")
    a = root.parent / "driver/UFS/atmosphere.F90"
    sub(a, "use fv_sg_mod,          only: fv_subgrid_z\n",
        "use fv_sg_mod,          only: fv_subgrid_z\nuse fv_mapz_mod,        only: moist_cp, moist_cv\n")
    sub(a, "  real, allocatable, dimension(:,:,:)   :: u_dt, v_dt, t_dt, qv_dt\n",
        "  real, allocatable, dimension(:,:,:)   :: u_dt, v_dt, t_dt, qv_dt\n"
        "  real, allocatable, dimension(:,:,:)   :: ke_tgt  ! cpl_ke_heating: KE (J/kg x Pa) the increments imply\n")
    sub(a, "   real(kind=kind_phys):: rcp, q0, qwat(nq), qt, rdt, qp\n",
        "   real(kind=kind_phys):: rcp, q0, qwat(nq), qt, rdt, qp\n"
        "   real(kind=kind_phys):: ub, vb, ua0, va0, dpp\n"
        "   real, allocatable :: ked0(:,:,:)\n   real :: ked1, dte, tnew, cxm(isc:iec), qcx(isc:iec)\n")
    sub(a, "!$OMP             private (nb, blen, i, j, k, k1, ix, im, q0, qwat, qt, tracer_name, qp)\n",
        "!$OMP             private (nb, blen, i, j, k, k1, ix, im, q0, qwat, qt, tracer_name, qp, ub, vb, ua0, va0, dpp)\n")
    sub(a, "!$OMP                      snowwat, graupel, nq_adv, flip_vc)   &\n",
        "!$OMP                      snowwat, graupel, nq_adv, flip_vc, ke_tgt, dt_atmos)   &\n")
    sub(a, "!--- put u/v tendencies into haloed arrays u_dt and v_dt\n",
        "   if (Atm(n)%flagstruct%cpl_ke_heating .and. .not. allocated(ke_tgt)) allocate(ke_tgt(isc:iec,jsc:jec,npz))\n"
        "!--- put u/v tendencies into haloed arrays u_dt and v_dt\n")
    sub(a, "         u_dt(i,j,k1) = u_dt(i,j,k1) + (IPD_Stateout%gu0(im,k) - IPD_Statein%ugrs(im,k)) * rdt\n",
        "         if (Atm(n)%flagstruct%cpl_ke_heating) then\n"
        "! KE change the A-grid increments imply: fv_subgrid_z part (already in u_dt) on the old delp, physics part on its own mass\n"
        "           ub = IPD_Statein%ugrs(im,k)\n           vb = IPD_Statein%vgrs(im,k)\n"
        "           ua0 = ub - dt_atmos*u_dt(i,j,k1)\n           va0 = vb - dt_atmos*v_dt(i,j,k1)\n"
        "           if (flip_vc) then\n             dpp = IPD_Statein%prsi(im,k) - IPD_Statein%prsi(im,k+1)\n"
        "           else\n             dpp = IPD_Statein%prsi(im,k+1) - IPD_Statein%prsi(im,k)\n           endif\n"
        "           ke_tgt(i,j,k1) = 0.5*(ub**2 + vb**2 - ua0**2 - va0**2)*Atm(n)%delp(i,j,k1)            &\n"
        "                          + 0.5*(IPD_Stateout%gu0(im,k)**2 + IPD_Stateout%gv0(im,k)**2 - ub**2 - vb**2)*dpp\n"
        "         endif\n"
        "         u_dt(i,j,k1) = u_dt(i,j,k1) + (IPD_Stateout%gu0(im,k) - IPD_Statein%ugrs(im,k)) * rdt\n")
    kd = ("0.25*Atm(n)%gridstruct%rsin2(i,j)*(Atm(n)%u(i,j,k)**2 + Atm(n)%u(i,j+1,k)**2 + Atm(n)%v(i,j,k)**2 &\n"
          "                   + Atm(n)%v(i+1,j,k)**2 - (Atm(n)%u(i,j,k) + Atm(n)%u(i,j+1,k))*(Atm(n)%v(i,j,k) &\n"
          "                   + Atm(n)%v(i+1,j,k))*Atm(n)%gridstruct%cosa_s(i,j))")
    sub(a, "       call timing_on('FV_UPDATE_PHYS')\n    call fv_update_phys( dt_atmos, isc, iec, jsc, jec, isd, ied, jsd, jed, Atm(n)%ng, nt_dyn, &\n",
        "       call timing_on('FV_UPDATE_PHYS')\n"
        "    if (Atm(n)%flagstruct%cpl_ke_heating) then\n"
        "      allocate(ked0(isc:iec,jsc:jec,npz))\n"
        "      do k=1,npz\n        do j=jsc,jec\n          do i=isc,iec\n"
        "            ked0(i,j,k) = " + kd + "\n"
        "          enddo\n        enddo\n      enddo\n    endif\n"
        "    call fv_update_phys( dt_atmos, isc, iec, jsc, jec, isd, ied, jsd, jed, Atm(n)%ng, nt_dyn, &\n")
    sub(a, "                         Atm(n)%phys_diag, Atm(n)%nudge_diag )\n       call timing_off('FV_UPDATE_PHYS')\n",
        "                         Atm(n)%phys_diag, Atm(n)%nudge_diag )\n"
        "    if (Atm(n)%flagstruct%cpl_ke_heating) then\n"
        "! heat (per cell, as fv_update_phys heats) the implied minus the realised D-grid KE change\n"
        "      do k=1,npz\n        do j=jsc,jec\n"
        "          if (Atm(n)%flagstruct%hydrostatic .or. Atm(n)%flagstruct%phys_hydrostatic) then\n"
        "            call moist_cp(isc,iec,isd,ied,jsd,jed, npz, j, k, nwat, sphum, liq_wat, rainwat,    &\n"
        "                          ice_wat, snowwat, graupel, hailwat, Atm(n)%q, qcx, cxm, Atm(n)%pt(isc:iec,j,k))\n"
        "          else\n"
        "            call moist_cv(isc,iec,isd,ied,jsd,jed, npz, j, k, nwat, sphum, liq_wat, rainwat,    &\n"
        "                          ice_wat, snowwat, graupel, hailwat, Atm(n)%q, qcx, cxm, Atm(n)%pt(isc:iec,j,k))\n"
        "          endif\n"
        "          do i=isc,iec\n"
        "            ked1 = " + kd + "\n"
        "            dte = ke_tgt(i,j,k)/Atm(n)%delp(i,j,k) - (ked1 - ked0(i,j,k))\n"
        "            tnew = Atm(n)%pt(i,j,k) + dte/cxm(i)\n"
        "            if (.not. Atm(n)%flagstruct%hydrostatic .and. Atm(n)%flagstruct%phys_hydrostatic) &\n"
        "                 Atm(n)%delz(i,j,k) = Atm(n)%delz(i,j,k)*tnew/Atm(n)%pt(i,j,k)\n"
        "            Atm(n)%pt(i,j,k) = tnew\n"
        "          enddo\n        enddo\n      enddo\n      deallocate(ked0)\n    endif\n"
        "       call timing_off('FV_UPDATE_PHYS')\n")


def d7s():
    m = root
    sub(m / "fv_arrays.F90", "   logical :: cpl_ke_heating = .false. !< heat the KE mismatch of the A- to D-grid wind-increment mapping\n",
        "   logical :: cpl_ke_heating = .false. !< heat the KE mismatch of the A- to D-grid wind-increment mapping\n"
        "   integer :: cpl_ke_smooth = 0  !< passes of a conservative 5-point smoother on that heating (0: per cell)\n")
    c = m / "fv_control.F90"
    sub(c, "     logical , pointer :: cpl_ke_heating\n", "     logical , pointer :: cpl_ke_heating\n     integer , pointer :: cpl_ke_smooth\n")
    sub(c, "       cpl_ke_heating                => Atm%flagstruct%cpl_ke_heating\n",
        "       cpl_ke_heating                => Atm%flagstruct%cpl_ke_heating\n"
        "       cpl_ke_smooth                 => Atm%flagstruct%cpl_ke_smooth\n")
    sub(c, "ignore_rst_cksum, cpl_ke_heating\n", "ignore_rst_cksum, cpl_ke_heating, cpl_ke_smooth\n")
    a = root.parent / "driver/UFS/atmosphere.F90"
    sub(a, "   real :: ked1, dte, tnew, cxm(isc:iec), qcx(isc:iec)\n",
        "   real :: ked1, dte, tnew, cxm(isc:iec), qcx(isc:iec)\n"
        "   real, allocatable :: kee(:,:,:)\n   real(kind=8) :: fsx(isc:iec+1,jsc:jec), fsy(isc:iec,jsc:jec+1)\n   integer :: ipass\n")
    kd = ("0.25*Atm(n)%gridstruct%rsin2(i,j)*(Atm(n)%u(i,j,k)**2 + Atm(n)%u(i,j+1,k)**2 + Atm(n)%v(i,j,k)**2 &\n"
          "                   + Atm(n)%v(i+1,j,k)**2 - (Atm(n)%u(i,j,k) + Atm(n)%u(i,j+1,k))*(Atm(n)%v(i,j,k) &\n"
          "                   + Atm(n)%v(i+1,j,k))*Atm(n)%gridstruct%cosa_s(i,j))")
    ar = "Atm(n)%gridstruct%area_64"
    sub(a, "! heat (per cell, as fv_update_phys heats) the implied minus the realised D-grid KE change\n",
        "! heat (per cell, as fv_update_phys heats) the implied minus the realised D-grid KE change\n"
        "      if (Atm(n)%flagstruct%cpl_ke_smooth > 0) then\n"
        "! per-area energy of the mismatch, smoothed in flux form (exactly conservative) to remove grid-scale dipoles\n"
        "        allocate(kee(isd:ied,jsd:jed,npz))\n        kee = 0.\n"
        "        do k=1,npz\n          do j=jsc,jec\n            do i=isc,iec\n"
        "              ked1 = " + kd + "\n"
        "              kee(i,j,k) = ke_tgt(i,j,k) - (ked1 - ked0(i,j,k))*Atm(n)%delp(i,j,k)\n"
        "            enddo\n          enddo\n        enddo\n"
        "        do ipass = 1, Atm(n)%flagstruct%cpl_ke_smooth\n"
        "          call mpp_update_domains(kee, Atm(n)%domain)\n"
        "          do k=1,npz\n"
        "            do j=jsc,jec\n              do i=isc,iec+1\n"
        f"                fsx(i,j) = 0.125d0*(dble(kee(i,j,k)) - dble(kee(i-1,j,k)))   &\n"
        f"                         *min({ar}(i-1,j), {ar}(i,j))\n"
        "              enddo\n            enddo\n"
        "            do j=jsc,jec+1\n              do i=isc,iec\n"
        f"                fsy(i,j) = 0.125d0*(dble(kee(i,j,k)) - dble(kee(i,j-1,k)))   &\n"
        f"                         *min({ar}(i,j-1), {ar}(i,j))\n"
        "              enddo\n            enddo\n"
        "            do j=jsc,jec\n              do i=isc,iec\n"
        f"                kee(i,j,k) = kee(i,j,k) + (fsx(i+1,j) - fsx(i,j) + fsy(i,j+1) - fsy(i,j))   &\n"
        f"                           /{ar}(i,j)\n"
        "              enddo\n            enddo\n"
        "          enddo\n        enddo\n      endif\n")
    sub(a, "            dte = ke_tgt(i,j,k)/Atm(n)%delp(i,j,k) - (ked1 - ked0(i,j,k))\n",
        "            if (Atm(n)%flagstruct%cpl_ke_smooth > 0) then\n"
        "              dte = kee(i,j,k)/Atm(n)%delp(i,j,k)\n"
        "            else\n"
        "              dte = ke_tgt(i,j,k)/Atm(n)%delp(i,j,k) - (ked1 - ked0(i,j,k))\n"
        "            endif\n")
    sub(a, "          enddo\n        enddo\n      enddo\n      deallocate(ked0)\n    endif\n",
        "          enddo\n        enddo\n      enddo\n      deallocate(ked0)\n      if (allocated(kee)) deallocate(kee)\n    endif\n")


def c8():
    a = root.parent / "driver/UFS/atmosphere.F90"
    sub(a, "   real(kind=kind_phys) :: fpl(npz+1), fpi(npz+1), fr\n",
        "   real(kind=kind_phys) :: fpl(npz+1), fpi(npz+1), fr, ked(npz)\n")
    sub(a, "         tk(k1) = Atm(n)%pt(i,j,k1)\n",
        "         tk(k1) = Atm(n)%pt(i,j,k1)\n"
        "         ! KE (FV3 total-energy form: D-grid KE + w^2/2) the written water mass carries\n"
        "         ked(k1) = 0.25*Atm(n)%gridstruct%rsin2(i,j)*(Atm(n)%u(i,j,k1)**2 + Atm(n)%u(i,j+1,k1)**2       &\n"
        "                 + Atm(n)%v(i,j,k1)**2 + Atm(n)%v(i+1,j,k1)**2 - (Atm(n)%u(i,j,k1) + Atm(n)%u(i,j+1,k1))   &\n"
        "                 *(Atm(n)%v(i,j,k1) + Atm(n)%v(i+1,j,k1))*Atm(n)%gridstruct%cosa_s(i,j)) + 0.5*Atm(n)%w(i,j,k1)**2\n")
    sub(a, "         if (iand(ibits, 4) /= 0) e = e + qse(k1)\n",
        "         if (iand(ibits, 4) /= 0) e = e + qse(k1)\n"
        "         if (iand(ibits, 8) /= 0) e = e - dm(k1)*ked(k1)\n")


def s1k():
    d = ccpp / "physics/physics/CONV/SAMF"
    for sch, hdr in (("samfdeepcnv", "     &    pflx,samf_kirchhoff,errmsg,errflg)\n"),
                     ("samfshalcnv", "     &     pflx,samf_kirchhoff,errmsg,errflg)\n")):
        f = d / f"{sch}.f"
        sub(f, hdr, hdr.replace("samf_kirchhoff,errmsg", "samf_kirchhoff,tgrs,errmsg"))
        sub(f, "      logical, intent(in) :: samf_kirchhoff\n",
            "      logical, intent(in) :: samf_kirchhoff\n      real(kind=kind_phys), intent(in) :: tgrs(:,:)\n")
        suball(f, "(t1(i,k) - t0c) * ck", "(tgrs(i,k) - t0c) * ck")
        sub(f, "     &                      / real(cp, kind=conv_wp) * tem * tem1\n",
            "     &                      / real(cp, kind=conv_wp) * tem * tem1\n"
            "!               frame F: fusion at L_f(T) = hfus + (c_l - c_i)(T - T0), step-initial T\n"
            "                if (samf_kirchhoff) new_t1(i,k) = new_t1(i,k)\n"
            "     &            + real((cliq - 1972.0_kind_phys) * (tgrs(i,k) - t0c)\n"
            "     &            / cp, kind=conv_wp) * tem * tem1\n")
        m = d / f"{sch}.meta"
        txt = edits.get(m) or m.read_text()
        i0 = txt.index(f"  name = {sch}_run")
        j0 = txt.index("[errmsg]", i0)
        edits[m] = txt[:j0] + ("[tgrs]\n  standard_name = physics_timestep_initial_air_temperature\n"
                               "  long_name = model layer mean temperature at the start of the physics step\n  units = K\n"
                               "  dimensions = (horizontal_loop_extent,vertical_layer_dimension)\n  type = real\n"
                               "  kind = kind_phys\n  intent = in\n") + txt[j0:]


def tfh():
    td = ccpp / "data/GFS_typedefs.F90"
    sub(td, "    logical              :: thompson_kirchhoff !< Thompson latent heats/heat capacity of the host energy frame\n",
        "    logical              :: thompson_kirchhoff !< Thompson latent heats/heat capacity of the host energy frame\n"
        "    logical              :: thompson_frame_heat !< Thompson heating = frame-F latent heat of its net phase change\n")
    sub(td, "    logical              :: thompson_kirchhoff = .false.        !< Thompson latent heats/heat capacity of the host energy frame\n",
        "    logical              :: thompson_kirchhoff = .false.        !< Thompson latent heats/heat capacity of the host energy frame\n"
        "    logical              :: thompson_frame_heat = .false.       !< Thompson heating = frame-F latent heat of its net phase change\n")
    sub(td, "sedi_semi, decfl, thompson_kirchhoff, samf_kirchhoff,", "sedi_semi, decfl, thompson_kirchhoff, samf_kirchhoff, thompson_frame_heat,")
    sub(td, "    Model%thompson_kirchhoff = thompson_kirchhoff\n",
        "    Model%thompson_kirchhoff = thompson_kirchhoff\n    Model%thompson_frame_heat = thompson_frame_heat\n")
    tm = ccpp / "data/GFS_typedefs.meta"
    old = ("[thompson_kirchhoff]\n  standard_name = flag_for_thompson_kirchhoff_latent_heat\n"
           "  long_name = flag for Thompson latent heats and heat capacity of the host energy frame\n"
           "  units = flag\n  dimensions = ()\n  type = logical\n")
    sub(tm, old, old + "[thompson_frame_heat]\n  standard_name = flag_for_thompson_frame_F_heating\n"
        "  long_name = flag for Thompson heating from the frame-F latent heat of its net phase change\n"
        "  units = flag\n  dimensions = ()\n  type = logical\n")
    w = ccpp / "physics/physics/MP/Thompson/mp_thompson.F90"
    sub(w, "      use module_mp_thompson, only : naIN0, naIN1, naCCN0, naCCN1, eps\n",
        "      use module_mp_thompson, only : naIN0, naIN1, naCCN0, naCCN1, eps\n"
        "      use module_mp_thompson, only : Cp_tfh => Cp, lvap0_tfh => lvap0, lfus_tfh => lfus\n")
    sub(w, "dnifa, dtgrs, ten_u, ten_v, pflx_mpl, pflx_mpi, errmsg, errflg)\n",
        "dnifa, dtgrs, ten_u, ten_v, pflx_mpl, pflx_mpi, frame_heat, t_old, errmsg, errflg)\n")
    sub(w, "         real(kind=kind_phys), intent(inout) :: pflx_mpl(:,:), pflx_mpi(:,:)\n",
        "         real(kind=kind_phys), intent(inout) :: pflx_mpl(:,:), pflx_mpi(:,:)\n"
        "         logical,                   intent(in   ) :: frame_heat\n"
        "         real(kind_phys),           intent(in   ) :: t_old(:,:)\n"
        "         real(kind_phys) :: fmass, fdv, fdi, ftt, ftb, fvt, fvb, fit, fib, fqa, fqb, fqreq\n"
        "         integer :: fi, fk\n")
    sub(w, "         dspechum = (new_spechum - spechum)/dtp\n",
        "         if (frame_heat) then\n"
        "           ! heating from the net phase change of each layer (water budget + exported precipitation fluxes,\n"
        "           ! vapour flux = remainder) at FV3's latent heats L(T) for the step-initial T, replacing Thompson's\n"
        "           do fi = 1, ncol\n             ftt = 0.0_kind_phys\n"
        "             do fk = nlev, 1, -1\n"
        "               fmass = (prsi(fi,fk) - prsi(fi,fk+1))/con_g\n"
        "               fdv = fmass*(new_spechum(fi,fk) - spechum(fi,fk))\n"
        "               fdi = fmass*(new_qi(fi,fk) - qi(fi,fk) + new_qs(fi,fk) - qs(fi,fk) + new_qg(fi,fk) - qg(fi,fk))\n"
        "               ftb = ftt - fdv - fdi - fmass*(new_qc(fi,fk) - qc(fi,fk) + new_qr(fi,fk) - qr(fi,fk))\n"
        "               fib = pflx_mpi(fi,fk)\n               fit = 0.0_kind_phys\n"
        "               if (fk < nlev) fit = pflx_mpi(fi,fk+1)\n"
        "               fvb = ftb - pflx_mpl(fi,fk) - fib\n               fvt = ftt\n"
        "               if (fk < nlev) fvt = ftt - pflx_mpl(fi,fk+1) - fit\n"
        "               fqa = fvt - fvb - fdv                ! vapour condensed or deposited in the layer\n"
        "               fqb = fdi - (fit - fib)              ! water frozen (from vapour or liquid) in the layer\n"
        "               fqreq = (lvap0_tfh + (1846.0_kind_phys - 4185.5_kind_phys)*(t_old(fi,fk) - 273.15_kind_phys))*fqa &\n"
        "                     + (lfus_tfh + (4185.5_kind_phys - 1972.0_kind_phys)*(t_old(fi,fk) - 273.15_kind_phys))*fqb\n"
        "               new_tgrs(fi,fk) = tgrs(fi,fk) + fqreq/(Cp_tfh*fmass)\n"
        "               ftt = ftb\n"
        "             enddo\n           enddo\n         endif\n"
        "         dspechum = (new_spechum - spechum)/dtp\n")
    wm = ccpp / "physics/physics/MP/Thompson/mp_thompson.meta"
    txt = edits.get(wm) or wm.read_text()
    i0 = txt.index("  name = mp_thompson_run")
    j0 = txt.index("[errmsg]", i0)
    edits[wm] = txt[:j0] + ("[frame_heat]\n  standard_name = flag_for_thompson_frame_F_heating\n"
                            "  long_name = flag for Thompson heating from the frame-F latent heat of its net phase change\n"
                            "  units = flag\n  dimensions = ()\n  type = logical\n  intent = in\n"
                            "[t_old]\n  standard_name = physics_timestep_initial_air_temperature\n"
                            "  long_name = model layer mean temperature at the start of the physics step\n  units = K\n"
                            "  dimensions = (horizontal_loop_extent,vertical_layer_dimension)\n  type = real\n"
                            "  kind = kind_phys\n  intent = in\n") + txt[j0:]


def pbk():
    td = ccpp / "data/GFS_typedefs.F90"
    sub(td, "    logical              :: dspheat_ke      !< flag for dissipative heating = resolved KE loss of the PBL momentum solve\n",
        "    logical              :: dspheat_ke      !< flag for dissipative heating = resolved KE loss of the PBL momentum solve\n"
        "    logical              :: pbl_kirchhoff   !< PBL condensate filler at FV3's L_h(T)\n")
    sub(td, "    logical              :: dspheat_ke     = .false.                  !< flag for dissipative heating = resolved KE loss of the PBL momentum solve\n",
        "    logical              :: dspheat_ke     = .false.                  !< flag for dissipative heating = resolved KE loss of the PBL momentum solve\n"
        "    logical              :: pbl_kirchhoff  = .false.                  !< PBL condensate filler at FV3's L_h(T)\n")
    sub(td, "shinhong, do_ysu, dspheat, dspheat_ke, lheatstrg,", "shinhong, do_ysu, dspheat, dspheat_ke, pbl_kirchhoff, lheatstrg,")
    sub(td, "    Model%dspheat_ke        = dspheat_ke\n", "    Model%dspheat_ke        = dspheat_ke\n    Model%pbl_kirchhoff     = pbl_kirchhoff\n")
    blk = ("[pbl_kirchhoff]\n  standard_name = flag_for_pbl_kirchhoff_latent_heat\n"
           "  long_name = flag for the PBL condensate filler at the host latent heat L_h(T)\n"
           "  units = flag\n  dimensions = ()\n  type = logical\n")
    tm = ccpp / "data/GFS_typedefs.meta"
    old = ("[dspheat_ke]\n  standard_name = flag_for_kinetic_energy_consistent_dissipation_heating\n"
           "  long_name = flag for dissipative heating equal to the resolved kinetic energy loss of the PBL momentum solve\n"
           "  units = flag\n  dimensions = ()\n  type = logical\n")
    sub(tm, old, old + blk)
    sm = ccpp / "physics/physics/PBL/SATMEDMF/satmedmfvdifq.meta"
    sub(sm, old + "  intent = in\n", old + "  intent = in\n" + blk + "  intent = in\n")
    f = ccpp / "physics/physics/PBL/SATMEDMF/satmedmfvdifq.F"
    sub(f, "     &     rlmx,elmx,sfc_rlm,tc_pbl,use_lpt,dspheat_ke,                 &\n",
        "     &     rlmx,elmx,sfc_rlm,tc_pbl,use_lpt,dspheat_ke,pbl_kirchhoff,   &\n")
    sub(f, "      logical, intent(in)  :: dspheat_ke\n", "      logical, intent(in)  :: dspheat_ke\n      logical, intent(in)  :: pbl_kirchhoff\n")
    sub(f, "                  f1(i,k) = f1(i,k) - elocp * f2(i,k+is)\n",
        "                  f1(i,k) = f1(i,k) - elocp * f2(i,k+is)\n"
        "                  if (pbl_kirchhoff) f1(i,k) = f1(i,k)\n"
        "     &   - (1846.d0-4185.5d0)*(t1(i,k)-273.15d0)/cp*f2(i,k+is)\n", count=2)
    sub(f, "                  f1(i,k) = f1(i,k) + elocp * f2(i,k)\n",
        "                  f1(i,k) = f1(i,k) + elocp * f2(i,k)\n"
        "                  if (pbl_kirchhoff) f1(i,k) = f1(i,k)\n"
        "     &   + (1846.d0-4185.5d0)*(t1(i,k)-273.15d0)/cp*f2(i,k)\n", count=2)


def th8():
    f = ccpp / "physics/physics/MP/Thompson/module_mp_thompson.F90"
    for x in ("rr", "ri", "rs", "rg"):
        suball(f, f"if ({x}(kts).gt.R1*rr_min) then\n",
               f"if (.true.) then  ! all mass leaving the lowest layer is precipitation (was {x}(kts) > R1*rr_min)\n")


def pbf():
    td = ccpp / "data/GFS_typedefs.F90"
    sub(td, "    real (kind=kind_phys), pointer :: pflx_mpi(:,:) => null()\n",
        "    real (kind=kind_phys), pointer :: pflx_mpi(:,:) => null()\n"
        "    real (kind=kind_phys), pointer :: pflx_pbll(:,:) => null()  !< PBL liquid condensate through layer bottom (kg m-2)\n"
        "    real (kind=kind_phys), pointer :: pflx_pbli(:,:) => null()  !< PBL frozen condensate through layer bottom (kg m-2)\n")
    sub(td, "    allocate (Stateout%pflx_mpi (IM,Model%levs+1))\n    Stateout%pflx_mpi = clear_val\n",
        "    allocate (Stateout%pflx_mpi (IM,Model%levs+1))\n    Stateout%pflx_mpi = clear_val\n"
        "    allocate (Stateout%pflx_pbll (IM,Model%levs+1))\n    Stateout%pflx_pbll = clear_val\n"
        "    allocate (Stateout%pflx_pbli (IM,Model%levs+1))\n    Stateout%pflx_pbli = clear_val\n")
    tm = ccpp / "data/GFS_typedefs.meta"
    old = ("[pflx_mpi]\n  standard_name = frozen_precipitation_mass_through_layer_bottom_from_microphysics\n"
           "  long_name = microphysics frozen precipitation through layer bottom per physics step\n  units = kg m-2\n"
           "  dimensions = (horizontal_dimension,vertical_interface_dimension)\n  type = real\n  kind = kind_phys\n")
    blk = lambda dim, it: "".join(
        f"[pflx_pbl{c}]\n  standard_name = {w}_condensate_mass_through_layer_bottom_from_pbl\n"
        f"  long_name = PBL {w} condensate transport through layer bottom per physics step (down positive)\n  units = kg m-2\n"
        f"  dimensions = ({dim},vertical_interface_dimension)\n  type = real\n  kind = kind_phys\n" + it
        for c, w in (("l", "liquid"), ("i", "frozen")))
    sub(tm, old, old + blk("horizontal_dimension", ""))
    f = ccpp / "physics/physics/PBL/SATMEDMF/satmedmfvdifq.F"
    sub(f, "     &     rlmx,elmx,sfc_rlm,tc_pbl,use_lpt,dspheat_ke,pbl_kirchhoff,   &\n",
        "     &     rlmx,elmx,sfc_rlm,tc_pbl,use_lpt,dspheat_ke,pbl_kirchhoff,   &\n"
        "     &     ntsw,ntgl,pflx_pbll,pflx_pbli,                               &\n")
    sub(f, "      logical, intent(in)  :: pbl_kirchhoff\n",
        "      logical, intent(in)  :: pbl_kirchhoff\n"
        "      integer, intent(in)  :: ntsw, ntgl\n"
        "      real(kind=kind_phys), intent(inout) :: pflx_pbll(:,:)\n"
        "      real(kind=kind_phys), intent(inout) :: pflx_pbli(:,:)\n"
        "      real(kind=kind_phys) :: pblfil(im,km), ql0, qi0\n")
    sub(f, "! For the negative liquid water, first borrow water from vapor\n",
        "      pblfil = 0.\n! For the negative liquid water, first borrow water from vapor\n")
    sub(f, "     &   - (1846.d0-4185.5d0)*(t1(i,k)-273.15d0)/cp*f2(i,k+is)\n",
        "     &   - (1846.d0-4185.5d0)*(t1(i,k)-273.15d0)/cp*f2(i,k+is)\n"
        "                  pblfil(i,k) = pblfil(i,k) - f2(i,k+is)\n", count=2)
    sub(f, "     &   + (1846.d0-4185.5d0)*(t1(i,k)-273.15d0)/cp*f2(i,k)\n",
        "     &   + (1846.d0-4185.5d0)*(t1(i,k)-273.15d0)/cp*f2(i,k)\n"
        "                  pblfil(i,k) = pblfil(i,k) + f2(i,k)\n", count=2)
    sub(f, "!> - Recover the tendencies of heat and moisture\n",
        "!  condensate transport through layer bottoms (kg m-2, down positive),\n"
        "!  filler phase change excluded; tracers 5, 6 are snow, graupel (q1=qgrs)\n"
        "      if (pbl_kirchhoff) then\n"
        "        do i = 1,im\n          pflx_pbll(i,km+1) = 0.\n          pflx_pbli(i,km+1) = 0.\n        enddo\n"
        "        do k = km,1,-1\n          do i = 1,im\n"
        "            ql0 = f2(i,k+(ntcw-1)*km)-q1(i,k,ntcw)-pblfil(i,k)\n"
        "            if (ntrw > 0) ql0 = ql0+f2(i,k+(ntrw-1)*km)-q1(i,k,ntrw)\n"
        "            qi0 = 0.\n"
        "            if (ntiw > 0) qi0 = f2(i,k+(ntiw-1)*km)-q1(i,k,ntiw)\n"
        "            if (ntsw > 0) qi0 = qi0+f2(i,k+(ntsw-1)*km)-q1(i,k,ntsw)\n"
        "            if (ntgl > 0) qi0 = qi0+f2(i,k+(ntgl-1)*km)-q1(i,k,ntgl)\n"
        "            pflx_pbll(i,k) = pflx_pbll(i,k+1) - ql0*del(i,k)*gravi\n"
        "            pflx_pbli(i,k) = pflx_pbli(i,k+1) - qi0*del(i,k)*gravi\n"
        "          enddo\n        enddo\n      endif\n"
        "!> - Recover the tendencies of heat and moisture\n")
    sm = ccpp / "physics/physics/PBL/SATMEDMF/satmedmfvdifq.meta"
    pk = ("[pbl_kirchhoff]\n  standard_name = flag_for_pbl_kirchhoff_latent_heat\n"
          "  long_name = flag for the PBL condensate filler at the host latent heat L_h(T)\n"
          "  units = flag\n  dimensions = ()\n  type = logical\n  intent = in\n")
    sub(sm, pk, pk + "[ntsw]\n  standard_name = index_of_snow_mixing_ratio_in_tracer_concentration_array\n"
        "  long_name = tracer index for snow water\n  units = index\n  dimensions = ()\n  type = integer\n  intent = in\n"
        "[ntgl]\n  standard_name = index_of_graupel_mixing_ratio_in_tracer_concentration_array\n"
        "  long_name = tracer index for graupel\n  units = index\n  dimensions = ()\n  type = integer\n  intent = in\n"
        + blk("horizontal_loop_extent", "  intent = inout\n"))
    a = root.parent / "driver/UFS/atmosphere.F90"
    sub(a, "   real(kind=kind_phys) :: fpl(npz+1), fpi(npz+1), fr, ked(npz)\n",
        "   real(kind=kind_phys) :: fpl(npz+1), fpi(npz+1), fr, ked(npz), fbl(npz+1), fbi(npz+1)\n")
    sub(a, "         fpi(k1+1) = grav*IPD_Stateout%pflx_mpi(im,k)\n",
        "         fpi(k1+1) = grav*IPD_Stateout%pflx_mpi(im,k)\n"
        "         fbl(k1+1) = grav*IPD_Stateout%pflx_pbll(im,k)\n"
        "         fbi(k1+1) = grav*IPD_Stateout%pflx_pbli(im,k)\n")
    sub(a, "         fr = ftop(k1+1) - fpl(k1+1) - fpi(k1+1)\n",
        "         ! PBL condensate transport: c_l/c_i exchange in the receiving layer\n"
        "         if (fbl(k1+1) + fbi(k1+1) >= 0.) then\n"
        "            qse(k1+1) = qse(k1+1) - (fbl(k1+1)*c_liq + fbi(k1+1)*c_ice)*(tk(k1+1) - tk(k1))\n"
        "         else\n"
        "            qse(k1) = qse(k1) - (fbl(k1+1)*c_liq + fbi(k1+1)*c_ice)*(tk(k1+1) - tk(k1))\n"
        "         endif\n"
        "         fr = ftop(k1+1) - fpl(k1+1) - fpi(k1+1) - fbl(k1+1) - fbi(k1+1)\n")


fixes = {"FX1": fx1, "SG1": sg1, "CP1": cp1, "R1": r1, "D7": d7, "D7S": d7s, "C8": c8, "S1K": s1k, "TFH": tfh, "PBK": pbk, "TH8": th8, "PBF": pbf}
for f in sys.argv[2:]:
    fixes[f]()
for p, s in edits.items():
    p.write_text(s)
    print("edited", p)
