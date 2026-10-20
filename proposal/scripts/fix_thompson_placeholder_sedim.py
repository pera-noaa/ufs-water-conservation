#!/usr/bin/env python3
"""Thompson flux-form sedimentation: the R1 placeholder is not transported as mass.

Layers without a species hold rX(k) = R1 and inherit the fall speed of the layer above, so
sed_X(k) = vt*R1 settles the placeholder (with M2, a frozen trace reaches the surface under any
column with ice/snow aloft). As M5 (diff 16) does for semi-Lagrangian rain/graupel: start floored
layers from their actual content, and do not re-floor the mass density inside the substep loop.
Applies to the flux-form ice, snow, rain and graupel branches. Numbers (R2 floors) are untouched.

usage: fix_thompson_placeholder_sedim.py <module_mp_thompson.F90>
Idempotent: every edit's anchor must match exactly once (or its result exactly once), else abort.
"""
import sys

def init_block(ind, r, q, name):
    return (f"{ind}! floored layers carry their actual {name}, so the R1 placeholder is not sedimented as mass\n"
            f"{ind}do k = kts, kte\n"
            f"{ind}   if ({r}(k) .le. R1) {r}(k) = max(0._wp, ({q}1d(k) + {q}ten(k)*DT)*rho(k))\n"
            f"{ind}enddo\n")


EDITS = [
    # rain, flux-form branch (sedi_semi = .false.)
    ("rain init",
     "         nstep = nint(1./onstep(1))\n\n         if(.not. sedi_semi) then\n",
     "         nstep = nint(1./onstep(1))\n\n         if(.not. sedi_semi) then\n"
     + init_block("            ", "rr", "qr", "rain")),
    ("rain top",
     "               rr(k) = max(R1, rr(k) - sed_r(k)*odzq*DT*onstep(1))\n",
     "               rr(k) = max(0._wp, rr(k) - sed_r(k)*odzq*DT*onstep(1))\n"),
    ("rain loop",
     "                  rr(k) = max(R1, rr(k) + (sed_r(k+1)-sed_r(k)) &\n",
     "                  rr(k) = max(0._wp, rr(k) + (sed_r(k+1)-sed_r(k)) &\n"),
    # cloud ice
    ("ice init",
     "         nstep = nint(1./onstep(2))\n         do n = 1, nstep\n",
     "         nstep = nint(1./onstep(2))\n" + init_block("         ", "ri", "qi", "ice")
     + "         do n = 1, nstep\n"),
    ("ice top",
     "            ri(k) = max(R1, ri(k) - sed_i(k)*odzq*DT*onstep(2))\n",
     "            ri(k) = max(0._wp, ri(k) - sed_i(k)*odzq*DT*onstep(2))\n"),
    ("ice loop",
     "               ri(k) = max(R1, ri(k) + (sed_i(k+1)-sed_i(k)) &\n",
     "               ri(k) = max(0._wp, ri(k) + (sed_i(k+1)-sed_i(k)) &\n"),
    # snow
    ("snow init",
     "         nstep = nint(1./onstep(3))\n         do n = 1, nstep\n",
     "         nstep = nint(1./onstep(3))\n" + init_block("         ", "rs", "qs", "snow")
     + "         do n = 1, nstep\n"),
    ("snow top",
     "            rs(k) = max(R1, rs(k) - sed_s(k)*odzq*DT*onstep(3))\n",
     "            rs(k) = max(0._wp, rs(k) - sed_s(k)*odzq*DT*onstep(3))\n"),
    ("snow loop",
     "               rs(k) = max(R1, rs(k) + (sed_s(k+1)-sed_s(k)) &\n",
     "               rs(k) = max(0._wp, rs(k) + (sed_s(k+1)-sed_s(k)) &\n"),
    # graupel, flux-form branch (sedi_semi = .false.)
    ("graupel init",
     "         nstep = nint(1./onstep(4))\n         if(.not. sedi_semi) then \n",
     "         nstep = nint(1./onstep(4))\n         if(.not. sedi_semi) then \n"
     + init_block("            ", "rg", "qg", "graupel")),
    ("graupel top",
     "               rg(k) = max(R1, rg(k) - sed_g(k)*odzq*DT*onstep(4))\n",
     "               rg(k) = max(0._wp, rg(k) - sed_g(k)*odzq*DT*onstep(4))\n"),
    ("graupel loop",
     "                  rg(k) = max(R1, rg(k) + (sed_g(k+1)-sed_g(k)) &\n",
     "                  rg(k) = max(0._wp, rg(k) + (sed_g(k+1)-sed_g(k)) &\n"),
]


def main():
    fn = sys.argv[1]
    src = open(fn).read()
    out, applied, already = src, 0, 0
    for name, old, new in EDITS:
        n_new = out.count(new)
        if n_new == 1:
            already += 1
            continue
        if n_new > 1:
            sys.exit(f"ABORT {name}: result matches {n_new} times")
        n_old = out.count(old)
        if n_old != 1:
            sys.exit(f"ABORT {name}: anchor matches {n_old} times")
        out = out.replace(old, new)
        applied += 1
    if applied:
        open(fn, "w").write(out)
    print(f"{fn}: {applied} applied, {already} already present")


if __name__ == "__main__":
    main()
