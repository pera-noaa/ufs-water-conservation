#!/usr/bin/env python3
"""Held fix 13a for any Thompson copy: in flux-form rain, ice, snow and graupel sedimentation, floored layers carry their
actual content, so the R1 placeholder is not sedimented as mass (floor start before the substeps; the in-loop
max(R1, ...) floors become max(0, ...)). Held together with M2 (UFS patches/held/). Keeps the copy's MAX/max case and
its real kind (0._wp where the copy uses wp). Aborts unless every anchor matches once; refuses a second run.
Usage: python3 port_thompson_placeholder_any.py <module_mp_thompson.F90|.F>"""
import re
import sys
from pathlib import Path

p = Path(sys.argv[1])
s = p.read_text()
if "the R1 placeholder is not sedimented as mass" in s:
    sys.exit("ABORT: already patched")
up = bool(re.search(r"rr\(k\) = MAX\(R1, rr\(k\) - sed_r", s))
mx = "MAX" if up else "max"
zero = "0._wp" if re.search(r"real\(wp\)|_wp\b", s) else "0."

for x, n, name in (("r", 1, "rain"), ("i", 2, "ice"), ("s", 3, "snow"), ("g", 4, "graupel")):
    # the flux-form block: 'if (ANY(L_qX ...)) then', its nstep line, and for rain/graupel the sedi_semi test
    hdr = re.compile(rf"\n *if \(ANY\(L_q{x} \.eqv\. \.true\.\)\) then\n *nstep = (?:nint|NINT)\(1\./onstep\({n}\)\)\n"
                     r"(?:[ \t]*\n)*(?: *if ?\(\.not\. sedi_semi\) then *\n)?(?=( *)do n = 1, nstep\n)")
    h = list(hdr.finditer(s))
    if len(h) != 1:
        sys.exit(f"ABORT {name} block: expected 1 match, found {len(h)}")
    ind = h[0].group(1)
    ins = (f"{ind}! floored layers carry their actual {name}, so the R1 placeholder is not sedimented as mass\n"
           f"{ind}do k = kts, kte\n"
           f"{ind}   if (r{x}(k) .le. R1) r{x}(k) = {mx}({zero}, (q{x}1d(k) + q{x}ten(k)*DT)*rho(k))\n"
           f"{ind}enddo\n")
    s = s[:h[0].end()] + ins + s[h[0].end():]
    for pat in (rf"r{x}\(k\) = (?:max|MAX)\(R1, (r{x}\(k\) - sed_{x}\(k\)\*odzq\*DT\*onstep\({n}\)\))",
                rf"r{x}\(k\) = (?:max|MAX)\(R1, (r{x}\(k\) \+ \(sed_{x}\(k\+1\)-sed_{x}\(k\)\) &)"):
        m = list(re.finditer(pat, s))
        if len(m) != 1:
            sys.exit(f"ABORT {name} floor: expected 1 match of {pat!r}, found {len(m)}")
        s = s[:m[0].start()] + f"r{x}(k) = {mx}({zero}, {m[0].group(1)}" + s[m[0].end():]
p.write_text(s)
print(f"patched {p} (13a: rain, ice, snow, graupel; {mx}, {zero})")
