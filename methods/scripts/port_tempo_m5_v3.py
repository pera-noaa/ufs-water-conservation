#!/usr/bin/env python3
"""Port M5 (ccpp-physics diff 16) to TEMPO src/module_mp_tempo_main.F90 (main and the pinned versions), after the
C1-M2 port and T1. Water at or below r1 goes to vapour with its latent heat instead of being deleted.
Version 3 (round-3 red team, F1-F5): as version 2, except
  semi-Lagrangian  the routine is back to its T1 order (floor, then tendency), so the fall speeds between substeps and
                   from step to step are those before M5 (version 2 took the tendency before the floor, which removed
                   the floored mass that the fall-speed rule copies down above the precipitation top, and slowed rain
                   and graupel); the floor's mass, which the tendency books, is condensed from vapour with its latent
                   heat instead of created (F2). Only rain, graupel and hail mass pay; numbers and graupel volume are
                   not water
  hail split       (main) the rerun of the graupel check after hail is split off starts from zero tendencies, so it
                   neither undoes the first call's exchange nor turns negative graupel into positive (F3); the split
                   and the recombination leave ng1d and qb1d alone when they are absent (out-of-bounds write)
  vapour floor     vapour below min_qv at the end of the step is refilled first from the same layer's condensate
                   (normal path; latent heat, numbers scaled with mass), then from the column's vapour, mass-weighted;
                   only a column with none to spare is floored, the water created is counted in
                   tempo_main_diags%vapour_floor_water, and the latent heat of negatives filled from vapour that is
                   not there is taken back (F4, F5). The early return applies the entry exchange only where it acted;
                   a column without tendencies is returned bit for bit
  exchanges        the check routines, M1 and the semi-Lagrangian floor record the vapour they take to fill negatives
                   or the floor (qvneg) and its heating (tneg), for that take-back
  standard sedi    as version 2: placeholders at or below the limit are not transported (no in-loop vapour exchange
                   there: the in-loop fall-speed recomputation is commented out in every version, see the first commit)
Usage: python3 port_tempo_m5_v3.py <TEMPO checkout>. Each edit must match exactly where expected, else nothing is
written."""
import re
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "src/module_mp_tempo_main.F90"
s = f.read_text()


def one(s, old, new, what):
    if s.count(old) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {s.count(old)}: {old.strip()[:70]!r}")
    return s.replace(old, new)


SPECIES = {"cloud": ("c", "lvocp"), "rain": ("r", "lvocp"), "ice": ("i", "lsocp"), "snow": ("s", "lsocp"),
           "graupel": ("g", "lsocp"), "hail": ("h", "lsocp")}
present = [r for r in SPECIES if re.search(rf"^ *subroutine {r}_check_and_update\(", s, re.M)]
if sorted(present) not in (sorted(SPECIES), sorted(set(SPECIES) - {"hail"})):
    sys.exit(f"ABORT: unexpected set of check_and_update routines {present}")
hail = "hail" in present

# routines: optional arguments, declarations, and the vapour exchange before the overwrite
for r in present:
    q = "q" + SPECIES[r][0]
    a = re.search(rf"^ *subroutine {r}_check_and_update\(", s, re.M).start()
    b = s.index(f"end subroutine {r}_check_and_update", a)
    body = s[a:b]
    close = body.index(")")
    body = body[:close] + ", qvten, tten, lat_ocp, qvneg, tneg" + body[close:]
    decl = "    real(wp), dimension(:), intent(in) :: rho\n"
    if body.count(decl) != 1:
        sys.exit(f"ABORT {r}: rho declaration")
    body = body.replace(decl, decl + "    real(wp), dimension(:), intent(inout), optional :: qvten, tten, qvneg, tneg\n"
                                     "    real(wp), dimension(:), intent(in), optional :: lat_ocp\n")
    cond = re.findall(rf"if \({q}1d\(k\)\+{q}ten\(k\)\*(\w+) > r1\) then", body)
    over = re.findall(rf"^( +){q}ten\(k\) = -{q}1d\(k\) \* (\w+)\n", body, re.M)
    if len(cond) != 1 or len(over) != 1:
        sys.exit(f"ABORT {r}: {len(cond)} conditions, {len(over)} overwrites")
    ind, odt = over[0]
    dt = cond[0]
    x = f"({q}1d(k) + {q}ten(k)*{dt})"
    body = body.replace(f"{ind}{q}ten(k) = -{q}1d(k) * {odt}\n",
                        f"{ind}if (present(qvten)) then ! at or below r1: to vapour with its latent heat, not deleted\n"
                        f"{ind}  qvten(k) = qvten(k) + {x}*{odt}\n"
                        f"{ind}  tten(k) = tten(k) - lat_ocp(k)*{x}*{odt}\n"
                        f"{ind}  if ({x} < 0._wp) then ! a negative filled from vapour: recorded for vapour_floor\n"
                        f"{ind}    qvneg(k) = qvneg(k) - {x}\n"
                        f"{ind}    tneg(k) = tneg(k) - lat_ocp(k)*{x}\n"
                        f"{ind}  endif\n"
                        f"{ind}endif\n"
                        f"{ind}{q}ten(k) = -{q}1d(k) * {odt}\n", 1)
    s = s[:a] + body + s[b:]

ta = re.search(r"^ *subroutine tempo_main\(", s, re.M).start()
tb = s.index("end subroutine tempo_main", ta)
main = s[ta:tb]
fu = re.findall(r"^    ! final update -+\n", main, re.M)
sd = re.findall(r"^    ! sedimentation -+\n", main, re.M)
if len(fu) != 1 or len(sd) != 1:
    sys.exit(f"ABORT calls: {len(fu)} final-update and {len(sd)} sedimentation markers")

# inverse time step in tempo_main: odt, or the module's global_inverse_dt before v3.0.5
if re.search(r"^    odt = 1\._wp / dt$", main, re.M):
    odt = "odt"
elif re.search(r"^    global_inverse_dt = 1\._wp / dt$", main, re.M):
    odt = "global_inverse_dt"
else:
    sys.exit("ABORT: no inverse time step in tempo_main")

# calls in tempo_main before the final update pass the vapour arguments; after it qv1d and t1d are final and M1 has
# already exchanged everything at or below r1, so the arguments could not act
final_at = main.index(fu[0])
out, pos, ncalls, nskip = [], 0, 0, 0
for m in re.finditer(rf"^( *)call ({'|'.join(present)})_check_and_update\(", main, re.M):
    if m.start() > final_at:
        nskip += 1
        continue
    depth, i = 0, m.end() - 1
    while True:
        c = main[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        elif c == "!":
            sys.exit("ABORT calls: comment inside a call")
        i += 1
    out.append(main[pos:i] + f", &\n{m.group(1)}  qvten=qvten, tten=tten, lat_ocp={SPECIES[m.group(2)][1]}, "
                             f"qvneg=qvneg, tneg=tneg)")
    pos = i + 1
    while main[pos] == " ":  # trailing blanks after the call would now end the new line
        pos += 1
    ncalls += 1
main = "".join(out) + main[pos:]
if ncalls < 2 * len(present) or nskip != len(present) + 1 + hail or \
        len(re.findall(r"_check_and_update\(", s[:ta] + s[tb:])) != len(present) + 1:
    sys.exit(f"ABORT calls: {ncalls} before and {nskip} after the final update; check_and_update also called outside?")

# semi-Lagrangian sedimentation of rain, graupel and hail mass: the floor the routine applies to the transported state
# (which the tendency includes, as before) is condensed from vapour, with its latent heat
nsemi = 0
calls = list(re.finditer(r"call semilagrangian_sedimentation\(dz1d=dz1d, rho=rho, xr=(r[rgh]), xten=q[rgh]ten, &\n"
                         r"( +)vt=\w+, steps=substeps_sedi, limit=r1, precip=tempo_main_diags%\w+", main))
if len(calls) != (3 if hail else 2):
    sys.exit(f"ABORT semi calls: {len(calls)}")
for m in reversed(calls):
    lat = "lvocp" if m.group(1) == "rr" else "lsocp"
    i = main.index(")", m.end())
    main = main[:i] + f", &\n{m.group(2)}qvten=qvten, tten=tten, lat_ocp={lat}, qvneg=qvneg, tneg=tneg" + main[i:]
    nsemi += 1

# hail split (main): the rerun starts from zero tendencies; ng1d and qb1d only where present
if hail:
    split = ("    do k = 1, nz\n      if (l_qh(k)) then\n        qg1d(k) = qg1d(k) - qh1d(k)\n"
             "        ng1d(k) = ng1d(k) - nh(k)/rho(k)\n"
             "        qb1d(k) = qb1d(k) - qh1d(k)*meters3_to_liters/rho_g(nrhg)\n"
             "        qgten(k) = 0._wp\n        ngten(k) = 0._wp\n        qbten(k) = 0._wp\n      endif\n    enddo\n")
    main = one(main, split,
               "    do k = 1, nz\n      if (l_qh(k)) then\n        qg1d(k) = qg1d(k) - qh1d(k)\n"
               "        if (present(ng1d) .and. present(qb1d)) then\n"
               "          ng1d(k) = ng1d(k) - nh(k)/rho(k)\n"
               "          qb1d(k) = qb1d(k) - qh1d(k)*meters3_to_liters/rho_g(nrhg)\n"
               "        endif\n      endif\n    enddo\n", "hail split")
    rerun = "    ! if hail is split from graupel, rerun graupel checks\n    if (any(l_qh)) then\n"
    main = one(main, rerun, rerun +
               "      ! the first check has already applied its changes to qg1d, ng1d and qb1d (and moved what it\n"
               "      ! removed to vapour): its tendencies would be applied a second time\n"
               "      qgten = 0._wp\n      ngten = 0._wp\n      qbten = 0._wp\n", "hail rerun")
    comb = ("        if (ngten(k) >= 0._wp) ng1d(k) = ng1d(k) + nh(k)/rho(k)\n"
            "        qb1d(k) = qb1d(k) + qh1d(k)*meters3_to_liters/rho_g(nrhg)\n")
    main = one(main, comb, "        if (present(ng1d) .and. present(qb1d)) then\n"
               "          if (ngten(k) >= 0._wp) ng1d(k) = ng1d(k) + nh(k)/rho(k)\n"
               "          qb1d(k) = qb1d(k) + qh1d(k)*meters3_to_liters/rho_g(nrhg)\n        endif\n",
               "hail recombination")

# early return: the entry exchange (in qvten, tten) is applied where it acted, with the vapour floor; a column without
# tendencies is returned exactly as it came
fl = re.findall(r"^      t1d\(k\)  = t1d\(k\) \+ tten\(k\)\*(\w+)\n      qv1d\(k\) = max\(min_qv, \(qv1d\(k\) \+ qvten\(k\)\*(\w+)\)\)\n",
                main, re.M)
if len(fl) != 1 or fl[0][0] != fl[0][1]:
    sys.exit(f"ABORT early return: final update {fl}")
tdt = fl[0][0]
main = one(main, "    if (.not. do_micro .and. .not. supersaturated) return\n",
           "    if (.not. do_micro .and. .not. supersaturated) then\n"
           "      ! the entry checks changed q1d in place and left the matching vapour and heat in qvten, tten: apply\n"
           "      ! them where they acted (refilling vapour they took below min_qv); elsewhere the state is untouched\n"
           "      do k = 1, nz\n"
           "        l_act(k) = qvten(k) /= 0._wp .or. tten(k) /= 0._wp\n"
           "      enddo\n"
           f"      call vapour_floor(rho, dz1d, qv1d, qvten, tten, qvneg, tneg, l_act, {tdt}, {odt}, &\n"
           "        tempo_main_diags%vapour_floor_water)\n"
           "      do k = 1, nz\n"
           f"        t1d(k)  = t1d(k) + tten(k)*{tdt}\n"
           f"        qv1d(k) = qv1d(k) + qvten(k)*{tdt}\n"
           "      enddo\n"
           "      return\n"
           "    endif\n", "early return")
er = main.index("    if (.not. do_micro .and. .not. supersaturated) then\n")
if re.search(r"^\s*(qvten|tten)\(k\) = (?!0\._wp)", main[:er], re.M) or re.search(r"^\s*(qvten|tten) = ", main[:er], re.M):
    sys.exit("ABORT early return: other writes to qvten/tten before the return")

# normal path: before M1, vapour that would end below min_qv is refilled from the same layer's condensate; M1 records
# the vapour it takes to fill negatives; after M1 the column refill and floor
m1 = "    ! condensate the final clips would delete is exchanged with vapour (with its latent heat) instead\n"
spc = [("c", "lvap(k)", "nc1d", "ncten"), ("r", "lvap(k)", "nr1d", "nrten"), ("i", "lsub", "ni1d", "niten"),
       ("s", "lsub", None, None), ("g", "lsub", "ng1d", "ngten")] + ([("h", "lsub", None, None)] if hail else [])
blk = ("    ! vapour that would end the step below min_qv is refilled first from the same layer's condensate, with its\n"
       "    ! latent heat (numbers scaled with mass), then by vapour_floor from the column's vapour\n"
       "    do k = 1, nz\n"
       "      xcl = qv1d(k) + qvten(k)*dt\n"
       "      if (xcl < min_qv) then\n"
       "        xliq = max(qc1d(k) + qcten(k)*dt, 0._wp) + max(qr1d(k) + qrten(k)*dt, 0._wp)\n"
       "        xice = " + " + ".join(f"max(q{q}1d(k) + q{q}ten(k)*dt, 0._wp)" for q, *_ in spc[2:4]) + " + &\n"
       "          " + " + ".join(f"max(q{q}1d(k) + q{q}ten(k)*dt, 0._wp)" for q, *_ in spc[4:]) + "\n"
       "        if (xliq + xice > 0._wp) then\n"
       "          frc = min(1._wp, (min_qv - xcl)/(xliq + xice))\n"
       f"          qvten(k) = qvten(k) + frc*(xliq + xice)*{odt}\n"
       f"          tten(k) = tten(k) - frc*ocp(k)*(lvap(k)*xliq + lsub*xice)*{odt}\n")
for q, lat, n1, nt in spc:
    blk += f"          q{q}ten(k) = q{q}ten(k) - frc*max(q{q}1d(k) + q{q}ten(k)*dt, 0._wp)*{odt}\n"
blk += f"          nrten(k) = nrten(k) - frc*(nr1d(k) + nrten(k)*dt)*{odt}\n"
blk += f"          niten(k) = niten(k) - frc*(ni1d(k) + niten(k)*dt)*{odt}\n"
blk += (f"          if (present(nc1d)) ncten(k) = ncten(k) - frc*(nc1d(k) + ncten(k)*dt)*{odt}\n"
        "          if (present(ng1d) .and. present(qb1d)) then\n"
        f"            ngten(k) = ngten(k) - frc*(ng1d(k) + ngten(k)*dt)*{odt}\n"
        f"            qbten(k) = qbten(k) - frc*(qb1d(k) + qbten(k)*dt)*{odt}\n"
        "          endif\n"
        "        endif\n"
        "      endif\n"
        "    enddo\n\n")
main = one(main, m1, blk + m1, "layer refill")
a = main.index(m1)
b = main.index("    enddo\n", a) + len("    enddo\n")
mb = main[a:b]
nx = mb.count(f"        qvten(k) = qvten(k) + xcl*{odt}\n")
if nx != len(spc):
    sys.exit(f"ABORT M1: {nx} exchanges for {len(spc)} species")
for q, lat, *_ in spc:
    old = (f"        q{q}ten(k) = q{q}ten(k) - xcl*{odt}\n        qvten(k) = qvten(k) + xcl*{odt}\n"
           f"        tten(k) = tten(k) - {lat}*ocp(k)*xcl*{odt}\n")
    if mb.count(old) != 1:
        sys.exit(f"ABORT M1 q{q}")
    mb = mb.replace(old, old + "        if (xcl < 0._wp) then\n          qvneg(k) = qvneg(k) - xcl\n"
                              f"          tneg(k) = tneg(k) - {lat}*ocp(k)*xcl\n        endif\n")
mb += ("\n    ! vapour still below min_qv is refilled from the column's vapour; only a column with none to spare is floored\n"
       "    l_act = .true.\n"
       f"    call vapour_floor(rho, dz1d, qv1d, qvten, tten, qvneg, tneg, l_act, dt, {odt}, &\n"
       "      tempo_main_diags%vapour_floor_water)\n")
main = main[:a] + mb + main[b:]

# locals, zeroing, diagnostic
dcl = "    real(wp), dimension(kts:kte) :: rhon !! density after latent heating, for fall speeds only\n"
main = one(main, dcl, dcl + "    real(wp), dimension(kts:kte) :: lvocp, lsocp !! latent heat over cp, for water sent to vapour\n"
           "    real(wp), dimension(kts:kte) :: qvneg, tneg !! vapour taken to fill negatives, and its heating\n"
           "    real(wp) :: xliq, xice, frc\n"
           "    logical, dimension(kts:kte) :: l_act !! levels the vapour floor may refill\n",
           "locals (run port_tempo_scheme first)")
z = "      tten(k) = 0._wp\n      qvten(k) = 0._wp\n"
main = one(main, z, z + "      qvneg(k) = 0._wp\n      tneg(k) = 0._wp\n", "zeroing")
fz = "    tempo_main_diags%frz_rain_precip = 0._wp\n"
main = one(main, fz, fz + "    tempo_main_diags%vapour_floor_water = 0._wp\n", "diagnostic zeroing")

# latent heat over cp from the entry state
ent = re.search(r"\n      temp\(k\) = t1d\(k\)\n      qv\(k\) = max\(min_qv, qv1d\(k\)\)\n", main)
if ent is None or main.count("      temp(k) = t1d(k)\n      qv(k) = max(min_qv, qv1d(k))\n") != 1:
    sys.exit("ABORT entry loop")
e = main.index("    enddo\n", ent.end()) + len("    enddo\n")
main = (main[:e] + "\n    do k = 1, nz\n"
        "      lvocp(k) = (lvap0 + (2106.0_wp - 4218.0_wp)*(temp(k) - t0))/(cp*(1._wp + 0.887_wp*qv(k)))\n"
        "      lsocp(k) = lsub/(cp*(1._wp + 0.887_wp*qv(k)))\n    enddo\n" + main[e:])
for name in ("lvap0", "cp", "xliq", "xice", "frc", "qvneg", "tneg", "l_act"):
    if len(re.findall(rf"^\s*(real|logical)\b[^\n!]*::[^\n!]*\b{name}\b", main, re.M)) != (1 if name not in ("lvap0", "cp") else 0):
        sys.exit(f"ABORT: {name} declared {'more than once' if name not in ('lvap0', 'cp') else 'as a local'} in tempo_main")
s = s[:ta] + main + s[tb:]
s = one(s, ", lsub\n  use module_mp_tempo_utils", ", lsub, lvap0, cp\n  use module_mp_tempo_utils", "imports")

# the diagnostic
dg = [m.group(0) for m in re.finditer(r"^    real\(wp\) :: frz_rain_precip( = 0\._wp)?\n", s, re.M)]
if len(dg) != 1:
    sys.exit("ABORT diagnostic type")
s = one(s, dg[0], dg[0] + f"    real(wp) :: vapour_floor_water{dg[0][len('    real(wp) :: frz_rain_precip'):-1]}"
        " !! water created by the vapour floor where the column had none to spare [kg m-2]\n", "diagnostic type")

# vapour_floor, after sedimentation
vf = '''
  subroutine vapour_floor(rho, dz1d, qv1d, qvten, tten, qvneg, tneg, l_act, dt, odt, created)
    !! vapour that would end the step below min_qv at a level in l_act is refilled from the column's vapour (every
    !! level above min_qv gives the same fraction of its excess). Only a column with none to spare is floored: that
    !! water is created and counted, and the latent heat of negatives filled from vapour that was not there (qvneg,
    !! tneg) is taken back
    real(wp), dimension(:), intent(in) :: rho, dz1d, qv1d, qvneg, tneg
    real(wp), dimension(:), intent(inout) :: qvten, tten
    logical, dimension(:), intent(in) :: l_act
    real(wp), intent(in) :: dt, odt
    real(wp), intent(inout) :: created
    real(wp) :: xdef, xavl, fgive, ffill, qvf, short
    integer :: k, nz

    nz = size(qv1d)
    xdef = 0._wp
    xavl = 0._wp
    do k = 1, nz
      qvf = qv1d(k) + qvten(k)*dt
      if (l_act(k)) xdef = xdef + max(min_qv - qvf, 0._wp)*rho(k)*dz1d(k)
      xavl = xavl + max(qvf - min_qv, 0._wp)*rho(k)*dz1d(k)
    enddo
    if (xdef <= 0._wp) return
    fgive = 0._wp
    ffill = 0._wp
    if (xavl > 0._wp) then
      fgive = min(1._wp, xdef/xavl)
      ffill = min(1._wp, xavl/xdef)
    endif
    do k = 1, nz
      qvf = qv1d(k) + qvten(k)*dt
      if (l_act(k) .and. qvf < min_qv) then
        short = (min_qv - qvf)*(1._wp - ffill)
        qvten(k) = qvten(k) + (min_qv - qvf)*odt
        if (short > 0._wp) then
          created = created + short*rho(k)*dz1d(k)
          if (qvneg(k) > 0._wp) tten(k) = tten(k) - min(short, qvneg(k))*tneg(k)/qvneg(k)*odt
        endif
      elseif (qvf > min_qv .and. fgive > 0._wp) then
        qvten(k) = qvten(k) - (qvf - min_qv)*fgive*odt
      endif
    enddo
  end subroutine vapour_floor
'''
s = one(s, "  end subroutine sedimentation\n", "  end subroutine sedimentation\n" + vf, "vapour_floor")

# semilagrangian_sedimentation: optional vapour arguments; where the floor raises the transported state (and so the
# tendency), that mass is taken from vapour with its latent heat
a = s.index("  subroutine semilagrangian_sedimentation(")
b = s.index("  end subroutine semilagrangian_sedimentation", a)
sl = s[a:b]
hdr = re.match(r"  subroutine semilagrangian_sedimentation\(([^)]*)\)\n", sl)
if hdr is None:
    sys.exit("ABORT semi: header")
sl = sl.replace(hdr.group(0), f"  subroutine semilagrangian_sedimentation({hdr.group(1)}, &\n"
                "      qvten, tten, lat_ocp, qvneg, tneg)\n", 1)
dcl = "    real(wp), dimension(:), intent(inout) :: xr, xten\n"
if sl.count(dcl) != 1:
    sys.exit("ABORT semi: xr declaration")
sl = sl.replace(dcl, dcl + "    real(wp), dimension(:), intent(inout), optional :: qvten, tten, qvneg, tneg\n"
                "    real(wp), dimension(:), intent(in), optional :: lat_ocp\n")
fl = re.findall(r"^      orho = 1\._wp / rho\(k\)\n      xr\(k\) = max\(xr\(k\), limit\)\n      xten\(k\) = xten\(k\) \+ "
                r"\(xr\(k\) - rr_save\(k\)\) \* &\n        orho\*(\w+)\n", sl, re.M)
if len(fl) != 1:
    sys.exit(f"ABORT semi: floor and tendency ({len(fl)})")
o = fl[0]
sl = sl.replace("      orho = 1._wp / rho(k)\n      xr(k) = max(xr(k), limit)\n",
                "      orho = 1._wp / rho(k)\n"
                "      if (present(qvten) .and. xr(k) < limit) then ! the floor, booked in xten, is condensed from vapour\n"
                f"        qvten(k) = qvten(k) - (limit - xr(k))*orho*{o}\n"
                f"        tten(k) = tten(k) + lat_ocp(k)*(limit - xr(k))*orho*{o}\n"
                "        qvneg(k) = qvneg(k) + (limit - xr(k))*orho\n"
                "        tneg(k) = tneg(k) + lat_ocp(k)*(limit - xr(k))*orho\n"
                "      endif\n"
                "      xr(k) = max(xr(k), limit)\n", 1)
s = s[:a] + sl + s[b:]

# standard sedimentation: placeholders not transported
a = s.index("subroutine sedimentation(")
b = s.index("end subroutine sedimentation", a)
sdm = s[a:b]
if "allocate(sed_r(nz), source=0._wp)" not in sdm:
    sys.exit("ABORT sedimentation flux: sed_r not zeroed")
sdm = one(sdm, "      sed_r(k) = vt(k)*xr(k)\n",
          "      ! inputs at or below limit (placeholders for absent mass) are not transported\n"
          "      if (xr(k) > limit) sed_r(k) = vt(k)*xr(k)\n", "sedimentation flux")
s = s[:a] + sdm + s[b:]

f.write_text(s)
print(f"patched {f.relative_to(f.parents[1])}: M5 v3 ({len(present)} routines, {ncalls} calls pass qvten, {nskip} "
      f"after the final update do not; {nsemi} semi-Lagrangian mass calls pay their floor from vapour; early return and "
      f"final update on vapour_floor ({odt}){'; hail split' if hail else ''})")
