# Passive-tracer mass conservation in UFS (C96 control_p8_ugwpv1, 24 h, 64-bit dycore)

## Status

One patch from this workstream is in the final series: FV2, row 05 `05_FV2.diff`, class BF, unconditional (no switch).
FV2 makes the dynamics → physics conversion divide by the same layer mass the write-back multiplies by.

| 24 h, C96 p8_ugwpv1, 64-bit dycore | base tree | with FV2 |
|---|---|---|
| pt_dyn_nopbl mass change / initial mass | +3.22e-15 | +2.27e-16 |
| pt_ghg mass change / initial mass | +3.16e-15 | +2.37e-16 |
| dyn → phys conversion term, pt_dyn_nopbl [rms per step] | +3.07e-15 [2.8e-16] | +5.2e-17 [4.8e-18] |

- FV2 red team (this report): stateless, so restarts are unchanged; layout 4×6 is bit-identical to 3×8.
- With FV2 every remaining term is round-off (≤ 0.1 ulp of the global mass per step); the dycore biases were not chased.
- The May drift is the accounting of the offline sum, not a model defect (12 h figure; the 10-day trend was not re-run).
- In develop, SAMF deep destroys 2 % per day of a generic tracer; SA1 (water diff 01, in the series base) removes it.
- T1 (SAMF tracer Courant up to 5) was found here and not fixed here. It is fixed by row 27 `27_T1_02b.diff` (BF, unconditional; `trsamf/`, red team `trred/`).
- The dry-ratio spread of a uniform tracer (rms 1.07e-3, max 1.22e-2 at 24 h) was measured here. `trunif/` located its generators; rows 28 `28_DRY_03b.diff` (PC, no switch) and 30 `30_DYN_v6.diff` (PC, `dry_tracer_adv` F / T, `dry_tracer_ic` F / F) fix it.
- Note: the FV2 section calls it a "candidate" to propose only if exact bookkeeping is wanted; the follow-ups, TRACKER (BUG) and SERIES (BF) class it as a bug fix.
- Note: F2(d) calls the dry transport a PHYSICS CHANGE and SERIES row 28 says PC; TRACKER lists DRY (03b) as NUM.

## Current answers

## Per-term attribution (24 h sum / initial mass; [rms of the per-step term])

Runs:
- base tree: `tm2` (10150450);
- FV2: `tmf1` (10150671).

Tables are in `$T/rt/<run>/tm_analysis.txt`. "<x" means every per-step value is below x.

| term | pt_dyn_nopbl base | pt_ghg base | pt_dyn_nopbl FV2 | pt_ghg FV2 | air FV2 |
|---|---|---|---|---|---|
| dyn_core + tracer_2d_1L (×2 per step) | +4.8e-17 [4e-18] | +4.9e-17 | +4.8e-17 | +4.7e-17 | +4.8e-17 |
| Lagrangian_to_Eulerian incl. fillz (×2) | +1.1e-16 [2e-17] | +1.1e-16 | +1.4e-16 | +1.3e-16 | +4e-18 |
| neg_adj3, end of fv_dynamics, gaps | 0 | 0 | 0 | 0 | 0 |
| fv_subgrid_z | −3e-21 | −1e-21 | −7e-21 | 1e-22 | 0 |
| dyn → phys conversion (`atmos_phys_driver_statein`) | **+3.07e-15 [2.8e-16]** | **+3.01e-15** | +5.2e-17 [4.8e-18] | +5.3e-17 | (condensate, by design) |
| physics (all schemes) | +2e-20 | −3.5e-18 | +1.7e-19 | +2.4e-18 | (water) |
| — SAMF deep (DCNV post) | +3e-21 | +1.5e-19 | +1.8e-19 | +1.8e-19 | |
| — SAMF shallow (SCNV post) | +2e-20 | −3e-20 | −9e-21 | −2e-20 | |
| — PBL (applied in GWD post) | 0 | −3.6e-18 | 0 | +2.3e-18 | |
| fill_gfs (sphum only) | 0 | 0 | 0 | 0 | |
| nopbl override | −2e-20 (undoes the physics exactly) | 0 | −1.7e-19 | 0 | |
| phys → dyn write-back | −1.4e-17 | +2e-18 | −8.7e-18 | +2.6e-18 | (water) |
| fv_update_phys | 0 | 0 | 0 | 0 | 0 |
| **total** | **+3.22e-15** | **+3.16e-15** | **+2.27e-16** | **+2.37e-16** | |

### FV2 (candidate): physics conversion divides and multiplies by different layer masses

**Code.** `atmos_phys_driver_statein` converts tracers to the physics basis by dividing by `prsl` (delp minus
condensate):
- `qgrs = q·delp / prsl`;
- it then builds `prsi` as a running sum from the model top, `prsi(k) = prsi(k+1) + prsl(k)`.

`atmosphere_state_update` converts back by multiplying by a different thickness:
- `q0 = prsi(k) − prsi(k+1)`;
- tracer mass after physics = `q0·gq0`.

`prsi(k) − prsi(k+1)` is `prsl(k)` plus the rounding of a sum of order 1e5 Pa. That is an error of eps·p/dp per
cell rather than eps. It is not random:
- Three runs with the flow perturbed (T × (1 + 1e-7·N(0,1)), `tm3`, `tm4`) give +3.07, +3.08 and
  +3.10e-15/day, always positive, and the same in every tracer and in dry air.
- An offline replica on the double-precision 24 h restart (`statein_check.py`, one state, not area-weighted)
  puts the bias in the cells where the condensate correction is tiny or negative. Those are cells where
  cond·delp is below half an ulp of the interface pressure or below zero, so the running sum drops the
  correction. Results:
  - total +1.7e-18;
  - cells with no condensate −7e-22;
  - 0 < cond·delp < ½ulp +6.7e-19;
  - the remainder, +1.1e-18, is from cells with negative condensate;
  - with FV2, +2e-20.

**Fix** (`patches/01_FV2_fv3_statein_consistent_layer_mass.diff`, GFDL_atmos_cubed_sphere
`driver/UFS/atmosphere.F90`, 2 lines + 1 comment). Divide by the thickness the write-back multiplies by:
`qgrs = q·delp / (prsi(k) − prsi(k+1))`, in both the `flip_vc` and the non-flipped branch. The round trip is
then exact to eps. The diff applies on the base tree (on top of 19_FV1) and, with a −1 line offset, without FV1.

**Meter.**
- The conversion term drops from +3.07e-15 to +5.2e-17 per day, and its rms per step from 2.8e-16 to
  4.8e-18, which matches independent rounding.
- No other term changes beyond its own scatter.
- 24 h totals drop 14×, to about 2 ulp.

**Against the unfixed run.**
- Fields cannot be compared point by point. A round-off change grows through convective and microphysical
  thresholds in one step: after step 1, T differs by up to 1.3 K for FV2 and 2.5 K for the 1e-7 perturbation.
  By 24 h FV2 and the perturbation run differ from the base by the same amounts (T rms 0.148 K vs 0.155 K).
- Global mass-weighted means at 24 h (T, q, cloud water, tracers, ps) for FV2 fall inside the spread of the
  three base-tree runs (`global_means.py`).

**Red team.**
- Restarts: the fix is stateless (statein is rebuilt every step from the dycore state and nothing is saved),
  so restart behaviour is unchanged.
- Decomposition: layout 4×6 (`tmfd`) is bit-identical to 3×8 in every history field and in the restart files.
- Water: the same conversion carries the water species, so their round trip also becomes exact. Dry air is
  untouched, because the write-back keeps `delp·(1−Σq)`.
- Other configurations: the code is shared by every FV3-based UFS configuration (GFS, RRFS, HAFS, 32-bit
  dycore, `MULTI_GASES`). The change only replaces one divisor with a quantity equal to it within rounding,
  and that quantity is always positive.
- Scope: it is round-off hygiene. The bias it removes is ~1e-12 per year. Propose it only if exact tracer
  bookkeeping is wanted.

### Remaining terms (with FV2), and why they are round-off
- The dycore acoustic step + tracer advection: +2.2e-17 per k_split per day for **every tracer and for air
  mass** (`air` +4.8e-17/day). Tracers inherit the dycore's own air-mass rounding. It is a fixed-sign bias of
  about 0.001 ulp per call. The likely cause, not verified, is the flux divergence × `rarea`, which does not
  cancel to the last bit.
- Remap: +3e-17 to +1.1e-16 per k_split per day, rms 2e-17 per call. The sign is mostly positive, but pt_plume's
  24 h total changes sign between `tmf1` and `tmf2` (+2.1e-17 vs −7.9e-17). It is consistent with the same
  running-sum mechanism (`pe1` built from `delp`).
- Every per-step term is ≤ 0.1 ulp of the global mass, and the 24 h totals are 1–2 ulp. Fixing these would
  touch core dycore numerics for a 1e-14/yr effect, so they were not chased.

### F1. Unmodified develop (@112b1d46) vs base (develop + water set), same hook + meters
`$T/dev` = `$U/ufs-weather-model` (git-clean develop; differs from base only in the water-set files) + hook + meters
+ uniform-reset hook; all anchors applied unchanged (no adaptation). Runs `dev1` (10150873) and `tm5` (10150932),
24 h, all meters. 24 h change / initial mass:

| term | tracer | develop | base (water set) |
|---|---|---|---|
| SAMF deep (DCNV post) | pt_cnv / pt_plume / pt_umoist | **−2.02e-2 / −4.42e-2 / −1.01e-2** | −1e-19 / 7e-19 / −6e-20 |
| | pt_ghg / pt_udry (chem path) | +1.39e-5 / −3.0e-8 | 1.5e-19 / 2e-20 |
| SAMF shallow (SCNV post) | pt_cnv / pt_plume / pt_umoist | −6.7e-4 / −7.6e-4 / −2.2e-4 | 1e-19 / 3e-19 / −3e-20 |
| | pt_ghg / pt_udry | −3.8e-7 / −1.3e-8 | −3e-20 / 1e-19 |
| PBL, dycore, conversions | all | as base (≤3.3e-15) | ≤3.1e-15 |
| **24 h total** | pt_dyn_nopbl / pt_cnv / pt_plume / pt_umoist / pt_ghg / pt_udry | 3.4e-15 / **−2.09e-2** / **−4.49e-2** / **−1.03e-2** / +1.35e-5 / −4.3e-8 | 3.2e-15 (all) |

The water set does this through SA1 (SAMF cloud-base TVD double count, `samfdeepcnv.f`/`samfshalcnv.f`): in develop,
SAMF deep destroys 2 % of a convectively transported generic tracer per day (4.5 % for the plume tracer, 1 % for a
uniform one); chemistry-path tracers lose/gain ~1e-5/day. With SA1 the SAMF terms are at round-off. T1 is present in
develop too (pt_umoist max 1.86e-4 at 24 h).

### F4. May drift — explained
pt_dyn_nopbl from this run's own history (`may_trap.py`, tm2), relative change from f000:

| | f006 | f012 | f018 | f024 |
|---|---|---|---|---|
| Σq·dpres/g (trap) | +5.1e-6 | +4.3e-6 | +4.0e-6 | +3.4e-6 |
| Σq·dpres/(1−Σcond)/g | −1.1e-11 | −3.9e-11 | −1.5e-11 | −3.2e-11 |
| in-model meter | | | | +3.2e-15 |

The trap gives the May order of magnitude (+7.2e-6 / 12 h there) and the correct accounting none (float32 output
noise): **explained** (for the 12-h figure; the 10-day trend was not re-run).

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| Passive-tracer mass conservation in UFS (C96 control_p8_ugwpv1, 24 h, 64-bit dycore) | title | current | `report.md` (and top of `report.history.md`) |
| Status (2026-10-17, updated after follow-ups F1–F5 — see section at the end) | dated status, mass table with and without FV2 | superseded by Status (head) | `report.history.md` |
| Setup | trees, builds, case, scripts | archival | `report.history.md` |
| Which scheme touches which tracer (this tree, p8_ugwpv1, Thompson) | scheme-to-tracer map, test tracers, IC, chem-PBL test hook | archival | `report.history.md` |
| Meters (`meters/02_meters_ccpp-physics.diff`, `meters/03_meters_fv3.diff`) | meter design and points | archival | `report.history.md` |
| Per-term attribution (24 h sum / initial mass; [rms of the per-step term]) | per-term 24 h mass table, base vs FV2 | current | `report.md` |
| Defects and fixes | parent heading | archival | `report.history.md` |
| FV2 (candidate): physics conversion divides and multiplies by different layer masses | FV2 code, fix, meter, red team (SERIES row 05) | current | `report.md` |
| Remaining terms (with FV2), and why they are round-off | residual round-off terms | current | `report.md` |
| Finding T1 (not a mass defect; not fixed): SAMF deep convection moves tracers with Courant numbers up to 5 | T1 symptom, meters, cause | superseded by F3. T1 red team and SERIES row 27 | `report.history.md` |
| Uniform tracers (case c) | dry-ratio drift of uniform tracers | superseded by F2. Dry-mole-fraction consistency of pt_udry, per process, and `trunif/report.md` (step-1 attribution corrected) | `report.history.md` |
| Follow-ups (coordinator, 17 Oct evening) | regenerated diffs; FV2 called a bug fix | archival | `report.history.md` |
| F1. Unmodified develop (@112b1d46) vs base (develop + water set), same hook + meters | develop vs base: SAMF loss removed by SA1 | current | `report.md` |
| F2. Dry-mole-fraction consistency of pt_udry, per process | dry-ratio spread per process, mechanism, proposed dry transport | superseded by `trunif/report.md` and SERIES rows 28, 30 | `report.history.md` |
| F3. T1 red team | causal sub-step test, dt 180, Courant histogram | superseded by SERIES row 27 (`trsamf/`, `trred/`) | `report.history.md` |
| F4. May drift — explained | May drift is an accounting trap | current | `report.md` |
| F5. Which configurations PBL-mix a GHG (trans_aero) — and does T1 hit it | configurations exposed to T1 in develop | superseded by SERIES row 27 (T1 fixed) | `report.history.md` |
| Incident (process) | `field_table` written through a shared symlink | archival | `report.history.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
