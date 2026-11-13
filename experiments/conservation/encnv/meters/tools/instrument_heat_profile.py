#!/usr/bin/env python3
"""Where the D3A/D3B/D4/D12/NGW heating lands (diagnostic builds only; after apply_encnv.py and instrument_gw_split.py).
Usage: instrument_heat_profile.py <ufs-weather-model>
Accumulates per physics level k (1 = bottom), area-weighted (J), over steps 1..NPRINT; prints once at kdt = NPRINT
  'EMZ k c1..c14 x1..x9':
  c1 D3A deep  c2 D3A shallow  c3 D3B deep  c4 D3B shallow  c5 D4 GSL heating (dtdt_gw - dtdt_ngw)
  c6 sum m*area (all columns and steps)  c7 D3B layer heating < 0  c8 D4 layer heating < 0
  c9 NGW heating as run  c10 NGW -d(KE) of its own increment (diagnostic)  c11 D12 cross-term heating (diagnostic)
  c12 D3B interface dissipation < 0  c13 D3B layer-1 remainder (column momentum change x u-bar)  c14 unused
  x1..x5 max |dT/dt| (K/day) for c1..c5; x6 c9; x7 c10; x8 c11; x9 unused.
D3A/D3B terms are metered only if the fix is in the tree; NGW/D12 always (from em_gw)."""
import sys
from pathlib import Path

NPRINT = 100
root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
idir = root / "Interstitials/UFS_SCM_NEPTUNE"
samf = root / "CONV/SAMF"


def sub(p, old, new, count=1):
    s = p.read_text()
    if s.count(old) != count:
        sys.exit(f"ABORT {p.name}: {old.strip()[:60]!r} found {s.count(old)}")
    p.write_text(s.replace(old, new))


common = idir / "energy_meter_common.F90"
sub(common, "  real(kind=8), save :: emy(8) = 0.d0\n",
    "  real(kind=8), save :: emy(8) = 0.d0\n"
    "  real(kind=8), save, public :: emz(200, 14) = 0.d0, emzx(200, 9) = 0.d0\n")
p12 = idir / "em_p12.F90"
sub(p12, "    real(kind=8) :: gbuf(8), grbuf(8)\n",
    "    real(kind=8) :: gbuf(8), grbuf(8)\n    real(kind=8) :: zb(200, 14), zx(200, 9)\n    integer :: kz\n"
    f"    if (kdt == {NPRINT} .and. emkdt(12) /= {NPRINT}) then\n"
    "       call MPI_Reduce(emz, zb, 2800, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "       call MPI_Reduce(emzx, zx, 1800, MPI_DOUBLE_PRECISION, MPI_MAX, mpiroot, mpicomm, ierr)\n"
    "       if (mpirank == mpiroot) then\n"
    "          do kz = 1, levs\n"
    "             write(*,'(a,i4,23es16.8)') 'EMZ ', kz, zb(kz,:), zx(kz,:)\n"
    "          enddo\n"
    "       endif\n"
    "    endif\n")


def acc_line(c, emh):
    return (f"              emz(k,{c}) = emz(k,{c}) + real(cp,8)*{emh}\n"
            f"     &          * real(delp(i,k),8)/real(grav,8)*real(garea(i),8)\n"
            f"              emzx(k,{c}) = max(emzx(k,{c}),\n"
            f"     &          abs({emh})/real(delt,8)*86400.d0)\n")


for f, cA, cB, mass in ((samf / "samfdeepcnv.f", 1, 3, True), (samf / "samfshalcnv.f", 2, 4, False)):
    s = f.read_text()
    hasA = "freezing of the ice part releases hfus" in s
    hasB = "CMT dissipative heating (samf_cmt_heat)" in s
    sub(f, "      use funcphys , only : fpvs\n",
        "      use funcphys , only : fpvs\n      use energy_meter_common, only : emz, emzx\n")
    sub(f, "      implicit none\n", "      implicit none\n      real(kind=8) :: emh\n")
    if hasA:
        old = "     &                      / real(cp, kind=conv_wp) * tem * tem1\n"
        sub(f, old, old + "              emh = real(hfus,8)/real(cp,8)*tem*tem1\n" + acc_line(cA, "emh"))
    if hasB:
        old = "              cmtq(k-1) = cmtq(k-1) + 0.5_conv_wp * tem\n"
        sub(f, old, old + "              emz(k,12) = emz(k,12) + min(0.d0, real(tem,8))\n"
                          "     &          / real(grav,8)*real(garea(i),8)\n")
        old = ("     &              * (new_v1(i,1) + real(v1(i,1), kind=conv_wp)))\n")
        sub(f, old, old + "            emz(1,13) = emz(1,13) + 0.5d0*(cmtu*(new_u1(i,1)\n"
                          "     &        + u1(i,1)) + cmtv*(new_v1(i,1) + v1(i,1)))\n"
                          "     &        / real(grav,8)*real(garea(i),8)\n")
        old = ("              new_t1(i,k) = new_t1(i,k) + cmtq(k)\n"
               "     &          / (real(cp, kind=conv_wp)\n"
               "     &          * real(delp(i,k), kind=conv_wp))\n"
               "            enddo\n")
        sub(f, old, old + "            do k = 1, km\n"
                          f"              emz(k,{cB}) = emz(k,{cB}) + cmtq(k)/real(grav,8)\n"
                          "     &          * real(garea(i),8)\n"
                          "              emz(k,7) = emz(k,7) + min(0.d0, cmtq(k)/real(grav,8)\n"
                          "     &          * real(garea(i),8))\n"
                          f"              emzx(k,{cB}) = max(emzx(k,{cB}), abs(cmtq(k))\n"
                          "     &          / (real(cp,8)*real(delp(i,k),8))/real(delt,8)*86400.d0)\n"
                          "            enddo\n")
    if mass:
        sub(f, "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n",
            "      do k = 1, km\n        do i = 1, im\n"
            "          emz(k,6) = emz(k,6)\n"
            "     &      + real(delp(i,k),8)/real(grav,8)*real(garea(i),8)\n"
            "        enddo\n      enddo\n"
            "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n")

gw = idir / "em_gw.F90"
sub(gw, "  use energy_meter_common, only: emy\n", "  use energy_meter_common, only: emy, emz, emzx\n")
sub(gw, "          e(8) = e(8) + m*abs(hg + kg)\n",
    "          e(8) = e(8) + m*abs(hg + kg)\n"
    "          emz(k,5) = emz(k,5) + m*hg*a\n"
    "          emz(k,8) = emz(k,8) + min(0.d0, m*hg*a)\n"
    "          emzx(k,5) = max(emzx(k,5), abs(hg)/con_cp/dtp*86400.d0)\n"
    "          emz(k,9) = emz(k,9) + m*con_cp*dtp*dtdt_ngw(i,k)*a\n"
    "          emzx(k,6) = max(emzx(k,6), abs(dtdt_ngw(i,k))*86400.d0)\n"
    "          emz(k,10) = emz(k,10) - m*(dun*(u0 + 0.5d0*dun) + dvn*(v0 + 0.5d0*dvn))*a\n"
    "          emzx(k,7) = max(emzx(k,7), abs(dun*(u0 + 0.5d0*dun) + dvn*(v0 + 0.5d0*dvn))/con_cp/dtp*86400.d0)\n"
    "          emz(k,11) = emz(k,11) - m*(du*(ue - u0) + dv*(ve - v0))*a\n"
    "          emzx(k,8) = max(emzx(k,8), abs(du*(ue - u0) + dv*(ve - v0))/con_cp/dtp*86400.d0)\n")
print("heat profile meter (v2) added")
