#!/usr/bin/env python3
"""Second-round write-back meters (WBB2), on top of instrument_wbb.py: separate the real*4 dry-mass error from lost sub-ulp tendencies.
Usage: python3 instrument_wbb2.py <ufs_model.fd>   (writes atmosphere.F90.preWBB2). Per tracer m (1 trpa, 2 trpb) and region r
(1: FV layers 1-40, 2: below), cumulative per rank, kg or cell counts, printed as 'WBB2 n m r':
  1 physics change sum(gq0-qgrs)*dp   2 fix C error in cells whose new value is unrepresentable (R4(qwat/q0x)=q_old, R4(q0x)=delp_old)
  3 fix C error in all other cells   4 count of 2 with gq0/=qgrs   5 cells with gq0/=qgrs
  6 current error in cells where physics changed nothing (gq0=qgrs for every advected tracer)   7 fix C error there   8 count of 6
  9 cells whose stored delp moved (delp_new/=delp_old)   10 sum q_new*(delp_new-delp_old) over those cells"""
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


sub("  real(kind=8), save :: wbb_acc(12,4,2) = 0.d0\n",
    "  real(kind=8), save :: wbb_acc(12,4,2) = 0.d0\n  real(kind=8), save :: wbb2_acc(10,2,2) = 0.d0\n")
sub("   integer :: wbb_m, wbb_r, wbb_iq, wbb_lo, wbb_hi\n",
    "   integer :: wbb_m, wbb_r, wbb_iq, wbb_lo, wbb_hi\n"
    "   real(kind=8) :: wbb2_l(10,2,2), wbb2_dp, wbb2_c\n   real :: wbb2_qo(2), wbb2_r4\n   logical :: wbb2_none\n")
sub("flip_vc, wbd, ptm_acc, wbb_acc)   &\n", "flip_vc, wbd, ptm_acc, wbb_acc, wbb2_acc)   &\n")
sub("!$OMP                      wbb_d1, wbb_m, wbb_r, wbb_iq, wbb_lo, wbb_hi)",
    "!$OMP                      wbb_d1, wbb_m, wbb_r, wbb_iq, wbb_lo, wbb_hi, wbb2_l, wbb2_dp, wbb2_c, wbb2_qo, wbb2_r4, wbb2_none)")
sub("     wbb_l = 0.d0\n", "     wbb_l = 0.d0\n     wbb2_l = 0.d0\n")
sub("         qwat(1:nq_adv) = q0*IPD_Data(nb)%Stateout%gq0(ix,k,1:nq_adv)\n",
    "         qwat(1:nq_adv) = q0*IPD_Data(nb)%Stateout%gq0(ix,k,1:nq_adv)\n         wbb2_dp = q0\n")
sub("         wbb_q0x = wbb_d0*(1.d0 - wbb_sq) + qt\n",
    "         wbb_q0x = wbb_d0*(1.d0 - wbb_sq) + qt\n"
    "         wbb2_qo(1) = Atm(n)%q(i,j,k1,ptm_iq(1))\n"
    "         wbb2_qo(2) = Atm(n)%q(i,j,k1,ptm_iq(2))\n")
L = lambda c, v: f"            wbb2_l({c},wbb_m,wbb_r) = wbb2_l({c},wbb_m,wbb_r) + {v}\n"
sub("            wbb_l(12,wbb_m,wbb_r) = wbb_l(12,wbb_m,wbb_r) + (dble(wbb_d4) - wbb_q0x)*wbb_ar\n         enddo\n",
    "            wbb_l(12,wbb_m,wbb_r) = wbb_l(12,wbb_m,wbb_r) + (dble(wbb_d4) - wbb_q0x)*wbb_ar\n         enddo\n"
    "         wbb2_none = all(IPD_Data(nb)%Stateout%gq0(ix,k,1:nq_adv) == IPD_Data(nb)%Statein%qgrs(ix,k,1:nq_adv))\n"
    "         do wbb_m = 1, 2\n"
    "            wbb_t = qwat(ptm_iq(wbb_m))\n"
    "            wbb2_r4 = wbb_t/wbb_q0x\n"
    "            wbb2_c = dble(wbb2_r4)*dble(wbb_d1) - wbb_t\n"
    + L(1, "(IPD_Data(nb)%Stateout%gq0(ix,k,ptm_iq(wbb_m)) - IPD_Data(nb)%Statein%qgrs(ix,k,ptm_iq(wbb_m)))*wbb2_dp*wbb_ar")
    + "            if (wbb2_r4 == wbb2_qo(wbb_m) .and. dble(wbb_d1) == wbb_d0) then\n"
    + L(2, "wbb2_c*wbb_ar").replace("            ", "               ", 1)
    + "               if (IPD_Data(nb)%Stateout%gq0(ix,k,ptm_iq(wbb_m)) /= IPD_Data(nb)%Statein%qgrs(ix,k,ptm_iq(wbb_m))) &\n"
    "                  wbb2_l(4,wbb_m,wbb_r) = wbb2_l(4,wbb_m,wbb_r) + 1.d0\n"
    "            else\n"
    + L(3, "wbb2_c*wbb_ar").replace("            ", "               ", 1)
    + "            endif\n"
    "            if (IPD_Data(nb)%Stateout%gq0(ix,k,ptm_iq(wbb_m)) /= IPD_Data(nb)%Statein%qgrs(ix,k,ptm_iq(wbb_m))) &\n"
    "               wbb2_l(5,wbb_m,wbb_r) = wbb2_l(5,wbb_m,wbb_r) + 1.d0\n"
    "            if (wbb2_none) then\n"
    + L(6, "(dble(Atm(n)%q(i,j,k1,ptm_iq(wbb_m)))*dble(wbb_d4) - wbb_t)*wbb_ar").replace("            ", "               ", 1)
    + L(7, "wbb2_c*wbb_ar").replace("            ", "               ", 1)
    + L(8, "1.d0").replace("            ", "               ", 1)
    + "            endif\n"
    "            if (dble(wbb_d4) /= wbb_d0) then\n"
    + L(9, "1.d0").replace("            ", "               ", 1)
    + L(10, "dble(Atm(n)%q(i,j,k1,ptm_iq(wbb_m)))*(dble(wbb_d4) - wbb_d0)*wbb_ar").replace("            ", "               ", 1)
    + "            endif\n"
    "         enddo\n")
sub("     wbb_acc = wbb_acc + wbb_l\n", "     wbb_acc = wbb_acc + wbb_l\n     wbb2_acc = wbb2_acc + wbb2_l\n")
sub("         write(*,'(a,i7,2i2,12es24.15)') 'WBB ', wbd_n, wbb_m, wbb_r, wbb_acc(:,wbb_m,wbb_r)\n      enddo\n   enddo\n",
    "         write(*,'(a,i7,2i2,12es24.15)') 'WBB ', wbd_n, wbb_m, wbb_r, wbb_acc(:,wbb_m,wbb_r)\n      enddo\n   enddo\n"
    "   do wbb_m = 1, 2\n"
    "      do wbb_r = 1, 2\n"
    "         write(*,'(a,i7,2i2,10es24.15)') 'WBB2 ', wbd_n, wbb_m, wbb_r, wbb2_acc(:,wbb_m,wbb_r)\n"
    "      enddo\n"
    "   enddo\n")
bak = atm.with_suffix(".F90.preWBB2")
if bak.exists():
    sys.exit(f"ABORT: {bak} exists")
bak.write_text(atm.read_text())
atm.write_text(s)
print(f"instrumented {atm}")
