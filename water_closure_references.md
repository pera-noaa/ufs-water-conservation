# Water closure: literature, upstream status, maintainers (checked 2026-10-13)

Upstream heads checked: ufs-community/ccpp-physics `ufs/dev` @242a2fc (2026-10-01), NCAR/ccpp-physics `main` @f601ce9
(2026-10-06), NOAA-GFDL/GFDL_atmos_cubed_sphere `dev/emc` @71ff473 and `main` @8b94b9f, NCAR/TEMPO `main` @c62699f.
Defects are lettered as in `proposal/water_closure_proposal.md` (A SAMF, B Thompson basis, C Thompson internals, D
Noah-MP hand-off); "dry mass" is the missing dry-mass transport option. **None of A–D is fixed upstream, and no issue
or PR reports them.**

## Literature

"Opened" means the full text was read; otherwise only the abstract.

| Source | What it says | Relevance | Read |
|---|---|---|---|
| Han, Yang, Montuoro, Li, Sun 2022, NCEP Office Note 506, doi:10.25923/5051-3r70 | Introduces SAMF TVD mass flux plus a column-conserving negative-tracer borrowing step (Eqs. 10–11). Blames remaining negatives on "imbalances in the divergence of parcel fluxes"; notes zeroing "increases the total mass of the tracer". Never discusses kb/jmin. | A's source; treats the symptom, not the kb/jmin mismatch | opened |
| Han et al. 2017, Wea. Forecasting 32, 10.1175/WAF-D-17-0046.1 | Scale/aerosol-aware SAMF; TVD is not here (it came in 2022) | background | abstract |
| Bengtsson et al. 2022, MWR 150, 10.1175/MWR-D-22-0114.1 | Prognostic updraft area fraction | current SAMF closure | abstract |
| Thompson et al. 2008, MWR 136, 10.1175/2008MWR2387.1 | Scheme description; no mention of conservation | B and C undocumented | opened |
| Thompson & Eidhammer 2014, JAS 71, 10.1175/JAS-D-13-0305.1 | Aerosol-aware version; no mass-conservation discussion | same | opened |
| Harris et al. 2021, NOAA Tech Memo OAR GFDL 2021-001, §9.1, repository.library.noaa.gov/view/noaa/30725 | FV3 delp is total mass. "The dry mass in each grid cell should be unchanged by the physical parameterizations." Eq. 9.5 is the exact update. §10: GFS physics uses moist (dry + vapour) mass. | reference algorithm for B and dry mass | opened |
| Zhou, Harris, Chen 2022, GFDL Tech Memo 2022-02, §2.4, repository.library.noaa.gov/view/noaa/44636 | GFDL MP converts FV3 total mass → dry mass using all water species and back (Eqs. 2.18–2.21); "air mass is exactly conserved in the GFDL MP" | working in-UFS example of the basis Thompson lacks (B) | opened |
| Lin 2004, MWR 132, 10.1175/1520-0493(2004)132<2293:AVLFDC>2.0.CO;2 | Lagrangian FV core; tracer transport with time-accumulated mass fluxes keeps tracer mass consistent with air mass | dry-mass background | opened |
| Harris et al. 2020, JAMES 12, 10.1029/2020MS002223 | SHiELD with in-line GFDL MP | dry-mass context | abstract |
| Zhou et al. 2019, BAMS, 10.1175/BAMS-D-17-0246.1 | GFDL MP in variable-resolution FV3 | context | abstract |
| Lauritzen et al. 2018, JAMES 10, 10.1029/2017MS001257 | CAM-SE moved to a dry-mass coordinate partly for consistent physics coupling; clipping in coupling causes energy and hydrological-cycle biases | strongest precedent for a dry-mass option (C, dry mass) | opened |
| Zhang et al. 2018, GMD 11, 10.5194/gmd-11-1971-2018 | E3SM water conservation: largest error from physics–dynamics coupling; second, surface moisture flux re-derived from latent heat with a constant factor "ignoring the distinction from sublimation"; clipping fixed with mass fixers | same bug class as D; covers C; best single citation | opened |
| Lauritzen & Williamson 2019, JAMES 11, 10.1029/2018MS001549 | Energy-error budget of CAM incl. physics–dynamics coupling | framing | abstract |
| Lauritzen et al. 2022, JAMES 14, 10.1029/2022MS003117 | Unified thermodynamics; add missing precipitation/evaporation terms | framing | abstract |
| Takacs, Suárez, Todling 2016, QJRMS 142, 10.1002/qj.2763 (read as NASA TM-2014-104606 Vol. 37) | GEOS-5: change layer mass by net water produced, rescale all constituents to keep dry mass, plus a dry-mass constraint in the analysis | operational precedent (B, dry mass) | TM opened |
| Diamantakis & Flemming 2014, GMD 7, 10.5194/gmd-7-965-2014 | Global mass fixers for IFS humidity and cloud; no loss of 10-day skill | interim remedy | opened |
| Becker et al. 2022, ECMWF Newsletter 172 | IFS spurious water source 4.6 % of precipitation at 9 km, 10.7 % at 4 km; clipping negatives "effectively adds condensate mass"; fixers reduce it to ~0.1 % | C analogue with numbers | opened |
| Niu et al. 2011, JGR 116, 10.1029/2010JD015139 | Noah-MP description | D | abstract |
| He et al. 2023, GMD 16, 10.5194/gmd-16-5131-2023 | Noah-MP v5 refactor; host coupling; no latent-heat consistency with hosts | D undocumented | opened |

No published UFS/GFS total-water budget closure study was found. The closest item is the open request for CMEPS budgets,
ufs-community/ufs-weather-model#2349.

## Upstream status

| Defect | Status | Evidence |
|---|---|---|
| A. SAMF kb/jmin double count | present | `ufs/dev` `samfdeepcnv.f` L1622 (`qcko(kb)=qo(kb)`), L2551–2561 (`eta*tem1`, `edto*etad*tem1`), tracers L2635–2645; NCAR `main` identical; shallow identical. Origin NCAR/ccpp-physics#754 (2021); untouched by #812, ufs#232, ufs#384 |
| B. Thompson q↔r basis | present | `ufs/dev` `mp_thompson.F90` L690–704 (÷(1−q_v)), L944–957 (÷(1+r_v)); since ufs#299 (2026-04) the scheme returns tendencies, same arithmetic. FV3 `dev/emc` `driver/UFS/atmosphere.F90` L1659–1677 unchanged. TEMPO `mp_tempo.F90` L437–454 same conversion |
| C. Thompson internals | present | C1: cloud sedimentation out of `kts` (L4044–4057) not counted. C2: `prg_rci` set L3029 before the limiters (L3140–3176), never recomputed; `prg_rcs` same. C3: `rho` recomputed after latent heating at L3386, 3660, 3743, before sedimentation. Clips L4241–4300. TEMPO `check_over_depletion` has the C2 gap |
| D. Noah-MP latent heat | present, tracked | `ufs/dev` `noahmpdrv.F90` L1526 `evap/density/con_hvap`; `module_sf_noahmplsm.F90` L188–189 `hsub=2.8440e06`, `hvap=2.5104e06`. NCAR/ccpp-physics#582 (open since 2021-03): use host constants |
| Dry-mass tracer transport | absent | only `adjust_dry_mass` (init) and `adj_mass_vmr` (in `fv_update_phys`, unreachable from UFS, which passes no `q_dt`) |
| Diagnostic: SAMF condensate `cnvtrans` | broken on `develop` | `GFS_suite_interstitial_4` builds `dtend_*_cnvtrans` from per-scheme dcnv/scnv condensate tendencies that only GF and C3 convection fill; with SAMF it is zero (measured on `develop` @112b1d46) |

## Other lineages (survey 2026-10-13)

Read-only survey of the same code in other hosts. SHAs: ufs-community/ccpp-physics `ufs/dev` c7dc705 (2026-10-13;
identical to the UFSATM pin 242a2fc for every file below); NCAR/ccpp-physics `main` f601ce9; NCAR/TEMPO `main` c62699f
(ccpp-physics pins `tempo_v3` at 2856696); wrf-model/WRF `develop` 1086c86 (2026-06-08); MPAS-Dev/MPAS-Model `develop`
aa6d8cd (2026-10-13); NCAR/noahmp `master` 1a6225b; NOAA-EMC/noahmp `develop` 2c7b3bc (the ufs-weather-model
`NOAHMP-interface` pin); GFDL_atmos_cubed_sphere `dev/emc` 71ff473 and `main` 8b94b9f.

| Defect | UFS `ufs/dev` = NCAR `main` | TEMPO | WRF | MPAS |
|---|---|---|---|---|
| A | present, identical (since NCAR/ccpp-physics#754, commit ed3768b, 2021) | n/a | n/a | n/a |
| B | present (`mp_thompson.F90` 690–704 in, 944–958 out) | present (`mp_tempo.F90` 437–455, 532–549) | cannot occur: dry mixing ratios passed (`module_microphysics_driver.F` 1177ff) | cannot occur (`mpas_atmphys_interface.F` 660–662) |
| C1 | present (4044–4056) | partial: `cloud_precip` accumulated but feeds only the freezing-rain diagnostic | present (3824–3836) | present (3443–3455) |
| C2 | present (3189–3199; `prg_rci` only at 3029) | present (`check_over_depletion` 1649–1673) | present (2940–2950) | present (2656–2666) |
| C3 | present (rho recomputed 3386, 3660, 3743) | present (512, 605, 633, 828) | present (3193, 3490, 3572) | present (2846, 3127, 3209) |
| ρ·dz vs host mass | `dz` from `phii` (before convection) | same driver pattern | geometric `dz8w`; host dry ρ not passed | fixed `zgrid`; host dry ρ not passed |
| D | present (`noahmpdrv.F90` 1526) | — | absent: QFX = canopy + ground evaporation + transpiration (NCAR/noahmp WRF driver) | absent (NCAR/noahmp MPAS driver) |

- **D is a CCPP-port defect.** Every NCAR/noahmp driver (WRF, HRLDAS, MPAS, LIS, ERF;
  `drivers/*/WaterVarOutTransferMod.F90` L59–64) passes the water mass flux. The LH/`con_hvap` form is in the
  ccpp-physics copy (compiled by UFS for the in-atmosphere land model: ufsatm `ccpp_prebuild_config_fv3.py` L210), in
  NOAA-EMC/noahmp's CCPP driver (L1568) and in its NUOPC land component (`lnd_comp_driver.F90` L716). NOAA-EMC/noahmp's
  CCPP driver also still sets glacier canopy evaporation and transpiration to `undefined` (L1228–1229), so diff 04
  there needs them zeroed, as on the v1 snapshot. NCAR/ccpp-physics#582 is open with no fix PR.
- **FV3 coupling.** `dev/emc` `driver/UFS` and `main` `driver/SHiELD` pass the dry + vapour basis and rebuild delp as
  old dry mass + Σ(physics dp × returned q). SHiELD's in-line GFDL MP converts on a dry basis using all condensate
  (`gfdl_mp.F90` 1320–1335, 1591) and holds dry mass exactly. `main` has no UFS driver. Run-time fixers reachable from
  UFS: only the IAU dry-mass fixer, inside the IAU window.
- **SAMF elsewhere.** GFDL `main` in-line `sa_sas.F90`/`sa_aamf.F90` have no TVD and no cloud-base subtraction
  (defect A as such is absent; not checked for exact conservation). `hwrf_samfdeep` does not bypass the moisture TVD.
- **The `cnvtrans` gap** is identical on both ccpp-physics branches: `GFS_DCNV_generic_post` and
  `GFS_SCNV_generic_post` skip condensates under `satmedmf`, and SAMF never writes `dtend`.
- **MPAS only:** condensate above `config_microphysics_top` (default 45 km) is zeroed each step while vapour is left
  alone (`mpas_atmphys_interface.F` 936–946, 999–1003; added 2025-10-17).
- Not checked: ccpp-scm, HAFS forks, MPAS `physics_mmm`, the C3 convection submodule.

## Related issues and PRs

- NCAR/ccpp-physics#753 / #754 (2021): introduced SAMF TVD and the "subtract the double counting" code.
- NCAR/ccpp-physics#811 / #812 (2022): density-weighted the negative fixer; kb/jmin untouched.
- NCAR/ccpp-physics#954 (2022): NRL negative-qv fixes in SAS overshoot.
- ufs-community/ccpp-physics#232 (2025): SAMF TKE and number transport; #384 (2026-10): single-precision refactor.
- NCAR/ccpp-physics#567 (2021): Thompson `convert_dry_rho`; ufs-community/ccpp-physics#299 (2026-04): schemes return tendencies.
- NCAR/ccpp-physics#582 (open): Noah-MP should use host constants.
- NOAA-GFDL/GFDL_atmos_cubed_sphere#228 / #232: VMR mass adjustment (GFDL path only); #230 (open): decentred tendency coupling; #125 / #126 and ufs-community/ufs-weather-model#730: tracer mass during `na_init`.
- **NOAA-EMC/global-workflow#2576** (Jian He, closed 2025-09): passive CO2 loses 2 % in 35 days in continuous runs; attributed to restart regridding, closed as superseded.
- ufs-community/ufs-weather-model#2349 (open): CMEPS heat and water budgets.

## Maintainers

- **ccpp-physics** (same CODEOWNERS in `ufs/dev` and NCAR `main`): global @grantfirl @rhaesung @Qingfu-Liu
  @dustinswales @mzhangw @climbfuji; SAMF @JongilHan66 @lisa-bengtsson; Thompson @gthompsnWRF @RuiyuSun
  @AndersJensen-NOAA; Noah-MP @barlage @cenlinhe. Recent `ufs/dev` merges: grantfirl, rhaesung.
- **NCAR/TEMPO**: @AndersJensen-NOAA, @dustinswales. **NCAR/noahmp**: cenlinhe.
- **GFDL_atmos_cubed_sphere**: merges @vithikashah001, @laurenchilutti; science lharris4, linjiongzhou,
  JosephMouallem; the `dev/emc` UFS driver is maintained by EMC/DTC staff (DusanJovic-NOAA, DeniseWorthen, dustinswales).
- **ufsatm**: @noaa-emc/fv3atm-team. **ufs-weather-model**: @ufs-community/ufs-wm-gatekeepers.
