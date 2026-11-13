#!/usr/bin/env python3
"""Candidate fixes for Thompson's negative hydrometeors (module_mp_thompson.F90, with or without the instrument_wb_neg_stages.py meters).
Usage: python3 fix_thompson_neg_csed_rcs.py <ufs-weather-model> csed|rcs|both|rcsnoise [--force1]
  csed: cloud-water sedimentation is substepped so no layer's outflow exceeds its content (Courant number <= 1), the
        convention already used for rain, ice, snow and graupel; one substep reproduces the original arithmetic.
        --force1 pins the substep count at 1 (a control that must reproduce the unfixed answers bit for bit).
  rcs:  below T_0 the snow gain from rain-snow collection is capped at the rain lost to it (applied after the rain
        limiter, before the snow limiter), so diff 03's closure prg_rcs = -(prr_rcs + prs_rcs) cannot go negative.
  rcsnoise: control for rcs, not a fix: where rcs would cap, prs_rcs is scaled by 1+1e-12 instead (same seed locations,
        no physical change), to size the chaotic spread of the 24 h precipitation difference.
Every anchor must match exactly once, else nothing is written."""
import re
import sys
from pathlib import Path

m = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90"
what = sys.argv[2]
force1 = "--force1" in sys.argv[3:]
s = m.read_text()


def sub(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {m.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    s = s.replace(old, new)


if what in ("csed", "both"):
    sub("      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n",
        "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n      real(wp) :: dtc\n      integer :: nstepc\n")
    pat = re.compile(
        r"(      if \(ANY\(L_qc \.eqv\. \.true\.\)\) then\n)"
        r"(         do k = kte, kts, -1\n            sed_c\(k\) = vtck\(k\)\*rc\(k\)\n)"
        r"(?P<met>(?:            if \(k \.le\. ksed1\(5\).*\n(?:               wbt.*\n)+            endif\n)?)"
        r"(            sed_n\(k\) = vtnck\(k\)\*nc\(k\)\n         enddo\n"
        r"         do k = ksed1\(5\), kts, -1\n            odzq = 1\./dzq\(k\)\n)"
        r"            orho = 1\./rho\(k\)\n"
        r"(            qcten\(k\) = qcten\(k\) \+ \(sed_c\(k\+1\)-sed_c\(k\)\) \*odzq\*orho\n"
        r"            ncten\(k\) = ncten\(k\) \+ \(sed_n\(k\+1\)-sed_n\(k\)\) \*odzq\*orho\n)"
        r"            rc\(k\) = max\(R1, rc\(k\) \+ \(sed_c\(k\+1\)-sed_c\(k\)\) \*odzq\*DT\)\n"
        r"            nc\(k\) = max\(10\., nc\(k\) \+ \(sed_n\(k\+1\)-sed_n\(k\)\) \*odzq\*DT\)\n"
        r"         enddo\n"
        r"(         ! cloud water settling out of the lowest layer reaches the surface: count it as precipitation\n)"
        r"         if \(ksed1\(5\) \.ge\. kts\) pptrain = pptrain \+ sed_c\(kts\)\*DT\n"
        r"(?P<m76>(?:         if \(ksed1\(5\) \.ge\. kts\) wbt\(76\) = wbt\(76\) \+ sed_c\(kts\)\n)?)"
        r"      endif\n")
    hits = pat.findall(s)
    if len(hits) != 1:
        sys.exit(f"ABORT {m.name}: cloud sedimentation block matched {len(hits)} times")
    mm = pat.search(s)
    met = mm.group("met").replace("            if (k .le. ksed1(5)", "            if (n .eq. 1 .and. k .le. ksed1(5)")
    nset = ("         nstepc = 1\n" if force1 else
            "         nstepc = 1\n"
            "         do k = ksed1(5), kts, -1\n"
            "            if (vtck(k) .gt. 0.) nstepc = max(nstepc, int(DT*vtck(k)/dzq(k) + 1.))\n"
            "         enddo\n")
    new = (mm.group(1)
           + "         ! substeps keep each layer's outflow within its content (Courant number <= 1), as for the other species\n"
           + nset
           + "         onstep(5) = 1./real(nstepc, kind=wp)\n"
           + "         dtc = DT*onstep(5)\n"
           + "         do n = 1, nstepc\n"
           + mm.group(2) + met + mm.group(4)
           + "            orho = onstep(5)/rho(k)\n"
           + mm.group(5)
           + "            rc(k) = max(R1, rc(k) + (sed_c(k+1)-sed_c(k)) *odzq*dtc)\n"
           + "            nc(k) = max(10., nc(k) + (sed_n(k+1)-sed_n(k)) *odzq*dtc)\n"
           + "         enddo\n"
           + mm.group(6)
           + "         if (ksed1(5) .ge. kts) pptrain = pptrain + sed_c(kts)*dtc\n"
           + ("         if (ksed1(5) .ge. kts) wbt(76) = wbt(76) + sed_c(kts)*onstep(5)\n" if mm.group("m76") else "")
           + "         enddo\n"
           + "      endif\n")
    # indent the substep body one level
    head, body_tail = new.split("         do n = 1, nstepc\n")
    body, tail = body_tail.rsplit("         enddo\n      endif\n", 1)
    body = "".join("   " + ln if ln.strip() else ln for ln in body.splitlines(True))
    new = head + "         do n = 1, nstepc\n" + body + "         enddo\n      endif\n"
    s = s[:mm.start()] + new + s[mm.end():]
if what in ("rcs", "both"):
    sub("            prr_rcg(k) = prr_rcg(k) * ratio\n         endif\n",
        "            prr_rcg(k) = prr_rcg(k) * ratio\n         endif\n"
        "         ! snow cannot gain more from rain-snow collection than the rain loses to it\n"
        "         if (temp(k).lt.T_0 .and. prs_rcs(k).gt.-prr_rcs(k)) prs_rcs(k) = -prr_rcs(k)\n")
if what == "rcsnoise":
    sub("            prr_rcg(k) = prr_rcg(k) * ratio\n         endif\n",
        "            prr_rcg(k) = prr_rcg(k) * ratio\n         endif\n"
        "         if (temp(k).lt.T_0 .and. prs_rcs(k).gt.-prr_rcs(k)) prs_rcs(k) = prs_rcs(k)*(1.0_wp+1.0e-12_wp)\n")
m.with_suffix(m.suffix + ".preNEG").write_text(m.read_text())
m.write_text(s)
print(f"fixed ({what}{', force1' if force1 else ''}) {m}")
