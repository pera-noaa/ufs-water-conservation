# Noah-MP and its coupling (`module_sf_noahmplsm.F90`, `module_sf_noahmp_glacier.F90`, `noahmpdrv.F90` and the surface interstitials in ccpp-physics; copies in NOAA-EMC/noahmp and NCAR/noahmp)

**Status (13 November 2026).** Noah-MP and the code that couples it to the atmosphere create, delete or double-step land
water and the energy that goes with it; the largest, NM2, makes the land gain 3–5 % of global precipitation with
`frac_grid`. Posted, in review, none merged (package 3): [#409](https://github.com/ufs-community/ccpp-physics/pull/409)
(NM3, NM4, NM12) and [#410](https://github.com/ufs-community/ccpp-physics/pull/410) (NM1; snow-layer heat SL2, CS1, CB1;
stacked on #409); the same snow-heat fix for Noah-MP v5 is [NCAR/noahmp#274](https://github.com/NCAR/noahmp/pull/274).
No reviews yet on any of the three. Not posted: NM2 (with the sea-ice once-per-step fix, after [#414](https://github.com/ufs-community/ccpp-physics/pull/414) merges); NM7, NM9,
NM10r, NM11 + CMC and the canopy wetted fraction E2 (round-2 issue drafts 2 and 3); NM5, NM6, NM8 and NP1; every other copy.

## Defects and fixes

Line numbers in `ufs/dev` @242a2fc: [water proposal, Appendix B](../proposals/water_closure_proposal.md#appendix-b--location-of-each-defect-in-current-upstream).
Cases are C96 `control_p8_ugwpv1` unless stated; "harness" is a single-column test that compiles the real `noahmpdrv_run`.

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| NM1 | The driver hands the atmosphere `evap = latent_heat/ρ/con_hvap`, but Noah-MP removed the water with its own `hvap`, and `hsub` over frozen surfaces. | atmosphere gains 0.07–0.10 % of global precipitation more than the land loses (C96, 24 h) | pass the water Noah-MP removed, `(ecan + etran + edir)/ρ`, as NCAR's own drivers do | [#410](https://github.com/ufs-community/ccpp-physics/pull/410) review | [proposal §3](../proposals/water_closure_proposal.md#3-noah-mp-and-its-coupling-fixes-nm1nm11), [diff 08](../patches/08_NM1_noahmp_water_flux.diff), [PR text](../upstream/posted/PR_NM2_410.md) |
| NM2 | With `frac_grid`, `GFS_surface_loop_control_part2` re-flags coastal land for the second surface pass and Noah-MP steps it again from its already-updated state. | land gains 3–5 % of global precipitation (C96, 6–24 h); 24–27 % of the land stepped twice every step | step land once per time step (two forms, below) | drafted, not posted (round-1 track 1d) | [proposal §3](../proposals/water_closure_proposal.md#3-noah-mp-and-its-coupling-fixes-nm1nm11), [diff 09](../patches/09_NM2_noahmp_single_step_per_timestep.diff), [09b](../patches/09b_NM2-EMC_noahmp-emc_driver_iter.diff), [PR draft §3.5](../proposals/pr_round1_descriptions.md#35-surface-iteration-sea-ice-and-nsst) |
| NM3 | With `frac_grid`, `GFS_surface_composites_pre` overwrites the land snow `weasd_lnd` with the cell mean every step. | thin coastal snow lost, about 0.005 mm per land column per 6 h | keep `weasd_lnd` with `frac_grid`, as RUC does | [#409](https://github.com/ufs-community/ccpp-physics/pull/409) review | [proposal §3](../proposals/water_closure_proposal.md#3-noah-mp-and-its-coupling-fixes-nm1nm11), [diff 10](../patches/10_NM3_frac_grid_land_snow_persistent.diff), [PR text](../upstream/posted/PR_NM1_409.md) |
| NM4 | At a cold start `GFS_phys_time_vary_init` builds the snow layers from the cell-mean `weasd` and `snowd`, not the land snow. | 0.29 kg/m² of land snow lost on the first step | build them from `weasdl`, `snodl`; no layers where there is depth but no snow water | [#409](https://github.com/ufs-community/ccpp-physics/pull/409) review | [diff 11](../patches/11_NM4_noahmp_snow_init_from_land_snow.diff) |
| NM5 | Snow without layers is zeroed when `snowh <= 1e-6` m or `sneqv <= 1e-3` mm, and the water goes nowhere. | removes 0.009 % of global precipitation from the land | put the truncated snow in the top soil layer as ice | not posted | [diff 12](../patches/12_NM5_noahmp_thin_snow_to_soil.diff) |
| NM6 | `canwater` zeroes canopy liquid or ice at or below 10⁻⁶ mm. | removes 4 × 10⁻⁷ of land precipitation | add the truncated water to the rain and snow reaching the ground | not posted | [diff 13](../patches/13_NM6_noahmp_canopy_truncation_to_ground.diff) |
| NM7 | `canwater` clips negative transpiration (`etran = max(fctr/hvap, 0)`), so condensation heat warms the canopy but no water condenses. | Noah-MP's latent energy exceeds its water's by 0.024 W/m² per land column | add the condensate to the canopy dew (frost on a frozen canopy); energy solve unchanged | drafted, not posted (round-2 issue 3a) | [diff 14](../patches/14_NM7_noahmp_negative_transpiration_to_canopy_dew.diff), [issue draft](../proposals/round2_issues.md#3-noah-mp-four-waterenergy-decisions) |
| NM8 | Noah-MP charges its own latent heats (2.5104e6, 2.844e6 J/kg), but after NM1 the vapour enters the atmosphere carrying the host's. | the land pays 0.4 % more latent energy than its vapour carries (+0.131 W/m² per land column) | set `hvap`, `hsub`, `hfus` from `con_hvap`, `con_hfus` at the start of `noahmpdrv_run`; no interface change | not posted | [diff 15](../patches/15_NM8_noahmp_latent_heats_from_host.diff) |
| NM9 | Glacier snow is set by assignment: reset to 600 mm every call, floored at 0.1 mm, zeroed when thin; the water added or removed goes nowhere. | a glacier column −860 mm in 120 days; all snowfall on land ice deleted (harness) | keep the assignments, book their water as runoff and glacier flow | drafted, not posted (round-2 issue 3b) | [proposal §3](../proposals/water_closure_proposal.md#3-noah-mp-and-its-coupling-fixes-nm1nm11), [diff 16](../patches/16_NM9_noahmp_glacier_book_snow_changes.diff) |
| NM10 | With `opt_snf = 4` the microphysics' frozen fraction of grid-scale precipitation is applied to convective precipitation too. | a trace of grid-scale snow turns convective rain on land into snow (phase, not water) | NM10r (17r): convective phase from the host's `srflag`; land and host then agree to 1.2 × 10⁻¹⁰ of frozen mass (C96, 24 h) | drafted, not posted (round-2 issue 3c) | [17r](../patches/revised/17r_NM10r_noahmp_precip_phase.diff), [conservation §6](../proposals/conservation_proposal.md#6-surface-noah-mp-nsst-and-sea-ice) |
| NM11 | `energy` charges the ground's vapour at `hvap` when `tg` is above freezing, but `water` takes that vapour from the snow ice whenever there is snow. | 0.13–0.61 W/m² over a snow season, up to 78 W/m² in one step (harness) | `latheag = hsub` with snow; any remaining phase mismatch returned to the top soil layer as heat | drafted, not posted (round-2 issue 3d) | [diff 18](../patches/18_NM11_noahmp_ground_vapour_latent_heat.diff) |
| NM12 | `combine` (land and glacier) tests the entry layer count `isnow_old < -1`, not `isnow < -1`, so a ≥ 2-layer pack melting out in one step merges into an inactive slot. | per firing: water −0.10 to +0.16 mm, energy −1.1 to −8.5 MJ/m²; fires 5 × 10⁻⁶ per call of melt-out-prone packs at 720 s, 1.7 × 10⁻² at 3600 s (harness); C96 24 h bitwise | test `isnow`, as NCAR did in NCAR/noahmp@218eb5a ([#47](https://github.com/NCAR/noahmp/issues/47)) | [#409](https://github.com/ufs-community/ccpp-physics/pull/409) review; NOAA-EMC/noahmp companion 20b not posted | [nm12 report](../experiments/conservation/nm12/report.md), [20b run](../experiments/runs_29oct/nm12_emc.md) |
| SL2 | In `combine`, a thin layer merged by mass keeps the receiver's temperature, snow that stops being layered drops its layers' sensible heat, and truncated bulk snow changes soil-1 ice at T1. | with CS1, CB1: Noah-MP soil energy residual 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ W/m² (C96, 24 h) | merge heat with per-mass capacities; heat of removed layers to the top soil layer | [#410](https://github.com/ufs-community/ccpp-physics/pull/410) review; [NCAR/noahmp#274](https://github.com/NCAR/noahmp/pull/274) review | [ensfc2](../experiments/conservation/ensfc2/report.md), [v5 PR text](../upstream/posted/PR_NCAR_noahmp_274.md) |
| CS1 | `csnow` builds the heat capacity from capped volume fractions, so liquid beyond the pore space has none. | −57,043 J/m²/K of 175,101 (Noah-MP v5 standalone test) | heat capacity from the ice and liquid mass | as SL2 | [v5 PR text](../upstream/posted/PR_NCAR_noahmp_274.md), [test program](../upstream/ncar_noahmp/test_snow_heat.F90) |
| CB1 | `combo` multiplies per-m³ heat capacities by layer masses in kg/m², and some branches set T = tfrz without a phase change. | +1,393 and +542 J/m² per combination (Noah-MP v5 standalone test) | per-mass capacities, as CTSM's `Combo` | as SL2 | [v5 PR text](../upstream/posted/PR_NCAR_noahmp_274.md) |
| NP1 | `phasechange` deletes the heat of a snow layer that melts out when the layer below is sub-freezing. | did not fire (C96, 24 h, March) | keep the heat | not posted | [ensfc](../experiments/conservation/ensfc/report.md), [diff](../experiments/conservation/ensfc2/patches/06_sfc_NP1.diff) |
| CMC | `canwater` caps canopy evaporation after the energy solve charged it; frozen-canopy transpiration is charged at `hsub` but taken from soil liquid; canopy melt and freeze move `hfus·Δm` with no heat. | land charged − carried 0.0148 W/m² | return the difference to the top soil layer (the NM11 path) | drafted, not posted (round-2 issue 3d, with NM11) | [conservation §6](../proposals/conservation_proposal.md#6-surface-noah-mp-nsst-and-sea-ice), [diff](../experiments/conservation/ensfc2/patches/09_sfc_CMC.diff) |
| E2 | `fwet` comes from the ice alone whenever there is any canopy ice; the ice capacity is ~50× the liquid's, so a trace of ice hides the liquid and stops canopy evaporation. | 45–48 % of wet-canopy steps hold both phases; on those `fwet` averages 0.09, against 0.58 from the liquid alone | switch `noahmp_fwet_opt` (0 = stock; 2, the larger fraction, recommended) in the ccpp and NOAA-EMC/noahmp copies | drafted, not posted (round-2 issue 2) | [canopy report](../experiments/conservation/canopy/report.md), [Appendix E](../proposals/water_closure_proposal.md#appendix-e--separate-issues-found-along-the-way), [issue draft](../proposals/round2_issues.md#2-thompson-surface-sedimentation-trace-and-the-noah-mp-canopy-wetted-fraction) |

## Not proposed, or a judgement call

- **NM2 has two forms**, equivalent within noise in six global tests: (a) one clause of
  `GFS_surface_loop_control_part2` stops re-flagging Noah-MP land, with no interface change (preferred); (b) an optional
  `iter` argument in `noahmpdrv`, which needs the same declaration in NOAA-EMC/noahmp (09b) or `control_p8_atmlnd`
  crashes. The PR draft asks the owners to choose; sea ice (SI1) has the same cause ([alternatives](../proposals/pr_round1.md#alternatives)).
- **NM5, NM6, NM8 were dropped from round 1** because where the truncated water or heat goes is a choice; NM8 also
  because Noah-MP's own constants may be intended. No issue text exists for NM5 or NM8; NM6 is parked as tiny.
- **Round-2 issue 3 asks four questions** ([draft](../proposals/round2_issues.md#3-noah-mp-four-waterenergy-decisions)):
  NM7 as above, or suppress the case in the energy solve as CTSM does; is NM9's 600 mm reset intended (its ice goes into
  `drain`, which hosts read as liquid, so closing the energy needs a frozen-runoff flux in the interface and couplers);
  adopt the host's skin-temperature criterion for convective phase (NM10r, a physics change; NM10's own rule disagreed
  with the host on 5.0 % of land column-steps with convective precipitation, 0.83 % of its mass); route NM11's and
  CMC's mismatch heat to soil layer 1 (land over snow changes beyond noise, snow cover +0.16 %).
- **NM10 (diff 17) is superseded by 17r.** The regression results in the water proposal were measured with 17.
- **E2 is a land forecast change.** Options 1 / 2 move canopy evaporation +32 / +36 % and land latent heat +1.5 /
  +1.2 % (0–24 h, all energy options on). Option 2 is recommended because adding water never lowers `fwet`; option 3 is
  v5's dominant-phase rule. The documents disagree on its class (switched bug fix, or an issue). The first candidate,
  `patches/candidates/issue4_noahmp_fwet_mass_weighted.diff`, is withdrawn: its local `cwat` shadows the specific heat
  of water ([corrections](../proposals/conservation_proposal.md#14-corrections)).
- **Energy options, all default off and bitwise when off** ([conservation §6](../proposals/conservation_proposal.md#6-surface-noah-mp-nsst-and-sea-ice), W/m² global, C96 24 h):
  - CH1 / CH2 `noahmp_canopy_heat`: `vege_flux` books only the last Newton increment of canopy heat storage, 0.052 → 3 × 10⁻¹⁷; CH2 is large (t2m +0.27 K).
  - SW1 `noahmp_sw_radshare`: Noah-MP absorbs SW with its own albedo and geometry, −0.093 → 0 where landfrac = 1; land uSW rms 12.1 (noise 2.1).
  - EV1 `sfc_evap_enthalpy`: frame-F enthalpy of evaporated water, applied = booked to 6 × 10⁻¹⁷.
  - AD1 `noahmp_heat_advect`: soil water moved between layers carries no sensible heat, 0.058 → 1 × 10⁻¹⁴.
  - KF1 `noahmp_kirchhoff`: melt and freeze at constant `hfus`, 0.200 → 2.8 × 10⁻⁸ (step 1 only); a trade-off of 6 % of `hfus` at −10 °C.
  - AIR1 `noahmp_pore_air`: pore air's heat moves with soil water unbooked, 2.4 × 10⁻³ → 8.5 × 10⁻¹⁵.
  - PH2 / PH3 `precip_phase_host`: soil and glacier take the host's phase; after NM10r it governs glaciers only. The host side (PH1) and the precipitation enthalpy (EP1, PL1) are on the [surface page](surface.md).
- **Not fixed:** NM1 is incomplete with the MYNN surface layer (`sfcdif4` derives moisture from latent heat). NM5 with
  implausible host input (large snow, depth ≤ 10⁻⁶ m) can push soil-1 ice past porosity. SL1 was withdrawn as
  misattributed; SL2, CS1, CB1 replace it.
- **Other copies** ([survey](../patches/ports/survey_noahmp_copies.md), [ports](../patches/ports/README.md)), none posted:
  - NOAA-EMC/noahmp `develop` 2c7b3bc, pinned by `develop`, GFS.v17 and HAFS.v2.2: NM1, NM5, NM6, NM8, NM7, NM9 (no reset), NM10 and 09b as eight commits ([series](../patches/ports/noahmp-emc_develop_D_H_I_K_L.diff)); land component Σ residual −5.2 × 10⁻⁴ → −8 × 10⁻¹³ of ΣP. It follows the UFS decisions on NM5, NM6, NM8 and issue 3. RRFS's pin 0cd3e23 needs 09b only, for form (b).
  - NM12's companion 20b passes all ten pre-registered criteria in `datm_cdeps_lnd_gswp3`; the stock test never fires it, so it moves no baseline ([run](../experiments/runs_29oct/nm12_emc.md)).
  - ccpp-physics production branches (GFS.v17, HAFS.v2.2, RRFS.v1, SRW v3, AQM.v7) carry the series adapted, with NM8 in the run phase, NM9 and NM10; whether operations want backports is open.
  - NCAR Noah-MP v5 (and WRF, HRLDAS, MPAS, LIS, ERF) has NM5, NM6, NM7 and NM8; an issue for NM5–NM7 is drafted ([draft](../patches/ports/ncar_noahmp_issue_draft.md)). ERF has an NM1 analogue. v5 already tests the current layer count (NM12).
  - **NM11 is not ported** to any other copy. Every copy surveyed carries it; the hold for the UFS reproducibility run is lifted, and porting is a decision.

## Reproduce

- Diffs: water series [`../patches/08_…` to `18_…`](../patches/README.md) with 09b and [17r](../patches/revised/17r_NM10r_noahmp_precip_phase.diff);
  NM12 [`20`](../experiments/conservation/nm12/patches/20_NM12_noahmp_combine_melt_out.diff) and
  [`20b`](../experiments/conservation/nm12/patches/20b_NM12-EMC_noahmp-emc_combine_melt_out.diff); SL2, CS1, CB1, NP1, CMC and the
  options in [`ensfc2/patches/`](../experiments/conservation/ensfc2/patches/) (13–15, 06, 09, 11) and
  [`preclag/patches/16b_…`](../experiments/conservation/preclag/patches/16b_sfc_options_r4_meta_fixed.diff); E2
  [`canopy/patches/01_E2_…`](../experiments/conservation/canopy/patches/01_E2_noahmp_fwet_opt.diff). Apply order and rows
  12, 33, 35, 37–42, 57: [`SERIES.md`](../experiments/conservation/replay/SERIES.md).
- Meters: [`../methods/METERS.md`](../methods/METERS.md) (land meters: Noah-MP storage in and out of each call, `errwat`,
  each truncation site); surface energy meters in [`ensfc2/meters/`](../experiments/conservation/ensfc2/meters/); the
  NM12 harness in [`nm12/harness/`](../experiments/conservation/nm12/harness/); the v5 test program
  [`test_snow_heat.F90`](../upstream/ncar_noahmp/test_snow_heat.F90).
- Compare against: [water proposal §6](../proposals/water_closure_proposal.md#6-results) (Noah-MP `errwat`
  −1.2 × 10⁻⁸ mm over 1.77 million column-steps with NM1–NM6); [ensfc2 final closure](../experiments/conservation/ensfc2/report.md)
  (soil 4.33 × 10⁻⁸, glacier 6 × 10⁻¹⁶ W/m²); [canopy](../experiments/conservation/canopy/report.md) for E2.
- RT: with #409, #410, #408 and the GFDL MP v3 fixes, full Intel + GNU `rt.sh` on Hercules (develop 3e48f4cc,
  baselines 20261022): 54 builds compile, 116 tests identical, 101 change answers, 15 restart/IAU tests not started,
  none fails ([PR text](../upstream/posted/PR_NM1_409.md)). Package 3's own RT comes after package 2, on new baselines;
  only land-coupled and `frac_grid` tests should change ([roadmap §3](../upstream/ROADMAP.md#3-package-3-noah-mp--409-410)).
