# PR round 1: history

*Verbatim earlier version of `pr_round1.md` (19 October 2026, before the clean-up): the red-team findings with their
evidence, and the job IDs of the cancelled pre-red-team runs. The current plan is `pr_round1.md`.*

---

# PR round 1: the obvious bug fixes

*Plan for the first round of upstream PRs, drawn from the water proposal (`water_closure_proposal.md`, diffs 01–19 +
09b) and the conservation follow-on (`conservation_proposal.md`, series rows in `conservation/replay/SERIES.md`).
Nothing has been posted. Re-cut root on Hercules: `$U/pr1` (`$U` = `/work2/noaa/co2/ash/ufs-chem-v1/upstream`).*

## Status

| Item | State |
|---|---|
| Scope | **38 diffs** after the red team: 16 water (incl. 09b), 21 conservation (incl. PBL05), the TEMPO twin of TH1. R1, TOPT and MYNN moved to round 2 (section "Red team") |
| PRs | 6 ccpp-physics (SAMF + PBL05, Thompson, TEMPO driver, Noah-MP + NM2, sea ice + NSST, GFDL MP v3), GFDL `dev/emc`, NOAA-EMC/noahmp, ufsatm, WM; 2 issues; one baseline change |
| Branches | local, on current heads (WM `develop` f1d68949); every commit carries the AI-assisted trailer; patches `pr_round1_patches/` (76 files) |
| Checks | the new tree = the old minus exactly R1, TOPT, MYNN; 15 of 15 group pairs merge; each group alone on `develop`: v1 groups compiled, v2 groups running (job 10170333) |
| Regression | official run on `rt2` (job 10170334, own node) and reproducibility pair on `rtc2` (10170320 → 10170335) running |
| Waiting upstream | open after ccpp-physics#390 and #389 merge; resolved rebases prepared (`prep-samf-on390`, `prep-tempo-on389`) |
| Descriptions | `pr_round1_descriptions.md`; round-2 issue drafts (9) in `round2_issues.md` |
| Posted | nothing |

## Rule for round 1

A change is in round 1 only if all four hold:
1. the code plainly does not do what it intends (wrong denominator, double count, wrong units, a step taken twice, a
   phase change with no latent heat);
2. the fix only restores that intent: no new design choice, no new switch;
3. it is unconditional;
4. its forecast impact is at noise (the `consv_te` = 0.999 control), or the change is the bug's own signal.

## Round 1, grouped by PR (code owners)

Numbers: `W01`–`W19` are water diffs (`proposal/patches/`), bare numbers are conservation series rows
(`conservation/replay/patches/`).

| PR | Repository | Fixes | Notes |
|---|---|---|---|
| SAMF + PBL | ccpp-physics `ufs/dev` | SA1 (W01), D3A (07), F3 01a (23), PBL05 (52), SAMF08 (55) | owners @JongilHan66 (+ @lisa-bengtsson for SAMF). D3A adds `hfus`. Open after #390 |
| Thompson | ccpp-physics `ufs/dev` | TH1–TH7 (W02–W07) | TH5 edits `.meta` (`prsi`, already in the hosts) |
| TEMPO driver | ccpp-physics `ufs/dev` | TH1's twin in `mp_tempo` (`ports/TEMPO-driver/0001`) | default owners. Exposes TEMPO's own +0.33 % residual. Open after #389 |
| Noah-MP | ccpp-physics `ufs/dev` + NOAA-EMC/noahmp `develop` | NM1–NM6, NM8 (W08–W13, W15); NM12 (12); NP1 (33); SL2, CS1, CB1 (38–40) | NM2 needs 09b in NOAA-EMC/noahmp (the land component crashes without it); NM12 is NCAR/noahmp#47 |
| Sea ice, NSST | ccpp-physics `ufs/dev` | SI1, SI2, FL1 (31, 32, 36); QR1 (34) | owners @wd20xw, @XuLi-NOAA |
| GFDL MP v3 | ccpp-physics `ufs/dev` | GFDL02, GFDL07 (49, 54) | owner @RuiyuSun |
| FV3 | GFDL_atmos_cubed_sphere `dev/emc` | FX1, SG1, CP1, FV2, INLQ (01, 02, 03, 05, 29); FV1 (W19) | no CODEOWNERS; independent of the rest |
| Build | NOAA-EMC/ufsatm `develop` | SAMF32 (25) + submodule bump | tag @rhaesung (author of ufsatm#1133, also a ccpp-physics code manager); changes answers in the `_conv32` tests |

## Held: bugs whose fix needs owner judgement (round 2, issue first)

| Fix | Reason |
|---|---|
| T1 02b (27) | SAMF tracer Courant numbers up to 5 is a bug; the 426-line sub-stepping fix moves o3 and TKE (9–13 of 72 cells outside a 4-member spread, 3.6 expected) |
| TH8 + TH9 (43) | Right for Thompson; at noise only with E2, so it travels with E2 |
| E2 `noahmp_fwet_opt` (42) | Bug, switched: canopy evaporation +36 %, land LH +1.2 % |
| NM7 (W14) | Energy–water consistency; CTSM solves it differently, owners choose |
| NM9 (W16) | The 600 mm glacier reset is design; the fix carries a FIXME (ice runoff booked as liquid) |
| NM11 (W18) + CMC (35) | Land over snow changes beyond noise; CMC returns heat through NM11's path |
| NM10 / NM10r (W17 / 17r) | Phase criterion is a physics change |
| GF03 (50) | Bug (a) mixed with consistency (b–d), switched; precipitation +8.9 % |
| DY1–DY3 (45, bits 1, 8, 16) | Red-teamed dycore bugs, but behind `dyn_te_exact` with design bits 32, 64; GFDL decides whether the bug bits go unconditional |
| F3 01b (24) | Deposition export: a feature |
| R1 (04) | Clear bug, but its two new `Radtend` fields must first exist in NCAR/ccpp-scm and ufsatm (ccpp-physics CI runs capgen against both) and the MPAS host (#397) |
| TOPT (26) | Clear bug; overlaps #397's `tend_opt` restructuring, and option 4 → error is a design choice |
| MYNN01, MYNN01b (47, 48) | Clear bugs; #392 replaces `module_bl_mynn.F90` with the NCAR/MYNN-EDMF submodule. Port there after #392 |

## Later rounds: physics changes and options

D1 `dspheat_ke`, D3B, D4/D12, D4n, D7/D7S, C1 (incl. flow work), C8, S1/S1K, PBK, PBF, K1, TFH, DRY, DYN v6,
surface options r3/r4 (CH1/CH2, PH1–PH3, SW1, LW2, EV1, AD1, KF1, EP1 + PL1, AIR1), E1, MYNN04, MYNN06,
`dyn_te_exact` bits 32/64, MPAS 0012/0014. Decided settings: `conservation_proposal.md` section 15.

## Re-cut

Base: fresh `ufs-community/ufs-weather-model` `develop`, recursive (`$U/pr1/ufs-weather-model`, cloned 19 October),
kept pristine; the patched copy is `$U/pr1/r1` (`apply_r1.sh`, `recipe_r1.txt`, log `apply_r1.log`). Every pin
equals its branch head, so diffs cut from `r1` against the clone are PR-ready:

| Repository | Branch | Head = WM pin |
|---|---|---|
| ufs-weather-model | `develop` | f1d68949 (2026-10-16) |
| NOAA-EMC/ufsatm | `develop` | aa0ba811 (2026-10-16) |
| ufs-community/ccpp-physics | `ufs/dev` | d9b70feb (2026-10-15) |
| NOAA-GFDL/GFDL_atmos_cubed_sphere | `dev/emc` | 71ff473b (2026-08-05) |
| NOAA-EMC/noahmp | `develop` | 2c7b3bc2 (2025-10-29) |

The water series was cut on ccpp-physics 242a2fc0 and the conservation series on WM 112b1d46.

Apply order (water before conservation, series order within each):
W01 W02 W03 W04 W05 W06 W07 W08 W09 W10 W11 W12 W13 W15 W19 (+ 09b in NOAHMP-interface), then
01 02 03 04 05 07 12 23 25 26 29 31 32 33 34 36 38(as cut) 39 40 47 48 49 52 54 55.

Apply (`$U/pr1/apply_r1.log`): 40 of 41 at -F0 with no fuzz; the Noah-MP rows 12, 33, 38–40 apply although they
were cut on top of the held NM7, NM9–NM11. SAMF08 (55) hunk 1 needs fuzz 1: its context has `trcmax`, from the held
T1 (27); the hunk only adds `logical caon(im)`.

**Branches** (`$U/pr1/series`, local only; built by `mkseries_r1.sh`, regrouped by `rebuild_r1b.sh`; the
pre-red-team branches are kept as `v1-*`):

| Repository | Branch | Commits | Contents |
|---|---|---|---|
| ccpp-physics | `pr1-round1` | 30 | every round-1 fix |
| ccpp-physics | `pr1-samf`, `-thompson`, `-tempo`, `-noahmp`, `-seaice_nsst`, `-gfdlmp` | 5, 6, 1, 12, 4, 2 | one PR each, cherry-picked onto `ufs/dev` |
| ccpp-physics | `prep-samf-on390`, `prep-tempo-on389` | 5, 1 | the same, replayed onto `ufs/dev` + #390 / #389 with the one conflict each resolved (`resolve_prep.py`) |
| GFDL_atmos_cubed_sphere | `pr1-round1` | 6 | FX1, SG1, CP1, FV2, INLQ, FV1 |
| ufsatm | `pr1-round1` | 2 | SAMF32, submodule bump |
| NOAA-EMC/noahmp | `pr1-round1` | 1 | 09b |
| ufs-weather-model | `pr1-round1` | 1 | submodule bump (`.gitmodules` still upstream: no forks yet) |

Every commit: author and committer `Ash Pera <ashley.pera@noaa.gov>`; message = defect, fix, measured effect (W01–W13,
W15 from `git/ufs-dev/all`, W19 from the FV3 series, the rest in `$U/pr1/msgs/`), ending
`AI-assisted: written with Claude Opus 5.5; reviewed by author`.

**Checks.**

| Check | Result | Can fail |
|---|---|---|
| Patched tree = series (`diff -r`) | `r1` = v1 series (before TEMPO); `rt2`, `rtc2` = series | pristine vs `r1`: 28 files |
| Regrouping drops exactly R1, TOPT, MYNN | v1 `pr1-round1` with those 4 commits reverted = new `pr1-round1` | v1 vs new: differ |
| Each ccpp-physics group picks onto `ufs/dev` alone | 6 of 6 | — |
| Any merge order (`mergetest/`) | 15 of 15 pairs clean; all six merged = `pr1-round1` | — |
| Against open upstream PRs (merged onto `ufs/dev` first) | #390 conflicts with SAMF, #389 with TEMPO (one block each, resolved in `prep-*`); #397, #399 clean; #381, #392, #359 conflict with `ufs/dev` themselves | — |
| Message rewrites change no code | every branch tree identical to its pre-rewrite backup (`orig-`, `em-`, `m4-`, `tr-`); every branch on the upstream head | — |
| Pointers | ufsatm → ccpp-physics and FV3 heads; WM → ufsatm and noahmp heads | — |
| Compile, all fixes (v1, job 10164440) | rc 0: `atm_dyn32_conv32` suites + HRRR/GF with `-DSAMFCNV_32BIT=ON`; `atml` with 09b | — |
| Compile, each PR alone on `develop` | v1 groups (job 10169904): samf, thompson, noahmp, nm2, seaice_nsst, mynn rc 0, rest running; v2 groups samf, tempo, noahmp (`atml` + 09b), ufsatm alone (`-DSAMFCNV_32BIT=ON`): job 10170333 | — |
| Regression, official log | job 10170334 on `rt2`, pinned to `hercules-dtn-2`: full `rt.sh -a co2 -e`, Intel + GNU, no `-c`, vs `develop-20261008` | — |
| Reproducibility (`rt.sh -c`, then `-m`) | on `rtc2`: baselines job 10170320 (`hercules-dtn-1`), compare job 10170335 (after it, not on `dtn-2`) | — |

- **ecflow**: `rt.sh` puts its server on the job's node at port uid + 1500, so two runs on one node collide (the first
  `rt_final2`, 10170319, exited in 12 s). Concurrent runs need different nodes.
- **Disk**: the cancelled v1 runs (`rt_r1` 1.6 TB, `rt_final`, `rt_repro`) were deleted; co2 was at 669.2 of 677.2 TiB.
- **SAMF32 changes answers in the `_conv32` tests**: with the fix SAMF really is single precision there.
- **TEMPO**: the driver fix uncovers TEMPO's own scheme residual (+0.33 % of grid-scale precipitation in
  `control_p8_ugwpv1_tempo`), which the driver error cancelled; the scheme fixes are proposed to NCAR/TEMPO,
  unmerged. TH5's twin (`ports/TEMPO-driver/0002`) is not included: not measured alone in UFS, adds a `.meta` argument.
- **Backups and scratch** on Hercules: `cut_labels/`, `mergetest/`, `grp/`, `r1`, `rt1`, `rtc`; branches `v1-*`,
  `orig-*`, `em-*`, `rw-*`, `m4-*`, `tr-*`.

## Red team (19 October): least work for the code owners

All eight findings applied 19 October (3 and 7 wait for #390 and #389 to merge). Checked against upstream on 19 October (open PRs, CI workflows, host metadata, CODEOWNERS). Evidence in
`$U/pr1/mergetest/` (trial merges) and the scratch copies of the SCM and ufsatm host metadata.

**Blocking findings**

| # | Finding | Evidence | Fix (our work, not theirs) |
|---|---|---|---|
| 1 | **R1 fails ccpp-physics CI.** CI runs capgen against NCAR/ccpp-scm `main` and NOAA-EMC/ufsatm `develop`, not our PRs. R1's two new names (`air_pressure_difference_between_interfaces_on_{sw,lw}_radiation_timestep`) are in neither host. Every other new name is present (or framework-provided: `ccpp_loop_counter`) | `ci_scm_ccpp_capgen.yml`, `ci_ufsatm_ccpp_capgen.yml`; host `.meta` grep | Hold R1 for round 2 with an NCAR/ccpp-scm PR and the ufsatm fields merged first (and MPAS host, #397) |
| 2 | **MYNN PR is overtaken.** ccpp-physics#392 (open, changes requested) deletes `module_bl_mynn.F90` (7,746 lines) for the NCAR/MYNN-EDMF submodule and rewrites the wrapper | PR file list | Hold MYNN; port to NCAR/MYNN-EDMF + the new wrapper after #392, with @joeolson42 / @XiaSun-Atmos |
| 3 | **Two approved PRs conflict with ours**: #390 (SAMF, @lisa-bengtsson) in `samfdeepcnv.f`; #389 (TEMPO merra2, @AndersJensen-NOAA) in `mp_tempo.F90`. One small block each | trial merges onto `ufs/dev` + PR | Open after they merge; rebase ourselves. #389's block: apply the mass-basis fix to `merra2_aerosol_aware` too |
| 4 | **TOPT overlaps a code manager's draft**: #397 (MPAS coupling, @dustinswales) restructures the same `tend_opt` cases in `GFS_GWD_generic_post`; and option 4 → CCPP error is a design choice | trial merge; 33-line block | Hold TOPT for round 2, coordinated with #397 |

**Split changes that cut owner and code-manager work**

| # | Change | Why |
|---|---|---|
| 5 | **Merge NM2 into the Noah-MP PR** | same owners (@barlage @cenlinhe); one PR fewer; the noahmp companion is needed by the WM PR either way |
| 6 | **Move PBL05 into the SAMF PR** | `satmedmfvdifq` is @JongilHan66's, as SAMF; removes the interstitials PR once R1 and TOPT are held |
| 7 | **TEMPO driver as its own small PR**, after #389 | it exposes TEMPO's own +0.33 % residual (fixes unmerged at NCAR/TEMPO); in the Thompson PR it would hold Thompson hostage. `mp_tempo` has only default owners |
| 8 | **ufsatm PR = SAMF32 + submodule bump** (R1's typedefs leave) | tag the author of ufsatm#1133 (merged 1 October), whose option SAMF32 makes work; answers change in the `_conv32` tests |

Result: 6 ccpp-physics PRs (SAMF + PBL05, Thompson, TEMPO driver, Noah-MP + NM2, sea ice + NSST, GFDL MP v3) instead
of 8, plus GFDL, noahmp, ufsatm and WM PRs and 2 issues; one baseline change.

**Smaller points**
- **Sequencing**: GFDL `dev/emc` merges rarely (last 5 August); the FV3 PR is independent and must not block the WM
  PR. The WM PR can drop any stalled subcomponent PR.
- **Verifiability**: reviewers cannot run our meters. Each description row should be checkable by reading (the
  commit messages do this); keep effects in plain units.
- **Cost**: the v1 regressions (10164467, 10169990, 10170109/10) were cancelled and rerun on the reduced tree.

## Procedure

Sources (read 19 October 2026): the WM wiki pages *Making Code Changes in the UFS Weather Model and Its
Subcomponents*, *Expectations for Developers* and *Testing Expectations & Commit Queue* (both edited 2026-10-05); the
PR templates of each repository; the CCPP Technical Documentation, *Code Management*.

**Order.**
1. A ufs-weather-model issue. Every PR must link at least one.
2. PRs from forks, lowest repository first: ccpp-physics `ufs/dev` (and GFDL `dev/emc`, NOAA-EMC/noahmp
   `develop`), then NOAA-EMC/ufsatm `develop`, then ufs-weather-model `develop`. The ufsatm and WM PRs point
   `.gitmodules` at our fork branches while open; the last commit before merge restores `.gitmodules` and sets the
   merged hashes. CI (`tests/ci/repo_check.sh`) fails if a submodule branch is behind its authoritative head.
3. The WM PR lists every sub-PR under "Sub component Pull Requests".
4. All three merge the same day, bottom up, after WM testing.

**What we run.** Full `./rt.sh -a co2 -e` on the latest code, Intel and GNU, on Hercules ("acceptable
alternative" to Ursa), **without `-c`**. Commit `tests/logs/RegressionTests_hercules.log` and
`tests/test_changes.list` (even if empty). Baseline failures are expected for answer changes; we judge them.
`BL_DATE` is 20261008. Code managers make the baselines and run the other machines (Jenkins `*-RT` labels).

**WM template.** Description; commit-message tree; priority; Git Tracking (issue, sub-PRs, blocking PRs);
documentation; Regression Test Changes (**Updates/Changes Baselines**); input data; subcomponent branch changes;
library changes; the Commit Queue checklist. **GenAI disclosure**: "Yes. [tool] was used…", with a sub-box that the
code "has been reviewed, edited, and validated by NWS staff"; unchecked, OMD code managers review it.

**Other templates.** ccpp-physics: description, tests (may point to the WM PR), dependencies, documentation.
ufsatm: description incl. whether answers change, testing, dependencies. GFDL `dev/emc`: description / Fixes #,
how tested, a 6-item checklist; fork and issue first. NOAA-EMC/noahmp: no template.

**Labels** (set by code managers): `CCPP`, `UFSATM`, `NMP`, `Baseline Updates`; then `Ready for Review` (2+
approvals) → `Ready for Commit Queue` → `In Testing` → merge. Queue: priority, then oldest first (Project 70).

**Approvals.** WM 2 (enforced); ufsatm 2 observed; ccpp-physics 3 observed (code owners + code managers).

**Reviewers** (ccpp-physics `CODEOWNERS`; each line adds @grantfirl @rhaesung @Qingfu-Liu @dustinswales):
SAMF @JongilHan66 @lisa-bengtsson; Thompson @gthompsnWRF @RuiyuSun @AndersJensen-NOAA; GFDL v3 @RuiyuSun;
Noah-MP @barlage @cenlinhe; CICE @wd20xw; NSST @XuLi-NOAA; `satmedmfvdifq` @JongilHan66; `mp_tempo` default only. ufsatm and noahmp have no
effective CODEOWNERS; the WM has `@ufs-community/ufs-wm-gatekeepers`.

**Not ours.** DTC ports merged `ufs/dev` changes to NCAR/ccpp-physics `main` (about 5 weeks later).

**Timing.** Recent answer-changing chains: FRAM (ccpp-physics#387 → ufsatm#1137 → WM#3351), about 6 weeks;
SAMF single precision (ccpp-physics#384 → ufsatm#1133 → WM#3341), 5 weeks.

**Not verified.** Branch-protection review counts on ccpp-physics and ufsatm; whether contributors can set `*-RT`
labels. The wiki's label section is stale and disagrees with the template on Derecho.

**Our round as WM chains.** Each chain is one baseline change, so bundling matters: separate ccpp-physics PRs per
owner, one ufsatm/WM chain, the GFDL and noahmp PRs riding in it: one regression run, one baseline change. Nothing is posted without Ash's approval.

## Superseded checks (moved from the head, 20 October 2026)

Replaced by the 37-fix regression and reproducibility rows.

| Check | Result | Can fail |
|---|---|---|
| Regression vs `develop-20261008`, the 38 (10170334, `rt2`) | 15 pass; 180 baseline not identical (answers change, expected); 29 unable to start (restart children of changed parents); 10 did not complete: the HAFS crash, 7 `/work2` I/O errors staging inputs, 2 lost Slurm-controller contacts | the HAFS crash |
| Reproducibility, the 38 (`rtc2`: `-c` 10170320, then compare 10170335) | 225 of 234 bitwise; 8 did not complete (the HAFS crash, 7 `/work2` I/O errors); 1 missing baseline (MPI library load failure in the `-c` run) | — |
| Regression and reproducibility, the 38 + SAMFCFL (option-A data) | cancelled; partial logs in `rt_logs_samfcfl/partial/` | — |

## Status before the track split (moved from the head, 20 October 2026)

The head's status table when round 1 was one bundle (one WM PR, one baseline change), just before it was split into
tracks 1a, 1b, 1c.

| Item | State |
|---|---|
| Scope | **37 fixes**: 15 water (incl. 09b), 21 conservation (incl. PBL05), the TEMPO twin of TH1. SA1 (W01) held |
| PRs | 6 ccpp-physics, GFDL `dev/emc`, NOAA-EMC/noahmp, ufsatm, ufs-weather-model; 2 issues; one baseline change |
| HAFS crash | a pre-existing SAMF instability (see *HAFS crash*); SA1 raised its rate 1.7× and is held, with our cap, for the SAMF issue (descriptions §8). The 37 run at develop's rate, no crash |
| Branches | local on current heads (WM `develop` f1d68949), one commit per fix, AI-assisted trailer on every commit |
| Checks | every PR compiles alone on `develop` and merges in any order; the 37's regression changes answers only (no test fails to run); reproducibility bitwise (see *Checks*) |
| Open | regional precipitation moves 2–9 % in 8 Thompson/MYNN tests (36× noise); the Thompson PR alone gives all of it (`attr/attr_table.txt`); `a55b6faa` carries it; its three parts running (`attr/c2a`–`c2c`). all 188 changed tests screened |
| Waiting upstream | SAMF PR after ccpp-physics#390, TEMPO PR after #389; resolved rebases prepared |
| Hold-outs | R1, TOPT, MYNN and the owner-judgement bugs: `round2_issues.md` |
| Posted | nothing |

## Single-bundle ufsatm and WM PR drafts (moved from `pr_round1_descriptions.md` §6–§7, 20 October 2026)

The one ufsatm PR and one WM PR for all 37 fixes, before the split into tracks. Headings demoted.

#### 6. NOAA-EMC/ufsatm PR (base `develop`)

#### Description
- `ccpp/CMakeLists.txt`: `-DSAMFCNV_32BIT=ON` (#1133) compiled 2 of SAMF's 5 files single precision: the filter
  searched the scheme files only, and `mo_conv_kind.F90`, `progsigma_calc.f90`, `progomega_calc.f90` are capgen
  dependencies, so `conv_wp` stayed 8-byte. Now all 5; configure stops if only some are found. @rhaesung
- Updates `ccpp/physics` and `fv3/atmos_cubed_sphere` for the round-1 bug fixes.

Answers change: the physics fixes everywhere, and SAMF is now really single precision in the `_conv32` tests.

#### Issue(s) addressed
- ufs-community/ufs-weather-model#TBD

#### Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD. Baselines change.

#### Dependencies
ufs-community/ccpp-physics#TBD (×6), NOAA-GFDL/GFDL_atmos_cubed_sphere#TBD

---

#### 7. ufs-weather-model PR (base `develop`)

*To split by track (7a, 7b, 7c) once each track's RT is run; the text below is the single-PR draft for all 37.*

#### Commit Queue Requirements:
- [x] This PR addresses a relevant WM issue: #TBD
- [ ] All subcomponent pull requests (if any) have been reviewed by their code managers.
- [x] Run the full Intel+GNU RT suite (compared to current baselines) on Hercules.
   - [x] Commit log file w/full results from RT suite run.
   - [x] Verify that `test_changes.list` indicates which tests, if any, are changed by this PR.
- Transparency in the use of generative AI is required by NOAA policy. Was GenAI used in this work?
   - [x] Yes. Claude Opus 5.5 (Anthropic) was used to assist with developing this code.
     - [ ] The code has been reviewed, edited, and validated by NWS staff.
- [x] Fill out all sections of this template.

#### Description:
37 independent, answer-changing bug fixes that remove water, energy and tracer-mass errors in the P8 physics and the
FV3 coupling. Each fix is one commit in its subcomponent, with the defect, fix and measured effect in the commit
message. Largest effects: Noah-MP steps coastal land twice with `frac_grid` (land gains 3–5 % of global
precipitation); Thompson's humidity conversion removes 0.4 % of grid-scale rain; `control_p8_mynn` depends on the
decomposition. `hafs_global_1nest_atm` has a pre-existing SAMF instability (ufs-community/ccpp-physics#TBD); these
fixes leave its rate at develop's.

#### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes (water, energy, tracer mass); update UFSATM and NOAHMP
  * UFSATM - SAMFCNV_32BIT compiles all SAMF files single precision
    * ccpp-physics - Bug fixes in SAMF, satmedmfvdifq, Thompson, TEMPO driver, Noah-MP, sea ice, NSST, GFDL MP v3
    * atmos_cubed_sphere - consv_te weight, fv_sg energy, physics coupling mass, prsl constants, inline_q damping
  * NOAHMP - CCPP driver copy accepts the optional iter argument
```

#### Priority:
- [x] Normal

#### Git Tracking
#### UFSWM:
* Closes #TBD

#### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * ccpp-physics: ufs-community/ccpp-physics#TBD (SAMF + PBL), #TBD (Thompson), #TBD (TEMPO driver), #TBD (Noah-MP),
    #TBD (sea ice, NSST), #TBD (GFDL MP v3)
  * atmos_cubed_sphere: NOAA-GFDL/GFDL_atmos_cubed_sphere#TBD
* NOAHMP: NOAA-EMC/noahmp#TBD

#### UFSWM Blocking Dependencies:
- [x] None

#### Documentation:
- [x] Documentation update NOT required.
   - Explanation: bug fixes; no new options.

---
#### Changes
#### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. 188 tests change answers; `test_changes.list` has 217 (with the 29 restart children).

#### Input data Changes:
- [x] None.

#### Subcomponent Branch Changes
- [x] No

#### Library Changes/Upgrades:
- [x] No Updates
