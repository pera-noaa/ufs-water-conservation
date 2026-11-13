#!/usr/bin/env python3
"""M4 for WRF's Thompson (phys/module_mp_thompson.F + phys/module_microphysics_driver.F): Thompson computes its own dry
density rho_t = 0.622 p/(R T (qv+0.622)) and uses rho_t*dz as the layer's air mass, while WRF's dry-air mass per layer is
rho*dz8w with rho = 1/alt from the dynamics; the two differ slightly, so sedimentation moves host water by the wrong
amount. mp_gt_driver gets an optional rho_dry (WRF's dry density) and, when present, sets dz1d = dz*rho_dry/rho_t, so
Thompson's rho*dz is exactly WRF's dry-air mass; all three Thompson calls in the driver pass it.
Usage: python3 port_thompson_m4_wrf.py <WRF checkout>  (after the C1-M2 and M5 commits)"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
mp, drv = root / "phys/module_mp_thompson.F", root / "phys/module_microphysics_driver.F"
s, d = mp.read_text(), drv.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


a = s.index("      SUBROUTINE mp_gt_driver(")
b = s.index("      END SUBROUTINE mp_gt_driver", a)
body = s[a:b]
body = one(body, "                              th, pii, p, w, dz,                         &\n",
           "                              th, pii, p, w, dz, rho_dry,                &\n", "arguments")
body = one(body, "      REAL, DIMENSION(ims:ime, kms:kme, jms:jme), OPTIONAL, INTENT(INOUT):: &\n                          nc, nwfa, nifa, nbca, qb, ng\n",
           "      REAL, DIMENSION(ims:ime, kms:kme, jms:jme), OPTIONAL, INTENT(INOUT):: &\n                          nc, nwfa, nifa, nbca, qb, ng\n"
           "      REAL, DIMENSION(ims:ime, kms:kme, jms:jme), OPTIONAL, INTENT(IN):: rho_dry\n", "declaration")
body = one(body, "            dz1d(k) = dz(i,k,j)\n",
           "            dz1d(k) = dz(i,k,j)\n"
           "            ! with the host's dry density, Thompson's rho*dz is exactly the host's dry-air mass\n"
           "            if (present(rho_dry)) dz1d(k) = dz(i,k,j)*rho_dry(i,k,j) &\n"
           "                 *R*t1d(k)*(MAX(1.E-10,qv(i,k,j))+0.622)/(0.622*p1d(k))\n", "dz1d")
s = s[:a] + body + s[b:]

calls = [i for i in range(len(d)) if d.startswith("             CALL mp_gt_driver(", i)]
if len(calls) != 3:
    sys.exit(f"ABORT driver: expected 3 mp_gt_driver calls, found {len(calls)}")
for c in reversed(calls):
    k = d.index("                     DZ=dz8w,                            &\n", c)
    e = d.index("\n", k) + 1
    d = d[:e] + "                     RHO_DRY=rho,                        &\n" + d[e:]
mp.write_text(s)
drv.write_text(d)
print("patched module_mp_thompson.F, module_microphysics_driver.F (M4 for WRF: 3 calls)")
