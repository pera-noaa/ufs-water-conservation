#!/usr/bin/env python3
"""Fix H: Noah-MP's thin-snow truncation (snowh <= 1e-6 m or sneqv <= 1e-3 mm -> no snow) moves the truncated snow into
the top soil layer as ice instead of deleting it (v1 snapshot and ufs/dev layouts).
Usage: python3 apply_noahmp_h_patch.py <dir containing physics/SFC_Models>
Ice dripping off the canopy (precip_heat) reaches the ground as ~1e-4 mm of snowfall per step, and snowh2o deleted it:
-15.6 mm per 1.77M column-steps in our C96 case. The same truncation in energy (before water) and at the end of
noahmp_sflx (after the error check) is fixed the same way; with layers (isnow < 0) the mass stays in the layers."""
import sys
from pathlib import Path

f90 = Path(sys.argv[1]) / "physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = f90.read_text()


def one(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


def trunc(ind, store, body=2):
    i, j = " " * ind, " " * (ind + body)
    old = f"\n{i}if(snowh <= 1.e-6 .or. sneqv <= 1.e-3) then\n{j}snowh = 0.0\n{j}sneqv = 0.0\n{i}end if\n"
    new = (f"\n{i}if(snowh <= 1.e-6 .or. sneqv <= 1.e-3) then\n"
           f"{j}! the truncated snow goes to the top soil layer as ice\n"
           f"{j}if(isnow == 0) {store}(1) = {store}(1) + sneqv/(dzsnso(1)*1000.)\n"
           f"{j}snowh = 0.0\n{j}sneqv = 0.0\n{i}end if\n")
    return old, new


# energy: before ground snow cover; phasechange then takes smc - sh2o as soil ice
s = one(s, "     fsno = 0." + trunc(5, "smc")[0], "     fsno = 0." + trunc(5, "smc")[1])
# snowh2o: soil ice is carried as sice here (smc = sh2o + sice after soilwater)
s = one(s, "   end if\n" + trunc(3, "sice")[0] + "\n! for deep snow\n", "   end if\n" + trunc(3, "sice")[1] + "\n! for deep snow\n")
# noahmp_sflx after error(): smc is the output; the next call rebuilds sice = smc - sh2o
s = one(s, "    end if\n" + trunc(4, "smc", 1)[0] + "\n    if(swdown.ne.0.) then\n",
        "    end if\n" + trunc(4, "smc", 1)[1] + "\n    if(swdown.ne.0.) then\n")
f90.write_text(s)
print(f"patched {f90.name} (H: 3 truncations)")
