#!/usr/bin/env python3
"""Meter fix H's three thin-snow truncations (diagnostic builds only; apply after instrument_wb_noahmpx.py and
apply_noahmp_h_patch.py). Usage: python3 instrument_wb_noahmph.py <ufs_model.fd>
WBK | count and sum (mm, unweighted over columns) of the snow moved to the soil, isnow == 0 and sneqv /= 0, at
  energy (1,4), snowh2o (2,5), end of noahmp_sflx (3,6), printed at finalize after WBE."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
mpt = root / "MP/Thompson/mp_thompson.F90"
s, m = lsm.read_text(), mpt.read_text()


def one(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


s = one(s, "  real(kind=8), public, save :: wbe(16) = 0.d0\n",
        "  real(kind=8), public, save :: wbe(16) = 0.d0, wbk(6) = 0.d0\n")
for k, (ind, store) in enumerate(((7, "smc"), (5, "sice"), (5, "smc")), start=1):
    fix = f"\n{' ' * ind}if(isnow == 0) {store}(1) = {store}(1) + sneqv/(dzsnso(1)*1000.)\n"
    s = one(s, fix, f"\n{' ' * ind}if(isnow == 0 .and. sneqv /= 0.) then\n"
                    f"{' ' * ind}  wbk({k}) = wbk({k}) + 1.d0; wbk({k + 3}) = wbk({k + 3}) + sneqv\n"
                    f"{' ' * ind}endif" + fix)
m = one(m, "         use module_sf_noahmplsm, only: wbe\n", "         use module_sf_noahmplsm, only: wbe, wbk\n")
m = one(m, "         write(*,'(a,16es24.15)') 'WBE ', wbe\n",
        "         write(*,'(a,16es24.15)') 'WBE ', wbe\n         write(*,'(a,6es24.15)') 'WBK ', wbk\n")
for p, t in ((lsm, s), (mpt, m)):
    p.with_suffix(p.suffix + ".preWBK").write_text(p.read_text())
    p.write_text(t)
    print(f"instrumented {p.relative_to(root)}")
