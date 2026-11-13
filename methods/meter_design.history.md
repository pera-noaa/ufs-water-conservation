> Verbatim earlier versions of [`meter_design.md`](meter_design.md), oldest first, headings untouched. Version 1: one probe
> scheme with namelist labels. Version 2: options O/A/B/C before the prototypes were built and measured.

> **Version 1**

# Budget meters as maintained UFS code: scope

What it would take to replace this project's research meters ([`METERS.md`](METERS.md)) with one budget meter
that the UFS code managers will merge and other developers will run. Draft for discussion; nothing here is posted.

## Summary

| | |
|---|---|
| **Proposal** | One CCPP scheme, `budget_probe`, placed between schemes in the suite file, plus `budget_end` last in `phys_ts`. The host owns the per-column accumulators, the global sums (reproducible across layouts) and one printed `BUDGET` line per window. Water and passive-tracer mass first, energy later, dycore last |
| **Default** | Off (`budget_meter = .false.`). Off costs one early return per probe per chunk; on, it changes no answers |
| **Not proposed** | The in-scheme forensic meters (Thompson stages, Noah-MP storage terms, write-back statements). They stay as scripted patches in this repository |
| **Decoupled from the fix packages** | The meter PR changes no answers, so it can land before packages 1–3. Only the regression check that uses it waits for the fixes |
| **Size** | PR 1 is about 300–400 lines across ccpp-physics, ufsatm and CCPPStandardNames. Today's energy meter alone is a 3,442-line diff |
| **First step** | A design issue on ccpp-physics, linked from ufs-community/ufs-weather-model#3404, asking the three questions under "Decisions for the maintainers" before any code |

## What "merged and used" requires

The reviewers are the CCPP physics and framework code managers, the ufsatm code managers and, for the dycore part,
GFDL. Their stated and evident constraints:

1. **No answer changes and no baseline changes.** Any baseline change needs a full RT on every platform, and the
   managers are already batching three of them for our fixes.
2. **CCPP conventions.**
   - Schemes take standard-name arguments only. No module state, no host-specific types, no FMS or MPI in a physics
     scheme beyond what is already there.
   - Every new variable gets a standard name in ESCOMP/CCPPStandardNames.
   - It must build under capgen-v1. ufsatm moved to capgen (#1145, October 2026; `ccpp/CMakeLists.txt` calls
     `ccpp_capgen`, and new schemes are registered in `SCHEME_FILES`). It must also build under `ccpp_prebuild`, which
     the SCM still uses, because ccpp-physics PRs reach the SCM too.
3. **Threads and decomposition.** The UFS runs physics chunks on OpenMP threads (`CCPP_driver.F90`,
   `schedule(dynamic,1)`: one thread runs `phys_ps` and then `phys_ts` on one chunk, and chunks are disjoint). Anything less than thread-safe and layout-independent will be found and rejected.
4. **Small, reviewable PRs, each with one definite answer.** Open design questions go in an issue first.
5. **A user and a test.** Code nobody runs rots. The users are:
   - scheme developers, who need a one-line answer to "does my change conserve?" (TTE-EDMF #403 and MLM #390 both
     reached review without conserving);
   - UFS-Chem, which needs GHG tracer mass to close;
   - the regression suite, which can stop a non-conserving change on its own PR.

## What the research meters taught

| Keep | Drop |
|---|---|
| Probes as separate CCPP schemes between schemes: they read state only, compile in their own files, and were bitwise passive in every gate | Edits inside physics routines. They change FMA contraction in release builds (`experiments/conservation/samfinit/report.md`), so meter on vs off differs at round-off |
| The "effective state" each probe reads, state + pending tendency × dt, as `em_probe` does. It closes energy to 10⁻¹² W/m² across process-split and time-split schemes | 12 copied probe schemes (`em_p01`–`em_p12`) that differ only in their index |
| Double-precision accumulation in the physics' own frame: Δp = `prsi(k) − prsi(k+1)`, fixed during the physics step | Module-level accumulators: wrong with 2 threads (`experiments/conservation/trdyn/report.md`) |
| Closure against the fluxes the physics reports (`evap`, `rain`) and against bracketed deliberate sources (`h2ophys`) | Fixed buffers (`emnc = 8192` columns per rank) with no bounds check |
| Known-bad fixtures: the meter must report the +0.26 % water source on unfixed develop | Per-rank text records summed by bespoke Python; `MPI_SUM` reductions whose last bits depend on the layout |
| Layout-independent column hashes (`SMH`) for locating a first difference | One record format and reader per campaign |

## Design

### 1. Physics: one probe scheme, placed many times

- **`budget_probe`** can appear any number of times in a physics group.
  - Both frameworks allow a repeated scheme. In capgen-v1, `suite_resolver.py` (`_dedup_scheme_names`) calls a
    repeated scheme's init and finalize once per group and its run once per occurrence; `mkstatic.py` in prebuild keeps
    duplicates.
  - No upstream suite repeats a scheme yet (the old `GFS_debug` schemes were removed in ccpp-physics#378), so this is
    the first use in practice. Say so in PR 0.
  - Each call adds one to a per-column counter, `budget_slot(i)`, and stores that column's integrals in slot
    `budget_slot(i)`.
  - A per-column counter is correct whatever the chunk order and thread count. Every column passes every probe once per
    step, and every scheme receives the whole chunk (partial work is masked inside the scheme).
- **Integrals per column, real(8), in the physics frame:**
  - water: six species, and vapour separately;
  - mass of each tracer in a namelist list (`budget_tracers`);
  - energy, in phase 4: enthalpy, latent and kinetic terms with the dycore-consistent heat capacities, taken from host
    constants rather than hard-coded.
- **`budget_end`** goes last in `phys_ts`, not in `stochastics`.
  - `atmos_model.F90` runs the `stochastics` group only when SPPT, SHUM, SKEB, land perturbations or the cellular
    automaton are on.
  - `GFS_stochastics` perturbs `gq0` and `tprcp`, and clips negatives, so it is an undeclared water source in its own
    right.
  - Phase 1 reports that the meter does not cover the stochastics group. A probe pair in that group could make it a
    segment of its own later.
  - `control_p8` sets `do_ca`, so a gate run there executes the group: it is the configuration to test against.

  `budget_end`:
  - forms each segment's change (slot n+1 minus slot n);
  - subtracts that segment's declared boundary flux;
  - adds the residual to per-column window accumulators;
  - resets the counter;
  - flags an error if the slot count differs from the number of labels.
- **Labels.** A namelist list, `budget_probe_labels`, names the segments in suite-file order (`pbl`, `deepcnv`, `mp`,
  …, reusing the `dtend` process names). A miscount is fatal at the first step, so a suite edit cannot silently shift
  them. Neither framework tells a scheme instance its position in the suite; capgen has only the model
  `instance_number`.
- **Placement rules:**
  - Probes only after a `*_post` or other interstitial, never between a core scheme and its `_post`.
    - Core schemes return `ten_*` tendencies, which the `_post` applies according to `tend_opt_*`.
    - The effective state is `gq0 + dtp·dqdt` under `tend_opt_*` 1–3 (the defaults: pbl 2, gwd 3, the rest 1).
    - At init, `budget_probe` refuses `tend_opt_* = 4`.
  - No probes inside a `subcycle loop > 1` (the surface iteration), because the counter would advance twice.
    capgen-v1's `ccpp_loop_counter` argument could lift this later.
  - Probes only in `phys_ps` and `phys_ts`: not in `radiation` (it does not run every step), `time_vary`,
    `stochastics` or `fast_physics`.

### 2. Declared boundary terms

A segment's residual is meaningful only against what that scheme is allowed to exchange. Phase 1 declares only
whole-physics terms, each from a variable the host already has:

| Quantity | Change over the physics step must equal |
|---|---|
| Column water | `dt·evap·Δp₁/(g·Δz₁)` − `1000·rain` (precipitation, m → kg/m²) + the bracketed `GFS_photochemistry` segment |
| Passive-tracer mass | 0, plus any bracketed source segment (emissions, chemistry). Wet deposition, once booked, is declared too |

Notes on the water row:
- **Evaporation is declared as the PBL applies it.** That is `dtdz1·evap` in `satmedmfvdifq` (`evap` in
  kg kg⁻¹ m s⁻¹, Δp₁ from `prsi`, Δz₁ from `phii`). The booked `dqsfc` uses `rho_a`, which is local to
  `satmedmfvdifq` and not a host variable. The applied and booked forms differ (FV1, ~4 × 10⁻⁸ of E); the
  land-side hand-off is a phase-3 segment.
- **`h2ophys` runs inside `GFS_photochemistry` together with ozone** (`h2o_phys = .true.` in the RT namelists).
  The probe pair brackets `GFS_photochemistry` and `GFS_photochemistry_post` together.
- **`rain`** (Diag, m) is final after `GFS_MP_generic_post`. **`evap`** (Sfcprop) persists across groups.

Per-scheme declarations (PBL ↔ evaporation, convection ↔ convective rain, microphysics ↔ grid-scale precipitation)
come in phase 3, one scheme family at a time, agreed with each scheme's owners. Declarations are the ongoing cost of
the design, so they go in one table in `budget_end`, beside the labels, not scattered through schemes.

### 3. Host side (ufsatm)

- **Namelist** (`gfs_physics_nml`):

  | Variable | Default |
  |---|---|
  | `budget_meter` | `.false.` |
  | `budget_probe_labels` | none |
  | `budget_tracers` | none |
  | `budget_window` | equals `fhzero` |
  | `budget_tol_water` | 0 = report only |
  | `budget_tol_tracer` | 0 = report only |

- **Storage.** Columns are contiguous upstream (`ncols`, chunks `chunk_begin:chunk_end`).
  - `budget_col(ncols, nquant, nslot)` and `budget_slot(ncols)` live in a new `GFS_budget_type`, or in `Diag`, sized
    from the labels: no caps.
  - Allocated only when the meter is on.
  - A new type must be added to `CCPP_data` and its capgen metadata.
- **Reduction.**
  - At each window end, `atmos_model.F90` sums the accumulators with FMS's extended-fixed-point reproducing sum, the
    route FV3's own `g_sum` takes: `mpp_reproducing_sum` (`mpp_efp`; `BITWISE_EFP_SUM`).
  - All quantity × segment sums go through one collective (`mpp_efp_list_sum_across_PEs`).
  - The sum takes any 2-D array, so there is no (i, j) mapping. It allows one tile per PE, as the global runs have.
  - Not `BITWISE_EXACT_SUM`: it gathers the whole global field onto every PE, once per quantity.
  - The totals are then bitwise identical across layouts and thread counts, so a check sized near round-off cannot
    flicker.
- **Output.** One line per window, quantity and segment, from the root PE:

  ```
  BUDGET <quantity> <window end, h> <segment label> <change> <declared> <residual> [<units>]
  ```

  - Optionally, accumulated residual maps registered in `GFS_diagnostics.F90` (`budget_res_water`, …), so `diag_table`
    can write where a budget fails.
- **Check.** If a tolerance is set and `|residual| > tol`, the host calls `mpp_error(FATAL)` naming the segment. That is
  the regression test's failure mode. Whether code managers accept a diagnostic stopping a run is not known. The
  fallback is a report-only meter plus an RT-side comparison of the `BUDGET` lines.

### 4. Dycore and coupling (GFDL_atmos_cubed_sphere, last)

- FV3 already prints global mass diagnostics at `print_freq` (`prt_mass` in `fv_diagnostics`).
- The dycore meter extends that idea: the same quantities around `fv_dynamics`, the physics → dynamics state update
  and `fv_update_phys`, emitting the same `BUDGET` record.
- It needs the GFDL maintainers and the `dev/emc` branch, so it is a separate proposal after the physics meter is in
  use.

## Gates (each must be shown to fail before it is trusted)

| Gate | Pass | Known-bad that must fail |
|---|---|---|
| G1 passive | Meter on vs off, release build (not `-no-fma`): every history and restart file bitwise | A probe that writes one state value |
| G2 detects | Unfixed develop: water residual ≈ +0.26 % of P, in the convection and microphysics segments; fixed tree: round-off | Fixed tree plus a one-line reversion of SA1 |
| G3 layout | 3×8 vs 4×6: identical `BUDGET` lines | Plain `MPI_SUM` reduction |
| G4 threads | 1 vs 2 OpenMP threads: identical `BUDGET` lines | Module-level accumulator |
| G5 restart | 24 h vs 12 + 12: identical second-window lines (windows are restart-local and aligned to restart times; no meter restart state) | — |
| G6 cost | Off: RT wall time within run-to-run noise. On: measured and reported | — |
| G7 precision | 32-bit dycore build (HAFS): tolerance about 3 × 10⁻⁷ kg/m² per step; 64-bit: about 10⁻¹² | — |

## Phasing

| PR | Content | Answers change? | Depends on |
|---|---|---|---|
| 0 | Design issue: the three decisions below | — | nothing |
| 1 | `budget_probe`, `budget_end`, host storage, reduction and `BUDGET` output; whole-physics water and tracer mass; probes at the start of `phys_ps`, around `GFS_photochemistry` and `GFS_photochemistry_post`, and at the end of `phys_ts` in the RT suites; standard names | no (G1) | PR 0 answers |
| 2 | RT test `control_p8_budget`: meter on, tolerances set, Intel + GNU; the PR text shows it failing on pre-fix develop | no (new test only) | PR 1; fix packages 1–3 merged |
| 3 | Per-segment probes and declarations for the p8 suites (PBL, SAMF, Thompson, Noah-MP hand-off), one scheme family per PR with its owners | no | PR 1 |
| 4 | Energy: integrals and declared terms (fixer, dissipative heating, radiation, precipitation enthalpy) | no | PR 3; agreement on the declared terms |
| 5 | FV3 dycore and coupling meter (GFDL) | no | PR 1 in use |
| 6 | Single-column budget tests in ccpp-physics CI (README §7 stage A) | no | the scheme's fix merged |

Each meter PR is a ccpp-physics + ufsatm + ufs-weather-model triple, the same shape as the fix packages, plus a
CCPPStandardNames PR.

## Decisions for the maintainers (PR 0)

1. **Probes in the production suite files**, off by default (one line per probe; the off cost is an early return), or
   separate `*_budget.xml` suites? Recommendation: the production files. Separate suites add build time and drift from
   their originals.
2. **Where the host data lives:** a new `GFS_budget_type`, or `Diag`? Recommendation: a new type. It is allocated
   only when on and keeps `Diag`'s restart and output logic untouched.
3. **Segment labels:** a namelist list checked against the probe count, or a new framework feature that tells a scheme
   instance its position in the suite (neither framework has one)? Recommendation: the namelist now; ask the CCPP
   framework developers whether capgen-v1 would take the feature.

## Why probes rather than `dtend`

The project README (§7) suggested building on `dtend`. The probe design takes `dtend`'s process names but not its
mechanism:
- **`dtend` books what each scheme reports, not what the state does.** Clips, fills and floors between booked
  processes never appear in it, and that is where most of the defects in this project were found.
- **Integrating it from history output is biased** by about 10⁻⁴ kg/m² per 6 h (`METERS.md`, pitfall 5).
- **Integrating it in-model at every update site** would touch every `*_generic_post` interstitial. That changes
  release-build code in each of those files: a baseline change and a review across many owners.
- **Probes measure the state** and touch no existing scheme.

## Risks

| Risk | Mitigation |
|---|---|
| Maintainers decline probes in production suites | `*_budget.xml` variants for the RT suites only |
| Declarations disputed by scheme owners | Phase 1 needs none; per-scheme declarations are proposed one family at a time, each with a measured closure |
| MPAS dycore (`CCPP_driver` runs MPAS physics in groups named `physics` and `microphysics`) | Physics schemes are dycore-agnostic; the MPAS suites need their own probe placement and host reduction, after PR 1 |
| The stochastics group goes unmetered | Stated in the `BUDGET` output when stochastic physics is on; a bracketed segment later |
| ccpp-physics PRs also reach the SCM, which still builds with prebuild | Build the SCM with the probes in PR 1's CI |
| 32-bit physics builds (`CCPP_32BIT`) | Accumulators are real(8) regardless of `kind_phys`; G7 sets the tolerance |
| The meter becomes one more thing nobody runs | PR 2 makes it a regression test, and the PR 1 documentation shows a scheme developer's one-line use |

---

> **Version 2** (replaced after the prototypes; results in [`meter_proto/results.md`](meter_proto/results.md))

# Budget meters as maintained UFS code: scope

What it would take to replace this project's research meters ([`METERS.md`](METERS.md)) with budget checks that
the UFS code managers will merge and other developers will run. Draft for discussion; nothing here is posted. The
first version (one probe scheme with namelist labels) is in [`meter_design.history.md`](meter_design.history.md).

## Summary

| | |
|---|---|
| **Recommendation** | Build in three layers, each usable on its own. (A) A host meter in ufsatm: whole-physics and non-physics budgets for every suite, with no ccpp-physics or suite changes. (B) Per-scheme checks in the pattern CAM-SIMA already runs under capgen (`check_energy_chng`). (C) Ask the CCPP framework developers for a generic per-call hook, which would let (B) drop its repeated suite lines |
| **First PR** | A, in ufsatm only, plus one answer-neutral output from `GFS_photochemistry_run`. Changes no answers. Estimated at 250–350 lines |
| **Default** | Off. Then on in the existing `control_p8` test once fix packages 1–3 merge. It writes to stdout only, so no output file and no baseline changes |
| **Not proposed** | The in-scheme forensic meters (Thompson stages, Noah-MP storage terms, write-back statements). They stay as scripted patches in this repository |
| **Verified** | Every claim that can be checked without implementing it, against upstream source and with a capgen-v1 test (section "Verification") |
| **First step** | Prototype A, B (SAMF) and C, check each against the research meters (section "Next step"), then a design issue on ufsatm and ccpp-physics, linked from ufs-community/ufs-weather-model#3404, asking the four questions under "Decisions for the maintainers" |

## What "merged and used" requires

1. **No answer changes and no baseline changes.** The code managers are already batching three baseline changes for
   our fixes.
2. **CCPP conventions.**
   - Schemes take standard-name arguments only. No module state, no host-specific types.
   - New variables get names in ESCOMP/CCPPStandardNames.
   - Builds under capgen-v1 (ufsatm, since #1145) and `ccpp_prebuild` (the SCM).
3. **Threads and decomposition.** One OpenMP thread runs `phys_ps` then `phys_ts` on one chunk (`CCPP_driver.F90`,
   `schedule(dynamic,1)`).
4. **Small PRs, each with one definite answer.** Open design questions go in an issue first.
5. **Ownership where the knowledge is.** A declaration of what a scheme may exchange belongs to that scheme's owners,
   not to the meter's author.
6. **A user and a test.**
   - Scheme developers (TTE-EDMF #403 and MLM #390 both reached review without conserving).
   - UFS-Chem (GHG tracer mass).
   - The regression suite.

## The options

| | O. Probe scheme (first version) | A. Host meter (ufsatm) | B. CAM-SIMA-style checks | C. capgen per-call hook |
|---|---|---|---|---|
| **How** | One `budget_probe` scheme repeated in the suite file; labels from a namelist; declarations in one table | Column integrals before and after `CCPP_step("physics")` and across the rest of the step, in `atmos_model.F90` | A check scheme repeated after each family; a family-owned `<family>_prepare_flux_for_budget` interstitial sets `scheme_name` and the declared fluxes | A capgen option, like the existing `--trace`, that emits a guarded host-hook call after every scheme run call, passing the scheme name |
| **Granularity** | segments you place | whole physics + everything else | per family | every scheme, automatically |
| **Repos** | ccpp-physics, ufsatm, standard names, WM | ufsatm (+ WM namelist) | ccpp-physics, ufsatm, standard names (shared with CAM-SIMA) | ccpp-framework, ufsatm |
| **Suite edits** | yes, every suite | none | yes, per family | none |
| **Labels** | namelist; drift undetectable when a probe moves | fixed (`physics`, `non_physics`) | a scheme-name variable set next to the scheme (`ccpp_scheme_name` in the dictionary; CAM-SIMA's `scheme_name` is not in it) | the scheme name, free |
| **Declarations** | central table, the meter author's | whole-physics only | per family, by its owners | still needed; B's interstitials or a table |
| **Who must agree** | CCPP physics + ufsatm | ufsatm | CCPP physics, scheme owners, ufsatm | CCPP framework developers |
| **Precedent** | none in UFS suites | ufsatm already books `non_physics` `dtend` as `qgrs − gq0` (`atmos_model.F90` ~L300) | `check_energy_chng`, `zm_prepare_flux_for_check_energy` in ESCOMP/atmospheric_physics (`suite_cam7.xml`) | capgen-v1 `--trace` (`capgen/generator/trace.py`) emits compile-time-gated code in every cap |
| **Main risk** | labels and declarations rot | cannot say which scheme | slow: one owner group at a time | framework in transition; SCM (prebuild) gets nothing |
| **Merge odds** | medium | high | medium–high (NCAR precedent) | uncertain |

**Not chosen: a column-integral twin of `dtend`.** `dtend` is written in 28 ccpp-physics files (177 references). It
records only what schemes book, so clips and floors between booked processes are invisible. It needs `ldiag3d` and
`qdiag3d` with their 3-D arrays, and its `conv_trans` terms are always zero. It stays as an attribution aid: a
segment's residual minus Σ `dtend`·Δp/g over that segment is exactly the water no scheme booked.

**O is superseded.** A covers its PR 1 without any scheme. B replaces its namelist labels and central declaration
table. Its sound parts carry over into B:
- the per-column slot counter;
- the placement rules: never between a core scheme and its `_post`, never inside `subcycle loop > 1`, only in
  `phys_ps`/`phys_ts`.

## A. Host meter (PR 1)

**Where:** a new module file, `ccpp/driver/GFS_budget.F90`, called from `fv3/atmos_model.F90` with one line before
and one after `CCPP_step("physics")`. A separate file keeps the new arithmetic out of `atmos_model.F90`'s code
generation. The host already has everything it needs: `Statein` (`qgrs`, `prsi`, `phii`), `Stateout` (`gq0`),
`Sfcprop%evap`, `Intdiag%rain`, `Grid%area`.

**Snapshots.** The meter keeps its own copies of the state at the start and at the end of the physics, rather than
reading `Statein`/`Stateout` later:
- **`qgrs` changes during the physics.** `rrfs_smoke_wrapper` and `rrfs_smoke_postpbl` overwrite `Statein%qgrs` for
  smoke and dust (7 HRRR/RRFS suites).
- **`gq0` changes after the physics.** The chemistry import (`GFS_Stateout%gq0(…,ntchs:ntche)`) and the FV3 state
  update (IAU increments, `fill_gfs`, the `nopbl` reset) write it in place.
- **So the existing `non_physics` `dtend` diagnostic is the wrong template.** It differences against the
  already-modified `gq0`.

**Segments, per column, real(8):**

| Segment | Change | Declared |
|---|---|---|
| `physics` | Σ over water species of (`gq0` − `qgrs`)·Δp/g with Δp from `Statein%prsi`. This is exactly the research WBP meter, and it reads the applied state, not state + pending tendency | E − P + photochemistry |
| `non_physics` | water at the start of step n+1 minus water at the end of the physics in step n | 0; IAU runs are marked not covered (the IAU dry-mass fixer rescales `q(1:nwat)` by `betad`, so the change is not just `tracer_inc`) |
| tracers | the same two segments for each tracer in `budget_tracers` | depends on the tracer's class (below) |

- **`non_physics` covers everything after the physics in one term**, with no GFDL change: stochastics, the state
  update, `*nopbl` tracers, the `cplchm` import, IAU, r4 storage in 32-bit builds, and the dycore.
- **Species come from `nwat` and the tracer indices**, not a fixed six. Zhao–Carr has 2 water species; NSSL with hail
  has more.
- **Evaporation.** What the host can use depends on the PBL scheme:

  | PBL scheme | Suites | Applied water flux available to the host? |
  |---|---|---|
  | satmedmfvdif, hedmf, moninshoc, YSU, shinhongvdif | few or unused | yes: `dqsfc` is the column sum of the applied tendency (`GFS_Intdiag%dqsfci`) |
  | satmedmfvdifq | 26 | no: applies `dtdz1·evap` (dt·evap·Δp₁/(gΔz₁)), books `dqsfc = rho_a·hvap·evap` |
  | MYNN | 26 | no: clips `qfx` to [−2 × 10⁻⁴, 5 × 10⁻⁴] kg m⁻² s⁻¹ and books the clipped flux; its solve is ρ·dz-weighted |

  - PR 1 declares `dqsfci/hvap` for every scheme.
  - For satmedmfvdifq, booked and applied differ by ~4 × 10⁻⁸ of E on develop and by round-off with FV1 (our
    measurement, `../proposals/water_closure_proposal.md`), far below the fatal threshold.
  - MYNN's difference is unmeasured. G2 measures it before any MYNN suite gets the fatal threshold.
  - Two small PRs, one each for satmedmfvdifq and MYNN, make `dqsfc` the applied flux, as the other schemes already
    do.
- **Precipitation.** `rain` (Diag, m) is `rainc + frain·rain1` over all phases, and is final after
  `GFS_MP_generic_post`. `frain = 1` because UFS runs `dt_dycore = dt_phys`; the meter checks this at init.
- **Photochemistry.** `h2ophys` runs inside `GFS_photochemistry`, which the host cannot bracket.
  - `GFS_photochemistry_run` computes `ten_q(:,:,ntqv)` and already takes `dp`. It can output Σ `ten_q`·dp/g·dtp
    without touching any existing statement.
  - `GFS_photochemistry_post` applies exactly `dtp·ten_q` under the default `tend_opt_photochem = 1`.
  - This output is the one ccpp-physics change in PR 1. The size of the source, ~1.2 × 10⁻⁷ kg/m² per 6 h, is our
    measurement.
- **Tracer classes**, declared per tracer (namelist or a field_table attribute):

  | Class | Declared |
  |---|---|
  | passive | 0 |
  | emitted | its emission flux |
  | scavenged | its booked deposition |
  | nopbl | reported, not checked |

  At init, the meter refuses a tracer with `fscav > 0` declared passive.

  No in-physics tracer sink is booked today, so "emitted" and "scavenged" are report-only until each one is:
  - **SAMF scavenging** keeps `wet_dep` local and outputs nothing. It is active when `cplchm` and `trans_trac` are
    on, and the RT default `fscav` is `"*:0.3"` for every chemistry tracer.
  - **MYNN `mix_chem`** applies dry deposition at k = 1 and clamps output to `max(1e-12, …)`, which is a small
    source. Neither amount is stored.
  - **The RRFS smoke wrapper** adds fire smoke inside the physics.
- **Coverage.** Each line says "not covered" for segments the configuration changes outside the declaration: SPPT,
  SHUM, SKEB and the cellular automaton in `stochastics` (which perturb `gq0` and `tprcp`), and `cplchm` coupling.

**Reduction and output.**
- Per window (default `fhzero`), the root PE prints one line per quantity and segment:

  ```
  BUDGET <quantity> <window end h> <segment> <change> <declared> <residual> <sum|r|> <max|r|> <hash of max|r| column> [not covered: …]
  ```

- `change`, `declared` and `residual` are area-weighted global means (kg/m² per window). The residual is the sum of
  signed column residuals; `sum|r|` is the sum of their absolute values, so compensating errors cannot hide.
- Sums use FMS's extended-fixed-point reproducing sum, with every quantity in one collective
  (`mpp_efp_list_sum_across_PEs`). FV3's `g_sum` takes the same route when called with `reproduce=.true.`, as the
  energy fixer does. The max uses `mpp_max`. The lines are therefore identical across layouts and thread counts.
  - EFP refuses more than one tile per PE (true of every UFS configuration).
  - It sums over the current pelist, which UFS sets per grid, so a nest's budget covers only that nest.
- The lines avoid the words `rt.sh` greps for in logs ("PASS", "NOT IDENTICAL", "TIME LIMIT", "quota").
- The column hash is layout-independent, as in the research suites meter (`SMH`). It locates the worst column without
  a second run.
- Storage: per-column arrays in a new host type (allocated only when on), registered in `CCPP_data` and its capgen
  metadata. No module state.

**Thresholds** (namelist):

| Threshold | Size | Effect |
|---|---|---|
| `budget_tol_report` | near round-off: ~10⁻¹² kg/m² per step (64-bit), ~3 × 10⁻⁷ (32-bit dycore) | flags the line |
| `budget_tol_fatal` | ~10⁻⁶ kg/m² per window | `mpp_error(FATAL)` naming the segment |

The fatal threshold keeps about three orders of margin below the defects fixed here (~10⁻³ kg/m² per 6 h). It is not
tripped by round-off, compiler changes or held TH8's sub-threshold remainder.

## B. Per-scheme checks (phase 3)

- **Follow CAM-SIMA.** A check scheme, `ufs_budget_check`, repeated in the suite file after each family. Before it,
  that family's `<family>_prepare_flux_for_budget` interstitial sets `scheme_name` and the family's declared boundary
  fluxes, the way `zm_prepare_flux_for_check_energy` does for CAM-SIMA's ZM convection.
- **Share one vocabulary with CAM-SIMA.** CAM-SIMA's own names `scheme_name` and
  `net_water_vapor_fluxes_through_top_and_bottom_of_atmosphere_column` are not in CCPPStandardNames (they are listed
  in its `doc/NamesNotInDictionary.txt`), and the dictionary has `ccpp_scheme_name`. So propose the budget names to
  CCPPStandardNames jointly with CAM-SIMA, not as UFS-only names.
- **Ported, not shared.** The scheme itself cannot be used verbatim:
  - it takes tracers as capgen `ccpp_constituents`, which `CCPP_driver` never registers (UFS passes `gq0`/`qgrs`);
  - it calls CAM-SIMA host modules (`cam_thermo`, `air_composition`);
  - about 6 of its roughly 40 standard names exist in the UFS host.
- **Metadata rules** (verified with capgen-v1):
  - dimensions on `horizontal_dimension`;
  - host arrays passed as optional need `TARGET`;
  - a per-column slot counter is safe with chunks on threads.
- **Effective state.** The check reads `gq0 + dtp·dqdt` only where the family's `_post` leaves tendencies pending.
  `budget_end` books any `dtp·dqdt` still pending at the end of the physics as a leak: a tendency the state update will
  never apply. Under a mismatched `tend_opt_*` chain that loss is otherwise silent.
- **Each family's owners own its interstitial**, so a new scheme author adds their declaration in their own PR. Start
  with the families the fixes already touched: SAMF, satmedmfvdifq, Thompson, Noah-MP's hand-off.

## C. Framework hook (ask in PR 0)

- **What it would do.** A capgen-v1 option that emits, after every scheme run call in a group cap, a call to a
  host-provided hook with the scheme name and a host-chosen list of standard-name variables. It would be gated at
  compile time like `trace`, and so cost nothing when off.
- **Pitch it generically**, not as a budget feature. The same hook serves per-scheme checksums, NaN checks and
  first-difference hunts (the research `SMH` meter).
- **If accepted**, B keeps its `*_prepare_flux_for_budget` declarations but drops the repeated check lines.
- **It does not reach the SCM** while the SCM builds with prebuild.

## Verification of this design (upstream source as of November 2026)

| Claim | Result | Evidence |
|---|---|---|
| A repeated scheme with optional, run-time-`active` arrays works under capgen-v1 | **verified by test**. Each occurrence gets its own pointer, local to the run routine; 1 and 4 OpenMP threads exact; off passes absent arrays; the known-bad case fails | [`meter_proto/capgen_repeat_probe/`](meter_proto/capgen_repeat_probe/README.md); framework @1959c303 |
| New scheme metadata | capgen-v1 rejects `horizontal_loop_extent` in dimensions (use `horizontal_dimension`); host arrays passed as optional need `TARGET` | same test |
| No IPO/LTO in UFS builds | **verified**. Neither appears in WM, ufsatm or FV3 CMake; `IntelMixed` adds `-no-ip`; generated caps are built at `-O0` | WM `cmake/*.cmake`, ufsatm `ccpp/CMakeLists.txt` |
| A separate file cannot change other files' results | **verified** for a new scheme or module file; new code inside `atmos_model.F90` could change that file's own code generation, hence `GFS_budget.F90` | Release: Intel `-O3 -fp-model precise -march=core-avx2`, FMA allowed except on WCOSS2/Acorn; GNU `-O2` |
| Extra stdout cannot fail an RT test or need a baseline | **verified**. Tests compare only `LIST_FILES`; stdout is grepped only for wall time and RSS | `tests/run_test.sh` ~L515–617 |
| A fatal conservation check has precedent | **verified**: Noah-MP's energy-balance abort is active in `control_p8` | `module_sf_noahmplsm.F90`, `atmos_model.F90:388` |
| Host variables, units, frames | **verified**: `rain` m per physics step; `evap` kg kg⁻¹ m s⁻¹; `area` m²; the state update converts with the same Δp the meter uses; nothing pending reaches the dycore under the default `tend_opt` chain | GFS_typedefs.meta; GFDL `atmosphere.F90` ~L1661 |
| `non_physics` computable in the host | **verified**, with own snapshots (above) | `atmos_model.F90` L277–419; `module_fcst_grid_comp.F90` L1479–1549 |
| Booked evaporation is the applied one | **partly**: yes for 5 PBL schemes; no for satmedmfvdifq and MYNN | table above |
| Passive tracers have no in-physics sink | **false** with `cplchm` (SAMF scavenging), MYNN `mix_chem` and RRFS smoke; true for `control_p8` (`cplchm` off) | tracer classes above |
| UFS can reuse `check_energy_chng` verbatim | **false**: constituents, CAM-SIMA host modules, missing names | section B |
| `scheme_name` is in CCPPStandardNames | **false** (the first draft said it was): the dictionary has `ccpp_scheme_name` | `standard_names.xml` |
| Not verifiable without implementing | MYNN's booked-vs-applied gap; EFP on regional and nest domains at run time; whether the meter call site runs under the per-grid pelist; the code managers' answers | — |

## Gates (each shown to fail before it is trusted)

| Gate | Pass | Known-bad that must fail |
|---|---|---|
| G1 passive | Meter on vs off, same release build: every history and restart file bitwise | a meter that writes one state value |
| G1b baselines | Post-PR build with the meter off vs current RT baselines: full RT, Intel + GNU, including a 2-thread test | — |
| G2 detects | Unfixed develop: `physics` water residual ≈ +0.26 % of P; fixed tree: below `budget_tol_report` | fixed tree + a one-line reversion of SA1 |
| G3 layout | 3×8 vs 4×6: identical `BUDGET` lines | a plain `MPI_SUM` reduction |
| G4 threads | 1 vs 2 OpenMP threads: identical lines | a module-level accumulator |
| G5 restart | 24 h vs 12 + 12: identical second-window lines. Windows follow the physics buckets (zeroed at `mod(kdt-1, nszero) == 0`, with `kdt` counted from the initial time), so a restart at a multiple of `fhzero` reproduces them. `fhzero` is not required to divide the restart time (only a warning), so the meter marks a partial first window. `control_p8`: `FHZERO=6`, restart at 12 h | — |
| G6 cost | Off: RT wall time within run-to-run noise; on: measured | — |
| G7 precision | `non_physics` in a 32-bit dycore build ~3 × 10⁻⁷ per step, 64-bit ~10⁻¹² | the 32-bit build must not pass the 64-bit report threshold |
| G8 coverage | `control_p8` (`do_ca`): lines say "stochastics not covered"; a deterministic run: they don't | — |

## Phasing

| PR | Content | Answers change? | Depends on |
|---|---|---|---|
| 0 | Design issue: the four decisions below | — | nothing |
| 1 | A: host meter, water + tracer mass, `physics` and `non_physics`; photochemistry column export | no (G1, G1b) | PR 0 |
| 2 | Turn the meter on in `control_p8` with both thresholds, Intel + GNU (stdout only: no new baseline). The PR text shows it failing on pre-fix develop | no | PR 1; fix packages 1–3 |
| 3 | B, one family per PR, with its owners; PBL families export their applied surface water flux | no | PR 1 |
| 4 | Energy, in CAM-SIMA's energy vocabulary (its total-energy formula names); declared terms for the fixer, dissipative heating, radiation and precipitation enthalpy | no | PR 3 |
| 5 | FV3 dycore and coupling, split out of `non_physics` (GFDL) | no | PR 1 in use |
| 6 | Single-column budget tests in ccpp-physics CI (README §7 stage A) | no | the scheme's fix merged |
| — | C, if the framework developers take it | no | their answer in PR 0 |

## Next step: prototype and compare

The options differ in where the code lives and who maintains it, not in what they measure. On the same tree, every
correct implementation must give the same residuals. So the useful experiment is not a contest between them; it is
a correctness check of each prototype against the research meters, which have known answers.

| Prototype | Where | Reference it must reproduce |
|---|---|---|
| A, host meter | `GFS_budget.F90` on develop and on the full-fix tree, C96 `control_p8` 24 h | `physics`: the research WBP meter, to round-off (same formula, same frame). Physics residual against WBQ. `non_physics`: the dycore meters, 0 to 10⁻¹² (64-bit) |
| B, one family (SAMF) | a `samf_prepare_flux_for_budget` interstitial + check scheme, same runs | SAMF's segment equals the research convection meters; known-bad: revert SA1 |
| C, capgen hook | the framework patched locally to emit the hook after every call; the toy test, then the same UFS build | per-scheme residuals equal B's for SAMF; every other scheme's residual listed with no suite edits |

Exploring further options has low value: host, scheme, framework and diagnostics are the four places such a meter can
live, and all four are on the table. What remains uncertain is the code managers' answers, and working prototypes
with these comparisons are the strongest material for PR 0.

## Decisions for the maintainers (PR 0)

1. **Host meter location:** `atmos_model.F90` around `CCPP_step("physics")`, or `CCPP_driver.F90` between the
   `phys_ps` and `phys_ts` calls (one more segment, the same cost)? Recommendation: `atmos_model.F90` first. It also
   holds the step-to-step state that `non_physics` needs.
2. **Per-scheme checks:** adopt CAM-SIMA's pattern (a repeated check scheme plus family-owned
   `*_prepare_flux_for_budget` interstitials) in UFS suites? Recommendation: yes, with shared standard names.
3. **Framework:** would capgen-v1 take a generic, compile-time-gated per-call host hook?
4. **A fatal check in `control_p8`:** acceptable at ~10⁻⁶ kg/m² per window? There is precedent:
   - Noah-MP already stops `control_p8` on an energy-budget error. It sets `errflg = 1` when `|erreng| > 0.01` or
     `|errsw| > 0.01` (`module_sf_noahmplsm.F90` ~L1559, L1639), which `atmos_model.F90:388` turns into
     `mpp_error(FATAL)`.
   - FV3's `range_warn` only prints.

   The fallback is report-only plus an RT-side comparison of the `BUDGET` lines.

## Risks

| Risk | Mitigation |
|---|---|
| A says "physics leaks" but not where | B for attribution; meanwhile `dtend` (residual − Σ booked) and the research meters in this repository |
| PBL schemes other than satmedmfvdifq apply evaporation differently | measured under G2 for each PBL in the RT suites; fatal threshold sized above it; applied-flux exports under B |
| MPAS (`CCPP_driver` runs MPAS physics in groups `physics` and `microphysics`) | A is FV3-host code; an MPAS host meter follows the same pattern later |
| HRRR/RRFS suites change `qgrs` inside the physics (smoke, dust) | the meter's own start-of-physics snapshot |
| MYNN's booked evaporation is clipped and ρ·dz-weighted | report-only for MYNN suites until G2 measures it or MYNN exports the applied flux |
| The meter becomes one more thing nobody runs | PR 2 makes it part of `control_p8`; the PR 1 documentation shows a scheme developer's one-line use |
