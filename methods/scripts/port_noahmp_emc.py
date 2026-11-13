#!/usr/bin/env python3
"""Port fixes D, H and I to NOAA-EMC/noahmp (develop): the CCPP driver drivers/ccpp/noahmpdrv.F90 (used by the NUOPC
land component) and src/module_sf_noahmplsm.F90. Usage: python3 port_noahmp_emc.py <noahmp checkout>
  D  noahmpdrv hands the atmosphere the water Noah-MP removed, (ecan + etran + edir)/density, not latent heat /
     con_hvap; over glacier, canopy evaporation and transpiration become 0 instead of `undefined` (9.99e20), as
     ccpp-physics ufs/dev already has them (3fe1f187). The NUOPC driver's x(rho*con_hvap) for history and /(rho*con_hvap)
     before coupling cancel, so it needs no change.
  H, I  the same edits as ccpp-physics diffs 11 and 12 (apply_noahmp_h_patch.py, apply_noahmp_i_patch.py), whose
     anchors match this copy of module_sf_noahmplsm.F90 unchanged."""
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent
drv = root / "drivers/ccpp/noahmpdrv.F90"
s = drv.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


s = one(s, "      evap(i) = evap(i) / density / con_hvap\n",
        "      ! the water Noah-MP removed (its own hvap/hsub), not latent heat / con_hvap\n"
        "      evap(i) = (ecan(i) + etran(i) + edir(i)) / density\n", "D")
s = one(s, "        evaporation_canopy     = undefined\n        transpiration          = undefined\n",
        "        evaporation_canopy     = 0.0\n        transpiration          = 0.0\n", "D glacier")

# H and I through the tested ccpp-physics scripts: present src/ under the ccpp-physics path, write back
lsm = root / "src/module_sf_noahmplsm.F90"
with tempfile.TemporaryDirectory() as t:
    p = Path(t) / "physics/SFC_Models/Land/Noahmp"
    p.mkdir(parents=True)
    (p / "module_sf_noahmplsm.F90").write_text(lsm.read_text())
    for script in ("apply_noahmp_h_patch.py", "apply_noahmp_i_patch.py"):
        r = subprocess.run([sys.executable, str(here / script), t], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"ABORT {script}: {r.stdout}{r.stderr}")
        print(r.stdout.strip())
    new_lsm = (p / "module_sf_noahmplsm.F90").read_text()

drv.write_text(s)
lsm.write_text(new_lsm)
print("patched drivers/ccpp/noahmpdrv.F90 (D) and src/module_sf_noahmplsm.F90 (H, I)")
