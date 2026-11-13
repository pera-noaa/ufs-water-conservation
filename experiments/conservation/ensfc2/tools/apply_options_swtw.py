#!/usr/bin/env python3
"""Incremental (trees made before 18 Oct 01:00): SW1 also when Noah-MP's own fsa is 0 (twilight), as in apply_options.py."""
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp"
lsm, gla = root / "module_sf_noahmplsm.F90", root / "module_sf_noahmp_glacier.F90"
s = lsm.read_text()
a = ("     if (swt >= 0. .and. fsa > 0.) then\n        sav = sav*swt/fsa\n        sag = sag*swt/fsa\n"
     "        fsr = fsr + fsa - swt\n        fsa = swt\n     endif\n")
b = ("     if (swt >= 0.) then\n        if (fsa > 0.) then\n           sav = sav*swt/fsa\n           sag = sag*swt/fsa\n"
     "        else\n           sav = 0.\n           sag = swt\n        endif\n        fsr = fsr + fsa - swt\n        fsa = swt\n     endif\n")
assert s.count(a) == 1; lsm.write_text(s.replace(a, b))
s = gla.read_text()
a = "     if (swt >= 0. .and. fsa > 0.) then\n        sag = sag*swt/fsa\n        fsr = fsr + fsa - swt\n        fsa = swt\n     endif\n"
b = "     if (swt >= 0.) then\n        sag = swt\n        fsr = fsr + fsa - swt\n        fsa = swt\n     endif\n"
assert s.count(a) == 1; gla.write_text(s.replace(a, b))
print("swtw applied")
