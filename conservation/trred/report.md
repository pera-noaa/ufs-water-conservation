# trred: red team of trsamf patches 02 (T1 sub-step + donor start) and 03 (DRY)

## Status

trred red-teamed trsamf's patches 02 (T1 sub-step + donor start) and 03 (DRY); both are in the final series in revised form.

| Patch | Verdict | Final series (SERIES) | Class | Switch |
|---|---|---|---|---|
| 02 | SOUND WITH CHANGES: keep the sub-stepping, drop the donor-layer start | row 27 `27_T1_02b.diff` (02b, donor start dropped) | BF | — |
| 03 | SOUND | row 28 `28_DRY_03b.diff` (03b, context only) | PC | none (chemistry tracers) |

| Measure | Value |
|---|---|
| o3 increment, nsub=1 vs sub-stepped, C>2: median / p90 | 0.19 / 0.27 |
| TKE, C>2, columns with negatives: nsub=1 / sub-stepped | 0.13 / 0.016 |
| pt_udry dry-ratio rms / max: interface start (vS0) vs donor start | 2.355e-5 / 1.165e-3 vs 2.353e-5 / 1.165e-3 |
| o3/TKE sub-stepping: max zonal T difference; T, q, o3 zonal cells beyond t 3.18 (3.6 of 72 expected) | 5.8 mK; 9, 11, 13 of 72 |
| 03 dry-fraction approximation: increment change rms (max) | 2.0e-3 (7.7e-3) |

- Gates: restart 12+12 h and layout 4x6 = 3x8 bit-identical (restart: all but the two hook-reset uniform tracers); FV3_GFS_v17_p8 SAMF mass terms ≤ 2e-19; replay G2 ≤ 5.5e-13 of the increment, and its known-bad (parcel start flipped) fails.
- The o3/TKE part of row 27 is a detectable forecast change; this report asks that it be declared so, while SERIES and TRACKER class row 27 BF, unconditional.
- Scavenging booking is a pre-existing index error (chem_pw uses eta(k-1)); eta(k)·wf(k) closes it to ≤ 5e-15. That fix is row 23 `23_F3_01a.diff` (BF, `latent/`).
- `-DSAMFCNV_32BIT=ON` is a no-op upstream (the define never reaches `mo_conv_kind.F90`); bears on row 25 `25_SAMF32.diff` (BF, build).
- Identity claims compare one executable or builds verified identical, so the samfinit FMA issue does not affect them.

## Current answers

### Item 6 scavenging (pt_ghg fscav 0.5; `scripts/item346.py`)
- Booked wet_dep / column mass removed by SAMF deep: median 0.999, range 0.991-1.04 (patched) vs 0.988-1.03 (unfixed).
  Same in replay; booking chem_pw with eta(k) (and wf(k)) instead of eta(k-1) (wf(k-1)) closes it to <= 5e-15 in both.
  So: pre-existing index error in the booking (samfdeepcnv chem_pw = ... eta(i,k-1)), not introduced by patch 03;
  patch 03 keeps the same closure. wet_dep is a local array (never exported) and the borrowing else-branch zeroes
  wet_dep before adding it (`wet_dep = 0; new_qtr = new_qtr + wet_dep/dp`), both pre-existing.
### Item 5 restart (fcd exe, 24 h straight with 12 h restart vs warm start at 12 h)
- RESTART at 24 h: fv_core, sfc_data, phy_data all bit-identical; fv_tracer bit-identical for 14/16 tracers incl. o3,
  TKE, pt_ghg (DRY + chem path), pt_cnv/pt_plume (T1). pt_udry/pt_umoist differ only because the trsamf test hook
  (`testhook_uniform_reset.py`) re-initialises them at the first dynamics call of every run, including a warm start.
### Item 3 offline (unfixed dump dD0, 1000 deep columns)
| tracer | cols | rms(incr nsub=1 - incr sub-stepped)/rms(incr sub-stepped) median / p90 | cols with negatives nsub=1 / sub / p02 |
|---|---|---|---|
| o3, C>2 | 185 | 0.19 / 0.27 | 0 / 0 / 0 |
| o3, C<=1 | 262 | 0.05 / 0.19 | 0 / 0 / 0 |
| TKE, C>2 | 185 | 0.38 / 0.74 | 0.13 / 0.016 / 0 |
| pt_cnv, C>2 | 185 | 1.4 / 2.7 | 0.55 / 0.21 / 0.005 |
Vertical sign changes of the o3 increment are not larger at nsub=1 (8.8 vs 9.8): o3 shows a time-step error, not an
oscillation; TKE shows non-positivity (later clipped by SAMF's borrowing).
### Gates on the fixed dump eD1 (patched, 1498 columns)
- G1 qv della replay == model dellaq to <= 3.4e-14 (PASS): the replay knows qv's transport exactly.
### Item 1/2 on 1000 real deep columns (eD1/dD1; `scripts/item1.py`, logs/item1_dD1.txt)
- Parcel start relative to the interface mean, |x - mean|/q(kb): qv's rule qo(kb) 0.28 % median (p90 1.5 %), donor
  0.59 % (1.4 %); signs agree in 52 % of columns. qv does not start from the donor layer; it starts near the mean.
- One step, operators applied to qv, rms distance from the operator with qv's own interface values (B), relative
  to the base increment: base tracer op 0.10 (p90 0.17), donor nsub=1 0.13, patch 02 0.17 (p90 0.27). The tracer
  path already departs from qv's transport in base; patch 02 widens it by ~70 %. In sub-cloud layers every tracer
  op differs from the model qv increment by ~100 % (downdraft saturation, rain evaporation): a qv-shadow tracer is
  not qv-consistent in base either.
- Deep columns with nsub = 1 (patch 02 keeps the interface start there): 2.7 %.
- Frozen-column iteration, 60 steps, 80 columns (dipole = |2nd difference across kb/kb+1|, median initial -> final):
| input | mean start sub-stepped (fxe1) | qv-rule start (interface = layer kb+1) sub-stepped | donor sub-stepped (02) | mean nsub=1 / donor nsub=1 |
|---|---|---|---|---|
| exactly uniform | 0 -> 0 (max|c-1| 4e-14) | 0 -> 0 | 0 -> 0 | 9.9e12 / 3.0e16 (C>1 blows up round-off) |
| pt_umoist (condensate-basis structure) | 1.0e-4 -> 2.6e-2 (p90 7e4) | -> 1.2e-3 | -> 1.2e-5 | 6.1 / 4.0e-4 (p90 3e8 / 1e11) |
| qv profile (normalised) | 6.2e-3 -> 2.5 (p90 1e7) | -> 0.23 (p90 6.7) | -> 3.1e-3 | 339 / 0.13 |
  Answer to trunif's question: the dipole is not generated from a uniform field by any operator; it is grown from
  existing structure by the interface-mean start (layer kb gets no updraft/compensating tendency under SA1 while
  kb+1 is driven by the kb/kb+1 mean). The same operator grows it from qv's own profile, and qv's own start rule
  also grows it (x37 vs x400): the mechanism would hit water too if the PBL did not remix the lowest layers each step.
- Real-model test with PBL mixing (vS0 = T1=2 SRC=0 DRY=1, same exe as fxf5 = SRC=1; T, q, qc, dp, u, ps
  bit-identical): pt_udry dry-ratio rms/max 2.355e-5 / 1.165e-3 vs 2.353e-5 / 1.165e-3 with donor start. pt_ghg
  differs rms 0.23, max 52 ppm-eq (the start convention is a physics choice of that size); only the non-PBL generic
  pt_umoist gets the dipole (0.749/1.250 vs 0.989/1.015). In p8 every real SAMF-transported tracer (o3, TKE,
  chemistry, nwfa/nifa when present) is also in vdftra (CCPP_typedefs otsptflag vs GFS_PBL_generic_pre).
### Item 3 noise (4 members: IC p0 + T perturbed 1e-7, seeds 3/4/5; A = o3/TKE untouched, B = as patched; atmf024)
| field | global B-A (rel) | paired t (3 dof) | zonal cells (18 lat x 4 bands) with |t| > 3.18 | max zonal |mean d| / member sd |
|---|---|---|---|---|
| T | -3.1e-4 K (-1.2e-6) | -1.6 | 9 / 72 | 5.8 mK / 0.6 mK |
| q | -1.8e-5 rel | -0.6 | 11 / 72 | 3.8e-6 / 3.6e-8 |
| clwmr | +1.1e-4 rel | +0.1 | 3 / 72 | |
| icmr | +2.9e-3 rel | +3.3 | 2 / 72 | |
| o3mr | -1.2e-6 rel | -4.6 | 13 / 72 | |
| pressfc | -0.048 Pa | -2.5 | 3 / 18 | |
  3.6 / 72 expected by chance. Global means: no field outside the spread except o3 itself (the transported field).
  The builder's +0.2 % cloud water is not reproduced (+0.01 %, t 0.06). Zonal T/q/o3 carry a small systematic signal
  (up to 6 mK) above the 24 h member spread: o3/TKE sub-stepping is a detectable forecast change, not round-off.
### Item 4 (eD1, 1000 columns, `item346.py`)
- Updraft dry fraction vs environment interface dry fraction, eta-weighted |w_up - w_env|/w_env: median 1.9e-3, p90
  2.4e-3, max 3.2e-3. Per-component dry fractions (updraft 1-qcko, downdraft 1-qrcdo, compensating flux closing the
  dry-air balance) change the chemistry-tracer SAMF increment by rms 2.0e-3 (pt_ghg; p90 4.1e-3, max 7.7e-3) of the
  patch-03 increment. Both variants conserve column mass (<= 1e-14 of gross) and keep a uniform dry ratio (1e-15).
  The builder's "a few 1e-3" holds.
### Item 5 other gates
- Layout 4x6 vs 3x8 (fcd exe): atmf024 and all RESTART files bit-identical, every tracer.
- FV3_GFS_v17_p8 (the suite of atmaero/UFS-Chem; namelist from default_vars UGWP v0): runs; SAMF deep/shallow mass
  terms <= 2e-19 of initial mass for every tracer; uniform-tracer max change per call 6.0e-3 (p8_ugwpv1: 7.2e-3).
- -DSAMFCNV_32BIT=ON: compiles, but s32 (fcd + 32-bit) and g32f are bit-identical to the 64-bit fcd run (TP lines),
  g32b to the 64-bit fxe0: the flag is a no-op in this develop. CMake puts -DSAMFCNV_USE_SP on samfdeepcnv.f /
  samfshalcnv.f only; mo_conv_kind.F90 (where `#ifdef SAMFCNV_USE_SP` selects conv_wp) gets only -real-size 64
  (build flags.make), so conv_wp = kind_phys. Pre-existing upstream build bug. Forced-SP test build rr_f32b pending.

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| trred: red team of trsamf patches 02 (T1 sub-step + donor start) and 03 (DRY) | title | current | `report.md` (and top of `report.history.md`) |
| Status (2026-10-17, done) - verdicts | dated verdicts and gates | superseded by Status (head) | `report.history.md` |
| Findings so far (code reading) | F1–F4 code reading, 31-column sample | superseded by Item 1/2 on 1000 real deep columns (eD1/dD1; `scripts/item1.py`, logs/item1_dD1.txt) and Item 6 scavenging (pt_ghg fscav 0.5; `scripts/item346.py`) | `report.history.md` |
| Results (in progress, appended as they land) | parent heading | archival | `report.history.md` |
| Offline replay gates (`scripts/gate.py`, dump runs dD1 = patched T1=1 SRC=1 DRY=1, dD0 = unfixed; 1498 deep columns each) | G2 replay gate; G1 failure on the old dump | superseded by Gates on the fixed dump eD1 (patched, 1498 columns) (G1); G2 result restated in Status | `report.history.md` |
| Item 6 scavenging (pt_ghg fscav 0.5; `scripts/item346.py`) | wet-deposition booking ratio | current | `report.md` |
| Item 5 restart (fcd exe, 24 h straight with 12 h restart vs warm start at 12 h) | restart gate | current | `report.md` |
| Item 3 offline (unfixed dump dD0, 1000 deep columns) | o3/TKE/pt_cnv error without sub-stepping | current | `report.md` |
| Gates on the fixed dump eD1 (patched, 1498 columns) | G1 qv replay PASS | current | `report.md` |
| Item 1/2 on 1000 real deep columns (eD1/dD1; `scripts/item1.py`, logs/item1_dD1.txt) | parcel start, operator distance, dipole, vS0 test | current | `report.md` |
| Item 3 noise (4 members: IC p0 + T perturbed 1e-7, seeds 3/4/5; A = o3/TKE untouched, B = as patched; atmf024) | o3/TKE forecast signal vs spread | current | `report.md` |
| Item 4 (eD1, 1000 columns, `item346.py`) | DRY dry-fraction approximation | current | `report.md` |
| Item 5 other gates | layout, p8 suite, 32-bit flag | current (its "rr_f32b pending" is answered by the forced conv_wp 4 runs in Status (2026-10-17, done) - verdicts) | `report.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
