#!/usr/bin/env python3
"""Round-4 surface energy OPTIONS (gfs_physics_nml, default off). Apply after apply_options.py (round 3, with its
lwrad and twilight parts) and apply_bugfix_r4.py. Usage: apply_options_r4.py <ufs-weather-model>

  sfc_precip_enthalpy = T   EP1: precipitation lands with its frame-F enthalpy (encpl: water crosses at T1).
                            Noah-MP soil and glacier: the land gains, per kg, c_l (T1 - tfrz) for liquid and
                            c_i (T1 - T0) - c_l (tfrz - T0) for frozen (frame-F capacities: con_cliq, FV3 c_ice 1972),
                            above its latent; what PAH and the stored water's content do not supply heats the top
                            layer (snow, else soil / glacier ice). Sea ice: snowfall (stored at -li) gets the same
                            frame-F content, hfus - li included, in ice layer 1.
  lw_sfc_return       = T   LW2: the land keeps the LW it emitted beyond the radiation-time land emission
                            (stored at each radiation call): its top layer gets fira - (ulw_rad - dlw_rad), so the
                            land's net LW is the radiation's; the lowest layer gets only the rest (sea ice, the
                            composite remainder). Implies the LW1 bookkeeping.
  noahmp_pore_air     = T   AIR1: water entering or leaving soil pores does not carry the pore air's heat away
                            (Noah-MP counts pore air, cpair*(smcmax-smc), in the soil heat capacity).
  sfc_evap_enthalpy (round 3) now also covers glacier columns (EV1).
Every anchor must match exactly once; nothing is written unless all match."""
import sys
from pathlib import Path

top = Path(sys.argv[1]) / "UFSATM/ccpp"
root = top / "physics/physics"
gtd = top / "data/GFS_typedefs.F90"
gtm = top / "data/GFS_typedefs.meta"
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
gla = root / "SFC_Models/Land/Noahmp/module_sf_noahmp_glacier.F90"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
drvm = root / "SFC_Models/Land/Noahmp/noahmpdrv.meta"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
icem = root / "SFC_Models/SeaIce/CICE/sfc_sice.meta"
cpo = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.F90"
cpom = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_post.meta"
edits = {}


def get(p):
    return edits.get(p) or p.read_text()


def sub(path, old, new, after=None, before=None, count=1):
    s = get(path)
    lo, hi = 0, len(s)
    if after is not None:
        if s.count(after) != 1:
            sys.exit(f"ABORT {path.name}: anchor count {s.count(after)}: {after.strip()[:60]!r}")
        lo = s.index(after)
    if before is not None:
        hi = s.index(before, lo)
    seg = s[lo:hi]
    if seg.count(old) != count:
        sys.exit(f"ABORT {path.name}: {seg.count(old)} matches: {old.strip()[:70]!r}")
    edits[path] = s[:lo] + seg.replace(old, new) + s[hi:]


def pre(p, a, t, **kw):
    sub(p, a, t + a, **kw)


def post(p, a, t, **kw):
    sub(p, a, a + t, **kw)


def post_line(path, frag, text):
    s = get(path)
    lines = s.splitlines(keepends=True)
    hits = [k for k, l in enumerate(lines) if frag in l]
    if len(hits) != 1:
        sys.exit(f"ABORT {path.name}: line fragment count {len(hits)}: {frag!r}")
    lines.insert(hits[0] + 1, text)
    edits[path] = "".join(lines)


def meta_entry(name, std, long, units, dims="()", typ="real", intent=None, optional=False):
    t = f"[{name}]\n  standard_name = {std}\n  long_name = {long}\n  units = {units}\n  dimensions = {dims}\n  type = {typ}\n"
    if typ == "real":
        t += "  kind = kind_phys\n"
    if intent:
        t += f"  intent = {intent}\n"
    if optional:
        t += "  optional = True\n"
    return t


def meta_append(path, text):
    s = get(path)
    edits[path] = (s if s.endswith("\n") else s + "\n") + text


# ================================================================== switches and storage (GFS_typedefs)
OPTS = [("sfc_precip_enthalpy", "flag_for_surface_precipitation_enthalpy",
         "flag: precipitation lands with its frame-F enthalpy (Noah-MP, sea ice)"),
        ("lw_sfc_return", "flag_for_land_keeps_longwave_excess",
         "flag: land keeps the LW it emits beyond the radiation-time land emission"),
        ("noahmp_pore_air", "flag_for_noahmp_pore_air_heat_kept",
         "flag: Noah-MP soil pores keep the air heat when water moves")]
post_line(gtd, "    logical              :: noahmp_kirchhoff   !<",
          "".join(f"    logical              :: {n:<19}!< {l}\n" for n, s, l in OPTS))
post_line(gtd, "    logical              :: noahmp_kirchhoff   = .false.",
          "".join(f"    logical              :: {n:<19}= .false.\n" for n, s, l in OPTS))
post(gtd, "                               noahmp_kirchhoff,                                            &\n",
     "                               sfc_precip_enthalpy, lw_sfc_return, noahmp_pore_air,         &\n")
post_line(gtd, "    Model%noahmp_kirchhoff = noahmp_kirchhoff", "".join(f"    Model%{n} = {n}\n" for n, s, l in OPTS))
post_line(gtd, "        print *, ' noahmp_kirchhoff : ', Model%noahmp_kirchhoff",
          "".join(f"        print *, ' {n} : ', Model%{n}\n" for n, s, l in OPTS))
s = get(gtm)
k = s.index("[noahmp_kirchhoff]\n")
j = s.index("\n[", k) + 1
edits[gtm] = s[:j] + "".join(meta_entry(n, st, l, "flag", typ="logical") for n, st, l in OPTS) + s[j:]
ULWSTD = "surface_upwelling_longwave_flux_over_land_on_radiation_timestep"
post_line(gtd, "    real (kind=kind_phys), pointer :: albdifnir_lnd_rad (:) => null()",
          "    real (kind=kind_phys), pointer :: ulw_lnd_rad (:) => null()  !< land upward LW at the last radiation call\n")
post_line(gtd, "    allocate (Sfcprop%albdifnir_lnd_rad (IM))", "    allocate (Sfcprop%ulw_lnd_rad (IM))\n")
post_line(gtd, "    Sfcprop%albdifnir_lnd_rad = -1.0_kind_phys", "    Sfcprop%ulw_lnd_rad = -1.0_kind_phys\n")
s = get(gtm)
k = s.index("[albdifnir_lnd_rad]\n")
j = s.index("\n[", k) + 1
edits[gtm] = s[:j] + meta_entry("ulw_lnd_rad", ULWSTD, "land upward LW at the last radiation call", "W m-2",
                                dims="(horizontal_dimension)") + s[j:]

# ================================================================== Noah-MP soil
post(lsm, "  public  :: noahmp_options_energy\n",
     "  logical, save :: opt_ep  = .false.  ! precipitation lands with its frame-F enthalpy\n"
     "  logical, save :: opt_air = .false.  ! soil pores keep the air heat when water moves\n"
     "  real (kind=kind_phys), save :: ci_f = 1972.0  ! frame F ice heat capacity (FV3 c_ice)\n"
     "  public  :: noahmp_options_energy2\n")
pre(lsm, "  subroutine noahmp_options_energy(cnh, kir, adv, cl, cpv, t0)\n",
    "  subroutine noahmp_options_energy2(ep, air, ci)\n"
    "    logical, intent(in) :: ep, air\n"
    "    real (kind=kind_phys), intent(in) :: ci\n"
    "    opt_ep = ep\n    opt_air = air\n    ci_f = ci\n"
    "  end subroutine noahmp_options_energy2\n\n")
HC = ("  real (kind=kind_phys) function top_hcap(parameters, nsnow, isnow, snice, snliq, dzsnso, sh2o, sice)\n"
      "    ! heat capacity (j/m2/k) of the top layer, snow if layered, else soil, as the thermal properties use it\n"
      "    type (noahmp_parameters), intent(in) :: parameters\n"
      "    integer, intent(in) :: nsnow, isnow\n"
      "    real (kind=kind_phys), intent(in) :: snice(-nsnow+1:0), snliq(-nsnow+1:0), dzsnso(-nsnow+1:), sh2o(:), sice(:)\n"
      "    if (isnow < 0) then\n"
      "       top_hcap = snow_hcap(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))\n"
      "    else\n"
      "       top_hcap = soil_hcap1(parameters, sh2o(1), sice(1), dzsnso(1))\n"
      "    endif\n"
      "  end function top_hcap\n\n")
pre(lsm, "  subroutine noahmp_options_energy2(ep, air, ci)\n", HC)
SF = "  subroutine noahmp_sflx (parameters, &\n"
sub(lsm, "                   ,errmsg, errflg, fpcv_host, sw_target, hevap)\n",
    "                   ,errmsg, errflg, fpcv_host, sw_target, hevap, lwnet_ref, hprec_out, hlw_out)\n", after=SF, before="  end subroutine noahmp_sflx")
post(lsm, "  real (kind=kind_phys), optional, intent(out) :: hevap     !< evaporation enthalpy not carried by the vapour (w/m2)\n",
     "  real (kind=kind_phys), optional, intent(in)  :: lwnet_ref !< radiation-time land net upward LW (w/m2), lw2\n"
     "  real (kind=kind_phys), optional, intent(out) :: hprec_out !< ep1 heat given to the top layer (j/m2)\n"
     "  real (kind=kind_phys), optional, intent(out) :: hlw_out   !< lw2 heat kept by the top layer (j/m2)\n", after=SF, before="  end subroutine noahmp_sflx")
post(lsm, "  real (kind=kind_phys)              :: fpcvh, swt, hev\n",
     "  real (kind=kind_phys)              :: hprec, dqp, dqlw\n", after=SF, before="  end subroutine noahmp_sflx")
# LW2: right after the energy step
pre(lsm, "    qsfcveg  = eah*ep_2/(sfcprs + epsm1*eah)\n",
    "    ! lw2: the land keeps the LW it emitted beyond the radiation-time land emission\n"
    "    dqlw = 0.\n"
    "    if (present(lwnet_ref)) then\n"
    "       if (lwnet_ref > -1.e10) then\n"
    "          dqlw = (fira - lwnet_ref)*dt\n"
    "          stc(isnow+1) = stc(isnow+1) + dqlw/top_hcap(parameters, nsnow, isnow, snice, snliq, dzsnso, sh2o, &\n"
    "                                                    smc - sh2o)\n"
    "       endif\n"
    "    endif\n"
    "    if (present(hlw_out)) hlw_out = dqlw\n", after=SF, before="  end subroutine noahmp_sflx")
sub(lsm, "                 qsnbot ,esnow  ,hev )  !out\n", "                 qsnbot ,esnow  ,hev    ,hprec )  !out\n", after=SF, before="  end subroutine noahmp_sflx")
post(lsm, "     if (present(hevap)) hevap = hev\n",
     "     ! ep1: precipitation lands with its frame-F enthalpy; PAH and the stored water's content supplied hprec\n"
     "     dqp = 0.\n"
     "     if (opt_ep) then\n"
     "        dqp = (rain*cl_f*(sfctmp - tfrz) + snow*(ci_f*(sfctmp - t0_f) - cl_f*(tfrz - t0_f)) - pah)*dt - hprec\n"
     "        stc(isnow+1) = stc(isnow+1) + dqp/top_hcap(parameters, nsnow, isnow, snice, snliq, dzsnso, sh2o, sice)\n"
     "     endif\n"
     "     if (present(hprec_out)) hprec_out = dqp\n")
# water(): stored precipitation content
WA = "  subroutine water (parameters,vegtyp ,nsnow  ,nsoil  ,imelt  ,dt     ,uu     , & !in\n"
sub(lsm, "                    qsnbot ,esnow  ,hevap) \n", "                    qsnbot ,esnow  ,hevap  ,hprec) \n", after=WA, before="  end subroutine water")
post(lsm, "  real (kind=kind_phys), intent(out)                              :: hevap   !evaporation enthalpy not carried by the vapour [w/m2]\n",
     "  real (kind=kind_phys), intent(out)                              :: hprec   !content of the precipitation stored [j/m2]\n"
     "  real (kind=kind_phys)                                           :: hprcs, qairh\n", after=WA, before="  end subroutine water")
sub(lsm, "          &          qsnbot ,snoflow,ponding1       ,ponding2, hsnow)  !out\n",
    "          &          qsnbot ,snoflow,ponding1       ,ponding2, hsnow, hprcs)  !out\n", after=WA, before="  end subroutine water")
post(lsm, "   hevap = hevap + (qsnsub - qsnfro)*hvt1 + hsnow/dt\n", "   hprec = hprcs\n", after=WA, before="  end subroutine water")
post(lsm, "                                                    + qsnbot*(tsbot - stc(1)))\n",
     "       ! rain throughfall stored in the soil: at tg with advection, else at the layer-1 temperature\n"
     "       if (qinsur > 0.) then\n"
     "          if (opt_adv) then\n"
     "             hprec = hprec + cwk*qinfl/qinsur*dt*qthru*(tg - tfrz)\n"
     "          else\n"
     "             hprec = hprec + cwk*qinfl/qinsur*dt*qthru*(stc(1) - tfrz)\n"
     "          endif\n"
     "       endif\n", after=WA, before="  end subroutine water")
# AIR1: the AD1 temperature update also keeps the pore air heat
sub(lsm, "       if (opt_adv) then\n          do iz = 1, nsoil\n"
         "             stc(iz) = stc(iz) + qadv(iz)/(dzsnso(iz)*(hcp0(iz) + (cwat - cpair)*(sh2o(iz) - sh2o0(iz))))\n"
         "          enddo\n       endif\n",
    "       do iz = 1, nsoil\n"
    "          qairh = 0.\n"
    "          if (opt_air) qairh = cpair*(sh2o(iz) - sh2o0(iz))*dzsnso(iz)*(stc(iz) - tfrz)  ! air1: pore air heat kept\n"
    "          if (.not. opt_adv) qadv(iz) = 0.\n"
    "          if (opt_adv .or. opt_air) stc(iz) = stc(iz) + (qadv(iz) + qairh) &\n"
    "                                 /(dzsnso(iz)*(hcp0(iz) + (cwat - cpair)*(sh2o(iz) - sh2o0(iz))))\n"
    "       enddo\n", after=WA, before="  end subroutine water")
# snowwater -> snowfall / snowh2o
SW = "  subroutine snowwater (parameters,nsnow  ,nsoil  ,imelt  ,dt     ,zsoil  , & !in\n"
sub(lsm, "                        qsnbot ,snoflow,ponding1       ,ponding2, hsnow)  !out\n",
    "                        qsnbot ,snoflow,ponding1       ,ponding2, hsnow, hprcs)  !out\n", after=SW, before="  end subroutine snowwater")
post(lsm, "  real (kind=kind_phys),                              intent(out) :: hsnow  !< sensible content of sublimated water [j/m2]\n",
     "  real (kind=kind_phys),                              intent(out) :: hprcs  !< content of precipitation stored in snow [j/m2]\n"
     "  real (kind=kind_phys)                                               :: hpf, hpr\n", after=SW, before="  end subroutine snowwater")
sub(lsm, "                  snliq  ,sneqv  )                           !inout\n",
    "                  snliq  ,sneqv  ,hpf )                      !inout\n", after=SW, before="  end subroutine snowwater")
sub(lsm, "                  qsnbot ,ponding1       ,ponding2, hsnow)   !out\n",
    "                  qsnbot ,ponding1       ,ponding2, hsnow, hpr)   !out\n", after=SW, before="  end subroutine snowwater")
post(lsm, "                  qsnbot ,ponding1       ,ponding2, hsnow, hpr)   !out\n", "   hprcs = hpf + hpr\n", after=SW, before="  end subroutine snowwater")
SFL = "  subroutine snowfall (parameters,nsoil  ,nsnow  ,dt     ,qsnow  ,snowhin , & !in\n"
sub(lsm, "                       snliq  ,sneqv  )                            !inout\n",
    "                       snliq  ,sneqv  ,hpf )                       !inout\n", after=SFL, before="  end subroutine snowfall")
post(lsm, "  integer :: newnode            ! 0-no new layers, 1-creating new layers\n",
     "  real (kind=kind_phys), intent(out) :: hpf  !< sensible content created by the snowfall (j/m2, rel. tfrz)\n",
     after=SFL, before="  end subroutine snowfall")
post(lsm, "    newnode  = 0\n", "    hpf = 0.\n", after=SFL, before="  end subroutine snowfall")
post(lsm, "      snliq(0) = 0.\n    end if\n",
     "    if (newnode == 1) hpf = snow_hcap(snice(0), snliq(0), dzsnso(0))*(stc(0) - tfrz)\n", after=SFL, before="  end subroutine snowfall")
sub(lsm, "         snice(isnow+1)  = snice(isnow+1)   + qsnow   * dt\n",
    "         hpf = snow_hcap(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))*(stc(isnow+1) - tfrz)\n"
    "         snice(isnow+1)  = snice(isnow+1)   + qsnow   * dt\n", after=SFL, before="  end subroutine snowfall")
post(lsm, "         dzsnso(isnow+1) = dzsnso(isnow+1)  + snowhin * dt\n",
     "         hpf = snow_hcap(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))*(stc(isnow+1) - tfrz) - hpf\n",
     after=SFL, before="  end subroutine snowfall")
SH = "  subroutine snowh2o (parameters,nsnow  ,nsoil  ,dt     ,qsnfro ,qsnsub , & !in \n"
sub(lsm, "                      qsnbot ,ponding1       ,ponding2, hsnow)   !out\n",
    "                      qsnbot ,ponding1       ,ponding2, hsnow, hpr)   !out\n", after=SH, before="  end subroutine snowh2o")
post(lsm, "   real (kind=kind_phys),                            intent(out)   :: hsnow  !< sensible content of sublimated water [j/m2]\n",
     "   real (kind=kind_phys),                            intent(out)   :: hpr    !< content of rain stored in snow [j/m2]\n",
     after=SH, before="  end subroutine snowh2o")
pre(lsm, "   hsnow = 0.\n", "   hpr = 0.\n", after=SH, before="  end subroutine snowh2o")
sub(lsm, "         snliq(isnow+1) = snliq(isnow+1) + qrain * dt\n",
    "         hpr = snow_hcap(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))*(stc(isnow+1) - tfrz)\n"
    "         snliq(isnow+1) = snliq(isnow+1) + qrain * dt\n", after=SH, before="  end subroutine snowh2o")
post(lsm, "         snliq(isnow+1) = max(0., snliq(isnow+1))\n",
     "         hpr = snow_hcap(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))*(stc(isnow+1) - tfrz) - hpr\n",
     after=SH, before="  end subroutine snowh2o")

# cs1 consistency for round-3 code: KF1 and AD1 snow capacities per mass
sub(lsm, "                  svn  = min(1., mice(j)/(dzsnso(j)*denice))\n"
         "                  hcpn = cice*svn + cwat*min(1.-svn, mliq(j)/(dzsnso(j)*denh2o))\n",
    "                  hcpn = (cice/denice*mice(j) + cwat/denh2o*mliq(j))/dzsnso(j)   ! per mass (cs1)\n")
sub(lsm, "        svn  = min(1., snice(j)/(dzsnso(j)*denice))\n"
         "        hcpo = (cice*svn + cwat*min(1.-svn, snliq(j)/(dzsnso(j)*denh2o)))*dzsnso(j)\n"
         "        hcpn = (cice*svn + cwat*min(1.-svn, (snliq(j)+qin)/(dzsnso(j)*denh2o)))*dzsnso(j)\n",
    "        hcpo = cice/denice*snice(j) + cwat/denh2o*snliq(j)          ! per mass (cs1)\n"
    "        hcpn = cice/denice*snice(j) + cwat/denh2o*(snliq(j)+qin)\n")

# ================================================================== Noah-MP glacier
post(gla, "  real (kind=kind_phys)            :: hfus   = 0.3336e06 !< latent heat of fusion (j/kg); host value set in noahmpdrv_run\n",
     "  ! energy options and frame F constants, set in noahmpdrv_run (same values from every call)\n"
     "  logical               :: opt_ep_gla = .false., opt_ev_gla = .false.\n"
     "  real (kind=kind_phys) :: cl_f_gla = 4185.5, cpv_f_gla = 1846.0, ci_f_gla = 1972.0, t0_f_gla = 273.15\n")
GL = "  subroutine noahmp_glacier (&\n"
sub(gla, "                   errmsg    ,errflg, fpice_host, sw_target) \n",
    "                   errmsg    ,errflg, fpice_host, sw_target, lwnet_ref, hevap, hprec_out, hlw_out) \n", after=GL, before="  end subroutine noahmp_glacier")
post(gla, "  real (kind=kind_phys)                                           :: fpih, swt\n",
     "  real (kind=kind_phys), optional                 , intent(in)    :: lwnet_ref  !< radiation-time net upward LW, lw2\n"
     "  real (kind=kind_phys), optional                 , intent(out)   :: hevap      !< ev1 (w/m2)\n"
     "  real (kind=kind_phys), optional                 , intent(out)   :: hprec_out  !< ep1 heat to the top layer (j/m2)\n"
     "  real (kind=kind_phys), optional                 , intent(out)   :: hlw_out    !< lw2 heat kept (j/m2)\n"
     "  real (kind=kind_phys)                                           :: hsng, hprg, dqp, dqlw, hcg\n", after=GL, before="  end subroutine noahmp_glacier")
pre(gla, "    sice = max(0.0, smc - sh2o)   \n    sneqvo  = sneqv\n",
    "    ! lw2: the glacier keeps the LW it emitted beyond the radiation-time land emission\n"
    "    dqlw = 0.\n"
    "    if (present(lwnet_ref)) then\n"
    "       if (lwnet_ref > -1.e10) then\n"
    "          dqlw = (fira - lwnet_ref)*dt\n"
    "          if (isnow < 0) then\n"
    "             hcg = snow_hcap_glacier(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))\n"
    "          else\n"
    "             hcg = 1.e6*(0.8194 + 0.1309*0.5*dzsnso(1))*dzsnso(1)\n"
    "          endif\n"
    "          stc(isnow+1) = stc(isnow+1) + dqlw/hcg\n"
    "       endif\n"
    "    endif\n"
    "    if (present(hlw_out)) hlw_out = dqlw\n", after=GL, before="  end subroutine noahmp_glacier")
sub(gla, "                         fpice  ,esnow  ,fpih)                                   !out\n",
    "                         fpice  ,esnow  ,fpih   ,hsng   ,hprg )                  !out\n", after=GL, before="  end subroutine noahmp_glacier")
post(gla, "     if(opt_gla == 2) then\n       edir = qvap - qdew\n       fgev = edir * lathea\n     end if\n",
     "\n     ! ev1: per kg the glacier loses hsub (charged) plus its ice's content; the vapour carries hvap + cp_v (T1-T0)\n"
     "     if (present(hevap)) then\n"
     "        hevap = 0.\n"
     "        if (opt_ev_gla) hevap = (qvap - qdew)*(cl_f_gla*(tfrz - t0_f_gla) - cpv_f_gla*(sfctmp - t0_f_gla)) + hsng/dt\n"
     "     endif\n"
     "     ! ep1: precipitation lands with its frame-F enthalpy (no PAH on glaciers)\n"
     "     dqp = 0.\n"
     "     if (opt_ep_gla) then\n"
     "        dqp = (prcp*(1.-fpice)*cl_f_gla*(sfctmp - tfrz) &\n"
     "            + prcp*fpice*(ci_f_gla*(sfctmp - t0_f_gla) - cl_f_gla*(tfrz - t0_f_gla)))*dt - hprg\n"
     "        if (isnow < 0) then\n"
     "           hcg = snow_hcap_glacier(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))\n"
     "        else\n"
     "           hcg = 1.e6*(0.8194 + 0.1309*0.5*dzsnso(1))*dzsnso(1)\n"
     "        endif\n"
     "        stc(isnow+1) = stc(isnow+1) + dqp/hcg\n"
     "     endif\n"
     "     if (present(hprec_out)) hprec_out = dqp\n", after=GL, before="  end subroutine noahmp_glacier")
WG = "  subroutine water_glacier (nsnow  ,nsoil  ,imelt   ,dt       ,prcp     ,sfctmp , & !in\n"
sub(gla, "                            fpice  ,esnow  ,fpih)                                   !out\n",
    "                            fpice  ,esnow  ,fpih   ,hsng   ,hprg )                  !out\n", after=WG, before="  end subroutine water_glacier")
post(gla, "  real (kind=kind_phys),                            intent(in)    :: fpih    !< host frozen fraction (< 0: T rule)\n",
     "  real (kind=kind_phys),                            intent(out)   :: hsng    !< sublimated snow content (j/m2)\n"
     "  real (kind=kind_phys),                            intent(out)   :: hprg    !< stored precipitation content (j/m2)\n",
     after=WG, before="  end subroutine water_glacier")
sub(gla, "                             qsnbot  ,snoflow ,ponding1 ,ponding2)          !out\n",
    "                             qsnbot  ,snoflow ,ponding1 ,ponding2, hsng, hprg)  !out\n", after=WG, before="  end subroutine water_glacier")
SWG = "  subroutine snowwater_glacier (nsnow   ,nsoil   ,imelt    ,dt     ,sfctmp , & !in\n"
sub(gla, "                                qsnbot  ,snoflow ,ponding1 ,ponding2)          !out\n",
    "                                qsnbot  ,snoflow ,ponding1 ,ponding2, hsng, hprg)  !out\n", after=SWG, before="  end subroutine snowwater_glacier")
post(gla, "  real (kind=kind_phys),                              intent(out) :: ponding2 !<\n",
     "  real (kind=kind_phys),                              intent(out) :: hsng   !< sublimated snow content (j/m2)\n"
     "  real (kind=kind_phys),                              intent(out) :: hprg   !< stored precipitation content (j/m2)\n"
     "  real (kind=kind_phys)                                           :: hpf, hpr\n", after=SWG, before="  end subroutine snowwater_glacier")
sub(gla, "                          snliq  ,sneqv  )                           !inout\n",
    "                          snliq  ,sneqv  ,hpf )                      !inout\n", after=SWG, before="  end subroutine snowwater_glacier")
sub(gla, "                          qsnbot )                                       !out\n",
    "                          qsnbot ,hsng   ,hpr )                          !out\n", after=SWG, before="  end subroutine snowwater_glacier")
post(gla, "                          qsnbot ,hsng   ,hpr )                          !out\n", "   hprg = hpf + hpr\n", after=SWG, before="  end subroutine snowwater_glacier")
SFG = "  subroutine snowfall_glacier (nsoil  ,nsnow  ,dt     ,qsnow  ,snowhin , & !in\n"
sub(gla, "                               snliq  ,sneqv  )                            !inout\n",
    "                               snliq  ,sneqv  ,hpf )                       !inout\n", after=SFG, before="  end subroutine snowfall_glacier")
post(gla, "  integer :: newnode            !< 0-no new layers, 1-creating new layers\n",
     "  real (kind=kind_phys), intent(out) :: hpf  !< sensible content created by the snowfall (j/m2, rel. tfrz)\n",
     after=SFG, before="  end subroutine snowfall_glacier")
post(gla, "    newnode  = 0\n", "    hpf = 0.\n", after=SFG, before="  end subroutine snowfall_glacier")
post(gla, "      snliq(0) = 0.\n    end if\n",
     "    if (newnode == 1) hpf = snow_hcap_glacier(snice(0), snliq(0), dzsnso(0))*(stc(0) - tfrz)\n", after=SFG, before="  end subroutine snowfall_glacier")
sub(gla, "         snice(isnow+1)  = snice(isnow+1)   + qsnow   * dt\n",
    "         hpf = snow_hcap_glacier(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))*(stc(isnow+1) - tfrz)\n"
    "         snice(isnow+1)  = snice(isnow+1)   + qsnow   * dt\n", after=SFG, before="  end subroutine snowfall_glacier")
post(gla, "         dzsnso(isnow+1) = dzsnso(isnow+1)  + snowhin * dt\n",
     "         hpf = snow_hcap_glacier(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))*(stc(isnow+1) - tfrz) - hpf\n",
     after=SFG, before="  end subroutine snowfall_glacier")
SHG = "  subroutine snowh2o_glacier (nsnow    ,nsoil    ,dt     ,qsnfro ,qsnsub , & !in \n"
sub(gla, "                              qsnbot )                                       !out\n",
    "                              qsnbot ,hsng   ,hpr )                          !out\n", after=SHG, before="  end subroutine snowh2o_glacier")
post(gla, "   real (kind=kind_phys)                        :: wgdif     !< ice mass after minus sublimation\n",
     "   real (kind=kind_phys), intent(out)           :: hsng      !< sublimated snow content (j/m2)\n"
     "   real (kind=kind_phys), intent(out)           :: hpr       !< rain stored in snow content (j/m2)\n", after=SHG, before="  end subroutine snowh2o_glacier")
pre(gla, "   if(sneqv == 0.) then\n", "   hsng = 0.\n   hpr = 0.\n", after=SHG, before="  end subroutine snowh2o_glacier")
sub(gla, "      wgdif = snice(isnow+1) - qsnsub*dt + qsnfro*dt\n",
    "      hsng = (qsnsub - qsnfro)*dt*cice/denice*(stc(isnow+1) - tfrz)\n"
    "      wgdif = snice(isnow+1) - qsnsub*dt + qsnfro*dt\n", after=SHG, before="  end subroutine snowh2o_glacier")
sub(gla, "         snliq(isnow+1) = snliq(isnow+1) + qrain * dt\n",
    "         hpr = snow_hcap_glacier(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))*(stc(isnow+1) - tfrz)\n"
    "         snliq(isnow+1) = snliq(isnow+1) + qrain * dt\n", after=SHG, before="  end subroutine snowh2o_glacier")
post(gla, "         snliq(isnow+1) = max(0., snliq(isnow+1))\n",
     "         hpr = snow_hcap_glacier(snice(isnow+1), snliq(isnow+1), dzsnso(isnow+1))*(stc(isnow+1) - tfrz) - hpr\n",
     after=SHG, before="  end subroutine snowh2o_glacier")

# ================================================================== driver
sub(drv, "      hflx_evap_enth, con_cliq, con_cvap, con_t0c                                &\n",
    "      hflx_evap_enth, con_cliq, con_cvap, con_t0c,                               &\n"
    "      sfc_precip_enthalpy, lw_sfc_return, noahmp_pore_air, ulw_lnd_rad, sfcdlw_rad &\n")
post(drv, "  real(kind=kind_phys), intent(in) :: con_cliq, con_cvap, con_t0c  ! constants: not optional (CCPP passes parameters)\n",
     "  logical, optional, intent(in) :: sfc_precip_enthalpy, lw_sfc_return, noahmp_pore_air\n"
     "  real(kind=kind_phys), dimension(:), optional, intent(inout) :: ulw_lnd_rad\n"
     "  real(kind=kind_phys), dimension(:), optional, intent(in)    :: sfcdlw_rad\n"
     "  logical :: epd, lwr, aird\n"
     "  real(kind=kind_phys) :: lwref\n")
post(drv, "  call noahmp_options_energy(opt_cnh_d, kir_d, adv_d, con_cliq, con_cvap, con_t0c)\n",
     "  epd = .false.\n  if (present(sfc_precip_enthalpy)) epd = sfc_precip_enthalpy\n"
     "  lwr = .false.\n  if (present(lw_sfc_return)) lwr = lw_sfc_return .and. present(ulw_lnd_rad) .and. present(sfcdlw_rad)\n"
     "  aird = .false.\n  if (present(noahmp_pore_air)) aird = noahmp_pore_air\n"
     "  call noahmp_options_energy2(epd, aird, 1972.0_kind_phys)   ! FV3's c_ice (frame F)\n"
     "  opt_ep_gla = epd\n  opt_ev_gla = eve\n"
     "  cl_f_gla = con_cliq\n  cpv_f_gla = con_cvap\n  ci_f_gla = 1972.0_kind_phys\n  t0_f_gla = con_t0c\n")
post(drv, "      albinir_rad(1:im) = albinir(1:im)\n",
     "      if (present(ulw_lnd_rad) .and. present(adjsfculw_land)) ulw_lnd_rad(1:im) = adjsfculw_land(1:im)\n")
post(drv, "      hev = 0.\n",
     "      lwref = -1.e20\n"
     "      if (lwr) then\n"
     "        if (ulw_lnd_rad(i) >= 0.) lwref = ulw_lnd_rad(i) - sfcdlw_rad(i)\n"
     "      endif\n")
sub(drv, "          fpice_host=merge(srflag(i), -1.0_kind_phys, pph), sw_target=swt)\n",
    "          fpice_host=merge(srflag(i), -1.0_kind_phys, pph), sw_target=swt,              &\n"
    "          lwnet_ref=lwref, hevap=hev)\n")
sub(drv, "          fpcv_host=fpcvh, sw_target=swt, hevap=hev)\n",
    "          fpcv_host=fpcvh, sw_target=swt, hevap=hev, lwnet_ref=lwref)\n")
sub(drv, "  use noahmp_glacier_globals, only : hvap_gla => hvap, hsub_gla => hsub, hfus_gla => hfus\n",
    "  use noahmp_glacier_globals, only : hvap_gla => hvap, hsub_gla => hsub, hfus_gla => hfus\n"
    "  use noahmp_glacier_globals, only : opt_ep_gla, opt_ev_gla, cl_f_gla, cpv_f_gla, ci_f_gla, t0_f_gla\n")
meta_append(drvm, "".join([
    meta_entry("sfc_precip_enthalpy", "flag_for_surface_precipitation_enthalpy", "flag: precipitation frame-F enthalpy",
               "flag", typ="logical", intent="in", optional=True),
    meta_entry("lw_sfc_return", "flag_for_land_keeps_longwave_excess", "flag: land keeps its LW excess", "flag",
               typ="logical", intent="in", optional=True),
    meta_entry("noahmp_pore_air", "flag_for_noahmp_pore_air_heat_kept", "flag: pore air heat kept", "flag",
               typ="logical", intent="in", optional=True),
    meta_entry("ulw_lnd_rad", ULWSTD, "land upward LW at the last radiation call", "W m-2",
               dims="(horizontal_loop_extent)", intent="inout", optional=True),
    meta_entry("sfcdlw_rad", "surface_downwelling_longwave_flux_on_radiation_timestep", "total sky sfc downward lw flux",
               "W m-2", dims="(horizontal_loop_extent)", intent="in", optional=True)]))

# ================================================================== composites_post: LW2 leaves the land part in the land
sub(cpo, "      sfcdlw_rad, sfculw_rad, hflx_evap_enth, prsi, dtdt, con_cp)\n",
    "      sfcdlw_rad, sfculw_rad, hflx_evap_enth, prsi, dtdt, con_cp, lw_sfc_return, ulw_lnd_rad)\n")
post(cpo, "      logical :: lwc, eve\n",
     "      logical, optional, intent(in) :: lw_sfc_return\n"
     "      real(kind=kind_phys), dimension(:), optional, intent(in) :: ulw_lnd_rad\n"
     "      logical :: lwr\n")
post(cpo, "      lwc = .false.\n      if (present(lw_sfc_consistent)) lwc = lw_sfc_consistent\n",
     "      lwr = .false.\n      if (present(lw_sfc_return)) lwr = lw_sfc_return\n"
     "      lwc = lwc .or. lwr\n")
pre(cpo, "            qsfc_heat = qsfc_heat - (sfculw_rad(i) - sfcdlw_rad(i))\n",
    "            ! lw2: the land kept what it emitted beyond its radiation-time emission\n"
    "            if (lwr .and. txl > zero .and. dry(i)) then\n"
    "              if (ulw_lnd_rad(i) >= zero) qsfc_heat = qsfc_heat                                   &\n"
    "                - txl*((adjsfculw_land(i) - adjsfcdlw(i)) - (ulw_lnd_rad(i) - sfcdlw_rad(i)))\n"
    "            endif\n")
meta_append(cpom, meta_entry("lw_sfc_return", "flag_for_land_keeps_longwave_excess", "flag: land keeps its LW excess",
                             "flag", typ="logical", intent="in", optional=True)
            + meta_entry("ulw_lnd_rad", ULWSTD, "land upward LW at the last radiation call", "W m-2",
                         dims="(horizontal_loop_extent)", intent="in", optional=True))

# ================================================================== GFS_MP_generic_post: PH1 at L_f(T1) when the surface books frame-F enthalpy
mpp = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.F90"
mppm = root / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.meta"
sub(mpp, "precip_phase_host, con_hfus, con_cp)", "precip_phase_host, con_hfus, con_cp, sfc_precip_enthalpy, con_cliq)")
post(mpp, "      real(kind=kind_phys),                    intent(in)    :: con_hfus, con_cp\n",
     "      logical, optional,                       intent(in)    :: sfc_precip_enthalpy\n"
     "      real(kind=kind_phys),                    intent(in)    :: con_cliq\n"
     "      real(kind=kind_phys)                                   :: lfph\n")
sub(mpp, "              if (precip_phase_host .and. csnow > zero) gt0(i,1) = gt0(i,1)                  &\n"
         "                + con_hfus*rhowater*csnow*con_g / (con_cp*(prsi(i,1)-prsi(i,2)))\n",
    "              ! with sfc_precip_enthalpy the surface receives the snow with its frame-F enthalpy (FV3 c_ice) at the\n"
    "              ! lowest-layer T before this scheme's tendencies: freezing the rain there releases hfus + (c_l - c_i)(T1 - T0)\n"
    "              lfph = con_hfus\n"
    "              if (present(sfc_precip_enthalpy)) then\n"
    "                if (sfc_precip_enthalpy) lfph = con_hfus + (con_cliq - 1972.0_kind_phys)*(save_t(i,1) - con_t0c)\n"
    "              endif\n"
    "              if (precip_phase_host .and. csnow > zero) gt0(i,1) = gt0(i,1)                  &\n"
    "                + lfph*rhowater*csnow*con_g / (con_cp*(prsi(i,1)-prsi(i,2)))\n")
meta_append(mppm, meta_entry("sfc_precip_enthalpy", "flag_for_surface_precipitation_enthalpy",
                             "flag: precipitation frame-F enthalpy", "flag", typ="logical", intent="in", optional=True)
            + meta_entry("con_cliq", "specific_heat_of_liquid_water_at_constant_pressure", "specific heat of liquid water",
                         "J kg-1 K-1", intent="in")
            )

# ================================================================== sfc_sice: EP1 for snowfall on the ice
sub(ice, "     &       adjsfculw_ice\n     &     )\n", "     &       adjsfculw_ice, sfc_precip_enthalpy, con_hfus, con_cliq\n     &     )\n",
    after="      subroutine sfc_sice_run")
post(ice, "      real (kind=kind_phys) :: tice0(im), tref0(im)\n",
     "      logical, optional, intent(in) :: sfc_precip_enthalpy\n"
     "      real (kind=kind_phys), intent(in) :: con_hfus, con_cliq\n"
     "      real (kind=kind_phys) :: snowm(im), dqp, e1, e1x, b1x, tc1\n"
     "      real (kind=kind_phys), parameter :: di_e = 917.0_kind_phys,\n"
     "     &  ci_e = 2054.0_kind_phys, li_e = 3.34e5_kind_phys,\n"
     "     &  tfi_e = -0.054_kind_phys, tfi0_e = tfi_e - 0.0001_kind_phys\n")
post(ice, "      if (.not. do_sice) return\n", "      snowm = zero\n")
pre(ice, "            weasd(i) = weasd(i) + 1000.0_kind_phys*tprcp(i)*srflag(i)\n",
    "            snowm(i) = 1000.0_kind_phys*tprcp(i)*srflag(i)\n")
pre(ice, "      do k = 1, kice\n        do i = 1, im\n          if (flag(i)) then\n            tiice(i,k) = min(stsice(i,k), t0c)\n",
    "!     ep1: snowfall (stored at -li_e) gets its frame-F content (FV3 c_ice 1972, hfus) in ice layer 1\n"
    "      if (present(sfc_precip_enthalpy)) then\n"
    "      if (sfc_precip_enthalpy) then\n"
    "      do i = 1, im\n"
    "        if (flag(i) .and. snowm(i) > zero .and. hice(i) > zero) then\n"
    "          dqp = snowm(i)*(1972.0_kind_phys*(t1(i) - t0c) - con_hfus\n"
    "     &        - con_cliq*tfi_e + li_e)\n"
    "          tc1 = min(stsice(i,1) - t0c, tfi0_e)\n"
    "          e1  = ci_e*(tc1 - tfi_e) - li_e*(one - tfi_e/tc1)\n"
    "          e1  = e1 + dqp/(di_e*0.5_kind_phys*hice(i))\n"
    "          e1x = ci_e*(tfi0_e - tfi_e) - li_e*(one - tfi_e/tfi0_e)\n"
    "          e1  = min(e1, e1x)\n"
    "          b1x = e1 + ci_e*tfi_e + li_e\n"
    "          stsice(i,1) = (b1x - sqrt(b1x*b1x\n"
    "     &                - 4.0_kind_phys*ci_e*li_e*tfi_e))\n"
    "     &                / (ci_e+ci_e) + t0c\n"
    "        endif\n"
    "      enddo\n"
    "      endif\n"
    "      endif\n\n")
meta_append(icem, meta_entry("sfc_precip_enthalpy", "flag_for_surface_precipitation_enthalpy",
                             "flag: precipitation frame-F enthalpy", "flag", typ="logical", intent="in", optional=True)
            + meta_entry("con_hfus", "latent_heat_of_fusion_of_water_at_0C", "latent heat of fusion", "J kg-1", intent="in")
            + meta_entry("con_cliq", "specific_heat_of_liquid_water_at_constant_pressure", "specific heat of liquid water",
                         "J kg-1 K-1", intent="in"))

for p, s in edits.items():
    p.write_text(s)
    print("options r4", p.name)
