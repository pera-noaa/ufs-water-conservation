#!/usr/bin/env python3
"""Coupling-write energy meter (diagnostic builds only), on a tree that has the dycore meters
(meter_fv3_dycore_coupling.diff) and C1 (instrument_cpl_fix.py).
Usage: instrument_cpl_meter.py <ufs-weather-model>
cpl_water_energy runs every step (it applies heating only for the bits set) and sums per column x area
(Pa*J/kg*m2; the table divides by grav), one line per step 'EBQ kstep x1..x34':
  1 W_IE=sum dm_w*cv_w*T  2 W_PE=sum dm*phi_mid  3 W_K=sum dm*KA  4 dWv 5 dWl 6 dWi  7 P_liq 8 P_ice 9 E=dW+P
  10 E*T1 11 P_liq*T1 12 P_ice*T1 13 (E-P)*phis  14 FW=-Rv*sum dmv*T  15 PE_rel=sum dm*(phi_mid-phis)
  16 S=sum dm_w*cp_w*(T-T0) - E*cpv*(T1-T0) + P_liq*cl*(T1-T0) + P_ice*ci*(T1-T0)  17 S_cross (c-bar rule)
  18-20 sum qpe, qfw, qse  21-23 sum|qpe|,|qfw|,|qse| (layers)  24 applied  25 physics heating cp_air*dT*m_p
  26 S_cross with c_liq for all downward flux  27 S_cross downward part  28 S_cross upward part
  29 PE release by downward net flux  30 by upward net flux  31-33 sum over columns |PE_rel|,|FW|,|S_cross|
  34 area. Anchors must match once."""
import sys
from pathlib import Path

base = Path(sys.argv[1]) / "UFSATM"
root = base / "fv3/atmos_cubed_sphere"
mapz = root / "model/fv_mapz.F90"
atm = root / "driver/UFS/atmosphere.F90"
amod = base / "fv3/atmos_model.F90"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


# storage and print (fv_mapz, next to the dycore meter's ebs/ebx)
sub(mapz, "  real(kind=8), public, save :: ebs(12, 12) = 0.d0, ebx(8) = 0.d0\n",
    "  real(kind=8), public, save :: ebs(12, 12) = 0.d0, ebx(8) = 0.d0\n"
    "  real(kind=8), public, save :: ebq(34) = 0.d0\n"
    "  real(kind=8), public, allocatable, save :: ebq_prc(:,:)\n")
sub(mapz, "   call mpp_sum(ebx, size(ebx))\n", "   call mpp_sum(ebx, size(ebx))\n   call mpp_sum(ebq, size(ebq))\n")
sub(mapz, "      write(*, '(a,i6,8es25.16)') 'EBX ', kstep, ebx\n",
    "      write(*, '(a,i6,8es25.16)') 'EBX ', kstep, ebx\n"
    "      write(*, '(a,i6,34es25.16)') 'EBQ ', kstep, ebq\n")
sub(mapz, "   ebx = 0.d0\n end subroutine eb_print", "   ebx = 0.d0\n   ebq = 0.d0\n end subroutine eb_print")

# precipitation of this physics step per column (kg m-2), physics chunk index
sub(amod, "use atmosphere_mod,     only: atmosphere_state_update\n",
    "use atmosphere_mod,     only: atmosphere_state_update\nuse fv_mapz_mod,       only: ebq_prc\n")
sub(amod, "    call atmosphere_state_update(Atmos%Time, GFS_control, GFS_statein, GFS_stateout, IAU_Data, Atm_block, flip_vc)\n",
    "    if (.not. allocated(ebq_prc)) allocate(ebq_prc(2, size(GFS_intdiag%rain)))\n"
    "    ebq_prc(1,:) = 1000.d0*GFS_intdiag%rain(:)\n"
    "    ebq_prc(2,:) = 1000.d0*(GFS_intdiag%snow(:) + GFS_intdiag%ice(:) + GFS_intdiag%graupel(:))\n"
    "    call atmosphere_state_update(Atmos%Time, GFS_control, GFS_statein, GFS_stateout, IAU_Data, Atm_block, flip_vc)\n")

# run the routine every step
sub(atm, "     if (Atm(n)%flagstruct%cpl_water_energy > 0) call cpl_water_energy(",
    "     call cpl_water_energy(")
sub(atm, "use fv_mapz_mod,       only: eb_state, eb_print, ebx\n",
    "use fv_mapz_mod,       only: eb_state, eb_print, ebx, ebq, ebq_prc\n")
sub(atm, "   real(kind=kind_phys) :: qpe(npz), qfw(npz), qse(npz), qp, cb, e\n",
    "   real(kind=kind_phys) :: qpe(npz), qfw(npz), qse(npz), qp, cb, e\n"
    "   real(kind=8) :: x(34), a, dml, dmi, phm, ka, f, dt1, pl, pic, ev, t1, cpe, cfw, csx\n"
    "   real(kind=kind_phys), parameter :: cv_vap = 3.*rvgas\n")
METER = """      ! energy meter (diagnostic builds only)
      x(:) = 0.d0
      a = Atm(n)%gridstruct%area_64(i,j)
      cpe = 0.d0
      cfw = 0.d0
      do k1 = 1, npz
         if (flip_vc) then
            k = npz+1-k1
            qp = IPD_Statein%prsi(im,k) - IPD_Statein%prsi(im,k+1)
         else
            k = k1
            qp = IPD_Statein%prsi(im,k+1) - IPD_Statein%prsi(im,k)
         endif
         dml = qp*(IPD_Stateout%gq0(im,k,liq_wat) + IPD_Stateout%gq0(im,k,rainwat)) &
             - Atm(n)%delp(i,j,k1)*(Atm(n)%q(i,j,k1,liq_wat) + Atm(n)%q(i,j,k1,rainwat))
         dmi = qp*(IPD_Stateout%gq0(im,k,ice_wat) + IPD_Stateout%gq0(im,k,snowwat) + IPD_Stateout%gq0(im,k,graupel)) &
             - Atm(n)%delp(i,j,k1)*(Atm(n)%q(i,j,k1,ice_wat) + Atm(n)%q(i,j,k1,snowwat) + Atm(n)%q(i,j,k1,graupel))
         phm = 0.5d0*(phib(k1) + phib(k1+1))
         ka = 0.5d0*(dble(Atm(n)%ua(i,j,k1))**2 + dble(Atm(n)%va(i,j,k1))**2)
         x(1) = x(1) + (dmv(k1)*cv_vap + dml*c_liq + dmi*c_ice)*tk(k1)
         x(2) = x(2) + dm(k1)*phm
         x(3) = x(3) + dm(k1)*ka
         x(4) = x(4) + dmv(k1)
         x(5) = x(5) + dml
         x(6) = x(6) + dmi
         x(14) = x(14) - rvgas*dmv(k1)*tk(k1)
         x(15) = x(15) + dm(k1)*(phm - phib(npz+1))
         x(16) = x(16) + (dmv(k1)*cp_vapor + dml*c_liq + dmi*c_ice)*(tk(k1) - t_frz)
         x(18) = x(18) + qpe(k1)
         x(19) = x(19) + qfw(k1)
         x(20) = x(20) + qse(k1)
         x(21) = x(21) + abs(qpe(k1))
         x(22) = x(22) + abs(qfw(k1))
         x(23) = x(23) + abs(qse(k1))
         x(25) = x(25) + cp_air*(IPD_Stateout%gt0(im,k) - IPD_Statein%tgrs(im,k))*qp
      enddo
      do k1 = 1, npz
         f = ftop(k1+1)
         if (k1 < npz) then
            dt1 = tk(k1+1) - tk(k1)
            x(26) = x(26) + f*c_liq*dt1
            if (f >= 0.) then
               cb = c_liq
               if (tk(k1) < t_frz) cb = c_ice
               x(17) = x(17) + f*cb*dt1
               x(27) = x(27) + f*cb*dt1
            else
               x(17) = x(17) + f*cp_vapor*dt1
               x(28) = x(28) + f*cp_vapor*dt1
            endif
            phm = 0.5d0*(phib(k1) - phib(k1+2))
         else
            phm = 0.5d0*(phib(k1) + phib(k1+1)) - phib(npz+1)
         endif
         if (f >= 0.) then
            x(29) = x(29) + f*phm
         else
            x(30) = x(30) + f*phm
         endif
      enddo
      pl = (ebq_prc(1,im) - ebq_prc(2,im))*grav
      pic = ebq_prc(2,im)*grav
      ev = x(4) + x(5) + x(6) + pl + pic
      t1 = tk(npz)
      x(7) = pl
      x(8) = pic
      x(9) = ev
      x(10) = ev*t1
      x(11) = pl*t1
      x(12) = pic*t1
      x(13) = (x(4) + x(5) + x(6))*phib(npz+1)
      x(16) = x(16) + (-ev*cp_vapor + pl*c_liq + pic*c_ice)*(t1 - t_frz)
      x(31) = abs(x(15))
      x(32) = abs(x(14))
      x(33) = abs(x(17))
      x(34) = 1.d0
"""
sub(atm, "      do k1 = 1, npz\n         e = 0.\n", METER + "      do k1 = 1, npz\n         e = 0.\n")
sub(atm, "         t_dt(i,j,k1) = t_dt(i,j,k1) + e*rdt/(cp_air*dpn(k1))\n      enddo\n",
    "         t_dt(i,j,k1) = t_dt(i,j,k1) + e*rdt/(cp_air*dpn(k1))\n         x(24) = x(24) + e\n      enddo\n"
    "!$OMP CRITICAL (ebq_acc)\n      ebq = ebq + x*a\n!$OMP END CRITICAL (ebq_acc)\n")

for p, s in edits.items():
    p.write_text(s)
    print("edited", p)
