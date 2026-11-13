#!/usr/bin/env python3
"""Fix E's interface (UFS diff 08): noahmpdrv_run takes the CCPP loop counter `iter` as an OPTIONAL TRAILING argument
(with first_iter = iter == 1 when present, .true. otherwise) instead of a required argument after flag_iter, so a
caller with the original argument list (NOAA-EMC/noahmp's land component, linked against this copy in atm-land builds,
together with that repo's companion 08b) still lines up. Converts the earlier form of E; aborts unless every anchor
matches once; refuses a file already converted.
Usage: python3 port_noahmp_e_optional_any.py <noahmpdrv.F90> <noahmpdrv.meta> <pre-E noahmpdrv.F90>"""
import re
import sys
from pathlib import Path

f90, meta, pre = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
s, m, s0 = f90.read_text(), meta.read_text(), pre.read_text()
if "first_iter" in s:
    sys.exit("ABORT: already converted")


def once(pat, txt, what, flags=0):
    r = list(re.finditer(pat, txt, flags))
    if len(r) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {len(r)}")
    return r[0]


# argument list: the earlier E's 'flag_iter, iter, con_g' line back to the pre-E line
a = once(r"\n[^\n]*flag_iter, iter, con_g,[^\n]*\n", s, "argument line")
b = once(r"\n[^\n]*flag_iter, ?con_g,[^\n]*\n", s0, "pre-E argument line")
s = s[:a.start()] + b.group(0) + s[a.end():]
d = once(r"\n *integer *, intent\(in\) *:: iter *! surface iteration \(ccpp loop counter\)\n", s, "earlier declaration")
s = s[:d.start()] + "\n" + s[d.end():]

# iter as the last argument
r0 = s.index("subroutine noahmpdrv_run")
hdr = s[r0:r0 + s[r0:].index("implicit none")]
e = list(re.finditer(r"\n( *)(\w+)( *)&\n( *)\)\n", hdr))
if len(e) == 1:  # ')' on its own line
    e = e[0]
    last = f"{e.group(1)}{e.group(2)},{e.group(3)[1:] if len(e.group(3)) > 1 else ' '}&\n"
    it = f"{e.group(1)}iter{' ' * (len(e.group(2)) + len(e.group(3)) - 4)}&\n"
    s = s[:r0 + e.start()] + "\n" + last + it + f"{e.group(4)})\n" + s[r0 + e.end():]
else:  # ')' after the last argument (older copies)
    e = once(r"(\w+)\)[ \t]*\n", hdr, "argument list end")
    s = s[:r0 + e.start()] + f"{e.group(1)}, iter)" + s[r0 + e.end() - 1:]
fl = once(r"\n *logical *, dimension\(:\) *, intent\(in\) *:: flag_iter *![^\n]*\n", s, "flag_iter declaration")
s = (s[:fl.end()] + "  ! optional and last: NOAA-EMC/noahmp's land component calls this routine with the original arguments\n"
     "  integer, optional                      , intent(in)    :: iter       ! surface iteration (ccpp loop counter)\n"
     "  logical                                                :: first_iter ! land is stepped on the first iteration only\n"
     + s[fl.end():])

# first_iter
c = once(r"(\n *if \(flag_iter\(i\) \.and\. dry\(i\) \.and\. )iter == 1(\) then\n)", s, "land test")
s = s[:c.start()] + c.group(1) + "first_iter" + c.group(2) + s[c.end():]
r0 = s.index("subroutine noahmpdrv_run")
k = list(re.finditer(r"\n  if \(cpllnd \.and\. cpllnd2atm\) return\n", s[r0:]))
fi = "  first_iter = .true.\n  if (present(iter)) first_iter = iter == 1\n"
if len(k) == 1:
    pos = r0 + k[0].end()
    s = s[:pos] + "\n" + fi + s[pos:]
else:
    k = once(r"\n(?= *do i = 1, im\n)", s[r0:], "run loop")
    pos = r0 + k.end()
    s = s[:pos] + fi + "\n" + s[pos:]

# metadata: the run table's [iter] moves to the end of that table, optional
t0 = m.index("name = noahmpdrv_run")
nxt = m.find("[ccpp-arg-table]", t0)
t1 = nxt if nxt >= 0 else len(m)
tab = m[t0:t1]
blk = once(r"\[iter\]\n(?:  [^\n]*\n)+", tab, "meta [iter]")
tab = tab[:blk.start()] + tab[blk.end():]
ents = list(re.finditer(r"\[[a-z_0-9]+\]\n(?:  [^\n]*\n)+", tab))
pos = ents[-1].end()
tab = tab[:pos] + blk.group(0) + "  optional = True\n" + tab[pos:]
m = m[:t0] + tab + m[t1:]
f90.write_text(s)
meta.write_text(m)
print(f"converted {f90} and {meta}")
