*History of `conservation_patches.md`: the manifest as it stood before the cleanup of 18 October 2026, verbatim. Its open questions (sections A.2, A.4, E) were resolved by `conservation/replay/SERIES.md`; the head is `conservation_patches.md`.*

# Conservation follow-on: patch manifest

*Companion to `conservation_proposal.md`. Draft, 18 October 2026. Nothing has been posted. Lists every diff of the
final tree `full13` in the order it was applied, then the diffs that are not in it, then the instrumentation, then
what has to be re-anchored when the series is replayed. Local paths are relative to
`/Users/pera/Documents/ash-code/ufs-chem-v1/conservation/`.*

**Verified series (supersedes the uncertainties below).** `conservation/replay/SERIES.md` and
`replay/apply_series.sh` give the canonical order of the 55 proposed diffs (+ `56_NOFMA`, build setting, not
proposed). Applied at `patch -F0` to the base (develop @112b1d46 + water diffs 01–19 + 09b), they reproduce `full13`
with an empty `diff -r`, and the rebuilt executable's 24-h run is byte-identical to full13's (136 files). Seven rows
are rebased copies (28, 30, 38, 42, 50, 51, 53); per-repository combined diffs are in `replay/repo_diffs/`. Where
this manifest's Hercules numbers or order differ from `SERIES.md`, `SERIES.md` is right (`replay/report.md`).

**Hercules roots.**
- `$U` = `/work2/noaa/co2/ash/ufs-chem-v1/upstream`.
- `$E` = `$U/cons/energy`, the integrator. Its copies are in `$E/accepted/NN_<owner>_<name>.diff`.
- Agent roots: `$U/cons/<agent>`.

**Base.**
- `$U/p20rt_final/ufs-weather-model` = `develop` @112b1d46 + water diffs 01–19 + 09b, 64-bit dycore.
- `fx` = base + FX1 SG1 CP1 (`$E/fx`). Every fix diff was cut on `fx`, on `$E/all_full`, or on `$E/full10`, as
  noted per row.
- Release builds of every tree used for a bitwise gate add `-no-fma` (`samfinit/tools/nofma.py`,
  `$U/cons/ensfc2/tools/nofma.py`). That is a build setting, not a proposed diff.

**Repository / sub-component** (column "Target"):

| Label | Repository | Paths |
|---|---|---|
| FV3 model | NOAA-GFDL/GFDL_atmos_cubed_sphere | `model/` |
| FV3 driver | NOAA-GFDL/GFDL_atmos_cubed_sphere | `driver/UFS/atmosphere.F90` (the UFS driver lives in the FV3 repository; the water proposal's FV1 went there) |
| ccpp-physics | ufs-community/ccpp-physics | `physics/` |
| UFSATM | ufs-community/UFSATM | `ccpp/data/GFS_typedefs.*`, `ccpp/data/CCPP_typedefs.*`, `ccpp/driver/GFS_diagnostics.F90`, `ccpp/driver/GFS_restart.F90`, `ccpp/CMakeLists.txt` (build/cmake) |
| noahmp | NOAA-EMC/noahmp | `src/` (in the tree: `NOAHMP-interface/noahmp/src/`) |
| MPAS | MPAS-Dev/MPAS-Model | — |

Most diffs are cut against `ufs-weather-model` with paths `b/UFSATM/...`. They apply with `patch -p1` at the
`ufs-weather-model` root; ensfc2's apply with `-p2` (paths `fx/ufs-weather-model/...`). FV2, NM12 and trdyn 02b/03b
have repository-relative paths; the integrator finds the base directory and `-p` level by a `-F0` dry run
(`energy/meters/tools/integrate.sh`). A diff that touches several targets has to be split by repository for the PRs.

## A. Proposed diffs, in the `full13` apply order

Classes: BF = BUG FIX, PC = PHYSICS CHANGE, NC = NUMERICAL CONSISTENCY. "Default" is the stock value; "all-on" is the
value in the final closure run (`$E/runs/final13_switches.sed`). A "—" in the switch column means unconditional.

### A.1 `fx`: base + FX1 SG1 CP1

| # | Fix | Local path | Hercules | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 1 | FX1 | `energy/patches/01_fv3-fv_mapz_consv_te_fixer_weight.diff` | in `$E/fx`; built by anchors (`apply_fixes.py FX1`); a separate Hercules diff file is not recorded locally | FV3 model | BF | — |
| 2 | SG1 | `energy/patches/02_fv3-fv_sg_relax_total_energy.diff` | as 1 | FV3 model | BF | — |
| 3 | CP1 | `energy/patches/03_fv3-atmosphere_state_update_heating_mass.diff` | as 1 | FV3 driver | BF | — |

### A.2 `all_full`: `integrate.sh` = fx + R1 + accepted patches in order

Order from energy §8 ("FV2, enpbl 04, D3A, D7, encnv 02–04, NM12, encpl 04, 05, 10r"). The `$E/accepted` numbers
01, 03 and 07 are confirmed by `energy/meters/tools/mkgate10.sh`. **Numbers 02, 04–06 and 08–11 are not recorded in
any local file**: they are inferred from that order and marked "?".

| # | Fix | Local path | Hercules | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 4 | R1 | `energy/patches/04_ccpp-dcyc2t3_radiative_heating_current_mass.diff` | applied first by `apply_fixes_r2.py R1` (anchors) | ccpp-physics (`dcyc2t3`), UFSATM (`GFS_typedefs`) | BF | — |
| 5 | FV2 | `tracer/patches/01_FV2_fv3_statein_consistent_layer_mass.diff` | `$E/accepted/01_FV2_fv3_statein_consistent_layer_mass.diff` | FV3 driver | BF | — |
| 6 | D1 `dspheat_ke` | `enpbl/patches/04_ccpp-satmedmfvdifq_dspheat_ke.diff` | `$E/accepted/02_…`? | ccpp-physics (satmedmfvdifq), UFSATM | PC | `dspheat_ke` .false. / .true. |
| 7 | D3A | `encnv/patches/01_D3A.diff` | `$E/accepted/03_encnv_D3A.diff` | ccpp-physics (SAMF) | BF | — |
| 8 | D7 | `energy/patches/05_fv3-cpl_ke_heating_option.diff` | uncertain: `$E/accepted/04_…`? or anchors (`apply_fixes_r3.py D7`) | FV3 driver, FV3 model | NC | `cpl_ke_heating` .false. / .true. |
| 9 | D3B | `encnv/patches/02_D3B.diff` | `$E/accepted/04–06_…`? | ccpp-physics (SAMF), UFSATM | PC | `samf_cmt_heat` .false. / .true. |
| 10 | D4 + D12 | `encnv/patches/03_D4.diff` | as 9 | ccpp-physics (`ugwpv1_gsldrag`, `GFS_GWD_generic_post`), UFSATM | PC | `gwd_ke_heat` .false. / .true. |
| 11 | D4n | `encnv/patches/04_D4N.diff` | as 9 | ccpp-physics (`ugwpv1_gsldrag`), UFSATM | PC | `ngw_heat_opt` 0 / 2 |
| 12 | NM12 | `nm12/patches/20_NM12_noahmp_combine_melt_out.diff` | `$E/accepted/07_NM12_noahmp_combine_melt_out.diff`; harness `$U/cons/nm12` | ccpp-physics (Noah-MP lsm + glacier) | BF | — |
| 13 | C1 | `encpl/patches/04_fv3-cpl_water_energy.diff` | `$E/accepted/08_…`? | FV3 driver, FV3 model | PC | `cpl_water_energy` 0 / 15 (bits 1 PE, 2 flow work, 4 sensible, 8 = C8, row 20) |
| 14 | K1 | `encpl/patches/05_ccpp-thompson_kirchhoff_option.diff` | `$E/accepted/09_…`? | ccpp-physics (Thompson), UFSATM | PC | `thompson_kirchhoff` .false. / .true. |
| 15 | S1 + precipitation-flux export | `encpl/patches/06_precip_flux_export_c1v2_samf_kirchhoff.diff` (as cut; does not apply after 9–11) | `$E/accepted/10r_…` = 06 re-anchored by `energy/patches/tools/rebase_encpl06.py` | ccpp-physics (SAMF, Thompson), UFSATM, FV3 driver | PC | `samf_kirchhoff` .false. / .true.; export acts under `cpl_water_energy` bits 1, 4 |

### A.3 `full6`: `all_full` + energy round 4 + latent

Energy 06–12 were applied by anchors (`apply_fixes.py <tree> TH8 S1K TFH PBK C8 D7S PBF`). The diffs in
`energy/patches/` were cut in that order on `all_full` (energy §9.3).

| # | Fix | Local path | Hercules | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 16 | TH8 | `energy/patches/06_ccpp-thompson_count_all_sedimented_precip.diff` (= `canopy/patches/02_TH8_…`, byte-identical) | `$E/accepted/23_energy_06_TH8_thompson_count_all_sedimented_precip.diff` (copy made for the gates) | ccpp-physics (Thompson) | BF, **only with TH9 (row 43) or E2 (row 42)** | — |
| 17 | S1K | `energy/patches/07_ccpp-samf_kirchhoff_ice_and_initial_T.diff` | anchors | ccpp-physics (SAMF) | PC | `samf_kirchhoff` (as 15) |
| 18 | TFH | `energy/patches/08_ccpp-thompson_frame_F_heating.diff` | anchors | ccpp-physics (Thompson), UFSATM | PC | `thompson_frame_heat` .false. / .true. |
| 19 | PBK | `energy/patches/09_ccpp-satmedmfvdifq_filler_kirchhoff.diff` | anchors | ccpp-physics (satmedmfvdifq), UFSATM | PC | `pbl_kirchhoff` .false. / .true. |
| 20 | C8 | `energy/patches/10_fv3-cpl_water_energy_bit8_water_KE.diff` | anchors | FV3 driver | PC | `cpl_water_energy` bit 8 |
| 21 | D7S | `energy/patches/11_fv3-cpl_ke_smooth.diff` | anchors | FV3 driver, FV3 model | NC | `cpl_ke_smooth` 0 / 32 (needs `cpl_ke_heating`) |
| 22 | PBF | `energy/patches/12_ccpp-fv3-pbl_condensate_flux_export.diff` | anchors | ccpp-physics (satmedmfvdifq), UFSATM, FV3 driver | PC | acts under `cpl_water_energy` bit 4 with `pbl_kirchhoff` |
| 23 | F3 01a | `latent/patches/01a_F3_samf_scavenging_booking.diff` (= `trdyn/patches/01a_…`, byte-identical) | `$E/accepted/12_latent_01a_F3_samf_scavenging_booking.diff` | ccpp-physics (SAMF) | BF | — |
| 24 | F3 01b | `latent/patches/01b_F3_samf_wet_deposition_export_on_all_full.diff` (on `all_full` + 01a; the original `01b_…export.diff` applies on `fx`) | `$E/accepted/13_…`? (inferred); also `$U/cons/latent/bin/` | ccpp-physics (SAMF), UFSATM (`GFS_typedefs`, `GFS_diagnostics`) | NC (diagnostic) | — |
| 25 | SAMF32 | `latent/patches/02_SAMF32_cmake_filter_dependencies.diff` | `$E/accepted/14_latent_02_SAMF32_cmake_filter_dependencies.diff` | UFSATM (build/cmake) | BF (build) | acts only with `-DSAMFCNV_32BIT=ON` |
| 26 | TOPT | `latent/patches/03_TOPT_process_split_sum_applied_once.diff` | `$E/accepted/15_latent_03_TOPT_process_split_sum_applied_once.diff` | ccpp-physics (interstitials, `dcyc2t3`, `mynnedmf_wrapper_post`) | BF | option 4 of `tend_opt_pbl/gwd/rad_scaler` becomes a CCPP error (decision) |

### A.4 `full9` → `full10`: trdyn + ensfc2 rounds 1–3

`full9` applied trdyn 02b, 03b and 01_DYN **v5** (`$E/accepted/18b_…`) with `rebase_trdyn.py`, then ensfc2 04–11.
`full10` replaced `sw_core.F90` only, with `fx`-6 + 04_INLQ + v6 (`energy/meters/tools/mk10.sh`). v6 differs from v5
only in `sw_core.F90`; mk10.sh checks that the other hunks are byte-identical. **A straight replay of 02b, 03b, 04,
v6 on `full6` was not run as such.** trdyn verified that order (`base + 01a + 02b + 03b + 04 + v6`, all `-F0`) on the
tracer base and on `fx`, not on `full6`, where `rebase_trdyn.py` (written for v5) is needed.

| # | Fix | Local path | Hercules | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 27 | T1 (02b) | `trdyn/patches/02b_T1_samf_tracer_substep.diff` | `$E/accepted/16_trdyn_02b_T1_samf_tracer_substep.diff` | ccpp-physics (SAMF) | BF | — (sub-stepping for every SAMF tracer incl. o3, TKE; Ash decided 17 Oct) |
| 28 | DRY (03b) | `trdyn/patches/03b_DRY_chem_tracers_dry_mixing_ratio_transport.diff` (changed lines identical to `trsamf/patches/03_DRY_…`) | `$E/accepted/17_trdyn_03b_DRY_chem_tracers_dry_mixing_ratio_transport.diff` | ccpp-physics (SAMF, satmedmfvdifq) | PC (chemistry tracers only) | none: acts on `chemistry` tracers with `trans_aero`; inert in p8 |
| 29 | 04_INLQ | `trdyn/patches/04_INLQ_inline_q_damping_mass_single_valued.diff` | `$E/accepted/18c_trdyn_04_INLQ_inline_q_damping_mass_single_valued.diff`; source `$U/cons/trdyn/patches/` | FV3 model (`sw_core`) | BF | — (acts only with `inline_q`) |
| 30 | `dry_tracer_adv`, `dry_tracer_ic`, `dry_negadj` (01_DYN v6) | `trdyn/patches/01_DYN_dry_tracer_adv_remap_ic_v6.diff` | `$E/accepted/18d_trdyn_01_DYN_dry_tracer_adv_remap_ic_v6.diff`; source `$U/cons/trdyn/patches/` | FV3 model (9 files), FV3 driver | PC | `dry_tracer_adv` .false. / .true.; `dry_tracer_ic` .false. / .false. |
| 31 | SI1 | `ensfc2/patches/04_sfc_SI1.diff` (= `ensfc/patches/04_…`) | `$U/cons/ensfc2/patches/04_sfc_SI1.diff` | ccpp-physics (sea ice) | BF | — |
| 32 | SI2 | `ensfc2/patches/05_sfc_SI2.diff` | `$U/cons/ensfc2/patches/` | ccpp-physics (sea ice) | BF | — |
| 33 | NP1 | `ensfc2/patches/06_sfc_NP1.diff` | `$U/cons/ensfc2/patches/` | ccpp-physics (Noah-MP) | BF | — |
| 34 | QR1 | `ensfc2/patches/08_sfc_QR1.diff` | `$U/cons/ensfc2/patches/` | ccpp-physics (NSST) | BF | — |
| 35 | CMC | `ensfc2/patches/09_sfc_CMC.diff` | `$U/cons/ensfc2/patches/` | ccpp-physics (Noah-MP) | BF | — |
| 36 | FL1 | `ensfc2/patches/10_sfc_FL1.diff` | `$U/cons/ensfc2/patches/` | ccpp-physics (sea ice) | BF | — |
| 37 | surface options, round 3 | `ensfc2/patches/11_sfc_options.diff` | `$U/cons/ensfc2/patches/` | ccpp-physics (Noah-MP, sea ice, `GFS_MP_generic_post`, `GFS_surface_composites_post`, `rrtmg_lw_post`), UFSATM (`GFS_typedefs`, `CCPP_typedefs`) | PC / NC by item | `noahmp_canopy_heat` 0 / 1; `precip_phase_host` F / T; `noahmp_sw_radshare` F / T; `lw_sfc_consistent` F / **F** (replaced by `lw_sfc_return`); `sfc_evap_enthalpy` F / T; `noahmp_heat_advect` F / T; `noahmp_kirchhoff` F / T |

### A.5 `full11`: ensfc2 round 4 + canopy (`energy/meters/tools/mk11.sh`, `mk11b.sh`)

| # | Fix | Local path | Hercules | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 38 | SL2 | `ensfc2/patches/13_sfc_SL2.diff` (needs NM12, row 12, for context) | `$E/accepted/24_ensfc2_13_sfc_SL2.diff`; hunk 8 re-anchored by `rebase_r11.py 13` | ccpp-physics (Noah-MP lsm + glacier) | BF | — |
| 39 | CS1 | `ensfc2/patches/14_sfc_CS1.diff` | `$E/accepted/25_ensfc2_14_sfc_CS1.diff` | ccpp-physics (Noah-MP lsm + glacier) | BF | — |
| 40 | CB1 | `ensfc2/patches/15_sfc_CB1.diff` | `$E/accepted/26_ensfc2_15_sfc_CB1.diff` | ccpp-physics (Noah-MP lsm + glacier) | BF | — |
| 41 | surface options, round 4 (EP1, LW2, AIR1, glacier EV1, PH1 at L_f(T1)) | **`preclag/patches/16b_sfc_options_r4_meta_fixed.diff`**, which is `ensfc2/patches/16_sfc_options_r4.diff` with one `+` line fixed (see D.2) | `$E/accepted/27_ensfc2_16_sfc_options_r4.diff` (= 16 as delivered) + the `mk11b.sh` sed = 16b | ccpp-physics (Noah-MP, sea ice, `GFS_MP_generic_post`, `GFS_surface_composites_post`), UFSATM | PC | `sfc_precip_enthalpy` F / T; `lw_sfc_return` F / T; `noahmp_pore_air` F / T |
| 42 | E2 | `canopy/patches/01_E2_noahmp_fwet_opt.diff` | `$E/accepted/28_canopy_01_E2_noahmp_fwet_opt.diff` (7 hunks re-anchored by `rebase_r11.py E2`); source `$U/cons/canopy/patches/` | ccpp-physics (Noah-MP), UFSATM, **noahmp** (`NOAHMP-interface/noahmp/src/module_sf_noahmplsm.F90`: module default 0 + setter `noahmp_options_fwet`, no namelist plumbing) | BF, switched (decision) | `noahmp_fwet_opt` 0 / 2 |
| 43 | TH9 | `canopy/patches/03_TH9_thompson_sed_actual.diff` (cut on the K1/TFH Thompson text: does not apply to `fx`; the gate arm used `canopy/tools/apply_th9.py`) | `$E/accepted/29_canopy_03_TH9_thompson_sed_actual.diff`; hunks 1–2 re-anchored in the metered tree only (`rebase_r11.py TH9`) | ccpp-physics (Thompson), UFSATM | BF | `thompson_sed_actual` .false. / .true. (decision: unconditional) |
| 44 | E1 | `canopy/patches/04_E1_nst_spray_implicit.diff` | `$E/accepted/30_canopy_04_E1_nst_spray_implicit.diff` | ccpp-physics (`sfc_nst`, `sfc_ocean`), UFSATM | PC | `nst_spray_opt` 0 / 1 |

### A.6 `full12`: FV3 tally fix (`mk12.sh`)

| # | Fix | Local path | Hercules | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 45 | `dyn_te_exact` v2 (tally D1, D2, D3, bits 2, 4; options 32, 64) | `fv3tally/patches/01_fv3-dyn_te_exact.diff` (= `.v2.diff`, md5 ddc59580…; `.v1.diff` superseded) | `$E/accepted/31_fv3tally_01_fv3-dyn_te_exact_v2.diff` from `$U/cons/fv3tally/patches/01_fv3-dyn_te_exact.v2.diff`; fv_dynamics hunks 1–2 re-anchored in the metered tree only (`rebase_r11.py DTE`) | FV3 model (`dyn_core`, `sw_core`, `fv_dynamics`, `fv_mapz`, `fv_arrays`, `fv_control`) | bits 1–16 BF; 32, 64 PC (design options) | `dyn_te_exact` 0 / 31 |

### A.7 `full13`: preclag + suites (`mk13.sh`)

Applied in this order: 41, then 32–40. `$U/cons/suites/patches` does not exist on Hercules. The suites diffs come
from the agent's `suites/fixes/*_v6–v8`, byte-identical to `suites/patches/` locally (energy §9.8).

| # | Fix | Local path | Hercules | Target | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|
| 46 | PL1 | `preclag/patches/01_PL1_sfc_precip_t1_carry.diff` | `$E/accepted/41_preclag_01_PL1_sfc_precip_t1_carry.diff` | ccpp-physics (`GFS_MP_generic_post`, Noah-MP, sea ice), UFSATM (`GFS_typedefs`, `GFS_restart`: restart field `sfc_precip_t1`) | BF of the EP1 option | `sfc_precip_t1_carry` .false. / .true. (acts only with `sfc_precip_enthalpy`) |
| 47 | MYNN 01 | `suites/patches/01_E3_mynn_surface_flux_density_dew_and_filler_mass.diff` | `$E/accepted/32_…` | ccpp-physics (MYNN-EDMF) | BF (a–c), NC (d) | — |
| 48 | MYNN 01b (v2) | `suites/patches/01b_E3_mynn_moisture_check_latent_heat_double_count.diff` | `$E/accepted/33_…` | ccpp-physics (MYNN-EDMF) | BF | — |
| 49 | GFDL 02 | `suites/patches/02_E4_gfdlmp_v3_mass_basis.diff` | `$E/accepted/34_…` | ccpp-physics (GFDL MP v3) | BF | — |
| 50 | GF 03 | `suites/patches/03_E5_gf_water_closure.diff` | `$E/accepted/35_…` (switch hunks re-anchored: `rebase_r11.py REJ`) | ccpp-physics (GF), UFSATM | BF + NC | `gf_closure` .false. / .true. (inert in p8) |
| 51 | MYNN 04 | `suites/patches/04_E3c_mynn_surface_heat_flux_theta.diff` | `$E/accepted/36_…` (REJ) | ccpp-physics (MYNN-EDMF), UFSATM | NC | `mynn_sfc_heat` .false. / .true. (inert in p8) |
| 52 | suites 05 | `suites/patches/05_PBL_satmedmfvdifq_surface_flux_layer_mass.diff` | `$E/accepted/37_…` | ccpp-physics (satmedmfvdifq) | NC | — |
| 53 | MYNN 06 | `suites/patches/06_E3d_mynn_static_energy_mixing.diff` | `$E/accepted/38_…` (REJ) | ccpp-physics (MYNN-EDMF), UFSATM | PC | `mynn_mix_sl` .false. / .true. (inert in p8) |
| 54 | GFDL 07 | `suites/patches/07_E4c_gfdlmp_v3_rain_sedimentation_heat_capacity.diff` | `$E/accepted/39_…` | ccpp-physics (GFDL MP v3) | BF | — |
| 55 | suites 08 | `suites/patches/08_SAMF_deep_ca_trigger_early_return_decomposition.diff` | `$E/accepted/40_…` | ccpp-physics (SAMF deep) | BF | — |

The `$E/accepted/32–40` file names after the number are not recorded locally. `mk13.sh` finds them as
`$A/<n>_*.diff`. The mapping 32 → 01 … 40 → 08 follows from its REJ stages (35, 36, 38 = 03, 04, 06) and the bug-fix
arm `gB13` = 32 33 34 37 39 40 = 01 01b 02 05 07 08.

**The bug-fix arm** of the default-off gate (energy §9.5, §9.6, §9.8): `fx` + 4 R1, 16 TH8, 5 FV2, 7 D3A, 12 NM12,
23 01a, 25 SAMF32, 26 TOPT, 27 02b, 29 04_INLQ, 31–36 (SI1 SI2 NP1 QR1 CMC FL1), 38–40 (SL2 CS1 CB1), 47 48 49 52 54 55
(suites 01 01b 02 05 07 08). TH9 is switch-gated and not in that arm. `full13` with every switch off is bitwise equal
to it (`-no-fma`).

### A.8 MPAS-A (separate repository)

| # | Patches | Local path | Hercules | Target | Class | Switch: default |
|---|---|---|---|---|---|---|
| 56 | 0001–0004 Thompson water, 0005–0007 scalar transport, 0008–0009 TH8/TH9 | `../proposal/patches/ports/MPAS-conservation/0001-…` to `0009-…` | `$U/mpas/e24` (generators `mk_ebud5.py`, `mk_edis.py`) | MPAS (`git am` on `develop` aa6d8cd69) | BF | — |
| 57 | 0012 layer coupling (option B) | `…/0012-Layer-local-microphysics-energy-coupling-option-defa.patch` | as 56 | MPAS | PC | `config_mp_energy_coupling` `'stock'` |
| 58 | 0013 global energy fixer | `…/0013-Global-energy-fixer-option-default-off.patch` | as 56 | MPAS | FIXER (labelled) | `config_energy_fixer` off |
| 59 | 0014 dissipative heating | `…/0014-Dissipative-heating-return-the-KE-removed-by-explici.patch` | as 56 | MPAS | PC | `config_dissipative_heating` 0 (2 recommended) |

0010 (sedimentation export) and 0011 (meter) are instrumentation (part C) but sit inside the MPAS `git am` series,
because 0012–0014 apply on top of them.

## B. Diffs that are not in `full13`

| Local path | Status |
|---|---|
| `ensfc2/patches/12_sfc_NM10r.diff` | built, not integrated: Noah-MP takes the host's convective-phase decision unconditionally. Pending Ash (proposal §15, decision 6); revising water diff 17 needs re-verification |
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
| `../proposal/patches/held/TH8_…`, `TH9_…` | the water proposal's held versions; rows 16 and 43 replace them (TH9 now behind `thompson_sed_actual`) |
| `../proposal/patches/candidates/issue4_noahmp_fwet_mass_weighted.diff` | defective (local `cwat` shadows the specific heat of water); superseded by row 42 |

## C. Instrumentation and test hooks (not proposed)

Separate diffs, never part of a fix. Each was gated as passive: metered vs plain tree bitwise, with `-no-fma` where
the edit touches a physics file.

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
| `samfinit/tools/nofma.py` | build setting: appends `-no-fma` to the AVX2 branch of `cmake/IntelMixed.cmake` | any tree |
| MPAS 0010, 0011 | sedimentation export; energy meter with reproducing sums (`config_energy_meter`) | MPAS series |

## D. Re-anchoring needed when the series is replayed

These hunks fail `patch -F0` on the integrated tree because a neighbouring patch changed their context. The scripts
re-apply the `.rej` content verbatim and change only the anchors. A split into PRs against `ufs/dev` will meet the
same conflicts in whatever order the PRs merge.

| Clash | Where | Tool |
|---|---|---|
| encpl 06 (row 15) after encnv 02–04 | SAMF argument lists, `.meta` tails, the code just before `ten_t` | `energy/patches/tools/rebase_encpl06.py` → `$E/accepted/10r_…` |
| trdyn 03b and 01_DYN v5 after energy round 4 (rows 16–22) | PBK/PBF declarations in satmedmfvdifq; the D7/D7S namelist line in `fv_control`; in metered trees the `fv_dynamics` use line and the `Lagrangian_to_Eulerian` call next to the meter | `energy/patches/tools/rebase_trdyn.py` (written for v5; v6 shares those hunks) |
| ensfc2 13 hunk 8 (row 38) | cut on `fx`; its `hc1` declaration sits next to ensfc2 11's `svn, hcpo, hcpn` | `energy/patches/tools/rebase_r11.py 13` |
| **canopy E2 (row 42) vs ensfc2 16 (row 41)** | both cut on `full10`: 7 E2 hunks sit next to 16's new lines (namelist, `Model%` copy, print, `noahmpdrv` argument list, options call, `.meta` tail, `module_sf_noahmplsm` option declarations) | `rebase_r11.py E2` |
| canopy TH9 hunks 1–2 (row 43) | metered tree only (Thompson energy-meter lines) | `rebase_r11.py TH9` |
| `dyn_te_exact` `fv_dynamics` hunks 1–2 (row 45) | metered tree only (dycore meter probe after `Rayleigh_Super`) | `rebase_r11.py DTE <diff>` |
| suites 03, 04, 06 switch hunks (rows 50, 51, 53) | `GFS_typedefs.F90` namelist line and `Model%` copy next to TH9's line | `rebase_r11.py REJ ccpp/data/GFS_typedefs.F90` |
| latent 01b (row 24) | its signature and end-of-routine hunks conflict with D3A's `hfus` argument and encpl 06 | use `01b_…_on_all_full.diff` (or `latent/scripts/fix_f3.py`, anchors) |
| TH9 (row 43) on `fx` | cut on K1/TFH Thompson text; does not apply to `fx` | `canopy/tools/apply_th9.py` (anchors). A version cut on `fx` is needed if TH9 becomes unconditional |

Every stage of `rebase_r11.py` runs right after its own patch, because `patch` overwrites `.rej` files. The script
aborts on anything other than an exact replacement or an insertion after a unique context line, and exits 1 if any
`.rej` is left.

## D.2 Known defects in delivered diffs, and their fixes

| Diff | Defect | Fix |
|---|---|---|
| `ensfc2/patches/16_sfc_options_r4.diff` | `GFS_MP_generic_post.meta` declares `[tgrs]` with `standard_name = air_temperature`, which is `gt0`'s name in that table: capgen aborts on the duplicate | `physics_timestep_initial_air_temperature` (Statein%tgrs, the step-start T1 PH1 wants): `preclag/patches/16b_…` (one `+` line). Energy's `full11`–`full13` carry the same change via `mk11b.sh` |
| `../proposal/patches/candidates/issue4_…` | local `cwat` shadows Noah-MP's specific heat of water | replaced by row 42 |

## E. Uncertainties in this manifest

- **`$E/accepted` numbers 02, 04–06, 08–11 and 13** are inferred from the documented `all_full` order and the
  latent block 12–15. They are not in any local file. 19–22 do not appear anywhere locally. Energy's round-4 diffs
  (rows 16–22) and R1/FX1/SG1/CP1 were applied by anchor scripts (`apply_fixes_r2/r3/r4.py`) rather than from
  `accepted/`, except the TH8 copy (23).
- **Whether D7 (row 8) was applied as a diff or by anchors** in `all_full` is not recorded; both forms exist.
- **The exact `$E/accepted/32–40` file names** are not recorded locally (the numbering is; section A.7).
- **The replay order 02b → 03b → 04 → v6 on `full6`** was not run as one sequence (section A.4).
- **The energy §9.7 flag** that `01_fv3-dyn_te_exact.diff` on Hercules differed from `.v2.diff` at integration time no
  longer holds for the local copies (identical). Energy used `.v2`.
- **Hercules paths of the energy, enpbl, encnv, encpl and preclag patch directories** are not recorded locally
  beyond `$E/accepted/`; agent roots are `$U/cons/<agent>`.
- **Line counts** (added/removed, from the local diffs, for sizing PRs): largest are ensfc2 11 (+816/−40), 01_DYN v6
  (+716/−19), 02b (+424), ensfc2 16/16b (+383/−35), dyn_te_exact v2 (+230/−6), encpl 06 (+185/−10); smallest NM12
  (+2/−2), GFDL 02 (+2/−1), SI2 (+1/−1).
