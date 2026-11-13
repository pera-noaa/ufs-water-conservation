## Description of Changes:
One bug fix in the TEMPO driver (`mp_tempo`). It has the same mass-basis bug as `mp_thompson`, fixed in #406: species are converted to mixing ratio with `1/(1 − q_v)` and back with `1/(1 + r_v)` using the updated vapour, while the host rebuilds the layer mass from the old `q_v`. The fix uses the input humidity in both directions.

| Test | Precipitation |
|---|---|
| `regional_wofs_tempo` (3 km) | −1.96 % (noise 0.34 %) |

Where there is net condensation, the old round trip created water, so the fix lowers precipitation there.

The fix also exposes TEMPO's own water residual (+0.33 % of grid-scale precipitation in `control_p8_ugwpv1_tempo`), which the driver error was cancelling. Fixes for that are proposed to NCAR/TEMPO separately.

## Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR and the Thompson fixes, 23 October 2026 (develop 5651397d, baselines 20261016): all 54 builds compile; 57 tests are identical, 150 change answers, and 25 restart tests did not start because their parent tests change answers; none fails to run. The log will be in the ufs-weather-model PR that follows review.

## Dependencies:
Companion of #406 (Thompson, same bug); the two are independent and can merge in either order. Overlaps #389 in one block; whichever merges second needs a one-block rebase. Ours onto #389 is ready.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

