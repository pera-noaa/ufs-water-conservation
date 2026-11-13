#!/usr/bin/env python3
"""Fix D on the 2024 snapshot: the atmosphere gets Noah-MP's own water flux (ecan + etran + edir), not LH/con_hvap.
Usage: python3 apply_noahmp_d_patch.py <ufs_model.fd>
The snapshot's glacier branch leaves canopy evaporation and transpiration 'undefined' (9.99e20); upstream ufs/dev sets
them to 0.0, which this also does, so the sum is valid on glacier points. Every replacement must match exactly once."""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "FV3/ccpp/physics/physics/SFC_Models/Land/Noahmp/noahmpdrv.F90"
s = f.read_text()
PLAN = [
    ("        evaporation_canopy     = undefined\n        transpiration          = undefined\n",
     "        evaporation_canopy     = 0.0\n        transpiration          = 0.0\n"),
    ("      evap(i) = evap(i) / density / con_hvap\n",
     "      ! the water Noah-MP removed (its own hvap/hsub), not latent heat / con_hvap\n"
     "      evap(i) = (ecan(i) + etran(i) + edir(i)) / density\n"),
]
orig = s
for old, new in PLAN:
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT: expected 1 match, found {n}: {old.strip()[:60]!r}")
    s = s.replace(old, new)
f.with_suffix(f.suffix + ".preD").write_text(orig)
f.write_text(s)
print(f"patched {f}")
