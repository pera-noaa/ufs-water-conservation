## Description of Changes:
Two bug fixes in GFDL MP v3, one commit each. Both change answers in the GFDL MP v3 suites.

| Fix | What goes wrong | Effect (`control_iovr4_gfdlmpv3`) |
|---|---|---|
| Mass basis (wrapper) | GFDL MP returns specific ratios of its updated layer mass, and the `delp` to match; the wrapper discards that `delp`, so the host applies the ratios to its pre-physics layer mass | The bug creates 1.03 % of the microphysics precipitation; with the fix the water residual is at round-off. Mean T +0.001 K, precipitation +0.15 % |
| Sedimentation heat (`terminal_fall`) | Falling rain and cloud water carry heat with the heat capacity of ice (`c_ice`), not liquid (`c_liq`) | Energy residual (GFDL MP's constants, with the water's potential energy) +0.20 → −0.007 W/m². Mean T −0.003 K |

The mass-basis fix rescales the returned species by `delp_out/delp_in` in the wrapper, so `gfdl_cloud_microphys_v3_mod.F90` keeps GFDL's mass handling. The sedimentation bug is also in GFDL's own `gfdl_mp.F90`: NOAA-GFDL/GFDL_atmos_cubed_sphere#430.

## Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR, the SAMF/PBL fixes (#408) and the Noah-MP fixes (#409, #410), 27 October 2026 (develop 3e48f4cc, baselines 20261022): all 54 builds compile; 116 tests are identical, 101 change answers, and 15 restart/IAU tests did not start because their parent tests change answers; none fails to run. The log will be in the ufs-weather-model PR that follows review. Effects are from budget meters added to the model (C96, 24 h).

## Dependencies:
None. Companions: #406 and #407 fix the same mass-basis bug in Thompson and the TEMPO driver. The ufs-weather-model PR, with the RT log, follows review.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
