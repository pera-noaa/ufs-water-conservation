#!/usr/bin/env python3
"""Candidate fix for the last Thompson water loss (ccpp-physics ufs/dev module_mp_thompson.F90; also on top of the
instrument_wb_ups.py meters). Usage: python3 fix_thompson_r1_conserve_ups.py <ufs-weather-model> [entry|sl|rten|both|all]   (both = entry+sl)
  entry: at entry, hydrometeors at or below R1 (tiny positive or negative) are exchanged with vapour, with their
         latent heat, instead of being set to zero (the same treatment M1 gives them at exit).
  sl:    semi_lagrange_sedim returns the transported mass plus the mass it did not transport (inputs <= R1, which
         include Thompson's R1 placeholders for absent species), unfloored, so its column change equals minus its
         surface precipitation; the rain-number call keeps its R2 floor in the caller.
  rten:  where the rain left after the source/sink processes is at or below R1 (as density), the branch that sets
         qrten = -qr1d/dt first exchanges that remainder with vapour, with its latent heat, instead of deleting it.
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

m = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90"
what = sys.argv[2] if len(sys.argv) > 2 else "both"
s = m.read_text()


def sub(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {m.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    s = s.replace(old, new)


LV = "(lvap0 + (2106.0 - 4218.0)*(t1d(k)-273.15))"
OCP = "/(Cp*(1.+0.887*qv(k)))*(1-IFDRY)"
if what in ("entry", "both", "all"):
    for q, n, r, lat in (("qc", "nc", "rc", LV), ("qi", "ni", "ri", "lsub"), ("qr", "nr", "rr", LV),
                         ("qs", None, "rs", "lsub"), ("qg", None, "rg", "lsub")):
        old = f"         else\n            {q}1d(k) = 0.0\n" + (f"            {n}1d(k) = 0.0\n" if n else "") \
              + f"            {r}(k) = R1\n"
        new = ("         else\n"
               "            ! at or below R1: to vapour with its latent heat, not deleted\n"
               f"            qv1d(k) = qv1d(k) + {q}1d(k)\n"
               f"            t1d(k) = t1d(k) - {lat}*{q}1d(k){OCP}\n"
               + old[len("         else\n"):])
        sub(old, new)
if what in ("sl", "both", "all"):
    sub("      rql(:) = max(qn(:),R1)\n",
        "      ! mass not transported (inputs <= R1) stays in place; no floor, so the column change is -precip\n"
        "      rql(:) = qn(:) + (rql(:) - qq(:))\n")
    sub("               call semi_lagrange_sedim(kte,dzq,vtnrk,nr,vtr,pdummy,dtcfl,R2)\n",
        "               call semi_lagrange_sedim(kte,dzq,vtnrk,nr,vtr,pdummy,dtcfl,R2)\n"
        "               nr(:) = max(nr(:), R2)\n")
if what in ("rten", "all"):
    sub("            qrten(k) = -qr1d(k)*odts\n            nrten(k) = -nr1d(k)*odts\n",
        "            ! rain left at or below R1 goes to vapour with its latent heat, not deleted\n"
        "            qvten(k) = qvten(k) + (qr1d(k) + qrten(k)*dtsave)*odts\n"
        "            tten(k) = tten(k) - lvap(k)*ocp(k)*(qr1d(k) + qrten(k)*dtsave)*odts*(1-IFDRY)\n"
        "            qrten(k) = -qr1d(k)*odts\n            nrten(k) = -nr1d(k)*odts\n")
m.with_suffix(m.suffix + ".preFIX" + ("" if what in ("entry", "sl", "both", "all") else "_" + what)).write_text(m.read_text())
m.write_text(s)
print(f"fixed ({what}) {m}")
