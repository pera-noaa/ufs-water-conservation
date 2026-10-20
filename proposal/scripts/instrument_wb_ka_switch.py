#!/usr/bin/env python3
"""Make a metered A' samfdeepcnv.f switchable at run time: A before step WKA_KSW (env, default never), A' from it on.
Usage: python3 instrument_wb_ka_switch.py <samfdeepcnv.f>   (the A'-metered file from instrument_wb_ka.py; rewritten in place)
The A' face correction is multiplied by wka_sw (0 before the switch, 1 after): adding 0*x leaves flxtvd bit-identical to A,
and 1*x is A' exactly, so steps before WKA_KSW reproduce the A run bit for bit. The meter's face formulas follow wka_sw.
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

p = Path(sys.argv[1])
s = p.read_text()
if "! fix A': " not in s or "wka_kdt" not in s:
    sys.exit("ABORT: not an A'-metered samfdeepcnv.f")
R = [
    ("     &         + eta(i,k) * (qo(i,k) - tem1)\n", "     &         + wka_sw * eta(i,k) * (qo(i,k) - tem1)\n"),
    ("     &         - edto(i) * etad(i,k) * (qo(i,k) - tem1)\n",
     "     &         - wka_sw * edto(i) * etad(i,k) * (qo(i,k) - tem1)\n"),
    ("     &           + eta(i,k) * (ctro(i,k,n) - tem1)\n", "     &           + wka_sw * eta(i,k) * (ctro(i,k,n) - tem1)\n"),
    ("     &           - edto(i) * etad(i,k) * (ctro(i,k,n) - tem1)\n",
     "     &           - wka_sw * edto(i) * etad(i,k)\n     &           * (ctro(i,k,n) - tem1)\n"),
    ("     &          + edto(i) * etad(i,k) * qo(i,k)\n",
     "     &          + edto(i)*etad(i,k)*(tem1+wka_sw*(qo(i,k)-tem1))\n"),
    ("              if(k == kb(i)) wka_jd(i) = wka_jd(i) + eta(i,k) * qo(i,k)\n",
     "              if(k == kb(i)) wka_jd(i) = wka_jd(i)\n"
     "     &          + eta(i,k)*(tem1+wka_sw*(qo(i,k)-tem1))\n"),
    ("      integer, save :: wka_kdt = -1\n", "      integer, save :: wka_kdt = -1, wka_ksw = -1\n"),
    ("      logical wka_box(im)\n", "      logical wka_box(im)\n      real(kind=kind_phys) wka_sw\n      character(len=16) wka_env\n"),
    ("      if(kdt /= wka_kdt) then\n",
     "      if(wka_ksw < 0) then\n"
     "        wka_ksw = huge(1)\n"
     "        call get_environment_variable('WKA_KSW', wka_env)\n"
     "        if(len_trim(wka_env) > 0) read(wka_env,*) wka_ksw\n"
     "        write(*,'(a,i12)') 'WKA_KSW ', wka_ksw\n"
     "      endif\n"
     "      wka_sw = 0.\n"
     "      if(kdt >= wka_ksw) wka_sw = 1.\n"
     "      if(kdt /= wka_kdt) then\n"),
]
for a, b in R:
    if s.count(a) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(a)}: {a.strip()[:60]!r}")
    s = s.replace(a, b)
for ln in s.split("\n"):
    if len(ln) > 72 and not ln.startswith(("!", "c", "C")) and "wka" in ln:
        sys.exit(f"ABORT: line > 72 columns: {ln!r}")
p.write_text(s)
print(f"switchable A/A' at WKA_KSW: {p}")
