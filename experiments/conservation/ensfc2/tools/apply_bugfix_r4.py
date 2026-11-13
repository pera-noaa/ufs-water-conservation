#!/usr/bin/env python3
"""Round-4 surface energy BUG FIXES (Noah-MP soil and glacier copies), by anchor substitution.
Apply after NM12 (water diff 20). Usage: apply_bugfix_r4.py <ufs-weather-model> TAG [TAG ...]
  SL2  snow layers keep their heat when they are combined or removed:
       - combine: a thin layer (snice <= 0.1 mm) merged by mass into a neighbour mixes its sensible heat into it
         (the code added the mass at the neighbour's temperature);
       - combine: snow that stops being layered (single-layer melt-out, total depth < 0.025 m) has no temperature as
         bulk snow; its layers' sensible heat goes to the top soil (glacier: top ice) layer;
       - combine (soil): over-sublimated snow taken from soil ice leaves at tfrz (soil keeps its heat);
       - snowh2o (soil): truncated bulk snow joins the top soil layer as ice at tfrz.
  CS1  csnow/csnow_glacier: the snow heat capacity capped the ice and liquid volume fractions (liquid beyond the
       pore space and ice beyond solid density had no heat capacity), so mass moving in or out of the caps changed
       the layer's heat; per-mass capacities cice/denice*snice + cwat/denh2o*snliq (the fractions stay capped for
       the conductivity).
  CB1  combo/combo_glacier: the enthalpy used cice, cwat (J m-3 K-1) as per-kg capacities and its branches
       set T = tfrz (or dropped hfus*wliq) without changing phase; per-kg capacities and one formula
       T = tfrz + (h - hfus*wliq)/C, phasechange settles the phases.
Every anchor must match exactly once (per file); nothing is written unless all match."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/SFC_Models/Land/Noahmp"
tags = sys.argv[2:]
lsm = root / "module_sf_noahmplsm.F90"
gla = root / "module_sf_noahmp_glacier.F90"
edits = {}


def get(p):
    return edits.get(p) or p.read_text()


def sub(path, old, new, after=None, before=None):
    s = get(path)
    lo, hi = 0, len(s)
    if after is not None:
        if s.count(after) != 1:
            sys.exit(f"ABORT {path.name}: anchor count {s.count(after)}: {after.strip()[:60]!r}")
        lo = s.index(after)
    if before is not None:
        hi = s.index(before, lo)
    seg = s[lo:hi]
    if seg.count(old) != 1:
        sys.exit(f"ABORT {path.name}: {seg.count(old)} matches: {old.strip()[:70]!r}")
    edits[path] = s[:lo] + seg.replace(old, new) + s[hi:]


def pre(p, a, t, **kw):
    sub(p, a, t + a, **kw)


def post(p, a, t, **kw):
    sub(p, a, a + t, **kw)


HCAP = ("  real (kind=kind_phys) function {n}(wice, wliq, dz)\n"
        "    ! sl2: sensible heat capacity of a snow layer (j/m2/k), per mass as csnow uses it (cs1)\n"
        "    real (kind=kind_phys), intent(in) :: wice, wliq, dz\n"
        "    {n} = 0.\n"
        "    if (dz > 0.) {n} = cice/denice*max(0.,wice) + cwat/denh2o*max(0.,wliq)\n"
        "  end function {n}\n\n")
SOILCAP = ("  real (kind=kind_phys) function soil_hcap1(parameters, sh2o1, sice1, dz)\n"
           "    ! sl2: heat capacity of the top soil layer (j/m2/k), as thermoprop\n"
           "    type (noahmp_parameters), intent(in) :: parameters\n"
           "    real (kind=kind_phys), intent(in) :: sh2o1, sice1, dz\n"
           "    soil_hcap1 = dz*(sh2o1*cwat + (1.0-parameters%smcmax(1))*parameters%csoil &\n"
           "               + (parameters%smcmax(1)-sh2o1-sice1)*cpair + sice1*cice)\n"
           "  end function soil_hcap1\n\n")

if "SL2" in tags:
    for path, cname, hc, gcap in [
            (lsm, "  subroutine combine (parameters,nsnow  ,nsoil  ,iloc   ,jloc   ,         & !in\n", "snow_hcap",
             "soil_hcap1(parameters, sh2o(1), sice(1), dzsnso(1))"),
            (gla, "  subroutine combine_glacier (nsnow    ,nsoil  ,                         & !in\n", "snow_hcap_glacier",
             "1.e6*(0.8194 + 0.1309*0.5*dzsnso(1))*dzsnso(1)")]:
        endc = "  end subroutine combine"
        pre(path, cname, HCAP.format(n=hc) + (SOILCAP if path == lsm else ""))
        decl = ("    real (kind=kind_phys)    :: zwliq                 ! total liquid water in snow\n" if path == lsm else
                "    real (kind=kind_phys)    :: zwliq                 !< total liquid water in snow\n")
        post(path, decl, "    real (kind=kind_phys)    :: hsn, hgnd, hc1        ! sl2: snow heat merged / to the ground\n",
             after=cname, before=endc)
        pre(path, "       do j = isnow_old+1,0\n", "       hgnd = 0.\n", after=cname, before=endc)
        for a, b in (("j+1", "j"), ("j-1", "j")):
            blk = (f"                snliq({a}) = snliq({a}) + snliq(j)\n"
                   f"                snice({a}) = snice({a}) + snice(j)\n"
                   f"                dzsnso({a}) = dzsnso({a}) + dzsnso(j)\n")
            sub(path, blk,
                f"                hsn = {hc}(snice(j),snliq(j),dzsnso(j))*(stc(j)-tfrz) &\n"
                f"                    + {hc}(snice({a}),snliq({a}),dzsnso({a}))*(stc({a})-tfrz)\n" + blk +
                f"                hc1 = {hc}(snice({a}),snliq({a}),dzsnso({a}))\n"
                f"                if (hc1 > 0.) stc({a}) = tfrz + hsn/hc1\n", after=cname, before=endc)
        pre(path, "                 snliq(j) = 0.0\n                 snice(j) = 0.0\n                 dzsnso(j) = 0.0\n",
            f"                 hgnd = hgnd + {hc}(snice(j),snliq(j),dzsnso(j))*(stc(j)-tfrz)\n", after=cname, before=endc)
        if path == lsm:
            sub(path, "                   sice(1) = max(0.0,sice(1)+ponding1/(dzsnso(1)*1000.))\n",
                "                   hc1 = soil_hcap1(parameters, sh2o(1), sice(1), dzsnso(1))\n"
                "                   sice(1) = max(0.0,sice(1)+ponding1/(dzsnso(1)*1000.))\n"
                "                   stc(1) = tfrz + hc1*(stc(1)-tfrz)/soil_hcap1(parameters, sh2o(1), sice(1), dzsnso(1))\n",
                after=cname, before=endc)
        pre(path, "          isnow  = 0\n          sneqv = zwice\n",
            "          do i = isnow+1, 0\n"
            f"             hgnd = hgnd + {hc}(snice(i),snliq(i),dzsnso(i))*(stc(i)-tfrz)\n"
            "          enddo\n", after=cname, before=endc)
        apply = (f"       if (hgnd /= 0.) then   ! sl2: heat of snow that is no longer layered\n"
                 f"          stc(1) = stc(1) + hgnd/({gcap})\n"
                 "          hgnd = 0.\n"
                 "       endif\n")
        pre(path, "       if(isnow ==0) return   ! mb: get out if no longer multi-layer\n", apply, after=cname, before=endc)
        s = get(path)
        k = s.index(cname)
        j = s.index(endc, k)
        edits[path] = s[:j] + apply + s[j:]
    SH = "  subroutine snowh2o (parameters,nsnow  ,nsoil  ,dt     ,qsnfro ,qsnsub , & !in \n"
    sub(lsm, "     if(isnow == 0) sice(1) = sice(1) + sneqv/(dzsnso(1)*1000.)\n",
        "     if(isnow == 0) then\n"
        "        hc1 = soil_hcap1(parameters, sh2o(1), sice(1), dzsnso(1))\n"
        "        sice(1) = sice(1) + sneqv/(dzsnso(1)*1000.)\n"
        "        stc(1) = tfrz + hc1*(stc(1)-tfrz)/soil_hcap1(parameters, sh2o(1), sice(1), dzsnso(1))  ! sl2: joins at tfrz\n"
        "     endif\n", after=SH, before="  end subroutine snowh2o")
    post(lsm, "   real (kind=kind_phys) :: ponding1, ponding2\n", "   real (kind=kind_phys) :: hc1\n", after=SH,
         before="  end subroutine snowh2o")

if "CS1" in tags:
    for path in (lsm, gla):
        sub(path, "      cvsno(iz) = cice*snicev(iz)+cwat*snliqv(iz)\n",
            "      ! cs1: heat capacity per mass (the volume fractions are capped for porosity and conductivity)\n"
            "      cvsno(iz) = (cice/denice*snice(iz) + cwat/denh2o*snliq(iz))/dzsnso(iz)\n")

if "CB1" in tags:
    o1 = ("    h = (cice*wice+cwat*wliq) * (t-tfrz)+hfus*wliq\n"
          "    h2= (cice*wice2+cwat*wliq2) * (t2-tfrz)+hfus*wliq2\n")
    n1 = ("    ! cb1: per-kg heat capacities (cice, cwat are per m3); phases kept, phasechange settles them\n"
          "    h = (cice/denice*wice+cwat/denh2o*wliq) * (t-tfrz)+hfus*wliq\n"
          "    h2= (cice/denice*wice2+cwat/denh2o*wliq2) * (t2-tfrz)+hfus*wliq2\n")
    o2 = ("    if(hc < 0.)then\n"
          "       tc = tfrz + hc/(cice*wicec + cwat*wliqc)\n"
          "    else if (hc.le.hfus*wliqc) then\n"
          "       tc = tfrz\n"
          "    else\n"
          "       tc = tfrz + (hc - hfus*wliqc) / (cice*wicec + cwat*wliqc)\n"
          "    end if\n")
    n2 = "    tc = tfrz + (hc - hfus*wliqc) / (cice/denice*wicec + cwat/denh2o*wliqc)\n"
    for path in (lsm, gla):
        sub(path, o1, n1)
        sub(path, o2, n2)

for p, s in edits.items():
    p.write_text(s)
    print("fixed", p.name)
