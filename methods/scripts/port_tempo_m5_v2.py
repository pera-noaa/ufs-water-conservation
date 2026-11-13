#!/usr/bin/env python3
"""Port M5 (ccpp-physics diff 16) to TEMPO src/module_mp_tempo_main.F90 (main and the pinned versions), after the
C1-M2 port and T1. Water at or below r1 goes to vapour with its latent heat instead of being deleted. Version 2
(round-2 review): the entry exchange also reaches the state on the early return; calls after the final update no
longer pass the vapour arguments (they cannot act there); the flux-form sedimentation no longer transports placeholders.
  check_and_update  each hydrometeor *_check_and_update routine, when q1d + qten*dt <= r1, overwrote qten to delete
                    what was left (negative after an overshoot, which then created water). With the new optional
                    arguments qvten, tten and lat_ocp it first moves that amount to vapour; every call in tempo_main
                    before the final update passes them, with latent heat over cp from the entry state (lvap for
                    cloud and rain, lsub for ice, snow, graupel, hail). Calls after the final update (qv1d and t1d
                    already updated, everything at or below r1 already exchanged by M1) and the diagnostic PBL-cloud
                    copy do not pass them
  early return      the entry calls change q1d in place but leave the matching vapour and heat in qvten and tten;
                    where tempo_main returns early (no hydrometeor above r1, not supersaturated) it now applies them
                    to qv1d and t1d exactly as the final update does
  sedimentation     semilagrangian_sedimentation took its tendency after flooring xr at limit, so the floor created
                    water; take the tendency before the floor, which stays in the transported state only. The flux-form
                    sedimentation routine leaves inputs at or below limit (the r1/r2 placeholders of absent species,
                    into which the fall-speed routines copy the fall speed from above, and layers it has floored) out
                    of the transport, so they are no longer booked as precipitation; they stay in place. Not done in
                    the semi-Lagrangian routine, where the placeholders also enter the edge values of the layer below
                    them: leaving them out there changes the reconstruction, not just the booking (measured: the
                    1-h precipitation of the 59-level test column shifts by -0.56 % at 20 s on 9adf9ef)
Usage: python3 port_tempo_m5_v2.py <TEMPO checkout>. Each edit must match exactly where expected, else nothing is
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

# routines: optional arguments, declarations, and the vapour exchange before the overwrite
for r in present:
    q = "q" + SPECIES[r][0]
    a = re.search(rf"^ *subroutine {r}_check_and_update\(", s, re.M).start()
    b = s.index(f"end subroutine {r}_check_and_update", a)
    body = s[a:b]
    close = body.index(")")
    body = body[:close] + ", qvten, tten, lat_ocp" + body[close:]
    decl = "    real(wp), dimension(:), intent(in) :: rho\n"
    if body.count(decl) != 1:
        sys.exit(f"ABORT {r}: rho declaration")
    body = body.replace(decl, decl + "    real(wp), dimension(:), intent(inout), optional :: qvten, tten\n"
                                     "    real(wp), dimension(:), intent(in), optional :: lat_ocp\n")
    cond = re.findall(rf"if \({q}1d\(k\)\+{q}ten\(k\)\*(\w+) > r1\) then", body)
    over = re.findall(rf"^( +){q}ten\(k\) = -{q}1d\(k\) \* (\w+)\n", body, re.M)
    if len(cond) != 1 or len(over) != 1:
        sys.exit(f"ABORT {r}: {len(cond)} conditions, {len(over)} overwrites")
    ind, odt = over[0]
    dt = cond[0]
    body = body.replace(f"{ind}{q}ten(k) = -{q}1d(k) * {odt}\n",
                        f"{ind}if (present(qvten)) then ! at or below r1: to vapour with its latent heat, not deleted\n"
                        f"{ind}  qvten(k) = qvten(k) + ({q}1d(k) + {q}ten(k)*{dt})*{odt}\n"
                        f"{ind}  tten(k) = tten(k) - lat_ocp(k)*({q}1d(k) + {q}ten(k)*{dt})*{odt}\n"
                        f"{ind}endif\n"
                        f"{ind}{q}ten(k) = -{q}1d(k) * {odt}\n", 1)
    s = s[:a] + body + s[b:]

# calls in tempo_main before the final update pass them; after it, qv1d and t1d are final and M1 has already
# exchanged everything at or below r1, so the arguments could not act
ta = re.search(r"^ *subroutine tempo_main\(", s, re.M).start()
tb = s.index("end subroutine tempo_main", ta)
main = s[ta:tb]
fu = re.findall(r"^    ! final update -+\n", main, re.M)
if len(fu) != 1:
    sys.exit(f"ABORT calls: {len(fu)} final-update markers")
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
    out.append(main[pos:i] + f", &\n{m.group(1)}  qvten=qvten, tten=tten, lat_ocp={SPECIES[m.group(2)][1]})")
    pos = i + 1
    while main[pos] == " ":  # trailing blanks after the call would now end the new line
        pos += 1
    ncalls += 1
main = "".join(out) + main[pos:]
# after the final update: one call per species, the PBL-cloud copy and, with hail, the graupel re-check after the
# hail recombination
if ncalls < 2 * len(present) or nskip != len(present) + 1 + ("hail" in present) or \
        len(re.findall(r"_check_and_update\(", s[:ta] + s[tb:])) != len(present) + 1:
    sys.exit(f"ABORT calls: {ncalls} before and {nskip} after the final update; check_and_update also called outside?")

# early return: the entry exchange (in qvten, tten) reaches the state exactly as in the final update
fl = re.findall(r"^      t1d\(k\)  = t1d\(k\) \+ tten\(k\)\*(\w+)\n      qv1d\(k\) = max\(min_qv, \(qv1d\(k\) \+ qvten\(k\)\*(\w+)\)\)\n",
                main, re.M)
if len(fl) != 1 or fl[0][0] != fl[0][1]:
    sys.exit(f"ABORT early return: final update {fl}")
tdt = fl[0][0]
main = one(main, "    if (.not. do_micro .and. .not. supersaturated) return\n",
           "    if (.not. do_micro .and. .not. supersaturated) then\n"
           "      ! the entry checks changed q1d in place and left the matching vapour and heat in qvten, tten\n"
           "      do k = 1, nz\n"
           f"        t1d(k)  = t1d(k) + tten(k)*{tdt}\n"
           f"        qv1d(k) = max(min_qv, (qv1d(k) + qvten(k)*{tdt}))\n"
           "      enddo\n"
           "      return\n"
           "    endif\n", "early return")
er = main.index("    if (.not. do_micro .and. .not. supersaturated) then\n")
pre = main[:er]
# nothing but the entry checks may have written qvten or tten before the return (they are zeroed at the start)
if re.search(r"^\s*(qvten|tten)\(k\) = (?!0\._wp)", pre, re.M) or re.search(r"^\s*(qvten|tten) = ", pre, re.M):
    sys.exit("ABORT early return: other writes to qvten/tten before the return")

# latent heat over cp from the entry state
dcl = "    real(wp), dimension(kts:kte) :: rhon !! density after latent heating, for fall speeds only\n"
main = one(main, dcl, dcl + "    real(wp), dimension(kts:kte) :: lvocp, lsocp !! latent heat over cp, for water sent to vapour\n",
           "locals (run port_tempo_scheme first)")
ent = re.search(r"\n      temp\(k\) = t1d\(k\)\n      qv\(k\) = max\(min_qv, qv1d\(k\)\)\n", main)
if ent is None or main.count("      temp(k) = t1d(k)\n      qv(k) = max(min_qv, qv1d(k))\n") != 1:
    sys.exit("ABORT entry loop")
e = main.index("    enddo\n", ent.end()) + len("    enddo\n")
main = (main[:e] + "\n    do k = 1, nz\n"
        "      lvocp(k) = (lvap0 + (2106.0_wp - 4218.0_wp)*(temp(k) - t0))/(cp*(1._wp + 0.887_wp*qv(k)))\n"
        "      lsocp(k) = lsub/(cp*(1._wp + 0.887_wp*qv(k)))\n    enddo\n" + main[e:])
s = s[:ta] + main + s[tb:]
for name in ("lvap0", "cp"):
    if re.search(rf"^\s*real\b[^\n!]*::[^\n!]*\b{name}\b", main, re.M):
        sys.exit(f"ABORT: {name} is a local in tempo_main")
s = one(s, ", lsub\n  use module_mp_tempo_utils", ", lsub, lvap0, cp\n  use module_mp_tempo_utils", "imports")

# semi-Lagrangian sedimentation: tendency before the floor. Placeholders stay in its transport: there they also
# shape the edge values at the top of a precipitating layer, so leaving them out changes the reconstruction (the
# piecewise-linear safeguard), not only the booking
sl = re.findall(r"^      xr\(k\) = max\(xr\(k\), limit\)\n      xten\(k\) = xten\(k\) \+ \(xr\(k\) - rr_save\(k\)\) \* &\n        orho\*(\w+)\n", s, re.M)
if len(sl) != 1:
    sys.exit(f"ABORT sedimentation: {len(sl)} matches")
s = one(s, f"      xr(k) = max(xr(k), limit)\n      xten(k) = xten(k) + (xr(k) - rr_save(k)) * &\n        orho*{sl[0]}\n",
        "      ! the tendency excludes the floor, which would create water; the floor stays in the transported state\n"
        f"      xten(k) = xten(k) + (xr(k) - rr_save(k)) * &\n        orho*{sl[0]}\n      xr(k) = max(xr(k), limit)\n",
        "sedimentation tendency")

# standard sedimentation: placeholders not transported
a = s.index("subroutine sedimentation(")
b = s.index("end subroutine sedimentation", a)
sd = s[a:b]
if "allocate(sed_r(nz), source=0._wp)" not in sd:
    sys.exit("ABORT sedimentation flux: sed_r not zeroed")
sd = one(sd, "      sed_r(k) = vt(k)*xr(k)\n",
         "      ! inputs at or below limit (placeholders for absent mass) are not transported\n"
         "      if (xr(k) > limit) sed_r(k) = vt(k)*xr(k)\n", "sedimentation flux")
s = s[:a] + sd + s[b:]

f.write_text(s)
print(f"patched {f.relative_to(f.parents[1])}: M5 ({len(present)} routines, {ncalls} calls pass qvten, {nskip} after "
      f"the final update do not; early return on {tdt}; semi-Lagrangian floor; flux-form placeholders)")
