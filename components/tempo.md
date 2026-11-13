# TEMPO microphysics (`mp_tempo.F90` in ccpp-physics; `module_mp_tempo_main.F90` in [NCAR/TEMPO](https://github.com/NCAR/TEMPO))

**Status (13 November 2026).** The CCPP driver has Thompson's mass-basis and layer-depth defects, and the scheme
creates +0.377 % of its own precipitation (C96, 6–24 h, TEMPO 2856696), mostly through an inverted fallback test in
semi-Lagrangian sedimentation. Driver: [#407](https://github.com/ufs-community/ccpp-physics/pull/407) approved by
rhaesung, not merged; the layer depth (TH5) was added at 1c664a4f and the TEMPO RT subset passed; it goes in package 2.
Scheme: NCAR merged T1 ([#61](https://github.com/NCAR/TEMPO/pull/61)) and its own form of C2
([#62](https://github.com/NCAR/TEMPO/pull/62)) into `tempo_v3.3.0` (71588d1); C3 is posted as a density-only PR on that
branch ([NCAR/TEMPO#63](https://github.com/NCAR/TEMPO/pull/63)); there it removes 0.15 % (6–24 h, residual −0.34 → −0.19 %; [runs](../upstream/tempo/PREREG_tempo_v330.md#result)). At TEMPO c62699f (UFS's current pin) the base creates
+0.43 %; C2 + C3 leave +0.50 % (C3 removes a sink) and T1 turns it to −0.33 % with 4.3 % less precipitation
([runs](../upstream/tempo/PREREG_tempo_port.md#result)); the per-leak table below is at 2856696. Open: C1 and the r1 leftovers (judgement calls), and
Thompson's `prg_rcg` exposure, which TEMPO c62699f and `tempo_v3.3.0` also have and C2 does not fix.

## Defects and fixes

Percentages are of TEMPO's own grid-scale precipitation, C96 `control_p8_ugwpv1_tempo`, 24 h, with #407. Scheme leaks
are measured leave-one-out (every other fix in) at TEMPO 2856696; [results](../upstream/tempo/results.md).

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| TH1 (driver) | `mp_tempo.F90` converts species to mixing ratio with `1/(1 − q_v)` and back with `1/(1 + r_v)` of the updated vapour, while the host rebuilds mass from the old `q_v`. | develop's round trip hides TEMPO's own creation: net residual +0.18 % before the fix, +0.43 % after, gross column error Σ\|R\|/P 1.85 → 0.93 % (6–24 h, TEMPO v3.2.5); `regional_wofs_tempo` precipitation −1.96 % (noise 0.34 %) | input humidity both ways, as #406 | [#407](https://github.com/ufs-community/ccpp-physics/pull/407) approved | [#407 text](../upstream/posted/PR_TP_407.md), [v3.2.5 runs](../experiments/runs_29oct/tempo_v325.md), [patch](../patches/ports/TEMPO-driver/0001-mp_tempo-convert-to-and-from-mixing-ratio-with-the-s.patch) |
| TH5 (driver) | The driver takes layer depth from `phii`, not the host's layer mass. | removes 0.011 % (6–24 h); ρ·dz vs host mass 4.7e-3 → ≤4.7e-16 (column test); forecast at noise, T and ps rms 1.02× and 0.96× the noise pair (v3.2.5) | `dz` from `prsi` and the entry density, every inner step | [#407](https://github.com/ufs-community/ccpp-physics/pull/407), added after approval (1c664a4f); TEMPO RT subset passed | [plan](../upstream/tempo/PLAN_tempo_upstream.md), [RT gates](../upstream/tempo/PREREG_tp407.md), [patch](../patches/ports/TEMPO-driver/0002-mp_tempo-take-the-layer-depth-from-the-host-s-layer-.patch) |
| T1 | `semilagrangian_sedimentation` falls back to piecewise constant where `qpi(k) > 0` instead of `< 0` (inverted in v3.0.0), and the negative edges it keeps are raised to the floor. | creates ≈ 0.64 % (6–24 h), ≈ 0.72 % (0–6 h); fixing it lowers grid-scale precipitation 5 % | the one-line sign change (Juang and Hong 2010, eq. A4; Thompson's copy) | fixed: NCAR/TEMPO [#61](https://github.com/NCAR/TEMPO/pull/61), in `tempo_v3.3.0` | [issue draft](../upstream/tempo/issue_tempo_t1.md), [results](../upstream/tempo/results.md#red-team-27-oct), [port 0002](../patches/ports/TEMPO-scheme/0002-TEMPO-semi-Lagrangian-sedimentation-falls-back-to-pi.patch) |
| C2 | Graupel gains (`prg_rcs`, `prg_rci`) are not re-closed after the per-term clamps and `check_over_depletion` limit the matching losses. | creates 0.86 % (0–6 h), 0.004 % (6–24 h) | recompute both gains after the limiters; below freezing cap snow's gain at the rain lost | fixed: NCAR/TEMPO [#62](https://github.com/NCAR/TEMPO/pull/62) (NCAR's form, also re-closing graupel volume), in `tempo_v3.3.0` | [PR draft](../upstream/tempo/pr_tempo_c2c3.md), [results](../upstream/tempo/results.md) |
| C3 | `rho` is recomputed from the heated temperature and used by sedimentation while `dz1d` is unchanged, so it implies a different layer mass. | removes 0.120 % (0–6 h), 0.118 % (6–24 h) | keep the entry density; updated density only to `thermo_vars` | [NCAR/TEMPO#63](https://github.com/NCAR/TEMPO/pull/63) open, against `tempo_v3.3.0` | [PR draft](../upstream/tempo/pr_tempo_c2c3.md), [results](../upstream/tempo/results.md) |
| C1 | Cloud water settling out of the lowest layer goes only into `cloud_precip`, which leaves `tempo_main` only through `freezing_rain`; cloud sediments in one step. | removes 0.199 % (0–6 h), 0.137 % (6–24 h) | count it as rain and substep cloud (measured form) | not proposed (judgement call, below) | [report draft, fix 4](../upstream/tempo/ncar_tempo_issue.md), [results](../upstream/tempo/results.md) |
| commit 3 | Water at or below `r1` is deleted in the six `*_check_and_update` routines and the sedimentation floors are raised from nothing. | creates 0.001 % with T1 fixed | pay the leftovers and the floor from vapour | not proposed (judgement call, below) | [results](../upstream/tempo/results.md), [port 0003](../patches/ports/TEMPO-scheme/0003-TEMPO-water-at-or-below-r1-goes-to-vapour-instead-of.patch) |
| `prg_rcg` | Below freezing the graupel check counts the unscaled rain–graupel gain ([L1629](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1629)) after the rain check scaled `prr_rcg` ([L1607](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1607)); the reset comes later ([L1657–1661](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1657-L1661)). | not measured (found by reading the code) | as Thompson: `prg_rcg = −prr_rcg` right after the rain check | not proposed; not covered by C2; still in `tempo_v3.3.0` | [Thompson issue draft](../upstream/issues/issue_thompson_prg_rcg.md), [`thompson.md`](thompson.md) |

## Not proposed, or a judgement call

- **C1, three forms:** count settled cloud as rain and substep it (measured; matches how `freezing_rain` treats it),
  return it as a separate drizzle/fog-deposition output, or do not settle cloud out of the lowest layer. It waits for
  the owners' choice on Thompson's TH2, which has the same two forms.
- **commit 3** is the class of Thompson's TH6/TH7: where sub-`r1` water goes is a choice. Once T1 is fixed it is worth
  0.001 %.
- **C2, other form:** scale snow's gain by the rain limit instead of capping it. Both close to 2e-7; precipitation
  differs by 0.03 %.
- **C3, other form:** with each new `rho`, set `dz1d` from the layer mass and rescale the stored densities. In Thompson
  the two forms differ in precipitation by up to 0.3 % globally and 0.65 % in regional tests.
- **T1 timing:** TEMPO's v3.2.x hail tuning (NCAR/TEMPO [#49](https://github.com/NCAR/TEMPO/issues/49),
  [#53](https://github.com/NCAR/TEMPO/issues/53)) was done with the inverted test, so whether and when to change it is
  the owners' call. Always falling back to piecewise constant also closes, with precipitation −0.6 % against the
  corrected test, so it is not a way to keep v3's precipitation. Red team (24 h C96): tropics −15 to −19 %, rain water
  path +84 %. The draft GPU port ([#57](https://github.com/NCAR/TEMPO/pull/57)) carries the same line.
- **Figures that differ by method:** the T1 issue draft quotes 0.58 % (left out of the build without commit 3) and
  +0.38 % for the base; #407's text quotes +0.33 % from the earlier split meter. All are explained in
  [results](../upstream/tempo/results.md#red-team-27-oct); at c62699f the base measures +0.432 % (1c664a4f).
- **TH8 counterpart** (lowest-layer thresholds) is held for round 2 with Thompson's
  ([`held/TEMPO-scheme/`](../patches/ports/held/TEMPO-scheme/)); TEMPO needs no TH9.
- **Other TEMPO pins** (2856696 for UFS's October pin, 881614f in WRF, 9adf9ef in ufs-community MPAS) and WRF's `rho_dry`
  port are parked until those hosts move their pins ([ports](../patches/ports/README.md)).

## Reproduce

- **Driver patches:** [`TEMPO-driver/`](../patches/ports/TEMPO-driver/) (`ufs/dev`), [`TEMPO-driver-ncar-main/`](../patches/ports/TEMPO-driver-ncar-main/);
  #407's first commit as cut: [`ccpp-physics_tempo/`](../patches/pr_round1_patches/ccpp-physics_tempo/).
- **Scheme patches:** [`TEMPO-scheme/`](../patches/ports/TEMPO-scheme/) (three commits on c62699f; the fork branches
  split C2 + C3 and T1 out of them), the pin ports `TEMPO-scheme-<pin>/`, and the single-fix variants on 2856696
  ([`variants.diff`](../upstream/tempo/variants.diff)).
- **Meter:** `TPW` in `mp_tempo_run`: Σ area·(host-frame column water change + the call's precipitation)
  ([method](../upstream/tempo/results.md#method); general guide [`../methods/METERS.md`](../methods/METERS.md)).
- **Compare against:** the [runs table](../upstream/tempo/results.md#runs) (T0 +0.377 %, all fixes −0.00002 %, 6–24 h)
  and the [v3.2.5 runs](../experiments/runs_29oct/tempo_v325.md) (D7 +0.434 %, D7T5 +0.450 %).
- **c62699f runs:** base, C2, C3, C2 + C3, T1 and TH5's before, with pre-registered gates (all pass) and predictions:
  [`PREREG_tempo_port.md`](../upstream/tempo/PREREG_tempo_port.md#result).
- **RT:** #407 at 1c664a4f (Intel, WM develop 517e02c9, baselines `develop-20261104`): `control_p8_ugwpv1` identical;
  `control_p8_ugwpv1_tempo`, `control_p8_ugwpv1_tempo_aerosol`, `regional_wofs_tempo` run to completion with changed
  answers ([gates](../upstream/tempo/PREREG_tp407.md)). Earlier full `rt.sh` with #406, Intel + GNU: 54/54 compile,
  57 identical, 150 change answers, 25 restart tests not started, none fails ([#407 text](../upstream/posted/PR_TP_407.md)).
  TEMPO CI (build, unit tests, MPAS column test; no stored answers) passes on both fork branches.
