#!/usr/bin/env python3
"""r15 trace: passive water probes in satmedmfvdifq (+ module storage in mfscuq_mlm_mod, report in GFS_budget).
Usage: apply_probe.py <ufs-weather-model tree>. Every anchor must match exactly once, else nothing is written.
Probe slots (kg/m2 per step per column, water = vdiff slots 1..6 = qv qc qi qr qs qg in P8 Thompson):
 1 MLM water change dt*W(rtg_after_mlm - rtg0)     2 solver W(f2_tridin - q1)        3 solver surface source dtdz1*evap*del1/g
 4 fixers W(f2_fixed - f2_tridin)                   5 scheme total dt*W(rtg_end - rtg0) 6 declared E = dt*rho_a*evap
 7 W(min(q1+dt*(rtg_end-rtg0),0))                    8 W(min(q1,0)) on entry           9 W(min(q1+dt*mlm_tend,0))
10 MLM-active flag (mscuflg after call)             11 MLM gross dt*W|mlm_tend|        12 = 5-6 scheme residual
13 = 5-(1+2+4) decomposition check                  14 = 2-3 solver residual
Switch at run time: &budget_nml budget_probe (needs budget_hook, 1 thread)."""
import sys
from pathlib import Path

root = Path(sys.argv[1])
P = root / 'UFSATM/ccpp/physics/physics/PBL/SATMEDMF'
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f'ABORT {path}: expected 1 match, found {n}: {old.strip()[:70]!r}')
    edits[path] = s.replace(old, new)


def W(slot, expr, extra=''):
    return (f"        do mpr = 1, npr\n          do k = 1, km\n            do i = 1, im\n"
            f"              prw = del(i,k)*gravi\n{extra}"
            f"              prb(i,{slot}) = prb(i,{slot}) + {expr}*prw\n"
            f"            enddo\n          enddo\n        enddo\n")


m = P / 'mfscuq_mlm.f'
sub(m, "      module mfscuq_mlm_mod\n      contains\n",
    "      module mfscuq_mlm_mod\n"
    "      use machine, only : kind_phys\n"
    "!prb  r15 trace: passive water probes, filled by satmedmfvdifq\n"
    "      logical, save :: prb_on = .false.\n"
    "      integer, parameter :: nprb = 14\n"
    "      real(kind=kind_phys), allocatable, save :: prb(:,:)\n"
    "      contains\n")

s = P / 'satmedmfvdifq.F'
txt = s.read_text()
for tok in (' prq0', ' prw', ' mpr', ' npr', ' prt'):
    if tok + ' ' in txt or tok + '(' in txt or tok + ',' in txt or tok + '\n' in txt:
        sys.exit(f'ABORT name clash {tok}')
sub(s, "      use mfscuq_mlm_mod, only : mfscuq_mlm\n",
    "      use mfscuq_mlm_mod, only : mfscuq_mlm, prb_on, prb, nprb\n")
sub(s, "      real(kind=kind_phys) radmin(im)\n",
    "      real(kind=kind_phys) radmin(im)\n"
    "!prb\n      real(kind=kind_phys), allocatable :: prq0(:,:,:)\n"
    "      real(kind=kind_phys) prw, prt\n      integer mpr, npr\n")
sub(s, "!+mlm !stratocumulus mixed-layer model for turbulent fluxes\n",
    "!prb  r15 trace: snapshot of the water slots of rtg before the MLM\n"
    "      if (prb_on) then\n"
    "        npr = min(6, ntrac1)\n"
    "        if (allocated(prb)) then\n"
    "          if (size(prb,1) < im) deallocate(prb)\n"
    "        endif\n"
    "        if (.not. allocated(prb)) allocate(prb(im,nprb))\n"
    "        prb(1:im,1:nprb) = 0.\n"
    "        allocate(prq0(im,km,npr))\n"
    "        prq0(1:im,1:km,1:npr) = rtg(1:im,1:km,1:npr)\n"
    + W(8, "min(q1(i,k,mpr),0.)") +
    "      endif\n"
    "!+mlm !stratocumulus mixed-layer model for turbulent fluxes\n")
sub(s, "     &        eflux,rflux,wflux,pflux)\n\n         do k = 1, km1\n",
    "     &        eflux,rflux,wflux,pflux)\n"
    "!prb\n"
    "         if (prb_on) then\n"
    + W(1, "prt", "              prt = delt*(rtg(i,k,mpr)-prq0(i,k,mpr))\n"
        "              prb(i,11) = prb(i,11) + abs(prt)*prw\n"
        "              prb(i,9) = prb(i,9) + min(q1(i,k,mpr)+prt,0.)*prw\n") +
    "           do i = 1, im\n"
    "             if (mscuflg(i)) prb(i,10) = 1.\n"
    "           enddo\n"
    "         endif\n"
    "\n         do k = 1, km1\n")
sub(s, "      call tridin(im,km,ntrac1,al,ad,au,f1,f2,au,f1,f2)\n",
    "      call tridin(im,km,ntrac1,al,ad,au,f1,f2,au,f1,f2)\n"
    "!prb\n"
    "      if (prb_on) then\n"
    + W(2, "prt", "              prt = f2(i,k+(mpr-1)*km)-q1(i,k,mpr)\n") +
    "        do i = 1, im\n"
    "          prb(i,3) = dtdz1(i)*evap(i)*del(i,1)*gravi\n"
    "          prb(i,6) = delt*rho_a(i)*evap(i)\n"
    "        enddo\n"
    "      endif\n")
sub(s, "!> - Recover the tendencies of heat and moisture\n",
    "!prb\n"
    "      if (prb_on) then\n"
    + W(4, "prt", "              prt = f2(i,k+(mpr-1)*km)-q1(i,k,mpr)\n") +
    "        do i = 1, im\n"
    "          prb(i,4) = prb(i,4) - prb(i,2)\n"
    "        enddo\n"
    "      endif\n"
    "!> - Recover the tendencies of heat and moisture\n")
sub(s, "!> ## Save PBL height for diagnostic purpose\n",
    "!prb\n"
    "      if (prb_on) then\n"
    + W(5, "prt", "              prt = delt*(rtg(i,k,mpr)-prq0(i,k,mpr))\n"
        "              prb(i,7) = prb(i,7) + min(q1(i,k,mpr)+prt,0.)*prw\n") +
    "        do i = 1, im\n"
    "          prb(i,12) = prb(i,5) - prb(i,6)\n"
    "          prb(i,13) = prb(i,5) - (prb(i,1) + prb(i,2) + prb(i,4))\n"
    "          prb(i,14) = prb(i,2) - prb(i,3)\n"
    "        enddo\n"
    "        deallocate(prq0)\n"
    "      endif\n"
    "!> ## Save PBL height for diagnostic purpose\n")

g = root / 'UFSATM/ccpp/driver/GFS_budget.F90'
sub(g, "  use CCPP_data,         only: GFS_control, GFS_statein, GFS_stateout, GFS_intdiag, GFS_grid, GFS_interstitial\n",
    "  use CCPP_data,         only: GFS_control, GFS_statein, GFS_stateout, GFS_intdiag, GFS_grid, GFS_interstitial\n"
    "  use mfscuq_mlm_mod,    only: prb_on, prb, nprb\n")
sub(g, "  logical  :: budget_hook = .false.       ! C\n",
    "  logical  :: budget_hook = .false.       ! C\n"
    "  logical  :: budget_probe = .false.      ! r15 trace: satmedmfvdifq water probes (needs hook, 1 thread)\n")
sub(g, "  namelist /budget_nml/ budget_meter, budget_hook, budget_tol_report, budget_tol_fatal\n",
    "  namelist /budget_nml/ budget_meter, budget_hook, budget_tol_report, budget_tol_fatal, budget_probe\n")
sub(g, "  real(r8), allocatable :: c_dw(:,:)\n",
    "  real(r8), allocatable :: c_dw(:,:)\n  real(r8), allocatable :: p_acc(:,:)\n")
sub(g, "    allocate(c_dw(n, nslot_max))\n",
    "    allocate(c_dw(n, nslot_max))\n"
    "    if (budget_probe) then\n"
    "      if (.not. budget_hook) call mpp_error(FATAL, 'GFS_budget: budget_probe needs budget_hook')\n"
    "      if (GFS_control%nthreads > 1) call mpp_error(FATAL, 'GFS_budget: budget_probe needs 1 thread')\n"
    "      allocate(p_acc(n, nprb))\n"
    "      p_acc = 0\n"
    "      prb_on = .true.\n"
    "    endif\n")
sub(g, "    c_dw = 0\n    if (associated(GFS_intdiag%budget_b_dw)) then\n",
    "    c_dw = 0\n    if (allocated(p_acc)) p_acc = 0\n    if (associated(GFS_intdiag%budget_b_dw)) then\n")
sub(g, "    if (group /= 'phys_ps' .and. group /= 'phys_ts') return\n",
    "    if (group /= 'phys_ps' .and. group /= 'phys_ts') return\n"
    "    if (prb_on .and. trim(scheme) == 'satmedmfvdifq') then\n"
    "      if (allocated(prb)) p_acc(lb:ub, :) = p_acc(lb:ub, :) + prb(1:ub-lb+1, :)\n"
    "    endif\n")
sub(g, "      call line('water', 'C:sum_vs_A', csum, gmean(s_dw, Atm_block), csum - gmean(s_dw, Atm_block), &\n"
       "                gmean(s_gap, Atm_block), gmax(s_gap))\n",
    "      call line('water', 'C:sum_vs_A', csum, gmean(s_dw, Atm_block), csum - gmean(s_dw, Atm_block), &\n"
    "                gmean(s_gap, Atm_block), gmax(s_gap))\n"
    "      if (prb_on) then\n"
    "        do s = 1, nprb\n"
    "          write(nm, '(a,i2.2)') 'P:satmedmfvdifq:', s\n"
    "          call line('water', trim(nm), gmean(p_acc(:, s), Atm_block), 0._r8, 0._r8, &\n"
    "                    gmean(abs(p_acc(:, s)), Atm_block), gmax(p_acc(:, s)))\n"
    "        enddo\n"
    "      endif\n")

for p, t in edits.items():
    p.write_text(t)
print('APPLY_PROBE_OK', *(str(p.relative_to(root)) for p in edits))
