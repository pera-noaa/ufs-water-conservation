## Description of Changes:
The TEMPO driver has the same mass-basis bug as `mp_thompson` (fixed in ufs-community/ccpp-physics#TBD): species are converted to mixing ratio with `1/(1-q_v)` and back with `1/(1+r_v,new)`, while the host rebuilds the layer mass from the old `q_v`. One commit; uses the input humidity in both directions.

This fix exposes TEMPO's own water residual (+0.33 % of grid-scale precipitation in `control_p8_ugwpv1_tempo`), which the driver error was cancelling. Fixes for that are proposed to NCAR/TEMPO separately.

`regional_wofs_tempo` (storm scale, 3 km): precipitation −1.96 % (noise 0.34 %). With net condensation the old round trip created water, so the fix lowers precipitation where condensation dominates.

## Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD (Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 57 tests identical, 150 change answers, 25 restart children not started (their parents change answers); none fails to run). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

## Dependencies:
ufs-community/ufs-weather-model#TBD

Overlaps ufs-community/ccpp-physics#389 in one block; whichever merges second needs a rebase. Ours onto #389 is ready.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
