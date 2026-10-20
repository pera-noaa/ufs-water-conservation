> **History of [README.md](README.md).** The ports README as of 15 October 2026, verbatim: dated status notes, superseded rounds (TEMPO rounds 1–2, MPAS dynamics v1 design) and the diagnosis that led to each fix. The head carries what is currently true; its register says what lives here.

# Ports of the water-closure fixes to other copies of the code

**Status (14 October 2026, night). Nothing has been posted.** The fixes and their UFS measurements are in
`../../water_closure_proposal.md`; this folder carries them to the other repositories that hold the same code. Every
series below has had an independent review, by reviewers who did not write the patches; their findings and what was
done about them are in [Review](#review-findings-and-dispositions). The physics references are in
[`references.md`](references.md) and [`references.bib`](references.bib).

- **Closed and measured:**
  - WRF Thompson: microphysics +1.5e-2 → +1.7e-6 of P.
  - MPAS Thompson: domain +2.0e-2 → +3.8e-5 of P. The remainder is MPAS's monotonic transport clip; with the dynamics
    fix it is ≤1.4e-14 kg/m². The microphysics and coupling meters read ≤1e-15 kg/m².
  - TEMPO standalone: ≤1e-14 after M5.
  - TEMPO in UFS: R_tot/P 0.00 % with all fixes.
  - NOAA-EMC/noahmp land component: −5.2e-4 → −8e-13.
  - Production GFS.v17: R_tot/P +0.24…+0.27 % → 0.00 %.
- **TEMPO round 3 fixes the red team's five breaks (local, gfortran; not yet rerun in UFS, WRF or with Intel):**

  | finding | round 2 | round 3 |
  |---|---|---|
  | F1, 9adf9ef standard sedimentation: in-loop fall-speed overdraft | up to 1.4e5 kg/m² created, ΔT 1.1e6 K | ≤5.4e-15 kg/m², ΔT ≤0.83 K |
  | F2, semi-Lagrangian floor order: graupel delivered by 900 s (main) | 39 % | 98 % (pre-M5 98 %) |
  | F3, main hail-aware + hyperaware: second entry check | 9.5e-4 | ~1e-15 |
  | F4, early-return vapour clip in a dry column | 1.24e-3 kg/m² created | 0 |
  | F5, negative cloud in dry layers | 0.127 kg/m² and 0.25 K created | ≤4e-16; heat matches the vapour condensed |
  | fuzz, calls with residual >1e-13 (per version) | 3139–3246 | 7 (2.0–2.1e-13, semi-Lagrangian remap rounding; same values in quadruple precision) |

  - **How:** F1 removes the in-loop fall-speed recomputation (as 881614f and later already do). F2 keeps the
    semi-Lagrangian floor as mass and condenses it from vapour with its latent heat. F3 zeroes the graupel tendencies
    before the hail-split rerun and guards `ng1d`/`qb1d`. F4/F5 refill vapour below `min_qv` from the layer's condensate,
    then the column's vapour, and floor only a column with none to spare, counting that water in
    `tempo_main_diags%vapour_floor_water`.
  - **Behaviour changes, disclosed in the messages:** F1 changes the 59-level column's hourly precipitation by +7.6e-4
    (20 s) and +1.8e-4 (60 s); in 9adf9ef at 20 s, M5 raises it by +0.56 %, outside the ±0.04 % perturbation spread (the
    run moves +1.6 % with a constant 1e-9 K per step).
  - **Open:** the semi-Lagrangian floor is paid from vapour rather than removed. That is the same R1-placeholder class as
    the Thompson M2 finding, where the UFS series' owner is removing the placeholder at the source; TEMPO keeps it for
    the fall speed above the precipitation top. `WRF-tempo/` still points at round 2.
- **The day-6.4 v1 crash is not caused by our fixes.** It is an existing NSST sea-spray instability (`lseaspray`, the P8
  default): the explicit spray flux on a 22 m layer overshoots about 14× per 720 s step in a C96 eyewall at the 30 m/s
  wind cap. Unmodified v1 shows the same oscillation from the same restart; it disappears with spray off and stays
  bounded at half the step. Details: proposal §7. A′ and the M4 inner loop are in every production series (r4 on).
- **Land side of the M2 artefact fixed (O = UFS diff 19, series `noahmp-precip-phase`; harness-measured here, being run
  in the full model by the UFS series' owner).** Noah-MP had two switches that flip on any trace of frozen water:
  `fpice` applied the grid-scale frozen ratio to convective rain, and the canopy wet fraction ignored liquid whenever
  any ice was intercepted. O applies the microphysics fraction to grid-scale precipitation only (convective is snow
  below freezing, the host's own srflag rule) and sets the wet fraction from the larger of the ice and liquid fill
  fractions (the phases share the same leaves). In the harness a tropical column with 1e-14 mm/s of grid-scale snow now evaporates exactly what the
  snow-free column does (4.35 → 8.94 mm in 2 days, no phantom snowpack). It is on ufs/dev (diff 19), all five
  production branches and NOAA-EMC/noahmp; `port_noahmp_fpice_any.py` reproduces diff 19 byte for byte. Thompson's placeholder
  transport (below) is still to be fixed at the source.
- **Blocker found by the forecast-impact red team: M2 cuts land canopy evaporation by about 40 % (all copies carrying M2,
  production included).** M2 books R1-level frozen sedimentation as a trace of grid-scale snow almost everywhere.
  Noah-MP with `iopt_snf = 4` sets `fpice = min(1, prcp_frozen/prcpnonc)` and applies it to all precipitation,
  convective included, so tropical convective rain on land falls as snow. Root cause (UFS series' owner, from the code):
  in flux-form ice and snow sedimentation a layer under falling ice or snow holds `R1` and inherits the fall speed of
  the layer above, and the in-loop `max(R1, …)` floors re-create it each substep, so R1 is transported as if it were
  mass. Candidate fix at the source: extend M5's floor start to the flux-form branches and drop the in-loop floors.
  Being tested on develop + 01–18; the M2 decision goes to the user. No M2 change is mirrored until then. The user
  chose to fix the Noah-MP side as well (O, above). See [Forecast impact](#forecast-impact-red-team-24-h-c96).
- **Fix 07's vapour refill and M5's noreturn are ported (harness-checked, not rerun in a model):** WRF, MPAS, ufs_mpas
  and all five production branches. They are folded into each copy's M1 and M5 commits, and nothing else changed.
  In WRF the refill also scales graupel number and volume. WRF double-precision harness:

  | case | closure2 | closure3 |
  |---|---|---|
  | quiet-path negative condensate (red-team F1), 5 columns | up to +1.515 kg/m² water, +4.92 K; fixer fires on every column | ≤3.6e-15 kg/m²; fixer never |
  | attack battery, 93 columns: fixer columns / Σ residual | 7 / 9.03e-2 kg/m² | 0 / 6.98e-2 kg/m² |
  | heat without water, 96 columns: fixer columns / Σ residual | 24 / 1.376 kg/m² | 0 / 0.277 kg/m² (bone-dry columns, floored by design) |
  | plausible fuzz, 2000 columns (seed 11) | 4.3e-14 max | bit-identical to closure2 |

  The MPAS copies add the same lines without the graupel number and volume (MPAS's Thompson lacks them) and are
  syntax-checked only. F3/F5 (latent heat for negatives no vapour pays for) remain open, as in ufs/dev.
- **Glacier fix N mirrored (harness-measured, not yet run in a model):** GFS.v17 and HAFS.v2.2 get the full N (the 600 mm
  reset, floor and truncations); RRFS.v1, SRW v3, AQM.v7 and NOAA-EMC/noahmp have no reset and get the floor and
  truncations. The glacier ice stays in `drain`, marked FIXME in the code (user decision: a frozen-runoff field is
  deferred).
- **D was wrong on RRFS.v1, SRW v3 and AQM.v7, now fixed in their 0004:** those drivers set canopy evaporation and
  transpiration to `undefined` (9.99e20) over land ice, so D's `evap = (ecan+etran+edir)/density` handed every glacier
  point about 2e21 mm of evaporation. They are now 0 there, as upstream did in 3fe1f187. GFS.v17, HAFS.v2.2 and the EMC
  port already had 0.
- **Compile status:** the physics compiles with all suites on Hercules for GFS.v17 (built and run), HAFS.v2.2, GCAFS.v1.0
  and RRFS.v1. On AQM.v7 all nine patched files compile; the only failure is in the unpatched `unified_ugwp.F90`,
  which the current Intel compiler rejects (error #7496, pre-existing). SRW is not built.
- **Outside the microphysics, WRF:** the WRF domain loses 0.1 % of P through its `diff_opt=2` horizontal scalar
  diffusion with TKE K. The no-PBL `vertical_diffusion_mp` path creates water (an ideal-case path only).
  `diff_opt=1` horizontal diffusion and WSM3 close.

## Targets

| Path | Target | Fixes | Status |
|---|---|---|---|
| `TEMPO-driver/`, `TEMPO-driver-ncar-main/` (ccpp-physics) | ufs-community/ccpp-physics `ufs/dev` c7dc705; NCAR `main` f601ce9 (`physics/MP/TEMPO/mp_tempo.F90`) | B; M4 for TEMPO | round 1 built and run in UFS (below). Round 2 computes dz inside the inner loop; `scripts/tempo_test/check_tempo_driver_dz.py` runs the real `tempo_run` for 4 inner steps (relative error 4.7e-3 at steps 2–4 before, ≤4.7e-16 after) |
| `TEMPO-scheme/`, `tempo_main_water_closure.diff` | NCAR/TEMPO `main` c62699f (`src/module_mp_tempo_main.F90`) | C1, C2, C3, M1, M2; T1; M5 (three commits) | round 3: red-team reproductions and fuzz (status above); round 2: standalone column ≤1e-14 and the three single-call tests (below). Round 1, with B, M4 and the UFS series, gave R_tot/P = 0.00 % in UFS |
| `TEMPO-scheme-<pin>/`, `tempo_<pin>_water_closure.diff` | the same file at 2856696 (ccpp-physics `tempo_v3`, UFS), 881614f (WRF `phys/TEMPO`, v3.0.5), 9adf9ef (ufs-community/MPAS-Model `physics_noaa/TEMPO`) | as `main` | as `main`, each with its own tables. A fix in `main` reaches UFS and WRF only when they move their pins |
| `WRF-thompson/`, `wrf_release-v4.8.1_thompson_water_closure.diff` | wrf-model/WRF `release-v4.8.1` 315a8319 (`phys/module_mp_thompson.F`, `phys/module_microphysics_driver.F`) | C1, C2, C3, M1 (with 07's refill), M2; M5 (with noreturn); M4-WRF; C1/C2 completion; graupel ≤R1 to vapour (five commits) | built and run in WRF (below) before the refill, noreturn and commits 4–5; those are checked in the double-precision harness only |
| `MPAS-thompson/`, `mpas_develop_thompson_water_closure.diff` | MPAS-Dev/MPAS-Model `develop` aa6d8cd (`physics_wrf/module_mp_thompson.F`, `mpas_atmphys_driver_microphysics.F`) | C1, C2, C3, M1 (with 07's refill), M2; M5 (with noreturn); C1/C2 completion; M4-MPAS | built and run in MPAS (below) before the refill and noreturn; those are syntax-checked only |
| `MPAS-dynamics/`, `mpas_develop_dynamics_water_closure.diff` | MPAS-Dev/MPAS-Model `develop` aa6d8cd (`src/core_atmosphere/dynamics/mpas_atm_time_integration.F`) | MP1 (monotonic transport clip), MP2 (pre-physics clip): column-conserving borrowing (`atm_nonneg_column`, ON506 eqs. 10–11), with a domain fallback for empty columns in MP2 | built and run in MPAS (below). **v1, to be replaced by v2** (positive-definite upwind renormalisation after Skamarock 2006, MPAS's `config_positive_definite`, column-local guard, no domain fallback): supercell gates pass (below); red-team matrix rebuilding |
| `ufs-MPAS-thompson/`, `ufs-mpas_noaa-develop_thompson_water_closure.diff` | ufs-community/MPAS-Model `noaa/develop` b5c26d6b (the Thompson file is identical to MPAS-Dev's) | as MPAS-Dev | the same commits; not used inside UFS today (UFSATM builds MPAS without `DO_PHYSICS`) |
| `noahmp-emc_develop_D_H_I_K_L/`, `.diff` | NOAA-EMC/noahmp `develop` 2c7b3bc | D, H, I, K, L, N (no reset), O | run in the UFS land component (below). K changes `noahmpdrv_init`'s interface the same way as the ccpp-physics copy: they must land together |
| `ccpp-physics-production/<branch>/` | `production/GFS.v17` 8007f2c (20 patches), `production/HAFS.v2.2` 525174d (20; also GCAFS.v1.0 7395db5), `production/RRFS.v1` edd85a5 (19), `release/srw-v3` 2d8b1f20 (19), `production/AQM.v7` 67d069ad (19) | the UFS series adapted to each branch, plus the C1/C2 completion, then N and O as the last two patches; AQM also M4 with its Thompson's own constants | every series applies with `git am` from its base. GFS.v17 built and run with the first 18 (below); N and O are measured in the single-column harness only. HAFS, GCAFS and RRFS: `ccpp_physics` compiles with every suite. AQM: every patched file compiles (`make -k`); `unified_ugwp.F90` (unpatched) does not, with the current compiler. SRW not built. The older trees need `I_MPI_CC=icx` and, for RRFS/AQM, `-fp-model precise` in place of the icc-only C flags in `cmake/Intel.cmake` (build system only) |
| `ncar_noahmp_issue_draft.md` | NCAR/noahmp `master` 1a6225b | H, I, L (issue text) | v5 has I and L identically; H at a 1e-6 mm threshold, not measured |
| `survey_noahmp_copies.md`, `survey_other_copies.md` | every other copy found (GEOS, HRRR, BRAMS, COAWST, UACM, MONAN, ERF, SHiELD, GFS.v16, HREF) | — | which defects each carries |

## Which fixes go where

- **M5** (water at or below R1 to vapour):
  - WRF and MPAS Thompson have its entry and leftover-rain parts. The third part, in `semi_lagrange_sedim`, is a UFS
    addition with no counterpart there.
  - In TEMPO the counterparts are the six `*_check_and_update` routines and the sedimentation floors. M5 gives the
    routines optional `qvten`/`tten`/`lat_ocp` and applies the tendency before the floor.
  - At TEMPO's early return (`.not. do_micro .and. .not. supersaturated`) the entry vapour and heat tendencies are
    applied exactly as at the final update, so M5 holds on that path too.
- **C1/C2 completion** (cloud sedimentation substeps; below 0 C, cap the snow gain from rain-snow collection at the rain
  lost to it): the UFS series' 0003 was amended after the first ports. Each ported series carries it as one extra
  commit; TEMPO round 2 has it in its port commit.
  - The ports were checked with `scripts/port_thompson_c1c2_amend_any.py`. Run on the pre-amendment files, it
    reproduces the WRF/MPAS amendment, and it refuses a file that is already amended or that lacks C1/C2.
- **07 refill and M5 noreturn:** vapour left below 1e-10 at the end of the step is refilled from the same layer's
  condensate (with its latent heat), then from the column's spare vapour, and floored only if the column has none.
  The early return is skipped when any layer enters below the floor. Same lines in every Thompson copy; WRF also
  scales graupel number and volume.
- **L** is in `canwater` in every copy of the v4-style code, and in v5 (`CanopyHydrologyMod`).
- **B** belongs to the CCPP interface. WRF and MPAS pass dry mixing ratios; TEMPO's CCPP driver needs it.
- **M4** (layer depth from the host's dry mass):
  - In the CCPP drivers it is `dz = dp(1−q)/(gρ_scheme)`.
  - In WRF and MPAS it is an optional `rho_dry` argument to `mp_gt_driver` with `dz1d = dz·ρ_dry/ρ_scheme`. Each call
    has no inner loop, so `dz1d` and `ρ_scheme` refer to the same state.
  - In a driver with an inner loop (the Thompson and TEMPO CCPP drivers when `dt_inner < dtp`), dz must be recomputed
    each inner step. All tests so far ran with `dt_inner = dt_atmos` (ndt = 1).
  - AQM.v7's Thompson keeps its own `R = 287.04` and `0.622`, so its M4 uses those.
- **K** adds `con_hvap` and `con_hfus` to `noahmpdrv_init` as optional trailing arguments, set only when both are
  present. In the atm-land build NOAA-EMC/noahmp's land component links against whichever `noahmpdrv` module comes
  first (both copies share the name), so the original positional call must still line up; inserting them before
  `errmsg` crashed `control_p8_atmlnd_debug` (found by the UFS series' owner). The EMC port passes them by keyword.
- **G** (Noah-MP snow layers from the land snow) builds no layers where the initial state has snow depth but no snow
  water: dividing by a small land fraction turned such a depth into layers with no ice, a divide by zero in Noah-MP's
  energy on the first step in the coupled regression tests (found by the UFS series' owner; same guard on every branch).
- **D** belongs to the CCPP Noah-MP driver; NCAR's own Noah-MP drivers already pass the water flux. Where a driver
  sets the glacier's canopy fluxes to `undefined`, D must zero them (RRFS.v1, SRW v3, AQM.v7).
- **N** (glacier snow booked, not created or deleted): the 600 mm reset exists only in ufs/dev, GFS.v17 and HAFS.v2.2.
  The other copies cap the pack instead (`mwd` = 100 mm, AQM 2000 mm, leaving as `snoflow`) and need only the 0.1 mm
  floor and the two thin-snow truncations. In every copy the ice goes to `runsub`/`drain`, marked FIXME.

## Measurements

### UFS, TEMPO (`control_p8_ugwpv1_tempo`, C96, 24 h, `sedi_semi`)

R_mp/Pls, % of grid-scale precipitation, 6–24 h (the 0–6 h window carries a bookkeeping offset, below):

| run | R_mp/Pls |
|---|---|
| unmodified | ≈0 (+0.03) |
| B | +0.30…+0.34 |
| B + T1 | −0.29…−0.37 |
| B + port + T1 | −0.05…−0.08 (inside the script's split bias, below) |
| B + port + T1 + M5 | −0.05…−0.08 |
| all fixes (UFS series 16 + J + TEMPO 3 + driver B, M4): R_tot/P | 0.00 % for 6–24 h |

Unmodified TEMPO closed in UFS only because B's driver error cancelled the scheme's own creation (T1 and the C fixes).

**What this table can resolve (meters red team).**
- **The per-scheme split is biased.** `water_budget_by_scheme.py`'s split puts −0.04…−0.08 % of Pls into R_mp in
  6-h windows, and −0.18…−0.33 % in 24-h windows, while R_tot = 0 and R_dyn mirrors it. A synthetic model that
  conserves water exactly shows the same pattern from a thickness tide alone. So this is a bias of the split, not a
  floor and not a microphysics loss.
- **The rows from B + port + T1 down cannot resolve anything below ~0.05 %.** The total is the reliable number: R_tot/P
  = 0.00 % (|R_tot| < 0.005 % of P) bounds any real TEMPO loss to about 0.014 % of Pls. There is no in-model TEMPO meter
  in UFS.

### TEMPO standalone column

TEMPO's 59-level test column, water closure of every call (`scripts/tempo_test/water_closure_test.F90`;
`_pre305.F90` for 9adf9ef). Σ(W₁ − W₀ + P)/ΣP, 20 s × 180 / 60 s × 60 steps:

| version | sedimentation | original | C1–C3, M1, M2 | + T1 |
|---|---|---|---|---|
| `main` c62699f | standard | 4.6e-5 / 3.7e-4 | 1.3e-7 / 4.3e-8 | 1.3e-7 / 4.3e-8 |
| | semi-Lagrangian | 4.9e-4 / 1.6e-3 | 5.7e-4 / 1.0e-3 | 1.3e-7 / 4.4e-8 |
| 2856696 (UFS) | standard | 4.1e-5 / 3.7e-4 | 1.3e-7 / 4.3e-8 | 1.3e-7 / 4.3e-8 |
| | semi-Lagrangian | 2.6e-3 / 3.1e-3 | 1.8e-3 / 2.8e-3 | 1.3e-7 / 4.4e-8 |
| 881614f (WRF) | standard | 4.1e-5 / 3.7e-4 | 1.3e-7 / 4.3e-8 | 1.3e-7 / 4.3e-8 |
| | semi-Lagrangian | 2.1e-3 / 2.9e-3 | 1.8e-3 / 2.8e-3 | 1.3e-7 / 4.4e-8 |
| 9adf9ef (UFS MPAS fork) | standard | 4.2e-5 / 1.1e-3 | 2.8e-8 / 4.3e-8 | 2.8e-8 / 4.3e-8 |
| | semi-Lagrangian | 4.1e-3 / 2.6e-3 | 3.3e-3 / 2.3e-3 | 3.0e-8 / 4.4e-8 |

With M5 added, every version closes to ≤1e-14 under both schemes; the residual above came from the check-and-update
deletions and overshoots. This column never reaches the early-return path, so round 2 adds three single-call cases
(`scripts/tempo_test/water_closure_test_v2.F90`, modes `early`, `csub`, `cap`; gfortran `-O0 -fcheck=all
-fdefault-real-8`, tables built locally; the Intel column numbers above reproduce to two digits).

Round 2 column closure, Σres/ΣP (20 s × 180 / 60 s × 60). The largest single step is ≤8.8e-14 kg/m². With one
substep, the cloud substepping is bit-for-bit neutral (`cmp` of final states, 16 cases).

| version | scheme | round 1 (port+T1+M5) | round 2 |
|---|---|---|---|
| `main` | standard | −5.1e-15 / 2.4e-15 | −6.8e-15 / −2.6e-15 |
| | semi-Lagrangian | −5.9e-15 / −1.3e-15 | 4.5e-15 / 3.4e-15 |
| 2856696 | standard | −8.4e-16 / 1.3e-15 | −2.6e-15 / −1.5e-15 |
| | semi-Lagrangian | −9.6e-15 / 1.4e-15 | 1.7e-15 / −1.1e-15 |
| 881614f | standard | −8.9e-15 / −6.4e-15 | 2.4e-15 / 3.9e-15 |
| | semi-Lagrangian | 6.4e-15 / 3.8e-15 | 7.8e-15 / 2.4e-15 |
| 9adf9ef | standard | −5.9e-15 / −4.3e-15 | −4.5e-15 / −1.7e-15 |
| | semi-Lagrangian | −5.2e-15 / −1.1e-14 | 2.1e-15 / 5.1e-16 |

Single-call cases (identical in all four versions):

| case | round 1 | round 2 |
|---|---|---|
| early return: subsaturated, qr 5e-13, qc −1e-8 | +2.1e-6 kg/m² created | ≤9e-16 |
| cloud substepping: fog in a 5 m lowest layer, 600 s, Courant 5.6 | surface precipitation 5.58 × the fog present; 0.042 kg/m² from vapour | 6 substeps; 1.000 × the fog; none from vapour |
| C2 cap: cold rain and snow, 600 s | re-closed prg_rcs −1.5e-8 kg m⁻³ s⁻¹ | never negative; full series ≤5e-15 |

- **Remaining water source:** the early-return path shares the final update's `max(min_qv, …)` vapour floor. That
  floor is the one remaining way the scheme can create water: when a negative condensate is filled from a nearly dry
  layer.
- **r1 placeholders:** not transported in the flux-form sedimentation (round 2). In the semi-Lagrangian scheme they
  also set the edge values at precipitation tops, so they are left in place: about 1.6e-10 kg/m² per step of booked
  precipitation, and the books still close.
- **Precipitation change, round 2 vs round 1:** its direct effect is about 2e-10 of P over the hour. Larger changes
  (up to 4e-4 on 9adf9ef at 20 s with the semi-Lagrangian scheme) are within that run's spread under 1e-14…1e-9 vapour
  perturbations.
- **Seen in passing, not water:** 9adf9ef's ice sedimentation calls `sedimentation` once with `steps=substeps_sedi` and
  no loop, so only 1/steps of the ice flux is applied when there is more than one substep. Water is still conserved.

**T1.**
- **The defect:** `semilagrangian_sedimentation` tests `qpi(k) > 0 .or. qmi(k) < 0`. Juang & Hong (2010) eq. (A4), the
  piecewise-linear (PLM) safeguard, and Thompson's copy test `< 0` for both edges. TEMPO's test therefore keeps exactly
  the profile with a negative upper edge, and `max(xr, limit)` then fills it with water. It has been in every version
  since v3.0.0 (e41f020).
- **What the fix changes:** it moves UFS rain and graupel sedimentation from effectively piecewise-constant (the old
  test fell back on almost every positive cell) to piecewise-linear, which will change precipitation timing.

### WRF (`em_quarter_ss` supercell, doubly periodic, no surface fluxes, 2 h)

| run | domain (W+P change)/P | microphysics meter (WBMP, WRF dry mass)/P |
|---|---|---|
| Thompson original | +1.4 % | +1.51e-2 |
| Thompson C1–M2 + M5 | −0.12 % | −1.4e-4 (Thompson's own frame +1.7e-6) |
| + M4-WRF | −0.107 % | +1.7e-6 |
| TEMPO original | +1.11 % | — |
| TEMPO port (verified build) | −0.070 % | — |
| Kessler | −0.60 % | — |
| WSM3 (CT-L's ARL WRF microphysics), `diff_opt=2` | −0.23 % | — |

The remaining domain loss is WRF's dynamics. Variants of the Thompson + M4 run, with the domain change as a fraction
of P:

| variant | domain/P | microphysics/P |
|---|---|---|
| `diff_opt=2`, `km_opt=2` (TKE), `moist_adv_opt=1` (base) | −1.07e-3 | +1.7e-6 |
| `mix_full_fields=.false.` | −1.03e-3 | +1.7e-6 |
| `moist_adv_opt=2` (monotone) | −1.05e-3 | +1.2e-6 |
| `diff_opt=2`, `km_opt=1` (constant K) | −2.7e-5 | +1.6e-5 |
| `diff_opt=0` | −1.8e-6 | +4.4e-7 |
| `moist_adv_opt=0` (no positive-definite limiter) | +4.4e-2 | +4.5e-2 |
| `diff_opt=1`, `km_opt=4`, no PBL | +0.93 (water created) | +6.8e-3 |
| `diff_opt=1`, `km_opt=4`, `kvdif=0` | +1.2e-6 | +1.5e-6 |
| `diff_opt=1`, `km_opt=1`, `kvdif=0` | −1.1e-6 | +1.4e-6 |
| WSM3, `diff_opt=0` | −7.3e-6 | — |
| WSM3, `diff_opt=1`, `km_opt=4`, `kvdif=0` | −5.5e-7 | — |

- **W1. `horizontal_diffusion_s` (`diff_opt=2`) does not conserve mass.**
  - Each column's flux divergence is weighted by its own `g/(dnw·rdzw)` (= ρ dz per unit dη), and the coordinate-slope
    terms are not in flux form, so the domain sum does not telescope.
  - With TKE eddy diffusivity in a storm it loses 0.1 % of P; with constant K it is small. Vertical diffusion
    telescopes.
- **W2. `vertical_diffusion_mp` (`diff_opt=1` with `bl_pbl_physics=0`, qv only) creates water.**
  - It sets the surface flux equal to the first interior flux (`vflux(i,0)=vflux(i,1)`), and its 1/α weighting does
    not telescope.
  - WRF uses it only without a PBL scheme, i.e. in idealized runs. Real-data runs, including CT-L's (UW PBL), never
    reach it.
- **The real-data path conserves.** `diff_opt=1` horizontal diffusion (mass-weighted flux form) closes, and WSM3
  closes. WRF's classic Noah (CT-L's land model) cannot be tested in an ideal case and remains a gap.

**WRF verification** (em_quarter_ss, 2 h, 600 calls). Gates:
- **Meter:** reproduces both the known-bad original (+1.512e-2) and the earlier fixed result (+1.694e-6).
- **Builds:** source md5s match after configure/compile in all five, so WRF did not reset the submodules. The
  round-2 manifest fails on the original build, so the check can fail.

"host" is the per-call meter in WRF's dry mass; "scheme" uses the scheme's own density:

| run | host/P | scheme/P | domain/P |
|---|---|---|---|
| Thompson, 4 commits (mp 8) | +1.694e-6 | +1.418e-4 | −1.068e-3 |
| Thompson aerosol-aware (mp 28), original | +1.484e-2 | +1.498e-2 | +1.381e-2 |
| Thompson aerosol-aware (mp 28), 4 commits | +1.578e-6 | +1.415e-4 | −1.036e-3 |
| TEMPO (mp 88), original | +1.167e-2 | +1.181e-2 | +1.111e-2 |
| TEMPO round 2 | −1.385e-4 | +8.2e-7 | −7.22e-4 |
| TEMPO round 2 + layer mass (`WRF-tempo/`) | +8.4e-7 | +1.401e-4 | −5.81e-4 |

- **The C1/C2 completion (commit 4) is not exercised by this case.** The output is byte-identical to the 3-commit
  build: the layers are too thick for cloud Courant numbers above 1, and the rain-snow cap never binds.
- **Thompson hail-aware (mp 38)** needed its table built (`write_thompson_mp38table`). That run, and a real-data
  classic Noah case built from data already on Hercules (12 km, 12 h, GFS 0.25°), were running when the Hercules
  connection dropped. **Classic Noah closes:** Σ residual / ΣP = +8.7e-6 over 2.6M land point-steps (float32), max
  4.5e-5 kg/m² per step; the meter's control, with the canopy store left out, reads −4.75e-2, so it can fail. mp 38
  is still unread.
- **`WRF-tempo/`:**
  - a TEMPO commit (an optional `rho_dry` in `tempo_run`, on round-2 881614f);
  - two WRF commits: `phys/TEMPO` moved to the round-2 series, and `rho_dry=rho` passed to TEMPO.
  - The submodule pointers refer to local commits; they must be re-pointed once TEMPO merges the series.
  - TEMPO's `tempo_run` `.meta` table already disagrees with its Fortran interface, so `rho_dry` was not added there.

**WRF dynamics fixes** (`WRF-dynamics/`, three commits on 315a8319; built and run, with every gate pre-registered).

- **W1:** `horizontal_diffusion_s` in exact flux form. Each face flux carries its own face depth and length. The slope
  terms become differences of w-level fluxes. Where layer depth does not vary horizontally the tendencies are unchanged.
- **W2:** `vertical_diffusion_mp` (qv) and the `'m'` branch of `vertical_diffusion` (all other species, scalars, chem,
  tracers). No flux through the ground (`vflux(0)=0`), and a mass flux that telescopes.
- **W3:** the same defect in `vertical_diffusion_3dmp` (theta), in its own commit. **Keeping it is a decision:** it
  changes the cold pool of the no-PBL idealized storm substantially (θ′ rms 2.06 → 1.60 K, P 2.78 → 2.19).

Offline, the old operators are out of balance by 7.0e-3 (W1) and −0.10 (W2) of Σ|T|, the new ones by 3e-17 and 2e-18.
In the supercell, "dyn" is the domain residual minus the microphysics meter, as a fraction of P:

| case | dyn, before | dyn, after | domain total after | microphysics after |
|---|---|---|---|---|
| `diff_opt=2`, `km_opt=2` | −1.07e-3 | +9.8e-6 | +1.16e-5 | +1.8e-6 |
| `diff_opt=2`, `km_opt=1` | −4.4e-5 | −2.3e-5 | −6.9e-6 | +1.6e-5 |
| `mix_full_fields=.false.` | −1.03e-3 | +6.1e-7 | +2.3e-6 | +1.7e-6 |
| `diff_opt=1`, `km_opt=4`, no PBL | +0.923 | −5.4e-6 | +1.66e-2 | +1.66e-2 |

- **Resolution:** WRF runs in single precision, so values near 1e-6 of P are at float32 resolution (about W/P × 6e-8).
  The microphysics rows are all positive (+4e-7 … +1.6e-5) and configuration-dependent, which looks more like a real
  small source than roundoff. The likely source is host negatives meeting Thompson's vapour floor; to be tested.
- **Unchanged where they should be:**
  - With `diff_opt=0`, with `kvdif=0` and with YSU, the fixed builds are bit-identical to the control. The comparator
    reports a difference on a changed run, so it can fail.
  - Dry mass is unchanged.
  - Storms change within the pre-registered bounds (case 1: P 4.578 → 4.580, max w 44.8 → 44.7 m/s).
- **Open:**
  - **Residuals of 1e-5 remain** in the first two cases. A diagnostic run measuring each routine's conservation per
    call in the model (job 10120179) was submitted but not read before the Hercules connection dropped. A
    periodic-halo leak is an untested hypothesis.
  - **The no-PBL case's +1.66e-2 is inside Thompson.** The hypothesis is that Thompson zeroes the negatives that
    diffusing q − qv_base produces; not yet confirmed.
  - **Not changed:** momentum vertical diffusion (`vertical_diffusion_u`/`_v`, the same ground condition, a dynamics
    choice), and the WRFPLUS tangent-linear/adjoint copies (`wrftladj/`), which now linearise the old operators.

### MPAS (supercell, `config_init_case=5`, 84×84 doubly periodic 2 km mesh, double precision, 2 h)

Water in MPAS's dry mass (ρ_zz/rdzw) plus `rainnc`; R/(P−P0) at 2 h:

| run | R/ΔP |
|---|---|
| Kessler | −6.5e-15 |
| Thompson original | +1.97e-2 |
| C1–M2 + M5 | −1.20e-4 |
| + Thompson R set to 287.0 (diagnostic only) | +2.4e-5 |
| + M4-MPAS | +3.6e-5 (1e-14 through 0:50) |
| + C1/C2 completion + M4-MPAS | +3.8e-5 (1e-14 through 0:50) |

- **What M4 removes:** the R = 287.04 vs 287.0 frame term, measured at 1.38e-4 against a prediction of 1.39e-4, and the
  0.622 term.
- **Microphysics and coupling close.** Two meters were added: one per `mp_gt_driver` call in the host's frame, and one
  around `microphysics_from_MPAS` → `mp_gt_driver` → `microphysics_to_MPAS` in MPAS's own state. With the full series
  both read ≤1e-15 kg/m² in every window. The meters leave the run bit-identical, and their precipitation equals the
  closure's.
- **v2 supercell gates** (`$R/logs/gates_v2.10120776.log`; pre-registration `mpas_run/PREREGISTRATION.txt`, v2 section):

  | case | closure max\|R\| (kg/m²) | guard / old-clip meter | pre-registered |
  |---|---|---|---|
  | monotonic dt 12, dt 8; positive-definite; Kessler (v2 and commits 1+2) | ≤1.4e-14 | ≤8e-14 per window; old clip ~1e-20 | met (E1–E4, E6) |
  | commits 1+2 at dt 8 and Kessler vs unfixed | bit-identical (20 variables) | — | met |
  | both limiters off (v2) | +0.41 | the guard's plain clip in columns without positive mass | closure fails, as expected; size 0.33–0.36 predicted, 0.41 seen |
  | unfixed monotonic / no-limiter | +6.0e-5 / +1.40 | old clip equals the closure | must fail: fails |

  The red-team matrix (decomposition, restart, dt 20, edge states; E7) failed to build because compute nodes cannot
  reach GitHub for MPAS's externals; the trees now use local clones of the same commits and are rebuilding.
- **MP1. MPAS's monotonic scalar transport creates the rest.** The domain gains +6.0e-5 kg/m² from 1:00 (+3.8e-5 of P at
  2 h). The source is the `max(0, scalar_new)` clip at the end of `atm_advance_scalars_mono_work`.
  - Metered, its water equals the closure residual at every 10-minute output, to all printed digits.
  - It binds where the vertical Courant number exceeds 1: 1.07–1.17 in Thompson's 48 m/s updrafts at dt = 12 s.
    Kessler's storm stays below 0.96, which is why Kessler closes.
  - At dt = 8 s (Courant number ≤0.78) the domain closes to ≤7e-15 for the full 2 h.
- **MP2. `atm_srk3` zeroes negative scalars before the physics** (`where (scalars_2 < 0) scalars_2 = 0`, commented "for
  now").
  - It adds nothing with the monotonic limiter on.
  - With `config_monotonic = false` it creates +1.40 kg/m² (0.7 of P), while the microphysics adds 1.3e-9.
- **Fixed (`MPAS-dynamics/`, two commits on aa6d8cd).**
  - MP1 and MP2 now zero negative values and take the same mass from the column's positive values, in proportion,
    weighted by the density the update used. MP2 also covers columns with no positive mass: it takes that mass from the
    scalar's positive mass over the domain, using one global sum per step.
  - Applies to all transported scalars.

  | run (full Thompson series) | domain R at 2 h before | after | max w before → after (m/s) | mean P at 2 h before → after (kg/m²) |
  |---|---|---|---|---|
  | monotonic, dt 12 s (MP1 binds) | +6.05e-5 | ≤1.4e-14 at every output | 48.6 → 48.7 | 1.5755 → 1.5747 |
  | `config_monotonic=.false.` (MP2 binds) | +1.40 (0.69 of P) | +3.0e-9 (Thompson's qv floor, below) | 48.5 → 50.0 | 2.0223 → 1.3586 |
  | monotonic, dt 8 s | roundoff | roundoff | 50.7 → 50.8 | 1.5753 → 1.5723 |
  | Kessler, dt 12 s | −1.4e-14 | −7e-15 | 40.0 → 40.0 | 2.1965 → 2.1965 |

  - **How much the fixer moves:** at dt 12 s it moved 5.7e-5 kg/m² within columns, none between them, and changed any
    column's moist mass by at most 0.61 %. Without the limiter, 1.38 kg/m² moved within columns and 0.334 kg/m² through
    the domain fallback. That run's precipitation falls by a third, because the old clip had been supplying 1.4 kg/m² of
    water.
  - **Not bit-for-bit neutral at dt 8 s or with Kessler.** Roundoff negatives (about 1e-20 kg/m²) that the old clip
    zeroed are now conserved, so the runs part at roundoff.
  - **Vertical substepping** (Courant number ≤1) was not implemented; it would be a larger change to MPAS's limiter.
    Rain number (a non-water scalar) changes by at most 1e-8 #/m² through the fixer.
- **Remaining, Thompson:** the final `qv = max(1e-10, …)` floor creates water when vapour arrives at exactly 0. A
  trace of the no-limiter run sums to its residual exactly (2.9129e-9 kg/m²). Not fixed.
  Possible fixes are moving negative water to vapour, or substepping the vertical transport.

### NOAA-EMC/noahmp (D, H, I, K, L), in the UFS land component

`datm_cdeps_lnd_gswp3` (data atmosphere, GSWP3 forcing, 24 h, 144 land ranks), `develop` 112b1d46 with
NOAHMP-interface 2c7b3bc. The meter (`scripts/instrument_noahmp_emc_meter.py`, diagnostic builds only) sums each soil
column's storage change minus (precipitation − canopy evaporation − transpiration − soil evaporation − runoff)·dt. The
instrumented original reproduces the regression baseline bit for bit.

| run | soil column-steps | Σ residual (mm) | Σ residual / Σ P |
|---|---|---|---|
| original 2c7b3bc | 402 552 | −1.50 (one-signed) | −5.2e-4 |
| D, H, I, K, L | 402 552 | −2.3e-9 | −8e-13 |

The losses are H and I. D, K and L change fluxes and energy, which this meter does not see.

### Noah-MP fix O (trace frozen precipitation), single-column harness

The red team's `noahmpdrv_run` harness built from each copy's own sources, with a driver variant that feeds convective
rain (`$SCR/fpice/tests/tF_fpice.py`), two days at dt = 600 s; and a unit test of `atm` (`$SCR/fpice/ut/`).

| copy | tropical conv. rain + 1e-14 mm/s grid snow: E (mm), snowpack | same column, no snow: E | cold conv. snow, 265 K: snowpack (mm) | fuzz, 24 000 calls |
|---|---|---|---|---|
| ufs/dev, GFS.v17, HAFS.v2.2, SRW v3 | 4.35, 6.6 mm → 8.94, 0 | 8.94 | 0.15 → 7.8 | water and energy closure unchanged; differences only in mixed-phase canopies (max form) |
| RRFS.v1 | 4.23, 7.1 mm → 8.91, 0 | 8.91 | 0.14 → 9.9 | same |
| NOAA-EMC/noahmp | 4.39, 5.9 mm → 8.89, 0 | 8.89 | 0.13 → 7.8 | same |
| AQM.v7 | compiled only | | | |

`atm` unit test: grid-scale-only cases bit-for-bit unchanged; rain + snow = prcp to one rounding step (4e-19 mm/s).

### Noah-MP glacier fix N, single-column harness

The red team's `noahmpdrv_run` harness (`$SCR/redteam/noahmp`), built from each branch's own driver, glacier and LSM
sources. `tG_glacier`: 5 regimes × 7 initial snow states, one day at dt = 600 s. Fuzz: 24 000 random calls (seed 7).

| copy | glacier day, Σ residual per column (mm), before → N | fuzz glacier Σ residual (mm), before → N | soil points |
|---|---|---|---|
| GFS.v17, HAFS.v2.2 (reset) | −26.2…+600 → ≤1.3e-13 per call | −1 060 → 1.1e-12 | bit-for-bit |
| RRFS.v1, SRW v3, EMC (no reset) | 0…+2.44 (the floor) → ≤1.4e-17 per call | 9e-13 → 9e-13 | bit-for-bit |
| AQM.v7 | compiled only; its driver predates the harness | | |

The RRFS and SRW runs needed D's glacier fix first: before it, the harness's evaporation read 1.2e24 mm per call.

### Production GFS.v17 (`control_p8_ugwpv1`, C96, 24 h, `water_budget_by_scheme.py`)

| window | original R_tot/P | series R_tot/P | original R_cnv/Pc | series R_cnv/Pc | original R_mp/Pls | series R_mp/Pls |
|---|---|---|---|---|---|---|
| 0–6 h | +3.94 % | +3.62 % | +0.89 % | +0.01 % | −0.09 % | −0.04 % |
| 6–12 h | +0.27 % | +0.00 % | +0.80 % | +0.01 % | −0.75 % | −0.06 % |
| 12–18 h | +0.25 % | −0.00 % | +0.75 % | −0.01 % | −0.65 % | −0.04 % |
| 18–24 h | +0.24 % | +0.00 % | +0.81 % | +0.01 % | −0.64 % | −0.07 % |

- **Series:** the 17-patch series, before the C1/C2 completion. With the completion (18 patches, `wb_v17_port2`):
  R_tot/P +3.61 / −0.00 / −0.00 / −0.00 %, R_cnv/Pc +0.01 / +0.01 / −0.01 / +0.01 %, R_mp/Pls −0.04 / −0.06 / −0.04 /
  −0.07 %, and no runtime errors.
- **0–6 h:** the +3.6 % is not spin-up. `atmf000` is written after step 1 while the window's tendencies include it,
  so R_dyn = −(step-1 physics water change). It is bookkeeping, the same in every build, and not the cold-start
  removal (0.0024 kg/m², before `atmf000`).
- **Round 3** (A′, M4 inner loop, M5 floor start; `wb_v17_port3`, `_di150`): R_tot/P +3.64 / +0.00 / +0.00 / −0.00 %
  at `dt_inner` = 720 s and +3.45 / +0.00 / +0.00 / +0.00 % at 150 s; R_cnv/Pc ±0.01 %, R_mp/Pls −0.04…−0.07 %.
- **0–6 h confirmed by the meter red team:** the step-1 physics water change (WBP, kdt 1) is −0.0244 kg/m², the 0–6 h
  R_dyn (+0.0244). Metered and unmetered develop runs are bit-identical in all 12 atmf/sfcf files.
- **Base:** `production/GFS.v17` ufs-weather-model with RTPWD `GFSv17opn_20251014`.

## Other UFS suites (C96, 24 h, ufs/dev + the series; R_tot = water budget residual, % of P)

In-model meters in diagnostic builds (answer-neutral: 60/60 output files bit-identical; they read 0 on the closed GFS
v17 p8 suite and after each fix). Proposed fixes in [`suites/`](suites/), not yet in any series; owner: the UFS series.

| suite | R_tot 6–12 / 12–18 / 18–24 h | cause | with the fix |
|---|---|---|---|
| p8_mynn, hrrr, rrfs_v1beta, rrfs_v1nssl | +2.0…+3.5 % | MYNN-EDMF `mynn_tendencies`: (A) the surface vapour, sqw and sqc sources use `rhosfc` where the flux was divided by `rho1`, and `rhosfc` has a typo (T + p608·q for T·(1 + p608·q)): +0.85 % of E; (B) the dew limiter `min(0.9*sqv-1e-8, 0)` is 0, so every downward vapour flux is zeroed in the atmosphere but booked as removed: +0.55…0.9 % of E | p8_mynn 0.00 / 0.00 / 0.00 %; hrrr, v1beta −0.03…−0.10 % (Thompson split bias); nssl −0.8…+0.2 % (NSSL microphysics, not metered) |
| control_iovr4_gfdlmpv3 | −0.30 / −0.31 / −0.33 % (R_mp −1.0 % of Pls) | GFDL MP v3 `mpdrv` converts back from mixing ratio with 1/(1+qv_new) after converting in with 1/(1−qv_in) (Thompson's B/C1 defect; v1 does it right) | 0.00 / 0.00 / 0.00 % |
| csawmg | +10.6 / +10.5 / +11.0 % (same in the original) | in convection (Chikira–Sugiyama) or its coupling; not localised | — |
| rap (GF, RUC) | −6.0 / −5.8 / −4.8 % (−9.0 … −7.2 % with the MYNN fix) | water lost outside the dtend-metered physics (R_dyn); GF's dtend booked under another process; not localised | — |
| c48 | 0.00 % (original +0.5…0.6 %) | — | — |

Run setup fixes (budget copies only): csawmg diag_table and `qdiag3d`; c48 write tasks; rap `max_output_fields`;
rrfs_v1beta compression level; rap and hrrr extended to 24 h. The same `rhosfc/rho1` factor multiplies MYNN's
sensible-heat flux and drag (energy, not fixed). Files: `upstream/suites_closure/` (Hercules), `$SCR/suites_closure/`.

## Forecast impact (red team, 24 h C96)

Original vs fixed, against a noise floor from 9 bit-perturbed initial-condition pairs. Confirmed = at least 3× the noise
maximum and coherent across related fields. Change relative to noise only: there is no skill verification and only one
start date. Files: `$SCR/redteam/impact/out/` (local), `upstream/redteam_impact/` (Hercules).

| fix | confirmed change | in the commit message? |
|---|---|---|
| M2 | land canopy evaporation −39 % (×124 noise), land latent heat −2.2 % (−0.75 W/m²), q2m −0.7 %; land points with precipitation 56 → 86 %; still −0.7 to −1.1 W/m² at day 10 | no |
| D | host latent-heat output −12 % over pure sublimation, −4.2 % over snow-covered land | contradicted "latent heat is unchanged"; reworded on every branch |
| A (first form) | lowest 5 layers +0.010 to +0.014 K, q −0.03 to −0.06 % | no |
| A′, M4 inner loop, M5 floor start (GFS.v17 port2 → port3, not separable) | precipitation −0.57 %, tropics −1.0 %, z500 −0.09 m | no |
| E | T2m land +0.033 K, q2m +0.17 %, canopy evaporation +10 % | no |
| F, G | land SWE −0.45 / +0.69 kg/m²; glacier SWE −2.85 kg/m² (F) | mechanism only |
| T1 (TEMPO) | grid-scale precipitation −5 % globally, −15 to −19 % in the tropics; rain water path +84 % | qualitative only |
| B, C3, M4, M1, H, I, J, K, M5, L, C1/C2 completion | within noise | — |

The develop-series runs (including the 10-day run) were built with the first form of deep A, not the published diff 01;
only production round 3 ran diff 01.

## Review findings and dispositions

| Series | Finding | Disposition |
|---|---|---|
| WRF/MPAS Thompson | red-team F1: quiet-path negative condensate created water via the qv floor | 07 refill and noreturn ported (all eight copies) |
| | C1/C2 lacked the amended 0003's substepping and cap | added (commit 4 in WRF, commit 3 in MPAS) |
| | messages: stale "not built or run"; M4's comparison mixed normalisations; C3 and graupel-volume wording; AI line missing | rewritten; trees unchanged |
| | M5 entry branches take negative inputs too | stated in M5's message; same as the reference |
| Production | C1/C2 stale on all five branches | completion patch added to all five |
| | AQM.v7 M4 used host constants while its Thompson keeps 287.04/0.622 | fixed (AQM patch 0018) |
| | AQM.v7 B asymmetry under `merra2_aerosol_aware` | pre-existing, number concentrations only; noted |
| | RRFS.v1/SRW v3/AQM.v7: D summed glacier canopy fluxes set to `undefined` (9.99e20) | fixed in their 0004 (found by the N harness) |
| TEMPO | early-return M5, M4 inner loop, C2 cap, C1 substepping, T1 message, frozen-fraction order, no-op M5 arguments, r1 placeholders | fixed in round 2. The r1 placeholders are fixed in flux-form sedimentation only; the frozen fraction was checked by code order |
| | red team on round 2: F1–F5 | fixed in round 3 |
| NOAA-EMC/noahmp | messages: D's history `evap`; K's "water unchanged"; H's glacier scope; land-component measurement missing; L's contradiction | rewritten; trees unchanged |
| | interface: K (and E in the UFS series) change `noahmpdrv_*` in both copies | must land in lockstep |
| UFS series (other session) | A deep: cloud-base drain independent of q(kb), heating not undone by borrowing; probable blow-up cause | relayed; A′ under test there; production A held |
| | M4 inner loop; C1 not in `pfll1` (UFS-Chem wet deposition); G with `frac_grid=false`; E coastal coefficients; F with `gcycle`; D host LH; J notes | relayed |

## Scripts

In `../../scripts/`:
- **TEMPO:** `apply_tempo_b_patch.py`; round 3: `port_tempo_scheme_v3.py`, `port_tempo_m5_v3.py`, `make_msgs_v3.py`; round 2: `port_tempo_scheme_v2.py`, `fix_tempo_semi_lagrangian_v2.py`,
  `port_tempo_m5_v2.py`, `apply_tempo_m4_patch_v2.py` (round 1: the same names without `_v2`).
- **WRF and MPAS:** `port_thompson_wrf_mpas.py`, `port_thompson_m5_wrf_mpas.py`, `port_thompson_m4_wrf.py`,
  `port_thompson_m4_mpas.py`, `port_thompson_c1c2_amend.py`.
- **Any Thompson copy, CCPP or WRF style:** `port_thompson_c1c2_amend_any.py`, `port_thompson_m4_inner_any.py`,
  `port_thompson_negr_floor_any.py`, `port_thompson_qv_floor_any.py` (07 refill), `port_thompson_m5_noreturn_any.py`.
- **NOAA-EMC/noahmp:** `port_noahmp_emc.py`, `port_noahmp_emc_k.py`.
- **Any Noah-MP glacier copy, with or without the reset:** `port_noahmp_glacier_N_any.py` (N, with its FIXMEs).
- **K's optional trailing arguments, any copy:** `port_noahmp_k_optional_any.py` (reproduces diff 15 byte for byte).
- **Any v4-style Noah-MP copy:** `port_noahmp_fpice_any.py` (O); tests in `$SCR/fpice/` (`ut/t_fpice.F90`, `tests/tF_fpice.py`).
- **Meters:** `instrument_noahmp_emc_meter.py`, `instrument_wrf_mp_meter.py`, `wrf_water_closure.py`.
- **Budget runs:** `make_wb_rundir.sh` (rt run directory to budget run).
- **Tests:** `tempo_test/` (standalone column closure; `water_closure_test_v2.F90` with the single-call cases,
  `instrument_tempo_cap.py`, `tabulate_closure.py`, `build_v2.sh`, `run_v2.sh`, `check_tempo_driver_dz.py`).
