#!/usr/bin/env python3
"""Tracer-mass meters (diagnostic builds only). Usage: instrument_tm.py <ufs-weather-model tree> <tm_meter.F90>
Points (rank sums, gathered and Neumaier-summed on root, printed 'TM step ip m(0:nq+1)', Pa m2):
 1 A atmosphere_dynamics start | 2/5 B before dyn_core (n_map 1/2) | 3/6 C after tracer_2d | 4/7 D after
 Lagrangian_to_Eulerian | 8 E before neg_adj3 | 9 F after neg_adj3 | 10 G after p_split loop | 11 H after
 fv_subgrid_z | 12 I state_update start | 13 J physics in (qgrs, physics dp) | 14 K physics out (gq0) |
 15 L after fill_gfs | 16 M after nopbl override | 17 N after write-back (dyn frame) | 18 O after fv_update_phys
Physics slots (cumulative change, 'TP step slot ...'): 1 GFS_DCNV_generic_post, 2 GFS_SCNV_generic_post,
 3 GFS_GWD_generic_post (applies surface+PBL+GWD tendencies). 'TU' = global min/max of pt_udry dry ratio, pt_umoist.
Every anchor must match exactly once."""
import sys, shutil
from pathlib import Path

top = Path(sys.argv[1]); meter_src = Path(sys.argv[2])
fv3 = top / "UFSATM/fv3/atmos_cubed_sphere"
dyn = fv3 / "model/fv_dynamics.F90"
atm = fv3 / "driver/UFS/atmosphere.F90"
inter = top / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


shutil.copy(meter_src, inter / "tm_meter.F90")

# ---------------- physics post schemes ----------------
META_ADD = """[tm_prsi]
  standard_name = air_pressure_at_interface
  long_name = air pressure at model layer interfaces
  units = Pa
  dimensions = (horizontal_loop_extent,vertical_interface_dimension)
  type = real
  kind = kind_phys
  intent = in
[tm_area]
  standard_name = cell_area
  long_name = area of the grid cell
  units = m2
  dimensions = (horizontal_loop_extent)
  type = real
  kind = kind_phys
  intent = in
[tm_qgrs]
  standard_name = physics_timestep_initial_tracer_concentration
  long_name = tracer concentration at the start of the physics time step
  units = kg kg-1
  dimensions = (horizontal_loop_extent,vertical_layer_dimension,number_of_tracers)
  type = real
  kind = kind_phys
  intent = in
[errmsg]
"""
for slot, (name, sel, endsel) in enumerate([
        ("GFS_DCNV_generic_post", "      case_DCNV_ten: select case (tend_opt_dcnv)\n", "      end select case_DCNV_ten"),
        ("GFS_SCNV_generic_post", "      case_SCNV_ten: select case (tend_opt_scnv)\n", "      end select case_SCNV_ten\n"),
        ("GFS_GWD_generic_post", "      case_GWD_ten: select case (tend_opt_gwd)\n", "      end select case_GWD_ten\n")], start=1):
    f90 = inter / f"{name}.F90"; meta = inter / f"{name}.meta"
    sub(meta, "  dependencies = ../../hooks/machine.F\n", "  dependencies = ../../hooks/machine.F,tm_meter.F90\n")
    sub(meta, "[errmsg]\n", META_ADD)
    sub(f90, "errmsg, errflg)\n", "tm_prsi, tm_area, tm_qgrs, errmsg, errflg)\n")
    sub(f90, "      implicit none\n",
        "      use tm_meter, only: tm_phys_mass, tm_phys_add, tm_iu, tm_ucheck, tm_iud, tm_icnv, tm_dry_phys, tm_dry_slot, tm_osc_check\n      implicit none\n"
        "      real(kind=kind_phys), intent(in) :: tm_prsi(:,:), tm_area(:), tm_qgrs(:,:,:)\n"
        "      real(8), allocatable :: tm_s0(:,:), tm_s1(:,:), tm_u0(:,:), tm_xq(:,:), tm_xt(:,:), tm_xc(:,:)\n"
        "      real(8) :: tm_r0(3), tm_r1(3)\n")
    sub(f90, sel, "      allocate(tm_s0(2,0:ntrac+1), tm_s1(2,0:ntrac+1))\n"
        "      call tm_phys_mass(im, levs, ntrac, gq0, tm_prsi, tm_area, tm_s0)\n"
        "      if (tm_iu > 0) tm_u0 = gq0(1:im,:,tm_iu)\n"
        "      if (tm_iud > 0) call tm_dry_phys(im, levs, gq0(1:im,:,tm_iud), tm_qgrs(1:im,:,1), tm_prsi, tm_area, tm_r0)\n"
        + ("      tm_xq = gq0(1:im,:,1); tm_xt = gt0(1:im,:)\n      if (tm_icnv > 0) tm_xc = gq0(1:im,:,tm_icnv)\n" if slot == 1 else "")
        + sel)
    sub(f90, endsel, endsel.rstrip(" \n") + "\n"
        "      call tm_phys_mass(im, levs, ntrac, gq0, tm_prsi, tm_area, tm_s1)\n"
        f"      call tm_phys_add({slot}, ntrac, tm_s0, tm_s1)\n"
        f"      if (tm_iu > 0) call tm_ucheck({slot}, im, levs, tm_u0, gq0(1:im,:,tm_iu))\n"
        "      if (tm_iud > 0) call tm_dry_phys(im, levs, gq0(1:im,:,tm_iud), tm_qgrs(1:im,:,1), tm_prsi, tm_area, tm_r1)\n"
        f"      if (tm_iud > 0) call tm_dry_slot({slot}, tm_r0, tm_r1)\n"
        + ("      call tm_osc_check(1, im, tm_xq, gq0(1:im,:,1)); call tm_osc_check(2, im, tm_xt, gt0(1:im,:))\n"
           "      if (tm_iu > 0) call tm_osc_check(3, im, tm_u0, gq0(1:im,:,tm_iu))\n"
           "      if (tm_icnv > 0) call tm_osc_check(4, im, tm_xc, gq0(1:im,:,tm_icnv))\n" if slot == 1 else ""))

# ---------------- SAMF deep Courant meter ----------------
conv = top / "UFSATM/ccpp/physics/physics/CONV/SAMF"
sub(conv / "samfdeepcnv.f", "      use machine , only : kind_phys\n      use funcphys , only : fpvs\n\n      implicit none\n",
    "      use machine , only : kind_phys\n      use funcphys , only : fpvs\n      use tm_meter, only : tm_cfl_deep\n\n      implicit none\n")
sub(conv / "samfdeepcnv.f", "      if (.not.hwrf_samfdeep) then\n       indx = ntk - 2\n       do n = 1, ntr\n",
    "      call tm_cfl_deep(im,km,cnvflg,kb,jmin,ktcon,eta,etad,edto,\n"
    "     &     xmb,del,dt2)\n"
    "      if (.not.hwrf_samfdeep) then\n       indx = ntk - 2\n       do n = 1, ntr\n")

# ---------------- fv_dynamics ----------------
DM = "call tm_dyn_rec({ip}, isd, jsd, is, ie, js, je, npz, nq, nwat, q, delp, gridstruct%area_64)\n"
sub(dyn, "   use fv_sg_mod,           only: neg_adj3, neg_adj2, neg_adj4\n",
    "   use fv_sg_mod,           only: neg_adj3, neg_adj2, neg_adj4\n   use tm_meter,            only: tm_dyn_rec\n")
sub(dyn, "      if ( flagstruct%trdm2 > 1.e-4 ) then\n         call start_group_halo_update(i_pack(13), dp1, domain)\n      endif\n",
    "      if ( flagstruct%trdm2 > 1.e-4 ) then\n         call start_group_halo_update(i_pack(13), dp1, domain)\n      endif\n"
    "      " + DM.format(ip="2+3*(min(n_map,2)-1)"))
sub(dyn, "                                             call timing_off('tracer_2d')\n",
    "                                             call timing_off('tracer_2d')\n      " + DM.format(ip="3+3*(min(n_map,2)-1)"))
sub(dyn, "                                                  call timing_off('Remapping')\n\n     if ( flagstruct%molecular_diffusion ) then\n",
    "                                                  call timing_off('Remapping')\n      " + DM.format(ip="4+3*(min(n_map,2)-1)")
    + "\n     if ( flagstruct%molecular_diffusion ) then\n")
sub(dyn, "  if( nwat == 6 ) then\n     if (cld_amt > 0) then\n      call neg_adj3(",
    "  " + DM.format(ip="8") + "  if( nwat == 6 ) then\n     if (cld_amt > 0) then\n      call neg_adj3(")
sub(dyn, "  if( nwat == 5 ) then\n     if (cld_amt > 0) then\n      call neg_adj2(",
    "  " + DM.format(ip="9") + "  if( nwat == 5 ) then\n     if (cld_amt > 0) then\n      call neg_adj2(")

# ---------------- atmosphere.F90 ----------------
WA = ("call tm_dyn_rec({ip}, isd, jsd, isc, iec, jsc, jec, npz, nq, Atm(n)%flagstruct%nwat, Atm(n)%q, Atm(n)%delp, "
      "Atm(n)%gridstruct%area_64)\n")
sub(atm, "use fv_update_phys_mod, only: fv_update_phys\n",
    "use fv_update_phys_mod, only: fv_update_phys\nuse tm_meter,          only: tm_dyn_rec, tm_phys_mass, tm_pt_zero, tm_pt_add, "
    "tm_pts, tm_acc, tm_np, tm_nslot, tm_neu, tm_iu, tm_umax, tm_cfl, &\n"
    "                              tm_iud, tm_icnv, tm_dr, tm_drs, tm_dry_phys, tm_osc, tm_cflh\n")
sub(atm, "   do psc=1,abs(p_split)\n", "   tm_iud = max(get_tracer_index(MODEL_ATMOS, 'pt_udry'), 0); tm_icnv = max(get_tracer_index(MODEL_ATMOS, 'pt_cnv'), 0)\n"
    "   tm_iu = max(get_tracer_index(MODEL_ATMOS, 'pt_umoist'), 0)\n"
    "   " + WA.format(ip=1) + "   do psc=1,abs(p_split)\n")
sub(atm, "    enddo !p_split\n", "    enddo !p_split\n    " + WA.format(ip=10))
sub(atm, "   call mpp_clock_end (id_subgridz)\n\n end subroutine atmosphere_dynamics\n",
    "   " + WA.format(ip=11) + "   call mpp_clock_end (id_subgridz)\n\n end subroutine atmosphere_dynamics\n")
# state update
sub(atm, "   real psum, qsum, psumb, qsumb, betad\n   character(len=32) :: tracer_name\n",
    "   real psum, qsum, psumb, qsumb, betad\n   character(len=32) :: tracer_name\n"
    "   real(8), allocatable :: tm_bs(:,:,:,:), tm_ar(:), tm_bd(:,:,:)\n   integer :: tm_b\n")
sub(atm, "   if( nq<3 ) call mpp_error(FATAL, 'GFS phys must have 3 interactive tracers')\n\n   if (IAU_Data%in_interval) then\n",
    "   if( nq<3 ) call mpp_error(FATAL, 'GFS phys must have 3 interactive tracers')\n\n"
    "   " + WA.format(ip=12) +
    "   allocate(tm_bs(2,0:nq+1,4,Atm_block%nblks), tm_ar(IPD_control%chunk_end(Atm_block%nblks)), tm_bd(3,4,Atm_block%nblks))\n"
    "   tm_bd = 0.d0\n"
    "   do nb = 1, Atm_block%nblks\n"
    "     do ix = 1, Atm_block%blksz(nb)\n"
    "       tm_ar(IPD_control%chunk_begin(nb)+ix-1) = Atm(n)%gridstruct%area_64(Atm_block%index(nb)%ii(ix),Atm_block%index(nb)%jj(ix))\n"
    "     enddo\n"
    "   enddo\n\n"
    "   if (IAU_Data%in_interval) then\n")
sub(atm, "snowwat, graupel, nq_adv, flip_vc, ke_tgt, dt_atmos)   &\n", "snowwat, graupel, nq_adv, flip_vc, ke_tgt, dt_atmos, tm_bs, tm_ar, tm_bd, tm_iud)   &\n")
sub(atm, "private (nb, blen, i, j, k, k1, ix, im, q0, qwat, qt, tracer_name, qp, ub, vb, ua0, va0, dpp)",
    "private (nb, blen, i, j, k, k1, ix, im, q0, qwat, qt, tracer_name, qp, ub, vb, ua0, va0, dpp, tm_b)")
TB = ("     call tm_phys_mass(blen, npz, nq, {arr}(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb),:,:), "
      "IPD_Statein%prsi(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb),:), "
      "tm_ar(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb)), tm_bs(:,:,{s},nb))\n"
      "     if (tm_iud > 0) call tm_dry_phys(blen, npz, {arr}(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb),:,tm_iud), "
      "IPD_Statein%qgrs(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb),:,1), "
      "IPD_Statein%prsi(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb),:), "
      "tm_ar(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb)), tm_bd(:,{s},nb))\n")
FILL = ("     if (Atm(n)%flagstruct%fill_gfs) call fill_gfs(blen, npz, IPD_Statein%prsi(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb),:), &\n"
        "                                                   IPD_Stateout%gq0(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb),:,:), 1.e-9_kind_phys)\n")
sub(atm, FILL, TB.format(arr="IPD_Statein%qgrs", s=1) + TB.format(arr="IPD_Stateout%gq0", s=2) + FILL
    + TB.format(arr="IPD_Stateout%gq0", s=3))
sub(atm, "     enddo\n\n\n     if (Atm(n)%flagstruct%cpl_water_energy > 0) call cpl_water_energy(",
    "     enddo\n" + TB.format(arr="IPD_Stateout%gq0", s=4) + "\n\n     if (Atm(n)%flagstruct%cpl_water_energy > 0) call cpl_water_energy(")
sub(atm, "   enddo  ! nb-loop\n",
    "   enddo  ! nb-loop\n"
    "   do tm_b = 1, 4\n"
    "     call tm_pt_zero(12+tm_b)\n"
    "     do nb = 1, Atm_block%nblks\n"
    "       call tm_pt_add(12+tm_b, nq, tm_bs(:,:,tm_b,nb))\n"
    "     enddo\n"
    "   enddo\n"
    "   do tm_b = 1, 4\n"
    "     tm_dr(:,12+tm_b) = 0.d0\n"
    "     do nb = 1, Atm_block%nblks\n"
    "       tm_dr(1:2,12+tm_b) = tm_dr(1:2,12+tm_b) + tm_bd(1:2,tm_b,nb)\n"
    "       tm_dr(3,12+tm_b) = max(tm_dr(3,12+tm_b), tm_bd(3,tm_b,nb))\n"
    "     enddo\n"
    "   enddo\n"
    "   deallocate(tm_bs, tm_ar, tm_bd)\n"
    "   " + WA.format(ip=17))
sub(atm, "       call timing_off('FV_UPDATE_PHYS')\n   call mpp_clock_end (id_dynam)\n",
    "       call timing_off('FV_UPDATE_PHYS')\n   call mpp_clock_end (id_dynam)\n"
    "   " + WA.format(ip=18) + "   call tm_report(Atm(n), nq)\n")
REPORT = """
 !> tracer-mass meter report (diagnostic builds only): gather rank Neumaier pairs, sum on root in PE order
 subroutine tm_report(A, nq)
   use mpp_mod, only: mpp_gather, mpp_npes, mpp_pe, mpp_root_pe, mpp_min, mpp_max, mpp_sum
   type(fv_atmos_type), intent(in) :: A
   integer, intent(in) :: nq
   integer, save :: tm_step = 0
   integer :: nv, r, ip, m, iu, im, nw, i, j, k, off
   real(8), allocatable :: sb(:), rb(:)
   real(8) :: s(2), v(0:nq+1), vl(0:nq+1), u(4), qd, um(4, tm_nslot), tm_t8(8)
   tm_step = tm_step + 1
   nv = 2*(nq+2)*(tm_np + tm_nslot)
   allocate(sb(nv), rb(nv*mpp_npes()))
   sb(1:2*(nq+2)*tm_np) = reshape(tm_pts(:, 0:nq+1, :), (/2*(nq+2)*tm_np/))
   sb(2*(nq+2)*tm_np+1:nv) = reshape(tm_acc(:, 0:nq+1, :), (/2*(nq+2)*tm_nslot/))
   rb = 0.d0
   call mpp_gather(sb, rb)
   if (mpp_pe() == mpp_root_pe()) then
     do ip = 1, tm_np + tm_nslot
       do m = 0, nq+1
         s = 0.d0
         off = ((ip-1)*(nq+2) + m)*2
         do r = 0, mpp_npes()-1
           call tm_neu(s, rb(r*nv + off + 1))
           call tm_neu(s, rb(r*nv + off + 2))
         enddo
         v(m) = s(1) + s(2); vl(m) = s(2) - (v(m) - s(1))
       enddo
       if (ip <= tm_np) then
         if (ip <= 18) write(*,'(a,i5,i4,128es26.17e3)') 'TM ', tm_step, ip, (v(m), vl(m), m=0,nq+1)
       else
         if (ip - tm_np <= 3) write(*,'(a,i5,i4,128es26.17e3)') 'TP ', tm_step, ip - tm_np, (v(m), vl(m), m=0,nq+1)
       endif
     enddo
   endif
   deallocate(sb, rb)
   iu = get_tracer_index(MODEL_ATMOS, 'pt_udry'); im = get_tracer_index(MODEL_ATMOS, 'pt_umoist')
   tm_iu = max(im, 0)
   um = tm_umax
   do ip = 1, 3
     qd = um(1,ip); call mpp_max(um(1,ip)); if (qd /= um(1,ip)) um(2,ip) = 0.d0
     call mpp_max(um(2,ip)); call mpp_sum(um(3,ip)); call mpp_sum(um(4,ip))
   enddo
   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i5,3(es12.4,f6.0,2es12.4))') 'TQ ', tm_step, um(:,1:3)
   tm_umax = 0.d0
   qd = tm_cfl(1); call mpp_max(tm_cfl(1)); if (qd /= tm_cfl(1)) tm_cfl(2) = 0.d0
   call mpp_max(tm_cfl(2)); call mpp_sum(tm_cfl(3)); call mpp_sum(tm_cfl(4))
   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i5,es12.4,f6.0,2f10.0)') 'TC ', tm_step, tm_cfl
   tm_cfl = 0.d0
   call mpp_sum(tm_cflh, 7)
   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i5,7f10.0)') 'TH ', tm_step, tm_cflh
   tm_cflh = 0.d0
   do ip = 1, 18
     call mpp_sum(tm_dr(1:2,ip), 2); call mpp_max(tm_dr(3,ip))
   enddo
   if (mpp_pe() == mpp_root_pe()) then
     do ip = 1, 18
       write(*,'(a,i5,i4,3es24.15)') 'TD ', tm_step, ip, tm_dr(:,ip)
     enddo
   endif
   do ip = 1, 3
     call mpp_sum(tm_drs(1,ip)); call mpp_max(tm_drs(2,ip))
   enddo
   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i5,6es24.15)') 'TS ', tm_step, tm_drs(:,1:3)
   tm_drs = 0.d0
   tm_t8 = reshape(tm_osc(1:2,:), (/8/)); call mpp_sum(tm_t8, 8); tm_osc(1:2,:) = reshape(tm_t8, (/2,4/))
   do ip = 1, 4
     call mpp_max(tm_osc(3,ip))
   enddo
   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i5,12es12.4)') 'TO ', tm_step, tm_osc
   tm_osc = 0.d0
   nw = A%flagstruct%nwat
   u = (/ huge(1.d0), -huge(1.d0), huge(1.d0), -huge(1.d0) /)
   do k = 1, A%npz
     do j = jsc, jec
       do i = isc, iec
         if (iu > 0) then
           qd = A%q(i,j,k,iu)/(1.d0 - sum(A%q(i,j,k,1:nw)))
           u(1) = min(u(1), qd); u(2) = max(u(2), qd)
         endif
         if (im > 0) then
           u(3) = min(u(3), A%q(i,j,k,im)); u(4) = max(u(4), A%q(i,j,k,im))
         endif
       enddo
     enddo
   enddo
   call mpp_min(u(1)); call mpp_max(u(2)); call mpp_min(u(3)); call mpp_max(u(4))
   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i5,4es26.17e3)') 'TU ', tm_step, u
 end subroutine tm_report
"""
sub(atm, " end subroutine atmosphere_state_update\n", " end subroutine atmosphere_state_update\n" + REPORT)

for path, s in edits.items():
    path.write_text(s)
    print(f"instrumented {path.relative_to(top)}")
