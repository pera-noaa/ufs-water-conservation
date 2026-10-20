#!/usr/bin/env python3
"""Per-statement real*8 meters (WBB) inside atmosphere_state_update's physics->dycore write-back, on top of instrument_tr.py.
Usage: python3 instrument_wbb.py <ufs_model.fd>   (atmosphere.F90 must already carry the PTM meters; writes atmosphere.F90.preWBB)
Per species group m (1 trpa, 2 trpb, 3 sphum, 4 total water 1..nwat) and region r (1: FV layers 1-40 from the top, 2: below),
cumulative per rank, kg (x area/g), printed as 'WBB n m r' after each atmosphere_state_update next to PTM:
  1 target sum qwat (= sum gq0*dp, real*8)   2 error sum(q4*delp4 - qwat)   3 delp-store part q4*(delp4 - q0)
  4 q-store part (q4 - qwat/q0)*q0   5 real*4 dry-mass part -qwat*(q0 - q0x)/q0, q0x = delp_old*(1 - sum q_old) + qt in real*8
  6 shadow fix B: error if q = qwat/delp4 (divide by the stored delp)   7 shadow fix C: error if the dry mass is real*8 (q0x)
  8 sum|cell error|   9 sum|cell error| for fix B   10 cells with error < 0   11 cells with error > 0   12 sum(delp4 - q0x)
No model variable is written; answers must be bit-identical to the build without these lines."""
import sys
from pathlib import Path

atm = Path(sys.argv[1]) / "FV3/atmos_cubed_sphere/driver/fvGFS/atmosphere.F90"
s = atm.read_text()


def sub(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT: expected 1 match, found {n}: {old.strip()[:80]!r}")
    s = s.replace(old, new)


sub("  integer, save :: wbd_n = 0\n", "  integer, save :: wbd_n = 0\n  real(kind=8), save :: wbb_acc(12,4,2) = 0.d0\n")
sub("   real(kind=8) :: ptm_t, ptm_s1, ptm_sg\n",
    "   real(kind=8) :: ptm_t, ptm_s1, ptm_sg\n"
    "   real(kind=8) :: wbb_l(12,4,2), wbb_d0, wbb_sq, wbb_q0x, wbb_t, wbb_a, wbb_x, wbb_e, wbb_e2, wbb_ar\n"
    "   real :: wbb_q4, wbb_d4, wbb_r4, wbb_d1\n"
    "   integer :: wbb_m, wbb_r, wbb_iq, wbb_lo, wbb_hi\n")
sub("snowwat, graupel, nq_adv, flip_vc, wbd, ptm_acc)   &\n",
    "snowwat, graupel, nq_adv, flip_vc, wbd, ptm_acc, wbb_acc)   &\n")
sub("tracer_name, wb_f0, wb_f1, wb_ix, wb_k, ptm_m, ptm_s1, ptm_sg)",
    "tracer_name, wb_f0, wb_f1, wb_ix, wb_k, ptm_m, ptm_s1, ptm_sg) &\n"
    "!$OMP             private (wbb_l, wbb_d0, wbb_sq, wbb_q0x, wbb_t, wbb_a, wbb_x, wbb_e, wbb_e2, wbb_ar, wbb_q4, wbb_d4, wbb_r4, &\n"
    "!$OMP                      wbb_d1, wbb_m, wbb_r, wbb_iq, wbb_lo, wbb_hi)")
sub("\n\n     do k = 1, npz\n       if(flip_vc) then\n         k1 = npz+1-k !reverse the k direction\n",
    "\n\n     wbb_l = 0.d0\n     do k = 1, npz\n       if(flip_vc) then\n         k1 = npz+1-k !reverse the k direction\n")
L = lambda c, v: f"               wbb_l({c},wbb_m,wbb_r) = wbb_l({c},wbb_m,wbb_r) + {v}\n"
sub("         Atm(n)%delp(i,j,k1) = q0\n         Atm(n)%q(i,j,k1,1:nq_adv) = qwat(1:nq_adv) / q0\n",
    "         wbb_d0 = Atm(n)%delp(i,j,k1)\n"
    "         wbb_sq = 0.d0\n"
    "         do wbb_iq = 1, nwat\n"
    "            wbb_sq = wbb_sq + dble(Atm(n)%q(i,j,k1,wbb_iq))\n"
    "         enddo\n"
    "         wbb_q0x = wbb_d0*(1.d0 - wbb_sq) + qt\n"
    "         Atm(n)%delp(i,j,k1) = q0\n"
    "         Atm(n)%q(i,j,k1,1:nq_adv) = qwat(1:nq_adv) / q0\n"
    "         ! WBB meters (diagnostic build): per-statement write-back error, real*8, no model state written\n"
    "         wbb_r = 2\n"
    "         if (k1 <= 40) wbb_r = 1\n"
    "         wbb_ar = Atm(n)%gridstruct%area_64(i,j)/9.80665d0\n"
    "         wbb_d4 = Atm(n)%delp(i,j,k1)\n"
    "         wbb_d1 = wbb_q0x\n"
    "         do wbb_m = 1, 4\n"
    "            if (wbb_m <= 2) then\n"
    "               wbb_lo = ptm_iq(wbb_m)\n"
    "               wbb_hi = wbb_lo\n"
    "            elseif (wbb_m == 3) then\n"
    "               wbb_lo = sphum\n"
    "               wbb_hi = sphum\n"
    "            else\n"
    "               wbb_lo = 1\n"
    "               wbb_hi = nwat\n"
    "            endif\n"
    "            wbb_e = 0.d0\n"
    "            wbb_e2 = 0.d0\n"
    "            do wbb_iq = wbb_lo, wbb_hi\n"
    "               wbb_t = qwat(wbb_iq)\n"
    "               wbb_q4 = Atm(n)%q(i,j,k1,wbb_iq)\n"
    "               wbb_a = dble(wbb_q4)*dble(wbb_d4) - wbb_t\n"
    "               wbb_e = wbb_e + wbb_a\n"
    + L(1, "wbb_t*wbb_ar") + L(2, "wbb_a*wbb_ar")
    + L(3, "dble(wbb_q4)*(dble(wbb_d4) - q0)*wbb_ar")
    + L(4, "(dble(wbb_q4) - wbb_t/q0)*q0*wbb_ar")
    + L(5, "-wbb_t*(q0 - wbb_q0x)/q0*wbb_ar")
    + "               wbb_r4 = wbb_t/dble(wbb_d4)\n"
    "               wbb_x = dble(wbb_r4)*dble(wbb_d4) - wbb_t\n"
    "               wbb_e2 = wbb_e2 + wbb_x\n"
    + L(6, "wbb_x*wbb_ar")
    + "               wbb_r4 = wbb_t/wbb_q0x\n"
    + L(7, "(dble(wbb_r4)*dble(wbb_d1) - wbb_t)*wbb_ar")
    + "            enddo\n"
    "            wbb_l(8,wbb_m,wbb_r) = wbb_l(8,wbb_m,wbb_r) + abs(wbb_e)*wbb_ar\n"
    "            wbb_l(9,wbb_m,wbb_r) = wbb_l(9,wbb_m,wbb_r) + abs(wbb_e2)*wbb_ar\n"
    "            if (wbb_e < 0.d0) wbb_l(10,wbb_m,wbb_r) = wbb_l(10,wbb_m,wbb_r) + 1.d0\n"
    "            if (wbb_e > 0.d0) wbb_l(11,wbb_m,wbb_r) = wbb_l(11,wbb_m,wbb_r) + 1.d0\n"
    "            wbb_l(12,wbb_m,wbb_r) = wbb_l(12,wbb_m,wbb_r) + (dble(wbb_d4) - wbb_q0x)*wbb_ar\n"
    "         enddo\n")
sub("       enddo\n     enddo\n\n     !--- diagnostic tracers are assumed to be updated in-place\n",
    "       enddo\n     enddo\n"
    "!$OMP critical (wbb_merge)\n"
    "     wbb_acc = wbb_acc + wbb_l\n"
    "!$OMP end critical (wbb_merge)\n"
    "\n     !--- diagnostic tracers are assumed to be updated in-place\n")
sub("      write(*,'(a,i7,i2,15es24.15)') 'PTM ', wbd_n, ptm_m, ptm_acc(:,ptm_m)\n   enddo\n",
    "      write(*,'(a,i7,i2,15es24.15)') 'PTM ', wbd_n, ptm_m, ptm_acc(:,ptm_m)\n   enddo\n"
    "   do wbb_m = 1, 4\n"
    "      do wbb_r = 1, 2\n"
    "         write(*,'(a,i7,2i2,12es24.15)') 'WBB ', wbd_n, wbb_m, wbb_r, wbb_acc(:,wbb_m,wbb_r)\n"
    "      enddo\n"
    "   enddo\n")
bak = atm.with_suffix(".F90.preWBB")
if bak.exists():
    sys.exit(f"ABORT: {bak} exists (already instrumented?)")
bak.write_text(atm.read_text())
atm.write_text(s)
print(f"instrumented {atm}")
