#!/usr/bin/env python3
"""Meter the glacier thin-snow truncations H does not cover (diagnostic builds only; apply after instrument_wb_noahmph.py).
Usage: python3 instrument_wb_glacier_z.py <ufs_model.fd>
WBZ | count and sum (mm, unweighted over columns) of sneqv set to zero at the end of noahmp_glacier, after error_glacier
  (1,3), and in snowh2o_glacier (2,4), printed at finalize after WBK."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
mpt = root / "MP/Thompson/mp_thompson.F90"
g, m = gla.read_text(), mpt.read_text()


def one(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


g = one(g, "  real(kind=8), public, save :: wbl_errwat_g = 0.d0, wbl_prcp_g = 0.d0\n",
        "  real(kind=8), public, save :: wbl_errwat_g = 0.d0, wbl_prcp_g = 0.d0, wbz(4) = 0.d0\n")
for k, (ind, cond) in enumerate(((4, "snowh <= 1.e-6 .or. sneqv <= 1.e-3"), (3, "snowh <= 1.e-8 .or. sneqv <= 1.e-6")), start=1):
    old = f"{' ' * ind}if({cond}) then\n"
    g = one(g, old, old + f"{' ' * ind}  if(sneqv /= 0.) then; wbz({k}) = wbz({k}) + 1.d0; wbz({k + 2}) = wbz({k + 2}) + sneqv; endif\n")
m = one(m, "         use module_sf_noahmplsm, only: wbe, wbk\n",
        "         use module_sf_noahmplsm, only: wbe, wbk\n         use noahmp_glacier_routines, only: wbz\n")
m = one(m, "         write(*,'(a,6es24.15)') 'WBK ', wbk\n",
        "         write(*,'(a,6es24.15)') 'WBK ', wbk\n         write(*,'(a,4es24.15)') 'WBZ ', wbz\n")
for p, t in ((gla, g), (mpt, m)):
    p.with_suffix(p.suffix + ".preWBZ").write_text(p.read_text())
    p.write_text(t)
    print(f"instrumented {p.relative_to(root)}")
