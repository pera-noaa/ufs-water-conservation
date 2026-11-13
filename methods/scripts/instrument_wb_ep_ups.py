#!/usr/bin/env python3
"""Double-precision closure of the physics' water against its own fluxes, every step and column (WBQ), for the upstream
layout; port of instrument_wb_ep.py without its dependence on the land meters. Diagnostic builds only; apply after
instrument_wb_phys_ups.py. Usage: python3 instrument_wb_ep_ups.py <ufs-weather-model>
No .meta change: satmedmfvdifq, the h2ophys run method and GFS_MP_generic_post append per-column values, chunk after
chunk, to queues in GFS_physics_post, which reads them back in the same order (one OpenMP thread) and closes each
column against the WBP meter:
  E_add = water satmedmfvdifq adds from the surface flux, dt*evap*del1/(g*dz1)    E_book = dt*evap*rho_a (as reported)
  H     = h2ophys' column change, sum(dq*dp)/g                                     P      = 1000*rain (m -> kg/m2)
  R     = WBP column change - (E_add + H - P)
WBQ kdt | 1 E_add | 2 E_book | 3 P | 4 H (all sum(x*area), kg) | 5 sum(|R|*area) (kg) | 6 max |R| (kg/m2) | 7 sum(R*area)
cumulative per rank, printed with WBP when the step index changes and at finalize."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
post = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90"
pbl = root / "PBL/SATMEDMF/satmedmfvdifq.F"
h2o = root / "photochem/module_h2ophys.F90"
mpp = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.F90"
drv = root / "MP/Thompson/mp_thompson.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


NC = 8192  # > columns per rank
sub(post, "  integer, public, save :: wbp_kdt = -1\n",
    "  integer, public, save :: wbp_kdt = -1\n"
    "  real(kind=8), public, save :: wbq(7) = 0.0d0\n"
    f"  real(kind=8), public, save :: wbq_c(4,{NC}) = 0.0d0\n"
    "  real(kind=8), allocatable, public, save :: wbq_h(:,:)\n"
    "  integer, public, save :: wbq_n(3) = 0\n"
    "  integer, save :: wbq_r = 0\n")
sub(post, "    real(kind=8) :: wb_s\n", "    real(kind=8) :: wb_s, wb_h, wb_r\n    integer :: j\n")
sub(post, "       if (wbp_kdt >= 0) write(*,'(a,i7,3es24.15)') 'WBP ', wbp_kdt, wbp\n",
    "       if (wbp_kdt >= 0) write(*,'(a,i7,3es24.15)') 'WBP ', wbp_kdt, wbp\n"
    "       if (wbp_kdt >= 0) write(*,'(a,i7,7es24.15)') 'WBQ ', wbp_kdt, wbq\n")
sub(post, "       wbp(3) = wbp(3) + garea(i)\n",
    "       wbp(3) = wbp(3) + garea(i)\n"
    "       j = wbq_r + i\n"
    "       wb_h = 0.0d0\n"
    "       if (allocated(wbq_h)) then\n"
    "          do k = 1, nLev\n"
    "             wb_h = wb_h + wbq_h(j,k)*(prsi(i,k)-prsi(i,k+1))\n"
    "          enddo\n"
    "          wb_h = wb_h/con_g\n"
    "       endif\n"
    "       wb_r = wb_s - (wbq_c(1,j) + wb_h - wbq_c(3,j))\n"
    "       wbq(1) = wbq(1) + wbq_c(1,j)*garea(i)\n"
    "       wbq(2) = wbq(2) + wbq_c(2,j)*garea(i)\n"
    "       wbq(3) = wbq(3) + wbq_c(3,j)*garea(i)\n"
    "       wbq(4) = wbq(4) + wb_h*garea(i)\n"
    "       wbq(5) = wbq(5) + abs(wb_r)*garea(i)\n"
    "       wbq(6) = max(wbq(6), abs(wb_r))\n"
    "       wbq(7) = wbq(7) + wb_r*garea(i)\n"
    "       wbq_c(:,j) = 0.0d0\n"
    "       if (allocated(wbq_h)) wbq_h(j,:) = 0.0d0\n")
sub(post, "    if(.not.ldiag3d) then\n",
    "    ! all queued columns of this step read: start the queues again\n"
    "    wbq_r = wbq_r + nCol\n"
    "    if (wbq_r >= wbq_n(1)) then\n"
    "       wbq_r = 0\n"
    "       wbq_n = 0\n"
    "    endif\n\n"
    "    if(.not.ldiag3d) then\n")
# boundary layer (fixed form, <= 72 columns): f2(i,1) = q1(i,1,1) + dtdz1(i)*evap(i) is what it adds
sub(pbl, "      use machine  , only : kind_phys\n      use funcphys , only : fpvs\n!\n      implicit none\n",
    "      use machine  , only : kind_phys\n      use funcphys , only : fpvs\n"
    "      use GFS_physics_post, only: wbq_c, wbq_n\n!\n      implicit none\n")
sub(pbl, "        dqsfc(i) = rho_a(i) * hvap * evap(i)\n      enddo\n",
    "        dqsfc(i) = rho_a(i) * hvap * evap(i)\n"
    "        wbq_c(1,wbq_n(1)+i) = dt2*evap(i)*del(i,1)/\n"
    "     &               (grav*(zi(i,2)-zi(i,1)))\n"
    "        wbq_c(2,wbq_n(1)+i) = dt2*evap(i)*rho_a(i)\n"
    "      enddo\n"
    "      wbq_n(1) = wbq_n(1) + im\n")
# h2ophys run method
sub(h2o, "  subroutine run(this, dt, p, h2opltc, h2o, dqv_dt_prd, dqv_dt_qv)\n",
    "  subroutine run(this, dt, p, h2opltc, h2o, dqv_dt_prd, dqv_dt_qv)\n"
    "    use GFS_physics_post, only: wbq_h, wbq_n\n")
sub(h2o, "    nCol = size(p,1)\n    nLev = size(p,2)\n",
    "    nCol = size(p,1)\n    nLev = size(p,2)\n"
    f"    if (.not. allocated(wbq_h)) allocate(wbq_h({NC},nLev))\n"
    "    wbq_h(wbq_n(2)+1:wbq_n(2)+nCol,1:nLev) = h2o(1:nCol,1:nLev)\n")
sub(h2o, "    enddo\n\n\n    return\n  end subroutine run\n",
    "    enddo\n\n"
    "    wbq_h(wbq_n(2)+1:wbq_n(2)+nCol,1:nLev) = h2o(1:nCol,1:nLev) - wbq_h(wbq_n(2)+1:wbq_n(2)+nCol,1:nLev)\n"
    "    wbq_n(2) = wbq_n(2) + nCol\n\n"
    "    return\n  end subroutine run\n")
# precipitation as finally reported
sub(mpp, "      module GFS_MP_generic_post\n", "      module GFS_MP_generic_post\n      use GFS_physics_post, only: wbq_c, wbq_n\n")
sub(mpp, "      endif\n\n      end subroutine GFS_MP_generic_post_run\n",
    "      endif\n\n      do i = 1, im\n         wbq_c(3,wbq_n(3)+i) = 1.0d3*rain(i)\n      enddo\n      wbq_n(3) = wbq_n(3) + im\n\n"
    "      end subroutine GFS_MP_generic_post_run\n")
# finalize print
sub(drv, "         write(*,'(a,i7,3es24.15)') 'WBP ', wbp_kdt, wbp\n",
    "         write(*,'(a,i7,3es24.15)') 'WBP ', wbp_kdt, wbp\n"
    "         write(*,'(a,i7,7es24.15)') 'WBQ ', wbp_kdt, wbq\n")
sub(drv, "         use GFS_physics_post, only: wbp, wbp_kdt\n", "         use GFS_physics_post, only: wbp, wbp_kdt, wbq\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBQ").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
