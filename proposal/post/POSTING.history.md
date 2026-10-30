# Posting tracks 0a, 0b, 0c: history

Verbatim archive of `POSTING.md` as it stood on 27 October 2026 (plan table, procedure, dated log). The current state is in `POSTING.md`. File paths below are as they were then: superseded drafts are now in `_superseded/` (`_superseded/MANIFEST.md`) and script copies in `tools/`.

---

# Posting tracks 0a, 0b, 0c

Posted: item 0, the SAMF issue, ufs-community/ccpp-physics#401 (20 October 2026; `numbers.json`). `post_bundle.py [numbers.json]` renders `bodies/` from `../pr_round1_descriptions.md` in
each repository's template order, unwrapped for GitHub. It fills each `#TBD` from `numbers.json` and prints, per
item, what is still unfilled and the `gh` command. Tracks 1c and 1d, and the GFDL issue (§2, which goes with the
FV3 PR), are not in the bundle.

| # | Item | Repository | Head (fork `pera-noaa`) → base | Body |
|---|---|---|---|---|
| 0 | SAMF issue (0a), **posted #401** | ufs-community/ccpp-physics | — | `00_SAMF_ISSUE.md` |
| 1 | WM issue (0a), **posted #3404** | ufs-community/ufs-weather-model | — | `issue_3404_body.md` |
| 2 | SAMF + PBL (0b), **posted #408** | ufs-community/ccpp-physics | `pr1-samf` → `ufs/dev` | `bodies_v2/02_PR_SAMF.md` |
| 3a | Noah-MP 1: `frac_grid` snow, layer count (0b), **posted #409** | ufs-community/ccpp-physics | `pr1-noahmp-1` → `ufs/dev` | `03a_PR_NM1.md` |
| 3b | Noah-MP 2: evaporation, snow heat (0b; on 3a), **posted #410** | ufs-community/ccpp-physics | `pr1-noahmp-2` → `ufs/dev` | `03b_PR_NM2.md` |
| 4 | GFDL MP v3 (0b; mass basis in the CCPP wrapper; body to rewrite after `rt_x0b` and the re-measure) | ufs-community/ccpp-physics | `pr1-gfdlmp-w` → `ufs/dev` | `04_PR_GMP.md` |
| 5 | Thompson (0c), **posted #406** | ufs-community/ccpp-physics | `pr1-thompson` → `ufs/dev` | `posted/PR_TH.md` |
| 6 | TEMPO driver (0c), **posted #407** | ufs-community/ccpp-physics | `pr1-tempo` → `ufs/dev` | `posted/PR_TP.md` |
| 7 | ufsatm 0b | NOAA-EMC/ufsatm | `pr1-0b` → `develop` | `07_ATM_0b.md` |
| 8 | ufsatm 0c | NOAA-EMC/ufsatm | `pr1-0c` → `develop` | `08_ATM_0c.md` |
| 9 | WM 0b | ufs-community/ufs-weather-model | `pr1-0b` → `develop` | `09_WM_0b.md` |
| 10 | WM 0c | ufs-community/ufs-weather-model | `pr1-0c` → `develop` | `10_WM_0c.md` |
| 11 | SA1, **posted #405** (not in the bundle) | ufs-community/ccpp-physics | `pr1-sa1` → `ufs/dev` | no local copy (`../pr_round1.md` cites `bodies/11_PR_SA1.md`); `gh pr view 405` |
| — | MLM issue, **posted #404** (not in the bundle) | ufs-community/ccpp-physics | — | `issue_390_mlm.md` |
| — | FPE issue, **posted #3406** (not in the bundle; GCC Bug 128221, JCSDA/spack-stack#2188) | ufs-community/ufs-weather-model | — | `fpe/wm_issue.md` |
| 12 | Noah-MP v5 snow heat (upstream), **posted NCAR/noahmp#274** | NCAR/noahmp | `snow-layer-heat` → `develop` | `bodies_v2/11_PR_NCAR_NM.md` |
| 13 | GFDL `sedi_heat` issue + PR (upstream; with item 4, each cites the other) | NOAA-GFDL/GFDL_atmos_cubed_sphere | `sedi-heat-liquid` → `main` | `gfdl_sedi/issue.md`, `gfdl_sedi/pr.md` |

`numbers.json` keys: `SAMF_ISSUE`, `WM_ISSUE`, `PR_SAMF`, `PR_NM` (old `bodies/`; `bodies_v2/` uses `PR_NM1`, `PR_NM2`, `PR_NCAR_NM`), `PR_GMP`, `PR_TH`, `PR_TP`, `ATM_0b`,
`ATM_0c`, `WM_0b`, `WM_0c` (numbers); `RT_0b`, `RT_0c` (the RT result line, replacing `[RT 0b]`/`[RT 0c]`). The WM PR
RT boxes stay unticked, and the PR is created as a draft, until its `RT_*` key is set.

## Before posting

State (20 October 2026): steps 1 and 3 done. Branches pushed to `pera-noaa/ccpp-physics` (the five PR branches,
`pr1-0b` c4314069, `pr1-0c` 3da54198), `pera-noaa/ufsatm` (`pr1-0b` 68264fb7, `pr1-0c` 9c7f8371) and
`pera-noaa/ufs-weather-model` (`pr1-0b` 165b3d13, `pr1-0c` fa4aafe2) by `push_forks.sh`. Step 2: 0c done (10187059: 54 compiles
pass, 59 identical, 150 changed, 25 restart children not started, none fails to run); its log and
`test_changes.list` are committed on WM `pr1-0c` (98844b7a) and pushed; `RT_0c` set. 0b's first run (10187047) lost 3
tests to I/O errors copying EPIC's input data (`rt_logs_t0b_run1/`); the rerun (10189670) lost 6 the same way
(`rt_logs_t0b_run2/`; the files read cleanly afterwards on both service nodes); third run 10190986 on `dtn-3`. Fifth run 10200567 (22 Oct, driver `--mem=64G` with `unset SLURM_MEM_*`): 54 compiles pass, 118 identical, 101 changed, 15 restart/IAU children not started, none lost (`rt_logs_t0b_run5/`); its log and `test_changes.list` committed on WM `pr1-0b` as a1c632d5 and fetched into `series`. **Push blocked (22 Oct):** upstream WM `develop` moved f1d68949 → 5651397d (15:08Z; CDEPS sync, UFSATM bump to ufsatm 54cebd36 = diagnostic-tendency fix #3383, PR template; `BL_DATE` 20261008 → 20261016; 4 tests change: `control_diag_debug`, `rap_diag_debug`, intel and gnu). ufsatm `develop` moved aa0ba811 → 54cebd36; ccpp-physics `ufs/dev` unchanged (d9b70feb). Both WM track branches (0b, and 0c already pushed) and both ufsatm branches need rebasing, and both track RTs rerunning against 20261016. Runs 1–4's `stmp` dirs deleted.
In all runs every test that started either matched or changed answers as expected.

**23 Oct: rebased onto the new heads.** #390 merged (ccpp-physics `ufs/dev` 9b65688c), ufsatm `develop` c9c98451 (#1138), WM `develop` still 5651397d.
- **ccpp-physics** (`rebase9b.sh`): the five PR branches cherry-picked onto 9b65688c; old heads kept as `pr1-*-d9b70feb`.
  - noahmp c1cad62a, gfdlmp 69a3a82d, thompson bbe56251, tempo ea6ff1c3: patch-ids equal.
  - samf 3e5a4f09: from `prep-samf-on390`. Its CA-trigger commit was re-resolved around #390's `progomega` guards and now only adds lines.
- **Track trees** `rt_u0b`, `rt_u0c` (`track_setup2.sh`; all WM submodules at develop's pins; series `pr1-0b`/`pr1-0c` replaced, old kept as `pr1-0*-old22oct`):
  - physics 33d33b30 / 9e8a5142;
  - ufsatm 2d8b5aa / e02f1ad;
  - WM bc69c789 / 2b1ec42a.
- **RTs** 10210659 (0b), 10210693 (0c), vs BL_DATE 20261016. `develop-20261022` baselines already exist on Hercules, so WM #3355 will likely move BL_DATE.
- **RT results** (both rc 0; logs and `test_changes.list` committed on WM `pr1-0b` f66de571 and `pr1-0c` 0ededd27, copied to series; `RT_0b`/`RT_0c` set):
  - 0b: 116 identical, 101 changed, 15 not started.
  - 0c: 57 identical, 150 changed, 25 not started.
  - Same test-by-test outcomes as 22 Oct; develop dropped `datm_cdeps_lnd_era5` and its restart test.
- **Not yet pushed to the forks** (`push_forks.sh` still has the d9b70feb/aa0ba811/f1d68949 bases).

1. **Branches** (Hercules, `track_setup.sh 0b`, then `0c`): ccpp-physics `pr1-0b`/`pr1-0c` (the track's PR branches
   merged on `ufs/dev`), ufsatm and WM `pr1-0b`/`pr1-0c` (bumps; `.gitmodules` at the fork branches).
   Gates: gitlinks = HEADs, FV3 and noahmp at develop's pins.
2. **Full RT per track** (`rt_t0b.sbatch`, `rt_t0c.sbatch`, about 7 h each, run together on two nodes): commit
   `tests/logs/RegressionTests_hercules.log` and `test_changes.list` on each WM branch; set `RT_0b`/`RT_0c`.
3. **Forks**: `pera-noaa/ccpp-physics`, `ufsatm`, `ufs-weather-model` (none exist yet; `noahmp` only for 1d's `iter` form). Push the branches
   in the table, plus ccpp-physics `pr1-0b`/`pr1-0c`, which the ufsatm `.gitmodules` points at.

## Posting

Post in the table's order and add each number to `numbers.json` as you go: the WM issue once the WM PRs it names can
follow, then lowest repository first, so every body links what already exists. Then rerun `post_bundle.py numbers.json` (no item should list
anything unfilled) and update the bodies that were posted with forward `#TBD`s (`gh issue edit` / `gh pr edit
--body-file`). WM PRs leave draft once their RT is committed.

Phase 0 holds only fixes with one definite answer: NM2 (Noah-MP once per time step) is in 1d, and TH2, TH6, TH7 in
1e (`../pr_round1.md`, *Tracks*), so 0b has no noahmp PR.

Upstream overlaps: SAMF + PBL with ccpp-physics#390, TEMPO with #389 (both open). The bodies say so; rebases onto
both are ready (`prep-samf-on390`, `prep-tempo-on389`).

**24 Oct: cleaned bodies** in `bodies_v2/` (plain-language tables, staged tests and dependencies, NM 7 commits, WM 0b 14 fixes) supersede `bodies/` for items 02–10; placeholders listed in `bodies_v2/README.md`. 0b RT rerun with the 7-commit Noah-MP: `track_setup2.sh` with `RUN=v` → `rt_v0b`.

**24 Oct: posted** ufs-community/ccpp-physics#406 (Thompson, `pr1-thompson` bbe56251) and #407 (TEMPO driver, `pr1-tempo` ea6ff1c3), linked to each other; bodies `posted/PR_TH.md`, `posted/PR_TP.md`.

**24 Oct: 0b rerun** (`rt_v0b`, 7-commit Noah-MP; job 10213381): 116 identical, 100 changed, 15 not started, and `cpld_debug_sfs_gnu` did not complete (FPE in MOM6 `post_surface_thermo_diags`, step 6, ocean rank 295). Rerun alone (10215432) it completed and changes answers. Full log restored and committed on WM `pr1-0b` 02b0c489 (the single-test log kept as `rt_v0b_sfs_rerun_RegressionTests_hercules.log`). Forks updated: physics `pr1-0b` 07ccb2f2, ufsatm `pr1-0b` 51cd7fb5, WM `pr1-0b` 02b0c489. `[RT 0b]` filled in `bodies_v2/` 02, 03, 04, 09; `RT_0b` set.

- **FPE (`cpld_debug_sfs_gnu`)**: gcc cond_fma bug; see `fpe/README.md`. gcc report first; spack-stack issue held until the gcc bug number exists.

**25–27 Oct: replies and comment rewrite.**
- Posted 27 Oct (UTC): #401 reply to Lisa with the convective-precipitation plot (`reply_401_lisa.posted.md`), #405 reply to Han's 26 Oct objection (`reply_405_3.md`), #406 reply to climbfuji on the review thread (`reply_406_climbfuji.md`).
- Code comments in #405–#407 rewritten (one line, what the merged code does) and folded into the original commits; force-pushed with lease: `pr1-sa1` 57266f25, `pr1-thompson` 8ed761d6 (4 commits), `pr1-tempo` 1674d9ed. Trees byte-identical to the previous heads. Hercules `series` synced for all three.
- Track 0c rebuilt on the new heads (`rebuild_0c_cmt.sh`, log `rebuild_0c_cmt.log`): physics `pr1-0c` 549f8716 (the same octopus merge), ufsatm `pr1-0c` b4dd90c7, WM `pr1-0c` 50dfbde5 (bump 0b60f95a + the RT-log commit), each the old commit with only the gitlink changed; old heads kept as `pr1-0c-before-cmt`. Gates: the 3 changed Fortran files equal their branch and are code-equal to 9e8a5142 (known-bad caught). Pushed to the forks 27 Oct (`push_forks2.sh`; WM with the upstream-head gate relaxed to base-is-ancestor, since WM `develop` moved 5651397d → 3e48f4cc with #3355, the MLM). WM 0b and 0c rebased onto 3e48f4cc (`track_setup3.sh`, BL_DATE 20261022; physics and ufsatm reused unchanged): series WM `pr1-0b` ac98ba3a, `pr1-0c` 61d73894 (old tips kept as `pr1-0*-before-w`), the same bump commits without the RT-log commits. RTs `rt_w0c` 10288631, then `rt_w30b` 10289329 (afterany; `rt_w0b` 10288522 and `rt_w20b` 10289120 were cancelled when the 0b branches were cleaned). Then commit each log and `test_changes.list`, set `RT_0b`/`RT_0c`, push. The committed RT log names the hashes it ran on (2b1ec42a, e02f1ad, 9e8a5142); code is identical.

**27 Oct: `rt_w0c` done** (10288631, 4 h 55 min, develop 3e48f4cc, baselines 20261022): 54 compiles pass; 57 identical, 150 change answers, 25 restart children not started; none fails to run. `test_changes.list` is identical to the 23 Oct run's (`rt_t0c`, `rt_u0c`). Log committed on WM `pr1-0c` c41667a5 (old tip `pr1-0c-before-rtlog`); `RT_0c` and `10_WM_0c.md` updated. Not pushed.

**27 Oct: `rt_w30b` done** (10289329, develop 3e48f4cc, baselines 20261022, on physics 01847384 / ufsatm b37ad447): 54 compiles pass; 116 identical, 101 change answers, 15 not started; none fails to run (`cpld_debug_sfs_gnu` completed this time). `test_changes.list` identical to the 24 Oct full run. Log committed on WM `pr1-0b` b839573d (old tip `pr1-0b-before-rtlog`); `RT_0b` and the Tests lines of 03, 04, 09 updated (the #3406 sentence dropped). Not pushed.
- `series` `pr1-sa1` synced to the fork's 57266f25 (old kept as `pr1-sa1-ae8399bd`). Track 0b is untouched by the rewrite.
- #406 approved by Ruiyu Sun (26 Oct). #407, #404, #3404: no comments.

**Open:**
- `reply_403_2.md` (diffusion, #403): held; post now or after Han makes the diffusion optional.
- Items 2–4, 7–10: not posted. SAMF + PBL waits for Han and Lisa on #401/#405.
- gcc Bugzilla report (`fpe/README.md`) once the account exists, then the spack-stack issue.

**27 Oct: Noah-MP and GFDL MP v3 cleaned** (items 3, 4; not posted). Comments one line each, saying what the code does (internal `sl2:`/`cs1:`/`cb1:` tags and justifications removed); the helper functions moved above `combine`'s doxygen tag; one unused `hc1` declaration in `snowh2o` removed; commit messages rewritten in plain prose, with the measurement caveats kept (coastal snow measured with the time-step fix; combine heat with the thin-snow fix). Each commit code-identical to its original apart from that declaration (`nmgmp/gate.py`; known-bad caught). Series: `pr1-noahmp` 01a0ab75, `pr1-gfdlmp` d45ef9ca (old kept as `-before-clean`); track 0b rebuilt: physics `pr1-0b` 4695671e, ufsatm 09c63718, WM d896e628 (`rebuild_0b_clean.sh`, `track_setup3.sh` with `RUN=w2`). Bodies `bodies_v2/03_PR_NM.md`, `04_PR_GMP.md` tidied (companions #406/#407 linked, the Claude Code line added; old copies `*.pre27oct`). Forks not updated.

**27 Oct: FPE issue posted** as ufs-community/ufs-weather-model#3406 (`fpe/wm_issue.md`; says the gcc report waits on the Bugzilla account). Noah-MP and GFDL MP commit messages cut to the defect and the fix (893 → 256 words); the precedents, caveats and numbers moved to `bodies_v2/03_PR_NM.md` (a Notes list) and `04_PR_GMP.md`; both bodies cite #3406 for the `cpld_debug_sfs_gnu` stop. Trees unchanged. Series: `pr1-noahmp` 075e8b46, `pr1-gfdlmp` 919ab856 (the first cleaned version kept as `-clean1`); track 0b: physics `pr1-0b` 01847384 (tree = the first cleaned merge), ufsatm b37ad447, WM e97a5448 (`rt_w30b`).

**27 Oct: replies posted.** #406 climbfuji's line-951 sign question answered in thread (discussion_r4391719325; `reply_406_signs.posted.md`: the identity, FV3 `atmosphere.F90` L1659–1677 at 71ff473 rebuilds species mass from the pre-physics layer mass, `(1+qv_in)/(1+qv_out)`). Line-693 suggestion (use `spechum`, also in #407) not yet applied. mana#543 rebased onto main as ab6c441, CI passed, reply posted (issuecomment-6448287736).

**27 Oct: cleaned Noah-MP and GFDL MP pushed** to pera-noaa/ccpp-physics from the local bundle (`nmgmp/clean2.bundle`): `pr1-noahmp` f051b17a → 075e8b46, `pr1-gfdlmp` 69a3a82d → 919ab856 (gates: base 9b65688c = fork ufs/dev, identity and trailer on every commit, known-bad caught). Track branches (physics/ufsatm `pr1-0b`, WM `pr1-0b` b839573d, WM `pr1-0c` c41667a5) wait for Hercules.

**27 Oct: track branches pushed** (`push_forks3.sh`: push_forks2 with WM base 3e48f4cc and the fork base fast-forwarded): physics `pr1-0b` 01847384 (others unchanged), ufsatm `pr1-0b` b37ad447, WM `pr1-0b` b839573d and `pr1-0c` c41667a5 (each with its 27 Oct RT log); fork WM `develop` 5651397d → 3e48f4cc. All forks now match `series`.

**27 Oct: #406 line-693 suggestion applied** (`rebuild_693.sh`, log `rebuild_693.log` on Hercules): `qv = spechum/(1-spechum)` amended into the mass-basis commits of #406 (73e3b58c, later 3 replayed) and #407; force-pushed: `pr1-thompson` 8ed761d6 → 0e22f8c2, `pr1-tempo` 1674d9ed → bd82d044. Track 0c rebuilt: physics 911b85fd, ufsatm a30c17dd, WM 2504cc22 (bump 732c3a91; RT log unchanged, it names 549f8716, which differs only by these two lines, bitwise equivalent). Old heads `*-before-693`. Gates: one-line branch diffs, per-commit patches/messages/authors unchanged, known-bad caught. Reply posted in the line-693 thread.

**27 Oct: GCC Bug 128221 filed** (target, 17.0, UNCONFIRMED; text `fpe/gcc/bugzilla_description.txt`, attachment `condfma.i`, URL godbolt.org/z/39ozdM3hr). #3406 body updated to link it (replaces "will report it to gcc once my Bugzilla account is approved"). spack-stack issue draft (`fpe/spack_stack_issue.md`) now unblocked; #TBD-GCC filled, "counterpart of #2075 and FMS#1898" wording still to fix.

**27 Oct: spack-stack issue posted**: JCSDA/spack-stack#2188 (`fpe/spack_stack_issue.md`, 386 words; links #3406 and GCC Bug 128221). #3406 updated to link #2188.

**27 Oct: Noah-MP body (item 3) edited for the owners** (not posted; old copy `bodies_v2/03_PR_NM.pre-owners.md`): @barlage @cenlinhe tagged (CODEOWNERS for `Noahmp/*noahmp*`); layer-count fix cited as identical to NCAR/noahmp@218eb5a; `combo` noted as matching CTSM `Combo` (`SnowHydrologyMod.F90` L3932–3936); NCAR Noah-MP v5 master noted as having the same three snow-heat defects (`SnowLayerCombineMod` merges without a temperature update, `SnowThermalPropertyMod` L60 capped volume fractions, `SnowLayerWaterComboMod` L47–60 per-m³ heat capacities with masses), with an offer to file there. 609 → 656 words.

**27 Oct: Noah-MP split in two** (not pushed, not posted). Local `scratchpad/nmsplit/split.sh` from the fork's `pr1-noahmp` 075e8b46: `pr1-noahmp-1` ec105b74 = coastal snow, snow initialisation, layer count (land and glacier); `pr1-noahmp-2` 93ded54e = evaporation + combine/csnow/combo heat, stacked on -1 (both edit `combine`). Gates: patch-id, message, author and trailer of each commit unchanged; -2 tree = 075e8b46 tree (so `rt_w30b` and track 0b cover both unchanged); known-bad (-2 minus combo) caught; -1 touches only its five files. Bodies `bodies_v2/03a_PR_NM1.md` (owners tagged for 218eb5a) and `03b_PR_NM2.md` (owners tagged, CTSM `Combo`, v5 offer); placeholders `#NM1`/`#NM2` fill at posting (post 3a first). `03_PR_NM.md` kept as the single-PR version. 07/09 placeholders now `#TBD-PR_NM1, #TBD-PR_NM2`.

**27 Oct: NCAR Noah-MP v5 PR drafted** (not pushed, not posted; no `pera-noaa/noahmp` fork yet). Branch `snow-layer-heat` on NCAR/noahmp `develop` 57b9373: 36ee137 `SnowLayerCombine` (merge heat with per-mass capacities; removed layers' heat to layer 1 via `HeatCapacSoilSnow(1)`, so land and glacier alike), 240fb21 `SnowThermalProperty` (capacity from mass), 0451f42 `SnowLayerWaterCombo` (per-mass, CTSM `Combo` form). Unlike the UFS commit, no soil-heat rescale on the over-sublimation path (v5 moves that deficit to soil liquid instead). Standalone harness `ncar_noahmp/test_snow_heat.F90` + `run.sh REV double|single`: develop fails 7/7 (known-bad), branch passes 7/7 at ≤ 6e-9 J/m² (double; single ≤ 3 J/m², rounding); per commit: combine fixes 1–4, thermal 7, combo 5–6. Body `bodies_v2/11_PR_NCAR_NM.md` (cites #NM2; test program in a details block). Branch saved as `ncar_noahmp/snow-layer-heat.bundle`.

**27 Oct: GFDL MP mass-basis fix moved to the wrapper (local only; not pushed, track 0b not rebuilt, no RT).** Red-team: GFDL MP is self-consistent (returns species on `delp_out = dp·(1 + r_v)`), and GFDL upstream `model/gfdl_mp.F90` (main) has the same conversion (L1586–1588); the bug is that the CCPP wrapper keeps `delp` local and discards it. Upstream also has the `sedi_heat` `c_ice` bug (L2692). New branch `pr1-gfdlmp-w` (nmsplit/repo; bundle `gfdl_wrap/pr1-gfdlmp-w.bundle`): f4c9304 wrapper rescales qv..qg by `delp/del` and sets `delp = del` (for `rad_ref`), `_mod` untouched; 0423ea5 = sedi commit, patch-id unchanged. Column test of the real wrapper + module (`gfdl_wrap/test_gmp.F90`, RT `gfdl_cloud_microphysics_v3_nml`, 16 columns × 64 levels, dt 225 s): base loses water = 0.37 % of precipitation over 32 steps; in-module fix and wrapper fix both close to ≤ 6e-14 kg/m² (≈ 2–5e-16 of precip). One call: species agree to 8e-16 relative; T differs ≤ 2.1e-5 K (the final tz→pt conversion's `c8` uses the returned species, so GFDL basis vs host basis). After 32 steps mod vs wrap: qv 1.2e-7, T 1.8e-4 K, precip 1.4e-3 kg/m², vs base 9.3e-5, 0.21 K, 0.13. Old `pr1-gfdlmp` 919ab856 kept.

**27 Oct: track 0b rebuilt with the wrapper-form GFDL fix; RT and meters running.** Hercules series: physics `pr1-gfdlmp-w` 0423ea54, `pr1-noahmp-1` ec105b74, `pr1-noahmp-2` 93ded54e fetched (`pr1/gw.bundle`). `rebuild_0b_gw.sh` (log `rebuild_0b_gw.log`): physics `pr1-0b` 01847384 → 9e6ec22c (same octopus merge, parents 9b65688c, 3e5a4f09, pr1-noahmp-2, pr1-gfdlmp-w; diff vs old merge = exactly 919ab856 → pr1-gfdlmp-w; known-bad caught); ufsatm `pr1-0b` b37ad447 → fc9d2380 (gitlink swapped, parent fd72b97 kept). Old heads `pr1-0b-before-gw`. `RUN=x WM_OLD=3e48f4cc ATM_OLD=b37ad447 track_setup3.sh 0b`: WM `pr1-0b` dc907cc2 (old b839573d kept as `pr1-0b-before-x`), RT `rt_x0b` job 10299062. Meters (`cons/suites/tools/gw_meter.sh`): trees `gA` (meter + 02 v6 + 07 v8) and `gW` (meter + 02w v9 + 07 v8; `fixes/02w_E4_gfdlmp_v3_mass_basis_wrapper_v9.diff`), differing only in 02 (gated); build job 10299075; then `gw_meter.sh runs` (control_iovr4_gfdlmpv3, 24 h).

**27 Oct: GFDL re-measure done** (job 10299224; `cons/suites/report.md` §4): wrapper form (gW) vs in-module (gA): MP water rW/P 1.5e-14 vs 1.6e-15, GFDL frame + PE −0.0070 vs −0.0075 W/m², gW − gA at noise (rms ratios 0.96–1.16). `04_PR_GMP.md`'s numbers hold. **Comments and messages to the rules** (local `nmsplit/repo`, `scratchpad/recomment.py`, gate: per-commit diff without comment lines unchanged, known-bad caught): `pr1-samf-c` f5a9fc81 (3 comments shortened, 1 two-line comment cut to one, "Measured" paragraphs dropped from the 4 messages), `pr1-noahmp-1c` b0999980 (one 81-character subject shortened; tree unchanged), `pr1-noahmp-2c` 5e5770b2 (2 parentheticals dropped), `pr1-gfdlmp-wc` 552b1d54 (wrapper comment), NCAR `snow-layer-heat-c` 3a720c4f (comment, CTSM aside, trailer blank line). Not pushed; track 0b to relink onto them after `rt_x0b` (comments only). `02_PR_SAMF.md`: wet deposition is deep and shallow, PBL row reworded, CA impact added, #390 history dropped.

**27 Oct: posted #408, #409, #410 and NCAR/noahmp#274.** Fork `pera-noaa/ccpp-physics`: `pr1-samf` force-pushed 3e5a4f09 → f5a9fc81 (comments and messages only; lease on the old head), `pr1-noahmp-1` b0999980, `pr1-noahmp-2` 5e5770b2 (new); gates: base 9b65688c = upstream `ufs/dev`, identity and trailer on every commit, NM-2 on NM-1. `pera-noaa/noahmp` forked; `snow-layer-heat` 3a720c4f on NCAR `develop` 57b93739. #409 posted with a neutral reference to NM2, then edited to #410; #410 edited to cite NCAR/noahmp#274. Titles: "SAMF and PBL conservation fixes", "Noah-MP snow fixes with frac_grid", "Noah-MP evaporation and snow heat fixes", "Conserve snow layer heat when layers merge or vanish". Posted texts in `posted/`. Reviewers (CODEOWNERS): #408 Han, Lisa + code managers; #409, #410 barlage, cenlinhe + code managers. Fork `pr1-noahmp` (075e8b46, the single-PR form) left in place.

**27 Oct: GFDL `sedi_heat` drafted** (`gfdl_sedi/`). Upstream `main` 8b94b9f3 `model/gfdl_mp.F90` L2692 passes `c_ice` for every species; `dev/emc` (UFS's branch) has no `gfdl_mp.F90`, so only `main` (SHiELD) is affected. v1 (ccpp-physics `v1_2019`) used `c_ice` for the solid flux (L813) and `c_liq` for rain in `warm_rain` (L1126): a v3 regression. Fix commit 365dd36 on `main` (same change as the UFS commit; branch `gfdl_sedi/sedi-heat-liquid.bundle`), not compiled outside UFS. Issue 238 words (bug template), PR 164 (PR template). Facts checked: both meter runs had the UFS mass-basis fix, so "+0.20 before, −0.007 after".

**27 Oct: GFDL `sedi_heat` fix tested in GFDL's own code** (`gfdl_sedi/test_sedi.F90`, `fms_stub.F90`, `run.sh`): `main`'s `gfdl_mp.F90` built standalone (gfortran 16.2, `-fcheck=all -ffpe-trap`), `terminal_fall` public in a test copy. One 300 s step, 40 layers, column internal + water PE + outflow: rain or cloud water, `main` +1.18e5 J/m² (6.2e-5 of the column; known-bad), fix 2.0e-16 (single 2.1e-8, rounding); snow 0 on both (moved: max |dq| 9e-4). `-Wall` warnings unchanged (17 double, 144 single). PR draft gains the test table and program; issue cites it. Issue 280 words, PR 194 + program.

**27 Oct: fork `pera-noaa/GFDL_atmos_cubed_sphere` made** (`main` 8b94b9f3, same as upstream). Branch `sedi-heat-liquid` (365dd36, one commit on upstream `main`) pushed; no PR yet.

**27 Oct: unposted bodies reviewed; leftovers.**
- `07_ATM_0b.md`, `08_ATM_0c.md`: known PR numbers filled (#408–#410; #406, #407 with #389), AI-use and Claude Code lines added. `09_WM_0b.md`: "commit messages give the measured effect" (no longer true) → "the ccpp-physics PRs give the measured effects"; `[0b …]` placeholders filled from the record (global P8 3-D T +0.001–0.006 K, precipitation −0.27 to +0.29 %; HAFS 0 of 20 crash, as develop); #408–#410. `10_WM_0c.md`: same message fix; #406/#407 with #407 after #389; RT line notes the run predates the #406 input-humidity line, which cannot change answers (`new_spechum = spechum` at Thompson L602 and TEMPO L388, not reassigned before L693/L437; checked). Old copies `*.pre-review`.
- `04_PR_GMP.md` rewritten for the wrapper form (old `04_PR_GMP.pre-wrapper.md`); Tests line is `[RT 0b]` until `rt_x0b`; cites the GFDL issue (#TBD-GFDL_SEDI_ISSUE).
- ufo#81: reply to fmahebert drafted (`reply_ufo81.md`, 98 words). Checked on OOPS `develop` ef934f23: `time interpolation: linear` widens the window only in the nonlinear path (GetValues.h L395); `processTL`/`processAD` keep `halfWidth_ = tstep/2` (L628, L805); `GetValueTLADs.h` has no time interpolation; `hofx_tinterp.yaml` is H(x) only.
- `reply_403_2.md`: still correct (Han, 23 Oct: leak blamed on sigma surfaces; scalars' horizontal diffusion to become optional). Held during the #405 dispute; #405 is now approved.
- `pr1-thompson_p1` (phase 1e) rebased from the d9b70feb-era Thompson onto the posted `pr1-thompson` 0e22f8c2 and brought to the rules (`thp1/` on Hercules, `recomment.py` with an ONTO argument; gate: per-commit code unchanged): 4afaf48a (fa2af5de TH2, fb9cd251 TH6, 4afaf48a TH7). Messages cut to defect and fix (≤ 72 columns; TH2 subject shortened), 12 comment lines → 10 one-liners. Thompson code differs from the old head only by the base's input-humidity line. Old kept as `pr1-thompson_p1-before-rebase`. Not pushed, not compiled on the new base (phase 1 gets its own RT).

**27 Oct: ufo#81 reply posted** ([issuecomment-6454421513](https://github.com/JCSDA/ufo/pull/81#issuecomment-6454421513); `reply_ufo81.posted.md`, 74 words; first draft `reply_ufo81.v1.md`).

**27 Oct: #403 reply to Han posted** ([issuecomment-6454583567](https://github.com/ufs-community/ccpp-physics/pull/403#issuecomment-6454583567); `reply_403_2.posted.md`, 111 words: the leak is the mixing-ratio application, not sigma surfaces; z surfaces would leak too; mass-weighted face fluxes fix it on sigma; optional is fine. Drafts `.v1`–`.v4`).

**27 Oct: track 0c checked before posting 08/10** (`post/check_0c.sh`, run in Hercules `series`): forks = series (physics `pr1-0c` 911b85fd, ufsatm a30c17dd, WM 2504cc22); #406/#407 heads 0e22f8c2/bd82d044, both mergeable; upstream heads unchanged (9b65688c, c9c98451, 3e48f4cc). Physics `pr1-0c` tree = a fresh octopus merge of 9b65688c + 0e22f8c2 + bd82d044 (known-bad 549f8716, the RT's tree, differs by the two line-693 lines only). ufsatm: parent c9c98451, only `.gitmodules` + gitlink (= physics `pr1-0c`). WM: develop an ancestor, gitlink = ufsatm `pr1-0c`, only `.gitmodules`, UFSATM, RT log, `tests/test_changes.list` (175 = 150 + 25, same as c41667a5). All OK; 08/10 ready.

**27 Oct: 08/10 red-teamed.** (1) Changed set vs suites (`suite_check.sh`, `rt_w0c` run dirs, suite XMLs at the 0c ufsatm): the 150 changed runs are exactly the runs whose suite calls `mp_thompson` or `mp_tempo` (`gnv1_nested` = `FV3_global_nest_v1`, Thompson); no Thompson/TEMPO run unchanged; the 25 entries without a run dir are the restart children; `MPAS_RRFS` has no microphysics (radiation only) and is unchanged. (2) Precipitation 0.9–5.3 % is the 8 most affected regional tests (`attr/attr_p0c_table.txt`), not all regional tests; WoFS TEMPO −1.96 %. 10 said "regional and convection-allowing tests" and "independent" (Thompson commit 5 needs 3): reworded. 09 "independent" dropped. (3) WM PR template changed in 5651397d (22 Oct): new "All CI is passing" item, GenAI "No" option, "What's Missing?" section, longer item texts. 09/10 Commit Queue block replaced verbatim from the live template (`wm_template_fix.py`; ticks: issue, RT, log, test_changes.list, GenAI Yes, all sections; CI and NWS review unticked), "What's Missing?" added unticked (as #3402). Old copies `*.pre-template.md`. The template's NOTE says keep the PR in draft until all requirements are complete: post 09/10 as drafts. (4) ufsatm template unchanged since Feb 2025; 08 follows it. #389 still open.
(5) Bare cross-repo refs: in a WM or ufsatm PR, `#407` links to that repo's #407. 12 refs to ccpp-physics PRs in 07–10 qualified (`ufs-community/ccpp-physics#…`, including `#TBD-PR_GMP`); `#3404` (WM) and `#1133` (ufsatm's own PR, in 07) left bare. 10's RT note reworded around them.

**27 Oct: 0c fixes re-read against the round-1 rule** (diffs `pera-noaa/ccpp-physics` d2868cc1, 41d11ad6, 45e71be4, 0e22f8c2, bd82d044). TH1 and the TEMPO driver: one answer (the host holds layer mass fixed, so `q = r(1−q_in)`; same arithmetic as the GFDL wrapper fix). TH3 graupel: bug plain (gains computed before the limiters, losses scaled after); the fix sets the gains from the limited losses and caps `prs_rcs` at the rain lost (T < T0); no other closing form seen; largest effect (−1.0 to −4.1 % regional precipitation), passes rule 4 only as the bug's own signal; Thompson owners have not reviewed. TH4 density: bug plain; an argued second form exists (keep the updated density and recompute dz from it; ρ·dz = layer mass either way; fall speeds differ by the heating's density change, at noise). TH5 layer depth (−0.014 %): adds `prsi` and an optional `dm` argument, dz = dm/ρ (hydrostatic, not the geometric depth); the alternative keeps a recomputed geometric dz and derives ρ from it; the weakest fit to rule 2. **TEMPO v3 has the same three patterns**, in the pinned 2856696 and NCAR/TEMPO `main` c62699f: graupel gains not re-closed after `check_over_depletion`, `rho` recomputed after heating (5 places), `dz` from `phii` in `mp_tempo.F90` L460. **#407's body says TEMPO-core fixes "are proposed to NCAR/TEMPO separately": nothing has been filed** (no issue or PR from us on NCAR/TEMPO).

**27 Oct: drafts for #406 and #407** (not posted): `reply_406_owners.md` (#406 comment: Anders on the graupel commit; density/layer-depth alternative form; TEMPO shares the patterns; notes the #407 correction) and `pr407_body_fix.md` (replaces the false "fixes are proposed to NCAR/TEMPO" sentence). Red-teamed: graupel mechanism confirmed in pre-fix code (gains at L2792/L3029, limiters at ~L3140–3175 scale only the losses; clips at L2796–2798); TEMPO `main` c62699f: `qgten` adds `prg_rci`/`prg_rcs`, which `check_over_depletion` never resets; `rho` recomputed after heating and used in `sedimentation`; `mp_tempo` dz from `phii` is ccpp-physics code (#407's file), so not "for NCAR/TEMPO". `dm/ρ` (dry over dry) = hydrostatic depth. 1.0–4.1 % is the 8 most affected regional tests. gthompsnWRF inactive since 2024: dropped from the tag. v1 copies kept. Order: edit #407, then post the #406 comment.

**27 Oct: `rt_x0b` done** (10299062, 3 h 57 min, COMPLETED 0:0; physics 9e6ec22c, ufsatm fc9d2380, WM dc907cc2; baselines develop-20261022): 54 compiles pass; 116 identical, 101 change answers, 15 restart/IAU children not started; no other failure. `test_changes.list` (116) identical to `rt_w30b`'s (b839573d). `RT_0b` unchanged (same text); 04's Tests line filled. Next (local): relink track 0b onto the rule-cleaned `-c` branches (comments only, code-equal gate), commit the RT log on WM `pr1-0b`; then push with approval.

**27 Oct: #407 body corrected** (approved): the "Fixes for that are proposed to NCAR/TEMPO separately" sentence replaced by `pr407_body_fix.md` NEW (TEMPO has the graupel limiters and density update; report to NCAR/TEMPO; `mp_tempo` layer depth to follow in #407 once #406's form is settled). Before: `posted/PR_TP_407.before-tempo-fix.md`; now: `posted/PR_TP_407.md`. Owes: a NCAR/TEMPO report.

**27 Oct: #406 comment cut 20 %** (175 → 138 words, `reply_406_owners.md`; v2 kept); held until the alternative-form tests report.

**27 Oct: track 0b relinked onto the rule-cleaned branches** (`rebuild_0b_c.sh`, log on Hercules `rebuild_0b_c.log`; `c0b.bundle` carried pr1-samf-c, pr1-noahmp-1c/-2c, pr1-gfdlmp-wc to `series`): physics `pr1-0b` 9e6ec22c → d4015acb (octopus on 9b65688c + f5a9fc81, 5e5770b2, 552b1d54; code-equal with comments stripped, `codecmp.py`; known-bad 01847384 caught on the two GFDL files), ufsatm fc9d2380 → d52b9309 (gitlink only), WM dc907cc2 → 3f8ddbb8 (gitlink only) + 46b662cd (rt_x0b log and `test_changes.list`, message as b839573d). Old heads `*-before-c`. The RT log names 9e6ec22c/fc9d2380 (comment-only difference). Not pushed.

**27 Oct: tests of the alternative Thompson density/layer-depth form started** (files in `thdz/`). Alternative (`thdz_edit.py alt`): density fix reverted (rho recomputed at the three updates, as develop), `dz = dm/ρ` reset after each, and at the two in-loop updates the stored mass/number densities rescaled by ρ_new/ρ_old (develop rebuilds cloud, then rain, with the old ρ just before ρ changes). (1) Closure, suites meter on the full10 base (Thompson segment ≤1e-15 there): trees dzO (base = ours), dzB (density fix reverted, known-bad), dzA (alternative), differing only in `module_mp_thompson.F90` (gated); build 10303519, runs 10303578 (control_p8_mynn, rap_control, 24 h). (2) Regional: attr unit `p0d` = p0c's tree (physics 61085fb2) + the same edit, 9 tests, job 10303579; screen vs develop-20261008 and vs p0c's run dir, against w_noise. (3) TEMPO per-fix attribution: separate agent, `tempo_attr/`.

**27 Oct: alternative-form closure (test 1) done** (build 10303519, runs 10303578; suites meter, Thompson segment rW / MP precipitation over 24 h): ours (dzO) 7.7e-16 (p8_mynn), 2.1e-15 (rap); known-bad dzB (density fix reverted) 1.7e-3, 1.0e-4; alternative dzA 5.6e-16, 7.3e-16. The alternative closes to round-off like ours; the gate fails on the known-bad. MP precipitation alt vs ours: −0.046 % (mynn), +0.30 % (rap). `rt_screen.py` on these runs reads only the last tile file (tile 6), so its numbers are not global; noise pair `consv_te=0.999` on dzO (both suites) submitted, 10303836.

**27 Oct: docs cleaned.** `POSTING.md` split: head (Status, plan, procedure, files) and this file (the old `POSTING.md` verbatim above, then this log). 29 superseded drafts and copies moved to `_superseded/` (`MANIFEST.md` names each one's replacement; nothing deleted); `bodies_v2/` holds only the unposted 04, 07–10 (README rewritten); script copies moved to `tools/`. `09_WM_0b.md` notes the RT log's pre-relink hashes. `../pr_round1.md` Status rows (Branches, Waiting upstream, Posted, PRs) brought to the relinked 0b, the #407 correction and the posted NCAR PR (old copy in the session scratchpad). The TEMPO per-fix attribution agent was stopped after its build (`$U/cons/tp_attr`, 10303620); nothing run.

**27 Oct: alternative-form noise pair done** (10303836; dzO with `consv_te=0.999`). Global Thompson precipitation over 24 h relative to ours (dzO): noise −0.280 % (p8_mynn), +0.040 % (rap); alternative −0.046 %, +0.303 %; density fix reverted −0.419 %, +0.245 %. One noise sample per suite: the alternative's global effect is within the range the 0.999 control spans (0.04–0.28 %), but global 24-h precipitation does not separate even the known-bad from noise, so the regional `p0d` comparison is the one that decides. Residuals unchanged (dzO_c999 1.3e-15, 1.7e-16).

**27 Oct: alternative-form regional test done** (`p0d`, 10303579; 12 runs, all changed vs develop as expected; `attr/screen_p0d.txt`, `attr/screen_p0d_vs_p0c.txt`). Precipitation, alternative − ours (p0d − p0c): `regional_control` +0.36 % (one-ulp noise 0.24 %, `rt_logs_noise_screen.txt`), `cpld_regional_atm_fbh` +0.65 % (no noise reference), `hrrr_c3_debug` +0.27 % intel / +0.03 % gnu, `gnv1_nested` −0.13 %, `conus13km_gl_inline` −0.006 % (noise 0.03 % on `conus13km_control`), `regional_spp_sppt_shum_skeb` and HRRR/RAP debug ≤ 0.03 %; T2m, PW, 3-D T and q at or below noise. `regional_wofs_tempo` (TEMPO suite, Thompson unused) identical: the harness is consistent. Both forms move precipitation 1–5 % from develop. #406 comment updated with the result (`reply_406_owners.md`, 179 words; 138-word draft in `_superseded/`). Not posted.

**27 Oct: #406 owners comment dropped** (the PR has a Thompson owner's approval; asking for more review or offering to switch forms invites churn at ≤0.4 %). Draft in `_superseded/reply_406_owners.md`; the alternative-form numbers above stand for a reviewer who asks. The TEMPO findings go to Anders in the NCAR/TEMPO report instead.

**27 Oct: TEMPO per-fix runs restarted** from the stopped agent's builds (`$U/cons/tp_attr`; tree = rt_w0c copy, physics bd82d044 = #407, tempo_v3 2856696; build 10303620). Meter `TPW` in `mp_tempo.F90` (all variants): host-frame column water change Σ(q_new − q_in)·Δp/g plus the call's precipitation, area-summed per rank; checked: inputs untouched, `prcp` accumulates within the call (m → ×1000), after the back-conversion. Variants vs T0 (#407 + meter): C1 (28 lines), C2 (11), C3 (15), M1 (37), T1 (3), P1 = C1+C2+C3+M1 (91), P13 (port without T1, 337), TH5 (driver dz, 9 lines in `mp_tempo.F90`), port (340), all = port + TH5. Runs `control_p8_ugwpv1_tempo` C96 24 h, jobs 10305347 (T0 C1 C2 C3 M1 T1), 10305348 (P1 P13 TH5 port all); `tp_budget.py` tabulates R/P per 6-h window. Gate: T0 must reproduce ≈ +0.3 %, all ≈ 0.

**27 Oct: TEMPO per-fix attribution done** (`tempo_attr/results.md`, `variants.diff`; runs 10305347–8, all rc 0, 120 steps × 144 ranks). R/P 6–24 h with #407: +0.377 % (T0); gate passes (all = port + TH5: −2e-7). Commit 3 (r1 floors, vapour floor) ≈ +0.58 % of creation; graupel (C2) creates 0.83 % in 0–6 h, 0.005 % after; cloud settling (C1) removes 0.14 %; density (C3) removes 0.04 %; driver layer depth (TH5) removes 0.011 %; M1 ≤ 0.002 %. T1 (fallback sign) −0.64 % alone and −5 % precipitation, < 0.001 % with commit 3: a physics change, report separately. #407's sentence (graupel and density) is true but not the main source.

**27 Oct: TEMPO attribution red-teamed** (`tempo_attr/results.md`, *Red team*). All patterns still in NCAR/TEMPO `main` c62699f (T1 sign at L1911, against Thompson's `qpi(k).lt.0.0`; floors L1808/1814/1984; cloud settling only in `cloud_precip`); no NCAR/TEMPO issue or PR covers them; UFS runs `sedi_semi = .true.`. The largest source's fix (commit 3: floors paid from vapour) is TH6/TH7's class (a judgement), C1 is TH2's; only C2, C3, TH5 and T1 have one answer. Add-one deltas below 0.01 % are not resolved: leave-one-out from `all` submitted (L_C1, L_C2, L_C3, L_3, L_T1; build 10305938, setup 10305939 submits the runs; M1 not separable). #407's +0.33 % is the October meter's; this meter gives +0.36…+0.39 per window. T1's −5 % is TEMPO's grid-scale precipitation.

**27 Oct: TEMPO leave-one-out done** (build 10305938, runs 10306256; `tempo_attr/results.md` rewritten, add-one version in `_superseded/`). Isolated leaks, 6–24 h (0–6 h): C1 −0.137 % (−0.199), C2 +0.004 % (+0.861), C3 −0.118 % (−0.120), commit 3 with T1 fixed +0.001 %, T1 with commit 3 in 0, TH5 −0.011 %. The non-T1 leaks sum to −0.261 % / +0.533 %, against −0.263 % / +0.538 % measured with only T1 fixed: T1 (fallback sign feeding the floors) creates ≈ 0.64 %, the main source, and changes TEMPO precipitation −5 %. Density is 3× the add-one estimate. Graupel, density, layer depth (#407's three) and T1 have one answer; C1 and commit 3 are judgement fixes (TH2, TH6/TH7 classes).

### 27 Oct 2026: NCAR/TEMPO issue drafted and red-teamed

- Draft `tempo_attr/ncar_tempo_issue.md`; v1 in `_superseded/ncar_tempo_issue.v1.md`.
- Red-team corrections in v2: row 1 is not leave-one-out (commit 3 hides it), so the method is stated per row. The +0.38 % is reconciled with #407's +0.33 %. "Three leaks offset" became one adds, two offset. The residual after fixes 1–4 is stated.
- Red-team findings: the sign was inverted in v3.0.0 (NCAR/TEMPO#24; v2 had `.lt.`); draft GPU port NCAR/TEMPO#57 carries it. The graupel per-term clamps also break the identity. The TEMPO driver never outputs `cloud_precip`.
- Alternatives added: always piecewise constant (T1, unrun); scaling snow's gain instead of the cap (C2, unrun); updated depth (C3, the Thompson alternative form); a separate output or no settling out of the lowest layer (C1).
- 28 Oct: alternatives run (`tp_attr` X_T1inv, X_T1c, X_C2p; build 10308650, runs 10308759). Always-constant closes but doesn't keep v3's precipitation (−0.6 % vs the corrected test; v3 +5.4 %). Proportional C2 closes the same (P +0.03 %). T1 leave-one-out is 0.58 % (from L_3). Issue draft v3; v2 in `_superseded/`.

---

Archive: `POSTING.md` as it stood on 29 October 2026, before the package rewrite (verbatim).

# Posting tracks 0a, 0b, 0c

## Status (28 October 2026)

- **Posted:**
  - ccpp-physics: issues #401 (SAMF) and #404 (MLM); PRs #405 (SA1), #406 (Thompson), #407 (TEMPO driver), #408 (SAMF + PBL), #409 and #410 (Noah-MP).
  - ufs-weather-model: issues #3404 (staged plan) and #3406 (FPE).
  - ccpp-physics #413 (GFDL MP v3; fork `pr1-gfdlmp` now 552b1d54), GFDL_atmos_cubed_sphere issue #430 and PR #431 (`sedi_heat`), 28 Oct.
  - Commit messages shortened 29 Oct (same trees, authors, dates; force-pushed): #407 ca0fb920, #408 a3a39c1b, #409 459308ff, #410 a3b6720e, #413 593e3161; titles of #407 and #413 shortened. Series has them as `pr1-*-rw`. The 0b/0c physics merges (d4015acb, 911b85fd) still use the old commits: relink after the Orion checks. #405/#406 (approved) unchanged. JCSDA/spack-packages#103 merged 29 Oct by climbfuji.
  - #408 replies, 28 Oct: Han (wet deposition, `reply_408_han.md`) and Lisa (delete the early returns; `pending` as fallback; `reply_408_lisa.md`, evidence `samf_returns/`).
  - Build environment (side track): NOAA-GFDL/FMS#1937 (gcc AVX-512 FPEs, 28 Oct); JCSDA/spack-stack#2144 (Orion/Hercules installed envs; condensed reply 28 Oct, assigned to EPIC) with its merged fixes JCSDA/spack-stack#2145 and #2146.
  - Elsewhere: NCAR/noahmp#274, JCSDA/spack-stack#2188, GCC Bug 128221.
  - #407's body was corrected 27 Oct: it had claimed TEMPO fixes were already proposed to NCAR/TEMPO.
- **Ready, not posted:**
  - 08 then 10 (track 0c): checked and red-teamed. Post the WM PR as a draft, per its template's note.
- **Waiting:**
  - 14 + 15 POSTED (track sx = #405 + floor #414): ufsatm **NOAA-EMC/ufsatm#1156**, WM **ufs-community/ufs-weather-model#3408** (physics `pr1-sa1x` bbb4749f, ufsatm `pr1-sx` 046f4713, WM `pr1-sx` 6a240b4b with RT log). RT job 10317863: 54 compiles, 122 identical, 95 change, 15 not started, 0 fail (#405 alone: 4nests did not complete; #401 instability, comment 6488726665). #414 body has the RT line. rhaesung reply ON HOLD (revise for this pairing).
  - SAMF/PBL package (rhaesung 10-29, issuecomment-6500346441: groups #405+#408+#414 / #406+#407+#413 / #409+#410): #3408 set to draft; #408 added on top (physics `pr1-sa1x` f2a09680, ufsatm `pr1-sx` 0b5097e6, WM `pr1-sx` 362fc3e5, not pushed); RT job 10322653 (`track_sxs.sh`, `rt_sxs`, ECF_OFF 25). Reply to rhaesung POSTED (issuecomment-6501639298). #408 early-return question to Lisa (issuecomment-6485108259) unanswered: wait for her; `reply_408_returns.md` HELD, don't ping. If she wants it in #408, package 1 reruns. Then: commit log, push, retitle/redescribe #1156/#3408, undraft.
  - 0b and 0c are on WM develop 3e48f4cc (BL 20261022); develop is now 783f524a (BL 20261026), so both need relinking and a new RT before posting.
  - 07 and 09 (track 0b): relinked (physics d4015acb, ufsatm d52b9309, WM 46b662cd), not pushed. Push first, then post after 04.
  - #406 owners comment dropped (owner-approved PR; alternative-form numbers kept in `POSTING.history.md` for a reviewer who asks).
- **Owed:** a NCAR/TEMPO report of the graupel and density patterns (#407 says it will follow). Drafted, not posted: `tempo_attr/ncar_tempo_issue.md`. Per-fix attribution done, leave-one-out (`tempo_attr/results.md`). Most of the +0.38 % comes from the semi-Lagrangian fallback sign (T1, ≈ +0.64 %; a forecast change). Graupel creates 0.86 % in the first 6 h. Cloud settling, density and layer depth remove 0.14, 0.12 and 0.01 %. The October ports and their UFS closure are in `../patches/ports/README.md`.
- **Running:** Thompson alternative density/layer-depth form (`thdz/`).
  - Closure done: it closes to round-off like ours, and the known-bad fails.
  - Global precipitation within the `consv_te = 0.999` noise range; regional: alternative − ours up to 0.36 % (0.65 % in `cpld_regional_atm_fbh`) vs one-bit noise up to 0.24 %.
- **Fork vs local:** `pera-noaa/ccpp-physics` `pr1-0b` (01847384) and `pr1-gfdlmp` (919ab856) are older than `series`. `pr1-0c`, `pr1-samf`, `pr1-noahmp-1/-2`, `pr1-thompson`, `pr1-tempo`, `pr1-sa1` and `pr1-xlamue` match.

## Plan

| # | Item | Repository | Head (fork `pera-noaa`) → base | Body |
|---|---|---|---|---|
| 0 | SAMF issue, **#401** | ufs-community/ccpp-physics | — | `bodies/00_SAMF_ISSUE.md` |
| 1 | WM issue, **#3404** | ufs-community/ufs-weather-model | — | `issue_3404_body.md` |
| 2 | SAMF + PBL, **#408** | ufs-community/ccpp-physics | `pr1-samf` → `ufs/dev` | `posted/PR_SAMF_408.md` |
| 3a | Noah-MP 1, **#409** | ufs-community/ccpp-physics | `pr1-noahmp-1` → `ufs/dev` | `posted/PR_NM1_409.md` |
| 3b | Noah-MP 2 (on 3a), **#410** | ufs-community/ccpp-physics | `pr1-noahmp-2` → `ufs/dev` | `posted/PR_NM2_410.md` |
| 4 | GFDL MP v3 (mass basis in the wrapper; `sedi_heat`) | ufs-community/ccpp-physics | `pr1-gfdlmp-wc` (local 552b1d54; push as `pr1-gfdlmp`) → `ufs/dev` | `bodies_v2/04_PR_GMP.md` |
| 5 | Thompson, **#406** | ufs-community/ccpp-physics | `pr1-thompson` → `ufs/dev` | `posted/PR_TH.md` |
| 6 | TEMPO driver, **#407** | ufs-community/ccpp-physics | `pr1-tempo` → `ufs/dev` | `posted/PR_TP_407.md` |
| 7 | ufsatm 0b | NOAA-EMC/ufsatm | `pr1-0b` → `develop` | `bodies_v2/07_ATM_0b.md` |
| 8 | ufsatm 0c | NOAA-EMC/ufsatm | `pr1-0c` → `develop` | `bodies_v2/08_ATM_0c.md` |
| 9 | WM 0b (draft) | ufs-community/ufs-weather-model | `pr1-0b` → `develop` | `bodies_v2/09_WM_0b.md` |
| 10 | WM 0c (draft) | ufs-community/ufs-weather-model | `pr1-0c` → `develop` | `bodies_v2/10_WM_0c.md` |
| 11 | SA1, **#405** | ufs-community/ccpp-physics | `pr1-sa1` → `ufs/dev` | `gh pr view 405` |
| 14 | ufsatm sx (#405 + #414), **NOAA-EMC/ufsatm#1156** | NOAA-EMC/ufsatm | `pr1-sx` → `develop` | `bodies_v2/14_ATM_sa1.md` |
| 15 | WM sx (#405 + #414), **ufs-community/ufs-weather-model#3408** | ufs-community/ufs-weather-model | `pr1-sx` → `develop` | `bodies_v2/15_WM_sa1.md` |
| 16 | xlamue floor, **#414** | ufs-community/ccpp-physics | `pr1-xlamue` → `ufs/dev` | `gh pr view 414` |
| 12 | Noah-MP v5 snow heat, **NCAR/noahmp#274** | NCAR/noahmp | `snow-layer-heat` → `develop` | `posted/PR_NCAR_noahmp_274.md` |
| 13 | GFDL `sedi_heat` issue + PR | NOAA-GFDL/GFDL_atmos_cubed_sphere | `sedi-heat-liquid` → `main` | `gfdl_sedi/issue.md`, `gfdl_sedi/pr.md` |
| — | MLM issue, **#404** | ufs-community/ccpp-physics | — | `issue_390_mlm.md` |
| — | FPE issue, **#3406** | ufs-community/ufs-weather-model | — | `fpe/wm_issue.md` |

## Procedure

- Post in dependency order and add each number to `numbers.json`. It has no `PR_GMP`, `GFDL_SEDI_ISSUE`, `ATM_0b`, `ATM_0c`, `WM_0b` or `WM_0c` yet; `RT_0b` and `RT_0c` are set.
- Before posting a body, `grep -n 'TBD\|\[RT' bodies_v2/<file>` must print nothing.
- In ufsatm and WM bodies, every ccpp-physics reference is qualified (`ufs-community/ccpp-physics#N`), because a bare `#N` links to the host repository.
- WM PRs follow the live template (`.github/pull_request_template.md`, changed 22 Oct). `tools/wm_template_fix.py` rebuilds the Commit Queue block.
- After posting, copy the body to `posted/` and log the post in `POSTING.history.md` if it needs a record beyond the Status.

## Files

- `bodies_v2/`: unposted bodies only. `posted/`: the text as posted. `bodies/` and `post_bundle.py`: the older bundle renderer.
- `reply_*.posted.md`: replies as posted. `reply_*.md`: drafts or earlier replies.
- `_superseded/`: older drafts and copies, listed in `MANIFEST.md`. `tools/`: local copies of the Hercules scripts.
- `gfdl_sedi/`, `gfdl_wrap/`, `ncar_noahmp/`, `fpe/`, `thdz/`, `tempo_attr/`: per-item drafts, tests and harnesses.

History, the dated log and the earlier plan: [`POSTING.history.md`](POSTING.history.md).
