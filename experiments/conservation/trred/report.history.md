*History of `report.md` (trred), moved verbatim on 18 October 2026. The head is `report.md`.*

# trred: red team of trsamf patches 02 (T1 sub-step + donor start) and 03 (DRY)

## Status (2026-10-17, done) - verdicts
- **02: SOUND WITH CHANGES.** Keep the sub-stepping (BUG FIX: explicit TVD update beyond its bound; o3 time-step
  error 19 % median at C>2, TKE negatives in 13 % of C>2 columns vs 1.6 % sub-stepped). Drop the donor-layer start
  (`trsrc = .false.`): (i) it is applied only where nsub > 1 (`trdo = trdry .or. nsub > 1`; 2.7 % of deep columns
  and most shallow ones keep the interface start), (ii) qv starts near the interface mean (0.28 % from it vs donor
  0.59 %, sign agreement 52 %), so donor start widens the tracer-vs-qv operator gap from 0.10 to 0.17 of the
  increment, (iii) for every PBL-mixed tracer it buys nothing: vS0 (SRC=0) pt_udry rms/max 2.355e-5/1.165e-3 vs
  2.353e-5/1.165e-3, mass terms <= 6e-19. Only non-PBL generic tracers keep the dipole (pt_umoist 0.75/1.25); if that
  class matters, apply the donor start unconditionally and declare it a tracer-only PHYSICS CHANGE.
  Declare the o3/TKE part as forecast-changing: zonal T up to 6 mK, q, o3 outside the 4-member spread (9-13/72
  cells at p<.05 vs 3.6 expected); global means inside the spread except o3 (-1.2e-6); +0.2 % cloud water not
  reproduced (+0.01 %).
- **03: SOUND.** Approximation measured: |w_up - w_env|/w_env 1.9e-3 median (max 3.2e-3) -> increment change 2.0e-3
  (max 7.7e-3); uniform-dry and mass exact either way. Scavenging: booked/removed 0.99-1.04 both unfixed and patched;
  the gap is a pre-existing index (chem_pw uses eta(k-1); eta(k)*wf(k) closes to 5e-15). 03 needs no change for
  01_DYN; with 02's `trsrc=.false.` only that context line moves. Optional separate BUG FIX: book trpw with
  eta(k)*wf(k) (and chem_pw with eta(k) in base).
- Gates: restart 12+12 h bit-identical (all but the two hook-reset uniform tracers); layout 4x6 = 3x8 bit-identical;
  FV3_GFS_v17_p8 runs and conserves (<= 2e-19); SAMFCNV_32BIT=ON is a no-op upstream (define never reaches
  mo_conv_kind.F90); with conv_wp forced to 4 both unfixed and patched run, mass terms ~1e-10/day (SP round-off),
  patched uniform max 8.1e-3/call vs 6.5e12 unfixed.
- Item 7: all identity claims here compare runs of one executable (env switches) or builds verified identical
  (dmp = dmp2 TM/TP; rstS = trsamf fcd1; s32 = g32f = fcd), so the samfinit FMA / uninitialised-read issue does not
  affect them; restart and layout gates pass. Cross-build "bitwise" claims would need -no-fma or ctlc999.
- Hercules `$U/cons/trred` (bin/, rt/, logs/, trees dmp b32 bsu f32, ic_p3..5). Local: scripts/, src/. No jobs left.

## Findings so far (code reading)
- F1: patch 02 applies the donor start only where nsub > 1 (`trdo = trdry .or. nsub > 1`); nsub = 1 columns keep
  the interface-mean start + SA1 face. The parcel-source convention therefore switches with the Courant number.
- F2: qv's interface value is NOT the arithmetic mean: samfdeepcnv L755-775 sets qo(k) = qo(k+1) + dq (saturation
  curve extrapolated half a layer down from layer k+1), and qcko(kb) = qo(kb). Tracers use ctro = (c_k + c_k+1)/2,
  u/v use the mean. So base code already starts a qv-shadow tracer differently from qv.
- F2b (sample, 31 deep columns, `scripts/item1.py`): start value minus interface mean, relative to q(kb): qv rule
  0.4 %, donor 0.9 %, opposite signs in 97 % of columns (qo(kb) - mean = -0.47 (q(kb) - mean)). One-step operators
  applied to qv, rms distance from the operator that uses qv's own interface values, relative to the base increment:
  base (mean) 0.12, donor nsub=1 0.16, patch 02 0.18. So the base tracer path already departs from qv's transport by
  12 %; patch 02 makes it 18 %.
- F4 (frozen-column iteration, same sample): exactly uniform input stays uniform under every operator (SAMF makes no
  structure from nothing, as trunif found). Any structured input - pt_umoist's condensate-basis profile OR qv's own
  profile - develops a kb/kb+1 second-difference under the interface-mean start with sub-stepping (x12 for pt_umoist,
  x23 for qv in 30 steps) because layer kb gets no updraft/compensating tendency (SA1) while kb+1 is driven by the
  mean; qv's own rule (interface = layer kb+1) gives x6 (pt_umoist x2); donor start damps (pt_umoist x0.03, qv x0.8).
- F3: SAMF wet deposition (wet_dep) is a local array, never exported; the chem_pw booking uses eta(k-1) while the
  flux-form loss uses eta(k) (pre-existing in base; patch 02 copies it, patch 03 adds wf(k-1)).

## Results (in progress, appended as they land)
### Offline replay gates (`scripts/gate.py`, dump runs dD1 = patched T1=1 SRC=1 DRY=1, dD0 = unfixed; 1498 deep columns each)
- G2: Python replay of the patch 02/03 tracer transport reproduces the model's new_qtr for o3, pt_dyn_nopbl, pt_cnv,
  pt_plume, pt_ghg (incl. fscav=0.5 scavenging) to <= 5.5e-13 of the increment (unfixed run: <= 3.7e-13 with the base
  operator). Uniform tracers to ~1e-19 absolute. G2x (parcel start flipped) misses by 2-120 % median: the gate can fail.
- G1 (qv della replay) FAILED on dD1/dD0 because qcko/qcdo are overwritten by the closure's test state after dellaq;
  dump fixed (`dump_deep2.py`, exe rr_dmp2), rerun eD1 pending.
