## Description of Changes:
Twelve fixes in Noah-MP and its interstitials, one commit each.

| Fix | Bug | Effect |
|---|---|---|
| Once per time step | with `frac_grid`, coastal land is re-flagged and stepped again on the second surface iteration (24–27 % of land, every step) | land gains 3–5 % of global precipitation |
| Evaporation hand-off | latent heat ÷ a different constant | atmosphere gains 0.07–0.10 % of global precipitation |
| Coastal snow (`frac_grid`) | land snow overwritten with the cell mean every step | thin coastal snow lost |
| Snow initialisation | cold-start snow layers built from the cell-mean snow | 0.29 kg/m² land snow lost at step 1 |
| Thin snow | snow < 10⁻³ mm without layers deleted | 0.009 % of global precipitation |
| Canopy truncation | canopy water ≤ 10⁻⁶ mm deleted | 4 × 10⁻⁷ of land precipitation |
| Latent heats | Noah-MP's own constants, not the host's | land pays 0.4 % more latent energy than its vapour carries |
| `combine` count | tests `isnow_old`, not `isnow` (NCAR/noahmp#47) | per firing up to 0.16 mm water, 8.5 MJ/m² |
| Melt-out heat | leftover heat deleted when the layer below is frozen | did not fire in the test case |
| Snow layer heat (3 commits) | merge keeps receiver's T; capped volume fractions; m⁻³ capacities used per kg | Noah-MP soil energy residual 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ W/m² |

The once-per-step fix adds an optional last argument `iter` (`ccpp_loop_counter`) to `noahmpdrv_run`.

## Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD ([RT 0b]). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

## Dependencies:
- NOAA-EMC/noahmp#TBD (its copy of the driver must declare `iter`, or `control_p8_atmlnd` crashes)
- ufs-community/ufs-weather-model#TBD (7a; bumps NOAHMP-interface too)

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#TBD

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
