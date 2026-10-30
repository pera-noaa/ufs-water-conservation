## Description of Changes:
Four bug fixes in Noah-MP and the code that couples it to the atmosphere, one commit each. All change answers in suites that use Noah-MP. This PR builds on #409, whose three commits appear here until it merges.

@barlage @cenlinhe, all four commits change Noah-MP's own files; I'd welcome your review.

| Fix | What goes wrong | Effect |
|---|---|---|
| Evaporation hand-off (`noahmpdrv`) | The atmosphere receives Noah-MP's latent heat divided by the host's `con_hvap`, not the water Noah-MP removed; the two use different latent heats | The atmosphere gains 0.07–0.10 % of global precipitation more water than the land loses |
| Snow layer heat (3 commits: `combine`, `csnow`, `combo`) | Merged layers keep the receiver's temperature, and layers that vanish drop their heat; `csnow` builds heat capacities from capped volume fractions, and `combo` uses per-volume heat capacities with layer masses | Noah-MP's soil energy residual 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ W/m², measured with a thin-snow fix that comes later |

Notes:
- Evaporation: Noah-MP removes water with its own `hvap` and, over frozen surfaces, `hsub`, so the atmosphere received 0.4 % more water than unfrozen land lost and 14 % more over snow and frozen ground. The new flux is the one the WRF, HRLDAS, MPAS and LIS drivers pass (`QFX`). Noah-MP's own latent heat flux is unchanged; the host's diagnostic `rho*con_hvap*evap` now follows the water and is up to 12 % lower where sublimation dominates. See also NCAR/ccpp-physics#582.
- Snow layer heat: with all three and the layer-count fix in #409, the temperature rms difference is 0.147 K and land fields are at noise. `combo` now matches CTSM's `Combo` (`SnowHydrologyMod.F90`), which uses per-kg heat capacities. NCAR Noah-MP v5 has the same three defects; the same fixes for v5 are in NCAR/noahmp#274.

Related fixes come later, separately: those where the destination of the water or heat is a judgement (truncated thin snow, truncated canopy water, the heat of a melted-out snow layer, and Noah-MP's own latent heats).

## Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR (including #409), the SAMF/PBL fixes (#408) and the GFDL MP v3 fixes, 27 October 2026 (develop 3e48f4cc, baselines 20261022): all 54 builds compile; 116 tests are identical, 101 change answers, and 15 restart/IAU tests did not start because their parent tests change answers; none fails to run. The log will be in the ufs-weather-model PR that follows review. Effects in the table are from budget meters added to the model (C96 `control_p8_ugwpv1`, 24 h).

## Dependencies:
#409. The ufs-weather-model PR, with the RT log, follows review.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
