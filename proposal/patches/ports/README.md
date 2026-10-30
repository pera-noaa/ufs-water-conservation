# Ports of the water-closure fixes to other copies of the code

**Status (17 October 2026). The ports are not posted** (UFS upstream state: `../../post/POSTING.md`); every series applies with `git am` to a tree identical to its
branch. Fixes and UFS measurements: `../../water_closure_proposal.md`; references: [`references.md`](references.md);
independent reviews: [dispositions](#review-findings-and-dispositions); verification: [where each copy stands](#where-each-copy-stands);
old fix letters: [labels](#labels).

- **Measured in a model:** WRF and MPAS Thompson, WRF dynamics (W1–W3), WRF classic Noah, TEMPO in UFS, the NOAA-EMC
  land component, production GFS.v17, MPAS water, dry mass and energy over 24 h (`MPAS-conservation/`).
- **Harness only, not yet rerun in a model:** TEMPO round 3; TH6's refill and TH7's noreturn (WRF, MPAS, production);
  NM9, NM10, NM8's run-phase form, NM4's guard (production, EMC). MPAS dynamics v2 has passed its red team and is in
  `MPAS-conservation/`; `MPAS-dynamics/` still holds v1.
- **Open:**
  - **TH8 is held (user decision)** in every copy except MPAS, with Thompson's placeholder fix TH9: kept in `held/`,
    out of every series but `MPAS-conservation/`, where the user applied it. Without it, sedimentation below the old thresholds is deleted again (UFS: about 1e-7 kg/m² per 6 h).
  - **Noah-MP canopy wet fraction** ignores liquid under any ice; fixing it moves land beyond noise, so it is issue 4 of
    `../../ccpp_physics_issue_draft.md`, not a fix. **Glacier ice** is booked in `drain` (NM9, FIXME in the code).
  - **WRF:** the 1e-5 dynamics residuals are not the scalar diffusion operators ([probes](#wrf-em_quarter_ss-supercell-doubly-periodic-no-surface-fluxes-2-h));
    their source is not located. The no-PBL +1.66e-2 is 88 % negatives entering Thompson (TH6's refill not rerun there).
    `WRF-tempo/` on TEMPO round 2 (with TH8). **TEMPO:** the semi-Lagrangian placeholder floor is paid from vapour (the TH8 class).
  - **NM11** (ground latent heat; UFS diff 18) is not ported. Its hold is lifted: the UFS reproducibility run is back
    (`develop` + diffs 01–19 and 09b, NM11 in the tree, against baselines made from that tree: 54/54 compiles, 234/234
    tests bit for bit, 12 of them on one retry; `p20rt_final/` on Hercules). Porting is the user's call. Every
    Noah-MP copy surveyed carries it ([`survey_noahmp_copies.md`](survey_noahmp_copies.md#nm11-ground-latent-heat-keyed-on-ground-temperature-only)).
  - **Other suites:** MYNN-EDMF and GFDL MP v3 fixes proposed; csawmg (+10.5 % of P) and rap (−6 to −9 %) not localised.

## Where each copy stands

| copy | measure | original | now | measured in |
|---|---|---|---|---|
| WRF Thompson, mp 8 / 28 / 38 | microphysics meter / P, supercell 2 h | +1.51e-2 / +1.48e-2 / +1.68e-2 | +1.7e-6 / +1.6e-6 / +1.4e-6 (float32 resolution) | WRF, before TH6's refill and TH7's noreturn |
| WRF TEMPO, mp 88 | the same | +1.17e-2 | +8.4e-7 (round 2 + layer mass) | WRF, round 2 |
| WRF dynamics, `diff_opt=2`, TKE | dynamics residual / P | −1.07e-3 | +9.8e-6 | WRF (W1) |
| WRF dynamics, `diff_opt=1`, no PBL | the same | +0.923 | −5.4e-6 | WRF (W2) |
| WRF classic Noah, 12 km real data, 12 h | land residual / P | — | +8.7e-6 (float32) | WRF |
| MPAS Thompson | domain residual / P, 2 h | +1.97e-2 | +3.8e-5; ≤1.4e-14 kg/m² with the dynamics fix | MPAS |
| MPAS dynamics v2 | closure, max \|R\| | +6.0e-5 kg/m² | ≤1.4e-14 kg/m² | MPAS supercell; red team passed |
| MPAS, `MPAS-conservation/` (with TH8/TH9, layer + fixer) | ΔW/W, ΔMd/Md, ΔE/E over 24 h | 1.3e-3, ≤7e-15, — | −1.6e-16, 0, +1.9e-16 (energy: dycore part by the labelled fixer) | MPAS supercell, 24 h |
| TEMPO, four versions | fuzz calls with residual > 1e-13 | 3139–3246 (round 2) | 7, all ≤ 2.1e-13 | standalone column, round 3 |
| TEMPO in UFS | R_tot/P, 6–24 h | — | 0.00 % at `dt_inner` 720 and 150 s | UFS C96, rounds 1–2 |
| NOAA-EMC land component | Σ residual / ΣP | −5.2e-4 | −8e-13 | UFS land component, 24 h |
| Production GFS.v17 | R_tot/P, 6–24 h | +0.24…+0.27 % | 0.00 % at `dt_inner` 720 and 150 s | UFS C96, round 3 |
| HAFS.v2.2, GCAFS.v1.0, RRFS.v1 / AQM.v7 / SRW v3 | build | — | compiles, all suites / patched files compile / not built | Hercules |
| Noah-MP NM9 and NM10, all ports | single-column water and energy closure | see below | ≤1e-12 mm per call | `noahmpdrv_run` harness |

## Targets

| Path | Target | Fixes |
|---|---|---|
| `TEMPO-driver/`, `TEMPO-driver-ncar-main/` | ccpp-physics `ufs/dev` c7dc705; NCAR `main` f601ce9 (`mp_tempo.F90`) | TH1; TH5, recomputed every inner step (`check_tempo_driver_dz.py`: 4.7e-3 → ≤4.7e-16) |
| `TEMPO-scheme/`, `tempo_main_water_closure.diff` | NCAR/TEMPO `main` c62699f | TH2–TH4, TH6 (port); T1; TH7 with the round-3 refill (three commits) |
| `TEMPO-scheme-<pin>/`, `tempo_<pin>_water_closure.diff` | 2856696 (UFS `tempo_v3`), 881614f (WRF `phys/TEMPO`), 9adf9ef (ufs-community MPAS) | as `main`; 9adf9ef's port also drops the in-loop fall-speed recomputation (F1). A fix reaches UFS and WRF only when they move their pins |
| `WRF-thompson/`, `wrf_release-v4.8.1_thompson_water_closure.diff` | wrf-model/WRF `release-v4.8.1` 315a8319 | TH2–TH4, TH6 with its refill; TH7 with noreturn; TH5-WRF; TH2/TH3 completion; graupel ≤R1 to vapour (five commits) |
| `WRF-tempo/` | the same WRF; TEMPO 881614f round 2 | `rho_dry` into `tempo_run`; submodule moved to the round-2 series (local commits) |
| `WRF-dynamics/`, `wrf_release-v4.8.1_dynamics_water_closure.diff` | the same WRF | W1 (`horizontal_diffusion_s` flux form), W2 (`vertical_diffusion_mp` and the `'m'` branch), W3 (theta, own commit) |
| `MPAS-thompson/`, `mpas_develop_thompson_water_closure.diff` | MPAS-Dev/MPAS-Model `develop` aa6d8cd | TH2–TH4, TH6 with its refill; TH7 with noreturn; TH2/TH3 completion; TH5-MPAS |
| `ufs-MPAS-thompson/`, `ufs-mpas_noaa-develop_thompson_water_closure.diff` | ufs-community/MPAS-Model `noaa/develop` b5c26d6b | as MPAS-Dev (identical file); unused inside UFS today (built without `DO_PHYSICS`) |
| `MPAS-dynamics/`, `mpas_develop_dynamics_water_closure.diff` | MPAS-Dev `develop` aa6d8cd | v1: MP1/MP2 column borrowing with a domain fallback. Superseded by v2 (positive-definite upwind renormalisation after Skamarock 2006, MPAS's `config_positive_definite`, column-local guard; red team passed), which is `MPAS-conservation/` 0005–0007 |
| `MPAS-conservation/` | MPAS-Dev `develop` aa6d8cd | the whole MPAS series, 24 h machine precision, each patch labelled in its README: Thompson 0001–0004 (= `MPAS-thompson/`), dynamics v2 0005–0007, TH8 and TH9 0008–0009 (BUG FIX); sedimentation export 0010 and energy meter 0011 (INSTRUMENTATION); layer-local energy coupling 0012 (PHYSICS CHANGE, option B, opt-in); reproducible global energy fixer 0013 (FIXER); dissipative heating 0014 (PHYSICS CHANGE, opt-in). 0011–0014 behind `&nhyd_model` switches, stock defaults |
| `noahmp-emc_develop_D_H_I_K_L/`, `.diff` | NOAA-EMC/noahmp `develop` 2c7b3bc (pinned by ufs-weather-model `develop`, GFS.v17, HAFS.v2.2) | NM1, NM5, NM6, NM8, NM7 (commit order), NM9 (no reset), NM10, and 09b: NM2's optional `iter` in this copy's `noahmpdrv_run` (eight commits) |
| `noahmp-emc_0cd3e23_rrfs_companion/` | NOAA-EMC/noahmp 0cd3e23 (pinned by RRFS.v1) | 09b only |
| `ccpp-physics-production/<branch>/` | `production/GFS.v17` 8007f2c (19), `production/HAFS.v2.2` 525174d (19; also GCAFS.v1.0), `production/RRFS.v1` edd85a5 (18), `release/srw-v3` 2d8b1f20 (18), `production/AQM.v7` 67d069ad (18) | the UFS series adapted to each branch (SA1, TH5 with its inner loop, TH6's refill, TH7's noreturn, NM2 with an optional trailing `iter`, NM8 in the run phase, NM4's guard), the TH2/TH3 completion, then NM9 and NM10 last. AQM's TH5 uses its Thompson's own 287.04 and 0.622 |
| `held/<target>/` | on top of each series above | TH8 (lowest-layer thresholds removed) and, for the Thompson copies, TH9 (the R1 placeholder not sedimented as mass); TEMPO needs no TH9. Held by the user |
| `suites/` | ccpp-physics paths | proposed MYNN-EDMF and GFDL MP v3 fixes, not in any series |
| `ncar_noahmp_issue_draft.md` | NCAR/noahmp `master` 1a6225b | NM5, NM6, NM7 as issue text (not posted) |
| `survey_noahmp_copies.md`, `survey_other_copies.md` | every other copy found | which defects each carries |

Older trees build with `I_MPI_CC=icx` and, for RRFS/AQM, `-fp-model precise` in place of the icc-only C flags in
`cmake/Intel.cmake` (build system only). AQM's unpatched `unified_ugwp.F90` fails with the current compiler (#7496).

## Which fixes go where

- **TH1** belongs to the CCPP interface; WRF and MPAS pass dry mixing ratios.
- **TH5** (layer depth from the host's dry mass): in the CCPP drivers `dz = dp(1−q)/(gρ_scheme)`, recomputed every inner
  step; in WRF and MPAS an optional `rho_dry` to `mp_gt_driver` with `dz1d = dz·ρ_dry/ρ_scheme` (no inner loop there).
- **TH2/TH3 completion** (cloud sedimentation substeps; below 0 °C the snow gain from rain-snow collection capped at the
  rain lost): one extra commit in each port; in TEMPO's port commit. Checked with `port_thompson_c1c2_amend_any.py`.
- **TH6's refill and TH7's noreturn:** vapour left below 1e-10 is refilled from the layer's condensate (with its latent heat),
  then from the column's spare vapour, and floored only if the column has none; the early return is skipped when any
  layer enters below the floor. Same lines in every Thompson copy; WRF also scales graupel number and volume.
- **TH8 and TH9 (held):** TH8 counts all sedimentation out of the lowest layer as precipitation; TH9 starts flux-form
  rain, ice, snow and graupel sedimentation from each layer's actual content, so the R1 placeholder is not transported
  as mass. With both and NM10, TH8 is within noise from 6 to 24 h at C96 but not in the first 6 h (land canopy
  evaporation −2.4 %): genuine sub-threshold traces reach Noah-MP's canopy wet-fraction switch (issue 4).
- **TH7** (water at or below R1 to vapour): WRF and MPAS have its entry and leftover-rain parts; its third part is in
  UFS's `semi_lagrange_sedim` only. In TEMPO the counterparts are the six `*_check_and_update` routines and the
  sedimentation floors, including the early-return path.
- **T1** (TEMPO): `semilagrangian_sedimentation` tests `qpi > 0 .or. qmi < 0`; Juang & Hong (2010) eq. (A4) and
  Thompson test `< 0` for both edges. The fix moves UFS rain and graupel sedimentation from effectively
  piecewise-constant to piecewise-linear, so precipitation timing changes.
- **NM1** belongs to the CCPP Noah-MP driver (NCAR's drivers already pass the water flux). Where a driver sets the
  glacier's canopy fluxes to `undefined` (RRFS.v1, SRW v3, AQM.v7), NM1 zeroes them: otherwise every glacier point would
  hand the atmosphere ~2e21 mm of evaporation.
- **NM2** passes the CCPP loop counter to `noahmpdrv_run` as an optional trailing `iter` and steps the land on the first
  surface iteration only. In atm-land builds NOAA-EMC/noahmp's land component calls the run routine with its original
  arguments and may reach the ccpp-physics copy (same module name); an absent optional argument works only if the
  caller's interface declares it, so the land component's own `noahmpdrv_run` gets the same optional `iter` (09b).
  The interfaces were identical before: GFS.v17 vs EMC 2c7b3bc, RRFS.v1 vs EMC 0cd3e23. SRW and AQM build no land
  component.
- **NM4** builds Noah-MP's snow layers from the land snow, and none where the initial state has snow depth but no snow
  water (old-format coupled initial conditions gave layers without ice: a divide by zero in Noah-MP's energy).
- **NM8** sets Noah-MP's module latent heats (soil and glacier) at the start of `noahmpdrv_run` from the `con_hvap` and
  `con_hfus` it already receives, so no interface changes. Adding them to `noahmpdrv_init` first broke the land
  component's positional call (atm-land debug crash), and as optional arguments did not compile: the CCPP cap points a
  pointer at the host's PARAMETER constants.
- **NM7** is in `canwater` in every v4-style copy and in v5 (`CanopyHydrologyMod`).
- **NM9** (glacier snow booked, not created or deleted): the 600 mm reset exists only in ufs/dev, GFS.v17 and HAFS.v2.2;
  the other copies cap the pack (`mwd` = 100 mm, AQM 2000 mm) and need only the 0.1 mm floor and the two thin-snow
  truncations. The ice goes to `runsub`/`drain`, marked FIXME.
- **NM10** (= UFS diff 17): Noah-MP's frozen fraction applies to grid-scale precipitation only (convective is snow below
  freezing, the host's srflag rule; fresh-snow density blended by mass). Without convective precipitation the result is
  bit-for-bit unchanged.
- **W1–W3** (WRF dynamics): W1 puts `horizontal_diffusion_s` in exact flux form; W2 gives `vertical_diffusion_mp` and
  the `'m'` branch no flux through the ground and a telescoping mass flux; W3 does the same for theta and is a separate
  decision (it changes the no-PBL storm's cold pool: θ′ rms 2.06 → 1.60 K). Only `diff_opt=1` without a PBL reaches
  W2/W3; W1 changes every `diff_opt=2` case.

## Measurements

### UFS, TEMPO (`control_p8_ugwpv1_tempo`, C96, 24 h)

| run | R_mp/Pls, 6–24 h |
|---|---|
| unmodified | +0.03 % (the driver error TH1 fixes cancelled the scheme's own creation) |
| TH1 | +0.30…+0.34 % |
| TH1 + T1 | −0.29…−0.37 % |
| TH1 + port + T1 (+ TH7) | −0.05…−0.08 % (inside the split bias) |
| all fixes: R_tot/P | 0.00 % (round 2 also at `dt_inner` = 150 s; 0–6 h +2.83 %, presumably the step-1 bookkeeping shown for GFS.v17, not checked here) |

`water_budget_by_scheme.py`'s per-scheme split puts −0.04…−0.08 % of Pls into R_mp in 6-h windows (−0.18…−0.33 % in
24-h windows) while R_tot = 0: a synthetic model that conserves water exactly shows the same pattern. The total bounds
any real TEMPO loss to about 0.014 % of Pls.

### TEMPO standalone, round 3 (59-level column and fuzz, gfortran)

| finding (red team on round 2) | round 2 | round 3 |
|---|---|---|
| F1, 9adf9ef standard sedimentation: in-loop fall-speed overdraft | up to 1.4e5 kg/m² created, ΔT 1.1e6 K | ≤5.4e-15 kg/m², ΔT ≤0.83 K |
| F2, semi-Lagrangian floor order: graupel delivered by 900 s (`main`) | 39 % | 98 % (pre-TH7: 98 %) |
| F3, `main` hail-aware + hyperaware: second entry check | 9.5e-4 | ~1e-15 |
| F4, early-return vapour clip, dry column | 1.24e-3 kg/m² created | 0 |
| F5, negative cloud in dry layers | 0.127 kg/m² and 0.25 K created | ≤4e-16; heat matches the vapour condensed |
| fuzz, calls with residual > 1e-13 (per version) | 3139–3246 | 7 (≤2.1e-13, semi-Lagrangian remap rounding) |

Round 3 was measured with TH8 in the port commit. With TH8 now held, rain leaving the lowest layer below
`low_limit_mass_for_precip` is uncounted again; not re-measured (the lookup tables were deleted). Compiles (gfortran).

Column closure ≤7.9e-15 of P; driver dz check ≤4.9e-16. Disclosed behaviour changes: F1 moves the column's hourly
precipitation by +7.6e-4 (20 s) and +1.8e-4 (60 s); in 9adf9ef at 20 s TH7 raises it by +0.56 %, outside a ±0.04 %
perturbation spread (a constant 1e-9 K per step moves that run by +1.6 %).

### Thompson TH6 refill and TH7 noreturn (WRF double-precision harness)

| case | before | after |
|---|---|---|
| quiet-path negative condensate (red team), 5 columns | up to +1.515 kg/m², +4.92 K; fixer on every column | ≤3.6e-15 kg/m²; fixer never |
| attack battery, 93 columns: fixer columns / Σ residual | 7 / 9.03e-2 kg/m² | 0 / 6.98e-2 kg/m² |
| heat without water, 96 columns | 24 / 1.376 kg/m² | 0 / 0.277 kg/m² (bone-dry columns, floored by design) |
| plausible fuzz, 2000 columns | 4.3e-14 max | bit-identical |

The MPAS copies are syntax-checked only. Latent heat for negatives that no vapour pays for (red-team F3/F5) remains,
as in ufs/dev.

### WRF (`em_quarter_ss` supercell, doubly periodic, no surface fluxes, 2 h)

"host" is the per-call meter in WRF's dry mass, "scheme" the scheme's own density:

| run | host/P | scheme/P | domain/P |
|---|---|---|---|
| Thompson, 4 commits (mp 8) | +1.694e-6 | +1.418e-4 | −1.068e-3 |
| Thompson aerosol-aware (mp 28), original | +1.484e-2 | +1.498e-2 | +1.381e-2 |
| Thompson aerosol-aware (mp 28), 4 commits | +1.578e-6 | +1.415e-4 | −1.036e-3 |
| Thompson hail-aware (mp 38), original | +1.680e-2 | +1.694e-2 | +1.556e-2 |
| Thompson hail-aware (mp 38), 4 commits | +1.382e-6 | +1.423e-4 | −1.250e-3 |
| TEMPO (mp 88), original | +1.167e-2 | +1.181e-2 | +1.111e-2 |
| TEMPO round 2 + layer mass (`WRF-tempo/`) | +8.4e-7 | +1.401e-4 | −5.81e-4 |

The meter reproduces the known-bad original and the earlier fixed result; source md5s match after each build. The TH2/TH3
completion is not exercised by this case (output byte-identical). The remaining domain loss is the dynamics:

| case | dynamics/P, before | after (W1–W3) | domain after | microphysics after |
|---|---|---|---|---|
| `diff_opt=2`, `km_opt=2` | −1.07e-3 | +9.8e-6 | +1.16e-5 | +1.8e-6 |
| `diff_opt=2`, `km_opt=1` | −4.4e-5 | −2.3e-5 | −6.9e-6 | +1.6e-5 |
| `mix_full_fields=.false.` | −1.03e-3 | +6.1e-7 | +2.3e-6 | +1.7e-6 |
| `diff_opt=1`, `km_opt=4`, no PBL | +0.923 | −5.4e-6 | +1.66e-2 | +1.66e-2 |

- Offline, the old operators are out of balance by 7.0e-3 (W1) and −0.10 (W2) of Σ|T|, the new ones by ≤3e-17.
- **In the model** (job 10120179, read-only probes per call; pre-registered in `dynfix/PREREGISTRATION.txt`): S is the
  water a call adds, ΣS/Σ|T| summed over all calls, "negatives" the water in negative mixing ratios entering Thompson.

  | case | operator | ΣS/Σ\|T\|, before | after | max per call, after | negatives/P, after | microphysics/P, after |
  |---|---|---|---|---|---|---|
  | `diff_opt=2`, `km_opt=2` | `horizontal_diffusion_s` | +7.7e-4 | +7.5e-11 | 1.6e-4 | +5.3e-7 | +1.8e-6 |
  | `diff_opt=2`, `km_opt=1` | the same | +4.2e-5 | −1.2e-10 | 7.3e-6 | +2.7e-7 | +1.6e-5 |
  | `mix_full_fields=.false.` | the same | +7.9e-4 | +9.9e-11 | 7.5e-4 | +5.1e-7 | +1.7e-6 |
  | `diff_opt=1`, `km_opt=4`, no PBL | `vertical_diffusion_mp`, `'m'` | +1.1e-2 | +3.9e-9 | 7.9e-8 | +1.47e-2 | +1.66e-2 |

  The probe is inert (the probed run reproduces every closure digit above). The per-call gate (< 1e-5) fails by its
  letter in the first and third cases: 17 and 18 of 6000 calls, all with Σ|T| ≤ 0.29 against 2e9 for the largest call;
  Σ|S|/Σ|T| over all calls is 2.5e-9. So the remaining 1e-5 of P is not these operators. Negatives explain 88 % of the
  no-PBL microphysics residual, 29 % in the first and third cases and 2 % in the second.
- With `diff_opt=0`, `kvdif=0` and YSU the fixed builds are bit-identical to the control; dry mass is unchanged; the
  storm changes within the pre-registered bounds.
- WRF runs in single precision: values near 1e-6 of P are at float32 resolution. The positive microphysics rows
  (+4e-7…+1.6e-5) are only partly host negatives meeting Thompson's floors (2–29 %, probes above); TH6's refill not rerun.
- Not changed: momentum vertical diffusion, and the WRFPLUS tangent-linear/adjoint copies.
- **Classic Noah (real data, 12 km, 12 h):** Σ residual / ΣP = +8.7e-6 over 2.6M land point-steps, max 4.5e-5 kg/m²
  per step; the meter's control (canopy store left out) reads −4.75e-2, so it can fail.

### MPAS (supercell, 84×84 doubly periodic 2 km mesh, double precision, 2 h)

| run | domain residual / P at 2 h |
|---|---|
| Kessler | −6.5e-15 |
| Thompson original | +1.97e-2 |
| TH2–TH4, TH6, TH8 + TH7 (with TH8, now held) | −1.20e-4 |
| + TH2/TH3 completion + TH5-MPAS | +3.8e-5 (1e-14 through 0:50) |

The microphysics and coupling meters read ≤1e-15 kg/m² in every window. The rest is the dynamics: MP1, the monotonic
transport clip `max(0, scalar_new)` where the vertical Courant number exceeds 1 (+6.0e-5 kg/m²); MP2, `atm_srk3`'s
`where (scalars_2 < 0) scalars_2 = 0`, which creates +1.40 kg/m² without the monotonic limiter.

**v2 supercell gates** (pre-registered, `mpas_run/PREREGISTRATION.txt`, v2 section):

| case | closure max \|R\| (kg/m²) | guard / old-clip meter | pre-registration |
|---|---|---|---|
| monotonic dt 12 and dt 8; positive-definite; Kessler (v2 and commits 1+2) | ≤1.4e-14 | ≤8e-14 per window; old clip ~1e-20 | met |
| commits 1+2 at dt 8 and Kessler vs unfixed | bit-identical | — | met |
| both limiters off (v2) | +0.41 | the guard's plain clip in columns without positive mass | fails as expected; 0.33–0.36 predicted |
| unfixed monotonic / no limiter | +6.0e-5 / +1.40 | old clip equals the closure | must fail: fails |

**v1, as installed in `MPAS-dynamics/`:**

| run | domain R at 2 h before | after | max w (m/s) | mean P at 2 h (kg/m²) |
|---|---|---|---|---|
| monotonic, dt 12 s (MP1 binds) | +6.05e-5 | ≤1.4e-14 | 48.6 → 48.7 | 1.5755 → 1.5747 |
| no monotonic limiter (MP2 binds) | +1.40 | +3.0e-9 (Thompson's qv floor) | 48.5 → 50.0 | 2.0223 → 1.3586 |
| monotonic, dt 8 s | roundoff | roundoff | 50.7 → 50.8 | 1.5753 → 1.5723 |
| Kessler, dt 12 s | −1.4e-14 | −7e-15 | 40.0 → 40.0 | 2.1965 → 2.1965 |

### MPAS, 24 h conservation (`MPAS-conservation/`, supercell, 16 tasks)

Switches `config_mp_energy_coupling = 'layer'`, `config_energy_fixer = true`. Energy is E = IE + PE + KE + Lv0·Wv −
Lf0·(Wi + Pice) in the energy the dynamics integrates. Full budget, Hpe check, dry thermal and impact:
`../../../conservation/mpas/report.md`.

| quantity, 24 h | stock | 0001–0007 | + TH8/TH9 | + 0010–0013 |
|---|---|---|---|---|
| ΔW/W | 1.3e-3 | −1e-9 | 2.2e-15 | −1.6e-16 |
| ΔMd/Md | ≤7e-15 | ≤7e-15 | ≤7e-15 | 0 |
| ΔE/E | — | — | −4.3e-4 | +1.9e-16 (fixer) |

Energy splits two ways:
- **Physics and coupling close genuinely**, to ≤9e-6 J/m² per column-step.
- **The dycore residual** (−3.8e5 J/m², 1.67 % of gross condensation heating) is closed by the labelled fixer. A
  per-term tally puts 65 % of it in KE removed by explicit diffusion and damping with no heat returned (design); the
  opt-in 0014 returns it as heat (local work, or positive-definite dissipation rescaled to it), and the fixer falls
  to 1.31e5 J/m². The remaining 35 %, the net error of the
  energy-conserving operators, is open.

The fixer's sums are order-independent fixed-point sums, so runs are bit-identical at 7, 12 and 16 tasks and across
a 12 h restart. With its switch off, each of 0011–0014 is bit-identical to the patch before it. Option B (the layer
coupling, 0012) is an opt-in physics change, default stock (Ash's decision): peak w +10 %, colder cold pool,
precipitation unchanged within noise. Dissipative heating (0014) is an opt-in physics change, default off: peak w
+1.0 to +1.1 m/s, cold-pool area +11 % (positive-definite) or +21 % (local), precipitation unchanged within noise.

### NOAA-EMC/noahmp in the UFS land component (`datm_cdeps_lnd_gswp3`, 24 h)

| run | soil column-steps | Σ residual (mm) | Σ residual / Σ P |
|---|---|---|---|
| original 2c7b3bc | 402 552 | −1.50 (one-signed) | −5.2e-4 |
| NM1, NM5, NM6, NM8, NM7 | 402 552 | −2.3e-9 | −8e-13 |

The losses are NM5 and NM6; NM1, NM8 and NM7 change fluxes and energy, which this meter does not see. NM9 and NM10 are measured in the
harness below.

### Noah-MP NM9 and NM10, single-column harness (`noahmpdrv_run`, each copy's own sources)

| copy | NM9: glacier day, residual per column | NM9: fuzz glacier Σ residual | NM10: tropical rain + 1e-14 mm/s grid snow, 2 days: E, snowpack | NM10: same column without snow | NM10: cold convective snow, 265 K, snowpack |
|---|---|---|---|---|---|
| GFS.v17, HAFS.v2.2 (reset) | −26.2…+600 mm → ≤1.3e-13 per call | −1 060 → 1.1e-12 mm | 4.35 mm, 6.6 mm → 8.58 mm, 0 | 8.94 mm | 0.15 → 7.8 mm |
| SRW v3 | 0…+2.44 mm (the floor) → ≤1.4e-17 | 9e-13 → 9e-13 | 4.35, 6.6 → 8.58, 0 | 8.94 | 0.15 → 7.8 |
| RRFS.v1 | 0…+2.44 → ≤1.4e-17 | 9e-13 → 9e-13 | 4.23, 7.1 → 8.53, 0 | 8.91 | 0.14 → 9.9 |
| NOAA-EMC/noahmp | 0…+2.44 → ≤1.4e-17 | 9e-13 → 9e-13 | 4.39, 5.9 → 8.52, 0 | 8.89 | 0.13 → 7.9 |
| AQM.v7 | compiled only (its driver predates the harness) | | | | |

Soil points are bit-for-bit unchanged by NM9. NM10 changes only convective precipitation: without it, 24 000 fuzz calls per
copy are bit-for-bit unchanged. The tropical column's remaining 4 % against the snow-free one is the canopy wet-fraction
switch (an issue, above). NM8's run-phase form and NM4's guard leave the harness
bit-identical.

### Production GFS.v17 (`control_p8_ugwpv1`, C96, 24 h)

| window | original R_tot/P | round 3 R_tot/P | original R_cnv/Pc | round 3 R_cnv/Pc | original R_mp/Pls | round 3 R_mp/Pls |
|---|---|---|---|---|---|---|
| 0–6 h | +3.94 % | +3.64 % | +0.89 % | +0.01 % | −0.09 % | −0.04 % |
| 6–12 h | +0.27 % | +0.00 % | +0.80 % | +0.01 % | −0.75 % | −0.06 % |
| 12–18 h | +0.25 % | +0.00 % | +0.75 % | −0.01 % | −0.65 % | −0.04 % |
| 18–24 h | +0.24 % | −0.00 % | +0.81 % | +0.01 % | −0.64 % | −0.07 % |

At `dt_inner` = 150 s the round-3 R_tot/P is +3.45 / +0.00 / +0.00 / +0.00 %. The 0–6 h value is bookkeeping:
`atmf000` is written after step 1, and the step-1 physics water change (−0.0244 kg/m²) equals the window's R_dyn. Base:
`production/GFS.v17` ufs-weather-model with RTPWD `GFSv17opn_20251014`.

### Other UFS suites (C96, 24 h, ufs/dev + the series)

In-model meters in diagnostic builds (answer-neutral, and 0 on the closed GFS v17 p8 suite). Fixes in `suites/`.

| suite | R_tot/P, 6–12 / 12–18 / 18–24 h | cause | with the fix |
|---|---|---|---|
| p8_mynn, hrrr, rrfs_v1beta, rrfs_v1nssl | +2.0…+3.5 % | MYNN-EDMF `mynn_tendencies`: the surface vapour, sqw and sqc sources use `rhosfc` where the flux was divided by `rho1`, and `rhosfc` has a typo (+0.85 % of E); the dew limiter is always 0, so downward fluxes are booked but never applied (+0.55…0.9 % of E) | p8_mynn 0.00 %; hrrr, v1beta −0.03…−0.10 % (split bias); nssl −0.8…+0.2 % (NSSL microphysics) |
| control_iovr4_gfdlmpv3 | −0.30 / −0.31 / −0.33 % | GFDL MP v3 `mpdrv` converts back with 1/(1+qv_new) after converting in with 1/(1−qv_in) | 0.00 % |
| csawmg | +10.6 / +10.5 / +11.0 % (also in the original) | convection (Chikira–Sugiyama) or its coupling; not localised | — |
| rap (GF, RUC) | −6.0 / −5.8 / −4.8 % | lost outside the metered physics (R_dyn); not localised | — |
| c48 | 0.00 % (original +0.5…0.6 %) | — | — |

The same `rhosfc/rho1` factor multiplies MYNN's sensible-heat flux and drag (energy, not fixed).

### Forecast impact (red team, 24 h C96)

Original vs fixed against a noise floor from 9 bit-perturbed initial-condition pairs; confirmed = at least 3× the noise
maximum and coherent across related fields. One start date, no skill verification.

| fix | confirmed change | in the commit message |
|---|---|---|
| TH8 | land canopy evaporation −39 %, land latent heat −0.75 W/m², q2m −0.7 %; still −0.7 to −1.1 W/m² at day 10; with TH9 and NM10: within noise 6–24 h, canopy evaporation −2.4 % in 0–6 h | TH8 held |
| NM1 | host latent-heat output −12 % over pure sublimation, −4.2 % over snow-covered land | yes, reworded on every branch |
| SA1 (first form) | lowest 5 layers +0.010 to +0.014 K, q −0.03 to −0.06 % | no |
| SA1, TH5 inner loop, TH7 floor start (GFS.v17, not separable) | precipitation −0.57 %, tropics −1.0 %, z500 −0.09 m | no |
| NM2 | T2m over land +0.033 K, q2m +0.17 %, canopy evaporation +10 % | no |
| NM3, NM4 | land SWE −0.45 / +0.69 kg/m²; glacier SWE −2.85 kg/m² (NM3) | mechanism only |
| T1 (TEMPO) | grid-scale precipitation −5 % globally, −15 to −19 % in the tropics; rain water path +84 % | qualitative only |
| NM10 (phase rule; UFS series' owner, 3 extra noise pairs) | within noise on every metric | yes |
| canopy wet fraction (once part of NM10; max or sum) | canopy evaporation +18 %, snow sublimation −13 %, land latent heat −0.55 %, T2m −0.11 K, q2m −0.9 %, reaching z500 | an issue, not a fix |
| TH1, TH4, TH5, TH6, NM5, NM6, FV1, NM8, TH7, NM7, TH2/TH3 completion | within noise | — |

## Review findings and dispositions

| Series | Finding | Disposition |
|---|---|---|
| WRF/MPAS Thompson | quiet-path negative condensate created water through the qv floor (red team) | TH6's refill and TH7's noreturn ported |
| | TH2/TH3 lacked the amended 0003's substepping and cap | completion commit added |
| | messages: stale "not built or run", mixed normalisations, TH4 and graupel-volume wording, AI line missing | rewritten; trees unchanged |
| | TH7 entry branches take negative inputs too | stated in TH7's message; same as the reference |
| Production | TH2/TH3 stale on all five branches | completion added |
| | AQM.v7 TH5 used host constants while its Thompson keeps 287.04/0.622 | fixed |
| | AQM.v7 TH1 asymmetry under `merra2_aerosol_aware` | pre-existing, number concentrations only; noted |
| | RRFS.v1/SRW v3/AQM.v7: NM1 summed glacier canopy fluxes set to `undefined` | fixed in their NM1 commit |
| | NM8's arguments before `errmsg` broke the land component's positional call (atm-land debug crash); optional arguments then failed to compile (CCPP cap pointer to a PARAMETER) | latent heats set in the run phase; init interface unchanged |
| | NM4 built ice-less snow layers from old-format coupled initial conditions | no layers without snow water |
| | NM2's `iter` was a required argument after `flag_iter`: the land component's call would shift every later argument; optional trailing then needs the land component's interface to declare it (atm-lnd debug crash) | optional trailing `iter` in both copies (09b) |
| TEMPO | round 1: early-return TH7, TH5 inner loop, TH3 cap, TH2 substepping, T1 message, frozen-fraction order, no-op TH7 arguments, r1 placeholders | fixed in round 2 (r1 placeholders in flux-form sedimentation only) |
| | red team on round 2: F1–F5 | fixed in round 3 |
| NOAA-EMC/noahmp | messages: NM1's history `evap`, NM8's "water unchanged", NM5's glacier scope, missing measurement, NM7's contradiction | rewritten; trees unchanged |
| UFS series (UFS-Chem session) | SA1's deep half (cloud-base drain independent of q(kb)) | SA1's final form in every series; the day-6.4 v1 crash is an NSST sea-spray instability, not SA1 (proposal §7) |
| | TH5 inner loop; TH2 not in `pfll1`; NM4 with `frac_grid=false`; NM2 coastal coefficients; NM3 with `gcycle`; NM1 host LH; FV1 | TH5 inner loop folded into TH5; the rest relayed |

## Scripts

In `../../scripts/`:
- **TEMPO:** `apply_tempo_b_patch.py`; round 3: `port_tempo_scheme_v3.py`, `port_tempo_m5_v3.py`, `make_msgs_v3.py`
  (earlier rounds: the `_v2` names and those without a suffix).
- **WRF and MPAS:** `port_thompson_wrf_mpas.py`, `port_thompson_m5_wrf_mpas.py`, `port_thompson_m4_wrf.py`,
  `port_thompson_m4_mpas.py`, `port_thompson_c1c2_amend.py`.
- **Any Thompson copy:** `port_thompson_placeholder_any.py` (held TH9; reproduces it byte for byte), `port_thompson_c1c2_amend_any.py`, `port_thompson_m4_inner_any.py`,
  `port_thompson_negr_floor_any.py`, `port_thompson_qv_floor_any.py` (TH6's refill), `port_thompson_m5_noreturn_any.py`.
- **Noah-MP:** `port_noahmp_emc.py`, `port_noahmp_emc_k.py` (EMC); any copy: `port_noahmp_glacier_N_any.py`,
  `port_noahmp_fpice_any.py` (NM10; reproduces diff 17), `port_noahmp_k_runphase_any.py` (NM8; reproduces diff 15), `port_noahmp_e_optional_any.py` (NM2; reproduces diff 09).
- **Meters and budgets:** `instrument_noahmp_emc_meter.py`, `instrument_wrf_mp_meter.py`, `wrf_water_closure.py`,
  `make_wb_rundir.sh`.
- **Tests:** `tempo_test/` (standalone column closure and single-call cases). Harnesses in the session scratchpad:
  `redteam/noahmp/` (Noah-MP), `fpice/` (NM10), `port07/harness/` (Thompson in WRF).

## Labels

Fixes are named by home (SA = SAMF, TH = Thompson, NM = Noah-MP, FV = FV3). Commit messages, branch and directory names
(`noahmp-emc_develop_D_H_I_K_L/`), the scripts (names, docstrings, abort messages, including their old diff numbers) and
`README.history.md` keep the old letters; diff numbers in this file are the UFS series' new application order.

| old | A | B | C1 | C2 | C3 | M4 | M1 (and 07, its refill) | M5 | M2 (held) | 13a (held) | J |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new | SA1 | TH1 | TH2 | TH3 | TH4 | TH5 | TH6 | TH7 | TH8 | TH9 | FV1 |

| old | D | E | 08b | F | G | H | I | L | K | N | O |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new | NM1 | NM2 | 09b | NM3 | NM4 | NM5 | NM6 | NM7 | NM8 | NM9 | NM10 |

NM11 (diff 18) is new and has no old letter.

A′ (A's final form) is SA1; "A (first form)" is SA1's first form. Unchanged: T1 (TEMPO), W1–W3 (WRF dynamics), MP1/MP2
(MPAS dynamics), the red-team findings F1–F5, issues 1–6.

## Register

What moved to [`README.history.md`](README.history.md), verbatim (the history keeps every measured number):

| Former section | Status | Where |
|---|---|---|
| Status notes of 14 October (evening, night) | superseded by the status above | history |
| TEMPO round 2 broken in five places; round 2 done | superseded by round 3 | history (tables above) |
| Held for the UFS series' author (A's deep half, M4 inner loop) | resolved: SA1's final form and the inner loop in every series; the crash is NSST sea spray | history |
| Blocker: M2; land side of M2 (O with the canopy wet fraction) | resolved: TH8 held with TH9; NM10 phase-only; the wet fraction an issue | history |
| TEMPO standalone: original → round 2 column tables, single-call cases, r1 placeholders, the early-return floor | superseded by round 3 | history |
| 9adf9ef's ice sedimentation applies 1/steps of the flux (seen in passing, not water) | open, not water | history |
| WRF dynamics variants table and W1/W2 diagnosis | evidence for W1–W3 | history |
| WRF verification gates; mp 38 table build; `WRF-tempo/` `.meta` note | current in brief above | history |
| MPAS: R = 287.0 diagnostic run, M4 frame term, MP1/MP2 diagnosis, v1 design and fixer amounts | v1 to be superseded by v2 | history |
| MPAS: Thompson's final qv floor creates water at qv = 0 (2.9e-9 kg/m²) | addressed by TH6's refill (not rerun in MPAS) | history |
| WRF: classic Noah "remains a gap" | superseded: measured (above) | history |
| M4: "all tests ran with ndt = 1" | superseded: GFS.v17 round 3 at `dt_inner` = 150 s | history |
