#!/usr/bin/env python3
"""K's driver part, run-phase form (UFS diff 15): noahmpdrv_init and its .meta are restored from the commit before K,
and noahmpdrv_run sets Noah-MP's module latent heats at its start from the con_hvap and con_hfus it already receives
(both the CCPP cap and NOAA-EMC/noahmp's land component pass them), so no interface changes. An OPTIONAL init argument
does not compile: the CCPP cap points a pointer at the host's PARAMETER constants.
Inserted before `if (cpllnd .and. cpllnd2atm) return` where present, else after the run phase's `errflg = 0`.
Aborts unless every anchor matches once; refuses a file already converted.
Usage: python3 port_noahmp_k_runphase_any.py <noahmpdrv.F90> <noahmpdrv.meta> <pre-K noahmpdrv.F90> <pre-K noahmpdrv.meta>"""
import re
import sys
from pathlib import Path

f90, meta, f90_0, meta_0 = (Path(a) for a in sys.argv[1:5])
s, m, s0, m0 = f90.read_text(), meta.read_text(), f90_0.read_text(), meta_0.read_text()
if "hvap_lsm => hvap" in s:
    sys.exit("ABORT: already converted")


def span(txt, pat_a, pat_b, what):
    a = list(re.finditer(pat_a, txt))
    if len(a) != 1:
        sys.exit(f"ABORT {what}: start matched {len(a)} times")
    b = re.search(pat_b, txt[a[0].start():])
    if not b:
        sys.exit(f"ABORT {what}: end not found")
    return a[0].start(), a[0].start() + b.end()


# init routine and its metadata table back to the pre-K text
i0, i1 = span(s, r"\n *subroutine noahmpdrv_init\(", r"\n *end subroutine noahmpdrv_init\n", "init (current)")
j0, j1 = span(s0, r"\n *subroutine noahmpdrv_init\(", r"\n *end subroutine noahmpdrv_init\n", "init (pre-K)")
s = s[:i0] + s0[j0:j1] + s[i1:]
i0, i1 = span(m, r"name = noahmpdrv_init\n", r"\n(?=\[ccpp-arg-table\])", "init table (current)")
j0, j1 = span(m0, r"name = noahmpdrv_init\n", r"\n(?=\[ccpp-arg-table\])", "init table (pre-K)")
m = m[:i0] + m0[j0:j1] + m[i1:]

# run phase: the module variables and their assignment
r0 = s.index("subroutine noahmpdrv_run")
u = list(re.finditer(r"\n( *)use module_sf_noahmp_glacier *\n", s[r0:]))
if not u:
    sys.exit("ABORT: run-phase glacier use not found")
u = u[0]
ind = u.group(1)
pos = r0 + u.end()
s = (s[:pos] + f"{ind}use module_sf_noahmplsm,    only : hvap_lsm => hvap, hsub_lsm => hsub, hfus_lsm => hfus\n"
     f"{ind}use noahmp_glacier_globals, only : hvap_gla => hvap, hsub_gla => hsub, hfus_gla => hfus\n" + s[pos:])
r0 = s.index("subroutine noahmpdrv_run")
blk = ("  ! the host's latent heats, so the land pays the latent energy its water carries in the atmosphere\n"
       "  hvap_lsm = con_hvap\n  hfus_lsm = con_hfus\n  hsub_lsm = con_hvap + con_hfus\n"
       "  hvap_gla = hvap_lsm\n  hfus_gla = hfus_lsm\n  hsub_gla = hsub_lsm\n\n")
c = list(re.finditer(r"\n(?=  if \(cpllnd \.and\. cpllnd2atm\) return\n)", s[r0:]))
if len(c) == 1:
    pos = r0 + c[0].end()
else:
    e = list(re.finditer(r"\n *errflg = 0\n\n", s[r0:]))
    if not e:
        sys.exit("ABORT: no run-phase anchor")
    pos = r0 + e[0].end()
s = s[:pos] + blk + s[pos:]
f90.write_text(s)
meta.write_text(m)
print(f"converted {f90} and {meta}")
