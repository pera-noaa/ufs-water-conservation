#!/usr/bin/env python3
"""Thompson water-closure patches C3/C4 (on top of apply_thompson_c_patches.py 'c12').
Usage: python3 apply_thompson_c34_patches.py <ufs_model.fd> c3|c3f|c34
c3: keep the entry density for mass conversions at the pre-sedimentation update (the post-condensation density is
    used for fall speeds only).
c3f: c3 plus the two later density recomputes (after saturation adjustment and after rain evaporation), so
    sedimentation conserves the host's column mass.
c4: count every surface sedimentation flux as precipitation (drop the rX(kts) > 1000*R1 gates).
Every replacement must match exactly the expected count, else nothing is written."""
import re
import sys
from pathlib import Path

root, which = Path(sys.argv[1]), sys.argv[2]
f = root / "FV3/ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90"

C3 = [("""      REAL:: dtsave, odts, odt, odzq, hgt_agl, SR
""", """      REAL:: dtsave, odts, odt, odzq, hgt_agl, SR, rhon
"""), ("""         qv(k) = MAX(1.E-10, qv1d(k) + DT*qvten(k))
         rho(k) = 0.622*pres(k)/(R*temp(k)*(qv(k)+0.622))
         rhof(k) = SQRT(RHO_NOT/rho(k))
""", """         qv(k) = MAX(1.E-10, qv1d(k) + DT*qvten(k))
         ! rho stays the entry density so sedimentation conserves the host's column mass; rhon sets fall speeds
         rhon = 0.622*pres(k)/(R*temp(k)*(qv(k)+0.622))
         rhof(k) = SQRT(RHO_NOT/rhon)
"""), ("""            visco(k) = (1.718+0.0049*tempc-1.2E-5*tempc*tempc)*1.0E-5
         endif
         vsc2(k) = SQRT(rho(k)/visco(k))
         lvap(k) = lvap0 + (2106.0 - 4218.0)*tempc
         tcond(k) = (5.69 + 0.0168*tempc)*1.0E-5 * 418.936
         ocp(k) = 1./(Cp*(1.+0.887*qv(k)))
         lvt2(k)=lvap(k)*lvap(k)*ocp(k)*oRv*otemp*otemp
         if (is_aerosol_aware)                                                 &
           nwfa(k) = MAX(11.1E6*rho(k), (nwfa1d(k) + nwfaten(k)*DT)*rho(k))
""", """            visco(k) = (1.718+0.0049*tempc-1.2E-5*tempc*tempc)*1.0E-5
         endif
         vsc2(k) = SQRT(rhon/visco(k))
         lvap(k) = lvap0 + (2106.0 - 4218.0)*tempc
         tcond(k) = (5.69 + 0.0168*tempc)*1.0E-5 * 418.936
         ocp(k) = 1./(Cp*(1.+0.887*qv(k)))
         lvt2(k)=lvap(k)*lvap(k)*ocp(k)*oRv*otemp*otemp
         if (is_aerosol_aware)                                                 &
           nwfa(k) = MAX(11.1E6*rho(k), (nwfa1d(k) + nwfaten(k)*DT)*rho(k))
""")]
C3F = ("""          temp(k) = t1d(k) + DT*tten(k)
          rho(k) = 0.622*pres(k)/(R*temp(k)*(qv(k)+0.622))
""", """          temp(k) = t1d(k) + DT*tten(k)
""")
C4_RE = re.compile(r"^ *if \(r[rigs]\(kts\)\.gt\.R1\*1000\.\) &\n", re.M)

s = f.read_text()
orig = s
for old, new in C3:
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT: expected 1 match, found {n}: {old.strip()[:60]!r}")
    s = s.replace(old, new)
if which == "c3f":
    n = s.count(C3F[0])
    if n != 2:
        sys.exit(f"ABORT: expected 2 later density recomputes, found {n}")
    s = s.replace(*C3F)
elif which == "c34":
    s, n = C4_RE.subn("", s)
    if n != 4:
        sys.exit(f"ABORT: expected 4 precipitation gates, found {n}")
elif which != "c3":
    sys.exit(f"unknown variant {which}")
f.with_suffix(f.suffix + ".preC3").write_text(orig)
f.write_text(s)
print(f"patched {f.relative_to(root)} ({which})")
