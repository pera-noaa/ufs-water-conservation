#!/usr/bin/env python3
"""Add the passive tracers trpa (profile) and trpb (from the IC) to a staged run's field_table, before sgs_tke, so they
are tracers 10 and 11, and write both to the atmf history files. Usage: python3 edit_tr_tables.py <RUNDIR>
A symlinked table is replaced by an edited regular file (the link target is never written). Anchors must match once."""
import os
import sys

rd = sys.argv[1]
FT_OLD = "# prognostic subgrid scale turbulent kinetic energy\n"
FT_NEW = ('# passive tracer a: vertical profile only, 1e-3 at the surface to 1e-4 at the top (meter build)\n'
          ' "TRACER", "atmos_mod", "trpa"\n'
          '           "longname",     "passive tracer a"\n'
          '           "units",        "kg/kg"\n'
          '       "profile_type", "profile", "surface_value=1.e-3, top_value=1.e-4" /\n'
          '# passive tracer b: 3-D field read from INPUT/gfs_data (meter build)\n'
          ' "TRACER", "atmos_mod", "trpb"\n'
          '           "longname",     "passive tracer b"\n'
          '           "units",        "kg/kg"\n'
          '       "profile_type", "fixed", "surface_value=4.e-4" /\n' + FT_OLD)
DT_OLD = '"gfs_dyn",     "graupel",     "grle",      "fv3_history",    "all",  .false.,  "none",  2\n'
DT_NEW = (DT_OLD + '"gfs_dyn",     "trpa",        "trpa",      "fv3_history",    "all",  .false.,  "none",  2\n'
          '"gfs_dyn",     "trpb",        "trpb",      "fv3_history",    "all",  .false.,  "none",  2\n')

for name, old, new in (("field_table", FT_OLD, FT_NEW), ("diag_table", DT_OLD, DT_NEW)):
    p = f"{rd}/{name}"
    s = open(p).read()
    if s.count(old) != 1 or "trpa" in s:
        sys.exit(f"ABORT {p}: anchor count {s.count(old)}, or trpa already present")
    os.unlink(p)
    with open(p, "w") as f:
        f.write(s.replace(old, new))
    print(f"edited {p}")
