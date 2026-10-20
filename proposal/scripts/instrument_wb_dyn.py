#!/usr/bin/env python3
"""Water meters in the FV3 dynamical core and the physics->dynamics update (diagnostic builds only).
Usage: python3 instrument_wb_dyn.py <ufs_model.fd>      (v1 snapshot layout; pair with instrument_wb_phys.py)
W = sum over the six water tracers (first nwat in q) of q*delp/g*area_64, compute domain, real(8). Cumulative per rank:
  WBD n | 1 fv_dynamics (all p_split calls) | 2 of which neg_adj3 | 3 fv_subgrid_z | 4 physics update write
        (atmosphere_state_update, incl. fill_gfs and IAU) | 5 fv_update_phys | 6 fill_gfs, physics frame
        (part of 4) | 7 gap end-of-dynamics -> start-of-update | 8 gap end-of-update -> next dynamics | 9 area (m2)
printed (kg) after every atmosphere_state_update; n = steps done (atmf000 is after n = 1). Sum over ranks at equal n.
Hand-off residual = (4)/area - physics meter (WBP) step change/area. Every anchor must match exactly once."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/atmos_cubed_sphere"
dyn = root / "model/fv_dynamics.F90"
atm = root / "driver/fvGFS/atmosphere.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


FUNC = """
 real(kind=8) function wb_water(isd, ied, jsd, jed, is, ie, js, je, npz, nwat, q, delp, area)
   ! water meter: sum of q*delp/g*area over the first nwat tracers, compute domain (diagnostic builds only)
   integer, intent(in) :: isd, ied, jsd, jed, is, ie, js, je, npz, nwat
   real, intent(in) :: q(isd:ied, jsd:jed, npz, *), delp(isd:ied, jsd:jed, npz)
   real(kind=8), intent(in) :: area(isd:ied, jsd:jed)
   integer :: i, j, k, m
   wb_water = 0.d0
   do m = 1, nwat
      do k = 1, npz
         do j = js, je
            do i = is, ie
               wb_water = wb_water + dble(q(i,j,k,m))*dble(delp(i,j,k))*area(i,j)
            enddo
         enddo
      enddo
   enddo
   wb_water = wb_water/9.80665d0
 end function wb_water
"""
WA = "wb_water(isd,ied,jsd,jed,isc,iec,jsc,jec,npz,Atm(n)%flagstruct%nwat,Atm(n)%q,Atm(n)%delp,Atm(n)%gridstruct%area_64)"

# fv_dynamics.F90: accumulators, the meter function, and a meter around neg_adj3
sub(dyn, "public :: fv_dynamics\n",
    "public :: fv_dynamics\npublic :: wbd, wb_water\nreal(kind=8), save :: wbd(8) = 0.d0\n")
sub(dyn, "\ncontains\n", "\ncontains\n" + FUNC)
sub(dyn, "    real, intent(inout) :: q(   bd%isd:bd%ied  ,bd%jsd:bd%jed  ,npz, ncnst) !< specific humidity and constituents\n",
    "    real, intent(inout) :: q(   bd%isd:bd%ied  ,bd%jsd:bd%jed  ,npz, ncnst) !< specific humidity and constituents\n"
    "    real(kind=8) :: wb_x0\n")
sub(dyn, "  if( nwat == 6 ) then\n     if (cld_amt > 0) then\n",
    "  wb_x0 = wb_water(isd,ied,jsd,jed,is,ie,js,je,npz,nwat,q,delp,gridstruct%area_64)\n"
    "  if( nwat == 6 ) then\n     if (cld_amt > 0) then\n")
sub(dyn, "q(isd,jsd,1,graupel), check_negative=flagstruct%check_negative)\n     endif\n",
    "q(isd,jsd,1,graupel), check_negative=flagstruct%check_negative)\n     endif\n"
    "     wbd(2) = wbd(2) + (wb_water(isd,ied,jsd,jed,is,ie,js,je,npz,nwat,q,delp,gridstruct%area_64) - wb_x0)\n")

# atmosphere.F90
sub(atm, "use fv_dynamics_mod,    only: fv_dynamics\n", "use fv_dynamics_mod,    only: fv_dynamics, wbd, wb_water\n")
sub(atm, "  integer :: p_split = 1\n",
    "  integer :: p_split = 1\n"
    "  real(kind=8), save :: wb_d2 = -1.d0, wb_s2 = -1.d0, wb_area = 0.d0\n"
    "  integer, save :: wbd_n = 0\n")
# dynamics
sub(atm, "   type(time_type) :: atmos_time\n", "   type(time_type) :: atmos_time\n   real(kind=8) :: wb_t\n")
sub(atm, "   do psc=1,abs(p_split)\n",
    f"   wb_t = {WA}\n"
    "   if (wb_s2 >= 0.d0) wbd(8) = wbd(8) + (wb_t - wb_s2)\n"
    "   wbd(1) = wbd(1) - wb_t\n"
    "   do psc=1,abs(p_split)\n")
sub(atm, "    enddo !p_split\n",
    "    enddo !p_split\n"
    f"   wb_t = {WA}\n"
    "   wbd(1) = wbd(1) + wb_t\n"
    "   wbd(3) = wbd(3) - wb_t\n")
sub(atm, "   call mpp_clock_end (id_subgridz)\n",
    f"   wb_t = {WA}\n"
    "   wbd(3) = wbd(3) + wb_t\n"
    "   wb_d2 = wb_t\n"
    "   call mpp_clock_end (id_subgridz)\n")
# physics -> dynamics update
sub(atm, "   real psum, qsum, psumb, qsumb, betad\n",
    "   real psum, qsum, psumb, qsumb, betad\n"
    "   real(kind=8) :: wb_t, wb_f0, wb_f1\n"
    "   integer :: wb_ix, wb_k\n")
sub(atm, "   if( nq<3 ) call mpp_error(FATAL, 'GFS phys must have 3 interactive tracers')\n\n   if (IAU_Data%in_interval) then\n",
    "   if( nq<3 ) call mpp_error(FATAL, 'GFS phys must have 3 interactive tracers')\n\n"
    f"   wb_t = {WA}\n"
    "   if (wb_d2 >= 0.d0) wbd(7) = wbd(7) + (wb_t - wb_d2)\n"
    "   wbd(4) = wbd(4) - wb_t\n\n"
    "   if (IAU_Data%in_interval) then\n")
sub(atm, "snowwat, graupel, nq_adv, flip_vc)   &\n", "snowwat, graupel, nq_adv, flip_vc, wbd)   &\n")
sub(atm, "private (nb, blen, i, j, k, k1, ix, q0, qwat, qt, tracer_name)",
    "private (nb, blen, i, j, k, k1, ix, q0, qwat, qt, tracer_name, wb_f0, wb_f1, wb_ix, wb_k)")
FILLSUM = ("     {v} = 0.d0\n"
           "     do wb_k = 1, npz\n"
           "       do wb_ix = 1, blen\n"
           "         {v} = {v} + IPD_Data(nb)%Stateout%gq0(wb_ix,wb_k,1)"
           "*abs(IPD_Data(nb)%Statein%prsi(wb_ix,wb_k)-IPD_Data(nb)%Statein%prsi(wb_ix,wb_k+1)) &\n"
           "                 *Atm(n)%gridstruct%area_64(Atm_block%index(nb)%ii(wb_ix),Atm_block%index(nb)%jj(wb_ix))\n"
           "       enddo\n"
           "     enddo\n")
FILL = ("     if (Atm(n)%flagstruct%fill_gfs) call fill_gfs(blen, npz, IPD_Data(nb)%Statein%prsi, "
        "IPD_Data(nb)%Stateout%gq0, 1.e-9_kind_phys)\n")
sub(atm, FILL, FILLSUM.format(v="wb_f0") + FILL + FILLSUM.format(v="wb_f1")
    + "     wbd(6) = wbd(6) + (wb_f1 - wb_f0)/9.80665d0\n")
sub(atm, "   call timing_off('GFS_TENDENCIES')\n",
    f"   wb_t = {WA}\n"
    "   wbd(4) = wbd(4) + wb_t\n"
    "   wbd(5) = wbd(5) - wb_t\n"
    "   call timing_off('GFS_TENDENCIES')\n")
sub(atm, "       call timing_off('FV_UPDATE_PHYS')\n",
    "       call timing_off('FV_UPDATE_PHYS')\n"
    f"   wb_t = {WA}\n"
    "   wbd(5) = wbd(5) + wb_t\n"
    "   wb_s2 = wb_t\n"
    "   wbd_n = wbd_n + 1\n"
    "   if (wb_area == 0.d0) wb_area = sum(Atm(n)%gridstruct%area_64(isc:iec,jsc:jec))\n"
    "   write(*,'(a,i7,9es24.15)') 'WBD ', wbd_n, wbd, wb_area\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBD").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
