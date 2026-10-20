# Coupling water enthalpy and Kirchhoff consistency (D2, D5) — encpl

*Written by the coordinator from the agent's round-2 hand-off (the agent declined to write report files).*

## Status

encpl's three diffs are in the final series (`replay/SERIES.md`); all are PHYSICS CHANGE (PC), default off.

| Row | Diff | Switch: default / all-on | Before → after (W m⁻², 24 h) |
|---|---|---|---|
| 13 | `13_C1.diff` (`patches/04_fv3-cpl_water_energy.diff`) | `cpl_water_energy` 0 / 15 (bits 1 PE, 2 flow work, 4 sensible; 8 = C8, energy) | coupling thermodynamic residual +0.673 → −1.4e-12 (bits 1+2+4) |
| 14 | `14_K1.diff` (`patches/05_…`) | `thompson_kirchhoff` F / T | Thompson Kirchhoff remainder +0.028 → 0 |
| 15 | `15_S1_export.diff` (`accepted/10r` = `patches/06_…` rebased) | `samf_kirchhoff` F / T; export under bits 1, 4 | SAMF Kirchhoff remainder deep −0.245, shallow +0.128 (completed by S1K, row 17) |

- Frame F is FV3's own total energy plus Σm(Lv00·qv − Li00·qice); its definition is in "Frame F" of the original
  Status (`report.history.md`) and in the proposal's Method.
- Impact, all bits: LH −2.04 W m⁻², precipitation −3.4 %; bit 2 alone LH −1.97 W m⁻². Off is bitwise; 3×8 = 4×6.
- **Red team (fwred): flow work HOLDS WITH QUALIFICATIONS.** It is ±R_v·T on every vapour mass change at fixed delz;
  the net is a sink, −0.62 W m⁻². A forecast improvement is not shown.
- **Decided:** `cpl_water_energy` is opt-in, default 0 (proposal §15). The round-1 Kirchhoff remainder +0.665 was a
  heuristic; measured with species fluxes it is −0.013 W m⁻².
- History: [`report.history.md`](report.history.md) holds the original Status block, verbatim.

## Red team (fwred, `fwred/report.md`): CLAIM HOLDS WITH QUALIFICATIONS

- Mechanism confirmed independently: L_h = L_e + R_v·T, the R_v·T being work the overlying column does as the layer's
  gas shrinks. `atmosphere_state_update` rebuilds delp and never touches delz; with `phys_hydrostatic=.false.`
  `fv_update_phys` keeps delz fixed (moist_cv), so the column's later settling releases that work a second time. 1-D
  compressible column with acoustic relaxation (energy-conserving to 0.6 J/m²), 1 g/kg condensed: isobaric 2.474 K;
  fixed volume with L_e, relaxed 2.471 K; FV3 path relaxed 2.596 K → excess 1.257e5 J/kg (R_v·T0 = 1.261e5).
  `phys_hydrostatic=.true.` rescales delz by T but not by gas content: also double-counts. Hydrostatic dycore: consistent.
- **Sign and scope (correction):** the error is ±R_v·T on EVERY vapour mass change at fixed delz, not only condensation.
  Condensation aloft gains +R_v·T; surface vapour entering the boundary layer misses R_v·T. Gross each ~4 W m⁻²; the net
  is a SINK, FW = −R_v·Σdm_v·T = −0.62 W m⁻². Bit 2 therefore adds +0.62 W m⁻² net and mostly moves heat from the
  mid-troposphere into the boundary layer (consistent with −0.06 K mid / +0.05 K low).
- GFDL MP (nonhydrostatic): lv00 = hlv − (cv_vap − c_liq)·tice; slope right, a constant +R_v·tice (1.26e5 J/kg) offset.
  Its hydrostatic setting is consistent.
- −3.4 % precipitation is the all-bits result; bit 2 alone: LH −1.97 W m⁻².
- Class: PHYSICS CORRECTION to the coupling convention; a forecast improvement is not shown. No real-model column test
  (rests on FV3's dynamics conserving E_F as the column settles; the fixer moves only 0.006 W m⁻² between bits 0 and 7).
- Lauritzen et al. 2022 §4.5.2 covers only the cp/cv rescaling; it neither supports nor contradicts the R_v·T term.

## D2 split, frame F, W m⁻², 24 h

| term | flags off, round 1 (mc0) | flags off, species fluxes (prm0) | all bits (prm7) |
|---|---|---|---|
| D2_F (frame E_D: +1.30) | +3.803 | +3.803 | +4.511 |
| (a) boundary enthalpy | +3.145 | +3.145 | +3.996 |
| PE (net; gross 1.47, vapour −0.99) | −0.480 | −0.480 | applied |
| flow work | −0.620 | −0.620 | applied |
| sensible exchange | +1.095 (heuristic) | +1.773 | applied |
| Kirchhoff remainder | +0.665 | −0.013 | −0.021 |
| K (momentum, with D7) | −0.0025 | −0.0025 | −0.0024 |
| thermodynamic residual | −0.005 | +0.673 | −1.4e-12 |

Checks against eb_state agree to ≤ 2e-10.

## Impact at 24 h vs the noise control (T rms 0.150 K, band means ≤ 5e-4 K)

| change | class | effect |
|---|---|---|
| bit 1 (PE, Pauluis) | PHYSICS (missing term) | +0.02 K, precipitation +0.8 % |
| bit 2 (flow work) | PHYSICS CORRECTION (latent heat convention) | −0.06 K mid / +0.05 K low, LH −1.97 W m⁻² |
| bit 4 (sensible exchange) | PHYSICS (missing term) | −0.04 K, LH −0.31 W m⁻², precipitation −1.3 % |
| all bits | | LH −2.04 W m⁻², precipitation −3.4 % |
| K1 `thompson_kirchhoff` | PHYSICS OPTION | noise; Thompson gap 220–250 K: deposition −0.14 %, condensation −0.24 %, freezing +1.3 % of its heat |
| S1 `samf_kirchhoff` | PHYSICS OPTION | +0.013 K, LH +0.22 W m⁻², precipitation +0.6 % |

## Files
Patches `04_fv3-cpl_water_energy.diff`, `05_ccpp-thompson_kirchhoff_option.diff`, `06_*` (S1 / species-flux export),
`meter_cpl_thompson.diff`, `meter_r2.diff` in `patches/`; tools (`column_fw.py`, `cpl_table.py`, `lev_diff.py`,
`impact.sh`) in `tools/`; runs in `$U/cons/encpl/runs`.
