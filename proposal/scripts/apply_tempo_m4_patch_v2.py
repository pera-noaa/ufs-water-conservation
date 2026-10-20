#!/usr/bin/env python3
"""M4 for TEMPO's CCPP driver (physics/MP/TEMPO/mp_tempo.F90 + .meta): dz came from phii, which get_phi_fv3 computes
before convection heats the column, so TEMPO's rho*dz differed from the host's layer mass and sedimentation lost host
water. Take dz = dp*(1-spechum)/(g*rho) with rho exactly as TEMPO computes it (its own rdry, roverrv, min_qv), so
TEMPO's rho*dz is the host's dry-air mass whatever its gas constants. Version 2 (round-2 review): dz is computed inside
the inner loop (do it = 1, ndt) from the current new_tgrs and qv, because tempo_main recomputes rho from the state at
each call; computed once before the loop it held only for the first inner step. Adds prsi to mp_tempo.meta (standard
name already in UFSATM and SCM). Apply after apply_tempo_b_patch.py.
Usage: python3 apply_tempo_m4_patch_v2.py <ccpp-physics checkout>"""
import sys
from pathlib import Path

d = Path(sys.argv[1]) / "physics/MP/TEMPO"
f90, meta = d / "mp_tempo.F90", d / "mp_tempo.meta"
s, m = f90.read_text(), meta.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


s = one(s, "      use module_mp_tempo_params, only : roverrv, eps, naccn0, naccn1, nain0, nain1\n",
        "      use module_mp_tempo_params, only : roverrv, eps, naccn0, naccn1, nain0, nain1, min_qv\n", "imports")
s = one(s, "        tgrs, prsl, phii, omega, &\n", "        tgrs, prsl, prsi, phii, omega, &\n", "run arguments")
s = one(s, "         real(kind_phys),           intent(in   ) :: prsl(:,:)\n         real(kind_phys),           intent(in   ) :: phii(:,:)\n",
        "         real(kind_phys),           intent(in   ) :: prsl(:,:)\n"
        "         real(kind_phys),           intent(in   ) :: prsi(:,:)\n"
        "         real(kind_phys),           intent(in   ) :: phii(:,:)\n", "declaration")
s = one(s, "         !> - Layer width in m from geopotential in m2 s-2\n         dz = (phii(:,2:nlev+1) - phii(:,1:nlev)) / con_g\n\n",
        "", "dz")
s = one(s, "         do it = 1, ndt\n\n            !> - Density of air in kg m-3\n",
        "         do it = 1, ndt\n\n"
        "            !> - Layer width in m from the host's layer mass, with rho as TEMPO computes it from the current state,\n"
        "            !! so that TEMPO's rho*dz is exactly the host's dry air at every inner step; geopotential predates\n"
        "            !! convection\n"
        "            dz = (prsi(:,1:nlev) - prsi(:,2:nlev+1)) * (1.0_kind_phys - spechum) * rdry * new_tgrs &\n"
        "                 * (max(min_qv, qv) + roverrv) / (con_g * roverrv * prsl)\n\n"
        "            !> - Density of air in kg m-3\n", "dz in the inner loop")
m = one(m, "[phii]\n  standard_name = geopotential_at_interface\n",
        "[prsi]\n  standard_name = air_pressure_at_interface\n  long_name = air pressure at model layer interfaces\n"
        "  units = Pa\n  dimensions = (horizontal_loop_extent,vertical_interface_dimension)\n  type = real\n"
        "  kind = kind_phys\n  intent = in\n[phii]\n  standard_name = geopotential_at_interface\n", "meta")
f90.write_text(s)
meta.write_text(m)
print("patched mp_tempo.F90, mp_tempo.meta (M4)")
