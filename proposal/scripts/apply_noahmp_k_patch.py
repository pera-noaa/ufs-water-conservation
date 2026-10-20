#!/usr/bin/env python3
"""Fix K: Noah-MP takes its latent heats from the host (con_hvap, con_hfus; hsub = con_hvap + con_hfus) instead of its
own constants (hvap 2.5104e6, hfus 0.3336e6, hsub 2.844e6), so the energy the land pays for the water it evaporates or
sublimates equals the latent energy that water carries in the atmosphere (the energy side of fix D; cf.
NCAR/ccpp-physics#582). v1 snapshot and ufs/dev layouts. Usage: python3 apply_noahmp_k_patch.py <dir containing physics/>
The three constants become module variables with the old values as defaults; noahmpdrv_init sets them from two new
arguments with the run phase's standard names, in both the soil and the glacier modules."""
import sys
from pathlib import Path

d = Path(sys.argv[1]) / "physics/SFC_Models/Land/Noahmp"
lsm, gla = d / "module_sf_noahmplsm.F90", d / "module_sf_noahmp_glacier.F90"
drv, meta = d / "noahmpdrv.F90", d / "noahmpdrv.meta"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    if s.count(old) != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


for f in (lsm, gla):
    for name, val, doc in (("hsub", "2.8440e06", "latent heat of sublimation (j/kg)"),
                           ("hvap", "2.5104e06", "latent heat of vaporization (j/kg)"),
                           ("hfus", "0.3336e06", "latent heat of fusion (j/kg)")):
        sub(f, f"  real (kind=kind_phys), parameter :: {name:<6} = {val} !< {doc}\n",
            f"  real (kind=kind_phys)            :: {name:<6} = {val} !< {doc}; host value set in noahmpdrv_init\n")
sub(drv, "                                do_mynnsfclay,do_mynnedmf,          &\n",
    "                                do_mynnsfclay,do_mynnedmf,          &\n"
    "                                con_hvap, con_hfus,                 &\n")
sub(drv, "        use namelist_soilveg\n        use noahmp_tables\n",
    "        use namelist_soilveg\n        use noahmp_tables\n"
    "        use module_sf_noahmplsm,    only: hvap, hsub, hfus\n"
    "        use noahmp_glacier_globals, only: hvap_gla => hvap, hsub_gla => hsub, hfus_gla => hfus\n")
s = edits.get(drv) or drv.read_text()
a = s.index("      subroutine noahmpdrv_init(")
b = s.index("      end subroutine noahmpdrv_init", a)
init = s[a:b]
for old, new in (("        logical,              intent(in) :: do_mynnedmf\n",
                  "        logical,              intent(in) :: do_mynnedmf\n"
                  "        real (kind=kind_phys), intent(in) :: con_hvap, con_hfus\n"),
                 ("        pores (:) = maxsmc (:)\n        resid (:) = drysmc (:)\n",
                  "        pores (:) = maxsmc (:)\n        resid (:) = drysmc (:)\n\n"
                  "        ! the host's latent heats, so the land pays the latent energy its water carries in the atmosphere\n"
                  "        hvap = con_hvap\n        hfus = con_hfus\n        hsub = con_hvap + con_hfus\n"
                  "        hvap_gla = hvap\n        hfus_gla = hfus\n        hsub_gla = hsub\n")):
    if init.count(old) != 1:
        sys.exit(f"ABORT noahmpdrv_init: {old.strip()[:50]!r} found {init.count(old)}")
    init = init.replace(old, new)
edits[drv] = s[:a] + init + s[b:]
mt = meta.read_text()
a = mt.index("  name = noahmpdrv_init\n")
b = mt.index("[ccpp-arg-table]", a)
sec = mt[a:b]
ent = ("[do_mynnedmf]\n  standard_name = flag_for_mellor_yamada_nakanishi_niino_pbl_scheme\n  long_name = flag to activate MYNN-EDMF\n"
       "  units = flag\n  dimensions = ()\n  type = logical\n  intent = in\n")
if sec.count(ent) != 1:
    sys.exit("ABORT noahmpdrv.meta: init do_mynnedmf entry")
sec = sec.replace(ent, ent +
    "[con_hvap]\n  standard_name = latent_heat_of_vaporization_of_water_at_0C\n  long_name = latent heat of evaporation/sublimation\n"
    "  units = J kg-1\n  dimensions = ()\n  type = real\n  kind = kind_phys\n  intent = in\n"
    "[con_hfus]\n  standard_name = latent_heat_of_fusion_of_water_at_0C\n  long_name = latent heat of fusion\n"
    "  units = J kg-1\n  dimensions = ()\n  type = real\n  kind = kind_phys\n  intent = in\n")
edits[meta] = mt[:a] + sec + mt[b:]
for p, t in edits.items():
    p.write_text(t)
print("patched module_sf_noahmplsm.F90, module_sf_noahmp_glacier.F90, noahmpdrv.F90, noahmpdrv.meta (K)")
