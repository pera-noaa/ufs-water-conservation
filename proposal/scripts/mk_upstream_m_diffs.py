#!/usr/bin/env python3
"""Write M4 and M1 into a ufs/dev ccpp-physics tree (on top of diffs 01-05), for generating diffs 06 and 07.
Usage: python3 mk_upstream_m_diffs.py <ccpp/physics dir> m4|m1
m4 (diff 06): mp_thompson takes the host's interface pressure and sets dz = dp*(1 - spechum)/(g*rho). Upstream Thompson
   takes R and RoverRv from the host (con_rd, con_eps), so the driver's rho is Thompson's entry density and Thompson's
   rho*dz is exactly the host's dry-air layer mass; dz from phii predates deep and shallow convection.
m1 (diff 07): condensate the final clip would delete (negative, or <= R1) is exchanged with vapour, with its latent heat.
Every replacement must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root, which = Path(sys.argv[1]) / "physics/MP/Thompson", sys.argv[2]
edits = {}


def sub(name, old, new):
    p = root / name
    s = edits.get(p) or p.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[p] = s.replace(old, new)


if which == "m4":
    sub("mp_thompson.F90", "                              tgrs, prsl, phii, omega,             &\n",
        "                              tgrs, prsl, prsi, phii, omega,       &\n")
    sub("mp_thompson.F90", "         real(kind_phys),           intent(in   ) :: phii(:,:)\n",
        "         real(kind_phys),           intent(in   ) :: prsi(:,:)\n"
        "         real(kind_phys),           intent(in   ) :: phii(:,:)\n")
    sub("mp_thompson.F90",
        "         !> - Layer width in m from geopotential in m2 s-2\n"
        "         dz = (phii(:,2:nlev+1) - phii(:,1:nlev)) / con_g\n",
        "         !> - Layer width in m from the host's layer mass, so that Thompson's rho*dz is exactly the host's dry air\n"
        "         !! (Thompson's R and RoverRv are con_rd and con_eps, as in rho); geopotential predates convection\n"
        "         dz = (prsi(:,1:nlev) - prsi(:,2:nlev+1)) * (1.0_kind_phys - spechum) / (con_g * rho)\n")
    PRSL = ("[prsl]\n  standard_name = air_pressure\n  long_name = mean layer pressure\n  units = Pa\n"
            "  dimensions = (horizontal_loop_extent,vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n"
            "  intent = in\n")
    sub("mp_thompson.meta", PRSL,
        PRSL + "[prsi]\n  standard_name = air_pressure_at_interface\n  long_name = air pressure at model layer interfaces\n"
        "  units = Pa\n  dimensions = (horizontal_loop_extent,vertical_interface_dimension)\n  type = real\n"
        "  kind = kind_phys\n  intent = in\n")
elif which == "m1":
    m = "module_mp_thompson.F90"
    sub(m, "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n",
        "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n      real(wp) :: xcl\n")
    body = "".join(
        f"         xcl = {q}1d(k) + {q}ten(k)*DT\n"
        f"         if (xcl .le. R1) then\n"
        f"            {q}ten(k) = {q}ten(k) - xcl*odt\n"
        f"            qvten(k) = qvten(k) + xcl*odt\n"
        f"            tten(k) = tten(k) - {lat}*ocp(k)*xcl*odt*(1-IFDRY)\n"
        f"         endif\n"
        for q, lat in (("qc", "lvap(k)"), ("qi", "lsub"), ("qr", "lvap(k)"), ("qs", "lsub"), ("qg", "lsub")))
    sub(m, "!> - All tendencies computed, apply and pass back final values to parent.\n",
        "!> - All tendencies computed, apply and pass back final values to parent.\n"
        "      ! condensate the final clip would delete is exchanged with vapour (with its latent heat) instead\n"
        f"      do k = kts, kte\n{body}      enddo\n")
else:
    sys.exit(f"unknown change {which}")

for p, s in edits.items():
    p.write_text(s)
    print(f"patched {p.name} ({which})")
