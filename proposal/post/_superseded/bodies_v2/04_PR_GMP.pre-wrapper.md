## Description of Changes:
Two bug fixes in GFDL MP v3, one commit each. Both change answers in the GFDL MP v3 suites.

| Fix | What goes wrong | Effect (`control_iovr4_gfdlmpv3`) |
|---|---|---|
| Mass basis | Species are converted to mixing ratio with `1/(1 − q_v)`, but back with `1/(1 + r_v)` using the updated vapour, so the round trip changes the water the host holds | The bug creates 1.03 % of the microphysics precipitation; with the fix the water residual is at round-off. Mean T +0.001 K, precipitation +0.15 % |
| Sedimentation heat | Falling rain and cloud water carry heat with the heat capacity of ice (`c_ice`), not liquid (`c_liq`) | Energy residual (GFDL's frame, with water potential energy) +0.20 → −0.007 W/m². Mean T −0.003 K |

## Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR, the SAMF/PBL fixes and the Noah-MP fixes, 27 October 2026 (develop 3e48f4cc, baselines 20261022): all 54 builds compile; 116 tests are identical, 101 change answers, and 15 restart/IAU tests did not start because their parent tests change answers; none fails to run. The log will be in the ufs-weather-model PR that follows review. Effects are from budget meters added to the model (C96, 24 h).

## Dependencies:
None. Companions: #406 and #407 fix the same mass-basis bug in Thompson and the TEMPO driver. The ufs-weather-model PR, with the RT log, follows review.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
