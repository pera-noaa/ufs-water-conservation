#!/usr/bin/env python3
"""Integrator merge for full11/mq11: re-anchor, verbatim, hunks that clash only with neighbouring lines. One stage per
patch, run right after it (patch overwrites .rej files, so stages must not share a run):
  13  ensfc2 13_sfc_SL2 hunk 8 (cut on fx; ensfc2 11's `svn, hcpo, hcpn` declaration sits in the same block)
  E2  canopy 01_E2 hunks next to ensfc2 16's new lines (both cut on full10): namelist, Model% copy, print,
      noahmpdrv argument list / options call / meta tail, module_sf_noahmplsm option declarations
  TH9 canopy 03_TH9 hunks 1-2 in the metered tree (Thompson energy-meter lines sit next to them)
  DTE fv3tally 01_fv3-dyn_te_exact v2, fv_dynamics hunks 1-2 in the metered tree (the dycore meter's eb_state probe
      follows the Rayleigh call; it stays right after the call, the new pkz block follows it). Text taken from the diff.
  REJ generic, for switch-only hunks (suites 03/04/06 in GFS_typedefs.F90 next to canopy TH9's lines): each hunk of
      the file's .rej is applied verbatim: one '-' and one '+' line = exact replacement; '+' lines only = inserted after
      the unique context line that precedes them. Anything else aborts.
Usage: rebase_r11.py <ufs-weather-model> <stage> [diff for DTE | file for REJ]. Exits 1 if any .rej is left."""
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "UFSATM"
stage = sys.argv[2]
done = []
NM = "ccpp/physics/physics/SFC_Models/Land/Noahmp/"
NOAH, DRV, META = NM + "module_sf_noahmplsm.F90", NM + "noahmpdrv.F90", NM + "noahmpdrv.meta"
THOM = "ccpp/physics/physics/MP/Thompson/module_mp_thompson.F90"
TYPE = "ccpp/data/GFS_typedefs.F90"


def fix(rel, old, new, append=False):
    p = root / rel
    if not Path(str(p) + ".rej").exists():
        return
    s = p.read_text()
    if new in s:
        return
    if append:
        if not s.endswith(old):
            sys.exit(f"ABORT {rel}: tail anchor")
        p.write_text(s + new)
    else:
        if s.count(old) != 1:
            sys.exit(f"ABORT {rel}: anchor found {s.count(old)} times: {old.strip()[:70]!r}")
        p.write_text(s.replace(old, new))
    done.append(rel.split("/")[-1])


rels = []
if stage == "13":
    rels = [NOAH]
    fix(NOAH,
        "   real (kind=kind_phys) :: svn, hcpo, hcpn\n   real (kind=kind_phys) :: ponding1, ponding2\n"
        "   real (kind=kind_phys), parameter :: max_liq_mass_fraction = 0.4\n",
        "   real (kind=kind_phys) :: svn, hcpo, hcpn\n   real (kind=kind_phys) :: ponding1, ponding2\n"
        "   real (kind=kind_phys) :: hc1\n"
        "   real (kind=kind_phys), parameter :: max_liq_mass_fraction = 0.4\n")
elif stage == "E2":
    rels = [TYPE, DRV, META, NOAH]
    fix(TYPE,
        "                               noahmp_kirchhoff,                                            &\n"
        "                               sfc_precip_enthalpy, lw_sfc_return, noahmp_pore_air,         &\n",
        "                               noahmp_kirchhoff, noahmp_fwet_opt,                           &\n"
        "                               sfc_precip_enthalpy, lw_sfc_return, noahmp_pore_air,         &\n")
    fix(TYPE, "    Model%noahmp_kirchhoff = noahmp_kirchhoff\n",
        "    Model%noahmp_kirchhoff = noahmp_kirchhoff\n    Model%noahmp_fwet_opt = noahmp_fwet_opt\n")
    fix(TYPE, "        print *, ' noahmp_kirchhoff : ', Model%noahmp_kirchhoff\n",
        "        print *, ' noahmp_kirchhoff : ', Model%noahmp_kirchhoff\n"
        "        print *, ' noahmp_fwet_opt : ', Model%noahmp_fwet_opt\n")
    fix(DRV, "      hflx_evap_enth, con_cliq, con_cvap, con_t0c,                               &\n",
        "      hflx_evap_enth, con_cliq, con_cvap, con_t0c, noahmp_fwet_opt,              &\n")
    fix(DRV, "  call noahmp_options_energy(opt_cnh_d, kir_d, adv_d, con_cliq, con_cvap, con_t0c)\n",
        "  call noahmp_options_energy(opt_cnh_d, kir_d, adv_d, con_cliq, con_cvap, con_t0c)\n"
        "  if (present(noahmp_fwet_opt)) then\n    call noahmp_options_fwet(noahmp_fwet_opt)\n  else\n"
        "    call noahmp_options_fwet(0)\n  endif\n")
    fix(META, "  intent = in\n  optional = True\n",
        "[noahmp_fwet_opt]\n  standard_name = control_for_noahmp_canopy_wetted_fraction\n"
        "  long_name = Noah-MP canopy wetted fraction rule\n  units = index\n  dimensions = ()\n  type = integer\n"
        "  intent = in\n  optional = True\n", append=True)
    fix(NOAH,
        "  logical, save :: opt_adv = .false.  ! soil water moved between layers carries its sensible heat\n"
        "  real (kind=kind_phys), save :: cl_f = 4185.5, cpv_f = 1846.0, t0_f = 273.15  ! frame F constants\n"
        "  public  :: noahmp_options_energy\n",
        "  logical, save :: opt_adv = .false.  ! soil water moved between layers carries its sensible heat\n"
        "  integer, save :: opt_fwt = 0        ! canopy wetted fraction rule (noahmp_options_fwet)\n"
        "  real (kind=kind_phys), save :: cl_f = 4185.5, cpv_f = 1846.0, t0_f = 273.15  ! frame F constants\n"
        "  public  :: noahmp_options_energy\n  public  :: noahmp_options_fwet\n")
elif stage == "TH9":
    rels = [THOM]
    fix(THOM, "   logical                      :: thompson_kirchhoff = .false.\n",
        "   logical                      :: thompson_kirchhoff = .false.\n"
        "!..thompson_sed_actual: floored layers sediment their actual mass, not the R1 placeholder\n"
        "   logical                      :: thompson_sed_actual = .false.\n")
    fix(THOM, "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon\n",
        "      real(wp) :: dtsave, odts, odt, odzq, hgt_agl, SR, rhon, sfloor\n")
elif stage == "DTE":
    FVD = "fv3/atmos_cubed_sphere/model/fv_dynamics.F90"
    rels = [FVD]
    if Path(str(root / FVD) + ".rej").exists():
        d = Path(sys.argv[3]).read_text().split("\n")
        i0 = next(i for i, l in enumerate(d) if l.startswith("+++ ") and "fv_dynamics.F90" in l)
        hunks, cur = [], None
        for l in d[i0 + 1:]:
            if l.startswith("diff ") or l.startswith("--- "):
                break
            if l.startswith("@@"):
                cur = []
                hunks.append(cur)
            elif cur is not None:
                cur.append(l)
        for h in hunks[:2]:
            minus = [l[1:] for l in h if l.startswith("-")]
            plus = [l[1:] for l in h if l.startswith("+")]
            assert len(minus) == 1, minus
            p_ = root / FVD
            t = p_.read_text().split("\n")
            idx = [i for i, l in enumerate(t) if l == minus[0]]
            if len(idx) != 1:
                sys.exit(f"ABORT DTE anchor x{len(idx)}: {minus[0].strip()[:60]}")
            i = idx[0]
            if len(plus) == 2:                 # hunk 2: argument added
                t[i:i + 1] = plus
            else:                              # hunk 1: call tail (2 lines), meter probe stays, then the pkz block
                assert "eb_state" in t[i + 1], t[i + 1]
                t[i:i + 2] = plus[:2] + [t[i + 1]] + plus[2:]
            p_.write_text("\n".join(t))
            done.append(f"fv_dynamics hunk ({len(plus)} lines)")
elif stage == "REJ":
    rel = sys.argv[3]
    rels = [rel]
    q = Path(str(root / rel) + ".rej")
    if q.exists():
        hunks, cur = [], None
        for l in q.read_text().split("\n"):
            if l.startswith("@@"):
                cur = []
                hunks.append(cur)
            elif cur is not None and l[:1] in ("-", "+", " ") and not l.startswith(("---", "+++")):
                cur.append(l)
        p_ = root / rel
        t = p_.read_text().split("\n")
        for h in hunks:
            minus = [l[1:] for l in h if l.startswith("-")]
            plus = [l[1:] for l in h if l.startswith("+")]
            if len(minus) == 1 and len(plus) == 1:
                idx = [i for i, l in enumerate(t) if l == minus[0]]
                if len(idx) != 1:
                    sys.exit(f"ABORT REJ replace anchor x{len(idx)}: {minus[0].strip()[:60]}")
                t[idx[0]] = plus[0]
            elif not minus and plus:
                k = next(i for i, l in enumerate(h) if l.startswith("+"))
                ctx = h[k - 1][1:]
                idx = [i for i, l in enumerate(t) if l == ctx]
                if len(idx) != 1:
                    sys.exit(f"ABORT REJ insert anchor x{len(idx)}: {ctx.strip()[:60]}")
                t[idx[0] + 1:idx[0] + 1] = plus
            else:
                sys.exit(f"ABORT REJ: hunk shape -{len(minus)} +{len(plus)}")
            done.append(f"{rel.split('/')[-1]} ({'replace' if minus else 'insert'})")
        p_.write_text("\n".join(t))
else:
    sys.exit("stage: 13 | E2 | TH9 | DTE | REJ")
for rel in rels:
    for ext in (".rej", ".orig"):
        q = Path(str(root / rel) + ext)
        if q.exists():
            q.unlink()
left = [str(q) for q in root.rglob("*.rej")]
print(f"stage {stage} re-anchored:", ", ".join(done) or "none", "| rejects left:", left or "none")
sys.exit(1 if left else 0)
