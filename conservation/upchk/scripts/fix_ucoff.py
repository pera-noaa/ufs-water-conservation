#!/usr/bin/env python3
"""fix_ucoff.py <ufs-weather-model> : (after add_pblw.py) index the MLM/PBL buffer ucb by global column offset
(ucmoff, reset at uc_t01's first block of a step, advanced in uc_exit), as em_probe does; the block-local index
kept only one block per PE because each scheme runs over all blocks before uc_fin."""
import sys
from pathlib import Path
d = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE"
reps = {"upchk_meter_common.F90": [
    ("  integer, save :: ucsk(ucnc) = 0\n", "  integer, save :: ucsk(ucnc) = 0, ucmoff = 0\n"),
    ("       uckdt(p) = kdt\n       ucoff(p) = 0\n", "       uckdt(p) = kdt\n       ucoff(p) = 0\n       if (p == 1) ucmoff = 0\n"),
    ("       ucb(:, i) = x\n", "       ucb(:, ucmoff+i) = x\n"),
    ("       ucb(17, i) = w - rho_a(i)*evap(i)\n       ucb(18, i) = g\n       ucb(19, i) = r\n       ucb(20, i) = rho_a(i)*evap(i)\n    enddo\n",
     "       ucb(17, ucmoff+i) = w - rho_a(i)*evap(i)\n       ucb(18, ucmoff+i) = g\n       ucb(19, ucmoff+i) = r\n"
     "       ucb(20, ucmoff+i) = rho_a(i)*evap(i)\n    enddo\n    ucmoff = ucmoff + im\n")],
    "uc_fin.F90": [("       ucm = ucm + a*ucb(:, i)\n       ucb(:, i) = 0.d0\n",
                    "       ucm = ucm + a*ucb(:, j0+i)\n       ucb(:, j0+i) = 0.d0\n")]}
for f, rr in reps.items():
    p = d / f
    t = p.read_text()
    for a, b in rr:
        assert t.count(a) == 1, (f, a)
        t = t.replace(a, b)
    p.write_text(t)
print("ucb indexed by column offset")
