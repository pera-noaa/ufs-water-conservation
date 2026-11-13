# replay: the proposal's diff series reproduces full14 exactly

## Status update (18 Oct 2026): series moved to full14 (`SERIES.md`; the full13 version is `SERIES.history.md`)
- **Series:** 55 proposed diffs + `56_NOFMA`. Nothing was renumbered.
  - Row 16 (TH8) is retired.
  - 43 = `13_TH8-TH9_unconditional` (cut on fx, verbatim).
  - 46 = PL1 composed with `delta_PL1_folded_into_EP1`.
  - New row 57 = NM10r (`delta_NM10r`, verbatim).
  - Rows 50, 51 and 53 are verbatim again: TH9's switch lines are gone.
  - Counts: 50 verbatim, 4 rebased (28, 30, 38, 42), 1 composed (46).
- **Gate:** `diff -r` of fresh base + `apply_series.sh` against `$E/full14` is EMPTY. Known-bad (57 omitted) fails on
  3 files.
- **Bug-fix arm:** the unconditional rows (incl. 43 and 57; 38 and 57 as cut) equal `$E/gB14` exactly.
- **Runs (exe job 10158558):** all-on 24 h vs `rs14_S` and default-off vs `gA14_off` are both byte-identical, in every
  atmf, sfcf and RESTART file. All-on cannot tell full13 from full14 (rs13_S = rs14_S), so default-off is the
  discriminating check (gA13_off vs gA14_off differs).
- **Meters:** full14 has 0 meter-only identifiers; mq14 has 24; the series' + lines have 0 hits.
- **Water 17r:** applies at -F0 on develop + water 01–16, and water 18 applies after it (3 offsets). Known-bad: 17r
  after 17 fails.
- **Files:** `patches/` and `repo_diffs/` are full14; `patches_full13/` and `repo_diffs_full13/` keep full13.

## Status (18 Oct 2026, full13; superseded by the update above)
- Base: develop @112b1d46 + water diffs 01–19 + 09b (`$E/base` = `$U/p20rt_final` source).
- Series: 55 proposed diffs (manifest rows 1–55) + `56_NOFMA` (build setting, not proposed; `apply_series.sh <tree> 56_NOFMA` skips it). 48 verbatim (19 with line offsets, no fuzz); 7 rebased from the integrator's own re-anchoring (28 03b, 30 DYN v6, 38 SL2, 42 E2, 50/51/53 suites 03/04/06); none extracted.
- Row 42 carries a one-line merge (noahmpdrv.F90 argument list edited by rows 41 and 42); row 15 (`accepted/10r`) a similar one-line merge in samfshalcnv.f.
- Gate: fresh base + `apply_series.sh` vs `$E/full13`, `diff -r` (excl. .git, build dirs, exes, logs, modules, *.orig/*.rej) EMPTY. Known-bad (omit `52_PBL05`) fails on satmedmfvdifq.F. Stage boundaries equal `$E/fx`, all_full, full6, full10–13.
- Meters: full13 contains none of 380 meter-only identifiers; mq13 (known-bad) shows 21.
- Build/run: replay tree built (job 10157729), 24 h run byte-identical to `rs13_S` in 30 atmf, 30 sfcf, 76 RESTART files (job 10157768); comparator flags rs13_S vs rs12_S.
- full13 holds 7 stray `*.orig` backups from the integrator's patch calls (harmless).

## Per-repository combined diffs (`repo_diffs/`, base → full13, submodule-relative)
| repository | files | +/− |
|---|---|---|
| GFDL_atmos_cubed_sphere | 10 | +1199 / −36 |
| ccpp-physics | 41 | +2987 / −201 |
| UFSATM (ccpp/data, ccpp/driver, ccpp/CMakeLists.txt) | 7 | +446 / −3 |
| noahmp (E2 only) | 1 | +28 / 0 |
| ufs-weather-model (−no-fma, not proposed) | 1 | +1 / −1 |

MPAS (manifest rows 56–59) is a separate repository, outside this replay.

## Files
`SERIES.md` (canonical order, class, switch, repo), `apply_series.sh`, `patches/` (+ `series.txt`), `repo_diffs/`, `tools/`, `logs/`; Hercules mirror `$U/cons/replay`.
(Written by main from the agent's hand-off; the agent could not write report.md.)
