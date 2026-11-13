## Description
In-model budgets of a C96 `control_p8_ugwpv1` forecast show the physics creating water (+0.25 % of precipitation per day; +0.45 % at C384) and losing 2 % per day of a convectively transported tracer. With the water fixed, the atmosphere's energy budget still leaves +2.1 W/m² unexplained. We traced these to small, independent bugs in SAMF, the PBL, Thompson and the TEMPO driver, Noah-MP and its coupling, sea ice, NSST, GFDL MP v3, the SAMF single-precision build, and the FV3 driver and dycore. Each fix is one commit, with its own measurement.

### To Reproduce:
Any P8 forecast; the budget residuals need meters. Two defects are visible without them:
- `control_p8_mynn` with layout 3×8 and 4×6 differs in 90 of 126 `atmf024` variables (SAMF early returns before the cellular-automaton trigger).
- With `frac_grid`, Noah-MP steps 24–27 % of land twice per time step (land gains 3–5 % of global precipitation).

## Additional context
We will send the fixes in stages: ccpp-physics (or FV3) PRs first, then the NOAA-EMC/ufsatm and ufs-weather-model PRs once they have been reviewed, so the baseline changes come together.
1. Noah-MP, GFDL MP v3 and Thompson. The TEMPO driver follows ufs-community/ccpp-physics#389.
2. SAMF and the PBL, and the SAMF single-precision build (ufsatm).
3. After the SAMF overshoot (ufs-community/ccpp-physics#401): land and sea ice stepped once per time step, sea ice and NSST, and FV3 (NOAA-GFDL/GFDL_atmos_cubed_sphere). Then three Thompson fixes that have a second reasonable form.

The SAMF cloud-base fix is ufs-community/ccpp-physics#405.

Working notes, with each defect, its fix, the measurements and the scripts (https://github.com/pera-noaa/ufs-water-conservation):
- Water: [`water_closure_proposal.md`](https://github.com/pera-noaa/ufs-water-conservation/blob/main/proposal/water_closure_proposal.md)
- Energy and tracer mass: [`conservation_proposal.md`](https://github.com/pera-noaa/ufs-water-conservation/blob/main/proposal/conservation_proposal.md)
- Submission plan and regression-test results: [`pr_round1.md`](https://github.com/pera-noaa/ufs-water-conservation/blob/main/proposal/pr_round1.md)
- The SAMF overshoot (ufs-community/ccpp-physics#401): [`hafs_samf/`](https://github.com/pera-noaa/ufs-water-conservation/tree/main/proposal/hafs_samf)

