#!/usr/bin/env python3
"""M5 completion (folded into diff 16): a column whose entry exchange left vapour below the floor skips Thompson's
no-microphysics early return, so the end-of-step refill (diff 07) handles it instead of mp_gt_driver's
neighbour-average fixer. Usage: python3 apply_thompson_m5_noreturn_patch.py <module_mp_thompson.F90> (ufs/dev or v1)"""
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()
old = "      if (no_micro) return\n"
if s.count(old) != 1:
    sys.exit(f"ABORT {f.name}: expected 1 match, found {s.count(old)}")
s = s.replace(old, "!..Entry exchanges can leave vapour below the floor; such a column goes through the end-of-step refill.\n"
                   "      do k = kts, kte\n"
                   "         if (qv1d(k) .lt. 1.E-10) no_micro = .false.\n"
                   "      enddo\n" + old)
f.write_text(s)
print(f"patched {f} (M5: no early return below the vapour floor)")
