#!/usr/bin/env python3
"""Fix I, first version (superseded by apply_noahmp_i_patch.py, which conserves energy): Noah-MP's canopy truncation in canwater (canliq or canice <= 1e-6 mm -> 0) evaporates or sublimates the
truncated water through ecan instead of deleting it (v1 snapshot and ufs/dev layouts).
Usage: python3 apply_noahmp_i_patch.py <dir containing physics/SFC_Models>
Interception of a few 1e-7 mm per step (light rain or canopy ice drip) fell under the threshold and was deleted: errwat
-0.014 mm per 1.77M column-steps in our C96 case. ecan feeds the land evaporation passed to the atmosphere, so the
mass leaves as vapour; the latent heat of <= 1e-6 mm per step (< 4e-6 W/m2) is not added to fcev."""
import sys
from pathlib import Path

f90 = Path(sys.argv[1]) / "physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = f90.read_text()


def one(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


s = one(s, "       if(canliq <= 1.e-06) canliq = 0.0\n",
        "       if(canliq <= 1.e-06) then\n"
        "         ! the truncated canopy water evaporates (counted in ecan)\n"
        "         qevac  = qevac + canliq/dt\n"
        "         canliq = 0.0\n"
        "       end if\n")
s = one(s, "      if(canice.le.1.e-6) canice = 0.\n",
        "      if(canice.le.1.e-6) then\n"
        "        ! the truncated canopy ice sublimates (counted in ecan)\n"
        "        qsubc  = qsubc + canice/dt\n"
        "        canice = 0.\n"
        "      end if\n")
f90.write_text(s)
print(f"patched {f90.name} (I: 2 canopy truncations)")
