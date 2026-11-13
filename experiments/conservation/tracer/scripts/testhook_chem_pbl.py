#!/usr/bin/env python3
"""Test-only hook: field_table 'chemistry' tracers get the cplchm treatment without a chemistry component,
i.e. convective transport via SAMF's chemical-tracer path (itc>0, fscav from fscav_aero) and PBL diffusion
(trans_aero), so a passive tracer is mixed as a real UFS-Chem GHG would be. No effect without chemistry tracers.
Usage: testhook_chem_pbl.py <ufs-weather-model tree>"""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "UFSATM/ccpp/data/CCPP_typedefs.F90"
s = f.read_text()
reps = [("    Interstitial%trans_aero = Model%cplchm .and. Model%trans_trac\n",
         "    Interstitial%trans_aero = (Model%cplchm .or. Model%ntchm > 0) .and. Model%trans_trac  ! TEST HOOK\n"),
        ("      if (Model%satmedmf) Interstitial%nvdiff = Interstitial%nvdiff + 1\n    elseif ( Model%imp_physics == Model%imp_physics_nssl ) then\n",
         "      if (Interstitial%trans_aero .and. .not. Model%cplchm) Interstitial%nvdiff = Interstitial%nvdiff + Model%ntchm  ! TEST HOOK\n"
         "      if (Model%satmedmf) Interstitial%nvdiff = Interstitial%nvdiff + 1\n    elseif ( Model%imp_physics == Model%imp_physics_nssl ) then\n")]
for old, new in reps:
    if s.count(old) != 1:
        sys.exit(f"ABORT: {s.count(old)} matches for {old.strip()[:70]!r}")
    s = s.replace(old, new)
f.write_text(s)
print("hooked", f)
