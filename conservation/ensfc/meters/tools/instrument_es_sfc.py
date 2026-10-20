#!/usr/bin/env python3
"""Surface-component energy meters (diagnostic builds only): Noah-MP (soil and glacier), sea ice (sfc_sice), NSST,
and the atmosphere side of the hand-off. Apply on top of the atmosphere meters (instrument_eb_phys.py).
Usage: instrument_es_sfc.py <ufs-weather-model>
Per-column values go to esb(:, i) (energy_meter_common; zeroed per block in em_p02), are area x type-fraction
weighted in em_p05 into esg, and em_p12 prints the previous step's global sums as 'ESG kdt s v(10)' (s = 1..20).
Every anchor must match the stated number of times; nothing is written unless all match."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
itl = root / "Interstitials/UFS_SCM_NEPTUNE"
emc = itl / "energy_meter_common.F90"
p02 = itl / "em_p02.F90"
p05 = itl / "em_p05.F90"
p05m = itl / "em_p05.meta"
p12 = itl / "em_p12.F90"
cmp_ = itl / "GFS_surface_composites_post.F90"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
nst = root / "SFC_Layer/UFS/sfc_nst.f90"
edits = {}


def sub(path, old, new, count=1, after=None):
    s = edits.get(path) or path.read_text()
    if after is not None:  # replace the first `old` after the unique anchor `after`
        if s.count(after) != 1:
            sys.exit(f"ABORT {path.name}: anchor count {s.count(after)}: {after.strip()[:70]!r}")
        i = s.index(after)
        j = s.find(old, i)
        if j < 0:
            sys.exit(f"ABORT {path.name}: {old.strip()[:70]!r} not found after anchor")
        edits[path] = s[:j] + new + s[j + len(old):]
        return
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def pre(path, anchor, text, **kw):
    sub(path, anchor, text + anchor, **kw)


def post(path, anchor, text, **kw):
    sub(path, anchor, anchor + text, **kw)


# ---------------------------------------------------------------- energy_meter_common: storage, accumulation
sub(emc, "  public :: em_probe, emc, emg, emx, emkdt, emf\n",
    "  public :: em_probe, emc, emg, emx, emkdt, emf\n"
    "  public :: es_zero, es_acc, esb, esg, esgd, eskdt\n")
post(emc, "  integer, save :: emoff(emnp) = 0, emkdt(emnp) = -1\n",
     "  ! surface components: per-block column store esb, per-step global sums esg (esgd = previous step)\n"
     "  integer, parameter, public :: esnb = 120, esng = 200\n"
     "  real(kind=8), allocatable, save :: esb(:,:)\n"
     "  real(kind=8), save :: esg(esng) = 0.d0, esgd(esng) = 0.d0\n"
     "  integer, save :: eskdt = -1\n")
pre(emc, "end module energy_meter_common\n",
    "  subroutine es_zero(im)\n"
    "    integer, intent(in) :: im\n"
    "    if (allocated(esb)) then\n"
    "       if (size(esb, 2) < im) deallocate(esb)\n"
    "    endif\n"
    "    if (.not. allocated(esb)) allocate(esb(esnb, max(im, 256)))\n"
    "    esb(:, 1:im) = 0.d0\n"
    "    esb(61, 1:im) = -1.d34\n"
    "  end subroutine es_zero\n"
    "  subroutine es_acc(i, jj, a)\n"
    "    ! weights: land esb(5:59) x a*txl (soil -> 1:55, glacier -> 56:110); ice esb(60:84) x a*txi -> 111:135;\n"
    "    ! open water esb(85:109) x a*txo -> 136:160; atmosphere side x a -> 161:179\n"
    "    integer, intent(in) :: i, jj\n"
    "    real(kind=kind_phys), intent(in) :: a\n"
    "    real(kind=8) :: wl, wi, wo, d1, d2\n"
    "    wl = a*esb(1, i)\n"
    "    wi = a*esb(2, i)\n"
    "    wo = a*esb(3, i)\n"
    "    esb(6, i) = esb(7, i) - esb(6, i)\n"
    "    esb(7, i) = 0.d0\n"
    "    if (esb(4, i) == 1.d0) esg(1:55) = esg(1:55) + wl*esb(5:59, i)\n"
    "    if (esb(4, i) == 2.d0) esg(56:110) = esg(56:110) + wl*esb(5:59, i)\n"
    "    if (esb(60, i) > 0.d0) then\n"
    "       esb(61, i) = esb(62, i) - esb(61, i)\n"
    "       esb(62, i) = 0.d0\n"
    "       esg(111:135) = esg(111:135) + wi*esb(60:84, i)\n"
    "    endif\n"
    "    if (esb(85, i) > 0.d0) then\n"
    "       d1 = esb(87, i) - esb(86, i)\n"
    "       d2 = esb(88, i) - esb(87, i)\n"
    "       esb(86, i) = d1 + d2\n"
    "       esb(87, i) = d1\n"
    "       esb(88, i) = d2\n"
    "       esg(136:160) = esg(136:160) + wo*esb(85:109, i)\n"
    "    endif\n"
    "    esg(161:169) = esg(161:169) + a*emf(4:12, jj)\n"
    "    esg(170) = esg(170) + a\n"
    "    esg(171) = esg(171) + wl\n"
    "    esg(172) = esg(172) + wi\n"
    "    esg(173) = esg(173) + wo\n"
    "    esg(174) = esg(174) + wl*emf(11, jj)\n"
    "    esg(175) = esg(175) + wi*emf(11, jj)\n"
    "    esg(176) = esg(176) + wo*emf(11, jj)\n"
    "    esg(177) = esg(177) + wl*emf(10, jj)\n"
    "    esg(178) = esg(178) + wi*emf(10, jj)\n"
    "    esg(179) = esg(179) + wo*emf(10, jj)\n"
    "  end subroutine es_acc\n")

# ---------------------------------------------------------------- em_p02: zero the block store
post(p02, "                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, j0)\n",
     "    call es_zero(im)\n")

# ---------------------------------------------------------------- em_p05: roll and accumulate (needs garea)
sub(p05, "dtsfc1, dqsfc1,  &\n       errmsg, errflg)", "dtsfc1, dqsfc1, garea,  &\n       errmsg, errflg)")
post(p05, "    real(kind=kind_phys), intent(in) :: dqsfc1(:)\n",
     "    real(kind=kind_phys), intent(in) :: garea(:)\n")
pre(p05, "    errmsg = ''\n",
    "    if (kdt /= eskdt) then\n"
    "       esgd = esg\n"
    "       esg = 0.d0\n"
    "       eskdt = kdt\n"
    "    endif\n"
    "    do i = 1, im\n"
    "       call es_acc(i, j0+i, garea(i))\n"
    "    enddo\n")
pre(p05m, "[errmsg]\n",
    "[garea]\n  standard_name = cell_area\n  long_name = grid cell area\n  units = m2\n"
    "  dimensions = (horizontal_loop_extent)\n  type = real\n  kind = kind_phys\n  intent = in\n")

# ---------------------------------------------------------------- em_p12: reduce and print the previous step
sub(p12, "    real(kind=8) :: buf(10*emnp+12), rbuf(10*emnp+12)\n",
    "    real(kind=8) :: buf(10*emnp+12), rbuf(10*emnp+12)\n    real(kind=8) :: esr(esng)\n")
pre(p12, "       emg = 0.d0\n       emx = 0.d0\n",
    "       if (mpirank == mpiroot) then\n"
    "          call MPI_Reduce(MPI_IN_PLACE, esgd, esng, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "          do s = 1, esng/10\n"
    "             write(*,'(a,i6,i4,10es25.16)') 'ESG ', emkdt(12), s, esgd(10*(s-1)+1:10*s)\n"
    "          enddo\n"
    "       else\n"
    "          call MPI_Reduce(esgd, esr, esng, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "       endif\n")

# ---------------------------------------------------------------- composites_post: type fractions
sub(cmp_, "      implicit none\n", "      use energy_meter_common, only: esb\n      implicit none\n",
    after="   subroutine GFS_surface_composites_post_run (")
post(cmp_, "          txo   = max(zero, wfrac-txi)   ! txo = open water fraction\n",
     "          esb(1,i) = txl\n          esb(2,i) = txi\n          esb(3,i) = txo\n")

# ---------------------------------------------------------------- Noah-MP soil: heat content and per-call terms
post(lsm, "  public  :: noahmp_sflx\n",
     "  ! energy meter (diagnostic builds only): budget terms of the column just computed (J m-2, kg m-2)\n"
     "  real(kind=8), public, save :: esl(30) = 0.d0\n"
     "  real(kind=8), save :: es_tv0 = 0.d0, es_hcv = 0.d0, es_hs = 0.d0, es_hl = 0.d0\n"
     "  public :: es_hland, es_hcol\n")
ARGS = "parameters, nsnow, nsoil, isnow, stc, dzsnso, snice, snliq, smc, sh2o, sneqv, canice"
DECL = ("    type (noahmp_parameters), intent(in) :: parameters\n"
        "    integer, intent(in) :: nsnow, nsoil, isnow\n"
        "    real(kind=kind_phys), intent(in) :: stc(-nsnow+1:nsoil), dzsnso(-nsnow+1:nsoil), snice(-nsnow+1:0), &\n"
        "                                        snliq(-nsnow+1:0), smc(nsoil), sh2o(nsoil), sneqv, canice\n")
pre(lsm, "  subroutine noahmp_sflx (parameters, &\n",
    f"  subroutine es_hland({ARGS}, hs, hl)\n"
    "    ! land heat content, J m-2: sensible = Noah-MP heat capacities x (T - tfrz); latent = -hfus per kg of ice\n"
    "    ! (snow layers, layerless snow, soil ice, canopy ice). The canopy is massless (no sensible term).\n"
    + DECL +
    "    real(kind=8), intent(out) :: hs, hl\n"
    "    real(kind=8) :: sv, lv\n"
    "    integer :: iz\n"
    "    hs = 0.d0\n    hl = 0.d0\n"
    "    do iz = isnow+1, 0\n"
    "       sv = min(1.d0, snice(iz)/(dzsnso(iz)*denice))\n"
    "       lv = min(1.d0 - sv, snliq(iz)/(dzsnso(iz)*denh2o))\n"
    "       hs = hs + (cice*sv + cwat*lv)*dzsnso(iz)*(stc(iz) - tfrz)\n"
    "       hl = hl - hfus*snice(iz)\n"
    "    enddo\n"
    "    if (isnow == 0) hl = hl - hfus*sneqv\n"
    "    do iz = 1, nsoil\n"
    "       hs = hs + dzsnso(iz)*(stc(iz) - tfrz)*(sh2o(iz)*cwat + (1.0-parameters%smcmax(iz))*parameters%csoil &\n"
    "            + (parameters%smcmax(iz)-smc(iz))*cpair + (smc(iz)-sh2o(iz))*cice)\n"
    "       hl = hl - hfus*1000.d0*dzsnso(iz)*(smc(iz) - sh2o(iz))\n"
    "    enddo\n"
    "    hl = hl - hfus*canice\n"
    "  end subroutine es_hland\n"
    f"  subroutine es_seg(k, {ARGS})\n"
    + DECL +
    "    integer, intent(in) :: k\n"
    "    real(kind=8) :: hs, hl\n"
    f"    call es_hland({ARGS}, hs, hl)\n"
    "    esl(k) = hs - es_hs\n    esl(k+1) = hl - es_hl\n    es_hs = hs\n    es_hl = hl\n"
    "  end subroutine es_seg\n"
    "  subroutine es_hcol(parameters, glacier, nsoil, isnow, tss, zsnso, snice, snliq, smc, sh2o, sneqv, canice, hs, hl)\n"
    "    ! heat content from the driver's state (interface depths); glacier: snow + ice layers (glacier heat capacity)\n"
    "    type (noahmp_parameters), intent(in) :: parameters\n"
    "    logical, intent(in) :: glacier\n"
    "    integer, intent(in) :: nsoil, isnow\n"
    "    real(kind=kind_phys), intent(in) :: tss(-2:nsoil), zsnso(-2:nsoil), snice(-2:0), snliq(-2:0), smc(nsoil), &\n"
    "                                        sh2o(nsoil), sneqv, canice\n"
    "    real(kind=8), intent(out) :: hs, hl\n"
    "    real(kind=kind_phys) :: dz(-2:nsoil), zero1(1)\n"
    "    real(kind=8) :: zmid\n"
    "    integer :: iz, iz2\n"
    "    dz = 0.\n"
    "    do iz = isnow+1, nsoil\n"
    "       if (iz == isnow+1) then\n          dz(iz) = -zsnso(iz)\n       else\n"
    "          dz(iz) = zsnso(iz-1) - zsnso(iz)\n       endif\n"
    "    enddo\n"
    "    if (.not. glacier) then\n"
    "       call es_hland(parameters, 3, nsoil, isnow, tss, dz, snice, snliq, smc, sh2o, sneqv, canice, hs, hl)\n"
    "    else\n"
    "       zero1 = 0.\n"
    "       call es_hland(parameters, 3, 0, isnow, tss(-2:0), dz(-2:0), snice, snliq, zero1, zero1, sneqv, &\n"
    "                     0._kind_phys, hs, hl)\n"
    "       do iz = 1, nsoil\n"
    "          zmid = 0.5d0*dz(iz)\n"
    "          do iz2 = 1, iz-1\n             zmid = zmid + dz(iz2)\n          enddo\n"
    "          hs = hs + 1.d6*(0.8194d0 + 0.1309d0*zmid)*dz(iz)*(tss(iz) - tfrz)\n"
    "       enddo\n"
    "    endif\n"
    "  end subroutine es_hcol\n")
pre(lsm, "     troot  = 0.\n",
    "     esl = 0.d0\n     es_hcv = 0.d0\n     es_tv0 = tv\n"
    f"     call es_hland({ARGS}, es_hs, es_hl)\n"
    "     esl(1) = es_hs\n     esl(2) = es_hl\n")
pre(lsm, "    call energy (parameters,ice    ,vegtyp ,ist    ,nsnow  ,nsoil  , & !in\n",
    f"    call es_seg(3, {ARGS})\n")
pre(lsm, "    qsfcveg  = eah*ep_2/(sfcprs + epsm1*eah)\n",
    f"    call es_seg(5, {ARGS})\n"
    "    esl(11) = canhs*dt\n"
    "    esl(12) = es_hcv*(tv - es_tv0)\n"
    "    esl(13) = (sav+sag-(fira+fsh+fcev+fgev+fctr+ssoil+canhs)+pah)*dt\n"
    "    esl(29) = ssoil*dt\n"
    "    es_tv0 = tv\n")
pre(lsm, "   crop_active = .false.\n",
    f"   call es_seg(7, {ARGS})\n"
    "   esl(20) = es_hcv*(tv - es_tv0)\n")
pre(lsm, "    if(swdown.ne.0.) then\n      albedo = fsr / swdown\n",
    f"    call es_seg(9, {ARGS})\n"
    "    esl(26) = snow*dt\n    esl(27) = rain*dt\n")
pre(lsm, "    if(opt_tbot == 1) then\n       eflxb2  = 0.\n",
    "    esl(14) = eflxb*dt\n"
    "    esl(15) = 0.d0\n"
    "    do iz = isnow+1, nsoil\n"
    "       esl(15) = esl(15) + (stc(iz)-tbeg(iz))*dzsnso(iz)*hcpct(iz)\n"
    "    enddo\n"
    "    esl(15) = esl(15) - (ssoil + eflxb)*dt\n")
pre(lsm, "                  hm(j+1) = hm(j+1) + heatr    ! barlage\n",
    "                  if (imelt(j+1) == 0) esl(16) = esl(16) + heatr*dt\n")
pre(lsm, "               if (mliq(j)*mice(j)>0.) stc(j) = tfrz\n",
    "               if (mliq(j)*mice(j)>0.) esl(17) = esl(17) + (stc(j)-tfrz)/fact(j)*dt\n")
pre(lsm, "      pahv = max(pahv,-20.0)       ! put some artificial limits here for stability\n",
    "      esl(18) = pahv + fveg*pahg + (1.0-fveg)*pahb\n")
post(lsm, "      pahb = min(pahb,20.0)\n",
     "      esl(18) = (esl(18) - (pahv + fveg*pahg + (1.0-fveg)*pahb))*dt\n")
post(lsm, "         canice= max(0.,canice + (qints - icedrip)*dt)\n",
     "         esl(28) = (qints - icedrip)*dt\n")
post(lsm, "      ecan = qevac + qsubc - qdewc - qfroc\n",
     "      esl(19) = hfus*(qmeltc - qfrzc)*dt\n"
     "      esl(22) = (qsubc - qfroc)*dt\n"
     "      esl(21) = (fcev + fctr - hvap*(etran + qevac - qdewc) - hsub*(qsubc - qfroc))*dt\n"
     "      if (frozen_canopy) esl(30) = (hsub - hvap)*etran*dt\n")
pre(lsm, "   lheat = (latheag - hsub)*(qsnsub - qsnfro)*dt\n",
    "   esl(23) = (qsnsub - qsnfro)*dt\n")
pre(lsm, "      qsdew = 0.0\n      qseva = 0.0\n",
    "      esl(23) = esl(23) + (qseva - qsdew)*dt\n")
pre(lsm, "   stc(1) = stc(1) + lheat / (dzsnso(1) * (sh2o(1)*cwat",
    "   esl(24) = lheat\n")
post(lsm, "      stc(0)   = min(273.16, sfctmp)   ! temporary setup\n",
     "      esl(25) = esl(25) + cice*min(1._kind_phys, sneqv/(dzsnso(0)*denice))*dzsnso(0)*(stc(0)-tfrz)\n")
post(lsm, "        canhs = dtv*hcv/dt\n", "        es_hcv = hcv\n")

# ---------------------------------------------------------------- Noah-MP glacier: latent recompute, bottom flux
post(gla, "  private :: atm_glacier\n", "  real(kind=8), public, save :: esgl(3) = 0.d0\n")
pre(gla, "   beg_wb = sneqv\n", "   esgl = 0.d0\n")
sub(gla, "     if(opt_gla == 2) then\n       edir = qvap - qdew\n       fgev = edir * lathea\n     end if\n",
    "     esgl(1) = fgev*dt\n"
    "     if(opt_gla == 2) then\n       edir = qvap - qdew\n       fgev = edir * lathea\n     end if\n"
    "     esgl(2) = fgev*dt\n")
post(gla, "                          eflxb     )\n", "      esgl(3) = eflxb*dt\n")

# ---------------------------------------------------------------- Noah-MP driver: per-call land budget
post(drv, "  use noahmp_glacier_globals, only : hvap_gla => hvap, hsub_gla => hsub, hfus_gla => hfus\n",
     "  use energy_meter_common, only: esb\n  use noahmp_glacier_routines, only: esgl\n")
post(drv, "  type(noahmp_parameters) :: parameters\n",
     "  real(kind=8) :: es_hs, es_hl, es_h0\n")
HC = ("snow_levels, temperature_snow_soil, interface_depth, &\n"
      "                   snow_level_ice, snow_level_liquid, soil_moisture_vol, soil_liquid_vol, snow_water_equiv, "
      "canopy_ice, es_hs, es_hl)\n")
post(drv, "      parameters%prcpiceden = rhonewsn1(i)\n",
     "      call es_hcol(parameters, vegetation_category == isice_table, nsoil, " + HC +
     "      es_h0 = es_hs + es_hl\n")
post(drv, "      runoff    (i)   = runoff_surface\n",
     "      esb(4,i) = 1.d0\n"
     "      if (vegetation_category == isice_table) esb(4,i) = 2.d0\n"
     "      esb(5,i) = esb(5,i) + 1.d0\n"
     "      esb(6,i) = es_h0\n"
     "      call es_hcol(parameters, vegetation_category == isice_table, nsoil, " + HC +
     "      esb(7,i) = es_hs + es_hl\n"
     "      esb(8,i) = sw_absorbed_total*delt\n"
     "      esb(9,i) = lw_absorbed_total*delt\n"
     "      esb(10,i) = sensible_heat_total*delt\n"
     "      esb(11,i) = latent_heat_total*delt\n"
     "      esb(12,i) = precip_adv_heat_total*delt\n"
     "      esb(13,i) = ground_heat_total*delt\n"
     "      esb(14,i) = (ecan(i) + etran(i) + edir(i))*delt\n"
     "      esb(15,i) = runoff(i)*delt\n"
     "      esb(16,i) = drain(i)*delt\n"
     "      esb(19,i) = glacier_snow_floor\n"
     "      esb(20,i) = radiation_lw_forcing*delt\n"
     "      esb(21,i) = sw_radiation_forcing*delt\n"
     "      esb(22,i) = precipitation_forcing*delt\n"
     "      if (vegetation_category == isice_table) then\n"
     "        esb(17,i) = snowfall*delt\n"
     "        esb(23:25,i) = esgl(1:3)\n"
     "      else\n"
     "        esb(17,i) = esl(26)\n"
     "        esb(23:52,i) = esl(1:30)\n"
     "      endif\n"
     "      esb(18,i) = esb(22,i) - esb(17,i)\n"
     "      esb(53,i) = 1000.d0*tprcp(i)\n"
     "      esb(54,i) = (snow_mp(i) + graupel_mp(i) + ice_mp(i))*delt\n"
     "      esb(55,i) = rainc_mp(i)*delt\n"
     "      esb(56,i) = rainn_mp(i)*delt\n"
     "      esb(57,i) = 1000.d0*tprcp(i)*srflag(i)\n")

# ---------------------------------------------------------------- sea ice (fixed form)
post(ice, "      use funcphys, only : fpvs\n", "      use energy_meter_common, only: esb\n",
     after="      subroutine sfc_sice_run")
post(ice, "      logical :: flag(im)\n",
     "      real (kind=kind_phys) :: es_t0(im)\n      real (kind=8) :: es_h\n")
pre(ice, "          if (srflag(i) > zero) then\n            ep(i)    = ep(i)*(one-srflag(i))\n",
    "          esb(60,i) = esb(60,i) + 1.d0\n"
    "          es_h = es_hice(hice(i), weasd(i), tiice(i,1), tiice(i,2))\n"
    "          if (esb(61,i) < -1.d33) esb(61,i) = es_h\n"
    "          esb(63,i) = esb(63,i) - es_h\n"
    "          if (srflag(i) > zero) esb(75,i) = esb(75,i)\n"
    "     &      + 1000.d0*tprcp(i)*srflag(i)\n")
post(ice, "            tprcp(i) = tprcp(i)*(one-srflag(i))\n          endif\n",
     "          es_h = es_hice(hice(i), weasd(i), tiice(i,1), tiice(i,2))\n"
     "          esb(63,i) = esb(63,i) + es_h\n"
     "          esb(64,i) = esb(64,i) - es_h\n")
post(ice, "            snowd(i) = hice(i) + hice(i)\n!           print *,'fix: decrease snow depth to:',snowd(i)\n          endif\n",
     "          es_h = es_hice(hice(i), 1000.d0*snowd(i), stsice(i,1),\n"
     "     &                   stsice(i,2))\n"
     "          esb(64,i) = esb(64,i) + es_h\n"
     "          esb(65,i) = esb(65,i) - es_h\n"
     "          es_t0(i) = tice(i)\n")
post(ice, "     &       snowd, hice, stsice, tice, snof, snowmt, gflux )           !\n",
     "      do i = 1, im\n"
     "        if (flag(i)) then\n"
     "          es_h = es_hice(hice(i), 1000.d0*snowd(i), stsice(i,1),\n"
     "     &                   stsice(i,2))\n"
     "          esb(65,i) = esb(65,i) + es_h\n"
     "          esb(66,i) = esb(66,i) - es_h\n"
     "          tem = tice(i) - es_t0(i)\n"
     "          t12 = es_t0(i)*es_t0(i)\n"
     "          esb(67,i) = esb(67,i) + (sneti(i)-hfi(i)-hfd(i)*tem)*delt\n"
     "          esb(68,i) = esb(68,i) + focn(i)*delt\n"
     "          esb(69,i) = esb(69,i) + sneti(i)*delt\n"
     "          esb(70,i) = esb(70,i) + (dlwflx(i) - sfcemis(i)*sbc*t12*t12\n"
     "     &      - 4.d0*sfcemis(i)*sbc*t12*es_t0(i)*tem)*delt\n"
     "          esb(71,i) = esb(71,i) + (hfi(i) + dlwflx(i)\n"
     "     &      - sfcemis(i)*sbc*t12*t12 - evapi(i) + rch(i)*tem)*delt\n"
     "          esb(72,i) = esb(72,i) + (evapi(i) + (hfd(i)\n"
     "     &      - 4.d0*sfcemis(i)*sbc*t12*es_t0(i) - rch(i))*tem)*delt\n"
     "          esb(80,i) = esb(80,i) + evapi(i)/hvap*delt\n"
     "        endif\n"
     "      enddo\n")
post(ice, "          snwdph(i) = weasd(i) * dsi             ! snow depth in mm\n",
     "          es_h = es_hice(hice(i), weasd(i), tiice(i,1), tiice(i,2))\n"
     "          esb(66,i) = esb(66,i) + es_h\n"
     "          esb(62,i) = es_h\n"
     "          esb(73,i) = hflxi(i)*delt\n"
     "          esb(74,i) = evapi(i)*delt\n"
     "          esb(76,i) = dlwflx(i)*delt\n"
     "          t12 = tice(i)*tice(i)\n"
     "          esb(77,i) = sfcemis(i)*sbc*t12*t12*delt\n"
     "          esb(78,i) = sfcnsw(i)*delt\n")
pre(ice, "                hice(i) = hice(i) - h2*ci*(stsice(i,2) - tfi)/ (li*delt)\n",
    "                esb(79,i) = esb(79,i) + di*h2*ci*(stsice(i,2) - tfi)\n"
    "     &                    *(1.d0 - 1.d0/delt)\n"
    "                esb(84,i) = esb(84,i) + 1.d0\n")
sub(ice, "      contains\n", "      contains\n"
     "      real (kind=8) function es_hice(h, w, t1k, t2k)\n"
     "!     Winton heat content, liquid at tfi = -0.054 C reference, J m-2\n"
     "      real (kind=kind_phys), intent(in) :: h, w, t1k, t2k\n"
     "      real (kind=8) :: a, b\n"
     "      a = min(t1k - t0c, -0.054d0 - 1.d-4)\n"
     "      b = min(t2k - t0c, -0.054d0 - 1.d-4)\n"
     "      es_hice = 917.d0*0.5d0*h*(2054.d0*(a + 0.054d0)\n"
     "     &        - 3.34d5*(1.d0 + 0.054d0/a))\n"
     "     &        + 917.d0*0.5d0*h*(2054.d0*(b + 0.054d0) - 3.34d5)\n"
     "     &        - 3.34d5*w\n"
     "      end function es_hice\n", after="      subroutine sfc_sice_run")

# ---------------------------------------------------------------- NSST
post(nst, "  use machine ,               only : kind_phys, kp => kind_phys\n",
     "  use energy_meter_common, only: esb\n")
post(nst, "          call rhocoef(tsea,sss,rho_w,alpha,beta)          ! alpha & beta\n",
     "          esb(85,i) = esb(85,i) + 1.d0\n"
     "          esb(86,i) = rho_w*cp_w*xt(i)\n"
     "          esb(87,i) = esb(86,i)\n"
     "          esb(88,i) = esb(86,i)\n"
     "          esb(91,i) = 0.d0\n")
post(nst, "          f_nsol   = hflx(i) + evap(i) + ulwflx(i) - dlwflx(i) + omg_sh*qrain(i)\n",
     "          esb(89,i) = f_nsol*timestep\n"
     "          esb(90,i) = nswsfc(i)*timestep\n"
     "          esb(92,i) = omg_sh*qrain(i)*timestep\n"
     "          esb(93,i) = ulwflx(i)*timestep\n"
     "          esb(94,i) = dlwflx(i)*timestep\n"
     "          esb(95,i) = hflx(i)*timestep\n"
     "          esb(96,i) = evap(i)*timestep\n"
     "          esb(102,i) = 1.d3*rain(i)\n")
post(nst, "                         xt(i),xs(i),xu(i),xv(i),xz(i),xzts(i),xtts(i))\n",
     "             esb(87,i) = rho_w*cp_w*xt(i)\n")
post(nst, "                q_warm = fw*nswsfc(i)-f_nsol    !total heat absorbed in warm layer\n",
     "                esb(91,i) = q_warm*timestep\n")
pre(nst, "          call get_dtzm_point(xt(i),xz(i),dt_cool(i),z_c(i), zsea1,zsea2,dtz)\n",
    "          esb(88,i) = rho_w*cp_w*xt(i)\n")
post(nst, "          hflx(i) = hflx(i) + bets * hflxs - ptem * evaps\n",
     "          esb(99,i) = (bets*hflxs - ptem*evaps)*timestep\n"
     "          esb(100,i) = alps*evaps*timestep\n")
pre(nst, "          tem     = one / rho_a(i)\n",
    "          esb(97,i) = hflx(i)*timestep\n"
    "          esb(98,i) = evap(i)*timestep\n"
    "          esb(101,i) = sfcemis(i)*sbc*tskin(i)**4*timestep\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preES").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
