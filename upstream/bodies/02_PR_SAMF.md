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
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD (Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 116 tests identical, 101 change answers, 15 restart/IAU children not started (their parents change answers); none fails to run). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

## Dependencies:
ufs-community/ufs-weather-model#TBD

Rebased onto `ufs/dev` after ufs-community/ccpp-physics#390 (one block in `samfdeepcnv.f` re-resolved around its `progomega` guards). #403 adds arguments to `samfdeepcnv_run` beside ours (`hfus`); whichever merges second needs a one-block rebase.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
