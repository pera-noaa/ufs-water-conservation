#!/usr/bin/env python3
"""Reference fix N (diff 18, with its rain fix) for any Noah-MP glacier copy: book the snow the glacier code sets.
Branches with the 600 mm reset get the reset booking; branches without it get only the thin-snow truncations and the
driver's 0.1 mm floor. The glacier ice stays in runsub/drain, marked FIXME (it belongs in a frozen-runoff flux).
Aborts unless every anchor matches once.
Usage: python3 port_noahmp_glacier_N_any.py <module_sf_noahmp_glacier.F90|.f90> <noahmpdrv.F90>"""
import re
import sys
from pathlib import Path

gla, drv = Path(sys.argv[1]), Path(sys.argv[2])
s, d = gla.read_text(), drv.read_text()
FIX_ICE = "! FIXME: this is ice, but runsub/drain is read as liquid; it belongs in a frozen-runoff flux the interface lacks"
FIX_DRN = ("! FIXME: over land ice drain carries glacier ice and goes negative; it belongs in a frozen-runoff flux "
           "the interface lacks")


def once(pat, s, what):
    m = list(re.finditer(pat, s))
    if len(m) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {len(m)}")
    return m[0]


if "glacier_snow_floor" in d:
    sys.exit("ABORT: already patched")

# thin snow without layers, end of noahmp_glacier (after its water check): glacier flow
m = once(r"\n( *)if\(snowh <= 1\.e-6 \.or\. sneqv <= 1\.e-3\) then\n", s, "noahmp_glacier truncation")
i = m.group(1) + " "
s = s[:m.end()] + (f"{i}! the truncated snow joins the glacier, booked as glacier flow like snoflow\n{i}{FIX_ICE}\n"
                   f"{i}if(isnow == 0) runsub = runsub + sneqv/dt\n") + s[m.end():]

# thin snow without layers in snowh2o_glacier: surface runoff
m = once(r"\n( *)if\(snowh <= 1\.e-8 \.or\. sneqv <= 1\.e-6\) then\n", s, "snowh2o_glacier truncation")
i = m.group(1) + "  "
s = s[:m.end()] + f"{i}! the truncated snow leaves as surface runoff\n{i}if(isnow == 0) ponding2 = ponding2 + sneqv\n" + s[m.end():]

# the 600 mm reset, where present
reset = "!reset the glacier to 2m depth with 600mm SWE" in s
if reset:
    m = once(r"\n *qsnbot \) +!out\n(?=\n!reset the glacier to 2m depth with 600mm SWE\n)", s, "reset")
    s = s[:m.end()] + (
        "\n!the reset below keeps 600 mm of ice: the liquid it removes leaves as surface runoff and\n"
        "!the ice it adds or removes is booked as glacier flow, so it creates no water\n"
        "   if(isnow < 0) then\n"
        "     ponding2 = ponding2 + sum(snliq(isnow+1:0))\n"
        f"     {FIX_ICE}\n"
        "     snoflow  = snoflow + (sum(snice(isnow+1:0)) - 600.0)/dt\n"
        "   else\n"
        f"     {FIX_ICE}\n"
        "     snoflow  = snoflow + (sneqv - 600.0)/dt\n"
        "     ponding2 = ponding2 + qrain*dt  ! rain the caller would add only while isnow == 0\n"
        "   end if\n") + s[m.end():]

# driver: the 0.1 mm land-ice floor, booked as negative baseflow
m = once(r"\n( *real \(kind=kind_phys\) +):: runoff_baseflow( +)![^\n]*\n", d, "runoff_baseflow declaration")
d = d[:m.end()] + f"{m.group(1)}:: glacier_snow_floor{m.group(2)[3:] or ' '}!       | snow added by the glacier floor [mm]\n" + d[m.end():]
m = once(r"\n( *)if\(vegtype\(i\) == isice_table \) then\n( *)if\(weasd\(i\) < 0\.1\) then\n", d, "floor")
d = (d[:m.start()] + f"\n{m.group(1)}glacier_snow_floor = 0.0" + d[m.start():m.end()]
     + f"{m.group(2)}  glacier_snow_floor = 0.1 - weasd(i)  ! booked as negative baseflow below\n" + d[m.end():])
m = once(r"\n( *)drain +\(i\) += runoff_baseflow\n", d, "drain")
dt = "timestep" if re.search(r"\btimestep\b", d) else sys.exit("ABORT: no timestep in driver")
d = (d[:m.start()] + f"\n{m.group(1)}{FIX_DRN}\n{m.group(1)}drain     (i)   = runoff_baseflow - glacier_snow_floor/{dt}\n"
     + d[m.end():])

gla.write_text(s)
drv.write_text(d)
print(f"patched {gla} and {drv} ({'with' if reset else 'no'} reset)")
