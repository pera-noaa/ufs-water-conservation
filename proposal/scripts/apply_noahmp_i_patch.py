#!/usr/bin/env python3
"""Fix I: Noah-MP's canopy truncation in canwater (canliq or canice <= 1e-6 mm -> 0) sends the truncated water to the
ground with the rain and the truncated ice with the snowfall, instead of deleting it (v1 snapshot and ufs/dev layouts).
Usage: python3 apply_noahmp_i_patch.py <dir containing physics/SFC_Models>
Interception of a few 1e-7 mm per step fell under the threshold and was deleted: errwat -0.014 mm per 1.77M
column-steps in our C96 case. No phase change, so no latent heat is created or lost (the first version,
apply_noahmp_i_ecan_patch.py, evaporated it through ecan without the latent heat in fcev). canwater returns the
truncated amounts (qcanl, qcani, mm/s); water() adds them to qrain, qsnow, and snowhin at the fresh-snow density."""
import sys
from pathlib import Path

f90 = Path(sys.argv[1]) / "physics/SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
s = f90.read_text()


def one(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(old)}: {old.strip()[:60]!r}")
    return s.replace(old, new)


# canwater: two new outputs
s = one(s, "                       cmc    ,ecan   ,etran  , & !out\n                       fwet      )",
        "                       cmc    ,ecan   ,etran  ,qcanl  ,qcani  , & !out\n                       fwet      )")
FWET = "  real (kind=kind_phys), intent(out)   :: fwet    !< wetted or snowed fraction of the canopy (-)\n"
LOC = ("  real (kind=kind_phys)                :: maxliq  !canopy capacity for rain interception (mm)\n"
       "  real (kind=kind_phys)                :: qevac   !evaporation rate (mm/s)\n")
if s.count(LOC) != 1:
    sys.exit(f"ABORT: canwater locals anchor found {s.count(LOC)} times")
i = s.index(LOC)
j = s.rindex(FWET, 0, i)  # canwater's fwet: the last one before its locals
s = s[:j] + (FWET +
        "  real (kind=kind_phys), intent(out)   :: qcanl   !< truncated canopy water to the ground (mm/s)\n"
        "  real (kind=kind_phys), intent(out)   :: qcani   !< truncated canopy ice to the ground (mm/s)\n") + s[j + len(FWET):]
if i - j > 600:
    sys.exit("ABORT: canwater fwet declaration not next to its locals")
s = one(s, "! initialization\n\n      ecan    = 0.0\n",
        "! initialization\n\n      ecan    = 0.0\n      qcanl   = 0.0\n      qcani   = 0.0\n")
s = one(s, "       if(canliq <= 1.e-06) canliq = 0.0\n",
        "       if(canliq <= 1.e-06) then\n"
        "         ! the truncated canopy water drips to the ground\n"
        "         qcanl  = canliq/dt\n"
        "         canliq = 0.0\n"
        "       end if\n")
s = one(s, "      if(canice.le.1.e-6) canice = 0.\n",
        "      if(canice.le.1.e-6) then\n"
        "        ! the truncated canopy ice falls to the ground\n"
        "        qcani  = canice/dt\n"
        "        canice = 0.\n"
        "      end if\n")
# water(): receive them and pass them on with the rain and snowfall (qrain, qsnow, snowhin are intent(in) here)
s = one(s, "                  cmc    ,ecan   ,etran  , & !out\n                  fwet      )",
        "                  cmc    ,ecan   ,etran  ,qcanl  ,qcani  , & !out\n                  fwet      )")
s = one(s, "  real (kind=kind_phys)                                           :: qinsur  !water input on soil surface [m/s]\n",
        "  real (kind=kind_phys)                                           :: qinsur  !water input on soil surface [m/s]\n"
        "  real (kind=kind_phys)                                           :: qcanl, qcani !truncated canopy water, ice to the ground (mm/s)\n")
s = one(s, "          &          sfctmp ,snowhin,qsnow  ,qsnfro ,qsnsub , & !in\n"
           "          &          qrain  ,ficeold,iloc   ,jloc   ,         & !in\n",
        "          &          sfctmp ,snowhin+qcani/bdfall,qsnow+qcani,qsnfro ,qsnsub , & !in\n"
        "          &          qrain+qcanl,ficeold,iloc   ,jloc   ,         & !in\n")
s = one(s, "       qinsur = qinsur+(qsnbot + qsdew + qrain) * 0.001\n",
        "       qinsur = qinsur+(qsnbot + qsdew + qrain + qcanl) * 0.001\n")
f90.write_text(s)
print(f"patched {f90.name} (I: canopy truncations to the ground)")
