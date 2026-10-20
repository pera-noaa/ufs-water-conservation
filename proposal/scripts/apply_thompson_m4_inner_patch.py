#!/usr/bin/env python3
"""M4 for every Thompson inner step (folded into diff 06): the driver passes the host's dry-air layer mass, and
mp_gt_driver sets each layer's width from it at the density the column routine will use, every inner step.
Usage: python3 apply_thompson_m4_inner_patch.py <dir containing physics/MP/Thompson> (ufs/dev with diff 06 applied)
Every anchor must match exactly once (the three driver calls: three times), else nothing is written."""
import sys
from pathlib import Path

d = Path(sys.argv[1]) / "physics/MP/Thompson"
drv, mod = d / "mp_thompson.F90", d / "module_mp_thompson.F90"
a, b = drv.read_text(), mod.read_text()


def sub(s, old, new, n=1):
    if s.count(old) != n:
        sys.exit(f"ABORT: expected {n} match(es), found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


a = sub(a, "         real(kind_phys) :: dz(1:ncol,1:nlev)               !< m\n",
        "         real(kind_phys) :: dz(1:ncol,1:nlev)               !< m\n"
        "         real(kind_phys) :: dm(1:ncol,1:nlev)               !< kg m-2\n")
a = sub(a, """         !> - Layer width in m from the host's layer mass, so that Thompson's rho*dz is exactly the host's dry air
         !! (Thompson's R and RoverRv are con_rd and con_eps, as in rho); geopotential predates convection
         dz = (prsi(:,1:nlev) - prsi(:,2:nlev+1)) * (1.0_kind_phys - spechum) / (con_g * rho)
""", """         !> - Host's dry-air layer mass; mp_gt_driver takes each layer's width as this over Thompson's own density at
         !! every inner step, so that Thompson's rho*dz is exactly the host's dry air (geopotential predates convection)
         dm = (prsi(:,1:nlev) - prsi(:,2:nlev+1)) * (1.0_kind_phys - spechum) / con_g
         dz = dm / rho
""")
a = sub(a, "dz=dz, dt_in=dtstep", "dz=dz, dm=dm, dt_in=dtstep", 3)
b = sub(b, """                              pfils, pflls,                           &
                              fs_fac_rain, fs_fac_snow)
""", """                              pfils, pflls,                           &
                              fs_fac_rain, fs_fac_snow, dm)
""")
b = sub(b, """         real(wp), dimension(ims:ime, kms:kme, jms:jme), intent(in):: &
                           p, w, dz
""", """         real(wp), dimension(ims:ime, kms:kme, jms:jme), intent(in):: &
                           p, w, dz
         ! host dry-air layer mass (kg m-2): if present, sets dz1d at each inner step
         real(wp), dimension(ims:ime, kms:kme, jms:jme), optional, intent(in):: dm
""")
b = sub(b, "                  w1d(k) = w(i,k,j)\n                  dz1d(k) = dz(i,k,j)\n",
        "                  w1d(k) = w(i,k,j)\n")
b = sub(b, """                  nr1d(k) = nr(i,k,j)
                  rho(k) = RoverRv*p1d(k) / (R*t1d(k)*(qv1d(k)+RoverRv))
""", """                  nr1d(k) = nr(i,k,j)
                  rho(k) = RoverRv*p1d(k) / (R*t1d(k)*(qv1d(k)+RoverRv))
                  if (present(dm)) then
                     ! width at this inner step's density, as the column routine computes it, so rho*dz stays the host's mass
                     dz1d(k) = dm(i,k,j) / (RoverRv*p1d(k) / (R*t1d(k)*(max(1.E-10, qv1d(k))+RoverRv)))
                  else
                     dz1d(k) = dz(i,k,j)
                  endif
""")
drv.write_text(a)
mod.write_text(b)
print(f"patched {drv.name}, {mod.name} (M4 every inner step)")
