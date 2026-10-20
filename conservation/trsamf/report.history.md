*History of `report.md` (trsamf), moved verbatim on 18 October 2026. The head is `report.md`.*

# SAMF/PBL passive-tracer transport: SA1 causal check, T1 fix, dry-ratio consistency

## Status (2026-10-17, 21:00 CDT) - tasks 1-4 done
- **T-SA1 (task 1)**: develop + SA1 only (`sa1r`) puts SAMF deep/shallow at round-off for every tracer (|dM| <= 1.3e-18/day;
  develop -2.02e-2 pt_cnv). A meter of the cloud-base defect formula equals the develop DCNV and SCNV changes to 6 digits
  for every tracer (`dvm1`). Chemistry path = same arithmetic (fscav=0): with the chem tracers' PBL tendency discarded
  (`dvm2`) pt_ghg == pt_cnv bitwise; the 1500x difference is PBL mixing at cloud base. Text for the proposal below.
- **T1 fix (task 2)** `patches/02_T1_samf_tracer_substep_donor_source.diff` (deep + shallow): sub-steps the tracer transport
  to donor Courant <= 0.5 and starts tracer parcels from the donor layer. pt_umoist 24 h range 0/216x -> 0.989/1.015;
  mass to round-off; with the fix restricted to passive tracers T,q,qc,dp,u,ps bit-identical (`fxf2`). Sub-stepping
  alone leaves a growing 2-layer dipole (0.75/1.25), see generator 3.
- **DRY fix (task 3)** `patches/03_DRY_chem_tracers_dry_mixing_ratio_transport.diff` (on T1; SAMF deep, shallow,
  satmedmfvdifq): exact. With pt_udry reset exactly uniform before every physics step (`fxf4`) every physics slot keeps it
  uniform to 2e-14 (unfixed `fxf6`: 1.0e-2 in one step); mass to round-off; T,q bit-identical. 24 h pt_udry rms dev
  1.07e-3 -> 2.3e-5, max 1.2e-2 -> 1.0e-3; the residual is made by the FV3 dycore, not physics.
- **Classification (task 4)**: SA1 BUG FIX; T1 sub-stepping BUG FIX (restores the explicit TVD update's stability
  bound); donor-layer parcel source PHYSICS CHANGE (tracer-only design change); DRY PHYSICS CHANGE.
- Clean patch builds (`fct1`, `fcd1`) are bit-identical to the env-switched test runs (`fxf1`, `fxf3`).
- Open: see end. Not done: restart/decomposition/32-bit red team of T1/DRY (both are column-local and stateless).
- **Generators of structure in uniform fields (for trunif):**
  1. FV3 dycore `dyn_core`+`tracer_2d_1L` (meter points 2->3): from an exactly uniform dry ratio (rms 1.1e-17) the first
     call gives rms 1.1e-6, max|dev| 1.08e-4; remap adds up to 8e-5/step. With the DRY fix this is the only source
     (24 h dMS dyn_core+tracer_2d +1.15e-9, remap +4.0e-10; all physics slots <= 0).
  2. Physics in the moist basis, from exactly uniform input every step (`fxf6`, 24 h sum dMS): SAMF deep +6.26e-7,
     SAMF shallow +1.11e-7, **PBL +1.48e-7** (the PBL is a generator too; its net in free runs is negative only because it
     also mixes existing anomalies). DRY fix: all three <= 1e-29 (`fxf4`). So SAMF and satmedmfvdifq do preserve a
     constant in their own basis (to 2e-14 after 120 steps); the generator is the moist-vs-dry frame.
  3. SAMF cloud-base source convention: tracer parcels start from the interface mean ctro(kb) / ctro(jmin) and (with SA1)
     the kb face carries ctro both ways, so layer kb's own anomaly is invisible while the neighbour's value drives it:
     exponentially growing dipole in the lowest two layers of a non-PBL-mixed tracer (e-fold ~25 steps, 0.75/1.25 after
     24 h at 4.5N 155E, `fxe1`) even at Courant <= 0.5. Donor-layer sources remove it.

## Setup
- Hercules `$W=$U/cons/trsamf` (U=/work2/noaa/co2/ash/ufs-chem-v1/upstream); `bin/` = copy of the tracer agent's
  `$T/bin` + mine. Read-only inputs: `$T/base` (develop + water set), `$U/ufs-weather-model` (git-clean develop
  @112b1d46), `$T/ic` (six-tracer IC), RT template `$U/rt/wb_m19_di720`.
- `bin/mk_tree.sh <name> <src> [x.diff|x.py|post:x.py]`: copy tree, pre-items, then the tracer agent's hook +
  meters + uniform reset, plus `post_tx.py` (prints tm_meter's new `tm_x(100)` accumulators as `TX` lines).
- `bin/mkrun.sh <name> <exe> [VAR=VAL]`: run dir via (adapted) make_rundir.sh, exports VARs in job_card, submits.
- Trees: `sa1` = develop + `01_SA1` diff; `dvm` = develop + `hook_npc_env.py` + `meter_defect_dev.py`;
  `fxe` = base + `fix_trsamf.py exp`.
- Clean trees: `fct` = base + `fix_trsamf.py t1`; `fcd` = base + `fix_trsamf.py t1dry` (both + meters).
- Experimental tree `fxf` = base + `fix_trsamf.py exp` (env TRSAMF_T1=0/1/2, TRSAMF_SRC, TRSAMF_DRY, TRSAMF_CMAX) +
  `hook_reset_every.py` (TRSAMF_RESET: pt_udry exactly uniform before every physics step) + `meter_timing.py`.
  `fxe` = same without SRC/reset/timing. `dvm` rev2 adds `meter_shal_diag.py` (rev1 exe kept as fv3_dvm_rev1.exe).
- Analysis: `analyze_tx.py` (TX records wrap mid-number; parse with `txparse.py`, which joins continuation lines),
  `compare_ppm.py` (ppm-eq = difference x 400 ppm / field's global dp-weighted mean), `umoist_frame.py`, `col_profile.py`.

## Runs (24 h, C96L127, dt 720, 64-bit; all with hook + meters; `$W/rt/<run>`)
| run | exe / switches | purpose |
|---|---|---|
| sa1r | develop + SA1 | task 1 causal |
| dvm1 / dvm2 | develop + defect meter / + TRSAMF_NPC=1 | defect = slot; path equivalence |
| fxe0 | fxe, all off | == tracer agent's tm5 bitwise (control) |
| fxe1 / fxe2 | T1=1 / T1=2 (pt_* only), no SRC | sub-stepping alone |
| fxe3 | DRY=1 | dry fix alone |
| fxf1 / fxf2 | T1=1 SRC=1 / T1=2 SRC=1 | T1 fix (all tracers / passive only) |
| fxf3 | T1=1 SRC=1 DRY=1 | full fix |
| fxf4 / fxf6 | RESET=1 with T1=2 SRC=1 DRY=1 / RESET=1 only | uniform-input test, fixed / unfixed |
| fxf5 | T1=2 SRC=1 DRY=1 | full fix, passive only (T,q identity) + timing |
| fct1 / fcd1 | clean T1 / clean T1+DRY | == fxf1 / fxf3 bitwise |

## Task 4. Impact on tracers (24 h, ppm-equivalent of a 400 ppm scaling; vs unfixed fxe0; same weather unless noted)
| change | class | pt_ghg rms / max | pt_udry rms / max | pt_cnv (generic) rms | T, q, ... |
|---|---|---|---|---|---|
| SA1 (develop -> +SA1) | BUG FIX | mass -1.4e-5/day | | mass -2 %/day | (water proposal) |
| T1 sub-stepping, pt_* only (fxe2) | BUG FIX | 0.59 / 41 | 0.009 / 1.1 | 139 | bit-identical |
| + donor-layer source (fxf2) | PHYSICS CHANGE | 0.65 / 48 | 0.011 / 1.5 | 140 | bit-identical |
| DRY only (fxe3) | PHYSICS CHANGE | 0.59 / 8.7 | 0.41 / 4.9 (= the removed artefact) | 0 | bit-identical |
| T1 + DRY, pt_* only (fxf5) | | 0.77 / 49 | 0.41 / 4.9 | 140 | bit-identical |
| T1 + DRY as patched (o3, TKE also sub-stepped; fxf3) | | 4.3 / 161 (weather) | 0.42 / 4.9 | | T rms 0.168 K (perturbation pair tm3/tm4: 0.157 K) |
Patched run global means (T, q, ps) fall inside the three-member perturbation spread; global cloud water is +0.2 %
(4.167e-6 vs 4.153-4.159e-6), possibly real via TKE transport (not resolved with three members).

## Open questions
1. Apply T1 to TKE and ozone? The patch does (they have the same instability); it changes the forecast at the
   round-off-divergence level plus possibly +0.2 % global cloud water. Excluding them needs the ozone index in SAMF.
2. DRY covers chemistry tracers only; generic tracers stay moist and are not PBL-mixed (they still drift by surface
   water fluxes in the lowest layer). The PBL part relies on the chem tracers being the ntchm before TKE in vdftra.
3. Red team not done for T1/DRY: restart, layout, 32-bit SAMF (conv_wp), other suites (HAFS uses hwrf_samfdeep: block
   skipped), GOCART scavenging with fscav > 0 (scavenging is recomputed per sub-step; untested).
4. The dycore generator (1): FV3's tracer_2d/remap do not keep a uniform dry ratio (1e-4 per call) - for trunif.
5. Compiler sensitivity: adding inert diagnostic code to samfshalcnv changed answers once (dvm rev2 vs rev1), so
   bit-identity claims hold per build, not across builds; all identity claims above compare runs of one exe or builds
   verified identical.
