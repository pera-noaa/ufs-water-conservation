#!/usr/bin/env python3
"""Fix B for the 32-bit write-back tracer-mass bias: divide the tracer mass by the delp actually stored, not by the real*8 q0.
Usage: python3 fix_writeback_apply.py <atmosphere.F90>   (fvGFS or UFS driver; writes <file>.preFIXB; exactly one match required)"""
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()
old = "         Atm(n)%q(i,j,k1,1:nq_adv) = qwat(1:nq_adv) / q0\n"
new = "         Atm(n)%q(i,j,k1,1:nq_adv) = qwat(1:nq_adv) / Atm(n)%delp(i,j,k1)   ! divide by the stored (rounded) delp\n"
if s.count(old) != 1 or s.count("         Atm(n)%delp(i,j,k1) = q0\n") != 1:
    sys.exit("ABORT: anchor count != 1")
if s.index("         Atm(n)%delp(i,j,k1) = q0\n") > s.index(old):
    sys.exit("ABORT: delp is not stored before q")
bak = f.with_suffix(f.suffix + ".preFIXB")
if bak.exists():
    sys.exit(f"ABORT: {bak} exists")
bak.write_text(s)
f.write_text(s.replace(old, new))
print(f"applied fix B to {f}")
