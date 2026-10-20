#!/usr/bin/env python3
"""Thompson internal water-closure patches (on top of apply_water_patches.py 'both').
Usage: python3 apply_thompson_c_patches.py <ufs_model.fd> c1|c2|c12
c1: count cloud water settling out of the lowest layer as precipitation.
c2: re-close graupel gains (rain-collects-ice, cold rain-collects-snow) after the rate limiters.
Every replacement must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root, which = Path(sys.argv[1]), sys.argv[2]
f = root / "FV3/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90"

C1 = ("""         rc(k) = MAX(R1, rc(k) + (sed_c(k+1)-sed_c(k)) *odzq*DT)
         nc(k) = MAX(10., nc(k) + (sed_n(k+1)-sed_n(k)) *odzq*DT)
      enddo
""", """         rc(k) = MAX(R1, rc(k) + (sed_c(k+1)-sed_c(k)) *odzq*DT)
         nc(k) = MAX(10., nc(k) + (sed_n(k+1)-sed_n(k)) *odzq*DT)
      enddo
      ! cloud water settling out of the lowest layer reaches the surface: count it as precipitation
      if (ksed1(5) .ge. kts) pptrain = pptrain + sed_c(kts)*DT
""")
C2 = ("""         prr_rcg(k) = ratio * SIGN(1.0, SNGL(prr_rcg(k)))
         prg_rcg(k) = -prr_rcg(k)
""", """         prr_rcg(k) = ratio * SIGN(1.0, SNGL(prr_rcg(k)))
         prg_rcg(k) = -prr_rcg(k)
         ! graupel gains must match the (possibly limited) losses that feed them
         prg_rci(k) = pri_rci(k) + prr_rci(k)
         if (temp(k).lt.T_0) prg_rcs(k) = -(prr_rcs(k) + prs_rcs(k))
""")
plan = {"c1": [C1], "c2": [C2], "c12": [C1, C2]}[which]
s = f.read_text()
for old, new in plan:
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT: expected 1 match, found {n}: {old.strip()[:60]!r}")
    s = s.replace(old, new)
f.with_suffix(f.suffix + ".preC").write_text(f.read_text())
f.write_text(s)
print(f"patched {f.relative_to(root)} ({which})")
