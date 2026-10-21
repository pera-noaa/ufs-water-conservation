## Description
In-model budgets of a C96 `control_p8_ugwpv1` forecast show the physics creating water (+0.25 % of precipitation per day; +0.45 % at C384) and losing 2 % per day of a convectively transported tracer; with the water fixed, the atmosphere's energy budget still leaves +2.1 W/m² unexplained. We traced these to small, independent bugs in SAMF, the PBL, Thompson (and the TEMPO driver), Noah-MP and its coupling, sea ice, NSST, GFDL MP v3, the SAMF single-precision build, and the FV3 driver and dycore. This round fixes 37; the SAMF cloud-base fix waits on ufs-community/ccpp-physics#401.

### To Reproduce:
Any P8 forecast; the budget residuals need meters. Two defects are visible without them:
- `control_p8_mynn` with layout 3×8 and 4×6 differs in 90 of 126 `atmf024` variables (SAMF early returns before the cellular-automaton trigger).
- With `frac_grid`, Noah-MP steps 24–27 % of land twice per time step (land gains 3–5 % of global precipitation).

## Additional context
Fixes, one commit each, in five WM PRs, all answer-changing. Now: ufs-community/ufs-weather-model#TBD (SAMF, PBL, Noah-MP, GFDL MP v3, SAMF single precision) and #TBD (Thompson, TEMPO driver), with their ccpp-physics, NOAA-EMC/noahmp and NOAA-EMC/ufsatm PRs. After the SAMF overshoot (ufs-community/ccpp-physics#401), which `hafs_global_1nest_atm` is sensitive to: land and sea ice stepped once per time step, sea ice and NSST (ccpp-physics), and FV3 (NOAA-GFDL/GFDL_atmos_cubed_sphere). Then three Thompson fixes that have a second reasonable form. Notes and data: https://github.com/pera-noaa/ufs-water-conservation.
