#!/usr/bin/env python3
"""M5's no-early-return fix (as apply_thompson_m5_noreturn_patch.py) for any Thompson copy that carries M5's entry
exchange and diff 07's vapour-floor refill (CCPP ufs/dev and production, WRF, MPAS): a column whose entry exchange left
vapour below the floor skips the no-microphysics early return, so the end-of-step refill handles it instead of
mp_gt_driver's neighbour-average fixer. Keeps the copy's indentation; aborts unless every anchor matches once, and
refuses a second run. Usage: python3 port_thompson_m5_noreturn_any.py <module_mp_thompson.F90|.F>"""
import re
import sys
from pathlib import Path

mp = Path(sys.argv[1])
s = mp.read_text()


def once(pat, s, what, flags=0):
    m = list(re.finditer(pat, s, flags))
    if len(m) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {len(m)}")
    return m[0]


if "Entry exchanges can leave vapour below the floor" in s:
    sys.exit("ABORT: already has the no-early-return fix")
# prerequisites: M5's entry exchange (cloud water to vapour) and 07's refill, which this routes the column into
once(r"^ *qv1d\(k\) = qv1d\(k\) \+ qc1d\(k\) *$", s, "M5 entry exchange (cloud water)", re.M)
once(r"\n!\.\.Vapour left below the floor is refilled, not created", s, "07 vapour-floor refill")
r = once(r"^( *)if \(no_micro\) return *$", s, "early return", re.I | re.M)
i = r.group(1)
m = r.start()
s = (s[:m] + "!..Entry exchanges can leave vapour below the floor; such a column goes through the end-of-step refill.\n"
     f"{i}do k = kts, kte\n{i}   if (qv1d(k) .lt. 1.E-10) no_micro = .false.\n{i}enddo\n" + s[m:])
mp.write_text(s)
print(f"patched {mp} (M5: no early return below the vapour floor)")
