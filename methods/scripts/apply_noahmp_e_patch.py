#!/usr/bin/env python3
"""Fix E: Noah-MP land is computed once per time step (v1 snapshot and ufs/dev layouts).
Usage: python3 apply_noahmp_e_patch.py <dir containing physics/SFC_Models/Land/Noahmp>
GFS_surface_loop_control_part2 excludes Noah-MP land from the second surface iteration, but with frac_grid a coastal
cell is also wet, and (wet .and. nstf_name1 > 0) re-flags it; noahmpdrv tests only flag_iter .and. dry, so the land of
low-wind coastal cells is stepped twice per time step, from its already-updated state, with no restore (Noah and RUC
save and restore their state for the second pass; Noah-MP has no such code). The fix passes the CCPP loop counter and
computes land only on the first pass. Every replacement must match exactly once, else nothing is written."""
import sys
from pathlib import Path

d = Path(sys.argv[1]) / "physics/SFC_Models/Land/Noahmp"
edits = {}


def sub(name, old, new):
    p = d / name
    s = edits.get(p) or p.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[p] = s.replace(old, new)


sub("noahmpdrv.F90", "      shdmin, shdmax, snoalb, sfalb, flag_iter,con_g,            &\n",
    "      shdmin, shdmax, snoalb, sfalb, flag_iter, iter, con_g,     &\n")
sub("noahmpdrv.F90", "  logical             , dimension(:)     , intent(in)    :: flag_iter  !\n",
    "  logical             , dimension(:)     , intent(in)    :: flag_iter  !\n"
    "  integer                                , intent(in)    :: iter       ! surface iteration (ccpp loop counter)\n")
sub("noahmpdrv.F90", "    if (flag_iter(i) .and. dry(i)) then\n",
    "    ! land is stepped once: a coastal (wet and dry) cell can be re-flagged for the second iteration\n"
    "    if (flag_iter(i) .and. dry(i) .and. iter == 1) then\n")
sub("noahmpdrv.meta",
    "[flag_iter]\n  standard_name = flag_for_iteration\n  long_name = flag for iteration\n  units = flag\n"
    "  dimensions = (horizontal_loop_extent)\n  type = logical\n  intent = in\n",
    "[flag_iter]\n  standard_name = flag_for_iteration\n  long_name = flag for iteration\n  units = flag\n"
    "  dimensions = (horizontal_loop_extent)\n  type = logical\n  intent = in\n"
    "[iter]\n  standard_name = ccpp_loop_counter\n  long_name = loop counter for subcycling loops in CCPP\n"
    "  units = index\n  dimensions = ()\n  type = integer\n  intent = in\n")

for p, s in edits.items():
    p.write_text(s)
    print(f"patched {p.name} (E)")
