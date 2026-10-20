#!/usr/bin/env python3
"""Integrator merge for trdyn 03b / 01_DYN_v5 on all_full + energy round 4: re-anchor, verbatim, the hunks that clash only
with neighbouring energy edits (PBK/PBF declarations, D7/D7S namelist names, meter lines). Run after `patch -F0` left
.rej files. Usage: rebase_trdyn.py <ufs-weather-model>. Removes the .rej/.orig files it resolves."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM"
done = []


def fix(rel, old, new):
    p = root / rel
    rej = Path(str(p) + ".rej")
    if not rej.exists():
        return
    s = p.read_text()
    if new in s:
        return
    if s.count(old) != 1:
        sys.exit(f"ABORT {rel}: anchor found {s.count(old)} times: {old.strip()[:70]!r}")
    p.write_text(s.replace(old, new))
    done.append(rel)


fix("ccpp/physics/physics/PBL/SATMEDMF/satmedmfvdifq.F",
    "      integer i,is,k,n,ndt,km1,kmpbl,kmscu,ntrac1,idtend\n",
    "      integer i,is,k,n,ndt,km1,kmpbl,kmscu,ntrac1,idtend\n"
    "      logical, intent(in) :: trans_aero\n      integer, intent(in) :: ntchm\n      logical trdry(ntrac)\n"
    "      integer ndry, nd, is0\n"
    "      real(kind=kind_phys) q1c(im,km,ntrac), trwl(im,km),\n"
    "     &   tral(im,km), trad(im,km), trau(im,km), trf3(im,km*ntrac),\n"
    "     &   trwf, trdd, trdu\n")
fix("fv3/atmos_cubed_sphere/model/fv_control.F90",
    "range_warn, dwind_2d, inline_q, z_tracer, reproduce_sum,",
    "range_warn, dwind_2d, inline_q, z_tracer, dry_tracer_adv, dry_tracer_ic, reproduce_sum,")
fix("fv3/atmos_cubed_sphere/model/fv_dynamics.F90",
    "   use fv_tracer2d_mod,     only: tracer_2d, tracer_2d_1L, tracer_2d_nested\n",
    "   use fv_tracer2d_mod,     only: tracer_2d, tracer_2d_1L, tracer_2d_nested, dry_tracer_mask, dry_negadj\n")
p = root / "fv3/atmos_cubed_sphere/model/fv_dynamics.F90"
if Path(str(p) + ".rej").exists():
    s = p.read_text()
    old = "                     flagstruct%moist_phys, grav_var)\n"
    new = "                     flagstruct%moist_phys, grav_var, flagstruct%dry_tr(1:nr))\n"
    if new not in s:
        if s.count(old) != 1:
            sys.exit("ABORT fv_dynamics L2E call anchor")
        p.write_text(s.replace(old, new))
        done.append("fv_dynamics L2E")
for rel in ("ccpp/physics/physics/PBL/SATMEDMF/satmedmfvdifq.F", "fv3/atmos_cubed_sphere/model/fv_control.F90",
            "fv3/atmos_cubed_sphere/model/fv_dynamics.F90"):
    for ext in (".rej", ".orig"):
        q = Path(str(root / rel) + ext)
        if q.exists():
            q.unlink()
left = [str(q) for q in root.rglob("*.rej")]
print("re-anchored:", ", ".join(done) or "none", "| rejects left:", left or "none")
sys.exit(1 if left else 0)
