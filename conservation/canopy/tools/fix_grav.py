#!/usr/bin/env python3
"""fix_grav.py <files...> : rename the E1 gravity argument grav -> con_g (sfc_nst already has a local grav)."""
import sys
from pathlib import Path
for f in sys.argv[1:]:
    p = Path(f); s = p.read_text(); n0 = s
    for a, b in (("nst_spray_opt, prsi, grav,", "nst_spray_opt, prsi, con_g,"),
                 ("intent(in) :: grav\n", "intent(in) :: con_g\n"), ("intent(in) :: grav, timestep\n", "intent(in) :: con_g, timestep\n"),
                 ("timestep * grav /", "timestep * con_g /"), ("[grav]\n", "[con_g]\n")):
        s = s.replace(a, b)
    p.write_text(s); print(f, "changed" if s != n0 else "unchanged")
