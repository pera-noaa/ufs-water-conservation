#!/usr/bin/env python3
"""DEBUG ONLY: checkpoint hashes inside samfdeepcnv (before each 'totflg = .true.' and at the tendency output) for
step SM_DBG_KDT: per column key (psp, garea) + [cp, cnvflg, kb, kbcon, ktcon, jmin, aa1, edto, xmb, sum t-like].
Applied on top of dbg_samf.py (needs its kdtdbg argument and declarations). usage: dbg_samf2.py <ufs-weather-model>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF/samfdeepcnv.f"
s = f.read_text()
assert "kdtdbg" in s
s = s.replace("      integer(kind=8) :: hdb(24)\n", "      integer(kind=8) :: hdb(24)\n      integer :: cpdb\n      integer(kind=8) :: g8(10)\n", 1)
def ck(n, ind):
    return "\n".join([
        f"{ind}call dbg_cp({n})"]) + "\n"
lines = s.split("\n")
out = []; n = 0
for l in lines:
    if l.strip() == "totflg = .true." and l.startswith("      "):
        n += 1
        out.append(f"      call dbg_cp({n})")
    out.append(l)
s = "\n".join(out)
a = "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n"
assert s.count(a) == 1
s = s.replace(a, f"      call dbg_cp({n+1})\n" + a)
# internal subroutine via contains: put before 'end subroutine samfdeepcnv_run'
sub = f"""      return
      contains
      subroutine dbg_cp(cp)
      integer, intent(in) :: cp
      character(len=16) :: e
      integer :: ie, kd, r, u, ii
      character(len=32) :: fn
      call get_environment_variable('SM_DBG_KDT', e, status=ie)
      kd = -1
      if (ie == 0) read(e, *) kd
      if (kdtdbg /= kd) return
      call MPI_Comm_rank(MPI_COMM_WORLD, r, ie)
      write(fn, '(a,i5.5,a)') 'samf_cp_', r, '.txt'
      open(newunit=u, file=trim(fn), position='append')
      do ii = 1, im
        g8 = 0
        g8(1) = transfer(psp(ii), 0_8)
        g8(2) = transfer(garea(ii), 0_8)
        g8(3) = cp
        if (cnvflg(ii)) g8(4) = 1
        g8(5) = kb(ii)*1000000 + kbcon(ii)*1000 + ktcon(ii)
        g8(6) = jmin(ii)
        g8(7) = transfer(real(aa1(ii),8), 0_8)
        g8(8) = transfer(real(edto(ii),8), 0_8)
        g8(9) = transfer(real(xmb(ii),8), 0_8)
        g8(10) = transfer(real(sum(new_t1(ii,:)),8), 0_8)
        g8(10) = g8(10) + transfer(real(sum(new_q1(ii,:)),8),0_8)
        write(u, '(10z17)') g8
      enddo
      close(u)
      end subroutine dbg_cp
"""
a = "      return\n      end subroutine samfdeepcnv_run\n"
assert s.count(a) == 1
s = s.replace(a, sub + "      end subroutine samfdeepcnv_run\n")
f.write_text(s); print("checkpoints:", n + 1)
