## Description of Changes:
Four bug fixes in `mp_thompson` and `module_mp_thompson`, one commit each. Each bug makes Thompson create or remove water. Sizes below are fractions of grid-scale precipitation (C96 `control_p8_ugwpv1`, 24 h).

| Fix | What goes wrong | Water the bug creates (+) or removes (−) |
|---|---|---|
| Mass basis | Humidity is converted to mixing ratio with `1/(1 − q_v)`, but back with `1/(1 + r_v)` using the updated vapour | −0.4 % |
| Graupel | Graupel gains are not recomputed after the rate limiters | +0.76 % in the first 6 h, +0.03 % after |
| Density | Air density is recomputed after latent heating, before sedimentation | −0.11 % |
| Layer depth | Layer thickness comes from heights computed before convection; it now uses `prsi` (already provided by the hosts) | −0.014 % |

The effect is larger in the short, high-resolution regional tests (3 km, 1–6 h cold starts). Precipitation with the four fixes, together with the TEMPO driver fix (which acts only in TEMPO suites):

| Test | Precipitation |
|---|---|
| `regional_spp_sppt_shum_skeb` | −5.3 % |
| `cpld_regional_atm_fbh` | −3.0 % |
| `conus13km_gl_inline` | −2.5 % |
| `regional_control`, `gnv1_nested` | −1.4 % |
| HRRR/RAP debug (1 h) | −0.9 to −1.3 % |

Most of this is the graupel fix (−1.0 to −4.1 % alone) and the mass basis (up to −2.0 %): water the bugs created during spin-up. Noise from a one-bit perturbation is ≤ 0.24 %.

Three more Thompson fixes follow in a separate PR, because each has a second reasonable form: cloud water settling out of the lowest layer, clipped condensate, and water at or below the `R1` threshold.

## Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR and the TEMPO driver fix, 23 October 2026 (develop 5651397d, baselines 20261016): all 54 builds compile; 57 tests are identical, 150 change answers, and 25 restart tests did not start because their parent tests change answers; none fails to run. The log will be in the ufs-weather-model PR that follows review. Effects are from budget meters added to the model.

## Dependencies:
None. The ufs-weather-model PR, with the RT log, follows review.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
