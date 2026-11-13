#!/usr/bin/env python3
"""Diff 07's vapour-floor refill (as apply_thompson_qv_floor_patch.py) for any Thompson copy that already carries M1's
clip exchange (CCPP ufs/dev and production in either code style, WRF, MPAS). The end-of-step update no longer floors
vapour at 1.E-10; after the final clips, vapour left below the floor is refilled first from the layer's condensate (with
its latent heat, using the copy's own lvap/lsub/ocp tokens from the M1 clip exchange; number concentrations, and graupel
number and volume where the copy has them, scaled with mass), then from the column's other vapour, mass-weighted; only a
column with no vapour to spare is still floored. Keeps the copy's indentation, MAX/max case and real kind; aborts unless
every anchor matches once, and refuses a second run.
Usage: python3 port_thompson_qv_floor_any.py <module_mp_thompson.F90|.F>"""
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


if "Vapour left below the floor is refilled" in s:
    sys.exit("ABORT: already has the vapour-floor refill")
for v in ("xdef", "xavl", "xcnd", "frc"):
    if re.search(rf"\b{v}\b", s, re.I):
        sys.exit(f"ABORT: identifier {v} already used in this copy")

# M1's clip exchange gives the copy's latent-heat tokens (liquid: cloud water; ice: cloud ice)
liq = once(r"\n *tten\(k\) = tten\(k\) - (\S+?)\*(\S+?)\*xcl\*odt\*\(1-IFDRY\)\n(?= *endif\n *xcl = qi1d\(k\) \+ qiten\(k\)\*DT\n)",
           s, "M1 cloud-water clip exchange")
lv, oc = liq.group(1), liq.group(2)
ice = once(r"\n *xcl = qi1d\(k\) \+ qiten\(k\)\*DT\n(?: *[^\n]*\n){3} *tten\(k\) = tten\(k\) - (\S+?)\*" + re.escape(oc)
           + r"\*xcl\*odt\*\(1-IFDRY\)\n", s, "M1 cloud-ice clip exchange")
ls = ice.group(1)

# end-of-step update: vapour no longer floored there
m = once(r"^( *)qv1d\(k\) = (max|MAX)\(1\.E-10, qv1d\(k\) \+ qvten\(k\)\*DT\)$", s, "final vapour update", re.M)
mx = m.group(2)
mn = "MIN" if mx == "MAX" else "min"
pos = m.start() - 1
s = s[:m.start()] + f"{m.group(1)}qv1d(k) = qv1d(k) + qvten(k)*DT" + s[m.end():]

# the loop holding it: its 'do k = kts, kte' (indent i) and the first 'enddo' at that indent after it
do = list(re.finditer(r"\n( *)do k = kts, kte\n", s[:pos]))
if not do:
    sys.exit("ABORT: final update loop start not found")
i = do[-1].group(1)
end = re.compile(rf"\n{i}enddo\n").search(s, pos)
if not end:
    sys.exit("ABORT: final update loop end not found")
body = s[do[-1].start():end.end()]
for need in (r"qg1d\(k\) = qg1d\(k\) \+ qgten\(k\)\*DT", r"qs1d\(k\) = qs1d\(k\) \+ qsten\(k\)\*DT"):
    if not re.search(need, body):
        sys.exit(f"ABORT: final update loop does not contain {need}")
graupel_moments = bool(re.search(r"ng1d\(k\) = \w+\(R2/rho\(k\), ng1d\(k\) \+ ngten\(k\)\*DT\)", body, re.I))
if graupel_moments and "qb1d(k)" not in body:
    sys.exit("ABORT: graupel number without graupel volume in the final update loop")

# real kind: the copy's own, from the xcl declaration M1 added
d = once(r"\n( *)(real\(wp\)|REAL)( ?:: ?)(?:[\w ,]*, ?)?xcl\b[^\n]*\n", s, "xcl declaration", re.I)
K = "_wp" if d.group(2) == "real(wp)" else ""
b, b2, b3 = i + "   ", i + "      ", i + "         "
F = "1.E-10"
sc = ["qc1d", "nc1d", "qr1d", "nr1d", "qi1d", "ni1d", "qs1d", "qg1d"] + (["ng1d", "qb1d"] if graupel_moments else [])
block = (f"\n!..Vapour left below the floor is refilled, not created: first from the layer's\n"
         f"!.. condensate, with its latent heat, then from the column's other vapour.\n"
         f"{i}do k = kts, kte\n"
         f"{b}if (qv1d(k) .lt. {F}) then\n"
         f"{b2}xcnd = qc1d(k) + qr1d(k) + qi1d(k) + qs1d(k) + qg1d(k)\n"
         f"{b2}if (xcnd .gt. 0.) then\n"
         f"{b3}frc = {mn}(1.{K}, ({F} - qv1d(k))/xcnd)\n"
         f"{b3}t1d(k) = t1d(k) - frc*{oc}*(1-IFDRY)                           &\n"
         f"{b3}       * ({lv}*(qc1d(k)+qr1d(k)) + {ls}*(qi1d(k)+qs1d(k)+qg1d(k)))\n"
         f"{b3}qv1d(k) = qv1d(k) + frc*xcnd\n"
         + "".join(f"{b3}{q}(k) = {q}(k)*(1.-frc)\n" for q in sc) +
         f"{b2}endif\n"
         f"{b}endif\n"
         f"{i}enddo\n"
         f"{i}xdef = 0.\n"
         f"{i}xavl = 0.\n"
         f"{i}do k = kts, kte\n"
         f"{b}xdef = xdef + {mx}({F} - qv1d(k), 0.{K})*rho(k)*dzq(k)\n"
         f"{b}xavl = xavl + {mx}(qv1d(k) - {F}, 0.{K})*rho(k)*dzq(k)\n"
         f"{i}enddo\n"
         f"{i}if (xdef .gt. 0. .and. xavl .gt. 0.) then\n"
         f"{b}frc = {mn}(1.{K}, xdef/xavl)\n"
         f"{b}xcnd = {mn}(1.{K}, xavl/xdef)\n"
         f"{b}do k = kts, kte\n"
         f"{b2}if (qv1d(k) .lt. {F}) then\n"
         f"{b3}qv1d(k) = qv1d(k) + ({F} - qv1d(k))*xcnd\n"
         f"{b2}else\n"
         f"{b3}qv1d(k) = qv1d(k) - (qv1d(k) - {F})*frc\n"
         f"{b2}endif\n"
         f"{b}enddo\n"
         f"{i}endif\n"
         f"!..Only a column with no vapour to spare is still floored.\n"
         f"{i}do k = kts, kte\n"
         f"{b}qv1d(k) = {mx}({F}, qv1d(k))\n"
         f"{i}enddo\n")
s = s[:end.end()] + block + s[end.end():]

# declarations: after dtcfl/rainsfc/graulsfc where the copy has it (as ufs/dev), else after the xcl declaration
m = list(re.finditer(r"\n( *)(real\(wp\)|REAL)( ?:: ?)dtcfl, ?rainsfc, ?graulsfc\n", s, re.I))
if len(m) > 1:
    sys.exit(f"ABORT dtcfl declaration: expected at most 1 match, found {len(m)}")
m = m[0] if m else once(r"\n( *)(real\(wp\)|REAL)( ?:: ?)(?:[\w ,]*, ?)?xcl\b[^\n]*\n", s, "xcl declaration", re.I)
s = s[:m.end()] + f"{m.group(1)}{m.group(2)}{m.group(3)}xdef, xavl, xcnd, frc\n" + s[m.end():]
mp.write_text(s)
print(f"patched {mp} (vapour-floor refill; {lv}/{ls}/{oc}; {mx}; kind '{K or 'default'}'"
      f"{'; graupel number and volume scaled' if graupel_moments else ''})")
