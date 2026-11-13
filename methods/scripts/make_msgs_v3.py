#!/usr/bin/env python3
"""make_msgs_v3.py <msgs dir>: round-3 commit messages. Port and T1 keep their round-2 text (<v>.<i>.r2.txt, written
by make_series3.sh), except 9adf9ef, whose port gains F1 and new numbers; M5 is rewritten for every version from the
template below with that version's measurements (tempo_round3/results_wct*.txt, the red team's harness)."""
import sys
import textwrap
from pathlib import Path

M = Path(sys.argv[1])
AI = "AI-assisted: written with Claude Code (Anthropic); reviewed by the author.\n"


def sub(s, old, new):
    if s.count(old) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(old)}: {old[:60]!r}")
    return s.replace(old, new)


# ---- 9adf9ef: port (F1) and T1 (numbers) ------------------------------------------------------------------------------
p = (M / "9adf9ef.1.r2.txt").read_text()
p = sub(p, """M2  The sedimentation flux out of the lowest layer was counted as surface
    precipitation only above low_limit_mass_for_precip. Count all of it.
""", """M2  The sedimentation flux out of the lowest layer was counted as surface
    precipitation only above low_limit_mass_for_precip. Count all of it.

And one fix of this version's own (v3.0.5 and later already have it):

F1  Standard (flux-form) rain and graupel sedimentation fixed the number of
    substeps from the fall speeds before the loop, then recomputed the fall
    speeds after every substep, so with faster fall speeds a layer could
    lose more than it held. The overdraft became negative condensate that
    the clips filled with created water: up to 3.7 kg/m2 in one call of a
    random column and 1.4e5 kg/m2 in a single graupel layer (dt = 600 s,
    hail-aware). The recomputation is commented out exactly as in v3.0.5,
    so the substeps keep every layer's outflow within its content. This
    changes behaviour with semi_sedi_flag off: the fall speeds stay those
    of the start of the step (as from v3.0.5), and snow, which takes the
    rain fall speed for its boost, sees those too. In the test column below
    the hour's precipitation changes by +2.3e-2 kg/m2 (+7.6e-4) at 20 s and
    +5.6e-3 kg/m2 (+1.8e-4) at 60 s.
""")
p = sub(p, """x 180 / 60 s x 60 steps. Standard sedimentation: 4.2e-5 / 1.1e-3 before,
2.8e-8 / 4.3e-8 after; the remaining residual is water created at up to
2.2e-8 kg/m2 per step, 4.7e-9 per step on average at 20 s and 2.2e-8 at 60
s, which the third commit removes.""", """x 180 / 60 s x 60 steps. Standard sedimentation: 4.2e-5 / 1.1e-3 before,
2.9e-8 / 4.3e-8 after; the remaining residual is water created at up to
2.2e-8 kg/m2 per step, 4.8e-9 per step on average at 20 s and 2.2e-8 at 60
s, which the third commit removes.""")
p = sub(p, """  that the intermediate checks then deleted; in this version the call's
  residual stays at 0.14 kg/m2 at this stage, dominated by the intermediate
  checks' deletions that the third commit removes, and the cap takes 9.1e-4
  kg/m2 of it.""", """  that the intermediate checks then deleted (water created); with the cap
  the call's residual is 3.2e-9 kg/m2, the level the third commit removes.""")
(M / "9adf9ef.1.txt").write_text(p)
t = (M / "9adf9ef.2.r2.txt").read_text()
t = sub(t, "as with standard sedimentation (2.8e-8\n/ 4.3e-8).", "as with standard sedimentation (2.9e-8\n/ 4.3e-8).")
(M / "9adf9ef.2.txt").write_text(t)

# ---- M5 ---------------------------------------------------------------------------------------------------------------
V = {
    "c62699f": dict(
        hail=True, s2="1.3e-7 / 4.3e-8 (standard)\nand 1.3e-7 / 4.4e-8 (semi-Lagrangian)", s2step="2.3e-8 kg/m2 per step",
        res="7.9e-15", step="5.8e-14",
        dp=("The hour's precipitation against the previous commit: standard -6.8e-7 and\n"
            "+6.1e-5 kg/m2 at 20 and 60 s (the 60 s runs separate at the second\n"
            "step, as with version 2 of this commit); semi-Lagrangian -3.6e-7 and\n"
            "-1.9e-3 kg/m2 (-6.3e-5), where 1e-14 to 1e-9 relative perturbations of\n"
            "the initial vapour move the previous commit by -8.4e-9 to +2.8e-7 and\n"
            "-2.2e-3 to 0 kg/m2."),
        fuzz="2.0e-13", i29=True),
    "2856696": dict(
        hail=False, s2="1.3e-7 / 4.3e-8 (standard)\nand 1.3e-7 / 4.4e-8 (semi-Lagrangian)", s2step="2.4e-8 kg/m2 per step",
        res="6.3e-15", step="7.3e-14",
        dp=("The hour's precipitation against the previous commit: standard -2.5e-7 and\n"
            "-8.9e-8 kg/m2 at 20 and 60 s; semi-Lagrangian -4.1e-4 and -5.2e-4 kg/m2\n"
            "(-1.3e-5, -1.7e-5), where 1e-14 to 1e-9 relative perturbations of the\n"
            "initial vapour move the previous commit by -4.6e-4 to +5.6e-7 and -3.2e-4\n"
            "to +3.4e-4 kg/m2."),
        fuzz="2.1e-13", i29=True),
    "881614f": dict(
        hail=False, s2="1.3e-7 / 4.3e-8 (standard)\nand 1.3e-7 / 4.4e-8 (semi-Lagrangian)", s2step="2.4e-8 kg/m2 per step",
        res="3.9e-15", step="5.9e-14",
        dp=("The hour's precipitation against the previous commit: standard -1.1e-6 and\n"
            "-8.9e-8 kg/m2 at 20 and 60 s; semi-Lagrangian +6.9e-5 and -5.3e-5 kg/m2\n"
            "(+2.3e-6, -1.7e-6), where 1e-14 to 1e-9 relative perturbations of the\n"
            "initial vapour move the previous commit by 0 to +6.7e-5 and -2.9e-7 to\n"
            "+8.2e-4 kg/m2."),
        fuzz="2.1e-13", i29=False),
    "9adf9ef": dict(
        hail=False, s2="2.9e-8 / 4.3e-8 (standard)\nand 3.0e-8 / 4.4e-8 (semi-Lagrangian)",
        s2step="2.4e-8 kg/m2 per step (on average\n4.8e-9 at 20 s and 2.2e-8 at 60 s)",
        res="2.9e-15", step="5.4e-14",
        dp=("The hour's precipitation against the previous commit: standard -1.4e-7 and\n"
            "-8.9e-8 kg/m2 at 20 and 60 s; semi-Lagrangian at 60 s -1.6e-4 kg/m2\n"
            "(-5.1e-6), where 1e-14 to 1e-9 relative perturbations of the initial\n"
            "vapour move the previous commit by -1.6e-7 to +6.4e-4 kg/m2.\n"
            "Semi-Lagrangian at 20 s: +0.17 kg/m2 (+5.6e-3), far outside the\n"
            "range (+-1.2e-2 kg/m2) but not specific to this commit: the run shifts\n"
            "as far with the exchanges alone (+5.1e-3) or the floor payment alone\n"
            "(+5.8e-3), and by +1.6e-2 when instead 1e-9 K is added to (or taken\n"
            "from) every level at every step. That run is this sensitive to any change\n"
            "that persists from step to step; version 2 of this commit moved it by\n"
            "+5.2e-3."),
        fuzz="2.1e-13", i29=False),
}

TEMPLATE = """TEMPO: water at or below r1 goes to vapour instead of being deleted

Each hydrometeor *_check_and_update routine, when q1d + qten*dt <= r1,
overwrote qten so the species ended the step at zero. What was left was
deleted, or created when an overshoot had left it negative. Give the
routines optional qvten, tten and lat_ocp arguments and move that amount to
vapour with its latent heat before the overwrite. Every call in tempo_main
up to the final update passes them, with latent heat over cp from the entry
state (lvap for cloud and rain, lsub for {ice_list}), including the
checks between semi-Lagrangian substeps. The calls after the final update
do not: qv1d and t1d are final there, and the clip exchange (M1, first
commit) has already moved everything at or below r1. Nor does the
diagnostic copy of cloud plus PBL cloud used for the effective radii. The
routines and M1 also record the vapour they take to fill a negative
(qvneg) and its heating (tneg), for the floor below.

Vapour floor. An exchange can take more vapour than its level holds (a
negative in a dry layer), and the host can pass vapour below min_qv; the
final update then clipped it at min_qv, creating water. Vapour that would
end the step below min_qv is now refilled first from the same layer's
condensate (with its latent heat, numbers scaled with mass), then from the
column's vapour, every level above min_qv giving the same fraction of its
excess, as the vapour floor of fix M1 does in Thompson. Only a column with
no vapour to spare is still floored: that water is created and counted in
tempo_main_diags%vapour_floor_water (kg m-2), and the latent heat of the
negatives it filled is taken back, so heat always matches the water that
actually changed phase. -1e-4 kg/kg of cloud in three dry layers above
rain: the previous commit deleted it at entry (0.127 kg/m2 created);
version 2 of this commit filled it from vapour that was not there (0.25 K
of latent heat, and the clip still created the water); now it is filled
from the column's vapour (0.25 K, nothing created). A column that cannot
pay has every level at or below min_qv: none of 30,880 test calls,
including 3,000 random columns, had one; a constructed one (no vapour,
-1e-6 kg/kg of cloud at two levels) creates 8.7e-4 kg/m2, counted, with no
heat.

Early return (no hydrometeor above r1, not supersaturated). The routines
zero q1d in place at entry and leave the matching vapour and heat in qvten
and tten; those were dropped. They are now applied where they acted, with
the same vapour floor; elsewhere the column is returned exactly as it came.
A column with no tendencies is returned bit for bit, also where the host
passed vapour below min_qv (version 2 of this commit raised it there,
creating 1.24e-3 kg/m2 per call for -1e-6 kg/kg at three levels). A
subsaturated 10-level
column with 5e-13 kg/kg of rain, -1e-8 kg/kg of cloud at one level and
traces of ice, snow and graupel at or below r1: the call created 2.1e-6
kg/m2 of water; now 9e-16.

Semi-Lagrangian sedimentation books in its tendency the r1 floor it applies
to the transported state, which created water. That floor is now condensed
from vapour, with its latent heat ({semi_species} mass; numbers and
graupel volume are not water), and the routine keeps its order. Taking the
tendency before the floor instead (version 2 of this commit) also removes
the floored mass from levels the precipitation has just left, and that mass
is what the fall-speed routines see there: a floored level holds (r1/rho)*rho,
just above or below r1 depending on rounding, and is given its own fall speed
or the one copied from above. Without it the velocity above the precipitation
top was zero and rain and graupel fell slower ({timing}). Now the first
call's precipitation is bit for bit the previous commit's in every
semi-Lagrangian case tested (70 single columns, each also with the initial
vapour perturbed by 1e-15 to 1e-12). Later steps start from states that
differ by the exchanged vapour and so differ by about as much as such
perturbations make the previous commit differ from itself (because of that
rounding edge; on main and v3.0.5 the mean of nine perturbed runs moves by a
median 0.1 of the previous commit's own spread over those cases, against 0.5
to 1 with version 2).

The flux-form sedimentation routine transported every level, including the
r1 and r2 placeholders the check routines leave in empty levels, into which
the fall-speed routines copy the fall speed from above. That mass was booked
as precipitation and paid for from vapour by the exchanges. It now leaves
inputs at or below limit in place (r1-sized changes only: its fall speeds
are fixed for the step).
{hail_para}
Port of ufs-community/ccpp-physics fix M5, which does the same for Thompson
(2e-8 of the precipitation in UFS). In TEMPO's 59-level test column (closure
as in the first commit, gfortran, double precision, 20 s x 180 / 60 s x 60),
after the previous two commits the residual was {s2} of the precipitation,
water created at up to {s2step}; with this commit |sum(W1 - W0 + P)|/sum(P)
is at most {res} with either sedimentation scheme and time step (largest
single step {step} kg/m2, double-precision rounding). {dp}

Over 30,880 one-column calls (adversarial cases: negative, tiny and r1-sized
condensate, dry and supersaturated layers, thin layers and large Courant
numbers, hail-aware on and off; and 3,000 random columns) the largest
residual is {fuzz} kg/m2, from 300-600 s semi-Lagrangian steps whose
remap rounds at that level (the same calls in version 2); no negative
condensate is left, and at every level the latent heat matches the
condensate gained or lost (to 1.2e-4, the temperature dependence of Lv).

""" + AI

HAIL = """
Hail (hyperaware): after hail is split off, the graupel check runs again
on the tendencies the first run left. The first run has already applied
them to qg1d, ng1d and qb1d (and moved what it removed to vapour), so the
second run applied them twice: graupel at or below r1 was turned back into
graupel (-1e-6 kg/kg became +1e-6, 9.5e-4 kg/m2 created in one call), and
the number and volume limits were applied twice. Its tendencies now start
from zero. The split and the hail-graupel recombination also wrote ng1d
and qb1d when they are absent (out of bounds; a crash with bounds checking);
they now leave them alone.
"""

for v, d in V.items():
    timing = ("two-layer rain at 300 s delivered 0.335 instead of 0.441 kg/m2 in its\n"
              "first step; graupel 39 % instead of 98 % of its total by 900 s" if d["i29"] else
              "a single graupel layer at 300 s delivered 48 % instead of 79 % of its\n"
              "total by 900 s")
    m = TEMPLATE.format(ice_list="ice, snow, graupel, hail" if d["hail"] else "ice, snow, graupel",
                        semi_species="rain, graupel and hail" if d["hail"] else "rain and graupel", timing=timing,
                        hail_para=HAIL if d["hail"] else "", s2=d["s2"], s2step=d["s2step"], res=d["res"],
                        step=d["step"], dp=d["dp"], fuzz=d["fuzz"])
    paras = m.split("\n\n")
    out = [paras[0]] + [textwrap.fill(" ".join(q.split()), width=76, break_long_words=False, break_on_hyphens=False)
                        if q.strip() and not q.startswith("AI-assisted") else q.rstrip("\n") for q in paras[1:]]
    (M / f"{v}.3.txt").write_text("\n\n".join(out).rstrip("\n") + "\n")
print("messages written:", sorted(x.name for x in M.glob("*.txt") if not x.name.endswith(".r2.txt")))
