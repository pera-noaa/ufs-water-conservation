#!/usr/bin/env python3
"""fix_split_passive.py <ufs-weather-model> : (after add_def1split.py) compute the deform_1 parts in their own loop after
the deform_1/deform_2 loop, so the deform_1 statement is untouched (inside the loop the stores let -O3 share
dudz**2+dvdz**2 with deform_1 and reorder its sum: not bitwise passive, s403_3d vs p403_3d)."""
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "UFSATM/fv3/atmos_cubed_sphere/model/dyn_core.F90"
t = p.read_text()
reps = [
    ("!$OMP              dudx,dudy,dudz,dvdx,dvdy,dvdz,dwdx,dwdy,dwdz,uc_d2,uc_p1,uc_p2,uc_p3) &\n",
     "!$OMP              dudx,dudy,dudz,dvdx,dvdy,dvdz,dwdx,dwdy,dwdz,uc_d2) &\n"),
    ("             uc_p1(i,j,k) = 2*dwdz(i,j,k)**2\n"
     "             uc_p2(i,j,k) = dudz(i,j,k)**2+dvdz(i,j,k)**2\n"
     "             uc_p3(i,j,k) = tmp\n", ""),
    ("             uc_d2(i,j,k) = (dudx(i,j,k)+dvdy(i,j,k))**2\n          enddo\n       enddo\n   enddo\n",
     "             uc_d2(i,j,k) = (dudx(i,j,k)+dvdy(i,j,k))**2\n          enddo\n       enddo\n   enddo\n"
     "! upchk meter: deform_1 parts, in a loop of their own (passive)\n"
     "   do k=1,npz\n       do j=js,je\n          do i=is,ie\n"
     "             if(k > 1) then\n"
     "               tmp1 = 0.5*(dwdx(i,j,k-1)+dwdx(i,j,k))\n"
     "               tmp2 = 0.5*(dwdy(i,j,k-1)+dwdy(i,j,k))\n"
     "             else\n"
     "               tmp1 = dwdx(i,j,k)\n"
     "               tmp2 = dwdy(i,j,k)\n"
     "             endif\n"
     "             uc_p3(i,j,k) = tmp1*dudz(i,j,k)+tmp2*dvdz(i,j,k)\n"
     "             uc_p1(i,j,k) = 2*dwdz(i,j,k)**2\n"
     "             uc_p2(i,j,k) = dudz(i,j,k)**2+dvdz(i,j,k)**2\n"
     "          enddo\n       enddo\n   enddo\n")]
for a, b in reps:
    assert t.count(a) == 1, a[:70]
    t = t.replace(a, b)
p.write_text(t)
print("deform_1 parts moved to their own loop")
