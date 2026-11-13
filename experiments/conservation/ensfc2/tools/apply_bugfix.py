#!/usr/bin/env python3
"""Round-3 surface energy BUG FIXES, unconditional, by anchor substitution (works with or without meters).
Usage: apply_bugfix.py <ufs-weather-model> TAG [TAG ...]
  QR1  sfc_nst: rain is lwe m per step (tprcp_wat); qrain and sep need kg m-2 s-1
  CMC  Noah-MP canwater: heat the canopy books but cannot carry (evaporation/sublimation cap, frozen-canopy
       transpiration charged at hsub but taken from soil liquid, canopy melt/freeze latent heat) returns to the
       top soil layer through the NM11 lheat path
  FL1  sfc_sice ice3lay: flooded snow (heat content -li) joins both ice layers' heat content (snow-ice formation)
Every anchor must match exactly once; nothing is written unless all match."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics"
tags = sys.argv[2:]
lsm = root / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90"
ice = root / "SFC_Models/SeaIce/CICE/sfc_sice.f"
nst = root / "SFC_Layer/UFS/sfc_nst.f90"
edits = {}


def sub(path, old, new, after=None):
    s = edits.get(path) or path.read_text()
    if after is not None:
        if s.count(after) != 1:
            sys.exit(f"ABORT {path.name}: anchor count {s.count(after)}: {after.strip()[:70]!r}")
        i = s.index(after)
        j = s.find(old, i)
        if j < 0:
            sys.exit(f"ABORT {path.name}: {old.strip()[:70]!r} not after anchor")
        edits[path] = s[:j] + new + s[j + len(old):]
        return
    if s.count(old) != 1:
        sys.exit(f"ABORT {path.name}: expected 1 match, found {s.count(old)}: {old.strip()[:70]!r}")
    edits[path] = s.replace(old, new)


if "QR1" in tags:
    sub(nst, "          tem      = (1.0e3_kp * rain(i) / rho_w) * alfac * cp_w\n",
        "          tem      = (1.0e3_kp * (1.0e3_kp*rain(i)/timestep) / rho_w) * alfac * cp_w  ! rain is m per step\n")
    sub(nst, "          sep      = sss*(evap(i)/le-rain(i))/rho_w\n",
        "          sep      = sss*(evap(i)/le-1.0e3_kp*rain(i)/timestep)/rho_w\n")

if "CMC" in tags:
    CW = "  subroutine canwater (parameters,vegtyp ,dt     , & !in\n"
    sub(lsm, "                       fwet      )                           !out\n",
        "                       fwet   ,lheatc )                       !out\n", after=CW)
    sub(lsm, "  real (kind=kind_phys), intent(out)   :: qcani   !< truncated canopy ice to the ground (mm/s)\n",
        "  real (kind=kind_phys), intent(out)   :: qcani   !< truncated canopy ice to the ground (mm/s)\n"
        "  real (kind=kind_phys), intent(out)   :: lheatc  !< heat charged to the canopy that it cannot carry [j/m2]\n")
    sub(lsm, "      ecan    = 0.0\n      qcanl   = 0.0\n      qcani   = 0.0\n",
        "      ecan    = 0.0\n      qcanl   = 0.0\n      qcani   = 0.0\n      lheatc  = 0.0\n")
    sub(lsm, "       qevac = min(canliq/dt,qevac)\n",
        "       ! evaporation the canopy water cannot supply was charged in the energy step: its heat returns\n"
        "       lheatc = (qevac - min(canliq/dt,qevac))*hvap*dt\n"
        "       qevac = min(canliq/dt,qevac)\n")
    sub(lsm, "      qsubc = min(canice/dt,qsubc) \n",
        "      lheatc = lheatc + (qsubc - min(canice/dt,qsubc))*hsub*dt\n"
        "      qsubc = min(canice/dt,qsubc) \n")
    sub(lsm, "      ecan = qevac + qsubc - qdewc - qfroc\n",
        "      ecan = qevac + qsubc - qdewc - qfroc\n"
        "\n! frozen canopy: transpiration was charged hsub but is soil liquid; canopy melt/freeze latent heat\n"
        "      if (frozen_canopy) lheatc = lheatc + (hsub - hvap)*etran*dt\n"
        "      lheatc = lheatc - hfus*(qmeltc - qfrzc)*dt\n")
    sub(lsm, "  real (kind=kind_phys)                                           :: lheat   !latent heat charged minus latent heat used by the ground vapour [j/m2]\n",
        "  real (kind=kind_phys)                                           :: lheat   !latent heat charged minus latent heat used by the ground vapour [j/m2]\n"
        "  real (kind=kind_phys)                                           :: lheatc  !heat charged to the canopy that it cannot carry [j/m2]\n")
    sub(lsm, "                  fwet      )                           !out\n",
        "                  fwet   ,lheatc )                       !out\n",
        after="   call canwater (parameters,vegtyp ,dt     , & !in\n")
    sub(lsm, "   lheat = (latheag - hsub)*(qsnsub - qsnfro)*dt\n",
        "   lheat = (latheag - hsub)*(qsnsub - qsnfro)*dt + lheatc\n")

if "FL1" in tags:
    sub(ice, "     &,                        c1, ip, k12, k32, tsf, f1, tmelt, bmelt\n",
        "     &,                        c1, ip, k12, k32, tsf, f1, tmelt, bmelt\n"
        "      real (kind=kind_phys) :: hold, efl, bfl\n")
    sub(ice, "            hsni     = (hdi - hice(i)) * dsdi\n            hice (i) = hice(i) + hsni\n",
        "            hsni     = (hdi - hice(i)) * dsdi\n"
        "            hold     = hice(i)\n"
        "            hice (i) = hice(i) + hsni\n"
        "!           flooded snow (heat content -li) joins both layers\n"
        "            efl = min(stsice(i,2)-t0c, tfi0)\n"
        "            efl = (hold*(ci*(efl-tfi)-li) - hsni*li) / hice(i)\n"
        "            stsice(i,2) = tfi + (efl+li)/ci + t0c\n"
        "            bfl = min(stsice(i,1)-t0c, tfi0)\n"
        "            efl = (hold*(ci*(bfl-tfi)-li*(one-tfi/bfl)) - hsni*li)\n"
        "     &          / hice(i)\n"
        "            bfl = efl + ci*tfi + li\n"
        "            stsice(i,1) = (bfl - sqrt(bfl*bfl\n"
        "     &                  - 4.0_kind_phys*ci*li*tfi))\n"
        "     &                  / (ci+ci) + t0c\n")

for p, s in edits.items():
    p.write_text(s)
    print("fixed", p.name)
