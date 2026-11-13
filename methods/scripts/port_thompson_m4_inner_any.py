#!/usr/bin/env python3
"""M4 at every Thompson inner step, for any CCPP Thompson copy that already has M4 (dz from host mass in mp_thompson.F90).
The driver also computes the host's dry-air layer mass dm = dp*(1-spechum)/g and passes it to every mp_gt_driver call;
mp_gt_driver takes an optional dm and, inside the inner-step loop, sets dz1d = dm / rho with rho as this copy computes it
there (its own constants, qv floored at 1e-10 as the column routine does). Matches by pattern; aborts unless every anchor
matches the expected number of times.
Usage: python3 port_thompson_m4_inner_any.py <dir holding mp_thompson.F90 and module_mp_thompson.F90>"""
import re
import sys
from pathlib import Path

d = Path(sys.argv[1])
drv, mod = d / "mp_thompson.F90", d / "module_mp_thompson.F90"
a, b = drv.read_text(), mod.read_text()
if "dm=dm" in a:
    sys.exit("ABORT: already has dm")


def once(pat, s, what, flags=0):
    m = list(re.finditer(pat, s, flags))
    if len(m) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {len(m)}")
    return m[0]


# driver: declare dm, compute it ahead of the M4 dz statement, pass it to every mp_gt_driver call
m = once(r"\n( *)real\(kind_phys\) *:: *dz\(1:ncol,1:nlev\)[^\n]*\n", a, "dz declaration")
a = a[:m.end()] + f"{m.group(1)}real(kind_phys) :: dm(1:ncol,1:nlev)               !< kg m-2\n" + a[m.end():]
m = once(r"\n( *)dz = \(prsi\(:,1:nlev\) - prsi\(:,2:nlev\+1\)\) \* \(1\.0_kind_phys - spechum\)", a, "M4 dz statement")
ind = m.group(1)
a = (a[:m.start() + 1] + f"{ind}! host's dry-air layer mass: mp_gt_driver sets each layer's width from it at every inner step\n"
     f"{ind}dm = (prsi(:,1:nlev) - prsi(:,2:nlev+1)) * (1.0_kind_phys - spechum) / con_g\n" + a[m.start() + 1:])
ncall = len(re.findall(r"^ *call mp_gt_driver\(", a, re.I | re.M))  # statements, not comments
nd = a.count("dz=dz,")
if ncall == 0 or nd != ncall:
    sys.exit(f"ABORT driver calls: {ncall} calls, {nd} 'dz=dz,'")
a = a.replace("dz=dz,", "dz=dz, dm=dm,")

# column routine: optional dm argument and declaration
h = once(r"subroutine mp_gt_driver\(", b, "mp_gt_driver header", re.I)
lines = b[h.start():].split("\n")
off = h.start()
for ln in lines:
    st = ln.strip()
    if not st.startswith("#") and st.endswith(")") and not st.endswith("&"):
        k = ln.rstrip().rfind(")")
        b = b[:off + k] + ", dm" + b[off + k:]
        break
    off += len(ln) + 1
else:
    sys.exit("ABORT: end of mp_gt_driver argument list not found")
m = once(r"\n( *)(real\(wp\)|REAL), DIMENSION\(ims:ime, kms:kme, jms:jme\), INTENT\(IN\) *:: *&\n *(?:pii, )?p, w, dz\n", b,
         "p, w, dz declaration", re.I)
b = (b[:m.end()] + f"{m.group(1)}! host dry-air layer mass (kg m-2): if present, sets dz1d at each inner step\n"
     f"{m.group(1)}{m.group(2)}, " + ("dimension(ims:ime, kms:kme, jms:jme), optional, intent(in):: dm\n" if m.group(2).islower()
     else "DIMENSION(ims:ime, kms:kme, jms:jme), OPTIONAL, INTENT(IN):: dm\n") + b[m.end():])

# inner-step loop: dz1d from dm at the density this copy computes in the same loop
m = once(r"\n *dz1d\(k\) = dz\(i,k,j\)\n", b, "dz1d assignment")
b = b[:m.start()] + "\n" + b[m.end():]
pos = m.start()
# the density statement of the same loop: the first rho(k) = ...p1d...t1d...qv1d... after the removed line, within 40 lines
m = re.compile(r"\n( *)rho\(k\) = ([^\n]*p1d\(k\)[^\n]*t1d\(k\)[^\n]*qv1d\(k\)[^\n]*)\n").search(b, pos)
if not m or b[pos:m.start()].count("\n") > 40:
    sys.exit("ABORT: rho statement not found in the dz1d loop")
ind, rexpr = m.group(1), m.group(2)
rq = rexpr.replace("qv1d(k)+", "max(1.E-10, qv1d(k))+", 1)
if rq == rexpr:
    sys.exit("ABORT: qv1d(k)+ not in the rho expression")
b = (b[:m.end()] + f"{ind}if (present(dm)) then\n"
     f"{ind}   ! width at this inner step's density, as the column routine computes it, so rho*dz stays the host's mass\n"
     f"{ind}   dz1d(k) = dm(i,k,j) / ({rq})\n"
     f"{ind}else\n{ind}   dz1d(k) = dz(i,k,j)\n{ind}endif\n" + b[m.end():])
drv.write_text(a)
mod.write_text(b)
print(f"patched {drv.name}, {mod.name} (M4 every inner step; {ncall} calls; rho = {rexpr.strip()})")
