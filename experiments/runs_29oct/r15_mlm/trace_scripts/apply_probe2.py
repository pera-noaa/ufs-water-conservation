#!/usr/bin/env python3
"""r15 trace, stage 2 (on a tree that already has apply_probe.py):
 - satmedmfvdifq slots 15 = flag q1(i,1,1) < qmin, 16 = solver surface source - declared E (= P03 - P06)
 - mp_thompson_run: raw negatives of the inputs (1-6: qv qc qr qi qs qg) and outputs (7-12), weighted with
   GFS_statein%prsi in the GFS_budget hook -> 'P:mp_thompson:NN' (kg/m2 per window)
 - --old-dtdz1: revert the PBL surface flux to the 29-Oct tree's dtdz1 = dt2/(zi(2)-zi(1))
Usage: apply_probe2.py <tree> [--old-dtdz1]. Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root = Path(sys.argv[1])
old = '--old-dtdz1' in sys.argv
P = root / 'UFSATM/ccpp/physics/physics'
edits = {}


def sub(path, a, b):
    s = edits.get(path) or path.read_text()
    n = s.count(a)
    if n != 1:
        sys.exit(f'ABORT {path}: expected 1 match, found {n}: {a.strip()[:70]!r}')
    edits[path] = s.replace(a, b)


m = P / 'PBL/SATMEDMF/mfscuq_mlm.f'
sub(m, "      integer, parameter :: nprb = 14\n", "      integer, parameter :: nprb = 16\n")
s = P / 'PBL/SATMEDMF/satmedmfvdifq.F'
sub(s, "          prb(i,14) = prb(i,2) - prb(i,3)\n",
    "          prb(i,14) = prb(i,2) - prb(i,3)\n"
    "          prb(i,16) = prb(i,3) - prb(i,6)\n"
    "          if (q1(i,1,1) < qmin) prb(i,15) = 1.\n")
if old:
    sub(s, "!  surface fluxes applied to the host layer mass del/g\n"
           "         dtdz1(i)  = dt2 * rho_a(i) * g / del(i,1)\n",
        "!r15 trace: 29-Oct tree form (geometric depth)\n"
        "         dtdz1(i)  = dt2 / (zi(i,2)-zi(i,1))\n")

t = P / 'MP/Thompson/mp_thompson.F90'
sub(t, "      integer, parameter :: ext_ndiag3d = 37\n",
    "      integer, parameter :: ext_ndiag3d = 37\n"
    "      ! r15 trace: passive negative-water probes (inputs 1-6, outputs 7-12: qv qc qr qi qs qg)\n"
    "      logical, save, public :: mprb_on = .false.\n"
    "      real(kind_phys), allocatable, save, public :: mprb(:,:,:)\n")
sub(t, "         new_qg = qg\n",
    "         new_qg = qg\n"
    "         if (mprb_on) then\n"
    "           if (allocated(mprb)) then\n"
    "             if (size(mprb,1) < ncol .or. size(mprb,2) /= nlev) deallocate(mprb)\n"
    "           endif\n"
    "           if (.not. allocated(mprb)) allocate(mprb(ncol,nlev,12))\n"
    "           mprb(1:ncol,:,:) = 0._kind_phys\n"
    "           mprb(1:ncol,:,1) = min(spechum(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,2) = min(qc(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,3) = min(qr(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,4) = min(qi(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,5) = min(qs(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,6) = min(qg(1:ncol,:), 0._kind_phys)\n"
    "         endif\n")
sub(t, "         dqg = (new_qg - qg)/dtp\n",
    "         dqg = (new_qg - qg)/dtp\n"
    "         if (mprb_on) then\n"
    "           mprb(1:ncol,:,7) = min(new_spechum(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,8) = min(new_qc(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,9) = min(new_qr(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,10) = min(new_qi(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,11) = min(new_qs(1:ncol,:), 0._kind_phys)\n"
    "           mprb(1:ncol,:,12) = min(new_qg(1:ncol,:), 0._kind_phys)\n"
    "         endif\n")

g = root / 'UFSATM/ccpp/driver/GFS_budget.F90'
sub(g, "  use mfscuq_mlm_mod,    only: prb_on, prb, nprb\n",
    "  use mfscuq_mlm_mod,    only: prb_on, prb, nprb\n  use mp_thompson,       only: mprb_on, mprb\n")
sub(g, "  real(r8), allocatable :: p_acc(:,:)\n", "  real(r8), allocatable :: p_acc(:,:), m_acc(:,:)\n")
sub(g, "      allocate(p_acc(n, nprb))\n      p_acc = 0\n      prb_on = .true.\n",
    "      allocate(p_acc(n, nprb))\n      p_acc = 0\n      prb_on = .true.\n"
    "      allocate(m_acc(n, 12))\n      m_acc = 0\n      mprb_on = .true.\n")
sub(g, "    if (allocated(p_acc)) p_acc = 0\n", "    if (allocated(p_acc)) p_acc = 0\n    if (allocated(m_acc)) m_acc = 0\n")
sub(g, "      if (allocated(prb)) p_acc(lb:ub, :) = p_acc(lb:ub, :) + prb(1:ub-lb+1, :)\n    endif\n",
    "      if (allocated(prb)) p_acc(lb:ub, :) = p_acc(lb:ub, :) + prb(1:ub-lb+1, :)\n    endif\n"
    "    if (mprb_on .and. trim(scheme) == 'mp_thompson' .and. allocated(mprb)) then\n"
    "      do i = lb, ub\n"
    "        do m = 1, 12\n"
    "          w = 0._r8\n"
    "          do k = 1, GFS_control%levs\n"
    "            w = w + mprb(i-lb+1, k, m)*(GFS_statein%prsi(i, k) - GFS_statein%prsi(i, k+1))\n"
    "          enddo\n"
    "          m_acc(i, m) = m_acc(i, m) + w/con_g\n"
    "        enddo\n"
    "      enddo\n"
    "    endif\n")
sub(g, "                    gmean(abs(p_acc(:, s)), Atm_block), gmax(p_acc(:, s)))\n        enddo\n",
    "                    gmean(abs(p_acc(:, s)), Atm_block), gmax(p_acc(:, s)))\n        enddo\n"
    "        do s = 1, 12\n"
    "          write(nm, '(a,i2.2)') 'P:mp_thompson:', s\n"
    "          call line('water', trim(nm), gmean(m_acc(:, s), Atm_block), 0._r8, 0._r8, &\n"
    "                    gmean(abs(m_acc(:, s)), Atm_block), gmax(m_acc(:, s)))\n"
    "        enddo\n")

for p, x in edits.items():
    p.write_text(x)
print('APPLY_PROBE2_OK', 'old_dtdz1' if old else '', *(str(p.relative_to(root)) for p in edits))
