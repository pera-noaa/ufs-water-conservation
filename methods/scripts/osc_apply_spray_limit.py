#!/usr/bin/env python3
"""Candidate fix (test only): cap NSST's sea-spray evaporation so one explicit step cannot drive the lowest layer past saturation.
Usage: python3 osc_apply_spray_limit.py <sfc_nst.f90>   (rewritten in place; a .preSPRAY copy is kept)
The spray term moves evaps*dt of water into, and (alps-gams)*evaps*dt*hvap of heat out of, a layer of mass m1 = 2*(ps-prsl1)/g;
its saturation deficit d = qs(T1)-q1 then changes by -(alps + (alps-gams)*gam)*evaps*dt/(m1*hvap), gam = 1/bb1 - 1. The cap
keeps that change no larger than d (evaporation) or than -d (condensation onto spray). Every anchor must match exactly once."""
import sys
from pathlib import Path

p = Path(sys.argv[1])
s = p.read_text()
old = ("          evaps = evaps * rho_a(i) * hvap * (qss1 - q0(i))\n")
new = ("          evaps = evaps * rho_a(i) * hvap * (qss1 - q0(i))\n"
       "! cap: one explicit step may at most remove the layer's saturation deficit\n"
       "          ptem = (alps + (alps - gams) * (1. / bb1 - 1.)) * timestep\n"
       "          tem = abs(qss1 - q0(i)) * 2. * (ps(i) - prsl1(i)) / 9.80665\n"
       "          tem = tem * hvap / ptem\n"
       "          evaps = sign(min(abs(evaps), tem), evaps)\n")
if s.count(old) != 1 or "! cap: one explicit step" in s:
    sys.exit(f"ABORT: anchor count {s.count(old)} or already patched")
p.with_suffix(p.suffix + ".preSPRAY").write_text(s)
p.write_text(s.replace(old, new))
print(f"spray cap applied: {p}")
