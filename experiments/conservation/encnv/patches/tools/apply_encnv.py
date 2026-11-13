#!/usr/bin/env python3
"""Energy fixes for SAMF convection and GSL drag, applied by anchor substitution to a ufs-weather-model tree.
Usage: apply_encnv.py <ufs-weather-model> <fix id> [<fix id> ...]
  D3A  samfdeepcnv/samfshalcnv: detrained condensate put into ice (263->233 K ramp) gets its latent heat of fusion
  D3B  samfdeepcnv/samfshalcnv: CMT KE loss returned as heat in the interface (Boville-Bretherton) form,
       namelist samf_cmt_heat (default .false.)
  D4   ugwpv1_gsldrag: GSL drag (ls, bl, ss, tofd) KE loss as heat, -d(KE)/cp per layer, taken after the NGW
       increment; GFS_GWD_generic_post: heat for the cross term of the joint process-split update (D12);
       namelist gwd_ke_heat (default .false.)
  D4N  ugwpv1_gsldrag: UGWP-v1 NGW heating, namelist ngw_heat_opt: 0 as is (default), 1 = -d(KE)/cp of its own
       increment only, 2 = keep it and withdraw the column's net NGW energy input at the launch level
  D3B_R1, D4_R1  round-1 unconditional per-layer versions (kept for reproducibility)
  Order: D3A, D3B, D4, D4N (each later diff is made on top of the earlier ones).
Every anchor must match the stated number of times; nothing is written unless all match."""
import sys
from pathlib import Path

phys = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
samf = phys / "CONV/SAMF"
edits = {}


def sub(path, old, new, count=1, last=False):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    if last:  # replace only the last occurrence
        i = s.rindex(old)
        edits[path] = s[:i] + new + s[i + len(old):]
    else:
        edits[path] = s.replace(old, new)


ccpp = Path(sys.argv[1]) / "UFSATM/ccpp"
td, tm = ccpp / "data/GFS_typedefs.F90", ccpp / "data/GFS_typedefs.meta"


def nml(name, typ, default, std, lname):
    # new GFS physics namelist switch, next to the GSL drag flags
    sub(td, "    logical              :: do_gsl_drag_tofd     !< flag for GSL drag (turbulent orog form drag only)\n",
        "    logical              :: do_gsl_drag_tofd     !< flag for GSL drag (turbulent orog form drag only)\n"
        f"    {typ:20s} :: {name:20s} !< {lname}\n")
    sub(td, "    logical              :: do_gsl_drag_tofd     = .false.      !< flag for GSL drag (turbulent orog form drag only)\n",
        "    logical              :: do_gsl_drag_tofd     = .false.      !< flag for GSL drag (turbulent orog form drag only)\n"
        f"    {typ:20s} :: {name:20s} = {default:12s} !< {lname}\n")
    old = "                               do_gwd_opt_psl, do_ngw_ec,                                   &\n"
    sub(td, old, old + "                               " + f"{name},".ljust(61) + "&\n")
    sub(td, "    Model%do_gsl_drag_tofd     = do_gsl_drag_tofd\n",
        "    Model%do_gsl_drag_tofd     = do_gsl_drag_tofd\n" + f"    Model%{name:20s} = {name}\n")
    sub(td, "      print *, ' do_gsl_drag_tofd     : ', Model%do_gsl_drag_tofd\n",
        "      print *, ' do_gsl_drag_tofd     : ', Model%do_gsl_drag_tofd\n"
        + f"      print *, ' {name:20s} : ', Model%{name}\n")
    sub(tm, "[do_gwd_opt_psl]\n", meta_block(name, typ, std, lname, None) + "[do_gwd_opt_psl]\n")


def meta_block(name, typ, std, lname, intent):
    t = "logical" if typ == "logical" else "integer"
    b = f"[{name}]\n  standard_name = {std}\n  long_name = {lname}\n  units = flag\n  dimensions = ()\n  type = {t}\n"
    return b + (f"  intent = {intent}\n" if intent else "")


HFUS_META = ("[hfus]\n  standard_name = latent_heat_of_fusion_of_water_at_0C\n  long_name = latent heat of fusion\n"
             "  units = J kg-1\n  dimensions = ()\n  type = real\n  kind = kind_phys\n  intent = in\n")


def add_hfus(f, meta, argold):
    # new argument hfus right after hvap (Fortran and metadata order agree)
    sub(f, argold, argold.replace("hvap,rd,rv,     ", "hvap,hfus,rd,rv,"))
    sub(f, "      implicit none\n", "      implicit none\n      real(kind=kind_phys), intent(in) :: hfus\n")
    sub(meta, "  intent = in\n[rd]\n", "  intent = in\n" + HFUS_META + "[rd]\n")


def d3a():
    f, m = samf / "samfdeepcnv.f", samf / "samfdeepcnv.meta"
    add_hfus(f, m, "     &    eps,epsm1,fv,grav,hvap,rd,rv,     ")
    sub(f, "                new_qtr(i,k,1) = new_qtr(i,k,1) + tem * tem1  ! ice\n"
           "                new_qtr(i,k,2) = new_qtr(i,k,2) + tem * (1.0_conv_wp\n"
           "     &                         - tem1) ! water\n",
        "                new_qtr(i,k,1) = new_qtr(i,k,1) + tem * tem1  ! ice\n"
        "                new_qtr(i,k,2) = new_qtr(i,k,2) + tem * (1.0_conv_wp\n"
        "     &                         - tem1) ! water\n"
        "!               freezing of the ice part releases hfus (h is liquid-referenced)\n"
        "                new_t1(i,k) = new_t1(i,k) + real(hfus, kind=conv_wp)\n"
        "     &                      / real(cp, kind=conv_wp) * tem * tem1\n")
    f, m = samf / "samfshalcnv.f", samf / "samfshalcnv.meta"
    add_hfus(f, m, "     &     eps,epsm1,fv,grav,hvap,rd,rv,     ")
    sub(f, "                ! Ice\n                new_qtr(i,k,1) = new_qtr(i,k,1) + tem * tem1\n",
        "                ! Ice\n                new_qtr(i,k,1) = new_qtr(i,k,1) + tem * tem1\n"
        "!               freezing of the ice part releases hfus (h is liquid-referenced)\n"
        "                new_t1(i,k) = new_t1(i,k) + real(hfus, kind=conv_wp)\n"
        "     &                      / real(cp, kind=conv_wp) * tem * tem1\n")


CMT_HEAT = ("!             CMT dissipative heating: KE lost by momentum transport, -d(KE)/cp\n"
            "              new_t1(i,k) = new_t1(i,k) - 0.5_conv_wp\n"
            "     &          * (new_u1(i,k)**2 + new_v1(i,k)**2\n"
            "     &          - real(u1(i,k), kind=conv_wp)**2\n"
            "     &          - real(v1(i,k), kind=conv_wp)**2)\n"
            "     &          / real(cp, kind=conv_wp)\n")


def d3b_r1():
    f = samf / "samfdeepcnv.f"
    old = ("              new_v1(i,k) = real(v1(i,k), kind=conv_wp)\n"
           "     &                    + tem2 * dellav(i,k)\n")
    sub(f, old, old + CMT_HEAT)
    f = samf / "samfshalcnv.f"
    old = ("              new_v1(i,k) = real(v1(i,k), kind=conv_wp) + dellav(i,k)\n"
           "     &                    * xmb(i) * dt2\n")
    sub(f, old, old + CMT_HEAT)


def d4_r1():
    f = phys / "GWD/ugwpv1_gsldrag.F90"
    old = "!\n! get total sso-OGW + NGW\n!\n"
    new = ("!\n! GSL drag (ls, bl, ss, tofd) dissipative heating: KE lost by the drag, -d(KE)/cp\n!\n"
           "    if ( do_gsl_drag_ls_bl.or.do_gsl_drag_ss.or.do_gsl_drag_tofd) then\n"
           "      do k=1,levs\n        do i=1,im\n"
           "          Pdtdt(i,k) = Pdtdt(i,k) - ( Pdudt(i,k)*(ugrs(i,k) + 0.5*dtp*Pdudt(i,k))       &\n"
           "                                    + Pdvdt(i,k)*(vgrs(i,k) + 0.5*dtp*Pdvdt(i,k)) )/con_cp\n"
           "        enddo\n      enddo\n    endif\n" + old)
    sub(f, old, new)


def uc(a):  # real(a, kind=conv_wp)
    return f"real({a}, kind=conv_wp)"


CMT_IF = (
    "!> - CMT dissipative heating (samf_cmt_heat), Boville-Bretherton interface form: momentum moved\n"
    "!!   across each interface x time-centred shear, half to each adjacent layer; column total = -d(KE)\n"
    "      if (samf_cmt_heat) then\n"
    "        do i = 1, im\n"
    "          if (cnvflg(i)) then\n"
    "            cmtu = 0.0_conv_wp\n"
    "            cmtv = 0.0_conv_wp\n"
    "            do k = 1, km\n"
    "              cmtq(k) = 0.0_conv_wp\n"
    "            enddo\n"
    "            do k = km, 2, -1\n"
    "              cmtu = cmtu - real(delp(i,k), kind=conv_wp)\n"
    "     &             * (new_u1(i,k) - real(u1(i,k), kind=conv_wp))\n"
    "              cmtv = cmtv - real(delp(i,k), kind=conv_wp)\n"
    "     &             * (new_v1(i,k) - real(v1(i,k), kind=conv_wp))\n"
    "              tem = 0.5_conv_wp * (cmtu * (new_u1(i,k)\n"
    "     &            + real(u1(i,k), kind=conv_wp) - new_u1(i,k-1)\n"
    "     &            - real(u1(i,k-1), kind=conv_wp))\n"
    "     &            + cmtv * (new_v1(i,k)\n"
    "     &            + real(v1(i,k), kind=conv_wp) - new_v1(i,k-1)\n"
    "     &            - real(v1(i,k-1), kind=conv_wp)))\n"
    "              cmtq(k)   = cmtq(k)   + 0.5_conv_wp * tem\n"
    "              cmtq(k-1) = cmtq(k-1) + 0.5_conv_wp * tem\n"
    "            enddo\n"
    "            cmtu = cmtu - real(delp(i,1), kind=conv_wp)\n"
    "     &           * (new_u1(i,1) - real(u1(i,1), kind=conv_wp))\n"
    "            cmtv = cmtv - real(delp(i,1), kind=conv_wp)\n"
    "     &           * (new_v1(i,1) - real(v1(i,1), kind=conv_wp))\n"
    "            cmtq(1) = cmtq(1) + 0.5_conv_wp * (cmtu * (new_u1(i,1)\n"
    "     &              + real(u1(i,1), kind=conv_wp)) + cmtv\n"
    "     &              * (new_v1(i,1) + real(v1(i,1), kind=conv_wp)))\n"
    "            do k = 1, km\n"
    "              new_t1(i,k) = new_t1(i,k) + cmtq(k)\n"
    "     &          / (real(cp, kind=conv_wp)\n"
    "     &          * real(delp(i,k), kind=conv_wp))\n"
    "            enddo\n"
    "          endif\n"
    "        enddo\n"
    "      endif\n")

SAMF_SW_META = meta_block("samf_cmt_heat", "logical", "flag_for_convective_momentum_transport_dissipation_heating",
                          "flag for SAMF convective momentum transport dissipative heating", "in")


def d3b():
    nml("samf_cmt_heat", "logical", ".false.", "flag_for_convective_momentum_transport_dissipation_heating",
        "flag for SAMF convective momentum transport dissipative heating")
    for f, argold, argnew in (
            (samf / "samfdeepcnv.f", "     &    sigmab_coldstart,cat_adj_deep,              ",
             "     &    sigmab_coldstart,cat_adj_deep,samf_cmt_heat,"),
            (samf / "samfshalcnv.f", "cat_adj_shal,errmsg,errflg)",
             "cat_adj_shal,samf_cmt_heat,\n     &     errmsg,errflg)")):
        sub(f, argold, argnew)
        old = "      integer, intent(in)  :: im, km, nn, itc, ntc, ntk, ntr, ncloud\n"
        sub(f, old, old + "      logical, intent(in)  :: samf_cmt_heat\n"
                          "      real(kind=conv_wp) :: cmtu, cmtv, cmtq(km)\n")
        old = "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n"
        sub(f, old, CMT_IF + old)
        m = f.with_suffix(".meta")
        sub(m, "[errmsg]\n", SAMF_SW_META + "[errmsg]\n", count=2, last=True)


GWD_SW_META = meta_block("gwd_ke_heat", "logical", "flag_for_gravity_wave_drag_dissipation_heating",
                         "flag for GSL drag dissipative heating = -d(KE)/cp and the joint-update cross term", "in")
NGW_SW_META = meta_block("ngw_heat_opt", "integer", "control_for_nonorographic_gravity_wave_heating",
                         "UGWP-v1 NGW heating: 0 scheme, 1 -d(KE)/cp of its own increment, 2 withdraw net input at launch",
                         "in")


def d4():
    nml("gwd_ke_heat", "logical", ".false.", "flag_for_gravity_wave_drag_dissipation_heating",
        "flag for GSL drag dissipative heating = -d(KE)/cp and the joint-update cross term")
    f = phys / "GWD/ugwpv1_gsldrag.F90"
    sub(f, "          lprnt, ipr, spp_wts_gwd, spp_gwd, errmsg, errflg)\n",
        "          lprnt, ipr, spp_wts_gwd, spp_gwd, gwd_ke_heat, errmsg, errflg)\n")
    sub(f, "    integer :: i, k\n", "    integer :: i, k\n    logical, intent(in) :: gwd_ke_heat\n"
                                 "    real(kind=kind_phys) :: un, vn\n")
    sub(phys / "GWD/ugwpv1_gsldrag.meta", "[errmsg]\n", GWD_SW_META + "[errmsg]\n", count=3, last=True)
    old = "!\n! get total sso-OGW + NGW\n!\n"
    new = ("!\n! gwd_ke_heat: GSL drag (ls, bl, ss, tofd) dissipative heating, -d(KE)/cp of the drag increment\n"
           "! applied after the NGW increment, so the joint GWD update conserves energy\n!\n"
           "    if (gwd_ke_heat .and. (do_gsl_drag_ls_bl.or.do_gsl_drag_ss.or.do_gsl_drag_tofd)) then\n"
           "      do k=1,levs\n        do i=1,im\n"
           "          un = 0.\n          vn = 0.\n"
           "          if (do_ugwp_v1) then\n"
           "            un = dtp*dudt_ngw(i,k)\n            vn = dtp*dvdt_ngw(i,k)\n          endif\n"
           "          Pdtdt(i,k) = Pdtdt(i,k) - ( Pdudt(i,k)*(ugrs(i,k) + un + 0.5*dtp*Pdudt(i,k))   &\n"
           "                                    + Pdvdt(i,k)*(vgrs(i,k) + vn + 0.5*dtp*Pdvdt(i,k)) )/con_cp\n"
           "        enddo\n      enddo\n    endif\n" + old)
    sub(f, old, new)
    # D12: joint process-split update (pending + GWD tendencies) -> heat for the KE cross term
    g = phys / "Interstitials/UFS_SCM_NEPTUNE/GFS_GWD_generic_post.F90"
    sub(g, "      &  index_of_y_wind, index_of_process_orographic_gwd, errmsg, errflg)\n",
        "      &  index_of_y_wind, index_of_process_orographic_gwd, gwd_ke_heat, con_cp, errmsg, errflg)\n")
    sub(g, "      integer, intent(in) :: im, levs, ntrac, tend_opt_gwd\n",
        "      integer, intent(in) :: im, levs, ntrac, tend_opt_gwd\n      logical, intent(in) :: gwd_ke_heat\n"
        "      real(kind=kind_phys), intent(in) :: con_cp\n")
    old = ("        case (3) !add tendencies to sum and apply\n"
           "                  !Current state = current state + dt*(accumulated tendency + current tendency)\n"
           "                  !Accumulated tendency = 0\n")
    sub(g, old, old +
        "          if (gwd_ke_heat) then\n"
        "            ! joint update of the pending (PBL) and GWD wind increments: heat the KE cross term\n"
        "            do k=1,levs\n              do i=1,im\n"
        "                gt0(i,k) = gt0(i,k) - dtp*dtp*(dudt(i,k)*ten_u(i,k) + dvdt(i,k)*ten_v(i,k))/con_cp\n"
        "              end do\n            end do\n          endif\n")
    gm = g.with_suffix(".meta")
    cp_meta = ("[con_cp]\n  standard_name = specific_heat_of_dry_air_at_constant_pressure\n"
               "  long_name = specific heat of dry air at constant pressure\n  units = J kg-1 K-1\n"
               "  dimensions = ()\n  type = real\n  kind = kind_phys\n  intent = in\n")
    sub(gm, "[errmsg]\n", GWD_SW_META + cp_meta + "[errmsg]\n")


def d4n():
    nml("ngw_heat_opt", "integer", "0", "control_for_nonorographic_gravity_wave_heating",
        "UGWP-v1 NGW heating: 0 scheme, 1 -d(KE)/cp of its own increment, 2 withdraw net input at launch")
    f = phys / "GWD/ugwpv1_gsldrag.F90"
    sub(f, "spp_wts_gwd, spp_gwd, gwd_ke_heat, errmsg, errflg)\n",
        "spp_wts_gwd, spp_gwd, gwd_ke_heat, ngw_heat_opt,       &\n          errmsg, errflg)\n")
    sub(f, "    logical, intent(in) :: gwd_ke_heat\n",
        "    logical, intent(in) :: gwd_ke_heat\n    integer, intent(in) :: ngw_heat_opt\n"
        "    integer :: kl\n    real(kind=kind_phys) :: ngwe\n")
    sub(f, "    use cires_ugwpv1_module,   only:  knob_ugwp_version, cires_ugwp_dealloc, tamp_mpa\n",
        "    use cires_ugwpv1_module,   only:  knob_ugwp_version, cires_ugwp_dealloc, tamp_mpa\n"
        "    use cires_ugwpv1_module,   only:  knob_ugwp_palaunch\n")
    sub(phys / "GWD/ugwpv1_gsldrag.meta", GWD_SW_META + "[errmsg]\n", GWD_SW_META + NGW_SW_META + "[errmsg]\n")
    old = "    end if   ! do_ugwp_v1\n"
    sub(f, old, old +
        "!\n! ngw_heat_opt = 1: NGW heating is the KE loss of its own wind increment only\n"
        "! ngw_heat_opt = 2: keep it; withdraw the column's net NGW energy input at the launch level\n!\n"
        "    if (do_ugwp_v1 .and. ngw_heat_opt == 1) then\n"
        "      do k=1,levs\n        do i=1,im\n"
        "          dtdt_ngw(i,k) = -( dudt_ngw(i,k)*(ugrs(i,k) + 0.5*dtp*dudt_ngw(i,k))          &\n"
        "                           + dvdt_ngw(i,k)*(vgrs(i,k) + 0.5*dtp*dvdt_ngw(i,k)) )/con_cp\n"
        "        enddo\n      enddo\n"
        "    else if (do_ugwp_v1 .and. ngw_heat_opt == 2) then\n"
        "      do i=1,im\n"
        "        ngwe = 0.\n"
        "        do k=1,levs\n"
        "          ngwe = ngwe + del(i,k)*( con_cp*dtdt_ngw(i,k)                                  &\n"
        "                 + dudt_ngw(i,k)*(ugrs(i,k) + 0.5*dtp*dudt_ngw(i,k))                    &\n"
        "                 + dvdt_ngw(i,k)*(vgrs(i,k) + 0.5*dtp*dvdt_ngw(i,k)) )\n"
        "        enddo\n"
        "        do kl=1,levs\n          if (prsl(i,kl) < knob_ugwp_palaunch) exit\n        enddo\n"
        "        kl = max(kl-1, 3)     ! launch layer, as in cires_ugwpv1_ngw_solv2\n"
        "        dtdt_ngw(i,kl) = dtdt_ngw(i,kl) - ngwe/(con_cp*del(i,kl))\n"
        "      enddo\n"
        "    endif\n")


fixes = {"D3A": d3a, "D3B": d3b, "D4": d4, "D4N": d4n, "D3B_R1": d3b_r1, "D4_R1": d4_r1}
for fid in sys.argv[2:]:
    fixes[fid]()
for p, s in edits.items():
    p.write_text(s)
    print("patched", p.relative_to(Path(sys.argv[1])))
