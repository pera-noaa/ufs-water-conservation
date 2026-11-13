#!/usr/bin/env python3
"""Meter noahmpdrv's glacier snow floor (weasd < 0.1 mm reset to 0.1 mm on land ice every call; diagnostic builds only;
apply after instrument_wb_glacier_z.py). Usage: python3 instrument_wb_glacier_floor.py <ufs_model.fd>
WBGF | 1 events, 2 water created (mm, unweighted over columns), 3 events after the first time step, 4 water created
  after it; printed at finalize after WBZ."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
mpt = root / "MP/Thompson/mp_thompson.F90"
g, d, m = gla.read_text(), drv.read_text(), mpt.read_text()


def one(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


g = one(g, "wbz(4) = 0.d0\n", "wbz(4) = 0.d0, wbgf(4) = 0.d0\n")
d = one(d, "      if(vegtype(i) == isice_table ) then\n        if(weasd(i) < 0.1) then\n",
        "      if(vegtype(i) == isice_table ) then\n        if(weasd(i) < 0.1) then\n"
        "          wbgf(1) = wbgf(1) + 1.d0; wbgf(2) = wbgf(2) + (0.1d0 - weasd(i))\n"
        "          if (itime > 1) then; wbgf(3) = wbgf(3) + 1.d0; wbgf(4) = wbgf(4) + (0.1d0 - weasd(i)); endif\n")
d = one(d, "\n      use module_sf_noahmplsm\n", "\n      use module_sf_noahmplsm\n      use noahmp_glacier_routines, only: wbgf\n")
m = one(m, "         write(*,'(a,4es24.15)') 'WBZ ', wbz\n",
        "         write(*,'(a,4es24.15)') 'WBZ ', wbz\n         write(*,'(a,4es24.15)') 'WBGF', wbgf\n")
m = one(m, "         use noahmp_glacier_routines, only: wbz\n", "         use noahmp_glacier_routines, only: wbz, wbgf\n")
for p, t in ((gla, g), (drv, d), (mpt, m)):
    p.with_suffix(p.suffix + ".preWBGF").write_text(p.read_text())
    p.write_text(t)
    print(f"instrumented {p.relative_to(root)}")
