#!/usr/bin/env python3
"""Thompson negative-hydrometeor meter by species and stage (WBT 33..77); apply after instrument_wb_ups_rten.py.
Usage: python3 instrument_wb_neg_stages.py <ufs-weather-model>. Reads state only (no answer change). Slots, kg/m2 in the
entry-density frame (wb_rho*dzq) unless noted, species order c,i,r,s,g, cumulative through kdt like the WBT meters:
  33-37 negative mass after the source/sink stage | 38-42 after cond/evap | 43-47 after sedimentation (before melt/freeze)
  48-52 at exit before the exchange (= slot 9 split) | 53-57 count of negative layers at exit
  58-62 exit negatives in the lowest layer | 63-67 exit negatives with temp >= T_0 | 68 column-steps with any exit negative
  69 max exit negative (kg/kg, max over ranks) | 70 cloud-sed layers with vtck*DT > dzq (count) | 71-75 exit negatives
  below 500 m AGL (layer bottom) | 76 cloud-water surface sedimentation flux sum(sed_c(kts)), kg/m2/s (x DT in the
  report; a product here would be shared with the pptrain update and change its FMA contraction) | 77 cloud-sed overshoot
  sum(max(0, vtck*DT/dzq - 1)*rc*dzq) over layers | 78 graupel loss from prg_rcs < 0 after the diff-03 closure, kg/m2/s
  (x DT in the report) | 79 count of such layers | 80-84 count of exit negatives below -1e-9 kg/kg | 85 qc exit
  negatives over land (lsml == 1). Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
m = root / "MP/Thompson/module_mp_thompson.F90"
d = root / "MP/Thompson/mp_thompson.F90"
post = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_physics_post.F90"
edits = {}
NW = 85
SP = ("qc", "qi", "qr", "qs", "qg")


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


def neg(base):
    return ("      do k = kts, kte\n" + "".join(
        f"         wb_x = {q}1d(k) + {q}ten(k)*DT\n"
        f"         if (wb_x .lt. 0.) wbt({base + j}) = wbt({base + j}) - wb_x*wb_rho(k)*dzq(k)\n"
        for j, q in enumerate(SP)) + "      enddo\n")


exitb = ("      wb_nc = 0\n      wb_z = 0.0D0\n      do k = kts, kte\n" + "".join(
    f"         wb_x = {q}1d(k) + {q}ten(k)*DT\n"
    "         if (wb_x .lt. 0.) then\n"
    f"            wbt({48 + j}) = wbt({48 + j}) - wb_x*wb_rho(k)*dzq(k)\n"
    f"            wbt({53 + j}) = wbt({53 + j}) + 1.0D0\n"
    f"            if (k .eq. kts) wbt({58 + j}) = wbt({58 + j}) - wb_x*wb_rho(k)*dzq(k)\n"
    f"            if (temp(k) .ge. T_0) wbt({63 + j}) = wbt({63 + j}) - wb_x*wb_rho(k)*dzq(k)\n"
    f"            if (wb_z .lt. 500.0D0) wbt({71 + j}) = wbt({71 + j}) - wb_x*wb_rho(k)*dzq(k)\n"
    f"            if (wb_x .lt. -1.e-9) wbt({80 + j}) = wbt({80 + j}) + 1.0D0\n"
    + (f"            if (lsml .eq. 1) wbt(85) = wbt(85) - wb_x*wb_rho(k)*dzq(k)\n" if q == "qc" else "") +
    "            wbt(69) = max(wbt(69), -dble(wb_x))\n"
    "            wb_nc = 1\n"
    "         endif\n" for j, q in enumerate(SP)) +
    "         wb_z = wb_z + dzq(k)\n      enddo\n      wbt(68) = wbt(68) + dble(wb_nc)\n")

sub(m, "   real(kind=8), public, save :: wbt(32) = 0.0d0\n", f"   real(kind=8), public, save :: wbt({NW}) = 0.0d0\n")
sub(m, "      real(wp) :: wb_x, wb_rho(kts:kte)\n",
    "      real(wp) :: wb_x, wb_rho(kts:kte)\n      real(kind=8) :: wb_z\n      integer :: wb_nc\n")
sub(m, "!> - Update variables for TAU+1 before condensation & sedimention.\n",
    "!> - Update variables for TAU+1 before condensation & sedimention.\n" + neg(33))
sub(m, "!>  - Sedimentation of mixing ratio is the integral of v(D)*m(D)*N(D)*dD,\n",
    "!>  - Sedimentation of mixing ratio is the integral of v(D)*m(D)*N(D)*dD,\n" + neg(38))
sub(m, "!> - Instantly melt any cloud ice into cloud water if above 0C and\n",
    neg(43) + "!> - Instantly melt any cloud ice into cloud water if above 0C and\n")
sub(m, "!> - All tendencies computed, apply and pass back final values to parent.\n",
    "!> - All tendencies computed, apply and pass back final values to parent.\n" + exitb)
sub(m, "            sed_c(k) = vtck(k)*rc(k)\n",
    "            sed_c(k) = vtck(k)*rc(k)\n"
    "            if (k .le. ksed1(5) .and. vtck(k)*DT .gt. dzq(k)) then\n"
    "               wbt(70) = wbt(70) + 1.0D0\n"
    "               wbt(77) = wbt(77) + (vtck(k)*DT/dzq(k) - 1.0)*rc(k)*dzq(k)\n"
    "            endif\n")
sub(m, "         if (ksed1(5) .ge. kts) pptrain = pptrain + sed_c(kts)*DT\n",
    "         if (ksed1(5) .ge. kts) pptrain = pptrain + sed_c(kts)*DT\n"
    "         if (ksed1(5) .ge. kts) wbt(76) = wbt(76) + sed_c(kts)\n")
sub(m, "         if (temp(k).lt.T_0) prg_rcs(k) = -(prr_rcs(k) + prs_rcs(k))\n",
    "         if (temp(k).lt.T_0) prg_rcs(k) = -(prr_rcs(k) + prs_rcs(k))\n"
    "         if (prg_rcs(k) .lt. 0.) then\n"
    "            wbt(78) = wbt(78) - prg_rcs(k)*dzq(k)\n"
    "            wbt(79) = wbt(79) + 1.0D0\n"
    "         endif\n")
sub(post, "'(a,i7,32es17.9)'", f"'(a,i7,{NW}es17.9)'")
sub(d, "'(a,i7,32es17.9)'", f"'(a,i7,{NW}es17.9)'")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBN").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
