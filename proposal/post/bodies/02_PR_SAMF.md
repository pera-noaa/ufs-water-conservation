## Description of Changes:
Four bug fixes, one commit each. All change answers.

| Fix | Bug | Effect |
|---|---|---|
| Ice fusion heat | detrained condensate turns to ice with no heat of fusion | −0.42 W/m² (deep), −0.018 (shallow) → 10⁻¹³; +0.016 K at 500–200 hPa |
| Wet deposition | booked with `eta(k-1)`, removed with `eta(k)`; erased in the borrowing branch | scavenged tracer + deposition −7.4 × 10⁻⁴/day → 3 × 10⁻¹⁵ |
| PBL surface fluxes | `satmedmfvdifq` applies kinematic fluxes with `1/Δz` instead of `ρ_a g/δp` | `FV3_GFS_v16` water 2.6 × 10⁻⁸ → 4 × 10⁻¹⁶ kg/m²/day; last-bit in P8 |
| CA trigger | six early returns before `ca_trigger` can re-enable a column | `control_p8_mynn` 3×8 vs 4×6: 90/126 variables differ → 0 |

New argument: `hfus` (`latent_heat_of_fusion_of_water_at_0C`, already provided by the hosts).

## Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD ([RT 0b]). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

## Dependencies:
ufs-community/ufs-weather-model#TBD

Overlaps ufs-community/ccpp-physics#390 in one block; whichever merges second needs a rebase. Ours onto #390 is ready.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#TBD

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
