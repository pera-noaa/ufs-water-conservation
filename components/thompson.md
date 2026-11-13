# Thompson microphysics (`module_mp_thompson.F90`, `mp_thompson.F90` in ccpp-physics)

**Status (13 November 2026).** Thompson removes water on net, −0.68 % of grid-scale precipitation at C96 on `develop`:
its CCPP driver converts on two mass bases, and the scheme loses track of mass in graupel limiting, sedimentation and
clipping. [#406](https://github.com/ufs-community/ccpp-physics/pull/406) (TH1, TH3, TH4, TH5) is approved by
dustinswales, rhaesung and AndersJensen-NOAA, not merged; it goes in microphysics package 2 with #407 and #413.
Drafted, not posted: TH2, TH6, TH7 (each has a second reasonable form); TH8 + TH9 as one round-2 diff, waiting on the
Noah-MP canopy wetted-fraction question; and the `prg_rcg` re-close issue promised in #406's review. The energy
options K1 and TFH are default-off and not posted.

## Defects and fixes

Line numbers for each defect in `ufs/dev` @242a2fc: [water proposal, Appendix B](../proposals/water_closure_proposal.md#appendix-b--location-of-each-defect-in-current-upstream).
Percentages are of grid-scale precipitation (P_grid) unless stated.

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| TH1 | `mp_thompson.F90` converts species to mixing ratio with `1/(1 − q_v)` but back with `1/(1 + r_v)` of the updated vapour, while FV3 rebuilds mass on the input layer mass. | removes 0.4 % of grid-scale rain (C96, 24 h) | convert back with `×(1 − spechum)`, the input humidity both ways | [#406](https://github.com/ufs-community/ccpp-physics/pull/406) approved | [proposal §2](../proposals/water_closure_proposal.md#2-thompson-microphysics-fixes-th1th7-and-th8-with-th9-in-round-2), [diff 02](../patches/02_TH1_thompson_mass_basis.diff), [reply on the sign](../upstream/replies/reply_406_signs.posted.md) |
| TH2 | Cloud water settling out of the lowest layer is added to no precipitation total, and cloud sedimentation is not substepped, so a thin layer can lose more than it holds. | removes 0.15 % of grid-scale rain (C96); `regional_control` reported precipitation +10.9 % with the fix | count `sed_c(kts)` as rain; substep cloud like the other species | drafted, not posted (second-form PR) | [proposal §2](../proposals/water_closure_proposal.md#2-thompson-microphysics-fixes-th1th7-and-th8-with-th9-in-round-2), [diff 03](../patches/03_TH2-TH3_thompson_settling_and_graupel_closure.diff), [PR text §3.7](../proposals/pr_round1_descriptions.md#37-thompson-fixes-with-a-second-form-track-1e) |
| TH3 | Graupel gains from rain–snow and rain–ice collection are not recomputed after the clips and rate limiters cut the matching losses. | creates 0.76 % of grid-scale rain in the first 6 h, 0.03 % after (C96 cold start) | recompute both graupel gains after the limiters; below 0 °C cap snow's gain at the rain lost | [#406](https://github.com/ufs-community/ccpp-physics/pull/406) approved | [proposal §2](../proposals/water_closure_proposal.md#2-thompson-microphysics-fixes-th1th7-and-th8-with-th9-in-round-2), [diff 03](../patches/03_TH2-TH3_thompson_settling_and_graupel_closure.diff), [reply to review](../upstream/replies/reply_406_anders.md) |
| TH4 | Density is recomputed from the heated temperature three times before sedimentation, so each kilogram that falls removes about 1 + ΔT/T kilograms of host water. | removes 0.11 % of grid-scale rain (C96) | entry density for every mass conversion; updated density only for fall speeds and viscosity | [#406](https://github.com/ufs-community/ccpp-physics/pull/406) approved | [proposal §2](../proposals/water_closure_proposal.md#2-thompson-microphysics-fixes-th1th7-and-th8-with-th9-in-round-2), [diff 04](../patches/04_TH4_thompson_sedimentation_density.diff) |
| TH5 | The driver takes layer depth from `phii`, computed before convection heats the column, so ρ·dz drifts from the host's layer mass. | removes 0.014 % of grid-scale rain (C96); a depth fixed for the whole step lost 0.026 % of precipitation in 24 h with `dt_inner` = 150 s | pass `prsi`; depth = host dry-air layer mass / Thompson's entry density, every inner step | [#406](https://github.com/ufs-community/ccpp-physics/pull/406) approved | [proposal §2](../proposals/water_closure_proposal.md#2-thompson-microphysics-fixes-th1th7-and-th8-with-th9-in-round-2), [diff 05](../patches/05_TH5_thompson_layer_depth_from_host_mass.diff), [reply on `dz`](../upstream/replies/reply_406_anders_dz.md) |
| TH6 | Hydrometeors that end the step negative or below `R1` are deleted, and vapour below its 10⁻¹⁰ floor is topped up from nothing. | creates 0.002 % (C96) | clipped condensate to vapour with its latent heat; refill the floor from the layer's condensate, then the column's vapour | drafted, not posted (second-form PR) | [proposal §2](../proposals/water_closure_proposal.md#2-thompson-microphysics-fixes-th1th7-and-th8-with-th9-in-round-2), [diff 06](../patches/06_TH6_thompson_clipped_condensate_and_vapour_floor.diff) |
| TH7 | Water at or below `R1` = 10⁻¹² is deleted on entry, in `semi_lagrange_sedim` and as leftover rain after the source/sink terms. | removes 2 × 10⁻⁸ of precipitation; physics residual −6.0 × 10⁻⁸ → −4.0 × 10⁻¹⁵ kg/m² (`develop`, 24 h) | to vapour with its latent heat; `semi_lagrange_sedim` returns what it does not move | drafted, not posted (second-form PR) | [proposal §2](../proposals/water_closure_proposal.md#2-thompson-microphysics-fixes-th1th7-and-th8-with-th9-in-round-2), [diff 07](../patches/07_TH7_thompson_r1_to_vapour.diff) |
| TH8 | Sedimentation out of the lowest layer is counted as precipitation only above `R1·rr_min`, although its mass has left. | removes 2 × 10⁻⁷ of precipitation; water 7.1 × 10⁻¹² kg/m²/s, energy +2.37 × 10⁻⁶ W/m² (C96, 24 h); alone, land canopy evaporation −68 % (f06), −47 % (f24) | count all of it | drafted, not posted (round-2 issue 2, one diff with TH9) | [proposal §7](../proposals/water_closure_proposal.md#7-what-remains), [energy §5](../proposals/conservation_proposal.md#5-microphysics-thompson), [round-2 issue 2](../proposals/round2_issues.md#2-thompson-surface-sedimentation-trace-and-the-noah-mp-canopy-wetted-fraction), [held diff](../patches/held/TH8_thompson_count_all_surface_sedimentation.diff) |
| TH9 | Flux-form ice and snow sedimentation moves the `R1` placeholder of an absent species as if it were mass, re-created every substep; with TH8 it becomes booked fake precipitation. | with TH8, land canopy evaporation at f06 −68 % → −2.9 % with stock `fwet` (C96); at noise from 6 h only with the E2 `fwet` change | start flux-form sedimentation from each layer's actual content | drafted, not posted (one unconditional diff with TH8) | [energy §5](../proposals/conservation_proposal.md#5-microphysics-thompson), [canopy report](../experiments/conservation/canopy/report.md), [held diff](../patches/held/TH9_thompson_placeholder_not_sedimented.diff) |
| `prg_rcg` | Below freezing the graupel check counts the unscaled rain–graupel gain, which Re-enforce then cuts to the limited rain loss; graupel can end negative and be zeroed, which creates water. | not measured (found by reading the code) | set `prg_rcg = −prr_rcg` right after the rain check, as #406 does for rain–snow | drafted, not posted (issue owed on #406) | [issue draft](../upstream/issues/issue_thompson_prg_rcg.md), [reply to review](../upstream/replies/reply_406_anders.md) |

## Not proposed, or a judgement call

- **TH2, second form:** keep settled cloud in the lowest layer. It also conserves, gives `regional_control` +4.8 %
  instead of +10.9 %, and suppresses cloud deposition at the ground. The PR text states both forms and recommends
  counting ([alternatives](../proposals/pr_round1.md#alternatives)).
- **TH6 and TH7, second forms:** return the clipped condensate only and leave the floor (TH6); fix only the entry and
  leftover rain (TH7). Where the water goes is a choice, so both forms go in one PR.
- **TH4/TH5 alternative** ([`thdz/`](../upstream/thdz/)): recompute ρ as `develop` does, reset `dz = dm/ρ` after each
  update and rescale the stored densities. It closes to round-off like the proposed form (rW/P 5.6e-16 and 7.3e-16
  against 7.7e-16 and 2.1e-15, `control_p8_mynn` and `rap_control`, 24 h); MP precipitation −0.046 % and +0.30 %
  against ours. Kept for a reviewer who asks ([roadmap step 2.6](../upstream/ROADMAP.md#2-package-2-microphysics--406-407-approved-413),
  [record](../upstream/POSTING.history.md)).
- **TH5 interface:** `dz` stays beside `dm`, as AndersJensen-NOAA asked; the module computes the depth from `dm` at
  each inner step. Computing `dz` once in the driver would lose the 0.026 % above.
- **TH8 without TH9 is withdrawn**; the pair ships unconditionally once the Noah-MP `fwet` question
  ([round-2 issue 2](../proposals/round2_issues.md#2-thompson-surface-sedimentation-trace-and-the-noah-mp-canopy-wetted-fraction))
  is answered. "TH8 is about noise" was a global-mean statement and is corrected.
- **K1 `thompson_kirchhoff`** (default `.false.`, physics change): Thompson's own c_p(1 + 0.887 r_v) and L(T). Changes
  its latent heat at 220–250 K by −0.14 % (deposition), −0.24 % (condensation), +1.3 % (freezing); at noise.
- **TFH `thompson_frame_heat`** (default `.false.`, physics change): Thompson frame-F gap +0.0083 → 9 × 10⁻¹³ W/m²;
  0.143 K / 7.73 Pa / 3.01 W/m², at noise ([energy §5](../proposals/conservation_proposal.md#5-microphysics-thompson)).
- **Edges left:** a column with no vapour can still be floored after TH6's refill, and TH7's entry exchange leaves
  latent heat unpaid where no vapour exists (under 40 J/m²).
- **Not tested:** cycled runs and analysis increments (whether they cause TH3-like bursts).
- **Other copies:** TH2–TH4 and TH6 are in the WRF, MPAS and TEMPO copies of the scheme. The WRF and MPAS ports are
  measured, not posted ([ports](../patches/ports/README.md#which-fixes-go-where)); TEMPO: [`tempo.md`](tempo.md).

## Reproduce

- **Diffs** against `ufs/dev` @242a2fc, applied in order: [02](../patches/02_TH1_thompson_mass_basis.diff),
  [03](../patches/03_TH2-TH3_thompson_settling_and_graupel_closure.diff),
  [04](../patches/04_TH4_thompson_sedimentation_density.diff),
  [05](../patches/05_TH5_thompson_layer_depth_from_host_mass.diff),
  [06](../patches/06_TH6_thompson_clipped_condensate_and_vapour_floor.diff),
  [07](../patches/07_TH7_thompson_r1_to_vapour.diff); TH8 then TH9 from [`held/`](../patches/held/), or as one diff,
  [`43_TH8-TH9_unconditional.diff`](../experiments/conservation/replay/patches/43_TH8-TH9_unconditional.diff).
- **Commit series:** #406's four commits as cut ([`ccpp-physics_thompson/`](../patches/pr_round1_patches/ccpp-physics_thompson/));
  TH2, TH6, TH7 on top ([`ccpp-physics_thompson_p1/`](../patches/pr_round1_patches/ccpp-physics_thompson_p1/)).
- **Energy options:** K1 [`05_ccpp-thompson_kirchhoff_option.diff`](../experiments/conservation/encpl/patches/05_ccpp-thompson_kirchhoff_option.diff),
  TFH [`08_ccpp-thompson_frame_F_heating.diff`](../experiments/conservation/energy/patches/08_ccpp-thompson_frame_F_heating.diff).
- **Meter:** [`../methods/METERS.md`](../methods/METERS.md), rows "Does the physics create or destroy water?" and
  "Where in Thompson?" (upstream layout); the suites meter for the `thdz/` comparison.
- **Compare against:** the per-fix, `develop` (C96, C384) and 10-day tables in
  [proposal §6](../proposals/water_closure_proposal.md#6-results).
- **RT:** #406 with #407, full `rt.sh`, Intel + GNU (develop 5651397d, baselines 20261016): 54/54 compile, 57 tests
  identical, 150 change answers, 25 restart tests not started, none fails ([#406 text](../upstream/posted/PR_TH.md)).
  A local package-2 merge (#406 + #407 + #413, WM develop 560345cc): 151 baseline changes, 109 pass, 25 restart tests
  not started, 1 run failure that also fails on `develop` ([record](../upstream/tempo/PREREG_tp407.md)). The final
  water tree (diffs 01–19 + 09b) against its own baselines: 234/234 bit for bit
  ([Appendix A](../proposals/water_closure_proposal.md#appendix-a--patches-and-scripts)).
