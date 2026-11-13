# Upstream posting: state and plan

## Status (12 November 2026)

- **Merge route: waiting on the code managers.** One ufsatm/WM pair per group is agreed. rhaesung and gspetro-NOAA asked
  that `ufs/dev` get exactly the tested tree; answered ([#405 6833781836](https://github.com/ufs-community/ccpp-physics/pull/405#issuecomment-6833781836)):
  one combined ccpp-physics PR per group from the package branch, and asked whether #403 or package 1 merges first.
- **#403** (Jongil Han's PBL/convection update) re-implements #405, #408 and #414 and carries his shallow `xlamue` form
  (62485fc1). Approved by rhaesung and JongilHan66. #414 stays deep-only ([6833781177](https://github.com/ufs-community/ccpp-physics/pull/414#issuecomment-6833781177)).
- **Package 1, SAMF/PBL** (#405, #408, #414, all approved): full RT on the complete tree done (`rt_sxd5`, below). Push
  and the #1156/#3408 body update held (Ash) until the merge order is settled.
- **Package 2, microphysics** (#406, #407 approved; #413 in review): waits on #413. No pair yet.
- **No reviews yet:** #409, #410 (package 3), #413, NOAA-EMC/ufsatm#1156, NCAR/noahmp#274, GFDL_atmos_cubed_sphere#430/#431.
- **Issues open, no reply:** #401; #404 (description rewritten: fix v3 with guards, RT pass, forecast impact, negative
  condensate); NCAR/ccpp-physics#1251 (untagged, not run); WM #3404, #3406. #403 answered on `diff3d` (÷ the physics' `del`).
- **Owed:** NCAR/TEMPO PR (graupel + density, ported to c62699fb) and the T1 fallback-sign issue; plan `tempo/PLAN_tempo_upstream.md`.
- **Owed on #406 (12 Nov replies):** open a separate issue for the base `prg_rcg` re-close in Re-enforce (same exposure as the rain-snow limit). Draft: `issues/issue_thompson_prg_rcg.md`. (`series` `pr1-thompson` fast-forwarded to abd89364 on 12 Nov; package 2 not built yet, so nothing to relink.)
- **Build side track:** FMS#1937 answered; JCSDA/spack-packages#103 merged; JCSDA/spack-stack#2144 with EPIC.

| PR | Approved by | Merged |
|---|---|---|
| #405 | dustinswales | no |
| #406 | dustinswales, rhaesung | no |
| #407 | rhaesung | no |
| #408 | JongilHan66 | no |
| #414 | JongilHan66, Qingfu-Liu | no |

Dated posting log and earlier status blocks: [`POSTING.history.md`](POSTING.history.md). Roadmap: [`ROADMAP.md`](ROADMAP.md).

## Package 1: what is where

| Repo | Branch (fork `pera-noaa`) | On GitHub | Held on Hercules (`$U/pr1/series`, `$U/pr1/rt_sxs`) |
|---|---|---|---|
| ccpp-physics | `pr1-sa1x` | bbb4749f (#405 + #414) | f2a09680 (+ merge of #408 a3a39c1b) |
| ufsatm | `pr1-sx` | 046f4713 | 0b5097e6 |
| ufs-weather-model | `pr1-sx` | 6a240b4b (RT log, #405 + #414) | 362fc3e5, 47dbddfb (RT log with #408) |
| tested full tree (`$U/pr1/rt_sxd5`) | ccpp-physics 44defba3, ufsatm 7861900, WM 3d0703d2 | not pushed; no bundles yet | #408 incl. e5624dd6 (deep returns); e50fcc77 (shallow returns) not in it, bitwise-neutral (`shal_xlamue_414.md`, pA = pA0) |

All three held tips fast-forward the GitHub ones; local copies are in `fpe/pr_fms/cp` and the scratch clones, bundles in
`$U/pr1/sxs_bundles/`. Bodies for the update: `bodies_v2/14_ATM_sxs.md`, `bodies_v2/15_WM_sxs.md`; new titles
"Update ccpp-physics for SAMF/PBL conservation fixes (#405, #408, #414)" and "SAMF and PBL conservation fixes".

| RT (Hercules, Intel + GNU, WM develop 783f524a, baselines 20261026) | job | compiles | identical | changed | not started | failed |
|---|---|---|---|---|---|---|
| #405 alone (`rt_sa1`) | 10314680 | 54/54 | 122 | 94 | 15 | 1 (`hafs_global_multiple_4nests_atm`, #401) |
| #405 + #414 (`rt_sx`, posted log) | 10317863 | 54/54 | 122 | 95 | 15 | 0 |
| #405 + #408 + #414 (`rt_sxs`, held) | 10322653 | 54/54 | 122 | 95 (same tests) | 15 | 0 |
| #405 + #408 + #414 + deep early returns deleted (`rt_sxd5`, WM develop 560345cc, baselines 20261028) | 10328901 | 54/54 | 122 | 95 (same tests as `rt_sxs`) | 15 | 0 |

`rt_sxs` was checked to contain #408: `control_p8` 24-h output differs from `rt_sx` (T up to 5.2 K, q up to 4.6 g/kg).
The 4-nest HAFS crash is the #401 instability (5 `consv_te` members: develop 1 crash, #405 2, either + floor 0;
[#401 comment 6488726665](https://github.com/ufs-community/ccpp-physics/issues/401#issuecomment-6488726665)).

## Items

| # | Item | Repository | Head (fork `pera-noaa`) → base | Text | State |
|---|---|---|---|---|---|
| 0 | SAMF instability issue, **#401** | ufs-community/ccpp-physics | — | `bodies/00_SAMF_ISSUE.md` | open |
| — | MLM issue, **#404** | ufs-community/ccpp-physics | — | `issues/issue_404_body_v2.md` | open, rewritten 12 Nov (test-base line corrected same day: develop 560345cc + package 1), no reply |
| — | `shinhongvdif` stale index, **NCAR/ccpp-physics#1251** | NCAR/ccpp-physics | — | `issues/issue_vdiff_indices_draft.md` | open, untagged |
| — | Jongil's PBL/convection PR, **#403** (not ours) | ufs-community/ccpp-physics | — | `replies/reply_403_jongil_dxc.md` (our last reply, 12 Nov) | approved; re-implements package 1 |
| 1 | WM staged-plan issue, **#3404** | ufs-community/ufs-weather-model | — | `issues/issue_3404_body.md` | open |
| — | FPE issue, **#3406** | ufs-community/ufs-weather-model | — | `fpe/wm_issue.md` | open |
| 11 | SA1, **#405** | ufs-community/ccpp-physics | `pr1-sa1` → `ufs/dev` | `gh pr view 405` | approved; package 1 |
| 2 | SAMF + PBL, **#408** | ufs-community/ccpp-physics | `pr1-samf` → `ufs/dev` | `posted/PR_SAMF_408.md` | approved; package 1 |
| 16 | `xlamue` floor, **#414** | ufs-community/ccpp-physics | `pr1-xlamue` → `ufs/dev` | `posted/PR_XLAMUE_414.md` | approved; package 1 |
| 14 | ufsatm package 1, **NOAA-EMC/ufsatm#1156** | NOAA-EMC/ufsatm | `pr1-sx` → `develop` | `posted/ATM_1156.md` | update held |
| 15 | WM package 1, **ufs-community/ufs-weather-model#3408** | ufs-community/ufs-weather-model | `pr1-sx` → `develop` | `posted/WM_3408.md` | draft; update held |
| 5 | Thompson, **#406** | ufs-community/ccpp-physics | `pr1-thompson` → `ufs/dev` | `posted/PR_TH.md` | approved (dustinswales, rhaesung); AndersJensen-NOAA changes requested 12 Nov, answered same day (`replies/reply_406_anders.md`), approved by him 23:02Z at abd89364; L720 interface kept as is (`replies/reply_406_anders_dz.md`); package 2 |
| 6 | TEMPO driver, **#407** | ufs-community/ccpp-physics | `pr1-tempo` → `ufs/dev` | `posted/PR_TP_407.md` | approved; package 2; 13 Nov: ufs/dev merged + layer depth (1c664a4f), TEMPO RT subset passed (`tempo/PREREG_tp407.md`), note 6848990859 |
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
- After posting, copy the text as posted to `posted/` (or `replies/reply_*.posted.md`).

## Files

- `bodies_v2/`: unposted bodies only. `posted/`: texts as posted. `bodies/` and `post_bundle.py`: the older renderer.
- `replies/`: `reply_*.posted.md` as posted, `reply_*.md` drafts or earlier replies, and the reply reviews. `issues/`: issue bodies and drafts.
- `_superseded/`: older drafts and copies, listed in `MANIFEST.md`. `tools/`: local copies of the Hercules scripts.
- `gfdl_sedi/`, `gfdl_wrap/`, `ncar_noahmp/`, `fpe/`, `thdz/`, `tempo/`, `samf_returns/`: per-item drafts, tests
  and harnesses. `fpe/pr_fms/{cp,sp,spack}/` are third-party git clones, not tracked.

History, the dated log and earlier plans: [`POSTING.history.md`](POSTING.history.md).
