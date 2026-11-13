# Gravity-wave drag heating (`ugwpv1_gsldrag.F90`, `drag_suite.F90`, `cires_ugwpv1_solv2.F90`, `GFS_GWD_generic_post.F90` in ccpp-physics)

**Status (13 November 2026).** GSL drag removes kinetic energy without heating (D4), the PBL × GWD cross term of the
joint process-split update is heated by neither scheme (D12), and UGWP-v1's non-orographic heating is a net energy
source because it comes from a prescribed launch flux (D4n). Separately, the process-split sum that
`GFS_GWD_generic_post` applies is dropped for some `tend_opt` combinations (TOPT). None is posted. D4, D12 and D4n are
default-off options in the conservation proposal; they change the forecast beyond noise, so the owners decide. TOPT is
drafted as round-2 issue 7 and overlaps [#397](https://github.com/ufs-community/ccpp-physics/pull/397).

## Defects and fixes

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| D4 | GSL drag removes KE with no heating: `gsd_diss_ht_opt` is a local `.false.`, and when on it heats only the ls + bl part, clipped at 0. | GSL −0.3198 W/m² (C96 `control_p8_ugwpv1`, 24 h) | `gwd_ke_heat` (default off): heat the KE change of the summed GSL increment, taken after the NGW increment → 0; +0.0075 K at 1100–500 hPa, local max 100–210 K/day near the lid. | not proposed (proposal only, owner decision) | [encnv D4](../experiments/conservation/encnv/report.md#d4-physics-gwd_ke_heat-gsl-drag), [conservation §4](../proposals/conservation_proposal.md#4-convection-samf-with-the-gravity-wave-drag-heating-that-shares-its-switches), [row 10](../experiments/conservation/replay/patches/10_D4.diff) |
| D12 | With `tend_opt_pbl` 2 and `tend_opt_gwd` 3, `GFS_GWD_generic_post` applies the PBL and GWD wind increments, both computed from the same state, in one update; the cross term dtp²·(dudt·ten_u + dvdt·ten_v) of its KE is heated by neither. | −0.0663 W/m²; below 850 hPa, mean 3.6 × 10⁻³ K/day, max 47 K/day | Under `gwd_ke_heat`: `gt0 −= dtp²·(dudt·ten_u + dvdt·ten_v)/cp` in case 3 → 0 (new arguments `con_cp` and the switch). | not proposed (proposal only) | [encnv D12](../experiments/conservation/encnv/report.md#d12-physics-gwd_ke_heat-process-split-cross-term), [row 10](../experiments/conservation/replay/patches/10_D4.diff) |
| D4n | UGWP-v1 NGW heating is parameterised from a prescribed launch flux, not taken from the resolved flow. | NGW heating +0.365, its own KE loss 0.033: net source +0.335 W/m² | `ngw_heat_opt` (default 0): 1 = −ΔKE only; 2 = keep the heating and remove the column's net NGW input at the launch layer → 0. Option 2: −0.009 K at 500–200 hPa; option 1: −0.125 K above 1 hPa. | not proposed (proposal only; option 2 recommended) | [encnv](../experiments/conservation/encnv/report.md), [row 11](../experiments/conservation/replay/patches/11_D4n.diff) |
| TOPT | The process-split sum (radiation, PBL, GWD) is applied only by a scheme with option 3, and nothing checks that a 3 follows a 2: tendencies are dropped for (`tend_opt_pbl`, `tend_opt_gwd`) = (1,1), (1,2), (2,1), (2,2), (3,2); option 4 discards silently; `FV3_HRRR_gf_nogwd` never applies radiation or PBL with the defaults. | energy residual +110 to −142 W/m² in the broken combinations (C96 `control_p8_ugwpv1`, 24 h) | Apply any pending sum once in `GFS_suite_interstitial_3`; option 4 is a CCPP error → 2.08–3.12 (default 2.090, bitwise); fixed (2,1), (2,2) at noise. | round-2 issue 7 drafted, not posted | [issue draft](../proposals/round2_issues.md#7-process-split-tendencies-dropped-for-some-tend_opt-combinations), [conservation §8](../proposals/conservation_proposal.md#8-tendency-application-topt-and-gravity-wave-drag), [latent](../experiments/conservation/latent/report.md), [row 26](../experiments/conservation/replay/patches/26_TOPT.diff) |

## Not proposed, or a judgement call

- **Beyond noise, so switched.** `gwd_ke_heat` and `ngw_heat_opt` are the two GWD switches whose forecast change exceeds
  the `consv_te` 0.999 noise ([conservation §15](../proposals/conservation_proposal.md#15-decisions)).
- **D4's peaks near the lid** come from mesoscale GWD breaking in the 50–100 m/s upper-stratosphere and mesosphere jets,
  capped only by `dtfac_meso`; the flux leaves through the lid. The global-mean D4 heating at 0.1–0 hPa is 4 × 10⁻³ K/day.
- **D4n option.** 83 % of the NGW heating is at 500–200 hPa, just above the launch level. Option 2 cancels the net source
  there and leaves the stratosphere and mesosphere unchanged; option 1 halves the mesospheric heating. Option 2 is the
  recommended setting.
- **D12 is not needed** with `tend_opt_pbl` 1 (immediate apply): GWD then sees the post-PBL wind and its −ΔKE is exact.
  The `tend_opt_*` options are `gfs_physics_nml` entries, not hard-coded (an older note said otherwise;
  [conservation §14](../proposals/conservation_proposal.md#14-corrections)).
- **TOPT questions for the owners:** fold the fix into #397 or follow it with a separate PR; option 4 as a CCPP error
  (the patch) or a warning, which would keep 4 as a deliberate switch-off.
- **TOPT does not cover** deep, shallow or MP option 2 after the flush point, or SW/LW options other than 4.
- **Time-split PBL** (`tend_opt_pbl` 1 or 3) differs from the default by 0.21 K and 14.6 Pa by design, not by defect
  ([pbl.md](pbl.md)).

## Reproduce

- Patches: rows 10 (D4 + D12), 11 (D4n) and 26 (TOPT) of the [series](../experiments/conservation/replay/SERIES.md);
  the same changes as `encnv/patches/03_D4.diff`, `04_D4N.diff` and `latent/patches/03_TOPT_process_split_sum_applied_once.diff`.
- Meters: the energy meters ([`../methods/METERS.md`](../methods/METERS.md)) with `encnv/meters/meter_gw_split.diff`
  (bitwise passive); `meter_heat_profile.diff` gives heating by level but is not bitwise passive.
- Runs to compare: [encnv](../experiments/conservation/encnv/report.md) (segment residuals, NGW heating by band) and the
  TOPT gate table in [latent](../experiments/conservation/latent/report.md) (every (`tend_opt_pbl`, `tend_opt_gwd`)
  pair, base and fixed).
- RT: none (nothing posted). Gates: default off bitwise identical to the unfixed tree; 4×6 = 3×8; for TOPT the default
  (2,3) is bitwise and option 4 aborts cleanly in 25–112 s.
