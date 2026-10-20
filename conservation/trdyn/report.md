# trdyn: dry-consistent FV3 tracer transport (class c) and dry IC option (class d)

## Status

Two FV3 patches from this workstream are in the final series. It also delivered rows 27 and 28 (trsamf's 02 and 03
as 02b and 03b; see `trsamf/report.md`). Nothing is left open in the dycore.

| SERIES row | Class | Switch: default / all-on | 24 h, before → after |
|---|---|---|---|
| 29 `29_INLQ_04.diff` | BF | — | inline_q on: mass pt_cnv / pt_ghg / pt_plume 1.04e-9 / 1.89e-9 / 1.51e-9 → 5.9e-15 / 5.9e-15 / 8.4e-15; dry air −8.6e-12 → 5.1e-17 |
| 30 `30_DYN_v6.diff` | PC | `dry_tracer_adv` F / T; `dry_tracer_ic` F / F | uniform pt_udry, end to end rms / max 2.29e-5 / 9.8e-4 → 3.72e-14 / 4.90e-13; IC 4.9e-6 / 3.4e-4 → 4.2e-17 / 2.2e-16 |

- v6 is v5 rebased on 04: the dry inline_q branch takes its dry mass from 04's pre-update delp. With inline_q on, v6
  gives 3.9e-14 / 6.1e-13. SERIES regenerated row 30 by re-anchoring; its + and − lines equal v6's.
- Switches off: bitwise. Switches on: weather, water and generic tracers bitwise while chemistry tracers are passive.
- v4 onward covers tracer_2d, tracer_2d_nested with its BCs, and inline_q; FILL2D is a FATAL guard. The FATAL scope
  in Design (01_DYN) is round 1's and no longer holds. v5 adds `dry_negadj` for neg_adj2/3/4.
- 32-bit dycore: 2.37e-5 / 1.22e-3 → 1.04e-6 / 2.03e-5 (float32 floor). GOCART: the switch moves weather and aerosols
  only at the chaotic-noise level. Regional and HAFS moving nests are untested.
- Impact (round 1, v1): class c alone 0.056 / 2.0 ppm rms / max on pt_ghg; with the dry IC 2.1 / 12.5 (reinterpreted
  IC). Cost about +1.5 % of the forecast.

## Current answers

## Classification
- dry_tracer_adv: PHYSICS CHANGE (numerical-consistency design change). Per-species limiting is FV3's intended design;
  the change makes non-water tracers ride the dry air the limited water fluxes imply. Exact to round-off, no water or
  dynamics change; it applies to every "chemistry" tracer, so in UFS-Chem with radiatively active aerosols it would
  change the forecast through them.
- dry_tracer_ic: PHYSICS CHANGE (input convention): chemistry IC fields are dry mixing ratios.

## Design (01_DYN)
Switches in `&fv_core_nml`: `dry_tracer_adv`, `dry_tracer_ic` (both .false.). Tracers affected: field_table
`"tracer_usage","chemistry"` (the GHG/UFS-Chem tracers, same set as trsamf DRY); water = tracers 1..nwat (as the
physics write-back). Water, T, u, v, delp and all other tracers take the unchanged code path.

**Advection (`tracer_2d_1L`, per level and per sub-cycle).** Non-dry tracers (incl. water) run first, unchanged, and
the limited water fluxes fw_i (fx, fy out of fv_tp_2d, already x mfx) are kept. Dry-air flux fd = mfx - sum_i fw_i
(fixed order). Dry tracer: c = q/(1 - sw) on the data domain (sw = water at the start of the sub-step), fv_tp_2d(c)
with the same Courant numbers / ra_x / ra_y / hord but mass fluxes fd, update q_new = (q dp1 + div(fd c_face))/dp2.
Since dp2 (1 - sw_new) = dp1 (1 - sw) + div(fd) identically (water update is q_w dp2 = q_w dp1 + div fw_i), a uniform c
gives q_new/(1-sw_new) = c0 to round-off; tracer mass update is the unfixed one's form (q dp1 + flux divergence).
nord_tr damping is not used by tracer_2d_1L; tracer_2d (z_tracer=F), tracer_2d_nested and inline_q are not
implemented: FATAL if dry_tracer_adv is set with them.

**Remap (`mapn_tracer_dry`, called instead of mapn_tracer when dry tracers exist).** Saves c = q/(1-sw) and the old dry
edges pd1 (cumulative dp1 (1 - sw)), calls the unchanged mapn_tracer for all tracers (water bitwise as before), builds
new dry edges pd2 from dp2 (1 - remapped water), rescales pd2 to the old column dry mass (difference is round-off),
remaps c from pd1 to pd2 with map1_q2 (same kord_tr, iv=0), fillz on c with dry weights, returns q = c D2/dp2.
Uniform c: PPM preserves constants; mass sum(q dp2) = sum(c D2) = sum(c D1).

**IC (`atmosphere.F90`).** dry_tracer_ic and cold start: after fv_restart (external_ic remap, which maps the file's
field as a scalar, constant-preserving) the chemistry tracers are kept as dry ratios; after adiabatic_init (or at once
if na_init = 0) q = c_IC (1 - sum water of the final state). The IC file must then hold dry mixing ratios.

## Round 2 (2026-10-18): FATAL scope limits replaced, 02b/03b, 32-bit, nest, OpenMP, F3
Deliverables (`patches/`): **01_DYN_dry_tracer_adv_remap_ic_v4.diff** (supersedes v1-v3; FV3 only, 10 files),
**02b_T1_samf_tracer_substep.diff** (02 without trsrc: interface-mean parcel start + SA1 face everywhere; sub-stepping
kept for every SAMF tracer incl. ozone/TKE; trpw booked with eta(k)*wf(k) as latent 01a), **03b_DRY_...diff** (03
rebased on 02b, context line only; changed lines identical to 03). Apply order: base [+ latent 01a] + 02b + 03b + 01_DYN v4.
All apply with -F0 on the tracer base and on energy/fx (01_DYN: 2 hunks offset; 02b+03b stack verified on fx copies;
01a+02b+03b stack verified). The 32-bit/nest tree n32 is byte-identical to base + v4 (+02b+03b+chem hook).

What v4 adds over round 1:
- **tracer_2d** (z_tracer=.false.): same dry-flux construction per level/sub-step; nord_tr damping of c uses dry mass
  dp1(1-sw) in deln_flux (zero for uniform c; flux form, so mass-exact).
- **tracer_2d_nested + BCs**: same construction. Nest: the parent sends the dry ratio c of dry tracers
  (setup_nested_grid_BCs), the child converts its BC halo q = c(1-sw_BC) after every BC apply (fv_nesting initial
  apply, tracer_2d_nested, dyn_core inline_q). Interpolation (space, time) and the pd clip then act on c; the halo is
  exactly dry-uniform for a uniform c whatever happens to the BC water (pd clip, remap_BC). Two-way update never
  touches q in this tree (update_remap_tqw: q remap FATAL; nestupdate 7). Regional: halo BC values are converted only
  if dry_tracer_ic (BC files then hold dry ratios like the IC); with moist BC files c=q/(1-sw) is used as is (no
  guarantee; untested, see below).
- **inline_q** (d_sw, per acoustic step): same construction (water fluxes gx,gy kept; dry flux = delp mass flux -
  sum; damping with delp(1-sw)). Not used by any RT (grep), but works and is exact (table).
- **FILL2D**: FATAL guard (only compiled with -DFILL2D, not in any UFS build, only for hord_tr<8; fill2D moves water
  horizontally with no dry-air flux, so a consistent version needs fill2D's fluxes exported - not worth it unused).
- **Remap edges in R_GRID** (v3): the dry-pressure edges are cumulative sums ~1e5 Pa; in a 32-bit dycore ulp(1e5 Pa)
  / thin-layer D gave 8e-5 per remap. Now 64-bit edges + an R_GRID copy of map1_q2 (map1_dry); in 64-bit identical
  arithmetic to v2 (a2 == a1 bitwise).
- **dry_tracer_ic** (v4): q is set to c(1-sw) right after external_ic as well as after adiabatic_init. Before, q held
  c during adiabatic_init, so the parent sent c/(1-sw) as nest BCs and the first post-init BC t0 was wrong by
  ~sum(water): nest boundary rows 5e-4, decaying inward (found by the nest test, fixed, re-tested).
- Mask now `flagstruct%dry_tr` (allocated at the first fv_dynamics call; read by d_sw/dyn_core/fv_nesting).

Gates (64-bit = C96 control_p8_ugwpv1 24 h metered; uniform tracer pt_udry, 1e-6 dry):
| gate | unfixed | fixed |
|---|---|---|
| off = bitwise, z_tracer=T (c0 dc vs u0 v2) | | all 2520 TM lines identical |
| off = bitwise, z_tracer=F nord_tr=2 trdm2=0.05 (tc vs t0) | | identical |
| off = bitwise, 32-bit (s0c vs s0, atmf024 25 vars) | | identical |
| tracer_2d + damping: shadow per-call max, advection / remap | 2.0e-4 / 2.5e-4 | 6.7e-16 / 1.2e-13 |
| tracer_2d: pt_udry 24 h rms / max (tc / t1) | 2.24e-5 / 1.08e-3 | 1.40e-11 / 1.79e-9 (*) |
| inline_q: pt_udry 24 h (q0 / q1); dycore shadow max | 2.34e-5 / 1.28e-3 | 9.8e-13 / 1.25e-10 (*); 1.2e-13 |
| weather with switch on (TM air+water+o3+tke+generic) | | identical (t0/t1, q0/q1, o0/a1) |
| mass 24 h, tracer_2d run pt_ghg / pt_udry (tc / t1) | 4.64e-15 / 3.98e-15 | 4.52e-15 / 3.82e-15 |
| 02b+03b+v4, uniform start (b1) vs 02+03 (a2), 24 h rms / max | 3.72e-14 / 4.64e-13 (02) | 3.72e-14 / 4.89e-13 (02b) |
| 02b end-to-end, both switches, dry IC (b2): IC (SI3) / 24 h | | 2.2e-16 / 3.72e-14, 4.90e-13 |
| 02b mass 24 h pt_ghg / pt_udry (b2) | | 3.08e-15 / 2.57e-15 |
| OpenMP 2 threads vs 1, switch on (h2 vs a2): TM lines, atmf024 | | identical (TP physics-slot meter sums differ: meter accumulators not thread-safe) |
| 32-bit C96 24 h pt_udry rms / max (s0 / s2v), float32 atmf | 2.37e-5 / 1.22e-3 | 1.04e-6 / 2.03e-5 |
| 32-bit mass 24 h pt_ghg / pt_udry / pt_cnv (s0 / s2v) | 3.03e-6 / -7.8e-8 / 3.21e-6 | 3.25e-6 / 3.3e-8 / 3.21e-6 |
| nest gnv1 (32-bit, 3 h, native restarts) parent rms / max (g0d adv off / g1n) | 9.0e-6 / 6.6e-4 | 3.4e-7 / 5.0e-6 |
| nest tile7 rms / max; within 10 rows of the boundary / interior | 1.35e-5 / 7.8e-4 | 9.5e-7 / 7.7e-6, no boundary signature |
| F3 gate fscav 0.5, 01a+02b+03b: (dM_atm + D)/M0 pt_ghg / pt_udry | (latent unfixed -7.4e-4) | 3.0e-15 / 2.6e-15 (no-sink pt_cnv 3.2e-15) |
(*) the residual is neg_adj3 (shadow per-call max 2.3e-7 in tc and t1 alike, 1.5e-7 in q0 and q1): with nord_tr
damping or inline_q, water goes negative and neg_adj3 borrows water vertically at fixed delp, i.e. moves dry air with
no tracer flux. Pre-existing water-only fixer, inactive (0) in the operational z_tracer + hord_tr 8 config. Making it
consistent needs the implied vertical dry-air flux (column-conserving borrow) applied to dry tracers; not done.
32-bit: dycore state, the dyn<->phys conversions and the write-back round to float32 every step; 1e-6 rms over 120
steps is that random walk (6e-8 x sqrt(~300 operations)). 32-bit mass changes 3e-6/day for every tracer, fixed or not
(pt_cnv generic identical): property of the 32-bit dycore, not of the fix.
F3: 389 shallow else-branch (borrowing) events in the run; column residual sum/D 8.5e-16 deep, 1.1e-15 shallow.

Untested: regional (regional_control uses MYNN PBL, no DRY physics, and the BC files carry no chemistry tracers);
HAFS moving nests; GOCART suites. Not chased: neg_adj3 (above).

## Round 3 (2026-10-18): v4/v5 64-bit end-to-end measured, neg_adj, GOCART
**neg_adj (v5).** neg_adj2/3/4 fill negative water by borrowing it from other layers at fixed delp, which moves dry
air between layers with no tracer flux. `dry_negadj` (fv_tracer2d) saves the layer water mass delp*sum(w) before the
neg_adj blocks and afterwards moves each dry tracer with the implied downward dry-air flux G(k+1/2) = sum_{j<=k} dW_j
(upwind dry ratio, flux form, G = 0 at top and bottom). Exact for a uniform c; tracer mass conserved exactly; columns
where neg_adj moved nothing are untouched; only runs when dry tracers exist (allocate), so off = bitwise.

Trees (64-bit, metered): dz = base + 01a + 02b + 03b + v5, dzc = same without v5. (dz has the v5 mask before the
"type=diagnostic" exclusion; no diagnostic chemistry tracers in these runs.) GOCART: ga = base + 01a + 02b + 03b + v5
(byte-identical to the patch), gac without v5; APP=ATMAERO, -D32BIT, suite FV3_GFS_v17_p8; RT atmaero_control_p8_rad
(aerosol-radiation feedback on, iaer 2011), 24 h.

| gate | unfixed | fixed |
|---|---|---|
| v5 off = bitwise (zc vs z0): TM lines, atmf024 | | identical |
| v5 end-to-end both switches, dry IC (z2): IC dev SI3 rms / max | | 4.2e-17 / 2.2e-16 |
| z2 24 h pt_udry rms / max | | 3.72e-14 / 4.90e-13 |
| z2 mass 24 h pt_ghg / pt_udry / pt_cplume | | 3.08e-15 / 2.57e-15 / 3.34e-15 |
| nord_tr=2, z_tracer=F (t1 v4 / zt v5) 24 h rms / max | 1.40e-11 / 1.79e-9 | 3.80e-14 / 4.87e-13 |
| neg_adj3 shadow per-call max (t1 / zt) | 2.3e-7 | 4.4e-16 |
| zt mass pt_ghg / pt_udry | 4.52e-15 / 3.82e-15 | 4.49e-15 / 3.79e-15 |
| inline_q (q1 v4 / zq v5) 24 h rms / max | 9.8e-13 / 1.25e-10 | 3.88e-14 / 5.06e-13 |
| GOCART off = bitwise (ggc vs gg0, RESTART fv_core + fv_tracer) | | identical |
| GOCART switch on vs off (gg1 - gg0), weather T / u rms | | 0.169 K / 0.29 m/s (noise control ggp, consv_te 0.999: 0.176 K / 0.31 m/s) |
| GOCART burdens 24 h (gg1/gg0 - 1) | | 5e-5 .. 3.6e-3 across 23 species; noise control 4e-5 .. 3.7e-3 |
- inline_q itself is not mass-conserving (all tracers ~1e-9/day, generic ones too, q0 = q1 = zq): pre-existing.
- GOCART: a uniform-dry test tracer cannot be carried. GOCART overwrites every chemistry tracer it does not know:
  pt_udry (chemistry, fscav 0) is read as 1e-6 and is 0 at 12 h. The uniform gate for the dycore/physics code
  path in a 32-bit dycore is s2v (round 2: 1.0e-6 / 2.0e-5, float32 accumulation). The impact of the switch on
  GOCART aerosols and weather is at the chaotic-noise level of a consv_te 0.999 perturbation in 24 h (feedback on).

## Round 4 (2026-10-18): inline_q mass loss
**Cause (bug).** In d_sw's inline_q block delp is updated on the compute domain before the tracer fv_tp_2d calls,
which pass `mass=delp` to the del-n damping (nord_t, damp_t = vtdm4 with do_vort_damp). deln_flux weights a face
flux by mass(i-1)+mass(i): on a PE-boundary face one PE uses its new delp and the old halo value of its neighbour, the
neighbour the reverse, so the two PEs add different damping fluxes for the same face and tracer mass leaks at PE
boundaries (water too; scales with tracer gradients, so a uniform tracer loses ~nothing). tracer_2d (round 2 nord_tr
run) uses dp1 with a fresh halo and conserves. **Fix (04_INLQ):** keep the pre-update delp on the data domain (halo
already holds the neighbours' pre-update values) and use it as the damping mass. BUG FIX (restores single-valued,
flux-form fluxes). v6: the dry inline_q branch uses the same array for its dry mass.

| gate (C96 64-bit 24 h, inline_q=.true.) | unfixed (qc, dzc) | 04 (q4i) | 04 + v6, dry on (q6i) |
|---|---|---|---|
| tracer mass pt_cnv / pt_ghg / pt_plume | 1.04e-9 / 1.89e-9 / 1.51e-9 | 5.9e-15 / 5.9e-15 / 8.4e-15 | 5.9e-15 / 5.8e-15 / 8.4e-15 |
| dry-air mass | -8.6e-12 | 5.1e-17 | 5.1e-17 |
| pt_udry dry ratio 24 h rms / max | | | 3.9e-14 / 6.1e-13 |
| inline_q off = bitwise vs no-fix build (zc vs q40 04; zc vs q60 04+v6): TM, atmf024 | | identical | identical |
| weather 04+v6 vs 04 (TM air, water, o3, tke, generic tracers) | | | identical |
- With inline_q on, 04 changes the forecast (water's damping fluxes change too): atmf024 differs from the unfixed
  inline_q run (22 of 25 vars), as expected for a conservation fix in the water transport of an option no RT uses.

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| # trdyn: dry-consistent FV3 tracer transport (class c) and dry IC option (class d) | title | current | both |
| ## Status (2026-10-18, round 3 done) | chronological status | superseded by `## Status` above | `report.history.md` |
| ## Results | v1 numbers and gates (off, layout, restart, positivity, cost) | superseded by Round 3 for the end-to-end numbers; layout, restart and cost gates were run on v1 only | `report.history.md` |
| ## Impact (ppm-equivalent at 400 ppm, 24 h, atmf float32) | ppm impact of classes c and d | archival (v1; not re-measured) | `report.history.md` |
| ## Classification | PHYSICS CHANGE for both switches | current | `report.md` |
| ## Scope and limits | round 1 scope | superseded by Round 2 (v4) | `report.history.md` |
| ## Design (01_DYN) | core advection, remap and IC construction | current; FATAL scope sentence superseded by Round 2 | `report.md` |
| ## Files | patches, scripts, jobs | archival | `report.history.md` |
| ## Round 2 (2026-10-18): FATAL scope limits replaced, 02b/03b, 32-bit, nest, OpenMP, F3 | v4, 02b/03b, 32-bit, nest, OpenMP, F3 gates | current; the neg_adj3 residual (*) superseded by Round 3 | `report.md` |
| ## Round 3 (2026-10-18): v4/v5 64-bit end-to-end measured, neg_adj, GOCART | v5 dry_negadj, end-to-end gates, GOCART | current | `report.md` |
| ## Round 4 (2026-10-18): inline_q mass loss | 04_INLQ bug fix, v6 | current | `report.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
