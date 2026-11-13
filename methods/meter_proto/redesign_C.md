# Option C redesigned: capgen inserts an instrument *scheme*, not a host hook

Review of prototype C (`ufs/GFS_budget.F90` `budget_post_call_hook`, `ufs/apply_meterproto.py` capgen edits) and a
replacement design. Measured numbers are from [`results.md`](results.md); design context in
[`../meter_design.md`](../meter_design.md).

## Summary

| | |
|---|---|
| **Proposal** | capgen option `--instrument SCHEME:GROUPS` inserts a call to an ordinary CCPP scheme after every run call in the named groups, resolving its arguments from metadata like any other scheme, and passing three framework variables: `ccpp_call_site_index`, `ccpp_scheme_name`, `ccpp_loop_counter` |
| **Main departure** | The hook stops being an untyped host subroutine that reaches into `GFS_Stateout`/`GFS_Interstitial(thread)` and becomes a scheme with standard-name arguments. The framework change is generic and host-agnostic; all budget knowledge leaves the host |
| **Declarations** | Owned by the family: the scheme where a family's change lands (its `_post`) adds to a running declared total and exports water it holds outside the state. No host family table, no suite edits |
| **Pitch to the framework** | As the answer to NCAR/ccpp-framework #783 / #770 (capgen-v1 has no replacement for the retired `GFS_debug` checksum scheme, retired because it was "hardcoded to the GFS DDTs"). First client: a checksum instrument; second: the budget instrument |
| **Fallback if the framework declines** | The same instrument scheme listed by hand in the suite file: B's pattern, identical code and metadata |
| **Default** | Not generated: caps byte-identical to today. Generated in the existing DEBUG compiles (`atm_debug_dyn32`, 17 suites; run by `control_debug_p8`), report-only |

## 1. Prototype C as built

| | Finding | Evidence |
|---|---|---|
| Right | Zero suite edits; every run call metered (27 sites `phys_ps`, 17 `phys_ts`) | generated caps on Hercules |
| Right | Closes: Σ sites − A dW ~1e-17 (fix), ~1e-16 (dev); C SAMF family = B to ~1e-16 | results.md |
| Right | Answer-neutral (0 of 3402 differ) and thread-reproducible (BUDGET lines 1 vs 2 threads identical) | results.md G1 table |
| Cannot | **Scheme attribution.** Since ccpp-physics#299 schemes return tendencies; every core scheme's slot reads 0 and all change lands in the `_post` interstitials. C delivers family attribution, which B already gives | results.md Findings |
| Cannot | **Spans.** SAMF holds condensate in `clw` between `GFS_suite_interstitial_3` and `_4`; per-call rows inside the span are meaningless alone. The report fakes the span with a call-order state machine (`f` stays 3 until `_4`) | `report` in GFS_budget.F90 |
| Fragile | **Slots by counting.** `slot(lb:ub)+1` per call; `s = slot(lb)` assumes every column of a chunk saw the same calls; names set first-writer-wins under `!$omp critical`; `nslot_max = 160`. Surface-loop schemes take two slots. Any run-time-conditional call (none today) would misalign every later slot silently | `budget_post_call_hook` |
| Fragile | **Host owns families.** A `select case` on scheme-name strings (`satmedmfvdifq`, `mp_thompson`, …) for one suite; a MYNN or GFDL-MP suite falls into `rest` with no error; a typo is silent | `report` |
| Fragile | **Untyped interface, host coupling.** Fixed signature `(suite, group, scheme, lb, ub, thread, errmsg, errflg)`: the hook must `use CCPP_data` and index `GFS_Interstitial(thread_num)%dqdt` itself. That is the DDT coupling for which `GFS_debug` was retired (#770), and every generated cap now `use`s a host module | capgen edit; cap line 309 |
| Waste | Hook emitted in every group, `radiation` included (8 calls), filtered by string compare at run time; the meter's own B schemes are metered too | cap grep |
| Not gated | Not compile-time gated as the design promised: CMake always passes `--post-call-hook`, so a "meters off" build still makes 44 calls per chunk per step with three string arguments. Wall time (one sample each: plain 154 s, off 169 s, on 167 s) does not resolve the cost | `apply_meterproto.py`; results.md |
| Framework | Asks the framework team to accept a budget-specific, UFS-shaped feature mid-unification; the SCM (prebuild) gets nothing until it moves to capgen-v1 | meter_design.md §C |

## 2. Design

### 2.1 What the generator emits

`capgen --instrument ufs_budget_probe:phys_ps,phys_ts` (CMake `CCPP_INSTRUMENT`, WM `-DCCPP_INSTRUMENT=...`). For each
named group capgen numbers the run calls statically (site 0 = group entry, then 1…N in suite order, unique per suite)
and emits, after each call and at group entry:

```fortran
    do ccpp_loop_counter = 1, 2
      call sfc_diff_run(...)
      if (errflg /= 0) return
      call ufs_budget_probe_run(site=17, iter=ccpp_loop_counter, scheme='sfc_diff',            &
           gq0=GFS_Stateout%gq0(lb:ub,:,:), dqdt=GFS_Interstitial(mythread)%dqdt(lb:ub,:,:),     &
           prsi=GFS_Statein%prsi(lb:ub,:), held=held_p%ptr, dcum=dcum_p%ptr,                     &
           acc=GFS_Budget%site_dw(lb:ub,:), on=GFS_Control%budget_meter, errmsg=errmsg, errflg=errflg)
      if (errflg /= 0) return
```

The argument list is not written by anyone: capgen resolves it from `ufs_budget_probe.meta` exactly as for a suite
scheme (slicing, threads, optional/`active` pointers, all proven in `capgen_repeat_probe/`). The init phase receives
`ccpp_call_site_names(nsites)`, a generated `character, parameter` table, so the report names sites with no run-time
string handling and allocates exactly `nsites` slots.

Generator rules (each a capgen error, so violations never reach a build):
1. The instrument may write only variables that no non-instrument scheme in the suite references (capgen has the
   whole suite's variable usage). Everything else it takes is forced `intent(in)`. This makes "reads state only" a
   generation-time property rather than a code-review promise.
2. A requested variable missing in a listed group is an error naming the group (replaces run-time `group /=` filters).
3. The instrument is never instrumented, and never inserted between a subcycle's iterations other than after each call.

### 2.2 Keying

Slot = `(site, quantity)`; iterations of a subcycle accumulate into the same site (optionally `(site, iter)` for
loop diagnostics). No counter, no critical section, no `nslot_max`, no assumption that a chunk's columns share a
history. Storage `site_dw(ncols, nsites, nquant)` lives in a host DDT allocated only when on (C96, 24 PEs: ~2300
columns × 45 sites × 8 B ≈ 0.8 MB per quantity per PE).

### 2.3 What the probe computes

Per column, the effective conserved amount `W = Σ_species (gq0 + dtp·dqdt)·Δp/g + held`, real(8), species from
`nwat` and tracer indices (as A). Per site: `ΔW = W − W_prev`, `D = dcum − dcum_prev` (declared), residual
`ΔW − D`, all accumulated per window. `W_prev`/`dcum_prev` are the probe's own storage. Site 0 of `phys_ps` opens
the step; site 0 of `phys_ts` checks that nothing changed between groups. At the last site the pending
`dtp·dqdt` the state update will not apply is booked as a leak (B's `budget_end` rule).

### 2.4 Declarations: by the family, where the change lands

Two new standard names, proposed to CCPPStandardNames jointly with CAM-SIMA (whose
`net_water_vapor_fluxes_through_top_and_bottom_of_atmosphere_column` and `scheme_name` are listed as not in the
dictionary; provisional names here):

| Variable | Written by | Meaning |
|---|---|---|
| `cumulative_declared_column_water_change_in_physics` (kg m⁻², running) | the scheme at whose site the family's change appears, `+=` its declared boundary flux × dtp | GFS_PBL_generic_post: +E applied; GFS_photochemistry_post: +H; GFS_MP_generic_post: −P_ls; SAMF closer: −P_conv |
| `column_water_held_outside_tracer_state` (kg m⁻², level) | a family that moves water out of `gq0`/`dqdt` into an interstitial, and back | SAMF: `clw` between `GFS_suite_interstitial_3` and `_4`; later Noah-MP's hand-off |

- Both are optional, `active`-gated outputs that no physics reads: answer-neutral by construction and by G1.
- A running total, not a per-call value, so the probe never has to zero it (rule 1 holds) and a stale value cannot
  be re-read at the next site.
- **Undeclared-change detector:** a site with `|ΔW| > tol` and `D = 0` is printed as `UNDECLARED`. This is the
  use case for scheme developers (TTE-EDMF #403, MLM #390): a new scheme that changes water without declaring shows
  up at its own site with no meter-side edit.
- "Family" is no longer a host concept: a family is the set of sites between declarations; the host's `select case`
  and the `interstitial_3…_4` state machine are deleted.

### 2.5 Switching and answer neutrality

| Build | Generated code | Run-time | Neutrality argument |
|---|---|---|---|
| default | none: caps byte-identical to upstream | — | diff of generated caps |
| `CCPP_INSTRUMENT` set | one call per site per chunk | `budget_meter` (namelist) → probe returns at once | rule 1 + G1 bitwise on/off |

### 2.6 Generality

- **Other suites/hosts:** nothing suite-specific in the framework or host; MYNN, GFDL-MP and RRFS suites get sites
  automatically and need only their families' declarations. SCM: as soon as it builds with capgen-v1 (the
  unification target); an SCM case is a cheap per-site test bed. CAM-SIMA: the same insertion would replace its
  repeated `check_energy_chng` lines, with `ccpp_scheme_name` supplied by the framework (unverified; ask them in PR 0).
- **Tracers:** `nquant = 1 + n(budget_tracers)`; per-tracer declared totals for emission/deposition as they get
  booked (meter_design.md tracer classes).
- **Energy:** a second quantity in CAM-SIMA's total-energy vocabulary; same keying, same declaration mechanism.
- **Other instruments:** checksum/NaN/first-difference (`SMH`) probes use the identical insertion; that is the
  framework's own motive.

### 2.7 Output

Per window, root PE, A's line format and EFP reproducing sums: one `BUDGET water <h> site:<group>:<scheme> ΔW D
residual sum|r| max|r| hash` row for each site with nonzero ΔW or D; one `UNDECLARED` row per offending site; one
`sites_vs_physics` row (Σ sites − A's `physics` change, globally and as max over columns: a per-column self-check
every window). Optional 2-D history field of the worst site's residual later.

### 2.8 Regression tests and cost

- **RT:** instrument the existing DEBUG compiles; `control_debug_p8` prints the rows, report-only. Debug runs are
  compared to baselines bitwise, so G1 is enforced by RT itself on every PR. The fatal threshold stays with A in
  `control_p8`.
- **Cost:** per site per column `levs × nwat` multiply-adds (127 × 7 ≈ 900); ~45 sites ≈ 40 k flop per column-step,
  estimated a few % of physics. Zero when not generated; one call + pointer setup when generated and off.

### 2.9 Repositories and order

| PR | Repo | Content | Depends on |
|---|---|---|---|
| F1 | ccpp-framework | `--instrument`, site numbering, `ccpp_call_site_index`/`_names`, rules 1–3, end-to-end test (a checksum probe + `capgen_repeat_probe` extended) | #783/#770 discussion |
| U1 | ufsatm | A (unchanged), budget DDT, CMake option, DEBUG compiles instrumented | F1 (A does not) |
| P1… | ccpp-physics | `ufs_budget_probe` scheme; then one family's declarations per PR (SAMF, satmedmfvdifq, Thompson, photochemistry first) | U1 |

## 3. Verification

| Claim | Must reproduce | Known-good | Known-bad that must fail |
|---|---|---|---|
| Off is free | — | default build: generated caps diff-identical to upstream | a generator change that reorders one argument → diff |
| Read-only | 0 of 3402 differ on/off | probe as specified | probe declaring `gq0` `inout` → capgen refuses; with rule bypassed, writing one value → G1 differs |
| Closure | Σ sites − A ~1e-17 (fix), ~1e-16 (dev) | full instrumentation | instrument only `phys_ts` → `sites_vs_physics` off by ~E |
| Family numbers | pbl 2e-14 / 3e-8; photochem 1e-16; samf 1e-15 / +3.4e-3; mp −1.6e-3; rest 0 (fix / dev); B − C SAMF ~1e-16 | fix tree SAMF; Thompson TH1–TH7 tree mp: −1.29e-7 per window (measured) | dev tree SAMF (+0.78 % P_conv); fix + SA1 reverted |
| Spans | — | with `held` exported, each SAMF site residual ≤ 1e-14 (fix) | `held` forced to 0 → equal and opposite rows at `interstitial_3`/`_4` |
| Keying | surface loop: one row per site | toy suite, subcycle of 2 | prototype counter on a toy suite with a skipped call → rows shift (shows why keying matters) |
| Detector | — | toy leak scheme with its declaration → clean | same scheme undeclared → `UNDECLARED` at its site |
| Threads / layout | BUDGET lines 1 vs 2 threads identical | 3×8 vs 4×6, 1 vs 2 threads | module-level accumulator; plain `MPI_SUM` |
| Groups | radiation cap: 0 calls (prototype 8) | grep generated caps | listing `radiation` with `dqdt` requested → capgen error |
| Cost | — | ≥ 3 samples each of plain, generated-off, on | — |

## 4. Top three risks

| # | Risk | What retires it |
|---|---|---|
| 1 | The framework team declines or defers during capgen-v1 unification | Pitch as #783/#770 with the checksum probe as first client and an end-to-end test in their suite; A ships regardless; the instrument scheme works unchanged as a hand-placed suite entry (B), so no work is lost |
| 2 | Families never declare: the instrument shows ΔW per site but no residual | `UNDECLARED` makes absence visible in `control_debug_p8`; ship the four families already fixed with numbers above; declaration is ~5 lines + meta in a scheme the owner already edits |
| 3 | `W` is wrong somewhere (other `tend_opt` chains, MYNN clipping, held water not exported, RRFS smoke writing `qgrs`) and false residuals cost trust | `sites_vs_physics` per column every window ties the instrument to A; report-only across all 17 DEBUG suites, each nonzero row triaged before any threshold; tolerances from G7 precision measurements |
