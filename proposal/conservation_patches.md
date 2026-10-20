# Conservation follow-on: patch manifest

*Companion to `conservation_proposal.md`. Draft, 18 October 2026. Nothing has been posted. Lists every diff of the
final tree `full14` in apply order, then the diffs that are not in it, the instrumentation, and the re-anchoring a
replay or a PR split meets. Local paths are relative to `/Users/pera/Documents/ash-code/ufs-chem-v1/conservation/`.*

## Status

- **Submission.** Round 1 re-cuts the unconditional bug fixes (minus R1, TOPT, MYNN) on current upstream heads,
  regrouped by owner: `pr_round1.md`. This manifest describes the full `full14` series.
- **Authority.** `replay/SERIES.md` and `replay/apply_series.sh` define the series: 55 proposed diffs (rows 01–57; row 16
  is retired into 43, and 56 is `56_NOFMA`, the `-no-fma` build setting, not proposed). Where this manifest and `SERIES.md` differ,
  `SERIES.md` is right.
- **Verified.** Applied at `patch -F0` to the base, the series reproduces `full14`: `diff -r` of the sources is empty,
  and the rebuilt executable's 24-h runs, all-on and default-off, are byte-identical to full14's. Known-bad: leaving out
  row 57 fails on 3 files. The bug-fix arm (`fx` + the unconditional rows) equals energy's `gB14`. The `full13` series
  is kept as `replay/patches_full13/`.
- **Files.** The series files are `replay/patches/NN_<name>.diff`. Four are rebased copies (28, 30, 38, 42), with the
  same + and − lines as their source except one merged line in 42; row 46 is composed (old PL1 + the `full14` delta). Per-repository combined diffs are in
  `replay/repo_diffs/`.
- **`full14` decisions** (18 October): row 16 (TH8) is retired into 43, which ships TH8 + TH9 unconditionally; 46
  is PL1 under `sfc_precip_enthalpy`; new row 57 is NM10r. NM10r's standalone water diff is
  `energy/patches/water_17r/17r_NM10r_noahmp_precip_phase.diff` (also `../proposal/patches/revised/`).
- **History.** The manifest as it stood before `SERIES.md` resolved its open questions is in
  [`conservation_patches.history.md`](conservation_patches.history.md), verbatim.

**Hercules roots.**
- `$U` = `/work2/noaa/co2/ash/ufs-chem-v1/upstream`.
- `$E` = `$U/cons/energy`, the integrator. Its copies are in `$E/accepted/NN_<owner>_<name>.diff`.
- Agent roots: `$U/cons/<agent>`. The replay is `$U/cons/replay`.

**Base.**
- `$U/p20rt_final/ufs-weather-model` = `develop` @112b1d46 + water diffs 01–19 + 09b, 64-bit dycore.
- `fx` = base + FX1 SG1 CP1 (`$E/fx`). Each fix diff was cut on `fx`, on `$E/all_full` or on `$E/full10`.
- Every tree used for a bitwise gate is built with `-no-fma` (`samfinit/tools/nofma.py`; row 56). That is a build
  setting, not a proposed diff.

**Repository / sub-component** (column "Target"):

| Label | Repository | Paths |
|---|---|---|
| FV3 model | NOAA-GFDL/GFDL_atmos_cubed_sphere | `model/` |
| FV3 driver | NOAA-GFDL/GFDL_atmos_cubed_sphere | `driver/UFS/atmosphere.F90` (the UFS driver lives in the FV3 repository; the water proposal's FV1 went there) |
| ccpp-physics | ufs-community/ccpp-physics | `physics/` |
| UFSATM | ufs-community/UFSATM | `ccpp/data/GFS_typedefs.*`, `ccpp/data/CCPP_typedefs.*`, `ccpp/driver/GFS_diagnostics.F90`, `ccpp/driver/GFS_restart.F90`, `ccpp/CMakeLists.txt` (build/cmake) |
| noahmp | NOAA-EMC/noahmp | `src/` (in the tree: `NOAHMP-interface/noahmp/src/`) |
| MPAS | MPAS-Dev/MPAS-Model | — |

The series files apply with `-p1` at the `ufs-weather-model` root, except where `SERIES.md` gives another directory or
`-p2` (ensfc2's diffs). A diff that touches several targets has to be split by repository for the PRs; most switches
touch both ccpp-physics and UFSATM (scheme code plus `GFS_typedefs` plumbing).

## A. Proposed diffs, in the `full14` apply order

Classes: BF = BUG FIX, PC = PHYSICS CHANGE, NC = NUMERICAL CONSISTENCY. "Default" is the stock value; "all-on" is the
value in the final closure run (`$E/runs/final13_switches.sed`). A "—" in the switch column means unconditional.
"Local source" is the delivering agent's file; the column `$E/accepted` gives the integrator's copy, or "anchors" where
the integrator applied the change by an anchor script (the local diff reproduces it exactly at `-F0`).

### A.1 `fx`: base + FX1 SG1 CP1

| # | Fix | Local source | `$E/accepted` | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 01 | FX1 | `energy/patches/01_fv3-fv_mapz_consv_te_fixer_weight.diff` | anchors (`apply_fixes.py FX1`) | FV3 model | BF | — |
| 02 | SG1 | `energy/patches/02_fv3-fv_sg_relax_total_energy.diff` | anchors | FV3 model | BF | — |
| 03 | CP1 | `energy/patches/03_fv3-atmosphere_state_update_heating_mass.diff` | anchors | FV3 driver | BF | — |

### A.2 `all_full`: `integrate.sh` = fx + R1 + accepted patches in order

| # | Fix | Local source | `$E/accepted` | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 04 | R1 | `energy/patches/04_ccpp-dcyc2t3_radiative_heating_current_mass.diff` | anchors (`apply_fixes_r2.py R1`) | ccpp-physics (`dcyc2t3`), UFSATM (`GFS_typedefs`) | BF | — |
| 05 | FV2 | `tracer/patches/01_FV2_fv3_statein_consistent_layer_mass.diff` | 01 | FV3 driver | BF | — |
| 06 | D1 `dspheat_ke` | `enpbl/patches/04_ccpp-satmedmfvdifq_dspheat_ke.diff` | 02 | ccpp-physics (satmedmfvdifq), UFSATM | PC | `dspheat_ke` .false. / .true. |
| 07 | D3A | `encnv/patches/01_D3A.diff` | 03 (differs only in header timestamps) | ccpp-physics (SAMF) | BF | — |
| 08 | D7 | `energy/patches/05_fv3-cpl_ke_heating_option.diff` | anchors (`integrate_full.txt`: `FIX:D7`) | FV3 driver, FV3 model | NC | `cpl_ke_heating` .false. / .true. |
| 09 | D3B | `encnv/patches/02_D3B.diff` | 04 | ccpp-physics (SAMF), UFSATM | PC | `samf_cmt_heat` .false. / .true. |
| 10 | D4 + D12 | `encnv/patches/03_D4.diff` | 05 | ccpp-physics (`ugwpv1_gsldrag`, `GFS_GWD_generic_post`), UFSATM | PC | `gwd_ke_heat` .false. / .true. |
| 11 | D4n | `encnv/patches/04_D4N.diff` | 06 | ccpp-physics (`ugwpv1_gsldrag`), UFSATM | PC | `ngw_heat_opt` 0 / 2 |
| 12 | NM12 | `nm12/patches/20_NM12_noahmp_combine_melt_out.diff` | 07; harness `$U/cons/nm12` | ccpp-physics (Noah-MP lsm + glacier) | BF | — |
| 13 | C1 | `encpl/patches/04_fv3-cpl_water_energy.diff` | 08 | FV3 driver, FV3 model | PC | `cpl_water_energy` 0 / 15 (bits 1 PE, 2 flow work, 4 sensible, 8 = C8, row 20) |
| 14 | K1 | `encpl/patches/05_ccpp-thompson_kirchhoff_option.diff` | 09 | ccpp-physics (Thompson), UFSATM | PC | `thompson_kirchhoff` .false. / .true. |
| 15 | S1 + precipitation-flux export | `encpl/patches/06_precip_flux_export_c1v2_samf_kirchhoff.diff` (as cut; does not apply after 09–11) | 10r = 06 re-anchored by `energy/patches/tools/rebase_encpl06.py`; the series file is 10r | ccpp-physics (SAMF, Thompson), UFSATM, FV3 driver | PC | `samf_kirchhoff` .false. / .true.; export acts under `cpl_water_energy` bits 1, 4 |

`$E/accepted/11` does not exist.

### A.3 `full6`: `all_full` + energy round 4 + latent

Energy's round-4 diffs were cut in this order on `all_full` (energy §9.3); the integrator applied them by anchors
(`apply_fixes.py <tree> TH8 S1K TFH PBK C8 D7S PBF`).

| # | Fix | Local source | `$E/accepted` | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 16 | TH8 | **retired**: part of row 43 (number reserved) | 23 | — | — | — |
| 17 | S1K | `energy/patches/07_ccpp-samf_kirchhoff_ice_and_initial_T.diff` | anchors | ccpp-physics (SAMF) | PC | `samf_kirchhoff` (as row 15) |
| 18 | TFH | `energy/patches/08_ccpp-thompson_frame_F_heating.diff` | anchors | ccpp-physics (Thompson), UFSATM | PC | `thompson_frame_heat` .false. / .true. |
| 19 | PBK | `energy/patches/09_ccpp-satmedmfvdifq_filler_kirchhoff.diff` | anchors | ccpp-physics (satmedmfvdifq), UFSATM | PC | `pbl_kirchhoff` .false. / .true. |
| 20 | C8 | `energy/patches/10_fv3-cpl_water_energy_bit8_water_KE.diff` | anchors | FV3 driver | PC | `cpl_water_energy` bit 8 |
| 21 | D7S | `energy/patches/11_fv3-cpl_ke_smooth.diff` | anchors | FV3 driver, FV3 model | NC | `cpl_ke_smooth` 0 / 32 (needs `cpl_ke_heating`) |
| 22 | PBF | `energy/patches/12_ccpp-fv3-pbl_condensate_flux_export.diff` | anchors | ccpp-physics (satmedmfvdifq), UFSATM, FV3 driver | PC | acts under `cpl_water_energy` bit 4 with `pbl_kirchhoff` |
| 23 | F3 01a | `latent/patches/01a_F3_samf_scavenging_booking.diff` (= `trdyn/patches/01a_…`, byte-identical) | 12 | ccpp-physics (SAMF) | BF | — |
| 24 | F3 01b | `latent/patches/01b_F3_samf_wet_deposition_export_on_all_full.diff` (same + and − lines as `01b_…export.diff`, which is cut on `fx`) | 13 | ccpp-physics (SAMF), UFSATM (`GFS_typedefs`, `GFS_diagnostics`) | NC (diagnostic) | — |
| 25 | SAMF32 | `latent/patches/02_SAMF32_cmake_filter_dependencies.diff` | 14 | UFSATM (build/cmake) | BF (build) | acts only with `-DSAMFCNV_32BIT=ON` |
| 26 | TOPT | `latent/patches/03_TOPT_process_split_sum_applied_once.diff` | 15 | ccpp-physics (interstitials, `dcyc2t3`, `mynnedmf_wrapper_post`) | BF | — (option 4 of `tend_opt_pbl/gwd/rad_scaler` becomes a CCPP error) |

### A.4 `full9` → `full10`: trdyn + ensfc2 rounds 1–3

trdyn 02b → 03b → 04_INLQ → v6 applied in one pass on `full6` gives `$E/full10` exactly, with the same re-anchoring
of 03b and v6 that v5 needed (`rebase_trdyn.py`). Rows 31–36 come from `$U/cons/ensfc2/patches`, byte-identical to
`$E/accepted/19–22`.

| # | Fix | Local source | `$E/accepted` | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 27 | T1 (02b) | `trdyn/patches/02b_T1_samf_tracer_substep.diff` | 16 | ccpp-physics (SAMF) | BF | — (sub-stepping for every SAMF tracer incl. o3, TKE) |
| 28 | DRY (03b) | `trdyn/patches/03b_DRY_chem_tracers_dry_mixing_ratio_transport.diff` (changed lines identical to `trsamf/patches/03_DRY_…`) | 17; rebased in the series | ccpp-physics (SAMF, satmedmfvdifq) | PC (chemistry tracers only) | none: acts on `chemistry` tracers with `trans_aero`; inert in p8 |
| 29 | INLQ | `trdyn/patches/04_INLQ_inline_q_damping_mass_single_valued.diff` | 18c | FV3 model (`sw_core`) | BF | — (acts only with `inline_q`) |
| 30 | DYN v6: `dry_tracer_adv`, `dry_tracer_ic`, `dry_negadj` | `trdyn/patches/01_DYN_dry_tracer_adv_remap_ic_v6.diff` | 18d; rebased in the series | FV3 model (9 files), FV3 driver | PC | `dry_tracer_adv` .false. / .true.; `dry_tracer_ic` .false. / .false. |
| 31 | SI1 | `ensfc2/patches/04_sfc_SI1.diff` (= `ensfc/patches/04_…`) | ensfc2 copy | ccpp-physics (sea ice) | BF | — |
| 32 | SI2 | `ensfc2/patches/05_sfc_SI2.diff` | ensfc2 copy | ccpp-physics (sea ice) | BF | — |
| 33 | NP1 | `ensfc2/patches/06_sfc_NP1.diff` | ensfc2 copy | ccpp-physics (Noah-MP) | BF | — |
| 34 | QR1 | `ensfc2/patches/08_sfc_QR1.diff` | 19 | ccpp-physics (NSST) | BF | — |
| 35 | CMC | `ensfc2/patches/09_sfc_CMC.diff` | 20 | ccpp-physics (Noah-MP) | BF | — |
| 36 | FL1 | `ensfc2/patches/10_sfc_FL1.diff` | 21 | ccpp-physics (sea ice) | BF | — |
| 37 | surface options, round 3 | `ensfc2/patches/11_sfc_options.diff` | 22 | ccpp-physics (Noah-MP, sea ice, `GFS_MP_generic_post`, `GFS_surface_composites_post`, `rrtmg_lw_post`), UFSATM (`GFS_typedefs`, `CCPP_typedefs`) | PC / NC by item | `noahmp_canopy_heat` 0 / 1; `precip_phase_host` F / T; `noahmp_sw_radshare` F / T; `lw_sfc_consistent` F / **F** (replaced by `lw_sfc_return`); `sfc_evap_enthalpy` F / T; `noahmp_heat_advect` F / T; `noahmp_kirchhoff` F / T |

### A.5 `full11`: ensfc2 round 4 + canopy (`energy/meters/tools/mk11.sh`, `mk11b.sh`)

| # | Fix | Local source | `$E/accepted` | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 38 | SL2 | `ensfc2/patches/13_sfc_SL2.diff` (needs NM12, row 12, for context) | 24; rebased in the series (hunk 8, `rebase_r11.py 13`) | ccpp-physics (Noah-MP lsm + glacier) | BF | — |
| 39 | CS1 | `ensfc2/patches/14_sfc_CS1.diff` | 25 | ccpp-physics (Noah-MP lsm + glacier) | BF | — |
| 40 | CB1 | `ensfc2/patches/15_sfc_CB1.diff` | 26 | ccpp-physics (Noah-MP lsm + glacier) | BF | — |
| 41 | surface options, round 4 (EP1, LW2, AIR1, glacier EV1, PH1 at L_f(T1)) | **`preclag/patches/16b_sfc_options_r4_meta_fixed.diff`** = `ensfc2/patches/16_sfc_options_r4.diff` with one `+` line fixed (D.2) | 27 (= 16 as delivered) + the `mk11b.sh` sed = 16b | ccpp-physics (Noah-MP, sea ice, `GFS_MP_generic_post`, `GFS_surface_composites_post`), UFSATM | PC | `sfc_precip_enthalpy` F / T; `lw_sfc_return` F / T; `noahmp_pore_air` F / T |
| 42 | E2 | `canopy/patches/01_E2_noahmp_fwet_opt.diff` | 28; rebased in the series (7 hunks, `rebase_r11.py E2`; one merged line) | ccpp-physics (Noah-MP), UFSATM, **noahmp** (`NOAHMP-interface/noahmp/src/module_sf_noahmplsm.F90`: module default 0 + setter `noahmp_options_fwet`, no namelist plumbing) | BF, switched | `noahmp_fwet_opt` 0 / 2 |
| 43 | TH8 + TH9 | `energy/patches/13_ccpp-thompson_TH8-TH9_unconditional.diff` (cut on `fx`; replaces energy 06, canopy 02, canopy 03) | — | ccpp-physics (`module_mp_thompson.F90`) | BF | — |
| 44 | E1 | `canopy/patches/04_E1_nst_spray_implicit.diff` | 30 | ccpp-physics (`sfc_nst`, `sfc_ocean`), UFSATM | PC | `nst_spray_opt` 0 / 1 |

### A.6 `full12`: FV3 tally fix (`mk12.sh`)

| # | Fix | Local source | `$E/accepted` | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 45 | `dyn_te_exact` v2 (DY1, DY2, DY3, bits 2, 4; options 32, 64) | `fv3tally/patches/01_fv3-dyn_te_exact.diff` (= `.v2.diff`, md5 ddc59580…) | 31 | FV3 model (`dyn_core`, `sw_core`, `fv_dynamics`, `fv_mapz`, `fv_arrays`, `fv_control`) | bits 1–16 BF; 32, 64 PC (design options) | `dyn_te_exact` 0 / 31 |

### A.7 `full13`: preclag + suites (`mk13.sh`)

| # | Fix | Local source | `$E/accepted` | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 46 | PL1 | `replay/patches/46_PL1_under_EP1.diff` = `preclag/patches/01_PL1_…` + `energy/patches/full14/delta_PL1_folded_into_EP1.diff` | 41 + delta | ccpp-physics (`GFS_MP_generic_post`, Noah-MP, sea ice), UFSATM (`GFS_typedefs`, `GFS_restart`: restart field written only with EP1) | BF of the EP1 option | under `sfc_precip_enthalpy` |
| 47 | MYNN 01 | `suites/patches/01_E3_mynn_surface_flux_density_dew_and_filler_mass.diff` | 32 | ccpp-physics (MYNN-EDMF) | BF (a–c), NC (d) | — |
| 48 | MYNN 01b (v2) | `suites/patches/01b_E3_mynn_moisture_check_latent_heat_double_count.diff` | 33 | ccpp-physics (MYNN-EDMF) | BF | — |
| 49 | GFDL 02 | `suites/patches/02_E4_gfdlmp_v3_mass_basis.diff` | 34 | ccpp-physics (GFDL MP v3) | BF | — |
| 50 | GF 03 | `suites/patches/03_E5_gf_water_closure.diff` | 35; rebased in the series | ccpp-physics (GF), UFSATM | BF + NC | `gf_closure` .false. / .true. (inert in p8) |
| 51 | MYNN 04 | `suites/patches/04_E3c_mynn_surface_heat_flux_theta.diff` | 36; rebased in the series | ccpp-physics (MYNN-EDMF), UFSATM | NC | `mynn_sfc_heat` .false. / .true. (inert in p8) |
| 52 | PBL05 (suites 05) | `suites/patches/05_PBL_satmedmfvdifq_surface_flux_layer_mass.diff` | 37 | ccpp-physics (satmedmfvdifq) | NC | — |
| 53 | MYNN 06 | `suites/patches/06_E3d_mynn_static_energy_mixing.diff` | 38; rebased in the series | ccpp-physics (MYNN-EDMF), UFSATM | PC | `mynn_mix_sl` .false. / .true. (inert in p8) |
| 54 | GFDL 07 | `suites/patches/07_E4c_gfdlmp_v3_rain_sedimentation_heat_capacity.diff` | 39 | ccpp-physics (GFDL MP v3) | BF | — |
| 55 | SAMF08 (suites 08) | `suites/patches/08_SAMF_deep_ca_trigger_early_return_decomposition.diff` | 40 | ccpp-physics (SAMF deep) | BF | — |
| 57 | NM10r | `energy/patches/full14/delta_NM10r.diff` (= `ensfc2/patches/12_sfc_NM10r.diff` on the series) | — | ccpp-physics (`noahmpdrv`, Noah-MP), UFSATM | PC, unconditional | — (`precip_phase_host` now governs glaciers only) |
| 56 | `-no-fma` | `samfinit/tools/nofma.py` (script) | — | ufs-weather-model (`cmake/IntelMixed.cmake`) | **build setting, not proposed** | — |

`$E/accepted/32–40` are `32_suites_01_E3_…` … `40_suites_08_SAMF_…`, byte-identical to `suites/patches/`.

**The bug-fix arm** of the default-off gate (energy §9.5, §9.6, §9.8): `fx` + 04 R1, 16 TH8, 05 FV2, 07 D3A, 12 NM12,
23 01a, 25 SAMF32, 26 TOPT, 27 02b, 29 INLQ, 31–36 (SI1 SI2 NP1 QR1 CMC FL1), 38–40 (SL2 CS1 CB1), 47 48 49 52 54 55
(suites 01 01b 02 05 07 08). In `full14` the arm has 43 (TH8 + TH9) in place of 16, and 57 (NM10r); rows 38 and 57 go
in as originally cut. `full14` with every switch off is bitwise equal to it (`-no-fma`; `gB14`).

### A.8 MPAS-A (separate repository)

| # | Patches | Local source | Hercules | Target | Class | Switch: default |
|---|---|---|---|---|---|---|
| 56 | 0001–0004 Thompson water, 0005–0007 scalar transport, 0008–0009 TH8/TH9 | `../proposal/patches/ports/MPAS-conservation/0001-…` to `0009-…` | `$U/mpas/e24` (generators `mk_ebud5.py`, `mk_edis.py`) | MPAS (`git am` on `develop` aa6d8cd69) | BF | — |
| 57 | 0012 layer coupling (option B) | `…/0012-Layer-local-microphysics-energy-coupling-option-defa.patch` | as 56 | MPAS | PC | `config_mp_energy_coupling` `'stock'` |
| 58 | 0013 global energy fixer | `…/0013-Global-energy-fixer-option-default-off.patch` | as 56 | MPAS | FIXER (labelled) | `config_energy_fixer` off |
| 59 | 0014 dissipative heating | `…/0014-Dissipative-heating-return-the-KE-removed-by-explici.patch` | as 56 | MPAS | PC | `config_dissipative_heating` 0 (2 recommended) |

MPAS rows 56–59 are manifest rows, a separate `git am` series; they are not `SERIES.md` rows (its row 56 is
`56_NOFMA`). 0010 (sedimentation export) and 0011 (meter) are instrumentation (part C) but sit inside the MPAS
series, because 0012–0014 apply on top of them.

## B. Diffs that are not in `full14`

| Local path | Status |
|---|---|
| `ensfc2/patches/12_sfc_NM10r.diff` | in `full14` as row 57 (bug-fix arm: applied as cut). Standalone water diff 17r: `energy/patches/water_17r/` |
| `nm12/patches/20b_NM12-EMC_noahmp-emc_combine_melt_out.diff` | NOAA-EMC/noahmp companion of NM12 (`src/` lsm + glacier). Applies cleanly; **not built** in any UFS tree |
| `ensfc2/patches/16_sfc_options_r4.diff` | superseded by `preclag/patches/16b_…` (the meta `standard_name` fix); 16 as delivered fails capgen |
| `latent/patches/01b_F3_samf_wet_deposition_export.diff` | the same `+/-` lines as the `_on_all_full` version, cut on `fx`; use it when the series is split onto `ufs/dev` without D3A/encpl 06 |
| `fv3tally/patches/01_fv3-dyn_te_exact.v1.diff` | superseded by v2 |
| `trdyn/patches/01_DYN_dry_tracer_adv_remap_ic.diff` (v1), `…_v5.diff` | superseded by v6 (v5 = v6 except `sw_core.F90`) |
| `trdyn/patches/01a_F3_samf_scavenging_booking.diff` | byte-identical to `latent/patches/01a_…` (row 23) |
| `trsamf/patches/01_SA1_samf_cloud_base_double_count.diff` | byte-identical to water diff 01 (`../proposal/patches/01_SA1_…`), already in the base |
| `trsamf/patches/02_T1_samf_tracer_substep_donor_source.diff` | superseded by 02b (donor-layer start dropped by trred) |
| `trsamf/patches/03_DRY_chem_tracers_dry_mixing_ratio_transport.diff` | superseded by 03b (context only) |
| `canopy/patches/02_TH8_thompson_count_all_sedimented_precip.diff` | byte-identical to row 16 |
| `ensfc/patches/04_sfc_SI1.diff`, `05_sfc_SI2.diff`, `06_sfc_NP1.diff`, `07_round2_switchable.diff` | byte-identical to the ensfc2 copies; 07 (the env-switched round-2 build) is superseded by ensfc2 11 |
| `ensfc2/patches/07_round2_switchable.diff` | superseded by 11 |
| `encnv/patches/round1/D3A.diff`, `D3B.diff`, `D4.diff` | round-1 unconditional per-layer forms, superseded |
| `suites/patches/not_proposed/E4b_gfdlmp_v3_host_constant_pressure.diff` | tested, not proposed (`gfdl_mp_host_cp`; reduces the GFDL gap only 0.117 → 0.085 W/m²) |
| `../proposal/patches/held/TH8_…`, `TH9_…` | the water proposal's held versions; rows 16 and 43 replace them |
| `../proposal/patches/candidates/issue4_noahmp_fwet_mass_weighted.diff` | defective (local `cwat` shadows the specific heat of water); superseded by row 42 |

## C. Instrumentation and test hooks (not proposed)

Separate diffs, never part of a fix. Each was gated as passive: metered vs plain tree bitwise, with `-no-fma` where
the edit touches a physics file. `full14` carries no meter or test-hook code: 0 of 385 meter-only identifiers, no new
`getenv` (`SERIES.md`, Meters).

| Local path | What it is | Applies on |
|---|---|---|
| `energy/meters/meter_fv3_dycore_coupling.diff` | dycore/coupling energy meter (`EBD`, `EBX`), generator `energy/meters/tools/instrument_eb_dyn.py` | `fx` (`mfx`) |
| `energy/meters/meter_ccpp_physics.diff` | physics energy meter em_p01..12 (`EMS`, `EMF`); v2 with frame-F terms is generated by `instrument_eb_phys2.py` (`EB_PBLFLX`, `EB_PH1`, `EB_LAG`) and is not stored as a diff | `fx`; regenerated per tree |
| `encpl/patches/meter_r2.diff`, `meter_cpl_thompson.diff` | frame-F coupling meter (`EBQ`), Thompson coupling meter | `mall_*` (`mallq`) |
| `enpbl/meters/meter_pbl_tke.diff` | PBL TKE/KE budget | `mfx` + enpbl 04 |
| `encnv/meters/meter_gw_split.diff`, `meter_heat_profile.diff`, `meter_heat_profile_round1.diff` | GWD split (`EMG`), per-level heating (`EMZ`; edits samf*.f, so not bitwise passive in release builds) | `mfx` |
| `ensfc/meters/meter_surface.diff` (= `ensfc2/meters/meter_surface.diff`), `ensfc2/meters/meter_round3.diff`, `meter_round4.diff` | surface-component meters | `fx` / ensfc2 trees |
| `fv3tally/meters/meter_fv3tally.diff`, `meter_fv3tally_on_fix.diff`, `fv_etally.F90`, `instrument_tally.py` | FV3 per-term tally (`ETL`, `ETS`, env `FV3_ETALLY=1`); the two diffs do not stack | full10, full10 + row 45 |
| `preclag/patches/meter_PL1_lag_v2.diff` | precipitation hand-off lag meter (`EML`, 8 columns) | `mq12` + PL1 |
| `latent/meters/01_F3_meter_samf_wetdep.diff`, `02_F3_testhook_nortnp.diff` | wet-deposition meter; test hook (env `F3_NORTNP=1` skips the column borrowing) | tracer meters + trsamf TX print |
| `tracer/meters/01_testhook_chem_pbl_UFSATM-ccpp.diff`, `02_meters_ccpp-physics.diff`, `03_meters_fv3.diff`, `04_testhook_samf_substep_ccpp-physics.diff` | tracer-mass meters (Neumaier hi/lo), dry-ratio, Courant and uniform-reset hooks; the chem-PBL hook gives chemistry tracers the cplchm treatment without a chemistry component | base |
| `trunif/meters/05_shadow_tags_meter.diff` | shadow tracers and per-generator tags | tracer meters |
| `trdyn/meters/testhook_uniform_reset_env.py` | uniform reset at the first dynamics call (env `TRDYN_NORESET` skips it) | trdyn trees |
| `trsamf/scripts/meter_*.py`, `hook_*.py`, `tm_meter.F90` | SA1 defect meter, path-equivalence and reset hooks | trsamf trees |
| `canopy/patches/instrumentation/meter_spray_gain.diff`, `test_only_th8_env_switch.diff` | spray gain λ meter (`SPR`); env `CANOPY_TH8_OFF` for the TH8 tests | full10 |
| `suites/meters/01_suites_meter.diff`, `02_suites_meter_on_fixes.diff`, `instrument_sm.py` | suite water/energy/tracer meter (`SMX`, `SMH`) | full10; full10 + rows 47–55 |
| `samfinit/tools/nofma.py` | build setting: appends `-no-fma` to the AVX2 branch of `cmake/IntelMixed.cmake` (row 56) | any tree |
| MPAS 0010, 0011 | sedimentation export; energy meter with reproducing sums (`config_energy_meter`) | MPAS series |

## D. Re-anchoring needed when the series is split or reordered

These hunks fail `patch -F0` on the integrated tree because a neighbouring patch changed their context. The series
files already carry the re-anchored versions (`SERIES.md`, Rebased diffs). A split into PRs against `ufs/dev` will
meet the same conflicts in whatever order the PRs merge. The scripts re-apply the `.rej` content verbatim and change
only the anchors.

| Clash | Where | Tool |
|---|---|---|
| encpl 06 (row 15) after encnv 02–04 | SAMF argument lists, `.meta` tails, the code just before `ten_t` | `energy/patches/tools/rebase_encpl06.py` → `$E/accepted/10r_…` |
| trdyn 03b and 01_DYN v6 after energy round 4 (rows 16–22) | PBK/PBF declarations in satmedmfvdifq; the D7/D7S namelist line in `fv_control`; in metered trees the `fv_dynamics` use line and the `Lagrangian_to_Eulerian` call next to the meter | `energy/patches/tools/rebase_trdyn.py` (written for v5; v6 shares those hunks) |
| ensfc2 13 hunk 8 (row 38) | cut on `fx`; its `hc1` declaration sits next to ensfc2 11's `svn, hcpo, hcpn` | `energy/patches/tools/rebase_r11.py 13` |
| **canopy E2 (row 42) vs ensfc2 16 (row 41)** | both cut on `full10`: 7 E2 hunks sit next to 16's new lines (namelist, `Model%` copy, print, `noahmpdrv` argument list, options call, `.meta` tail, `module_sf_noahmplsm` option declarations) | `rebase_r11.py E2` |
| canopy TH9 hunks 1–2 (row 43) | metered tree only (Thompson energy-meter lines) | `rebase_r11.py TH9` |
| `dyn_te_exact` `fv_dynamics` hunks 1–2 (row 45) | metered tree only (dycore meter probe after `Rayleigh_Super`) | `rebase_r11.py DTE <diff>` |
| suites 03, 04, 06 switch hunks (rows 50, 51, 53) | `GFS_typedefs.F90` namelist line and `Model%` copy next to TH9's line | `full13` only (`rebase_r11.py REJ`); in `full14` TH9 has no switch lines and the rows apply verbatim |
| latent 01b (row 24) | its signature and end-of-routine hunks conflict with D3A's `hfus` argument and encpl 06 | use `01b_…_on_all_full.diff` (or `latent/scripts/fix_f3.py`, anchors) |
| TH9 (row 43) on `fx` | the `full13` diff was cut on K1/TFH Thompson text | resolved in `full14`: row 43 is cut on `fx` |

Every stage of `rebase_r11.py` runs right after its own patch, because `patch` overwrites `.rej` files. The script
aborts on anything other than an exact replacement or an insertion after a unique context line, and exits 1 if any
`.rej` is left.

## D.2 Known defects in delivered diffs, and their fixes

| Diff | Defect | Fix |
|---|---|---|
| `ensfc2/patches/16_sfc_options_r4.diff` | `GFS_MP_generic_post.meta` declares `[tgrs]` with `standard_name = air_temperature`, which is `gt0`'s name in that table: capgen aborts on the duplicate | `physics_timestep_initial_air_temperature` (Statein%tgrs, the step-start T1 PH1 wants): `preclag/patches/16b_…` (one `+` line). Energy's `full11`–`full13` carry the same change via `mk11b.sh` |
| `../proposal/patches/candidates/issue4_…` | local `cwat` shadows Noah-MP's specific heat of water | replaced by row 42 |

## E. Sizes

Added/removed lines in the local diffs, for sizing PRs: largest are ensfc2 11 (+816/−40), 01_DYN v6 (+716/−19), 02b
(+424), ensfc2 16/16b (+383/−35), dyn_te_exact v2 (+230/−6), encpl 06 (+185/−10); smallest NM12 (+2/−2), GFDL 02
(+2/−1), SI2 (+1/−1). Per repository, base → `full14` (`replay/repo_diffs/`): GFDL_atmos_cubed_sphere 10 files
+1199/−36, ccpp-physics 41 files +2948/−209, UFSATM 7 files +424/−3, noahmp 1 file +28/−0. Nothing touches
ccpp/framework, and `full14` adds no new files.

The uncertainties this manifest used to list (inferred `$E/accepted` numbers, whether D7 went in by diff or anchors,
the suites file names, the unreplayed 02b → v6 order, the `dyn_te_exact` file flag) are all resolved by `SERIES.md`;
the original text is in the history file.
