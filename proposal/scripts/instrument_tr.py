#!/usr/bin/env python3
"""Passive-tracer mass meters in the physics (TRP) and the FV3 dynamical core (PTM) (diagnostic builds only).
Usage: python3 instrument_tr.py <ufs_model.fd>     (apply to a copy of wbfinal, which already carries the WBP/WBD meters)
Tracers: field_table must put trpa and trpb at tracer indices 10 and 11, before sgs_tke (12); the model aborts otherwise.
Also makes satmedmfvdifq diffuse every tracer when TKE is the last tracer (CCPP_typedefs nvdiff = ntrac), which is what
the standard 10-tracer field_table already gets; without it, extra tracers are not diffused by the boundary layer.
Physics, per tracer m, cumulative per rank, kg (x*dp/g*area, dp = prsi(k)-prsi(k+1), real(8)):
  TRP kdt m | 1-3 whole physics (GFS_physics_post): signed, sum|column|, sum|layer| | 4-6 process-split update
            (GFS_suite_stateout_update: PBL) | 7-9 samfdeepcnv | 10-12 samfshalcnv | 13 sum over steps of qgrs mass
printed when the step index changes and at finalize, like WBP. Residual whole - (4+7+10) must be 0.
Dycore, per tracer m, cumulative per rank, kg (q*delp/g*area_64, real(8)):
  PTM n m | 1 fv_dynamics (all p_split) | 2 dyn_core+tracer_2d (delp frame) | 3 tracer_2d own (dp1 -> dp2) frame |
          4 Lagrangian_to_Eulerian | 5 mapn_tracer remap own frame | 6 fillz | 7 fv_subgrid_z | 8 statein frame
          (sum qgrs*dp - dycore) | 9 physics change sum (gq0-qgrs)*dp | 10 write back (dycore - sum gq0*dp) |
          11 fv_update_phys | 12 gaps | 13 sum|column| of 5 | 14 sum|column| of 6 | 15 tracer mass now
printed after every atmosphere_state_update; n = steps done. Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

top = Path(sys.argv[1]) / "FV3"
dc = top / "atmos_cubed_sphere"
ph = top / "ccpp/physics/physics"
arr, dyn, trc, mpz = (dc / "model" / f for f in ("fv_arrays.F90", "fv_dynamics.F90", "fv_tracer2d.F90", "fv_mapz.F90"))
atm = dc / "driver/fvGFS/atmosphere.F90"
itl = ph / "Interstitials/UFS_SCM_NEPTUNE"
post, sou, sou_m, int3 = (itl / f for f in ("GFS_physics_post.F90", "GFS_suite_stateout_update.F90",
                                            "GFS_suite_stateout_update.meta", "GFS_suite_interstitial_3.F90"))
deep, shal = ph / "CONV/SAMF/samfdeepcnv.f", ph / "CONV/SAMF/samfshalcnv.f"
drv = ph / "MP/Thompson/mp_thompson.F90"
typ = top / "ccpp/data/CCPP_typedefs.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


# ---------------------------------------------------------------- dycore
sub(arr, "\ncontains\n",
    "\n  ! PTM passive-tracer mass meters (diagnostic build): trpa, trpb must be tracers 10 and 11\n"
    "  integer, parameter :: ptm_n = 2, ptm_nv = 15\n"
    "  integer, parameter :: ptm_iq(ptm_n) = (/ 10, 11 /)\n"
    "  real(kind=8), save :: ptm_acc(ptm_nv, ptm_n) = 0.d0\n"
    "  real(kind=8), allocatable, save :: ptm_area(:,:)\n"
    "  logical, save :: ptm_on = .false.\n"
    "\ncontains\n\n"
    " real(kind=8) function ptm_mass(isd, ied, jsd, jed, is, ie, js, je, npz, iq, q, delp, area)\n"
    "   ! tracer mass: sum of q*delp/g*area for tracer iq over the compute domain\n"
    "   integer, intent(in) :: isd, ied, jsd, jed, is, ie, js, je, npz, iq\n"
    "   real, intent(in) :: q(isd:ied, jsd:jed, npz, *), delp(isd:ied, jsd:jed, npz)\n"
    "   real(kind=8), intent(in) :: area(isd:ied, jsd:jed)\n"
    "   integer :: i, j, k\n"
    "   ptm_mass = 0.d0\n"
    "   do k = 1, npz\n"
    "      do j = js, je\n"
    "         do i = is, ie\n"
    "            ptm_mass = ptm_mass + dble(q(i,j,k,iq))*dble(delp(i,j,k))*area(i,j)\n"
    "         enddo\n"
    "      enddo\n"
    "   enddo\n"
    "   ptm_mass = ptm_mass/9.80665d0\n"
    " end function ptm_mass\n")

MD = "ptm_mass(isd,ied,jsd,jed,is,ie,js,je,npz,ptm_iq(ptm_m),q,delp,gridstruct%area_64)"
sub(dyn, "inline_mp_type\n", "inline_mp_type, ptm_n, ptm_iq, ptm_acc, ptm_mass, ptm_on\n")
sub(dyn, "    real(kind=8) :: wb_x0\n", "    real(kind=8) :: wb_x0\n    real(kind=8) :: ptm_t\n    integer :: ptm_m\n")
sub(dyn, "                                           call timing_on('DYN_CORE')\n",
    "      if (ptm_on) then\n"
    "         do ptm_m = 1, ptm_n\n"
    f"            ptm_acc(2,ptm_m) = ptm_acc(2,ptm_m) - {MD}\n"
    "         enddo\n"
    "      endif\n"
    "                                           call timing_on('DYN_CORE')\n")
sub(dyn, "                                             call timing_off('tracer_2d')\n",
    "                                             call timing_off('tracer_2d')\n"
    "      if (ptm_on) then\n"
    "         do ptm_m = 1, ptm_n\n"
    f"            ptm_t = {MD}\n"
    "            ptm_acc(2,ptm_m) = ptm_acc(2,ptm_m) + ptm_t\n"
    "            ptm_acc(4,ptm_m) = ptm_acc(4,ptm_m) - ptm_t\n"
    "         enddo\n"
    "      endif\n")
sub(dyn, "                     flagstruct%moist_phys)\n\n     if ( flagstruct%molecular_diffusion ) then\n",
    "                     flagstruct%moist_phys)\n"
    "      if (ptm_on) then\n"
    "         do ptm_m = 1, ptm_n\n"
    f"            ptm_acc(4,ptm_m) = ptm_acc(4,ptm_m) + {MD}\n"
    "         enddo\n"
    "      endif\n\n     if ( flagstruct%molecular_diffusion ) then\n")

# tracer_2d_1L: own frame, q*dp1 at the start of each layer against q*dp2 at its end
sub(trc, "only: fv_grid_type, fv_nest_type, fv_atmos_type, fv_grid_bounds_type\n",
    "only: fv_grid_type, fv_nest_type, fv_atmos_type, fv_grid_bounds_type, ptm_n, ptm_iq, ptm_acc, ptm_on\n")
T1L = ("subroutine tracer_2d_1L(q, dp1, mfx, mfy, cx, cy, gridstruct, bd, domain, npx, npy, npz,   &\n"
       "                        nq,  hord, q_split, dt, id_divg, q_pack, dp1_pack, nord_tr, trdm, lim_fac)\n\n")
sub(trc, T1L + "      type(fv_grid_bounds_type), intent(IN) :: bd\n",
    T1L + "      type(fv_grid_bounds_type), intent(IN) :: bd\n"
    "      real(kind=8) :: ptm_s\n"
    "      integer :: ptm_m\n")
TSUM = ("     if (ptm_on) then\n"
        "        do ptm_m = 1, ptm_n\n"
        "           ptm_s = 0.d0\n"
        "           do j=js,je\n"
        "              do i=is,ie\n"
        "                 ptm_s = ptm_s + dble(q(i,j,k,ptm_iq(ptm_m)))*dble({dp})*gridstruct%area_64(i,j)\n"
        "              enddo\n"
        "           enddo\n"
        "           ptm_acc(3,ptm_m) = ptm_acc(3,ptm_m) {sg} ptm_s/9.80665d0\n"
        "        enddo\n"
        "     endif\n")
sub(trc, "! Begin k-independent tracer transport; can not be OpenMPed because the mpp_update call.\n  do k=1,npz\n",
    "! Begin k-independent tracer transport; can not be OpenMPed because the mpp_update call.\n  do k=1,npz\n"
    + TSUM.format(dp="dp1(i,j,k)", sg="-"))
sub(trc, "     enddo  ! time-split loop\n  enddo    ! k-loop\n",
    "     enddo  ! time-split loop\n" + TSUM.format(dp="dp2(i,j)", sg="+") + "  enddo    ! k-loop\n")

# mapn_tracer: remap in its own frame (q1*dp1 -> q2*dp2) and fillz, per column
sub(mpz, "R_GRID, inline_mp_type\n", "R_GRID, inline_mp_type, ptm_n, ptm_iq, ptm_acc, ptm_area, ptm_on\n")
sub(mpz, "      real:: pl, pr, dp, esl, fac1, fac2\n      integer:: i, k, l, m, k0, iq\n",
    "      real:: pl, pr, dp, esl, fac1, fac2\n      integer:: i, k, l, m, k0, iq\n"
    "      real(kind=8):: ptm_c(i1:i2,ptm_n), ptm_s, ptm_s0\n      integer:: ptm_m\n")
sub(mpz, "  if (fill) call fillz(i2-i1+1, km, nq, q2, dp2)\n",
    "  if (ptm_on) then\n"
    "     do ptm_m = 1, ptm_n\n"
    "        do i=i1,i2\n"
    "           ptm_s0 = 0.d0\n"
    "           ptm_s = 0.d0\n"
    "           do k=1,km\n"
    "              ptm_s0 = ptm_s0 + dble(q1(i,j,k,ptm_iq(ptm_m)))*dble(dp1(i,k))\n"
    "              ptm_s = ptm_s + dble(q2(i,k,ptm_iq(ptm_m)))*dble(dp2(i,k))\n"
    "           enddo\n"
    "           ptm_c(i,ptm_m) = ptm_s\n"
    "           ptm_acc(5,ptm_m) = ptm_acc(5,ptm_m) + (ptm_s-ptm_s0)*ptm_area(i,j)/9.80665d0\n"
    "           ptm_acc(13,ptm_m) = ptm_acc(13,ptm_m) + abs(ptm_s-ptm_s0)*ptm_area(i,j)/9.80665d0\n"
    "        enddo\n"
    "     enddo\n"
    "  endif\n"
    "  if (fill) call fillz(i2-i1+1, km, nq, q2, dp2)\n"
    "  if (ptm_on) then\n"
    "     do ptm_m = 1, ptm_n\n"
    "        do i=i1,i2\n"
    "           ptm_s = 0.d0\n"
    "           do k=1,km\n"
    "              ptm_s = ptm_s + dble(q2(i,k,ptm_iq(ptm_m)))*dble(dp2(i,k))\n"
    "           enddo\n"
    "           ptm_acc(6,ptm_m) = ptm_acc(6,ptm_m) + (ptm_s-ptm_c(i,ptm_m))*ptm_area(i,j)/9.80665d0\n"
    "           ptm_acc(14,ptm_m) = ptm_acc(14,ptm_m) + abs(ptm_s-ptm_c(i,ptm_m))*ptm_area(i,j)/9.80665d0\n"
    "        enddo\n"
    "     enddo\n"
    "  endif\n")

# atmosphere.F90: whole fv_dynamics, fv_subgrid_z, physics -> dynamics update, fv_update_phys, gaps
MA = "ptm_mass(isd,ied,jsd,jed,isc,iec,jsc,jec,npz,ptm_iq(ptm_m),Atm(n)%q,Atm(n)%delp,Atm(n)%gridstruct%area_64)"


def loop(body):
    return "   do ptm_m = 1, ptm_n\n      ptm_t = " + MA + "\n" + "".join(f"      {b}\n" for b in body) + "   enddo\n"


sub(atm, "fv_grid_bounds_type, phys_diag_type\n",
    "fv_grid_bounds_type, phys_diag_type, ptm_n, ptm_iq, ptm_acc, ptm_area, ptm_mass, ptm_on\n")
sub(atm, "  integer, save :: wbd_n = 0\n",
    "  integer, save :: wbd_n = 0\n  real(kind=8), save :: ptm_d2(2) = -1.d0, ptm_s2(2) = -1.d0\n")
sub(atm, "   cld_amt = get_tracer_index (MODEL_ATMOS, 'cld_amt')\n",
    "   cld_amt = get_tracer_index (MODEL_ATMOS, 'cld_amt')\n"
    "   if (get_tracer_index(MODEL_ATMOS, 'trpa') /= ptm_iq(1) .or. get_tracer_index(MODEL_ATMOS, 'trpb') /= ptm_iq(2)) &\n"
    "      call mpp_error(FATAL, 'PTM meter build: field_table must put trpa and trpb at tracers 10 and 11')\n")
sub(atm, "   real(kind=8) :: wb_t\n", "   real(kind=8) :: wb_t\n   real(kind=8) :: ptm_t\n   integer :: ptm_m\n")
sub(atm, "   wbd(1) = wbd(1) - wb_t\n   do psc=1,abs(p_split)\n",
    "   wbd(1) = wbd(1) - wb_t\n"
    "   if (.not. ptm_on) then\n"
    "      allocate(ptm_area(isd:ied,jsd:jed))\n"
    "      ptm_area = Atm(n)%gridstruct%area_64(isd:ied,jsd:jed)\n"
    "      ptm_acc = 0.d0\n"
    "      ptm_on = .true.\n"
    "   endif\n"
    + loop(["if (ptm_s2(ptm_m) >= 0.d0) ptm_acc(12,ptm_m) = ptm_acc(12,ptm_m) + (ptm_t - ptm_s2(ptm_m))",
            "ptm_acc(1,ptm_m) = ptm_acc(1,ptm_m) - ptm_t"])
    + "   do psc=1,abs(p_split)\n")
sub(atm, "   wbd(1) = wbd(1) + wb_t\n   wbd(3) = wbd(3) - wb_t\n",
    "   wbd(1) = wbd(1) + wb_t\n   wbd(3) = wbd(3) - wb_t\n"
    + loop(["ptm_acc(1,ptm_m) = ptm_acc(1,ptm_m) + ptm_t", "ptm_acc(7,ptm_m) = ptm_acc(7,ptm_m) - ptm_t"]))
sub(atm, "   wbd(3) = wbd(3) + wb_t\n   wb_d2 = wb_t\n",
    "   wbd(3) = wbd(3) + wb_t\n   wb_d2 = wb_t\n"
    + loop(["ptm_acc(7,ptm_m) = ptm_acc(7,ptm_m) + ptm_t", "ptm_d2(ptm_m) = ptm_t"]))
sub(atm, "   real(kind=8) :: wb_t, wb_f0, wb_f1\n",
    "   real(kind=8) :: wb_t, wb_f0, wb_f1\n   real(kind=8) :: ptm_t, ptm_s1, ptm_sg\n   integer :: ptm_m\n")
sub(atm, "   wbd(4) = wbd(4) - wb_t\n\n   if (IAU_Data%in_interval) then\n",
    "   wbd(4) = wbd(4) - wb_t\n"
    + loop(["if (ptm_d2(ptm_m) >= 0.d0) ptm_acc(12,ptm_m) = ptm_acc(12,ptm_m) + (ptm_t - ptm_d2(ptm_m))",
            "ptm_acc(8,ptm_m) = ptm_acc(8,ptm_m) - ptm_t"])
    + "\n   if (IAU_Data%in_interval) then\n")
sub(atm, "snowwat, graupel, nq_adv, flip_vc, wbd)   &\n", "snowwat, graupel, nq_adv, flip_vc, wbd, ptm_acc)   &\n")
sub(atm, "tracer_name, wb_f0, wb_f1, wb_ix, wb_k)", "tracer_name, wb_f0, wb_f1, wb_ix, wb_k, ptm_m, ptm_s1, ptm_sg)")
DPA = ("abs(IPD_Data(nb)%Statein%prsi(wb_ix,wb_k)-IPD_Data(nb)%Statein%prsi(wb_ix,wb_k+1)) &\n"
       "                 *Atm(n)%gridstruct%area_64(Atm_block%index(nb)%ii(wb_ix),Atm_block%index(nb)%jj(wb_ix))")
sub(atm, "     wb_f0 = 0.d0\n",
    "     do ptm_m = 1, ptm_n\n"
    "       ptm_s1 = 0.d0\n"
    "       ptm_sg = 0.d0\n"
    "       do wb_k = 1, npz\n"
    "         do wb_ix = 1, blen\n"
    f"           ptm_s1 = ptm_s1 + IPD_Data(nb)%Statein%qgrs(wb_ix,wb_k,ptm_iq(ptm_m))*{DPA}\n"
    "           ptm_sg = ptm_sg + (IPD_Data(nb)%Stateout%gq0(wb_ix,wb_k,ptm_iq(ptm_m)) &\n"
    f"                 - IPD_Data(nb)%Statein%qgrs(wb_ix,wb_k,ptm_iq(ptm_m)))*{DPA}\n"
    "         enddo\n"
    "       enddo\n"
    "       ptm_acc(8,ptm_m) = ptm_acc(8,ptm_m) + ptm_s1/9.80665d0\n"
    "       ptm_acc(9,ptm_m) = ptm_acc(9,ptm_m) + ptm_sg/9.80665d0\n"
    "       ptm_acc(10,ptm_m) = ptm_acc(10,ptm_m) - (ptm_s1 + ptm_sg)/9.80665d0\n"
    "     enddo\n"
    "     wb_f0 = 0.d0\n")
sub(atm, "   wbd(4) = wbd(4) + wb_t\n   wbd(5) = wbd(5) - wb_t\n",
    "   wbd(4) = wbd(4) + wb_t\n   wbd(5) = wbd(5) - wb_t\n"
    + loop(["ptm_acc(10,ptm_m) = ptm_acc(10,ptm_m) + ptm_t", "ptm_acc(11,ptm_m) = ptm_acc(11,ptm_m) - ptm_t"]))
sub(atm, "   wbd(5) = wbd(5) + wb_t\n   wb_s2 = wb_t\n",
    "   wbd(5) = wbd(5) + wb_t\n   wb_s2 = wb_t\n"
    + loop(["ptm_acc(11,ptm_m) = ptm_acc(11,ptm_m) + ptm_t", "ptm_s2(ptm_m) = ptm_t", "ptm_acc(15,ptm_m) = ptm_t"]))
sub(atm, "   write(*,'(a,i7,9es24.15)') 'WBD ', wbd_n, wbd, wb_area\n",
    "   write(*,'(a,i7,9es24.15)') 'WBD ', wbd_n, wbd, wb_area\n"
    "   do ptm_m = 1, ptm_n\n"
    "      write(*,'(a,i7,i2,15es24.15)') 'PTM ', wbd_n, ptm_m, ptm_acc(:,ptm_m)\n"
    "   enddo\n")

# ---------------------------------------------------------------- physics
sub(post, "  integer, save :: wbq_r = 0\n",
    "  integer, save :: wbq_r = 0\n"
    "  ! TRP passive-tracer meters (diagnostic build): trpa, trpb are tracers 10, 11; slots in the convective clw array\n"
    "  integer, parameter, public :: trp_n = 2\n"
    "  integer, parameter, public :: trp_iq(trp_n) = (/ 10, 11 /)\n"
    "  integer, public, save :: trp_slot(trp_n) = -1\n"
    "  real(kind=8), public, save :: trp_acc(13,trp_n) = 0.0d0\n")
sub(post, "    real(kind=8) :: wb_s, wb_h, wb_r\n",
    "    real(kind=8) :: wb_s, wb_h, wb_r\n    real(kind=8) :: trp_s, trp_d, trp_ms\n    integer :: trp_m\n")
sub(post, "       if (wbp_kdt >= 0) write(*,'(a,i7,7es24.15)') 'WBQ ', wbp_kdt, wbq\n",
    "       if (wbp_kdt >= 0) write(*,'(a,i7,7es24.15)') 'WBQ ', wbp_kdt, wbq\n"
    "       do trp_m = 1, trp_n\n"
    "          if (wbp_kdt >= 0) write(*,'(a,i7,i2,13es24.15)') 'TRP ', wbp_kdt, trp_m, trp_acc(:,trp_m)\n"
    "       enddo\n")
sub(post, "    ! all queued columns of this step read: start the queues again\n",
    "    do trp_m = 1, trp_n\n"
    "       do i = 1, nCol\n"
    "          trp_s = 0.0d0\n"
    "          trp_ms = 0.0d0\n"
    "          do k = 1, nLev\n"
    "             trp_d = gq0(i,k,trp_iq(trp_m)) - qgrs(i,k,trp_iq(trp_m))\n"
    "             trp_s = trp_s + trp_d*(prsi(i,k)-prsi(i,k+1))\n"
    "             trp_ms = trp_ms + qgrs(i,k,trp_iq(trp_m))*(prsi(i,k)-prsi(i,k+1))\n"
    "             trp_acc(3,trp_m) = trp_acc(3,trp_m) + abs(trp_d)*(prsi(i,k)-prsi(i,k+1))*garea(i)/con_g\n"
    "          enddo\n"
    "          trp_acc(1,trp_m) = trp_acc(1,trp_m) + trp_s*garea(i)/con_g\n"
    "          trp_acc(2,trp_m) = trp_acc(2,trp_m) + abs(trp_s)*garea(i)/con_g\n"
    "          trp_acc(13,trp_m) = trp_acc(13,trp_m) + trp_ms*garea(i)/con_g\n"
    "       enddo\n"
    "    enddo\n\n"
    "    ! all queued columns of this step read: start the queues again\n")

# process-split update (applies the boundary layer's tendencies)
sub(sou, "  use machine,       only: kind_phys\n",
    "  use machine,       only: kind_phys\n  use GFS_physics_post, only: trp_n, trp_iq, trp_acc\n")
sub(sou, "do3_dt_prd, do3_dt_ozmx, do3_dt_temp, do3_dt_ohoz, errmsg, errflg)\n",
    "do3_dt_prd, do3_dt_ozmx, do3_dt_temp, do3_dt_ohoz, garea, errmsg, errflg)\n")
sub(sou, "    ! Locals\n    integer :: i, k\n",
    "    real(kind=kind_phys), intent(in) :: garea(:)\n"
    "    ! Locals\n    integer :: i, k\n    real(kind=8) :: trp_s, trp_d\n    integer :: trp_m\n")
sub(sou, "    gq0(:,:,:) = qgrs(:,:,:) + dqdt(:,:,:) * dtp\n",
    "    gq0(:,:,:) = qgrs(:,:,:) + dqdt(:,:,:) * dtp\n"
    "    do trp_m = 1, trp_n\n"
    "       do i = 1, im\n"
    "          trp_s = 0.0d0\n"
    "          do k = 1, levs\n"
    "             trp_d = gq0(i,k,trp_iq(trp_m)) - qgrs(i,k,trp_iq(trp_m))\n"
    "             trp_s = trp_s + trp_d*dp(i,k)\n"
    "             trp_acc(6,trp_m) = trp_acc(6,trp_m) + abs(trp_d)*dp(i,k)*garea(i)*con_1ovg\n"
    "          enddo\n"
    "          trp_acc(4,trp_m) = trp_acc(4,trp_m) + trp_s*garea(i)*con_1ovg\n"
    "          trp_acc(5,trp_m) = trp_acc(5,trp_m) + abs(trp_s)*garea(i)*con_1ovg\n"
    "       enddo\n"
    "    enddo\n")
sub(sou_m, "[errmsg]\n",
    "[garea]\n  standard_name = cell_area\n  long_name = area of the grid cell\n  units = m2\n"
    "  dimensions = (horizontal_loop_extent)\n  type = real\n  kind = kind_phys\n  intent = in\n[errmsg]\n")

# convective-tracer slots (and the gate on the tracer layout)
sub(int3, "      implicit none\n\n      ! interface variables\n      logical, intent(in)     :: otsptflag(:)",
    "      use GFS_physics_post, only: trp_iq, trp_slot\n"
    "      implicit none\n\n      ! interface variables\n      logical, intent(in)     :: otsptflag(:)")
sub(int3, "            IF ( otsptflag(n) ) THEN\n            tracers = tracers + 1\n",
    "            IF ( otsptflag(n) ) THEN\n            tracers = tracers + 1\n"
    "            if (n == trp_iq(1)) trp_slot(1) = tracers\n"
    "            if (n == trp_iq(2)) trp_slot(2) = tracers\n")
sub(int3, "                clw(i,k,tracers) = gq0(i,k,n)\n              enddo\n            enddo\n          endif\n        enddo\n",
    "                clw(i,k,tracers) = gq0(i,k,n)\n              enddo\n            enddo\n          endif\n        enddo\n"
    "        if (ntrac /= 12 .or. trp_slot(1) < 3 .or. trp_slot(2) < 3) then\n"
    "          errflg = 1\n"
    "          errmsg = 'TRP meter build: needs 12 tracers with trpa, trpb (10, 11) convectively transported'\n"
    "          return\n"
    "        endif\n")

# SAMF deep and shallow: the tracer slots of qtr before and after (early returns leave qtr untouched)
SAMF_DECL = ("      real(kind=8) trp_q0(im,km,2), trp_s, trp_d\n"
             "      integer trp_m\n")
SAMF_IN = ("      do trp_m = 1, 2\n"
           "        do k = 1, km\n"
           "          do i = 1, im\n"
           "            trp_q0(i,k,trp_m) = qtr(i,k,trp_slot(trp_m))\n"
           "          enddo\n"
           "        enddo\n"
           "      enddo\n")


def samf_out(b):
    return ("      do trp_m = 1, 2\n"
            "        do i = 1, im\n"
            "          trp_s = 0.d0\n"
            "          do k = 1, km\n"
            "            trp_d = qtr(i,k,trp_slot(trp_m)) - trp_q0(i,k,trp_m)\n"
            "            trp_s = trp_s + trp_d*delp(i,k)\n"
            f"            trp_acc({b+2},trp_m) = trp_acc({b+2},trp_m)\n"
            "     &        + abs(trp_d)*delp(i,k)*garea(i)/grav\n"
            "          enddo\n"
            f"          trp_acc({b},trp_m) = trp_acc({b},trp_m)\n"
            "     &      + trp_s*garea(i)/grav\n"
            f"          trp_acc({b+1},trp_m) = trp_acc({b+1},trp_m)\n"
            "     &      + abs(trp_s)*garea(i)/grav\n"
            "        enddo\n"
            "      enddo\n")


for f, b, ini, fin in ((deep, 7, "      parameter (tf=233.16, tcr=263.16, tcrf=1.0/(tcr-tf))\n\n"
                                 "      ! Initialize CCPP error handling variables\n      errmsg = ''\n      errflg = 0\n",
                        "      endif ! (.not.hwrf_samfdeep)\n      return\n      end subroutine samfdeepcnv_run\n"),
                       (shal, 10, "      parameter (tf=233.16, tcr=263.16, tcrf=1.0/(tcr-tf))\n\n\n"
                                  "c-----------------------------------------------------------------------\n!\n"
                                  "! Initialize CCPP error handling variables\n      errmsg = ''\n      errflg = 0\n",
                        "!!\n      return\n      end subroutine samfshalcnv_run\n")):
    sub(f, "      use funcphys , only : fpvs\n",
        "      use funcphys , only : fpvs\n      use GFS_physics_post, only: trp_acc, trp_slot\n")
    p = ini.index("\n") + 1
    sub(f, ini, ini[:p] + SAMF_DECL + ini[p:] + SAMF_IN)
    q = fin.index("      return\n")
    sub(f, fin, fin[:q] + samf_out(b) + fin[q:])

# finalize print (last step)
sub(drv, "         use GFS_physics_post, only: wbp, wbp_kdt, wbq\n",
    "         use GFS_physics_post, only: wbp, wbp_kdt, wbq, trp_acc\n")
sub(drv, "         write(*,'(a,i7,7es24.15)') 'WBQ ', wbp_kdt, wbq\n",
    "         write(*,'(a,i7,7es24.15)') 'WBQ ', wbp_kdt, wbq\n"
    "         write(*,'(a,i7,i2,13es24.15)') 'TRP ', wbp_kdt, 1, trp_acc(:,1)\n"
    "         write(*,'(a,i7,i2,13es24.15)') 'TRP ', wbp_kdt, 2, trp_acc(:,2)\n")

# boundary layer diffuses every tracer when TKE is last (the standard 10-tracer table already has nvdiff == ntrac)
sub(typ, "        Interstitial%nvdiff = 9\n      endif\n      if (Model%satmedmf) Interstitial%nvdiff = Interstitial%nvdiff + 1\n"
         "    elseif ( Model%imp_physics == Model%imp_physics_nssl ) then\n",
    "        Interstitial%nvdiff = 9\n      endif\n      if (Model%satmedmf) Interstitial%nvdiff = Interstitial%nvdiff + 1\n"
    "      ! TRP diagnostic build: passive tracers before sgs_tke are diffused like the standard tracers\n"
    "      if (Model%satmedmf .and. .not.Model%ltaerosol .and. .not.Model%mraerosol .and. Model%ntke == Model%ntrac) &\n"
    "        Interstitial%nvdiff = Model%ntrac\n"
    "    elseif ( Model%imp_physics == Model%imp_physics_nssl ) then\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preTR").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(top)}")
