## Description of Changes:
Seven fixes in Noah-MP and its interstitials, one commit each.

| Fix | Bug | Effect |
|---|---|---|
| Evaporation hand-off | latent heat ÷ a different constant | atmosphere gains 0.07–0.10 % of global precipitation |
| Coastal snow (`frac_grid`) | land snow overwritten with the cell mean every step | thin coastal snow lost |
| Snow initialisation | cold-start snow layers built from the cell-mean snow | 0.29 kg/m² land snow lost at step 1 |
| `combine` count | tests `isnow_old`, not `isnow` (NCAR/noahmp#47) | per firing up to 0.16 mm water, 8.5 MJ/m² |
| Snow layer heat (3 commits) | merge keeps receiver's T; capped volume fractions; m⁻³ capacities used per kg | Noah-MP soil energy residual 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ W/m² (measured with the thin-snow fix, now held) |

Noah-MP's coastal land is also stepped twice per time step with `frac_grid`; that fix follows with its sea-ice twin (the same cause, two tested forms).

## Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD (Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 116 tests identical, 101 change answers, 15 restart/IAU children not started (their parents change answers); none fails to run). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

## Dependencies:
ufs-community/ufs-weather-model#TBD

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
