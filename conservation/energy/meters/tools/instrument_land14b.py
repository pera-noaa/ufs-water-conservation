#!/usr/bin/env python3
"""Diagnostic extension of the land meter (apply on a tree that has instrument_land14.py). Usage: instrument_land14b.py <ufs-weather-model>
Adds, per step, 'EMLAND2 kdt v(6)': 1 columns |frozen received - host frozen| > 1e-6 P | 2 the same > 1e-3 P |
3 sum |Noah-MP prcp - host P| (mm/s) | 4 sum host P (mm/s) | 5 columns |prcp - P| > 1e-9 P | 6 max |frozen diff|/P (MPI_MAX).
P = precipitation_forcing (1000 tprcp/delt), prcp = what atm() splits."""
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
sub(c, "  public :: emland, emlhost\n", "  public :: emland, emlhost, emland2, emlptot\n")
sub(c, "  real(kind=8), save :: emland(8) = 0.d0, emlhost = -1.d0",
    "  real(kind=8), save :: emland2(6) = 0.d0, emlptot = -1.d0\n  real(kind=8), save :: emland(8) = 0.d0, emlhost = -1.d0")
m = N / "module_sf_noahmplsm.F90"
sub(m, "  use energy_meter_common, only: emland, emlhost\n", "  use energy_meter_common, only: emland, emlhost, emland2, emlptot\n")
sub(m, "        if (prcpconv + prcpshcv > 0.) emland(5) = emland(5) + 1.d0\n",
    "        if (prcpconv + prcpshcv > 0.) emland(5) = emland(5) + 1.d0\n"
    "        if (abs(prcp*fpice - emlhost) > 1.d-6*prcp) emland2(1) = emland2(1) + 1.d0\n"
    "        if (abs(prcp*fpice - emlhost) > 1.d-3*prcp) emland2(2) = emland2(2) + 1.d0\n"
    "        emland2(3) = emland2(3) + abs(prcp - emlptot)\n"
    "        emland2(4) = emland2(4) + emlptot\n"
    "        if (abs(prcp - emlptot) > 1.d-9*prcp) emland2(5) = emland2(5) + 1.d0\n"
    "        emland2(6) = max(emland2(6), abs(prcp*fpice - emlhost)/prcp)\n")
d = N / "noahmpdrv.F90"
sub(d, "      use energy_meter_common, only: emlhost\n", "      use energy_meter_common, only: emlhost, emlptot\n")
sub(d, "        emlhost = srflag(i)*precipitation_forcing   ! land meter\n",
    "        emlhost = srflag(i)*precipitation_forcing   ! land meter\n        emlptot = precipitation_forcing\n")
p12 = I / "em_p12.F90"
sub(p12, "          write(*,'(a,i6,8es25.16)') 'EMLAND ', emkdt(12), lbuf\n",
    "          write(*,'(a,i6,8es25.16)') 'EMLAND ', emkdt(12), lbuf\n"
    "          lbuf(1:6) = emland2\n"
    "          call MPI_Reduce(MPI_IN_PLACE, lbuf, 5, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
    "          call MPI_Reduce(MPI_IN_PLACE, lbuf(6), 1, MPI_DOUBLE_PRECISION, MPI_MAX, mpiroot, mpicomm, ierr)\n"
    "          write(*,'(a,i6,6es25.16)') 'EMLAND2 ', emkdt(12), lbuf(1:6)\n")
s = p12.read_text()
old = ("          lbuf = emland\n"
       "          call MPI_Reduce(lbuf, lrbuf, 8, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n")
if s.count(old) != 1:
    sys.exit("ABORT em_p12 non-root anchor")
s = s.replace(old, old + "          lbuf(1:6) = emland2\n"
              "          call MPI_Reduce(lbuf, lrbuf, 5, MPI_DOUBLE_PRECISION, MPI_SUM, mpiroot, mpicomm, ierr)\n"
              "          call MPI_Reduce(lbuf(6), lrbuf(6), 1, MPI_DOUBLE_PRECISION, MPI_MAX, mpiroot, mpicomm, ierr)\n")
p12.write_text(s)
sub(p12, "       emland = 0.d0\n", "       emland = 0.d0\n       emland2 = 0.d0\n")
print("land meter b: EMLAND2")
