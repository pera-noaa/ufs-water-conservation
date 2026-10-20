#!/usr/bin/env python3
"""Fix candidate: substep Thompson cloud-water sedimentation (CFL<1 per substep) so it cannot remove more than the layer holds."""
# Usage: gc_fix_thompson_qc_sedim.py <module_mp_thompson.F90> [--count]  (v1 snapshot or ufs/dev; needs the 'count it
# as precipitation' line from the fixes). Columns with CFL < 1 in every layer keep the original code verbatim; only
# CFL >= 1 columns take the substepped path.
import re
import sys
from pathlib import Path

f = Path(sys.argv[1])
COUNT = len(sys.argv) > 2 and sys.argv[2] == "--count"  # meter: wbt(11) counts substepped columns
s = f.read_text()
pat = re.compile(
    r"(?P<ind> *)do k = kte, kts, -1\n"
    r" *sed_c\(k\) = vtck\(k\)\*rc\(k\)\n"
    r" *sed_n\(k\) = vtnck\(k\)\*nc\(k\)\n"
    r" *enddo\n"
    r" *do k = ksed1\(5\), kts, -1\n"
    r" *odzq = 1\./dzq\(k\)\n"
    r" *orho = 1\./rho\(k\)\n"
    r" *qcten\(k\) = qcten\(k\) \+ \(sed_c\(k\+1\)-sed_c\(k\)\) \*odzq\*orho\n"
    r" *ncten\(k\) = ncten\(k\) \+ \(sed_n\(k\+1\)-sed_n\(k\)\) \*odzq\*orho\n"
    r" *rc\(k\) = (?P<mx>MAX|max)\(R1, rc\(k\) \+ \(sed_c\(k\+1\)-sed_c\(k\)\) \*odzq\*DT\)\n"
    r" *nc\(k\) = (?P=mx)\(10\., nc\(k\) \+ \(sed_n\(k\+1\)-sed_n\(k\)\) \*odzq\*DT\)\n"
    r" *enddo\n"
    r" *! cloud water settling out of the lowest layer reaches the surface: count it as precipitation\n"
    r" *if \(ksed1\(5\) \.ge\. kts\) pptrain = pptrain \+ sed_c\(kts\)\*DT\n")
m = list(pat.finditer(s))
if len(m) != 1:
    sys.exit(f"ABORT {f.name}: expected 1 cloud-sedimentation block, found {len(m)}")
i, X = m[0].group("ind"), m[0].group("mx")
new = (f"{i}! substep so no layer loses more than it holds in one pass (CFL < 1 per substep)\n"
       f"{i}nstep_c = 1\n"
       f"{i}do k = ksed1(5), kts, -1\n"
       f"{i}   nstep_c = {X}(nstep_c, INT(DT*{X}(vtck(k),vtnck(k))/dzq(k) + 1.))\n"
       f"{i}enddo\n"
       f"{i}if (nstep_c == 1) then\n"
       + m[0].group(0) +
       f"{i}else\n"
       + (f"{i}wbt(11) = wbt(11) + 1.0D0\n" if COUNT else "") +
       f"{i}onstep_c = 1./REAL(nstep_c)\n"
       f"{i}do n = 1, nstep_c\n"
       f"{i}do k = kte, kts, -1\n"
       f"{i}   sed_c(k) = vtck(k)*rc(k)\n"
       f"{i}   sed_n(k) = vtnck(k)*nc(k)\n"
       f"{i}enddo\n"
       f"{i}do k = ksed1(5), kts, -1\n"
       f"{i}   odzq = 1./dzq(k)\n"
       f"{i}   orho = 1./rho(k)\n"
       f"{i}   qcten(k) = qcten(k) + (sed_c(k+1)-sed_c(k)) *odzq*onstep_c*orho\n"
       f"{i}   ncten(k) = ncten(k) + (sed_n(k+1)-sed_n(k)) *odzq*onstep_c*orho\n"
       f"{i}   rc(k) = {X}(R1, rc(k) + (sed_c(k+1)-sed_c(k)) *odzq*DT*onstep_c)\n"
       f"{i}   nc(k) = {X}(10., nc(k) + (sed_n(k+1)-sed_n(k)) *odzq*DT*onstep_c)\n"
       f"{i}enddo\n"
       f"{i}! cloud water settling out of the lowest layer reaches the surface: count it as precipitation\n"
       f"{i}if (ksed1(5) .ge. kts) pptrain = pptrain + sed_c(kts)*DT*onstep_c\n"
       f"{i}enddo\n"
       f"{i}endif\n")
s = s[:m[0].start()] + new + s[m[0].end():]
d = re.compile(r"\n( *)(INTEGER|integer), (DIMENSION|dimension)\(5\) *:: *ksed1\n")
if len(d.findall(s)) != 1:
    sys.exit(f"ABORT {f.name}: ksed1 declaration not found once")
s = d.sub(lambda mm: mm.group(0) + f"{mm.group(1)}{mm.group(2)}:: nstep_c\n"
          f"{mm.group(1)}REAL:: onstep_c\n", s)
f.with_suffix(f.suffix + ".preGCFIX").write_text(f.read_text())
f.write_text(s)
print(f"patched {f}")
