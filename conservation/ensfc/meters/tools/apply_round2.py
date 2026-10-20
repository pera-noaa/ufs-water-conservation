#!/usr/bin/env python3
"""Round-2 candidate surface energy fixes, each behind a run-time switch for experiments
(environment variable ESFIX = comma-separated tags; diagnostic builds only, the final diffs are unconditional).
Usage: apply_round2.py <ufs-weather-model>
  QR1  NSST: rain is m per step, qrain and sep need kg m-2 s-1
  CH1  Noah-MP vege_flux: massless canopy (no hcv damping), so the canopy balance closes and canhs = 0
  CH2  Noah-MP vege_flux: canopy heat storage over the whole step, canhs = hcv*(tv_new - tv_start)/dt
  CMC  Noah-MP canwater: heat the canopy books but cannot carry (evaporation cap, frozen-canopy transpiration at
       hsub, canopy melt/freeze latent heat) goes to the top soil layer, as NM11 does for the ground
  SL1  Noah-MP combine: sensible heat of snow layers removed or merged without mixing goes to the top soil layer
  FL1  sfc_sice ice3lay: snow-ice formation keeps each layer's heat content (snow joins at -li)
  PH1  GFS_MP_generic_post: convective precipitation that the host calls snow pays hfus in the lowest layer
  PH2  Noah-MP: convective precipitation phase from the host's rule (srflag), not T1 < tfrz
  PH3  Noah-MP glacier: precipitation phase from the host's srflag, not the T rule
  SW1  Noah-MP: absorbed SW = the radiation's net SW for the land (radiation-time albedo, its band fluxes)
Every anchor must match exactly once; nothing is written unless all match."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
drvm = root / "SFC_Models/Land/Noahmp/noahmpdrv.meta"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
nst = root / "SFC_Layer/UFS/sfc_nst.f90"
mpp = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.F90"
mppm = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.meta"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def pre(path, anchor, text):
    sub(path, anchor, text + anchor)


def post(path, anchor, text):
    sub(path, anchor, anchor + text)


def meta_add(path, entries, optional=True):
    s = edits.get(path) or path.read_text()
    add = ""
    for name, sn, ln, units, dims, typ, kind in entries:
        add += (f"[{name}]\n  standard_name = {sn}\n  long_name = {ln}\n  units = {units}\n  dimensions = {dims}\n"
                f"  type = {typ}\n" + (f"  kind = {kind}\n" if kind else "") + "  intent = in\n"
                + ("  optional = True\n" if optional else ""))
    edits[path] = s.rstrip("\n") + "\n" + add


def switch_fn(name):
    return (f"  logical function {name}(tag)\n"
            "    ! experiment switch (diagnostic builds only): ESFIX = comma-separated tags\n"
            "    character(len=*), intent(in) :: tag\n"
            "    character(len=256), save :: v = ' '\n"
            "    logical, save :: got = .false.\n"
            "    if (.not. got) then\n"
            "       call get_environment_variable('ESFIX', v)\n"
            "       got = .true.\n"
            "    endif\n"
            f"    {name} = index(','//trim(v)//',', ','//tag//',') > 0\n"
            f"  end function {name}\n")


# ------------------------------------------------------------------ switches
pre(lsm, "  subroutine noahmp_sflx (parameters, &\n", switch_fn("esfix_l"))
pre(gla, "  subroutine noahmp_glacier (&\n", switch_fn("esfix_g"))
pre(drv, "  subroutine noahmpdrv_run", switch_fn("esfix_d"))
pre(nst, "  subroutine sfc_nst_run", switch_fn("esfix_n"))
pre(mpp, "      subroutine GFS_MP_generic_post_run(", switch_fn("esfix_m"))
pre(ice, "      subroutine ice3lay\n",
    "      logical function esfixi(tag)\n"
    "      character(len=*), intent(in) :: tag\n"
    "      character(len=256), save :: v = ' '\n"
    "      logical, save :: got = .false.\n"
    "      if (.not. got) then\n"
    "        call get_environment_variable('ESFIX', v)\n"
    "        got = .true.\n"
    "      endif\n"
    "      esfixi = index(','//trim(v)//',', ','//tag//',') > 0\n"
    "      end function esfixi\n")

# ------------------------------------------------------------------ QR1
sub(nst, "    real(kind=kind_phys) :: ulwflx(im), nswsfc(im)\n",
    "    real(kind=kind_phys) :: ulwflx(im), nswsfc(im), rain_rate\n")
sub(nst, "          tem      = (1.0e3_kp * rain(i) / rho_w) * alfac * cp_w\n",
    "          rain_rate = rain(i)\n"
    "          if (esfix_n('QR1')) rain_rate = 1.0e3_kp*rain(i)/timestep   ! rain is m per step\n"
    "          tem      = (1.0e3_kp * rain_rate / rho_w) * alfac * cp_w\n")
sub(nst, "          sep      = sss*(evap(i)/le-rain(i))/rho_w\n",
    "          sep      = sss*(evap(i)/le-rain_rate)/rho_w\n")

# ------------------------------------------------------------------ CH1, CH2
pre(lsm, "  real (kind=kind_phys) :: hcv          !canopy heat capacity j/m2/k, C.He added",
    "  real (kind=kind_phys) :: tv_start, hcv_eff\n")
pre(lsm, "      loop1: do iter = 1, niterc", "      tv_start = tv\n")
post(lsm, "        hcv = fveg*(parameters%cbiom*vaie*cwat + canliq*cwat/denh2o + canice*cice/denice) !j/m2/k\n",
     "        hcv_eff = hcv\n        if (esfix_l('CH1')) hcv_eff = 0.\n")
post(lsm, "        b   = sav-irc-shc-evc-tr+pahv                          !additional w/m2\n",
     "        if (esfix_l('CH2')) b = b - hcv*(tv - tv_start)/dt\n")
sub(lsm, "        a   = fveg*(4.*cir*tv**3 + csh + (cev+ctr)*destv) + hcv/dt !volumetric heat capacity\n",
    "        a   = fveg*(4.*cir*tv**3 + csh + (cev+ctr)*destv) + hcv_eff/dt !volumetric heat capacity\n")
sub(lsm, "        canhs = dtv*hcv/dt\n",
    "        canhs = dtv*hcv_eff/dt\n        if (esfix_l('CH2')) canhs = hcv*(tv + dtv - tv_start)/dt\n")

# ------------------------------------------------------------------ CMC (canopy heat returned to the top soil layer)
post(lsm, "  public  :: noahmp_sflx\n",
     "  real(kind=kind_phys), save :: canopy_heat = 0.  ! J m-2 the canopy books but cannot carry, to the top soil layer\n"
     "  real(kind=kind_phys), public, save :: host_fpcv = -1.  ! host's convective frozen fraction (< 0: T1 rule)\n"
     "  real(kind=kind_phys), public, save :: sw_target = -1.  ! absorbed SW imposed by the driver (< 0: own)\n")
pre(lsm, "       qevac = min(canliq/dt,qevac)\n",
    "       canopy_heat = 0.\n"
    "       if (esfix_l('CMC')) canopy_heat = (qevac - min(canliq/dt,qevac))*hvap*dt\n")
pre(lsm, "      qsubc = min(canice/dt,qsubc)",
    "      if (esfix_l('CMC')) canopy_heat = canopy_heat + (qsubc - min(canice/dt,qsubc))*hsub*dt\n")
post(lsm, "      ecan = qevac + qsubc - qdewc - qfroc\n",
     "      if (esfix_l('CMC')) then\n"
     "        if (frozen_canopy) canopy_heat = canopy_heat + (hsub - hvap)*etran*dt\n"
     "        canopy_heat = canopy_heat - hfus*(qmeltc - qfrzc)*dt\n"
     "      endif\n")
post(lsm, "   lheat = (latheag - hsub)*(qsnsub - qsnfro)*dt\n", "   lheat = lheat + canopy_heat\n")

# ------------------------------------------------------------------ SL1
post(lsm, "    integer :: isnow_old             ! number of top snow layer\n",
     "    real(kind=kind_phys) :: hs_comb\n")
pre(lsm, "       isnow_old = isnow\n\n       do j = isnow_old+1,0\n",
    "       hs_comb = snow_sensible(nsnow, isnow, stc, snice, snliq, dzsnso)\n")
SLC = ("       if (esfix_l('SL1')) call snow_heat_to_soil(parameters, nsnow, nsoil, isnow, stc, snice, snliq, dzsnso, "
       "sh2o, sice, hs_comb)\n")
pre(lsm, "       if(isnow ==0) return   ! mb: get out if no longer multi-layer\n", SLC)
pre(lsm, "  end subroutine combine\n", SLC)
pre(lsm, "  subroutine noahmp_sflx (parameters, &\n",
    "  real(kind=kind_phys) function snow_sensible(nsnow, isnow, stc, snice, snliq, dzsnso)\n"
    "    ! sensible heat of the snow layers relative to tfrz (Noah-MP snow heat capacity), J m-2\n"
    "    integer, intent(in) :: nsnow, isnow\n"
    "    real(kind=kind_phys), intent(in) :: stc(-nsnow+1:), snice(-nsnow+1:), snliq(-nsnow+1:), dzsnso(-nsnow+1:)\n"
    "    real(kind=kind_phys) :: sv, lv\n"
    "    integer :: iz\n"
    "    snow_sensible = 0.\n"
    "    do iz = isnow+1, 0\n"
    "       if (dzsnso(iz) > 0.) then\n"
    "          sv = min(1._kind_phys, snice(iz)/(dzsnso(iz)*denice))\n"
    "          lv = min(1._kind_phys - sv, snliq(iz)/(dzsnso(iz)*denh2o))\n"
    "          snow_sensible = snow_sensible + (cice*sv + cwat*lv)*dzsnso(iz)*(stc(iz) - tfrz)\n"
    "       endif\n"
    "    enddo\n"
    "  end function snow_sensible\n"
    "  subroutine snow_heat_to_soil(parameters, nsnow, nsoil, isnow, stc, snice, snliq, dzsnso, sh2o, sice, hs)\n"
    "    ! snow layers removed or merged without mixing: their lost sensible heat goes to the top soil layer\n"
    "    type (noahmp_parameters), intent(in) :: parameters\n"
    "    integer, intent(in) :: nsnow, nsoil, isnow\n"
    "    real(kind=kind_phys), intent(inout) :: stc(-nsnow+1:)\n"
    "    real(kind=kind_phys), intent(in) :: snice(-nsnow+1:), snliq(-nsnow+1:), dzsnso(-nsnow+1:), sh2o(:), sice(:)\n"
    "    real(kind=kind_phys), intent(inout) :: hs\n"
    "    real(kind=kind_phys) :: hn\n"
    "    hn = snow_sensible(nsnow, isnow, stc, snice, snliq, dzsnso)\n"
    "    stc(1) = stc(1) + (hs - hn)/(dzsnso(1)*(sh2o(1)*cwat + (1.0-parameters%smcmax(1))*parameters%csoil &\n"
    "             + (parameters%smcmax(1)-sh2o(1)-sice(1))*cpair + sice(1)*cice))\n"
    "    hs = hn\n"
    "  end subroutine snow_heat_to_soil\n")

# ------------------------------------------------------------------ FL1 (fixed form)
post(ice, "     &,                        c1, ip, k12, k32, tsf, f1, tmelt, bmelt\n",
     "      real (kind=kind_phys) :: hold_fl, e_fl, b_fl\n")
sub(ice, "            hice (i) = hice(i) + hsni\n",
    "            hold_fl  = hice(i)\n"
    "            hice (i) = hice(i) + hsni\n"
    "            if (esfixi('FL1')) then\n"
    "!             flooded snow (heat content -li) joins both layers\n"
    "              e_fl = min(stsice(i,2)-t0c, tfi0)\n"
    "              e_fl = (hold_fl*(ci*(e_fl-tfi)-li) - hsni*li)/hice(i)\n"
    "              stsice(i,2) = tfi + (e_fl + li)/ci + t0c\n"
    "              b_fl = min(stsice(i,1)-t0c, tfi0)\n"
    "              e_fl = (hold_fl*(ci*(b_fl-tfi)-li*(one-tfi/b_fl))\n"
    "     &             - hsni*li)/hice(i)\n"
    "              b_fl = e_fl + ci*tfi + li\n"
    "              stsice(i,1) = (b_fl - sqrt(b_fl*b_fl\n"
    "     &                    - 4.0_kind_phys*ci*li*tfi))/(ci+ci) + t0c\n"
    "            endif\n")

# ------------------------------------------------------------------ PH1
sub(mpp, "        iopt_lake, iopt_lake_clm, lkm, use_lake_model, errmsg, errflg)\n",
    "        iopt_lake, iopt_lake_clm, lkm, use_lake_model, errmsg, errflg, con_hfus, con_cp, garea)\n")
post(mpp, "      logical, intent(in) :: cal_pre, lssav, ldiag3d, qdiag3d, cplflx, cplchm, cpllnd, progsigma, exticeden\n",
     "      real(kind=kind_phys), intent(in) :: con_hfus, con_cp\n"
     "      real(kind=kind_phys), dimension(:), intent(in), optional :: garea\n")
post(mpp, "            else\n              crain = zero\n              csnow = rainc(i)\n            endif\n",
     "            ! convective precipitation the host calls snow froze in the atmosphere, which pays hfus\n"
     "            if (csnow > zero) then\n"
     "              if (esfix_m('PH1')) gt0(i,1) = gt0(i,1) + con_hfus*rhowater*csnow*con_g &\n"
     "                                             / (con_cp*(prsi(i,1)-prsi(i,2)))\n"
     "            endif\n")
meta_add(mppm, [("con_hfus", "latent_heat_of_fusion_of_water_at_0C", "latent heat of fusion", "J kg-1", "()", "real",
                 "kind_phys"),
                ("con_cp", "specific_heat_of_dry_air_at_constant_pressure", "specific heat of dry air at constant pressure",
                 "J kg-1 K-1", "()", "real", "kind_phys")], optional=False)
meta_add(mppm, [("garea", "cell_area", "grid cell area", "m2", "(horizontal_loop_extent)", "real", "kind_phys")])

# ------------------------------------------------------------------ PH2, PH3
post(lsm, "          if(sfctmp < tfrz) fpcv = 1.0\n", "          if(host_fpcv >= 0.) fpcv = host_fpcv\n")
post(gla, "  real (kind=kind_phys)            :: hvap   = 2.5104e06 !< latent heat of vaporization (j/kg); host value set in noahmpdrv_run\n",
     "  real (kind=kind_phys)            :: host_fpice = -1.0 !< host frozen fraction of precipitation (< 0: T rule)\n")
pre(gla, "     bdfall = min(120.,67.92+51.25*exp((sfctmp-tfrz)/2.59)) !mb: change to min v3.7\n",
    "     if (host_fpice >= 0.) fpice = host_fpice\n")
sub(drv, "  use noahmp_glacier_globals, only : hvap_gla => hvap, hsub_gla => hsub, hfus_gla => hfus\n",
    "  use noahmp_glacier_globals, only : hvap_gla => hvap, hsub_gla => hsub, hfus_gla => hfus, host_fpice\n")
pre(drv, "        call noahmp_glacier (",
    "        host_fpice = -1.\n        if (esfix_d('PH3')) host_fpice = srflag(i)\n")
pre(drv, "        call noahmp_sflx (parameters                                          , &\n",
    "        host_fpcv = -1.\n"
    "        if (esfix_d('PH2') .and. rainc_mp(i) > 0.) then\n"
    "          host_fpcv = 0.\n"
    "          if (srflag(i)*precipitation_forcing - (snow_mp(i)+graupel_mp(i)+ice_mp(i)) > 0.5*rainc_mp(i)) &\n"
    "            host_fpcv = 1.\n"
    "        endif\n")

# ------------------------------------------------------------------ SW1
pre(lsm, "     emv = 1. - exp(-(elai+esai)/1.0)\n",
    "     if (sw_target >= 0. .and. fsa > 0.) then\n"
    "        sav = sav*sw_target/fsa\n"
    "        sag = sag*sw_target/fsa\n"
    "        fsr = fsr + fsa - sw_target\n"
    "        fsa = sw_target\n"
    "     endif\n")
post(drv, "  type(noahmp_parameters) :: parameters\n",
     "  real(kind=kind_phys) :: swa\n")
sub(drv, "      iter                                                       &\n      )\n",
    "      iter, adjvisbmd, adjvisdfd, adjnirbmd, adjnirdfd, lsswr     &\n      )\n")
post(drv, "  integer, optional                      , intent(in)    :: iter       ! surface iteration (ccpp loop counter)\n",
     "  real(kind=kind_phys), dimension(:), optional, intent(in) :: adjvisbmd, adjvisdfd, adjnirbmd, adjnirdfd\n"
     "  logical, optional, intent(in) :: lsswr\n")
post(drv, "  first_iter = .true.\n  if (present(iter)) first_iter = iter == 1\n",
     "  if (present(adjvisbmd) .and. first_iter) then\n"
     "    if (itime /= col_kdt) then\n      col_kdt = itime\n      col_off = 0\n    endif\n"
     "    if (.not. allocated(albrad)) then\n      allocate(albrad(4, 100000))\n      albrad = -1.\n    endif\n"
     "    if (present(lsswr)) then\n"
     "      if (lsswr) then\n"
     "        do i = 1, im\n"
     "          albrad(1, col_off+i) = albdvis(i)\n          albrad(2, col_off+i) = albivis(i)\n"
     "          albrad(3, col_off+i) = albdnir(i)\n          albrad(4, col_off+i) = albinir(i)\n"
     "        enddo\n"
     "      endif\n"
     "    endif\n"
     "  endif\n")
pre(drv, "        call noahmp_sflx (parameters                                          , &\n",
    "        sw_target = -1.\n"
    "        swa = -1.\n"
    "        if (present(adjvisbmd)) then\n"
    "          if (albrad(1, col_off+i) >= 0.) then\n"
    "            swa = adjvisbmd(i)*(1.-albrad(1,col_off+i)) + adjvisdfd(i)*(1.-albrad(2,col_off+i)) &\n"
    "                + adjnirbmd(i)*(1.-albrad(3,col_off+i)) + adjnirdfd(i)*(1.-albrad(4,col_off+i))\n"
    "            if (esfix_d('SW1')) sw_target = swa\n"
    "          endif\n"
    "        endif\n")
post(drv, "  end do ! im loop\n", "  if (present(adjvisbmd) .and. first_iter) col_off = col_off + im\n")
pre(drv, "      public :: noahmpdrv_init, noahmpdrv_run, &\n",
     "      ! radiation-time land albedo per column (direct vis, diffuse vis, direct nir, diffuse nir)\n"
     "      real(kind=8), allocatable, save :: albrad(:,:)\n"
     "      integer, save :: col_kdt = -1, col_off = 0\n")
meta_add(drvm, [(n, sn, ln, "W m-2", "(horizontal_loop_extent)", "real", "kind_phys") for n, sn, ln in [
    ("adjvisbmd", "surface_downwelling_direct_ultraviolet_and_visible_shortwave_flux", "sfc uv+vis beam sw downward flux"),
    ("adjvisdfd", "surface_downwelling_diffuse_ultraviolet_and_visible_shortwave_flux", "sfc uv+vis diff sw downward flux"),
    ("adjnirbmd", "surface_downwelling_direct_near_infrared_shortwave_flux", "sfc nir beam sw downward flux"),
    ("adjnirdfd", "surface_downwelling_diffuse_near_infrared_shortwave_flux", "sfc nir diff sw downward flux")]]
         + [("lsswr", "flag_for_calling_shortwave_radiation", "logical flags for sw radiation calls", "flag", "()",
             "logical", None)])

for path, s in edits.items():
    path.write_text(s)
    print(f"round2 {path.relative_to(root)}")
