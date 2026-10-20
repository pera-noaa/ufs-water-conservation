#!/usr/bin/env python3
"""full14 edits (Ash's decisions, 18 Oct 2026). Usage: edits14.py <ufs-weather-model> <stage> [diff]
  REV <diff>  reverse a unified diff BY CONTENT (each run of -/+ lines: the + block, found exactly once, becomes the -
              block; pure insertions are deleted). Used for canopy 03 (TH9 behind thompson_sed_actual), whose context
              in full13 has moved (suites 03/04/06 next to its typedefs lines, meter lines next to its Thompson hunks).
  PL1         fold preclag PL1 into EP1: the sfc_precip_t1_carry switch goes; GFS_MP_generic_post, noahmpdrv and
              sfc_sice use their existing sfc_precip_enthalpy argument; the restart field is keyed on EP1.
  NM10R       ensfc2 12_sfc_NM10r on the series: Noah-MP soil takes the host's convective-phase decision always
              (PH2 without precip_phase_host); comments as in 12_sfc_NM10r. PH1 and PH3 stay under the switch.
  EM01        metered tree: preclag's lag meter probe reads EP1's flag (its sfc_precip_t1_carry argument's meta).
Every anchor must match the stated number of times, else nothing is written for that file."""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
stage = sys.argv[2]
U = root / "UFSATM/ccpp"
PH = U / "physics/physics"
EP1 = "flag_for_surface_precipitation_enthalpy"


def edit(path, fn):
    s = path.read_text()
    t = fn(s)
    if t != s:
        path.write_text(t)
        print(f"{stage}: {path.relative_to(root)}")


def sub(s, old, new, n=1):
    if s.count(old) != n:
        sys.exit(f"ABORT {stage}: anchor x{s.count(old)} (want {n}): {old.strip()[:80]!r}")
    return s.replace(old, new)


def del_meta_block(s, name):
    lines = s.split("\n")
    i = [k for k, l in enumerate(lines) if l.strip() == f"[{name}]"]
    if len(i) != 1:
        sys.exit(f"ABORT {stage}: meta block [{name}] x{len(i)}")
    j = i[0] + 1
    while j < len(lines) and not lines[j].startswith("[") and lines[j].strip() != "":
        j += 1
    return "\n".join(lines[:i[0]] + lines[j:])


if stage == "REV":
    d = Path(sys.argv[3]).read_text().split("\n")
    files, cur, runs = {}, None, None
    for l in d:
        if l.startswith("+++ "):
            p = l[4:].split("\t")[0]
            p = p.split("/", 1)[1]  # strip a/ or b/
            cur = files.setdefault(p, [])
            runs = None
        elif l.startswith("@@"):
            runs = {"-": [], "+": []}
            cur.append(runs)
        elif runs is not None and l[:1] in ("-", "+") and not l.startswith(("---", "+++")):
            if l[0] == "-" and runs["+"]:  # a new run starts after + lines
                runs = {"-": [], "+": []}
                cur.append(runs)
            runs[l[0]].append(l[1:])
        elif runs is not None and l[:1] == " " and (runs["-"] or runs["+"]):
            runs = {"-": [], "+": []}
            cur.append(runs)
    for p, rr in files.items():
        f = root / p

        def rev(s, rr=rr, p=p):
            for r in rr:
                if not r["+"]:
                    if r["-"]:
                        sys.exit(f"ABORT REV {p}: pure deletion run, needs an anchor")
                    continue
                new = "\n".join(r["+"]) + "\n"
                old = "\n".join(r["-"]) + "\n" if r["-"] else ""
                s = sub(s, new, old)
            return s
        edit(f, rev)

elif stage == "PL1":
    edit(U / "data/GFS_typedefs.F90",
         lambda s: "\n".join(l for l in s.split("\n") if "sfc_precip_t1_carry" not in l)
         if sum("sfc_precip_t1_carry" in l for l in s.split("\n")) == 5 else sys.exit("ABORT PL1 typedefs: want 5 lines"))
    edit(U / "data/GFS_typedefs.meta", lambda s: del_meta_block(s, "sfc_precip_t1_carry"))
    edit(U / "driver/GFS_restart.F90",
         lambda s: sub(s, "Model%sfc_precip_t1_carry", "Model%sfc_precip_enthalpy", 2))
    for f, argl, decl in (
            (PH / "Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.F90",
             "        sfc_precip_t1_carry, tprcp_t1)",
             "      logical, optional,                       intent(in)    :: sfc_precip_t1_carry\n"),
            (PH / "SFC_Models/Land/Noahmp/noahmpdrv.F90",
             "      sfc_precip_t1_carry, tprcp_t1                                               &",
             "  logical, optional, intent(in) :: sfc_precip_t1_carry\n"),
            (PH / "SFC_Models/SeaIce/CICE/sfc_sice.f",
             "     &       sfc_precip_t1_carry, tprcp_t1",
             "      logical, optional, intent(in) :: sfc_precip_t1_carry\n")):
        def fold(s, argl=argl, decl=decl):
            s = sub(s, argl + "\n", argl.replace("sfc_precip_t1_carry, ", "") + "\n")
            s = sub(s, decl, "")
            return s.replace("sfc_precip_t1_carry", "sfc_precip_enthalpy")
        edit(f, fold)
        edit(f.with_suffix(".meta"), lambda s: del_meta_block(s, "sfc_precip_t1_carry"))

elif stage == "NM10R":
    edit(PH / "SFC_Models/Land/Noahmp/noahmpdrv.F90", lambda s: sub(s,
         "        ! PH2: the host's convective decision (GFS_MP_generic_post: csnow = rainc when tsfc < 273.15)\n"
         "        fpcvh = -1.\n"
         "        if (pph .and. precip_convective > 0.) then\n",
         "        ! the host's convective decision (GFS_MP_generic_post: csnow = rainc when tsfc < 273.15), from srflag\n"
         "        fpcvh = -1.\n"
         "        if (precip_convective > 0.) then\n"))
    edit(PH / "SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90", lambda s: sub(s,
         "        ! the microphysics fraction is for grid-scale precipitation; convective precipitation is snow below freezing\n",
         "        ! the microphysics fraction is for grid-scale precipitation; convective precipitation takes the host's\n"
         "        ! decision (srflag), or is snow below freezing when the host gives none\n"))
    edit(U / "data/GFS_typedefs.F90", lambda s: sub(s,
         "!< flag: surfaces take the host convective snow decision and the atmosphere pays hfus for it",
         "!< flag: glaciers take the host convective snow decision and the atmosphere pays hfus for it"))

elif stage == "EM01":
    m = PH / "Interstitials/UFS_SCM_NEPTUNE/em_p01.meta"

    def em(s):
        i = s.index("[sfc_precip_t1_carry]")
        j = s.index("standard_name =", i)
        k = s.index("\n", j)
        return s[:j] + f"standard_name = {EP1}" + s[k:]
    edit(m, em)
else:
    sys.exit("stage: REV <diff> | PL1 | NM10R | EM01")
