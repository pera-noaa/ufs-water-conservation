#!/usr/bin/env python3
"""M4 for MPAS's Thompson (src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F and
mpas_atmphys_driver_microphysics.F): Thompson's air mass per layer is its own rho_t*dz with rho_t = 0.622 p/(R T (qv+0.622)),
while MPAS's dry-air mass is rho_p*dz_p (rho_p = zz*rho_zz in microphysics_from_MPAS). mp_gt_driver gets an optional
rho_dry and, when present, sets dz1d = dz*rho_dry/rho_t; both mp_gt_driver calls pass rho_dry = rho_p.
Usage: python3 port_thompson_m4_mpas.py <MPAS-Model checkout>  (after the C1-M2 and M5 commits)"""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "src/core_atmosphere/physics"
mp, drv = root / "physics_wrf/module_mp_thompson.F", root / "mpas_atmphys_driver_microphysics.F"
s, d = mp.read_text(), drv.read_text()


def one(s, old, new, what, n=1):
    if s.count(old) != n:
        sys.exit(f"ABORT {what}: expected {n} match(es), found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


a = s.index("      SUBROUTINE mp_gt_driver(")
b = s.index("      END SUBROUTINE mp_gt_driver", a)
body = s[a:b]
body = one(body, "                              th, pii, p, w, dz, dt_in, itimestep,    &\n",
           "                              th, pii, p, w, dz, rho_dry,             &\n"
           "                              dt_in, itimestep,                       &\n", "arguments")
body = one(body, "      REAL, DIMENSION(ims:ime, kms:kme, jms:jme), INTENT(IN):: &\n                          pii, p, w, dz\n",
           "      REAL, DIMENSION(ims:ime, kms:kme, jms:jme), INTENT(IN):: &\n                          pii, p, w, dz\n"
           "      REAL, DIMENSION(ims:ime, kms:kme, jms:jme), OPTIONAL, INTENT(IN):: rho_dry\n", "declaration")
body = one(body, "            dz1d(k) = dz(i,k,j)\n",
           "            dz1d(k) = dz(i,k,j)\n"
           "            ! with the host's dry density, Thompson's rho*dz is exactly the host's dry-air mass\n"
           "            if (present(rho_dry)) dz1d(k) = dz(i,k,j)*rho_dry(i,k,j) &\n"
           "                 *R*t1d(k)*(MAX(1.E-10,qv(i,k,j))+0.622)/(0.622*p1d(k))\n", "dz1d")
s = s[:a] + body + s[b:]
pat = "dz         = dz_p         , &\n"
calls = [i for i in range(len(d)) if d.startswith("call mp_gt_driver(", i)]
if len(calls) != 2:
    sys.exit(f"ABORT driver: expected 2 mp_gt_driver calls, found {len(calls)}")
for c in reversed(calls):  # the dz line inside each mp_gt_driver call (other schemes' calls also pass dz_p)
    k = d.index(pat, c)
    d = d[:k] + "dz         = dz_p         , rho_dry    = rho_p        , &\n" + d[k + len(pat):]
mp.write_text(s)
drv.write_text(d)
print("patched module_mp_thompson.F, mpas_atmphys_driver_microphysics.F (M4 for MPAS: 2 calls)")
