#!/usr/bin/env python3
"""Suites meter (diagnostic builds only): exact per-process water, passive-tracer and energy budgets in
FV3_GFS_v17_p8_mynn, FV3_GFS_v16_gfdlmpv3 and FV3_RAP, plus scheme-internal terms in MYNN-EDMF, GF and GFDL MP v3.
Usage: instrument_sm.py <ufs-weather-model>
Every anchor must match exactly once, else nothing is written.

Probe schemes sm{m,g,r}_pNN (Interstitials/UFS_SCM_NEPTUNE, common module suites_meter_common.F90) follow the
schemes in PROBES. Each stores per column the effective state X = X0 + dtp*(pending process-split tendency),
layer mass m = (prsi(k)-prsi(k+1))/g:
  1 W (all water species)  2 cp*T  3 hvap*qv  4 -hfus*(qi+qs+qg)  5 KE  6 frame-F enthalpy (energy report 9.1)
  7 passive tracer u (index env SM_NTU)  8 passive tracer s (SM_NTS)  9 sum m*|q_u - 1e-6|  10 T(1)  11 Wv  12 Wice
Boundary fluxes are captured at the probe that ends the scheme's segment (per column, kg m-2 or J m-2 per step):
  1 SH*dt  2 E*dt = dqsfc1/hvap*dt  3 deep convective P  4 shallow convective P  5 MP P (all)  6 MP P frozen
The last probe reduces (MPI_Gather, summed on root in rank order: deterministic) and prints per step:
  SMS kdt seg  dW Wflux rW sum|rW| dEP FP rEP dKE dEF FF rEF dTu dTs dDev   (seg np = whole physics, np+1 = dyn)
  SMT kdt  W Tu Ts area            (state at probe 1)
  SMX kdt  x(1:32)                 (scheme-internal terms, area-weighted, kg or J)
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp"
phys = root / "physics/physics"
idir = phys / "Interstitials/UFS_SCM_NEPTUNE"
cfg = root / "config/ccpp_prebuild_config_fv3.py"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


metas = sorted(phys.rglob("*.meta")) + sorted((root / "data").glob("*.meta"))


def block(std):
    for m in metas:
        txt = m.read_text(errors="ignore")
        for b in re.split(r"\n(?=\[)", txt):
            if re.search(r"^\s*standard_name\s*=\s*" + re.escape(std) + r"\s*$", b, re.M) and b.startswith("[") \
                    and "ccpp-" not in b.splitlines()[0]:
                return [l for l in b.strip().splitlines() if not l.strip().startswith("intent")
                        and not l.strip().startswith("optional")]
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
          ("xlon", "longitude"), ("xlat", "latitude")]
ROLE_ARGS = {"pbl": [("dtsfc1", "instantaneous_surface_upward_sensible_heat_flux"),
                     ("dqsfc1", "instantaneous_surface_upward_latent_heat_flux")],
             "dcnv": [("rain1", "lwe_thickness_of_deep_convective_precipitation_amount")],
             "scnv": [("raincs", "lwe_thickness_of_shallow_convective_precipitation_amount")],
             "mp": [("prcp", "lwe_thickness_of_explicit_precipitation_amount"),
                    ("snow", "lwe_thickness_of_snow_amount"), ("ice", "lwe_thickness_of_ice_amount"),
                    ("graupel", "lwe_thickness_of_graupel_amount")],
             "final": [("garea", "cell_area"), ("mpicomm", "mpi_communicator"), ("mpirank", "mpi_rank"),
                       ("mpiroot", "mpi_root")]}
ROLE_STORE = {"pbl": "       smf(1, p, j) = dtp*dtsfc1(i)\n       smf(2, p, j) = dtp*dqsfc1(i)/con_hvap\n",
              "dcnv": "       smf(3, p, j) = 1000.d0*rain1(i)\n",
              "scnv": "       smf(4, p, j) = 1000.d0*raincs(i)\n",
              "mp": "       smf(5, p, j) = 1000.d0*prcp(i)\n       smf(6, p, j) = 1000.d0*(snow(i) + ice(i) + graupel(i))\n"}
TAIL = [("errmsg", "ccpp_error_message"), ("errflg", "ccpp_error_code")]

# (suite xml, prefix, [(scheme the probe follows, role)], GF segment (s0, s1) or None)
PROBES = [
    ("suite_FV3_GFS_v17_p8_mynn.xml", "smm",
     [("GFS_suite_interstitial_1", ""), ("GFS_surface_generic_post", ""), ("mynnedmf_wrapper_post", "pbl"),
      ("GFS_GWD_generic_post", ""), ("GFS_DCNV_generic_post", "dcnv"), ("cnvc90", ""),
      ("GFS_MP_generic_post", "mp"), ("GFS_physics_post", "final")], None),
    ("suite_FV3_GFS_v16_gfdlmpv3.xml", "smg",
     [("GFS_suite_interstitial_1", ""), ("GFS_surface_generic_post", ""), ("GFS_PBL_generic_post", "pbl"),
      ("GFS_GWD_generic_post", ""), ("GFS_DCNV_generic_post", "dcnv"), ("GFS_SCNV_generic_post", "scnv"),
      ("cnvc90", ""), ("GFS_MP_generic_post", "mp"), ("GFS_physics_post", "final")], None),
    ("suite_FV3_RAP.xml", "smr",
     [("GFS_suite_interstitial_1", ""), ("GFS_surface_generic_post", ""), ("mynnedmf_wrapper_post", "pbl"),
      ("GFS_GWD_generic_post", ""), ("GFS_suite_interstitial_3", ""), ("GFS_DCNV_generic_post", "dcnv"),
      ("GFS_suite_interstitial_4", ""), ("cnvc90", ""), ("GFS_MP_generic_post", "mp"),
      ("GFS_physics_post", "final")], (5, 7)),
]

COMMON_F90 = r"""!> \file suites_meter_common.F90
!! Suites water/tracer/energy meter: storage, probe and deterministic reduction (diagnostic builds only).
module suites_meter_common
  use machine, only: kind_phys
  use mpi_f08
  implicit none
  private
  public :: sm_probe, sm_final
  integer, parameter, public :: smnp = 12, smnc = 4096, smnq = 12, smnf = 6, smnx = 48, smnv = 16
  real(kind=8), public, save :: smf(smnf, smnp, smnc) = 0.d0
  real(kind=8), public, save :: smxc(smnx, smnc) = 0.d0
  integer, public, save :: sm_jcur = 0
  real(kind=8), save :: smc(smnq, smnp, smnc) = 0.d0, smprev(smnq, smnc) = 0.d0
  real(kind=8), allocatable, save :: smd(:,:), smacc(:)
  integer, save :: smoff(smnp) = 0, smkdt(smnp) = -1, smntu = -2, smnts = -2
  integer, save :: smacc_kdt = -1, smncall = 0, smnblk = -1
  integer(kind=8), save :: smh(smnp) = 0
  integer, save :: smdk = -2, smdp = -1, smdu = -1
  logical, save :: smdopen = .false.
  logical, public, save :: sm_hook_snow = .false.
  logical, save :: smhp(smnc) = .false.
contains

  subroutine sm_probe(p, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                      ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, xlon, xlat, j0)
    integer, intent(in) :: p, im, levs, kdt, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl
    real(kind=kind_phys), intent(in) :: xlon(:), xlat(:)
    real(kind=kind_phys), intent(in) :: dtp, con_g, con_cp, con_hvap, con_hfus
    real(kind=kind_phys), intent(in) :: gt0(:,:), gq0(:,:,:), gu0(:,:), gv0(:,:), prsi(:,:)
    real(kind=kind_phys), intent(in) :: dtdt(:,:), dqdt(:,:,:), dudt(:,:), dvdt(:,:)
    integer, intent(out) :: j0
    real(kind=8), parameter :: cpa = 1004.6d0, cpv = 1846.0d0, cl = 4185.5d0, ci = 1972.0d0, t0 = 273.15d0
    real(kind=8) :: x(smnq), m, t, qv, ql, qi, u, v, qu, qs, lv00, li00
    integer :: i, k, ierr, mm, rk
    character(len=16) :: env
    character(len=32) :: fn
    if (smntu == -2) then
       smntu = -1
       smnts = -1
       call get_environment_variable('SM_NTU', env, status=ierr)
       if (ierr == 0) read(env, *) smntu
       call get_environment_variable('SM_NTS', env, status=ierr)
       if (ierr == 0) read(env, *) smnts
       if (smntu > size(gq0, 3)) smntu = -1
       if (smnts > size(gq0, 3)) smnts = -1
       smdk = -1
       call get_environment_variable('SM_DUMP_KDT', env, status=ierr)
       if (ierr == 0) read(env, *) smdk
       call get_environment_variable('SM_DUMP_P', env, status=ierr)
       if (ierr == 0) read(env, *) smdp
       call get_environment_variable('SM_HOOK_SNOW', env, status=ierr)
       sm_hook_snow = (ierr == 0)
    endif
    if (kdt /= smkdt(p)) then
       smkdt(p) = kdt
       smoff(p) = 0
    endif
    j0 = smoff(p)
    sm_jcur = j0
    lv00 = con_hvap - (cpv - cl)*t0
    li00 = con_hfus - (cl - ci)*t0
    if (.not. allocated(smd)) allocate(smd(levs, smnc))
    do i = 1, im
       x = 0.d0
       do k = 1, levs
          m = (prsi(i,k) - prsi(i,k+1))/con_g
          t = gt0(i,k) + dtp*dtdt(i,k)
          u = gu0(i,k) + dtp*dudt(i,k)
          v = gv0(i,k) + dtp*dvdt(i,k)
          qv = gq0(i,k,ntqv) + dtp*dqdt(i,k,ntqv)
          ql = gq0(i,k,ntcw) + dtp*dqdt(i,k,ntcw)
          if (ntrw > 0) ql = ql + gq0(i,k,ntrw) + dtp*dqdt(i,k,ntrw)
          qi = 0.d0
          if (ntiw > 0) qi = qi + gq0(i,k,ntiw) + dtp*dqdt(i,k,ntiw)
          if (ntsw > 0) qi = qi + gq0(i,k,ntsw) + dtp*dqdt(i,k,ntsw)
          if (ntgl > 0) qi = qi + gq0(i,k,ntgl) + dtp*dqdt(i,k,ntgl)
          x(1) = x(1) + m*(qv + ql + qi)
          x(2) = x(2) + m*con_cp*t
          x(3) = x(3) + m*con_hvap*qv
          x(4) = x(4) - m*con_hfus*qi
          x(5) = x(5) + m*0.5d0*(u*u + v*v)
          if (p == 1) smd(k, j0+i) = m*(1.d0 - qv - ql - qi)
          x(6) = x(6) + smd(k, j0+i)*cpa*t + m*((qv*cpv + ql*cl + qi*ci)*t + lv00*qv - li00*qi) &
               + (smd(k, j0+i) + m*(qv + ql + qi))*0.5d0*(u*u + v*v)
          if (smntu > 0) then
             qu = gq0(i,k,smntu) + dtp*dqdt(i,k,smntu)
             x(7) = x(7) + m*qu
             x(9) = x(9) + m*abs(qu - 1.d-6)
          endif
          if (smnts > 0) then
             qs = gq0(i,k,smnts) + dtp*dqdt(i,k,smnts)
             x(8) = x(8) + m*qs
          endif
          x(11) = x(11) + m*qv
          x(12) = x(12) + m*qi
       enddo
       x(10) = gt0(i,1) + dtp*dtdt(i,1)
       smc(:, p, j0+i) = x
       do mm = 1, smnq
          smh(p) = smh(p) + transfer(x(mm), 0_8)
       enddo
       if (kdt == smdk .and. (p == smdp .or. smdp < 0)) then
          if (.not. smdopen) then
             smdopen = .true.
             call MPI_Comm_rank(MPI_COMM_WORLD, rk, ierr)
             write(fn, '(a,i5.5,a)') 'sm_dump_', rk, '.txt'
             open(newunit=smdu, file=trim(fn), status='replace', action='write')
          endif
          write(smdu, '(i6,i3,2f12.6,14z17)') kdt, p, xlon(i)*57.29577951308232d0, xlat(i)*57.29577951308232d0, &
               (transfer(x(mm), 0_8), mm=1,smnq), transfer(gt0(i,1), 0_8), transfer(prsi(i,1), 0_8)
       endif
       smf(:, p, j0+i) = 0.d0
    enddo
    smoff(p) = j0 + im
  end subroutine sm_probe

  subroutine sm_reduce(kdt, np, mpicomm, mpirank, mpiroot)
    integer, intent(in) :: kdt, np, mpirank, mpiroot
    type(MPI_Comm), intent(in) :: mpicomm
    real(kind=8), allocatable :: all(:,:), tot(:)
    integer(kind=8) :: smhr(smnp)
    integer :: n, nr, r, s, ierr
    n = size(smacc)
    call MPI_Comm_size(mpicomm, nr, ierr)
    allocate(tot(n))
    if (mpirank == mpiroot) then
       allocate(all(n, nr))
    else
       allocate(all(1, 1))
    endif
    call MPI_Gather(smacc, n, MPI_DOUBLE_PRECISION, all, n, MPI_DOUBLE_PRECISION, mpiroot, mpicomm, ierr)
    if (mpirank == mpiroot) then
       call MPI_Reduce(MPI_IN_PLACE, smh, np, MPI_INTEGER8, MPI_SUM, mpiroot, mpicomm, ierr)
    else
       call MPI_Reduce(smh, smhr, np, MPI_INTEGER8, MPI_SUM, mpiroot, mpicomm, ierr)
    endif
    if (mpirank == mpiroot) then
       tot = 0.d0
       do r = 1, nr
          tot = tot + all(:, r)
       enddo
       do s = 1, np + 1
          write(*,'(a,i6,i3,16es24.15e3)') 'SMS ', kdt, s, tot(smnv*(s-1)+1:smnv*s)
       enddo
       write(*,'(a,i6,4es24.15e3)') 'SMT ', kdt, tot(smnv*(np+1)+1:smnv*(np+1)+4)
       write(*,'(a,i6,12z17)') 'SMH ', kdt, smh(1:np)
       write(*,'(a,i6,48es24.15e3)') 'SMX ', kdt, tot(smnv*(np+1)+5:smnv*(np+1)+4+smnx)
    endif
    deallocate(all, tot)
    smacc = 0.d0
    smh = 0
  end subroutine sm_reduce

  subroutine sm_final(np, gfs0, gfs1, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                      ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, xlon, xlat, garea, &
                      mpicomm, mpirank, mpiroot)
    integer, intent(in) :: np, gfs0, gfs1, im, levs, kdt, ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, mpirank, mpiroot
    real(kind=kind_phys), intent(in) :: dtp, con_g, con_cp, con_hvap, con_hfus
    real(kind=kind_phys), intent(in) :: gt0(:,:), gq0(:,:,:), gu0(:,:), gv0(:,:), prsi(:,:), garea(:), xlon(:), xlat(:)
    real(kind=kind_phys), intent(in) :: dtdt(:,:), dqdt(:,:,:), dudt(:,:), dvdt(:,:)
    type(MPI_Comm), intent(in) :: mpicomm
    real(kind=8), parameter :: cpv = 1846.0d0, cl = 4185.5d0, ci = 1972.0d0, t0 = 273.15d0
    real(kind=8) :: d(smnq), f(smnf), r(smnv), a, wf, fp, ff, t1, lv00, li00, dw
    integer :: i, j, j0, s, o, c
    lv00 = con_hvap - (cpv - cl)*t0
    li00 = con_hfus - (cl - ci)*t0
    if (.not. allocated(smacc)) then
       allocate(smacc(smnv*(np+1) + 4 + smnx))
       smacc = 0.d0
    endif
    if (kdt /= smacc_kdt) then
       if (smacc_kdt >= 0 .and. smnblk < 0) then
          smnblk = smncall
          call sm_reduce(smacc_kdt, np, mpicomm, mpirank, mpiroot)
       endif
       smacc_kdt = kdt
       smncall = 0
    endif
    call sm_probe(np, im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &
                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, xlon, xlat, j0)
    do i = 1, im
       j = j0 + i
       a = garea(i)
       do s = 1, np + 1
          if (s < np) then
             d = smc(:, s+1, j) - smc(:, s, j)
             f = smf(:, s+1, j)
             t1 = smc(10, s, j)
          elseif (s == np) then
             d = smc(:, np, j) - smc(:, 1, j)
             f = sum(smf(:, 2:np, j), dim=2)
             t1 = smc(10, 1, j)
          else
             if (.not. smhp(j)) cycle
             d = smc(:, 1, j) - smprev(:, j)
             f = 0.d0
             t1 = smprev(10, j)
          endif
          wf = f(2) - f(3) - f(4) - f(5)
          fp = f(1) + con_hvap*f(2) + con_hfus*f(6)
          ff = f(1) + f(2)*(lv00 + cpv*t1) - (f(3) + f(4) + f(5) - f(6))*cl*t1 - f(6)*(ci*t1 - li00)
          r(1) = d(1)
          r(2) = wf
          r(3) = d(1) - wf
          r(4) = abs(d(1) - wf)
          r(5) = d(2) + d(3) + d(4)
          r(6) = fp
          r(7) = r(5) - fp
          r(8) = d(5)
          r(9) = d(6)
          r(10) = ff
          r(11) = d(6) - ff
          r(12) = d(7)
          r(13) = d(8)
          r(14) = d(9)
          r(15) = d(12)
          r(16) = d(11)
          o = smnv*(s-1)
          smacc(o+1:o+smnv) = smacc(o+1:o+smnv) + r*a
       enddo
       o = smnv*(np+1)
       smacc(o+1) = smacc(o+1) + smc(1, 1, j)*a
       smacc(o+2) = smacc(o+2) + smc(7, 1, j)*a
       smacc(o+3) = smacc(o+3) + smc(8, 1, j)*a
       smacc(o+4) = smacc(o+4) + a
       ! GF host-frame water change by column class (smxc(22) = 1 shallow-only, 2 deep, 3 other)
       if (gfs0 > 0) then
          c = nint(smxc(22, j))
          dw = smc(1, gfs1, j) - smc(1, gfs0, j)
          if (c >= 1 .and. c <= 3) smxc(22+c, j) = dw
       endif
       smacc(o+5:o+4+smnx) = smacc(o+5:o+4+smnx) + smxc(:, j)*a
       smxc(:, j) = 0.d0
       smprev(:, j) = smc(:, np, j)
       smhp(j) = .true.
    enddo
    smncall = smncall + 1
    if (smncall == smnblk) call sm_reduce(kdt, np, mpicomm, mpirank, mpiroot)
  end subroutine sm_final
end module suites_meter_common
"""


def decl(n):
    real1 = ("dtsfc1", "dqsfc1", "rain1", "raincs", "prcp", "snow", "ice", "graupel", "garea")
    if n in real1:
        return f"real(kind=kind_phys), intent(in) :: {n}(:)"
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
        "mpicomm": "type(MPI_Comm), intent(in) :: mpicomm", "mpirank": "integer, intent(in) :: mpirank",
        "mpiroot": "integer, intent(in) :: mpiroot",
        "xlon": "real(kind=kind_phys), intent(in) :: xlon(:)", "xlat": "real(kind=kind_phys), intent(in) :: xlat(:)",
        "errmsg": "character(len=*), intent(out) :: errmsg", "errflg": "integer, intent(out) :: errflg"}[n]


CARGS = ("im, levs, kdt, dtp, gt0, gq0, gu0, gv0, dtdt, dqdt, dudt, dvdt, prsi, &\n"
         "                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, xlon, xlat")


def scheme(prefix, p, role, np, gfseg):
    extra = ROLE_ARGS.get(role, [])
    names = [n for n, _ in COMMON] + [n for n, _ in extra] + [n for n, _ in TAIL]
    uses = "  use machine, only: kind_phys\n  use suites_meter_common\n"
    if role == "final":
        uses += "  use mpi_f08\n"
        g0, g1 = gfseg or (0, 0)
        body = (f"\n    call sm_final({np}, {g0}, {g1}, {CARGS}, garea, &\n"
                "                  mpicomm, mpirank, mpiroot)\n")
    else:
        body = f"\n    call sm_probe({p}, {CARGS}, j0)\n"
        if role in ROLE_STORE:
            body += f"    p = {p}\n    do i = 1, im\n       j = j0 + i\n" + ROLE_STORE[role] + "    enddo\n"
    decls = "\n".join("    " + decl(n) for n in names)
    nm = f"{prefix}_p{p:02d}"
    arglines, cur = [], ""
    for n in names:
        if len(cur) + len(n) > 80:
            arglines.append(cur)
            cur = ""
        cur += n + ", "
    arglines.append(cur.rstrip(", "))
    args = " &\n       ".join(arglines)
    f90 = (f"!> \\file {nm}.F90\n!! Suites meter probe {p} (diagnostic builds only).\nmodule {nm}\n{uses}  implicit none\n"
           f"contains\n!> \\section arg_table_{nm}_run Argument Table\n!! \\htmlinclude {nm}_run.html\n!!\n"
           f"  subroutine {nm}_run({args})\n{decls}\n    integer :: j0, i, j, p\n{body}\n"
           f"    errmsg = ''\n    errflg = 0\n  end subroutine {nm}_run\nend module {nm}\n")
    meta = [f"[ccpp-table-properties]\n  name = {nm}\n  type = scheme\n"
            f"  dependencies = ../../hooks/machine.F,suites_meter_common.F90\n",
            f"[ccpp-arg-table]\n  name = {nm}_run\n  type = scheme"]
    for n, std in COMMON + extra + TAIL:
        b = block(std)
        b[0] = f"[{n}]"
        intent = "out" if n in ("errmsg", "errflg") else "in"
        meta.append("\n".join(b) + f"\n  intent = {intent}")
    edits[idir / f"{nm}.F90"] = f90
    edits[idir / f"{nm}.meta"] = "\n".join(meta) + "\n"
    return nm


edits[idir / "suites_meter_common.F90"] = COMMON_F90
names = []
for xml, prefix, probes, gfseg in PROBES:
    np = len(probes)
    suite = root / "suites" / xml
    for p, (after, role) in enumerate(probes, start=1):
        names.append(scheme(prefix, p, role, np, gfseg))
        old = f"<scheme>{after}</scheme>"
        sub(suite, old, old + f"\n      <scheme>{prefix}_p{p:02d}</scheme>")

c_old = "    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90',\n"
sub(cfg, c_old, c_old + "".join(f"    'physics/physics/Interstitials/UFS_SCM_NEPTUNE/{n}.F90',\n" for n in names))
cm = root / "CMakeLists.txt"
m_old = '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.meta"\n'
sub(cm, m_old, m_old + "".join(f'  "${{SCHEME_FILES_DIR}}/Interstitials/UFS_SCM_NEPTUNE/{n}.meta"\n' for n in names))

# ---------------- scheme-internal terms (smxc slots, per column, kg m-2 or J m-2 per step)
USE = "  use suites_meter_common, only: smxc, sm_jcur, sm_hook_snow\n"
DEP_REL = {"PBL/MYNN_EDMF": "../../Interstitials/UFS_SCM_NEPTUNE/suites_meter_common.F90",
           "CONV/Grell_Freitas": "../../Interstitials/UFS_SCM_NEPTUNE/suites_meter_common.F90",
           "MP/GFDL/v3_2022": "../../../Interstitials/UFS_SCM_NEPTUNE/suites_meter_common.F90"}
mynn = phys / "PBL/MYNN_EDMF/module_bl_mynn.F90"
wrap = phys / "PBL/MYNN_EDMF/mynnedmf_wrapper.F90"
wmeta = wrap.with_suffix(".meta")
gfd = phys / "CONV/Grell_Freitas/cu_gf_driver.F90"
gfmeta = gfd.with_suffix(".meta")
gmp = phys / "MP/GFDL/v3_2022/gfdl_cloud_microphys_v3.F90"
gmeta = gmp.with_suffix(".meta")

# MYNN module: 3 surface water source as solved (rho*dz frame), 4 driver's intended rho(kts)*flqv*dt,
# 5/6 rho*dz-frame water change before/after moisture_check, 8 dew limiter cut, 10 surface heating as solved
sub(mynn, "MODULE module_bl_mynn\n\n  use bl_mynn_common,only: &\n", "MODULE module_bl_mynn\n" + USE + "\n  use bl_mynn_common,only: &\n")
sub(mynn, "    d(k)=sqw(k)  + dtz(k)*rhosfc*flq*rhoinv(k) + qcd(k)*delt - dtz(k)*rhoinv(k)*s_awqt(k+1) - dtz(k)*rhoinv(k)*sd_awqt(k+1)\n",
    "    d(k)=sqw(k)  + dtz(k)*rhosfc*flq*rhoinv(k) + qcd(k)*delt - dtz(k)*rhoinv(k)*s_awqt(k+1) - dtz(k)*rhoinv(k)*sd_awqt(k+1)\n"
    "    smxc(3,sm_jcur+i) = smxc(3,sm_jcur+i) + delt*rhosfc*flq\n")
sub(mynn, "!rho-weighted:  rhosfc*X*rhoinv(k)\n",
    "!rho-weighted:  rhosfc*X*rhoinv(k)\n"
    "    smxc(3,sm_jcur+i) = smxc(3,sm_jcur+i) + delt*rhosfc*qvflux\n"
    "    smxc(4,sm_jcur+i) = smxc(4,sm_jcur+i) + delt*rho(kts)*flqv\n"
    "    smxc(8,sm_jcur+i) = smxc(8,sm_jcur+i) + delt*rhosfc*(qvflux - flqv)\n")
sub(mynn, "    d(k)=thl(k)  + dtz(k)*rhosfc*flt*rhoinv(k) + tcd(k)*delt &\n",
    "    smxc(10,sm_jcur+i) = smxc(10,sm_jcur+i) + delt*rhosfc*flt*cp*exner(kts)\n"
    "    d(k)=thl(k)  + dtz(k)*rhosfc*flt*rhoinv(k) + tcd(k)*delt &\n")
MCALL = "    !ensure non-negative moist species\n    CALL moisture_check(kte, delt,"
sub(mynn, MCALL,
    "    IF (sm_hook_snow) sqs2(kts) = sqs2(kts) - 1.e-7   ! TEST HOOK: forced snow fill\n"
    "    DO k=kts,kte\n"
    "       smxc(5,sm_jcur+i) = smxc(5,sm_jcur+i) + (Dqv(k)+Dqc(k)+Dqi(k)+Dqs(k))*delt*rho(k)*dz(k)\n"
    "       smxc(40,sm_jcur+i) = smxc(40,sm_jcur+i) - rho(k)*dz(k)*cp*exner(k)*thl(k)\n"
    "       smxc(41,sm_jcur+i) = smxc(41,sm_jcur+i) - rho(k)*dz(k)*(sqc2(k)+sqi2(k)+sqs2(k))\n    ENDDO\n" + MCALL)
_t = edits[mynn]
_c = _t.index(MCALL)
_cands = [a for a in ("    !=====================\n    ! OZONE TENDENCY CHECK\n", "    !===================\n    ! AEROSOL TENDENCIES\n") if _t.find(a, _c) >= 0]
_post = min(_cands, key=lambda a: _t.find(a, _c))
_j = _t.find(_post, _c)
edits[mynn] = _t[:_j] + ("    DO k=kts,kte\n"
    "       smxc(6,sm_jcur+i) = smxc(6,sm_jcur+i) + (Dqv(k)+Dqc(k)+Dqi(k)+Dqs(k))*delt*rho(k)*dz(k)\n"
    "       smxc(40,sm_jcur+i) = smxc(40,sm_jcur+i) + rho(k)*dz(k)*cp*exner(k)*thl(k)\n"
    "       smxc(41,sm_jcur+i) = smxc(41,sm_jcur+i) + rho(k)*dz(k)*(sqc2(k)+sqi2(k)+sqs2(k))\n    ENDDO\n") + _t[_j:]
# MYNN module energy (rho*dz frame, J m-2): 33 dissipative heating, 34 cp*exner*d(thl) incl. surface source
sub(mynn, "    ! THETA TENDENCY\n",
    "    DO k=kts,kte\n"
    "       smxc(33,sm_jcur+i) = smxc(33,sm_jcur+i) + rho(k)*dz(k)*cp*exner(k)*diss_heat(k)*delt\n"
    "       smxc(34,sm_jcur+i) = smxc(34,sm_jcur+i) + rho(k)*dz(k)*cp*exner(k)*(thl(k) - (th(k) &\n"
    "            - xlvcp/exner(k)*sqc(k) - xlscp/exner(k)*sqi(k)))\n"
    "    ENDDO\n"
    "    ! THETA TENDENCY\n")
# MYNN thl equation terms (J m-2, rho*dz frame, cp*exner weighted): 35 countergradient tcd, 36 sub+det,
# 37 explicit mass-flux, 38 implicit operator (x - rhs), 39 implicit operator without exner (theta-integral)
TRI = "    DO k=kts,kte\n       !thl(k)=d(k-kts+1)\n"
sub(mynn, TRI, 
    "    DO k=kts,kte\n"
    "       smxc(35,sm_jcur+i) = smxc(35,sm_jcur+i) + rho(k)*dz(k)*cp*exner(k)*tcd(k)*delt\n"
    "       smxc(36,sm_jcur+i) = smxc(36,sm_jcur+i) + rho(k)*dz(k)*cp*exner(k)*(sub_thl(k)+det_thl(k))*delt\n"
    "       smxc(38,sm_jcur+i) = smxc(38,sm_jcur+i) + rho(k)*dz(k)*cp*exner(k)*(x(k)-d(k))\n"
    "       smxc(39,sm_jcur+i) = smxc(39,sm_jcur+i) + rho(k)*dz(k)*cp*(x(k)-d(k))\n"
    "    ENDDO\n"
    "    smxc(37,sm_jcur+i) = smxc(37,sm_jcur+i) - rho(kts)*dz(kts)*cp*exner(kts)*dtz(kts)*rhoinv(kts) &\n"
    "         *(s_awthl(kts+1)+sd_awthl(kts+1))\n"
    "    DO k=kts+1,kte-1\n"
    "       smxc(37,sm_jcur+i) = smxc(37,sm_jcur+i) + rho(k)*dz(k)*cp*exner(k)*dtz(k)*rhoinv(k) &\n"
    "            *((s_awthl(k)-s_awthl(k+1)) + (sd_awthl(k)-sd_awthl(k+1)))\n"
    "    ENDDO\n" + TRI)
# MYNN wrapper: 1 E as reported (qfx*dt, after the clip), 2 before the clip, 7 host-frame water of its tendencies,
# 9 SH as reported, 11 host-frame cp*dT of its tendencies, 12 clip events
sub(wrap, "     use module_bl_mynn, only: mynn_bl_driver\n",
    "     use module_bl_mynn, only: mynn_bl_driver\n" + USE.replace("  use", "     use", 1))
sub(wrap, "         !filter bad incoming fluxes\n",
    "         smxc(2,sm_jcur+i) = qfx(i)*delt\n"
    "         smxc(46,sm_jcur+i) = qflx(i)*prsl(i,1)/(r_d*t3d(i,1)*(1.+p608*max(qgrs_water_vapor(i,1),1e-8)))*delt\n"
    "         if (qfx(i) > .0005 .or. qfx(i) < -.0002 .or. hfx(i) > 1200. .or. hfx(i) < -500.) &\n"
    "            smxc(12,sm_jcur+i) = smxc(12,sm_jcur+i) + 1.\n"
    "         !filter bad incoming fluxes\n")
sub(wrap, "         dtsfc1(i) = hfx(i)\n         dqsfc1(i) = qfx(i)*XLV\n",
    "         dtsfc1(i) = hfx(i)\n         dqsfc1(i) = qfx(i)*XLV\n"
    "         smxc(1,sm_jcur+i) = qfx(i)*delt\n         smxc(9,sm_jcur+i) = hfx(i)*delt\n")
sub(wrap, "       if(allocated(save_qke_adv)) then\n",
    "       do i=1,im\n"
    "          do k=1,levs\n"
    "             smxc(7,sm_jcur+i) = smxc(7,sm_jcur+i) + (RQVBLTEN(i,k)+RQCBLTEN(i,k)+RQIBLTEN(i,k)+RQSBLTEN(i,k)) &\n"
    "                  *delt*delp(i,k)/grav\n"
    "             smxc(11,sm_jcur+i) = smxc(11,sm_jcur+i) + RTHBLTEN(i,k)*exner(i,k)*cp*delt*delp(i,k)/grav\n"
    "          enddo\n"
    "       enddo\n"
    "       if(allocated(save_qke_adv)) then\n")
sub(wmeta, "  dependencies = ../../hooks/machine.F,module_bl_mynn.F90,bl_mynn_common.f90\n",
    "  dependencies = ../../hooks/machine.F,module_bl_mynn.F90,bl_mynn_common.f90\n"
    f"  dependencies = {DEP_REL['PBL/MYNN_EDMF']}\n")

# GF: 13-15 raincv by class (1 shallow-only = pret<=0 with cutens>0, 2 deep = pret>0, 3 other),
# 16/17 GF's own shallow precipitation in classes 1/2, 18 deep, 19 mid, 21 qv floor events, 20 condensate floor (mixing ratio),
# 22 class; 23-25 host-frame water change of the GF segment by class (filled by the final probe)
sub(gfd, "   use cu_gf_sh  , only: cu_gf_sh_run\n",
    "   use cu_gf_sh  , only: cu_gf_sh_run\n" + USE.replace("  use", "   use", 1))
sub(gfd, "               qv(i,k)=max(1.e-16,qv(i,k)+dt*(cutens(i)*outqs(i,k)+cutenm(i)*outqm(i,k)+outq(i,k)*cuten(i)))\n",
    "               if (qv(i,k)+dt*(cutens(i)*outqs(i,k)+cutenm(i)*outqm(i,k)+outq(i,k)*cuten(i)) < 1.e-16) &\n"
    "                  smxc(21,sm_jcur+i) = smxc(21,sm_jcur+i) + 1.\n"
    "               qv(i,k)=max(1.e-16,qv(i,k)+dt*(cutens(i)*outqs(i,k)+cutenm(i)*outqm(i,k)+outq(i,k)*cuten(i)))\n")
sub(gfd, "                new_cliw(i,k) = max(0.,cliw(i,k) + tem * tem1)            ! ice\n",
    "                smxc(20,sm_jcur+i) = smxc(20,sm_jcur+i) + max(0.,-(cliw(i,k) + tem * tem1)) &\n"
    "                                   + max(0.,-(clcw(i,k) + tem *(1.0-tem1)))\n"
    "                new_cliw(i,k) = max(0.,cliw(i,k) + tem * tem1)            ! ice\n")
sub(gfd, "! Diagnostic tendency updates\n",
    "        do i=its,itf\n"
    "          if (pret(i).gt.0.) then\n"
    "            smxc(22,sm_jcur+i) = 2.\n"
    "            smxc(17,sm_jcur+i) = cutens(i)*prets(i)*dt\n"
    "          elseif (cutens(i).gt.0.) then\n"
    "            smxc(22,sm_jcur+i) = 1.\n"
    "            smxc(16,sm_jcur+i) = cutens(i)*prets(i)*dt\n"
    "          else\n"
    "            smxc(22,sm_jcur+i) = 3.\n"
    "          endif\n"
    "          smxc(12+nint(smxc(22,sm_jcur+i)),sm_jcur+i) = 1000.*raincv(i)\n"
    "          smxc(18,sm_jcur+i) = cuten(i)*pret(i)*dt\n"
    "          smxc(19,sm_jcur+i) = cutenm(i)*pretm(i)*dt\n"
    "        enddo\n"
    "! Diagnostic tendency updates\n")
gsh = phys / "CONV/Grell_Freitas/cu_gf_sh.F90"
# GF shallow, own frame (before neg_check and cutens): 26 sum dp_GF/g*(outq+outqc)*dt, 27 pre*dt
sub(gsh, "module cu_gf_sh\n    use machine , only : kind_phys\n",
    "module cu_gf_sh\n    use machine , only : kind_phys\n" + USE.replace("  use", "    use", 1))
sub(gsh, "! since kinetic energy is being dissipated, add heating accordingly (from ecmwf)\n",
    "      do i=its,itf\n"
    "         if(ierr(i).eq.0) then\n"
    "            do k=kts,ktop(i)\n"
    "               dp=(po_cup(i,k)-po_cup(i,k+1))*100.\n"
    "               smxc(26,sm_jcur+i) = smxc(26,sm_jcur+i) + (outq(i,k)+outqc(i,k))*dp/g*dtime\n"
    "            enddo\n"
    "            smxc(27,sm_jcur+i) = smxc(27,sm_jcur+i) + pre(i)*dtime\n"
    "         endif\n"
    "      enddo\n"
    "! since kinetic energy is being dissipated, add heating accordingly (from ecmwf)\n")
# GF closure option (fixed trees only): 42 net-moistening column-steps, 43 water those columns would have added (kg m-2)
GCW = "        if (dw > 0. .and. pos > 0.) then\n          f = 1. - dw/pos\n"
if GCW in (edits.get(gfd) or gfd.read_text()):
    sub(gfd, GCW, "        if (dw > 0. .and. pos > 0.) then\n"
        "          smxc(42,sm_jcur+i) = smxc(42,sm_jcur+i) + 1.\n"
        "          smxc(43,sm_jcur+i) = smxc(43,sm_jcur+i) + dw*dt\n"
        "          f = 1. - dw/pos\n")
sub(gfmeta, "  dependencies = cu_gf_deep.F90,cu_gf_sh.F90\n",
    "  dependencies = cu_gf_deep.F90,cu_gf_sh.F90\n"
    f"  dependencies = {DEP_REL['CONV/Grell_Freitas']}\n")

# GFDL MP v3 driver: 28 scheme-frame water change (q_new*delp_new - q_old*del), 29 precipitation before the
# rainmin zeroing (incl. settled cloud water), 30 prcp0 as booked, 31 settled cloud water, 32 host-frame change
sub(gmp, "      use machine, only: kind_phys, kind_dyn, kind_dbl_prec\n",
    "      use machine, only: kind_phys, kind_dyn, kind_dbl_prec\n" + USE.replace("  use", "      use", 1))
sub(gmp, "      tem   = dtp*con_p001/con_secinday\n",
    "      tem   = dtp*con_p001/con_secinday\n"
    "      do i = 1, im\n"
    "         do k = 1, levs\n"
    "            kk = levs-k+1\n"
    "            smxc(32,sm_jcur+i) = smxc(32,sm_jcur+i) + ((qv1(i,kk)+ql1(i,kk)+qr1(i,kk)+qi1(i,kk)+qs1(i,kk)+qg1(i,kk)) &\n"
    "                 - (gq0(i,k)+gq0_ntcw(i,k)+gq0_ntrw(i,k)+gq0_ntiw(i,k)+gq0_ntsw(i,k)+gq0_ntgl(i,k)))*del(i,k)/con_g\n"
    "            smxc(28,sm_jcur+i) = smxc(28,sm_jcur+i) + ((qv1(i,kk)+ql1(i,kk)+qr1(i,kk)+qi1(i,kk)+qs1(i,kk)+qg1(i,kk))*delp(i,kk) &\n"
    "                 - (gq0(i,k)+gq0_ntcw(i,k)+gq0_ntrw(i,k)+gq0_ntiw(i,k)+gq0_ntsw(i,k)+gq0_ntgl(i,k))*del(i,k))/con_g\n"
    "         enddo\n"
    "         smxc(29,sm_jcur+i) = (rain0(i)+ice0(i)+snow0(i)+graupel0(i)+water0(i))*tem*1000.0\n"
    "         smxc(31,sm_jcur+i) = water0(i)*tem*1000.0\n"
    "      enddo\n")
# GFDL MP energy in frame F (44: FV3 c_l 4185.5, c_i 1972, T0 273.15) and in GFDL's own constants (45: c_l 4218,
# c_i 2106, T0 273.16): dE + precipitation enthalpy leaving at the new lowest-layer T (J m-2)
sub(gmp, "      integer :: i, k, kk\n",
    "      integer :: i, k, kk\n      real(kind=8) :: smcl, smci, smt0, smlv, smli, sme0, sme1, smm, smq0, smq1, smb\n      integer :: smf\n      real(kind=8) :: smp0, smp1, smphi\n")
GE = """      do i = 1, im
        do smf = 1, 2
          if (smf == 1) then
            smcl = 4185.5d0; smci = 1972.d0; smt0 = 273.15d0
          else
            smcl = 4218.d0; smci = 2106.d0; smt0 = 273.16d0
          endif
          smlv = 2.5d6 - (1846.d0 - smcl)*smt0
          smli = 3.3358d5 - (smcl - smci)*smt0
          sme0 = 0.d0; sme1 = 0.d0; smp0 = 0.d0; smp1 = 0.d0
          do k = 1, levs
            kk = levs-k+1
            smm = del(i,k)/con_g
            smq0 = gq0(i,k)+gq0_ntcw(i,k)+gq0_ntrw(i,k)+gq0_ntiw(i,k)+gq0_ntsw(i,k)+gq0_ntgl(i,k)
            smq1 = qv1(i,kk)+ql1(i,kk)+qr1(i,kk)+qi1(i,kk)+qs1(i,kk)+qg1(i,kk)
            smphi = 0.5d0*(phii(i,k)+phii(i,k+1))
            smp0 = smp0 + smm*smq0*smphi
            smp1 = smp1 + smm*smq1*smphi
            sme0 = sme0 + smm*(1.d0-smq0)*1004.6d0*gt0(i,k) + smm*((gq0(i,k)*1846.d0 + (gq0_ntcw(i,k)+gq0_ntrw(i,k))*smcl &
                 + (gq0_ntiw(i,k)+gq0_ntsw(i,k)+gq0_ntgl(i,k))*smci)*gt0(i,k) + smlv*gq0(i,k) &
                 - smli*(gq0_ntiw(i,k)+gq0_ntsw(i,k)+gq0_ntgl(i,k))) + smm*0.5d0*(gu0(i,k)**2+gv0(i,k)**2)
            sme1 = sme1 + smm*(1.d0-smq0)*1004.6d0*pt(i,kk) + smm*((qv1(i,kk)*1846.d0 + (ql1(i,kk)+qr1(i,kk))*smcl &
                 + (qi1(i,kk)+qs1(i,kk)+qg1(i,kk))*smci)*pt(i,kk) + smlv*qv1(i,kk) &
                 - smli*(qi1(i,kk)+qs1(i,kk)+qg1(i,kk))) + smm*(1.d0-smq0+smq1)*0.5d0*(uin(i,kk)**2+vin(i,kk)**2)
          enddo
          smb = 1000.d0*rain0(i)*smcl*pt(i,levs) + 1000.d0*(snow0(i)+ice0(i)+graupel0(i))*(smci*pt(i,levs) - smli) &
              + 1000.d0*(rain0(i)+snow0(i)+ice0(i)+graupel0(i))*0.5d0*(uin(i,levs)**2+vin(i,levs)**2)
          smxc(43+smf,sm_jcur+i) = smxc(43+smf,sm_jcur+i) + sme1 - sme0 + smb
          smxc(46+smf,sm_jcur+i) = smxc(46+smf,sm_jcur+i) + sme1 - sme0 + smb + smp1 - smp0
        enddo
      enddo
"""
sub(gmp, "      do k=1,levs\n        kk = levs-k+1\n        do i=1,im\n           ten_qv(i,k)", GE + "      do k=1,levs\n        kk = levs-k+1\n        do i=1,im\n           ten_qv(i,k)")
sub(gmp, "      water0    = water0*tem\n",
    "      do i = 1, im\n         smxc(30,sm_jcur+i) = prcp0(i)*1000.0\n      enddo\n      water0    = water0*tem\n")
sub(gmeta, "  dependencies = gfdl_cloud_microphys_v3_mod.F90\n",
    "  dependencies = gfdl_cloud_microphys_v3_mod.F90\n"
    f"  dependencies = {DEP_REL['MP/GFDL/v3_2022']}\n")

for path, s in edits.items():
    path.write_text(s)
print("suites meter:", len(names), "probes;", len(edits), "files written")
