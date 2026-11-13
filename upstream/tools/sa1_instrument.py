"""Print-only SA1 water check in samfdeepcnv.f / samfshalcnv.f: per convecting column with rain,
R = dW + rain (what SAMF creates) and P = xmb*dt2*[eta(kb)*(qo(kb)-tem1) (+ edto*etad(jmin)*(qo(jmin)-tem1), deep)].
usage: sa1_instrument.py <physics dir CONV/SAMF>"""
import sys
from pathlib import Path

def sub(s, old, new, name):
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {name}: anchor found {n} times: {old[:60]!r}")
    return s.replace(old, new)

DECL = ("      real(kind=conv_wp) dbgp(im), dbgpk(im), dbgph(im),\n"
        "     &                   dbgq1b(im), dbgq2b(im), dbgqob(im),\n"
        "     &                   dbgt1b(im)\n")

def acc_block(kbonly):
    s = ("!     DEBUG ONLY (SA1 water check): created-water prediction\n"
         "            if(k == kb(i)) then\n"
         "              dbgpk(i) = eta(i,k) * (qo(i,k) - tem1)\n"
         "              dbgp(i) = dbgp(i) + dbgpk(i)\n"
         "              dbgph(i) = phkp\n"
         "              dbgq1b(i) = real(q1(i,k), kind=conv_wp)\n"
         "              dbgq2b(i) = real(q1(i,k+1), kind=conv_wp)\n"
         "              dbgqob(i) = qo(i,k)\n"
         "              dbgt1b(i) = tem1\n"
         "            endif\n")
    if not kbonly:
        s += ("            if(k == jmin(i)) dbgp(i) = dbgp(i)\n"
              "     &         + edto(i) * etad(i,k) * (qo(i,k) - tem1)\n")
    return s

def end_block(tag, crit, jm):
    return f"""!     DEBUG ONLY (SA1 water check): per rank, sums over columns with rain
      dbgsa1: block
        real(kind=8), save :: acc(13) = 0.d0
        integer, save :: ncall = 0, nsamp = 0
        real(kind=8) :: loc(13), dw_, rr_, pp_, ra_, ga_
        integer :: ii, kk
        loc = 0.d0
        do ii = 1, im
          if (cnvflg(ii) .and. rn(ii) > 0.0_kind_phys) then
            dw_ = 0.d0
            do kk = 1, km
              dw_ = dw_ + ((new_q1(ii,kk) - q1(ii,kk))
     &          + (new_qtr(ii,kk,1) - qtr(ii,kk,1))
     &          + (new_qtr(ii,kk,2) - qtr(ii,kk,2)))
     &          * delp(ii,kk) / grav
            enddo
            ra_ = 1000.d0 * rn(ii)
            rr_ = dw_ + ra_
            pp_ = xmb(ii) * dt2 * dbgp(ii)
            ga_ = garea(ii)
            loc(1) = loc(1) + 1.d0
            loc(2) = loc(2) + ga_ * rr_
            loc(3) = loc(3) + ga_ * pp_
            loc(4) = loc(4) + ga_ * abs(rr_ - pp_)
            loc(5) = loc(5) + ga_ * ra_
            loc(6) = max(loc(6), abs(rr_ - pp_))
            loc(7) = max(loc(7), abs(rr_))
            if (dbgph(ii) >= 0.d0 .and. dbgph(ii) < 1.d-12) then
              loc(8) = loc(8) + 1.d0
            elseif (dbgph(ii) >= 1.d-12 .and. dbgph(ii) < 0.999d0) then
              loc(9) = loc(9) + 1.d0
            elseif (dbgph(ii) >= 0.999d0) then
              loc(10) = loc(10) + 1.d0
            endif
            loc(11) = loc(11) + ga_ * abs(rr_)
            if (abs(rr_) > 1.d-3 * ra_) loc(12) = loc(12) + 1.d0
            if (dbgph(ii) >= 0.d0 .and. dbgph(ii) < 1.d-12)
     &        loc(13) = loc(13) + ga_ * xmb(ii) * dt2 * dbgpk(ii)
!$omp critical ({crit}c)
            if (nsamp < 4 .and. abs(pp_) > 2.d-2 * ra_) then
              nsamp = nsamp + 1
              write(*,'(a,2i4,12es12.4)') '{tag}C', kb(ii),
     &          {jm}(ii), dbgph(ii), dbgq1b(ii), dbgq2b(ii),
     &          dbgqob(ii), dbgt1b(ii), eta(ii,kb(ii)), xmb(ii),
     &          dt2, ra_, rr_, pp_, xmb(ii)*dt2*dbgpk(ii)
            endif
!$omp end critical ({crit}c)
          endif
        enddo
!$omp critical ({crit})
        acc(1:5) = acc(1:5) + loc(1:5)
        acc(6) = max(acc(6), loc(6))
        acc(7) = max(acc(7), loc(7))
        acc(8:13) = acc(8:13) + loc(8:13)
        ncall = ncall + 1
        if (mod(ncall, 20) == 0) then
          write(*,'(a,13es13.5)') '{tag}D', acc
          acc = 0.d0
        endif
!$omp end critical ({crit})
      end block dbgsa1
"""

d = Path(sys.argv[1])
# deep
f = d / "samfdeepcnv.f"; s = f.read_text()
s = sub(s, "      real(kind=conv_wp) rrkp, phkp\n", "      real(kind=conv_wp) rrkp, phkp\n" + DECL, "deep decl")
a = ("      flxtvd = 0.0_conv_wp\n      do k = 1, km1\n        do i = 1, im\n"
     "          if(cnvflg(i) .and. k < ktcon(i)) then\n")
s = sub(s, a, "      dbgp = 0.0_conv_wp\n      dbgph = -1.0_conv_wp\n" + a, "deep init")
a = ("!\n! subtract the double counting change rates at jmin+1 & kb beforehand\n!\n"
     "            if(k == jmin(i)) then\n              dp = 1000.0_conv_wp * del(i,k+1)\n"
     "              dellaq(i,k+1) = dellaq(i,k+1) - edto(i)\n")
s = sub(s, a, acc_block(False) + a, "deep acc")
a = "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n"
s = sub(s, a, end_block("DBGSA1D", "dbgsa1d", "jmin") + a, "deep end")
f.write_text(s)
# shallow
f = d / "samfshalcnv.f"; s = f.read_text()
s = sub(s, "      real(kind=conv_wp) rrkp, phkp\n", "      real(kind=conv_wp) rrkp, phkp\n" + DECL, "shal decl")
a = ("      flxtvd = 0.0_conv_wp\n      do k = 1, km1\n        do i = 1, im\n          if(cnvflg(i) .and.\n"
     "     &      (k >= kb(i) .and. k < ktcon(i))) then\n")
s = sub(s, a, "      dbgp = 0.0_conv_wp\n      dbgph = -1.0_conv_wp\n" + a, "shal init")
a = ("     &             * (qo(i,k) - real(q1(i,k+1), kind=conv_wp))\n"
     "              flxtvd(i,k) = eta(i,k) * tem1\n")
# water loop only: the tracer loop's line is indented differently
s = sub(s, a, a + acc_block(True), "shal acc")
a = "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n"
s = sub(s, a, end_block("DBGSA1S", "dbgsa1s", "ktcon") + a, "shal end")
f.write_text(s)
for f in (d / "samfdeepcnv.f", d / "samfshalcnv.f"):
    for n, l in enumerate(f.read_text().splitlines(), 1):
        if "dbg" in l.lower() or "rr_" in l or "loc(" in l or "acc" in l:
            if len(l) > 72 and not l.lstrip().startswith("!"):
                sys.exit(f"ABORT {f.name}:{n} longer than 72: {l!r}")
print("SA1_INSTRUMENT_OK")
