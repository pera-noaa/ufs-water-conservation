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
