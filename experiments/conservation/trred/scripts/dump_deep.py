#!/usr/bin/env python3
"""trred diagnostic (not a fix): dump every Nth SAMF-deep convecting column (env TRRED_DUMP=N, off when unset/0)
to samfdump/deep_<pid>.bin for offline replays. Adds trred_dump_deep to tm_meter.F90 and two hooks to samfdeepcnv.f.
usage: dump_deep.py <ufs-weather-model tree>"""
import sys
from pathlib import Path
top = Path(sys.argv[1])
phys = top / "UFSATM/ccpp/physics/physics"
f = phys / "CONV/SAMF/samfdeepcnv.f"
m = phys / "Interstitials/UFS_SCM_NEPTUNE/tm_meter.F90"
s = f.read_text()
def sub(s, old, new):
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {n} matches: {old.strip()[:70]!r}")
    return s.replace(old, new)
s = sub(s, "      use tm_meter, only : tm_x\n",
        "      use tm_meter, only : tm_x\n      use tm_meter, only : trred_dump_deep\n")
s = sub(s, "      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n",
        "      real(kind=conv_wp) tsumn(im), tsump(im), rtnp(im)\n"
        "      real(kind=conv_wp) dmp_qoi(im,km)\n")
old = ("            ctro(i,k,n) = .5_conv_wp * (ctro(i,k,n) + ctro(i,k+1,n))\n"
       "          endif\n        enddo\n      enddo\n      enddo\n      endif\n")
s = sub(s, old, old + "      dmp_qoi = qo\n")
old = "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n"
s = sub(s, old,
        "      call trred_dump_deep(im,km,nn,ntr,ntc,itc,ntk,cnvflg,kb,jmin,\n"
        "     &  ktcon,kbcon,kmax,kd94,rn,xmb,edto,xlamdet,dt2,eta,etad,\n"
        "     &  xlamue,xlamud,zi,del,delp,c0t,q,q1,dmp_qoi,dellaq,qcko,\n"
        "     &  qrcko,qcdo,qrcdo,new_q1,qtr,new_qtr,chem_pw,wet_dep,fscav)\n"
        + old)
f.write_text(s)
t = m.read_text()
t = t.replace("            tm_samf_substep, tm_x\n", "            tm_samf_substep, tm_x, trred_dump_deep\n", 1)
assert "trred_dump_deep\n" in t
code = r'''
  !> trred: dump every Nth deep convecting column (env TRRED_DUMP=N) for offline replays (64-bit SAMF only)
  subroutine trred_dump_deep(im, km, nn, ntr, ntc, itc, ntk, cnvflg, kb, jmin, ktcon, kbcon, kmax, kd94, rn, xmb, &
       edto, xlamdet, dt2, eta, etad, xlamue, xlamud, zi, del, delp, c0t, q, q1, qoi, dellaq, qcko, qrcko, qcdo, &
       qrcdo, new_q1, qtr, new_qtr, chem_pw, wet_dep, fscav)
    use iso_c_binding, only : c_int
    interface
      function c_getpid() bind(c, name='getpid')
        import :: c_int
        integer(c_int) :: c_getpid
      end function c_getpid
    end interface
    integer, intent(in) :: im, km, nn, ntr, ntc, itc, ntk
    logical, intent(in) :: cnvflg(im)
    integer, intent(in) :: kb(im), jmin(im), ktcon(im), kbcon(im), kmax(im), kd94(im)
    real(8), intent(in) :: rn(:), xmb(im), edto(im), xlamdet(im), dt2
    real(8), intent(in) :: eta(im,km), etad(im,km), xlamue(im,km), xlamud(im,km), zi(im,km), del(im,km), &
         c0t(im,km), qoi(im,km), dellaq(im,km), qcko(im,km), qrcko(im,km), qcdo(im,km), qrcdo(im,km), new_q1(im,km)
    real(8), intent(in) :: delp(:,:), q(:,:), q1(:,:), qtr(:,:,:), fscav(:)
    real(8), intent(in) :: new_qtr(im,km,nn), chem_pw(im,km,ntc), wet_dep(im,km,ntc)
    integer, save :: every = -1, u = -1, cnt = 0, nrec = 0
    integer, parameter :: maxrec = 4000
    character(len=64) :: s
    integer :: i, st, hdr(16)
    real(8) :: r(8)
    if (every < 0) then
      every = 0
      call get_environment_variable('TRRED_DUMP', s, status=st)
      if (st == 0) read(s, *, iostat=st) every
      if (st /= 0) every = 0
      if (every > 0) then
        write(s, '(a,i0,a)') 'samfdump/deep_', c_getpid(), '.bin'
        open(newunit=u, file=trim(s), access='stream', form='unformatted', status='replace', iostat=st)
        if (st /= 0) every = 0
      endif
    endif
    if (every <= 0) return
    do i = 1, im
      if (.not. cnvflg(i)) cycle
      cnt = cnt + 1
      if (mod(cnt, every) /= 0 .or. nrec >= maxrec) cycle
      nrec = nrec + 1
      hdr = 0
      hdr(1:16) = (/ 20261017, km, ntr, ntc, itc, ntk, kb(i), jmin(i), ktcon(i), kbcon(i), kmax(i), kd94(i), &
                     merge(1, 0, rn(i) > 0.d0), i, nn, cnt /)
      r = 0.d0
      r(1:5) = (/ xmb(i), edto(i), xlamdet(i), dt2, rn(i) /)
      write(u) hdr, r
      if (ntc > 0) write(u) fscav(1:ntc)
      write(u) eta(i,:), etad(i,:), xlamue(i,:), xlamud(i,:), zi(i,:), del(i,:), delp(i,1:km), c0t(i,:), &
               q(i,1:km), q1(i,1:km), qoi(i,:), dellaq(i,:), qcko(i,:), qrcko(i,:), qcdo(i,:), qrcdo(i,:), new_q1(i,:)
      write(u) qtr(i,1:km,3:ntr+2), new_qtr(i,1:km,3:ntr+2)
      if (ntc > 0) write(u) chem_pw(i,:,1:ntc), wet_dep(i,:,1:ntc)
    enddo
    flush(u)
  end subroutine trred_dump_deep
'''
t = t.replace("end module tm_meter", code + "end module tm_meter", 1)
m.write_text(t)
print("DUMP_OK")
