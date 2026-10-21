## Description of Changes:
| Fix | Bug | Effect (`control_iovr4_gfdlmpv3`) |
|---|---|---|
| Mass basis | in with `1/(1-q_v,in)`, back with `1/(1+q_v,new)` | removes 1.03 % of microphysics precipitation |
| Sedimentation heat | rain and cloud water fall with `c_ice` | +0.20 → −0.007 W/m² |

## Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD ([RT 0b]). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

## Dependencies:
ufs-community/ufs-weather-model#TBD

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#TBD

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).
