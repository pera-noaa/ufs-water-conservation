# Posting tracks 0a, 0b, 0c

Posted: item 0, the SAMF issue, ufs-community/ccpp-physics#401 (20 October 2026; `numbers.json`). `post_bundle.py [numbers.json]` renders `bodies/` from `../pr_round1_descriptions.md` in
each repository's template order, unwrapped for GitHub. It fills each `#TBD` from `numbers.json` and prints, per
item, what is still unfilled and the `gh` command. Tracks 1c and 1d, and the GFDL issue (§2, which goes with the
FV3 PR), are not in the bundle.

| # | Item | Repository | Head (fork `pera-noaa`) → base | Body |
|---|---|---|---|---|
| 0 | SAMF issue (0a), **posted #401** | ufs-community/ccpp-physics | — | `00_SAMF_ISSUE.md` |
| 1 | WM issue (0a) | ufs-community/ufs-weather-model | — | `01_WM_ISSUE.md` |
| 2 | SAMF + PBL (0b) | ufs-community/ccpp-physics | `pr1-samf` → `ufs/dev` | `02_PR_SAMF.md` |
| 3 | Noah-MP (0b) | ufs-community/ccpp-physics | `pr1-noahmp` → `ufs/dev` | `03_PR_NM.md` |
| 4 | GFDL MP v3 (0b) | ufs-community/ccpp-physics | `pr1-gfdlmp` → `ufs/dev` | `04_PR_GMP.md` |
| 5 | Thompson (0c) | ufs-community/ccpp-physics | `pr1-thompson` → `ufs/dev` | `05_PR_TH.md` |
| 6 | TEMPO driver (0c) | ufs-community/ccpp-physics | `pr1-tempo` → `ufs/dev` | `06_PR_TP.md` |
| 7 | ufsatm 0b | NOAA-EMC/ufsatm | `pr1-0b` → `develop` | `07_ATM_0b.md` |
| 8 | ufsatm 0c | NOAA-EMC/ufsatm | `pr1-0c` → `develop` | `08_ATM_0c.md` |
| 9 | WM 0b | ufs-community/ufs-weather-model | `pr1-0b` → `develop` | `09_WM_0b.md` |
| 10 | WM 0c | ufs-community/ufs-weather-model | `pr1-0c` → `develop` | `10_WM_0c.md` |

`numbers.json` keys: `SAMF_ISSUE`, `WM_ISSUE`, `PR_SAMF`, `PR_NM`, `PR_GMP`, `PR_TH`, `PR_TP`, `ATM_0b`,
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
