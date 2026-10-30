# Phase-0 drafts (23 Oct): what would be posted, in order

Nothing here is posted. `#TBD` fills as each item is opened. Branches are pushed to the `pera-noaa` forks on today's heads.

---

## WM_ISSUE: issue on ufs-community/ufs-weather-model

**Title:** Water, energy and tracer-mass conservation bugs in UFS physics and FV3 coupling  

### Description
In-model budgets of a C96 `control_p8_ugwpv1` forecast show the physics creating water (+0.25 % of precipitation per day; +0.45 % at C384) and losing 2 % per day of a convectively transported tracer; with the water fixed, the atmosphere's energy budget still leaves +2.1 W/m² unexplained. We traced these to small, independent bugs in SAMF, the PBL, Thompson (and the TEMPO driver), Noah-MP and its coupling, sea ice, NSST, GFDL MP v3, the SAMF single-precision build, and the FV3 driver and dycore. This round fixes 37; the SAMF cloud-base fix waits on ufs-community/ccpp-physics#401.

### To Reproduce:
Any P8 forecast; the budget residuals need meters. Two defects are visible without them:
- `control_p8_mynn` with layout 3×8 and 4×6 differs in 90 of 126 `atmf024` variables (SAMF early returns before the cellular-automaton trigger).
- With `frac_grid`, Noah-MP steps 24–27 % of land twice per time step (land gains 3–5 % of global precipitation).

### Additional context
Fixes, one commit each, in five WM PRs, all answer-changing. Now: ufs-community/ufs-weather-model#TBD (SAMF, PBL, Noah-MP, GFDL MP v3, SAMF single precision) and #TBD (Thompson, TEMPO driver), with their ccpp-physics, NOAA-EMC/noahmp and NOAA-EMC/ufsatm PRs. After the SAMF overshoot (ufs-community/ccpp-physics#401), which `hafs_global_1nest_atm` is sensitive to: land and sea ice stepped once per time step, sea ice and NSST (ccpp-physics), and FV3 (NOAA-GFDL/GFDL_atmos_cubed_sphere). Then three Thompson fixes that have a second reasonable form. Notes and data: https://github.com/pera-noaa/ufs-water-conservation.

---

## PR_SAMF: PR on ufs-community/ccpp-physics

**Title:** SAMF: ice fusion heat, wet deposition, CA-trigger early returns; PBL surface flux mass  
**Branch:** `pera-noaa:pr1-samf` → `ufs/dev`  

### Description of Changes:
Four bug fixes, one commit each. All change answers.

| Fix | Bug | Effect |
|---|---|---|
| Ice fusion heat | detrained condensate turns to ice with no heat of fusion | −0.42 W/m² (deep), −0.018 (shallow) → 10⁻¹³; +0.016 K at 500–200 hPa |
| Wet deposition | booked with `eta(k-1)`, removed with `eta(k)`; erased in the borrowing branch | scavenged tracer + deposition −7.4 × 10⁻⁴/day → 3 × 10⁻¹⁵ |
| PBL surface fluxes | `satmedmfvdifq` applies kinematic fluxes with `1/Δz` instead of `ρ_a g/δp` | `FV3_GFS_v16` water 2.6 × 10⁻⁸ → 4 × 10⁻¹⁶ kg/m²/day; last-bit in P8 |
| CA trigger | six early returns before `ca_trigger` can re-enable a column | `control_p8_mynn` 3×8 vs 4×6: 90/126 variables differ → 0 |

New argument: `hfus` (`latent_heat_of_fusion_of_water_at_0C`, already provided by the hosts).

### Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD (Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 116 tests identical, 101 change answers, 15 restart/IAU children not started (their parents change answers); none fails to run). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

### Dependencies:
ufs-community/ufs-weather-model#TBD

Rebased onto `ufs/dev` after ufs-community/ccpp-physics#390 (one block in `samfdeepcnv.f` re-resolved around its `progomega` guards). #403 adds arguments to `samfdeepcnv_run` beside ours (`hfus`); whichever merges second needs a one-block rebase.

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#TBD

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## PR_NM: PR on ufs-community/ccpp-physics

**Title:** Noah-MP: water and energy bugs in the driver, coastal snow, snow initialisation, truncations, snow layers  
**Branch:** `pera-noaa:pr1-noahmp` → `ufs/dev`  

### Description of Changes:
Eleven fixes in Noah-MP and its interstitials, one commit each.

| Fix | Bug | Effect |
|---|---|---|
| Evaporation hand-off | latent heat ÷ a different constant | atmosphere gains 0.07–0.10 % of global precipitation |
| Coastal snow (`frac_grid`) | land snow overwritten with the cell mean every step | thin coastal snow lost |
| Snow initialisation | cold-start snow layers built from the cell-mean snow | 0.29 kg/m² land snow lost at step 1 |
| Thin snow | snow < 10⁻³ mm without layers deleted | 0.009 % of global precipitation |
| Canopy truncation | canopy water ≤ 10⁻⁶ mm deleted | 4 × 10⁻⁷ of land precipitation |
| Latent heats | Noah-MP's own constants, not the host's | land pays 0.4 % more latent energy than its vapour carries |
| `combine` count | tests `isnow_old`, not `isnow` (NCAR/noahmp#47) | per firing up to 0.16 mm water, 8.5 MJ/m² |
| Melt-out heat | leftover heat deleted when the layer below is frozen | did not fire in the test case |
| Snow layer heat (3 commits) | merge keeps receiver's T; capped volume fractions; m⁻³ capacities used per kg | Noah-MP soil energy residual 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ W/m² |

Noah-MP's coastal land is also stepped twice per time step with `frac_grid`; that fix follows with its sea-ice twin (the same cause, two tested forms).

### Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD (Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 116 tests identical, 101 change answers, 15 restart/IAU children not started (their parents change answers); none fails to run). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

### Dependencies:
ufs-community/ufs-weather-model#TBD

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#TBD

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## PR_GMP: PR on ufs-community/ccpp-physics

**Title:** GFDL MP v3: convert back on the input mass basis; rain sediments with c_liq  
**Branch:** `pera-noaa:pr1-gfdlmp` → `ufs/dev`  

### Description of Changes:
| Fix | Bug | Effect (`control_iovr4_gfdlmpv3`) |
|---|---|---|
| Mass basis | in with `1/(1-q_v,in)`, back with `1/(1+q_v,new)` | removes 1.03 % of microphysics precipitation |
| Sedimentation heat | rain and cloud water fall with `c_ice` | +0.20 → −0.007 W/m² |

### Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD (Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 116 tests identical, 101 change answers, 15 restart/IAU children not started (their parents change answers); none fails to run). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

### Dependencies:
ufs-community/ufs-weather-model#TBD

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#TBD

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## PR_TH: PR on ufs-community/ccpp-physics

**Title:** Thompson: water-budget fixes (mass basis, graupel re-closure, density, layer depth)  
**Branch:** `pera-noaa:pr1-thompson` → `ufs/dev`  

### Description of Changes:
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

### Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD (Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 57 tests identical, 150 change answers, 25 restart children not started (their parents change answers); none fails to run). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

### Dependencies:
ufs-community/ufs-weather-model#TBD

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#TBD

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## PR_TP: PR on ufs-community/ccpp-physics

**Title:** mp_tempo: convert to and from mixing ratio with the same humidity  
**Branch:** `pera-noaa:pr1-tempo` → `ufs/dev`  

### Description of Changes:
The TEMPO driver has the same mass-basis bug as `mp_thompson` (fixed in ufs-community/ccpp-physics#TBD): species are converted to mixing ratio with `1/(1-q_v)` and back with `1/(1+r_v,new)`, while the host rebuilds the layer mass from the old `q_v`. One commit; uses the input humidity in both directions.

This fix exposes TEMPO's own water residual (+0.33 % of grid-scale precipitation in `control_p8_ugwpv1_tempo`), which the driver error was cancelling. Fixes for that are proposed to NCAR/TEMPO separately.

`regional_wofs_tempo` (storm scale, 3 km): precipitation −1.96 % (noise 0.34 %). With net condensation the old round trip created water, so the fix lowers precipitation where condensation dominates.

### Tests Conducted:
Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel + GNU `rt.sh` on Hercules: see ufs-community/ufs-weather-model#TBD (Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 57 tests identical, 150 change answers, 25 restart children not started (their parents change answers); none fails to run). With all round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.

### Dependencies:
ufs-community/ufs-weather-model#TBD

Overlaps ufs-community/ccpp-physics#389 in one block; whichever merges second needs a rebase. Ours onto #389 is ready.

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#TBD

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## ATM_0b: PR on NOAA-EMC/ufsatm

**Title:** Round-1 conservation bug fixes, track 0b: SAMF single-precision build fix; update ccpp-physics  
**Branch:** `pera-noaa:pr1-0b` → `develop`  

### Description
- `ccpp/CMakeLists.txt`: `-DSAMFCNV_32BIT=ON` (#1133) compiled 2 of SAMF's 5 files single precision: the filter searched the scheme files only, and `mo_conv_kind.F90`, `progsigma_calc.f90`, `progomega_calc.f90` are capgen dependencies, so `conv_wp` stayed 8-byte. Now all 5; configure stops if only some are found. @rhaesung
- Updates `ccpp/physics` for the track-0b fixes: SAMF + PBL, Noah-MP, GFDL MP v3.

Answers change: the physics fixes in the suites that use them, and SAMF is now really single precision in the `_conv32` tests.

### Issue(s) addressed
- ufs-community/ufs-weather-model#TBD

### Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD. Baselines change.

### Dependencies
ufs-community/ccpp-physics#TBD (SAMF + PBL), #TBD (Noah-MP), #TBD (GFDL MP v3)

---

## ATM_0c: PR on NOAA-EMC/ufsatm

**Title:** Round-1 conservation bug fixes, track 0c: update ccpp-physics (Thompson, TEMPO driver)  
**Branch:** `pera-noaa:pr1-0c` → `develop`  

### Description
Updates `ccpp/physics` for the Thompson and TEMPO-driver fixes. No code change in ufsatm. Answers change in the Thompson and TEMPO suites.

### Issue(s) addressed
- ufs-community/ufs-weather-model#TBD

### Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD. Baselines change.

### Dependencies
ufs-community/ccpp-physics#TBD (Thompson), #TBD (TEMPO driver)

---

## WM_0b: PR on ufs-community/ufs-weather-model

**Title:** Round-1 conservation bug fixes, track 0b (SAMF, PBL, Noah-MP, GFDL MP v3); update UFSATM  
**Branch:** `pera-noaa:pr1-0b` → `develop`  

### Commit Queue Requirements:
- [x] This PR addresses a relevant WM issue: #TBD
- [ ] All subcomponent pull requests (if any) have been reviewed by their code managers.
- [x] Run the full Intel+GNU RT suite (compared to current baselines) on Hercules.
   - [x] Commit log file w/full results from RT suite run.
   - [x] Verify that `test_changes.list` indicates which tests, if any, are changed by this PR.
- Transparency in the use of generative AI is required by NOAA policy. Was GenAI used in this work?
   - [x] Yes. Claude Opus 5.5 (Anthropic) was used to assist with developing this code.
     - [ ] The code has been reviewed, edited, and validated by NWS staff.
- [x] Fill out all sections of this template.

### Description:
18 independent, answer-changing bug fixes that remove water, energy and tracer-mass errors in SAMF, the PBL, Noah-MP, GFDL MP v3 and the SAMF single-precision build. Each fix is one commit in its subcomponent, with the defect, fix and measured effect in the commit message. Largest effects: SAMF drops the heat of fusion of the ice it detrains (0.42 W/m²); GFDL MP v3 creates 1.03 % of its precipitation; `control_p8_mynn` depends on the decomposition. In the global tests the mean 3-D temperature rises 0.001–0.006 K and precipitation changes by −0.3 to +0.3 %: the heat of fusion SAMF was dropping (0.42 W/m²), restored. `hafs_global_1nest_atm` has a pre-existing SAMF instability (ufs-community/ccpp-physics#401); with these fixes it crashes in 0 of 20 perturbed members, as develop. One of five WM PRs from the same issue.

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 0b (SAMF, PBL, Noah-MP, GFDL MP v3); update UFSATM
  * UFSATM - SAMFCNV_32BIT compiles all SAMF files single precision
    * ccpp-physics - Bug fixes in SAMF, satmedmfvdifq, Noah-MP, GFDL MP v3
```

### Priority:
- [x] Normal

### Git Tracking

### UFSWM:
* Addresses #TBD (with the other round-1 WM PRs; the last to merge closes it)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * ccpp-physics: ufs-community/ccpp-physics#TBD (SAMF + PBL), #TBD (Noah-MP), #TBD (GFDL MP v3)

### UFSWM Blocking Dependencies:
- [x] None

### Documentation:
- [x] Documentation update NOT required.
   - Explanation: bug fixes; no new options.

### Changes

### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 116 tests identical, 101 change answers, 15 restart/IAU children not started (their parents change answers); none fails to run

### Input data Changes:
- [x] None.

### Subcomponent Branch Changes
- [x] No

### Library Changes/Upgrades:
- [x] No Updates

---
<!-- STOP!!! THE FOLLOWING IS FOR CODE MANAGERS ONLY. PLEASE DO NOT FILL OUT -->
### Testing Log:
- RDHPCS
  - [ ] Orion
  - [ ] Hercules
  - [ ] GaeaC6
  - [ ] Ursa
- WCOSS2
  - [ ] Dogwood/Cactus
- [ ] CI
- [ ] opnReqTest (complete task if unnecessary)

### Testing Remarks:
<!-- Lead CM: List (1) testing issues that we are bypassing (e.g., failing CI due to remarks or an early-merged component PR)
(2) Issues that have been opened based on testing results (3) any other relevant info --> -

---

## WM_0c: PR on ufs-community/ufs-weather-model

**Title:** Round-1 conservation bug fixes, track 0c (Thompson, TEMPO driver); update UFSATM  
**Branch:** `pera-noaa:pr1-0c` → `develop`  

### Commit Queue Requirements:
- [x] This PR addresses a relevant WM issue: #TBD
- [ ] All subcomponent pull requests (if any) have been reviewed by their code managers.
- [x] Run the full Intel+GNU RT suite (compared to current baselines) on Hercules.
   - [x] Commit log file w/full results from RT suite run.
   - [x] Verify that `test_changes.list` indicates which tests, if any, are changed by this PR.
- Transparency in the use of generative AI is required by NOAA policy. Was GenAI used in this work?
   - [x] Yes. Claude Opus 5.5 (Anthropic) was used to assist with developing this code.
     - [ ] The code has been reviewed, edited, and validated by NWS staff.
- [x] Fill out all sections of this template.

### Description:
Five independent, answer-changing bug fixes that close water-budget errors in Thompson microphysics and fix the same mass-basis error in the TEMPO driver. Each fix is one commit, with the defect, fix and measured effect in the commit message. In the regional and convection-allowing tests precipitation falls by 0.9–5.3 % (`regional_wofs_tempo` 2.0 %): water that the graupel limiters and the mass-basis round trips created is no longer created. The ccpp-physics PRs give the attribution by fix. One of five WM PRs from the same issue.

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 0c (Thompson, TEMPO driver); update UFSATM
  * UFSATM - update ccpp-physics
    * ccpp-physics - Thompson water budget fixes; TEMPO driver mass basis
```

### Priority:
- [x] Normal

### Git Tracking

### UFSWM:
* Addresses #TBD (with the other round-1 WM PRs; the last to merge closes it)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * ccpp-physics: ufs-community/ccpp-physics#TBD (Thompson), #TBD (TEMPO driver)

### UFSWM Blocking Dependencies:
- [x] None

### Documentation:
- [x] Documentation update NOT required.
   - Explanation: bug fixes; no new options.

### Changes

### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. Hercules, 23 October 2026, develop 5651397d, baselines 20261016: 54 compiles pass; 57 tests identical, 150 change answers, 25 restart children not started (their parents change answers); none fails to run

### Input data Changes:
- [x] None.

### Subcomponent Branch Changes
- [x] No

### Library Changes/Upgrades:
- [x] No Updates

---
<!-- STOP!!! THE FOLLOWING IS FOR CODE MANAGERS ONLY. PLEASE DO NOT FILL OUT -->
### Testing Log:
- RDHPCS
  - [ ] Orion
  - [ ] Hercules
  - [ ] GaeaC6
  - [ ] Ursa
- WCOSS2
  - [ ] Dogwood/Cactus
- [ ] CI
- [ ] opnReqTest (complete task if unnecessary)

### Testing Remarks:
<!-- Lead CM: List (1) testing issues that we are bypassing (e.g., failing CI due to remarks or an early-merged component PR)
(2) Issues that have been opened based on testing results (3) any other relevant info --> -

