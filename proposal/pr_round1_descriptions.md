# PR round 1: issue and PR descriptions (drafts)

*Drafts, not posted. Fill `#TBD` once opened; `[RT 1a]`, `[RT 1b]`, `[RT 1c]`, `[HAFS 1a]` once each track's run is in.
Round 1 posts in three tracks (`pr_round1.md`, *Tracks*), each with its own ufsatm and WM PR:

| Track | PRs (sections) | Order |
|---|---|---|
| 1a global conservation | ccpp-physics SAMF + PBL, Noah-MP, sea ice/NSST, GFDL MP v3 (§3.1, §3.4–3.6); NOAA-EMC/noahmp (§5); ufsatm (§6a); WM (§7a) | first; SAMF after ccpp-physics#390 |
| 1b microphysics | ccpp-physics Thompson, TEMPO driver (§3.2, §3.3); ufsatm (§6b); WM (§7b) | second; TEMPO after #389 |
| 1c dycore | GFDL issue and PR (§2, §4); ufsatm (§6c); WM (§7c) | when GFDL merges `dev/emc` |

Before any track: the SAMF issue (§8) and the WM issue (§1). Measurements: C96 `control_p8_ugwpv1`, 24 h, in-model
budget meters, unless stated.*

---

## 1. ufs-weather-model issue

**Title:** Water, energy and tracer-mass conservation bugs in UFS physics and FV3 coupling

## Description
In-model budgets of a C96 `control_p8_ugwpv1` forecast show the physics creating water (+0.25 % of precipitation
per day; +0.45 % at C384) and losing 2 % per day of a convectively transported tracer; with the water fixed, the
atmosphere's energy budget still leaves +2.1 W/m² unexplained. We traced these to small, independent bugs in SAMF,
the PBL, Thompson (and the TEMPO driver), Noah-MP and its coupling, sea ice, NSST, GFDL MP v3, the SAMF
single-precision build, and the FV3 driver and dycore. This round fixes 37; the SAMF cloud-base fix waits on
ufs-community/ccpp-physics#TBD.

### To Reproduce:
Any P8 forecast; the budget residuals need meters. Two defects are visible without them:
- `control_p8_mynn` with layout 3×8 and 4×6 differs in 90 of 126 `atmf024` variables (SAMF early returns before
  the cellular-automaton trigger).
- With `frac_grid`, Noah-MP steps 24–27 % of land twice per time step (land gains 3–5 % of global precipitation).

## Additional context
Fixes, one commit each, in three WM PRs: ufs-community/ufs-weather-model#TBD (SAMF, PBL, Noah-MP, sea ice, NSST,
GFDL MP v3, SAMF single precision), #TBD (Thompson, TEMPO driver), #TBD (FV3), with their ccpp-physics (6),
NOAA-GFDL/GFDL_atmos_cubed_sphere, NOAA-EMC/noahmp and NOAA-EMC/ufsatm PRs. All change answers.

---

## 2. GFDL_atmos_cubed_sphere issue

**Title:** Energy and tracer-mass bugs in the `consv_te` fixer, `fv_sg`, the UFS driver and `inline_q` damping

Six bugs (fixes and measurements in NOAA-GFDL/GFDL_atmos_cubed_sphere#TBD):
1. `consv_te` fixer weight ≠ heat capacity it heats (`fv_mapz`).
2. `fv_sg` relaxes T, u, v, w separately after mixing total energy, losing KE (`fv_sg`, nwat = 6).
3. Physics heating applied to the new layer mass, not the mass the physics heated (`atmosphere_state_update`).
4. Tracers divided and multiplied by different layer thicknesses (`atmos_phys_driver_statein`).
5. `prsl` built with the dycore's single-precision gas constant (`atmos_phys_driver_statein`).
6. `inline_q` tracer damping uses different `delp` on the two sides of a PE boundary (`d_sw`).

---

## 3. ccpp-physics PRs (base `ufs/dev`)

Common to all six:

> **Tests Conducted:** Intel on Hercules: compiled alone on `develop` and with the other round-1 fixes. Full Intel +
> GNU `rt.sh` on Hercules: see this track's ufs-community/ufs-weather-model#TBD ([RT 1a] or [RT 1b]). With all
> round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then
> `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.
>
> **Documentation:** none needed.
>
> **Issue:** ufs-community/ufs-weather-model#TBD
>
> **Contributors:** Lori Bruhwiler (NOAA GML).

### 3.1 SAMF and satmedmfvdifq

**Title:** SAMF: ice fusion heat, wet deposition, CA-trigger early returns; PBL surface flux mass

## Description of Changes:
Four bug fixes, one commit each. All change answers.

| Fix | Bug | Effect |
|---|---|---|
| Ice fusion heat | detrained condensate turns to ice with no heat of fusion | −0.42 W/m² (deep), −0.018 (shallow) → 10⁻¹³; +0.016 K at 500–200 hPa |
| Wet deposition | booked with `eta(k-1)`, removed with `eta(k)`; erased in the borrowing branch | scavenged tracer + deposition −7.4 × 10⁻⁴/day → 3 × 10⁻¹⁵ |
| PBL surface fluxes | `satmedmfvdifq` applies kinematic fluxes with `1/Δz` instead of `ρ_a g/δp` | `FV3_GFS_v16` water 2.6 × 10⁻⁸ → 4 × 10⁻¹⁶ kg/m²/day; last-bit in P8 |
| CA trigger | six early returns before `ca_trigger` can re-enable a column | `control_p8_mynn` 3×8 vs 4×6: 90/126 variables differ → 0 |

New argument: `hfus` (`latent_heat_of_fusion_of_water_at_0C`, already provided by the hosts).

## Dependencies:
ufs-community/ufs-weather-model#TBD

### 3.2 Thompson

**Title:** Thompson: close the water budget (mass basis, settling, graupel, density, layer depth, clipping, threshold)

## Description of Changes:
Seven fixes in `mp_thompson`/`module_mp_thompson`, one commit each. Sizes are fractions of grid-scale
precipitation.

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

Noise (one-ulp perturbation): ≤ 0.24 %. The graupel fix removes water created during spin-up, largest in these
short cold starts (0.76 % in the first 6 h at C96). The cloud sedimentation substepping changes precipitation by
≤ 0.23 % except `gnv1_nested` (−1.2 %).

## Dependencies:
ufs-community/ufs-weather-model#TBD

### 3.3 TEMPO driver

**Title:** mp_tempo: convert to and from mixing ratio with the same humidity

## Description of Changes:
The TEMPO driver has the same mass-basis bug as `mp_thompson` (fixed in ufs-community/ccpp-physics#TBD): species
are converted to mixing ratio with `1/(1-q_v)` and back with `1/(1+r_v,new)`, while the host rebuilds the layer mass
from the old `q_v`. One commit; uses the input humidity in both directions.

This fix exposes TEMPO's own water residual (+0.33 % of grid-scale precipitation in `control_p8_ugwpv1_tempo`),
which the driver error was cancelling. Fixes for that are proposed to NCAR/TEMPO separately.

`regional_wofs_tempo` (storm scale, 3 km): precipitation −1.96 % (noise 0.34 %). With net condensation the old
round trip created water, so the fix lowers precipitation where condensation dominates.

## Dependencies:
ufs-community/ufs-weather-model#TBD

### 3.4 Noah-MP

**Title:** Noah-MP: water and energy bugs in the driver, frac_grid stepping, snow initialisation, truncations, snow layers

## Description of Changes:
Twelve fixes in Noah-MP and its interstitials, one commit each.

| Fix | Bug | Effect |
|---|---|---|
| Once per time step | with `frac_grid`, coastal land is re-flagged and stepped again on the second surface iteration (24–27 % of land, every step) | land gains 3–5 % of global precipitation |
| Evaporation hand-off | latent heat ÷ a different constant | atmosphere gains 0.07–0.10 % of global precipitation |
| Coastal snow (`frac_grid`) | land snow overwritten with the cell mean every step | thin coastal snow lost |
| Snow initialisation | cold-start snow layers built from the cell-mean snow | 0.29 kg/m² land snow lost at step 1 |
| Thin snow | snow < 10⁻³ mm without layers deleted | 0.009 % of global precipitation |
| Canopy truncation | canopy water ≤ 10⁻⁶ mm deleted | 4 × 10⁻⁷ of land precipitation |
| Latent heats | Noah-MP's own constants, not the host's | land pays 0.4 % more latent energy than its vapour carries |
| `combine` count | tests `isnow_old`, not `isnow` (NCAR/noahmp#47) | per firing up to 0.16 mm water, 8.5 MJ/m² |
| Melt-out heat | leftover heat deleted when the layer below is frozen | did not fire in the test case |
| Snow layer heat (3 commits) | merge keeps receiver's T; capped volume fractions; m⁻³ capacities used per kg | Noah-MP soil energy residual 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ W/m² |

The once-per-step fix adds an optional last argument `iter` (`ccpp_loop_counter`) to `noahmpdrv_run`.

## Dependencies:
- NOAA-EMC/noahmp#TBD (its copy of the driver must declare `iter`, or `control_p8_atmlnd` crashes)
- ufs-community/ufs-weather-model#TBD (7a; bumps NOAHMP-interface too)

### 3.5 Sea ice and NSST

**Title:** sfc_sice and sfc_nst: ice stepped twice, heat divided by Δt twice, flooded-snow heat, rain units

## Description of Changes:
Four fixes, one commit each.

| Fix | Bug | Effect |
|---|---|---|
| Once per step | NSST re-flags icy cells for the second iteration; ice stepped again (1.9 % of ice column-steps) | calls per column-step 1.0186 → 1.0000 |
| Excess heat | `ice3lay` divides J/m² by `li*delt` | deletes (1 − 1/Δt) of it; thin ice near melting |
| Flooded snow | becomes ice at the layers' T, not with its −li heat content | −7.9 × 10⁻³ → 10⁻¹³ W/m² |
| NSST rain | `rain` (m per step) used as kg m⁻² s⁻¹ in `qrain` and `sep` | rain heat flux × 1000/720 at Δt 720 s |

Together: ice thickness rms 1.7 × 10⁻³ m (noise 8 × 10⁻⁵); other fields at noise.

## Dependencies:
ufs-community/ufs-weather-model#TBD

### 3.6 GFDL MP v3

**Title:** GFDL MP v3: convert back on the input mass basis; rain sediments with c_liq

## Description of Changes:

| Fix | Bug | Effect (`control_iovr4_gfdlmpv3`) |
|---|---|---|
| Mass basis | in with `1/(1-q_v,in)`, back with `1/(1+q_v,new)` | removes 1.03 % of microphysics precipitation |
| Sedimentation heat | rain and cloud water fall with `c_ice` | +0.20 → −0.007 W/m² |

## Dependencies:
ufs-community/ufs-weather-model#TBD

---

## 4. GFDL_atmos_cubed_sphere PR (base `dev/emc`)

**Title:** Energy and tracer-mass fixes: consv_te weight, fv_sg energy, physics coupling mass, prsl constants, inline_q damping

**Description**

Six answer-changing bug fixes, one commit each. Fixes #TBD.

| Fix | File | Effect |
|---|---|---|
| `consv_te` weight = the heat capacity it heats | `fv_mapz` | fixer error −5.5 × 10⁻⁴ → 4 × 10⁻¹⁰ W/m² |
| `fv_sg`: T from the relaxed total energy (nwat = 6) | `fv_sg` | −1.6 × 10⁻⁴ → 3 × 10⁻¹¹ W/m² (sponge only) |
| Physics heating on the mass it heated | `atmosphere.F90` | −8.6 × 10⁻³ → 4 × 10⁻¹⁰ W/m² |
| Tracers divided and multiplied by the same thickness | `atmosphere.F90` | tracer mass +3.1 × 10⁻¹⁵ → 5 × 10⁻¹⁷ per day |
| `prsl` with the physics' gas constants | `atmosphere.F90` | 32-bit: 4 × 10⁻⁸ of evaporation → 2 × 10⁻¹⁶ |
| `inline_q` damping with the pre-update `delp` | `sw_core` | with `inline_q`: tracer mass 10⁻⁹ → 10⁻¹⁴ per day; off: bitwise |

**How Has This Been Tested?**
Intel on Hercules, in UFS (ufs-community/ufs-weather-model#TBD): compile, full Intel + GNU `rt.sh` ([RT 1c]); with
all round-1 fixes, reproducibility 123 of 123 bitwise. Effects from in-model budget meters (C96 `control_p8_ugwpv1`, 24 h, 64-bit dycore).

**Checklist:** [x] style, [x] self-review, [x] comments, [ ] documentation (none needed), [x] no new warnings,
[ ] dependent changes merged (none).

---

## 5. NOAA-EMC/noahmp PR (base `develop`)

**Title:** CCPP driver copy: accept the optional `iter` argument

Companion of ufs-community/ccpp-physics#TBD, which steps Noah-MP land once per time step through a new optional
`iter` argument of `noahmpdrv_run`. In atmosphere–land builds the land component is compiled against this copy's
interface but calls the ccpp-physics routine; without `iter` declared here, `control_p8_atmlnd` crashes. Declares
the same optional `iter` in `drivers/ccpp/noahmpdrv.F90` and `.meta`. Tested in
ufs-community/ufs-weather-model#TBD (`atml` build, land-component tests).

---

## 6. NOAA-EMC/ufsatm PRs (base `develop`), one per track

### 6a. Track 1a: SAMF32 build fix and the 1a physics

## Description
- `ccpp/CMakeLists.txt`: `-DSAMFCNV_32BIT=ON` (#1133) compiled 2 of SAMF's 5 files single precision: the filter
  searched the scheme files only, and `mo_conv_kind.F90`, `progsigma_calc.f90`, `progomega_calc.f90` are capgen
  dependencies, so `conv_wp` stayed 8-byte. Now all 5; configure stops if only some are found. @rhaesung
- Updates `ccpp/physics` for the track-1a fixes: SAMF + PBL, Noah-MP, sea ice/NSST, GFDL MP v3.

Answers change: the physics fixes in the suites that use them, and SAMF is now really single precision in the
`_conv32` tests.

### Issue(s) addressed
- ufs-community/ufs-weather-model#TBD

## Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD (7a). Baselines change.

## Dependencies
ufs-community/ccpp-physics#TBD (SAMF + PBL), #TBD (Noah-MP), #TBD (sea ice, NSST), #TBD (GFDL MP v3)

### 6b. Track 1b: Thompson and TEMPO

## Description
Updates `ccpp/physics` for the Thompson and TEMPO-driver fixes. No code change in ufsatm. Answers change in the
Thompson and TEMPO suites.

### Issue(s) addressed
- ufs-community/ufs-weather-model#TBD

## Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD (7b). Baselines change.

## Dependencies
ufs-community/ccpp-physics#TBD (Thompson), #TBD (TEMPO driver)

### 6c. Track 1c: FV3

## Description
Updates `fv3/atmos_cubed_sphere` for the FV3 fixes (NOAA-GFDL/GFDL_atmos_cubed_sphere#TBD). No code change in
ufsatm. Answers change everywhere.

### Issue(s) addressed
- ufs-community/ufs-weather-model#TBD

## Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD (7c). Baselines change.

## Dependencies
NOAA-GFDL/GFDL_atmos_cubed_sphere#TBD

---

## 7. ufs-weather-model PRs (base `develop`), one per track

Common to 7a–7c:

## Commit Queue Requirements:
- [x] This PR addresses a relevant WM issue: #TBD
- [ ] All subcomponent pull requests (if any) have been reviewed by their code managers.
- [x] Run the full Intel+GNU RT suite (compared to current baselines) on Hercules.
   - [x] Commit log file w/full results from RT suite run.
   - [x] Verify that `test_changes.list` indicates which tests, if any, are changed by this PR.
- Transparency in the use of generative AI is required by NOAA policy. Was GenAI used in this work?
   - [x] Yes. Claude Opus 5.5 (Anthropic) was used to assist with developing this code.
     - [ ] The code has been reviewed, edited, and validated by NWS staff.
- [x] Fill out all sections of this template.

> ### Priority:
> - [x] Normal
>
> ### UFSWM Blocking Dependencies:
> - [x] None
>
> ### Documentation:
> - [x] Documentation update NOT required.
>    - Explanation: bug fixes; no new options.
>
> ### Input data Changes:
> - [x] None.
>
> ### Subcomponent Branch Changes
> - [x] No
>
> ### Library Changes/Upgrades:
> - [x] No Updates

### 7a. Track 1a: global conservation fixes

## Description:
24 independent, answer-changing bug fixes that remove water, energy and tracer-mass errors in SAMF, the PBL,
Noah-MP and its coupling, sea ice, NSST, GFDL MP v3 and the SAMF single-precision build. Each fix is one commit in its
subcomponent, with the defect, fix and measured effect in the commit message. Largest effects: Noah-MP steps coastal
land twice with `frac_grid` (land gains 3–5 % of global precipitation); `control_p8_mynn` depends on the
decomposition. In the global tests the mean 3-D temperature rises 0.002–0.005 K and precipitation changes by −0.3 to
+0.3 %: the heat of fusion SAMF was dropping (0.42 W/m²), restored. `hafs_global_1nest_atm` has a pre-existing SAMF instability (ufs-community/ccpp-physics#TBD); these
fixes leave its rate at develop's [HAFS 1a]. One of three WM PRs from the same issue (also #TBD Thompson/TEMPO,
#TBD FV3).

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 1a (SAMF, PBL, Noah-MP, sea ice, NSST, GFDL MP v3); update UFSATM and NOAHMP
  * UFSATM - SAMFCNV_32BIT compiles all SAMF files single precision
    * ccpp-physics - Bug fixes in SAMF, satmedmfvdifq, Noah-MP, sea ice, NSST, GFDL MP v3
  * NOAHMP - CCPP driver copy accepts the optional iter argument
```

## Git Tracking
### UFSWM:
* Closes #TBD (with 7b, 7c)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * ccpp-physics: ufs-community/ccpp-physics#TBD (SAMF + PBL), #TBD (Noah-MP), #TBD (sea ice, NSST), #TBD (GFDL MP v3)
* NOAHMP: NOAA-EMC/noahmp#TBD

## Changes
### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. [RT 1a]

### 7b. Track 1b: Thompson and TEMPO water fixes

## Description:
Seven independent, answer-changing bug fixes that close the water budget of Thompson microphysics and fix the same
mass-basis error in the TEMPO driver. Each fix is one commit, with the defect, fix and measured effect in the commit
message. In the regional and convection-allowing tests precipitation changes by −4 to +11 %; that is the fixes' own
signal: cloud water settling to the ground is now counted as precipitation (`regional_control` +11 %, the
atmosphere unchanged), and water that the graupel limiters and the mass-basis round trip created is no longer created
(−1 to −4 %). The ccpp-physics PRs give the attribution by fix. One of three WM PRs from the same issue.

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 1b (Thompson, TEMPO driver); update UFSATM
  * UFSATM - update ccpp-physics
    * ccpp-physics - Thompson water budget fixes; TEMPO driver mass basis
```

## Git Tracking
### UFSWM:
* Closes #TBD (with 7a, 7c)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * ccpp-physics: ufs-community/ccpp-physics#TBD (Thompson), #TBD (TEMPO driver)

## Changes
### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. [RT 1b]

### 7c. Track 1c: FV3 energy and tracer-mass fixes

## Description:
Six independent, answer-changing bug fixes in the FV3 dycore and its UFS driver: the `consv_te` fixer weight,
`fv_sg` energy, the mass physics heating is applied to, tracer thickness in `statein`, `prsl` gas constants, and
`inline_q` damping. Each is one commit in NOAA-GFDL/GFDL_atmos_cubed_sphere. One of three WM PRs from the same issue.

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 1c (FV3); update UFSATM
  * UFSATM - update atmos_cubed_sphere
    * atmos_cubed_sphere - consv_te weight, fv_sg energy, physics coupling mass, prsl constants, inline_q damping
```

## Git Tracking
### UFSWM:
* Closes #TBD (with 7a, 7b)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * atmos_cubed_sphere: NOAA-GFDL/GFDL_atmos_cubed_sphere#TBD

## Changes
### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. [RT 1c]

---

## 8. ccpp-physics issue: SAMF sub-cloud overshoot

**To:** ufs-community/ccpp-physics. @JongilHan66 (SAMF and `satmedmfvdifq`), @lisa-bengtsson (SAMF; #390 edits the
same file); cc @BinLiu-NOAA (the HAFS suite and its TKE). Linked from the WM issue.

**Title:** SAMF: sub-cloud mass flux exceeds the CFL limit (one-step heating up to 39 K on develop)

## Description
On develop (f1d68949, Hercules Intel), `hafs_global_1nest_atm` has 257–294 SAMF deep-convection steps per 6 h that
heat a layer by more than 4 K, up to 39 K in one 90 s step (three `consv_te`-perturbed members). Almost all are below
cloud base, at layer CFL > 1. With our round-1 fixes plus the SAMF fix below, the test crashes: one cell (35° S,
54° W, 3.8 km, a winter cold front) gains 70.7 K in one step, then `compute_qs: saturation vapor pressure table
overflow`.

**Mechanism** (print-only instrumentation):
1. Below cloud base `eta(k) = eta(k+1)/(1 + (xlamue − xlamud) dz)`, with `xlamue = clamt/z` and `xlamud = 0.001 clamt`.
   Above about 1 km detrainment exceeds entrainment, so for elevated convection (`kb` near 3 km) `eta` grows downward:
   1 at `kbcon`, 101 at `kb`.
2. The TKE scaling holds `clamt` at its cap (15 × `clam`) in about 3000 columns per 6 h. The overshoot feeds TKE (up
   to 3.4 × 10⁴ m²/s² in the same cells), which keeps `clamt` capped.
3. `xmbmax` (Han and Pan 2011, eq. 7) limits CFL only at `kbcon`, where `eta` = 1; the layers below reach CFL 24 (54 in
   the crash).

`samfshalcnv` has the same three pieces but produced no event above 4 K here. Sub-stepping SAMF's tracer transport
does not change the counts.

| `hafs_global_1nest_atm`, 6 h | develop | develop + option A |
|---|---|---|
| single-step heatings > 4 K | 257, 274, 294 | 0 |
| of which layer CFL > 1 | 253, 269, 291 | 0 |
| largest | 24.5, 24.1, 39.0 K | — |
| mean precipitation, mm/day | 2.4368 (members ±0.0005) | 2.4321 (−0.19 %) |
| max TKE at 6 h, m²/s² | 3.4 × 10⁴ | 450 |

**A related fix we are holding.** SAMF's cloud-base double-counting correction subtracts the TVD-limited value at `kb`
and `jmin` instead of what the updraft took (`qo`): SAMF creates 0.8 % of convective rain and a convected tracer loses
2 %/day (C96 `control_p8_ugwpv1`, 24 h). Our fix changes the moisture flux at `kb`, where the overshoots occur; here it
alone raises the count 1.7× and lowers precipitation 1.25 %, and with it one member crashed. We will submit it with,
or after, the option you choose.

## Options (we can test any)
- **A** Also bound `xmbmax` by `dp/(g·dt·eta)` for `kb ≤ k < kbcon` (10 lines; tested above).
- **B** Keep `eta` ≤ 1 below cloud base (no organized detrainment below `kbcon`, or a cap).
- **C** Bound the convective TKE source. With A, about 450 m²/s² remains at 3.5 km in the same cells. It comes from
  "include TKE contribution from deep convection" (and its shallow twin), which adds `0.5·σ·w_u²`, with
  `w_u = η·xmb/(σρ)`, once per call rather than as a rate: +383 m²/s² per 90 s step there, about as much as the PBL
  dissipates. With σ at its 0.03 floor that implies `w_u` ≈ 160 m/s.

## Questions
1. Which option, and for `samfshalcnv` too?
2. Is the convective TKE source meant to be added once per call (no `dt`), and should `w_u` be bounded?

*Contributors: Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author.*
