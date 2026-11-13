# 1d (SI1, SI2, FL1, QR1) HAFS crash hold, rerun with the #414 floor

## Status

- **Verdict: the hold is cleared by its pre-registered criterion.** `hafs_global_1nest_atm`, 6 h, 20 members:
  (a) 0b + #414 floor + sea ice/NSST **0 of 20 crash**; (b) control 0b + #414 floor **0 of 20**. All 40 valid.
- Original hold (no floor, `q_t1a`): 3 of 20 (`consv_te` 1, 0.998, 0.994), develop 0 of 20.
- With the floor the SAMF overshoot tail is gone in both arms: (a) 1 event > 4 K in 20 members (4.2 K, `a2_c988`),
  (b) none; `q_t1a` had 241–369 per finished member, largest 72.8 K (a crashed one).
- Precipitation (parent, 6 h mean): (a) 2.43704 ± 0.00051, (b) 2.43749 ± 0.00069 (sd over members);
  a − b = −0.018 % (t = −2.3). Descriptive only, not a criterion.
- Caveats: (1) 0/20 vs 3/20 is p = 0.115 one-sided. It meets the hold's own terms but does not show the crash
  rates are equal. (2) The floor removes the overshoot path that produced the crashes, so this ensemble cannot see
  whether 1d raises that path's rate on code without the floor. 1d's clearance therefore depends on #414 merging first.
  (3) Both arms carry the print-only dbg4 blocks, as the original ensembles did.
- Set 1 (`{a,b}_c*`, 40 jobs) is invalid, not crashes. All failed at step 119 (3 h) with `Permission denied` on
  `grid_mspec*.nc`: the moving nest rewrites them at output time, and they were symlinked to the read-only
  template. Set 2 copies them. Set 1 dirs (~35 GB) are left in place under the no-delete rule; `r14_1d` totals 98 GB.
- Open: nothing in this test. Next step: pair 1d with #414 in the round-1 sequencing.

## Pre-registered criterion (written 29 Oct, before any member ran)

- Ensemble: `hafs_global_1nest_atm`, 6 h, 20 members, parent `consv_te` = 1, 0.999, ..., 0.981 (the original
  `q_t1a` / `q_t1ans` / `q_dev` set, `hafs_samf/q_ens3_stats.txt`).
- Arms: **(a)** physics `pr1-0b` + #414 floor + `pr1-seaice_nsst`; **(b)** `pr1-0b` + #414 floor. Both carry the
  print-only dbg4 SAMF blocks, as the original ensembles did.
- Crash = no `PROGRAM ufs HAS ENDED` in `out`, or a `FATAL` line in `err`. Only a crash with the `compute_qs`
  signature counts as the instability; any other failure makes the member invalid (rerun it, not counted).
- **Clears the hold:** (a) 0 of 20 crash, all 40 members valid.
- **Any crash in (a):** if (b) crashes in the same member, attributed to the base (0b + floor), not to 1d; the
  hold then moves to 0b + floor. If (b) does not, the hold stands.
- Secondary, descriptive only: largest single-step SAMF heating per member (dbg4), (a) vs (b).
- Power caveat, stated before the result: 0/20 vs the original 3/20 is p = 0.115 one-sided; 0/20 meets the
  hold's own terms (it was 3/20 vs 0/20), not a proof that the rates are equal.

## What was built

| | WM | ufsatm | physics (working tree, no commits) | exe md5 |
|---|---|---|---|---|
| (a) | `pr1-0b` 50a26f8c (= develop 783f524a + gitlink) | `pr1-0b` 322025f1 | `pr1-0b` d4015acb + ce5d4d04 diff + d9b70feb..b36e7463 diff + dbg4 | a1d03b1a |
| (b) | same | same | `pr1-0b` d4015acb + ce5d4d04 diff + dbg4 | dbe55710 |

Gates (build job 10327792, `r14_build.sb`; dry run on the login node first):
- **Floor:** in both arms the `samfdeepcnv.f` diff vs `pr1-0b` equals the ce5d4d04 diff line for line. After
  dbg4 is added it equals floor + dbg4 exactly, and `samfshalcnv.f` changes only by additions.
- **1d sources:** arm (a)'s three 1d files equal `pr1-seaice_nsst` and differ from `pr1-0b`; arm (b) is the
  reverse. Each check was run against both arms, so each can fail. md5s match `q/t1a` (the tree that crashed 3/20):
  `sfc_sice.f` 02a63f9d, `sfc_sice.meta` ab05998d, `sfc_nst.f90` 33f7e5b7; (b) 622b2634 / 42155e79 / 1a7b29e3.
- **Base unchanged on the 1d files:** `pr1-0b` and ufs/dev 9b65688c do not touch them since d9b70feb, and
  `pr1-seaice_nsst` is the branch merged in `q/t1a`.
- **Generated caps:** `sfc_sice_run` gets `iter=ccpp_loop_counter` in (a) and no `iter` in (b). This check
  failed in the job on my own bug (wrong build path, and the call range ended at `errflg`), which stopped the
  job before any member was submitted. Rerun by hand with both fixed: a = 1, b = 0. `r14_build.sb` is corrected.
- **Executables:** they differ, and both contain the dbg4 strings.
- **Submodules:** every one is at its gitlink. The tracked `build_*` files that the rsync exclude dropped were
  restored (`r14_setup2.sh`).
- **Run template:** `hafs_exp/tpl`; its namelists, configs and modulefiles are byte-identical to the
  `rt_x0b` `hafs_global_1nest_atm_intel` run dir.
- **Crash detector:** on the stats job's known controls it flags `q_t1a_c1000` (crash, `compute_qs`, step 92)
  and passes `q_t1a_c999` (ended, step 239).

## Jobs

| what | job IDs | result |
|---|---|---|
| build both arms | 10327792 | exes built; job stopped at the cap check (my bug, above) |
| set 1, 40 members (`{a,b}_c*`) | 10328045–10328085 (10328071 is not ours) | all invalid: `grid_mspec` Permission denied at step 119 |
| set 1 stats | 10328086 | `stats.10328086.log` |
| set 2, 40 members (`{a2,b2}_c*`) | 10328238–10328278 (10328243 is not ours) | all COMPLETED 0:0, 2 min 17 s – 2 min 23 s each, last ended 17:50:27 |
| set 2 stats | 10328279 | started 17:50:28, after the last member ended, so the dependency did not fire early. `stats2.10328279.log` |
| set 2 recheck (login node, after the 17:00–17:41 broker outage) | — | `stats2_recheck.txt`: 40 ended, 0 crash; 40/40 `out` contain `PROGRAM ufs HAS ENDED` |

Paths: `U=/work2/noaa/co2/ash/ufs-chem-v1/upstream`; runs and logs in `$U/pr1/r14_1d/`, scripts in
`$U/pr1/r14_1d_scripts/` (local copies in `runs_29oct/1d_hafs_scripts/`).

## Crash table, set 2 (consv_te = parent `input.nml`; nest 0.)

| consv_te | (a) ended / step / crash | (a) events > 4 K, max | (b) ended / step / crash | (b) events > 4 K, max |
|---|---|---|---|---|
| 1. | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.999 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.998 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.997 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.996 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.995 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.994 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.993 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.992 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.991 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.990 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.989 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.988 | 1 / 239 / 0 | 1, 4.2 K (CFL 1.5) | 1 / 239 / 0 | 0 |
| 0.987 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.986 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.985 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.984 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.983 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.982 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| 0.981 | 1 / 239 / 0 | 0 | 1 / 239 / 0 | 0 |
| **total** | **0 / 20 crash** | 1 event | **0 / 20 crash** | 0 |

The original `q_t1a` crashed at 1. (step 92), 0.998 (163) and 0.994 (56). Here they end in both arms. Per-member
precipitation and TKE-cap counts are in `stats2.10328279.log`.
