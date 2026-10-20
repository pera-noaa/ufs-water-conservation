#!/usr/bin/env python3
"""The two parts of reference fix 0003 (C1/C2) that the first WRF/MPAS ports lacked: substep Thompson's cloud
sedimentation with the Courant rule of the other species (a layer cannot lose more cloud than it holds), and below 0 C
cap the snow gain from rain-snow collection at the rain lost to it (so the re-closed prg_rcs cannot go negative).
Usage: python3 port_thompson_c1c2_amend.py <module_mp_thompson.F>  (WRF phys/ or MPAS physics_wrf/, after C1-M2)"""
import re
import sys
from pathlib import Path

mp = Path(sys.argv[1])
s = mp.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


# the cap uses the same temperature as this copy's C2 re-closure (twet in WRF, temp in MPAS)
m = re.search(r"if \((\w+)\(k\)\.lt\.T_0\) prg_rcs\(k\) = -\(prr_rcs\(k\) \+ prs_rcs\(k\)\)", s)
if not m:
    sys.exit("ABORT: C2 re-closure not found (apply C1-M2 first)")
tc = m.group(1)
s = one(s, "          prr_rcs(k) = prr_rcs(k) * ratio\n          prr_rcg(k) = prr_rcg(k) * ratio\n         endif\n\n!..Snow conservation.\n",
        "          prr_rcs(k) = prr_rcs(k) * ratio\n          prr_rcg(k) = prr_rcg(k) * ratio\n         endif\n"
        "         ! snow cannot gain more from rain-snow collection than the rain loses to it\n"
        f"         if ({tc}(k).lt.T_0 .and. prs_rcs(k).gt.-prr_rcs(k)) prs_rcs(k) = -prr_rcs(k)\n\n!..Snow conservation.\n",
        "cap")

old = """      if (ANY(L_qc .eqv. .true.)) then
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
"""
new = """      if (ANY(L_qc .eqv. .true.)) then
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
"""
s = one(s, old, new, "cloud sedimentation")
s = one(s, "      REAL, DIMENSION(5):: onstep\n", "      REAL, DIMENSION(5):: onstep\n      REAL:: dtsed\n      INTEGER:: nstepc\n",
        "declarations")
mp.write_text(s)
print(f"patched {mp} (cloud sedimentation substeps; rain-snow cap on {tc})")
