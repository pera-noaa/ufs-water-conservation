# NSST, sea ice and the precipitation hand-off (`sfc_nst.f90`, `sfc_ocean.F`, `sfc_sice.f`, `GFS_surface_loop_control_part2.F90`, `GFS_MP_generic_post.F90` in ccpp-physics)

**Status (13 November 2026).** Sea ice is stepped twice on 1.9 % of ice column-steps and mishandles its layer heat in
two places, NSST's rain heat flux uses the wrong units, and NSST's explicit sea spray oscillates in strong wind.
Nothing here is posted. SI1, SI2, FL1 and QR1 are drafted as one ccpp-physics PR with Noah-MP's NM2 (round-1 track
1d); its HAFS crash hold is cleared with the [#414](https://github.com/ufs-community/ccpp-physics/pull/414) `xlamue` floor, so it goes after #414 merges, and SI1 has two forms
for the owners to choose. The sea-spray fix E1 and the precipitation-enthalpy options (EP1 with its lag fix PL1, LW2,
PH1) are default-off physics changes in the unposted conservation proposal. Noah-MP's own items: [noahmp.md](noahmp.md).

## Defects and fixes

Cases are C96 `control_p8_ugwpv1`, 24 h, from 2021-03-22 06Z, unless stated. Area fractions: sea ice 0.0365, open
water 0.687.

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| SI1 | NSST re-flags icy cells for the second surface iteration, and `sfc_sice` steps the ice again. | 1.9 % of ice column-steps stepped twice; ≈ −0.010 W/m²; calls per column-step 1.0186 | step ice once per time step (two forms, below): calls 1.0000 | drafted, not posted (round-1 track 1d) | [conservation §6](../proposals/conservation_proposal.md#6-surface-noah-mp-nsst-and-sea-ice), [PR draft §3.5](../proposals/pr_round1_descriptions.md#35-surface-iteration-sea-ice-and-nsst), [diff](../experiments/conservation/ensfc2/patches/04_sfc_SI1.diff) |
| SI2 | `ice3lay` divides the excess lower-layer heat by Δt a second time, deleting (1 − 1/720) of it while T2 is still reset. | did not fire (March case); acts on thin ice near melting | divide once | drafted, not posted (track 1d) | [ensfc](../experiments/conservation/ensfc/report.md), [diff](../experiments/conservation/ensfc2/patches/05_sfc_SI2.diff) |
| FL1 | In `ice3lay`, flooded snow (heat content −L_i) becomes ice at the layers' temperatures. | −7.87 × 10⁻³ W/m² | convert it with its own heat content: −1.15 × 10⁻¹³ | drafted, not posted (track 1d) | [conservation §6](../proposals/conservation_proposal.md#6-surface-noah-mp-nsst-and-sea-ice), [diff](../experiments/conservation/ensfc2/patches/10_sfc_FL1.diff) |
| QR1 | `sfc_nst.f90` uses `rain` (water depth per step) as kg m⁻² s⁻¹ in `qrain` and `sep`. | rain heat flux × 1000/720 at Δt 720 s; qrain 0.300 → 0.417 W/m² with the fix; NSST-internal | convert to a rate | drafted, not posted (track 1d) | [ensfc](../experiments/conservation/ensfc/report.md), [diff](../experiments/conservation/ensfc2/patches/08_sfc_QR1.diff) |
| E1 | NSST's sea-spray fluxes (`sfc_nst`, `sfc_ocean`) are explicit; where the gain λ > 2 the lowest layer flips every other step. | blew up one 10-day C96 run at day 6.4 (v1 snapshot, cyclone eyewall); on `develop`, 271 oscillating cells in 10 days | `nst_spray_opt` = 1 (default 0): backward Euler with the lowest layer; 2 oscillating cells | not posted (conservation proposal only) | [canopy report, E.1](../experiments/conservation/canopy/report.md), [Appendix E.1](../proposals/water_closure_proposal.md#appendix-e--separate-issues-found-along-the-way), [diff](../experiments/conservation/canopy/patches/04_E1_nst_spray_implicit.diff) |
| PL1 | The surfaces book step N's precipitation at step N+1's T1, while the atmosphere exported it at T1(N). Acts only with the EP1 option. | hand-off lag −1.2106 × 10⁻² W/m² (land −2.41 × 10⁻³) | carry T1(N) with the precipitation, one restart field written only with EP1; folded into `sfc_precip_enthalpy`: lag 0 (exact) | not posted (conservation proposal only) | [preclag report](../experiments/conservation/preclag/report.md), [series diff 46](../experiments/conservation/replay/patches/46_PL1_under_EP1.diff) |

## Not proposed, or a judgement call

- **SI1 has two forms**, equivalent within noise (sea ice at C48: rms alternative − proposed 5.7 × 10⁻⁴ m against a
  2.8–3.0 × 10⁻³ m signal): (a) restore the commented-out `.not. icy` in `GFS_surface_loop_control_part2`, one line
  and no interface change, preferred; the water part of those cells then loses its low-wind second NSST pass; (b) an
  optional `iter` argument in `sfc_sice`. Noah-MP's NM2 has the same cause ([alternatives](../proposals/pr_round1.md#alternatives)).
- **The HAFS hold.** With the other round-1 fixes, SI1, SI2, FL1 and QR1 raised the `hafs_global_1nest_atm` crash
  rate to 3 of 20 members (develop 0 of 20). With the #414 floor, 0 of 20 in both arms; 0/20 against 3/20 is p = 0.115,
  and the floor removes the path that crashed, so the clearance depends on #414 merging first ([1d_hafs](../experiments/runs_29oct/1d_hafs.md)).
- **E1 cuts the spray flux.** It delivers 81 % of the explicit form's spray latent flux globally and 23–26 % in the
  unstable cells. Global latent heat −0.21 W/m² (noise −0.03), open-water latent heat −0.29 %. A solve coupled to the
  PBL's implicit diffusion would cut less; that is the owners' alternative. The water proposal's limiter (about 1/λ)
  was rejected. No tropical cyclone forms on current `develop` from this date, so the day-6.4 runaway is not
  reproduced; `sfc_ocean.F` is compile-checked only.
- **Precipitation and surface-enthalpy options, default off** ([conservation §6](../proposals/conservation_proposal.md#6-surface-noah-mp-nsst-and-sea-ice)):
  - PH1 `precip_phase_host`: the atmosphere pays fusion for the convective snow the host classifies, h_fus × host convective snow = 0.0725 W/m²; noise.
  - EP1 `sfc_precip_enthalpy`: precipitation lands with its frame-F enthalpy; PH1 then releases L_f(T1); removes the PH1 overheating of −1.78 × 10⁻³ W/m². PL1 is folded into it.
  - LW1 → LW2 `lw_sfc_return`: the surfaces emit at their current T while the atmosphere's LW uses radiation-time fluxes; LW2 keeps the difference in the land and closes to 5 × 10⁻¹⁴ W/m², but moves soil T1 +0.12 K (beyond noise). LW1 is superseded.
- **NSST is not changed by PL1**, by decision: its `qrain` is a wet-bulb skin flux on the current state and never
  reaches a closed budget.
- **Water crossing the surface carries enthalpy the FV3 coupling does not book**: `cpl_water_energy` bit 4 in the FV3
  driver, on the [FV3 page](fv3.md).
- **Declared terms, not defects** ([conservation §13](../proposals/conservation_proposal.md#13-what-remains)): the open
  ocean, about +6.6 W/m² into the prescribed SST, closes by definition; SW in 0.999 ≤ landfrac < 1 cells, −6.1 to
  −6.3 × 10⁻³ W/m²; the surface hand-off of LW2 + EV1 heating, +0.1135 W/m², an identity closed to 10⁻¹³.
- **Withdrawn:** the round-1 land SW hand-off error of −0.573 W/m² (it compared against the cell-mean net SW; the real
  land error is −0.156); SI3 (open water is an open boundary).
- **Not measured:** lakes; sea ice in the water budget (the energy budget closes to −1.1 × 10⁻¹³ W/m² after the fixes).

## Reproduce

- Diffs: [`ensfc2/patches/04_sfc_SI1.diff`](../experiments/conservation/ensfc2/patches/04_sfc_SI1.diff), `05_sfc_SI2`,
  `08_sfc_QR1`, `10_sfc_FL1` in the same folder; E1 [`canopy/patches/04_E1_nst_spray_implicit.diff`](../experiments/conservation/canopy/patches/04_E1_nst_spray_implicit.diff);
  PL1 [`preclag/patches/01_PL1_sfc_precip_t1_carry.diff`](../experiments/conservation/preclag/patches/01_PL1_sfc_precip_t1_carry.diff)
  and its folded form, series row 46; options rows 37 and 41. Apply order: [`SERIES.md`](../experiments/conservation/replay/SERIES.md).
- Meters: [`../methods/METERS.md`](../methods/METERS.md); surface meters [`ensfc/meters/meter_surface.diff`](../experiments/conservation/ensfc/meters/meter_surface.diff)
  and [`ensfc2/meters/`](../experiments/conservation/ensfc2/meters/); the lag meter
  [`preclag/patches/meter_PL1_lag_v2.diff`](../experiments/conservation/preclag/patches/meter_PL1_lag_v2.diff); the spray-gain
  meter [`canopy/patches/instrumentation/meter_spray_gain.diff`](../experiments/conservation/canopy/patches/instrumentation/meter_spray_gain.diff).
- Compare against: [ensfc2 final closure](../experiments/conservation/ensfc2/report.md) (sea ice −1.1 × 10⁻¹³ W/m²;
  hand-off LW / EV / PH 5 × 10⁻¹⁴ / 6 × 10⁻¹⁷ / 1.5 × 10⁻¹³); the E.1 run table in the
  [canopy report](../experiments/conservation/canopy/report.md); [preclag](../experiments/conservation/preclag/report.md) final gates.
- RT: in the round-1 regression with every round-1 fix, sea ice/NSST alone moves `regional_control` precipitation
  +0.7 %, global P8 3-D T ≤ 0.0008 K, WoFS −0.06 % ([checks](../proposals/pr_round1.md#checks)). The HAFS ensembles:
  [1d_hafs](../experiments/runs_29oct/1d_hafs.md).
