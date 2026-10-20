#!/usr/bin/env python3
"""C1: energy-consistent physics water-mass write (fv_core_nml cpl_water_energy, bit flags, default 0 = off).
Usage: instrument_cpl_fix.py <ufs-weather-model>
  bit 1 (PE)  the net water flux through each interface releases its geopotential drop as heat in the layers
              it crosses (precipitation: Pauluis et al. 2000 frictional heating; vapour lifted: the PE the
              fixed-volume write gives it for free is taken back)
  bit 2 (FW)  vapour mass enters/leaves a layer at constant pressure: + R_v*T*dm_v (flow work the fixed-delz
              write omits; the physics latent heats are enthalpies)
  bit 4 (S)   water crossing an interface is brought to the receiving layer's T by that layer
              (c_liq or c_ice downward by the upper layer's T, cp_vap upward)
Layer-local; frame and derivation: conservation/encpl/report.md. Anchors must match once."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/fv3/atmos_cubed_sphere"
arr = root / "model/fv_arrays.F90"
ctl = root / "model/fv_control.F90"
atm = root / "driver/UFS/atmosphere.F90"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


sub(arr, "   logical :: fill_gfs = .true. ! default behavior\n",
    "   logical :: fill_gfs = .true. ! default behavior\n"
    "   integer :: cpl_water_energy = 0 !< physics water-mass write: 1 PE, 2 vapour flow work, 4 sensible (bits)\n")
sub(ctl, "     logical , pointer :: fill_gfs\n", "     logical , pointer :: fill_gfs\n     integer , pointer :: cpl_water_energy\n")
sub(ctl, "       fill_gfs                      => Atm%flagstruct%fill_gfs\n",
    "       fill_gfs                      => Atm%flagstruct%fill_gfs\n"
    "       cpl_water_energy              => Atm%flagstruct%cpl_water_energy\n")
sub(ctl, "consv_te, fill, filter_phys, fill_dp, fill_wz, fill_gfs, consv_am,",
    "consv_te, fill, filter_phys, fill_dp, fill_wz, fill_gfs, cpl_water_energy, consv_am,")

sub(atm, "use constants_mod,          only: cp_air, rdgas, grav, rvgas, kappa, pstd_mks\n",
    "use constants_mod,          only: cp_air, rdgas, grav, rvgas, kappa, pstd_mks, cp_vapor\n")
sub(atm, "use constantsR4_mod,          only: cp_air, rdgas, grav, rvgas, kappa, pstd_mks\n",
    "use constantsR4_mod,          only: cp_air, rdgas, grav, rvgas, kappa, pstd_mks, cp_vapor\n")

CALL = """
     if (Atm(n)%flagstruct%cpl_water_energy > 0) call cpl_water_energy(nb, blen, Atm(n)%flagstruct%cpl_water_energy, &
                                     flip_vc, rdt, IPD_Control, IPD_Statein, IPD_Stateout, Atm_block)
"""
sub(atm, "\n\n     do k = 1, npz\n       if(flip_vc) then\n         k1 = npz+1-k !reverse the k direction\n       else\n"
    "         k1 = k\n       endif\n       do ix = 1, blen\n         i = Atm_block%index(nb)%ii(ix)\n"
    "         j = Atm_block%index(nb)%jj(ix)\n         im = IPD_control%chunk_begin(nb)+ix-1\n         u_dt(i,j,k1)",
    "\n" + CALL + "\n     do k = 1, npz\n       if(flip_vc) then\n         k1 = npz+1-k !reverse the k direction\n       else\n"
    "         k1 = k\n       endif\n       do ix = 1, blen\n         i = Atm_block%index(nb)%ii(ix)\n"
    "         j = Atm_block%index(nb)%jj(ix)\n         im = IPD_control%chunk_begin(nb)+ix-1\n         u_dt(i,j,k1)")

SUBR = """
 subroutine cpl_water_energy(nb, blen, ibits, flip_vc, rdt, IPD_Control, IPD_Statein, IPD_Stateout, Atm_block)
   ! Heating that makes the physics water-mass write energy-consistent in FV3's frame (cvm*T + phi + K
   ! + Kirchhoff latent terms; water leaves/enters at the surface at T(npz), phis). Called before the write.
   integer, intent(in) :: nb, blen, ibits
   logical, intent(in) :: flip_vc
   real(kind=kind_phys), intent(in) :: rdt
   type(IPD_control_type), intent(in) :: IPD_Control
   type(GFS_statein_type), intent(in) :: IPD_Statein
   type(GFS_stateout_type), intent(in) :: IPD_Stateout
   type(block_control_type), intent(in) :: Atm_block
   real(kind=kind_phys), parameter :: c_liq = 4.1855e+3, c_ice = 1972., t_frz = 273.15  ! = fv_mapz c_liq, c_ice
   real(kind=kind_phys) :: dpn(npz), dm(npz), dmv(npz), tk(npz), phib(npz+1), ftop(npz+1)
   real(kind=kind_phys) :: qpe(npz), qfw(npz), qse(npz), qp, cb, e
   integer :: ix, i, j, im, k, k1, n, nwat
   n = mygrid
   nwat = Atm(n)%flagstruct%nwat
   do ix = 1, blen
      i = Atm_block%index(nb)%ii(ix)
      j = Atm_block%index(nb)%jj(ix)
      im = IPD_control%chunk_begin(nb)+ix-1
      phib(npz+1) = Atm(n)%phis(i,j)
      do k1 = npz, 1, -1
         phib(k1) = phib(k1+1) - Atm(n)%grav_var(i,j,k1)*Atm(n)%delz(i,j,k1)
      enddo
      do k1 = 1, npz
         if (flip_vc) then
            k = npz+1-k1
            qp = IPD_Statein%prsi(im,k) - IPD_Statein%prsi(im,k+1)
         else
            k = k1
            qp = IPD_Statein%prsi(im,k+1) - IPD_Statein%prsi(im,k)
         endif
         ! same layer mass the write produces; dm, dmv: water and vapour mass change (Pa)
         dpn(k1) = Atm(n)%delp(i,j,k1)*(1.-sum(Atm(n)%q(i,j,k1,1:nwat))) + sum(qp*IPD_Stateout%gq0(im,k,1:nwat))
         dm(k1) = dpn(k1) - Atm(n)%delp(i,j,k1)
         dmv(k1) = qp*IPD_Stateout%gq0(im,k,sphum) - Atm(n)%delp(i,j,k1)*Atm(n)%q(i,j,k1,sphum)
         tk(k1) = Atm(n)%pt(i,j,k1)
      enddo
      ! net downward water flux through the top of each layer (Pa); ftop(npz+1) = P - E
      ftop(1) = 0.
      do k1 = 1, npz
         ftop(k1+1) = ftop(k1) - dm(k1)
      enddo
      qse(:) = 0.
      do k1 = 1, npz
         qpe(k1) = 0.5*(ftop(k1) + ftop(k1+1))*(phib(k1) - phib(k1+1))
         qfw(k1) = rvgas*tk(k1)*dmv(k1)
      enddo
      do k1 = 1, npz-1
         if (ftop(k1+1) >= 0.) then
            cb = c_liq
            if (tk(k1) < t_frz) cb = c_ice
            qse(k1+1) = qse(k1+1) - ftop(k1+1)*cb*(tk(k1+1) - tk(k1))
         else
            qse(k1) = qse(k1) - ftop(k1+1)*cp_vapor*(tk(k1+1) - tk(k1))
         endif
      enddo
      do k1 = 1, npz
         e = 0.
         if (iand(ibits, 1) /= 0) e = e + qpe(k1)
         if (iand(ibits, 2) /= 0) e = e + qfw(k1)
         if (iand(ibits, 4) /= 0) e = e + qse(k1)
         ! fv_update_phys injects cp_air*t_dt*dt*delp_new/grav
         t_dt(i,j,k1) = t_dt(i,j,k1) + e*rdt/(cp_air*dpn(k1))
      enddo
   enddo
 end subroutine cpl_water_energy

end module atmosphere_mod"""
sub(atm, "\nend module atmosphere_mod", SUBR)

for p, s in edits.items():
    p.write_text(s)
    print("edited", p)
