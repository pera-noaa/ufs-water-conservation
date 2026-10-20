#!/usr/bin/env python3
"""Energy meters in the FV3 dycore and the physics->dynamics coupling (diagnostic builds only).
Usage: instrument_eb_dyn.py <ufs-weather-model>
eb_state() sums, over the compute domain, x*delp*area/grav (real(8)) for
  1 IE=cvm*T  2 PE=0.5(phi_k+phi_k+1)  3 KD=D-grid KE (compute_total_energy form)  4 KW=0.5w^2
  5 KA=0.5(ua^2+va^2)  6 Wv=qv  7 Wl=ql+qr  8 Wi=qi+qs+qg  9 M=1  10 cp_air*T*(1-qc)  11 KA*(1-qc)  12 cpm*T
Probes (slot): 1 atmos_dynamics start | 2 after fv_dynamics | 3 after fv_subgrid_z | 4 state_update start
  5 before fv_update_phys | 6 after fv_update_phys | 7 fv_dynamics: te0 point | 8 after Rayleigh
  9 after last remap (fixer applied) | 10 after neg_adj3
Extra EBX: 1 te0 (g_sum te_2d/grav) 2 fixer intended energy consv*g_sum(te0-te)/grav 3 E_Flux
  4 intended physics heating sum(cp_air*t_dt*dt*delp)/grav (dyn frame, at fv_update_phys entry)
One line per step from the master: 'EBD kstep slot v1..v12' after mpp_sum; EBX line. Anchors must match once."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/fv3/atmos_cubed_sphere"
mapz = root / "model/fv_mapz.F90"
dyn = root / "model/fv_dynamics.F90"
upd = root / "model/fv_update_phys.F90"
atm = root / "driver/UFS/atmosphere.F90"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


FUNC = r"""
 subroutine eb_state(is, ie, js, je, isd, ied, jsd, jed, km, nwat, sphum, liq_wat, rainwat, ice_wat, &
                     snowwat, graupel, hailwat, u, v, w, delz, pt, delp, q, hs, ua, va, rsin2_l, cosa_s_l, &
                     area, grav_var, slot)
   ! energy meter (diagnostic builds only): rank sums of x*delp*area/grav into ebs(:,slot)
   integer, intent(in) :: is, ie, js, je, isd, ied, jsd, jed, km, nwat, slot
   integer, intent(in) :: sphum, liq_wat, rainwat, ice_wat, snowwat, graupel, hailwat
   real, intent(in) :: u(isd:ied, jsd:jed+1, km), v(isd:ied+1, jsd:jed, km)
   real, intent(in) :: w(isd:, jsd:, 1:), delz(is:, js:, 1:)
   real, intent(in), dimension(isd:ied, jsd:jed, km) :: pt, delp, ua, va
   real, intent(in) :: q(isd:ied, jsd:jed, km, *), hs(isd:ied, jsd:jed)
   real, intent(in) :: rsin2_l(isd:ied, jsd:jed), cosa_s_l(isd:ied, jsd:jed)
   real(kind=8), intent(in) :: area(isd:ied, jsd:jed)
   real, intent(in) :: grav_var(isd:ied, jsd:jed, km)
   real :: phiz(is:ie, km+1), cvm(is:ie), qd(is:ie)
   real(kind=8) :: a, x(12), qc, qi
   integer :: i, j, k
   do j = js, je
      do i = is, ie
         phiz(i, km+1) = hs(i, j)
      enddo
      do k = km, 1, -1
         do i = is, ie
            phiz(i, k) = phiz(i, k+1) - grav_var(i, j, k)*delz(i, j, k)
         enddo
      enddo
      do k = 1, km
         call moist_cv(is, ie, isd, ied, jsd, jed, km, j, k, nwat, sphum, liq_wat, rainwat, &
                       ice_wat, snowwat, graupel, hailwat, q, qd, cvm)
         do i = is, ie
            a = dble(delp(i, j, k))*area(i, j)/dble(grav)
            qi = dble(q(i, j, k, ice_wat)) + dble(q(i, j, k, snowwat)) + dble(q(i, j, k, graupel))
            if (hailwat > 0) qi = qi + dble(q(i, j, k, hailwat))
            qc = qi + dble(q(i, j, k, liq_wat)) + dble(q(i, j, k, rainwat))
            x(1) = dble(cvm(i))*dble(pt(i, j, k))
            x(2) = 0.5d0*(dble(phiz(i, k)) + dble(phiz(i, k+1)))
            x(3) = 0.25d0*dble(rsin2_l(i, j))*(dble(u(i, j, k))**2 + dble(u(i, j+1, k))**2 + &
                   dble(v(i, j, k))**2 + dble(v(i+1, j, k))**2 - (dble(u(i, j, k)) + dble(u(i, j+1, k)))* &
                   (dble(v(i, j, k)) + dble(v(i+1, j, k)))*dble(cosa_s_l(i, j)))
            x(4) = 0.5d0*dble(w(i, j, k))**2
            x(5) = 0.5d0*(dble(ua(i, j, k))**2 + dble(va(i, j, k))**2)
            x(6) = dble(q(i, j, k, sphum))
            x(7) = dble(q(i, j, k, liq_wat)) + dble(q(i, j, k, rainwat))
            x(8) = qi
            x(9) = 1.d0
            x(10) = dble(cp_air)*dble(pt(i, j, k))*(1.d0 - qc)
            x(11) = x(5)*(1.d0 - qc)
            x(12) = ((1.d0 - dble(q(i, j, k, sphum)) - qc)*dble(cp_air) + dble(q(i, j, k, sphum))*dble(cp_vapor) &
                    + x(7)*dble(c_liq) + qi*dble(c_ice))*dble(pt(i, j, k))
            ebs(:, slot) = ebs(:, slot) + x*a
         enddo
      enddo
   enddo
 end subroutine eb_state

 subroutine eb_print(kstep)
   ! energy meter: global sums of all slots, one line per slot from the master, then reset
   use mpp_mod, only: mpp_sum
   integer, intent(in) :: kstep
   integer :: s
   call mpp_sum(ebs, size(ebs))
   call mpp_sum(ebx, size(ebx))
   if (mpp_pe() == mpp_root_pe()) then
      if (kstep == 1) write(*, '(a,9es24.16)') 'EBC ', dble(cp_air), dble(rdgas), dble(rvgas), dble(grav), &
           dble(hlv), dble(hlf), dble(cp_vapor), dble(c_liq), dble(c_ice)
      do s = 1, size(ebs, 2)
         if (ebs(9, s) /= 0.d0) write(*, '(a,i6,i3,12es25.16)') 'EBD ', kstep, s, ebs(:, s)
      enddo
      write(*, '(a,i6,8es25.16)') 'EBX ', kstep, ebx
   endif
   ebs = 0.d0
   ebx = 0.d0
 end subroutine eb_print
"""

# fv_mapz.F90: storage, public names, functions, fixer-intended energy
sub(mapz, "  real(kind=4) :: E_Flux = 0.\n",
    "  real(kind=4) :: E_Flux = 0.\n  real(kind=8), public, save :: ebs(12, 12) = 0.d0, ebx(8) = 0.d0\n")
sub(mapz, "         rst_remap, mappm, E_Flux, remap_2d, map_scalar\n",
    "         rst_remap, mappm, E_Flux, remap_2d, map_scalar, eb_state, eb_print\n")
sub(mapz, " end subroutine moist_cp\n\nend module fv_mapz_mod",
    " end subroutine moist_cp\n" + FUNC + "\nend module fv_mapz_mod")
sub(mapz, "         dtmp = consv*g_sum(domain, te_2d, is, ie, js, je, ng, gridstruct%area_64, 0, reproduce=.true.)\n",
    "         dtmp = consv*g_sum(domain, te_2d, is, ie, js, je, ng, gridstruct%area_64, 0, reproduce=.true.)\n"
    "      if (mpp_pe() == mpp_root_pe()) ebx(2) = ebx(2) + dble(dtmp)/dble(grav)\n")
sub(mapz, "      E_Flux = dtmp / (grav*pdt*4.*pi*radius**2)    ! unit: W/m**2\n",
    "      E_Flux = dtmp / (grav*pdt*4.*pi*radius**2)    ! unit: W/m**2\n"
    "      if (mpp_pe() == mpp_root_pe()) ebx(3) = ebx(3) + dble(E_Flux)\n")

sub(mapz, "ng,gridstruct,E_Flux,pdt,dtmp,reproduce_sum,q,", "ng,gridstruct,E_Flux,pdt,dtmp,reproduce_sum,q,ebx,")

# fv_dynamics.F90: probes 7-10, te0 total
EBA = ("call eb_state(is, ie, js, je, isd, ied, jsd, jed, npz, nwat, sphum, liq_wat, rainwat, ice_wat, "
       "snowwat, graupel, hailwat, u, v, w, delz, pt, delp, q, phis, ua, va, gridstruct%rsin2, "
       "gridstruct%cosa_s, gridstruct%area_64, grav_var, {s})")
sub(dyn, "   use fv_mapz_mod,         only: compute_total_energy, Lagrangian_to_Eulerian, moist_cv, moist_cp\n",
    "   use fv_mapz_mod,         only: compute_total_energy, Lagrangian_to_Eulerian, moist_cv, moist_cp\n"
    "   use fv_mapz_mod,         only: eb_state, ebx\n")
sub(dyn, "      if( (flagstruct%consv_am .or. idiag%id_amdt>0) .and. (.not.do_adiabatic_init) ) then\n          call compute_aam(",
    "      if (.not.do_adiabatic_init) then\n         " + EBA.format(s=7) + "\n"
    "         if (consv_te > 0.) ebx(1) = ebx(1) + sum(dble(te_2d(is:ie,js:je))*gridstruct%area_64(is:ie,js:je))/dble(grav)\n"
    "      endif\n"
    "      if( (flagstruct%consv_am .or. idiag%id_amdt>0) .and. (.not.do_adiabatic_init) ) then\n          call compute_aam(")
sub(dyn, "                .not. gridstruct%bounded_domain, flagstruct%molecular_diffusion, consv_te, flagstruct%rf_cutoff, gridstruct, domain, bd)\n",
    "                .not. gridstruct%bounded_domain, flagstruct%molecular_diffusion, consv_te, flagstruct%rf_cutoff, gridstruct, domain, bd)\n"
    "             if (.not.do_adiabatic_init) " + EBA.format(s=8) + "\n")
sub(dyn, "                     flagstruct%moist_phys, grav_var)\n     \n                                                  call timing_off('Remapping')\n",
    "                     flagstruct%moist_phys, grav_var)\n     \n                                                  call timing_off('Remapping')\n"
    "     if (GFDL_interstitial%last_step .and. .not.do_adiabatic_init) " + EBA.format(s=9) + "\n")
sub(dyn, "                                q(isd,jsd,1,graupel), grav_var, check_negative=flagstruct%check_negative)\n     endif\n",
    "                                q(isd,jsd,1,graupel), grav_var, check_negative=flagstruct%check_negative)\n     endif\n"
    "     if (.not.do_adiabatic_init) " + EBA.format(s=10) + "\n")

# atmosphere.F90: probes 1-6, intended physics heating, print
EBT = ("call eb_state(isc, iec, jsc, jec, isd, ied, jsd, jed, npz, Atm(n)%flagstruct%nwat, sphum, liq_wat, rainwat, "
       "ice_wat, snowwat, graupel, hailwat, Atm(n)%u, Atm(n)%v, Atm(n)%w, "
       "Atm(n)%delz, Atm(n)%pt, Atm(n)%delp, Atm(n)%q, Atm(n)%phis, Atm(n)%ua, Atm(n)%va, "
       "Atm(n)%gridstruct%rsin2, Atm(n)%gridstruct%cosa_s, Atm(n)%gridstruct%area_64, Atm(n)%grav_var, {s})")
sub(atm, "use fv_update_phys_mod, only: fv_update_phys\n",
    "use fv_update_phys_mod, only: fv_update_phys\nuse fv_mapz_mod,       only: eb_state, eb_print, ebx\n")
sub(atm, "   a_step = a_step + 1\n", "   a_step = a_step + 1\n   " + EBT.format(s=1) + "\n")
sub(atm, "    enddo !p_split\n", "    enddo !p_split\n    " + EBT.format(s=2) + "\n")
sub(atm, "    t_dt = 0.\n\n   call mpp_clock_end (id_subgridz)\n",
    "    t_dt = 0.\n    " + EBT.format(s=3) + "\n\n   call mpp_clock_end (id_subgridz)\n")
sub(atm, "   call timing_on('GFS_TENDENCIES')\n   call atmos_phys_qdt_diag(",
    "   " + EBT.format(s=4) + "\n   call timing_on('GFS_TENDENCIES')\n   call atmos_phys_qdt_diag(")
sub(atm, "   call mpp_clock_begin (id_dynam)\n       call timing_on('FV_UPDATE_PHYS')\n",
    "   " + EBT.format(s=5) + "\n"
    "   ebx(4) = ebx(4) + sum(dble(t_dt(isc:iec,jsc:jec,:))*dble(dt_atmos)*dble(cp_air)*dble(Atm(n)%delp(isc:iec,jsc:jec,:)) &\n"
    "          *spread(Atm(n)%gridstruct%area_64(isc:iec,jsc:jec),3,npz))/dble(grav)\n"
    "   call mpp_clock_begin (id_dynam)\n       call timing_on('FV_UPDATE_PHYS')\n")
sub(atm, "       call timing_off('FV_UPDATE_PHYS')\n   call mpp_clock_end (id_dynam)\n",
    "       call timing_off('FV_UPDATE_PHYS')\n   call mpp_clock_end (id_dynam)\n"
    "   " + EBT.format(s=6) + "\n   call eb_print(a_step)\n")

for p, s in edits.items():
    p.write_text(s)
    print("edited", p)
