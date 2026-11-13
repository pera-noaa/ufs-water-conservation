#!/usr/bin/env python3
"""Per-scheme energy meters in CCPP physics, v2: adds the frame-F (encpl) water enthalpy column c8 at the step-initial
T (tgrs) and a frame-F residual per segment (diagnostic builds only).
Usage: instrument_eb_phys.py <ufs-weather-model>
Adds probe schemes em_p01..em_p12 (Interstitials/UFS_SCM_NEPTUNE/em_pNN.F90/.meta, common module
energy_meter_common.F90), inserts them into suite_FV3_GFS_v17_p8_ugwpv1.xml and the fv3 prebuild config.
Each probe stores, per column, the physics-frame energy of the effective state X = X0 + dtp*(pending
process-split tendency), mass m = (prsi(k)-prsi(k+1))/g fixed:
  c1 cp*T  c2 hvap*qv  c3 -hfus*(qi+qs+qg)  c4 0.5(u^2+v^2)  c5 W=qv+ql+qr+qi+qs+qg  c6 ice water
Probe 12 forms segment differences, boundary fluxes, residuals; MPI-reduced; line per step:
  'EMS kdt seg dE dcpT dLq dLf dK dW F |r|' (J and kg, area-integrated) + 'EMF' extras."""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp"
phys = root / "physics/physics"
idir = phys / "Interstitials/UFS_SCM_NEPTUNE"
suite = root / "suites/suite_FV3_GFS_v17_p8_ugwpv1.xml"
cfg = root / "config/ccpp_prebuild_config_fv3.py"

# ---- metadata blocks copied from existing tables by standard name
metas = sorted(phys.rglob("*.meta")) + sorted((root / "data").glob("*.meta"))


def block(std):
    for m in metas:
        txt = m.read_text(errors="ignore")
        for b in re.split(r"\n(?=\[)", txt):
            if re.search(r"^\s*standard_name\s*=\s*" + re.escape(std) + r"\s*$", b, re.M) and b.startswith("[") \
                    and "ccpp-" not in b.splitlines()[0]:
                lines = [l for l in b.strip().splitlines() if not l.strip().startswith("intent")
                         and not l.strip().startswith("optional")]
                return lines
    sys.exit(f"ABORT: no metadata block for {std}")


COMMON = [("im", "horizontal_loop_extent"), ("levs", "vertical_layer_dimension"), ("kdt", "index_of_timestep"),
          ("dtp", "timestep_for_physics"), ("gt0", "air_temperature"), ("gq0", "tracer_concentration"),
          ("gu0", "x_wind"), ("gv0", "y_wind"),
          ("dtdt", "process_split_cumulative_tendency_of_air_temperature"),
          ("dqdt", "process_split_cumulative_tendency_of_tracers"),
          ("dudt", "process_split_cumulative_tendency_of_x_wind"),
          ("dvdt", "process_split_cumulative_tendency_of_y_wind"),
          ("prsi", "air_pressure_at_interface"),
          ("ntqv", "index_of_specific_humidity_in_tracer_concentration_array"),
          ("ntcw", "index_of_cloud_liquid_water_mixing_ratio_in_tracer_concentration_array"),
          ("ntiw", "index_of_cloud_ice_mixing_ratio_in_tracer_concentration_array"),
          ("ntrw", "index_of_rain_mixing_ratio_in_tracer_concentration_array"),
          ("ntsw", "index_of_snow_mixing_ratio_in_tracer_concentration_array"),
          ("ntgl", "index_of_graupel_mixing_ratio_in_tracer_concentration_array"),
          ("con_g", "gravitational_acceleration"), ("con_cp", "specific_heat_of_dry_air_at_constant_pressure"),
          ("con_hvap", "latent_heat_of_vaporization_of_water_at_0C"),
          ("con_hfus", "latent_heat_of_fusion_of_water_at_0C"),
          ("tgrs", "physics_timestep_initial_air_temperature")]
import os
PBLFLX = ([("pflx_pbll", "liquid_condensate_mass_through_layer_bottom_from_pbl"),
           ("pflx_pbli", "frozen_condensate_mass_through_layer_bottom_from_pbl")] if os.environ.get("EB_PBLFLX") else [])
PH1 = bool(os.environ.get("EB_PH1"))
PH1ARG = [("tsfc", "surface_skin_temperature")] if PH1 else []
LAG = bool(os.environ.get("EB_LAG"))  # precipitation hand-off lag c P (T1(N+1) - T1(N)) and PH1 ice swap: EML line
EXTRA = {3: [("xmu", "zenith_angle_temporal_adjustment_factor_for_shortwave_fluxes"),
             ("topfsw", "sw_fluxes_top_atmosphere"), ("topflw", "lw_fluxes_top_atmosphere"),
             ("sfcfsw", "surface_sw_fluxes_assuming_total_and_clear_sky_on_radiation_timestep"),
             ("sfcflw", "surface_lw_fluxes_assuming_total_and_clear_sky_on_radiation_timestep"),
             ("adjsfcnsw", "surface_net_downwelling_shortwave_flux"),
             ("adjsfcdlw", "surface_downwelling_longwave_flux")],
         5: [("dtsfc1", "instantaneous_surface_upward_sensible_heat_flux"),
             ("dqsfc1", "instantaneous_surface_upward_latent_heat_flux")] + PBLFLX,
         8: [("rainc", "lwe_thickness_of_convective_precipitation_amount_on_dynamics_timestep"),
             ("pflx_dc", "precipitation_mass_through_layer_bottom_from_deep_convection")],
         9: [("rainc", "lwe_thickness_of_convective_precipitation_amount_on_dynamics_timestep"),
             ("pflx_sc", "precipitation_mass_through_layer_bottom_from_shallow_convection")],
         11: [("prcp", "lwe_thickness_of_explicit_precipitation_amount"),
              ("snow", "lwe_thickness_of_snow_amount"), ("ice", "lwe_thickness_of_ice_amount"),
              ("graupel", "lwe_thickness_of_graupel_amount"),
              ("rainc", "lwe_thickness_of_convective_precipitation_amount_on_dynamics_timestep"),
              ("pflx_mpl", "liquid_precipitation_mass_through_layer_bottom_from_microphysics"),
              ("pflx_mpi", "frozen_precipitation_mass_through_layer_bottom_from_microphysics")] + PH1ARG,
         12: [("garea", "cell_area"), ("mpicomm", "mpi_communicator"), ("mpirank", "mpi_rank"),
              ("mpiroot", "mpi_root")] + ([("frland", "land_area_fraction")] if LAG else [])}
TAIL = [("errmsg", "ccpp_error_message"), ("errflg", "ccpp_error_code")]

NP = 12
# probe placement: (probe, scheme it follows) ; probe 1 follows GFS_suite_interstitial_1
AFTER = {1: "GFS_suite_interstitial_1", 2: "GFS_surface_composites_pre", 3: "dcyc2t3",
         4: "sfc_diag_post", 5: "GFS_PBL_generic_post", 6: "GFS_GWD_generic_post",
         7: "GFS_photochemistry_post", 8: "GFS_DCNV_generic_post", 9: "GFS_SCNV_generic_post",
         10: "cnvc90", 11: "GFS_MP_generic_post", 12: "GFS_physics_post"}

COMMON_F90 = r"""!> \file energy_meter_common.F90
!! Energy meter storage and probe (diagnostic builds only).
module energy_meter_common
  use machine, only: kind_phys
  implicit none
  private
  public :: em_probe, emc, emg, emx, emkdt, emf, emdw, emsx, em_sxp, emlp, emlt, emla, eml
  integer, parameter, public :: emnp = 12, emnc = 8192
  real(kind=8), save :: emc(8, emnp, emnc) = 0.d0
  real(kind=8), allocatable, save :: emd(:,:)
  real(kind=8), allocatable, save :: emw(:,:), emdw(:,:)   ! previous-probe layer water; segment layer change
  real(kind=8), save :: emsx(emnp, emnc) = 0.d0            ! segment sensible exchange S_cross (cp_v for all flux)
  real(kind=8), save :: emg(14, emnp) = 0.d0, emx(12) = 0.d0, emf(16, emnc) = 0.d0
  real(kind=8), save :: emlp(emnc) = 0.d0, emlt(emnc) = 0.d0, emla(emnc) = 0.d0, eml(4) = 0.d0  ! lag meter
  integer, save :: emoff(emnp) = 0, emkdt(emnp) = -1
contains
  subroutine em_probe(p, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                      ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, tgrs, j0)
    ! energy meter: effective-state column energy in the physics frame, stored per column
    integer, intent(in) :: p, im, levs, kdt, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl
    real(kind=kind_phys), intent(in) :: dtp, con_g, con_cp, con_hvap, con_hfus
    real(kind=kind_phys), intent(in) :: gt0(:,:), gq0(:,:,:), gu0(:,:), gv0(:,:), prsi(:,:)
    real(kind=kind_phys), intent(in) :: dtdt(:,:), dqdt(:,:,:), dudt(:,:), dvdt(:,:), tgrs(:,:)
    integer, intent(out) :: j0
    real(kind=8) :: x(8), m, t, qv, ql, qi, u, v, tq, fl, sx, wl
    ! dycore-consistent (Kirchhoff) enthalpy, dry mass held at its probe-1 value, FV3 heat capacities
    real(kind=8), parameter :: cpa = 1004.6d0, cpv = 1846.0d0, cl = 4185.5d0, ci = 1972.0d0, t0 = 273.15d0
    real(kind=8) :: lv00, li00
    integer :: i, k
    if (kdt /= emkdt(p)) then
       emkdt(p) = kdt
       emoff(p) = 0
    endif
    j0 = emoff(p)
    lv00 = con_hvap - (cpv - cl)*t0
    li00 = con_hfus - (cl - ci)*t0
    if (.not. allocated(emd)) allocate(emd(levs, emnc))
    if (.not. allocated(emw)) then
       allocate(emw(levs, emnc), emdw(levs, emnc))
       emw = 0.d0
       emdw = 0.d0
    endif
    do i = 1, im
       x = 0.d0
       do k = 1, levs
          m = (prsi(i,k) - prsi(i,k+1))/con_g
          t = gt0(i,k) + dtp*dtdt(i,k)
          u = gu0(i,k) + dtp*dudt(i,k)
          v = gv0(i,k) + dtp*dvdt(i,k)
          qv = gq0(i,k,ntqv) + dtp*dqdt(i,k,ntqv)
          ql = gq0(i,k,ntcw) + dtp*dqdt(i,k,ntcw) + gq0(i,k,ntrw) + dtp*dqdt(i,k,ntrw)
          qi = gq0(i,k,ntiw) + dtp*dqdt(i,k,ntiw) + gq0(i,k,ntsw) + dtp*dqdt(i,k,ntsw) &
             + gq0(i,k,ntgl) + dtp*dqdt(i,k,ntgl)
          x(1) = x(1) + m*con_cp*t
          x(2) = x(2) + m*con_hvap*qv
          x(3) = x(3) - m*con_hfus*qi
          x(4) = x(4) + m*0.5d0*(u*u + v*v)
          x(5) = x(5) + m*(qv + ql + qi)
          x(6) = x(6) + m*qi
          if (p == 1) emd(k, j0+i) = m*(1.d0 - qv)
          tq = tgrs(i,k)
          ! frame F minus physics-frame water enthalpy, at the step-initial T (what the coupling books)
          x(8) = x(8) + m*(qv*(lv00 + cpv*tq - con_hvap) + ql*cl*tq + qi*(ci*tq - li00 + con_hfus))
          x(7) = x(7) + emd(k, j0+i)*cpa*t + m*((qv*cpv + ql*cl + qi*ci)*t + lv00*qv - li00*qi) &
               + (emd(k, j0+i) + m*(qv + ql + qi))*0.5d0*(u*u + v*v)
       enddo
       emc(:, p, j0+i) = x
       ! segment water change per layer, downward flux through layer bottoms, S_cross with cp_v (bottom interface excluded)
       fl = 0.d0
       sx = 0.d0
       do k = levs, 1, -1
          m = (prsi(i,k) - prsi(i,k+1))/con_g
          wl = m*(gq0(i,k,ntqv) + dtp*dqdt(i,k,ntqv) + gq0(i,k,ntcw) + dtp*dqdt(i,k,ntcw) + gq0(i,k,ntrw) &
             + dtp*dqdt(i,k,ntrw) + gq0(i,k,ntiw) + dtp*dqdt(i,k,ntiw) + gq0(i,k,ntsw) + dtp*dqdt(i,k,ntsw) &
             + gq0(i,k,ntgl) + dtp*dqdt(i,k,ntgl))
          emdw(k, j0+i) = wl - emw(k, j0+i)
          emw(k, j0+i) = wl
          fl = fl - emdw(k, j0+i)
          if (k > 1) sx = sx + fl*1846.d0*(tgrs(i,k-1) - tgrs(i,k))
       enddo
       if (p > 1) emsx(p, j0+i) = sx
       if (p == 1) emf(13, j0+i) = tgrs(i,1)
    enddo
    emoff(p) = j0 + im
  end subroutine em_probe

  subroutine em_sxp(p, j, levs, pflx, c, tgrs)
    ! precipitation part of S_cross for segment ending at probe p: exported flux carries c, not cp_v
    integer, intent(in) :: p, j, levs
    real(kind=kind_phys), intent(in) :: pflx(:), tgrs(:)
    real(kind=8), intent(in) :: c
    integer :: k
    do k = 2, levs
       emsx(p, j) = emsx(p, j) + pflx(k)*(c - 1846.d0)*(tgrs(k-1) - tgrs(k))
    enddo
  end subroutine em_sxp
end module energy_meter_common
"""


def f90_args(names):
    return ", ".join(names)


def decl(n):
    return {
        "im": "integer, intent(in) :: im", "levs": "integer, intent(in) :: levs", "kdt": "integer, intent(in) :: kdt",
        "dtp": "real(kind=kind_phys), intent(in) :: dtp",
        "gt0": "real(kind=kind_phys), intent(in) :: gt0(:,:)", "gq0": "real(kind=kind_phys), intent(in) :: gq0(:,:,:)",
        "gu0": "real(kind=kind_phys), intent(in) :: gu0(:,:)", "gv0": "real(kind=kind_phys), intent(in) :: gv0(:,:)",
        "dtdt": "real(kind=kind_phys), intent(in) :: dtdt(:,:)", "dqdt": "real(kind=kind_phys), intent(in) :: dqdt(:,:,:)",
        "dudt": "real(kind=kind_phys), intent(in) :: dudt(:,:)", "dvdt": "real(kind=kind_phys), intent(in) :: dvdt(:,:)",
        "prsi": "real(kind=kind_phys), intent(in) :: prsi(:,:)",
        "ntqv": "integer, intent(in) :: ntqv", "ntcw": "integer, intent(in) :: ntcw", "ntiw": "integer, intent(in) :: ntiw",
        "ntrw": "integer, intent(in) :: ntrw", "ntsw": "integer, intent(in) :: ntsw", "ntgl": "integer, intent(in) :: ntgl",
        "con_g": "real(kind=kind_phys), intent(in) :: con_g", "con_cp": "real(kind=kind_phys), intent(in) :: con_cp",
        "con_hvap": "real(kind=kind_phys), intent(in) :: con_hvap",
        "con_hfus": "real(kind=kind_phys), intent(in) :: con_hfus",
        "tgrs": "real(kind=kind_phys), intent(in) :: tgrs(:,:)",
        "garea": "real(kind=kind_phys), intent(in) :: garea(:)", "frland": "real(kind=kind_phys), intent(in) :: frland(:)", "xmu": "real(kind=kind_phys), intent(in) :: xmu(:)",
        "topfsw": "type(topfsw_type), intent(in) :: topfsw(:)", "topflw": "type(topflw_type), intent(in) :: topflw(:)",
        "sfcfsw": "type(sfcfsw_type), intent(in) :: sfcfsw(:)", "sfcflw": "type(sfcflw_type), intent(in) :: sfcflw(:)",
        "dtsfc1": "real(kind=kind_phys), intent(in) :: dtsfc1(:)", "dqsfc1": "real(kind=kind_phys), intent(in) :: dqsfc1(:)",
        "prcp": "real(kind=kind_phys), intent(in) :: prcp(:)", "snow": "real(kind=kind_phys), intent(in) :: snow(:)",
        "ice": "real(kind=kind_phys), intent(in) :: ice(:)", "graupel": "real(kind=kind_phys), intent(in) :: graupel(:)",
        "rainc": "real(kind=kind_phys), intent(in) :: rainc(:)", "tsfc": "real(kind=kind_phys), intent(in) :: tsfc(:)",
        "pflx_dc": "real(kind=kind_phys), intent(in) :: pflx_dc(:,:)", "pflx_sc": "real(kind=kind_phys), intent(in) :: pflx_sc(:,:)",
        "pflx_pbll": "real(kind=kind_phys), intent(in) :: pflx_pbll(:,:)", "pflx_pbli": "real(kind=kind_phys), intent(in) :: pflx_pbli(:,:)",
        "pflx_mpl": "real(kind=kind_phys), intent(in) :: pflx_mpl(:,:)", "pflx_mpi": "real(kind=kind_phys), intent(in) :: pflx_mpi(:,:)",
        "adjsfcnsw": "real(kind=kind_phys), intent(in) :: adjsfcnsw(:)",
        "adjsfcdlw": "real(kind=kind_phys), intent(in) :: adjsfcdlw(:)",
        "mpicomm": "type(MPI_Comm), intent(in) :: mpicomm", "mpirank": "integer, intent(in) :: mpirank",
        "mpiroot": "integer, intent(in) :: mpiroot",
        "errmsg": "character(len=*), intent(out) :: errmsg", "errflg": "integer, intent(out) :: errflg"}[n]


FINAL_BODY = r"""
    ! segment s = probe s -> s+1; fluxes per segment (J m-2, kg m-2), residual r = dE - F
    real(kind=8) :: d(8), rf, bc, t1, pd, ps, pl, pi, ev, e0, e1, f, w, frad, fpbl, fmp, wpbl, wmp, wcv, a
    integer :: s, jj, ierr
    real(kind=8) :: buf(14*emnp+12), rbuf(14*emnp+12), lv00, li00
    if (kdt /= emkdt(12) .and. emkdt(12) >= 0) then
       buf(1:14*emnp) = reshape(emg, (/14*emnp/))
       buf(14*emnp+1:) = emx
       if (mpirank == mpiroot) then
          call MPI_Reduce(MPI_IN_PLACE, buf, size(buf), MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)
          do s = 1, emnp
             write(*,'(a,i6,i3,14es25.16)') 'EMS ', emkdt(12), s, buf(14*(s-1)+1:14*s)
          enddo
          write(*,'(a,i6,12es25.16)') 'EMF ', emkdt(12), buf(14*emnp+1:)
       else
          call MPI_Reduce(buf, rbuf, size(buf), MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)
       endif
       emg = 0.d0
       emx = 0.d0
    endif
    call em_probe(12, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, tgrs, j0)
    do i = 1, im
       jj = j0 + i
       a = garea(i)
       frad = emf(1, jj)
       fpbl = emf(8, jj) + emf(9, jj)
       fmp = con_hfus*emf(11, jj)
       wpbl = emf(9, jj)/con_hvap
       wmp = -emf(10, jj)
       wcv = -emf(12, jj)
       ! frame-F boundary corrections at T1 (step-initial lowest-layer T): water enthalpy minus physics booking
       lv00 = con_hvap - (1846.d0 - 4185.5d0)*273.15d0
       li00 = con_hfus - (4185.5d0 - 1972.d0)*273.15d0
       t1 = emf(13, jj)
       ev = emf(9, jj)/con_hvap
       pd = emf(14, jj)
       ps = emf(15, jj) - emf(14, jj)
       pi = emf(11, jj)
       pl = emf(10, jj) - pi
       do s = 1, emnp - 1
          d = emc(:, s+1, jj) - emc(:, s, jj)
          f = 0.d0
          w = 0.d0
          if (s == 2) f = frad
          if (s == 4) then
             f = fpbl
             w = wpbl
          endif
          if (s == 10) then
             f = fmp + con_hfus*emf(16, jj)
             w = wmp
          endif
          emg(1, s) = emg(1, s) + (d(1)+d(2)+d(3)+d(4))*a
          emg(2:5, s) = emg(2:5, s) + d(1:4)*a
          emg(6, s) = emg(6, s) + d(5)*a
          emg(7, s) = emg(7, s) + f*a
          emg(8, s) = emg(8, s) + abs(d(1)+d(2)+d(3)+d(4) - f)*a
          emg(9, s) = emg(9, s) + (d(5) - w)*a
          emg(10, s) = emg(10, s) + d(7)*a
          bc = 0.d0
          if (s == 4) bc = ev*(lv00 + 1846.d0*t1 - con_hvap)
          if (s == 7) bc = -pd*4185.5d0*t1
          if (s == 8) bc = -ps*4185.5d0*t1
          if (s == 10) bc = -pl*4185.5d0*t1 - pi*(1972.d0*t1 - li00 + con_hfus) &
             - emf(16, jj)*(1972.d0*t1 - li00 + con_hfus - 4185.5d0*t1)
          rf = d(1)+d(2)+d(3)+d(4) - f + d(8) - bc
          emg(11, s) = emg(11, s) + rf*a
          emg(12, s) = emg(12, s) + abs(rf)*a
          emg(13, s) = emg(13, s) + emsx(s+1, jj)*a
          emg(14, s) = emg(14, s) + abs(rf - emsx(s+1, jj))*a
       enddo
       ! slot 12: whole physics (probe 1 -> 12), F = rad + pbl + mp, water vs all precip
       d = emc(:, 12, jj) - emc(:, 1, jj)
       emg(1, 12) = emg(1, 12) + (d(1)+d(2)+d(3)+d(4))*a
       emg(2:5, 12) = emg(2:5, 12) + d(1:4)*a
       emg(6, 12) = emg(6, 12) + d(5)*a
       emg(7, 12) = emg(7, 12) + (frad + fpbl + fmp + con_hfus*emf(16, jj))*a
       emg(8, 12) = emg(8, 12) + abs(d(1)+d(2)+d(3)+d(4) - frad - fpbl - fmp - con_hfus*emf(16, jj))*a
       emg(9, 12) = emg(9, 12) + (d(5) - wpbl - wmp - wcv)*a
       emg(10, 12) = emg(10, 12) + d(7)*a
       bc = ev*(lv00 + 1846.d0*t1 - con_hvap) - (pd + ps + pl)*4185.5d0*t1 - pi*(1972.d0*t1 - li00 + con_hfus) &
          - emf(16, jj)*(1972.d0*t1 - li00 + con_hfus - 4185.5d0*t1)
       rf = d(1)+d(2)+d(3)+d(4) - frad - fpbl - fmp - con_hfus*emf(16, jj) + d(8) - bc
       emg(11, 12) = emg(11, 12) + rf*a
       emg(12, 12) = emg(12, 12) + abs(rf)*a
       emg(13, 12) = emg(13, 12) + sum(emsx(2:12, jj))*a
       emg(14, 12) = emg(14, 12) + abs(rf - sum(emsx(2:12, jj)))*a
       e0 = emc(1,1,jj) + emc(2,1,jj) + emc(3,1,jj) + emc(4,1,jj)
       emx(1) = emx(1) + e0*a
       emx(2) = emx(2) + emc(5,1,jj)*a
       emx(3:10) = emx(3:10) + emf(2:9, jj)*a
       emx(11) = emx(11) + (emf(10, jj) + emf(12, jj))*a
       emx(12) = emx(12) + a
    enddo
"""

if LAG:
    # EML kdt: lag = sum c_w P(N) (T1(N+1) - T1(N)) a (global, land-weighted), columns not matched, PH1 ice swap
    # sum csnow (c_l - c_i)(T1 - T0) a. P(N) from this step's exported precipitation; T1 = step-start tgrs(:,1).
    _r = [("    real(kind=8) :: buf(14*emnp+12), rbuf(14*emnp+12), lv00, li00\n",
           "    real(kind=8) :: buf(14*emnp+12), rbuf(14*emnp+12), lv00, li00, lbuf(4), lrbuf(4), cs\n"),
          ("          write(*,'(a,i6,12es25.16)') 'EMF ', emkdt(12), buf(14*emnp+1:)\n",
           "          write(*,'(a,i6,12es25.16)') 'EMF ', emkdt(12), buf(14*emnp+1:)\n"
           "          lbuf = eml\n"
           "          call MPI_Reduce(MPI_IN_PLACE, lbuf, 4, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
           "          write(*,'(a,i6,4es25.16)') 'EML ', emkdt(12), lbuf\n"),
          ("          call MPI_Reduce(buf, rbuf, size(buf), MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n",
           "          call MPI_Reduce(buf, rbuf, size(buf), MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
           "          lbuf = eml\n"
           "          call MPI_Reduce(lbuf, lrbuf, 4, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"),
          ("       emx = 0.d0\n    endif\n", "       emx = 0.d0\n       eml = 0.d0\n    endif\n"),
          ("       emx(12) = emx(12) + a\n",
           "       emx(12) = emx(12) + a\n"
           "       cs = emf(16, jj)\n"
           "       if (emla(jj) == a) then\n"
           "          eml(1) = eml(1) + emlp(jj)*(t1 - emlt(jj))*a\n"
           "          eml(2) = eml(2) + emlp(jj)*(t1 - emlt(jj))*a*frland(i)\n"
           "       else\n"
           "          eml(3) = eml(3) + 1.d0\n"
           "       endif\n"
           "       eml(4) = eml(4) + cs*(4185.5d0 - 1972.d0)*(t1 - 273.15d0)*a\n"
           "       emlp(jj) = 4185.5d0*(pl + pd + ps - cs) + 1972.d0*(pi + cs)\n"
           "       emlt(jj) = t1\n"
           "       emla(jj) = a\n")]
    for _a, _b in _r:
        assert FINAL_BODY.count(_a) == 1, _a
        FINAL_BODY = FINAL_BODY.replace(_a, _b)


def scheme(p):
    final = p == NP
    extra = EXTRA.get(p, [])
    names = [n for n, _ in COMMON] + [n for n, _ in extra] + [n for n, _ in TAIL]
    uses = "  use machine, only: kind_phys\n  use energy_meter_common\n"
    if p == 3:
        uses += ("  use module_radsw_parameters, only: topfsw_type, sfcfsw_type\n"
                 "  use module_radlw_parameters, only: topflw_type, sfcflw_type\n")
    if final:
        uses += "  use mpi_f08\n"
    call = ("\n    call em_probe(%d, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &\n"
            "                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, tgrs, j0)\n" % p)
    store = {3: ("       emf(2, j0+i) = dtp*xmu(i)*(topfsw(i)%dnfxc - topfsw(i)%upfxc)\n"
                 "       emf(3, j0+i) = -dtp*topflw(i)%upfxc\n"
                 "       emf(4, j0+i) = dtp*xmu(i)*(sfcfsw(i)%dnfxc - sfcfsw(i)%upfxc)\n"
                 "       emf(5, j0+i) = dtp*(sfcflw(i)%dnfxc - sfcflw(i)%upfxc)\n"
                 "       emf(6, j0+i) = dtp*adjsfcnsw(i)\n       emf(7, j0+i) = dtp*adjsfcdlw(i)\n"
                 "       emf(1, j0+i) = emf(2, j0+i) + emf(3, j0+i) - emf(4, j0+i) - emf(5, j0+i)\n"),
             5: "       emf(8, j0+i) = dtp*dtsfc1(i)\n       emf(9, j0+i) = dtp*dqsfc1(i)\n" + (
                "       call em_sxp(5, j0+i, levs, pflx_pbll(i,:), 4185.5d0, tgrs(i,:))\n"
                "       call em_sxp(5, j0+i, levs, pflx_pbli(i,:), 1972.d0, tgrs(i,:))\n" if PBLFLX else ""),
             8: "       emf(14, j0+i) = 1000.d0*rainc(i)\n       call em_sxp(8, j0+i, levs, pflx_dc(i,:), 4185.5d0, tgrs(i,:))\n",
             9: "       emf(15, j0+i) = 1000.d0*rainc(i)\n       call em_sxp(9, j0+i, levs, pflx_sc(i,:), 4185.5d0, tgrs(i,:))\n",
             11: ("       emf(10, j0+i) = 1000.d0*prcp(i)\n"
                  "       emf(11, j0+i) = 1000.d0*(snow(i) + ice(i) + graupel(i))\n"
                  "       emf(12, j0+i) = 1000.d0*rainc(i)\n"
                  "       call em_sxp(11, j0+i, levs, pflx_mpl(i,:), 4185.5d0, tgrs(i,:))\n"
                  "       call em_sxp(11, j0+i, levs, pflx_mpi(i,:), 1972.d0, tgrs(i,:))\n"
                  + ("       emf(16, j0+i) = 0.d0\n       if (tsfc(i) < 273.15d0) emf(16, j0+i) = 1000.d0*rainc(i)\n" if PH1 else ""))}
    if final:
        body = FINAL_BODY
    elif p in store:
        body = call + "    do i = 1, im\n" + store[p] + "    enddo\n"
    else:
        body = call
    decls = "\n".join("    " + decl(n) for n in names)
    nm = f"em_p{p:02d}"
    arglines = []
    cur = ""
    for n in names:
        if len(cur) + len(n) > 80:
            arglines.append(cur)
            cur = ""
        cur += n + ", "
    arglines.append(cur.rstrip(", "))
    args = " &\n       ".join(arglines)
    f90 = (f"!> \\file {nm}.F90\n!! Energy meter probe {p} (diagnostic builds only).\nmodule {nm}\n{uses}  implicit none\n"
           f"contains\n!> \\section arg_table_{nm}_run Argument Table\n!! \\htmlinclude {nm}_run.html\n!!\n"
           f"  subroutine {nm}_run({args})\n{decls}\n    integer :: j0, i\n{body}\n"
           f"    errmsg = ''\n    errflg = 0\n  end subroutine {nm}_run\nend module {nm}\n")
    deps = "../../hooks/machine.F,energy_meter_common.F90"
    if p == 3:
        deps += ",../../Radiation/RRTMG/radsw_param.f,../../Radiation/RRTMG/radlw_param.f"
    meta = [f"[ccpp-table-properties]\n  name = {nm}\n  type = scheme\n  dependencies = {deps}\n",
            f"[ccpp-arg-table]\n  name = {nm}_run\n  type = scheme"]
    for n, std in COMMON + extra + TAIL:
        b = block(std)
        b[0] = f"[{n}]"
        intent = "out" if n in ("errmsg", "errflg") else "in"
        meta.append("\n".join(b) + f"\n  intent = {intent}")
    (idir / f"{nm}.F90").write_text(f90)
    (idir / f"{nm}.meta").write_text("\n".join(meta) + "\n")
    return nm


(idir / "energy_meter_common.F90").write_text(COMMON_F90)
names = [scheme(p) for p in range(1, NP + 1)]

s = suite.read_text()
if "em_p01" not in s:
    for p, after in AFTER.items():
        old = f"<scheme>{after}</scheme>"
        if s.count(old) != 1:
            sys.exit(f"ABORT suite: {old} found {s.count(old)}")
        s = s.replace(old, old + f"\n      <scheme>em_p{p:02d}</scheme>")
    suite.write_text(s)

c = cfg.read_text()
if "em_p01" not in c:
    old = "    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90',\n"
    if c.count(old) != 1:
        sys.exit("ABORT cfg anchor")
    c = c.replace(old, old + "".join(f"    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/{n}.F90',\n" for n in names))
    cfg.write_text(c)

# capgen scheme metadata list
cm = root / "CMakeLists.txt"
c = cm.read_text()
if "em_p01" not in c:
    old = '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.meta"\n'
    if c.count(old) != 1:
        sys.exit("ABORT cmake anchor")
    c = c.replace(old, old + "".join(f'  "${{SCHEME_FILES_DIR}}/Interstitials/UFS_SCM_NEPTUNE/{n}.meta"\n' for n in names))
    cm.write_text(c)
print("probes:", " ".join(names))
