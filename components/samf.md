# SAMF scale-aware mass-flux convection (`samfdeepcnv.f`, `samfshalcnv.f` in ccpp-physics)

**Status (13 November 2026).** SAMF's cloud-base correction creates water and moves tracers (SA1), its deep sub-cloud
mass flux grows downward and crashes HAFS (#401), and its fusion heat, wet-deposition booking and early returns are
wrong. Package 1 carries the fixes: [#405](https://github.com/ufs-community/ccpp-physics/pull/405) (SA1),
[#408](https://github.com/ufs-community/ccpp-physics/pull/408) (D3A, F3 01a, PBL05, SAMF08, early returns deleted) and
[#414](https://github.com/ufs-community/ccpp-physics/pull/414) (`xlamue` floor). All three are approved, none merged; the
full RT on the three has 0 failures. [#403](https://github.com/ufs-community/ccpp-physics/pull/403) (JongilHan66) re-implements all
three and is approved; the code managers have been asked which merges first. Open: T1 sub-stepping and the wet-deposition
export (drafted issues), the SAMF32 build fix (no ufsatm slot), and the energy options D3B and S1/S1K (default off).

## Defects and fixes

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| SA1 | The cloud-base correction subtracts the TVD-limited value `tem1`, not what the updraft took (`eta·qo(kb)`), so water and tracers are created or destroyed wherever the limiter acts (deep and shallow). | creates 0.8 % of convective rain (C96); +0.97 % at C384; a generic convected tracer −2.02 × 10⁻²/day (`develop`, C96, 24 h) | Cloud-base face of the flux and the subtraction both use `eta·qo(kb)` (deep also `edto·etad·qo(jmin)`). | [#405](https://github.com/ufs-community/ccpp-physics/pull/405) approved (dustinswales), package 1 | [water §1](../proposals/water_closure_proposal.md#1-convection-fix-sa1), [Appendix B](../proposals/water_closure_proposal.md#appendix-b--location-of-each-defect-in-current-upstream), [trsamf](../experiments/conservation/trsamf/report.md), [diff 01](../patches/01_SA1_samf_cloud_base_double_count.diff) |
| #401 | Below cloud base, detrainment `0.001·clamt` exceeds entrainment `clamt/z` above about 1 km once TKE raises `clamt`, so the deep sub-cloud mass flux grows downward (101 at `kb`); `xmbmax` bounds the CFL number only at `kbcon`. | `hafs_global_1nest_atm`, 48 h: develop crashes 6 of 10, largest one-step heating 49–96 K; `hafs_global_multiple_4nests_atm`: develop 1 of 5 | Floor deep `xlamue` at `0.001·clamt`: 0 of 10 crash, 5.5–7.6 K. | [#414](https://github.com/ufs-community/ccpp-physics/pull/414) approved (JongilHan66, Qingfu-Liu), package 1; issue [#401](https://github.com/ufs-community/ccpp-physics/issues/401) open | [#414 text](../upstream/posted/PR_XLAMUE_414.md), [#401 text](../upstream/bodies/00_SAMF_ISSUE.md), [HAFS crash](../proposals/pr_round1.md#hafs-crash), [hafs_samf](../experiments/hafs_samf/README.md), [#401 comment](https://github.com/ufs-community/ccpp-physics/issues/401#issuecomment-6488726665) |
| #414 shallow | Shallow has had `xlamud = 0.001·clamt` above `xlamue` below cloud base since fv3atm 06b956a, so its sub-cloud mass flux also grows downward. | `control_p8`, 24 h: grows in 357 k of 2.59 M convecting calls, up to 4.09×; no shallow step heats above 4 K | JongilHan66's form: floor at and below cloud base, cap above (in #403, 62485fc1). | not ours; in [#403](https://github.com/ufs-community/ccpp-physics/pull/403) (approved); #414 stays deep-only ([comment](https://github.com/ufs-community/ccpp-physics/pull/414#issuecomment-6833781177)) | [shal_xlamue_414.md](../upstream/shal_xlamue_414.md) |
| D3A | Detrained condensate is split into ice by a temperature ramp (263 → 233 K) with no heat of fusion. | deep −0.4195, shallow −0.0179 W/m² (C96 `control_p8_ugwpv1`, 24 h); +0.016 K at 500–200 hPa | Add `hfus/cp` × the ice part at the partition; new argument `hfus`. | [#408](https://github.com/ufs-community/ccpp-physics/pull/408) approved (JongilHan66), package 1 | [encnv](../experiments/conservation/encnv/report.md#d3a-bug-fix-samf-detrained-ice), [conservation §4](../proposals/conservation_proposal.md#4-convection-samf-with-the-gravity-wave-drag-heating-that-shares-its-switches), [commit](../patches/pr_round1_patches/ccpp-physics_samf/0001-SAMF-release-the-heat-of-fusion-when-detrained-conde.patch) |
| F3 (01a) | Wet deposition is booked with η(k−1) but removed with η(k), and the borrowing branch zeroes `wet_dep` before adding it back. | scavenged tracer + deposition −7.42 × 10⁻⁴ per day (fscav 0.5, C96, 24 h) | Book with η(k); keep `wet_dep` in the borrowing branch. → +3.0 × 10⁻¹⁵ | [#408](https://github.com/ufs-community/ccpp-physics/pull/408) approved | [latent](../experiments/conservation/latent/report.md), [commit](../patches/pr_round1_patches/ccpp-physics_samf/0002-SAMF-book-convective-wet-deposition-with-the-flux-th.patch) |
| SAMF08 | Six deep early returns sit before the cellular-automaton trigger can re-enable a column, so a column's convection depends on the other columns in its block. | `control_p8_mynn`, 3×8 vs 4×6: 90 of 126 atmf024 variables differ | No early return while a CA-triggered column remains (`caon`). → 0 differ | [#408](https://github.com/ufs-community/ccpp-physics/pull/408) approved | [suites §10.1](../experiments/conservation/suites/report.md#101-p8_mynn-decomposition--fix-08-bug-fix-samf-deep), [commit](../patches/pr_round1_patches/ccpp-physics_samf/0004-samfdeepcnv-no-early-return-before-the-cellular-auto.patch) |
| SAMF early returns | The other early returns skip per-column work done later in the routine (CA trigger, progomega memory, coldpool `buoyexcs`, MG `qlcn`/`qicn`), so results depend on the block. | standalone block test: #408 before deletion 11 of 12 combinations identical (MG differs) | Delete them (deep e5624dd6, shallow e50fcc77): bit-identical to the no-return reference in 48 block tests; physics +1.3 % in `control_p8`. | in [#408](https://github.com/ufs-community/ccpp-physics/pull/408#issuecomment-6485108259), as the owners asked | [samf_returns](../upstream/samf_returns/README.md) |
| T1 (02b) | Tracers (with o3 and TKE) are updated by an explicit TVD step at Courant numbers up to 5, stable only to about 1. | package 1, C96, 24 h: a tracer the PBL does not mix piles up 184–236× in the lowest layers; o3 one-step error median 18 % where C > 2; negative TKE in 12 % of those columns | Sub-step to donor Courant ≤ 0.5 (426 lines, no interface change): negative TKE 0.5 %, SAMF tracer mass ≤ 1.2 × 10⁻¹⁸. | round-2 issue 1 drafted, not posted; text needs the package-1 numbers | [r2_1_t1.md](../experiments/runs_29oct/r2_1_t1.md), [issue draft](../proposals/round2_issues.md#1-samf-tracer-transport-at-courant-numbers-above-1), [trred](../experiments/conservation/trred/report.md), [row 27](../experiments/conservation/replay/patches/27_T1_02b.diff) |
| F3 (01b) | `wet_dep` is computed per scavenged tracer but never exported (`Coupling%wetdpc_flux` is GF/`rrfs_sd` only), so a chemistry tracer's budget cannot close. | no forecast effect | New bucket `cnv_wetdep_<tracer>`; export = meter to 1.3 × 10⁻¹¹. | round-2 issue 9 drafted, not posted | [issue draft](../proposals/round2_issues.md#9-feature-export-samfs-convective-wet-deposition), [latent](../experiments/conservation/latent/report.md), [row 24](../experiments/conservation/replay/patches/24_F3_01b.diff) |
| SAMF32 | `-DSAMFCNV_32BIT=ON` filters the scheme files only, so the three capgen dependencies (`mo_conv_kind.F90`, `progsigma_calc.f90`, `progomega_calc.f90`) stay double and the option does nothing. | ON: 2 of 5 files single precision; OFF bitwise | Filter also searches the capgen dependencies; configure stops if only some are found. `control_p8_samf_conv32`: precipitation −0.50 %, 3-D T −0.0027 K. | not posted; no slot (NOAA-EMC/ufsatm#1156 carries no ufsatm code) | [conservation §9](../proposals/conservation_proposal.md#9-build-samf-single-precision), [ufsatm commit](../patches/pr_round1_patches/ufsatm/0001-ccpp-CMake-compile-SAMF-s-capgen-dependencies-in-sin.patch) |
| D3B | Convective momentum transport conserves momentum, not KE: KE is removed with no heating. | deep −0.1191, shallow −0.0289 W/m² (C96, 24 h) | Interface-form heating behind `samf_cmt_heat` (default off): → +2 × 10⁻¹³; +0.002 K at 500–200 hPa (noise). | not proposed (proposal only, owner decision) | [encnv](../experiments/conservation/encnv/report.md#d3b-physics-samf_cmt_heat-cmt-dissipation), [row 09](../experiments/conservation/replay/patches/09_D3B.diff) |
| S1, S1K | SAMF heats condensation at constant h_vap; frame F needs L_h(T), L_s(T) for detrained ice, and the step-initial T. | Kirchhoff remainder deep −0.245, shallow +0.128 W/m²; S1K gap deep +0.080 W/m² | `samf_kirchhoff` (default off): → 1 × 10⁻¹³; precipitation +0.6 %, rms at noise. | not proposed (proposal only) | [conservation §4](../proposals/conservation_proposal.md#4-convection-samf-with-the-gravity-wave-drag-heating-that-shares-its-switches), rows [15](../experiments/conservation/replay/patches/15_S1_export.diff), [17](../experiments/conservation/replay/patches/17_S1K.diff) |
| DRY (03b) | Chemistry tracers are moved with moist-air fluxes while the write-back keeps each layer's dry mass, so a tracer uniform in dry ratio loses uniformity (also in satmedmfvdifq). | uniform dry tracer, 24 h rms 1.07 × 10⁻³ (all generators); SAMF deep's share 1.04 × 10⁻³ rms | Dry-ratio transport for `chemistry` tracers with `trans_aero`, no switch: → 2.3 × 10⁻⁵; T and q bit-identical. | not proposed (proposal only) | [trsamf](../experiments/conservation/trsamf/report.md), [row 28](../experiments/conservation/replay/patches/28_DRY_03b.diff) |

## Not proposed, or a judgement call

- **SA1 ships with #414.** Alone in HAFS it raises the overshoot rate 1.7× and lowers HAFS precipitation 1.25 %. With
  the floor, overshoot events fall 22 → 12 per member at 48 h ([HAFS crash](../proposals/pr_round1.md#hafs-crash)).
- **SA1's second form**, starting the updraft from the limited value (`qcko(kb) = tem1`), is untested. Changing only
  deep's subtraction would instead heat layer `kb` by 0.07 K per convecting column-step (up to 1.35 K).
- **Other #401 fixes, not taken:** option A (CFL bound below cloud base) works but adds a limit, superseded by the
  floor; JongilHan66's `eta`, `etad` ≤ 1 test gives about 6 K cloud-base heating per step and precipitation −8.1 %; #403's
  floor (2a95266) moves precipitation 2–40× as much as #414 ([HAFS crash](../proposals/pr_round1.md#hafs-crash)).
- **Shallow floor vs cap** is structural, not measurable at 24 h: every form stays within the `consv_te` 0.999 noise and
  moves global precipitation ≤ 0.2 %. JongilHan66 chose his form for #403 ([shal_xlamue_414.md](../upstream/shal_xlamue_414.md)).
- **Parked #401 questions:** which part of 2a95266 moves precipitation, and the residual 4–9 K steps at CFL 1–5.4.
- **Early returns, fallback form:** if the +1.3 % cost is unwanted, a `pending(i)` flag and a single exit give the same
  block independence ([`proto_on_408.diff`](../upstream/samf_returns/proto_on_408.diff)). No UFS suite pairs SAMF deep with MG.
- **T1:** the donor-layer parcel start was dropped (it widens the tracer–q_v gap, 0.10 → 0.17 of the increment).
  Sub-stepping o3 and TKE is a choice that changes them. The draft's link to #401 option A is stale, since #401 took the
  floor. The older figures (100–200×, 19 %, 13 % → 1.6 %, 9–13 of 72 cells) are superseded by
  [r2_1_t1.md](../experiments/runs_29oct/r2_1_t1.md), where T and o3 zonal means are not distinguishable from a 4-member null.
- **D3A and PH1 are disjoint:** D3A pays fusion for detrained ice that stays aloft; PH1 ([surface.md](surface.md)) pays it
  for convective snow.
- **`dtend_*_cnvtrans`** are always zero with SAMF (`GFS_suite_interstitial_4`); a diagnostic gap, no patch.
- **NCAR `main`:** SA1 is a hand port there, because NCAR `main` lacks the single-precision rewrite
  ([#384](https://github.com/ufs-community/ccpp-physics/pull/384)).
- **Not a SAMF bug:** metered and plain builds first diverge in SAMF deep, but the cause is FMA contraction in the
  release flags. Compare executables with `-no-fma`, or against the noise control
  ([samfinit](../experiments/conservation/samfinit/report.md)).

## Reproduce

- Patches: [diff 01 (SA1)](../patches/01_SA1_samf_cloud_base_double_count.diff);
  [#408's four commits](../patches/pr_round1_patches/ccpp-physics_samf/); #414 is one line in `samfdeepcnv.f` (PR branch
  `pr1-xlamue`); options and unposted fixes as rows 09, 15, 17, 24, 25, 27, 28 of the
  [series](../experiments/conservation/replay/SERIES.md) (`apply_series.sh` applies a subset with `ONLY=`).
- Meters: [`../methods/METERS.md`](../methods/METERS.md) (energy meters for D3A/D3B/S1; tracer meters for SA1, T1, DRY;
  `latent/` for wet deposition).
- Runs: HAFS ensembles and print-only `dbg4` blocks in [hafs_samf](../experiments/hafs_samf/README.md); early-return block
  test and timing in [samf_returns](../upstream/samf_returns/README.md); T1 on package 1 in
  [r2_1_t1.md](../experiments/runs_29oct/r2_1_t1.md).
- RT: package 1 (#405 + #408 + #414, deep returns deleted; `rt_sxd5`, job 10328901): 54/54 compile, 122 identical,
  95 change, 15 not started, 0 fail ([POSTING.md](../upstream/POSTING.md)).
