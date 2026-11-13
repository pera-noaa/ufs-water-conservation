## Description of Changes:
Seven bug fixes in Noah-MP and the code that couples it to the atmosphere, one commit each. All change answers in suites that use Noah-MP.

| Fix | What goes wrong | Effect |
|---|---|---|
| Evaporation hand-off (`noahmpdrv`) | The atmosphere receives Noah-MP's latent heat divided by the host's `con_hvap`, not the water Noah-MP removed; the two use different latent heats | The atmosphere gains 0.07–0.10 % of global precipitation more water than the land loses |
| Coastal snow (`GFS_surface_composites_pre`) | With `frac_grid`, the land's snow is overwritten with the cell mean every step | Thin coastal snow is lost; Noah-MP's water check goes from +5 kg/m² per 6 h to −6 × 10⁻⁵, measured with the time-step fix below |
| Snow initialisation (`GFS_phys_time_vary`) | With `frac_grid`, cold-start snow layers are built from the cell-mean snow | 0.29 kg/m² of land snow lost at the first step |
| Snow layer count (`combine`) | Tests `isnow_old` instead of `isnow` (NCAR/noahmp#47) | Up to 0.16 mm of water and 8.5 MJ/m² per occurrence |
| Snow layer heat (3 commits: `combine`, `csnow`, `combo`) | Merged layers keep the receiver's temperature, and layers that vanish drop their heat; `csnow` builds heat capacities from capped volume fractions, and `combo` uses per-volume heat capacities with layer masses | Noah-MP's soil energy residual 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ W/m², measured with a thin-snow fix that comes later |

Notes:
- Evaporation: Noah-MP removes water with its own `hvap` and, over frozen surfaces, `hsub`, so the atmosphere received 0.4 % more water than unfrozen land lost and 14 % more over snow and frozen ground. The new flux is the one the WRF, HRLDAS, MPAS and LIS drivers pass (`QFX`). Noah-MP's own latent heat flux is unchanged; the host's diagnostic `rho*con_hvap*evap` now follows the water and is up to 12 % lower where sublimation dominates. See also NCAR/ccpp-physics#582.
- Snow initialisation: snow depth without snow water still builds no layers, as on develop. Otherwise dividing by a small land fraction can build layers with no ice, whose zero heat capacity divides by zero in Noah-MP's energy routine.
- Snow layer count: rare at short time steps (5 × 10⁻⁶ of calls on melt-out-prone packs at 720 s, 1.7 × 10⁻² at 3600 s); C96 24 h is bitwise unchanged by this fix alone.
- Snow layer heat: with all three and the layer-count fix, the temperature rms difference is 0.147 K and land fields are at noise.

Related fixes come later, separately:
- With `frac_grid`, coastal land is stepped twice per time step (the time-step fix). Sea ice has the same cause, and both have two tested forms.
- Fixes where the destination of the water or heat is a judgement: truncated thin snow, truncated canopy water, the heat of a melted-out snow layer, and Noah-MP's own latent heats.

## Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR, the SAMF/PBL fixes and the GFDL MP v3 fixes, 27 October 2026 (develop 3e48f4cc, baselines 20261022): all 54 builds compile; 116 tests are identical, 101 change answers, and 15 restart/IAU tests did not start because their parent tests change answers; none fails to run. The log will be in the ufs-weather-model PR that follows review. Effects in the table are from budget meters added to the model (C96 `control_p8_ugwpv1`, 24 h).

## Dependencies:
None. The ufs-weather-model PR, with the RT log, follows review.

## Documentation:
None needed.

## Issue (optional):
ufs-community/ufs-weather-model#3404

## Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
