*History of `report.md` (latent), moved verbatim on 18 October 2026. The head is `report.md`.*

# latent: three latent bugs (F3 SAMF scavenging booking, SAMF32 build option, TOPT tendency-option paths)

## Status (2026-10-18, done)
| bug | cause | fix (patch) | class | gate unfixed -> fixed |
|---|---|---|---|---|
| F3 | chem_pw booked with eta(k-1) (loss is eta(k)); borrowing else-branch zeroes wet_dep before adding it (mass lost); wet_dep never exported | 01a eta(k) + swap; 01b `Diag%cnv_wetdep(im,ntchm)` bucket, `cnv_wetdep_<tr>` output | 01a BUG FIX, 01b NUMERICAL CONSISTENCY (diagnostic) | 24 h (M_atm + D)/M0, fscav 0.5: -7.4e-4 -> 3.0e-15 (no-sink drift 3.2e-15); column residual/D 2e-3 (deep), 1.5e-2 (shallow) -> 6e-16, 1e-15, also with ~3500 else-branch events |
| SAMF32 | SAMF_NAMES filter searches SCHEME_FORTRAN_FILES only; mo_conv_kind/progsigma/progomega are CAPGEN_DEPENDENCIES (not CMake scoping) | 02 filter both lists + fail on partial match | BUG FIX (build) | ON: 2 -> 5 files get -real-size 32 -DSAMFCNV_USE_SP; C96 24 h runs; mass 6e-11/day (SP); OFF: flags identical, run bitwise = fx1 |
| TOPT | only an option-3 scheme applies the process-split sum; nothing guarantees one follows a 2; option 4 discards R/P/G | 03 flush pending sum at GFS_suite_interstitial_3; option 4 for pbl/gwd/rad_scaler -> CCPP error | BUG FIX | broken combos residual +110/+108/-127/-142/+0.65 W m-2 -> 2.08-3.12 (default 2.090); default bitwise |
- Not exact, with reason: TOPT combos with pbl = 1 or 3 are not within ctlc999 noise of the default (0.21 K), because
  time-split PBL is a different physics configuration; base-correct (1,3)/(3,1)/(3,3) show the same and are bitwise
  unchanged by the fix; within that family the fixed combos agree within noise. SAMF32 ON is exact only to SP round-off.
- Corrections to earlier notes: tend_opt_* ARE gfs_physics_nml entries (encnv said hard-coded); SAMF32 is not CMake
  directory scope (trred's hypothesis). Side finding: suite_FV3_HRRR_gf_nogwd never applies R and P with the default
  options (no GFS_GWD_generic_post); the TOPT flush fixes it.
- Decision for Ash: option 4 is now an error (it silently discards a tendency; for PBL the surface fluxes leave the
  surface and never reach the air). A warning would keep 4 as a deliberate switch-off.
- Integration: with trsamf 02, its trpw booking line needs the same eta(k)*wf(k) change. 01b needs a context rebase on
  all_full (D3A/encpl 06); the anchor scripts in scripts/ apply cleanly there.

Files: patches/01a_F3_samf_scavenging_booking.diff, 01b_F3_samf_wet_deposition_export.diff,
02_SAMF32_cmake_filter_dependencies.diff, 03_TOPT_process_split_sum_applied_once.diff (all `patch -p1` in
ufs-weather-model, on `$U/cons/energy/fx`); meters/01_F3_meter_samf_wetdep.diff (needs the tracer meters + trsamf TX
print), meters/02_F3_testhook_nortnp.diff (test hook). Scripts: scripts/ (fix_*.py anchor fixers, meter_f3.py,
f3_gate.py, wetdep_check.py, topt_table.py, mk_tree.sh, mkrun_e.sh, make_rundir.sh, mpar.sbatch, buildn.sbatch).
Hercules `$U/cons/latent`: trees mf0/mf3 (F3, -no-fma, metered), mf0h/mf3h (+hook), t3/mt3 (TOPT plain/metered),
s32 (SAMF32 OFF), ms32 (SAMF32 ON, metered); runs in rt/. No jobs left.

## 1. F3 — SAMF wet scavenging booking (samfdeepcnv.f and samfshalcnv.f, identical pattern in both)

### Code reading (fx = base + FX1 SG1 CP1; line numbers samfdeepcnv.f / samfshalcnv.f)
- Updraft scavenging (L1343-1365 / L1147-1168), per layer kb < k < kmax: `ercko(k) = ecko(k)` is saved *before*
  scavenging, then `ecko(k) -= c0t*dz*tem` with `tem = fscav*ecko/(1+c0t*dz)`.
- Flux form (L2445-2460 / ~1910): `dellae(k) += [-eta(k)*ercko(k) + eta(k-1)*ecko(k-1)]*g/dp` for k < ktcon, cloud top
  `dellae(ktcon) = eta(ktcon-1)*ecko(ktcon-1)*g/dp`. The interface-k flux leaves layer k with the unscavenged
  ercko(k) and enters layer k+1 with the scavenged ecko(k). Column loss = sum_{kb<k<ktcon} eta(k)*(ercko-ecko)(k)
  *xmb*dt2 = sum eta(k)*c0t*dz*tem*xmb*dt2. Scavenging computed for ktcon <= k < kmax never reaches the air (and the
  booking loop is k < ktcon, so that part is consistent).
- Booking: `chem_pw = c0t*dz*tem*eta(k-1)` -> `wet_dep = chem_pw*g*xmb*dt2` (units Pa*kg/kg; /g = kg m-2). Index
  error: eta(k-1) instead of eta(k). Ratio booked/removed = sum eta(k-1)s(k) / sum eta(k)s(k) (trred: 0.99-1.04).
- Borrowing (L3533-3553 / L2477-2495), only k in (kb, ktcon), only where `new_qtr < 0` after the column rtnp
  borrowing (which leaves negatives only in net-negative columns):
  - `wet_dep >= deficit`: `wet_dep -= deficit; q = 0` -> transfer, conserved.
  - else (base): `wet_dep = 0; q = q + wet_dep/dp` = `q + 0`. The tracer stays negative (unchanged) and the layer's
    booked deposition is erased. The scavenged mass already left the air through the flux form, so with the
    booking exported this mass is LOST (not double counted): atmosphere unchanged, deposition reduced by wet_dep(k).
    Intended (comment "borrow negative mass from wet deposition"): add wet_dep back, then zero it -> conserved.
- Deep convection's rn <= 0 reset (L3788-3815) restores new_qtr = qtr and zeroes wet_dep (k <= ktcon): consistent.
- `wet_dep` is local; nothing exports it. fscav = 0 (and generic tracers) never enter this path: chem_c = chem_pw =
  wet_dep = 0, and the else-branch adds 0 to a negative number (exact), so fixed tracers are bitwise unaffected.

## 3. TOPT — tendency-application options (tend_opt_*)

### Code
- Options (GFS_typedefs.F90 L3517-3532, namelist `gfs_physics_nml` L4236-4239, so reachable from input.nml):
  1 apply now; 2 add to the process-split sum (dtdt/dudt/dvdt/dqdt, Interstitial); 3 add and apply the sum, zero it;
  4 ignore. Defaults: rad_scaler 2, pbl 2, gwd 3, photochem/deep/shal/mp 1, sw/lwrad 4.
- The sum is zeroed by GFS_suite_interstitial_1 at the start of each physics step, filled by dcyc2t3 (radiative
  heating R, case 2), GFS_PBL_generic_post (P), GFS_GWD_generic_post (G); in this suite only an option-3 scheme
  applies it, and in the default only GFS_GWD_generic_post case 3 does. Nothing checks that a 2 is followed by a 3.
- Same structure in mynnedmf_wrapper_post (MYNN suites use it instead of GFS_PBL_generic_post).
- Side finding: suite_FV3_HRRR_gf_nogwd has dcyc2t3 and mynnedmf_wrapper_post but no GFS_GWD_generic_post, so with
  the default options R and P are never applied there (suite is not in any RT; latent). The fix below covers it.

### Map (other options at default; R = radiative heating, P = PBL, G = GWD tendencies)
| pbl \ gwd | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | base: R dropped. fixed: R at flush | base: R, G dropped. fixed: R+G at flush | OK both | base: R dropped, G ignored. fixed: stop |
| 2 | base: R, P dropped. fixed: R+P at flush | base: R, P, G dropped. fixed: all at flush | default, OK | base: R, P dropped. fixed: stop |
| 3 | OK both (R+P at PBL post) | base: G dropped. fixed: G at flush | OK both | base: G ignored. fixed: stop |
| 4 | base: P ignored, R dropped. fixed: stop | base: P ignored, R, G dropped. fixed: stop | base: P ignored. fixed: stop | fixed: stop |

### Gate setup
- Trees from base (`$U/p20rt_final`, the tracer meters' instrument_tm.py does not apply over CP1's atmosphere.F90;
  01a/01b touch no file that FX1/SG1/CP1 touch, and apply to fx with `patch -p1` cleanly, offsets only):
  `mf0` = base + -no-fma + tracer hook (chem path) + tracer meters + TX print + F3 meter; `mf3` = same + 01a + 01b.
- Case: tracer setup (6 passive tracers, `$T/ic`), C96L127, dt 720, 24 h; fscav_aero "*:0.5" (pt_ghg, pt_udry take
  the chemical path) and "*:0.0".
- Meter (meters/01_F3_meter_samf_wetdep.diff, on top of the tracer meters): per call, global sum of the scheme's own
  column change dM = sum (new_qtr - qtr)*delp*area/g, booked D = sum wet_dep*area/g, sum over columns of
  |dM_col + D_col|, borrowing-branch event counts. Global 24 h: TM meter mass (exact hi/lo sums) + sum of D.

### Gate results (24 h, f3_gate.py; relative to initial tracer mass M0 unless stated)
| quantity | unfixed (f0s5) | fixed (f3s5) | fscav = 0 (f0s0 = f3s0) |
|---|---|---|---|
| pt_ghg: (dM_atm + D_deep + D_shal)/M0 | -7.42e-4 | **+3.02e-15** | +3.21e-15 (= dM_atm, no D) |
| pt_udry: same | -4.91e-4 | **+2.64e-15** | +2.75e-15 |
| SAMF deep, global (dM+D)/D (pt_ghg / pt_udry) | +6.4e-5 / +5.2e-4 | 0 / 1.7e-16 | — |
| SAMF shallow, global (dM+D)/D | -1.51e-2 / -1.48e-2 | 0 / 0 | — |
| sum over columns abs(dM+D) / D, deep | 2.0e-3 | 6.0e-16 | — |
| same, shallow | 1.5e-2 | 9.9e-16 | — |
| D (deep + shallow) / M0, pt_ghg | 9.71e-2 | 9.79e-2 | 0 |
| borrowing events else / if | 0 / 0 | 0 / 0 | 0 / 0 |
- Fixed closes to the same 3e-15/day as a tracer with no sink (that is the dycore/coupling round-off the tracer agent
  measured without FV2). Shallow under-books by 1.5 % (eta(k-1) < eta(k) in the shallow updraft), deep by 0.006-0.05 %
  globally but 0.2 % column-by-column.
- DCNV/SCNV post applied mass change = scheme dM to <= 5e-16 (meter cross-check) in all runs.
- Export: sum over the four 6 h buckets of `cnv_wetdep_<tr>` x cell area (float32 sfcf) = meter D to -2.8e-11
  (pt_ghg) / -3.7e-11 (pt_udry); grid-file areas use R = 6371.0 km, the model 6371.2 km (a 6.28e-5 offset before
  correcting for it).
- Fixed vs unfixed, same -no-fma build pair: fscav 0: atmf012/024 (24 vars), sfcf024 (194 vars) and all 37 RESTART
  files byte-identical. fscav 0.5: also identical (incl. pt_ghg/pt_udry): with no borrowing events the fix changes
  only the booking, which no prognostic field reads.
- The borrowing branch is never reached in 24 h (the column rtnp borrowing removes the negatives first), so these runs
  cannot test it: test hook meters/02_F3_testhook_nortnp.diff (env F3_NORTNP=1 skips rtnp for chemical tracers).

## 2. SAMF32 — `-DSAMFCNV_32BIT=ON` had no effect

### Cause (from the build, not CMake scoping)
- `UFSATM/ccpp/CMakeLists.txt` L441-447 builds SAMF_FORTRAN_FILES by filtering **SCHEME_FORTRAN_FILES** (capgen
  `--scheme-files`: files that contain a CCPP scheme). mo_conv_kind.F90, progsigma_calc.f90 and progomega_calc.f90 are
  `dependencies =` of samfdeepcnv.meta / samfshalcnv.meta, so capgen reports them under `--dependencies`
  (CAPGEN_DEPENDENCIES) and the filter never sees them.
- The target fv3ccpp is created by `add_library` in the same CMakeLists.txt (L505), so directory scoping of source
  properties is not the issue (trred's hypothesis).
- trred's b32 build (`-DSAMFCNV_32BIT=ON`), fv3ccpp.dir/flags.make: `-real-size;64;-real-size;32;-DSAMFCNV_USE_SP` on
  samfdeepcnv.f and samfshalcnv.f only; mo_conv_kind.F90, progsigma_calc.f90, progomega_calc.f90 get `-real-size;64`.
  `#ifdef SAMFCNV_USE_SP` sits in mo_conv_kind.F90, so conv_wp stays kind_phys; the -real-size 32 on the two scheme
  files touches only default-kind reals, of which they have none in use (trred: bit-identical to 64-bit).
