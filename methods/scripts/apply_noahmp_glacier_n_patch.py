#!/usr/bin/env python3
"""Fix N (diff 18): glacier snow changes that Noah-MP and its driver make by assignment are booked as runoff, so the
glacier creates and deletes no water and refreezes no meltwater for free (iopt_gla = 2, ice an untracked reservoir):
  - snowwater_glacier's per-call reset to 600 mm of ice (if present): liquid in the old pack leaves as surface runoff
    (ponding2), the ice above or below 600 mm as glacier flow (snoflow -> runsub);
  - noahmpdrv's floor of 0.1 mm SWE on land ice: the added snow is negative baseflow (drain) for that call;
  - the two thin-snow truncations (end of noahmp_glacier; snowh2o_glacier): as apply_noahmp_h_glacier_patch.py.
Usage: python3 apply_noahmp_glacier_n_patch.py <dir containing physics/SFC_Models/Land/Noahmp> (ufs/dev or v1)
Every anchor must match exactly once, else nothing is written."""
import re
import subprocess
import sys
from pathlib import Path

d = Path(sys.argv[1]) / "physics/SFC_Models/Land/Noahmp"
gla, drv = d / "module_sf_noahmp_glacier.F90", d / "noahmpdrv.F90"
g, v = gla.read_text(), drv.read_text()


def sub(s, pat, rep, name):
    n = len(re.findall(pat, s))
    if n != 1:
        sys.exit(f"ABORT {name}: expected 1 match, found {n}: {pat[:70]!r}")
    return re.sub(pat, lambda m: rep(m) if callable(rep) else rep, s)


reset = "!reset the glacier to 2m depth with 600mm SWE\n"
if g.count(reset) == 1:
    g = g.replace(reset, """!the reset below keeps 600 mm of ice: the liquid it removes leaves as surface runoff and
!the ice it adds or removes is booked as glacier flow, so it creates no water
   if(isnow < 0) then
     ponding2 = ponding2 + sum(snliq(isnow+1:0))
     ! FIXME: this is ice, but runsub/drain is read as liquid; it belongs in a frozen-runoff flux the interface lacks
     snoflow  = snoflow + (sum(snice(isnow+1:0)) - 600.0)/dt
   else
     ! FIXME: this is ice, but runsub/drain is read as liquid; it belongs in a frozen-runoff flux the interface lacks
     snoflow  = snoflow + (sneqv - 600.0)/dt
     ponding2 = ponding2 + qrain*dt  ! rain the caller would add only while isnow == 0
   end if

""" + reset)
elif g.count(reset) > 1:
    sys.exit("ABORT glacier: reset comment found more than once")
v = sub(v, r"\n( *)if\(weasd\(i\) < 0\.1\) then\n( *)weasd\(i\)  = 0\.1\n",
        lambda m: f"\n{m.group(1)}if(weasd(i) < 0.1) then\n"
                  f"{m.group(2)}glacier_snow_floor = 0.1 - weasd(i)  ! booked as negative baseflow below\n"
                  f"{m.group(2)}weasd(i)  = 0.1\n", "noahmpdrv floor")
v = sub(v, r"\n( *)if\(vegtype\(i\) == isice_table \) then\n( *)if\(weasd\(i\) < 0\.1\) then\n",
        lambda m: f"\n{m.group(1)}glacier_snow_floor = 0.0\n" + m.group(0)[1:], "noahmpdrv floor init")
v = sub(v, r"\n( *)drain     \(i\)   = runoff_baseflow\n",
        lambda m: f"\n{m.group(1)}! FIXME: over land ice drain carries glacier ice and goes negative; it belongs in a frozen-runoff flux the interface lacks\n"
                  f"{m.group(1)}drain     (i)   = runoff_baseflow - glacier_snow_floor/timestep\n", "noahmpdrv drain")
v = sub(v, r"\n( *)real \(kind=kind_phys\)( +):: runoff_baseflow( +)!   out \| baseflow runoff \[mm/s\]\n",
        lambda m: m.group(0) + f"{m.group(1)}real (kind=kind_phys){m.group(2)}:: glacier_snow_floor    !       | snow added by the glacier floor [mm]\n",
        "noahmpdrv decl")
gla.write_text(g)
drv.write_text(v)
r = subprocess.run([sys.executable, str(Path(__file__).with_name("apply_noahmp_h_glacier_patch.py")), str(gla)])
if r.returncode:
    sys.exit("ABORT: thin-snow sites")
for p in d.glob("*.preHGLA"):
    p.unlink()
print(f"patched {gla.name}, {drv.name} (fix N{', reset booked' if reset in g else ', no reset'})")
