# UFS water and energy conservation: working notes

Working notes, patches and measurements behind a set of conservation bug fixes proposed to the UFS weather model
(ccpp-physics, GFDL_atmos_cubed_sphere, NOAA-EMC/noahmp, NOAA-EMC/ufsatm, ufs-weather-model). Linked from those
issues and pull requests so reviewers can check any number quoted there.

Ash Pera, NOAA GML / CIRES. Work in progress; the notes are a lab notebook, not documentation.

## Status (29 October 2026)

- **Measured** (C96, 24 h, every fix on): total energy closes to 1.6 × 10⁻¹² W/m², passive tracers to 3 × 10⁻¹⁵ per
  day; the water fixes remove +0.25 % of first-day precipitation at C96 (+0.45 % at C384). Restart, decomposition,
  switches-off and passive-meter gates are bitwise ([`conservation/README.md`](conservation/README.md)).
- **Upstream:** 8 ccpp-physics PRs posted (#405–#410, #413, #414), plus NCAR/noahmp#274 and
  GFDL_atmos_cubed_sphere#431. Approved: #405, #406, #408, #414.
- **Packaging:** the code managers want one ufsatm/WM pair per group, so RT baselines change three times, not eight:
  SAMF/PBL, microphysics, Noah-MP. Package 1 is open (NOAA-EMC/ufsatm#1156, ufs-community/ufs-weather-model#3408,
  draft). #408 gains the early-return deletion Lisa Bengtsson and Jongil Han asked for (e5624dd6); its package RT is
  queued on the 20261028 baselines.
- **Waiting on others:** reviewers for #407, #409, #410, #413, the GFDL and NCAR
  maintainers, EPIC (installed Orion/Hercules spack-stack envs).
- Per-item posting state: [`proposal/post/POSTING.md`](proposal/post/POSTING.md).

## Roadmap: what has to be tested and verified

Every upstream change meets one bar before it is proposed: a code-level explanation; a budget meter showing the fix
closes exactly its term; a forecast comparison against the unfixed run showing nothing beyond the defect's own signal,
judged against the `consv_te = 0.999` noise control; and a red team (restart, decomposition, the other suites and hosts
that share the code). Before any ufsatm/WM PR: a full Intel + GNU `rt.sh` on Hercules against current develop
baselines, its log and `test_changes.list` committed on the WM branch. A pre-existing SAMF instability (#401) flips
HAFS tests between crash and no crash under any answer change, so a HAFS failure is checked with five `consv_te`
members on develop and on the change before it is blamed on the change.

### 1. Package 1, SAMF / PBL — #405, #408, #414 (all approved)

| Step | Check | State |
|---|---|---|
| 1.1 | Full RT, #405 + #408 + #414 on develop 783f524a | **done**: 54/54 compile, 122 identical, 95 change, 15 restarts not started, 0 fail (job 10322653) |
| 1.2 | The RT build contains #408 | **done**: `control_p8` differs from the #405 + #414 run (T up to 5.2 K) |
| 1.3 | HAFS 4-nest crash is #401, not #405 | **done**: 5 members each, develop 1 crash, #405 2, either + `xlamue` floor (#414) 0 |
| 1.4 | Lisa's answer on deleting the SAMF early returns | **done**: delete them, in #408 (e5624dd6); bit-identical to the `noret` reference in 48 block tests; rerun 1.1 on develop 560345cc (`rt_sxd2`, queued) |
| 1.5 | Push the package commits, update #1156/#3408 titles and bodies, take #3408 out of draft | after the 1.4 RT (bodies in `proposal/post/bodies_v2/`) |
| 1.6 | If develop moves before the commit queue, or #403 (TTE-EDMF, same SAMF/PBL files) merges first | rebase, rerun 1.1 |

### 2. Package 2, microphysics — #406 (approved), #407, #413

| Step | Check | State |
|---|---|---|
| 2.1 | Reviews of #407 (TEMPO driver) and #413 (GFDL MP v3) | waiting |
| 2.2 | #407 against ccpp-physics#389 (one shared block) | rebase ready; apply if #389 merges first |
| 2.3 | Merge the three PR branches on current `ufs/dev`; full RT | after package 1 merges, on the new baselines |
| 2.4 | Changed tests are only those running Thompson, TEMPO or GFDL MP v3 | compare `test_changes.list` with the suite list |
| 2.5 | HAFS and regional tests: any failure checked against develop with `consv_te` members | with 2.3 |
| 2.6 | Thompson's alternative density/layer-depth form (`thdz/`) | closes to round-off like ours; precipitation within noise globally; kept for a reviewer who asks |

Related, outside the package: the NCAR/TEMPO report #407 promises (draft `proposal/post/tempo_attr/ncar_tempo_issue.md`,
to split into the semi-Lagrangian sign fix and fixes 2–4); GFDL's own MP copy, GFDL_atmos_cubed_sphere#430/#431.

### 3. Package 3, Noah-MP — #409, #410

| Step | Check | State |
|---|---|---|
| 3.1 | Reviews of #409 and #410 (#410 stacks on #409) | waiting |
| 3.2 | Merge both on current `ufs/dev`; full RT | after package 2, on the new baselines |
| 3.3 | Land-coupled and `frac_grid` tests change, nothing else | compare `test_changes.list` |
| 3.4 | NCAR/noahmp#274 (the same snow-heat fix in NCAR's Noah-MP v5) | in review, independent |

### 4. Later rounds (not posted)

| Item | Check before posting | Source |
|---|---|---|
| 1c, FV3 dycore (6 fixes) | WoFS 0.7–2.4× noise; needs `dev/emc` and the #401 answer | [`proposal/pr_round1.md`](proposal/pr_round1.md) |
| 1d, surface iteration, sea ice, NSST (6) | held: crashed `hafs_global_1nest_atm` in 3 of 20 members; rerun those members with the #414 floor | same |
| 1e, Thompson TH2, TH6, TH7 | each has a second reasonable form; post both forms | same |
| Round 2, nine owner-decision issues | each asks one question with a tested patch | [`proposal/round2_issues.md`](proposal/round2_issues.md) |
| Ports (WRF, MPAS, production GFS) | several measured in a model; the rest harness-only | [`proposal/patches/ports/README.md`](proposal/patches/ports/README.md) |
| #403 and #390 (others' PRs) | neither new path conserves; candidate causes identified | [`conservation/upchk/report.md`](conservation/upchk/report.md) |

### 5. Build-environment side track

| Item | State |
|---|---|
| gcc ≥ 12 AVX-512 FPEs in FMS (GCC Bug 128221; NOAA-GFDL/FMS#1937, ufs-community/ufs-weather-model#3406) | `-fno-tree-loop-if-convert` merged for `release/2.2` (JCSDA/spack-packages#103); FMS says to add it to `ReleaseUFS`/`DebugUFS`; cherry-picks for `spack-stack-dev` and spack/spack-packages prepared, not pushed |
| Installed Orion/Hercules spack-stack envs (JCSDA/spack-stack#2144) | repo fixes merged (#2145, #2146); the rest is with EPIC |

### 6. Hercules cleanup (Ash runs the deletes)

Staged, not run: the HAFS member runs (`$U/pr1/hafscheck/`, about 55 GB), the timing runs (`$U/pr1/rettime/run_*`,
about 5 GB), the conservation regression baselines (564 GB) and canopy build trees (4.8 GB). Keep `rt_sxs` until
package 1 merges.

### 7. End goal: conservation checked in CI and the regression tests

Once the fixes are in, keep them in: a change that breaks a budget should fail a test on its own PR, naming the
scheme. Today nothing does this. `rt.sh` checks only that outputs match the baseline bitwise, and ccpp-physics CI only
builds and runs capgen. #403 (TTE-EDMF) and #390 (MLM) both reached review without conserving.

| Stage | What | Needs | When |
|---|---|---|---|
| A | Single-column budget tests in ccpp-physics CI (GitHub runners, no HPC), one per fixed scheme, from our existing standalone drivers (SAMF, Noah-MP, GFDL sedimentation, snow heat) | the scheme's fix merged; owners agree to the test | propose on WM#3404 after package 1 merges |
| B | One RT test: C96 24 h `control_p8` with water and tracer-mass meters and an in-model check that stops the run above tolerance, Intel and GNU | packages 1–3 merged; meters upstreamed | after package 3 |
| C | Energy added to the stage-B test | the dycore and surface rounds merged; agreement on the declared terms (fixer, dissipation heating) | after the later rounds |

What it takes:
- **Meters as maintained code.** Ours are separate instrumentation diffs. They need to be off by default and free when
  off, preferably built on ccpp-physics's existing per-process tendency diagnostics (`dtend`) rather than a new
  framework. Release builds may change answers once when the meter code lands (FMA contraction): one baseline change.
- **Declared terms.** Each scheme states its boundary fluxes (e.g. SAMF moves water only as rain and detrainment). This
  is the main ongoing cost, for us and for every future scheme author, and what makes the check meaningful.
- **Tolerances by precision.** 32-bit dycore builds (HAFS) close water to about 3 × 10⁻⁷ kg/m² per step, 64-bit to
  about 10⁻¹². The RT is bitwise reproducible, so a residual moves only when answers move; a check sized relative to
  round-off does not flicker.
- **A gate that can fail.** Before proposing it, show it failing on current develop and passing with the fixes.
- **Not attached to the current packages:** adding it there would reopen approved PRs.

## Where to start

| File | What |
|---|---|
| `proposal/post/POSTING.md` | upstream posting: every issue and PR, branches, RT results, procedure |
| `proposal/triage_unposted.md` | the fixes not yet posted, triaged: ready, needs a run, needs a decision, parked |
| `proposal/runs_29oct/` | the 29 October checks behind that triage (one report per item) |
| `proposal/pr_round1.md` | round-1 plan: the 37 fixes, the tracks they post in, every check and its result |
| `proposal/pr_round1_descriptions.md` | drafts of the issue and PR texts |
| `proposal/round2_issues.md` | bugs whose fix needs an owner's decision |
| `proposal/water_closure_proposal.md`, `proposal/conservation_proposal.md` | the water and conservation proposals |
| `conservation/TRACKER.md` | status of each conservation study |
| `water_conservation_audit.md` | the original water-budget audit |

`*.history.md` files are archives behind the shorter head files of the same name.

## Layout

- `proposal/`: proposals, round-1 and round-2 drafts, `patches/` (one diff per water fix) and `pr_round1_patches/`
  (`git format-patch` per branch).
- `conservation/<study>/`: one directory per budget study (energy, tracer mass, PBL, convection, surface, …) with its
  report, meters, patches, scripts and logs. `conservation/replay/` holds the patch series.

Copies of patched upstream source trees are not included; the patches reproduce them on the stated upstream commits.
Measurements are from runs on NOAA RDHPCS Hercules and Orion; paths in the notes refer to those systems.

AI-assisted: written with Claude Opus 5.5; reviewed by author.
