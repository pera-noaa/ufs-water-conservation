#!/usr/bin/env python3
"""Fix H on glaciers (folded into diff 11): thin snow without layers that the glacier module zeroes is booked as runoff
instead of being deleted: as glacier flow (runsub, like snoflow) at the end of noahmp_glacier, and as surface runoff
(ponding2) in snowh2o_glacier, which cannot reach runsub. With iopt_gla = 2 (UFS) the glacier ice exchanges no water. Usage: python3 apply_noahmp_h_glacier_patch.py <module_sf_noahmp_glacier.F90> (v1 or ufs/dev)
Every anchor must match exactly once, else nothing is written."""
import re
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()


def sub(pat, rep):
    global s
    n = len(re.findall(pat, s))
    if n != 1:
        sys.exit(f"ABORT {f.name}: expected 1 match, found {n}: {pat[:70]!r}")
    s = re.sub(pat, rep, s)


# end of noahmp_glacier, after error_glacier: book it as glacier flow (runsub), the module's route for snow that
# joins the glacier (snoflow)
sub(r"\n( *)if\(snowh <= 1\.e-6 \.or\. sneqv <= 1\.e-3\) then\n",
    lambda m: f"\n{m.group(1)}if(snowh <= 1.e-6 .or. sneqv <= 1.e-3) then\n"
              f"{m.group(1)} ! the truncated snow joins the glacier, booked as glacier flow like snoflow\n"
              f"{m.group(1)} ! FIXME: this is ice, but runsub/drain is read as liquid; it belongs in a frozen-runoff flux the interface lacks\n"
              f"{m.group(1)} if(isnow == 0) runsub = runsub + sneqv/dt\n")
# snowh2o_glacier: ponding2 (mm) becomes surface runoff in water_glacier
sub(r"\n( *)if\(snowh <= 1\.e-8 \.or\. sneqv <= 1\.e-6\) then\n",
    lambda m: f"\n{m.group(1)}if(snowh <= 1.e-8 .or. sneqv <= 1.e-6) then\n"
              f"{m.group(1)}  ! the truncated snow leaves as surface runoff\n"
              f"{m.group(1)}  if(isnow == 0) ponding2 = ponding2 + sneqv\n")
f.with_suffix(f.suffix + ".preHGLA").write_text(f.read_text())
f.write_text(s)
print(f"patched {f} (H on glaciers)")
