# Budget meters as maintained UFS code: design

What it takes to replace this project's research meters ([`METERS.md`](METERS.md)) with budget checks the UFS
code managers will merge and other developers will run. Draft; nothing here is posted. Earlier versions (one probe
scheme; options O/A/B/C before the prototypes) are in [`meter_design.history.md`](meter_design.history.md).

## Status

| | |
|---|---|
| **Recommendation** | Three layers on one declaration mechanism. (1) A whole-physics meter in `CCPP_driver.F90` (A2). (2) A cumulative, standard-named *declared-change* total that the code applying a tendency adds its boundary flux to. (3) Attribution by a chain of checkpoints at the tendency-applying interstitials, first as explicit suite lines; the same probe offered to the CCPP framework as a generated insertion (`--instrument`) |
| **Evidence** | Prototypes A, B, C built into one `control_p8` executable ([`meter_proto/results.md`](meter_proto/results.md)): answer-neutral (0 of 3402 variables), `BUDGET` lines identical across 1/2 threads and 3×8/3×4 layouts, A − offline history budget 3e-8, B = C = A to 1e-16. Detects SAMF (+0.78 % of P_conv, unfixed) and Thompson (−0.6 % of P_ls; −1.29e-7 kg/m² per window with TH1–TH7) |
| **Why this design** | Three independent reviews, one per prototype, converged on it ([`meter_proto/redesign_synthesis.md`](meter_proto/redesign_synthesis.md)) |
| **First PR** | Layer 1 in ufsatm plus the counter's first writer (photochemistry, using its existing `dp`). No answer change, no suite or framework edit |
| **Open** | The code managers' answers (section "Decisions"); booked vs applied E in MYNN suites; meter cost (one timing sample per arm resolved nothing); restart and `fhzero_array` windows; neutrality on GNU and with FMA |
| **Next** | Build layers 1–3 as specified, rerun the fix / dev / Thompson-fixed arms and the open gates, then the PR 0 design issue |

## What "merged and used" requires

1. **No answer or baseline changes.** The code managers are already batching three baseline changes for our fixes.
2. **CCPP conventions.** Standard-name arguments only, no module state in schemes, new names in ESCOMP/CCPPStandardNames,
   builds under capgen-v1 (ufsatm since #1145) and `ccpp_prebuild` (the SCM).
3. **Threads and decomposition.** One OpenMP thread runs `phys_ps` then `phys_ts` on one chunk (`CCPP_driver.F90`,
   `schedule(dynamic,1)`).
4. **Small PRs, each with one definite answer.** Open design questions go in an issue first.
5. **Knowledge where the owners are.** What a process exchanges with the outside is declared by the code that applies
   it, not by the meter's author.
6. **A user and a test.** Scheme developers (TTE-EDMF #403 and MLM #390 both reached review without conserving),
   UFS-Chem (GHG tracer mass), the regression suite.

## Design

### Layer 1: whole-physics meter (A2)

All calls in `ccpp/CCPP_driver.F90`, shared by the FV3 and MPAS hosts; `atmos_model.F90` is not edited.

| Where | Call | Effect |
|---|---|---|
| after `ccpp_physics_init` | `budget_init` | read switches, allocate only when on, area sum, print configuration and coverage |
| next to `GFS_Intdiag%phys_zero` | `budget_window_end` | close the window where the physics buckets are zeroed; snapshot W(`qgrs`); close `non_physics`; reduce, print, check |
| chunk loop, before `phys_ps` / after `phys_ts` (MPAS: around `physics` and `microphysics`) | `budget_begin` / `budget_end(SEG_PHYS)` | the physics segment per chunk, inside the threaded loop |
| chunk loop, `stochastics` | `budget_begin` / `budget_end(SEG_STOCH)` | SPPT, SHUM and the cellular automaton measured instead of lumped into `non_physics` |
| `physics_final` | `budget_final` | report a partial last window, flagged |

- **Segments:** `physics`, `stochastics`, `non_physics` (dycore, state update, IAU, `cplchm` import, r4 storage).
- **Windows equal the history buckets by construction**, because they close at the statement that zeroes them,
  including the IAU-centre case. The prototype's `mod(kdt, nszero)` with `nszero` copied at init is right only while
  the bucket rule stays that simple. The window-end and next physics-begin snapshots read the same `qgrs`, so their
  difference must be 0: a free check that nothing writes the state in between.
- **Own snapshots.** `rrfs_smoke_wrapper`/`rrfs_smoke_postpbl` overwrite `qgrs` inside the physics (7 HRRR/RRFS
  suites); the chemistry import, IAU, `fill_gfs` and the `nopbl` reset write `gq0` after it. The existing
  `non_physics` `dtend` (`qgrs − gq0` in `atmos_model.F90`) differences against already-modified state.
- **Integrand:** Σ over species of the effective state `gq0 + dtp·dqdt` times Δp/g, real(8), species from `nwat` and
  the tracer indices (Zhao–Carr 2, NSSL with hail 7). One copy of the integral, in ccpp-physics, used by host and
  probes.
- **Boundary terms the meter reads itself:** E = `dqsfci/hvap·dtp`, P = `rain` (m per step, `rainc + frain·rain1`,
  final after `GFS_MP_generic_post`). Everything else comes from the counter (layer 2).
- **Reduction:** per-column arrays in a host type allocated only when on; (ncols, 1) packing; one
  `mpp_efp_list_sum_across_PEs` per window, so lines are identical across layouts and threads (measured). EFP needs
  one tile per PE (true of every UFS configuration) and sums over the current pelist, so a nest's budget is its own.
- **Output:** `BUDGET v1 <quantity> <window end h> <segment> <change> <declared> <residual> <sum|r|> <max|r|> <hash>
  [flags]`, avoiding the words `rt.sh` greps for. `sum|r|` is the sum of absolute column residuals, so compensating
  errors cannot hide; the hash is layout-independent. Bucket-accumulated residual maps through `diag_table`, written
  only when requested.
- **Thresholds** (kg/m² per window, namelist, per segment): physics report 1e-10, fatal 1e-5 (Thompson-fixed remainder
  1.29e-7, smallest defect 1.6e-3); `non_physics` and `stochastics` report-only in 32-bit builds (measured 1e-7 to
  9e-7). Fatal through `errflg` → `CCPP_step` → `mpp_error(FATAL)`, the path Noah-MP's energy abort already uses.
  `dtf /= dtp` flags the line instead of stopping the run.

### Layer 2: the declared-change total

One cumulative variable per quantity per column, zeroed at `budget_begin`, allocated only when on:

```
[budget_decl_water]
  standard_name = cumulative_declared_change_of_column_water_in_physics   ! provisional; propose jointly with CAM-SIMA
  units = kg m-2
  dimensions = (horizontal_dimension)
  type = real | kind = kind_phys | active = (flag_for_budget_meter)
```

- The code that applies a tendency adds its boundary flux, in an `optional`, `intent(inout)` argument, as a trailing
  loop after every existing statement. Because the total is cumulative, any segment's declared term is a difference
  of two readings, like the state.
- First writer: `GFS_photochemistry` (h2ophys, ~1.24e-7 kg/m² per 6 h), using the `dp` it already takes. E and P move
  from layer 1 into their owners (`GFS_PBL_generic_post` / `mynnedmf_wrapper`, the convection and microphysics posts)
  with layer 3.
- Tracers: `budget_decl_tracer(i, ntrac)`. Classes `passive` (declared 0; `fscav > 0` refused at init), `emitted`,
  `scavenged`, `nopbl` (reported, not checked). No in-physics tracer sink is booked today (SAMF `wet_dep` stays local;
  MYNN `mix_chem` deposits at k = 1 and clamps at 1e-12; RRFS smoke emits inside the physics), so those classes are
  report-only until each owner writes the total.
- Water held outside the tracer state (SAMF's condensate in `clw` between `GFS_suite_interstitial_3` and `_4`) is a
  second, optional export when per-call rows inside convection are wanted.

### Layer 3: attribution by a checkpoint chain

A checkpoint closes the segment since the previous checkpoint: change of the integrand, declared-change difference,
residual. The host seeds the chain from layer 1's start snapshot and books the rest as a `tail`, so segments telescope:
**Σ segments + tail = layer 1's physics change**, a closure that only a meter bug can break.

| Site (checkpoint after) | Segment it closes | Suites (of 56) |
|---|---|---|
| `GFS_PBL_generic_post` / `mynnedmf_wrapper` (post) | start → PBL | 28 / 26 |
| `GFS_photochemistry_post` | PBL → photochemistry (incl. GWD) | 53 |
| `GFS_suite_interstitial_4` | photochemistry → convection (the whole 3 → 4 span, every convection scheme) | 50 |
| `GFS_MP_generic_post` | convection → microphysics | 55 |
| host, after the physics | `tail` (pending `dtp·dqdt` never applied is a leak) | all |

- Sites are named constants; the segment index is the site. No run-time slot counter, no label registry, no critical
  section.
- **First form: explicit suite lines** (one per site) in the RT-tested suites. No edit inside shared interstitials, no
  framework dependency. A suite lint rejects a checkpoint between `GFS_suite_interstitial_3` and `_4`, between a scheme
  and its `_post`, or inside `subcycle loop > 1`.
- A site with a change and no declaration prints an `UNDECLARED` row: the check a new scheme's developer runs.
- Since ccpp-physics#299 schemes return tendencies and the `_post` interstitials apply them, so attribution below
  these families needs scheme-level exports, not more checkpoints (measured: every core scheme's slot read 0).

### Layer 4: generated insertion (framework, optional)

`capgen --instrument SCHEME:GROUPS` inserts an ordinary CCPP scheme after every run call of the named groups, its
arguments resolved from metadata, with a static call-site index and `ccpp_scheme_name`. Not generated by default (caps
byte-identical); capgen refuses an instrument that writes anything a physics scheme reads. Pitched for NCAR/ccpp-framework
#783 and #770 (debugging for capgen-v1; nothing replaced the retired `GFS_debug` checksum scheme), with a checksum probe
as its first client. If declined, layer 3's explicit lines remain. Detail: [`meter_proto/redesign_C.md`](meter_proto/redesign_C.md).

### Not chosen

| Option | Why not |
|---|---|
| Column-integral twin of `dtend` | records only what schemes book (clips and floors between booked processes are invisible); needs `ldiag3d`/`qdiag3d`; `conv_trans` terms always zero. Kept as an aid: segment residual − Σ `dtend`·Δp/g is the unbooked water |
| O: one probe scheme, namelist labels, central declaration table | labels and declarations rot (version 1) |
| B as prototyped: save/prepare/check triple per family, Diag accumulators | names grow as 4 × segments × quantities; segments do not tile; the declaration was the meter author's (`rainc` is written by the generic convection posts, not SAMF); not switchable |
| C as prototyped: untyped host hook after every call | host reaches into `GFS_Interstitial`; family table in the host with silent fall-through; slot counting; called even when off |
| Reusing CAM-SIMA's `check_energy_chng` verbatim | takes capgen `ccpp_constituents` (UFS registers none), calls CAM-SIMA host modules, ~6 of ~40 names exist in the UFS host. Share the vocabulary instead |

## Verification

| Claim | Result | Evidence |
|---|---|---|
| Meter on/off changes no answers | **measured**: 0 of 3402 variable-tiles, 1 and 2 threads | [`results.md`](meter_proto/results.md) |
| Layout- and thread-invariant lines | **measured**: 0 lines differ, 3×8×1 vs 3×4×2 | same |
| Host bracket loses nothing | **measured**: per-call sum − whole physics ~1e-17 | same |
| Independent closure | **measured**: whole budget − offline history budget 3e-8 (fix), 2e-8 (Thompson-fixed) | same |
| Detects the known defects | **measured**: SAMF +3.4e-3 (unfixed) vs 1e-15 (fixed); Thompson −1.6e-3 vs −1.29e-7 (TH1–TH7) | same |
| Repeated scheme with optional `active` arrays under capgen-v1 | **verified by test**, 1 and 4 threads exact; known-bad fails | [`meter_proto/capgen_repeat_probe/`](meter_proto/capgen_repeat_probe/README.md) |
| No IPO/LTO; caps at `-O0` | **verified** in WM, ufsatm, FV3 CMake | `ccpp/CMakeLists.txt`, `cmake/*.cmake` |
| Extra stdout cannot fail an RT test | **verified**: tests compare only `LIST_FILES` | `tests/run_test.sh` |
| A fatal conservation check has precedent | **verified**: Noah-MP's energy abort is active in `control_p8` | `module_sf_noahmplsm.F90`, `atmos_model.F90:388` |
| Booked E is the applied one | **partly**: yes for 5 PBL schemes; satmedmfvdifq differs by ~4e-8 of E; MYNN clips and is unmeasured | `../proposals/water_closure_proposal.md` |
| `scheme_name` is a standard name | **false**: the dictionary has `ccpp_scheme_name` | `standard_names.xml` |
| Not verifiable without implementing | MYNN's gap; EFP on regional and nest domains; the code managers' answers | — |

## Gates (each shown to fail before it is trusted)

| Gate | Pass | Known-bad that must fail | State |
|---|---|---|---|
| G1 passive | on vs off, every history file bitwise | a meter that writes one state value | **passed** (prototype) |
| G1b baselines | post-PR build, meter off, vs RT baselines: full RT, Intel + GNU, FMA on and off, a 2-thread test | — | open |
| G2 detects | per segment: unfixed vs fixed tree | fixed tree + SA1 reverted; drop one declaration | **passed** for SAMF and Thompson |
| G3/G4 layout, threads | identical lines | plain `MPI_SUM`; a module-level accumulator | **passed** combined (3×8×1 vs 3×4×2); known-bads not run |
| G5 restart | 24 h vs 12 + 12: identical second-window lines; partial first window flagged | — | open |
| G6 cost | off within noise, on measured, ≥ 3 samples per arm | — | open (one sample: noise ≥ 10 %) |
| G7 precision | `non_physics` 32-bit vs 64-bit | 32-bit must fail the 64-bit threshold | 32-bit measured (1e-7 to 9e-7 per window) |
| G8 coverage | `stochastics` nonzero with `do_ca`, exactly 0 deterministic | — | open |
| G9 chain closure | Σ segments + tail − physics ≤ 1e-15 | skip one checkpoint update | open (prototype C analogue ~1e-17) |

## Phasing

| PR | Content | Answers change? | Depends on |
|---|---|---|---|
| 0 | Design issue: the decisions below, with the prototype numbers | — | nothing |
| 1 | Layer 1 + the counter + photochemistry as first writer; water and tracer mass | no (G1, G1b) | PR 0 |
| 2 | Meter on in `control_p8`, report-only; fatal once the Thompson series merges; PR text shows unfixed vs fixed | no | PR 1; fix packages |
| 3 | Layer 3 checkpoints in the RT suites; E and P declarations move to their owners; PBL schemes export the applied flux | no | PR 1 |
| 4 | Energy, in CAM-SIMA's total-energy vocabulary | no | PR 3 |
| 5 | FV3 dycore and coupling split out of `non_physics` (GFDL) | no | PR 1 in use |
| 6 | Single-column budget tests in ccpp-physics CI (README §7 stage A) | no | the scheme's fix merged |
| — | Layer 4, if the framework developers take it | no | their answer |

## Decisions for the maintainers (PR 0)

1. **Meter calls in `CCPP_driver.F90`**, around each chunk's physics and at the bucket-zeroing statement (which is marked
   for removal once the framework handles diagnostics; the call moves with it)?
2. **A declared-change total** written by the code that applies a tendency, as an optional argument, with standard names
   proposed jointly with CAM-SIMA?
3. **Checkpoint lines in the RT suites**, or inside the shared interstitials themselves?
4. **Framework:** would capgen-v1 take a typed, metadata-resolved instrument insertion (#783/#770)?
5. **A fatal check in `control_p8`** at 1e-5 kg/m² per window after the Thompson series merges? Precedent: Noah-MP sets
   `errflg = 1` when `|erreng| > 0.01` or `|errsw| > 0.01`, which `atmos_model.F90:388` turns into `mpp_error(FATAL)`.
   Fallback: report-only plus an RT-side comparison of the `BUDGET` lines.

## Risks

| Risk | What retires it |
|---|---|
| E as booked ≠ E applied in the 26 MYNN suites (clipped, ρ·dz-weighted) | G2 on `hrrr_control`; MYNN report-only until measured; the scheme exports the applied flux |
| The counter write changes answers through code generation (FMA) | G1b on Intel and GNU, FMA on and off; trailing loop; fallback a separate declaration scheme |
| Maintainers reject calls in interstitials, the new names, or the framework feature | each layer stands alone; explicit suite lines need neither interstitial edits nor the framework |
| The integrand is wrong under another `tend_opt` chain or host | per-column `tail` and chain closure every window; report-only across suites before any threshold |
| A whole-physics number nobody acts on | residual maps in PR 1; checkpoints for attribution; `UNDECLARED` rows for new schemes |
