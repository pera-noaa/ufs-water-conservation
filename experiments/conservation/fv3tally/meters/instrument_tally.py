#!/usr/bin/env python3
"""Insert the fv3tally energy meter (fv_etally.F90 + probes) into a ufs-weather-model tree.
usage: instrument_tally.py <ufs-weather-model dir> <fv_etally.F90>
Every anchor must occur exactly once; the script aborts otherwise."""
import sys, shutil, os

W, MOD = sys.argv[1], sys.argv[2]
M = os.path.join(W, 'UFSATM/fv3/atmos_cubed_sphere/model')
ST = 'isd, ied, jsd, jed, u, v, w, delz, pt, delp, q, phis, gridstruct'


def edit(fn, pairs):
    p = os.path.join(M, fn)
    s = open(p).read()
    for where, anchor, text in pairs:
        n = s.count(anchor)
        if n != 1:
            sys.exit(f'ABORT {fn}: anchor occurs {n} times: {anchor[:70]!r}')
        if where == 'before':
            s = s.replace(anchor, text + anchor)
        else:
            s = s.replace(anchor, anchor + text)
    os.remove(p)                       # never write through a link
    open(p, 'w').write(s)


edit('fv_dynamics.F90', [
    ('after', "   use fv_sg_mod,           only: neg_adj3, neg_adj2, neg_adj4\n",
     "   use fv_etally_mod,       only: et_init, et_state, et_flush, et_on, et_act, MODE_T, MODE_TH, &\n"
     "                                  ET_RAY, ET_CONV, ET_DYN2, ET_TRC, ET_POST\n"),
    ('after', "!              if(is_master())  write(*,*) 'Total Energy Density (Giga J/m**2)=',te_den\n"
              "           endif\n      endif\n",
     "      call et_init(is, ie, js, je, npz, gridstruct)\n"
     "      et_act = et_on .and. consv_te > 0. .and. (.not.do_adiabatic_init)\n"
     f"      if (et_act) call et_state(0, MODE_T, {ST})\n"),
    ('after', "                  ua, va, delz, cp_air, rdgas, ptop, hydrostatic, .true., flagstruct%rf_cutoff, gridstruct, domain, bd)\n"
              "        endif\n      endif\n",
     f"      if (et_act) call et_state(ET_RAY, MODE_T, {ST})\n"),
    ('before', "  GFDL_interstitial%last_step = .false.\n",
     f"  if (et_act) call et_state(ET_CONV, MODE_TH, {ST})\n"),
    ('after', "                                           call timing_off('DYN_CORE')\n",
     f"      if (et_act) call et_state(ET_DYN2, MODE_TH, {ST})\n"),
    ('before', "         do iq=1,nr\n                                kord_tracer(iq) = flagstruct%kord_tr\n",
     f"         if (et_act) call et_state(ET_TRC, MODE_TH, {ST})\n"),
    ('after', "911  call cubed_to_latlon(u, v, ua, va, gridstruct, &\n"
              "          npx, npy, npz, 1, gridstruct%grid_type, domain, gridstruct%bounded_domain, flagstruct%c2l_ord, bd)\n",
     f"  if (et_act) call et_state(ET_POST, MODE_T, {ST})\n"
     "  if (et_act) call et_flush()\n  et_act = .false.\n"),
])

edit('dyn_core.F90', [
    ('after', "  use sw_core_mod,        only: c_sw, d_sw, d_md\n",
     "  use fv_etally_mod,      only: et_act, et_state, et_dcon_sum, et_dcon_cap, et_tsnap, et_theat, &\n"
     "                                MODE_TH, ET_DYN, ET_DCON, XH_RAW, XH_SMO\n"),
    ('before', "  if ( n_con/=0 .and. flagstruct%d_con > 1.e-5 ) then\n",
     f"  if (et_act) call et_state(ET_DYN, MODE_TH, {ST})\n"
     "  if (et_act .and. allocated(heat_source)) call et_dcon_sum(XH_RAW, isd, ied, jsd, jed, heat_source, gridstruct)\n"),
    ('after', "       call del2_cubed(heat_source, cnst_0p20*gridstruct%da_min, gridstruct, domain, npx, npy, npz, nf_ke, bd)\n",
     "       if (et_act) then\n"
     "          call et_dcon_sum(XH_SMO, isd, ied, jsd, jed, heat_source, gridstruct)\n"
     "          call et_dcon_cap(isd, ied, jsd, jed, heat_source, delp, bdt, flagstruct%delt_max, gridstruct)\n"
     "          call et_tsnap(MODE_TH, isd, ied, jsd, jed, delz, pt, delp, q, gridstruct)\n"
     "       endif\n"),
    ('before', "  if (allocated(heat_source)) deallocate( heat_source )",
     "  if (et_act .and. n_con/=0 .and. flagstruct%d_con > 1.e-5) call et_theat(MODE_TH, isd, ied, jsd, jed, delz, pt, delp, q)\n"
     f"  if (et_act) call et_state(ET_DCON, MODE_TH, {ST})\n"),
])

edit('sw_core.F90', [
    ('after', " use a2b_edge_mod, only: a2b_ord4\n",
     " use fv_etally_mod, only: et_act, et_dsw\n"),
    ('after', "      real :: damp, damp2, damp4, dd8, u2, v2, du2, dv2\n",
     "      real :: et_du(bd%is:bd%ie,bd%js:bd%je+1), et_dv(bd%is:bd%ie+1,bd%js:bd%je)\n"
     "      real :: et_dw(bd%is:bd%ie,bd%js:bd%je), et_wp(bd%is:bd%ie,bd%js:bd%je)\n"),
    ('before', "            if ( damp_w>1.E-5 ) then\n                 dd8 = kgb*abs(dt)\n",
     "            if ( et_act ) then\n"
     "               do j=js,je\n                  do i=is,ie\n"
     "                     et_wp(i,j) = w(i,j)\n                     et_dw(i,j) = 0.\n"
     "                  enddo\n               enddo\n            endif\n"),
    ('before', "            call fv_tp_2d(w, crx_adv,cry_adv, npx, npy, hord_vt, gx, gy, xfx_adv, yfx_adv, &\n",
     "            if ( et_act .and. damp_w>1.E-5 ) then\n"
     "               do j=js,je\n                  do i=is,ie\n                     et_dw(i,j) = dw(i,j)\n"
     "                  enddo\n               enddo\n            endif\n"),
    ('before', "   if ( d_con > 1.e-5 ) then\n      do j=js,je+1\n         do i=is,ie\n            ub(i,j) = vort(i,j) - vort(i+1,j)\n",
     "   if ( et_act ) then\n"
     "      do j=js,je+1\n         do i=is,ie\n            et_du(i,j) = vort(i,j) - vort(i+1,j)\n         enddo\n      enddo\n"
     "      do j=js,je\n         do i=is,ie+1\n            et_dv(i,j) = vort(i,j) - vort(i,j+1)\n         enddo\n      enddo\n"
     "   endif\n"),
    ('before', "#ifdef SW_DYNAMICS\n      endif ! test_case\n#endif\n\n end subroutine d_sw\n",
     "   if ( et_act .and. .not. hydrostatic ) call et_dsw(k, isd, ied, jsd, jed, u, v, w, delp, et_du, et_dv, &\n"
     "                                               ut, vt, damp_v, et_dw, et_wp, gridstruct)\n"),
])

QS = 'isd, ied, jsd, jed, u, v, w, delz, pt, delp, q(isd:ied,jsd:jed,1:km,1:nq), hs, gridstruct'
edit('fv_mapz.F90', [
    ('after', "  use fv_timing_mod,     only: timing_on, timing_off\n",
     "  use fv_etally_mod,     only: et_act, et_state, MODE_T, MODE_TH, MODE_DT, ET_REMAP, ET_FIX, ET_L2EX\n"),
    ('before', "!$OMP parallel default(none) shared(is,ie,js,je,km,ptop,u,v,pe,ua,va,isd,ied,jsd,jed,kord_mt,  &\n",
     f"  if (et_act) call et_state(ET_REMAP, MODE_DT, {QS})\n"),
    ('before', " end subroutine Lagrangian_to_Eulerian\n",
     "  if (et_act) then\n     if (last_step) then\n"
     f"        call et_state(ET_FIX, MODE_T, {QS})\n     else\n"
     f"        call et_state(ET_L2EX, MODE_TH, {QS})\n     endif\n  endif\n"),
])

cm = os.path.join(W, 'UFSATM/fv3/atmos_cubed_sphere/CMakeLists.txt')
s = open(cm).read()
a = "  model/fv_dynamics.F90\n"
if s.count(a) != 1:
    sys.exit('ABORT CMakeLists anchor')
s = s.replace(a, a + "  model/fv_etally.F90\n")
os.remove(cm); open(cm, 'w').write(s)
dst = os.path.join(M, 'fv_etally.F90')
if os.path.lexists(dst):
    sys.exit('ABORT fv_etally.F90 exists')
shutil.copyfile(MOD, dst)
print('instrumented', W)
