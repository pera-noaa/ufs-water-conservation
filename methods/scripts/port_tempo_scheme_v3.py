#!/usr/bin/env python3
"""Port the scheme-internal Thompson water fixes C1, C2, C3, M1 and M2 (ccpp-physics diffs 03, 05, 07, 13) to TEMPO
(NCAR/TEMPO src/module_mp_tempo_main.F90: main, and the versions UFS, WRF and UFS's MPAS fork pin).
Version 2 (round-2 review): C1 also substeps cloud sedimentation with the Courant rule, and the frozen fraction is
computed after the settled cloud water is added to rain; C2 also caps the snow gain from cold rain-snow collection.
Version 3 (round-3 red team, F1): in versions before v3.0.5 (9adf9ef) the standard (flux-form) rain and graupel
sedimentation recomputed the fall speeds inside the substep loop, after the number of substeps had been fixed from
the fall speeds before it, so a layer could lose more than it held (the overdraft became negative condensate, then
water created by the clips, or with M5 vapour and latent heat: dT up to 1e6 K). The in-loop recomputation is
commented out exactly as v3.0.5 (881614f) and later versions have it; the substeps then keep every layer's outflow
within its content. Versions that already have it commented out are unchanged.
Usage: python3 port_tempo_scheme_v3.py <TEMPO checkout>
  C1  cloud water settling out of the lowest layer (cloud_precip, so far only in the freezing-rain diagnostic) counted
      as rain, before the frozen fraction is computed; cloud sedimentation substepped so that no layer loses more
      than it holds (Courant number <= 1), as rain, ice, snow and graupel already are
  C2  graupel gains from rain-ice and (below freezing) rain-snow collection recomputed in check_over_depletion, after
      the limiters, with their graupel volume; below freezing the snow gain from rain-snow collection is first capped
      at the rain lost to it, so that the recomputed graupel gain cannot be negative
  C3  rho kept at the entry density for all mass conversions through sedimentation; the updated density (rhon) only
      for the fall-speed and ventilation factors from thermo_vars
  M1  before the final update, condensate the clips would delete (<= r1) is exchanged with vapour, with its latent heat
  M2  all of the sedimentation flux out of the lowest layer counted as surface precipitation
Each edit must match exactly where expected, else nothing is written. Versions differ in hail (main only), the
graupel-volume density (rho_g(nrhg) in main, rho_i before) and the import list; C2's volumes use each version's own
formulas."""
import re
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "src/module_mp_tempo_main.F90"
s = f.read_text()


def one(s, old, new, what, count=1):
    if s.count(old) != count:
        sys.exit(f"ABORT {what}: expected {count} match(es), found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


# imports and locals
imp = re.findall(r"^    meters3_to_liters, eps, aero_max, nwfa_default, nifa_default[^\n&]*\n", s, re.M)
if len(imp) != 1:
    sys.exit(f"ABORT imports: expected 1 match, found {len(imp)}")
s = one(s, imp[0], imp[0][:-1] + ", lsub\n", "imports")
s = one(s, "    real(wp), dimension(kts:kte) :: rho, rhof, rhof2 !! thermodynamic variables\n",
        "    real(wp), dimension(kts:kte) :: rho, rhof, rhof2 !! thermodynamic variables\n"
        "    real(wp), dimension(kts:kte) :: rhon !! density after latent heating, for fall speeds only\n"
        "    real(wp) :: xcl\n", "locals")

# C3: between the tendency update and sedimentation, density updates go to rhon, and thermo_vars uses rhon
a = s.index("    ! update after tendencies applied ---")
b = s.index("    ! sedimentation ---", a)
blk = s[a:b]
upd = "rho(k) = roverrv*pres(k)/(rdry*temp(k)*(qv(k)+roverrv))"
if blk.count(upd) != 3 or blk.count("call thermo_vars(qv, temp, pres, rho, rhof") != 3:
    sys.exit(f"ABORT C3: {blk.count(upd)} density updates, {blk.count('call thermo_vars(qv, temp, pres, rho, rhof')} thermo_vars calls")
blk = blk.replace("    ! update after tendencies applied ---",
                  "    ! rho stays the entry density so sedimentation conserves the host's column mass; rhon is only for\n"
                  "    ! fall speeds and ventilation\n    ! update after tendencies applied ---", 1)
blk = blk.replace(upd, "rhon(k) = roverrv*pres(k)/(rdry*temp(k)*(qv(k)+roverrv))")
blk = blk.replace("call thermo_vars(qv, temp, pres, rho, rhof", "call thermo_vars(qv, temp, pres, rhon, rhof")
s = s[:a] + blk + s[b:]

# C2: in check_over_depletion, after the rain-graupel re-closure
# the graupel volumes use each version's own expressions from rain-ice and rain-snow collection
vol = {}
for t in ("rci", "rcs"):
    e = re.findall(rf"^ +tend%pbg_{t}\(k\) = (.*)\n", s, re.M)
    if len(e) != 1:
        sys.exit(f"ABORT C2: expected 1 pbg_{t} expression, found {len(e)}")
    vol[t] = e[0].replace(" * ", "*")
rcg = re.findall(r"^      tend%pbg_rcg\(k\) = meters3_to_liters\*tend%prg_rcg\(k\)/(?:rho_g\(nrhg\)|rho_i) ! scale density change\n",
                 s, re.M)
if len(rcg) != 1:
    sys.exit(f"ABORT C2: expected 1 pbg_rcg re-closure, found {len(rcg)}")
s = one(s, rcg[0], rcg[0] + "\n"
        "      ! graupel gains must match the (possibly limited) losses that feed them\n"
        "      tend%prg_rci(k) = tend%pri_rci(k) + tend%prr_rci(k)\n"
        f"      tend%pbg_rci(k) = {vol['rci']}\n"
        "      if (temp(k) < t0) then\n"
        "        tend%prg_rcs(k) = -(tend%prr_rcs(k) + tend%prs_rcs(k))\n"
        f"        tend%pbg_rcs(k) = {vol['rcs']}\n"
        "      endif\n", "C2")
c2 = s[s.index("  subroutine check_over_depletion"):s.index("  end subroutine check_over_depletion")]
head = c2.split("tend%pbg_rcg(k) = ")[0]
for name in set(re.findall(r"[a-z_0-9]+", vol["rci"] + " " + vol["rcs"])) - {"tend", "prg_rci", "prg_rcs", "k"} | {"t0"}:
    if not re.search(rf"\b{name}\b", head) and not re.search(rf"\b{name}\b", s[:s.index("  subroutine tempo_main")]):
        sys.exit(f"ABORT C2: {name} not in scope in check_over_depletion")

# C2 cap: below freezing, after the rain limiter and before the snow limiter
cap_at = re.findall(r"^      ! losses to snow include sublimation; melting; collection by rain; *\n", s, re.M)
if len(cap_at) != 1:
    sys.exit(f"ABORT C2 cap: expected 1 snow-limiter comment, found {len(cap_at)}")
s = one(s, cap_at[0], "      ! below freezing, snow cannot gain more from rain-snow collection than the rain loses to it\n"
        "      if (temp(k) < t0 .and. tend%prs_rcs(k) > -tend%prr_rcs(k)) tend%prs_rcs(k) = -tend%prr_rcs(k)\n\n"
        + cap_at[0], "C2 cap")
c2 = s[s.index("  subroutine check_over_depletion"):s.index("  end subroutine check_over_depletion")]
if c2.index("tend%prs_rcs(k) = -tend%prr_rcs(k)\n\n") > c2.index("tend%prg_rcs(k) = -(tend%prr_rcs(k) + tend%prs_rcs(k))"):
    sys.exit("ABORT C2 cap: not before the recompute")

# C1 substepping: cloud sedimentation with the Courant rule of the other species (time step dt, or global_dt before v3.0.5)
rule = set(re.findall(r"substeps_sedi = max\(substeps_sedi, int\((\w+)/dz_by_vt \+ 1\._wp\)\)", s))
if len(rule) != 1:
    sys.exit(f"ABORT C1 substeps: Courant rule time step {rule}")
tdt = rule.pop()
cl = re.search(r"(    if \(any\(l_qc\)\) then\n"
               r"      call cloud_fallspeed\(rhof, w1d, l_qc, rc, nc, ilamc, dz1d, vtrc, vtnc, ktop_sedi\)\n)"
               r"(      call sedimentation\(xr=rc, vt=vtrc, [^\n]*&\n[^\n]*precip=tempo_main_diags%cloud_precip[^\n]*\n"
               r"      call sedimentation\(xr=nc, vt=vtnc, [^\n]*&\n[^\n]*\n)"
               r"(    endif *\n)", s)
if cl is None or len(re.findall(r"call cloud_fallspeed\(", s)) != 1:
    sys.exit("ABORT C1 substeps: cloud sedimentation block")
sed = "".join("  " + line + "\n" for line in cl.group(2).splitlines())
s = (s[:cl.start()] + cl.group(1)
     + "      ! substeps keep each layer's outflow within its content (Courant number <= 1), as for the other species\n"
     + "      do k = 1, ktop_sedi\n"
     + "        if (max(vtrc(k), vtnc(k)) > 0._wp) substeps_sedi = &\n"
     + f"          max(substeps_sedi, int({tdt}/(dz1d(k)/max(vtrc(k), vtnc(k))) + 1._wp))\n"
     + "      enddo\n      do n = 1, substeps_sedi\n" + sed + "      enddo\n" + cl.group(3) + s[cl.end():])

# M2: in sedimentation (the time step is the dt argument, or global_dt in versions before v3.0.5)
m2 = re.findall(r"^    if \(present\(precip\)\) then \n      if \(xr\(1\) > low_limit_mass_for_precip\) then\n"
                r"        precip = precip \+ sed_r\(1\)\*(dt|global_dt)\*\(1\._wp/real\(steps, kind=wp\)\)\n      endif \n    endif \n",
                s, re.M)
if len(m2) != 1:
    sys.exit(f"ABORT M2: expected 1 match, found {len(m2)}")
s = re.sub(r"^    if \(present\(precip\)\) then \n      if \(xr\(1\) > low_limit_mass_for_precip\) then\n"
           r"        precip = precip \+ sed_r\(1\)\*(?:dt|global_dt)\*\(1\._wp/real\(steps, kind=wp\)\)\n      endif \n    endif \n",
           "    ! all of the flux out of the lowest layer reaches the surface\n"
           f"    if (present(precip)) precip = precip + sed_r(1)*{m2[0]}*(1._wp/real(steps, kind=wp))\n", s, flags=re.M)
s = one(s, "    use module_mp_tempo_params, only : low_limit_mass_for_precip\n\n", "", "M2 import")
if "low_limit_mass_for_precip" in s:
    sys.exit("ABORT M2: low_limit_mass_for_precip still used")

# M1: before the final update
# inverse time step: odt in tempo_main, or the module's global_inverse_dt in versions before v3.0.5
if re.search(r"^    odt = 1\._wp / dt$", s, re.M):
    odt = "odt"
elif re.search(r"^    global_inverse_dt = 1\._wp / dt$", s, re.M):
    odt = "global_inverse_dt"
else:
    sys.exit("ABORT M1: no inverse time step in tempo_main")
m1 = "    ! condensate the final clips would delete is exchanged with vapour (with its latent heat) instead\n    do k = 1, nz\n"
species = [("qc", "lvap(k)"), ("qr", "lvap(k)"), ("qi", "lsub"), ("qs", "lsub"), ("qg", "lsub")]
if "qhten" in s:
    species.append(("qh", "lsub"))
for q, lat in species:
    m1 += (f"      xcl = {q}1d(k) + {q}ten(k)*dt\n"
           f"      if (xcl <= r1) then\n"
           f"        {q}ten(k) = {q}ten(k) - xcl*{odt}\n"
           f"        qvten(k) = qvten(k) + xcl*{odt}\n"
           f"        tten(k) = tten(k) - {lat}*ocp(k)*xcl*{odt}\n"
           f"      endif\n")
m1 += "    enddo\n\n"
s = one(s, "    ! final update ---", m1 + "    ! final update ---", "M1")

# C1: the freezing-rain diagnostic, which uses rain and cloud separately, moves to the head of the diagnostic output;
# the settled cloud water is then added to rain, so the frozen fraction's total includes it
frz = ("\n    ! freezing rain\n"
       "    call freezing_rain(temp=temp(1), rain_precip=tempo_main_diags%rain_precip, &\n"
       "      cloud_precip=tempo_main_diags%cloud_precip, &\n      frz_rain=tempo_main_diags%frz_rain_precip)\n")
s = one(s, frz, "", "C1 freezing rain")
hd = re.findall(r"^    ! diagnostic output -+\n", s, re.M)
if len(hd) != 1:
    sys.exit(f"ABORT C1: {len(hd)} diagnostic-output headers")
head = hd[0]
s = one(s, head + "    ! frozen fraction\n",
        head + frz[1:] + "\n"
        "    ! cloud water settling out of the lowest layer reaches the surface: count it as precipitation\n"
        "    tempo_main_diags%rain_precip = tempo_main_diags%rain_precip + tempo_main_diags%cloud_precip\n\n"
        "    ! frozen fraction\n", "C1")
d = s[s.index(head):]
if not d.index("call freezing_rain(") < d.index("rain_precip + tempo_main_diags%cloud_precip") < d.index("frozen_fraction ="):
    sys.exit("ABORT C1: diagnostic order")

# F1 (before v3.0.5): standard rain and graupel sedimentation keep the fall speeds the substeps were counted for
nf1 = 0
for xr, sp in (("rr", "rain"), ("rg", "graupel")):
    m = re.search(rf"^      else\n        do n = 1, substeps_sedi\n          call sedimentation\(xr={xr}, .*?\n        enddo\n",
                  s, re.M | re.S)
    if m is None:
        sys.exit(f"ABORT F1 {sp}: standard substep loop")
    blk = m.group(0)
    act = re.search(rf"^          vt{xr} = 0\._wp\n", blk, re.M)
    if act is None:
        if not re.search(rf"^          ! call {sp}_fallspeed\(", blk, re.M):
            sys.exit(f"ABORT F1 {sp}: neither active nor commented in-loop fall speeds")
        continue
    head, tail = blk[:act.start()], blk[act.start():]
    end = tail.index("        enddo\n")
    body = tail[:end]
    if not re.search(rf"call {sp}_check_and_update\(", body) or not re.search(rf"call {sp}_fallspeed\(", body):
        sys.exit(f"ABORT F1 {sp}: in-loop calls")
    body = "".join("          ! " + line[10:].rstrip() + "\n" for line in body.splitlines())
    blk2 = head + ("          ! the fall speeds stay those the substeps were counted for (as from v3.0.5): recomputed\n"
                   "          ! here, a layer could lose more than it holds\n") + body + tail[end:]
    s = s.replace(blk, blk2, 1)
    nf1 += 1

f.write_text(s)
print(f"patched {f.relative_to(f.parents[1])}: C1 (cloud substeps on {tdt}), C2 (cap; volumes {vol['rci']}, {vol['rcs']}), C3 (3 density updates, "
      f"3 thermo_vars calls), M1 ({len(species)} species), M2, F1 ({nf1} in-loop fall-speed recomputations commented out)")
