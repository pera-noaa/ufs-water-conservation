#!/usr/bin/env python3
"""Port M5 (ccpp-physics diff 16) to the WRF and MPAS copies of Thompson: water at or below R1 goes to vapour with its
latent heat instead of being deleted, at the entry else-branches (cloud, ice, rain, snow, graupel) and where the rain
tendency is overwritten to remove rain left at or below R1. The semi_lagrange_sedim part of M5 has no counterpart
(WRF and MPAS have no semi-Lagrangian sedimentation). Usage: python3 port_thompson_m5_wrf_mpas.py <module_mp_thompson.F>
Each edit must match exactly once, else nothing is written."""
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


C = "            ! at or below R1: to vapour with its latent heat, not deleted\n"
LIQ = "(lvap0 + (2106.0 - 4218.0)*(t1d(k)-273.15))"
for q, rest, lat in (("qc", "            nc1d(k) = 0.0\n            rc(k) = R1\n", LIQ),
                     ("qi", "            ni1d(k) = 0.0\n            ri(k) = R1\n", "lsub"),
                     ("qr", "            nr1d(k) = 0.0\n            rr(k) = R1\n", LIQ),
                     ("qs", "            rs(k) = R1\n", "lsub"),
                     ("qg", None, "lsub")):
    if rest is None:  # graupel: MPAS resets rg only; WRF also graupel number and volume
        forms = ["            rg(k) = R1\n", "            ng1d(k) = 0.0\n            qb1d(k) = 0.0\n"]
        hits = [r for r in forms if s.count(f"         else\n            qg1d(k) = 0.0\n" + r) == 1]
        if len(hits) != 1:
            sys.exit(f"ABORT entry qg: {len(hits)} of the known forms match")
        rest = hits[0]
    old = f"         else\n            {q}1d(k) = 0.0\n" + rest
    new = (f"         else\n" + C +
           f"            qv1d(k) = qv1d(k) + {q}1d(k)\n"
           f"            t1d(k) = t1d(k) - {lat}*{q}1d(k)/(Cp*(1.+0.887*qv(k)))*(1-IFDRY)\n"
           f"            {q}1d(k) = 0.0\n" + rest)
    s = one(s, old, new, f"entry {q}")
s = one(s, "         else\n           qrten(k) = -qr1d(k)*odts\n           nrten(k) = -nr1d(k)*odts\n",
        "         else\n"
        "           ! rain left at or below R1 goes to vapour with its latent heat, not deleted\n"
        "           qvten(k) = qvten(k) + (qr1d(k) + qrten(k)*dtsave)*odts\n"
        "           tten(k) = tten(k) - lvap(k)*ocp(k)*(qr1d(k) + qrten(k)*dtsave)*odts*(1-IFDRY)\n"
        "           qrten(k) = -qr1d(k)*odts\n           nrten(k) = -nr1d(k)*odts\n", "rain overwrite")
f.write_text(s)
print(f"patched {f.name}: M5 (5 entry branches, rain overwrite)")
