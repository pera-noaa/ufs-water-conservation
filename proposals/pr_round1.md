# PR round 1: the obvious bug fixes

*Plan and evidence for the first round of upstream changes, from the water proposal (`water_closure_proposal.md`) and
the conservation follow-on (`conservation_proposal.md`, series rows in `../experiments/conservation/replay/SERIES.md`). Per-item
posting state: `../upstream/POSTING.md`; roadmap: `../upstream/ROADMAP.md`. Issue and PR texts: `pr_round1_descriptions.md`; round 2:
`round2_issues.md`; every unposted item, tiered: `triage_unposted.md`. Hercules root `$U/pr1` (`$U` =
`/work2/noaa/co2/ash/ufs-chem-v1/upstream`). Earlier versions, verbatim: `pr_round1.history.md`.*

## Status (12 November 2026)

| Item | State |
|---|---|
| Posted | Phase 0 (tracks 0a, 0b, 0c), as ufs-community/ccpp-physics issue #401 (SAMF) and PRs #405 (SA1), #406 (Thompson), #407 (TEMPO driver), #408 (SAMF + PBL), #409 and #410 (Noah-MP), #413 (GFDL MP v3), #414 (`xlamue` floor, the #401 fix); issue #404 (MLM); ufs-weather-model issues #3404 (staged plan) and #3406 (FPE). #404's description now carries a tested fix (RT pass with `mlm` on); found with it, NCAR/ccpp-physics#1251 (`shinhongvdif` stale index). Upstream of the UFS copies: NCAR/noahmp#274 (snow heat), GFDL_atmos_cubed_sphere#430/#431 (`sedi_heat`) |
| Approved | #405, #406, #407, #408, #414. None merged |
| Packaging | The per-track ufsatm/WM PRs are replaced by one pair per package (the code managers' request): 1 SAMF/PBL (#405, #408, #414; NOAA-EMC/ufsatm#1156 + ufs-community/ufs-weather-model#3408, draft), 2 microphysics (#406, #407, #413), 3 Noah-MP (#409, #410). Package 1's full RT is done (`../upstream/POSTING.md`, `rt_sxd5`); merge order against #403, which re-implements #405, #408 and #414, asked on #405 |
| Not posted | 1c (6 fixes), 1d (6), 1e (3), SAMF32 (no ufsatm slot since packaging); NM5, NM6, NM8 and the melt-out heat fix, dropped from phase 0 because where truncated water or heat goes is a choice |
| 1d | The HAFS hold is cleared by its pre-registered criterion with the #414 floor; the clearance depends on #414 merging first (`../experiments/runs_29oct/1d_hafs.md`) |
| 1c | CP1 and FV2 do not pass F under the pre-registered rule; whether CP1's dose response suffices is open, Ash's call (`../experiments/runs_29oct/1c_wofs.md`) |
| Elsewhere | Round 2: `round2_issues.md`. Ports: `patches/ports/README.md`. Re-measurements of 29 October: `../experiments/runs_29oct/` |

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
pre-existing SAMF instability. What each track changes (the 37's measurements, *Checks*):

| Order | Track | PRs | Fixes | Answer change | HAFS | Reviewers who decide |
|---|---|---|---|---|---|---|
| 0 | **0a** SAMF issue | ccpp-physics issue (descriptions §8) | — | — | the cause | @JongilHan66 |
| 0 | **0b** global conservation | SAMF + PBL, Noah-MP (without NM2), GFDL MP v3; ufsatm (SAMF32 + bump); WM | 18 | global: 3-D T +0.002 to +0.005 K, all from SAMF + PBL's ice-fusion heat (the bug's own signal; without NM2 +0.001 to +0.006 K); regional: SAMF + PBL bitwise, Noah-MP ≤ 0.02 % | 0 of 20 crash, as develop | EMC global physics (GFS, HAFS) |
| 0 | **0c** microphysics | Thompson (TH1, TH3, TH4, TH5), TEMPO driver; ufsatm bump; WM | 5 | created water removed: regional precipitation −0.9 to −5.3 % (`regional_control` −1.4 %), WoFS −2.0 % (TEMPO) | not touched (0b + 1d + FV3 = the 37, bitwise in 10 members) | Thompson/TEMPO owners, RRFS/HRRR |
| 1 | **1c** dycore | FV3 (GFDL `dev/emc`); ufsatm bump; WM | 6 | WoFS 0.2–0.8 % per commit (0.7–2.4× noise), `cpld_regional_atm_fbh` −1.4 % | FV3 alone 0 of 3; with 0b + 1d = the 37 (1 of 10) | GFDL maintainers, then EMC |
| 1 | **1d** surface iteration, sea ice, NSST | NM2 (+ NOAA-EMC/noahmp in the `iter` form), sea ice/NSST; ufsatm bump; WM | 6 | global ≤ 0.0008 K, ≤ 0.13 %; regional ≤ 0.7 % (sea ice/NSST); NM2: land no longer gains 3–5 % of global precipitation (the bug's own signal) | with 0b: 3 of 20 crash, RT member included | @wd20xw @XuLi-NOAA, @barlage @cenlinhe, EMC |
| 1 | **1e** Thompson, second forms | TH2, TH6, TH7 (`pr1-thompson_p1`); ufsatm bump; WM | 3 | TH2: `regional_control` +10.9 % reported precipitation (settled cloud counted; keeping it in the air instead: +4.8 %); TH6, TH7 ≤ 0.002 % | not touched | Thompson owners |

| Track | As posted | State |
|---|---|---|
| 0a | ccpp-physics#401; its fix, the `xlamue` floor, is #414 | #414 approved, package 1 |
| 0b | SAMF + PBL #408 (package 1), GFDL MP v3 #413 (package 2), Noah-MP #409 and #410 (package 3); SAMF32 not posted | #408 approved |
| 0c | Thompson #406, TEMPO driver #407 (package 2) | both approved |
| 1c | not posted | needs a `dev/emc` merge; CP1, FV2 F gap (*Status*) |
| 1d | not posted | after #414; the form of NM2 and SI1 (*Alternatives*) |
| 1e | not posted | after package 2; the owners' choice of form |

Every PR compiles alone on `develop`, so the sets are independent. The 37's regression (`rt2`, `rt_logs_37/`) is
evidence for all of them, not a WM PR log. 1d's separation from 0b rests on 20 members and the RT member passing, not
on an identified cause (*HAFS crash*).

## The PRs

`W01`–`W19` are water diffs (`../patches/`); bare numbers are conservation series rows
(`experiments/conservation/replay/patches/`).

| PR | Track | Repository | Fixes | Owners | Notes | Posted |
|---|---|---|---|---|---|---|
| SAMF + PBL | 0b | ccpp-physics `ufs/dev` | D3A (07), F3 01a (23), PBL05 (52), SAMF08 (55) | @JongilHan66 @lisa-bengtsson | D3A adds `hfus`. After #390 | #408 |
| Noah-MP 1 | 0b | ccpp-physics | NM3, NM4 (W10, W11); NM12 (12) | @barlage @cenlinhe; code managers for the interstitials | NM12 = NCAR/noahmp@218eb5a (#47), never synced to the UFS copy | #409 |
| Noah-MP 2 | 0b | ccpp-physics, stacked on Noah-MP 1 (both edit `combine`) | NM1 (W08); SL2, CS1, CB1 (38–40) | @barlage @cenlinhe | CB1 = CTSM's `Combo`; SL2, CS1, CB1 also go to NCAR/noahmp v5 (same three defects). NM5, NM6, NM8, NP1: later round (*NM8 dropped*, in the history) | #410; SL2, CS1, CB1 also NCAR/noahmp#274 |
| Surface iteration, sea ice, NSST | 1d | ccpp-physics (+ NOAA-EMC/noahmp `develop` in the `iter` form) | NM2 (W09) + 09b; SI1, SI2, FL1 (31, 32, 36); QR1 (34) | @wd20xw @XuLi-NOAA @barlage @cenlinhe | NM2 and SI1: `iter` argument, or one clause of `GFS_surface_loop_control_part2` (*Alternatives*); the `iter` form of NM2 needs 09b (the land component crashes without it) | — |
| GFDL MP v3 | 0b | ccpp-physics | GFDL02, GFDL07 (49, 54) | @RuiyuSun | GFDL02 in the CCPP wrapper: GFDL MP returns its species on an updated `delp` that the wrapper discarded, so the wrapper rescales them by `delp_out/delp_in` and GFDL's module stays as upstream (column test `../upstream/gfdl_wrap/`). GFDL07's bug is also in GFDL's own `gfdl_mp.F90` (report it there) | #413; GFDL07 also GFDL_atmos_cubed_sphere#430/#431 |
| Build | 0b | NOAA-EMC/ufsatm `develop` | SAMF32 (25) + 0b submodule bump | @rhaesung (author of ufsatm#1133, also a ccpp-physics code manager) | answers change in the `_conv32` tests | — (no slot: #1156 carries no ufsatm code) |
| Thompson | 0c | ccpp-physics | TH1, TH3, TH4, TH5 | @gthompsnWRF @RuiyuSun @AndersJensen-NOAA | TH5 adds `prsi` (in the hosts) | #406 |
| Thompson, second forms | 1e | ccpp-physics | TH2, TH6, TH7 | @gthompsnWRF @RuiyuSun @AndersJensen-NOAA | on top of 0c's Thompson PR | — |
| TEMPO driver | 0c | ccpp-physics | TH1's twin in `mp_tempo` (`ports/TEMPO-driver/0001`) | default owners | exposes TEMPO's own +0.33 % residual (fixes at NCAR/TEMPO, unmerged). After #389 | #407 |
| FV3 | 1c | GFDL_atmos_cubed_sphere `dev/emc` | FX1, SG1, CP1, FV2, INLQ (01, 02, 03, 05, 29); FV1 (W19) | maintainers (no CODEOWNERS) | `dev/emc` merges rarely (last 5 August) | — |
| ufsatm bump | 0c, 1c, 1d, 1e | NOAA-EMC/ufsatm `develop` | submodule bump | ufsatm code managers | no code | one per package; package 1 NOAA-EMC/ufsatm#1156 |
| WM | 0b, 0c, 1c, 1d, 1e | ufs-weather-model `develop` | submodule bumps, RT log, `test_changes.list` | gatekeepers | one per track | one per package; package 1 ufs-community/ufs-weather-model#3408 |

Every ccpp-physics PR also gets the default owners (@grantfirl @rhaesung @Qingfu-Liu @dustinswales).

**Moved to round 2 by the red team** (issues 6–8 in `round2_issues.md`):

| Fix | Why not round 1 |
|---|---|
| R1 (04) | two new `Radtend` fields; ccpp-physics CI runs capgen against NCAR/ccpp-scm `main` and ufsatm `develop`, so the host fields must merge first (and the MPAS host, #397) |
| TOPT (26) | overlaps #397's `tend_opt` restructuring; option 4 → error is a design choice |
| MYNN01, MYNN01b (47, 48) | #392 replaces `module_bl_mynn.F90` with the NCAR/MYNN-EDMF submodule |

**SA1 and the SAMF cap** (held for the SAMF instability issue, ufs-community/ccpp-physics#401):

| Change | Why held | Outcome |
|---|---|---|
| SA1 (W01), `pr1-sa1` | alone raises the HAFS overshoot rate 1.7× and lowers HAFS precipitation 1.25 % (fails rule 4 there) | with the floor, events 22 → 12 per member at 48 h and precipitation −0.8 to −1.2 %, the water it stops creating (*HAFS crash*); posted as #405 |
| SAMFCFL, `pr1-samfcfl` | our cap (option A); a new limit (rule 2); deep only | superseded by the `xlamue` floor, #414 |

## Branches and patches

Posted heads and the package branches: `../upstream/POSTING.md`. Local tree `$U/pr1/series` (a copy of the pristine clone
`$U/pr1/ufs-weather-model`); patches `../patches/pr_round1_patches/` = `$U/pr1/cut/` (`git format-patch` per branch, 76 files).
The full branch table and the build recipe: `pr_round1.history.md`, *Branches and patches* of the 29 October version.
Branches for what is not posted:

| Set | Branch | Base |
|---|---|---|
| 1c | GFDL_atmos_cubed_sphere `pr1-round1` (6 commits) | `dev/emc` 71ff473b |
| 1d | ccpp-physics `pr1-noahmp_p1` (NM2 on `pr1-noahmp`), `pr1-seaice_nsst` (4); NOAA-EMC/noahmp `pr1-round1` (09b, `iter` form only) | `pr1-noahmp`; `ufs/dev` d9b70feb; noahmp `develop` 2c7b3bc2 |
| 1e | ccpp-physics `pr1-thompson_p1` 4afaf48a (TH2, TH6, TH7 on the posted #406 head 0e22f8c2; not compiled on the new base) | `pr1-thompson` |
| SAMF32 | ufsatm `pr1-round1` (SAMF32 + bump of all; 447ff08) | `develop` aa0ba811 |
| Dropped from phase 0 | `pr1-noahmp-withNM8` (NM8), `pr1-noahmp-10` (NM5, NM6, NM8, melt-out) | — |

- **Commits**: author and committer `Ash Pera <ashley.pera@noaa.gov>`; message = defect, fix, measured effect (water
  messages from `git/ufs-dev/all` and the FV3 series, the rest in `$U/pr1/msgs/`); then the paragraph
  `Part of a water-conservation project for UFS physics (NOAA GML / CIRES).`; last line
  `AI-assisted: written with Claude Opus 5.5; reviewed by author`.

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
| HAFS rerun with the #414 floor (`../experiments/runs_29oct/1d_hafs.md`; pre-registered) | 0b + floor + sea ice/NSST 0 of 20 crash, 0b + floor 0 of 20; overshoot tail gone in both (one event > 4 K); 0/20 vs 3/20 is p = 0.115, and the floor removes the path that crashed, so 1d's clearance depends on #414 merging first | any crash |

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
| WoFS re-measured (`../experiments/runs_29oct/1c_wofs.md`): 10-member noise ensemble, dose a ∈ {±1, ±2} | supersedes the ratios above: σ_n 0.33 % (`regional_wofs_tempo`), 0.27 % (`regional_wofs`), so the single samples were one noise draw; CP1 slope −0.52 %/unit (z −5.0), FV2 inside 2σ_n; neither passes F under the pre-registered rule | dose response absent |

## HAFS crash

With the 38 (incl. SA1), `hafs_global_1nest_atm_intel` stopped at 5 h 28 min 30 s (`compute_qs` table overflow): SAMF
deep convection heats one cell by +70.72 K in one step. The full study, with every run, Han's test, the red team
R1–R14, the surveys and the 48-h ensembles, is in `pr_round1.history.md` (29 October version, *HAFS crash*); trees in
`$U/pr1/q/`, runs in `$U/pr1/hafs_exp/q_*`, scripts and statistics in `../experiments/hafs_samf/`.

**Mechanism** (upstream; `samfshalcnv` has the same code):
1. Below cloud base `eta(k) = eta(k+1)/(1 + (xlamue - xlamud) dz)`, with `xlamue = clamt/z` and `xlamud = 0.001 clamt`.
   Above about 1 km detrainment wins, so for elevated convection `eta` grows downward (101 at `kb`).
2. The TKE scaling holds `clamt` at its cap (15 × `clam`). The overshoot feeds TKE, which keeps it there.
3. `xmbmax` limits CFL only at `kbcon`, where `eta` = 1.

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

**Outcome.**

| Question | Answer |
|---|---|
| Is the instability ours? | No. Develop reaches 39 K in one step at 6 h and, at 48 h, crashes in 6 of 10 members (Fisher one-sided p = 0.005) |
| The fix | F, `crtlame`·max(1, `clamt`/`clam`), which at `clam_deep` = 0.1 equals Han's form `xlamue` ≥ max(`crtlame`, 0.001·`clamt`) in deep: no step above 4 K in 20 members at 6 h, 0 of 10 crash at 48 h (develop 6); in the 12 surveyed RTs it removes every sub-cloud `eta` > 1.2 and all but one CFL > 5 step, precipitation +0.01 to +0.40 % (one run each, all positive). Posted as #414, approved |
| Han's test C (`eta`, `etad` ≤ 1) | no crash, but CFL-limited cloud-base heating of about 6 K per step independent of `dt`; precipitation −8.1 % |
| Option A (SAMFCFL) | 0 crashes, precipitation −0.18 %; a new limit (rule 2); superseded by #414 |
| 2a95266 (#403's floor) | fixes the instability as F does; its precipitation change is 2–40× F's (HAFS regional +1.7–1.8 %) |
| `progsigma` = true (operational HAFS v2.1, GFS v17 P8) | develop has no event above 4 K |
| SA1 with the floor | events 22 → 12 per member at 48 h; precipitation −1.16 % at 6 h (0.89 of the water the unfixed subtraction creates, which is 1.28 % of precipitation) and −0.79 % at 48 h. Posted as #405 |
| Open (triage #75) | which of 2a95266's three parts moves precipitation; residual 4–9 K steps at CFL 1–5.4 (not diagnosed); shallow not floored |

## Others' PRs met in round 1

| PR | Finding | Posted | Since |
|---|---|---|---|
| #390 MLM (merged) | the MLM smoothing does not conserve: −1.28 W/m² with `mlm` on | issue #404 | the drafted fix crashes as written; with an index guard it conserves (`../experiments/runs_29oct/mlm_diff3d.md`) |
| #403 TTE-EDMF | `diff3d` tendencies cancel per area, not per mass: net 0.05–2.7 % of the gross | comment on #403 | the proposed face flux closes only when divided by the physics' own layer mass (`../experiments/runs_29oct/mlm_diff3d.md`) |
| #405 review | Han: the subtraction keeps `dellaq(kb)` and `dellaq(jmin+1)` zero | answered: the leak is at `kb+1` | #405 approved |

## Alternatives

Fixes with a simpler or less visible alternative. Tested ones run as `attr/` units (develop pins plus the PR with the
alternative) against the PR as proposed.

| Fix (track) | Proposed | Alternative | Test | Result |
|---|---|---|---|---|
| Once per time step: NM2, SI1 (both 1d) | optional `iter` (`ccpp_loop_counter`) in `noahmpdrv` and `sfc_sice`; NM2 needs NOAA-EMC/noahmp's driver copy to declare it (else `control_p8_atmlnd` crashes) | the cause, one clause of `GFS_surface_loop_control_part2`: the water's second pass re-flags cells that are also Noah-MP land or icy. Do not re-flag them (for ice the commented-out original clause, `.not. icy`). One line, no interface change, no noahmp PR; the water part of those cells loses its low-wind second NSST pass | `g_nmalt`, `g_sealt` (6 global tests incl. `control_p8_atmlnd`); land and sea-ice state vs develop and vs the proposed fix (`cmp_land.py`, `attr/cmp_nmalt.txt`, `cmp_sealt.txt`) | **equivalent within noise**: Noah-MP's land signal is reproduced (land means of soilm −0.51, weasd +0.21 kg/m², snod +0.005 m, the same to 4–5 digits; rms alt − proposed 0.41–0.59 kg/m² against the 2.6–3.2 signal); sea ice at C48 rms alt − proposed 5.7 × 10⁻⁴ m against 2.8–3.0 × 10⁻³; precipitation and 3-D T within noise; `control_p8_atmlnd` runs without the noahmp change. Two forms, so both are in phase 1 (1d); the PR offers the loop-control form first (no noahmp PR) |
| Settled cloud water: TH2 (1e) | counted as rain (`regional_control` precipitation +10.9 %, the atmosphere unchanged) | no cloud settling out of the lowest layer: the water stays in the air (TEMPO v3 tracks the flux as `cloud_precip`, used only in its freezing-rain diagnostic) | `thB` (8 regional outliers) vs the Thompson PR (`attr/attr_thB_table.txt`) | both conserve, so phase 1 (1e), both forms stated, counting recommended: `regional_control` +4.8 % instead of +9.2 % (the kept cloud rains out later), the other 10 runs within 0.25 % of the PR (`cpld_regional_atm_fbh` the same, −2.6 %); it suppresses cloud deposition at the ground, which TEMPO tracks. Stated in the PR text (descriptions §3.2) |
| Clipping, R1: TH6, TH7 (1e) | condensate and sub-R1 water to vapour with latent heat; R1 also reworks `semi_lagrange_sedim` and the no-microphysics return (116 lines) | hold one or both for round 2 | not needed: effects measured (+0.002 %; 2 × 10⁻⁸ of precipitation) | phase 1 (1e): where the water goes is a choice |
| TEMPO driver (0c) | alone | with the NCAR/TEMPO fixes: the driver fix exposes TEMPO's own +0.33 % residual | — | timing |
| Mass basis: Thompson, TEMPO, GFDL MP v3 | three local fixes (GFDL MP's in the CCPP wrapper, its module untouched) | one shared conversion | — | kept local: three owners |
| SAMF overshoot (0a) | — | options A, B and the CFL bound to `ktcon` (*HAFS crash*, fix options) | done | A; the bound to `ktcon` = A; B does not help. Superseded by the `xlamue` floor (#414) |

No better alternative found for SAMF fusion heat (detraining liquid is a larger change), the PBL flux basis, wet
deposition, the CA trigger, the SAMF32 build, GFDL MP v3 and the other Noah-MP fixes.

## Known constraints

- **Lustre I/O errors on Hercules `/work2`**: 198 EIO in 191 of ~2,200 RT staging attempts on `dtn-1/2/3` from at
  least 15 October, 102 files on 36 OSTs over all 8 OSSes, in bursts, almost always in the first 256 KiB; ecflow's
  `ECF_TRIES 2` retry hides most of them. An RT driver run with `--mem=64G` and `unset SLURM_MEM_*` lost no test.
  Report: `tm5-zoom/docs/hpc_catalog/reports/2026-10-21_hercules_work2_io_errors.md` (MSU and DDN drafts beside it,
  nothing sent). Per-run table and failed files: `pr_round1.history.md`, *Known constraints* of the 29 October version.
- **`--mem` on an RT driver** is exported as `SLURM_MEM_PER_NODE`, and the test jobs' `srun` refuses it beside their
  per-CPU memory: unset it in the driver's sbatch.
- **ecflow**: `rt.sh` starts its server on the job's node at port uid + 1500. Two runs on one node collide (the
  second exits within seconds). Concurrent runs go to different `service` nodes, or (scratch clones only) `rt.sh`
  takes an offset, `$(( $(id -u) + 1500 + ${ECF_OFF:-0} ))`, as in `attr/`.
- **Stale lock**: `scancel` of an `rt.sh` job leaves `tests/lock`; the next run exits in 0 s. Remove it first.
- **Hashes in the RT log**: `rt.sh` records the submodule hashes when it finishes, so the RT trees must sit on the
  final commits; after any commit rewrite, `git reset` the RT trees (source unchanged) before the run ends.
- **Disk**: RT outputs kept: `rt_final4` 3.4 TB (the 37; evidence only, no longer a WM PR log), `rt_repro4` 565 GB,
  `rt_noise` 118 GB, and the `attr/` units. Earlier generations are deleted; their logs are in `rt_logs_pre_samfcfl/`
  and `rt_logs_samfcfl/partial/`.
- **TEMPO**: TH5's twin (`ports/TEMPO-driver/0002`, layer depth) is not in #407: it adds a `.meta` argument. It is at
  noise in the forecast on TEMPO v3.2.5 (`../experiments/runs_29oct/tempo_v325.md`); #407's body says it can follow once #406's form
  is settled.

## Procedure

Sources (read 19 October 2026): the WM wiki pages *Making Code Changes in the UFS Weather Model and Its
Subcomponents*, *Expectations for Developers* and *Testing Expectations & Commit Queue* (edited 2026-10-05); each
repository's PR template; the CCPP Technical Documentation, *Code Management*.

**Order.** Phase 0 is posted (*Status*). For what follows, packages replace tracks (`../upstream/POSTING.md`):
1. The GFDL issue (their guide asks for one) with 1c. The ufs-weather-model issue #3404 is linked by every WM PR.
2. Per package, PRs from forks, lowest repository first: ccpp-physics `ufs/dev`, GFDL `dev/emc`, NOAA-EMC/noahmp
   `develop`; then NOAA-EMC/ufsatm `develop`; then ufs-weather-model `develop`. The ufsatm and WM PRs point
   `.gitmodules` at our fork branches while open; the last commit before merge restores `.gitmodules` and sets the
   merged hashes. CI (`tests/ci/repo_check.sh`) fails if a submodule branch is behind its authoritative head.
3. Each WM PR lists its package's sub-PRs under "Sub component Pull Requests".
4. Per package: its PRs merge the same day, bottom up, after that package's WM testing.

**What we run, per package.** Full `./rt.sh -a lpdm -e` on the latest code, Intel and GNU, on Hercules ("acceptable
alternative" to Ursa), **without `-c`**. Commit `tests/logs/RegressionTests_hercules.log` and `tests/test_changes.list`
(even if empty). `BL_DATE` is the current one when the package is run (package 1: 20261026, its rerun 20261028). Code managers make the baselines
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
labels. The wiki's label section is stale. Global P8 of 0b as one unit: the singles add within 0.0011 K, and 1d
alone is ≤ 0.0008 K. (Answered: the code managers want one baseline change per package, not one per track.)

## Section register

The file has no § numbers; other documents cite its sections by name (*Tracks*, *HAFS crash*, *Known constraints*).

| Section | Status | Where |
|---|---|---|
| Status | current | head; the 19 Oct status, the 29 Oct *Posted* row and the 29 Oct status table in history |
| Rule for round 1 | current | head |
| Tracks | current; per-track ufsatm/WM PRs superseded by the three packages | head |
| The PRs; Moved to round 2 | current, with posted numbers | head |
| Held for the SAMF instability issue | resolved: SA1 posted as #405, SAMFCFL superseded by #414 | head (*SA1 and the SAMF cap*); history |
| Branches and patches | posted heads superseded by `../upstream/POSTING.md`; unposted branches current | head (summary); history (full table, build recipe, Hercules trees) |
| Checks: whole round, 0b, 0c, 1c | current; the 1c ratios superseded by `../experiments/runs_29oct/1c_wofs.md`, the 0b HAFS row by `../experiments/runs_29oct/1d_hafs.md` | head |
| HAFS crash: mechanism, crash-rate ensembles | current | head |
| HAFS crash: study table, fix options, findings, TKE budget | evidence for #414 | history |
| Reply to Han (#401, 21 Oct); red team R1–R14; 48 h; results; survey; Han accepts the floor; survey F; 2a95266; Lisa's questions | evidence for #414; summarised in *Outcome* | history |
| SA1 with the floor (22 Oct; result 23 Oct) | resolved: #405 | head (*Outcome*); history (water-counter table) |
| NM8 dropped from phase 0 (23 Oct) | current decision | head (*Status*); history |
| #390 merged; #403 horizontal-diffusion leak; #405 dispute | superseded in part by `../experiments/runs_29oct/mlm_diff3d.md` | head (*Others' PRs*); history |
| Comment rewrite (27 Oct) | done | history |
| Alternatives | current | head |
| Known constraints | current; the Lustre per-run table and file list | head; history |
| Procedure | current, per package | head |
| 19 Oct version: single-bundle plan, red-team findings, cancelled pre-red-team runs | superseded | history, lines 1–417 |

Earlier versions, verbatim: [`pr_round1.history.md`](pr_round1.history.md). The 29 October version starts at its
line 423; its line N is history line N + 422.
