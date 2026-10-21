## Description of Changes:
Seven fixes in `mp_thompson`/`module_mp_thompson`, one commit each. Sizes are fractions of grid-scale precipitation.

| Fix | Bug | Effect |
|---|---|---|
| Mass basis | humidity converted in with `1/(1-q_v)`, back with `1/(1+r_v,new)` | removes 0.4 % |
| Settling | cloud water leaving the lowest layer not counted as precipitation; cloud sedimentation not substepped | removes 0.15 % |
| Graupel | graupel gains not recomputed after the rate limiters | creates 0.76 % (first 6 h) |
| Density | density recomputed after latent heating, before sedimentation | removes 0.11 % |
| Layer depth | `dz` from heights computed before convection | removes 0.014 % (new argument `prsi`, already in the hosts) |
| Clipping | clipped condensate deleted; vapour floor filled from nothing | creates 0.002 % |
| R1 threshold | hydrometeors at or below R1 deleted | removes 2 × 10⁻⁸ |

In the regional and convection-allowing tests (3 km, 1–6 h cold starts), each fix alone on `develop`:

| Test | Precipitation, whole PR | Attribution |
|---|---|---|
| `regional_control` | +9.2 % | counting settled cloud water +10.9 % (3-D T +0.0008 K: reported, not state) |
| `regional_spp_sppt_shum_skeb` | −5.3 % | graupel −4.1 %, mass basis −1.6 % |
| `conus13km_gl_inline`, `gnv1_nested` | −2.4 %, −2.6 % | graupel −2.1 %, −1.1 % |
| `cpld_regional_atm_fbh` | −2.6 % | mass basis −2.0 %, graupel −1.1 % |
| HRRR/RAP debug (1 h) | −0.9 to −1.4 % | graupel −1.0 to −1.4 % |

Noise (one-ulp perturbation): ≤ 0.24 %. The graupel fix removes water created during spin-up, largest in these short cold starts (0.76 % in the first 6 h at C96). The cloud sedimentation substepping changes precipitation by ≤ 0.23 % except `gnv1_nested` (−1.2 %).

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
