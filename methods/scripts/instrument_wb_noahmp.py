#!/usr/bin/env python3
"""Noah-MP land water-balance meter by storage term (diagnostic builds only; apply after instrument_wb_land.py).
Usage: python3 instrument_wb_noahmp.py <ufs_model.fd>
Per computed land column and step, unweighted sums (mm), category 1 = soil points, 2 = glacier points (isice):
  WBN kdt  then for c = 1, 2 (Fortran order, wbn(c,t)): t = 1/2 canopy water in/out, 3/4 snow (weasd) in/out,
           5/6 soil water sum(smc*dz)*1000 in/out, 7/8 aquifer in/out, 9 precipitation used, 10 evapotranspiration,
           11 runoff (surface + baseflow), 12 Noah-MP errwat, 13 columns
"in" is the state the driver receives (before any driver adjustment), "out" what it returns. Canopy and aquifer are
undefined on glacier points and are left out there. Printed with WBL at each step change and at finalize."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "FV3/ccpp/physics/physics"
drv = root / "SFC_Models/Land/Noahmp/noahmpdrv.F90"
mpt = root / "MP/Thompson/mp_thompson.F90"
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {n}: {old.strip()[:60]!r}")
    edits[path] = s.replace(old, new)


SOIL = "1000.d0*(0.1d0*smc(i,1)+0.3d0*smc(i,2)+0.6d0*smc(i,3)+1.0d0*smc(i,4))"
sub(drv, "      integer, public, save :: wbl_kdt = -1\n",
    "      integer, public, save :: wbl_kdt = -1\n"
    "      real(kind=8), public, save :: wbn(2,13) = 0.d0\n"
    "      real(kind=8), save :: wbn_ci, wbn_si, wbn_mi, wbn_ai\n"
    "      integer, save :: wbn_c\n")
sub(drv, "    if (wbl_kdt >= 0) write(*,'(a,i7,10es24.15)') 'WBL ', wbl_kdt, wbl\n",
    "    if (wbl_kdt >= 0) write(*,'(a,i7,10es24.15)') 'WBL ', wbl_kdt, wbl\n"
    "    if (wbl_kdt >= 0) write(*,'(a,i7,26es24.15)') 'WBN ', wbl_kdt, wbn\n")
sub(drv, "    if (flag_iter(i) .and. dry(i)) then\n",
    "    if (flag_iter(i) .and. dry(i)) then\n"
    "      wbn_ci = canliqxy(i) + canicexy(i)\n"
    "      wbn_si = weasd(i)\n"
    f"      wbn_mi = {SOIL}\n"
    "      wbn_ai = waxy(i)\n")
sub(drv, "      wbl_tp(i) = 1000.0d0*tprcp(i)/delt\n",
    "      wbl_tp(i) = 1000.0d0*tprcp(i)/delt\n"
    "      wbn_c = 1\n"
    "      if ( vegetation_category == isice_table ) wbn_c = 2\n"
    "      if (wbn_c == 1) then\n"
    "        wbn(1,1) = wbn(1,1) + wbn_ci\n"
    "        wbn(1,2) = wbn(1,2) + canliqxy(i) + canicexy(i)\n"
    "        wbn(1,7) = wbn(1,7) + wbn_ai\n"
    "        wbn(1,8) = wbn(1,8) + waxy(i)\n"
    "      endif\n"
    "      wbn(wbn_c,3) = wbn(wbn_c,3) + wbn_si\n"
    "      wbn(wbn_c,4) = wbn(wbn_c,4) + weasd(i)\n"
    "      wbn(wbn_c,5) = wbn(wbn_c,5) + wbn_mi\n"
    f"      wbn(wbn_c,6) = wbn(wbn_c,6) + {SOIL}\n"
    "      wbn(wbn_c,9) = wbn(wbn_c,9) + wbl_pr(i)*delt\n"
    "      wbn(wbn_c,10) = wbn(wbn_c,10) + wbl_et(i)\n"
    "      wbn(wbn_c,11) = wbn(wbn_c,11) + (runoff_surface + runoff_baseflow)*delt\n"
    "      wbn(wbn_c,12) = wbn(wbn_c,12) + wbl_ew(i)\n"
    "      wbn(wbn_c,13) = wbn(wbn_c,13) + 1.d0\n")
sub(mpt, "         use noahmpdrv, only: wbl, wbl_kdt\n", "         use noahmpdrv, only: wbl, wbl_kdt, wbn\n")
sub(mpt, "         write(*,'(a,i7,10es24.15)') 'WBL ', wbl_kdt, wbl\n",
    "         write(*,'(a,i7,10es24.15)') 'WBL ', wbl_kdt, wbl\n"
    "         write(*,'(a,i7,26es24.15)') 'WBN ', wbl_kdt, wbn\n")

for path, s in edits.items():
    path.with_suffix(path.suffix + ".preWBN").write_text(path.read_text())
    path.write_text(s)
    print(f"instrumented {path.relative_to(root)}")
