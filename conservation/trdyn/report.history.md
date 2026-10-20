*History of `report.md` (trdyn), moved verbatim on 18 October 2026. The head is `report.md`.*

# trdyn: dry-consistent FV3 tracer transport (class c) and dry IC option (class d)

## Status (2026-10-18, round 3 done)
- Current: `patches/04_INLQ_inline_q_damping_mass_single_valued.diff` (BUG FIX, independent of the dry switch) and
  `patches/01_DYN_dry_tracer_adv_remap_ic_v6.diff` (= v5 rebased on 04: the dry inline_q damping mass uses the same
  pre-update delp). Apply order: base + 01a + 02b + 03b + 04 + v6; all -F0 on the tracer base and energy/fx.
  v5 (round 3, with the integrator) differs from v6 only in that one line; v1 kept for the record.
- Gates: "Round 3" table. Everything at round-off; nothing left open in the dycore.
- Classification: dry_tracer_adv / dry_tracer_ic PHYSICS CHANGE (opt-in, weather bitwise when chemistry tracers are
  passive); 02b sub-stepping and trpw booking BUG FIX.

## Results
| quantity (pt_udry = dry-uniform chem tracer) | unfixed | fixed |
|---|---|---|
| shadow, advection (dyn_core+tracer_2d) per-call max / 24 h sum MS (o0 / a1) | 1.8e-4 / 2.0e-10 | 6.7e-16 / 2.3e-30 |
| shadow, remap per-call max / 24 h sum MS | 1.6e-4 / 3.9e-11 | 1.2e-13 / 2.2e-27 |
| IC: dev at first dynamics step (SI3), rms / max (n0 / e2) | 4.9e-6 / 3.4e-4 | 4.2e-17 / 2.2e-16 |
| 24 h dev, uniform start (o0 / a1), rms / max | 2.28e-5 / 9.8e-4 | 3.7e-14 / 4.6e-13 |
| 24 h dev end-to-end incl. IC (n0 / e2), rms / max | 2.29e-5 / 9.8e-4 | 3.7e-14 / 4.6e-13 |
| TU global min/max of dry ratio at 24 h (e2) | 0.99930e-6 / 1.00098e-6 | 1.0000000000e-6 / 1.0000000000e-6 |
| tracer mass, 24 h relative, pt_ghg / pt_udry / pt_cplume | 3.17e-15 / 2.71e-15 / 3.49e-15 | 3.02e-15 / 2.54e-15 / 3.44e-15 |
| remap mass term per step rms, chem tracers | 1.5-5.5e-17 | 2.0-7.8e-17 |

Remaining physics-side residual: write-back 4.5e-14 max (trsamf DRY, pre-existing rounding); dycore round-off as above.
The remap's 1.2e-13 is at k = 127: dry edges are cumulative sums (ulp(1e5 Pa) / bottom-layer dry thickness); the
alternative output q = c(1 - sw2) is uniform to 1e-16 but then column mass moves by the same 1e-13 of the bottom layer.
I kept the mass-exact form.

Gates (`results/cmp2.txt`, TM lines = 17-digit global masses at 18 points per step):
- **Off = bitwise**: dc (no fix) vs dy with switches off (c0 / o0): all 2520 TM lines (air + 21 tracers),
  atmf024 (25 vars), 24 h RESTART fv_core / fv_tracer / sfc_data / phy_data bitwise identical.
- **On, weather unchanged**: o0 vs a1: air + water x6 + ice_nc, rain_nc, o3mr, sgs_tke + generic pt_* identical in
  every TM line; atmf024 22/25 identical (only pt_ghg, pt_udry, pt_cplume differ); RESTART fv_core, sfc, phy bitwise;
  fv_tracer 18/21 (the 3 chem tracers). n0 vs i1 (IC option alone) same pattern.
- **Layout**: e2 (3x8) vs e2L (4x6): atmf024 bitwise.
- **Restart**: e2R (12 h warm start from e2) vs e2: atmf018/024 bitwise; e2R vs e2L 24 h RESTART all bitwise.
- **Positivity / monotonicity** (pt_cplume plume with zeros, pt_ghg structured): q<0 cells 2 vs 2 (float32 history,
  already present unfixed); dry-ratio range at 24 h inside the initial range in both; pt_cplume max 11.877 (fixed) vs
  11.878 (unfixed), pt_ghg 2.28981 vs 2.28976 of initial max 2.656. No new extremum.
- **Cost** (PE 0 timers): TRACER_2D 11.6 -> 11.9 s (+3 %), REMAPPING 22.1 -> 24.4-25.3 s (+10-14 %, chem tracers
  are remapped twice), FV_DYNAMICS 88 -> 91.5 s, about +1.5 % of the forecast (wall time noise 214-235 s).

## Impact (ppm-equivalent at 400 ppm, 24 h, atmf float32)
| comparison | pt_ghg rms / max | pt_udry rms / max | pt_cplume rms / max | T, q, u, ps |
|---|---|---|---|---|
| class c only (o0 -> a1) | 0.056 / 2.0 | 0.0094 / 0.39 (= removed artefact) | 0.41 / 20.6 (plume mean is small) | bitwise |
| c + d, IC read as dry (n0 -> e2) | 2.1 / 12.5 (IC reinterpreted: x(1 - sum water)) | 0.0095 / 0.39 | 7.7 / 76 | bitwise |

## Scope and limits
- (Round 1; superseded by v4) Implemented for tracer_2d_1L (z_tracer = T, as used in UFS) only; tracer_2d (nord_tr damping path; would need
  mass = dp1 (1 - sw) in deln_flux), tracer_2d_nested and inline_q abort with FATAL when the switch is on.
- FILL2D (compile flag, only for hord_tr < 8) changes water after advection and would break the identity; not guarded.
- Exactness needs the dry flux = total - sum of limited water fluxes and the remap's dry edges from remapped water;
  both are available inside FV3, so no approximation was needed.
- (Round 1; all run in round 2, see below) Not run: 32-bit dycore (identity holds to 32-bit round-off by construction), OpenMP > 1 thread (dry loops are
  per-tracer, water sums in fixed order), other suites.

## Files
- `patches/01_DYN_dry_tracer_adv_remap_ic.diff`; `meters/testhook_uniform_reset_env.py` (test-only, skipped with
  env TRDYN_NORESET).
- `scripts/`: mk_tree.sh, build_*.sbatch, make_rundir.sh, mkruns.sh (A: c0 o0 a1; B: n0 i1 e2 e2L; C: e2R),
  multirun.sbatch, make_ic.py (ic_m: tracer IC + pt_cplume; ic_d: pt_udry = 1e-6 float64), mk_warm.sh, cmp_atmf.py,
  cmp_dyn.py, cmp_all.sh, cmp2.sh. Hercules copies of trunif analyzers + `analyze_tm2.py` (names for 21 tracers).
- `results/`: o0_sh.txt, a1_sh.txt (shadow tables), dry_attrib.txt (pt_udry per process), cmp2.txt (gates, impact).
- Jobs: builds 10152479/80; runs 10152503 (A), 10152504 (B), 10153186 (C); compares 10153187, 10153197.
