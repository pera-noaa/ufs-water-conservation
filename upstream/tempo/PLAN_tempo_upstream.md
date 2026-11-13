# TEMPO upstream path (answer to Anders, #407, 13 Nov 01:38Z)

**Status (13 November 2026).** #407 carries both TEMPO driver fixes (TH5 added, RT subset passed). NCAR merged the
fallback sign (NCAR/TEMPO#61) and its own form of the graupel re-close (#62) into `tempo_v3.3.0`, so steps 3–4 below
are overtaken: what is left is a density-only PR against `tempo_v3.3.0` (`pr_tempo_density.md`, branch
`entry-density-v330`, measured in `PREREG_tempo_v330.md`), posted 13 Nov as NCAR/TEMPO#63. Cloud settling and r1 leftovers
wait for Thompson's follow-up (phase 1), as there.

## Why this split

The four #406 fixes map onto TEMPO by where the code lives, not by PR:

| #406 fix (Thompson) | TEMPO counterpart | Lives in | Vehicle |
|---|---|---|---|
| mass basis | `mp_tempo.F90` conversions | ccpp-physics | #407 (done) |
| layer depth | `mp_tempo.F90` (TH5): `dz` from `prsi`, every inner step | ccpp-physics (TEMPO's inner loop is in `mp_tempo`) | #407, added |
| graupel re-close (+ snow-gain cap) | `tempo_main` C2 | NCAR/TEMPO | new PR |
| density for sedimentation | `tempo_main` C3 | NCAR/TEMPO | same PR |
| — | fallback sign T1 (`qpi(k) > 0`, L1911, inverted in v3.0.0) | NCAR/TEMPO | own issue (+ one-line PR if asked) |

- TH5 is the form Anders asked for on #406 L720 ("keep dz … calculated from dm"): the driver computes `dz` per inner
  step, no interface change, because the inner loop is in the driver.
- T1 is separate: it is TEMPO's largest leak (creates ≈0.6 % of precipitation) and fixing it lowers precipitation ≈5 %.
  v3.2.x hail tuning (#49, #53) was done with the inverted sign, so whether and when to fix it is Anders' call.

## Facts checked (13 Nov)

- ufs/dev 7ab37e41 pins `tempo_v3` = NCAR/TEMPO `main` c62699fb (no newer commits). `mp_tempo` calls
  `module_mp_tempo_driver` from that submodule; the in-repo `module_mp_tempo.F90` is the v2 copy.
- #407 is `mergeable=false`: ufs/dev changed `if (is_aerosol_aware)` to `… .or. merra2_aerosol_aware` beside our lines
  (mp_tempo L451 at base 9b65688c). Only conflict. ccpp-physics convention is to merge ufs/dev in (Lisa to #403).
- Our measurements (`results.md`) are at the old UFS pin 2856696. c62699fb is 7 commits on: `tempo_main` +529/−132
  (hail physics, v3.2.x). So C2/C3/T1 must be ported (check hail terms in the graupel re-close) and re-measured.
- NCAR/TEMPO: CODEOWNERS Anders + dustinswales; Anders merges. CI builds and runs unit tests and the MPAS column test;
  `test/tests.F90` has no stored answers, so answer-changing fixes pass. Open #57 (draft GPU port, +6532/−3486)
  carries the same lines; #41 (graupel density prefactor) conflicts with main; neither touches C2/C3/T1 sites.
- No pera-noaa/TEMPO fork yet.
- To check during the port: whether TEMPO has Thompson's `prg_rcg` exposure (`issue_thompson_prg_rcg.md`).

## Steps

1. Reply to Anders on #407 (`reply_407_tempo.md`).
2. #407: merge ufs/dev into `pr1-tempo` (resolve the one line), add TH5 as one commit. Gate: diff vs ufs/dev = the
   mass-basis lines + TH5 only; known-bad (a stray edit) caught. Test on Hercules: compile, the TEMPO RT tests against
   current develop baselines; meter run C96 `control_p8_ugwpv1_tempo` 24 h, before/after TH5. Push, one-line note.
3. Port C2+C3 (and T1 separately) to c62699fb; fork NCAR/TEMPO; branch per PR. Gates: TEMPO CI build + unit + column
   tests; UFS meter runs at c62699fb with #407+TH5: base, +C2, +C3, +C2+C3, +T1 (5 runs, plus precipitation).
4. Post the NCAR/TEMPO PR (C2+C3) and the T1 issue (from `ncar_tempo_issue.md`, cut to T1, other rows as context).
5. After NCAR/TEMPO merges: the `tempo_v3` hash bump in ccpp-physics (usually Anders/dustinswales).

Budget: ≈ 8 C96 24-h runs + one RT subset, a few node-hours.
