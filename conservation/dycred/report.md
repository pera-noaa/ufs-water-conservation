# dycred: red team of fv3tally's D1/D2/D3 (FV3 dissipative heating)

## Status (18 Oct 2026, done)
- **D1 CONFIRMED (BUG FIX).** Code: dyn_core recomputes pkz from the *pre-heating* pt, adds dtmp/pkz, and L2E then
  re-diagnoses T from pt at fixed delz (T_dens ∝ pt^(1/(1-cappa))), so realized dT = dtmp/(1-cappa). Offline replay on
  a real restart: dTE/heat = 1.4010 (mass mean, range 1.4000-1.4127). FV3's own fixer print, no meter: applied heat
  unfixed / bit 1 = **1.4007** at steps 1-4; 24 h D1 term **+0.2911** W m-2 (fv3tally +0.2905). Nothing downstream compensates.
- **D2 CONFIRMED (BUG FIX, second order).** The code's heat is exactly KE(u0+a) - KE(u0+2a+b) (algebra to 5e-11); the KE
  removed is KE(u0) - KE(u0+a+b); bit 16 equals it to 3e-11. Meter-free size: bit 16 raises the estimate by +2.4 to +2.7 %
  after step 2 (+5.7 % at step 1), consistent with fv3tally's 0.0195/0.725 = 2.7 %.
- **D3 CONFIRMED (BUG FIX).** Rayleigh heat goes into T, then T -> theta uses pkz from before the heating, so again
  x1/(1-kappa). Meter-free: unfixed minus bit 8 = +4.9e-4 to +8.2e-4 W m-2 per step (fv3tally +6.4e-4).
  Bit 8 vs no-Rayleigh leaves -4e-5 to -1.5e-4: the flow change Rayleigh makes. This test cannot confirm fv3tally's
  1.5e-13 closure.
- **Bits 2, 4**: real (sponge w-heat left in J/kg then divided by delp; w-heat about pre-advection w), immaterial.
- **Fix corrections** (none changes the numbers above for p8/nwat=6): see "Fix review".

## Evidence
### Code / history
- Heat block identical in full10, upstream develop (p20rt_final) and GFDL `origin/main` 8b94b9f (2026-09-21, clone in
  `$U/ufs-weather-model/UFSATM/fv3/atmos_cubed_sphere`). GFDL main stores `heat_source = dtmp !save actual K/s`, so the
  authors intend realized dT = dtmp. The dtmp/cv_air line dates from the 2017 import and has not changed since.
- The FV3 technical doc (fv3_technical_2021.tex, eq. diffhtg) says theta += L{d_con dK + dK_w}/(dp c_v p^kappa) and
  calls delt_max a K/s limit. It intends dT = dK/c_v and treats p^kappa as fixed. At fixed delz that is wrong.
- pt in the non-hydrostatic MOIST_CAPPA/USE_COND build is the density potential temperature
  T(1+zvir qv)(1-q_con)/pkz with moist cappa. The dyn_core comment "cp_air*(Virtual_Temperature/pkz)" is stale.
  heat_source is delp*J/kg (d_sw multiplies by delp), so dtmp is in K.
- Downstream: tracer_2d does not touch pt. L2E entry (kord_tm<0) computes T = pt*exp(cappa/(1-cappa)*log(rrg*delp/delz*pt)),
  which is a fresh diagnosis at fixed delz, and te_2d counts cvm*T. Nothing in nh_utils runs between the heat block and L2E.
- The hydrostatic branch heats at cp_air at fixed pressure, and its own TE counts cp_air*pt*pkz, so it is correct.
  The patch leaves it alone.

### Meter-free model test (`tools/mkcase.sh`, `runcases.sbatch`, `eng.py`; jobs 10155860, 10155861; fv3tally fx exe md5 91cd0528, -no-fma)
FV3's own `ENG Deficit` print each step (print_freq = -1). 1 h cases use na_init = 0, so every arm has the identical
state at step 1. W m-2 of TE created. Full table: `logs/eng_r1.txt`.

| quantity | step 1 | step 2 | step 3 | 24 h mean (na_init 1) |
|---|---|---|---|---|
| applied, unfixed (d_con 1 - d_con 0) | 4.0583 | 2.3752 | 1.7864 | 1.0166 |
| applied, bit 1 | 2.8974 | 1.6958 | 1.2753 | 0.7255 |
| ratio (D1 factor) | 1.4007 | 1.4007 | 1.4007 | 1.4012 |
| linearity, d_con 0.5 | 0.5000 | 0.5000 | 0.5000 | |
| bit 16 on top of bit 1 | +5.71 % | +3.22 % | +2.66 % | |
| damping-off control: d_con 0 - no damping (-KE removed + dA) | -2.9731 | | | |
| Rayleigh net, unfixed (vs tau 0) | +5.9e-4 | +5.6e-4 | +6.7e-4 | |
| Rayleigh net, bit 8 (vs tau 0) | -7.7e-5 | -1.0e-4 | -1.5e-4 | |

An independent arbiter for D1 that does not use the fix: at step 1 the damping-off run shows the damping removes about
2.97 W m-2. The unfixed code returns 4.06, which is 1.37x. Rescuing the code would need an adiabatic side effect of
about 1.1 W m-2 (37 % of KE removed). Bits 1 or 1+16 land within ±0.09 of it.

## Fix review (patches/01_fv3-dyn_te_exact.diff)
1. Bit 1 is exact (replay 1.000000) and keeps non-hydrostatic pressure consistent: p is diagnosed from pt, delp and delz.
   pkz stays pre-heating, as in the original, and L2E recomputes it. The cap now limits the realized dT at delt, which
   matches the doc's K/s meaning.
2. **Correction, generality.** The hand-rolled cvm in dyn_core.F90 and in Rayleigh_Super counts liq + rain, ice + snow +
   graupel. It omits `hailwat` (nwat = 7, e.g. NSSL suites) and differs from `moist_cv` for nwat = 2, where condensate is
   left out of cvm. In those suites the fix is not exactly "at FV3's cvm". Proposed: call `moist_cv` (fv_dynamics already
   imports it; dyn_core can use fv_mapz_mod), and in dyn_core take the condensate from the advected `q_con(i,j,k)` that
   defines pt, not from the stale q species.
3. **Correction, silent no-op.** Bits 1 and 8 compile only under MOIST_CAPPA && USE_COND && !MULTI_GASES, yet the
   non-MOIST_CAPPA branch has the same k1k bug. Proposed: `mpp_error(FATAL)` when dyn_te_exact has bits 1 or 8 set and
   these macros are absent.
4. Remaining inexactness: q at the heat block is pre-tracer_2d. fv3tally measured 1e-7 relative, which is negligible.
   The step-1 numbers show no displacement into remap or the fixer window: H0 - Hx = 0.4007·Hx to 1e-4.
5. Nesting and regional: same code path on the compute domain. Rayleigh_Super already runs for bounded domains. I saw
   no specific hazard but did not run nest or regional cases.
6. Alternative one-word D1 fix: cv_air -> cp_air in dtmp gives 1.0007 (max 1.009). It is not exact, so prefer fv3tally's form.

## Files
`tools/d1_replay.py`, `tools/d2_algebra.py`, `tools/eng.py`, `tools/mkcase.sh`, `tools/mkall1.sh`, `tools/runcases.sbatch`,
`tools/put.sh`; `logs/eng_r1.txt`, `logs/d1_replay.txt`. Hercules: `$U/cons/dycred` (runs/ outputs trimmed to logs).
