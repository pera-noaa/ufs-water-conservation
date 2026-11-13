#!/usr/bin/env python3
"""Land meter for full14 (diagnostic builds only; one OpenMP thread). Apply after instrument_eb_phys2.py (and preclag's
meter_PL1_lag_v2.diff). Usage: instrument_land14.py <ufs-weather-model>
Noah-MP soil columns, summed per step over columns (unweighted), printed by em_p12 as
  'EMLAND kdt v(8)': 1 columns with precipitation | 2 sum |frozen received - host frozen| (mm/s) | 3 sum host frozen
  srflag*P (mm/s) | 4 columns where they differ by > 1e-9 P | 5 columns with convective precipitation | 6 sum errwat
  (Noah-MP's own water balance, mm/step) | 7 sum |errwat| | 8 soil columns.
Frozen received = prcp*fpice at the end of atm() (what Noah-MP splits into snow); host frozen = srflag*precipitation_
forcing (the host's phase decision, GFS_MP_generic_post). Every anchor must match exactly once."""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
I = root / "Interstitials/UFS_SCM_NEPTUNE"
N = root / "SFC_Models/Land/Noahmp"


def sub(p, old, new):
    s = p.read_text()
    if s.count(old) != 1:
        sys.exit(f"ABORT {p.name}: anchor x{s.count(old)}: {old.strip()[:70]!r}")
    p.write_text(s.replace(old, new))


c = I / "energy_meter_common.F90"
sub(c, "  public :: em_probe, ", "  public :: emland, emlhost\n  public :: em_probe, ")
sub(c, "  real(kind=8), save :: emlp(emnc)",
    "  real(kind=8), save :: emland(8) = 0.d0, emlhost = -1.d0   ! land meter (instrument_land14.py)\n"
    "  real(kind=8), save :: emlp(emnc)")

m = N / "module_sf_noahmplsm.F90"
s = m.read_text()
i = s.index("module module_sf_noahmplsm")
mu = re.compile(r"^\s*use machine[^\n]*\n", re.M).search(s, i)
s = s[:mu.end()] + "  use energy_meter_common, only: emland, emlhost\n" + s[mu.end():]
m.write_text(s)
sub(m, "     snow   = prcp * fpice\n",
    "     snow   = prcp * fpice\n"
    "     if (prcp > 0. .and. emlhost >= 0.d0) then   ! land meter\n"
    "        emland(1) = emland(1) + 1.d0\n"
    "        emland(2) = emland(2) + abs(prcp*fpice - emlhost)\n"
    "        emland(3) = emland(3) + emlhost\n"
    "        if (abs(prcp*fpice - emlhost) > 1.d-9*prcp) emland(4) = emland(4) + 1.d0\n"
    "        if (prcpconv + prcpshcv > 0.) emland(5) = emland(5) + 1.d0\n"
    "     endif\n")
sub(m, "        errwat = end_wb-beg_wb-(prcp-ecan-etran-edir-runsrf-runsub)*dt\n",
    "        errwat = end_wb-beg_wb-(prcp-ecan-etran-edir-runsrf-runsub)*dt\n"
    "        emland(6) = emland(6) + errwat   ! land meter\n"
    "        emland(7) = emland(7) + abs(errwat)\n"
    "        emland(8) = emland(8) + 1.d0\n")

d = N / "noahmpdrv.F90"
s = d.read_text()
i = s.index("subroutine noahmpdrv_run")
mu = re.compile(r"^\s*use machine[^\n]*\n", re.M).search(s, i)
s = s[:mu.end()] + "      use energy_meter_common, only: emlhost\n" + s[mu.end():]
d.write_text(s)
sub(d, "        call noahmp_sflx (parameters ",
    "        emlhost = srflag(i)*precipitation_forcing   ! land meter\n        call noahmp_sflx (parameters ")
sub(N / "noahmpdrv.meta", "  dependencies = module_sf_noahmp_glacier.F90,module_sf_noahmplsm.F90,noahmp_tables.f90\n",
    "  dependencies = module_sf_noahmp_glacier.F90,module_sf_noahmplsm.F90,noahmp_tables.f90,"
    "../../../Interstitials/UFS_SCM_NEPTUNE/energy_meter_common.F90\n")

p12 = I / "em_p12.F90"
sub(p12, "          write(*,'(a,i6,8es25.16)') 'EML ', emkdt(12), lbuf\n",
    "          write(*,'(a,i6,8es25.16)') 'EML ', emkdt(12), lbuf\n"
    "          lbuf = emland\n"
    "          call MPI_Reduce(MPI_IN_PLACE, lbuf, 8, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "          write(*,'(a,i6,8es25.16)') 'EMLAND ', emkdt(12), lbuf\n")
sub(p12, "          call MPI_Reduce(lbuf, lrbuf, 8, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n",
    "          call MPI_Reduce(lbuf, lrbuf, 8, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "          lbuf = emland\n"
    "          call MPI_Reduce(lbuf, lrbuf, 8, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n")
sub(p12, "       eml = 0.d0\n", "       eml = 0.d0\n       emland = 0.d0\n")
print("land meter: energy_meter_common, module_sf_noahmplsm (atm, error), noahmpdrv (+meta), em_p12")
