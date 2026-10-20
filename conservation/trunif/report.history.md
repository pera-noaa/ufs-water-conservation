*History of `report.md` (trunif), moved verbatim on 18 October 2026. The head is `report.md`.*

# Uniform-tracer structure: which process generates it (trunif)

## Status (2026-10-17, done)
- Shadow meter (4 tracers reset to exact uniformity before every process) and tagged tracers (one per generator) built
  and run (`sh1` 10152286, `tg1` 10152328, C96 control_p8_ugwpv1, 64-bit, dt 720, 24 h). Both runs are bit-identical to
  the tracer agent's `tm5`: all 2520 TM lines (air + 16 tracers incl. water and every pt_*, 17 digits, every point and
  step) and atmf024 tmp/spfh/clwmr/dpres/ugrd/pt_* identical. Shadows and tags feed back into nothing.
- From an exactly uniform state only five processes create dry-ratio structure. Three are physics transports and create
  it by a frame inconsistency (class a). Two are the dycore's per-species limiters (class c). IC processing adds a small
  one-off (class d). Table below.
- Every scheme preserves a constant in its own basis: physics-basis constant through SAMF deep/shallow and PBL ≤ 2.2e-14
  per call (including Courant up to 5); moist constant through advection/remap ≤ 4.4e-16. The tracer agent's
  "a constant field would be preserved" by SAMF is now verified.
- Correction to `tracer/report.md` "Uniform tracers": the −0.9 %/+0.4 % after step 1 is step 1's SAMF deep (+shallow), not
  the IC. external_ic leaves max 9.0e-5 and adiabatic_init max 3.4e-4.

## Minimal fixes (none implemented here)
- **Class a (SAMF deep, shallow, PBL).** Physically, a dry-uniform tracer must stay uniform: convection and turbulence
  move moist air at fixed pressure layers, so dry air moves too. Two consistent remedies:
  - **Recommended, minimal:** move non-water tracers with the dry air inside the physics, as the write-back assumes.
    Transport c = q/(1−qv_in) with dry layer masses D = dp(1−qv_in) and fluxes scaled by one interface dry fraction
    (zero net dry flux). This is trsamf's TRSAMF_DRY. PHYSICS CHANGE, ~1 % on every chemistry tracer.
  - **Alternative:** make the write-back move dry air, D' = D − (transport part of Δqv)·dp. This needs a passive copy of
    qv through the transports and changes ps/T/dynamics everywhere. Not recommended.
- **Class c (advection, remap).** Build each tracer's flux from the dry-air flux: total mass flux minus the sum of the
  actually limited water-species fluxes, times dry-ratio face values. That keeps a uniform c and tracer mass exactly.
  - Same idea for remap: remap c over dry-pressure thickness.
  - This is a numerics change to tracer_2d/mapz; it is not small to implement.
  - Effect: rms 2.3e-5 (≈0.01 ppm CO2), max 1.2e-3 (≈0.5 ppm) at 24 h. That matches trsamf's fxe3 residual (rms
    2.3e-5, max 1.2e-3).
- **Class d (IC).** Give GHG ICs as a dry mole fraction and convert with the model's water after adiabatic_init. Or
  restore the non-water tracers' dry ratio after adiabatic_init, whose purpose is balancing the dynamics, not advecting
  tracers. Max 3.4e-4 once.
- **Class b (T1).** Sub-step SAMF's tracer update, or bound xmb by a Courant limit (trsamf task 2).

## Method
- **Shadow tracers.** Four extra field_table tracers, chemistry type, so SAMF and the PBL treat them like pt_udry:
  - `sh_d`: c0(1−Σw);
  - `sh_m`: c0;
  - `sh_p`: c0 per dry+vapour mass;
  - `sh_v`: Σw in the dycore, qv_in in the physics.
- **Reset and measure.** At 18 points per step each shadow is measured, then reset:
  - dycore A–H around dyn_core+tracer_2d, remap, neg_adj3, fv_subgrid_z;
  - physics: statein; GWD_post before and after it applies the PBL tendency (the PBL acts on qgrs); after DCNV_post and
    after SCNV_post apply their tendencies; at the write-back;
  - after fv_update_phys.
- **Recorded per point.** Dry-mass-weighted MS, max, level and lat/lon. Physics references are taken from qgrs: dry
  mass D = dp(1−qv_in), as the write-back keeps it.
- **Tags.** tg_adv/rmp/pbl/dcv/scv start dry-uniform. After every metered process except their own, the shadow's
  departure dev_P is subtracted in dry-ratio space: q −= dev_P·c0(1−Σw). This is mass-neutral, since Σ D·dev_P = 0.

## Files
- **Local `scripts/`:**
  - `tm_shadow.inc`, `instrument_shadow.py`: shadow meter, applied after the tracer agent's hook, meters and reset;
  - `instrument_tags.py`: tags;
  - `make_rundir.sh`: tracer agent's script with dst in trunif, the shadows and env TAGS added, job prefix tu_;
  - `analyze_sh.py`, `compare_tm.py`: bit-identity through the TM lines, with srun labels and line wrapping undone;
  - `pfull.py`, `mkdiff.sh`.
- **`meters/05_shadow_tags_meter.diff`:** shadow + tags on top of the tracer agent's 01–03.
- **Results:** `sh1_sh_analysis.txt`, `tg1_sh_analysis.txt`, `tg1_TG.txt`.
- **Hercules `$W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trunif`:** `sh/` tree (exe `tests/fv3_tu_sh_v1.exe`
  = shadow only, `fv3_tu_tg.exe` = shadow + tags), `rt/sh1`, `rt/tg1` (`out`, `sh_analysis.txt`), `bin/`.
