## Description of Changes:
Four fixes in `mp_thompson`/`module_mp_thompson`, one commit each. Sizes are fractions of grid-scale precipitation.

| Fix | Bug | Effect |
|---|---|---|
| Mass basis | humidity converted in with `1/(1-q_v)`, back with `1/(1+r_v,new)` | removes 0.4 % |
| Graupel | graupel gains not recomputed after the rate limiters | creates 0.76 % (first 6 h) |
| Density | density recomputed after latent heating, before sedimentation | removes 0.11 % |
| Layer depth | `dz` from heights computed before convection | removes 0.014 % (new argument `prsi`, already in the hosts) |

In the regional and convection-allowing tests (3 km, 1–6 h cold starts), the four fixes on develop (with the TEMPO driver fix, which acts only in TEMPO suites):

| Test | Precipitation |
|---|---|
| `regional_spp_sppt_shum_skeb` | −5.3 % |
| `cpld_regional_atm_fbh` | −3.0 % |
| `conus13km_gl_inline` | −2.5 % |
| `regional_control`, `gnv1_nested` | −1.4 % |
| HRRR/RAP debug (1 h) | −0.9 to −1.3 % |

Each fix alone: the graupel re-closure −1.0 to −4.1 %, the mass basis up to −2.0 %, the others ≤ 1.1 %: water these terms created.

Noise (one-ulp perturbation): ≤ 0.24 %. The graupel fix removes water created during spin-up, largest in these short cold starts (0.76 % in the first 6 h at C96).

Three more Thompson water fixes follow in a separate PR, because each has a second reasonable form: cloud water settling out of the lowest layer, clipped condensate, and water at or below R1.

## Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD ([RT 0c]). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

## Dependencies:
ufs-community/ufs-weather-model#TBD

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#TBD

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
