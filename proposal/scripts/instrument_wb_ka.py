#!/usr/bin/env python3
"""Answer-neutral SAMF-deep cloud-base meter (v1 tree, fix A or A'): fix A's water change at kb and the heating dellat gives it.
Usage: python3 instrument_wb_ka.py <ufs_model.fd>    (re-run after apply_samf_a2_patch.py on samfdeepcnv.f.preKA to meter A')
Adds kdt, xlon, xlat to samfdeepcnv_run (.meta: index_of_timestep, longitude, latitude). Per convecting column:
  Dkb = eta-part of flxtvd(kb) - eta(kb)*qo(kb) (what layer kb keeps of the cloud-base face term; 0 before A and with A'),
  dqA = Dkb*g/dp(kb)*xmb*dt2,  dTA = -hvap*dqA/cp (dellah has no updraft term at k <= kb);
  Dj  = gain of layer jmin+1 from the downdraft part of flxtvd(jmin) minus the subtraction, dTj likewise.
Prints, per rank and step (flushed when the next step starts):
  WKA kdt | 1 convecting columns | 2 sum|dTA| | 3 max|dTA| | 4 sum dTA | 5 columns with kb=1 | 6 columns with q(kb)<0
      after the feedback (borrowing acts at kb) | 7 columns with any q<0 (borrowing acts) | 8 max|dTj| |
      9 sum|dqA|*dp/g (kg/m2) | 10 max|SAMF dT at kb| | 11 max|SAMF dT at k=1| | 12 max T(1) at entry
  WKE kdt lon lat T(1) q(1) T(2) q(2)   at entry, for the box 71-76E, 15-9S and any column with T(1) > 320 K
  WKC kdt lon lat kb jmin ktcon phkp eta(kb) qo(kb) (face value) tem1(kb) q1(kb) q1(kb+1) xmb dqA dTA dTkb dT1 q(kb)post T1 q1 dTj
      at exit, for convecting columns in the box or with |dTA| > 1 K, |dT1| > 5 K or T(1) > 320 K.
Every anchor must match exactly once, else nothing is written."""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics/CONV/SAMF"
f = root / "samfdeepcnv.f"
meta = root / "samfdeepcnv.meta"
pre = f.with_suffix(".f.preKA")
src = pre.read_text() if pre.exists() else f.read_text()   # always instrument the un-metered source
A2 = "! fix A': " in src
edits = {}


def sub(path, old, new, base=None):
    s = edits.get(path) or (base if base is not None else path.read_text())
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


sub(f, "\n      contains\n",
    "\n      real(kind=8), save :: wka(12) = 0.d0\n      integer, save :: wka_kdt = -1\n\n      contains\n", base=src)
sub(f, "     &    maxMF, do_mynnedmf,errmsg,errflg)\n",
    "     &    maxMF, do_mynnedmf,kdt,xlon,xlat,errmsg,errflg)\n")
sub(f, "      integer, intent(in)  :: im, km, itc, ntc, ntk, ntr, ncloud\n",
    "      integer, intent(in)  :: im, km, itc, ntc, ntk, ntr, ncloud\n"
    "      integer, intent(in)  :: kdt\n"
    "      real(kind=kind_phys), intent(in) :: xlon(:), xlat(:)\n")
sub(f, "      real(kind=kind_phys) tsumn(im), tsump(im), rtnp(im)\n",
    "      real(kind=kind_phys) tsumn(im), tsump(im), rtnp(im)\n"
    "      real(kind=kind_phys) wka_fl(im), wka_jd(im), wka_t1(im),\n"
    "     &     wka_ph(im), wka_qkb(im), wka_qkb1(im), wka_tkb0(im),\n"
    "     &     wka_t10(im), wka_dqa(im), wka_dta(im), wka_dtj(im),\n"
    "     &     wka_qpost(im), wka_qo(im), wka_lo, wka_la\n"
    "      logical wka_box(im)\n")
# entry: flush the previous step, snapshot T(1), print the box
sub(f, "\n      dt2 = delt\n",
    "\n      if(kdt /= wka_kdt) then\n"
    "        if(wka_kdt > 0) write(*,'(a,i7,12es13.5)') 'WKA ',wka_kdt,wka\n"
    "        wka = 0.d0\n"
    "        wka_kdt = kdt\n"
    "      endif\n"
    "      do i = 1, im\n"
    "        wka_lo = xlon(i) * 57.2957795\n"
    "        wka_la = xlat(i) * 57.2957795\n"
    "        wka_box(i) = wka_lo > 71. .and. wka_lo < 76. .and.\n"
    "     &               wka_la > -15. .and. wka_la < -9.\n"
    "        wka_t10(i) = t1(i,1)\n"
    "        wka_fl(i) = 0.\n"
    "        wka_jd(i) = 0.\n"
    "        wka_ph(i) = -2.\n"
    "        wka(12) = max(wka(12), real(t1(i,1), kind=8))\n"
    "        if(wka_box(i) .or. t1(i,1) > 320.)\n"
    "     &    write(*,'(a,i7,2f9.3,4es14.6)') 'WKE ', kdt, wka_lo, wka_la,\n"
    "     &    t1(i,1), q1(i,1), t1(i,2), q1(i,2)\n"
    "      enddo\n"
    "      dt2 = delt\n")
# TVD water loop, after the double-count subtraction (A or A'); flxtvd(i,k) is final here
EF = "qo(i,k)" if A2 else "tem1"   # face of the eta part at kb == jmin / of the downdraft part at jmin == kb
sub(f, "            if(k == kb(i)) then\n"
       "              dp = 1000. * del(i,k)\n"
       "              dellaq(i,k) = dellaq(i,k) -\n"
       "     &            eta(i,k) * qo(i,k) * grav/dp\n"
       "            endif\n",
    "            if(k == kb(i)) then\n"
    "              dp = 1000. * del(i,k)\n"
    "              dellaq(i,k) = dellaq(i,k) -\n"
    "     &            eta(i,k) * qo(i,k) * grav/dp\n"
    "            endif\n"
    "            if(k == kb(i)) then\n"
    "              wka_t1(i) = tem1\n"
    "              wka_ph(i) = -1.\n"
    "              if(tem /= 0.) wka_ph(i) = phkp\n"
    "              wka_qkb(i) = q1(i,k)\n"
    "              wka_qo(i) = qo(i,k)\n"
    "              wka_qkb1(i) = q1(i,k+1)\n"
    "              wka_tkb0(i) = t1(i,k)\n"
    "              wka_fl(i) = flxtvd(i,k) - eta(i,k) * qo(i,k)\n"
    "              if(k < jmin(i)) wka_fl(i) = wka_fl(i)\n"
    "     &          + edto(i) * etad(i,k) * tem1\n"
    "              if(k == jmin(i)) wka_fl(i) = wka_fl(i)\n"
    f"     &          + edto(i) * etad(i,k) * {EF}\n"
    "            endif\n"
    "            if(k == jmin(i)) then\n"
    "              wka_jd(i) = -flxtvd(i,k) - edto(i)*etad(i,k)*qo(i,k)\n"
    "              if(k > kb(i)) wka_jd(i) = wka_jd(i) + eta(i,k) * tem1\n"
    f"              if(k == kb(i)) wka_jd(i) = wka_jd(i) + eta(i,k) * {EF}\n"
    "            endif\n")
# after the feedback update, before borrowing
sub(f, "!\n! Negative moisture is set to zero after borrowing it from\n",
    "      do i = 1, im\n"
    "        if(cnvflg(i)) then\n"
    "          dp = 1000. * del(i,kb(i))\n"
    "          wka_dqa(i) = wka_fl(i) * grav / dp * xmb(i) * dt2\n"
    "          wka_dta(i) = -hvap * wka_dqa(i) / cp\n"
    "          wka(9) = wka(9) + abs(wka_dqa(i)) * dp / grav\n"
    "          dp = 1000. * del(i,jmin(i)+1)\n"
    "          wka_dtj(i) = -hvap * wka_jd(i) * grav / dp * xmb(i) * dt2\n"
    "     &               / cp\n"
    "          wka_qpost(i) = q1(i,kb(i))\n"
    "          wka(1) = wka(1) + 1.d0\n"
    "          wka(2) = wka(2) + abs(wka_dta(i))\n"
    "          wka(3) = max(wka(3), abs(real(wka_dta(i), kind=8)))\n"
    "          wka(4) = wka(4) + wka_dta(i)\n"
    "          if(kb(i) == 1) wka(5) = wka(5) + 1.d0\n"
    "          if(q1(i,kb(i)) < 0.) wka(6) = wka(6) + 1.d0\n"
    "          wka(8) = max(wka(8), abs(real(wka_dtj(i), kind=8)))\n"
    "          do k = 1, ktcon(i)\n"
    "            if(q1(i,k) < 0.) then\n"
    "              wka(7) = wka(7) + 1.d0\n"
    "              exit\n"
    "            endif\n"
    "          enddo\n"
    "        endif\n"
    "      enddo\n"
    "!\n! Negative moisture is set to zero after borrowing it from\n")
# exit
sub(f, "      return\n      end subroutine samfdeepcnv_run\n",
    "      do i = 1, im\n"
    "        if(cnvflg(i)) then\n"
    "          wka(10) = max(wka(10),\n"
    "     &      abs(real(t1(i,kb(i)) - wka_tkb0(i), kind=8)))\n"
    "          wka(11) = max(wka(11), abs(real(t1(i,1)-wka_t10(i), kind=8)))\n"
    "          if(wka_box(i) .or. abs(wka_dta(i)) > 1. .or.\n"
    "     &       abs(t1(i,1)-wka_t10(i)) > 5. .or. t1(i,1) > 320.)\n"
    "     &      write(*,'(a,i7,2f9.3,3i4,f6.3,17es12.4)') 'WKC ', kdt,\n"
    "     &      xlon(i)*57.2957795, xlat(i)*57.2957795, kb(i), jmin(i),\n"
    "     &      ktcon(i), wka_ph(i), eta(i,kb(i)), wka_qo(i), wka_t1(i),\n"
    "     &      wka_qkb(i), wka_qkb1(i), xmb(i), wka_dqa(i), wka_dta(i),\n"
    "     &      t1(i,kb(i)) - wka_tkb0(i), t1(i,1) - wka_t10(i),\n"
    "     &      wka_qpost(i), t1(i,1), q1(i,1), wka_dtj(i), rn(i)\n"
    "        endif\n"
    "      enddo\n"
    "      return\n      end subroutine samfdeepcnv_run\n")

for ln in edits[f].split("\n"):
    if len(ln) > 72 and not ln.startswith(("!", "c", "C")) and "wka" in ln:
        sys.exit(f"ABORT: line > 72 columns: {ln!r}")

M = meta.read_text()
if "[kdt]" not in M:
    add = ("[kdt]\n  standard_name = index_of_timestep\n  long_name = current forecast iteration\n  units = index\n"
           "  dimensions = ()\n  type = integer\n  intent = in\n"
           "[xlon]\n  standard_name = longitude\n  long_name = longitude\n  units = radian\n"
           "  dimensions = (horizontal_loop_extent)\n  type = real\n  kind = kind_phys\n  intent = in\n"
           "[xlat]\n  standard_name = latitude\n  long_name = latitude\n  units = radian\n"
           "  dimensions = (horizontal_loop_extent)\n  type = real\n  kind = kind_phys\n  intent = in\n")
    i = M.rfind("[errmsg]\n")
    if M.count("[errmsg]\n") != 2 or i < M.find("name = samfdeepcnv_run"):
        sys.exit("ABORT meta: run-table [errmsg] not found")
    meta.with_suffix(".meta.preKA").write_text(M)
    meta.write_text(M[:i] + add + M[i:])
    print("instrumented samfdeepcnv.meta")
if not pre.exists():
    pre.write_text(src)
f.write_text(edits[f])
print(f"instrumented samfdeepcnv.f ({'A-prime' if A2 else 'A'} formulas)")
