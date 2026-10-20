# Water-closure patches and where they go

Checked 15 October 2026. Nothing has been posted.

## What is here

| Path | Contents |
|---|---|
| `01`–`18_*.diff` | Plain diffs against ufs-community/ccpp-physics `ufs/dev` @242a2fc (the commit `develop` pins), named by number and fix label (SA SAMF, TH Thompson, NM Noah-MP and its coupling); apply in order |
| `held/` | TH8 and the Thompson placeholder fix that goes with it, TH9 (applies after TH8): held, see the proposal's section 7 |
| `revised/` | `17r_NM10r_noahmp_precip_phase.diff`: NM10 revised so Noah-MP takes the host's convective phase (`srflag`); replaces 17, cut on `develop` + 01–16, 18 applies after it. Proposed in the energy follow-on (`conservation_proposal.md` section 6); this proposal's regression results were measured with 17 |
| `candidates/` | tested fixes offered in the issues, not proposed: `issue4_*` (Noah-MP canopy wetted fraction, mass-weighted; DEFECTIVE, local `cwat` shadows the module's specific heat of water; superseded by `conservation/canopy/patches/01_E2_noahmp_fwet_opt.diff`) and `issue7_*` (Grell–Freitas shallow precipitation from the applied tendencies); both change the forecast beyond noise |
| `09b_*.diff` | NM2's companion in NOAA-EMC/noahmp (`develop` @2c7b3bc, the NOAHMP-interface pin): its copy of the CCPP driver declares the same optional `iter`, so the land component's call matches; paths relative to that repository |
| `19_*.diff` | FV1, against NOAA-GFDL/GFDL_atmos_cubed_sphere `dev/emc` @71ff473 (the UFSATM pin, and `dev/emc` HEAD); paths relative to that repository |
| `git/ufs-dev/<series>/` | `git format-patch` series against `ufs/dev` HEAD c7dc705, one commit per fix with defect, fix and measured effect |
| `git/ncar-main/<series>/` | the same series against NCAR/ccpp-physics `main` f601ce9 (for DTC's later port; see below) |
| `git/fv3-dev-emc/prsl-physics-constants/` | fix FV1 as a `git format-patch` series against GFDL_atmos_cubed_sphere `dev/emc` 71ff473 |
| `ports/` | ports of the fixes to other repositories (TEMPO, WRF, MPAS, NOAA-EMC/noahmp, the production branches), maintained by a second session; see `ports/README.md` |

Series: `samf-cloud-base` (SA1), `thompson` (TH1–TH7), `noahmp-driver` (NM1, NM2), `frac-grid-snow` (NM3, NM4),
`noahmp-thin-snow` (NM5), `noahmp-canopy-water` (NM6, NM7), `noahmp-latent-heats` (NM8, NM11), `noahmp-glacier` (NM9),
`noahmp-precip-phase` (NM10), `all` (18 commits);
and, in the FV3 repository, `prsl-physics-constants` (FV1).

Verification:
- Every series applies with `git am` on its base.
- `ufs-dev/all` before NM11 gave files byte-identical to the final tree built on Hercules, `develop` + 01–17 and 19 (`patched19`;
  the 12 changed physics files compared by checksum). Its C96 budget closes to 0.00000 kg/m² per 6 h at 24 h, at
  `dt_inner` = 720 s and 150 s, every day of ten days, and at C384.
- Regression against `develop-20260921` (final tree before NM11, 288 tasks, Intel and GNU): 54/54 compiles, 17 pass and 180 change only baselines; 8 did not complete (6 /work2 input/output errors; 2 land-component tests that need 09b and complete with it); the 29 restart and decomposition tests could not start, because their parents change baselines.
- Reproducibility (final tree, 01–19 with 09b, Hercules, Intel and GNU): baselines made with `rt.sh -c` from the tree itself, then `rt.sh -m` against them: **234/234 pass bit for bit**, including 34 restart/warmstart, 17 decomposition, 14 threading and 1 MPI test, 57 debug and 29 coupled or land tests. 12 runs that hit /work2 I/O or Slurm-controller errors passed on retry. No crash, NaN, floating-point trap, `FATAL` or `PT UPDATE` message in any run directory (the earlier diff set had 12 crashes and 9 temperature-range violations). `cpld_debug_sfs_gnu`, which fails on `develop` (MOM6/FMS diagnostic overflow), passes.
- On NCAR `main`, everything applies unchanged except SA1. NCAR `main` lacks the single-precision SAMF rewrite
  (ufs-community/ccpp-physics#384), so SA1 is a hand port there. It is logically identical; it compiles with no
  warnings in every CCPP SCM build (57 suites) and runs in its GFS v17 cases.
- CCPP SCM (NCAR `main` series) and UFSATM capgen (`ufs/dev` series): 0 errors, validator and capgen pass, NM2's
  `iter` passed by keyword in every generated call. Not compiled there: `GFS_phys_time_vary.fv3.F90` (NM4; the SCM
  builds the `.scm` variant), which the UFS builds compile. TH5 leaves `phii` an unused argument of `mp_thompson_run`.

## Where each fix goes

> Submission order, bundling and the re-cut on current heads are now in `../pr_round1.md`; the routes and
> reviewers below still hold for the water fixes.

UFS rule (CCPP Tech Docs, Code Management): physics PRs go to the application fork, ufs-community/ccpp-physics
`ufs/dev`. DTC later re-submits each merged PR to NCAR/ccpp-physics `main` and handles ccpp-scm, so we do not open the
NCAR PR ourselves.

Every change here alters answers. The chain for each is three issues and three PRs, merged together through the
weather model's commit queue:

1. **ccpp-physics PR** to `ufs/dev`, using the series in `git/ufs-dev/`. CI runs `basic_checks` and capgen builds for
   UFSATM and SCM, so `.meta` edits (TH5, NM2, NM4) must pass capgen.
2. **NOAA-EMC/ufsatm PR** to `develop`, bumping the `ccpp/physics` pointer.
3. **ufs-community/ufs-weather-model PR** to `develop`, bumping the UFSATM pointer:
   - Commit `RegressionTests_<machine>.log` and `test_changes.list` from a full `rt.sh -e -a <acct>` run (Intel and
     GNU, without `-c`).
   - The PR template's commit-message tree, the "New Baselines" label, and the **GenAI disclosure**: AI-assisted code
     must be reviewed, edited and validated by NWS staff.
   - A WM issue is mandatory.
   - For NM2: a NOAA-EMC/noahmp PR with 09b, and the NOAHMP-interface pointer bump in the same WM PR.

| Fix | Where | Reviewers (CODEOWNERS) | Notes |
|---|---|---|---|
| SA1 | ccpp-physics `ufs/dev`: `CONV/SAMF/samfdeepcnv.f`, `samfshalcnv.f` | @JongilHan66 @lisa-bengtsson + default four | Open PRs touching SAMF: ufs#390, ufs#381; NCAR#1239/#1235 on `main`. Related: NCAR#811/#812 (tracer TVD) |
| TH1 | ccpp-physics `ufs/dev`: `MP/Thompson/mp_thompson.F90` | @gthompsnWRF @RuiyuSun @AndersJensen-NOAA + four | **Same defect in TEMPO's CCPP driver** `MP/TEMPO/mp_tempo.F90` (in: `/(1-spechum)`, L139; out: `/(1+qv)`, L233). That hunk belongs in the same ccpp-physics PR; written in `ports/TEMPO-driver/`. Open PR ufs#389 edits these files |
| TH2–TH4, TH6, TH7 | ccpp-physics `ufs/dev`: `MP/Thompson/module_mp_thompson.F90` | Thompson owners + four | TH8 and its placeholder fix are held (`held/`; proposal section 7): with them a trace of snow reaches Noah-MP, where canopy ice hides the canopy's water (issue 4). TH7's sedimentation part is in `semi_lagrange_sedim` (`sedi_semi`), a UFS addition; its entry and leftover-rain parts were not surveyed in the other copies. Scheme-internal, so also wanted in TEMPO (NCAR/TEMPO `main`, then a ccpp-physics submodule bump), WRF (`wrf-model/WRF` `release-v4.8.1` as a bug fix, `phys/module_mp_thompson.F`) and MPAS (`MPAS-Dev/MPAS-Model` `develop`, `physics_wrf/module_mp_thompson.F`). Those copies have diverged; ports in `ports/`. TEMPO also sediments cloud water in one step (`substeps_sedi = 1`), so diff 03's substepping applies there; diff 03's snow-gain cap is only needed with its own TH3 closure |
| TH5 | ccpp-physics `ufs/dev`: `mp_thompson.F90` + `.meta` | Thompson owners + four | `air_pressure_at_interface` already exists in UFSATM and SCM `GFS_typedefs.meta`; no host change |
| NM1 | ccpp-physics `ufs/dev`: `SFC_Models/Land/Noahmp/noahmpdrv.F90` | @barlage @cenlinhe + four | NOAA-EMC/noahmp `develop` (NUOPC land component) keeps a stale copy of the driver and converts `evap` with `rho*con_hvap` in `drivers/nuopc/lnd_comp_driver.F90`; follow-on series in `ports/noahmp-emc_develop_D_H_I_K_L/` |
| NM2 | ccpp-physics `ufs/dev`: `noahmpdrv.F90` + `.meta`; **with 09b in NOAA-EMC/noahmp** | Noah-MP owners + four | `iter` is an optional trailing argument. In atmosphere–land builds NOAA-EMC/noahmp's land component calls `noahmpdrv_run` against its own copy of the driver (a stale `update.sh` sync), and the linker resolves the call to ccpp-physics' routine; without 09b that call leaves `iter` undefined (SIGSEGV in `control_p8_atmlnd`). So NM2 needs a NOAA-EMC/noahmp PR and a NOAHMP-interface pointer bump in the same WM PR. Possibly related: ufs-weather-model#2656 (Noah-MP crash with frac_grid) |
| NM3 | ccpp-physics `ufs/dev`: `Interstitials/UFS_SCM_NEPTUNE/GFS_surface_composites_pre.F90` | default four only | Related only in name: NCAR#969 (metadata descriptors) |
| NM4 | ccpp-physics `ufs/dev`: `Interstitials/UFS_SCM_NEPTUNE/GFS_phys_time_vary.fv3.F90` + `.meta` | default four only | `.meta` edit, so capgen must pass; same series as NM3 |
| NM5 | ccpp-physics `ufs/dev`: `SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90` | @barlage @cenlinhe + four | The same file is byte-identical on NCAR `main`. NOAA-EMC/noahmp `develop` has the same three sites (`src/module_sf_noahmplsm.F90` L945, L2047, L8162): follow-on PR there. NCAR/noahmp v5 (`master`, used by WRF and MPAS) deletes at 10⁻⁶ mm (`SnowWaterMainMod.F90` L176, `SnowpackHydrologyMod.F90` L96): issue drafted in `ports/ncar_noahmp_issue_draft.md`. The glacier module's copies of these sites are in NM9 |
| NM6 | ccpp-physics `ufs/dev`: `SFC_Models/Land/Noahmp/module_sf_noahmplsm.F90` (`canwater`) | @barlage @cenlinhe + four | Byte-identical on NCAR `main`. Same two lines in NOAA-EMC/noahmp `develop` (`src/module_sf_noahmplsm.F90` L7328, L7337) and, unchanged, in NCAR/noahmp v5 (`CanopyHydrologyMod.F90` L92, L101): follow-on PR and issue. The truncated water goes to the ground with the rain and snowfall, so no phase change and no dependence on NM1 |
| NM7 | ccpp-physics `ufs/dev`: `module_sf_noahmplsm.F90` (`canwater`) | @barlage @cenlinhe + four | Energy–water consistency, not a water leak: negative transpiration heat now condenses as canopy dew or frost; the energy solve is unchanged. Same clip in NOAA-EMC/noahmp (in its follow-on series) and in NCAR/noahmp v5 (`CanopyHydrologyMod.F90` L75, L81). CTSM instead suppresses transpiration under dew inside its energy solve |
| NM8 | ccpp-physics `ufs/dev`: `module_sf_noahmplsm.F90`, `module_sf_noahmp_glacier.F90`, `noahmpdrv.F90` | @barlage @cenlinhe + four | Energy, not water: Noah-MP's latent heats from the host (`con_hvap`, `con_hfus`), set at the start of `noahmpdrv_run` from the arguments it already receives (no interface change: NOAA-EMC/noahmp's land component calls the driver positionally); #582's approach for these three constants. NOAA-EMC/noahmp has the same constants; its follow-on series includes NM8 (`ports/noahmp-emc_develop_D_H_I_K_L/`) |
| NM9 | ccpp-physics `ufs/dev`: `module_sf_noahmp_glacier.F90`, `noahmpdrv.F90` | @barlage @cenlinhe + four | Books the glacier's 600 mm reset, the driver's 0.1 mm floor and two thin-snow truncations as runoff. The ice terms go into `drain`, which the host reads as liquid; marked `FIXME`, since closing the energy needs a frozen-runoff flux. Files byte-identical on NCAR `main`. Trees without the reset (RRFS v1, SRW v3, AQM v7, NOAA-EMC/noahmp) need only the floor and truncation parts; ports in `ports/` |
| NM10 | ccpp-physics `ufs/dev`: `module_sf_noahmplsm.F90` (`atm`) | @barlage @cenlinhe + four | Precipitation phase with `opt_snf = 4`: convective snow below freezing, as the host's `srflag`. NCAR/noahmp v5 and NOAA-EMC/noahmp have the same rule. The canopy wetted-fraction switch found alongside is an issue only (issue 4 of the drafts), because its fix moves the land forecast well beyond noise |
| NM11 | ccpp-physics `ufs/dev`: `module_sf_noahmplsm.F90` (`energy`, `water`) | @barlage @cenlinhe + four | The ground's vapour charged at `hsub` whenever there is snow; any remaining mismatch between the latent heat charged and the phase moved returned to the top soil layer as heat. Same series as NM8. Changes the land over snow beyond noise (snow cover +0.16 %, ground heat flux +0.15 W/m²) |
| FV1 | **NOAA-GFDL/GFDL_atmos_cubed_sphere `dev/emc`**: `driver/UFS/atmosphere.F90` | `dev/emc` maintainers (the repository has no CODEOWNERS) | A different chain: FV3 PR to `dev/emc`, then a NOAA-EMC/ufsatm PR bumping `fv3/atmos_cubed_sphere`, then the WM PR; it can share the ufsatm/WM step with the ccpp-physics bump. Needs `use physcons` in the driver, which already uses `GFS_typedefs`. Only matters in 32-bit builds (`rdgas` single precision) |

Default four owners: @grantfirl @rhaesung @Qingfu-Liu @dustinswales.

**Two copies of the Noah-MP driver.** NOAA-EMC/noahmp (NOAHMP-interface) compiles its own copies of `noahmpdrv`,
`module_sf_noahmplsm` and `module_sf_noahmp_glacier`, synced from ccpp-physics by its `drivers/ccpp/update.sh` (on
`develop` about 300 lines behind each). In atmosphere–land builds both sets share module names. The land component is
compiled against its own copy's `.mod` interfaces, but runs the ccpp-physics routines: `libfv3ccpp.a` comes first on
the link line, so `libnoahmp.a`'s duplicates are never extracted, and no duplicate-symbol error is raised (checked
with `nm` and `addr2line` on the `control_p8_atmlnd` executables). So any change to `noahmpdrv`'s argument lists breaks those
builds unless NOAA-EMC/noahmp's copy changes with it: inserted arguments shift the rest, optional ones are only absent
if the caller's interface declares them, and CCPP passes optional arguments by pointer (so the host's `physcons`
parameters cannot be optional targets). NM8 therefore changes no interface, and NM2's optional `iter` comes with 09b.

**Bundling** (superseded by `../pr_round1.md`).
- One ccpp-physics PR (with the per-fix commits) means one UFSATM/WM chain and one baseline change.
- Separate PRs per series give each set of owners its own review, but each needs its own chain.
- Recent PRs (#383, #384, #387) each ran a full chain.
- A middle course: open the nine ccpp-physics series as separate PRs for review, and merge them through one
  UFSATM/WM chain.

**Before submitting:** nothing left on the regression side. The WM PR must carry 09b (the NOAHMP-interface bump; the
land-component tests crash without it) and new official baselines, since answers change against `develop-20260921` by
design. The ports' own open items are listed in `ports/README.md`.
