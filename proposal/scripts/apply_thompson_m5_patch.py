#!/usr/bin/env python3
"""Fix M5 (diff 16): Thompson water at or below R1 goes to vapour instead of being deleted (entry, semi-Lagrangian
sedimentation, leftover rain). Same change as fix_thompson_r1_conserve_ups.py 'all', with whitespace-tolerant anchors so
it applies to the v1 snapshot as well as ufs/dev. Usage: python3 apply_thompson_m5_patch.py <module_mp_thompson.F90>
Every anchor must match exactly once, else nothing is written."""
import re
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()


def sub(pat, rep):
    global s
    n = len(re.findall(pat, s))
    if n != 1:
        sys.exit(f"ABORT {f.name}: expected 1 match, found {n}: {pat[:70]!r}")
    s = re.sub(pat, rep, s)


LV = "(lvap0 + (2106.0 - 4218.0)*(t1d(k)-273.15))"
OCP = "/(Cp*(1.+0.887*qv(k)))*(1-IFDRY)"
for q, n, r, lat in (("qc", "nc", "rc", LV), ("qi", "ni", "ri", "lsub"), ("qr", "nr", "rr", LV),
                     ("qs", None, "rs", "lsub"), ("qg", None, "rg", "lsub")):
    pat = (rf"(\n( *)else\n)(( *){q}1d\(k\) = 0\.0\n" + (rf" *{n}1d\(k\) = 0\.0\n" if n else "")
           + rf" *{r}\(k\) = R1\n)")
    sub(pat, lambda m, q=q, lat=lat: m.group(1)
        + f"{m.group(4)}! at or below R1: to vapour with its latent heat, not deleted\n"
        + f"{m.group(4)}qv1d(k) = qv1d(k) + {q}1d(k)\n"
        + f"{m.group(4)}t1d(k) = t1d(k) - {lat}*{q}1d(k){OCP}\n" + m.group(3))
sub(r"\n( *)rql\(:\) = max\(qn\(:\),R1\)\n",
    lambda m: f"\n{m.group(1)}! mass not transported (inputs <= R1) stays in place; no floor, so the column change is -precip\n"
              f"{m.group(1)}rql(:) = qn(:) + (rql(:) - qq(:))\n")
sub(r"\n( *)(call semi_lagrange_sedim\(kte,dzq,vtnrk,nr,vtr,pdummy,dtcfl,R2\)\n)",
    lambda m: f"\n{m.group(1)}{m.group(2)}{m.group(1)}nr(:) = max(nr(:), R2)\n")
sub(r"\n( *)(qrten\(k\) = -qr1d\(k\)\*odts\n *nrten\(k\) = -nr1d\(k\)\*odts\n)",
    lambda m: f"\n{m.group(1)}! rain left at or below R1 goes to vapour with its latent heat, not deleted\n"
              f"{m.group(1)}qvten(k) = qvten(k) + (qr1d(k) + qrten(k)*dtsave)*odts\n"
              f"{m.group(1)}tten(k) = tten(k) - lvap(k)*ocp(k)*(qr1d(k) + qrten(k)*dtsave)*odts*(1-IFDRY)\n"
              f"{m.group(1)}{m.group(2)}")
f.write_text(s)
print(f"patched {f} (M5)")
