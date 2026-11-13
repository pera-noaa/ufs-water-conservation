# Conservation meters: handover guide

The in-model budget meters behind every water, energy and tracer number in this project: what each one measures, how
to apply it, how to read its output, and where it breaks. The design for replacing them with maintained upstream code
is [`meter_design.md`](meter_design.md).

## Status

- **The meters are diagnostic builds, not maintained code.** Each one is a Python script that patches Fortran source
  by exact-string anchors, or a frozen `diff` against one specific tree. None is upstream, and none rebases itself onto
  a newer `develop`.
- **They are trustworthy where they were used.** On every gated tree, a build with meters is bitwise identical to the
  same build without them (`-no-fma` builds; see Limits for the exceptions). Each meter was also shown to fail: on
  unmodified develop the physics meter reports the +0.26–0.29 % water source.
- **No meter code is in the proposed fixes.** `../experiments/conservation/replay/tools/meter_tokens.py` finds 0 meter-only
  identifiers in `full14` and 24 in the known-bad metered tree.
- **About eight separate meter families.** Each measurement campaign wrote its own, with its own output records and
  reader. The table below says which one to reach for.
- **Single-threaded only.** Every accumulator is module state. With 2 OpenMP threads the physics sums differ
  (`../experiments/conservation/trdyn/report.md`). Run with `atm_omp_num_threads = 1`.
- **On current `develop` (capgen-v1, after ufsatm #1145) use the prototype instead.** The upstream-layout physics
  meters no longer apply there: `GFS_physics_post` was refactored (no `qgrs`/`gq0`, now in the `stochastics` group).
  The prototype in `meter_proto/ufs/` gives whole-physics, non-physics and per-family water budgets, is
  answer-neutral, and is thread- and layout-invariant ([`meter_proto/results.md`](meter_proto/results.md)).

## Which meter for which question

| Question | Meter (apply) | Records | Reader |
|---|---|---|---|
| Does the physics create or destroy water, and in which family? (current `develop`) | `meter_proto/ufs/apply_meterproto.py <wm-root>`, then `&budget_nml budget_meter=.true., budget_hook=.true.` | `BUDGET water` | `meter_proto/ufs/mp_compare.py budget <rundir>` |
| Does the physics create or destroy water? (upstream layout) | `scripts/instrument_wb_phys_ups.py`, then `instrument_wb_ep_ups.py` | `WBP`, `WBQ` | `scripts/wb_meter_report_ups.py` |
| Where in Thompson? (upstream layout) | `instrument_wb_ups.py`, then `_ups_rten.py`, `_neg_stages.py`, `_negr_floor.py` | `WBT` slots | `wb_meter_report_ups.py`, `instrument_wb_neg_report.py`, `instrument_wb_negr_report.py` |
| Physics vs dycore water split (v1 snapshot) | `instrument_wb.py`, `instrument_wb_phys.py`, `instrument_wb_dyn.py` | `WBT`, `WBP`, `WBD` | `phys_meter_budget.py`, `dyn_meter_budget.py` |
| Land–atmosphere water hand-off, Noah-MP storage (v1 snapshot) | `instrument_wb_land.py`, then `instrument_wb_noahmp*.py`, `_glacier_*.py`, `_iter2.py` | `WBL`, `WBE`, `WBK`, `WBZ`, `WBGF`, `WBQ` | `land_meter_budget.py`, `iter2_budget.py` |
| Noah-MP water in NOAA-EMC/noahmp's own driver | `instrument_noahmp_emc_meter.py` | see docstring | docstring |
| Total energy per physics segment, dycore and coupling | `../experiments/conservation/energy/meters/meter_ccpp_physics.diff` + `meter_fv3_dycore_coupling.diff` (+ `encpl/patches/meter_r2.diff` for frame F) | `EMS`, `EMF`, `EBC`, `EBD`, `EBX` | `../experiments/conservation/energy/meters/tools/eb_table.py`, `eb_check.py` |
| FV3 dycore energy, term by term | `../experiments/conservation/fv3tally/meters/meter_fv3tally.diff` (+ `fv_etally.F90`); run-time switch `FV3_ETALLY=1` | see report | `../experiments/conservation/fv3tally/report.md` |
| Passive-tracer mass, dycore and physics | `../experiments/conservation/tracer/meters/02_meters_ccpp-physics.diff` + `03_meters_fv3.diff` (test hooks 01, 04 optional) | `TM`, `TP`, `TQ`, `TC`, `TH`, `TD`, `TS`, `TO`, `TU` | `../experiments/conservation/tracer/scripts/analyze_tm.py`, `analyze_dry.py` |
| Energy and water in MYNN-EDMF, GFDL MP v3, Grell–Freitas suites | `../experiments/conservation/suites/meters/01_suites_meter.diff` (`02_` on the fixed tree) | `SMS`, `SMT`, `SMH` (layout-independent column hashes), `SMX` | `../experiments/conservation/suites/report.md` |
| Surface energy, PBL heating, convective heating, SAMF wet deposition, precipitation-enthalpy lag, uniform-tracer structure | `meters/` (or `patches/meter_*`) in `ensfc/`, `ensfc2/`, `enpbl/`, `encnv/`, `latent/`, `preclag/`, `trunif/` | extend the energy or tracer records | that folder's `report.md` |

Single-purpose meters, each written to answer one question and recorded in the proposal or a campaign report:
`instrument_wb_ka*.py` (SAMF cloud base, fix SA1), `instrument_wb_osc_*.py` (step-771 oscillation),
`instrument_wb_gc*.py` (flagged columns per scheme), `instrument_wbb*.py` (write-back statements),
`instrument_wb_driver.py` (Thompson driver frame), `instrument_tr.py` (v1 passive tracers, `TRP`/`PTM`, read by
`tr_meter_budget.py`), `instrument_wrf_mp_meter.py` (WRF Thompson port).

The per-scheme split from `ldiag3d`/`qdiag3d` history output (`water_budget_by_scheme.py`) is not a meter. It is
biased by about 10⁻⁴ kg/m² per 6 h (pitfall 5 below), so use it only for differences between builds.

## Applying a meter

**Scripts** (`scripts/instrument_*.py <tree>`):
- They edit the source tree in place, so use a copy.
- The docstring names the tree layout: `<ufs_model.fd>` is the v1 snapshot; `<ufs-weather-model>` or `_ups` is the
  upstream layout.
- Order matters, and each docstring says "apply after …". 31 of the 42 scripts abort unless every anchor matches
  exactly once.
- A script that aborts means the source moved. Re-anchor the script; do not loosen the match.

**Diffs** (`conservation/*/meters/*.diff`):
- Apply from the tree root with `patch -p1 -F0` (the `-ruN` diffs are `-p1` from the directory named in their first
  line).
- The tree each diff was cut against is named in that folder's `report.md`. The diff headers do not name it
  consistently: `a/`, `mfx/`, `mopt/`, `meter/`.
- Never pass `-F` above 0. The build scripts in `energy/meters/tools/` that run `patch … || true` do check for
  `.rej` files afterwards; keep it that way.

**Builds:**
- Compare metered against unmetered only with `-no-fma` builds. In release builds, meter statements placed inside a
  physics routine change FMA contraction, so the answers differ at round-off (`../experiments/conservation/samfinit/report.md`).

## Running and reading

- Run with `atm_omp_num_threads = 1` and `srun --label`. The readers take the run directory and parse `out`
  (stdout).
- Rank prefixes: the water records are per rank and cumulative, and the readers sum them over ranks at equal `kdt`.
  `TM`, `EMS` and `SMS` are already reduced and printed by the root rank.
- Area weights: water readers use the model's own cell areas (from the meter) and print the snapshot-file area beside
  them, so a mismatch is visible.
- Window env vars: `WB_WINDOW` and `WB_END` (hours) for the water readers, `WB_AT` for `wb_meter_report_ups.py`.
  `TR_SNAP` and `TR_NMAX` for `tr_meter_budget.py`.
- Passive check before quoting a metered number: compare the metered and unmetered runs' history files with
  `instrument_wb_ka_bitcmp.py <runA> <runB>` or `../experiments/conservation/energy/meters/tools/cmp_allvars.py`. 0 differing
  variables is the pass.

## Pitfalls

Each of these produced a wrong number at least once. Full text: `../proposals/water_closure_proposal.md` §8.

1. `prate_ave` and the other `_ave` fields are averaged since the start of the run, not over the bucket. Use the
   `*b_ave` bucket fields (`prateb_ave`, `cpratb_ave`).
2. `atmf000` is written after the first time step. A budget that starts there carries a +0.023 kg/m² cold-start
   artefact.
3. The output `dpres` is `delp·(1 − Σ condensate)`, while tracers are per total mass. Use `dpres/(1 − Σ condensate)`
   for column water, or a fake "dynamics loss" of 3–6 × 10⁻⁵ kg/m² per 6 h appears.
4. The water readers' bucket must equal `fhzero`. A longer window over shorter buckets silently reads only the last
   bucket.
5. The per-scheme split from history output cannot resolve scheme residuals below about 0.05 % of the scheme's flux.
   For absolute levels, use a meter.
6. Match the meter's span to the budget window. A meter summed over 0–24 h compared with host 6–24 h windows includes
   the cold-start burst.
7. CCPP runs each scheme over all of a rank's blocks before the next scheme. A value handed from one scheme to a later
   one through a module array must be queued per block.
8. Glacier `waxy` is bookkeeping: it is set to 4900 mm and zeroed on the first call, so a land meter shows −4900 mm
   per glacier column once.
9. A meter placed at a point a fix never reaches shows inactivity, not conservation. `fv_update_phys` water never
   fired in these runs.

## Limits of the code

| Limit | Where | Consequence |
|---|---|---|
| Module-level accumulators | every family | wrong sums with more than one OpenMP thread |
| Fixed 8,192 columns per rank, no bounds check | `energy_meter_common.F90` (`emnc`) | silent overwrite when a rank holds more columns, e.g. C96 on 6 ranks or C384 on fewer than 108 |
| Hard-coded FV3 heat capacities next to the host's `con_cp` | `em_probe` | must be kept in step with FV3 by hand |
| 12 near-identical probe schemes `em_p01`–`em_p12` (generated by `energy/meters/tools/instrument_eb_phys.py`) | energy meter | 3,442-line diff; a probe change means regenerating every probe |
| One suite per energy meter (`FV3_GFS_v17_p8_ugwpv1`) | energy meter | other suites need the separate suites meter |
| Text records on stdout | every family | each family needs its own parser |
| Hercules paths hard-wired (`$U`, `$E`) | `energy/meters/tools/*.sh`, the run-staging scripts | the build and run scripts do not run elsewhere unedited |
| The heat-profile meter is not bitwise passive | `encnv/meters/meter_heat_profile.diff` | use it for attribution only, never for a closure number |

## Hercules

Trees and runs are under `$U = /work2/noaa/co2/ash/ufs-chem-v1/upstream`: `$U/cons/<folder>` for each conservation
campaign, and `$U/cons/energy` (`$E`) for the energy integrator's metered twins (`mall_*`, `mallq_*`). Metered water
trees carry an `m` suffix (`patched18m`).
