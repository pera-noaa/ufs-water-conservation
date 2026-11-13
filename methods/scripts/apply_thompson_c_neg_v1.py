#!/usr/bin/env python3
"""The diff 03 completion (cloud substepping + snow-gain cap; apply_thompson_c_neg_patch.py 'both') for the v1 snapshot's
module_mp_thompson.F90, which has C1/C2 applied. Usage: python3 apply_thompson_c_neg_v1.py <module_mp_thompson.F90>
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

f = Path(sys.argv[1])
s = f.read_text()


def sub(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"ABORT {f.name}: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    s = s.replace(old, new)


sub("      INTEGER, DIMENSION(5):: ksed1\n", "      INTEGER, DIMENSION(5):: ksed1\n      REAL:: dtsed\n      INTEGER:: nstepc\n")
sub("          prr_rcg(k) = prr_rcg(k) * ratio\n         endif\n",
    "          prr_rcg(k) = prr_rcg(k) * ratio\n         endif\n"
    "         ! snow cannot gain more from rain-snow collection than the rain loses to it\n"
    "         if (temp(k).lt.T_0 .and. prs_rcs(k).gt.-prr_rcs(k)) prs_rcs(k) = -prr_rcs(k)\n")
sub("""      if (ANY(L_qc .eqv. .true.)) then
      do k = kte, kts, -1
         sed_c(k) = vtck(k)*rc(k)
         sed_n(k) = vtnck(k)*nc(k)
      enddo
      do k = ksed1(5), kts, -1
         odzq = 1./dzq(k)
         orho = 1./rho(k)
         qcten(k) = qcten(k) + (sed_c(k+1)-sed_c(k)) *odzq*orho
         ncten(k) = ncten(k) + (sed_n(k+1)-sed_n(k)) *odzq*orho
         rc(k) = MAX(R1, rc(k) + (sed_c(k+1)-sed_c(k)) *odzq*DT)
         nc(k) = MAX(10., nc(k) + (sed_n(k+1)-sed_n(k)) *odzq*DT)
      enddo
      ! cloud water settling out of the lowest layer reaches the surface: count it as precipitation
      if (ksed1(5) .ge. kts) pptrain = pptrain + sed_c(kts)*DT
      endif
""", """      if (ANY(L_qc .eqv. .true.)) then
      ! substeps keep each layer's outflow within its content (Courant number <= 1), as for the other species
      nstepc = 1
      do k = ksed1(5), kts, -1
         if (vtck(k) .gt. 0.) nstepc = MAX(nstepc, INT(DT*vtck(k)/dzq(k) + 1.))
      enddo
      onstep(5) = 1./REAL(nstepc)
      dtsed = DT*onstep(5)
      do n = 1, nstepc
      do k = kte, kts, -1
         sed_c(k) = vtck(k)*rc(k)
         sed_n(k) = vtnck(k)*nc(k)
      enddo
      do k = ksed1(5), kts, -1
         odzq = 1./dzq(k)
         orho = onstep(5)/rho(k)
         qcten(k) = qcten(k) + (sed_c(k+1)-sed_c(k)) *odzq*orho
         ncten(k) = ncten(k) + (sed_n(k+1)-sed_n(k)) *odzq*orho
         rc(k) = MAX(R1, rc(k) + (sed_c(k+1)-sed_c(k)) *odzq*dtsed)
         nc(k) = MAX(10., nc(k) + (sed_n(k+1)-sed_n(k)) *odzq*dtsed)
      enddo
      ! cloud water settling out of the lowest layer reaches the surface: count it as precipitation
      if (ksed1(5) .ge. kts) pptrain = pptrain + sed_c(kts)*dtsed
      enddo
      endif
""")
f.with_suffix(f.suffix + ".preCNEG").write_text(f.read_text())
f.write_text(s)
print(f"patched {f} (diff 03 completion, v1)")
