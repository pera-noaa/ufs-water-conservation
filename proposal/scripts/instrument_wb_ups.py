#!/usr/bin/env python3
"""Thompson column-routine water meter by stage (WBT) for the upstream layout (ccpp-physics ufs/dev); port of
instrument_wb.py with finer stages. Diagnostic builds only; apply after instrument_wb_phys_ups.py and
instrument_wb_ep_ups.py. Usage: python3 instrument_wb_ups.py <ufs-weather-model>
All in the entry-density frame (rho0*dzq = host dry-air layer mass), kg/m2, summed over columns on each rank:
  WBT kdt | 1 entry stage | 2 precipitation | 3 source/sink stage | 4 condensation/evaporation stage
          | 5 sedimentation stage incl. precipitation (= 14..19) | 6 final stage | 7 total, all columns
          | 8 qv floor at exit (source) | 9 negatives left before the exit exchange | 10 tiny positives (<=R1) before it
          | 11 entry: 0 < q <= R1 zeroed (loss, >0) | 12 columns | 13 entry: q < 0 zeroed (source, >0)
          | 14..19 sedimentation by block: rain, cloud water, ice, snow, graupel, instant melt/freeze
          | 20..22 semi_lagrange_sedim mass calls: 20 floor max(qn,R1) raise | 21 input <= R1 excluded from transport
          |        | 22 transport non-conservation (sum qn dz + precip - sum qq dz); SL residual = 20 - 21 + 22
          | 23 entry: (layer, species) zeroed with 0 < q <= R1 (count) | 24 no_micro columns | 25 max |column total|
          | 26..30 entry tiny-positive loss by species: qc, qi, qr, qs, qg
cumulative through kdt, printed at each step change from GFS_physics_post and from mp_thompson_final.
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
m = root / "MP/Thompson/module_mp_thompson.F90"
d = root / "MP/Thompson/mp_thompson.F90"
post = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


NW = 30
SUMQ = "(qv1d(k)+qc1d(k)+qi1d(k)+qr1d(k)+qs1d(k)+qg1d(k))"
SUMT = "(qvten(k)+qcten(k)+qiten(k)+qrten(k)+qsten(k)+qgten(k))"
PPT = "(pptrain+pptsnow+pptgraul+pptice)"


def snap(slot):
    return ("      wb_s2 = " + PPT + "\n"
            f"      do k = kts, kte\n         wb_s2 = wb_s2 + {SUMT}*DT*wb_rho(k)*dzq(k)\n      enddo\n"
            f"      wbt({slot}) = wbt({slot}) + (wb_s2 - wb_s1)\n"
            "      wb_s1 = wb_s2\n")


sub(m, "   implicit none\n\n   logical, parameter, private :: iiwarm = .false.\n",
    "   implicit none\n\n"
    f"   real(kind=8), public, save :: wbt({NW}) = 0.0d0\n"
    "   logical, parameter, private :: iiwarm = .false.\n")
sub(m, "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n",
    "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n"
    "      real(kind=8) :: wb_w0, wb_wa, wb_w1, wb_ta, wb_tb, wb_tc, wb_ppt, wb_s1, wb_s2\n"
    "      real(wp) :: wb_x, wb_rho(kts:kte)\n")
# entry
ent = "".join(
    f"         if ({q}1d(k) .gt. 0. .and. {q}1d(k) .le. R1) then\n"
    f"            wbt(11) = wbt(11) + {q}1d(k)*wb_rho(k)*dzq(k)\n"
    f"            wbt({26 + j}) = wbt({26 + j}) + {q}1d(k)*wb_rho(k)*dzq(k)\n"
    "            wbt(23) = wbt(23) + 1.0D0\n"
    "         endif\n"
    f"         if ({q}1d(k) .lt. 0.) wbt(13) = wbt(13) - {q}1d(k)*wb_rho(k)*dzq(k)\n"
    for j, q in enumerate(("qc", "qi", "qr", "qs", "qg")))
sub(m, "!> - Put column of data into local arrays.\n",
    "!> - Put column of data into local arrays.\n"
    "      wb_w0 = 0.0D0\n"
    "      do k = kts, kte\n"
    "         wb_rho(k) = RoverRv*p1d(k) / (R*t1d(k)*(max(1.E-10, qv1d(k))+RoverRv))\n"
    f"         wb_w0 = wb_w0 + {SUMQ}*wb_rho(k)*dzq(k)\n"
    + ent + "      enddo\n")
sub(m, "      if (no_micro) return\n",
    "      wb_wa = 0.0D0\n"
    f"      do k = kts, kte\n         wb_wa = wb_wa + {SUMQ}*wb_rho(k)*dzq(k)\n      enddo\n"
    "      wbt(1) = wbt(1) + (wb_wa - wb_w0)\n"
    "      wbt(12) = wbt(12) + 1.0D0\n"
    "      if (no_micro) then\n"
    "         wbt(7) = wbt(7) + (wb_wa - wb_w0)\n"
    "         wbt(24) = wbt(24) + 1.0D0\n"
    "         wbt(25) = max(wbt(25), abs(wb_wa - wb_w0))\n"
    "      endif\n"
    "      if (no_micro) return\n")
sub(m, "!> - Update variables for TAU+1 before condensation & sedimention.\n",
    "!> - Update variables for TAU+1 before condensation & sedimention.\n"
    f"      wb_ta = 0.0D0\n      do k = kts, kte\n         wb_ta = wb_ta + {SUMT}*DT*wb_rho(k)*dzq(k)\n      enddo\n")
sub(m, "!>  - Sedimentation of mixing ratio is the integral of v(D)*m(D)*N(D)*dD,\n",
    "!>  - Sedimentation of mixing ratio is the integral of v(D)*m(D)*N(D)*dD,\n"
    f"      wb_tb = 0.0D0\n      do k = kts, kte\n         wb_tb = wb_tb + {SUMT}*DT*wb_rho(k)*dzq(k)\n      enddo\n"
    "      wb_s1 = wb_tb + " + PPT + "\n")
for anchor, slot in (
        ("      if (ANY(L_qc .eqv. .true.)) then\n         do k = kte, kts, -1\n            sed_c(k) = vtck(k)*rc(k)\n", 14),
        ("      if (ANY(L_qi .eqv. .true.)) then\n         nstep = nint(1./onstep(2))\n", 15),
        ("      if (ANY(L_qs .eqv. .true.)) then\n         nstep = nint(1./onstep(3))\n", 16),
        ("      if (ANY(L_qg .eqv. .true.)) then\n         nstep = nint(1./onstep(4))\n", 17),
        ("!> - Instantly melt any cloud ice into cloud water if above 0C and\n", 18)):
    sub(m, anchor, snap(slot) + anchor)
clip = "".join(
    f"         wb_x = {q}1d(k) + {q}ten(k)*DT\n"
    f"         if (wb_x .lt. 0.) wbt(9) = wbt(9) - wb_x*wb_rho(k)*dzq(k)\n"
    f"         if (wb_x .ge. 0. .and. wb_x .le. R1) wbt(10) = wbt(10) + wb_x*wb_rho(k)*dzq(k)\n"
    for q in ("qc", "qi", "qr", "qs", "qg"))
sub(m, "!> - All tendencies computed, apply and pass back final values to parent.\n",
    "!> - All tendencies computed, apply and pass back final values to parent.\n"
    + snap(19) +
    "      wb_tc = 0.0D0\n"
    f"      do k = kts, kte\n         wb_tc = wb_tc + {SUMT}*DT*wb_rho(k)*dzq(k)\n"
    "         wbt(8) = wbt(8) + MAX(0., 1.E-10 - (qv1d(k)+qvten(k)*DT))*wb_rho(k)*dzq(k)\n"
    + clip + "      enddo\n"
    "      wb_ppt = " + PPT + "\n")
sub(m, "! Diagnostics\n      calculate_extended_diagnostics: if (ext_diag) then\n",
    "      wb_w1 = 0.0D0\n"
    f"      do k = kts, kte\n         wb_w1 = wb_w1 + {SUMQ}*wb_rho(k)*dzq(k)\n      enddo\n"
    "      wbt(2) = wbt(2) + wb_ppt\n"
    "      wbt(3) = wbt(3) + wb_ta\n"
    "      wbt(4) = wbt(4) + (wb_tb - wb_ta)\n"
    "      wbt(5) = wbt(5) + (wb_tc - wb_tb) + wb_ppt\n"
    "      wbt(6) = wbt(6) + (wb_w1 - wb_wa) - wb_tc\n"
    "      wbt(7) = wbt(7) + (wb_w1 - wb_w0) + wb_ppt\n"
    "      wbt(25) = max(wbt(25), abs((wb_w1 - wb_w0) + wb_ppt))\n"
    "! Diagnostics\n      calculate_extended_diagnostics: if (ext_diag) then\n")
# semi-Lagrangian sedimentation, mass calls only (number calls pass R2 = 1e-6 as the floor)
sub(m, "! replace the new values\n      rql(:) = max(qn(:),R1)\n",
    "      if (R1 .lt. 1.e-9_wp) then\n"
    "        do k = 1, km\n"
    "          wbt(20) = wbt(20) + (max(qn(k),R1) - qn(k))*dz(k)\n"
    "          wbt(21) = wbt(21) + (rql(k) - qq(k))*dz(k)\n"
    "          wbt(22) = wbt(22) + (qn(k) - qq(k))*dz(k)\n"
    "        enddo\n"
    "        wbt(22) = wbt(22) + precip\n"
    "      endif\n"
    "! replace the new values\n      rql(:) = max(qn(:),R1)\n")

# prints
sub(post, "con_g, errmsg, errflg)\n", "con_g, errmsg, errflg)\n    use module_mp_thompson, only: wbt\n")
sub(post, "    if (kdt /= wbp_kdt) then\n",
    "    if (kdt /= wbp_kdt) then\n"
    f"       write(*,'(a,i7,{NW}es17.9)') 'WBT ', kdt, wbt\n")
sub(d, "         use GFS_physics_post, only: wbp, wbp_kdt, wbq\n",
    "         use GFS_physics_post, only: wbp, wbp_kdt, wbq\n         use module_mp_thompson, only: wbt\n")
sub(d, "         write(*,'(a,i7,7es24.15)') 'WBQ ', wbp_kdt, wbq\n",
    "         write(*,'(a,i7,7es24.15)') 'WBQ ', wbp_kdt, wbq\n"
    f"         write(*,'(a,i7,{NW}es17.9)') 'WBT ', wbp_kdt, wbt\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBT").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
