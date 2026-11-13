# r14_patch.py <pristine atmosphere.F90> <out>: CP1 and FV2 behind run-time switches + CP1 restored-term meter
# R14_A: CP1 dose a (t_dt * (1 + a (m_phys/delp_new - 1))); R14_K: noise k (t_dt * (1 + k eps32)); R14_B=1: FV2 on
import sys, re
src = open(sys.argv[1]).read()
n_sub = {}
def sub1(tag, old, new, s):
    c = s.count(old)
    if c != 1:
        sys.exit(f"GATE {tag}: anchor found {c} times")
    n_sub[tag] = 1
    return s.replace(old, new)

DECL = """!r14: CP1/FV2 attribution switches and CP1 restored-term meter (experiment build only)
  logical :: r14_ini = .false., r14_b = .false.
  real(kind=kind_phys) :: r14_a = 0.0_kind_phys, r14_k = 0.0_kind_phys, r14_eps = 0.0_kind_phys
  integer :: r14_n = 0, r14_nend = -1, r14_last0 = 1000000000
  real(kind=kind_phys), allocatable, dimension(:,:) :: r14_m, r14_ml, r14_h, r14_hl, r14_dev, r14_r1, r14_e1, r14_ma, r14_ha
"""
SUBS = """
 subroutine r14_setup()
   character(len=32) :: s
   integer :: st, ib
   if (r14_ini) return
   r14_ini = .true.
   call get_environment_variable('R14_A', s, status=st);     if (st == 0) read(s,*) r14_a
   call get_environment_variable('R14_K', s, status=st);     if (st == 0) read(s,*) r14_k
   call get_environment_variable('R14_B', s, status=st);     if (st == 0) then; read(s,*) ib; r14_b = (ib == 1); endif
   call get_environment_variable('R14_NEND', s, status=st);  if (st == 0) read(s,*) r14_nend
   call get_environment_variable('R14_LAST0', s, status=st); if (st == 0) read(s,*) r14_last0
   r14_eps = real(epsilon(1.0), kind_phys)
   allocate(r14_m(isc:iec,jsc:jec), r14_ml(isc:iec,jsc:jec), r14_h(isc:iec,jsc:jec), r14_hl(isc:iec,jsc:jec), &
            r14_dev(isc:iec,jsc:jec), r14_r1(isc:iec,jsc:jec), r14_e1(isc:iec,jsc:jec), &
            r14_ma(isc:iec,jsc:jec), r14_ha(isc:iec,jsc:jec))
   r14_m = 0.; r14_ml = 0.; r14_h = 0.; r14_hl = 0.; r14_dev = 0.; r14_r1 = 0.; r14_e1 = 0.; r14_ma = 0.; r14_ha = 0.
   if (is_master()) write(*,'(a,2es16.8,l3,2i11,es16.8)') ' R14 a k b nend last0 eps ', &
        r14_a, r14_k, r14_b, r14_nend, r14_last0, r14_eps
 end subroutine r14_setup

 subroutine r14_write()
   use mpp_mod, only: r14_pe => mpp_pe
   integer :: u, i, j
   character(len=64) :: fn
   write(fn,'(a,i5.5,a)') 'r14_meter.', r14_pe(), '.bin'
   open(newunit=u, file=trim(fn), access='stream', form='unformatted', status='replace')
   write(u) int(isc,4), int(iec,4), int(jsc,4), int(jec,4), int(r14_n,4), int(r14_last0,4)
   write(u) ((real(Atm(mygrid)%gridstruct%agrid(i,j,1),8), i=isc,iec), j=jsc,jec)
   write(u) ((real(Atm(mygrid)%gridstruct%agrid(i,j,2),8), i=isc,iec), j=jsc,jec)
   write(u) real(r14_m,8), real(r14_ml,8), real(r14_h,8), real(r14_hl,8), real(r14_dev,8), real(r14_r1,8), real(r14_e1,8), &
            real(r14_ma,8), real(r14_ha,8)
   close(u)
 end subroutine r14_write
"""
m = re.search(r"^contains[ \t]*\n", src, re.M)
if not m or src[:m.start()].count("\n") > 400:
    sys.exit("GATE module contains")
src = src[:m.start()] + DECL + src[m.start():m.end()] + SUBS + src[m.end():]
n_sub["contains"] = 1

src = sub1("decl", "   real(kind=kind_phys):: rcp, q0, qwat(nq), qt, rdt\n",
           "   real(kind=kind_phys):: rcp, q0, qwat(nq), qt, rdt, qp, f14, dtk\n", src)
src = sub1("rdt", "   rdt = 1.d0 / dt_atmos\n",
           "   rdt = 1.d0 / dt_atmos\n   call r14_setup()\n   r14_n = r14_n + 1\n", src)
src = sub1("omp_su",
           "!$OMP                      snowwat, graupel, nq_adv, flip_vc)   &\n"
           "!$OMP             private (nb, blen, i, j, k, k1, ix, im, q0, qwat, qt, tracer_name)\n",
           "!$OMP                      snowwat, graupel, nq_adv, flip_vc, r14_a, r14_k, r14_eps, r14_n, r14_last0, &\n"
           "!$OMP                      r14_m, r14_ml, r14_h, r14_hl, r14_dev, r14_r1, r14_e1, r14_ma, r14_ha)   &\n"
           "!$OMP             private (nb, blen, i, j, k, k1, ix, im, q0, qwat, qt, tracer_name, qp, f14, dtk)\n", src)
src = sub1("tdt_old",
           "         t_dt(i,j,k1) = t_dt(i,j,k1) + (IPD_Stateout%gt0(im,k) - IPD_Statein%tgrs(im,k)) * rdt\n", "", src)
src = sub1("qp", "         qwat(1:nq_adv) = q0*IPD_Stateout%gq0(im,k,1:nq_adv)\n",
           "         qwat(1:nq_adv) = q0*IPD_Stateout%gq0(im,k,1:nq_adv)\n         qp = q0\n", src)
src = sub1("tdt_new", "         Atm(n)%delp(i,j,k1) = q0\n",
           "         Atm(n)%delp(i,j,k1) = q0\n"
           "! r14: CP1 dose r14_a, noise r14_k; meter of the term CP1 restores, c_p dT (m_phys - delp_new)/g\n"
           "         dtk = IPD_Stateout%gt0(im,k) - IPD_Statein%tgrs(im,k)\n"
           "         f14 = (1.0_kind_phys + r14_a*(qp/q0 - 1.0_kind_phys)) * (1.0_kind_phys + r14_k*r14_eps)\n"
           "         t_dt(i,j,k1) = t_dt(i,j,k1) + dtk * rdt * f14\n"
           "         r14_m(i,j) = r14_m(i,j) + 1004.6_kind_phys*dtk*(qp - q0)/9.80665_kind_phys\n"
           "         r14_h(i,j) = r14_h(i,j) + 1004.6_kind_phys*dtk*q0/9.80665_kind_phys\n"
           "         if (r14_n > r14_last0) then\n"
           "           r14_ml(i,j) = r14_ml(i,j) + 1004.6_kind_phys*dtk*(qp - q0)/9.80665_kind_phys\n"
           "           r14_hl(i,j) = r14_hl(i,j) + 1004.6_kind_phys*dtk*q0/9.80665_kind_phys\n"
           "         endif\n"
           "         if (r14_n == 1) then\n"
           "           r14_r1(i,j) = r14_r1(i,j) + 1004.6_kind_phys*dtk*(qp - q0)/9.80665_kind_phys\n"
           "           r14_e1(i,j) = r14_e1(i,j) + 1004.6_kind_phys*dtk*f14*q0/9.80665_kind_phys\n"
           "         endif\n"
           "         r14_ma(i,j) = r14_ma(i,j) + abs(1004.6_kind_phys*dtk*(qp - q0)/9.80665_kind_phys)\n"
           "         r14_ha(i,j) = r14_ha(i,j) + abs(1004.6_kind_phys*dtk*q0/9.80665_kind_phys)\n"
           "         r14_dev(i,j) = max(r14_dev(i,j), abs(f14 - 1.0_kind_phys))\n", src)
src = sub1("write", "   enddo  ! nb-loop\n", "   enddo  ! nb-loop\n   if (r14_n == r14_nend) call r14_write()\n", src)
src = sub1("si_call", "! SA-3D-TKE added IPD_Tbd (kyf)\n", "   call r14_setup()\n! SA-3D-TKE added IPD_Tbd (kyf)\n", src)
src = sub1("omp_si", "!$OMP                      pktop, zvir, mygrid, dnats, nq_adv, flip_vc) &\n",
           "!$OMP                      pktop, zvir, mygrid, dnats, nq_adv, flip_vc, r14_b) &\n", src)
src = sub1("fv2_flip",
           "           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &\n"
           "                                                   / IPD_Statein%prsl(im,k)\n",
           "           if (r14_b) then\n"
           "           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &\n"
           "                                                   / (IPD_Statein%prsi(im,k) - IPD_Statein%prsi(im,k+1))\n"
           "           else\n"
           "           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &\n"
           "                                                   / IPD_Statein%prsl(im,k)\n"
           "           endif\n", src)
src = sub1("fv2_noflip",
           "           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &\n"
           "                                           / IPD_Statein%prsl(im,k)\n",
           "           if (r14_b) then\n"
           "           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &\n"
           "                                           / (IPD_Statein%prsi(im,k+1) - IPD_Statein%prsi(im,k))\n"
           "           else\n"
           "           IPD_Statein%qgrs(im,k,1:nq_adv) = IPD_Statein%qgrs(im,k,1:nq_adv) &\n"
           "                                           / IPD_Statein%prsl(im,k)\n"
           "           endif\n", src)
open(sys.argv[2], "w").write(src)
print("PATCH_OK", len(n_sub), "anchors:", ",".join(n_sub))
