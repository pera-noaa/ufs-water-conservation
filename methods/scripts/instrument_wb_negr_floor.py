#!/usr/bin/env python3
"""Rain exit negatives split by whether the layer entered rain sedimentation at the R1 floor (WBT 86..88); apply after instrument_wb_neg_stages.py.
Usage: python3 instrument_wb_negr_floor.py <ufs-weather-model>. Reads state only (no answer change).
  86 qr exit negatives (kg/m2, entry-density frame) in layers with rr <= R1 before rain sedimentation
  87 count of those layers | 88 count of those whose deficit -qr*rho is <= R1 (bounded by the floor)
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
m = root / "MP/Thompson/module_mp_thompson.F90"
d = root / "MP/Thompson/mp_thompson.F90"
post = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90"
edits = {}
NW0, NW = 85, 88


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


sub(m, f"   real(kind=8), public, save :: wbt({NW0}) = 0.0d0\n", f"   real(kind=8), public, save :: wbt({NW}) = 0.0d0\n")
sub(m, "      integer :: wb_nc\n", "      integer :: wb_nc\n      logical :: wb_fl(kts:kte)\n")
sub(m, "      if (ANY(L_qr .eqv. .true.)) then\n         nstep = nint(1./onstep(1))\n",
    "      wb_fl(:) = rr(:) .le. R1\n"
    "      if (ANY(L_qr .eqv. .true.)) then\n         nstep = nint(1./onstep(1))\n")
sub(m, "            wbt(50) = wbt(50) - wb_x*wb_rho(k)*dzq(k)\n",
    "            wbt(50) = wbt(50) - wb_x*wb_rho(k)*dzq(k)\n"
    "            if (wb_fl(k)) then\n"
    "               wbt(86) = wbt(86) - wb_x*wb_rho(k)*dzq(k)\n"
    "               wbt(87) = wbt(87) + 1.0D0\n"
    "               if (-wb_x*rho(k) .le. R1) wbt(88) = wbt(88) + 1.0D0\n"
    "            endif\n")
sub(post, f"'(a,i7,{NW0}es17.9)'", f"'(a,i7,{NW}es17.9)'")
sub(d, f"'(a,i7,{NW0}es17.9)'", f"'(a,i7,{NW}es17.9)'")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preNEGRF").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
