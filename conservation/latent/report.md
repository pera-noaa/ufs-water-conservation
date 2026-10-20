# latent: three latent bugs (F3 SAMF scavenging booking, SAMF32 build option, TOPT tendency-option paths)

## Status

All three bugs are fixed in the final series by four unconditional diffs.

| SERIES row | Fix | Class | Switch | 24 h, before → after |
|---|---|---|---|---|
| 23 `23_F3_01a.diff` | chem_pw booked with eta(k); else-branch adds wet_dep back | BF | — | (M_atm + D)/M0 pt_ghg, fscav 0.5: −7.42e-4 → +3.02e-15 (fx), +2.4e-16 (all_full); column residual/D deep / shallow 2.0e-3 / 1.5e-2 → 6.0e-16 / 9.9e-16 |
| 24 `24_F3_01b.diff` | `Diag%cnv_wetdep` bucket, `cnv_wetdep_<tr>` output (`_on_all_full`) | NC (diag) | — | exported vs meter 1.3e-11 / 4.8e-11 |
| 25 `25_SAMF32.diff` | cmake filter also searches CAPGEN_DEPENDENCIES | BF (build) | `-DSAMFCNV_32BIT=ON` | ON: 2 → 5 files get -real-size 32 -DSAMFCNV_USE_SP; OFF: bitwise |
| 26 `26_TOPT.diff` | pending process-split sum applied once at GFS_suite_interstitial_3; option 4 is a CCPP error | BF | — | broken combos +110/+108/-127/-142/+0.65 W m-2 → 2.08-3.12 (default 2.090, bitwise) |

- fscav 0 runs are byte-identical fixed vs unfixed; so are fscav 0.5 runs with no borrowing events.
- The borrowing branch, forced by a test hook (~3500 else-branch events), closes to 6e-16 per column.
- SAMF32 ON is exact only to single-precision round-off (tracer mass ~6e-11/day).
- TOPT combinations with pbl = 1 or 3 differ from the default by design (time-split PBL, T 0.21 K), not by defect.
- Option 4 for pbl, gwd and rad_scaler is a CCPP error, not a warning (decided; proposal §15).
- trsamf 02's trpw booking needed the same eta(k)*wf(k) change; row 27 (`02b`) carries it.

## Current answers

## 1. F3 — SAMF wet scavenging booking (samfdeepcnv.f and samfshalcnv.f, identical pattern in both)

### Existing export variable? None usable.
- `Coupling%wetdpc_flux` (`conv_wet_deposition_smoke_dust`, (im, nchem=3)) exists, but only for rrfs_sd smoke/dust,
  allocated under `rrfs_sd`, active under `do_smoke_coupling`, filled by Grell-Freitas only (cu_gf_driver), output as
  wetdpc_smoke/dust/coarsepm. Wrong species set (nchem fixed 3, not ntchm) and wrong scheme: not the right home.
- GOCART coupling (UFSATM/cpl/module_cplfields.F90): the atmosphere exports state to chemistry and imports
  inst_tracer_mass_frac + inst_tracer_diag_* only. No convective wet deposition field either way. So the SAMF-scavenged
  mass of GOCART tracers (fscav_aero) is removed from the coupled system with no deposition record anywhere.
- Minimal addition (patch 01b): `Diag%cnv_wetdep(im, ntchm)` [kg m-2], standard name
  `cumulative_convective_wet_deposition_of_chemical_tracers_in_bucket`, inout argument of samfdeepcnv and
  samfshalcnv (both add the column sum of the final wet_dep / g), zeroed in diag_phys_zero with the other buckets,
  written as `cnv_wetdep_<tracer>` (gfs_phys, 2D, per chemical tracer). Exporting it to GOCART through
  module_cplfields would be the next step on the GOCART side (not done: needs a consumer there).

## 3. TOPT — tendency-application options (tend_opt_*)

### Fix (patch 03, BUG FIX)
- GFS_suite_interstitial_3 (start, before deep convection reads the state; present in every GFS suite incl.
  HRRR_gf_nogwd) applies whatever process-split sum is still pending, once, then zeroes it. Element-wise
  `if (x /= 0)` so the default (sum already exactly 0 after GWD post case 3) touches nothing (no -0.0 sign flips).
- Option 4 for PBL (GFS_PBL_generic_post, mynnedmf_wrapper_post), GWD (GFS_GWD_generic_post) and rad_scaler (dcyc2t3)
  returns a CCPP error: "ignore" discards R, P or G and no scheme applies them; for P that also means the surface
  heat/moisture/momentum fluxes removed from land/ocean never reach the air. (A first version used `stop` in
  GFS_typedefs, the file's idiom: the 144 compute ranks stopped and the 16 write-component ranks hung until cancelled,
  so it was replaced; the CCPP error path aborts cleanly.) Decision point for Ash: a warning instead would keep 4 as a
  deliberate process switch-off.
- Not covered (noted): deep/shal/mp option 2 after the flush point, and sw/lwrad options other than 4
  (radiation_post would apply heating in the radiation group on radiation steps, on top of dcyc2t3).

### Fix (patches 01a, BUG FIX; 01b, NUMERICAL CONSISTENCY)
- 01a (booking): `chem_pw = c0t*dz*tem*eta(i,k)` in both schemes; else-branch adds `wet_dep/dp` back to the tracer
  before zeroing wet_dep. The tracer field is untouched by the booking change (chem_pw only feeds wet_dep); only the
  else-branch changes the tracer, and only for fscav > 0.
- 01b (export): see "Existing export variable?" above.
- With trsamf patch 02 (if integrated), its own booking line in `samf_tracer_transport` is the same defect and needs
  the same change: `trpw(k,n) += c0t(k)*dz*tem * eta(k-1)*wf(k-1)*rns` -> `eta(k)*wf(k)` (trred measured 5e-15
  closure with eta(k)*wf(k)); its chem_pw copy then feeds the fixed borrowing branch unchanged.

## 2. SAMF32 — `-DSAMFCNV_32BIT=ON` had no effect

### Fix (patch 02, BUG FIX, build system only)
- Filter `${SCHEME_FORTRAN_FILES} ${CAPGEN_DEPENDENCIES}`; REMOVE_DUPLICATES; configure-time FATAL_ERROR if some but
  not all of the 5 listed files are found (so a future rename cannot silently half-apply the option); STATUS line
  listing the files. OFF: the block is not entered, nothing changes.
- C3 imports and re-exports progsigma_calc but never calls it, so an SP progsigma does not break C3 builds.

### Gates
| gate | unfixed | fixed |
|---|---|---|
| ON: files with `-real-size 32 -DSAMFCNV_USE_SP` in flags.make | 2 (scheme files only) | **5** (mo_conv_kind, samfdeepcnv, samfshalcnv, progsigma_calc, progomega_calc) |
| ON: conv_wp really 4 | no (s32 = 64-bit run, trred) | yes: the tracer meter's real(8) `tm_cfl_deep(eta, etad, edto, xmb, del, dt2)` call no longer compiles (#6633 type mismatch); removed for this build (trred's rm_cfl_meter.py) |
| ON: C96 24 h run (ms32 + tracer meters) | — | completes (s32m0, s32m5) |
| ON: tracer mass 24 h, fscav 0 (pt_cnv / pt_ghg / pt_udry) | 3.3e-15 / 3.2e-15 / 2.7e-15 (64-bit) | 6.7e-11 / -6.1e-11 / -2.5e-11; per call DCNV, SCNV terms 1e-12..1e-10 (64-bit: 1e-19..1e-20) |
| OFF: flags.make vs the fx build (all 7 files, paths normalised) | — | identical |
| OFF: 24 h run vs fx1 (atmf024 18 vars, sfcf024 194 vars) | — | bitwise identical |
- SP mass error ~1e-10/day, as trred measured with conv_wp forced to 4.
- With trsamf 02/03 at 32 bit: trred's forced-SP builds of unfixed and patched (02 sub-stepping + 03 DRY) both run, with
  mass terms ~1e-10/day; patched uniform-tracer max change per call 8.1e-3 vs 6.5e12 unfixed. Their forcing edited
  mo_conv_kind.F90 only, which is what this fix enables (progsigma/progomega use conv_wp explicitly). Code reading of
  02/03: all new arithmetic is in conv_wp; the DRY write-back uses `1 - real(q, conv_wp)`, so in SP the dry-ratio
  uniformity and the F3 booking closure are limited to ~1e-7 relative (vs 1e-15), which is the SP round-off, not a defect.

### F3 borrowing branch (test hook + pt_plume made a chemistry tracer, `ft_plume_chem.py`; fscav 0.5, 24 h)
| run | borrow events else / if (deep; shallow) | wet_dep in else events / D (deep) | column sum abs(dM+D)/D deep / shallow | (dM+D)/M0 pt_plume / pt_ghg |
|---|---|---|---|---|
| hp0 unfixed + hook | 2062/470 ; 1446/43 | 3.3e-7 | 2.0e-3 / 1.5e-2 | -5.9e-4 / -7.4e-4 |
| hp3 fixed + hook | 2052/469 ; 1440/43 | 3.3e-7 | **5.9e-16 / 1.0e-15** | **+3.4e-15 / +3.0e-15** |
| hp3off fixed, no hook | 0/0 ; 847/2 | — | 5.9e-16 / 1.0e-15 | +3.4e-15 / +3.0e-15 |
- With ~3500 else-branch events, the fixed column residual stays at 6e-16, eight orders below the 3.3e-7 the base
  else-branch erases, so the gate resolves that defect too. Without any hook, a plume-shaped chemistry tracer already
  reaches the else-branch in shallow convection (847 events/day): the defect is reachable in UFS-Chem-like setups,
  but the mass at stake is small (the branch fires where the tracer and its deposition are near zero).

### TOPT gates (release builds; metered = energy meters, bitwise passive; 24 h; W m-2)
Bitwise: t3 (fixed, plain) default vs fx1 and m3 (fixed, metered) default vs mfx1: atmf024 18/18 and sfcf024 194/194
identical (release builds identical, so no FMA re-contraction). Fixed vs unfixed for the base-correct combos (1,3),
(3,1), (3,3): bitwise identical (the flush finds nothing pending). (3,1) = (3,3) bitwise.

| (pbl,gwd) | build | rad r | PBL r | GWD r | physics r | coupling | residual | f24 vs default: T rms K / ps Pa / LH W m-2 |
|---|---|---|---|---|---|---|---|---|
| (2,3) default | fixed = base | -7.66e-3 | +1.427 | -0.049 | +0.797 | +1.289 | **2.090** | 0 |
| noise: ctlc999 / c9999 vs consv_te 1 | base | | | | | | | 0.150 / 8.29 / 3.32 ; 0.149 / 8.32 / 3.30 |
| (2,1) | base | -4.2e-3 | +1.673 | -0.103 | -121.1 | -5.83 | **-126.9** | 1.77 / 244 / 519 |
| (2,1) | fixed | -7.65e-3 | +1.433 | -0.049 | +0.804 | +1.279 | **2.087** | 0.161 / 8.57 / 3.53 |
| (2,2) | base | -4.4e-3 | +8.705 | -1.816 | -136.6 | -5.86 | **-142.4** | 1.96 / 321 / 642 |
| (2,2) | fixed | -7.66e-3 | +1.426 | -0.049 | +0.797 | +1.277 | **2.078** | 0.163 / 8.69 / 3.48 |
| (1,1) | base | -5.7e-3 | +2.169 | -0.023 | +106.9 | +2.94 | **+109.8** | 1.14 / 80 / 21.5 |
| (1,1) | fixed | -7.64e-3 | +2.413 | -0.035 | +1.801 | +1.312 | **3.117** | 0.218 / 14.7 / 3.98 |
| (1,2) | base | -6.0e-3 | -0.269 | -0.910 | +104.5 | +3.01 | **+107.5** | 1.31 / 122 / 22.9 |
| (1,2) | fixed | -7.64e-3 | +2.409 | -0.035 | +1.796 | +1.303 | **3.103** | 0.218 / 14.7 / 4.12 |
| (3,2) | base | -7.9e-3 | -0.133 | -0.943 | -0.715 | +1.36 | **+0.651** | 0.90 / 98 / 11.0 |
| (3,2) | fixed | -7.65e-3 | +2.407 | -0.035 | +1.794 | +1.297 | **3.094** | 0.215 / 14.6 / 3.82 |
| (1,3) | base = fixed | -7.64e-3 | +2.408 | -0.035 | +1.794 | +1.290 | 3.087 | 0.216 / 14.6 / 3.76 |
| (3,1) = (3,3) | base = fixed | -7.64e-3 | +2.416 | -0.035 | +1.803 | +1.289 | 3.096 | 0.214 / 14.6 / 3.93 |
| (4,3) | base | -6.3e-3 | -219.0 | -0.119 | -219.2 | -7.69 | **-226.9** | 1.52 / 223 / 630 |
| (4,3), (2,4), rad_scaler 4 | fixed | CCPP error at the first physics step, clean abort in 25-112 s ("tend_opt_pbl = 4 would discard the PBL tendencies ...") | | | | | | |
- Every fixed combination closes like the default: rad r (the R1 term), coupling and the residual net of the PBL and GWD
  scheme terms (0.70-0.74 for all fixed combos, 0.712 default) are unchanged within threshold noise; the base broken
  combos are off by +105 to -230 W m-2 (dropped R, P, G).
- Within noise of the default: (2,1), (2,2) (0.161/0.163 K vs noise 0.149-0.150; ps, LH similar).
- Not within noise of the default, by design not by defect: every pbl = 1 or 3 combination, including the three that
  base already handles correctly ((1,3), (3,1), (3,3), bitwise identical before and after the fix). Applying the PBL
  tendency at once (time split) instead of jointly with GWD (process split) is a different physics configuration
  (T 0.21 K, ps 14.6 Pa) and moves the PBL scheme's own energy term from +1.43 to +2.41 W m-2 (heating +0.85).
  Within that family the fixed combos agree with the base-correct reference within noise: (1,1), (1,2) vs (1,3):
  0.158/0.160 K, 8.5/8.7 Pa, 3.4/3.6 W m-2; (3,2) vs (3,3): 0.148 K, 8.25 Pa, 3.39 W m-2; (3,3) vs (1,3) 0.153 K.
  The +1 W m-2 PBL term in time-split mode is a question for enpbl (their dspheat_ke closure was measured in the
  default process-split mode only).
- Anchor-based fixers (scripts/fix_f3.py both, fix_samf32.py, fix_topt.py) apply cleanly to energy's all_full tree
  (all accepted patches). The diffs apply to fx with `patch -p1 -F0`; on all_full, 01b's signature and end-of-routine
  hunks need a rebase (context changed by D3A's hfus argument and encpl 06), 01a/02/03 apply with offsets only.

## 4. Follow-up: 01b rebased on energy's all_full (2026-10-18)
- `patches/01b_F3_samf_wet_deposition_export_on_all_full.diff` (also `$U/cons/latent/bin/`): base = all_full + 01a
  (01a applies there with offsets only). Same +/- lines as the original 01b; only context differs (D3A's `hfus`
  argument, encpl 06 end-of-routine). Applies with `patch -p1 -F0`, no offsets. Original 01b kept.
- Gate trees (one build job): `af0` = all_full + -no-fma + chem hook + tracer meters + TX + F3 meter; `af3` = same +
  01a + 01b_on_all_full. The tracer meters needed three anchor updates for CP1/D7/encpl context in atmosphere.F90
  (`scripts/instrument_tm_af.py`; the post-nopbl probe now sits before the cpl_water_energy call, which does not touch
  tracers).
| 24 h | unfixed (a0s5) | fixed (a3s5) | fscav 0 (a0s0) |
|---|---|---|---|
| (M_atm + D)/M0 pt_ghg / pt_udry | -7.42e-4 / -4.92e-4 | **+2.4e-16 / +3.2e-16** | +2.3e-16 / +3.0e-16 (no sink) |
| column sum abs(dM+D)/D deep / shallow | 2.0e-3 / 1.5e-2 | 6.0e-16 / 9.9e-16 | — |
| exported cnv_wetdep vs meter | — | 1.3e-11 / 4.8e-11 | — |
- The floor is 2e-16 here instead of 3e-15 because all_full contains FV2 (the tracer agent's 2 ulp/day).
- fscav 0, a0s0 vs a3s0: atmf012/024 (24 vars), sfcf024 (194 vars), all 37 RESTART files byte-identical. fscav 0.5:
  RESTART also byte-identical (no borrowing events).

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| # latent: three latent bugs (F3 SAMF scavenging booking, SAMF32 build option, TOPT tendency-option paths) | title | current | both |
| ## Status (2026-10-18, done) | chronological status table, Files list | superseded by `## Status` above | `report.history.md` |
| ## 1. F3 — SAMF wet scavenging booking (samfdeepcnv.f and samfshalcnv.f, identical pattern in both) | F3 parent heading | current | both |
| ### Code reading (fx = base + FX1 SG1 CP1; line numbers samfdeepcnv.f / samfshalcnv.f) | F3 diagnosis | archival (diagnosis) | `report.history.md` |
| ### Existing export variable? None usable. | 01b export design | current | `report.md` |
| ## 3. TOPT — tendency-application options (tend_opt_*) | TOPT parent heading | current | both |
| ### Code | TOPT diagnosis | archival (diagnosis) | `report.history.md` |
| ### Map (other options at default; R = radiative heating, P = PBL, G = GWD tendencies) | which combos drop R, P, G | archival (diagnosis) | `report.history.md` |
| ### Fix (patch 03, BUG FIX) | TOPT fix | current | `report.md` |
| ### Fix (patches 01a, BUG FIX; 01b, NUMERICAL CONSISTENCY) | F3 fix | current | `report.md` |
| ### Gate setup | F3 trees, case, meter | archival | `report.history.md` |
| ### Gate results (24 h, f3_gate.py; relative to initial tracer mass M0 unless stated) | F3 gate on fx | superseded by ## 4. Follow-up: 01b rebased on energy's all_full (2026-10-18) | `report.history.md` |
| ## 2. SAMF32 — `-DSAMFCNV_32BIT=ON` had no effect | SAMF32 parent heading | current | both |
| ### Cause (from the build, not CMake scoping) | SAMF32 diagnosis | archival (diagnosis) | `report.history.md` |
| ### Fix (patch 02, BUG FIX, build system only) | SAMF32 fix | current | `report.md` |
| ### Gates | SAMF32 gates | current | `report.md` |
| ### F3 borrowing branch (test hook + pt_plume made a chemistry tracer, `ft_plume_chem.py`; fscav 0.5, 24 h) | F3 else-branch gate | current | `report.md` |
| ### TOPT gates (release builds; metered = energy meters, bitwise passive; 24 h; W m-2) | TOPT energy table | current | `report.md` |
| ## 4. Follow-up: 01b rebased on energy's all_full (2026-10-18) | 01b on all_full, F3 gate there | current | `report.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
