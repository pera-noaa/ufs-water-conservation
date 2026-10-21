# PR round 1: issue and PR descriptions (drafts)

*Drafts, not posted, except §8 (ufs-community/ccpp-physics#401, 20 Oct). Fill `#TBD` once opened; `[RT 0b]`, `[RT 0c]`, `[RT 1c]`, `[RT 1d]`, `[RT 1e]` once each track's run is in.
Round 1 posts in five tracks (`pr_round1.md`, *Tracks*), each with its own ufsatm and WM PR, in this order:

| Order | Track | PRs (sections) | Waits for |
|---|---|---|---|
| 0 | 0a issues | SAMF issue (§8), WM issue (§1), GFDL issue (§2) | — |
| 0 | 0b global conservation | ccpp-physics SAMF + PBL, Noah-MP, GFDL MP v3 (§3.1, §3.4, §3.6); ufsatm (§6a); WM (§7a) | SAMF: #390 |
| 0 | 0c microphysics | ccpp-physics Thompson, TEMPO driver (§3.2, §3.3); ufsatm (§6b); WM (§7b) | TEMPO: ccpp-physics#389 |
| 1 | 1c dycore | GFDL PR (§4); ufsatm (§6c); WM (§7c) | GFDL `dev/emc` merge; the SAMF issue's answer |
| 1 | 1d surface iteration, sea ice, NSST | ccpp-physics (§3.5); NOAA-EMC/noahmp (§5, `iter` form only); ufsatm (§6d); WM (§7d) | the SAMF issue's answer; the form |
| 1 | 1e Thompson, second forms | ccpp-physics (§3.7); ufsatm (§6e); WM (§7e) | 0c merged; the form |

Measurements: C96 `control_p8_ugwpv1`, 24 h, in-model budget meters, unless stated. Notes and data:
https://github.com/pera-noaa/ufs-water-conservation.*

---

## 1. ufs-weather-model issue

**Title:** Water, energy and tracer-mass conservation bugs in UFS physics and FV3 coupling

## Description
In-model budgets of a C96 `control_p8_ugwpv1` forecast show the physics creating water (+0.25 % of precipitation
per day; +0.45 % at C384) and losing 2 % per day of a convectively transported tracer; with the water fixed, the
atmosphere's energy budget still leaves +2.1 W/m² unexplained. We traced these to small, independent bugs in SAMF,
the PBL, Thompson (and the TEMPO driver), Noah-MP and its coupling, sea ice, NSST, GFDL MP v3, the SAMF
single-precision build, and the FV3 driver and dycore. This round fixes 37; the SAMF cloud-base fix waits on
ufs-community/ccpp-physics#401.

### To Reproduce:
Any P8 forecast; the budget residuals need meters. Two defects are visible without them:
- `control_p8_mynn` with layout 3×8 and 4×6 differs in 90 of 126 `atmf024` variables (SAMF early returns before
  the cellular-automaton trigger).
- With `frac_grid`, Noah-MP steps 24–27 % of land twice per time step (land gains 3–5 % of global precipitation).

## Additional context
Fixes, one commit each, in five WM PRs, all answer-changing. Now: ufs-community/ufs-weather-model#TBD (SAMF, PBL,
Noah-MP, GFDL MP v3, SAMF single precision) and #TBD (Thompson, TEMPO driver), with their ccpp-physics, NOAA-EMC/noahmp
and NOAA-EMC/ufsatm PRs. After the SAMF overshoot (ufs-community/ccpp-physics#401), which `hafs_global_1nest_atm` is
sensitive to: land and sea ice stepped once per time step, sea ice and NSST (ccpp-physics), and FV3
(NOAA-GFDL/GFDL_atmos_cubed_sphere). Then three Thompson fixes that have a second reasonable form.
Notes and data: https://github.com/pera-noaa/ufs-water-conservation.

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
> GNU `rt.sh` on Hercules: see this track's ufs-community/ufs-weather-model#TBD ([RT 0b], [RT 0c] or [RT 1d]). With all
> round-1 fixes together: none fails to run; reproducibility (restart, decomposition, threading; `rt.sh -c` then
> `-m`) 123 of 123 bitwise. Effects are from in-model budget meters, C96, 24 h.
>
> **Documentation:** none needed.
>
> **Issue:** ufs-community/ufs-weather-model#TBD
>
> **Contributors:** Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

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

Overlaps ufs-community/ccpp-physics#390 in one block; whichever merges second needs a rebase. Ours onto #390 is ready.

### 3.2 Thompson

**Title:** Thompson: water-budget fixes (mass basis, graupel re-closure, density, layer depth)

## Description of Changes:
Four fixes in `mp_thompson`/`module_mp_thompson`, one commit each. Sizes are fractions of grid-scale
precipitation.

| Fix | Bug | Effect |
|---|---|---|
| Mass basis | humidity converted in with `1/(1-q_v)`, back with `1/(1+r_v,new)` | removes 0.4 % |
| Graupel | graupel gains not recomputed after the rate limiters | creates 0.76 % (first 6 h) |
| Density | density recomputed after latent heating, before sedimentation | removes 0.11 % |
| Layer depth | `dz` from heights computed before convection | removes 0.014 % (new argument `prsi`, already in the hosts) |

In the regional and convection-allowing tests (3 km, 1–6 h cold starts), the four fixes on develop (with the TEMPO
driver fix, which acts only in TEMPO suites):

| Test | Precipitation |
|---|---|
| `regional_spp_sppt_shum_skeb` | −5.3 % |
| `cpld_regional_atm_fbh` | −3.0 % |
| `conus13km_gl_inline` | −2.5 % |
| `regional_control`, `gnv1_nested` | −1.4 % |
| HRRR/RAP debug (1 h) | −0.9 to −1.3 % |

Each fix alone: the graupel re-closure −1.0 to −4.1 %, the mass basis up to −2.0 %, the others ≤ 1.1 %: water these
terms created.

Noise (one-ulp perturbation): ≤ 0.24 %. The graupel fix removes water created during spin-up, largest in these
short cold starts (0.76 % in the first 6 h at C96).

Three more Thompson water fixes follow in a separate PR, because each has a second reasonable form: cloud water
settling out of the lowest layer, clipped condensate, and water at or below R1.

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

Overlaps ufs-community/ccpp-physics#389 in one block; whichever merges second needs a rebase. Ours onto #389 is ready.

### 3.4 Noah-MP

**Title:** Noah-MP: water and energy bugs in the driver, coastal snow, snow initialisation, truncations, snow layers

## Description of Changes:
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

Noah-MP's coastal land is also stepped twice per time step with `frac_grid`; that fix follows with its sea-ice twin
(the same cause, two tested forms).

## Dependencies:
ufs-community/ufs-weather-model#TBD

### 3.5 Surface iteration, sea ice and NSST

**Title:** Land and sea ice stepped once per time step; sea-ice heat divided by Δt twice, flooded-snow heat, NSST rain units

## Description of Changes:
Five fixes, one commit each.

| Fix | Bug | Effect |
|---|---|---|
| Land once per step | with `frac_grid`, coastal land is re-flagged and stepped again on the second surface iteration (24–27 % of land, every step) | land gains 3–5 % of global precipitation |
| Ice once per step | NSST re-flags icy cells for the second iteration; ice stepped again (1.9 % of ice column-steps) | calls per column-step 1.0186 → 1.0000 |
| Excess heat | `ice3lay` divides J/m² by `li*delt` | deletes (1 − 1/Δt) of it; thin ice near melting |
| Flooded snow | becomes ice at the layers' T, not with its −li heat content | −7.9 × 10⁻³ → 10⁻¹³ W/m² |
| NSST rain | `rain` (m per step) used as kg m⁻² s⁻¹ in `qrain` and `sep` | rain heat flux × 1000/720 at Δt 720 s |

Together (sea ice, NSST): ice thickness rms 1.7 × 10⁻³ m (noise 8 × 10⁻⁵); other fields at noise.

The two once-per-step fixes have one cause: `GFS_surface_loop_control_part2` re-flags a cell for the water's second
pass when the cell is also Noah-MP land or icy, and Noah-MP and `sfc_sice` step it again. Two forms, equivalent within
noise in the global P8 tests (land and ice state, precipitation, 3-D T):
- (a) do not re-flag those cells in that clause (for ice, the clause's commented-out original, `.not. icy`): one
  line, no interface change. The water part of those cells loses its low-wind second NSST pass.
- (b) an optional `iter` (`ccpp_loop_counter`) argument in `noahmpdrv` and `sfc_sice`; NOAA-EMC/noahmp's copy of the
  driver must declare it too, or `control_p8_atmlnd` crashes.

We prefer (a). Which do you want?

## Dependencies:
ufs-community/ufs-weather-model#TBD (7d); in form (b), NOAA-EMC/noahmp#TBD. Waits for ufs-community/ccpp-physics#401
(SAMF overshoot): with the track-0b fixes the four sea-ice/NSST fixes raised the `hafs_global_1nest_atm` crash rate
(3 of 20 members against 0 of 20).

### 3.6 GFDL MP v3

**Title:** GFDL MP v3: convert back on the input mass basis; rain sediments with c_liq

## Description of Changes:

| Fix | Bug | Effect (`control_iovr4_gfdlmpv3`) |
|---|---|---|
| Mass basis | in with `1/(1-q_v,in)`, back with `1/(1+q_v,new)` | removes 1.03 % of microphysics precipitation |
| Sedimentation heat | rain and cloud water fall with `c_ice` | +0.20 → −0.007 W/m² |

## Dependencies:
ufs-community/ufs-weather-model#TBD


### 3.7 Thompson: fixes with a second form (track 1e)

**Title:** Thompson: settled cloud water, clipped condensate and sub-R1 water

## Description of Changes:
Three water fixes on top of ufs-community/ccpp-physics#TBD (the four Thompson fixes), one commit each. Each conserves
water and has a second reasonable form; which do you prefer?

| Fix | Bug | This PR | Other form | Effect |
|---|---|---|---|---|
| Settled cloud water | cloud water sedimenting out of the lowest layer is added to no precipitation total; cloud sedimentation takes one full step where `vtck*DT > dz` | count it as rain; substep cloud sedimentation like the other species | keep it in the lowest layer | removes 0.15 %; `regional_control` reported precipitation +10.9 % (other form +4.8 %), the atmosphere unchanged |
| Clipped condensate | hydrometeors ending the step negative or below R1 are set to zero; vapour is floored at 10⁻¹⁰ | to vapour with its latent heat; the floor refilled from the layer's condensate, then the column's vapour | return the clipped condensate only, leave the floor | creates 0.002 % |
| Sub-R1 water | water at or below R1 deleted on entry, in `semi_lagrange_sedim` and for leftover rain | to vapour with its latent heat; `semi_lagrange_sedim` returns what it does not move | the entry and leftover rain only | removes 2 × 10⁻⁸ |

Sizes are fractions of grid-scale precipitation. Cloud water reaching the ground is water reaching the ground, so we
count it; keeping it in the air also conserves water.

## Dependencies:
ufs-community/ccpp-physics#TBD (Thompson); ufs-community/ufs-weather-model#TBD (7e)
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

## 5. NOAA-EMC/noahmp PR (base `develop`; track 1d, form (b) only)

**Title:** CCPP driver copy: accept the optional `iter` argument

Companion of ufs-community/ccpp-physics#TBD, which steps Noah-MP land once per time step through a new optional
`iter` argument of `noahmpdrv_run`. In atmosphere–land builds the land component is compiled against this copy's
interface but calls the ccpp-physics routine; without `iter` declared here, `control_p8_atmlnd` crashes. Declares
the same optional `iter` in `drivers/ccpp/noahmpdrv.F90` and `.meta`. Tested in
ufs-community/ufs-weather-model#TBD (`atml` build, land-component tests).

---

## 6. NOAA-EMC/ufsatm PRs (base `develop`), one per track

### 6a. Track 0b: SAMF32 build fix and the 0b physics

## Description
- `ccpp/CMakeLists.txt`: `-DSAMFCNV_32BIT=ON` (#1133) compiled 2 of SAMF's 5 files single precision: the filter
  searched the scheme files only, and `mo_conv_kind.F90`, `progsigma_calc.f90`, `progomega_calc.f90` are capgen
  dependencies, so `conv_wp` stayed 8-byte. Now all 5; configure stops if only some are found. @rhaesung
- Updates `ccpp/physics` for the track-0b fixes: SAMF + PBL, Noah-MP, GFDL MP v3.

Answers change: the physics fixes in the suites that use them, and SAMF is now really single precision in the
`_conv32` tests.

### Issue(s) addressed
- ufs-community/ufs-weather-model#TBD

## Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD (7a). Baselines change.

## Dependencies
ufs-community/ccpp-physics#TBD (SAMF + PBL), #TBD (Noah-MP), #TBD (GFDL MP v3)

### 6b. Track 0c: Thompson and TEMPO

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

### 6d. Track 1d: surface iteration, sea ice and NSST

## Description
Updates `ccpp/physics` for the surface-iteration, sea-ice and NSST fixes. No code change in ufsatm. Answers change
in the suites with `frac_grid` Noah-MP land, fractional sea ice or NSST.

### Issue(s) addressed
- ufs-community/ufs-weather-model#TBD

## Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD (7d). Baselines change.

## Dependencies
ufs-community/ccpp-physics#TBD (sea ice, NSST); after ufs-community/ccpp-physics#401 (SAMF overshoot)


### 6e. Track 1e: Thompson, second forms

## Description
Updates `ccpp/physics` for the three Thompson fixes with a second form (settled cloud water, clipped condensate,
sub-R1 water). No code change in ufsatm. Answers change in the Thompson suites.

### Issue(s) addressed
- ufs-community/ufs-weather-model#TBD

## Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD (7e). Baselines change.

## Dependencies
ufs-community/ccpp-physics#TBD (Thompson, second forms)
---

## 7. ufs-weather-model PRs (base `develop`), one per track

Common to 7a–7e:

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

### 7a. Track 0b: global conservation fixes

## Description:
18 independent, answer-changing bug fixes that remove water, energy and tracer-mass errors in SAMF, the PBL,
Noah-MP, GFDL MP v3 and the SAMF single-precision build. Each fix is one commit in its subcomponent, with the
defect, fix and measured effect in the commit message. Largest effects: SAMF drops the heat of fusion of the ice it
detrains (0.42 W/m²); GFDL MP v3 creates 1.03 % of its precipitation; `control_p8_mynn` depends on the
decomposition. In the global tests the mean 3-D temperature rises 0.001–0.006 K and precipitation changes by −0.3 to
+0.3 %: the heat of fusion SAMF was dropping (0.42 W/m²), restored. `hafs_global_1nest_atm` has a pre-existing SAMF instability (ufs-community/ccpp-physics#401); with
these fixes it crashes in 0 of 20 perturbed members, as develop. One of five WM PRs from the same issue.

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 0b (SAMF, PBL, Noah-MP, GFDL MP v3); update UFSATM
  * UFSATM - SAMFCNV_32BIT compiles all SAMF files single precision
    * ccpp-physics - Bug fixes in SAMF, satmedmfvdifq, Noah-MP, GFDL MP v3
```

## Git Tracking
### UFSWM:
* Addresses #TBD (with the other round-1 WM PRs; the last to merge closes it)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * ccpp-physics: ufs-community/ccpp-physics#TBD (SAMF + PBL), #TBD (Noah-MP), #TBD (GFDL MP v3)

## Changes
### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. [RT 0b]

### 7b. Track 0c: Thompson and TEMPO water fixes

## Description:
Five independent, answer-changing bug fixes that close water-budget errors in Thompson microphysics and fix the
same mass-basis error in the TEMPO driver. Each fix is one commit, with the defect, fix and measured effect in the
commit message. In the regional and convection-allowing tests precipitation falls by 0.9–5.3 %
(`regional_wofs_tempo` 2.0 %): water that the graupel limiters and the mass-basis round trips created is no
longer created. The ccpp-physics PRs give the attribution by fix. One of five WM PRs from the same issue.

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 0c (Thompson, TEMPO driver); update UFSATM
  * UFSATM - update ccpp-physics
    * ccpp-physics - Thompson water budget fixes; TEMPO driver mass basis
```

## Git Tracking
### UFSWM:
* Addresses #TBD (with the other round-1 WM PRs; the last to merge closes it)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * ccpp-physics: ufs-community/ccpp-physics#TBD (Thompson), #TBD (TEMPO driver)

## Changes
### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. [RT 0c]

### 7c. Track 1c: FV3 energy and tracer-mass fixes

## Description:
Six independent, answer-changing bug fixes in the FV3 dycore and its UFS driver: the `consv_te` fixer weight,
`fv_sg` energy, the mass physics heating is applied to, tracer thickness in `statein`, `prsl` gas constants, and
`inline_q` damping. Each is one commit in NOAA-GFDL/GFDL_atmos_cubed_sphere. One of five WM PRs from the same issue.

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 1c (FV3); update UFSATM
  * UFSATM - update atmos_cubed_sphere
    * atmos_cubed_sphere - consv_te weight, fv_sg energy, physics coupling mass, prsl constants, inline_q damping
```

## Git Tracking
### UFSWM:
* Addresses #TBD (with the other round-1 WM PRs; the last to merge closes it)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * atmos_cubed_sphere: NOAA-GFDL/GFDL_atmos_cubed_sphere#TBD

## Changes
### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. [RT 1c]

---

### 7d. Track 1d: surface-iteration, sea-ice and NSST fixes

## Description:
Five independent, answer-changing bug fixes: `frac_grid` Noah-MP land and sea ice stepped twice per time step (one
cause, in the surface loop control), sea-ice excess heat divided by Δt twice, flooded snow joining the ice without its heat content, and NSST rain used in the
wrong units. Each is one commit, with the defect, fix and measured effect in the commit message. Posted after the
SAMF overshoot is bounded (ufs-community/ccpp-physics#401): with the track-0b fixes, these raised the
`hafs_global_1nest_atm` crash rate. One of five WM PRs from the same issue.

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 1d (surface iteration, sea ice, NSST); update UFSATM
  * UFSATM - update ccpp-physics
    * ccpp-physics - land and ice stepped once per time step; sfc_sice and sfc_nst bug fixes
```

## Git Tracking
### UFSWM:
* Addresses #TBD (with the other round-1 WM PRs; the last to merge closes it)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * ccpp-physics: ufs-community/ccpp-physics#TBD (sea ice, NSST)

## Changes
### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. [RT 1d]


### 7e. Track 1e: Thompson fixes with a second form

## Description:
Three answer-changing Thompson water fixes, each conserving and each with a second reasonable form, on top of
track 0c: settled cloud water counted as precipitation (and cloud sedimentation substepped), clipped condensate and
water at or below R1 returned to vapour with their latent heat. `regional_control` reported precipitation rises
10.9 %: cloud water reaching the ground, now counted; the atmosphere is unchanged. One of five WM PRs from the same
issue.

### Commit Message:
```
* UFSWM - Round-1 conservation bug fixes, track 1e (Thompson settled cloud water, clipping, R1); update UFSATM
  * UFSATM - update ccpp-physics
    * ccpp-physics - Thompson: settled cloud water, clipped condensate and sub-R1 water conserved
```

## Git Tracking
### UFSWM:
* Addresses #TBD (with the other round-1 WM PRs; the last to merge closes it)

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD
  * ccpp-physics: ufs-community/ccpp-physics#TBD (Thompson, second forms)

## Changes
### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. [RT 1e]
---

## 8. ccpp-physics issue: SAMF sub-cloud overshoot (track 0a; posted as ufs-community/ccpp-physics#401)

**To:** ufs-community/ccpp-physics, bug-report template. @JongilHan66 (SAMF and `satmedmfvdifq`), @lisa-bengtsson
(SAMF; #390 edits the same file); cc @BinLiu-NOAA (the HAFS suite and its TKE). Posted first; linked from the WM issue.

**Title:** SAMF: sub-cloud mass flux exceeds the CFL limit

# Description

In `samfdeepcnv.f`, `xmbmax` (Han and Pan 2011, eq. 7) keeps the layer CFL ≤ 1 only at `kbcon`, where `eta` = 1.
Below cloud base `eta` can exceed 1 (101 at `kb` for elevated convection), so layers from `kb` to `kbcon` reach CFL
24 and heat by tens of kelvin in one step: on develop (f1d68949), `hafs_global_1nest_atm` has 257–351 layer-steps
above 4 K per 6 h, up to 52 K (20 perturbed members).

Develop survives, but only just: small, unrelated answer changes push the tail past the limit, and the test stops
with `compute_qs: saturation vapor pressure table overflow` after one cell gains about 70 K in a step. 24 of our
water/energy bug fixes, none touching `xmbmax`, crashed it in 3 of 20 members, the unperturbed RT member included;
develop crashed in none.

Expected: CFL ≤ 1 in every layer, as at `kbcon`. `samfshalcnv.f` has the same code but no event
above 4 K here.

### Possible fixes (we can test any)
- **A. Bound `xmb` by the CFL limit in every updraft layer** (tested, works): eq. 7 with the local `eta`, from `kb` to
  `ktcon`, not only at `kbcon`:
  ```fortran
  !  keep CFL <= 1 in every updraft layer, kb to ktcon, not only at kbcon (eta can exceed 1 there)
        do k = 1, km
          do i = 1, im
            if(cnvflg(i) .and. k >= kb(i) .and. k < ktcon(i)) then
              dp = 1000.0_conv_wp * del(i,k)
              xmbmax(i) = min(xmbmax(i), dp /
       &        (real(grav, kind=conv_wp) * dt2 * eta(i,k)))
            endif
          enddo
        enddo
  ```
  No crash in 40 members (develop and the 24 fixes), at most one layer-step above 4 K per member (≤ 4.8 K, CFL ≤ 0.9),
  precipitation −0.18 % (*Output*). Bounding only `kb ≤ k < kbcon` gives the same statistics in all 40 members: every
  binding layer is below cloud base.
- **B. Keep the vapour positive** (tested, does not help): cap `xmb` so that no layer loses more vapour in one step
  than it holds. Event counts stay at develop's, and the 24 fixes still crash 1 of 20 members.
- **C. Keep `eta` ≤ 1 below cloud base**: no organized detrainment below `kbcon`, or a cap.
- **D. Apply the convective tendencies implicitly, or sub-step them**, so they stay stable at CFL > 1. Sub-stepping
  only the tracer transport does not change the counts; heat and moisture would have to be included.
- **E. Bound the convective TKE source** (with any of the above). "include TKE contribution from deep convection" (and
  its shallow twin) adds `0.5·σ·w_u²`, `w_u = η·xmb/(σρ)`, once per call, not as a rate. With a CFL bound it still adds
  +383 m²/s² per 90 s step at 3.5 km in these cells, about what the PBL removes: `w_u` ≈ 160 m/s at σ's 0.03 floor.
  Alternatively, take `clamt`'s TKE scaling from the TKE before convection, so the overshoot cannot hold its own
  entrainment at the cap.

### Questions
1. Which option, and for `samfshalcnv` too?
2. Is the convective TKE source meant to be added once per call (no `dt`), and should `w_u` be bounded?
3. Would you take the bound as its own PR, ahead of other SAMF changes? We can open it.

## Steps to Reproduce

1. Insert the print-only block
   [`dbg4_deep.f`](https://github.com/pera-noaa/ufs-water-conservation/blob/main/proposal/hafs_samf/dbg4_deep.f) in
   `samfdeepcnv.f` before "Negative moisture is set to zero after borrowing" (one `DBGSAMF` line per layer heated
   > 4 K; bitwise the official baseline) and build develop (f1d68949) with the `hafsw` compile in `rt.conf`.
2. Run `hafs_global_1nest_atm` as `rt.sh` sets it up (6 h, about 2.5 min on 6 nodes); more members: `consv_te` =
   0.999, 0.998, … in `input.nml`.
3. Count the `DBGSAMF` lines
   ([`q_stats.py`](https://github.com/pera-noaa/ufs-water-conservation/blob/main/proposal/hafs_samf/q_stats.py)):
   257–351 per member on develop, up to 52 K, almost all at `kb ≤ k < kbcon` with CFL > 1.
4. For the crash, add a small answer change, e.g. our SAMF + PBL, Noah-MP, sea-ice/NSST and GFDL MP v3 patches
   ([`pr_round1_patches/`](https://github.com/pera-noaa/ufs-water-conservation/tree/main/proposal/pr_round1_patches)):
   3 of 20 members stop with the overflow, `consv_te` = 1 included.

## Additional Context

* Machine: Hercules (MSU)
* Compiler: Intel Fortran Classic 2021.13.1 (`rt.sh`)
* Suite Definition File or Scheme: `FV3_HAFS_v1_gfdlmp_tedmf` (`hafs_global_1nest_atm`; `dt_atmos` 90 s,
  `progsigma` false); `samfdeepcnv`, and `samfshalcnv` (same code)
* Related: #82 (2023), the same `compute_qs` overflow in a 25 km RRFS run with GFS v17 P8 physics, cured by a shorter
  `DT_ATMOS` or `samfdeepcnv.f`'s `cq` back at 1.3; both shrink what one SAMF step can move. #390 edits
  `samfdeepcnv.f`.

**Why `eta` grows and stays large.** Below cloud base `eta(k) = eta(k+1)/(1 + (xlamue − xlamud) dz)`, with
`xlamue = clamt/z` and `xlamud = 0.001 clamt`. Above about 1 km detrainment exceeds entrainment, so for elevated
convection (`kb` near 3 km) `eta` grows downward: 1 at `kbcon`, 101 at `kb`. The TKE scaling holds `clamt` at its cap
(15 × `clam`) in about 3000 columns per 6 h, and the overshoot feeds TKE (column means up to 2.4 × 10⁶ m²/s² in 20 members), which
keeps it capped. Sub-stepping SAMF's tracer transport does not change the counts.

**Fixes we are holding.** SAMF's cloud-base double-counting correction subtracts the TVD-limited value at `kb` and
`jmin` instead of what the updraft took (`qo`): SAMF creates 0.8 % of convective rain and a convected tracer loses
2 %/day (C96 `control_p8_ugwpv1`, 24 h). Our fix changes the moisture flux at `kb`, where the overshoots are, and here
raises the event count 1.7×; it will follow the option you choose. Our sea-ice/NSST and FV3 fixes also wait for the
bound.

Data, scripts and instrumentation:
https://github.com/pera-noaa/ufs-water-conservation/tree/main/proposal/hafs_samf

## Output

The crash (the 24 fixes, `consv_te` = 1):
```
FATAL from PE 0: compute_qs: saturation vapor pressure table overflow, nbad= 1
```
Its largest event: layer 18 (`kb` 17, `kbcon` 22) heats 72.8 K and loses 30.2 g/kg of vapour in one step, at CFL
14.3, `eta` 12.2, `xmb` = `xmbmax` (re-spaced):
```
DBGSAMF  i k kb kbcon jmin ktcon  dT(K)      dq(g/kg)   xmb        xmbmax     CFL        eta        del        TKE        clamt
DBGSAMF 16 18 17 22 27 28  7.283E+01 -3.020E+01  3.962E+00  3.962E+00  1.430E+01  1.217E+01  2.976E+00  5.961E+02  1.500E+00
```

Crash rate (6 h; members `consv_te` = 1, 0.999, …):

| Run | Members | Crashed | With a step > 60 K | Largest step per member: median, max |
|---|---|---|---|---|
| develop | 20 | 0 | 0 | 31 K, 52 K |
| + 24 fixes (SAMF, PBL, Noah-MP, sea ice/NSST, GFDL MP, SAMF build) | 20 | **3**, the RT member included | 4 | 40 K, 73 K |
| the 24 minus sea ice/NSST (4) | 20 | 0 | 0 | 32 K, 48 K |
| + all 37 fixes | 10 | 1 | 1 | 33 K, 74 K |

Event counts and precipitation overlap develop's throughout. No single fix stands out: without PBL05, the NSST rain
fix or the three sea-ice fixes, the 24 each crash 0 of 10.

The options (6 h, 20 members each; event counts and largest step over the finished members):

| | develop | + A | + B | the 24 fixes | + A | + B |
|---|---|---|---|---|---|---|
| crashed | 0 | 0 | 0 | 3 | 0 | 1 |
| layer-steps heated > 4 K, per member | 257–351 | 0–1 | 246–384 | 241–369 | 0–1 | 252–344 |
| of which layer CFL > 1, all members | 5769 | 0 | 5839 | 5009 | 0 | 5541 |
| largest step | 52.0 K | 4.8 K | 42.2 K | 64.2 K | 4.5 K | 44.0 K |
| largest column-mean TKE where `clamt` is capped, m²/s² | 2.4 × 10⁶ | 434 | 2.3 × 10⁶ | 1.2 × 10⁶ | 417 | 2.3 × 10⁶ |
| mean precipitation, mm/day | 2.4370 | 2.4327 (−0.18 %) | 2.4372 | 2.4365 | 2.4324 (−0.17 %) | 2.4364 |

*Contributors: Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author.*
