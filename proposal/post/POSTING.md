# Upstream posting: state and plan

## Status (29 October 2026)

- **Packaging.** rhaesung (ccpp-physics code manager) asked for one ufsatm/WM pair per group
  ([#405 comment 6500346441](https://github.com/ufs-community/ccpp-physics/pull/405#issuecomment-6500346441)); agreed
  ([reply 6501639298](https://github.com/ufs-community/ccpp-physics/pull/405#issuecomment-6501639298)). The ccpp-physics
  PRs stay separate so their reviews stand. Tracks 0b/0c are replaced by these packages.
- **Package 1, SAMF / PBL** (#405 ✓, #408 ✓, #414 ✓): pair NOAA-EMC/ufsatm#1156 + ufs-community/ufs-weather-model#3408
  (draft). Pushed: #405 + #414 only. RT with #408 added done; push and body update **on hold** (user, 29 Oct).
- **Package 2, microphysics** (#406 ✓, #407, #413): waiting for reviews of #407 and #413. No pair yet.
- **Package 3, Noah-MP** (#409, #410): waiting for reviews. No pair yet.
- **Held:** `reply_408_returns.md` — wait for Lisa's answer to the early-return question
  ([#408 comment 6485108259](https://github.com/ufs-community/ccpp-physics/pull/408#issuecomment-6485108259)); don't ping.
  If she wants the deletion in #408, package 1 reruns its RT.
- **Owed:** NCAR/TEMPO report (#407 says it will follow); draft `tempo_attr/ncar_tempo_issue.md`, to split into the
  semi-Lagrangian sign fix (issue + one-line PR) and fixes 2–4.
- **Build side track:** FMS#1937 answered (rem1776, 29 Oct: add the flag to `ReleaseUFS`/`DebugUFS` as needed).
  JCSDA/spack-packages#103 merged; cherry-picks for `spack-stack-dev` and spack/spack-packages prepared locally
  (`fpe/pr_fms/sp/`), not pushed. JCSDA/spack-stack#2144 is with EPIC.
- Approved (✓) as of 29 Oct: #405, #406, #408, #414. Roadmap and verification plan: [`../../README.md`](../../README.md).

## Package 1: what is where

| Repo | Branch (fork `pera-noaa`) | On GitHub | Held on Hercules (`$U/pr1/series`, `$U/pr1/rt_sxs`) |
|---|---|---|---|
| ccpp-physics | `pr1-sa1x` | bbb4749f (#405 + #414) | f2a09680 (+ merge of #408 a3a39c1b) |
| ufsatm | `pr1-sx` | 046f4713 | 0b5097e6 |
| ufs-weather-model | `pr1-sx` | 6a240b4b (RT log, #405 + #414) | 362fc3e5, 47dbddfb (RT log with #408) |

All three held tips fast-forward the GitHub ones; local copies are in `fpe/pr_fms/cp` and the scratch clones, bundles in
`$U/pr1/sxs_bundles/`. Bodies for the update: `bodies_v2/14_ATM_sxs.md`, `bodies_v2/15_WM_sxs.md`; new titles
"Update ccpp-physics for SAMF/PBL conservation fixes (#405, #408, #414)" and "SAMF and PBL conservation fixes".

| RT (Hercules, Intel + GNU, WM develop 783f524a, baselines 20261026) | job | compiles | identical | changed | not started | failed |
|---|---|---|---|---|---|---|
| #405 alone (`rt_sa1`) | 10314680 | 54/54 | 122 | 94 | 15 | 1 (`hafs_global_multiple_4nests_atm`, #401) |
| #405 + #414 (`rt_sx`, posted log) | 10317863 | 54/54 | 122 | 95 | 15 | 0 |
| #405 + #408 + #414 (`rt_sxs`, held) | 10322653 | 54/54 | 122 | 95 (same tests) | 15 | 0 |

`rt_sxs` was checked to contain #408: `control_p8` 24-h output differs from `rt_sx` (T up to 5.2 K, q up to 4.6 g/kg).
The 4-nest HAFS crash is the #401 instability (5 `consv_te` members: develop 1 crash, #405 2, either + floor 0;
[#401 comment 6488726665](https://github.com/ufs-community/ccpp-physics/issues/401#issuecomment-6488726665)).

## Items

| # | Item | Repository | Head (fork `pera-noaa`) → base | Text | State |
|---|---|---|---|---|---|
| 0 | SAMF instability issue, **#401** | ufs-community/ccpp-physics | — | `bodies/00_SAMF_ISSUE.md` | open |
| — | MLM issue, **#404** | ufs-community/ccpp-physics | — | `issue_390_mlm.md` | open, no reply |
| 1 | WM staged-plan issue, **#3404** | ufs-community/ufs-weather-model | — | `issue_3404_body.md` | open |
| — | FPE issue, **#3406** | ufs-community/ufs-weather-model | — | `fpe/wm_issue.md` | open |
| 11 | SA1, **#405** | ufs-community/ccpp-physics | `pr1-sa1` → `ufs/dev` | `gh pr view 405` | approved; package 1 |
| 2 | SAMF + PBL, **#408** | ufs-community/ccpp-physics | `pr1-samf` → `ufs/dev` | `posted/PR_SAMF_408.md` | approved; package 1 |
| 16 | `xlamue` floor, **#414** | ufs-community/ccpp-physics | `pr1-xlamue` → `ufs/dev` | `posted/PR_XLAMUE_414.md` | approved; package 1 |
| 14 | ufsatm package 1, **NOAA-EMC/ufsatm#1156** | NOAA-EMC/ufsatm | `pr1-sx` → `develop` | `posted/ATM_1156.md` | update held |
| 15 | WM package 1, **ufs-community/ufs-weather-model#3408** | ufs-community/ufs-weather-model | `pr1-sx` → `develop` | `posted/WM_3408.md` | draft; update held |
| 5 | Thompson, **#406** | ufs-community/ccpp-physics | `pr1-thompson` → `ufs/dev` | `posted/PR_TH.md` | approved; package 2 |
| 6 | TEMPO driver, **#407** | ufs-community/ccpp-physics | `pr1-tempo` → `ufs/dev` | `posted/PR_TP_407.md` | review; package 2 |
| 4 | GFDL MP v3, **#413** | ufs-community/ccpp-physics | `pr1-gfdlmp` → `ufs/dev` | `posted/PR_GMP_413.md` | review; package 2 |
| 3a | Noah-MP 1, **#409** | ufs-community/ccpp-physics | `pr1-noahmp-1` → `ufs/dev` | `posted/PR_NM1_409.md` | review; package 3 |
| 3b | Noah-MP 2 (on 3a), **#410** | ufs-community/ccpp-physics | `pr1-noahmp-2` → `ufs/dev` | `posted/PR_NM2_410.md` | review; package 3 |
| 12 | Noah-MP v5 snow heat, **NCAR/noahmp#274** | NCAR/noahmp | `snow-layer-heat` → `develop` | `posted/PR_NCAR_noahmp_274.md` | review |
| 13 | GFDL `sedi_heat`, issue **#430** + PR **#431** | NOAA-GFDL/GFDL_atmos_cubed_sphere | `sedi-heat-liquid` → `main` | `gfdl_sedi/issue_post.md`, `gfdl_sedi/pr_post.md` | review |
| 7–10 | ufsatm/WM tracks 0b, 0c | — | — | `_superseded/bodies_v2/` | replaced by packages |

## Procedure

- Add each new number to `numbers.json`.
- Before posting a body, `grep -n 'TBD\|\[RT' <file>` must print nothing.
- In ufsatm and WM bodies, qualify every ccpp-physics reference (`ufs-community/ccpp-physics#N`): a bare `#N` links to
  the host repository.
- WM PRs follow the live template (`.github/pull_request_template.md`); `tools/wm_template_fix.py` rebuilds the Commit
  Queue block. Commit the Hercules RT log and `test_changes.list` on the WM branch, never the local `rt.sh` edit.
- A package's physics branch is a `--no-ff` merge of its PR branches on `ufs/dev`, gated on its diff equalling the sum
  of the PRs' diffs. Later changes go on top; never force-push a posted branch.
- Hercules has no GitHub push credentials: move commits as `git bundle` (base64 through `broker run`) and push from
  the Mac.
- After posting, copy the text as posted to `posted/` (or `reply_*.posted.md`).

## Files

- `bodies_v2/`: unposted bodies only. `posted/`: texts as posted. `bodies/` and `post_bundle.py`: the older renderer.
- `reply_*.posted.md`: replies as posted; `reply_*.md`: drafts or earlier replies.
- `_superseded/`: older drafts and copies, listed in `MANIFEST.md`. `tools/`: local copies of the Hercules scripts.
- `gfdl_sedi/`, `gfdl_wrap/`, `ncar_noahmp/`, `fpe/`, `thdz/`, `tempo_attr/`, `samf_returns/`: per-item drafts, tests
  and harnesses. `fpe/pr_fms/{cp,sp,spack}/` are third-party git clones, not tracked.

History, the dated log and earlier plans: [`POSTING.history.md`](POSTING.history.md).
