#!/usr/bin/env python3
"""SHADOW METER (diagnostic builds only; apply after the tracer agent's testhook_chem_pbl.py, instrument_tm.py and
testhook_uniform_reset.py). Usage: instrument_shadow.py <tree> <tm_shadow.inc>
Four field_table tracers sh_d, sh_m, sh_p, sh_v are reset to an exactly uniform state (dry ratio, moist mmr, physics-basis
mmr; sh_v = sum water [dyn] or qv [physics]) before each process and their departure is measured after it.
Processes (ip): 1 O->A between steps | 2 A->B start of fv_dynamics | 3 B->C dyn_core+tracer_2d (x k_split) | 4 C->D remap
(x k_split) | 5 D->B gap | 6 D2->E gap | 7 E->F neg_adj3 | 8 F->G rest of fv_dynamics | 9 G->H fv_subgrid_z |
10 H->J statein conversion (qgrs) | 11 J->GWD_post before apply | 12 GWD_post apply (PBL, satmedmfvdifq) |
14 SAMF deep (GWD_post end -> DCNV_post apply; photochem in between touches ozone only) | 15 SAMF shallow (-> SCNV_post apply) |
16 SCNV_post -> M (mp, fill_gfs, nopbl) | 17 M->N write-back | 18 N->O fv_update_phys.
Prints 'SH step ip iq ms max k lat lon' and 'SI label ...' (IC). Every anchor must match exactly once."""
import sys
from pathlib import Path
top = Path(sys.argv[1]); inc = Path(sys.argv[2]).read_text()
fv3 = top / "UFSATM/fv3/atmos_cubed_sphere"
dyn = fv3 / "model/fv_dynamics.F90"; atm = fv3 / "driver/UFS/atmosphere.F90"
inter = top / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE"
met = inter / "tm_meter.F90"
edits = {}
def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count}, found {n}: {old.strip()[:90]!r}")
    edits[path] = s.replace(old, new)

# ---- module
sub(met, "            tm_samf_substep\n",
    "            tm_samf_substep, tm_shi, tm_wi, tm_sh_on, tm_shnp, tm_sha, tm_sh_dyn, tm_sh_phys, tm_sh_icstat\n")
sub(met, "contains\n", "  integer, save :: tm_shi(4) = 0, tm_wi(6) = 0          ! shadow: sh_d sh_m sh_p sh_v; water sphum liq ice rain snow graupel\n"
    "  logical, save :: tm_sh_on = .false.\n  integer, parameter :: tm_shnp = 20\n  real(8), save :: tm_sha(6, tm_shnp, 5) = 0.d0\ncontains\n")
sub(met, "end module tm_meter", inc + "end module tm_meter")

# ---- fv_dynamics
DA = "isd, jsd, is, ie, js, je, npz, q, delp, gridstruct%area_64, gridstruct%agrid_64"
sub(dyn, "   use tm_meter,            only: tm_dyn_rec\n", "   use tm_meter,            only: tm_dyn_rec, tm_sh_dyn\n")
for ip_old, ip_new in [("2+3*(min(n_map,2)-1)", "merge(2, 5, n_map==1)"), ("3+3*(min(n_map,2)-1)", "3"),
                       ("4+3*(min(n_map,2)-1)", "4"), ("8", "6"), ("9", "7")]:
    rec = f"call tm_dyn_rec({ip_old}, isd, jsd, is, ie, js, je, npz, nq, nwat, q, delp, gridstruct%area_64)\n"
    sub(dyn, rec, rec + f"      call tm_sh_dyn({ip_new}, {DA}, 1)\n")

# ---- atmosphere.F90
sub(atm, "                              tm_iud, tm_icnv, tm_dr, tm_drs, tm_dry_phys, tm_osc, tm_cflh\n",
    "                              tm_iud, tm_icnv, tm_dr, tm_drs, tm_dry_phys, tm_osc, tm_cflh, &\n"
    "                              tm_sh_dyn, tm_sh_phys, tm_sh_icstat, tm_shi, tm_wi, tm_sh_on, tm_sha, tm_shnp\n")
sub(atm, "   call fv_restart(Atm(mygrid)%domain, Atm, seconds, days, cold_start, Atm(mygrid)%gridstruct%grid_type, mygrid)\n",
    "   call fv_restart(Atm(mygrid)%domain, Atm, seconds, days, cold_start, Atm(mygrid)%gridstruct%grid_type, mygrid)\n"
    "   call tm_sh_ic(1)\n")
sub(atm, "      call adiabatic_init(zvir,Atm(mygrid)%flagstruct%nudge_dz, time)\n",
    "      call adiabatic_init(zvir,Atm(mygrid)%flagstruct%nudge_dz, time)\n      call tm_sh_ic(2)\n")
sub(atm, "   if (tm_first) then   ! TEST HOOK", "   if (tm_first) call tm_sh_ic(3)\n   if (tm_first) then   ! TEST HOOK")
WA = ("isd, jsd, isc, iec, jsc, jec, npz, Atm(n)%q, Atm(n)%delp, Atm(n)%gridstruct%area_64, Atm(n)%gridstruct%agrid_64")
def rec(ip):
    return (f"call tm_dyn_rec({ip}, isd, jsd, isc, iec, jsc, jec, npz, nq, Atm(n)%flagstruct%nwat, Atm(n)%q, Atm(n)%delp, "
            "Atm(n)%gridstruct%area_64)\n")
sub(atm, rec(1), rec(1) + "   call tm_sh_set_idx()\n   call tm_sh_dyn(1, " + WA + ", 1)\n"
    "   if (.not. tm_sh_on) then\n     tm_sha = 0.d0; tm_sh_on = .true.\n   endif\n")
sub(atm, rec(10), rec(10) + "    call tm_sh_dyn(8, " + WA + ", 1)\n")
sub(atm, rec(11), rec(11) + "   call tm_sh_dyn(9, " + WA + ", 2)\n")
sub(atm, rec(17), rec(17) + "   call tm_sh_dyn(17, " + WA + ", 1)\n")
sub(atm, "   call tm_report(Atm(n), nq)\n", "   call tm_sh_dyn(18, " + WA + ", 1)\n   call tm_report(Atm(n), nq)\n   call tm_sh_report()\n")
CB = "IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb)"
sub(atm, "     blen = Atm_block%blksz(nb)\n     call tm_phys_mass(blen, npz, nq, IPD_Statein%qgrs(",
    "     blen = Atm_block%blksz(nb)\n"
    f"     call tm_sh_phys(10, blen, npz, IPD_Statein%qgrs({CB},:,:), IPD_Statein%qgrs({CB},:,:), IPD_Statein%prsi({CB},:), tm_ar({CB}), 0)\n"
    "     call tm_phys_mass(blen, npz, nq, IPD_Statein%qgrs(")
M4 = "tm_ar(IPD_control%chunk_begin(nb):IPD_control%chunk_end(nb)), tm_bd(:,4,nb))\n"
sub(atm, M4, M4 + f"     call tm_sh_phys(16, blen, npz, IPD_Stateout%gq0({CB},:,:), IPD_Statein%qgrs({CB},:,:), IPD_Statein%prsi({CB},:), tm_ar({CB}), 2)\n")
SUBS = """
 !> shadow meter: tracer indices
 subroutine tm_sh_set_idx()
   tm_shi(1) = max(get_tracer_index(MODEL_ATMOS, 'sh_d'), 0); tm_shi(2) = max(get_tracer_index(MODEL_ATMOS, 'sh_m'), 0)
   tm_shi(3) = max(get_tracer_index(MODEL_ATMOS, 'sh_p'), 0); tm_shi(4) = max(get_tracer_index(MODEL_ATMOS, 'sh_v'), 0)
   tm_wi(1) = get_tracer_index(MODEL_ATMOS, 'sphum'); tm_wi(2) = get_tracer_index(MODEL_ATMOS, 'liq_wat')
   tm_wi(3) = get_tracer_index(MODEL_ATMOS, 'ice_wat'); tm_wi(4) = get_tracer_index(MODEL_ATMOS, 'rainwat')
   tm_wi(5) = get_tracer_index(MODEL_ATMOS, 'snowwat'); tm_wi(6) = get_tracer_index(MODEL_ATMOS, 'graupel')
 end subroutine tm_sh_set_idx

 !> shadow meter: IC check of pt_udry / pt_umoist (label 1 after fv_restart, 2 after adiabatic_init, 3 first dynamics call)
 subroutine tm_sh_ic(label)
   use mpp_mod, only: mpp_sum, mpp_max, mpp_pe, mpp_root_pe
   integer, intent(in) :: label
   real(8) :: r(12), s(4), v(2), vl(2), l(6)
   integer :: iud, ium
   call tm_sh_set_idx()
   iud = max(get_tracer_index(MODEL_ATMOS, 'pt_udry'), 0); ium = max(get_tracer_index(MODEL_ATMOS, 'pt_umoist'), 0)
   call tm_sh_icstat(isd, jsd, isc, iec, jsc, jec, Atm(mygrid)%npz, iud, ium, Atm(mygrid)%q, Atm(mygrid)%delp, &
                     Atm(mygrid)%gridstruct%area_64, Atm(mygrid)%gridstruct%agrid_64, r)
   s = (/ r(1), r(2), r(7), r(8) /); call mpp_sum(s, 4)
   v = (/ r(3), r(9) /); vl = v; call mpp_max(v, 2)
   l = (/ r(4), r(5), r(6), r(10), r(11), r(12) /)
   if (vl(1) /= v(1)) l(1:3) = -1.d30
   if (vl(2) /= v(2)) l(4:6) = -1.d30
   call mpp_max(l, 6)
   if (mpp_pe() == mpp_root_pe()) write(*,'(a,i3,2(es12.4,es12.4,f6.0,2f9.2))') 'SI ', label, &
        sqrt(s(1)/max(s(2),1.d-300)), v(1), l(1:3), sqrt(s(3)/max(s(4),1.d-300)), v(2), l(4:6)
 end subroutine tm_sh_ic

 !> shadow meter: reduce and print per-step stats, then zero
 subroutine tm_sh_report()
   use mpp_mod, only: mpp_sum, mpp_max, mpp_pe, mpp_root_pe
   integer, save :: st = 0
   integer, parameter :: nn = tm_shnp*5
   real(8) :: s(2*nn), v(nn), vl(nn), lk(nn), la(nn), lo(nn)
   integer :: ip, iq, ix
   st = st + 1
   do iq = 1, 5
     do ip = 1, tm_shnp
       ix = (iq-1)*tm_shnp + ip
       s(2*ix-1) = tm_sha(1,ip,iq); s(2*ix) = tm_sha(2,ip,iq)
       v(ix) = tm_sha(3,ip,iq); lk(ix) = tm_sha(4,ip,iq); la(ix) = tm_sha(5,ip,iq); lo(ix) = tm_sha(6,ip,iq)
     enddo
   enddo
   call mpp_sum(s, 2*nn)
   vl = v; call mpp_max(v, nn)
   where (vl /= v)
     lk = -1.d30; la = -1.d30; lo = -1.d30
   end where
   call mpp_max(lk, nn); call mpp_max(la, nn); call mpp_max(lo, nn)
   if (mpp_pe() == mpp_root_pe()) then
     do ip = 1, tm_shnp
       do iq = 1, 5
         ix = (iq-1)*tm_shnp + ip
         if (s(2*ix) > 0.d0) write(*,'(a,i5,i3,i2,2es12.4,f6.0,2f9.2)') 'SH ', st, ip, iq, s(2*ix-1)/s(2*ix), v(ix), &
              lk(ix), la(ix), lo(ix)
       enddo
     enddo
   endif
   tm_sha = 0.d0
 end subroutine tm_sh_report
"""
sub(atm, " end subroutine atmosphere_state_update\n", " end subroutine atmosphere_state_update\n" + SUBS)

# ---- physics
USE_OLD = "tm_dry_slot, tm_osc_check\n      implicit none\n"
USE_NEW = "tm_dry_slot, tm_osc_check, tm_sh_phys\n      implicit none\n"
for name in ("GFS_DCNV_generic_post", "GFS_SCNV_generic_post", "GFS_GWD_generic_post"):
    sub(inter / f"{name}.F90", USE_OLD, USE_NEW)
PH = "im, levs, gq0, tm_qgrs, tm_prsi, tm_area"
f = inter / "GFS_DCNV_generic_post.F90"
a = "      if (tm_icnv > 0) call tm_osc_check(4, im, tm_xc, gq0(1:im,:,tm_icnv))\n"
sub(f, a, a + f"      call tm_sh_phys(14, {PH}, 1)\n")
f = inter / "GFS_SCNV_generic_post.F90"
a = "      if (tm_iud > 0) call tm_dry_slot(2, tm_r0, tm_r1)\n"
sub(f, a, a + f"      call tm_sh_phys(15, {PH}, 1)\n")
f = inter / "GFS_GWD_generic_post.F90"
a = "      case_GWD_ten: select case (tend_opt_gwd)\n"
sub(f, a, f"      call tm_sh_phys(11, {PH}, 1)\n" + a)
a = "      if (tm_iud > 0) call tm_dry_slot(3, tm_r0, tm_r1)\n"
sub(f, a, a + f"      call tm_sh_phys(12, {PH}, 1)\n")
for path, s in edits.items():
    path.write_text(s)
    print("shadow", path.relative_to(top))
