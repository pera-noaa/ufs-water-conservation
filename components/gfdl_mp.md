# GFDL microphysics v3 (`gfdl_cloud_microphys_v3.F90`, `gfdl_cloud_microphys_v3_mod.F90` in ccpp-physics; `model/gfdl_mp.F90` in NOAA-GFDL/GFDL_atmos_cubed_sphere)

**Status (13 November 2026).** In UFS, the CCPP wrapper discards the updated `delp` that matches the species GFDL MP
returns, so the host rebuilds them on the wrong layer mass (the TH1 defect), and `terminal_fall` passes the ice heat
capacity for falling rain and cloud water; the second defect is also in GFDL's own `gfdl_mp.F90`. Both UFS fixes are
[#413](https://github.com/ufs-community/ccpp-physics/pull/413), open with no review yet; microphysics package 2 (#406,
#407, #413) waits on it. GFDL's copy: issue [#430](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/issues/430) and
PR [#431](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/pull/431), open, no review yet. The energy gaps left are
GFDL's own constants and frame; none is proposed.

## Defects and fixes

Case: C96 `control_iovr4_gfdlmpv3` (`FV3_GFS_v16_gfdlmpv3`), 24 h, in-model suites meter.

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| GFDL02 | `mpdrv` converts in with `1/(1 − q_v)` and out with `1/(1 + q_v,new)`, returning species on its updated `delp`; the CCPP wrapper keeps that `delp` local, so the host applies them to the pre-physics layer mass. | MP water −8.39 × 10⁻³ kg/m²/day, −1.03 % of MP precipitation; the suite loses 0.3 % of precipitation per 6 h | wrapper rescales the returned species by `delp_out/delp_in`; GFDL's module unchanged | [#413](https://github.com/ufs-community/ccpp-physics/pull/413), open, no review yet | [suites §4](../experiments/conservation/suites/report.md#4-e4-gfdl-mp-v3-fv3_gfs_v16_gfdlmpv3-control_iovr4_gfdlmpv3-do_sat_adj--true), [energy §10](../proposals/conservation_proposal.md#10-other-suites-mynn-edmf-gfdl-mp-v3-grellfreitas), [proposal E.4](../proposals/water_closure_proposal.md#appendix-e--separate-issues-found-along-the-way), [wrapper diff](../upstream/gfdl_wrap/wrapper_fix.diff) |
| GFDL07 | `terminal_fall` passes `c_ice` to `sedi_heat` for every species, so falling rain and cloud water exchange heat with the ice heat capacity. | energy residual (GFDL's constants, with water PE) +0.20 → −0.007 W/m² (the fix is 0.21); T −0.003 K | pass `c_liq` for rain and cloud water | [#413](https://github.com/ufs-community/ccpp-physics/pull/413), open, no review yet | [suites §10.2](../experiments/conservation/suites/report.md#102-design-energy-gaps), [#413 text](../upstream/posted/PR_GMP_413.md), [diff](../experiments/conservation/suites/patches/07_E4c_gfdlmp_v3_rain_sedimentation_heat_capacity.diff) |
| GFDL07 (GFDL copy) | The same `c_ice` call in GFDL's own `gfdl_mp.F90` ([L2692](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/blob/8b94b9f3e54dbd04caff0ef28913d3c2ea5c1a70/model/gfdl_mp.F90#L2692)). | one 300 s step of falling rain or cloud water creates 6 × 10⁻⁵ of the column energy (standalone `gfdl_mp.F90` from `main`); 2 × 10⁻¹⁶ with the fix | the same `c_liq` call | issue [#430](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/issues/430) + PR [#431](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/pull/431), open, no review yet | [issue text](../upstream/gfdl_sedi/issue_post.md), [PR text](../upstream/gfdl_sedi/pr_post.md), [test](../upstream/gfdl_sedi/test_sedi.F90) |

Forecast impact (24 h, against the `consv_te` = 0.999 noise pair): GFDL02 T +0.001 K, precipitation +0.15 %, rms
1.1–1.3× noise; GFDL07 T −0.003 K, rms 1.1–1.3×. Both are unconditional bug fixes.

## Not proposed, or a judgement call

- **GFDL02, in-module form:** convert back with the input humidity inside `mpdrv` (one line). It closes equally (MP
  water rW/P 1.6e-15 against 1.5e-14 for the wrapper form; the two forecasts differ within noise) and is superseded by
  the wrapper form, which leaves GFDL's module as upstream. GFDL MP itself is self-consistent (it returns species on its
  updated `delp`, and GFDL's own `gfdl_mp.F90` has the same conversion); the defect is the CCPP wrapper's, so nothing
  goes to GFDL for it ([posting record](../upstream/POSTING.history.md)).
- **E4b `gfdl_mp_host_cp`** (constant-pressure thermodynamics from the host): tested, not proposed. It cuts the gap only
  from 0.117 to 0.085 W/m², because `sedi_heat` keeps c_v hard-coded
  ([`E4b` diff](../experiments/conservation/suites/patches/not_proposed/E4b_gfdlmp_v3_host_constant_pressure.diff)).
- **Energy left by design:** −0.007 W/m² in GFDL's own frame (w-sedimentation KE is not metered), −0.028 W/m² in
  frame F with water PE; −0.021 W/m² comes from GFDL's own constants (c_liq 4218 vs 4185.5, c_ice 2106 vs 1972, tice
  273.16). `sedi_heat` turning the potential energy of falling hydrometeors into heat (+0.61 W/m²) is physical, a frame
  term ([energy §13](../proposals/conservation_proposal.md#13-what-remains)).
- **Inactive here:** `rainmin` zeroing and settled cloud water `water0` (not in `prcp0`) are zero in this case; they
  would leak if active.
- **Not touched:** the inline branch, where FV3 updates `delp` itself.
- **Not tested:** HAFS `FV3_HAFS_v1_gfdlmpv3_tedmf`; SHiELD.

## Reproduce

- **Patches:** mass basis, wrapper form [`wrapper_fix.diff`](../upstream/gfdl_wrap/wrapper_fix.diff); in-module form
  [`02_E4_gfdlmp_v3_mass_basis.diff`](../experiments/conservation/suites/patches/02_E4_gfdlmp_v3_mass_basis.diff);
  heat capacity [`07_E4c_…diff`](../experiments/conservation/suites/patches/07_E4c_gfdlmp_v3_rain_sedimentation_heat_capacity.diff),
  also as the commit [`ccpp-physics_gfdlmp/0002`](../patches/pr_round1_patches/ccpp-physics_gfdlmp/0002-GFDL-MP-v3-terminal_fall-rain-and-cloud-water-fall-w.patch).
  GFDL's copy: the bundle in [`gfdl_sedi/`](../upstream/gfdl_sedi/).
- **Column tests:** [`gfdl_wrap/`](../upstream/gfdl_wrap/) (`run.sh`, `test_gmp.F90`: the real wrapper and module, 16
  columns × 64 levels); [`gfdl_sedi/`](../upstream/gfdl_sedi/) (`run.sh REV PREC`, `test_sedi.F90`: GFDL `main`,
  gfortran).
- **Meter:** the suites meter, [`01_suites_meter.diff`](../experiments/conservation/suites/meters/01_suites_meter.diff)
  (`02_` on the fixed tree); see [`../methods/METERS.md`](../methods/METERS.md).
- **Compare against:** [suites §4](../experiments/conservation/suites/report.md#4-e4-gfdl-mp-v3-fv3_gfs_v16_gfdlmpv3-control_iovr4_gfdlmpv3-do_sat_adj--true)
  (unfixed m0 −8.39e-3, fixed mf6 −1.05e-15 kg/m²/day) and the frame table in
  [§10.2](../experiments/conservation/suites/report.md#102-design-energy-gaps).
- **RT:** #413 with #408, #409, #410, full `rt.sh`, Intel + GNU (develop 3e48f4cc, baselines 20261022): 54/54 compile,
  116 identical, 101 change answers, 15 restart/IAU tests not started, none fails ([#413 text](../upstream/posted/PR_GMP_413.md)).
  A local package-2 merge (#406 + #407 + #413): 151 baseline changes, 109 pass, 25 restart tests not started, 1 run
  failure that also fails on `develop` ([record](../upstream/tempo/PREREG_tp407.md)). Gates on the final tree:
  `gfdlmpv3` 3×8 = 4×6 bitwise ([suites §10.5](../experiments/conservation/suites/report.md#105-final-gates-x10m10--no-fma)).
