#!/usr/bin/env python3
"""Apply water-closure patches to a ufs_model.fd copy.
Usage: python3 apply_water_patches.py <ufs_model.fd> samf|thom|both
Every replacement must match exactly once, else nothing is written."""
import sys
from pathlib import Path

root, which = Path(sys.argv[1]), sys.argv[2]
P = root / "FV3/ccpp/physics/physics"

SAMF = {
    P / "CONV/SAMF/samfdeepcnv.f": [
        # water: subtract what the downdraft/updraft actually took (qo), not the limited flux value
        ("     &            edto(i) * etad(i,k) * tem1 * grav/dp\n",
         "     &            edto(i) * etad(i,k) * qo(i,k) * grav/dp\n"),
        ("     &            eta(i,k) * tem1 * grav/dp\n",
         "     &            eta(i,k) * qo(i,k) * grav/dp\n"),
        # tracers: same double count, environment value ctro
        ("     &              edto(i)*etad(i,k) * tem1 * grav/dp\n",
         "     &              edto(i)*etad(i,k) * ctro(i,k,n) * grav/dp\n"),
        ("     &              eta(i,k) * tem1 * grav/dp\n",
         "     &              eta(i,k) * ctro(i,k,n) * grav/dp\n"),
    ],
    P / "CONV/SAMF/samfshalcnv.f": [
        # cloud-base flux must equal what the updraft removes from layer kb
        ("\n              flxtvd(i,k) = eta(i,k) * tem1\n",
         "\n              flxtvd(i,k) = eta(i,k) * tem1\n"
         "              if(k == kb(i)) flxtvd(i,k) = eta(i,k) * qo(i,k)\n"),
        ("\n                flxtvd(i,k) = eta(i,k) * tem1\n",
         "\n                flxtvd(i,k) = eta(i,k) * tem1\n"
         "                if(k == kb(i)) flxtvd(i,k) = eta(i,k) * ctro(i,k,n)\n"),
    ],
}

OLD_BACK = """         spechum = qv/(1.0_kind_phys+qv)

         if (convert_dry_rho) then
           qc = qc/(1.0_kind_phys+qv)
           qr = qr/(1.0_kind_phys+qv)
           qi = qi/(1.0_kind_phys+qv)
           qs = qs/(1.0_kind_phys+qv)
           qg = qg/(1.0_kind_phys+qv)

           ni = ni/(1.0_kind_phys+qv)
           nr = nr/(1.0_kind_phys+qv)
           if (is_aerosol_aware .or. merra2_aerosol_aware) then
              nc = nc/(1.0_kind_phys+qv)
              nwfa = nwfa/(1.0_kind_phys+qv)
              nifa = nifa/(1.0_kind_phys+qv)
           end if
         end if
"""
NEW_BACK = """         ! back on the pre-microphysics (dry + old vapour) basis the host uses to rebuild mass; spechum still holds its input value
         if (convert_dry_rho) then
           qc = qc*(1.0_kind_phys-spechum)
           qr = qr*(1.0_kind_phys-spechum)
           qi = qi*(1.0_kind_phys-spechum)
           qs = qs*(1.0_kind_phys-spechum)
           qg = qg*(1.0_kind_phys-spechum)

           ni = ni*(1.0_kind_phys-spechum)
           nr = nr*(1.0_kind_phys-spechum)
           if (is_aerosol_aware .or. merra2_aerosol_aware) then
              nc = nc*(1.0_kind_phys-spechum)
              nwfa = nwfa*(1.0_kind_phys-spechum)
              nifa = nifa*(1.0_kind_phys-spechum)
           end if
         end if
         spechum = qv*(1.0_kind_phys-spechum)
"""
THOM = {P / "MP/Thompson/mp_thompson.F90": [(OLD_BACK, NEW_BACK)]}

plan = {"samf": SAMF, "thom": THOM, "both": {**SAMF, **THOM}}[which]
new = {}
for f, reps in plan.items():
    s = f.read_text()
    for old, rep in reps:
        n = s.count(old)
        if n != 1:
            sys.exit(f"ABORT {f.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
        s = s.replace(old, rep)
    new[f] = s
for f, s in new.items():
    f.with_suffix(f.suffix + ".orig").write_text(f.read_text())
    f.write_text(s)
    print(f"patched {f.relative_to(root)}")
