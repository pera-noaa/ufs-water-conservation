#!/usr/bin/env python3
"""Land <-> atmosphere water meters (diagnostic builds only; v1 snapshot layout; apply after instrument_wb.py and
instrument_wb_phys.py, which add the finalize print and WBP).
Usage: python3 instrument_wb_land.py <ufs_model.fd>
Per step, summed over land (weight = cell area * land fraction, kg), cumulative per rank:
  WBL kdt | 1 Noah-MP evapotranspiration debited from the land, (ecan + etran + edir)*dt (glacier: edir)
          | 2 water the atmosphere is given for it, evap_lnd * rho_a * dt (rho_a as satmedmfvdifq books it)
          | 3 what noahmpdrv thinks it handed over, evap_lnd * density * dt
          | 4 precipitation Noah-MP used (its own prcp in the water balance) | 5 precipitation the host handed it,
          1000*tprcp (previous step) | 6 Noah-MP's own water-balance error errwat (soil: whole column; glacier: snow)
          | 7 land area (m2, per step) | 8, 9 unweighted: water satmedmfvdifq actually adds from the surface flux,
          dt*evap*del1/(g*dz1), and what it books, dt*evap*rho_a | 10 unused
printed by noahmpdrv when the step index changes (cumulative through the previous step) and at finalize.
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
cmp_ = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.F90"
pbl = root / "PBL/SATMEDMF/satmedmfvdifq.F"
mpt = root / "MP/Thompson/mp_thompson.F90"
edits = {}


def sub(path, old, new, after=None):
    s = edits.get(path) or path.read_text()
    if after is not None:  # replace the first `old` after the unique anchor `after`
        if s.count(after) != 1:
            sys.exit(f"ABORT {path.name}: anchor count {s.count(after)}: {after.strip()[:60]!r}")
        i = s.index(after)
        j = s.find(old, i)
        if j < 0:
            sys.exit(f"ABORT {path.name}: {old.strip()[:60]!r} not found after anchor")
        edits[path] = s[:j] + new + s[j + len(old):]
        return
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


# Noah-MP soil: expose errwat and prcp of the column just computed
sub(lsm, "  public  :: noahmp_sflx\n",
    "  public  :: noahmp_sflx\n  real(kind=8), public, save :: wbl_errwat = 0.d0, wbl_prcp = 0.d0\n")
sub(lsm, "   else                 !kwm\n      errwat = 0.0      !kwm\n   endif\n",
    "   else                 !kwm\n      errwat = 0.0      !kwm\n   endif\n   wbl_errwat = errwat\n   wbl_prcp = prcp\n")
# Noah-MP glacier: same
sub(gla, "  private :: atm_glacier\n",
    "  private :: atm_glacier\n  real(kind=8), public, save :: wbl_errwat_g = 0.d0, wbl_prcp_g = 0.d0\n")
sub(gla, "   errwat = end_wb-beg_wb-(prcp-edir-runsrf-runsub)*dt\n",
    "   errwat = end_wb-beg_wb-(prcp-edir-runsrf-runsub)*dt\n   wbl_errwat_g = errwat\n   wbl_prcp_g = prcp\n")
# driver: per-column store, step-change print
sub(drv, "      use module_sf_noahmplsm\n",
    "      use module_sf_noahmplsm\n      use noahmp_glacier_routines, only: wbl_errwat_g, wbl_prcp_g\n",
    after="!> This module contains the CCPP-compliant NoahMP land surface model driver.\n")
sub(drv, "      public :: noahmpdrv_init, noahmpdrv_run\n",
    "      public :: noahmpdrv_init, noahmpdrv_run\n"
    "      real(kind=8), public, save :: wbl(10) = 0.d0, wbl_dt = 0.d0\n"
    "      integer, public, save :: wbl_kdt = -1\n"
    "      real(kind=8), public, allocatable, save :: wbl_et(:), wbl_pr(:), wbl_tp(:), wbl_ew(:), wbl_rn(:)\n")
sub(drv, "  do i = 1, im\n",
    "  if (itime /= wbl_kdt) then\n"
    "    if (wbl_kdt >= 0) write(*,'(a,i7,10es24.15)') 'WBL ', wbl_kdt, wbl\n"
    "    wbl_kdt = itime\n"
    "  endif\n"
    "  if (allocated(wbl_et)) then\n"
    "    if (size(wbl_et) < im) deallocate(wbl_et, wbl_pr, wbl_tp, wbl_ew, wbl_rn)\n"
    "  endif\n"
    "  if (.not. allocated(wbl_et)) allocate(wbl_et(im), wbl_pr(im), wbl_tp(im), wbl_ew(im), wbl_rn(im))\n"
    "  wbl_dt = delt\n"
    "  do i = 1, im\n")
sub(drv, "      edir      (i)   = evaporation_soil\n",
    "      edir      (i)   = evaporation_soil\n"
    "      if ( vegetation_category == isice_table ) then\n"
    "        wbl_et(i) = edir(i)*delt\n"
    "        wbl_ew(i) = wbl_errwat_g\n"
    "        wbl_pr(i) = wbl_prcp_g\n"
    "      else\n"
    "        wbl_et(i) = (ecan(i)+etran(i)+edir(i))*delt\n"
    "        wbl_ew(i) = wbl_errwat\n"
    "        wbl_pr(i) = wbl_prcp\n"
    "      endif\n"
    "      wbl_tp(i) = 1000.0d0*tprcp(i)/delt\n")
sub(drv, "      hflx(i) = hflx(i) / density / con_cp\n",
    "      wbl_rn(i) = density\n      hflx(i) = hflx(i) / density / con_cp\n")
# composites: land-weighted sums with the PBL's own rho_a
sub(cmp_, "      implicit none\n",
    "      use noahmpdrv, only: wbl, wbl_et, wbl_pr, wbl_tp, wbl_ew, wbl_rn, wbl_dt\n      implicit none\n",
    after="   subroutine GFS_surface_composites_post_run (")
sub(cmp_, "          evap(i)   = txl*evap_lnd(i)  + txi*evap_ice(i)  + txo*evap_wat(i)\n",
    "          evap(i)   = txl*evap_lnd(i)  + txi*evap_ice(i)  + txo*evap_wat(i)\n"
    "          if (txl > 0.) then\n"
    "            wbl(1) = wbl(1) + garea(i)*txl*wbl_et(i)\n"
    "            wbl(2) = wbl(2) + garea(i)*txl*evap_lnd(i)*wbl_dt &\n"
    "                     *prsl1(i)/(rd*t1(i)*(1.+rvrdm1*max(q1(i),1.e-8)))\n"
    "            wbl(3) = wbl(3) + garea(i)*txl*evap_lnd(i)*wbl_rn(i)*wbl_dt\n"
    "            wbl(4) = wbl(4) + garea(i)*txl*wbl_pr(i)*wbl_dt\n"
    "            wbl(5) = wbl(5) + garea(i)*txl*wbl_tp(i)*wbl_dt\n"
    "            wbl(6) = wbl(6) + garea(i)*txl*wbl_ew(i)\n"
    "            wbl(7) = wbl(7) + garea(i)*txl\n"
    "          endif\n")
# PBL: what is really added vs booked (fixed form, <= 72 columns)
sub(pbl, "      implicit none\n", "      use noahmpdrv, only: wbl\n      implicit none\n",
    after="      subroutine satmedmfvdifq_run(")
sub(pbl, "        dqsfc(i) = rho_a(i) * hvap * evap(i)\n",
    "        dqsfc(i) = rho_a(i) * hvap * evap(i)\n"
    "        wbl(8) = wbl(8) + dt2*evap(i)*del(i,1)/\n"
    "     &           (grav*(zi(i,2)-zi(i,1)))\n"
    "        wbl(9) = wbl(9) + dt2*evap(i)*rho_a(i)\n")
# final print
sub(mpt, "         use GFS_physics_post, only: wbp, wbp_kdt\n",
    "         use GFS_physics_post, only: wbp, wbp_kdt\n         use noahmpdrv, only: wbl, wbl_kdt\n")
sub(mpt, "         write(*,'(a,i7,3es24.15)') 'WBP ', wbp_kdt, wbp\n",
    "         write(*,'(a,i7,3es24.15)') 'WBP ', wbp_kdt, wbp\n"
    "         write(*,'(a,i7,10es24.15)') 'WBL ', wbl_kdt, wbl\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBL").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
