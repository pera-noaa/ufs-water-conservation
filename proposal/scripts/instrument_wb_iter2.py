#!/usr/bin/env python3
"""Measure defect E: what the second surface iteration does to Noah-MP land (diagnostic builds only; apply after
instrument_wb_land.py and instrument_wb_noahmp.py, without apply_noahmp_e_patch.py).
Usage: python3 instrument_wb_iter2.py <ufs_model.fd>
noahmpdrv gets the CCPP loop counter (not used to skip); for every column it recomputes on iteration 2, the second
call's precipitation, evapotranspiration and runoff (mm) are kept; GFS_surface_composites_post sums them over land,
weighted by cell area * land fraction (kg). Cumulative per rank, printed with WBL:
  WBQ kdt | 1 precipitation added again | 2 evapotranspiration debited again | 3 runoff again | 4 land area recomputed"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
meta = drv.with_suffix(".meta")
cmp_ = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.F90"
mpt = root / "MP/Thompson/mp_thompson.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


sub(drv, "      shdmin, shdmax, snoalb, sfalb, flag_iter,con_g,            &\n",
    "      shdmin, shdmax, snoalb, sfalb, flag_iter, iter, con_g,     &\n")
sub(drv, "  logical             , dimension(:)     , intent(in)    :: flag_iter  !\n",
    "  logical             , dimension(:)     , intent(in)    :: flag_iter  !\n"
    "  integer                                , intent(in)    :: iter       ! surface iteration (ccpp loop counter)\n")
sub(meta,
    "[flag_iter]\n  standard_name = flag_for_iteration\n  long_name = flag for iteration\n  units = flag\n"
    "  dimensions = (horizontal_loop_extent)\n  type = logical\n  intent = in\n",
    "[flag_iter]\n  standard_name = flag_for_iteration\n  long_name = flag for iteration\n  units = flag\n"
    "  dimensions = (horizontal_loop_extent)\n  type = logical\n  intent = in\n"
    "[iter]\n  standard_name = ccpp_loop_counter\n  long_name = loop counter for subcycling loops in CCPP\n"
    "  units = index\n  dimensions = ()\n  type = integer\n  intent = in\n")
sub(drv, "      real(kind=8), public, save :: wbn(2,13) = 0.d0\n",
    "      real(kind=8), public, save :: wbn(2,13) = 0.d0, wbqs(4) = 0.d0\n"
    "      real(kind=8), public, allocatable, save :: wbq(:,:)\n")
sub(drv, "    if (wbl_kdt >= 0) write(*,'(a,i7,26es24.15)') 'WBN ', wbl_kdt, wbn\n",
    "    if (wbl_kdt >= 0) write(*,'(a,i7,26es24.15)') 'WBN ', wbl_kdt, wbn\n"
    "    if (wbl_kdt >= 0) write(*,'(a,i7,4es24.15)') 'WBQ ', wbl_kdt, wbqs\n")
sub(drv, "  wbl_dt = delt\n",
    "  wbl_dt = delt\n"
    "  if (allocated(wbq)) then\n"
    "    if (size(wbq,1) < im) deallocate(wbq)\n"
    "  endif\n"
    "  if (.not. allocated(wbq)) allocate(wbq(im,3))\n"
    "  if (iter == 1) wbq(1:im,:) = 0.d0\n")
sub(drv, "      wbn(wbn_c,13) = wbn(wbn_c,13) + 1.d0\n",
    "      wbn(wbn_c,13) = wbn(wbn_c,13) + 1.d0\n"
    "      if (iter > 1) then\n"
    "        wbq(i,1) = wbl_pr(i)*delt\n"
    "        wbq(i,2) = wbl_et(i)\n"
    "        wbq(i,3) = (runoff_surface + runoff_baseflow)*delt\n"
    "      endif\n")
sub(cmp_, "      use noahmpdrv, only: wbl, wbl_et, wbl_pr, wbl_tp, wbl_ew, wbl_rn, wbl_dt\n",
    "      use noahmpdrv, only: wbl, wbl_et, wbl_pr, wbl_tp, wbl_ew, wbl_rn, wbl_dt, wbq, wbqs\n")
sub(cmp_, "            wbl(7) = wbl(7) + garea(i)*txl\n",
    "            wbl(7) = wbl(7) + garea(i)*txl\n"
    "            wbqs(1:3) = wbqs(1:3) + garea(i)*txl*wbq(i,1:3)\n"
    "            if (wbq(i,1)+wbq(i,2)+wbq(i,3) /= 0.d0) wbqs(4) = wbqs(4) + garea(i)*txl\n")
sub(mpt, "         use noahmpdrv, only: wbl, wbl_kdt, wbn\n", "         use noahmpdrv, only: wbl, wbl_kdt, wbn, wbqs\n")
sub(mpt, "         write(*,'(a,i7,26es24.15)') 'WBN ', wbl_kdt, wbn\n",
    "         write(*,'(a,i7,26es24.15)') 'WBN ', wbl_kdt, wbn\n"
    "         write(*,'(a,i7,4es24.15)') 'WBQ ', wbl_kdt, wbqs\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBQ").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
