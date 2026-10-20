#!/usr/bin/env python3
"""apply_meter_pl1.py <ufs-weather-model> : EML meter v2 (instrumentation only, on mq12 + PL1).
The lag of step N's precipitation is now measured at probe 1 of step N+1, i.e. before the surfaces of N+1, against the
temperature the surfaces book it at (tprcp_t1 with sfc_precip_t1_carry, else that step's T1). EML columns:
1 lag c P(N) (T_sfc - T1(N)), 2 its land part (frland), 3 unmatched columns, 4 PH1 swap (em_p12, unchanged),
5 sea-ice part ((1-frland) fice), 6 the stock lag c P(N) (T1(N+1) - T1(N)) (= old EML), 7 sum |c P_sfc - c P_atm| a
(J/K, surface-side capacity from tprcp, srflag vs the atmosphere's), 8 sum c P_atm a (J/K)."""
import sys
import pathlib

D = pathlib.Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE"
edits = {}


def rep(rel, old, new, n=1):
    edits.setdefault(rel, []).append((old, new, n))


rep("energy_meter_common.F90", "eml(4) = 0.d0", "eml(8) = 0.d0")
rep("em_p12.F90", "lbuf(4), lrbuf(4)", "lbuf(8), lrbuf(8)")
rep("em_p12.F90", "call MPI_Reduce(MPI_IN_PLACE, lbuf, 4,", "call MPI_Reduce(MPI_IN_PLACE, lbuf, 8,")
rep("em_p12.F90", "call MPI_Reduce(lbuf, lrbuf, 4,", "call MPI_Reduce(lbuf, lrbuf, 8,")
rep("em_p12.F90", "write(*,'(a,i6,4es25.16)') 'EML '", "write(*,'(a,i6,8es25.16)') 'EML '")
rep("em_p12.F90",
    "       if (emla(jj) == a) then\n"
    "          eml(1) = eml(1) + emlp(jj)*(t1 - emlt(jj))*a\n"
    "          eml(2) = eml(2) + emlp(jj)*(t1 - emlt(jj))*a*frland(i)\n"
    "       else\n"
    "          eml(3) = eml(3) + 1.d0\n"
    "       endif\n",
    "       ! pl1 meter: the lag of P(N) is taken at probe 1 of N+1 (em_p01), before the surfaces\n")
rep("em_p01.F90",
    "ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, tgrs, errmsg, errflg)\n",
    "ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, tgrs, garea, frland, fice, tprcp, srflag, &\n"
    "       tprcp_t1, sfc_precip_t1_carry, errmsg, errflg)\n")
rep("em_p01.F90",
    "    real(kind=kind_phys), intent(in) :: tgrs(:,:)\n",
    "    real(kind=kind_phys), intent(in) :: tgrs(:,:)\n"
    "    real(kind=kind_phys), intent(in) :: garea(:), frland(:), fice(:), tprcp(:), srflag(:), tprcp_t1(:)\n"
    "    logical, intent(in) :: sfc_precip_t1_carry\n"
    "    integer :: jj\n"
    "    real(kind=8) :: a, t1, tu, cps\n")
rep("em_p01.F90",
    "                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, tgrs, j0)\n",
    "                  ntqv, ntcw, ntiw, ntrw, ntsw, ntgl, con_g, con_cp, con_hvap, con_hfus, tgrs, j0)\n"
    "    ! pl1 meter: step N's precipitation (emlp, emlt from em_p12 of N) as the surfaces of N+1 will book it\n"
    "    do i = 1, im\n"
    "       jj = j0 + i\n"
    "       a = garea(i)\n"
    "       t1 = tgrs(i,1)\n"
    "       tu = t1\n"
    "       if (sfc_precip_t1_carry .and. tprcp_t1(i) > 0.d0) tu = tprcp_t1(i)\n"
    "       if (emla(jj) == a) then\n"
    "          eml(1) = eml(1) + emlp(jj)*(tu - emlt(jj))*a\n"
    "          eml(2) = eml(2) + emlp(jj)*(tu - emlt(jj))*a*frland(i)\n"
    "          eml(5) = eml(5) + emlp(jj)*(tu - emlt(jj))*a*(1.d0 - frland(i))*fice(i)\n"
    "          eml(6) = eml(6) + emlp(jj)*(t1 - emlt(jj))*a\n"
    "          cps = 1000.d0*tprcp(i)*(4185.5d0*(1.d0 - srflag(i)) + 1972.d0*srflag(i))\n"
    "          eml(7) = eml(7) + abs(cps - emlp(jj))*a\n"
    "          eml(8) = eml(8) + emlp(jj)*a\n"
    "       else\n"
    "          eml(3) = eml(3) + 1.d0\n"
    "       endif\n"
    "    enddo\n")


def ent(name, std, units, dims, typ="real", kind=True):
    s = f"[{name}]\n  standard_name = {std}\n  long_name = {name}\n  units = {units}\n  dimensions = {dims}\n  type = {typ}\n"
    return s + ("  kind = kind_phys\n" if kind else "") + "  intent = in\n"


H = "(horizontal_loop_extent)"
rep("em_p01.meta", "[errmsg]\n",
    ent("garea", "cell_area", "m2", H)
    + ent("frland", "land_area_fraction", "frac", "(horizontal_dimension)")
    + ent("fice", "sea_ice_area_fraction_of_sea_area_fraction", "frac", "(horizontal_dimension)")
    + ent("tprcp", "nonnegative_lwe_thickness_of_precipitation_amount_on_dynamics_timestep", "m", "(horizontal_dimension)")
    + ent("srflag", "precipitation_type", "flag", "(horizontal_dimension)")
    + ent("tprcp_t1", "air_temperature_at_surface_adjacent_layer_at_precipitation_fallout", "K", "(horizontal_dimension)")
    + ent("sfc_precip_t1_carry", "flag_for_surface_precipitation_at_fallout_temperature", "flag", "()", "logical", False)
    + "[errmsg]\n")

out = {}
for rel, ops in edits.items():
    p = D / rel
    assert p.exists() and not p.is_symlink(), p
    s = p.read_text()
    for old, new, n in ops:
        c = s.count(old)
        assert c == n, (rel, c, old[:70])
        s = s.replace(old, new)
    out[p] = (rel, len(ops), s)
for p, (rel, n, s) in out.items():
    p.write_text(s)
    print("edited", rel, n)
