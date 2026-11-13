# Boundary layer: satmedmfvdifq and the other GFS PBL schemes (`satmedmfvdifq.F`, `mfscuq_mlm.f`, `shinhongvdif.F90` in ccpp-physics)

**Status (13 November 2026).** satmedmfvdifq heats by TKE dissipation rather than by the KE its momentum solve removes
(D1, the largest single energy gap), its surface sources used 1/Δz instead of the layer mass (PBL05), and the MLM from
#390 neither conserves nor stays in bounds (#404). PBL05 is in [#408](https://github.com/ufs-community/ccpp-physics/pull/408)
(approved, package 1, not merged). Issue [#404](https://github.com/ufs-community/ccpp-physics/issues/404) carries a tested
fix with an RT pass; no reply. On [#403](https://github.com/ufs-community/ccpp-physics/pull/403) the `diff3d` leak is
answered (divide by the physics' `del`). [NCAR/ccpp-physics#1251](https://github.com/NCAR/ccpp-physics/issues/1251) is
open. Open: D1, PBK and PBF (default-off options, not posted), the MLM's negative condensate, and the MLM index fix (offered).

## Defects and fixes

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| D1 | The dissipative heating is the TKE dissipation of the last of 20 substeps, not the KE the momentum solve removes: TKE floors, shear production from the old winds and TKE gained outside the scheme add heat with no KE sink. | PBL +1.4273 W/m² (heating 3.677 vs KE loss 2.248; C96 `control_p8_ugwpv1`, 24 h) | Boville–Bretherton interface heating behind `dspheat_ke` (default off): → +1.6 × 10⁻¹²; land T2m −0.073 K (day), T2m rms 0.334 vs noise 0.156. | not proposed (proposal only, owner decision) | [enpbl](../experiments/conservation/enpbl/report.md#3-the-energy-consistent-option-patch-04), [conservation §3](../proposals/conservation_proposal.md#3-boundary-layer), [row 06](../experiments/conservation/replay/patches/06_D1_dspheat_ke.diff) |
| PBK | The condensate filler (vapour ↔ cloud water) uses constant h_vap, not L_h(T). | +4.8 × 10⁻⁵ W/m² | `pbl_kirchhoff` (default off): → 0, at noise. | not proposed (proposal only) | [conservation §3](../proposals/conservation_proposal.md#3-boundary-layer), [row 19](../experiments/conservation/replay/patches/19_PBK.diff) |
| PBF | PBL condensate transport is treated as vapour by the coupling's `cpl_water_energy` bit 4. | PBL gap −0.00485 W/m² | Export the condensate flux; acts under bit 4 with `pbl_kirchhoff`: → 8 × 10⁻¹³. | not proposed (proposal only) | [row 22](../experiments/conservation/replay/patches/22_PBF.diff) |
| PBL05 | Surface sources are applied with dt/(z_i2 − z_i1) while the fluxes were made kinematic with ρ_a, so applied ≠ reported by the non-hydrostatic δz deviation. | GFDL v16 suite water +2.6 × 10⁻⁸ kg/m²/day; zero by construction in P8 | `dtdz1 = dt2·rho_a·g/del(1)`: → −3.6 × 10⁻¹⁶; at noise. | [#408](https://github.com/ufs-community/ccpp-physics/pull/408) approved (JongilHan66), package 1 | [suites §10.3](../experiments/conservation/suites/report.md#103-satmedmfvdifq-water-residual--fix-05-numerical-consistency), [commit](../patches/pr_round1_patches/ccpp-physics_samf/0003-satmedmfvdifq-apply-surface-fluxes-to-the-host-layer.patch) |
| #404 cause 1 | MLM cloud-base smoothing replaces the k−1 tendencies of T, q and cloud water with the mean of their neighbours, which is not column-conserving. | −0.88 W/m², −6.0 × 10⁻⁴ kg/m² (C96 `control_p8`, 24 h, `mlm` on) | Take the change at k−1 from k and k−2 in proportion to their mass. | issue [#404](https://github.com/ufs-community/ccpp-physics/issues/404) open, fix in the description, no reply | [#404 text](../upstream/issues/issue_404_body_v2.md), [upchk](../experiments/conservation/upchk/report.md) |
| #404 cause 2 | MLM tendencies are `−ΔF/dz` of kinematic fluxes with no density, and `dz` is the thickness of layer k+1. | the MLM as merged: −1.28 W/m², +4.4 × 10⁻⁴ kg/m²/day (C96 `control_p8`, 24 h, `mlm` on) | Flux form `−g·(ρF(k+1) − ρF(k))/del(k)`, with `del` passed from satmedmfvdifq; MLM water and energy then close to ~1e-19 of the gross. | as above | [#404 text](../upstream/issues/issue_404_body_v2.md), [mlm_diff3d.md](../experiments/runs_29oct/mlm_diff3d.md) |
| #404 cause 3 | `mlmb` can be 0 in an active column (only `mlmb = 1` is screened), so the block at `mlmb − 1` writes level −1 and `b` is read unset. | NaN, segfaults, or bottom layers 40–52 K colder than the layer above | Switch the MLM off when `mlmb ≤ 1`; set `b` at every level. Cold columns −51.8 K → −3.6 K. | as above | [mlm_diff3d.md](../experiments/runs_29oct/mlm_diff3d.md) |
| #404 cause 4 | Inactive columns with `krad = 2` keep `mlmt = 0`, `mlmb = 1`, so the mixed-layer means divide 0 by 0. | `control_debug_p8` with `mlm` on traps at step 3 (Intel and GNU) | Compute the means only where `cnvflg` is true. | as above | [r15_mlm results](../experiments/runs_29oct/r15_mlm/results.md) |
| #404 index | `ntsw` and `ntinc` are full-tracer indices used on the vertically diffused arrays; they coincide in P8 as shipped (latent). | passive tracer added at slot 7, `mlm` on: 38 of 44 output files differ | New interstitial indices `ntswx`, `ntincx` in diffusion order (ufsatm `CCPP_typedefs` + `satmedmfvdifq.meta`); `mlm` off bitwise. | offered in #404, not posted | [r15_mlm index](../experiments/runs_29oct/r15_mlm/index.md) |
| MLM negative condensate | The explicit MLM update can remove more condensate from a layer than it holds (with or without the fix). | 0.14 kg/m² per day of negative water; Thompson's entry clip turns it into a 0.10 kg/m²/day water source, about 3 % of surface evaporation | None built: limit each condensate flux to its source layer, or solve the MLM fluxes implicitly. | asked in #404 | [r15_mlm results](../experiments/runs_29oct/r15_mlm/results.md), [trace.md](../experiments/runs_29oct/r15_mlm/trace.md) |
| #403 `diff3d` | FV3 `diff3d` horizontal-diffusion tendencies cancel per unit area, but satmedmfvdifq applies them to mixing ratios on its own layer mass, so the net leaks. | net/gross −2.8 × 10⁻² (T), −9.8 × 10⁻³ (`sphum`); PBL water −1.3 × 10⁻⁵ kg/m² (C96 `control_p8`, 24 h, `sa3dtke` on) | Divide the face-flux divergence by satmedmfvdifq's `del` (`delp` minus condensates), not FV3's `delp`: ≤ 7.5 × 10⁻¹⁶. JongilHan66's update ÷ `delp` cuts the leak about 17-fold only. | answered on [#403](https://github.com/ufs-community/ccpp-physics/pull/403#issuecomment-6818866209) (approved PR) and [NOAA-GFDL/GFDL_atmos_cubed_sphere#429](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/pull/429) | [mlm_diff3d.md](../experiments/runs_29oct/mlm_diff3d.md), [reply as posted](../upstream/replies/reply_403_4.md) |
| #403 stencil | The `diff3d` stencil differences `q·dx` across a face, so a uniform tracer gets a tendency wherever the grid spacing varies (it nets to zero). | up to 3.7 × 10⁻⁹ /s | Difference `q` itself: exactly 0. | in the same #403 comment | [reply as posted](../upstream/replies/reply_403_4.md), [dxc reply](https://github.com/ufs-community/ccpp-physics/pull/403#issuecomment-6837094612) |
| sa3dtke | With `sa3dtke`, TKE shear production uses the dycore's `def_1`, which exceeds the KE the PBL removes; 88 % of the extra production becomes heat. | PBL residual +1.432 → +2.510 W/m² (`sa3dtke` off → on, C96 `control_p8`, 24 h) | D1 `dspheat_ke` closes it: −1.832 × 10⁻³, the `diff3d` leak. | not posted | [upchk](../experiments/conservation/upchk/report.md) |
| NCAR#1251 | In `shinhongvdif.F90` the ozone tendency diagnostic sits outside the loops with stale `i`, `k`, so it adds `ten_q(1,1,ntoz)` everywhere. | reached in the SCM (`SCM_GFS_v15p2_saYSU`, `_ps` suite); bounds-checked builds trap; not run | `ten_q(:,:,ntoz)` | [NCAR/ccpp-physics#1251](https://github.com/NCAR/ccpp-physics/issues/1251) open, untagged | [issue text](../upstream/issues/issue_vdiff_indices_draft.md) |
| DRY (03b) | Chemistry tracers are mixed with moist-air fluxes while the write-back keeps each layer's dry mass (also in SAMF). | PBL's share of a uniform dry tracer's 24-h deviation: rms 1.8 × 10⁻⁴, max 7.0 × 10⁻³ | Dry-ratio transport for `chemistry` tracers, no switch; T and q bit-identical. | not proposed (proposal only) | [conservation §7](../proposals/conservation_proposal.md#7-tracer-transport-in-fv3), [row 28](../experiments/conservation/replay/patches/28_DRY_03b.diff) |

## Not proposed, or a judgement call

- **D1 needs `dspfac` = 1** to close; otherwise the residual is exactly (dspfac − 1) × the dissipation. Whether `dspfac`
  is ignored when `dspheat_ke` is on is the owners' call. A strictly non-negative variant (clip D < 0, rescale) is
  available. The round-1 per-layer −ΔKE form is withdrawn: it cooled layers that import KE (−0.62 W/m²).
- **D1 untested path:** with `use_oceanuv` the surface work is computed in the ground frame.
- **The #404 fix changes the forecast** beyond the 10-member `consv_te` spread: PBL height −0.7 %, precipitation −0.7 %,
  low cloud −1.2 % cover. Not split between density, layer thickness and smoothing ([results](../experiments/runs_29oct/r15_mlm/results.md)).
- **A 2.6 × 10⁻⁹ kg/m²/day PBL water gap** seen with the first MLM fix is the old `dtdz1` surface-flux line, which PBL05
  replaces; no further PBL change is implied ([trace.md](../experiments/runs_29oct/r15_mlm/trace.md)).
- **Hard-coded tracer slots:** `satmedmfvdifq.F` sums `q1(:,:,5)+q1(:,:,6)` (snow, graupel) for `sa3dtke`; correct only
  where snow is 5 and graupel 6. With MG and `cplchm`, `ntcwx` and the others are set before `cplchm` changes `nvdiff`.
  Neither is fixed ([index.md](../experiments/runs_29oct/r15_mlm/index.md)).
- **Other PBL schemes:** satmedmfvdif and satmedmfvdifq_can heat as D1 does; hedmf's heating is not −ΔKE; YSU and
  Shinhong have none, so their KE loss is an energy sink ([enpbl history §6](../experiments/conservation/enpbl/report.history.md)).
- **Time-split PBL** (`tend_opt_pbl` 1 or 3) differs from the default by 0.21 K and 14.6 Pa by design. The combinations
  that drop tendencies are TOPT ([gwd.md](gwd.md)).
- **MYNN's** remaining frame-P gap is the same TKE/KE accounting question as D1 ([mynn.md](mynn.md)).

## Reproduce

- Patches: [PBL05 commit](../patches/pr_round1_patches/ccpp-physics_samf/0003-satmedmfvdifq-apply-surface-fluxes-to-the-host-layer.patch);
  D1, PBK, PBF, DRY as rows 06, 19, 22, 28 of the [series](../experiments/conservation/replay/SERIES.md); #404 fix v3
  [`fix_v3.diff`](../experiments/runs_29oct/r15_mlm/fix_v3.diff) and the index fix
  ([ufsatm](../experiments/runs_29oct/r15_mlm/index_fix_ufsatm.diff), [ccpp-physics](../experiments/runs_29oct/r15_mlm/index_fix_ccpp-physics.diff));
  the #403 face-flux form is in the [posted reply](../upstream/replies/reply_403_4.md).
- Meters: [`../methods/METERS.md`](../methods/METERS.md) (energy meters and `enpbl/meters/`; the #403/#390 ports in
  `upchk/scripts/`).
- Runs to compare: [enpbl](../experiments/conservation/enpbl/report.md) (D1), [upchk](../experiments/conservation/upchk/report.md)
  (#403, #390), [mlm_diff3d.md](../experiments/runs_29oct/mlm_diff3d.md) and [r15_mlm](../experiments/runs_29oct/r15_mlm/results.md) (#404).
- RT: #404 fix v3 on ufs-weather-model 3d0703d2 (develop 560345cc + package 1), `mlm` on: `control_p8`, `control_debug_p8`
  (Intel and GNU), `control_restart_p8`, `control_decomp_p8`, `control_2threads_p8` pass. PBL05 is in the package-1 RT
  (54/54 compile, 0 fail; [POSTING.md](../upstream/POSTING.md)).
