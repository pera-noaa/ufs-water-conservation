#!/usr/bin/env python3
"""Water-accounting instrumentation for Thompson and SAMF (diagnostic builds only, not a fix).
Usage: python3 instrument_wb.py <ufs_model.fd>      (v1 snapshot layout; works with or without fixes A-C applied)
Thompson column routine, every column, all in the ENTRY-density frame (rho0*dzq = host dry-air layer mass), kg/m2,
summed over columns on each rank (unweighted); printed by mp_thompson_finalize as
  WBT  1 entry clip | 2 precipitation | 3 source/sink stage | 4 condensation/evaporation stage
       5 sedimentation stage incl. precipitation | 6 final clips | 7 total (1+3+4+5+6) | 8 qv floor (source)
       9 negatives zeroed (source) | 10 tiny positives zeroed (loss) | 11 unused | 12 columns
SAMF deep/shallow negative-vapour borrowing, per convecting column: WBNEGD / WBNEGS
       1 negative vapour borrowed (kg/m2, summed) | 2 columns that needed it | 3 convecting columns | 4 positive vapour in
       the transport layers (kg/m2, summed)
Every anchor must match exactly once, else nothing is written."""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics"
edits = {}


def sub(path, old, new, regex=False):
    s = edits.get(path) or path.read_text()
    if regex:
        n = len(re.findall(old, s))
        if n != 1:
            sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old[:60]!r}")
        s = re.sub(old, lambda m: new(m), s)
    else:
        n = s.count(old)
        if n != 1:
            sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
        s = s.replace(old, new)
    edits[path] = s


SUMQ = "(qv1d(k)+qc1d(k)+qi1d(k)+qr1d(k)+qs1d(k)+qg1d(k))"
SUMT = "(qvten(k)+qcten(k)+qiten(k)+qrten(k)+qsten(k)+qgten(k))"

m = root / "MP/Thompson/module_mp_thompson.F90"
sub(m, "      IMPLICIT NONE\n\n      LOGICAL, PARAMETER, PRIVATE:: iiwarm = .false.\n",
    "      IMPLICIT NONE\n\n      REAL(KIND=8), PUBLIC, SAVE:: wbt(12) = 0.0D0\n"
    "      LOGICAL, PARAMETER, PRIVATE:: iiwarm = .false.\n")
sub(m, r"      REAL:: dtsave, odts, odt, odzq, hgt_agl, SR(, rhon)?\n",
    lambda mm: mm.group(0) + "      REAL(KIND=8):: wb_w0, wb_wa, wb_w1, wb_ta, wb_tb, wb_tc, wb_ppt\n"
                             "      REAL:: wb_x, wb_rho(kts:kte)\n", regex=True)
sub(m, "!> - Put column of data into local arrays.\n",
    "!> - Put column of data into local arrays.\n"
    "      do k = kts, kte\n"
    "         wb_rho(k) = 0.622*p1d(k)/(R*t1d(k)*(MAX(1.E-10, qv1d(k))+0.622))\n"
    "      enddo\n"
    "      wb_w0 = 0.0D0\n"
    f"      do k = kts, kte\n         wb_w0 = wb_w0 + {SUMQ}*wb_rho(k)*dzq(k)\n      enddo\n")
sub(m, "      if (no_micro) return\n",
    "      wb_wa = 0.0D0\n"
    f"      do k = kts, kte\n         wb_wa = wb_wa + {SUMQ}*wb_rho(k)*dzq(k)\n      enddo\n"
    "      wbt(1) = wbt(1) + (wb_wa - wb_w0)\n"
    "      wbt(12) = wbt(12) + 1.0D0\n"
    "      if (no_micro) return\n")
for anchor, var in (("!> - Update variables for TAU+1 before condensation & sedimention.\n", "wb_ta"),
                    ("!>  - Sedimentation of mixing ratio is the integral of v(D)*m(D)*N(D)*dD,\n", "wb_tb")):
    sub(m, anchor, anchor + f"      {var} = 0.0D0\n"
        f"      do k = kts, kte\n         {var} = {var} + {SUMT}*DT*wb_rho(k)*dzq(k)\n      enddo\n")
clip = "".join(
    f"         wb_x = {q}1d(k) + {q}ten(k)*DT\n"
    f"         if (wb_x .lt. 0.) wbt(9) = wbt(9) - wb_x*wb_rho(k)*dzq(k)\n"
    f"         if (wb_x .ge. 0. .and. wb_x .le. R1) wbt(10) = wbt(10) + wb_x*wb_rho(k)*dzq(k)\n"
    for q in ("qc", "qi", "qr", "qs", "qg"))
sub(m, "!> - All tendencies computed, apply and pass back final values to parent.\n",
    "!> - All tendencies computed, apply and pass back final values to parent.\n"
    "      wb_tc = 0.0D0\n"
    f"      do k = kts, kte\n         wb_tc = wb_tc + {SUMT}*DT*wb_rho(k)*dzq(k)\n"
    "         wbt(8) = wbt(8) + MAX(0., 1.E-10 - (qv1d(k)+qvten(k)*DT))*wb_rho(k)*dzq(k)\n"
    + clip + "      enddo\n"
    "      wb_ppt = pptrain + pptsnow + pptgraul + pptice\n")
sub(m, "! Diagnostics\n      calculate_extended_diagnostics: if (ext_diag) then\n",
    "      wb_w1 = 0.0D0\n"
    f"      do k = kts, kte\n         wb_w1 = wb_w1 + {SUMQ}*wb_rho(k)*dzq(k)\n      enddo\n"
    "      wbt(2) = wbt(2) + wb_ppt\n"
    "      wbt(3) = wbt(3) + wb_ta\n"
    "      wbt(4) = wbt(4) + (wb_tb - wb_ta)\n"
    "      wbt(5) = wbt(5) + (wb_tc - wb_tb) + wb_ppt\n"
    "      wbt(6) = wbt(6) + (wb_w1 - wb_wa) - wb_tc\n"
    "      wbt(7) = wbt(7) + (wb_w1 - wb_w0) + wb_ppt\n"
    "! Diagnostics\n      calculate_extended_diagnostics: if (ext_diag) then\n")

d = root / "MP/Thompson/mp_thompson.F90"
sub(d, "      subroutine mp_thompson_finalize(errmsg, errflg)\n\n         implicit none\n",
    "      subroutine mp_thompson_finalize(errmsg, errflg)\n\n"
    "         use module_mp_thompson, only: wbt\n"
    "         use samfdeepcnv, only: wbneg_d => wbneg\n"
    "         use samfshalcnv, only: wbneg_s => wbneg\n"
    "         implicit none\n")
sub(d, "         if (.not.is_initialized) return\n\n         call thompson_finalize()\n",
    "         if (.not.is_initialized) return\n\n"
    "         write(*,'(a,12es17.9)') 'WBT ', wbt\n"
    "         write(*,'(a,4es17.9)') 'WBNEGD ', wbneg_d\n"
    "         write(*,'(a,4es17.9)') 'WBNEGS ', wbneg_s\n"
    "         call thompson_finalize()\n")

NEG = ("      do i = 1,im\n"
       "        if(cnvflg(i)) then\n"
       "          wbneg(3) = wbneg(3) + 1.d0\n"
       "          wbneg(4) = wbneg(4) + tsump(i)\n"
       "          if(tsumn(i) < 0.) then\n"
       "            wbneg(1) = wbneg(1) - tsumn(i)\n"
       "            wbneg(2) = wbneg(2) + 1.d0\n"
       "          endif\n"
       "        endif\n"
       "      enddo\n")
for f in ("samfdeepcnv.f", "samfshalcnv.f"):
    p = root / "CONV/SAMF" / f
    sub(p, "\n      contains\n", "\n      real(kind=8), save :: wbneg(4) = 0.d0\n\n      contains\n")
    sub(p, r"if\(q1\(i,k\) > 0\.\) tsump\(i\) = tsump\(i\) \+ tem\n(?: *endif\n)+ *enddo\n *enddo\n",
        lambda mm: mm.group(0) + NEG, regex=True)

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWB").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
