# PR round 1: the obvious bug fixes

*Plan for the first round of upstream PRs, from the water proposal (`water_closure_proposal.md`) and the conservation
follow-on (`conservation_proposal.md`, series rows in `conservation/replay/SERIES.md`). Posted: the SAMF issue
(ufs-community/ccpp-physics#401); nothing else.
Hercules root `$U/pr1` (`$U` = `/work2/noaa/co2/ash/ufs-chem-v1/upstream`). Issue and PR texts:
`pr_round1_descriptions.md`; round-2 issues: `round2_issues.md`; patches: `pr_round1_patches/`.*

## Status

| Item | State |
|---|---|
| Scope | **38 commits** (the 37 fixes; Thompson's TH2 and TH3 now separate) in five tracks (see *Tracks*). Phase 0, fixes with one definite answer: 0a the SAMF issue (posted, #401), 0b global conservation 18, 0c microphysics 5. Phase 1: 1c dycore 6 and 1d surface iteration, sea ice, NSST 6, after the SAMF issue's answer; 1e Thompson 3, fixes with more than one reasonable form. SA1 (W01) held |
| PRs | 7 ccpp-physics (phase 0: 5), GFDL `dev/emc`, NOAA-EMC/noahmp (1d, only with the `iter` form); per track one ufsatm and one ufs-weather-model PR; 3 issues (SAMF, posted; WM; GFDL) |
| Branches | local, one commit per fix on current heads (WM `develop` f1d68949), AI-assisted trailer on every commit. Phase-0 per-track branches built (`post/track_setup.sh`) and pushed to the `pera-noaa` forks (`post/push_forks.sh`); each track's full RT running (0b 10187047, 0c 10187059) |
| Whole round | the 37 together: answers change only, none fails to run, reproducibility bitwise, all 188 changed tests screened (*Checks*) |
| 0b | regional quiet; global: only SAMF + PBL exceeds noise (+0.002 to +0.006 K, measured with NM2), the ice-fusion heat it restores (without NM2: +0.001 to +0.006 K, precipitation −0.27 to +0.29 %). HAFS: without sea ice/NSST 0 of 20 members crash, as develop (HAFS runs Noah, so NM2 never acted there; *HAFS crash*) |
| 0c | TH1, TH3 (graupel), TH4, TH5, TEMPO driver: created water removed: regional precipitation −0.9 to −5.3 % (`regional_control` −1.4 %), WoFS −2.0 % (TEMPO) |
| 1c | WoFS 0.7–2.4× noise; waits on `dev/emc` and the SAMF issue |
| 1e | TH2 (settled cloud water counted, cloud sedimentation substepped), TH6 (clipped condensate to vapour), TH7 (sub-R1 water to vapour): conserving, but each has a second reasonable form; posted with the forms stated |
| 1d | NM2 (Noah-MP stepped once per time step; with its noahmp change in the `iter` form) and the four sea-ice/NSST fixes. Held: 0b with sea ice/NSST crashed `hafs_global_1nest_atm` in 3 of 20 members, the RT member included; no single fix identified (*HAFS crash*). Waits on the SAMF issue; NM2 and SI1 each have two tested forms (*Alternatives*) |
| HAFS crash | a pre-existing SAMF instability (*HAFS crash*): any change to HAFS answers moves its tail. Posted as ufs-community/ccpp-physics#401 (0a; descriptions §8). Han replied (21 Oct): `eta` ≤ 1 below cloud base unless the instability raises TKE; we ran his `eta` ≤ 1 test (*Reply to Han*). Answered 22 Oct ([comment](https://github.com/ufs-community/ccpp-physics/issues/401#issuecomment-6330453096), text `post/reply_401_4.md`): develop crashes 6/10 at 48 h, his test prevents it but leaves CFL-limited cloud-base heating (6 K per step at `dt` 45/90/180), proposes flooring `xlamue` at 0.001·`clamt`; `progsigma` true unaffected. Lisa answered with the run bundle. SA1 is held with it (it raised the event rate 1.7×), with our cap |
| Waiting upstream | TEMPO PR (0c) after ccpp-physics#389, SAMF PR (0b) after #390; resolved rebases prepared. Against #403 (2a95266): F3 01a, PBL05, SAMF08 and SA1 apply cleanly; D3A conflicts in one block, the `samfdeepcnv_run` argument list (`hfus` beside #403's new arguments) |
| Hold-outs | R1, TOPT, MYNN and the owner-judgement bugs: `round2_issues.md` |
| Alternatives | under test: stepping once per time step fixed in the surface loop control (no `iter` arguments, no noahmp PR); Thompson's settled cloud water kept in the air (*Alternatives*) |
| Posted | SAMF issue ufs-community/ccpp-physics#401 (20 Oct; §8, 0a). Nothing else upstream. Working notes public: github.com/pera-noaa/ufs-water-conservation (`../publish/` has the recipe) |

## Rule for round 1

A change is in round 1 only if all four hold:
1. the code plainly does not do what it intends (wrong denominator, double count, wrong units, a step taken twice, a
   phase change with no latent heat);
2. the fix only restores that intent: no new design choice, no new switch;
3. it is unconditional;
4. its forecast impact is at noise (the `consv_te` = 0.999 control), or the change is the bug's own signal.

Phase 0 also needs one definite answer: where a second reasonable form of the fix exists (tested or argued,
*Alternatives*), the fix goes to phase 1 and its PR states both forms.

And, for the least work for code owners: it needs no new host metadata and does not overlap an open upstream
restructuring.

## Tracks

Split by who must accept the answer change and by what changes `hafs_global_1nest_atm`, which sits on a
pre-existing SAMF instability. Each track is its own WM PR, with its own full RT and baseline change, and merges
when its own reviews are done.

| Order | Track | PRs | Fixes | Answer change | HAFS | Reviewers who decide | Before posting |
|---|---|---|---|---|---|---|---|
| 0 | **0a** SAMF issue | ccpp-physics issue (descriptions §8) | — | — | the cause | @JongilHan66 | nothing |
| 0 | **0b** global conservation | SAMF + PBL, Noah-MP (without NM2), GFDL MP v3; ufsatm (SAMF32 + bump); WM | 18 | global: 3-D T +0.002 to +0.005 K, all from SAMF + PBL's ice-fusion heat (the bug's own signal; without NM2 +0.001 to +0.006 K); regional: SAMF + PBL bitwise, Noah-MP ≤ 0.02 % | 0 of 20 crash, as develop | EMC global physics (GFS, HAFS) | track RT |
| 0 | **0c** microphysics | Thompson (TH1, TH3, TH4, TH5), TEMPO driver; ufsatm bump; WM | 5 | created water removed: regional precipitation −0.9 to −5.3 % (`regional_control` −1.4 %), WoFS −2.0 % (TEMPO) | not touched (0b + 1d + FV3 = the 37, bitwise in 10 members) | Thompson/TEMPO owners, RRFS/HRRR | track RT |
| 1 | **1c** dycore | FV3 (GFDL `dev/emc`); ufsatm bump; WM | 6 | WoFS 0.2–0.8 % per commit (0.7–2.4× noise), `cpld_regional_atm_fbh` −1.4 % | FV3 alone 0 of 3; with 0b + 1d = the 37 (1 of 10) | GFDL maintainers, then EMC | `dev/emc` merge; the SAMF issue's answer; track RT |
| 1 | **1d** surface iteration, sea ice, NSST | NM2 (+ NOAA-EMC/noahmp in the `iter` form), sea ice/NSST; ufsatm bump; WM | 6 | global ≤ 0.0008 K, ≤ 0.13 %; regional ≤ 0.7 % (sea ice/NSST); NM2: land no longer gains 3–5 % of global precipitation (the bug's own signal) | with 0b: 3 of 20 crash, RT member included | @wd20xw @XuLi-NOAA, @barlage @cenlinhe, EMC | the SAMF issue's answer; HAFS ensemble on 0b + 1d; the form of NM2 and SI1 |
| 1 | **1e** Thompson, second forms | TH2, TH6, TH7 (`pr1-thompson_p1`); ufsatm bump; WM | 3 | TH2: `regional_control` +10.9 % reported precipitation (settled cloud counted; keeping it in the air instead: +4.8 %); TH6, TH7 ≤ 0.002 % | not touched | Thompson owners | 0c merged; the owners' choice of form |

Every PR compiles alone on `develop`, so the tracks are independent; whichever WM PR merges later takes the earlier
ones' ufsatm and ccpp-physics pointers. The 37's regression (`rt2`, `rt_logs_37/`) is evidence for all four, not a WM
PR log. 1d's separation from 0b rests on 20 members and the RT member passing, not on an identified cause (*HAFS crash*).

## The PRs

`W01`–`W19` are water diffs (`proposal/patches/`); bare numbers are conservation series rows
(`conservation/replay/patches/`).

| PR | Track | Repository | Fixes | Owners | Notes |
|---|---|---|---|---|---|
| SAMF + PBL | 0b | ccpp-physics `ufs/dev` | D3A (07), F3 01a (23), PBL05 (52), SAMF08 (55) | @JongilHan66 @lisa-bengtsson | D3A adds `hfus`. After #390 |
| Noah-MP | 0b | ccpp-physics | NM1, NM3–NM6, NM8 (W08, W10–W13, W15); NM12 (12); NP1 (33); SL2, CS1, CB1 (38–40) | @barlage @cenlinhe | NM12 = NCAR/noahmp#47 |
| Surface iteration, sea ice, NSST | 1d | ccpp-physics (+ NOAA-EMC/noahmp `develop` in the `iter` form) | NM2 (W09) + 09b; SI1, SI2, FL1 (31, 32, 36); QR1 (34) | @wd20xw @XuLi-NOAA @barlage @cenlinhe | NM2 and SI1: `iter` argument, or one clause of `GFS_surface_loop_control_part2` (*Alternatives*); the `iter` form of NM2 needs 09b (the land component crashes without it) |
| GFDL MP v3 | 0b | ccpp-physics | GFDL02, GFDL07 (49, 54) | @RuiyuSun | |
| Build | 0b | NOAA-EMC/ufsatm `develop` | SAMF32 (25) + 0b submodule bump | @rhaesung (author of ufsatm#1133, also a ccpp-physics code manager) | answers change in the `_conv32` tests |
| Thompson | 0c | ccpp-physics | TH1, TH3, TH4, TH5 | @gthompsnWRF @RuiyuSun @AndersJensen-NOAA | TH5 adds `prsi` (in the hosts) |
| Thompson, second forms | 1e | ccpp-physics | TH2, TH6, TH7 | @gthompsnWRF @RuiyuSun @AndersJensen-NOAA | on top of 0c's Thompson PR |
| TEMPO driver | 0c | ccpp-physics | TH1's twin in `mp_tempo` (`ports/TEMPO-driver/0001`) | default owners | exposes TEMPO's own +0.33 % residual (fixes at NCAR/TEMPO, unmerged). After #389 |
| FV3 | 1c | GFDL_atmos_cubed_sphere `dev/emc` | FX1, SG1, CP1, FV2, INLQ (01, 02, 03, 05, 29); FV1 (W19) | maintainers (no CODEOWNERS) | `dev/emc` merges rarely (last 5 August) |
| ufsatm bump | 0c, 1c, 1d, 1e | NOAA-EMC/ufsatm `develop` | submodule bump | ufsatm code managers | no code |
| WM | 0b, 0c, 1c, 1d, 1e | ufs-weather-model `develop` | submodule bumps, RT log, `test_changes.list` | gatekeepers | one per track |

Every ccpp-physics PR also gets the default owners (@grantfirl @rhaesung @Qingfu-Liu @dustinswales).

**Moved to round 2 by the red team** (issues 6–8 in `round2_issues.md`):

| Fix | Why not round 1 |
|---|---|
| R1 (04) | two new `Radtend` fields; ccpp-physics CI runs capgen against NCAR/ccpp-scm `main` and ufsatm `develop`, so the host fields must merge first (and the MPAS host, #397) |
| TOPT (26) | overlaps #397's `tend_opt` restructuring; option 4 → error is a design choice |
| MYNN01, MYNN01b (47, 48) | #392 replaces `module_bl_mynn.F90` with the NCAR/MYNN-EDMF submodule |

**Held for the SAMF instability issue** (ufs-community/ccpp-physics#401, to @JongilHan66):

| Change | Why held |
|---|---|
| SA1 (W01), `pr1-sa1` | alone raises the HAFS overshoot rate 1.7× and lowers HAFS precipitation 1.25 % (fails rule 4 there); it changes the moisture flux at `kb`, where the overshoots are. With #403's floor (2a95266): event rate 22 → 12 per member at 48 h, precipitation −0.8 to −1.2 %, which is the water it stops creating (*SA1 with the floor: result*); ready as depending on #403 |
| SAMFCFL, `pr1-samfcfl` | our cap (option A); a new limit (rule 2); deep only, `samfshalcnv` has the same gap |

## Branches and patches

Local only, in `$U/pr1/series` (a copy of the pristine clone `$U/pr1/ufs-weather-model`; every pin there equals its
branch head):

| Repository | Branch | Track | Commits | Base |
|---|---|---|---|---|
| ccpp-physics | `pr1-samf`, `-noahmp`, `-gfdlmp` | 0b | 4, 11, 2 | `ufs/dev` d9b70feb |
| ccpp-physics | `pr1-noahmp_p1` (NM2 on `pr1-noahmp`), `pr1-seaice_nsst` | 1d | +1, 4 | `pr1-noahmp`; `ufs/dev` d9b70feb |
| ccpp-physics | `pr1-thompson`, `-tempo` | 0c | 4, 1 | `ufs/dev` d9b70feb |
| ccpp-physics | `pr1-thompson_p1` (TH2, TH6, TH7 on `pr1-thompson`) | 1e | +3 | `pr1-thompson` |
| ccpp-physics (backups) | `tr-pr1-thompson-pre-phase0` (8486c044), `tr-pr1-noahmp-pre-phase0` (ee943d88) | — | 6, 12 | each phase-1 head has exactly its tree |
| ccpp-physics | `pr1-round1` (all six, a4bee81f) | all | 29 | `ufs/dev` d9b70feb |
| ccpp-physics (held) | `pr1-sa1` (ae8399bd), `pr1-samfcfl` (766d0735) | — | 1, 1 | `ufs/dev` d9b70feb |
| ccpp-physics | `prep-samf-on390`, `prep-tempo-on389` | 0b, 0c | 4, 1 | `ufs/dev` + #390 / #389, conflict resolved |
| GFDL_atmos_cubed_sphere | `pr1-round1` | 1c | 6 | `dev/emc` 71ff473b |
| ufsatm | `pr1-round1` (SAMF32 + bump of all; 447ff08) | all | 2 | `develop` aa0ba811 |
| NOAA-EMC/noahmp | `pr1-round1` | 1d (`iter` form) | 1 (09b) | `develop` 2c7b3bc2 |
| ufs-weather-model | `pr1-round1` (bump of all; `.gitmodules` still upstream; 52c8f8c2) | all | 1 | `develop` f1d68949 |

- **To make per track**: ufsatm and WM branches whose bumps carry only that track's PRs (0c: Thompson and TEMPO
  merged; 0b: SAMF32 + SAMF, Noah-MP and GFDL MP merged; 1d: NM2 and sea ice/NSST (+ noahmp in the `iter`
  form); 1e: `pr1-thompson_p1`; 1c: FV3), each on the heads
  of the tracks merged before it. `q/t1ans` holds 0b with NM2 (13 files = 5 + 7 + 1); `attr/g_t1a` 0b + 1d.
- **Commits**: author and committer `Ash Pera <ashley.pera@noaa.gov>`; message = defect, fix, measured effect (water
  messages from `git/ufs-dev/all` and the FV3 series, the rest in `$U/pr1/msgs/`); then the paragraph
  `Part of a water-conservation project for UFS physics (NOAA GML / CIRES).`; last line
  `AI-assisted: written with Claude Opus 5.5; reviewed by author`.
- **How built**: `apply_r1.sh` + `recipe_r1.txt` apply the 41 pre-red-team diffs to the clone (all at -F0 except
  SAMF08 hunk 1, fuzz 1 for a context line from the held T1); `mkseries_r1.sh` commits them one per fix;
  `rebuild_r1b.sh` regroups (commits matched by patch-id); `resolve_prep.py` resolves the #390/#389 conflicts.
- **Patches**: `pr_round1_patches/` = `$U/pr1/cut/` (`git format-patch` per branch, 76 files; phase 1: `ccpp-physics_thompson_p1`, `ccpp-physics_noahmp_p1`, each on its phase-0 branch; held: `ccpp-physics_sa1_hold`, `ccpp-physics_samfcfl`; the pre-split sets in `cut/*.pre_phase0`).
- **Kept on Hercules**: `r1` (pre-red-team patched tree), `rt1`/`rtc` (its RT trees), `mergetest/`, `grp/`
  (develop-pinned template); `attr/<unit>` (attribution clones, as `attr/<pr>` for the single PRs: single PRs, single commits, the parts of `a55b6faa`,
  the WoFS and global units, the noise reference); branches `v1-*` (pre-regrouping) and the pre-rewrite backups
  `orig-*`, `em-*`, `rw-*`, `m4-*`, `tr-*` (`tr-*-pre-samfcfl`: before SAMFCFL; `tr-*-pre-nosa1`: before SA1 and
  SAMFCFL were dropped).

## Checks

Screen: `rt_screen.py` (window-mean precipitation, T2m, PW, q2m, 3-D T and q against each test's own baseline dir,
`baseline dir =` in its `rt_*.log`). An attribution unit is one PR, one commit or one part alone on develop
(`attr/attr_*_table.txt`).

### Whole round (the 37)

| Check | Result | Can fail |
|---|---|---|
| Tree = branches | `rt2`, `rtc2` = `series` (`diff -r` empty); every submodule at its parent's pointer | pristine vs `r1`: 28 files |
| Regrouping drops exactly R1, TOPT, MYNN | pre-regrouping `pr1-round1` with those 4 commits reverted = new `pr1-round1` | old vs new differ |
| Each ccpp-physics PR alone on `ufs/dev` | 6 of 6 pick cleanly | — |
| Any merge order | 15 of 15 pairs clean; all six merged = `pr1-round1` | — |
| Open upstream PRs (each merged onto `ufs/dev` first) | #390 vs SAMF and #389 vs TEMPO: one block each, resolved in `prep-*`; #397, #399 clean; #381, #392, #359 conflict with `ufs/dev` themselves | — |
| Message and email rewrites | every branch tree identical to its pre-rewrite backup; every branch on its upstream head | — |
| Compile, all pre-red-team fixes (job 10164440) | rc 0 (`atm_dyn32_conv32` suites + HRRR/GF with `-DSAMFCNV_32BIT=ON`; `atml` with 09b) | — |
| Compile, each PR alone on `develop` | rc 0 at the branch heads: thompson, seaice_nsst, gfdlmp, FV3 (10169904); tempo, noahmp (`atml` + 09b), ufsatm (`-DSAMFCNV_32BIT=ON`) (10170333); held SAMFCFL (10173398); 4-fix samf (10175400) | — |
| SA1 and SAMFCFL dropped | each rebuilt branch + the dropped commits re-added = the old tree (`pr1-round1`, `pr1-samf`, `prep-samf-on390`); the six PR branches merge cleanly and their union = `pr1-round1` | tree mismatch |
| Regression vs `develop-20261008` (10175908, `rt2`; `rt_logs_37/`) | 54 compiles and 17 tests pass; 188 tests change answers; 29 restart children not started; none failed to run, `hafs_global_1nest_atm` included. `test_changes.list`: 217. Run-dir audit: 205 dirs, 2 without `out` (retried by `rt.sh`; both compared) | the HAFS crash |
| Reproducibility (`rtc2`: `-c` 10175909, then `-l repro_m.conf` 10175910) | SUCCESS: 123 of 123 (102 tests bitwise, 21 compiles): the 71 restart/decomposition/threading/MPI tests and their parents; the 29 restart children equal their parents | — |
| Noise reference | one-ulp perturbation build (`q/noise`, 10 tests incl. `regional_control`, `conus13km_control`; 10175390): window-mean precipitation ≤ 0.24 %, T2m ≤ 0.0035 K, PW ≤ 0.011 %, 3-D T ≤ 0.0003 K, 3-D q ≤ 0.02 %; instantaneous precipitation unusable (up to 10 %). WoFS (`attr/w_noise`): precipitation −0.18 %, −0.34 % | — |
| Answer-change size (`rt_logs_37/screen188_flag.txt`, `screen_re37.txt`) | 188 of 188 screened, 55 above 5× noise; variants equal their parents to 4 decimals. Regional precipitation: `regional_control` +8.7 % (36×), `regional_noquilt` +7.9 %, `regional_spp_sppt_shum_skeb` −5.1 % (21×), `cpld_regional_atm_fbh` −3.5 %, `gnv1_nested` −2.5 %, `conus13km_gl_inline` −2.4 %, `regional_wofs_tempo` −1.8 %, `regional_wofs` −1.1 %; 1-h debug runs −0.04 to −1.8 %. Global P8: 3-D T +0.0009 to +0.0044 K (5–15×), precipitation ≤ 0.35 %. `control_p8_samf_conv32` (the ufsatm PR's test): −0.35 %, 3-D T −0.0002 K, PW +0.04 %, not flagged. `cpld_debug_sfs` (RESTART tiles, unweighted): T2m −0.006 K, `tprcp` −0.07 to −0.2 % | outliers > 5× noise |
| Screen coverage | `rap_sfcdiff_decomp`, `rap_progcld_thompson_debug` lost their output on `rt.sh`'s retry; rerun from a copy of `rt2` (`attr/re37`, `rt_logs_37/screen_re37.txt`): −0.05 %, −1.03 %, `rap_sfcdiff_decomp` = its parent. `regional_noquilt` read from `fv3_history` (unweighted), `cpld_debug_sfs` from RESTART | — |
| Per PR, 8 regional outliers (11 runs) | Thompson alone reproduces the 37 (`regional_control` +9.2 % vs +8.7 %, `regional_spp_sppt_shum_skeb` −5.3 % vs −5.1 %, `conus13km_gl_inline` −2.42 % vs −2.41 %, HRRR/RAP debug −0.9 to −1.4 %); FV3 ≤ 0.25 % except `cpld_regional_atm_fbh` −1.4 %; sea ice/NSST `regional_control` +0.7 %; SAMF + PBL 11 of 11 bitwise; Noah-MP ≤ 0.02 %. Sum of singles within 0.4 % of the 37 except `regional_control` (+9.9 vs +8.7). GFDL MP, TEMPO and the `_conv32` build do not reach these suites (`attr/attr_table.txt`) | sum ≠ the 37 |

### Track 0b (and 1d)

| Check | Result | Can fail |
|---|---|---|
| 0b without NM2, global P8 tests + `control_p8_atmlnd` (`attr/g_p0b`) | 3-D T +0.0010 to +0.0058 K (`control_c48.v2.sfc` +0.0002), within 0.0007 K of SAMF + PBL alone except `control_p8_samf_conv32` (the SAMF32 build, −0.0018 K); precipitation −0.27 to +0.29 %; `control_p8_atmlnd` runs (T +0.0014 K, precipitation +0.02 %) with noahmp at develop (`attr/attr_p0b_table.txt`, `_t.txt`) | above noise outside SAMF + PBL; `atmlnd` fails |
| Global P8, per PR and 0b + 1d together (`attr/g_*`, `attr_global_table.txt`): `control_p8`, `control_c48`, `control_c48.v2.sfc`, `control_p8_lndp`, `control_p8_rrtmgp`, `cpld_control_gfsv17`, `control_p8_samf_conv32`, `hafs_regional_atm_gfdlmpv3`; Thompson and FV3 alone for comparison | 3-D T: **SAMF + PBL** +0.0024 to +0.0062 K (8–20× noise) = the 37's warming; the ice-fusion heat it restores (0.42 W/m²) gives 0.0036 K/day, so the bug's own signal. Noah-MP −0.0003 to −0.0009 K; sea ice/NSST ≤ 0.0008 K; GFDL MP v3 only `hafs_regional_atm_gfdlmpv3` (precipitation −0.30 %, T −0.0008 K; its bug created 1.03 % of microphysics precipitation); build only `control_p8_samf_conv32` (−0.50 %, −0.0027 K: SAMF now single precision). Precipitation: SAMF + PBL +0.16 to +0.37 %, others ≤ 0.13 %. 0b together: 3-D T +0.0020 to +0.0050 K, precipitation −0.31 to +0.33 %; singles add to it within 0.0011 K. Thompson, FV3 alone: ≤ 0.18 %, ≤ 0.0012 K | a 0b PR outside noise and not its bug's signal; singles ≠ 0b together |
| HAFS instability rate, 0b + 1d (`hafs_global_1nest_atm`; `q/t1a`, `hafs_exp/q_t1a_*`, `q_ens3_stats.txt`) | **fails**: 3 of 20 members crash (`compute_qs` overflow; 66–73 K), the `consv_te` = 1 member (the RT configuration) included; develop 0 of 20 (p 0.12); 0b (0b + 1d − sea ice/NSST) 0 of 20; no single fix identified (*HAFS crash*, ensembles); event rate as develop. Hence 1d held | rate above develop's |

### Track 0c (and 1e)

| Check | Result | Can fail |
|---|---|---|
| Phase-0 Thompson (TH1, TH3, TH4, TH5) + TEMPO together, 8 regional outliers + WoFS (`attr/p0c`) | precipitation −0.9 to −5.3 % (`regional_spp_sppt_shum_skeb` −5.3, `cpld_regional_atm_fbh` −3.0, `conus13km_gl_inline` −2.5, `regional_control` and `gnv1_nested` −1.4, HRRR/RAP debug −0.9 to −1.3), WoFS TEMPO −1.96 % (`attr/attr_p0c_table.txt`): the water the graupel limiters and the mass-basis round trips created (per fix alone: graupel −1.0 to −4.1 %, mass basis up to −2.0 %). `regional_control` −1.4 % instead of +9.2 % with TH2 | above 5× noise |
| Thompson by commit (`attr/attr_split_table.txt`; commit 5 needs 3, run as 3+5) | `a55b6faa` carries it: `regional_control` +11.0 %, `regional_spp_sppt_shum_skeb` −4.1 %, `gnv1_nested` −2.6 %, `conus13km_gl_inline` −2.1 %, HRRR/RAP debug −0.9 to −1.3 %. `2909f960` (mass basis): `regional_spp` −1.6 %, `cpld_regional_atm_fbh` −2.0 %. Others ±1.1 % | sum ≠ the PR |
| Parts of `a55b6faa` (`attr_c2_table.txt`) | **settled cloud water counted**: `regional_control` +10.9 %, ≤ 0.8 % elsewhere; 3-D T +0.0008 K, q −0.0006 %, so reported, not state. **Graupel re-closure + snow cap**: every decrease (`regional_spp` −4.1 %, `conus13km_gl_inline` −2.1 %, `cpld_regional_atm_fbh` −1.1 %, HRRR/RAP debug −1.0 to −1.4 %). **Cloud substepping**: ≤ 0.23 % except `gnv1_nested` −1.2 %. Parts sum to the commit within 0.35 % except `gnv1_nested` | sum ≠ the commit |
| WoFS (`attr/attr_wofs_table.txt`) | `regional_wofs_tempo` (37: −1.8 %, 8× the C96-based noise): TEMPO −1.96 % (6× WoFS noise; the mass-basis bug created water under net condensation); FV3 commits 0.7–2.4× noise (1c); sea ice/NSST −0.06 %; Noah-MP bitwise; sum −3.3 %. `regional_wofs` (NSSL MP; 37: −1.1 %): FV3 only, sum −0.3 %. Sums miss the 37 by 0.8–1.5 points: not additive | sum ≠ the 37 |

### Track 1c

| Check | Result | Can fail |
|---|---|---|
| WoFS, FV3 commits singly (`attr_wofs_table.txt`) | `regional_wofs_tempo`: `atmosphere_state_update` −0.83 %, `statein` −0.43 %, `prsl` −0.24 %, `fv_sg` +0.25 %; `regional_wofs`: −0.59 %, +0.45 %, −0.13 % (`atmosphere_state_update`, `prsl`, `statein`); `consv_te` weights and `d_sw` bitwise | above 5× noise |

## HAFS crash

With the 38 (incl. SA1), `hafs_global_1nest_atm_intel` stops at 5 h 28 min 30 s (`compute_qs` table overflow): SAMF
deep convection heats one cell (35.0° S, 54.1° W, k = 21, 3.8 km, a winter cold front) by +70.72 K in one step.
Evidence from print-only instrumentation of SAMF and `GFS_MP_generic_post` (the instrumented develop is bitwise the
official baseline); trees in `$U/pr1/q/`, runs in `$U/pr1/hafs_exp/q_*`.

**Mechanism** (upstream; `samfshalcnv` has the same code):
1. Below cloud base `eta(k) = eta(k+1)/(1 + (xlamue - xlamud) dz)`, with `xlamue = clamt/z` and `xlamud = 0.001 clamt`.
   Above about 1 km detrainment wins, so for elevated convection `eta` grows downward (101 at `kb`).
2. The TKE scaling holds `clamt` at its cap (15 × `clam`). The overshoot feeds TKE, which keeps it there.
3. `xmbmax` limits CFL only at `kbcon`, where `eta` = 1.

**Study** (`hafs_global_1nest_atm`, 6 h, members `consv_te` = 1, 0.999, 0.998; deep SAMF single-step heatings > 4 K):

| Tree | Events | Capped-TKE columns | Largest | Precip, mm/day |
|---|---|---|---|---|
| develop | 257, 274, 294 | 2900–3200 | 39 K | 2.437 |
| FV3 fixes | 258, 328, 348 | 3100–3500 | 33 K | 2.438 |
| FV3 + D3A | 258, 328, 348 (= FV3) | 3100–3500 | 33 K | 2.438 |
| FV3 + PBL05 | 321, 341, 260 | 3200–3400 | 50 K | 2.438 |
| FV3 + sea ice/NSST | 264, 304, 320 | 3000–3400 | 44 K | 2.437 |
| FV3 + SA1 | 445, 462, 507 | 4500–4800 | 35 K | 2.407 |
| FV3 + SAMF fixes without PBL05 | 445, 462, 507 (= SA1) | 4500–4800 | 35 K | 2.407 |
| all physics, no FV3 | 420, 469, 467 | 4300–5000 | 65.5 K, CFL 55 | 2.407 |
| the 38 | 466 (crash), 464, 473 | 4500–5000 | 70.8 K, CFL 54 | 2.407 |
| the 38 + T1 sub-stepping | 470, 439, 424 | 4200–4500 | 29 K | 2.406 |
| **the 37** | 326, 319, 289 (no crash) | 3000–3200 | 35 K | 2.436 |
| **0b + 1d** (no FV3, no SA1; `q/t1a`) | 109 (crash < 3 h), 293, 210 (crash > 3 h) | 760–3070 | 72.8 K | 2.436 (the member that finished) |
| develop + SAMFCFL, control | 0 | — | — | 2.432 |
| the 38 + SAMFCFL, control | 1 | — | 4.0 K, CFL 0.85 | 2.406 |

**Crash-rate ensembles** (`consv_te` = 1, 0.999, … ; `hafs_exp/q_ens_stats.txt`, `q_ens_np_stats.txt`, `q_ens3_stats.txt`):

| Tree | Members | Crashes | Members with a step > 60 K | Largest per member: median, max | p vs develop (crashes; > 60 K) |
|---|---|---|---|---|---|
| develop | 20 | 0 | 0 | 31 K, 52 K | — |
| the 37 | 10 | 1 (0.991) | 1 | 33 K, 74 K | 0.33; 0.33 |
| 0b + 1d | 20 | **3** (1, 0.998, 0.994) | 4 | 40 K, 73 K | 0.12; 0.05 |
| 0b (0b + 1d − sea ice/NSST) | 20 | 0 | 0 | 32 K, 48 K | 1; 1 |
| 0b + 1d − PBL05 | 10 | 0 | 1 | 29 K, 63 K | 1; 0.33 |
| 0b + 1d − NSST rain | 10 | 0 | 1 | 29 K, 75.5 K (no crash) | 1; 0.33 |
| 0b + 1d − the three sea-ice fixes | 10 | 0 | 0 | 30 K, 51 K | 1; 1 |
| 0b + 1d + FV3 | 10 | = the 37, bitwise in all 10 (Thompson and TEMPO do not act in HAFS) | | | |

p: chance that this many of the pooled events fall in the tree (hypergeometric). Event counts and precipitation of
finished members overlap develop's in every tree (all 96 finished: 241–369 events, 2.4351–2.4391 mm/day). 0b + 1d's three crashes are all in
its first 10 members. No single fix is identified: every removal gives 0 crashes, but at 0b + 1d's 3 in 20, 0 in 10 has
probability 0.2. 0b is indistinguishable from develop in 20 members.

No shallow event above 4 K in any run. Gates: the develop control reproduces the earlier count (257); the 38's control
reproduces the crash (466, same step). "All physics, no FV3" included SA1, so it is not 0b + 1d.

**Fix options** (issue options A and B; 20 members each; `q/devA`, `devD`, `devE`, `t1aA`, `t1aD`, `t1aE`;
`hafs_samf/q_opt_stats.txt`, `opt_sum.py`):

| Tree | Crashes | Events > 4 K per member | CFL > 1, all members | Largest step | Precip, mm/day |
|---|---|---|---|---|---|
| develop | 0 | 257–351 | 5769 | 52.0 K | 2.4370 |
| + A, CFL bound `kb ≤ k < kbcon` (`fixb.f`, SAMFCFL) | 0 | 0–1 | 0 | 4.8 K | 2.4327 |
| + CFL bound `kb ≤ k < ktcon` (`optD.f`) | = A in all 20 | | | | |
| + B, vapour bound (`optE.f`) | 0 | 246–384 | 5839 | 42.2 K | 2.4372 |
| 0b + 1d | 3 | 241–369 | 5009 | 64.2 K | 2.4365 |
| 0b + 1d + A | 0 | 0–1 | 0 | 4.5 K | 2.4324 |
| 0b + 1d + CFL bound to `ktcon` | = A in all 20 | | | | |
| 0b + 1d + B | 1 | 252–344 | 5541 | 44.0 K | 2.4364 |

The bound above cloud base never binds (the executables differ; all 40 statistics lines are identical), so the issue
offers the bound in every updraft layer as A. B does not bind the overshoots.

**Findings.**
- The instability is upstream: develop reaches 39 K in one step.
- SA1 alone raises the event rate 1.7× and lowers precipitation 1.25 %; D3A, wet deposition and the CA fix do not act
  in HAFS, and PBL05, FV3 and sea ice stay at develop's level. The 37 (without SA1) run at develop's rate and
  precipitation (−0.03 %), no crash in three members.
- The extreme TKE (3.4 × 10⁴ m²/s² in develop) is a feedback of the overshoot; with SAMFCFL it peaks at 450–479.
  That residual is SAMF's TKE source ("include TKE contribution from deep convection", and the shallow twin), which
  adds `0.5·σ·w_u²`, `w_u = η·xmb/(σρ)`, once per call rather than as a rate. Per 90 s step at the hotspot (3.5 km,
  run `d6_dev_fixB_tke3`):

  | PBL | GWD → pre-convection | convection + MP | dycore |
  |---|---|---|---|
  | −375 | 0 | +383 | −10 |

  With σ at its 0.03 floor, +383 means `w_u` ≈ 160 m/s. Deep against shallow is not split.

### Reply to Han (#401, 21 Oct)

Han: GFS v16/v17 never crash on `xm`; below cloud base `eta` > 1.2 is not seen, since `crtlame` = 1e-4 floors
`xlamue`; large TKE would come from an instability; test `eta`, `etad` ≤ 1. The floor argument holds at
`clamt` = `clam` = 0.1 (above 1 km `xlamue` = `crtlame` = `xlamud` = 0.001·`clam`). For `tkemean` > `tkcrt` = 2 the
TKE scaling multiplies `clamt`, and so `xlamud`, by up to `cmxfac` = 15 and leaves `crtlame` alone: above 1 km
detrainment exceeds entrainment and `eta` grows downward.

Tests (20 members each, `hafs_samf/q_han.sh`; C and T also on `t1a`, same counts within 4 %):

| | develop (P) | C: `eta`, `etad` ≤ 1 | T: no convective TKE source | A (`q_opt`) |
|---|---|---|---|---|
| crashed, develop / `t1a` | 0 / 3 | 0 / 0 | 0 / 0 | 0 / 0 |
| layer-steps > 4 K per member | 257–351 | 5513–5935 | 0 | 0–1 |
| largest step | 52.0 K | 14.5 K | — | 4.8 K |
| convective columns with sub-cloud `eta` > 1.2 | 0.98 % (261,145); > 10: 5,311; max 102 | 0 | 40 of 28 M, max 1.2 | not counted |
| columns with `tkemean` > 2 | 10.6 % | 6.8 % | 2.3 % | not counted |
| `clamt` capped (`tkemean` > 28), all members | 62,421 | 0 | 0 | 66,970 (TKE ≤ 434) |
| mean precipitation, mm/day | 2.4370 | 2.2390 (−8.1 %) | 2.6497 (+8.7 %) | 2.4327 (−0.18 %) |

- Every column with `eta` > 1.2 had `tkemean` > 2 (26.6 M columns; the one at the print threshold has `clamt` = 0.2).
- C's events are a different population: `kb` = 1 (develop's: `kb` ≈ 17), at `kb ≤ k ≤ kbcon`, all heating, CFL ≤ 1
  (median 1.00, max 2.6 where `del` < `del(kbcon)`), `xmb` = `xmbmax` in 57–59 %. Capping `eta` lowers the closure's
  `xk`, so `xmb` rises to its limit.
- T: without SAMF's own TKE source the sub-cloud TKE stays low and `eta` stays ≤ 1.2. The large TKE comes from SAMF
  (∝ (`eta`·`xmb`)²), not from the PBL.
- Both C and T move precipitation by 8 %; A by 0.18 %.

**Red-team (21 Oct; independent review playing Han, plus our own checks).** Corrections and open items:

| # | Finding | Status |
|---|---|---|
| R1 | Crash counts carry little weight: 3/20 vs 0/20 is p = 0.115 one-sided, and the 20 members perturb one initial condition (parent `consv_te` only). The develop tail is the evidence: largest step per member 22.8–52.0 K, CFL up to 25; with A at most 4.8 K | reply leads with the tail; 40 more members each of `t1a` and `t1aA` running |
| R2 | One configuration: C96 L64 + nest, `dt` 90 s, cold start, 6 h, one date. The TKE source is added once per call, so its rate scales as 1/`dt` (8× control_p8, ~2× operational GFS) | `rt.sh` survey (GFS v16/v17 C48–C384, five HAFS) P, A, A1; `dt` 45/180/360; dose 0.5/0.25; 48 h |
| R3 | Han's GFS v16 example has no `cmxfac` (it came in 2023, ccpp-physics PR #65 for GFS v17); operational users of ×15 are HAFS v2.0/v2.1 (`progsigma` true in v2.1, σ floor 0.01, up to 3× the source) | `history_tke_scaling.md`; `progsigma` trial run |
| R4 | The issue omitted the `crtlame` floor; at `clamt` = `clam` the net rate above 1 km is 0, not negative. `clamt` = 0.13 for `tkemean` > 0.65 lets `eta` reach ~1.05–1.1 | concede in the reply |
| R5 | The posted loop ("the overshoot feeds TKE") is wrong in direction: under A there is no overshoot and `clamt` stays capped (66,970 column-steps). The loop is TKE source ∝ (`eta`·`xmb`)² → TKE → `clamt` → `eta` | correct in the reply |
| R6 | Option A divides by `eta`; `1 + ptem·dz` ≤ 0 (dz ≳ 700 m at the cap) gives `eta` ≤ 0 and a negative `xmbmax`. A also binds where `eta` ≤ 1 in thin layers (GFS L127 surface layers) | A1 (only where `eta` > 1) built; dbgeta2 counts `eta` ≤ 0; survey shows where A/A1 bind |
| R7 | A treats the symptom: `eta` ≈ 100 and TKE ≤ 434 remain. F (scaled `crtlame`) restores Han's invariant | F, G, H ensembles running |
| R8 | C's 20× ">4 K" count is threshold-driven: C's largest step 14.5 K, CFL ≤ 2.6, none > 5; 28 % fewer convective column-steps (unexplained); `etad` cap not separated | C1 (`eta` cap only) built; the table leads with largest step and CFL > 5 |
| R9 | Precipitation is the parent's 3–6 h bucket (`fhzero` = 3, global_latlon), spin-up, not climate | 48 h runs; nest output separate |
| R10 | The sub-cloud recursion compounds faster than exp(∫): 1/(1 − 0.47) = 1.89 per layer vs 1.60, so `eta` = 101 may be ~30 in the continuum | wording |
| R11 | Shallow is not the same: `clam_shal` = 0.3 gives `xlamud` = 3e-4 > `crtlame`, so the floor argument fails there even without TKE; shallow `cmxfac` = 10 | wording |
| R12 | Counts are column-steps pooled over 20 members and both grids: per member ~13,000 of 1.33 M with `eta` > 1.2, ~265 > 10 | wording |
| R13 | "Not as a rate" is answerable (PBL dissipation balances it: −375 vs +383); argue the `dt` dependence once measured | wording |
| R14 | Lisa (21 Oct 18:48) asked for a run directory on a NOAA machine | answered 22 Oct ([comment](https://github.com/ufs-community/ccpp-physics/issues/401#issuecomment-6330107787)): `/work2/noaa/co2/ash/share/ccpp401` (develop_48h crash, develop 6 h, crash_24fixes; world-readable since 22 Oct) |

**48 h: develop crashes on its own (21 Oct).** `hafs_global_1nest_atm`, develop + print-only blocks (devP2), 48 h, 10
members (`mkexp_long.sh`):

| 48 h, 10 members | crashed (`compute_qs` overflow) | largest step, per member | layer-steps > 4 K |
|---|---|---|---|
| develop | **6** (at 19–40 h: steps 777–1605) | crashed 64–96 K; finished 49–88 K | ~9,000 |
| A | 0 | 4.8–6.6 K | 10–20 |

Fisher one-sided p = 0.005. This answers "develop never crashes": in this configuration it does, with no patch of
ours, in the SAMF sub-cloud signature (CFL > 1, `eta` > 1). F's 48 h runs are not yet done (not launched).

**Results so far (21 Oct evening; `hafs_samf/q_fix_stats.txt`).** 20 members each, 6 h, develop sd of precipitation 0.0009:

| | develop | A | F (`crtlame`·max(1, `clamt`/`clam`)) | G (`w_u` ≤ `wc`) | H (TKE = max) | develop, `dt` 180 |
|---|---|---|---|---|---|---|
| layer-steps > 4 K per member | 257–351 | 0–1 | 0 (t1a 0–1) | 0–3 | 80–155 | 83–126 |
| largest step | 52.0 K | 4.8 K | 0 (t1a 4.1 K) | 9.9 K | 41.3 K (t1a 86.5) | 41.7 K |
| sub-cloud `eta` > 1.2 (max) | 261,145 (102) | 271,504 (81) | 0 | 12,270 (1.8) | 49,770 (95) | 67,209 (52) |
| `eta` ≤ 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `clamt` capped | 62,432 | 66,978 | 788 | 0 | 10,352 | 4,716 |
| precipitation | 2.4370 | −0.18 % | +0.02 % | +0.40 % | +6.7 % | +6.4 % |

F removes the overshoots with no precipitation change beyond the member spread, and restores the invariant Han's
reply relies on. `dt` 180 cuts capped columns 13× and events 3×: the TKE path depends on the step.

Survey (print-only develop, `rt.sh` vs develop's baselines; all 12 PASS, so the prints change nothing):

| test | `dt` | `eta` > 1.2 (max) | capped | steps > 4 K | largest |
|---|---|---|---|---|---|
| control_c48 | 720 | 79 (1.7) | 313 | 28 | 6.7 K |
| control_p8 (C96) | 720 | 168 (1.4) | 204 | 161 | 8.9 K |
| control_c192 | 600 | 2,647 (2.1) | 1,341 | 802 | 9.3 K |
| control_c384 (GFS v17 P8) | 300 | 43,924 (9.2) | 2,499 | 1,260 | 26.4 K, CFL 9.1 |
| control_c384gdas (GFS v16 suite, develop code) | 225 | 36,289 (8.5) | 3,198 | 678 | 19.8 K |
| hafs_regional_atm | 180 | 36,819 (9.3) | 10,022 | 5,207 | 17.3 K |
| hafs_regional_1nest_atm | 90 | 17,544 (34.1) | 4,504 | 743 | 48.3 K, CFL 15 |
| hafs_global_1nest_atm | 90 | 13,012 (100) | 2,922 | 257 | 24.5 K |

All these RTs run `progsigma` = false. One develop member with `progsigma` = true (operational HAFS v2.1, `mkexp_ps.sh`)
had no event > 4 K, no capped column and `eta` ≤ 1.3; 20-member ensembles of develop and t1a with it are running.

**All sets done (22 Oct 00:40Z; `hafs_samf/q_fix_stats_*.txt` on Hercules).**

| set | crashed | steps > 4 K / member | largest | `eta` > 1.2 | capped | precipitation |
|---|---|---|---|---|---|---|
| A1 (A only where `eta` > 1), 6 h | 0/20 | 0–1 | 4.7 K | 274,565 | 68,355 | 2.4329 |
| C1 (`eta` cap only) | 0/20 | 5513–5935 | 14.5 K | 0 | 0 | 2.2390 = C: the `etad` cap is a no-op |
| TKE source × 0.5 | 0/20 | 126–232 | 45.1 K | 119,169 | 19,917 | 2.5329 |
| TKE source × 0.25 | 0/20 | 30–92 | 34.5 K | 31,390 | 3,315 | 2.5899 |
| develop `dt` 45 s | 1/10 | 565–707 | 95.5 K | 538,519 | 332,156 | 2.2729 |
| develop `dt` 360 s | 0/10 | 44–62 | 36.6 K | 9,362 | 264 | 2.6990 |
| develop 48 h | 6/10 | ~9,000 | 88 K (finished) | 1.64 M | 440,966 | |
| A 48 h | 0/10 | 10–20 | 6.6 K | 2.70 M | 789,542 | |
| F 48 h | 0/10 | 16–28 | 7.6 K | 0 | 152,116 | |
| `progsigma` true, develop / t1a | 0/20, 0/20 | 0 | — | 337 (max 1.3) | 0 | 2.1039 |

| Han's test (C), 6 h, `dt` 45 / 90 / 180 s (10 members each) | 0/10 each | 9,401 / 5,697 / 3,178 | per-step median 6.1 / 6.0 / 6.0 K, p99 11.5 / 11.2 / 11.0, CFL median 1.00 | ≤ 1 | — | `q_step.py`: per-step heating independent of `dt`, so the CFL limit, not a rate |
| Han's test (C) 48 h | 0/10 | 48,414–50,138 | 15.2 K, CFL 3.6 | 0 | 0 | 3.1337 (A 2.8686, F 2.8571) |
| develop, `progsigma` true, 48 h | 0/10 | 0 | — | 1,225 (max 1.3) | 1,824 | 2.6678 |

Dose and `dt` are monotone in the capped count (62,432 at the default, 90 s). Survey A and A1: all 12 tests NOT
IDENTICAL, GFS included, so neither is answer-neutral.

**Han accepts the floor (22 Oct); test of his form submitted 22 Oct 10:37 CDT.** Survey F (`sv_setup.sh F`, job 10198036, `--mem=64G` driver): develop + `xlamue` ≥ max(`crtlame`, 0.001·`clamt`) in deep, the 12 RTs vs develop's baselines (`clam_deep` = 0.1 in all 12, so this equals F). `progsigma` true + F (`q_psF.sh`, q/devF exe): 20 × 6 h (`q_devFps_c*`, 10198005–25) and 10 × 48 h (`q_devFps_L*`, 10198026–35). Shallow untouched.

| `progsigma` true | crashed | steps > 4 K | `eta` > 1.2 | capped | precipitation |
|---|---|---|---|---|---|
| develop, 6 h / 48 h | 0/20, 0/10 | 0 | 337 (max 1.3) / 1,225 (max 1.3) | 0 / 1,824 | 2.1039 / 2.6678 |
| + F, 6 h / 48 h (`hafs_exp/qsum/devFps_*`) | 0/20, 0/10 | 0 | 0 / 0 | 0 / 1,790 | 2.1055 / 2.6706 |

Survey F's first submission (10198036) failed all 12 runs: the driver's `--mem=64G` is exported as `SLURM_MEM_PER_NODE`, and the test jobs' `srun` refuses it beside their per-CPU memory. The sbatch now unsets it; resubmitted as 10198724. The same applies to any `--mem` on the 0b driver.

Survey F (10198724, 22 Oct; `hafs_exp/qsum/sv_{P,F}.{stats,eta}`): all 12 NOT IDENTICAL (expected). Develop → F:

| test | `eta` > 1.2 (max) | capped | steps > 4 K | CFL > 5 | largest step (CFL) | precipitation |
|---|---|---|---|---|---|---|
| control_c48 | 79 (1.7) → 0 | 313 → 286 | 28 → 11 | 0 → 0 | 6.7 (3.6) → 6.1 (3.7) | −0.09 % |
| control_c48.v2.sfc | 0 → 0 | 0 → 0 | 10 → 10 | 0 → 0 | 5.6 → 5.6 | −0.02 % |
| control_stochy | 85 (1.5) → 0 | 0 → 0 | 12 → 12 | 0 → 0 | 4.9 → 7.5 (3.4) | +0.11 % |
| control_p8 | 168 (1.4) → 0 | 204 → 213 | 161 → 107 | 1 → 0 | 8.9 (5.1) → 8.3 (3.5) | |
| control_c192 | 2,647 (2.1) → 0 | 1,341 → 1,232 | 802 → 511 | 0 → 0 | 9.3 (4.8) → 7.5 (3.7) | |
| control_c384 | 43,924 (9.2) → 0 | 2,499 → 545 | 1,260 → 195 | 65 → 0 | 26.4 (9.1) → 8.3 (3.5) | +0.19 % |
| control_c384gdas | 36,289 (8.5) → 0 | 3,198 → 2 | 678 → 46 | 61 → 0 | 19.8 (8.5) → 5.6 (3.5) | +0.03 % |
| hafs_regional_atm | 36,819 (9.3) → 0 | 10,022 → 2,180 | 5,207 → 303 | 290 → 0 | 17.3 (9.6) → 7.9 (4.8) | |
| hafs_regional_atm_thompson_gfdlsf | 35,937 (10.8) → 0 | 10,873 → 2,621 | 6,038 → 325 | 464 → 1 | 22.4 (12.5) → 8.8 (5.4) | |
| hafs_regional_1nest_atm | 17,544 (34.1) → 0 | 4,504 → 1,183 | 743 → 2 | 121 → 0 | 48.3 (15.3) → 4.6 (2.5) | |
| hafs_global_1nest_atm | 13,012 (100) → 0 | 2,922 → 45 | 257 → 0 | 56 → 0 | 24.5 (24.0) → none | +0.04 % |
| hafs_global_storm_following_1nest_atm | 921 (76.3) → 0 | 125 → 0 | 26 → 0 | 12 → 0 | 16.1 (15.1) → none | +0.01 % |

One run each, so precipitation has no noise estimate. **Precipitation column superseded:** q_stats.py read 6 h only and unmasked regional fill values; fixed 22 Oct (latest `sfcfNNN.nc`, masked; the devFps 6 h value 2.1055 is unchanged). At the last output (GFS 6–24 h, HAFS 6 h), F − develop: c48 +0.23 %, c48.v2.sfc +0.18 %, stochy +0.07 %, p8 +0.07 %, c192 +0.05 %, c384 +0.25 %, c384gdas +0.03 %, hafs_regional_atm +0.04 %, thompson +0.10 %, regional nest +0.40 %, global nest +0.04 %, storm following +0.01 %: all 12 positive. F removes every sub-cloud
`eta` > 1.2 and all but one CFL > 5 step. Steps of 4–9 K at CFL 1–5.4 remain in GFS and HAFS regional (CFL > 3.7 only in hafs_regional_atm 4.8 and thompson 5.4), with `eta` ≤ 1.2;
develop has the same population where it has no `eta` > 1 (c48.v2.sfc, stochy). Not diagnosed: a guess is `xmbmax`
taken from `dp` at `kbcon` while thinner layers above it reach CFL > 1 (R6). Shallow: 2 steps > 4 K in c48.v2.sfc, both
trees.

**Christian Boyer's 2a95266** (ChristianBoyer-NOAA/ccpp-physics `CP-LEO-3D_TTE_EDMF-Merged`, 22 Oct 14:51Z; Han's cold-pool PR) is not F: the floor 0.001·`clamt` *replaces* `crtlame` (lower floor where `clamt` < 0.1), it is also in `samfshalcnv` (3e-4 in every shallow column), and `fent1`/`fent2` become `min(qeso ratio, 1)`² and ³ (were capped at 3 and 5.2). Testing it as is on develop (`boyer_2a95266.patch`, applies with offsets only): survey B (`sv_setup.sh B`) and `q_boyer.sh` (q/devB: 20 × 6 h, 10 × 48 h, 10 × 48 h `progsigma` true), launched 22 Oct; watched with `sj watch`.

Results (`hafs_exp/qsum/sv_B.*`, `devB_*`, `devBps_L`; all 68 jobs COMPLETED). Develop (P) / F / B:

| test | `eta` > 1.2 | steps > 4 K | CFL > 5 | largest, K | precipitation F / B |
|---|---|---|---|---|---|
| control_c48 | 79 / 0 / 0 | 28 / 11 / 10 | 0 / 0 / 0 | 6.7 / 6.1 / 6.1 | +0.23 / +0.46 % |
| control_c48.v2.sfc | 0 / 0 / 0 | 10 / 10 / 7 | 0 / 0 / 0 | 5.6 / 5.6 / 6.3 | +0.18 / +0.38 % |
| control_stochy | 85 / 0 / 0 | 12 / 12 / 11 | 0 / 0 / 0 | 4.9 / 7.5 / 6.8 | +0.07 / +0.45 % |
| control_p8 | 168 / 0 / 0 | 161 / 107 / 111 | 1 / 0 / 0 | 8.9 / 8.3 / 8.1 | +0.07 / +0.23 % |
| control_c192 | 2,647 / 0 / 0 | 802 / 511 / 525 | 0 / 0 / 0 | 9.3 / 7.5 / 7.8 | +0.05 / +0.28 % |
| control_c384 | 43,924 / 0 / 0 | 1,260 / 195 / 187 | 65 / 0 / 0 | 26.4 / 8.3 / 8.8 | +0.25 / +0.46 % |
| control_c384gdas | 36,289 / 0 / 0 | 678 / 46 / 48 | 61 / 0 / 0 | 19.8 / 5.6 / 6.2 | +0.03 / +0.15 % |
| hafs_regional_atm | 36,819 / 0 / 0 | 5,207 / 303 / 277 | 290 / 0 / 1 | 17.3 / 7.9 / 8.3 | +0.04 / +1.84 % |
| hafs_regional_atm_thompson_gfdlsf | 35,937 / 0 / 0 | 6,038 / 325 / 352 | 464 / 1 / 2 | 22.4 / 8.8 / 11.2 | +0.10 / +1.71 % |
| hafs_regional_1nest_atm | 17,544 / 0 / 0 | 743 / 2 / 1 | 121 / 0 / 0 | 48.3 / 4.6 / 4.5 | +0.40 / +0.51 % |
| hafs_global_1nest_atm | 13,012 / 0 / 0 | 257 / 0 / 0 | 56 / 0 / 0 | 24.5 / — / — | +0.04 / +0.34 % |
| hafs_global_storm_following_1nest_atm | 921 / 0 / 0 | 26 / 0 / 0 | 12 / 0 / 0 | 16.1 / — / — | +0.01 / +0.66 % |

Ensembles (`hafs_global_1nest_atm`): B 6 h 0/20 crashed, 0–1 steps > 4 K, max 4.7 K, precipitation 2.4454 (+0.34 %; F
+0.02 %); 48 h 0/10, 17–28 per member, max 8.6 K CFL 2.8, `eta` > 1.2 0, 2.8626 (F 2.8571); `progsigma` true 48 h
0/10, none > 4 K, `eta` > 1.2 0, 2.6747 (develop 2.6678, F 2.6706). B fixes the instability as F does; its
precipitation change is 2–40× F's (HAFS regional +1.7–1.8 %). Not attributed among its three parts (no `crtlame`,
shallow floor, `fent` cap).

`sj watch --settle-new 7200` (counted from the start) kept this watch silent 2 h after the last job; fixed in sj to
an idle gap, default 300 s.

Posted 22 Oct as [comment 6352169802](https://github.com/ufs-community/ccpp-physics/issues/401#issuecomment-6352169802) (`post/reply_401_6.md`). Han's cold-pool PR is ccpp-physics#403 (head = 2a95266; also GFDL_atmos_cubed_sphere#429, ufsatm#1154), which says it fixes #401. Open: which of 2a95266's three extra parts moves precipitation (offered to run each alone).

Lisa asked (22 Oct 22:07Z) which application we target, since most SAMF users run `progsigma` = .true. Answered ([comment 6356505604](https://github.com/ufs-community/ccpp-physics/issues/401#issuecomment-6356505604), `post/reply_401_lisa2.md`): UFS-Chem v1 with GFS v17 P8 physics, which sets `progsigma` = .true. (Jian's global-workflow `config.fcst`), so our target should not see it; we need the fix for the RT's `hafs_global_1nest_atm` (`progsigma` false); SA1 as the example; GFS v17 coupled and skill untested.

**SA1 with the floor (22 Oct).** SA1 (`pr1-sa1` ae8399bd) applies cleanly on `ufs/dev`, on #390 (3d2331e3) and on #403 (2a95266), offsets only. Held for rule 4 (alone: HAFS overshoot rate 1.7×, precipitation −1.25 %). Test: develop + 2a95266 + SA1 (`q_sa1.sh`, q/devBS; stacked diff +33 −9, gated) vs develop + 2a95266 (devB): 20 × 6 h, 10 × 48 h, 10 × 48 h `progsigma` true; launched 22:18 CDT, `sj watch`. Ready if devBS stays at devB's event rate and its precipitation change is about SA1's own signal; then posted as depending on #403.

**NM8 (Noah-MP latent heats) dropped from phase 0 (23 Oct, Ash: Noah-MP's own constants look moderately intentional, so this is a coupling choice, not a one-answer fix; later round):** `pr1-noahmp` 0bb5123b = the other 10 commits, patch-ids equal; with NM8 kept as `pr1-noahmp-withNM8`; fork `pr1-noahmp` updated to 0bb5123b. Then (Ash, same reason: where truncated water or leftover heat goes is a choice, as TH6/TH7) NM5 thin snow, NM6 canopy truncation and the melt-out heat fix also dropped: `pr1-noahmp` f051b17a, 7 commits, on the fork; the 10-commit version kept as `pr1-noahmp-10`. The combine snow-heat commit had refined NM5's block, so its NM5 hunk was removed (interdiff = that hunk only) and its message reworded; module syntax-checked (known-bad fails). Its 3.9e-4 → 4.3e-8 W/m² soil-energy measurement included NM5; re-measure with the 0b RT rerun. The 0b track merge (`pr1-0b`, fork and series) and its RT still include NM8, so they are rebuilt and rerun before the 0b WM PR. WM issue posted as ufs-community/ufs-weather-model#3404 (staged plan, `post/bodies/01_WM_ISSUE_staged.md`).

**#390 merged (23 Oct 16:58Z, `ufs/dev` 9b65688c; ufsatm #1138 merged 21:25Z; WM #3355 still open, `test_changes.list` lists no #390 changes).**
- **What it touches:** `mlm` (default false), the `progomega` "updraft memory" path, and shallow SAMF zeroing `cnvw`, `cnvc`, `ud_mf`, `dt_mf` only in its own columns (deep zeroes them for all columns first).
- **Our branches:** SA1 cherry-picks onto 9b65688c with an identical patch-id (local scratch only, not pushed); #390 does not touch its lines. The 0b SAMF PR, which was waiting on #390, is unblocked.
- **Review findings:**
  - MLM conservation (`conservation/upchk/report.md`): smoothing at `mfscuq_mlm.f` L524 not conserving; `−ΔF/dz` without density and with layer `k+1`'s `dz`; `ntsw`/`ntinc` are full-tracer indices used on the vdiff arrays.
  - The `progomega` re-enable (deep L1897–1909, shallow likewise) can revive a column that failed `jmin < ktcon`, with its `jmin` ≥ `ktcon`; columns switched off before `ktcon` is computed are caught by `sumx = 0`.
  - Shallow writes `omegaout` without `present()`.
- **MLM issue posted** as ufs-community/ccpp-physics#404 (23 Oct; body `post/issue_390_mlm_body.md`, fix `post/issue_390_mlm_fix.diff`, compiled only).

**#403 horizontal-diffusion leak (23 Oct).** Posted on ccpp-physics#403 ([comment 6370545905](https://github.com/ufs-community/ccpp-physics/pull/403#issuecomment-6370545905), text `post/reply_403_1.md`). `diff3d` tendencies cancel per unit area (1e-17 of the gross) but are applied to mixing ratios, so the mass-weighted net is 0.05–2.7 % of the gross (C96 24 h: T −1.5e-3 W/m², `sphum` −1.3e-5 kg/m², `o3mr` +6.8e-9 of its mass). Proposed: `q·delp` face fluxes. Measurements: `conservation/upchk/report.md`. Not raised: in `diff3d` the gradient is the difference of `q·dx` across a face, so a uniform tracer may get a tendency where `dx` varies (read from the code, not measured).

**SA1 with the floor: result (23 Oct). Posted as ufs-community/ccpp-physics#405** (head `pera-noaa:pr1-sa1` e4586ec6 on `ufs/dev` 9b65688c, body `post/bodies/11_PR_SA1.md`; merge after #403). Both conditions hold.
- Events above 4 K per step (`q_step.py`): 48 h, devB 22 per member (max 8.6 K, CFL ≤ 2.79), devBS 12 (max 7.9 K, CFL ≤ 2.85); 6 h and `progsigma` true about 0 in both. All 80 runs finished. With the floor, SA1 lowers the event rate rather than raising it 1.7×.
- Precipitation (`q_pr_ens.py`, devBS − devB, members spread by 0.03 %): 6 h −1.16 % ± 0.01 %; 48 h run mean −0.79 %; 48 h `progsigma` true −0.67 %.
- Water counter (`q_w.sh`, `q_w.py`; q/devBW, q/devBSW = devB, devBS + a counter of the water the unfixed cloud-base subtraction creates, W = `xmb·dt2·[eta(kb)(qo(kb) − q̂) + edto·etad(jmin)(qo(jmin) − q̂)]`, deep and shallow, parent grid; the counter leaves 6 h precipitation within 0.05 % of devB, devBS):

| run | W / convective rain | W / precipitation | Δ convective rain (BSW − BW) / W | Δ precipitation / W |
|---|---|---|---|---|
| 6 h (c1000, c999) | 1.64 % | 1.28 % | −0.83 | −0.89 (−1.14 %) |
| 48 h | 1.59 % | ≈ 1.24 % (taking convective rain as 78 % of the total, as at 6 h; the sfcf buckets do not tile 48 h) | −0.81 | ≈ −0.64 |
| 48 h `progsigma` true | 1.41 % | — | −0.69 | — |

  SA1 removes about 1.3 % of precipitation as created water; convective rain falls by 0.7–0.8 W in every configuration, total precipitation by 0.9 W at 6 h. The drop is SA1's own signal. Column-level |W| is 2.5–2.7 % of convective rain, so the term has both signs and nets positive. In the nest W is 1.5–1.8 % of convective rain. In HAFS this is twice the 0.8 % of convective rain quoted for our C96 GFS configuration (`post/reply_401_lisa2.md`).

Domains and time (`q_where.py`, MPI ranks 0–239 parent, 240–359 nest): events and `eta` > 1.2 in both grids, from the first
hour and rising to hour 6.

## Alternatives

Fixes with a simpler or less visible alternative. Tested ones run as `attr/` units (develop pins plus the PR with the
alternative) against the PR as proposed.

| Fix (track) | Proposed | Alternative | Test | Result |
|---|---|---|---|---|
| Once per time step: NM2, SI1 (both 1d) | optional `iter` (`ccpp_loop_counter`) in `noahmpdrv` and `sfc_sice`; NM2 needs NOAA-EMC/noahmp's driver copy to declare it (else `control_p8_atmlnd` crashes) | the cause, one clause of `GFS_surface_loop_control_part2`: the water's second pass re-flags cells that are also Noah-MP land or icy. Do not re-flag them (for ice the commented-out original clause, `.not. icy`). One line, no interface change, no noahmp PR; the water part of those cells loses its low-wind second NSST pass | `g_nmalt`, `g_sealt` (6 global tests incl. `control_p8_atmlnd`); land and sea-ice state vs develop and vs the proposed fix (`cmp_land.py`, `attr/cmp_nmalt.txt`, `cmp_sealt.txt`) | **equivalent within noise**: Noah-MP's land signal is reproduced (land means of soilm −0.51, weasd +0.21 kg/m², snod +0.005 m, the same to 4–5 digits; rms alt − proposed 0.41–0.59 kg/m² against the 2.6–3.2 signal); sea ice at C48 rms alt − proposed 5.7 × 10⁻⁴ m against 2.8–3.0 × 10⁻³; precipitation and 3-D T within noise; `control_p8_atmlnd` runs without the noahmp change. Two forms, so both are in phase 1 (1d); the PR offers the loop-control form first (no noahmp PR) |
| Settled cloud water: TH2 (1e) | counted as rain (`regional_control` precipitation +10.9 %, the atmosphere unchanged) | no cloud settling out of the lowest layer: the water stays in the air (TEMPO v3 tracks the flux as `cloud_precip`, used only in its freezing-rain diagnostic) | `thB` (8 regional outliers) vs the Thompson PR (`attr/attr_thB_table.txt`) | both conserve, so phase 1 (1e), both forms stated, counting recommended: `regional_control` +4.8 % instead of +9.2 % (the kept cloud rains out later), the other 10 runs within 0.25 % of the PR (`cpld_regional_atm_fbh` the same, −2.6 %); it suppresses cloud deposition at the ground, which TEMPO tracks. Stated in the PR text (descriptions §3.2) |
| Clipping, R1: TH6, TH7 (1e) | condensate and sub-R1 water to vapour with latent heat; R1 also reworks `semi_lagrange_sedim` and the no-microphysics return (116 lines) | hold one or both for round 2 | not needed: effects measured (+0.002 %; 2 × 10⁻⁸ of precipitation) | phase 1 (1e): where the water goes is a choice |
| TEMPO driver (0c) | alone | with the NCAR/TEMPO fixes: the driver fix exposes TEMPO's own +0.33 % residual | — | timing |
| Mass basis: Thompson, TEMPO, GFDL MP v3 | three local fixes | one shared conversion | — | kept local: three owners |
| SAMF overshoot (0a) | — | options A, B and the CFL bound to `ktcon` (*HAFS crash*, fix options) | done | A; the bound to `ktcon` = A; B does not help |

No better alternative found for SAMF fusion heat (detraining liquid is a larger change), the PBL flux basis, wet
deposition, the CA trigger, the SAMF32 build, GFDL MP v3 and the other Noah-MP fixes.

## Known constraints

- **Lustre I/O errors (investigated 21 Oct; report `tm5-zoom/docs/hpc_catalog/reports/2026-10-21_hercules_work2_io_errors.md`,
  MSU and DDN drafts beside it, nothing sent)**: 198 EIO in 191 of ~2,200 staging attempts on `dtn-1/2/3` since at least
  15 Oct, 102 files on 36 OSTs over all 8 OSSes, in bursts, almost always in the first 256 KiB; nothing in the client
  logs. Not our data, quota, one OST/OSS or node. Client vs server code not yet separated (`$P/lustre_probe/repro.py`
  staged, to run when no RT is staging). **Correction:** 0c had 20 failed attempts and the 19–20 Oct runs 36, hidden by
  ecflow's `ECF_TRIES 2` retry; the table below lists only tests lost after the retry. The third 0b run had 26 of 290
  attempts fail. Project quota: 717.6 of 727.2 TB soft (98.7 %).
  Original note: in the 0b track RT, `run_test.sh` failed to stage inputs with
  `cp: error copying '…' : Input/output error` from EPIC's RT input data
  (`/work2/noaa/epic/hercules/UFS-WM_RT/NEMSfv3gfs/input-data-20260617/`), a different file each time, so the model
  never started (`RUN DID NOT COMPLETE`).

  | Run (21 Oct) | Job, driver node | Tests lost | Logs |
  |---|---|---|---|
  | 0b, first | 10187047, `dtn-2` | 3: `atm_ds2s_docn_pcice_intel`, `atmaero_control_p8_intel`, `control_csawmg_gnu` | `rt_logs_t0b_run1/` |
  | 0b, rerun | 10189670, `dtn-2` | 6: `atmaero_control_p8_intel`, `atmaero_control_p8_rad_micro_intel`, `regional_atmaq_debug_intel`, `hrrr_control_gnu`, `control_csawmg_gnu`, `control_wam_debug_gnu` | `rt_logs_t0b_run2/` |
  | 0c | 10187059, `dtn-3` (concurrent with the first 0b run) | none (20 attempts failed and were retried) | `rt_t0c/tests/logs/` |
  | 0b, third | 10190986, `dtn-3` | TIMEOUT at 8 h (34 of 288 tasks undone; our SAMF queue load) | `rt_logs_t0b_run3/` |
  | 0b, fourth | 10194598, `dtn-1` | cancelled 22 Oct ~01:45Z (Ash: Lustre work first; rerun tomorrow, then only the gaps with `-l`) | `rt_logs_t0b_run4/` |
  | 0b, fifth | 10200567 (22 Oct 17:08 CDT; `sj` label `p0-0b-run5`) | driver now `--mem=64G` with `unset SLURM_MEM_*` (the Lustre EIO workaround; `rt_t0b.sbatch.pre_mem` is the old one); watched with `sj watch` | **complete** (17:08–19:42 CDT): 54 compiles pass, 118 identical, 101 changed, 15 restart/IAU children not started (each parent changed), **none lost**; 0 `Input/output error` in any test log; the changed set = run 1's 98 + its 3 lost = run 2's 96 + its 5 lost (`rt_logs_t0b_run5/`) |

  Files that failed: `INPUT_L127_gfsv17/sfc_data.tile{1,2,5}.nc` and `gfs_data.tile5.nc`, `FV3_fix/aerosol.dat`,
  `qr_acr_qsV2.dat`, `global_o3prdlos.f77`, `global_slmask.t1534.3072.1536.grb`, `MERRA2_y14_24/merra2_1423_{01,11}.nc`,
  `aer_data/LUTS/optics_OC.v1_3.dat`. Afterwards they read cleanly from the login node, and 60 files each from `dtn-2`
  and `dtn-3` (one-task `srun`). So: intermittent, probably under RT staging load; not reproduced by a single reader.
  To do: time-stamp the failures against the node's Lustre client logs or HPC status (an OST or MDS event?); check
  whether `dtn-2` saw more than `dtn-3`; try staging with many parallel readers; report to the Hercules helpdesk with
  the times and paths if it is the filesystem. The full RT of the 37 (19–20 October) had none.
- **ecflow**: `rt.sh` starts its server on the job's node at port uid + 1500. Two runs on one node collide (the
  second exits within seconds). Concurrent runs go to different `service` nodes, or (scratch clones only) `rt.sh`
  takes an offset, `$(( $(id -u) + 1500 + ${ECF_OFF:-0} ))`, as in `attr/`.
- **Stale lock**: `scancel` of an `rt.sh` job leaves `tests/lock`; the next run exits in 0 s. Remove it first.
- **Hashes in the RT log**: `rt.sh` records the submodule hashes when it finishes, so the RT trees must sit on the
  final commits; after any commit rewrite, `git reset` the RT trees (source unchanged) before the run ends.
- **Disk**: RT outputs kept: `rt_final4` 3.4 TB (the 37; evidence only, no longer a WM PR log), `rt_repro4` 565 GB,
  `rt_noise` 118 GB, and the `attr/` units. Earlier generations are deleted; their logs are in `rt_logs_pre_samfcfl/`
  and `rt_logs_samfcfl/partial/`.
- **TEMPO**: TH5's twin (`ports/TEMPO-driver/0002`, layer depth) is not included: not measured alone in UFS, and it
  adds a `.meta` argument.

## Procedure

Sources (read 19 October 2026): the WM wiki pages *Making Code Changes in the UFS Weather Model and Its
Subcomponents*, *Expectations for Developers* and *Testing Expectations & Commit Queue* (edited 2026-10-05); each
repository's PR template; the CCPP Technical Documentation, *Code Management*.

**Order.**
Posting bundle for 0a, 0b, 0c (bodies in template order, `gh` commands, prerequisites): `post/POSTING.md`.
1. The SAMF issue (posted, #401). The ufs-weather-model issue (every PR must link one; all four tracks link the same
   issue) right before the first PRs, once the WM PRs it names can follow; the GFDL issue (their guide asks for one)
   with 1c. Then the tracks in the order of *Tracks*.
2. Per track, PRs from forks, lowest repository first: ccpp-physics `ufs/dev`, GFDL `dev/emc`, NOAA-EMC/noahmp
   `develop`; then NOAA-EMC/ufsatm `develop`; then ufs-weather-model `develop`. The ufsatm and WM PRs point
   `.gitmodules` at our fork branches while open; the last commit before merge restores `.gitmodules` and sets the
   merged hashes. CI (`tests/ci/repo_check.sh`) fails if a submodule branch is behind its authoritative head.
3. Each WM PR lists its track's sub-PRs under "Sub component Pull Requests".
4. Per track: its PRs merge the same day, bottom up, after that track's WM testing.

**What we run, per track.** Full `./rt.sh -a lpdm -e` on the latest code, Intel and GNU, on Hercules ("acceptable
alternative" to Ursa), **without `-c`**. Commit `tests/logs/RegressionTests_hercules.log` and `tests/test_changes.list`
(even if empty). `BL_DATE` is 20261008 (or the current one when the track is run). Code managers make the baselines
and run the other machines (Jenkins `*-RT` labels).

**Templates.** WM: description, commit-message tree, priority, Git Tracking, documentation, Regression Test Changes
(**Updates/Changes Baselines**), input data, subcomponent branch changes, library changes, the Commit Queue checklist
and the **GenAI disclosure** (its "reviewed by NWS staff" box stays unchecked: OMD code managers then review).
ccpp-physics: description, tests (may point to the WM PR), dependencies, documentation. ufsatm: description incl.
whether answers change, testing, dependencies. GFDL: description / Fixes #, how tested, a 6-item checklist.
NOAA-EMC/noahmp: none.

**Labels** (code managers): `CCPP`, `UFSATM`, `NMP`, `Baseline Updates`; `Ready for Review` (2+ approvals) →
`Ready for Commit Queue` → `In Testing` → merge. Queue: priority, then oldest first (Project 70).

**Approvals.** WM 2 (enforced); ufsatm 2 observed; ccpp-physics 3 observed.

**Not ours.** DTC ports merged `ufs/dev` changes to NCAR/ccpp-physics `main` (about 5 weeks later).

**Timing.** Recent answer-changing chains: FRAM (ccpp-physics#387 → ufsatm#1137 → WM#3351), about 6 weeks; SAMF
single precision (ccpp-physics#384 → ufsatm#1133 → WM#3341), 5 weeks.

**Not verified.** Branch-protection review counts on ccpp-physics and ufsatm; whether contributors can set `*-RT`
labels. The wiki's label section is stale. Whether gatekeepers prefer one baseline change or one per track.
Global P8 of 0b as one unit: the singles add within 0.0011 K, and 1d alone is ≤ 0.0008 K.

Earlier versions, with the single-bundle plan, the red-team findings and their evidence: `pr_round1.history.md`.
