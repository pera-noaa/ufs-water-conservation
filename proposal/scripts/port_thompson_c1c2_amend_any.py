#!/usr/bin/env python3
"""Reference fix 0003's substepped cloud sedimentation and rain-snow cap, for any Thompson copy that already carries
the first C1/C2 port (CCPP production branches in either code style, WRF, MPAS). Matches by pattern, keeps the copy's
own case for MAX/REAL and its own kind (real(wp) where the copy uses wp), and aborts unless every anchor matches once.
Usage: python3 port_thompson_c1c2_amend_any.py <module_mp_thompson.F90|.F>"""
import re
import sys
from pathlib import Path

mp = Path(sys.argv[1])
s = mp.read_text()


def once(pat, s, what, flags=0):
    m = list(re.finditer(pat, s, flags))
    if len(m) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {len(m)}")
    return m[0]


if "nstepc" in s:
    sys.exit("ABORT: already amended (nstepc present)")

# cap, on the temperature this copy's C2 re-closure uses, at the end of rain conservation
tc = once(r"if \((\w+)\(k\)\.lt\.T_0\) prg_rcs\(k\) = -\(prr_rcs\(k\) \+ prs_rcs\(k\)\)", s, "C2 re-closure").group(1)
m = once(r"\n( *)prr_rcg\(k\) = prr_rcg\(k\) \* ratio\n( *)endif\n(?=\s*\n!\.\.Snow conservation|\s*\n!>  - Snow conservation)",
         s, "rain conservation end")
ind = m.group(2)
cap = (f"{ind}! snow cannot gain more from rain-snow collection than the rain loses to it\n"
       f"{ind}if ({tc}(k).lt.T_0 .and. prs_rcs(k).gt.-prr_rcs(k)) prs_rcs(k) = -prr_rcs(k)\n")
s = s[:m.end()] + cap + s[m.end():]

# cloud sedimentation block: from the L_qc test whose body computes sed_c, through its endif
m = once(r"\n( *)if \(ANY\(L_qc \.eqv\. \.true\.\)\) then\n( *)do k = kte, kts, -1\n *sed_c\(k\) = vtck\(k\)\*rc\(k\)\n"
         r" *sed_n\(k\) = vtnck\(k\)\*nc\(k\)\n *enddo\n *do k = ksed1\(5\), kts, -1\n *odzq = 1\./dzq\(k\)\n"
         r" *orho = 1\./rho\(k\)\n *qcten\(k\) = qcten\(k\) \+ \(sed_c\(k\+1\)-sed_c\(k\)\) \*odzq\*orho\n"
         r" *ncten\(k\) = ncten\(k\) \+ \(sed_n\(k\+1\)-sed_n\(k\)\) \*odzq\*orho\n"
         r" *rc\(k\) = (max|MAX)\(R1, rc\(k\) \+ \(sed_c\(k\+1\)-sed_c\(k\)\) \*odzq\*DT\)\n"
         r" *nc\(k\) = (?:max|MAX)\(10\., nc\(k\) \+ \(sed_n\(k\+1\)-sed_n\(k\)\) \*odzq\*DT\)\n *enddo\n"
         r" *! cloud water settling out of the lowest layer reaches the surface: count it as precipitation\n"
         r" *if \(ksed1\(5\) \.ge\. kts\) pptrain = pptrain \+ sed_c\(kts\)\*DT\n( *)endif\n", s, "cloud sedimentation")
i0, i1, mx = m.group(1), m.group(2), m.group(3)
up = mx == "MAX"
INT, REAL_ = ("INT", "REAL") if up else ("int", "real")
rk = ", kind=wp" if (not up and "real(wp)" in s) else ""
b = i1          # body indent
b2 = b + "   "   # inside the substep loop
new = (f"\n{i0}if (ANY(L_qc .eqv. .true.)) then\n"
       f"{b}! substeps keep each layer's outflow within its content (Courant number <= 1), as for the other species\n"
       f"{b}nstepc = 1\n"
       f"{b}do k = ksed1(5), kts, -1\n"
       f"{b}   if (vtck(k) .gt. 0.) nstepc = {mx}(nstepc, {INT}(DT*vtck(k)/dzq(k) + 1.))\n"
       f"{b}enddo\n"
       f"{b}onstep(5) = 1./{REAL_}(nstepc{rk})\n"
       f"{b}dtsed = DT*onstep(5)\n"
       f"{b}do n = 1, nstepc\n"
       f"{b2}do k = kte, kts, -1\n"
       f"{b2}   sed_c(k) = vtck(k)*rc(k)\n"
       f"{b2}   sed_n(k) = vtnck(k)*nc(k)\n"
       f"{b2}enddo\n"
       f"{b2}do k = ksed1(5), kts, -1\n"
       f"{b2}   odzq = 1./dzq(k)\n"
       f"{b2}   orho = onstep(5)/rho(k)\n"
       f"{b2}   qcten(k) = qcten(k) + (sed_c(k+1)-sed_c(k)) *odzq*orho\n"
       f"{b2}   ncten(k) = ncten(k) + (sed_n(k+1)-sed_n(k)) *odzq*orho\n"
       f"{b2}   rc(k) = {mx}(R1, rc(k) + (sed_c(k+1)-sed_c(k)) *odzq*dtsed)\n"
       f"{b2}   nc(k) = {mx}(10., nc(k) + (sed_n(k+1)-sed_n(k)) *odzq*dtsed)\n"
       f"{b2}enddo\n"
       f"{b2}! cloud water settling out of the lowest layer reaches the surface: count it as precipitation\n"
       f"{b2}if (ksed1(5) .ge. kts) pptrain = pptrain + sed_c(kts)*dtsed\n"
       f"{b}enddo\n"
       f"{m.group(4)}endif\n")
s = s[:m.start()] + new + s[m.end():]

# declarations next to onstep
m = once(r"\n( *)(real(?:\(wp\))?|REAL)\s*,\s*dimension\(5\)\s*::\s*onstep\b[^\n]*\n", s, "onstep declaration", re.I)
kind = m.group(2)
s = s[:m.end()] + f"{m.group(1)}{kind} :: dtsed\n{m.group(1)}{'INTEGER' if kind == 'REAL' else 'integer'} :: nstepc\n" + s[m.end():]
mp.write_text(s)
print(f"patched {mp} (cloud sedimentation substeps; rain-snow cap on {tc}; style {'upper' if up else 'lower'}{rk})")
