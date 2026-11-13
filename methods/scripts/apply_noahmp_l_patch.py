#!/usr/bin/env python3
"""Fix L (diff 17): negative transpiration heat becomes dew/frost on the canopy.
Usage: python3 apply_noahmp_l_patch.py <dir containing physics/SFC_Models>
vege_flux can return fctr < 0 (vapour condensing in the stomatal pathway, 13 % of land column-steps at C96). canwater
takes etran = max(fctr/L, 0), so the latent heat warms the canopy but no water condenses: Noah-MP's water and energy
disagree by -0.024 W/m2 per land column. Here the matching water condenses on the canopy as dew (liquid) or frost
(frozen canopy) and leaves the atmosphere through ecan; the energy solution is unchanged. CTSM instead zeroes
transpiration under dew conditions inside its energy solve (CanopyFluxesMod)."""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = f.read_text()
for old, new in (("        qdewc = abs( min( fcev/hvap, 0. ) )\n",
                  "        ! condensation in the transpiration pathway (fctr < 0) is dew on the canopy\n"
                  "        qdewc = abs( min( fcev/hvap, 0. ) ) + abs( min( fctr/hvap, 0. ) )\n"),
                 ("        qfroc = abs( min( fcev/hsub, 0. ) )\n",
                  "        qfroc = abs( min( fcev/hsub, 0. ) ) + abs( min( fctr/hsub, 0. ) )\n")):
    if s.count(old) != 1:
        sys.exit(f"ABORT: {old.strip()!r} found {s.count(old)} times")
    s = s.replace(old, new)
f.write_text(s)
print(f"patched {f.name} (L)")
