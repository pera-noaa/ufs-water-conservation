#!/usr/bin/env python3
"""Thompson per-process heat vs FV3's Kirchhoff frame (diagnostic builds only), on a tree with the physics
meter (meter_ccpp_physics.diff) and K1 (instrument_thompson_kirchhoff.py).
Usage: instrument_thompson_meter.py <ufs-weather-model>
Each heating site in mp_thompson calls tk_acc: heat the host receives, h = L_applied*dr*m_d*(1+qv)/(1+cpq*qv)
(= cp_air*m_p*dT), and gap = h - L_F(T)*dr*m_d, m_d = rho*dz. Processes: 1 cloud condensation/evaporation
2 rain evaporation 3 deposition/sublimation 4 freezing/riming 5 melting 6 clean-up exchanges with vapour
(small condensate, clip, vapour floor) 7 unused. em_p12 area-weights per column and prints, per step,
'EMK kdt p h gap |gap| h(220-250K) gap(220-250K) dm(kg)' (J and kg, global sums)."""
import sys
from pathlib import Path

base = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
mod = base / "MP/Thompson/module_mp_thompson.F90"
p12 = base / "Interstitials/UFS_SCM_NEPTUNE/em_p12.F90"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


def before(path, line, calls, count=1):
    sub(path, line, "".join(f"            call tk_acc(tka, {c})\n" for c in calls) + line, count)


MD = "rho(k)*dzq(k)"
sub(mod, "   logical                      :: thompson_kirchhoff = .false.\n",
    "   logical                      :: thompson_kirchhoff = .false.\n"
    "   real(8), public, save :: tkc(6, 7, 8192) = 0.d0   ! energy meter (diagnostic builds only)\n")
sub(mod, "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n",
    "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n      real(8) :: tka(6,7)\n")
sub(mod, "      dtsave = dt\n      odt = 1./dt\n", "      tka = 0.d0\n      dtsave = dt\n      odt = 1./dt\n")
L = "            t1d(k) = t1d(k) - "
before(mod, L + "(lvap0 + dlv*(t1d(k)-273.15))*qc1d(k)/",
       [f"6, 1, lvap0 + dlv*(t1d(k)-273.15), -qc1d(k), t1d(k), qv(k), {MD}"])
before(mod, L + "(lvap0 + dlv*(t1d(k)-273.15))*qr1d(k)/",
       [f"6, 1, lvap0 + dlv*(t1d(k)-273.15), -qr1d(k), t1d(k), qv(k), {MD}"])
for q in ("qi1d", "qs1d", "qg1d"):
    before(mod, L + f"ls_t(t1d(k))*{q}(k)/", [f"6, 2, ls_t(t1d(k)), -{q}(k), t1d(k), qv(k), {MD}"])
before(mod, "            tten(k) = tten(k) - lvap(k)*ocp(k)*(qr1d(k) + qrten(k)*dtsave)*odts*(1-IFDRY)\n",
       [f"6, 1, lvap(k), -(qr1d(k) + qrten(k)*dtsave)*odts*dt, temp(k), qv(k), {MD}"])
before(mod, "            tten(k) = tten(k) &\n                     + ( ls_t(temp(k))*ocp(k)*(pri_inu(k) + pri_ide(k) &\n",
       [f"3, 2, ls_t(temp(k)), (pri_inu(k) + pri_ide(k) + prs_ide(k) + prs_sde(k) + prg_gde(k) + pri_iha(k))*orho*dt, "
        f"temp(k), qv(k), {MD}",
        f"4, 3, lfus2, (pri_wfz(k) + pri_rfz(k) + prg_rfz(k) + prs_scw(k) + prg_scw(k) + prg_gcw(k) + prg_rcs(k) "
        f"+ prs_rcs(k) + prr_rci(k) + prg_rcg(k))*orho*dt, temp(k), qv(k), {MD}"])
before(mod, "            tten(k) = tten(k) &\n                     + ( lf_t(temp(k))*ocp(k)*(-prr_sml(k) - prr_gml(k) &\n",
       [f"5, 3, lf_t(temp(k)), -(prr_sml(k) + prr_gml(k) + prr_rcg(k) + prr_rcs(k))*orho*dt, temp(k), qv(k), {MD}",
        f"3, 2, ls_t(temp(k)), (prs_sde(k) + prg_gde(k))*orho*dt, temp(k), qv(k), {MD}"])
before(mod, "            tten(k) = tten(k) + lvap(k)*ocp(k)*prw_vcd(k)*(1-IFDRY)\n",
       [f"1, 1, lvap(k), prw_vcd(k)*dt, temp(k), qv(k), {MD}"])
before(mod, "            tten(k) = tten(k) - lvap(k)*ocp(k)*prv_rev(k)*(1-IFDRY)\n",
       [f"2, 1, lvap(k), -prv_rev(k)*dt, temp(k), qv(k), {MD}"])
before(mod, "               tten(k) = tten(k) - lf_t(temp(k))*ocp(k)*xri*odt*(1-IFDRY)\n",
       [f"5, 3, lf_t(temp(k)), -xri, temp(k), qv(k), {MD}"])
before(mod, "               tten(k) = tten(k) + lfus2*ocp(k)*xrc*odt*(1-IFDRY)\n",
       [f"4, 3, lfus2, xrc, temp(k), qv(k), {MD}"])
before(mod, "            tten(k) = tten(k) - lvap(k)*ocp(k)*xcl*odt*(1-IFDRY)\n",
       [f"6, 1, lvap(k), -xcl, temp(k), qv(k), {MD}"], count=2)
before(mod, "            tten(k) = tten(k) - ls_t(temp(k))*ocp(k)*xcl*odt*(1-IFDRY)\n",
       [f"6, 2, ls_t(temp(k)), -xcl, temp(k), qv(k), {MD}"], count=3)
before(mod, "               t1d(k) = t1d(k) - frc*ocp(k)*(1-IFDRY)                           &\n",
       [f"6, 1, lvap(k), -frc*(qc1d(k)+qr1d(k)), t1d(k), qv(k), {MD}",
        f"6, 2, ls_t(t1d(k)), -frc*(qi1d(k)+qs1d(k)+qg1d(k)), t1d(k), qv(k), {MD}"])
sub(mod, "\n   end subroutine mp_thompson\n", "\n      tkc(:,:,ii) = tkc(:,:,ii) + tka\n   end subroutine mp_thompson\n")
sub(mod, "\n   elemental real(wp) function ls_t(t)\n",
    """
   subroutine tk_acc(acc, ip, lt, lapp, dr, t, rv, md)
      !< energy meter (diagnostic builds only); lt 1 vapour-liquid 2 vapour-ice 3 liquid-ice
      real(8), intent(inout) :: acc(6,7)
      integer, intent(in) :: ip, lt
      real(wp), intent(in) :: lapp, dr, t, rv, md
      real(8) :: h, lf, g
      h = dble(lapp)*dble(dr)*dble(md)*(1.d0 + dble(rv))/(1.d0 + dble(cpq)*dble(rv))
      if (lt == 1) lf = dble(lvap0) + (1846.d0 - 4185.5d0)*(dble(t) - 273.15d0)
      if (lt == 2) lf = dble(lvap0) + dble(lfus) + (1846.d0 - 1972.d0)*(dble(t) - 273.15d0)
      if (lt == 3) lf = dble(lfus) + (4185.5d0 - 1972.d0)*(dble(t) - 273.15d0)
      g = h - lf*dble(dr)*dble(md)
      acc(1,ip) = acc(1,ip) + h
      acc(2,ip) = acc(2,ip) + g
      acc(3,ip) = acc(3,ip) + abs(g)
      if (t >= 220. .and. t <= 250.) then
         acc(4,ip) = acc(4,ip) + h
         acc(5,ip) = acc(5,ip) + g
      endif
      acc(6,ip) = acc(6,ip) + dble(dr)*dble(md)
   end subroutine tk_acc

   elemental real(wp) function ls_t(t)
""")

sub(p12, "  use mpi_f08\n  implicit none\n",
    "  use mpi_f08\n  use module_mp_thompson, only: tkc\n  implicit none\n  real(kind=8), save :: tkm(6, 7) = 0.d0\n")
sub(p12, "    real(kind=8) :: buf(10*emnp+12), rbuf(10*emnp+12)\n",
    "    real(kind=8) :: buf(10*emnp+12), rbuf(10*emnp+12), tbuf(42), trbuf(42)\n")
sub(p12, "       emg = 0.d0\n       emx = 0.d0\n",
    "       emg = 0.d0\n       emx = 0.d0\n"
    "       tbuf = reshape(tkm, (/42/))\n"
    "       if (mpirank == mpiroot) then\n"
    "          call MPI_Reduce(MPI_IN_PLACE, tbuf, 42, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "          do s = 1, 7\n"
    "             write(*,'(a,i6,i3,6es25.16)') 'EMK ', emkdt(12), s, tbuf(6*(s-1)+1:6*s)\n"
    "          enddo\n"
    "       else\n"
    "          call MPI_Reduce(tbuf, trbuf, 42, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "       endif\n"
    "       tkm = 0.d0\n")
sub(p12, "       a = garea(i)\n", "       a = garea(i)\n       tkm = tkm + tkc(:,:,i)*a\n       tkc(:,:,i) = 0.d0\n")

for p, s in edits.items():
    p.write_text(s)
    print("edited", p)
