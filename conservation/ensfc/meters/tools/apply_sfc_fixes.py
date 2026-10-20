#!/usr/bin/env python3
"""Candidate surface energy fixes, applied by anchor substitution to a ufs-weather-model tree (with or without meters).
Usage: apply_sfc_fixes.py <ufs-weather-model> <fix id> [<fix id> ...]
  SI1  sfc_sice: step the sea ice on the first surface iteration only (an icy cell with cice < 1 is also wet, and is
       re-flagged at wind < 2 m/s for NSST's second pass; the ice has no guess/restore, so it was stepped twice)
  SI2  sfc_sice ice3lay: excess lower-layer heat melts h2*ci*(T2-tfi)/li of ice, not that divided by delt
  SI3  NSST: in an icy cell (frac_grid, 0 < cice < 1) the open water absorbs the open-water share sfc_sice assumes
       (snetw), not the cell-mean net SW, so ice + open water = the cell net SW the atmosphere books
  NP1  Noah-MP phasechange: the heat of a snow layer that melts out warms the layer below when that layer is not
       melting (it was handed to hm(j+1), which is applied only to a melting layer)
Every anchor must match the stated number of times; nothing is written unless all match."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
icem = root / "SFC_Models/SeaIce/CICE/sfc_sice.meta"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
nst = root / "SFC_Layer/UFS/sfc_nst.f90"
nstm = root / "SFC_Layer/UFS/sfc_nst.meta"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def si1():
    sub(ice, "     &       errmsg, errflg\n     &     )\n", "     &       errmsg, errflg, iter\n     &     )\n")
    sub(ice, "      integer, intent(in) :: im, kice, ipr\n",
        "      integer, intent(in) :: im, kice, ipr\n"
        "      integer, optional, intent(in) :: iter\n")
    sub(ice, "        flag(i) = islmsk(i) == 2 .and. flag_iter(i)                     &\n"
             "     &                           .and. use_lake_model(i) /=1\n",
        "        flag(i) = islmsk(i) == 2 .and. flag_iter(i)                     &\n"
        "     &                           .and. use_lake_model(i) /=1\n"
        "!       ice is stepped once: an icy cell with open water is re-flagged for NSST's second pass\n"
        "        if (present(iter)) flag(i) = flag(i) .and. iter == 1\n")
    s = edits.get(icem) or icem.read_text()
    if s.count("standard_name = ccpp_loop_counter") != 0:
        sys.exit("ABORT sfc_sice.meta: iter already present")
    edits[icem] = s.rstrip("\n") + "\n[iter]\n  standard_name = ccpp_loop_counter\n" \
        "  long_name = loop counter for subcycling loops in CCPP\n  units = index\n  dimensions = ()\n" \
        "  type = integer\n  intent = in\n  optional = True\n"


def si2():
    sub(ice, "                hice(i) = hice(i) - h2*ci*(stsice(i,2) - tfi)/ (li*delt)\n",
        "                hice(i) = hice(i) - h2*ci*(stsice(i,2) - tfi)/ li\n")


def si3():
    sub(nst, "       qsurf, gflux, cmm, chh, evap, hflx, ep, errmsg, errflg     &  ! --- outputs:\n       )\n",
        "       qsurf, gflux, cmm, chh, evap, hflx, ep, errmsg, errflg,    &  ! --- outputs:\n"
        "       icy, cice, sfcdsw)\n")
    sub(nst, "    character(len=*), intent(out) :: errmsg\n",
        "    character(len=*), intent(out) :: errmsg\n"
        "    logical, dimension(:), intent(in), optional :: icy\n"
        "    real (kind=kind_phys), dimension(:), intent(in), optional :: cice, sfcdsw\n")
    sub(nst, "    real(kind=kind_phys) :: ulwflx(im), nswsfc(im)\n",
        "    real(kind=kind_phys) :: ulwflx(im), nswsfc(im), ffw\n")
    sub(nst, "          nswsfc(i) = sfcnsw(i) ! net solar radiation at the air-sea surface (positive downward)\n",
        "          nswsfc(i) = sfcnsw(i) ! net solar radiation at the air-sea surface (positive downward)\n"
        "          ! open water in an icy cell takes the share sfc_sice assumes (snetw): ice + water = cell net SW\n"
        "          if (present(icy)) then\n"
        "             if (icy(i) .and. cice(i) < one) then\n"
        "                ffw = one - cice(i)\n"
        "                nswsfc(i) = min(3.0_kp*sfcnsw(i)/(one+2.0_kp*ffw), sfcdsw(i)*(one-0.06_kp))\n"
        "             endif\n"
        "          endif\n")
    s = edits.get(nstm) or nstm.read_text()
    edits[nstm] = s.rstrip("\n") + "\n" + "".join(
        f"[{n}]\n  standard_name = {sn}\n  long_name = {ln}\n  units = {u}\n"
        f"  dimensions = (horizontal_loop_extent)\n  type = {t}\n{k}  intent = in\n  optional = True\n"
        for n, sn, ln, u, t, k in [
            ("icy", "flag_nonzero_sea_ice_surface_fraction", "flag indicating presence of some sea ice surface area fraction",
             "flag", "logical", ""),
            ("cice", "sea_ice_area_fraction_of_sea_area_fraction", "ice fraction over open water", "frac", "real",
             "  kind = kind_phys\n"),
            ("sfcdsw", "surface_downwelling_shortwave_flux", "total sky sfc downward sw flux", "W m-2", "real",
             "  kind = kind_phys\n")])


def np1():
    sub(lsm, "                  hm(j+1) = hm(j+1) + heatr    ! barlage\n"
             "                  xm(j+1) = hm(j+1)*dt/hfus    ! barlage\n",
        "                  if (imelt(j+1) > 0) then\n"
        "                    hm(j+1) = hm(j+1) + heatr    ! barlage\n"
        "                    xm(j+1) = hm(j+1)*dt/hfus    ! barlage\n"
        "                  else\n"
        "                    stc(j+1) = stc(j+1) + fact(j+1)*heatr  ! layer below not melting: warm it\n"
        "                  endif\n")


fixes = {"SI1": si1, "SI2": si2, "SI3": si3, "NP1": np1}
for f in sys.argv[2:]:
    fixes[f]()
for path, s in edits.items():
    path.write_text(s)
    print(f"fixed {path.relative_to(root)}")
