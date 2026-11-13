#!/usr/bin/env python3
"""Add-on to instrument_wb_ups.py (apply after it, before any fix): WBT grows to 32 slots,
  31 rain left after the source/sink processes that the 'xrr <= R1' branch discards when it overwrites qrten with
     -qr1d/dt (kg/m2, >0 = loss) | 32 number of such overwrites.
Usage: python3 instrument_wb_ups_rten.py <ufs-weather-model>. Every anchor must match exactly once."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
m = root / "MP/Thompson/module_mp_thompson.F90"
d = root / "MP/Thompson/mp_thompson.F90"
post = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


sub(m, "   real(kind=8), public, save :: wbt(30) = 0.0d0\n", "   real(kind=8), public, save :: wbt(32) = 0.0d0\n")
sub(m, "         else\n            qrten(k) = -qr1d(k)*odts\n            nrten(k) = -nr1d(k)*odts\n",
    "         else\n"
    "            wbt(31) = wbt(31) + (qr1d(k) + qrten(k)*dtsave)*wb_rho(k)*dzq(k)\n"
    "            wbt(32) = wbt(32) + 1.0D0\n"
    "            qrten(k) = -qr1d(k)*odts\n            nrten(k) = -nr1d(k)*odts\n")
sub(post, "'(a,i7,30es17.9)'", "'(a,i7,32es17.9)'")
sub(d, "'(a,i7,30es17.9)'", "'(a,i7,32es17.9)'")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBR").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
