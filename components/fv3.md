# FV3 dycore and its coupling to the physics (NOAA-GFDL/GFDL_atmos_cubed_sphere `model/` and `driver/UFS/atmosphere.F90`; in ccpp-physics `dcyc2t3.f` and `GFS_suite_interstitial_3.F90`)

**Status (13 November 2026).** The dycore heats dissipated kinetic energy with the wrong heat capacity (DY1–DY3), and
the hand-off between dycore and physics uses inconsistent masses or constants in several places (FV1, FX1, CP1, FV2,
R1); tracer transport moves a tracer that is uniform in dry mixing ratio off uniform. Nothing here is posted. FX1, SG1,
CP1, FV2, FV1 and INLQ are drafted as one GFDL_atmos_cubed_sphere `dev/emc` PR with an issue (round-1 track 1c), waiting
on a `dev/emc` merge and the [#401](https://github.com/ufs-community/ccpp-physics/issues/401) answer; CP1 and FV2 do not pass the pre-registered WoFS forecast test. DY1–DY3, R1
and TOPT are round-2 issue drafts with tested patches. The dry tracer transport and the coupling energy terms are
default-off physics changes in the unposted conservation proposal. Staged plan: [ufs-weather-model#3404](https://github.com/ufs-community/ufs-weather-model/issues/3404).

## Defects and fixes

Cases are C96 `control_p8_ugwpv1`, 24 h, dt 720 s, unless stated; W/m² are global 24-h means. FV1 is at
`dev/emc` @71ff473 `driver/UFS/atmosphere.F90` L2298.

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| FV1 | `atmos_phys_driver_statein` builds the physics' layer pressure `prsl` with the dycore's single-precision `rdgas`, and the physics turns it back into density with its own `con_rd`. | atmosphere gains 4 × 10⁻⁸ of evaporation more than the land loses (32-bit build) | compute `rTv` with the physics' `con_rd`, `con_fvirt`: 5 × 10⁻¹⁶ over 24 h | drafted, not posted (track 1c) | [water proposal §4](../proposals/water_closure_proposal.md#4-fv3-driver-fix-fv1), [diff 19](../patches/19_FV1_fv3_prsl_with_physics_gas_constants.diff) |
| FX1 | The `consv_te` fixer (`fv_mapz.F90`) converts its deficit to a T increment with weight c_v,air·Σpkz·δp but applies it at c_vm. | fixer window −5.5 × 10⁻⁴ W/m² | weight by the heat capacity it heats: −3.6 × 10⁻¹⁰ | drafted, not posted (track 1c) | [conservation §1](../proposals/conservation_proposal.md#1-fv3-dynamical-core-and-its-coupling-to-the-physics), [diff](../experiments/conservation/energy/patches/01_fv3-fv_mapz_consv_te_fixer_weight.diff) |
| SG1 | `fv_subgrid_z` (non-hydrostatic, nwat = 6) mixes total energy, then relaxes T, u, v, w, q separately; the relaxed state loses fra(1−fra)δ²/2 of KE. | −1.58 × 10⁻⁴ W/m² (sponge only) | T from the relaxed total energy: +3.0 × 10⁻¹¹ | drafted, not posted (track 1c) | [conservation §1](../proposals/conservation_proposal.md#1-fv3-dynamical-core-and-its-coupling-to-the-physics), [diff](../experiments/conservation/energy/patches/02_fv3-fv_sg_relax_total_energy.diff) |
| CP1 | The physics heats its own layer mass, but `atmosphere_state_update` applies the tendency to the new total δp, so each joule arrives × δp_new/m_p. | coupling heating −8.63 × 10⁻³ W/m² | heat the mass that was heated: +3.9 × 10⁻¹⁰ | drafted, not posted (track 1c) | [conservation §1](../proposals/conservation_proposal.md#1-fv3-dynamical-core-and-its-coupling-to-the-physics), [diff](../experiments/conservation/energy/patches/03_fv3-atmosphere_state_update_heating_mass.diff), [WoFS test](../experiments/runs_29oct/1c_wofs.md) |
| FV2 | `atmos_phys_driver_statein` divides tracers by `prsl` into the physics and multiplies by `prsi(k) − prsi(k+1)` on the way back; the sum drops corrections below half an ulp, always the same sign. | tracer conversion +3.07 × 10⁻¹⁵ per day (64-bit dycore) | one layer mass both ways: +5.2 × 10⁻¹⁷ per day | drafted, not posted (track 1c) | [tracer report](../experiments/conservation/tracer/report.md), [diff](../experiments/conservation/tracer/patches/01_FV2_fv3_statein_consistent_layer_mass.diff) |
| INLQ | With `inline_q`, `d_sw` weights tracer damping by the post-update δp on a PE's own cells and the pre-update δp in its halo, so two PEs add different fluxes on one face. | tracer mass 1.0–1.9 × 10⁻⁹ per day; dry air −8.6 × 10⁻¹² (`inline_q` on; no RT uses it) | the pre-update δp on both sides: 5.9–8.4 × 10⁻¹⁵ per day | drafted, not posted (track 1c) | [trdyn](../experiments/conservation/trdyn/report.md), [diff](../experiments/conservation/trdyn/patches/04_INLQ_inline_q_damping_mass_single_valued.diff) |
| DY1 | `dyn_core.F90` adds the `d_con` heat as `dtmp/pkz` to the density potential temperature at fixed δz with 1/c_v,air, so the realised ΔT is dtmp/(1−κ): c_p/c_v times the KE returned. | +0.2905 W/m²; +0.2911 from FV3's own `ENG Deficit` print, no meter | `dyn_te_exact` bit 1 | drafted, not posted (round-2 issue 5) | [fv3tally](../experiments/conservation/fv3tally/report.md), [dycred](../experiments/conservation/dycred/report.md), [issue draft](../proposals/round2_issues.md#5-three-energy-bugs-in-the-dycores-heating-of-dissipated-ke) |
| DY2 | `d_sw` takes the KE estimate about the half-damped wind (after divergence damping, before vorticity damping). | −0.0195 W/m² | bit 16: exact | as DY1 | as DY1 |
| DY3 | `Rayleigh_Super` heats the A-grid KE at c_v,air while TE loses the D-grid KE, and the stale `pkz` multiplies the heat by c_p/c_v. | +6.42 × 10⁻⁴ W/m² | bit 8: 1.5 × 10⁻¹³. DY1–DY3 with bits 2, 4 (`dyn_te_exact` = 31): fixer −0.570 → −0.304 W/m² | as DY1 | as DY1 |
| R1 | RRTMG's heating rates are per the layer mass at the radiation call; `dcyc2t3` applies the same K/s on the following steps while δp changes. | −7.65 × 10⁻³ W/m² (Σ\|r\| 2.70 × 10⁻²) | store δp at the last SW and LW calls (two new `Radtend` fields) and scale by δp_rad/δp_now: −8.4 × 10⁻¹⁴ | drafted, not posted (round-2 issue 6) | [conservation §2](../proposals/conservation_proposal.md#2-radiation), [issue draft](../proposals/round2_issues.md#6-radiative-heating-applied-to-a-stale-layer-mass), [diff](../experiments/conservation/energy/patches/04_ccpp-dcyc2t3_radiative_heating_current_mass.diff) |
| TOPT | The process-split sum (radiation, PBL, GWD) is applied only by a scheme with `tend_opt` = 3, and nothing checks that a 3 follows a 2; option 4 discards silently. | energy residual +110 to −142 W/m² in the broken combinations (1,1), (1,2), (2,1), (2,2), (3,2); `FV3_HRRR_gf_nogwd` never applies R or P with defaults | `GFS_suite_interstitial_3` applies a pending sum once; option 4 a CCPP error: 2.08–3.12 (default 2.09, bitwise) | drafted, not posted (round-2 issue 7) | [conservation §8](../proposals/conservation_proposal.md#8-tendency-application-topt-and-gravity-wave-drag), [issue draft](../proposals/round2_issues.md#7-process-split-tendencies-dropped-for-some-tend_opt-combinations), [diff](../experiments/conservation/latent/patches/03_TOPT_process_split_sum_applied_once.diff) |
| `dry_tracer_adv` | The hord_tr 8 limiter and the remap act on each water species separately, so a tracer uniform in dry ratio is not carried with the dry air the limited water fluxes imply. | per call: advection 1.8 × 10⁻⁴, remap 1.6 × 10⁻⁴ (relative deviation of a uniform dry tracer) | transport chemistry tracers dry-consistently (DYN v6, switch, default off): 6.7 × 10⁻¹⁶, 1.2 × 10⁻¹³ | not posted (conservation proposal only) | [conservation §7](../proposals/conservation_proposal.md#7-tracer-transport-in-fv3), [trdyn](../experiments/conservation/trdyn/report.md), [trunif](../experiments/conservation/trunif/report.md) |
| `dry_negadj` | `neg_adj2/3/4` borrow water between layers at fixed δp, moving dry air with no tracer flux (only where water goes negative, with `nord_tr` or `inline_q`). | 2.3 × 10⁻⁷ per call | under `dry_tracer_adv`: 4.4 × 10⁻¹⁶ per call | as `dry_tracer_adv` | as `dry_tracer_adv` |
| `dry_tracer_ic` | The IC's remap and adiabatic initialisation treat a chemistry tracer as a moist ratio. | IC deviation 3.4 × 10⁻⁴ (max) | switch `dry_tracer_ic` (default off): 2.2 × 10⁻¹⁶ | as `dry_tracer_adv` | as `dry_tracer_adv` |

## Not proposed, or a judgement call

- **CP1 and FV2 in WoFS.** CP1's precipitation change scales with the dose of the restored term (−0.52 %/unit,
  z = −5.0) but fails the pre-registered rule; FV2 is inside 2σ_n on precipitation and rank 11 of 11 on one T leg.
  Whether either meets "the defect's own signal" is open ([1c_wofs](../experiments/runs_29oct/1c_wofs.md)).
- **FX1 with `do_sat_adj` = .true.** is exact to first order only; `control_p8` does not exercise it.
- **`dyn_te_exact`.** Our patch puts the bug bits 1–16 behind the switch (default 0); issue 5 asks whether they should
  be unconditional. Bits 2 and 4 (sponge w-damping heat) are real but immaterial in p8. Bits 32 and 64 are design
  options: unheated sponge layers −1.69 × 10⁻³ → −4.2 × 10⁻⁵ W/m², remap TE change −0.1144 → −3 × 10⁻¹⁰; the fixer
  then removes −0.417 with 127. v2 supersedes v1. nwat = 7, the non-MOIST_CAPPA branch and MULTI_GASES are compile-only;
  bits 1, 8, 64 stop with FATAL under MULTI_GASES.
- **FV3's adiabatic +0.4145 W/m² is not proposed.** It does not converge with time step and barely moves with the
  tracer scheme: a property of the spatial discretization. The `consv_te` fixer stays on ([§13](../proposals/conservation_proposal.md#13-what-remains)).
- **Coupling energy options, default off** ([conservation §1](../proposals/conservation_proposal.md#1-fv3-dynamical-core-and-its-coupling-to-the-physics)):
  - C1 `cpl_water_energy` bit 1, water potential energy: net PE −0.480 W/m² → applied.
  - Bit 2, flow work: FV3 applies the physics' isobaric latent heat at fixed δz, so each vapour mass change is booked with ±R_v·T too much; net −0.620 → 0; latent heat −1.97 W/m². A forecast improvement is not shown, and there is no real-model column test ([fwred](../experiments/conservation/fwred/report.md)).
  - Bit 4, sensible enthalpy of water moving between layers and across the surface: +1.773 → applied. Bits 1 + 2 + 4 together: latent heat −2.04 W/m², precipitation −3.4 % ([encpl](../experiments/conservation/encpl/report.md)).
  - C8 (bit 8): KE of water mass written at the layer winds, −0.0025 → 0.
  - D7 `cpl_ke_heating` with D7S `cpl_ke_smooth` = 32: the A→D wind-increment KE differs from the physics'; not recommended without D7S (raw peak 0.87 K/step).
- **R1 needs host fields first.** ccpp-physics CI runs capgen against NCAR/ccpp-scm `main` and ufsatm `develop`, so the
  two `Radtend` fields must merge in SCM, ufsatm and the MPAS host ([#397](https://github.com/ufs-community/ccpp-physics/issues/397))
  first; the SCM and MPAS hosts are not tested.
- **TOPT overlaps #397**, which restructures the same cases: fold in, or follow it. Option 4 as a CCPP error (decided)
  rather than a warning is a design choice. Not covered: deep, shallow or MP option 2 after the flush point; SW/LW options
  other than 4. Time-split PBL (`tend_opt_pbl` 1 or 3) differs from the default by 0.21 K; that is a configuration, not a defect.
- **The dry tracer switches** act only on `"tracer_usage","chemistry"` tracers: weather is bitwise, cost +1.5 %.
  `dry_tracer_ic` must be set per run to match the IC files; it reinterprets a structured GHG field by 2.1 ppm rms,
  12.5 max. Regional FV3 BC handling and the HAFS moving nest are untested; `FILL2D` stops with FATAL. Without the
  switch, `neg_adj3` still moves dry air under `nord_tr` or `inline_q`.
- **`diff3d` ([#403](https://github.com/ufs-community/ccpp-physics/pull/403), not our PR).** FV3's horizontal-diffusion
  operator ([GFDL_atmos_cubed_sphere#429](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/pull/429)) leaks when
  `satmedmfvdifq` applies it on the physics' layer mass; it closes only when divided by that mass. Kept on the
  [PBL page](pbl.md); runs in [mlm_diff3d](../experiments/runs_29oct/mlm_diff3d.md).
- **Not addressed:** the dycore's single-precision `grav` differs from `con_g` by 1.65 × 10⁻⁸; the meters show no water
  effect at 10⁻⁶ kg/m² per window. In 64-bit builds FV1 should change nothing (not run).
- **Elsewhere:** [GFDL_atmos_cubed_sphere#430](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/issues/430)/[#431](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/pull/431) (`sedi_heat`) is GFDL microphysics; [ufs-weather-model#3406](https://github.com/ufs-community/ufs-weather-model/issues/3406) is an FMS
  build FPE, not FV3.

## Reproduce

- Diffs: FV1 [`../patches/19_…`](../patches/19_FV1_fv3_prsl_with_physics_gas_constants.diff); FX1, SG1, CP1, R1, D7, C8, D7S in
  [`energy/patches/`](../experiments/conservation/energy/patches/) (01–05, 10, 11); FV2 in
  [`tracer/patches/`](../experiments/conservation/tracer/patches/); INLQ and DYN v6 in
  [`trdyn/patches/`](../experiments/conservation/trdyn/patches/) (`04_INLQ_…`, `01_DYN_…_v6.diff`);
  `dyn_te_exact` v2 [`fv3tally/patches/01_fv3-dyn_te_exact.diff`](../experiments/conservation/fv3tally/patches/01_fv3-dyn_te_exact.diff);
  TOPT [`latent/patches/03_…`](../experiments/conservation/latent/patches/03_TOPT_process_split_sum_applied_once.diff);
  C1 [`encpl/patches/04_fv3-cpl_water_energy.diff`](../experiments/conservation/encpl/patches/04_fv3-cpl_water_energy.diff).
  Apply order: [`SERIES.md`](../experiments/conservation/replay/SERIES.md). PR and issue text for track 1c:
  [descriptions §2, §4](../proposals/pr_round1_descriptions.md#4-gfdl_atmos_cubed_sphere-pr-base-devemc).
- Meters: [`../methods/METERS.md`](../methods/METERS.md); dycore/coupling energy
  [`energy/meters/meter_fv3_dycore_coupling.diff`](../experiments/conservation/energy/meters/meter_fv3_dycore_coupling.diff);
  the per-term tally [`fv3tally/meters/`](../experiments/conservation/fv3tally/meters/) (env `FV3_ETALLY=1`); tracer mass
  [`tracer/meters/03_meters_fv3.diff`](../experiments/conservation/tracer/meters/03_meters_fv3.diff).
- Compare against: the [fv3tally](../experiments/conservation/fv3tally/report.md) term table (control sum +0.5701 W/m²);
  the meter-free check in [dycred](../experiments/conservation/dycred/report.md); the uniform dry tracer end to end,
  3.7 × 10⁻¹⁴ rms, 4.9 × 10⁻¹³ max in 24 h, from 1.07 × 10⁻³ / 1.22 × 10⁻² ([conservation §7](../proposals/conservation_proposal.md#7-tracer-transport-in-fv3));
  R1 in the [energy report §6](../experiments/conservation/energy/report.md#6-round-2); TOPT gates in [latent](../experiments/conservation/latent/report.md).
- RT: in the round-1 regression with every round-1 fix (Intel + GNU, Hercules), the FV3 commits alone move precipitation
  ≤ 0.25 % except `cpld_regional_atm_fbh` −1.4 %; reproducibility 123 of 123 bitwise ([checks](../proposals/pr_round1.md#checks)).
  Gates for `dyn_te_exact` and the dry tracer switches (off bitwise, restart, 3×8 = 4×6): fv3tally, trdyn.
