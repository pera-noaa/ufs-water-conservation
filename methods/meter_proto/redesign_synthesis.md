# Meter redesign: what the three reviews agree on, and the recommended design

Three independent reviews, one per prototype, each given only its prototype's code, [`results.md`](results.md) and
[`../meter_design.md`](../meter_design.md): [`redesign_A.md`](redesign_A.md) (host meter), [`redesign_B.md`](redesign_B.md)
(check schemes), [`redesign_C.md`](redesign_C.md) (capgen hook). None was built.

## Status

| | |
|---|---|
| **Convergence** | All three, unprompted, move flux knowledge out of the meter and into the code that applies the tendency (the `*_post` interstitials since ccpp-physics#299), as a cumulative standard-named declared-change total. All three keep A as the whole-physics base. B and C both key attribution by a fixed site, not a run-time counter |
| **Recommended** | A2 first (PR 1, no answer change, no suite or framework edit); owner-declared counter; attribution by B's telescoping checkpoint chain, placed as explicit scheme lines in the RT suites; C's `--instrument` offered to the framework under #783/#770 as the general mechanism for the same probe |
| **Adopted in** | [`../meter_design.md`](../meter_design.md), which is the current design; this file records the reviews' agreement and differences |
| **Open** | Maintainer acceptance (meter calls in shared interstitials, new standard names, a framework feature); E as booked ≠ E applied in MYNN suites (unmeasured); timing (one sample per arm resolved nothing) |

## Where the reviews agree

| Point | A | B | C |
|---|---|---|---|
| Whole-physics meter is the base and lands first | A2 in `CCPP_driver.F90` | B depends on A (seed, tail, reduce, print) | "A ships regardless" |
| Declarations owned by the code that applies the change | cumulative `budget_decl_<qty>` counter | `budget_declare` in the 7 tendency-applying interstitials | running declared total in each family's `_post` |
| The meter keeps no family/scheme table | E and P only | sites are generic interstitials | host `select case` deleted |
| Slots keyed statically | — | site constants | capgen call-site index |
| Off must be off (prototype was not) | allocate only when on | arrays unallocated, optional args absent | default caps byte-identical |
| One copy of the column integral, species from indices | `colint` | `column_amount` in ccpp-physics | as A |
| Timing needs repeated samples | ≥ 3 | ≥ 5 | ≥ 3 |

## Where they differ, and the call

| Question | Options | Recommendation |
|---|---|---|
| Where the whole-physics bracket sits | `atmos_model.F90` (prototype) / `CCPP_driver.F90` per chunk (A2) | A2: threaded, shared with MPAS, and windows close at `phys_zero`, which fixes a prototype bug (below) |
| How attribution reaches each segment | checkpoints inside 7 interstitials (B) / framework-inserted probe after every call (C) / explicit suite lines (B and C fallback) | explicit checkpoint lines at B's four sites in the RT-tested suites first (no framework dependency, no edit inside shared interstitials); propose C's `--instrument` to the framework in parallel; the probe scheme is the same in all three |
| SAMF's water held in `clw` between interstitial_3 and _4 | place no checkpoint inside the span, enforced by a suite lint (B) / export `column_water_held_outside_tracer_state` (C) | B's placement rule now; C's `held` variable when per-call rows inside convection are wanted |
| Undeclared change | residual per segment (B) / `UNDECLARED` row per site (C) | C's row: it is what a new scheme's developer would run |
| Output | stdout + diag_table residual maps (A2) | both: stdout for RT logs, maps to find a leak |
| Fatal threshold | physics 1e-5 per window (A2); B closure 1e-12 from day one | B's closure gate fatal from day one (only a meter bug can fail it); physics fatal after the Thompson series merges (measured remainder 1.29e-7, smallest defect 1.6e-3) |

## Prototype defects the reviews found (not visible in the results)

- **Window rule** (A): `mod(kdt, nszero)` with `nszero` frozen at init misaligns with the history buckets under `fhzero_array`
  and at the IAU-centre reset. Correct only for the constant `FHZERO` case tested.
- **"Meters off" was not off** (B, C): the B schemes run and the C hook is called (44 calls per chunk per step) whatever the
  namelist says, so the 169 s vs 154 s timing cannot be attributed.
- **Silent family fall-through** (C): a scheme not in the `select case` goes to `rest` with no error; MYNN and GFDL-MP suites
  would report there.
- **Slot counter** (C): assumes every column of a chunk saw the same calls; any run-time-conditional call would shift every
  later slot silently.
- **`samf_prepare_flux_for_budget` is not SAMF-specific** (B): it reads Diag `rainc`, written by the generic convection
  posts in all 46 suites with deep convection.
- **`dtf /= dtp` is fatal at init** (A): switching on a diagnostic should not abort a run.

## Suite facts (checked on the patched tree, 56 suite files)

28 of 56 suites run `GFS_PBL_generic_post` and 26 run MYNN (`FV3_ideal_mp_nssl` and `MPAS_RRFS` neither); 55 run `GFS_MP_generic_post`; 55 run at least one of the
tendency-applying posts; no suite runs `GFS_debug`. Suite counts in the three reviews are corrected to these (exact `<scheme>` matches). NCAR/ccpp-framework #783 ("Debugging capabilities for capgen v1") and #770 (variable tracker and debugging
feature) are open.

## Next

1. Build A2 plus the counter and the four-site checkpoint chain as explicit suite lines; rerun the arms fix, dev, th,
   1 and 2 threads, and `fhzero_array` and restart cases (A2's verification table).
2. Measure booked vs applied E in `hrrr_control` (MYNN) before any PBL threshold.
3. PR 0 issue with these numbers; ask the framework team on #783 whether a typed instrument insertion fits their plan.
