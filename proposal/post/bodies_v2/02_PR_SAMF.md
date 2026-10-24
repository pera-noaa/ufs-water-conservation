## Description of Changes:
Four bug fixes in SAMF convection and the `satmedmfvdifq` PBL, one commit each. All change answers.

| Fix | What goes wrong | Effect |
|---|---|---|
| Ice fusion heat (deep and shallow) | Detrained condensate is split into ice without releasing the heat of fusion | Deep convection loses 0.42 W/m² (shallow 0.018); with the fix, 10⁻¹³. The upper troposphere (500–200 hPa) warms 0.016 K. |
| Wet deposition (deep) | Scavenging is booked with `eta(k−1)` but removed with `eta(k)`, and is erased in the negative-value borrowing branch | Scavenged tracer and deposition do not add up: −7.4 × 10⁻⁴ per day → 3 × 10⁻¹⁵ |
| PBL surface fluxes (`satmedmfvdifq`) | Kinematic surface fluxes are applied with `1/Δz` instead of the layer mass, `ρ g/δp` | `FV3_GFS_v16`: water 2.6 × 10⁻⁸ → 4 × 10⁻¹⁶ kg/m²/day; last bit only in P8 |
| Cellular-automaton trigger (deep) | Six early returns can exit before `ca_trigger` switches a column back on, so results depend on the domain decomposition | `control_p8_mynn`, layout 3×8 vs 4×6: 90 of 126 variables differ → 0 |

New argument: `hfus` (`latent_heat_of_fusion_of_water_at_0C`, already provided by the hosts).

## Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR, the Noah-MP fixes and the GFDL MP v3 fixes, 23 October 2026 (develop 5651397d, baselines 20261016). [RT 0b] The log will be in the ufs-weather-model PR that follows review. Effects are from budget meters added to the model (C96 `control_p8_ugwpv1`, 24 h).

## Dependencies:
Rebased onto `ufs/dev` after #390; one block in `samfdeepcnv.f` was re-resolved around its `progomega` guards. #403 adds arguments to `samfdeepcnv_run` beside ours (`hfus`); whichever merges second needs a one-block rebase. The SAMF cloud-base fix is separate (#405).

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
