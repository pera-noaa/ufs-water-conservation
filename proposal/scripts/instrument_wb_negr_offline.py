#!/usr/bin/env python3
"""Offline harness: drives semi_lagrange_sedim from a given module_mp_thompson.F90 like mp_thompson's sedi_semi rain branch (R1 floor, substeps, qrten frame) and meters new negative rain.
Usage: python3 instrument_wb_negr_offline.py <fixed module_mp_thompson.F90> <upstream module_mp_thompson.F90> [workdir]
Variants: 1 = fixed routine as is (M5), 2 = fixed routine + floored layers enter with their actual rain
(fix_thompson_negr_rain_floor.py), 3 = upstream routine (max(qn,R1)). Needs gfortran."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def routine(src, name):
    s = Path(src).read_text()
    m = re.search(r"^ *SUBROUTINE semi_lagrange_sedim.*?END SUBROUTINE semi_lagrange_sedim", s, re.S | re.M)
    if not m:
        sys.exit(f"ABORT: semi_lagrange_sedim not found in {src}")
    return m.group(0).replace("semi_lagrange_sedim", name)


DRIVER = r'''program caller
! mimics mp_thompson's sedi_semi rain branch: rr floored at R1 where qr_pre <= R1; qrten accumulates (rr-rr_tmp)/(rho dt)
use slmf
use slmu
implicit none
integer, parameter :: km=127, ntrial=20000
real(8), parameter :: R1=1d-12
real(8) :: dz(km), rho(km), qpre(km), rr(km), rr0(km), rrt(km), vt(km), qrten(km), pf(km), qx(km), u, dt, dtcfl, precip, ptot
real(8) :: negm(3), negn(3), pm(3), qerr(3), negmax(3)
integer :: it, k, k1, k2, ip, npatch, niter, nstep, n, iv
negm=0; negn=0; pm=0; qerr=0; negmax=0
dt = 720d0
do it=1,ntrial
  do k=1,km
    dz(k) = 20d0*1.035d0**(k-1); rho(k) = 1.2d0*exp(-sum(dz(1:k))/8000d0)
  enddo
  qpre = 0d0
  call random_number(u); npatch = 1+int(u*4)
  do ip=1,npatch
    call random_number(u); k1 = 1+int(u*70)
    call random_number(u); k2 = min(km, k1+int(u*25))
    do k=k1,k2
      call random_number(u); qpre(k) = 10d0**(-11d0 + 8d0*u)
      call random_number(u); if (u<0.2) qpre(k) = 0d0
      call random_number(u); if (u<0.05) qpre(k) = -1d-12*u*20
    enddo
  enddo
  do iv=1,3   ! 1 = M5 as is, 2 = M5 + fix (floored cells carry qpre*rho), 3 = upstream max(qn,R1)
    do k=1,km
      if (qpre(k) > R1) then
        rr(k) = qpre(k)*rho(k)
      else
        rr(k) = R1
      endif
      if (iv==2 .and. rr(k) <= R1) rr(k) = qpre(k)*rho(k)
    enddo
    rr0 = rr; qrten = 0d0; ptot = 0d0
    call vel(rr, vt)
    nstep = 0
    do k=1,km
      if (vt(k) > 1d-3) nstep = max(nstep, int(dt*vt(k)/dz(k)+1d0))
    enddo
    niter = int(nstep/10)+1; dtcfl = dt/niter
    do n=1,niter
      rrt = rr
      if (iv==3) then
        call sls_up(km,dz,vt,rr,precip,pf,dtcfl,R1)
      else
        call sls_fixed(km,dz,vt,rr,precip,pf,dtcfl,R1)
      endif
      do k=1,km
        qrten(k) = qrten(k) + (rr(k)-rrt(k))*(1d0/(rho(k)*dt))
      enddo
      ptot = ptot + precip
      call vel(rr, vt)
    enddo
    qx = qpre + qrten*dt
    do k=1,km
      if (qx(k) < 0d0 .and. qpre(k) >= 0d0) then   ! new negatives only
        negm(iv) = negm(iv) - qx(k)*rho(k)*dz(k); negn(iv) = negn(iv)+1
        negmax(iv) = max(negmax(iv), -qx(k)*rho(k)/R1)
      endif
    enddo
    pm(iv) = pm(iv) + ptot
    qerr(iv) = qerr(iv) + (sum(qx*rho*dz) - sum(qpre*rho*dz) + ptot)
  enddo
enddo
print '(a)', 'variant: 1=M5  2=M5+fix  3=upstream'
do iv=1,3
  print '(i2,a,es12.4,a,f10.0,a,es12.4,a,es12.4,a,es12.4)', iv, ' new-neg mass/col',negm(iv)/ntrial,' n',negn(iv), &
    ' max neg rho*q/R1',negmax(iv),' precip/col',pm(iv)/ntrial,' q-frame budget resid/col',qerr(iv)/ntrial
enddo
contains
subroutine vel(r, v)
real(8), intent(in) :: r(km)
real(8), intent(out) :: v(km)
integer :: j
do j=1,km
  if (r(j) > R1) then
    v(j) = 1d0 + 8d0*min(1d0, (r(j)/1d-3)**0.25d0)
  else
    v(j) = 0d0
  endif
enddo
end subroutine
end program
'''

wd = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(tempfile.mkdtemp())
wd.mkdir(parents=True, exist_ok=True)
(wd / "slmf.f90").write_text("module slmf\nimplicit none\ninteger, parameter :: wp=8\ncontains\n"
                             + routine(sys.argv[1], "sls_fixed") + "\nend module slmf\n")
(wd / "slmu.f90").write_text("module slmu\nimplicit none\ninteger, parameter :: wp=8\ncontains\n"
                             + routine(sys.argv[2], "sls_up") + "\nend module slmu\n")
(wd / "caller.f90").write_text(DRIVER)
subprocess.run(["gfortran", "-O0", "slmf.f90", "slmu.f90", "caller.f90", "-o", "caller"], cwd=wd, check=True)
subprocess.run(["./caller"], cwd=wd, check=True)
