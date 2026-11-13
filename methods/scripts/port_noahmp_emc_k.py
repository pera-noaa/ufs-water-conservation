#!/usr/bin/env python3
"""Port fix K to NOAA-EMC/noahmp (develop): Noah-MP takes its latent heats from the host (con_hvap, con_hfus;
hsub = con_hvap + con_hfus) instead of its own constants. Usage: python3 port_noahmp_emc_k.py <noahmp checkout>
Runs the ccpp-physics script apply_noahmp_k_patch.py (whose anchors match this copy) on src/module_sf_noahmplsm.F90,
src/module_sf_noahmp_glacier.F90, drivers/ccpp/noahmpdrv.F90 and drivers/ccpp/noahmpdrv.meta, then adds the two new
arguments to the NUOPC land component's positional call of noahmpdrv_init (drivers/nuopc/lnd_comp_driver.F90, which
already imports con_hvap and con_hfus from physcons). The WRF driver (drivers/wrf) never calls noahmpdrv_init, so it
keeps the old values, which remain the defaults."""
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
here = Path(__file__).resolve().parent
files = {"module_sf_noahmplsm.F90": root / "src/module_sf_noahmplsm.F90",
         "module_sf_noahmp_glacier.F90": root / "src/module_sf_noahmp_glacier.F90",
         "noahmpdrv.F90": root / "drivers/ccpp/noahmpdrv.F90",
         "noahmpdrv.meta": root / "drivers/ccpp/noahmpdrv.meta"}
nuopc = root / "drivers/nuopc/lnd_comp_driver.F90"
s = nuopc.read_text()
old = ("      noahmp%static%do_mynnedmf, noahmp%static%errmsg, noahmp%static%errflg)\n")
if s.count(old) != 1 or "use physcons        , only: con_rd, con_hfus\n" not in s:
    sys.exit("ABORT nuopc: noahmpdrv_init call or physcons import not as expected")
s = s.replace(old, "      noahmp%static%do_mynnedmf, con_hvap, con_hfus, noahmp%static%errmsg, noahmp%static%errflg)\n")

with tempfile.TemporaryDirectory() as t:
    d = Path(t) / "physics/SFC_Models/Land/Noahmp"
    d.mkdir(parents=True)
    for name, src in files.items():
        (d / name).write_text(src.read_text())
    r = subprocess.run([sys.executable, str(here / "apply_noahmp_k_patch.py"), t], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ABORT apply_noahmp_k_patch.py: {r.stdout}{r.stderr}")
    out = {name: (d / name).read_text() for name in files}

for name, src in files.items():
    src.write_text(out[name])
nuopc.write_text(s)
print("patched src/module_sf_noahmplsm.F90, src/module_sf_noahmp_glacier.F90, drivers/ccpp/noahmpdrv.F90, "
      "drivers/ccpp/noahmpdrv.meta and drivers/nuopc/lnd_comp_driver.F90 (K)")
