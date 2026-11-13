#!/usr/bin/env python3
"""Revert fix A (SAMF cloud-base correction, water and tracers) in a ufs_model.fd copy that has it (the inverse of the
samf part of apply_water_patches.py). Usage: python3 revert_fix_a.py <ufs_model.fd>
Every replacement must match exactly once, else nothing is written. Afterwards the only differences from
samf*.f.orig (unmodified v1) should be meter lines."""
import sys
from pathlib import Path

P = Path(sys.argv[1]) / "FV3/ccpp/physics/physics/CONV/SAMF"
REV = {
    P / "samfdeepcnv.f": [
        ("     &            edto(i) * etad(i,k) * qo(i,k) * grav/dp\n",
         "     &            edto(i) * etad(i,k) * tem1 * grav/dp\n"),
        ("     &            eta(i,k) * qo(i,k) * grav/dp\n",
         "     &            eta(i,k) * tem1 * grav/dp\n"),
        ("     &              edto(i)*etad(i,k) * ctro(i,k,n) * grav/dp\n",
         "     &              edto(i)*etad(i,k) * tem1 * grav/dp\n"),
        ("     &              eta(i,k) * ctro(i,k,n) * grav/dp\n",
         "     &              eta(i,k) * tem1 * grav/dp\n"),
    ],
    P / "samfshalcnv.f": [
        ("              if(k == kb(i)) flxtvd(i,k) = eta(i,k) * qo(i,k)\n", ""),
        ("                if(k == kb(i)) flxtvd(i,k) = eta(i,k) * ctro(i,k,n)\n", ""),
    ],
}
new = {}
for f, reps in REV.items():
    s = f.read_text()
    for old, rep in reps:
        n = s.count(old)
        if n != 1:
            sys.exit(f"ABORT {f.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
        s = s.replace(old, rep)
    new[f] = s
for f, s in new.items():
    f.with_suffix(f.suffix + ".preNOA").write_text(f.read_text())
    f.write_text(s)
    print(f"reverted fix A in {f.name}")
