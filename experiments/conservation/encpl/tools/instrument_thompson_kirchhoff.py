#!/usr/bin/env python3
"""K1 (option, gfs_physics_nml thompson_kirchhoff, default .false. = unchanged): Thompson delivers the heat of
FV3's Kirchhoff-consistent frame. Latent heats applied to T become L_v(T) = hvap + (cp_v - c_l)(T - T0),
L_s(T) = hvap + hfus + (cp_v - c_i)(T - T0), L_f(T) = L_s - L_v = hfus + (c_l - c_i)(T - T0) (melting too),
and ocp = 1/(Cp*(1 + qv)) so the host's cp_air*m_p*dT equals L*dm exactly (was 1/(Cp*(1 + 0.887*qv))).
Rate formulas (Clausius-Clapeyron linearisations, melting rates) are not changed; the saturation adjustment's
lvt2 uses the new lvap and ocp, so it stays consistent with the heating it applies.
Usage: instrument_thompson_kirchhoff.py <ufs-weather-model>. Anchors must match the stated count."""
import sys
from pathlib import Path

base = Path(sys.argv[1]) / "UFSATM/ccpp"
mod = base / "physics/physics/MP/Thompson/module_mp_thompson.F90"
drv = base / "physics/physics/MP/Thompson/mp_thompson.F90"
dmeta = base / "physics/physics/MP/Thompson/mp_thompson.meta"
td = base / "data/GFS_typedefs.F90"
tmeta = base / "data/GFS_typedefs.meta"
edits = {}


def sub(path, old, new, count=1):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != count:
        sys.exit(f"ABORT {path.name}: expected {count} match, found {n}: {old.strip()[:80]!r}")
    edits[path] = s.replace(old, new)


def sub_first(path, old, new, before):
    """replace the first match only; it must come before the text 'before' (the next arg table)"""
    s = edits.get(path) or path.read_text()
    i = s.find(old)
    if i < 0 or i > s.find(before):
        sys.exit(f"ABORT {path.name}: first match missing or not in the init table: {old.strip()[:80]!r}")
    edits[path] = s[:i] + new + s[i + len(old):]


# ---- namelist flag (GFS_typedefs), passed to mp_thompson_init
sub(td, "    logical              :: sedi_semi       !< flag for semi Lagrangian sedi of rain\n",
    "    logical              :: sedi_semi       !< flag for semi Lagrangian sedi of rain\n"
    "    logical              :: thompson_kirchhoff !< Thompson latent heats/heat capacity of the host energy frame\n")
sub(td, "    logical              :: sedi_semi      = .false.            !< flag for semi Lagrangian sedi of rain\n",
    "    logical              :: sedi_semi      = .false.            !< flag for semi Lagrangian sedi of rain\n"
    "    logical              :: thompson_kirchhoff = .false.        !< Thompson latent heats/heat capacity of the host energy frame\n")
sub(td, "                               sedi_semi, decfl,                                            &\n",
    "                               sedi_semi, decfl, thompson_kirchhoff,                        &\n")
sub(td, "    Model%sedi_semi        = sedi_semi\n",
    "    Model%sedi_semi        = sedi_semi\n    Model%thompson_kirchhoff = thompson_kirchhoff\n")
sub(td, "        print *, ' sedi_semi         : ', Model%sedi_semi\n",
    "        print *, ' sedi_semi         : ', Model%sedi_semi\n"
    "        print *, ' thompson_kirchhoff: ', Model%thompson_kirchhoff\n")
sub(tmeta, "[sedi_semi]\n  standard_name = flag_for_semi_Lagrangian_sedi_rain\n",
    "[thompson_kirchhoff]\n  standard_name = flag_for_thompson_kirchhoff_latent_heat\n"
    "  long_name = flag for Thompson latent heats and heat capacity of the host energy frame\n"
    "  units = flag\n  dimensions = ()\n  type = logical\n"
    "[sedi_semi]\n  standard_name = flag_for_semi_Lagrangian_sedi_rain\n")

sub(drv, "                                  is_initialized, errmsg, errflg)\n",
    "                                  is_initialized, kirchhoff, errmsg, errflg)\n")
sub(drv, "         use module_mp_thompson, only : R_uni, k_b, M_w, M_a, N_avo, lvap0, lfus\n",
    "         use module_mp_thompson, only : R_uni, k_b, M_w, M_a, N_avo, lvap0, lfus, thompson_kirchhoff\n")
sub(drv, "         real(kind_phys),           intent(in   ) :: con_pi, con_t0c, con_rv, con_cp, con_rgas, &\n",
    "         logical,                   intent(in   ) :: kirchhoff\n"
    "         real(kind_phys),           intent(in   ) :: con_pi, con_t0c, con_rv, con_cp, con_rgas, &\n")
sub(drv, "         lvap0 = con_hvap\n         lfus = con_hfus\n",
    "         lvap0 = con_hvap\n         lfus = con_hfus\n         thompson_kirchhoff = kirchhoff\n")
sub_first(dmeta, "  standard_name = flag_for_thompson_mp_scheme_initialization\n  long_name = flag carrying scheme initialization status\n  units = flag\n  dimensions = ()\n  type = logical\n  intent = inout\n[errmsg]\n",
    "  standard_name = flag_for_thompson_mp_scheme_initialization\n  long_name = flag carrying scheme initialization status\n  units = flag\n  dimensions = ()\n  type = logical\n  intent = inout\n[kirchhoff]\n  standard_name = flag_for_thompson_kirchhoff_latent_heat\n"
    "  long_name = flag for Thompson latent heats and heat capacity of the host energy frame\n"
    "  units = flag\n  dimensions = ()\n  type = logical\n  intent = in\n[errmsg]\n", "  name = mp_thompson_run")

# ---- module_mp_thompson
sub(mod, "   real(wp),            private :: olfus        !set in thompson_init\n",
    "   real(wp),            private :: olfus        !set in thompson_init\n"
    "!..Latent heat slopes and moist heat capacity factor; thompson_kirchhoff: those of the host's (FV3) frame\n"
    "   logical                      :: thompson_kirchhoff = .false.\n"
    "   real(wp),            private :: dlv = 2106.0 - 4218.0, dls = 0., dlf = 0., cpq = 0.887\n")
sub(mod, "         lsub = lvap0 + lfus\n         olfus = 1./lfus\n",
    "         lsub = lvap0 + lfus\n         olfus = 1./lfus\n"
    "         if (thompson_kirchhoff) then\n"
    "            ! FV3 heat capacities: cp_vap 1846, c_liq 4185.5, c_ice 1972\n"
    "            dlv = 1846. - 4185.5\n            dls = 1846. - 1972.\n            dlf = 4185.5 - 1972.\n"
    "            cpq = 1.\n         endif\n")
sub(mod, "(2106.0 - 4218.0)", "dlv", count=5)
sub(mod, "0.887*qv(k)", "cpq*qv(k)", count=8)
sub(mod, "lsub*ocp(k)", "ls_t(temp(k))*ocp(k)", count=14)
sub(mod, "lfus*ocp(k)", "lf_t(temp(k))*ocp(k)", count=7)
sub(mod, "lfus2 = lsub - lvap(k)", "lfus2 = ls_t(temp(k)) - lvap(k)", count=2)
for q in ("qi1d", "qs1d", "qg1d"):
    sub(mod, f"t1d(k) = t1d(k) - lsub*{q}(k)/", f"t1d(k) = t1d(k) - ls_t(t1d(k))*{q}(k)/")
sub(mod, " + lsub*(qi1d(k)+qs1d(k)+qg1d(k)))", " + ls_t(t1d(k))*(qi1d(k)+qs1d(k)+qg1d(k)))")
sub(mod, "\nend module module_mp_thompson",
    "\n   elemental real(wp) function ls_t(t)\n"
    "      !< latent heat of sublimation applied to T (lsub unless thompson_kirchhoff)\n"
    "      real(wp), intent(in) :: t\n      ls_t = lsub + dls*(t - 273.15)\n   end function ls_t\n\n"
    "   elemental real(wp) function lf_t(t)\n"
    "      !< latent heat of melting applied to T (lfus unless thompson_kirchhoff)\n"
    "      real(wp), intent(in) :: t\n      lf_t = lfus + dlf*(t - 273.15)\n   end function lf_t\n"
    "\nend module module_mp_thompson")

for p, s in edits.items():
    p.write_text(s)
    print("edited", p)
