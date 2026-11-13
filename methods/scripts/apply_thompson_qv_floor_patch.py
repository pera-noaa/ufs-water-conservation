#!/usr/bin/env python3
"""Thompson's end-of-step vapour floor refills instead of creating water (folded into diff 07, M1): vapour left below
1.E-10 is refilled first from the layer's condensate (with its latent heat; number concentrations scaled with mass),
then from the column's other vapour (mass-weighted, as column borrowing); only a column with no vapour to spare is still
floored. Usage: python3 apply_thompson_qv_floor_patch.py <module_mp_thompson.F90> [--force-floor X] (ufs/dev or v1,
with M1 applied; --force-floor sets the floor to X for a forced test build). Every anchor must match exactly once."""
import re
import sys
from pathlib import Path

f = Path(sys.argv[1])
floor = sys.argv[sys.argv.index("--force-floor") + 1] if "--force-floor" in sys.argv else "1.E-10"
s = f.read_text()
ups = "real(wp) :: dtcfl, rainsfc, graulsfc" in s
K = "_wp" if ups else ""


def sub(pat, rep, flags=0):
    global s
    n = len(re.findall(pat, s, flags))
    if n != 1:
        sys.exit(f"ABORT {f.name}: expected 1 match, found {n}: {pat[:70]!r}")
    s = re.sub(pat, lambda m: rep, s, flags=flags)


if ups:
    sub(r"      real\(wp\) :: dtcfl, rainsfc, graulsfc\n",
        "      real(wp) :: dtcfl, rainsfc, graulsfc\n      real(wp) :: xdef, xavl, xcnd, frc\n")
else:
    sub(r"      REAL :: dtcfl,rainsfc,graulsfc\n", "      REAL :: dtcfl,rainsfc,graulsfc\n      REAL :: xdef, xavl, xcnd, frc\n")
sub(r"qv1d\(k\) = max\(1\.E-10, qv1d\(k\) \+ qvten\(k\)\*DT\)", "qv1d(k) = qv1d(k) + qvten(k)*DT", re.I)
block = f"""
!..Vapour left below the floor is refilled, not created: first from the layer's
!.. condensate, with its latent heat, then from the column's other vapour.
      do k = kts, kte
         if (qv1d(k) .lt. {floor}) then
            xcnd = qc1d(k) + qr1d(k) + qi1d(k) + qs1d(k) + qg1d(k)
            if (xcnd .gt. 0.) then
               frc = min(1.{K}, ({floor} - qv1d(k))/xcnd)
               t1d(k) = t1d(k) - frc*ocp(k)*(1-IFDRY)                           &
                      * (lvap(k)*(qc1d(k)+qr1d(k)) + lsub*(qi1d(k)+qs1d(k)+qg1d(k)))
               qv1d(k) = qv1d(k) + frc*xcnd
               qc1d(k) = qc1d(k)*(1.-frc)
               nc1d(k) = nc1d(k)*(1.-frc)
               qr1d(k) = qr1d(k)*(1.-frc)
               nr1d(k) = nr1d(k)*(1.-frc)
               qi1d(k) = qi1d(k)*(1.-frc)
               ni1d(k) = ni1d(k)*(1.-frc)
               qs1d(k) = qs1d(k)*(1.-frc)
               qg1d(k) = qg1d(k)*(1.-frc)
            endif
         endif
      enddo
      xdef = 0.
      xavl = 0.
      do k = kts, kte
         xdef = xdef + max({floor} - qv1d(k), 0.{K})*rho(k)*dzq(k)
         xavl = xavl + max(qv1d(k) - {floor}, 0.{K})*rho(k)*dzq(k)
      enddo
      if (xdef .gt. 0. .and. xavl .gt. 0.) then
         frc = min(1.{K}, xdef/xavl)
         xcnd = min(1.{K}, xavl/xdef)
         do k = kts, kte
            if (qv1d(k) .lt. {floor}) then
               qv1d(k) = qv1d(k) + ({floor} - qv1d(k))*xcnd
            else
               qv1d(k) = qv1d(k) - (qv1d(k) - {floor})*frc
            endif
         enddo
      endif
!..Only a column with no vapour to spare is still floored.
      do k = kts, kte
         qv1d(k) = max({floor}, qv1d(k))
      enddo
"""
sub(r"         if \(qg1d\(k\) \.le\. R1\) qg1d\(k\) = 0\.0\n      enddo\n",
    "         if (qg1d(k) .le. R1) qg1d(k) = 0.0\n      enddo\n" + block)
f.with_suffix(f.suffix + ".preQVF").write_text(f.read_text())
f.write_text(s)
print(f"patched {f} (vapour floor refills{', floor ' + floor if floor != '1.E-10' else ''})")
