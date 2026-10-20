#!/usr/bin/env python3
"""Fix F: with frac_grid, keep the persistent land snow (Sfcprop%weasdl) instead of overwriting it every step with the
cell-mean composite weasd (v1 snapshot and ufs/dev layouts; RUC was already exempt).
Usage: python3 apply_composites_f_patch.py <dir containing physics/Interstitials/UFS_SCM_NEPTUNE>
GFS_surface_composites_post sets weasd = txl*weasd_lnd + txi*weasd_ice; composites_pre then set weasd_lnd = weasd, so
coastal land snow was diluted by the land(+ice) fraction every step. Noah-MP restores layered snow from its layers
(that is its errwat); thin snow without layers was lost. weasdl is initialised at cold start (fv3atm_sfc_io)."""
import sys
from pathlib import Path

p = Path(sys.argv[1]) / "physics/Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_pre.F90"
s = p.read_text()
old = "           if(lsm /= lsm_ruc) weasd_lnd(i) = weasd(i)\n"
new = ("           ! with frac_grid, weasd is the cell mean and weasd_lnd the persistent land value (Sfcprop%weasdl)\n"
       "           if(lsm /= lsm_ruc .and. .not. frac_grid) weasd_lnd(i) = weasd(i)\n")
if s.count(old) != 1:
    sys.exit(f"ABORT: expected 1 match, found {s.count(old)}")
p.write_text(s.replace(old, new))
print(f"patched {p.name} (F)")
