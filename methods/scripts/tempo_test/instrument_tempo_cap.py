#!/usr/bin/env python3
"""Test-only instrumentation of module_mp_tempo_main.F90 (never committed). Adds public accumulators wcd(1:8) that
record, without changing any state arithmetic:
  wcd(1)  sum over levels and calls, below t0, of max(0, prs_rcs + prr_rcs) after the rain limiter: the snow gain in
          excess of the rain lost to rain-snow collection, i.e. the correction the C2 cap makes (kg m-3 s-1)
  wcd(2)  sum of min(0, prg_rcs) after the C2 recompute: negative graupel gain (kg m-3 s-1)
  wcd(3)  sum of min(0, qc1d + qcten*dt) entering M1: negative cloud filled from vapour (kg/kg)
  wcd(4)  sum of min(0, qg1d + qgten*dt) entering M1: negative graupel filled from vapour (kg/kg)
  wcd(5)  number of cloud-sedimentation passes with the substep rule (new code only)
  wcd(6)  largest cloud substep count (new code only)
  wcd(7)  sum over levels of max(0, vtrc*dt/dz) - 1 where positive, before sedimentation: Courant excess (any code)
Usage: instrument.py <file>"""
import re
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: {s.count(old)} matches")
    return s.replace(old, new)


s = one(s, "  public :: tempo_main, ty_tempo_main_diags\n",
        "  public :: tempo_main, ty_tempo_main_diags\n  real(wp), public :: wcd(8) = 0._wp !! test instrumentation\n", "decl")
a = s.index("  subroutine check_over_depletion")
b = s.index("  end subroutine check_over_depletion")
c = s[a:b]
m = re.search(r"^      ! (below freezing, snow cannot gain|losses to snow include)", c, re.M)
c = c[:m.start()] + "      if (temp(k) < t0) wcd(1) = wcd(1) + max(0._wp, tend%prs_rcs(k) + tend%prr_rcs(k))\n" + c[m.start():]
c = one(c, "      ! reset total rain-snow collection amount if reduced\n",
        "      wcd(2) = wcd(2) + min(0._wp, tend%prg_rcs(k))\n      ! reset total rain-snow collection amount if reduced\n", "prg")
s = s[:a] + c + s[b:]
for q, i in (("qc", 3), ("qg", 4)):
    mm = re.findall(rf"^      xcl = {q}1d\(k\) \+ {q}ten\(k\)\*\w+\n", s, re.M)
    if len(mm) != 1:
        sys.exit(f"ABORT M1 {q}")
    s = s.replace(mm[0], mm[0] + f"      wcd({i}) = wcd({i}) + min(0._wp, xcl)\n")
mm = re.findall(r"^          max\(substeps_sedi, int\(\w+/\(dz1d\(k\)/max\(vtrc\(k\), vtnc\(k\)\)\) \+ 1\._wp\)\)\n      enddo\n", s, re.M)
if len(mm) == 1:
    s = s.replace(mm[0], mm[0] + "      wcd(5) = wcd(5) + 1._wp\n      wcd(6) = max(wcd(6), real(substeps_sedi, wp))\n")
mm = re.findall(r"^ *call cloud_fallspeed\(rhof, w1d, l_qc, rc, nc, ilamc, dz1d, vtrc, vtnc, ktop_sedi\)\n", s, re.M)
if len(mm) != 1:
    sys.exit("ABORT cloud_fallspeed")
tdt = "global_dt" if "global_dt = dt" in s else "dt"
s = s.replace(mm[0], mm[0] + f"      wcd(7) = wcd(7) + sum(max(0._wp, vtrc(1:nz)*{tdt}/dz1d(1:nz) - 1._wp))\n")
f.write_text(s)
print("instrumented", f)
