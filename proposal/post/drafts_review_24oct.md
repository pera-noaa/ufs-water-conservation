# Cleaned phase-0 drafts (24 Oct)

Nothing here is posted. `#TBD-…` and `[RT 0b]` are filled when posting (see `bodies_v2/README.md`).

---

## SAMF + PBL (ccpp-physics) — held until Han/Lisa respond

### Description of Changes:
Four bug fixes in SAMF convection and the `satmedmfvdifq` PBL, one commit each. All change answers.

| Fix | What goes wrong | Effect |
|---|---|---|
| Ice fusion heat (deep and shallow) | Detrained condensate is split into ice without releasing the heat of fusion | Deep convection loses 0.42 W/m² (shallow 0.018); with the fix, 10⁻¹³. The upper troposphere (500–200 hPa) warms 0.016 K. |
| Wet deposition (deep) | Scavenging is booked with `eta(k−1)` but removed with `eta(k)`, and is erased in the negative-value borrowing branch | Scavenged tracer and deposition do not add up: −7.4 × 10⁻⁴ per day → 3 × 10⁻¹⁵ |
| PBL surface fluxes (`satmedmfvdifq`) | Kinematic surface fluxes are applied with `1/Δz` instead of the layer mass, `ρ g/δp` | `FV3_GFS_v16`: water 2.6 × 10⁻⁸ → 4 × 10⁻¹⁶ kg/m²/day; last bit only in P8 |
| Cellular-automaton trigger (deep) | Six early returns can exit before `ca_trigger` switches a column back on, so results depend on the domain decomposition | `control_p8_mynn`, layout 3×8 vs 4×6: 90 of 126 variables differ → 0 |

New argument: `hfus` (`latent_heat_of_fusion_of_water_at_0C`, already provided by the hosts).

### Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR, the Noah-MP fixes and the GFDL MP v3 fixes, 23 October 2026 (develop 5651397d, baselines 20261016). [RT 0b] The log will be in the ufs-weather-model PR that follows review. Effects are from budget meters added to the model (C96 `control_p8_ugwpv1`, 24 h).

### Dependencies:
Rebased onto `ufs/dev` after #390; one block in `samfdeepcnv.f` was re-resolved around its `progomega` guards. #403 adds arguments to `samfdeepcnv_run` beside ours (`hfus`); whichever merges second needs a one-block rebase. The SAMF cloud-base fix is separate (#405).

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#3404

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## Noah-MP (ccpp-physics) — stage 1

### Description of Changes:
Seven bug fixes in Noah-MP and the code that couples it to the atmosphere, one commit each. Each commit message gives the defect, the fix and the measured effect. All change answers in suites that use Noah-MP.

| Fix | What goes wrong | Effect |
|---|---|---|
| Evaporation hand-off (`noahmpdrv`) | The atmosphere receives Noah-MP's latent heat divided by the host's `con_hvap`, not the water Noah-MP removed. The two use different latent heats. | The atmosphere gains 0.07–0.10 % of global precipitation more water than the land loses |
| Coastal snow (`GFS_surface_composites_pre`) | With `frac_grid`, the land's snow is overwritten with the cell mean every step | Thin coastal snow is lost |
| Snow initialisation (`GFS_phys_time_vary`) | With `frac_grid`, cold-start snow layers are built from the cell-mean snow | 0.29 kg/m² of land snow lost at the first step |
| Snow layer count (`combine`) | Tests `isnow_old` instead of `isnow` (NCAR/noahmp#47) | Up to 0.16 mm of water and 8.5 MJ/m² per occurrence |
| Snow layer heat (3 commits: `combine`, `csnow`, `combo`) | Merged layers keep the receiver's temperature; layers that vanish drop their heat; heat capacities are computed per volume from capped volume fractions but used per kg | Noah-MP's soil energy residual 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ W/m², measured together with a thin-snow fix that is held for later |

Related fixes come later, separately:
- With `frac_grid`, coastal land is stepped twice per time step. Sea ice has the same cause, and both have two tested forms.
- Fixes where the destination of the water or heat is a judgement: truncated thin snow, truncated canopy water, the heat of a melted-out snow layer, and Noah-MP's own latent heats.

### Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR, the SAMF/PBL fixes and the GFDL MP v3 fixes, 23 October 2026 (develop 5651397d, baselines 20261016). [RT 0b] The log will be in the ufs-weather-model PR that follows review. Effects in the table are from budget meters added to the model (C96 `control_p8_ugwpv1`, 24 h).

### Dependencies:
None. The ufs-weather-model PR, with the RT log, follows review.

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#3404

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## GFDL MP v3 (ccpp-physics) — stage 1

### Description of Changes:
Two bug fixes in GFDL MP v3, one commit each. Both change answers in the GFDL MP v3 suites.

| Fix | What goes wrong | Effect (`control_iovr4_gfdlmpv3`) |
|---|---|---|
| Mass basis | Species are converted to mixing ratio with `1/(1 − q_v)` using the input vapour, but back with `1/(1 + q_v)` using the updated vapour, so the round trip does not return the mass it started with | The bug creates 1.03 % of the microphysics precipitation |
| Sedimentation heat | Falling rain and cloud water carry the heat capacity of ice (`c_ice`) instead of liquid water (`c_liq`) | Energy residual +0.20 → −0.007 W/m² |

### Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR, the SAMF/PBL fixes and the Noah-MP fixes, 23 October 2026 (develop 5651397d, baselines 20261016). [RT 0b] The log will be in the ufs-weather-model PR that follows review. Effects are from budget meters added to the model (24 h).

### Dependencies:
None. The ufs-weather-model PR, with the RT log, follows review.

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#3404

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## Thompson (ccpp-physics) — stage 1

### Description of Changes:
Four bug fixes in `mp_thompson` and `module_mp_thompson`, one commit each. Each bug makes Thompson create or remove water. Sizes below are fractions of grid-scale precipitation (C96 `control_p8_ugwpv1`, 24 h).

| Fix | What goes wrong | Water the bug creates (+) or removes (−) |
|---|---|---|
| Mass basis | Humidity is converted to mixing ratio with `1/(1 − q_v)`, but back with `1/(1 + r_v)` using the updated vapour | −0.4 % |
| Graupel | Graupel gains are not recomputed after the rate limiters | +0.76 % in the first 6 h, +0.03 % after |
| Density | Air density is recomputed after latent heating, before sedimentation | −0.11 % |
| Layer depth | Layer thickness comes from heights computed before convection; it now uses `prsi` (already provided by the hosts) | −0.014 % |

The effect is larger in the short, high-resolution regional tests (3 km, 1–6 h cold starts). Precipitation with the four fixes, together with the TEMPO driver fix (which acts only in TEMPO suites):

| Test | Precipitation |
|---|---|
| `regional_spp_sppt_shum_skeb` | −5.3 % |
| `cpld_regional_atm_fbh` | −3.0 % |
| `conus13km_gl_inline` | −2.5 % |
| `regional_control`, `gnv1_nested` | −1.4 % |
| HRRR/RAP debug (1 h) | −0.9 to −1.3 % |

Most of this is the graupel fix (−1.0 to −4.1 % alone) and the mass basis (up to −2.0 %): water the bugs created during spin-up. Noise from a one-bit perturbation is ≤ 0.24 %.

Three more Thompson fixes follow in a separate PR, because each has a second reasonable form: cloud water settling out of the lowest layer, clipped condensate, and water at or below the `R1` threshold.

### Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR and the TEMPO driver fix, 23 October 2026 (develop 5651397d, baselines 20261016): all 54 builds compile; 57 tests are identical, 150 change answers, and 25 restart tests did not start because their parent tests change answers; none fails to run. The log will be in the ufs-weather-model PR that follows review. Effects are from budget meters added to the model.

### Dependencies:
None. The ufs-weather-model PR, with the RT log, follows review.

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#3404

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## TEMPO driver (ccpp-physics) — after #389, or with Thompson

### Description of Changes:
One bug fix in the TEMPO driver (`mp_tempo`). It has the same mass-basis bug as `mp_thompson`, fixed in #TBD-PR_TH: species are converted to mixing ratio with `1/(1 − q_v)` and back with `1/(1 + r_v)` using the updated vapour, while the host rebuilds the layer mass from the old `q_v`. The fix uses the input humidity in both directions.

| Test | Precipitation |
|---|---|
| `regional_wofs_tempo` (3 km) | −1.96 % (noise 0.34 %) |

Where there is net condensation, the old round trip created water, so the fix lowers precipitation there.

The fix also exposes TEMPO's own water residual (+0.33 % of grid-scale precipitation in `control_p8_ugwpv1_tempo`), which the driver error was cancelling. Fixes for that are proposed to NCAR/TEMPO separately.

### Tests Conducted:
Intel and GNU on Hercules: full `rt.sh` with this PR and the Thompson fixes, 23 October 2026 (develop 5651397d, baselines 20261016): all 54 builds compile; 57 tests are identical, 150 change answers, and 25 restart tests did not start because their parent tests change answers; none fails to run. The log will be in the ufs-weather-model PR that follows review.

### Dependencies:
Overlaps #389 in one block; whichever merges second needs a one-block rebase. Ours onto #389 is ready.

### Documentation:
None needed.

### Issue (optional):
ufs-community/ufs-weather-model#3404

### Contributors (optional):
Lori Bruhwiler (NOAA GML). AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit).

---

## ufsatm track 0b — after review, as draft

### Description
- `ccpp/CMakeLists.txt`: with `-DSAMFCNV_32BIT=ON` (#1133), only 2 of SAMF's 5 source files were compiled in single precision. The filter searched the scheme files only, but `mo_conv_kind.F90`, `progsigma_calc.f90` and `progomega_calc.f90` are capgen dependencies, so `conv_wp` stayed 8-byte. Now all 5 are, and configure stops if only some are found. @rhaesung
- Updates `ccpp/physics` for the track-0b fixes: SAMF + PBL, Noah-MP, GFDL MP v3.

Answers change: the physics fixes in the suites that use them, and SAMF is now really single precision in the `_conv32` tests.

### Issue(s) addressed
- ufs-community/ufs-weather-model#3404

### Testing
Intel and GNU on Hercules: full `rt.sh`, log in ufs-community/ufs-weather-model#TBD-WM_0b. Baselines change.

### Dependencies
ufs-community/ccpp-physics#TBD-PR_SAMF (SAMF + PBL), #TBD-PR_NM (Noah-MP), #TBD-PR_GMP (GFDL MP v3)

---

## ufsatm track 0c — after review, as draft

### Description
Updates `ccpp/physics` for the Thompson and TEMPO-driver fixes. No code change in ufsatm. Answers change in the Thompson and TEMPO suites.

### Issue(s) addressed
- ufs-community/ufs-weather-model#3404

### Testing
Intel and GNU on Hercules: full `rt.sh`, log in ufs-community/ufs-weather-model#TBD-WM_0c. Baselines change.

### Dependencies
ufs-community/ccpp-physics#TBD-PR_TH (Thompson), #TBD-PR_TP (TEMPO driver)

---

## ufs-weather-model track 0b — after review, as draft

### Commit Queue Requirements:
- [x] This PR addresses a relevant WM issue: #3404
- [ ] All subcomponent pull requests (if any) have been reviewed by their code managers.
- [x] Run the full Intel+GNU RT suite (compared to current baselines) on Hercules.
   - [x] Commit log file w/full results from RT suite run.
   - [x] Verify that `test_changes.list` indicates which tests, if any, are changed by this PR.
- Transparency in the use of generative AI is required by NOAA policy. Was GenAI used in this work?
   - [x] Yes. Claude Opus 5.5 (Anthropic) was used to assist with developing this code.
     - [ ] The code has been reviewed, edited, and validated by NWS staff.
- [x] Fill out all sections of this template.

### Description:
14 independent bug fixes that remove water, energy and tracer-mass errors in SAMF, the PBL, Noah-MP, GFDL MP v3 and the SAMF single-precision build. Each fix is one commit in its subcomponent, and the commit message gives the defect, the fix and the measured effect. Largest effects: SAMF drops the heat of fusion of the ice it detrains (0.42 W/m²); GFDL MP v3 creates 1.03 % of its precipitation; `control_p8_mynn` depends on the domain decomposition. [0b global effect: mean 3-D temperature and precipitation change in the global tests, from the rerun RT] `hafs_global_1nest_atm` has a pre-existing SAMF instability (ufs-community/ccpp-physics#401); [0b hafs: crash count with these fixes vs develop]. One of the staged WM PRs for #3404.

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
* Addresses #3404, with the other staged WM PRs; the last to merge closes it

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD-ATM_0b
  * ccpp-physics: ufs-community/ccpp-physics#TBD-PR_SAMF (SAMF + PBL), #TBD-PR_NM (Noah-MP), #TBD-PR_GMP (GFDL MP v3)

### UFSWM Blocking Dependencies:
- [x] None

### Documentation:
- [x] Documentation update NOT required.
   - Explanation: bug fixes; no new options.

### Changes

### Regression Test Changes (Please commit test_changes.list):
- [x] PR Updates/Changes Baselines. [RT 0b]

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

## ufs-weather-model track 0c — after review, as draft

### Commit Queue Requirements:
- [x] This PR addresses a relevant WM issue: #3404
- [ ] All subcomponent pull requests (if any) have been reviewed by their code managers.
- [x] Run the full Intel+GNU RT suite (compared to current baselines) on Hercules.
   - [x] Commit log file w/full results from RT suite run.
   - [x] Verify that `test_changes.list` indicates which tests, if any, are changed by this PR.
- Transparency in the use of generative AI is required by NOAA policy. Was GenAI used in this work?
   - [x] Yes. Claude Opus 5.5 (Anthropic) was used to assist with developing this code.
     - [ ] The code has been reviewed, edited, and validated by NWS staff.
- [x] Fill out all sections of this template.

### Description:
Five independent, answer-changing bug fixes that close water-budget errors in Thompson microphysics and fix the same mass-basis error in the TEMPO driver. Each fix is one commit, with the defect, fix and measured effect in the commit message. In the regional and convection-allowing tests precipitation falls by 0.9–5.3 % (`regional_wofs_tempo` 2.0 %): water that the graupel limiters and the mass-basis round trips created is no longer created. The ccpp-physics PRs give the attribution by fix. One of the staged WM PRs for #3404.

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
* Addresses #3404, with the other staged WM PRs; the last to merge closes it

### Sub component Pull Requests:
* UFSATM: NOAA-EMC/ufsatm#TBD-ATM_0c
  * ccpp-physics: ufs-community/ccpp-physics#TBD-PR_TH (Thompson), #TBD-PR_TP (TEMPO driver)

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

