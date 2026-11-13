#!/usr/bin/env python3
"""r15 trace, stage 3 (on a stage-2 tree): negative cloud water left by the MLM tendency, by layer class.
mfscuq_mlm exports mlmb, mlmt, cldbase (module prbk); satmedmfvdifq slots, W(min(q1_qc + dt*mlm_tend_qc, 0)) over
MLM-active columns at: 17 k = mlmb-1 (bottom boundary block), 18 k = mlmt+1 (top boundary block),
19 k = cldbase-1 (cloud-base smoothing target, checked first), 20 mlmb <= k <= mlmt (interior), 21 other.
Usage: apply_probe3.py <tree>"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
P = root / 'UFSATM/ccpp/physics/physics/PBL/SATMEDMF'
edits = {}


def sub(path, a, b):
    s = edits.get(path) or path.read_text()
    n = s.count(a)
    if n != 1:
        sys.exit(f'ABORT {path}: expected 1 match, found {n}: {a.strip()[:70]!r}')
    edits[path] = s.replace(a, b)


m = P / 'mfscuq_mlm.f'
sub(m, "      integer, parameter :: nprb = 16\n", "      integer, parameter :: nprb = 21\n")
sub(m, "      real(kind=kind_phys), allocatable, save :: prb(:,:)\n",
    "      real(kind=kind_phys), allocatable, save :: prb(:,:)\n"
    "      integer, allocatable, save :: prbk(:,:)\n")
sub(m, "      enddo\n\n      return\n      end\n!> @}\n",
    "      enddo\n\n"
    "!prb  r15 trace: export the MLM layer indices\n"
    "      if (prb_on .and. allocated(prbk)) then\n"
    "         do i = 1, im\n"
    "            prbk(i,1) = mlmb(i)\n"
    "            prbk(i,2) = mlmt(i)\n"
    "            prbk(i,3) = cldbase(i)\n"
    "         enddo\n"
    "      endif\n"
    "      return\n      end\n!> @}\n")
s = P / 'satmedmfvdifq.F'
sub(s, "      use mfscuq_mlm_mod, only : mfscuq_mlm, prb_on, prb, nprb\n",
    "      use mfscuq_mlm_mod, only : mfscuq_mlm, prb_on, prb, nprb, prbk\n")
sub(s, "        prq0(1:im,1:km,1:npr) = rtg(1:im,1:km,1:npr)\n",
    "        prq0(1:im,1:km,1:npr) = rtg(1:im,1:km,1:npr)\n"
    "        if (allocated(prbk)) then\n"
    "          if (size(prbk,1) < im) deallocate(prbk)\n"
    "        endif\n"
    "        if (.not. allocated(prbk)) allocate(prbk(im,3))\n"
    "        prbk(1:im,1:3) = 0\n")
sub(s, "             if (mscuflg(i)) prb(i,10) = 1.\n           enddo\n",
    "             if (mscuflg(i)) prb(i,10) = 1.\n           enddo\n"
    "           do i = 1, im\n"
    "             if (mscuflg(i)) then\n"
    "               do k = 1, km\n"
    "                 prt = q1(i,k,ntcw)+delt*(rtg(i,k,ntcw)-prq0(i,k,ntcw))\n"
    "                 prw = min(prt,0.)*del(i,k)*gravi\n"
    "                 if (prbk(i,3).gt.2 .and. k.eq.prbk(i,3)-1) then\n"
    "                   prb(i,19) = prb(i,19) + prw\n"
    "                 elseif (k.eq.prbk(i,1)-1) then\n"
    "                   prb(i,17) = prb(i,17) + prw\n"
    "                 elseif (k.eq.prbk(i,2)+1) then\n"
    "                   prb(i,18) = prb(i,18) + prw\n"
    "                 elseif (k.ge.prbk(i,1).and.k.le.prbk(i,2)) then\n"
    "                   prb(i,20) = prb(i,20) + prw\n"
    "                 else\n"
    "                   prb(i,21) = prb(i,21) + prw\n"
    "                 endif\n"
    "               enddo\n"
    "             endif\n"
    "           enddo\n")
for p, x in edits.items():
    p.write_text(x)
print('APPLY_PROBE3_OK', *(str(p.relative_to(root)) for p in edits))
