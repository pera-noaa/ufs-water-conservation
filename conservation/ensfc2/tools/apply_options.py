#!/usr/bin/env python3
"""Round-3 surface energy OPTIONS (gfs_physics_nml switches, all default off; off = the stock code path).
Apply on top of the bug fixes (SI1 SI2 NP1 QR1 CMC FL1), with or without meters.
Usage: apply_options.py <ufs-weather-model>

  noahmp_canopy_heat = 0|1|2   Noah-MP canopy heat. 1 (CH1): massless canopy, hcv leaves the Newton step, canhs = 0.
                               2 (CH2): canopy heat storage over the whole step, canhs = hcv*(tv_new - tv_start)/dt,
                               and canwater keeps tv (melt/freeze latent heat goes to the soil through CMC).
  precip_phase_host  = T       PH1: GFS_MP_generic_post heats the lowest layer by hfus x the convective precipitation
                               the host calls snow (Thompson branch, tsfc < 273.15). PH2: Noah-MP soil takes that
                               decision for its convective precipitation (instead of NM10's sfctmp < tfrz).
                               PH3: Noah-MP glacier takes srflag as its frozen fraction (instead of its T rule).
  noahmp_sw_radshare = T       SW1: Noah-MP (soil and glacier) absorbs the radiation's share for the land:
                               land-only cells the cell net SW; mixed cells the radiation-time land albedos x this
                               step's band fluxes. sav/sag are rescaled (canopy/ground partition kept).
  lw_sfc_consistent  = T       LW1: the surfaces report the non-solar flux they booked (Noah-MP: its net LW; sea ice:
                               its linearised non-solar flux minus the SH and LH the atmosphere receives) through
                               adjsfculw_land/ice; GFS_surface_composites_post heats the lowest layer by
                               sum_type frac*(booked net up LW) - (radiation-time net up LW).
  sfc_evap_enthalpy  = T       EV1: Noah-MP soil columns report E*(h_land_source - h_v(T1)) in frame F (encpl):
                               the water's enthalpy where the land loses it (liquid c_w(T-tfrz), ice c_i(T-tfrz), canopy
                               water at tfrz) plus the latent heat charged, minus the vapour's h_v(T1) = hvap + cp_v(T1-T0);
                               GFS_surface_composites_post heats the lowest layer by land fraction x that.
  noahmp_heat_advect = T       AD1: soil water moved between layers (soilwater + groundwater) carries c_w (T_upstream);
                               boundary flows keep their layer temperature (booked at that T).
  noahmp_kirchhoff   = T       KF1: phasechange heats the remainder into the layer at its new composition, i.e. latent
                               heat L_f(T) = hfus + (c_w - c_i)(T - tfrz) with Noah-MP's own heat capacities.
Every anchor must match exactly once; nothing is written unless all match."""
import sys
from pathlib import Path

top = Path(sys.argv[1]) / "UFSATM/ccpp"
root = top / "physics/physics"
gtd = top / "data/GFS_typedefs.F90"
gtm = top / "data/GFS_typedefs.meta"
ctd = top / "data/CCPP_typedefs.F90"
ctm = top / "data/CCPP_typedefs.meta"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
drvm = root / "SFC_Models/Land/Noahmp/noahmpdrv.meta"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
icem = root / "SFC_Models/SeaIce/CICE/sfc_sice.meta"
mpp = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.F90"
mppm = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.meta"
cpo = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.F90"
cpom = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.meta"
edits = {}


def get(p):
    return edits.get(p) or p.read_text()


def sub(path, old, new, after=None, count=1):
    s = get(path)
    if after is not None:
        if s.count(after) != 1:
            sys.exit(f"ABORT {path.name}: anchor count {s.count(after)}: {after.strip()[:70]!r}")
        i = s.index(after)
        j = s.find(old, i)
        if j < 0:
            sys.exit(f"ABORT {path.name}: {old.strip()[:70]!r} not after anchor {after.strip()[:50]!r}")
        edits[path] = s[:j] + new + s[j + len(old):]
        return
    if s.count(old) != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {s.count(old)}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


def pre(path, a, t, **kw):
    sub(path, a, t + a, **kw)


def post(path, a, t, **kw):
    sub(path, a, a + t, **kw)


def post_line(path, frag, text):
    """insert text after the unique line containing frag"""
    s = get(path)
    lines = s.splitlines(keepends=True)
    hits = [k for k, l in enumerate(lines) if frag in l]
    if len(hits) != 1:
        sys.exit(f"ABORT {path.name}: line fragment count {len(hits)}: {frag!r}")
    lines.insert(hits[0] + 1, text)
    edits[path] = "".join(lines)


def meta_entry(name, std, long, units, dims="()", typ="real", kind=True, intent=None, optional=False, active=None):
    t = f"[{name}]\n  standard_name = {std}\n  long_name = {long}\n  units = {units}\n  dimensions = {dims}\n  type = {typ}\n"
    if kind and typ == "real":
        t += "  kind = kind_phys\n"
    if active:
        t += f"  active = ({active})\n"
    if intent:
        t += f"  intent = {intent}\n"
    if optional:
        t += "  optional = True\n"
    return t


def meta_append(path, text):
    s = get(path)
    if not s.endswith("\n"):
        s += "\n"
    edits[path] = s + text


# ================================================================== namelist switches (GFS_typedefs)
OPTS = [  # name, type, default, standard name, long name
    ("noahmp_canopy_heat", "integer", "0", "control_for_noahmp_canopy_heat_storage",
     "Noah-MP canopy heat: 0 stock, 1 massless canopy, 2 heat storage over the step"),
    ("precip_phase_host", "logical", ".false.", "flag_for_host_convective_precipitation_phase_at_surface",
     "flag: surfaces take the host convective snow decision and the atmosphere pays hfus for it"),
    ("noahmp_sw_radshare", "logical", ".false.", "flag_for_noahmp_radiation_share_of_shortwave",
     "flag: Noah-MP absorbs the radiation share of net shortwave for the land"),
    ("lw_sfc_consistent", "logical", ".false.", "flag_for_surface_booked_longwave_heating",
     "flag: lowest layer gets the surface-booked minus radiation-time net longwave"),
    ("sfc_evap_enthalpy", "logical", ".false.", "flag_for_land_evaporation_enthalpy_heating",
     "flag: lowest layer gets the land evaporation enthalpy the vapour does not carry"),
    ("noahmp_heat_advect", "logical", ".false.", "flag_for_noahmp_soil_water_heat_advection",
     "flag: soil water moved between layers carries its sensible heat"),
    ("noahmp_kirchhoff", "logical", ".false.", "flag_for_noahmp_kirchhoff_consistent_phase_change",
     "flag: Noah-MP phase change with L_f(T) consistent with its heat capacities"),
]
decl = "".join(f"    {t:<21}:: {n:<19}!< {l}\n" for n, t, d, s, l in OPTS)
post_line(gtd, "    integer              :: iopt_diag !2m t/q diagnostic approach", decl)
dflt = "".join(f"    {t:<21}:: {n:<19}= {d}\n" for n, t, d, s, l in OPTS)
post_line(gtd, "    integer              :: iopt_diag      =  2", dflt)
post(gtd, "                               iopt_trs, iopt_diag,                                         &\n",
     "                               noahmp_canopy_heat, precip_phase_host, noahmp_sw_radshare,   &\n"
     "                               lw_sfc_consistent, sfc_evap_enthalpy, noahmp_heat_advect,    &\n"
     "                               noahmp_kirchhoff,                                            &\n")
post_line(gtd, "    Model%iopt_diag        = iopt_diag", "".join(f"    Model%{n} = {n}\n" for n, t, d, s, l in OPTS))
post_line(gtd, "        print *, ' iopt_diag         : ', Model%iopt_diag",
          "".join(f"        print *, ' {n} : ', Model%{n}\n" for n, t, d, s, l in OPTS))
s = get(gtm)
k = s.index("[iopt_diag]\n")
j = s.index("\n[", k) + 1
edits[gtm] = s[:j] + "".join(meta_entry(n, st, l, "flag" if t == "logical" else "index", typ=t)
                             for n, t, d, st, l in OPTS) + s[j:]

# radiation-time land albedo (SW1), Sfcprop
ALB = [("albdirvis_lnd_rad", "surface_albedo_direct_visible_over_land_on_radiation_timestep", "direct visible"),
       ("albdirnir_lnd_rad", "surface_albedo_direct_NIR_over_land_on_radiation_timestep", "direct NIR"),
       ("albdifvis_lnd_rad", "surface_albedo_diffuse_visible_over_land_on_radiation_timestep", "diffuse visible"),
       ("albdifnir_lnd_rad", "surface_albedo_diffuse_NIR_over_land_on_radiation_timestep", "diffuse NIR")]
post_line(gtd, "    real (kind=kind_phys), pointer :: albdifnir_lnd (:) => null()",
          "".join(f"    real (kind=kind_phys), pointer :: {n} (:) => null()  !< land albedo the radiation used ({l})\n"
                  for n, st, l in ALB))
post_line(gtd, "    allocate (Sfcprop%albdifnir_lnd (IM))", "".join(f"    allocate (Sfcprop%{n} (IM))\n" for n, st, l in ALB))
post_line(gtd, "    Sfcprop%albdifnir_lnd = clear_val", "".join(f"    Sfcprop%{n} = -1.0_kind_phys\n" for n, st, l in ALB))
s = get(gtm)
k = s.index("[albdifnir_lnd]\n")
j = s.index("\n[", k) + 1
edits[gtm] = s[:j] + "".join(meta_entry(n, st, f"{l} land albedo used by the last radiation call", "frac",
                                        dims="(horizontal_dimension)") for n, st, l in ALB) + s[j:]

# land evaporation enthalpy heating (EV1), Interstitial
post_line(ctd, "    real (kind=kind_phys), pointer      :: adjsfculw_ice(:)   => null()",
          "    real (kind=kind_phys), pointer      :: hflx_evap_enth(:)  => null()  !< land evaporation enthalpy heating\n")
post_line(ctd, "    allocate (Interstitial%adjsfculw_ice   (ixs:ixe))", "    allocate (Interstitial%hflx_evap_enth  (ixs:ixe))\n")
post_line(ctd, "    deallocate (Interstitial%adjsfculw_ice)", "    deallocate (Interstitial%hflx_evap_enth)\n")
post_line(ctd, "    Interstitial%adjsfculw_ice   = clear_val", "    Interstitial%hflx_evap_enth  = clear_val\n")
EVSTD = "lowest_layer_heating_by_land_evaporation_enthalpy"
s = get(ctm)
k = s.index("[adjsfculw_ice]\n")
j = s.index("\n[", k) + 1
edits[ctm] = s[:j] + meta_entry("hflx_evap_enth", EVSTD,
                                "land evaporation enthalpy not carried by the vapour (frame F), per land area",
                                "W m-2", dims="(horizontal_dimension)") + s[j:]

# ================================================================== Noah-MP soil (module_sf_noahmplsm)
post(lsm, "  public  :: noahmp_sflx\n",
     "  ! energy options (gfs_physics_nml, set every call by noahmp_options_energy; same value from every thread)\n"
     "  integer, save :: opt_cnh = 0        ! canopy heat: 0 stock, 1 massless canopy, 2 storage over the step\n"
     "  logical, save :: opt_kir = .false.  ! phase change remainder heats the layer at its new composition\n"
     "  logical, save :: opt_adv = .false.  ! soil water moved between layers carries its sensible heat\n"
     "  real (kind=kind_phys), save :: cl_f = 4185.5, cpv_f = 1846.0, t0_f = 273.15  ! frame F constants\n"
     "  public  :: noahmp_options_energy\n")
pre(lsm, "  subroutine noahmp_sflx (parameters, &\n",
    "  subroutine noahmp_options_energy(cnh, kir, adv, cl, cpv, t0)\n"
    "    integer, intent(in) :: cnh\n"
    "    logical, intent(in) :: kir, adv\n"
    "    real (kind=kind_phys), intent(in) :: cl, cpv, t0\n"
    "    opt_cnh = cnh\n    opt_kir = kir\n    opt_adv = adv\n"
    "    cl_f = cl\n    cpv_f = cpv\n    t0_f = t0\n"
    "  end subroutine noahmp_options_energy\n\n")
SF = "  subroutine noahmp_sflx (parameters, &\n"
sub(lsm, "                   ,errmsg, errflg)\n", "                   ,errmsg, errflg, fpcv_host, sw_target, hevap)\n", after=SF)
post(lsm, "  character(len=*), intent(inout)    :: errmsg\n  integer,          intent(inout)    :: errflg\n",
     "  real (kind=kind_phys), optional, intent(in)  :: fpcv_host !< host frozen fraction of convective precipitation\n"
     "  real (kind=kind_phys), optional, intent(in)  :: sw_target !< absorbed SW imposed by the host (w/m2)\n"
     "  real (kind=kind_phys), optional, intent(out) :: hevap     !< evaporation enthalpy not carried by the vapour (w/m2)\n",
     after=SF)
post(lsm, "  real (kind=kind_phys)              :: q1\n",
     "  real (kind=kind_phys)              :: fpcvh, swt, hev\n", after=SF)
pre(lsm, "   call atm (parameters,ep_2, epsm1, sfcprs  ,sfctmp   ,q2      ,    &\n",
    "   fpcvh = -1.\n   if (present(fpcv_host)) fpcvh = fpcv_host\n"
    "   swt = -1.\n   if (present(sw_target)) swt = sw_target\n   hev = 0.\n\n")
sub(lsm, "             swdown  ,bdfall   ,rain    ,snow    ,fp      ,fpice   , prcp )     \n",
    "             swdown  ,bdfall   ,rain    ,snow    ,fp      ,fpice   , prcp, fpcvh )\n")
AT = "  subroutine atm (parameters,ep_2,epsm1,sfcprs  ,sfctmp   ,q2      ,       &\n"
sub(lsm, "                  swdown  ,bdfall   ,rain    ,snow    ,fp      , fpice   ,prcp )     \n",
    "                  swdown  ,bdfall   ,rain    ,snow    ,fp      , fpice   ,prcp, fpcvh )\n", after=AT)
post(lsm, "  real (kind=kind_phys)                          , intent(in)  :: cosz     !< cosine solar zenith angle [0-1]\n",
     "  real (kind=kind_phys)                          , intent(in)  :: fpcvh    !< host frozen fraction of convective precipitation (< 0: sfctmp rule)\n",
     after=AT)
post(lsm, "          if(sfctmp < tfrz) fpcv = 1.0\n", "          if(fpcvh >= 0.) fpcv = fpcvh\n")
# energy(): SW target
CE = "    call energy (parameters,ice    ,vegtyp ,ist    ,nsnow  ,nsoil  , & !in\n"
sub(lsm, "chleaf,chuc,chv2,chb2 )", "chleaf,chuc,chv2,chb2, swt )", after=CE)
EN = "  subroutine energy (parameters,ice    ,vegtyp ,ist    ,nsnow  ,nsoil  , & !in\n"
sub(lsm, "chleaf,chuc,chv2,chb2 )", "chleaf,chuc,chv2,chb2, swt )", after=EN)
post(lsm, "  type (noahmp_parameters), intent(in) :: parameters\n",
     "  real (kind=kind_phys)             , intent(in)    :: swt    !<absorbed SW imposed by the host (< 0: own)\n",
     after=EN)
pre(lsm, "! vegetation and ground emissivity\n\n     emv = 1. - exp(-(elai+esai)/1.0)\n",
    "! absorbed SW imposed by the host (radiation's land share); canopy/ground partition kept\n"
    "! (sun below Noah-MP's horizon while the radiation still has light: the ground takes it)\n"
    "     if (swt >= 0.) then\n"
    "        if (fsa > 0.) then\n"
    "           sav = sav*swt/fsa\n"
    "           sag = sag*swt/fsa\n"
    "        else\n"
    "           sav = 0.\n"
    "           sag = swt\n"
    "        endif\n"
    "        fsr = fsr + fsa - swt\n"
    "        fsa = swt\n"
    "     endif\n\n")
# water(): evaporation enthalpy out
CW = "     call water (parameters,vegtyp ,nsnow  ,nsoil  ,imelt  ,dt     ,uu     , & !in\n"
sub(lsm, "                 qsnbot ,esnow   )  !out\n", "                 qsnbot ,esnow  ,hev )  !out\n", after=CW)
post(lsm, "!     write(*,'(a20,10f15.5)') 'sflx:runoff=',runsrf*dt,runsub*dt,edir*dt\n",
     "     if (present(hevap)) hevap = hev\n")
# CH1 / CH2 in vege_flux
post(lsm, "  real (kind=kind_phys) :: hcv          !canopy heat capacity j/m2/k, C.He added \n",
     "  real (kind=kind_phys) :: hcvn         !canopy heat capacity in the newton step (0: massless canopy)\n"
     "  real (kind=kind_phys) :: tv_start     !canopy temperature at the start of the step\n")
pre(lsm, "      loop1: do iter = 1, niterc    !  begin stability iteration\n", "      tv_start = tv\n")
sub(lsm, "        b   = sav-irc-shc-evc-tr+pahv                          !additional w/m2\n"
         "!       a   = fveg*(4.*cir*tv**3 + csh + (cev+ctr)*destv) !volumetric heat capacity\n"
         "        a   = fveg*(4.*cir*tv**3 + csh + (cev+ctr)*destv) + hcv/dt !volumetric heat capacity\n",
    "        hcvn = hcv\n"
    "        if (opt_cnh == 1) hcvn = 0.                           ! massless canopy\n"
    "        b   = sav-irc-shc-evc-tr+pahv                          !additional w/m2\n"
    "        if (opt_cnh == 2) b = b - hcv*(tv - tv_start)/dt      ! storage over the whole step\n"
    "!       a   = fveg*(4.*cir*tv**3 + csh + (cev+ctr)*destv) !volumetric heat capacity\n"
    "        a   = fveg*(4.*cir*tv**3 + csh + (cev+ctr)*destv) + hcvn/dt !volumetric heat capacity\n")
sub(lsm, "        canhs = dtv*hcv/dt\n",
    "        canhs = dtv*hcvn/dt\n"
    "        if (opt_cnh == 2) canhs = hcv*(tv + dtv - tv_start)/dt\n")
sub(lsm, "         tv     = fwet*tfrz + (1.-fwet)*tv\n",
    "         if (opt_cnh /= 2) tv = fwet*tfrz + (1.-fwet)*tv\n", count=2)
# KF1 in phasechange
PC = "  subroutine phasechange (parameters,nsnow   ,nsoil   ,isnow   ,dt      ,fact    , & !in\n"
post(lsm, "  real (kind=kind_phys)                            :: xmf       !total latent heat of phase change\n",
     "  real (kind=kind_phys)                            :: hcpn      !heat capacity at the new composition (j/m3/k)\n"
     "  real (kind=kind_phys)                            :: svn       !snow ice volume fraction at the new composition\n",
     after=PC)
sub(lsm, "            stc(j) = stc(j) + fact(j)*heatr\n",
    "            if (opt_kir) then\n"
    "               ! the remainder heats the layer at its new composition: L_f(T) = hfus + (c_w-c_i)(T-tfrz)\n"
    "               if (j <= 0) then\n"
    "                  svn  = min(1., mice(j)/(dzsnso(j)*denice))\n"
    "                  hcpn = cice*svn + cwat*min(1.-svn, mliq(j)/(dzsnso(j)*denh2o))\n"
    "               else\n"
    "                  hcpn = dt/(fact(j)*dzsnso(j)) + (cwat*(mliq(j)-wliq0(j)) + cice*(mice(j)-wice0(j))) &\n"
    "                         / (1000.*dzsnso(j))\n"
    "               endif\n"
    "               stc(j) = stc(j) + heatr*dt/(hcpn*dzsnso(j))\n"
    "            else\n"
    "               stc(j) = stc(j) + fact(j)*heatr\n"
    "            endif\n", after=PC)

# water(): EV1 and AD1
WA = "  subroutine water (parameters,vegtyp ,nsnow  ,nsoil  ,imelt  ,dt     ,uu     , & !in\n"
sub(lsm, "                    qsnbot ,esnow) \n", "                    qsnbot ,esnow  ,hevap) \n", after=WA)
post(lsm, "  real (kind=kind_phys)                                           :: lheatc  !heat charged to the canopy that it cannot carry [j/m2]\n",
     "  real (kind=kind_phys), intent(out)                              :: hevap   !evaporation enthalpy not carried by the vapour [w/m2]\n"
     "  real (kind=kind_phys)                                           :: cwk, cik, csk, hvt1, esrc, edef, sice1\n"
     "  real (kind=kind_phys), dimension(       1:nsoil)                :: sh2o0, bnd, hcp0\n"
     "  real (kind=kind_phys)                                           :: dflx, qadv(nsoil), hsnow\n"
     "  real (kind=kind_phys)                                           :: rsat0, qthru, qcold, qinfl, qinfh, tsbot\n")
pre(lsm, "   etrani(1:nsoil) = 0.\n   snoflow         = 0.\n",
    "   ! frame F (encpl): per kg evaporated, the land loses (latent charged - hvap) + its water's enthalpy,\n"
    "   ! the vapour carries h_v(T1) - h_w(T0) = hvap + cp_v (T1 - T0); liquid at tfrz is worth cl_f (tfrz - T0)\n"
    "   cwk  = cwat/1000.\n   cik  = cice/1000.\n   csk  = cice/denice\n"
    "   hvt1 = cl_f*(tfrz - t0_f) - cpv_f*(sfctmp - t0_f)\n"
    "   hevap = 0.\n")
# canopy water (massless, worth tfrz): liquid hvap-hvap = 0, ice (hsub-hvap) - hfus = 0
post(lsm, "                  fwet   ,lheatc )                       !out\n",
     "   hevap = hevap + ecan*hvt1\n",
     after="   call canwater (parameters,vegtyp ,dt     , & !in\n")
# snow sublimation: content from snowwater (j/m2 relative to tfrz, sensible part only)
sub(lsm, "          &          qsnbot ,snoflow,ponding1       ,ponding2)  !out\n",
    "          &          qsnbot ,snoflow,ponding1       ,ponding2, hsnow)  !out\n",
    after="     call snowwater (parameters,nsnow  ,nsoil  ,imelt  ,dt     ,zsoil  , & !in\n")
pre(lsm, "   lheat = (latheag - hsub)*(qsnsub - qsnfro)*dt + lheatc\n",
    "   hevap = hevap + (qsnsub - qsnfro)*hvt1 + hsnow/dt\n")
# frozen ground: ice (or the liquid the missing ice came from) at stc(1) before the lheat return
post(lsm, "   if(frozen_ground) then\n      sice(1) =  sice(1) + (qsdew-qseva)*dt/(dzsnso(1)*1000.)\n",
     "      edef = max(0., -sice(1))*dzsnso(1)*1000./dt\n"
     "      hevap = hevap + (qseva - qsdew)*(hvt1 + cik*(stc(1)-tfrz)) + edef*(cwk - cik)*(stc(1)-tfrz)\n")
# liquid soil evaporation/dew and transpiration at the layer T after the lheat return
pre(lsm, "! convert units (mm/s -> m/s)\n\n    !ponding: melting water from snow when there is no layer\n",
    "   if (.not. frozen_ground) hevap = hevap + (qseva - qsdew)*(hvt1 + cwk*(stc(1)-tfrz))\n"
    "   do iz = 1, parameters%nroot\n"
    "      hevap = hevap + etran*btrani(iz)*(hvt1 + cwk*(stc(iz)-tfrz))\n"
    "   enddo\n\n")
# AD1: boundary flows per layer, internal fluxes by difference, upstream heat. The bookkeeping (no state change)
# always runs; the temperatures change only with opt_adv.
pre(lsm, "       call      soilwater (parameters,nsoil  ,nsnow  ,dt     ,zsoil  ,dzsnso , & !in\n",
    "       ! boundary water by layer (kg/m2): supersaturation the solver sends to runoff, transpiration, soil evaporation\n"
    "       rsat0 = 0.\n"
    "       do iz = 1, nsoil\n"
    "          sh2o0(iz) = sh2o(iz)\n"
    "          hcp0(iz)  = sh2o(iz)*cwat + (1.0-parameters%smcmax(iz))*parameters%csoil &\n"
    "                    + (parameters%smcmax(iz)-sh2o(iz)-sice(iz))*cpair + sice(iz)*cice\n"
    "          bnd(iz) = -max(0., sh2o(iz) - max(1.e-4, parameters%smcmax(iz) - sice(iz)))*dzsnso(iz)*1000.\n"
    "          rsat0 = rsat0 - bnd(iz)\n"
    "          bnd(iz) = bnd(iz) - etrani(iz)*1000.*dt\n"
    "       enddo\n"
    "       bnd(1) = bnd(1) - qseva*1000.*dt\n"
    "       ! water reaching the soil surface: rain throughfall at tg (PAH), snowmelt/ponding/canopy drip at tfrz,\n"
    "       ! dew at the layer T (mm/s)\n"
    "       qthru = 0.\n"
    "       qcold = (ponding+ponding1+ponding2)/dt\n"
    "       tsbot = tfrz\n"
    "       if (isnow < 0) tsbot = stc(0)                     ! snow-bottom outflow leaves the bottom snow layer\n"
    "       if (isnow == 0) then\n"
    "          qthru = qrain\n"
    "          qcold = qcold + qcanl\n"
    "       endif\n")
sub(lsm, "                            runsrf ,qdrain ,runsub ,wcnd   ,fcrmax )   !out\n",
    "                            runsrf ,qdrain ,runsub ,wcnd   ,fcrmax , qinfl )  !out\n"
    "       ! infiltration net of what the solver pushed out at the top; the layer excess is booked above\n"
    "       bnd(1) = bnd(1) + qinsur*1000.*dt - runsrf*dt + rsat0\n"
    "       bnd(nsoil) = bnd(nsoil) - qdrain*dt\n"
    "       qinfh = 0.\n"
    "       if (qinsur > 0.) qinfh = cwk*qinfl/qinsur*dt*(qthru*(tg - stc(1)) + qcold*(tfrz - stc(1)) &\n"
    "                                                    + qsnbot*(tsbot - stc(1)))\n",
    after="       call      soilwater (parameters,nsoil  ,nsnow  ,dt     ,zsoil  ,dzsnso , & !in\n")
sub(lsm, "                            qin    ,qdis   )                           !out\n",
    "                            qin    ,qdis   ,bnd   )                    !out\n",
    after="          call groundwater (parameters,nsnow  ,nsoil  ,dt     ,sice   ,zsoil  , & !in\n")
pre(lsm, "       if(opt_run == 5) then\n          call shallowwatertable (parameters,nsnow  ,nsoil, zsoil, dt       , & !in\n",
    "       ! downward internal flux below layer iz (kg/m2 per step) = minus the internal changes above\n"
    "       dflx = 0.\n"
    "       qadv = 0.\n"
    "       qadv(1) = qinfh\n"
    "       do iz = 1, nsoil-1\n"
    "          dflx = dflx - ((sh2o(iz) - sh2o0(iz))*dzsnso(iz)*1000. - bnd(iz))\n"
    "          if (dflx > 0.) then\n"
    "             qadv(iz+1) = qadv(iz+1) + cwk*dflx*(stc(iz) - stc(iz+1))\n"
    "          else\n"
    "             qadv(iz) = qadv(iz) - cwk*dflx*(stc(iz+1) - stc(iz))\n"
    "          endif\n"
    "       enddo\n"
    "       dflx = dflx - ((sh2o(nsoil) - sh2o0(nsoil))*dzsnso(nsoil)*1000. - bnd(nsoil))  ! 0 if all is booked\n"
    "       if (opt_adv) then\n"
    "          do iz = 1, nsoil\n"
    "             stc(iz) = stc(iz) + qadv(iz)/(dzsnso(iz)*(hcp0(iz) + (cwat - cpair)*(sh2o(iz) - sh2o0(iz))))\n"
    "          enddo\n"
    "       endif\n\n")
# soilwater: infiltration rate out (mean over the sub-steps)
SO = "  subroutine soilwater (parameters,nsoil  ,nsnow  ,dt     ,zsoil  ,dzsnso , & !in\n"
sub(lsm, "                        runsrf ,qdrain ,runsub ,wcnd   ,fcrmax )   !out\n",
    "                        runsrf ,qdrain ,runsub ,wcnd   ,fcrmax , qinfl )  !out\n", after=SO)
post(lsm, "  implicit none\n", "  real (kind=kind_phys), intent(out) :: qinfl  !< infiltration, mean over the sub-steps (m/s)\n", after=SO)
post(lsm, "    qdrain_save = 0.0\n", "    qinfl = 0.0\n", after=SO)
post(lsm, "       qdrain_save = qdrain_save + qdrain\n", "       qinfl = qinfl + pddum/niter\n", after=SO)
# groundwater: per-layer boundary flows (qin and aquifer refill at the bottom layer, qdis by layer)
GW = "  subroutine groundwater(parameters,nsnow  ,nsoil  ,dt     ,sice   ,zsoil  , & !in\n"
sub(lsm, "                         qin    ,qdis   )                           !out\n",
    "                         qin    ,qdis   ,bnd   )                    !out\n", after=GW)
post(lsm, "  real (kind=kind_phys),                           intent(out) :: qdis  !groundwater discharge [mm/s]\n",
     "  real (kind=kind_phys), dimension(1:nsoil),     intent(inout) :: bnd    !< boundary water change by layer (kg/m2)\n",
     after=GW)
post(lsm, "         mliq(nsoil) = mliq(nsoil) - qin * dt        ! [mm]\n",
     "         bnd(nsoil) = bnd(nsoil) - qin*dt\n", after=GW)
post(lsm, "         mliq(nsoil) = mliq(nsoil) + max(0.,(wa - 5000.))\n",
     "         bnd(nsoil) = bnd(nsoil) + max(0.,(wa - 5000.))\n", after=GW)
post(lsm, "         mliq(iz) = mliq(iz) - qdis*dt*hk(iz)*dzmm(iz)/wtsub\n",
     "         bnd(iz) = bnd(iz) - qdis*dt*hk(iz)*dzmm(iz)/wtsub\n", after=GW)
post(lsm, "        wa       = wa - xs\n", "        bnd(nsoil) = bnd(nsoil) + xs\n", after=GW)
# snowwater/snowh2o: sensible content of the sublimated/frosted snow and soil ice (j/m2, + = removed)
SW = "  subroutine snowwater (parameters,nsnow  ,nsoil  ,imelt  ,dt     ,zsoil  , & !in\n"
sub(lsm, "                        qsnbot ,snoflow,ponding1       ,ponding2)  !out\n",
    "                        qsnbot ,snoflow,ponding1       ,ponding2, hsnow)  !out\n", after=SW)
post(lsm, "  real (kind=kind_phys),                              intent(out) :: ponding2 !<\n",
     "  real (kind=kind_phys),                              intent(out) :: hsnow  !< sensible content of sublimated water [j/m2]\n",
     after=SW)
sub(lsm, "                  qsnbot ,ponding1       ,ponding2)           !out\n",
    "                  qsnbot ,ponding1       ,ponding2, hsnow)   !out\n", after=SW)
SH = "  subroutine snowh2o (parameters,nsnow  ,nsoil  ,dt     ,qsnfro ,qsnsub , & !in \n"
sub(lsm, "                      qsnbot ,ponding1       ,ponding2)          !out\n",
    "                      qsnbot ,ponding1       ,ponding2, hsnow)   !out\n", after=SH)
post(lsm, "   real (kind=kind_phys),                            intent(out)   :: qsnbot !< melting water out of snow bottom [mm/s]\n",
     "   real (kind=kind_phys),                            intent(out)   :: hsnow  !< sensible content of sublimated water [j/m2]\n",
     after=SH)
sub(lsm, "   if(sneqv == 0.) then\n      sice(1) =  sice(1) + (qsnfro-qsnsub)*dt/(dzsnso(1)*1000.)  ! barlage: sh2o->sice v3.6\n"
         "      if(sice(1) < 0.) then\n",
    "   hsnow = 0.\n"
    "   if(sneqv == 0.) then\n      sice(1) =  sice(1) + (qsnfro-qsnsub)*dt/(dzsnso(1)*1000.)  ! barlage: sh2o->sice v3.6\n"
    "      hsnow = (qsnsub-qsnfro)*dt*cice/1000.*(stc(1)-tfrz) + max(0.,-sice(1))*dzsnso(1)*(cwat-cice)*(stc(1)-tfrz)\n"
    "      if(sice(1) < 0.) then\n", after=SH)
sub(lsm, "      if(sneqv < 0.) then\n         sice(1) = sice(1) + sneqv/(dzsnso(1)*1000.)\n",
    "      if(sneqv < 0.) then\n         hsnow = hsnow - sneqv*cice/1000.*(stc(1)-tfrz)\n"
    "         if (sice(1) + sneqv/(dzsnso(1)*1000.) < 0.) hsnow = hsnow &\n"
    "            - (sice(1)*dzsnso(1)*1000. + sneqv)*(cwat-cice)/1000.*(stc(1)-tfrz)\n"
    "         sice(1) = sice(1) + sneqv/(dzsnso(1)*1000.)\n", after=SH)
sub(lsm, "   do j = isnow+1, 0\n     snliq(j) = snliq(j) + qin\n",
    "   do j = isnow+1, 0\n"
    "     if (opt_adv .and. qin > 0.) then\n"
    "        ! AD1: liquid from the layer above arrives at that layer's temperature\n"
    "        svn  = min(1., snice(j)/(dzsnso(j)*denice))\n"
    "        hcpo = (cice*svn + cwat*min(1.-svn, snliq(j)/(dzsnso(j)*denh2o)))*dzsnso(j)\n"
    "        hcpn = (cice*svn + cwat*min(1.-svn, (snliq(j)+qin)/(dzsnso(j)*denh2o)))*dzsnso(j)\n"
    "        stc(j) = tfrz + (hcpo*(stc(j)-tfrz) + cwat/denh2o*qin*(stc(j-1)-tfrz))/hcpn\n"
    "     endif\n"
    "     snliq(j) = snliq(j) + qin\n", after=SH)
post(lsm, "   real (kind=kind_phys) :: propor, temp\n", "   real (kind=kind_phys) :: svn, hcpo, hcpn\n", after=SH)
sub(lsm, "      wgdif = snice(isnow+1) - qsnsub*dt + qsnfro*dt\n",
    "      wgdif = snice(isnow+1) - qsnsub*dt + qsnfro*dt\n"
    "      hsnow = hsnow + (qsnsub - qsnfro)*dt*cice/denice*(stc(isnow+1)-tfrz)\n", after=SH)

# ================================================================== Noah-MP glacier
GL = "  subroutine noahmp_glacier (&\n"
sub(gla, "                   errmsg    ,errflg) \n", "                   errmsg    ,errflg, fpice_host, sw_target) \n", after=GL)
post(gla, "  real (kind=kind_phys)                           , intent(out)   :: fpice\n",
     "  real (kind=kind_phys), optional                 , intent(in)    :: fpice_host !< host frozen fraction (srflag)\n"
     "  real (kind=kind_phys), optional                 , intent(in)    :: sw_target  !< absorbed SW imposed by the host\n"
     "  real (kind=kind_phys)                                           :: fpih, swt\n", after=GL)
pre(gla, "   call atm_glacier (ep_2, epsm1,sfcprs ,sfctmp ,q2     ,soldn  ,cosz   ,thair  , & \n",
    "   fpih = -1.\n   if (present(fpice_host)) fpih = fpice_host\n"
    "   swt = -1.\n   if (present(sw_target)) swt = sw_target\n\n")
sub(gla, "                         ch2b      ,albsnd  ,albsni  ,z0h_total)                    !out\n",
    "                         ch2b      ,albsnd  ,albsni  ,z0h_total, swt)               !out\n",
    after="    call energy_glacier (nsnow     ,nsoil   ,isnow   ,dt      ,qsnow   ,rhoair  , & !in\n")
EG = "  subroutine energy_glacier (nsnow     ,nsoil   ,isnow   ,dt      ,qsnow   ,rhoair  , & !in\n"
sub(gla, "                             ch2b      ,albsnd  ,albsni  ,z0h_total)                    !out\n",
    "                             ch2b      ,albsnd  ,albsni  ,z0h_total, swt)               !out\n", after=EG)
post(gla, "  real (kind=kind_phys)                              , intent(in)    :: zbot   !< depth for tbot [m]\n",
     "  real (kind=kind_phys)                              , intent(in)    :: swt    !< absorbed SW imposed by the host (< 0: own)\n",
     after=EG)
post(gla, "                           sag     ,fsr     ,fsa     ,albsnd  ,albsni)     !out\n",
     "\n! absorbed SW imposed by the host (radiation's land share)\n"
     "     if (swt >= 0.) then\n"
     "        sag = swt\n"
     "        fsr = fsr + fsa - swt\n"
     "        fsa = swt\n"
     "     endif\n", after=EG)
sub(gla, "                         fpice  ,esnow)                                          !out\n",
    "                         fpice  ,esnow  ,fpih)                                   !out\n",
    after="     call water_glacier (nsnow  ,nsoil  ,imelt   ,dt       ,prcp     ,sfctmp , & !in\n")
WG = "  subroutine water_glacier (nsnow  ,nsoil  ,imelt   ,dt       ,prcp     ,sfctmp , & !in\n"
sub(gla, "                            fpice  ,esnow)                                          !out\n",
    "                            fpice  ,esnow  ,fpih)                                   !out\n", after=WG)
post(gla, "  integer, dimension(-nsnow+1:0) ,                  intent(in)    :: imelt   !< melting state index [1-melt; 2-freeze]\n",
     "  real (kind=kind_phys),                            intent(in)    :: fpih    !< host frozen fraction (< 0: T rule)\n",
     after=WG)
pre(gla, "     bdfall = min(120.,67.92+51.25*exp((sfctmp-tfrz)/2.59)) !mb: change to min v3.7\n\n     qrain   = prcp * (1.-fpice)\n",
    "     if (fpih >= 0.) fpice = fpih\n")

# ================================================================== Noah-MP driver
sub(drv, "      iter                                                       &\n      )\n",
    "      iter, noahmp_canopy_heat, precip_phase_host, noahmp_sw_radshare,           &\n"
    "      lw_sfc_consistent, sfc_evap_enthalpy, noahmp_heat_advect, noahmp_kirchhoff, &\n"
    "      lsswr, landfrac, adjvisbmd, adjvisdfd, adjnirbmd, adjnirdfd,               &\n"
    "      albdvis_rad, albdnir_rad, albivis_rad, albinir_rad, adjsfculw_land,       &\n"
    "      hflx_evap_enth, con_cliq, con_cvap, con_t0c                                &\n"
    "      )\n")
post(drv, "  integer, optional                      , intent(in)    :: iter       ! surface iteration (ccpp loop counter)\n",
     "  ! energy options (gfs_physics_nml) and what they need; optional, so external callers are unaffected\n"
     "  integer, optional, intent(in) :: noahmp_canopy_heat\n"
     "  logical, optional, intent(in) :: precip_phase_host, noahmp_sw_radshare, lw_sfc_consistent, &\n"
     "                                   sfc_evap_enthalpy, noahmp_heat_advect, noahmp_kirchhoff, lsswr\n"
     "  real(kind=kind_phys), dimension(:), optional, intent(in)    :: landfrac, adjvisbmd, adjvisdfd, adjnirbmd, adjnirdfd\n"
     "  real(kind=kind_phys), dimension(:), optional, intent(inout) :: albdvis_rad, albdnir_rad, albivis_rad, albinir_rad\n"
     "  real(kind=kind_phys), dimension(:), optional, intent(inout) :: adjsfculw_land, hflx_evap_enth\n"
     "  real(kind=kind_phys), intent(in) :: con_cliq, con_cvap, con_t0c  ! constants: not optional (CCPP passes parameters)\n"
     "  logical :: kir_d, adv_d\n"
     "  integer :: opt_cnh_d\n"
     "  logical :: pph, swr, lwc, eve\n"
     "  real(kind=kind_phys) :: fpcvh, swt, hev\n")
for b in ("albdvis", "albdnir", "albivis", "albinir"):
    sub(drv, f"  real(kind=kind_phys), dimension(:)     , intent(out)   :: {b} ",
        f"  real(kind=kind_phys), dimension(:)     , intent(inout) :: {b} ")
post(drv, "  if (present(iter)) first_iter = iter == 1\n",
     "\n  ! energy options\n"
     "  opt_cnh_d = 0\n  if (present(noahmp_canopy_heat)) opt_cnh_d = noahmp_canopy_heat\n"
     "  pph = .false.\n  if (present(precip_phase_host)) pph = precip_phase_host\n"
     "  swr = .false.\n  if (present(noahmp_sw_radshare)) swr = noahmp_sw_radshare\n"
     "  lwc = .false.\n  if (present(lw_sfc_consistent)) lwc = lw_sfc_consistent\n"
     "  eve = .false.\n  if (present(sfc_evap_enthalpy)) eve = sfc_evap_enthalpy\n"
     "  kir_d = .false.\n  if (present(noahmp_kirchhoff)) kir_d = noahmp_kirchhoff\n"
     "  adv_d = .false.\n  if (present(noahmp_heat_advect)) adv_d = noahmp_heat_advect\n"
     "  call noahmp_options_energy(opt_cnh_d, kir_d, adv_d, con_cliq, con_cvap, con_t0c)\n"
     "  ! the radiation ran this step with the land albedos Noah-MP left last step: keep them\n"
     "  if (present(albdvis_rad) .and. present(lsswr) .and. first_iter) then\n"
     "    if (lsswr) then\n"
     "      albdvis_rad(1:im) = albdvis(1:im)\n"
     "      albdnir_rad(1:im) = albdnir(1:im)\n"
     "      albivis_rad(1:im) = albivis(1:im)\n"
     "      albinir_rad(1:im) = albinir(1:im)\n"
     "    endif\n"
     "  endif\n")
sub(drv, "      call noahmp_options(idveg ,iopt_crs, iopt_btr , iopt_run, iopt_sfc,  &\n",
    "      ! SW1: radiation's land share (land-only cells: the cell net SW)\n"
    "      swt = -1.\n"
    "      if (swr) then\n"
    "        if (landfrac(i) >= 1.0_kind_phys) then\n"
    "          swt = snet(i)\n"
    "        elseif (albdvis_rad(i) >= 0.) then\n"
    "          swt = adjvisbmd(i)*(1.-albdvis_rad(i)) + adjvisdfd(i)*(1.-albivis_rad(i)) &\n"
    "              + adjnirbmd(i)*(1.-albdnir_rad(i)) + adjnirdfd(i)*(1.-albinir_rad(i))\n"
    "        endif\n"
    "      endif\n"
    "      hev = 0.\n"
    "      call noahmp_options(idveg ,iopt_crs, iopt_btr , iopt_run, iopt_sfc,  &\n")
GC = "        call noahmp_glacier (                                                                      &\n"
sub(drv, "          albedo_direct        ,albedo_diffuse,       errmsg               ,errflg )\n",
    "          albedo_direct        ,albedo_diffuse,       errmsg               ,errflg ,  &\n"
    "          fpice_host=merge(srflag(i), -1.0_kind_phys, pph), sw_target=swt)\n", after=GC)
SC = "        call noahmp_sflx (parameters                                          , &\n"
pre(drv, SC,
    "        ! PH2: the host's convective decision (GFS_MP_generic_post: csnow = rainc when tsfc < 273.15)\n"
    "        fpcvh = -1.\n"
    "        if (pph .and. precip_convective > 0.) then\n"
    "          fpcvh = 0.\n"
    "          if (srflag(i)*precipitation_forcing - (precip_snow + precip_graupel + precip_hail) &\n"
    "              > 0.5*precip_convective) fpcvh = 1.\n"
    "        endif\n")
sub(drv, "          errmsg                ,errflg                )\n",
    "          errmsg                ,errflg                ,                        &\n"
    "          fpcv_host=fpcvh, sw_target=swt, hevap=hev)\n", after=SC)
pre(drv, "      tsurf     (i)   = tskin(i)\n",
    "      ! LW1: the upward LW Noah-MP booked (lwdn + its net upward LW)\n"
    "      if (lwc) adjsfculw_land(i) = radiation_lw_forcing + lw_absorbed_total\n"
    "      if (eve) hflx_evap_enth(i) = hev\n")
DRV_ARGS = [
    meta_entry("noahmp_canopy_heat", "control_for_noahmp_canopy_heat_storage", "Noah-MP canopy heat option", "index",
               typ="integer", intent="in", optional=True),
    meta_entry("precip_phase_host", "flag_for_host_convective_precipitation_phase_at_surface",
               "flag: host convective snow decision at the surface", "flag", typ="logical", intent="in", optional=True),
    meta_entry("noahmp_sw_radshare", "flag_for_noahmp_radiation_share_of_shortwave",
               "flag: Noah-MP absorbs the radiation share of net SW", "flag", typ="logical", intent="in", optional=True),
    meta_entry("lw_sfc_consistent", "flag_for_surface_booked_longwave_heating",
               "flag: surface-booked LW to the lowest layer", "flag", typ="logical", intent="in", optional=True),
    meta_entry("sfc_evap_enthalpy", "flag_for_land_evaporation_enthalpy_heating",
               "flag: land evaporation enthalpy heating", "flag", typ="logical", intent="in", optional=True),
    meta_entry("noahmp_heat_advect", "flag_for_noahmp_soil_water_heat_advection",
               "flag: soil water heat advection", "flag", typ="logical", intent="in", optional=True),
    meta_entry("noahmp_kirchhoff", "flag_for_noahmp_kirchhoff_consistent_phase_change",
               "flag: Kirchhoff-consistent phase change", "flag", typ="logical", intent="in", optional=True),
    meta_entry("lsswr", "flag_for_calling_shortwave_radiation", "logical flags for sw radiation calls", "flag",
               typ="logical", intent="in", optional=True),
    meta_entry("landfrac", "land_area_fraction", "fraction of horizontal grid area occupied by land", "frac",
               dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("adjvisbmd", "surface_downwelling_direct_ultraviolet_and_visible_shortwave_flux",
               "sfc uv+vis beam sw downward flux", "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("adjvisdfd", "surface_downwelling_diffuse_ultraviolet_and_visible_shortwave_flux",
               "sfc uv+vis diff sw downward flux", "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("adjnirbmd", "surface_downwelling_direct_near_infrared_shortwave_flux",
               "sfc nir beam sw downward flux", "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("adjnirdfd", "surface_downwelling_diffuse_near_infrared_shortwave_flux",
               "sfc nir diff sw downward flux", "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True),
] + [meta_entry(f"{b}_rad", st, f"{l} land albedo used by the last radiation call", "frac",
                dims="(horizontal_loop_extent)", intent="inout", optional=True)
     for b, (n, st, l) in zip(("albdvis", "albdnir", "albivis", "albinir"), ALB)] + [
    meta_entry("adjsfculw_land", "surface_upwelling_longwave_flux_over_land", "surface upwelling longwave flux over land",
               "W m-2", dims="(horizontal_loop_extent)", intent="inout", optional=True),
    meta_entry("hflx_evap_enth", EVSTD, "land evaporation enthalpy not carried by the vapour (frame F)", "W m-2",
               dims="(horizontal_loop_extent)", intent="inout", optional=True),
    meta_entry("con_cliq", "specific_heat_of_liquid_water_at_constant_pressure", "specific heat of liquid water",
               "J kg-1 K-1", intent="in"),
    meta_entry("con_cvap", "specific_heat_of_water_vapor_at_constant_pressure", "specific heat of water vapor",
               "J kg-1 K-1", intent="in"),
    meta_entry("con_t0c", "temperature_at_zero_celsius", "temperature at 0 degree Celsius", "K",
               intent="in"),
]
meta_append(drvm, "".join(DRV_ARGS))
for b in ("albdvis", "albdnir", "albivis", "albinir"):
    s = get(drvm)
    k = s.index(f"[{b}]\n")
    j = s.index("  intent = out\n", k)
    if j > s.index("\n[", k):
        sys.exit(f"ABORT noahmpdrv.meta: intent of {b}")
    edits[drvm] = s[:j] + "  intent = inout\n" + s[j + len("  intent = out\n"):]

# ================================================================== GFS_MP_generic_post: PH1
sub(mpp, "        iopt_lake, iopt_lake_clm, lkm, use_lake_model, errmsg, errflg)\n",
    "        iopt_lake, iopt_lake_clm, lkm, use_lake_model, errmsg, errflg, precip_phase_host, con_hfus, con_cp)\n")
post(mpp, "      real(kind=kind_phys),                    intent(in)    :: dtf, frain, con_g, rainmin, rhowater\n",
     "      logical, optional,                       intent(in)    :: precip_phase_host\n"
     "      real(kind=kind_phys),                    intent(in)    :: con_hfus, con_cp\n")
post(mpp, "              crain = zero\n              csnow = rainc(i)\n            endif\n",
     "            ! PH1: convective precipitation the host calls snow froze aloft; the atmosphere pays hfus\n"
     "            if (present(precip_phase_host)) then\n"
     "              if (precip_phase_host .and. csnow > zero) gt0(i,1) = gt0(i,1)                  &\n"
     "                + con_hfus*rhowater*csnow*con_g / (con_cp*(prsi(i,1)-prsi(i,2)))\n"
     "            endif\n")
meta_append(mppm, meta_entry("precip_phase_host", "flag_for_host_convective_precipitation_phase_at_surface",
                             "flag: atmosphere pays hfus for host convective snow", "flag", typ="logical",
                             intent="in", optional=True)
            + meta_entry("con_hfus", "latent_heat_of_fusion_of_water_at_0C", "latent heat of fusion", "J kg-1",
                         intent="in")
            + meta_entry("con_cp", "specific_heat_of_dry_air_at_constant_pressure",
                         "specific heat of dry air at constant pressure", "J kg-1 K-1", intent="in"))

# ================================================================== sfc_sice: LW1 (booked non-solar minus SH and LH received)
sub(ice, "     &       errmsg, errflg, iter\n", "     &       errmsg, errflg, iter, lw_sfc_consistent, adjsfcdlw,\n"
                                             "     &       adjsfculw_ice\n")
post(ice, "      integer, optional, intent(in) :: iter\n",
     "      logical, optional, intent(in) :: lw_sfc_consistent\n"
     "      real (kind=kind_phys), dimension(:), optional, intent(in)    ::\n"
     "     &       adjsfcdlw\n"
     "      real (kind=kind_phys), dimension(:), optional, intent(inout) ::\n"
     "     &       adjsfculw_ice\n"
     "      real (kind=kind_phys) :: tice0(im), tref0(im)\n")
pre(ice, "!> - Call the three-layer thermodynamics sea ice model ice3lay().\n      call ice3lay\n",
    "!     linearisation point of ice3lay: tice reset to min(tice, tsf)\n"
    "      do i = 1, im\n"
    "        if (flag(i)) then\n"
    "          tice0(i) = tice(i)\n"
    "          tref0(i) = min(tice(i), t0c - 0.054_kind_phys)\n"
    "          if (snowd(i) > zero) tref0(i) = min(tice(i), t0c)\n"
    "        endif\n"
    "      enddo\n\n")
pre(ice, "          tsfc_wat(i) = tgice\n",
    "!         LW1: the non-solar flux ice3lay used, less the SH and LH the atmosphere receives, as upward LW\n"
    "          if (present(lw_sfc_consistent)) then\n"
    "            if (lw_sfc_consistent) adjsfculw_ice(i) = adjsfcdlw(i)\n"
    "     &        + hfi(i) + hfd(i)*(tice(i) - tref0(i))\n"
    "     &        - hflxi(i) - evapi(i)\n"
    "          endif\n")
meta_append(icem, meta_entry("lw_sfc_consistent", "flag_for_surface_booked_longwave_heating",
                             "flag: surface-booked LW to the lowest layer", "flag", typ="logical", intent="in", optional=True)
            + meta_entry("adjsfcdlw", "surface_downwelling_longwave_flux", "surface downwelling longwave flux",
                         "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True)
            + meta_entry("adjsfculw_ice", "surface_upwelling_longwave_flux_over_ice", "surface upwelling longwave flux over ice",
                         "W m-2", dims="(horizontal_loop_extent)", intent="inout", optional=True))

# ================================================================== composites_post: LW1 + EV1 heating of the lowest layer
sub(cpo, "      grav, prsik1, prslk1, prslki, z1, ztmax_wat, ztmax_lnd, ztmax_ice, huge, errmsg, errflg)\n",
    "      grav, prsik1, prslk1, prslki, z1, ztmax_wat, ztmax_lnd, ztmax_ice, huge, errmsg, errflg,                    &\n"
    "      lw_sfc_consistent, sfc_evap_enthalpy, adjsfcdlw, adjsfculw_land, adjsfculw_ice, adjsfculw_water,           &\n"
    "      sfcdlw_rad, sfculw_rad, hflx_evap_enth, prsi, dtdt, con_cp)\n")
post(cpo, "      character(len=*), intent(out) :: errmsg\n      integer,          intent(out) :: errflg\n",
     "      ! LW1 / EV1 (optional)\n"
     "      logical, optional, intent(in) :: lw_sfc_consistent, sfc_evap_enthalpy\n"
     "      real(kind=kind_phys), dimension(:), optional, intent(in) :: adjsfcdlw, adjsfculw_land, adjsfculw_ice, &\n"
     "        adjsfculw_water, sfcdlw_rad, sfculw_rad, hflx_evap_enth\n"
     "      real(kind=kind_phys), dimension(:,:), optional, intent(in)    :: prsi\n"
     "      real(kind=kind_phys), dimension(:,:), optional, intent(inout) :: dtdt\n"
     "      real(kind=kind_phys), intent(in) :: con_cp\n"
     "      logical :: lwc, eve\n"
     "      real(kind=kind_phys) :: qsfc_heat\n",
     after="   subroutine GFS_surface_composites_post_run (")
s = get(cpo)
if s.count("\n   contains\n") != 1:
    sys.exit("ABORT composites_post: internal contains")
k = s.index("\n   contains\n") + 1
blk = ("\n      ! LW1 / EV1: heat the lowest layer by what the surfaces booked and the atmosphere did not receive\n"
       "      lwc = .false.\n      if (present(lw_sfc_consistent)) lwc = lw_sfc_consistent\n"
       "      eve = .false.\n      if (present(sfc_evap_enthalpy)) eve = sfc_evap_enthalpy\n"
       "      if (lwc .or. eve) then\n"
       "        do i = 1, im\n"
       "          if (frac_grid) then\n"
       "            txl = landfrac(i)\n"
       "          else\n"
       "            txl = zero\n"
       "            if (dry(i)) txl = one\n"
       "          endif\n"
       "          txi = zero\n"
       "          if (icy(i)) txi = cice(i)*(one - txl)\n"
       "          txo = max(zero, one - txl - txi)\n"
       "          qsfc_heat = zero\n"
       "          if (lwc) then\n"
       "            if (txl > zero) qsfc_heat = qsfc_heat + txl*(adjsfculw_land(i) - adjsfcdlw(i))\n"
       "            if (txi > zero) qsfc_heat = qsfc_heat + txi*(adjsfculw_ice(i) - adjsfcdlw(i))\n"
       "            if (txo > zero) qsfc_heat = qsfc_heat + txo*(adjsfculw_water(i) - adjsfcdlw(i))\n"
       "            qsfc_heat = qsfc_heat - (sfculw_rad(i) - sfcdlw_rad(i))\n"
       "          endif\n"
       "          if (eve .and. dry(i)) qsfc_heat = qsfc_heat + txl*hflx_evap_enth(i)\n"
       "          dtdt(i,1) = dtdt(i,1) + qsfc_heat*grav/(con_cp*(prsi(i,1)-prsi(i,2)))\n"
       "        enddo\n"
       "      endif\n\n")
edits[cpo] = s[:k] + blk + s[k:]
meta_append(cpom, "".join([
    meta_entry("lw_sfc_consistent", "flag_for_surface_booked_longwave_heating",
               "flag: surface-booked LW to the lowest layer", "flag", typ="logical", intent="in", optional=True),
    meta_entry("sfc_evap_enthalpy", "flag_for_land_evaporation_enthalpy_heating",
               "flag: land evaporation enthalpy heating", "flag", typ="logical", intent="in", optional=True),
    meta_entry("adjsfcdlw", "surface_downwelling_longwave_flux", "surface downwelling longwave flux", "W m-2",
               dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("adjsfculw_land", "surface_upwelling_longwave_flux_over_land", "surface upwelling LW over land",
               "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("adjsfculw_ice", "surface_upwelling_longwave_flux_over_ice", "surface upwelling LW over ice",
               "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("adjsfculw_water", "surface_upwelling_longwave_flux_over_water", "surface upwelling LW over water",
               "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("sfcdlw_rad", "surface_downwelling_longwave_flux_on_radiation_timestep",
               "total sky sfc downward lw flux", "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("sfculw_rad", "surface_upwelling_longwave_flux_on_radiation_timestep",
               "total sky sfc upward lw flux", "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("hflx_evap_enth", EVSTD, "land evaporation enthalpy not carried by the vapour (frame F)", "W m-2",
               dims="(horizontal_loop_extent)", intent="in", optional=True),
    meta_entry("prsi", "air_pressure_at_interface", "air pressure at model layer interfaces", "Pa",
               dims="(horizontal_loop_extent,vertical_interface_dimension)", intent="in", optional=True),
    meta_entry("dtdt", "process_split_cumulative_tendency_of_air_temperature", "tendency of the temperature",
               "K s-1", dims="(horizontal_loop_extent,vertical_layer_dimension)", intent="inout", optional=True),
    meta_entry("con_cp", "specific_heat_of_dry_air_at_constant_pressure",
               "specific heat of dry air at constant pressure", "J kg-1 K-1", intent="in")]))

# ================================================================== rrtmg_lw_post: radiation-time upward LW for LW1
# (RRTMGP fills surface_upwelling_longwave_flux_on_radiation_timestep; RRTMG did not)
rlp = root / "Radiation/RRTMG/rrtmg_lw_post.F90"
rlpm = root / "Radiation/RRTMG/rrtmg_lw_post.meta"
sub(rlp, "                 errmsg, errflg)\n", "                 errmsg, errflg, sfculw)\n",
    after="      subroutine rrtmg_lw_post_run (")
post(rlp, "      real(kind=kind_phys), dimension(im),         intent(inout) ::  tsflw, sfcdlw\n",
     "      real(kind=kind_phys), dimension(:), optional, intent(inout) ::  sfculw\n")
post(rlp, "        sfcdlw(:) = sfcflw(:)%dnfxc\n", "        if (present(sfculw)) sfculw(:) = sfcflw(:)%upfxc\n")
meta_append(rlpm, meta_entry("sfculw", "surface_upwelling_longwave_flux_on_radiation_timestep",
                             "total sky sfc upward lw flux", "W m-2", dims="(horizontal_loop_extent)",
                             intent="inout", optional=True))

for p, s in edits.items():
    p.write_text(s)
    print("options", p.name)
