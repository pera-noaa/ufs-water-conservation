#!/usr/bin/env python3
"""Thompson closure patches M4 and M1 (v1 snapshot layout; apply on top of A-C, before instrument_wb.py).
Usage: python3 apply_thompson_m_patches.py <ufs_model.fd> z|zc
z  (M4): the driver gets the host's interface pressure and sets dz = dp*(1 - spechum)/(g*rho_T), with rho_T Thompson's
         own entry density (its R = 287.04 and 0.622, not con_rd/con_eps), so Thompson's rho*dz is exactly
         the host's dry-air layer mass. dz from phii is stale by the convective virtual-temperature change, because
         get_phi_fv3 runs before deep and shallow convection.
zc (M1): also, condensate the final clip would delete (negative, or <= R1) is exchanged with vapour, with its latent
         heat, instead of being set to zero.
Every replacement must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root, which = Path(sys.argv[1]) / "FV3/ccpp/physics/physics/MP/Thompson", sys.argv[2]
edits = {}


def sub(name, old, new):
    p = root / name
    s = edits.get(p) or p.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[p] = s.replace(old, new)


sub("mp_thompson.F90", "                              tgrs, prsl, phii, omega,             &\n",
    "                              tgrs, prsl, prsi, phii, omega,       &\n")
sub("mp_thompson.F90", "         real(kind_phys),           intent(in   ) :: phii(:,:)\n",
    "         real(kind_phys),           intent(in   ) :: phii(:,:)\n"
    "         real(kind_phys),           intent(in   ) :: prsi(:,:)\n")
sub("mp_thompson.F90", "         dz = (phii(:,2:nlev+1) - phii(:,1:nlev)) / con_g\n",
    "         ! from the host's layer mass with Thompson's own entry density (R = 287.04, 0.622), so Thompson's rho*dz\n"
    "         ! is exactly the host's dry air; phii predates convection\n"
    "         dz = (prsi(:,1:nlev) - prsi(:,2:nlev+1)) * (1.0_kind_phys - spechum) &\n"
    "              / (con_g * 0.622_kind_phys*prsl/(287.04_kind_phys*tgrs*(qv+0.622_kind_phys)))\n")
PRSL = ("[prsl]\n  standard_name = air_pressure\n  long_name = mean layer pressure\n  units = Pa\n"
        "  dimensions = (horizontal_loop_extent,vertical_layer_dimension)\n  type = real\n  kind = kind_phys\n"
        "  intent = in\n")
sub("mp_thompson.meta", PRSL,
    PRSL + "[prsi]\n  standard_name = air_pressure_at_interface\n  long_name = air pressure at model layer interfaces\n"
    "  units = Pa\n  dimensions = (horizontal_loop_extent,vertical_interface_dimension)\n  type = real\n"
    "  kind = kind_phys\n  intent = in\n")

if which == "zc":
    m = "module_mp_thompson.F90"
    s = (root / m).read_text()
    import re
    decl = re.search(r"      REAL:: dtsave, odts, odt, odzq, hgt_agl, SR(, rhon)?\n", s)
    if not decl:
        sys.exit("ABORT: declaration anchor")
    sub(m, decl.group(0), decl.group(0) + "      REAL:: xcl\n")
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
elif which != "z":
    sys.exit(f"unknown variant {which}")

for p, s in edits.items():
    p.with_suffix(p.suffix + ".preM").write_text(p.read_text())
    p.write_text(s)
    print(f"patched {p.name} ({which})")
