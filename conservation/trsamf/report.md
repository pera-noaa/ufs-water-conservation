# SAMF/PBL passive-tracer transport: SA1 causal check, T1 fix, dry-ratio consistency

## Status

Both transport patches are in the final series in the form trdyn and trred left them. SA1, the cause of develop's
2 %/day SAMF tracer loss, is water diff 01 in the series base, not a row.

| Patch | SERIES row | Class | Switch | 24 h, before → after |
|---|---|---|---|---|
| SA1 | base (water diff 01) | BUG FIX | — | SAMF deep pt_cnv mass −2.02e-2 → +1.6e-19 |
| T1 sub-stepping | 27 `27_T1_02b.diff` | BF | — | pt_umoist min / max (× 1e-6) 0 / 216 → 0.751 / 1.248; SAMF mass terms ≤ 5e-19 |
| DRY | 28 `28_DRY_03b.diff` | PC | none (chemistry tracers) | pt_udry rms / max 1.07e-3 / 1.22e-2 → 2.3e-5 / 1.2e-3 (DRY only, fxe3) |

- Row 27 is trdyn's `02b`: patch 02 without the donor-layer parcel start (`trsrc`), with o3 and TKE sub-stepped and
  trpw booked with eta(k)*wf(k). The donor start and the "T1 fix" column of Task 2 are not in the series.
- Row 28 is trdyn's `03b`: patch 03 rebased on 02b, changed lines identical to 03.
- Red team (`trred/`): 02 SOUND WITH CHANGES (keep sub-stepping, drop the donor start; o3/TKE sub-stepping changes
  the forecast); 03 SOUND. Restart 12+12 h and layout 4x6 = 3x8 are bit-identical.
- Without the donor start, generic tracers that the PBL does not mix keep the cloud-base dipole (0.75 / 1.25, trred).
- The uniform-field spread left after DRY is made by the FV3 dycore; trdyn (row 30) removes it.

## Current answers

## Task 1. SA1: causal confirmation and code explanation
24 h change / initial mass (develop: `dvm1`, develop + SA1 only: `sa1r`):

| term | pt_cnv | pt_plume | pt_umoist | pt_ghg | pt_udry |
|---|---|---|---|---|---|
| SAMF deep, develop | -2.02e-2 | -4.42e-2 | -1.01e-2 | +1.39e-5 | -3.0e-8 |
| SAMF deep, develop + SA1 | +1.6e-19 | -1.3e-18 | -3.0e-19 | +7.8e-20 | -1.7e-20 |
| SAMF shallow, develop | -6.7e-4 | -7.6e-4 | -2.2e-4 | -3.8e-7 | -1.3e-8 |
| SAMF shallow, develop + SA1 | -1.4e-19 | -1.1e-19 | -1.3e-21 | +5.0e-20 | -5.4e-20 |
| defect meter / slot, deep and shallow (develop) | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| deep: share from kb faces with phi=0 | 102 % | 102 % | 103 % | (sign mixed) | |
| gross cloud-base term sum xmb dt eta(kb) abs(c_kb - c_kb+1)/2 [Pa m2/day] | 2.66e12 | 4.8e11 | 6.2e11 | 8.5e9 | 7.0e7 |

**Text for the proposal (develop @112b1d46, ccpp-physics d670e19, `samfdeepcnv.f` line numbers).**

SAMF deep moves tracers in flux form except at the two faces where its parcels start. The updraft starts at kb with the
interface value ctro(kb) (interface averaging L806, `ecko(i,kb,n) = ctro(i,kb,n)` L1284) and the downdraft at jmin with
ctro(jmin) (L2193); summed over a column, the parcel exchange terms (L2371, L2441-2458, cloud top L2487) add
eta(kb)*ctro(kb) + edto*etad(jmin)*ctro(jmin) per unit cloud-base mass flux. The "double counting" subtraction (L2636-2646)
removes eta(kb)*tem1 from layer kb and edto*etad(jmin)*tem1 from layer jmin+1, where tem1 is the face value of the
compensating flux after the TVD limiter (L2603-2660: tem1 = ctr(k+1) + phi*(ctro(k) - ctr(k+1)) for subsidence, phi =
(r+|r|)/(1+|r|), r = ratio of adjacent layer differences, L2614-2627). The flux divergence telescopes and the positivity
rescaling (L3433-3480) conserves, so each convecting column with rain changes tracer mass by
dM = xmb*dt*[eta(kb)*(ctro(kb) - tem1(kb)) + edto*etad(jmin)*(ctro(jmin) - tem1(jmin))], which is nonzero wherever the
limiter is active; for subsidence ctro - tem1 = (1 - phi)*(c(kb) - c(kb+1))/2. A meter of exactly this expression equals
the in-model DCNV mass change to 6 significant digits for every tracer over 24 h; for the structured generic tracer it is
-2.25e12 Pa m2 = -2.02 % per day, 102 % of it from kb faces where phi = 0, i.e. where the tracer has a local extremum at
cloud base. SAMF shallow has the same defect at kb alone (`samfshalcnv.f`: `ecko(i,kb,n) = ctro(i,kb,n)` L1089,
`flxtvd(i,kb) = eta(i,kb)*tem1` L2047, layer kb itself never updated L2373); its meter also equals the SCNV change to 6
digits (-0.067 %/day, 99 % at phi = 0). With SA1 alone on develop both terms are at round-off.

The chemistry tracers do not take a different transport. `trans_aero` (CCPP_typedefs.F90 L1228; `itc` L1392) makes
`do_aerosols` true (L362-363), and the chemistry tracers then use the scavenging updraft (L1343-1364) and the
wet-deposition borrowing (L3497-3533) instead of L1321-1341; with fscav = 0 these are arithmetically identical
(chem_c = 0 leaves ecko unchanged, wet_dep = 0 makes the borrowing a no-op). Discarding only the PBL tendency of the two
chemistry tracers makes the structured chemistry tracer bit-identical to the generic one with the same initial field (at 6
and 24 h), with the same -2.02 %/day. The difference is the profile at cloud base: `trans_aero` also puts the chemistry
tracers into the PBL scheme (GFS_PBL_generic_pre.F90 L299-315), which mixes them every step before convection, so
c(kb) - c(kb+1) is small and smooth (phi near 1); the gross cloud-base term is 314x smaller for the PBL-mixed tracer. The
generic tracers are not PBL-mixed in this suite and SAMF deep's Courant numbers up to 5 (T1) leave sign-alternating layers
at cloud base where phi = 0, so the defect, a few per mille of the convective flux per column-step, accumulates to 2 %/day.

## Task 2. T1 fix (patch 02; deep + shallow; T, q, u, v, closure untouched)
Per convecting column, the tracer part of SAMF (interface values, updraft and downdraft tracer values incl. scavenging,
exchange terms, TVD compensating flux) is recomputed from the current tracers and applied in nsub = ceil(C/0.5) equal
sub-steps, C = max donor-cell Courant number of the compensating flux and of the parcel sources (mass fluxes, kb, jmin,
ktcon held); columns with nsub = 1 keep the original code. Tracer parcels start from the donor layer (updraft c(kb),
downdraft c(jmin+1), the layer the existing subtraction debits) instead of the interface mean, without the SA1 face
correction (conservative: the subtraction uses the same value). Shallow updates layer kb accordingly. 0.5 is the
sufficient TVD bound for the van Leer-limited flux without a (1-C) factor.

| 24 h | unfixed (fxe0) | sub-step only (fxe1; rows 2-5 fxe2) | T1 fix (fxf1; rows 2-5 fxf2) |
|---|---|---|---|
| pt_umoist min / max (x 1e-6) | 0 / 216 | 0.751 / 1.248 | 0.989 / 1.015 |
| pt_cnv, pt_plume max / mean | 287, 1136 | 3.9, 21 | 2.5, 11.9 |
| uniform tracer, cells changed > 1 % per call (deep / shallow) | 2.44 M / 0.28 M | 56 / 54 | 0 / 0 |
| SAMF mass terms, all tracers | <= 1.3e-18 | <= 5e-19 | <= 5.5e-19 |
| T, q, qc, dp, u, ps vs unfixed (fix on pt_* only: fxe2, fxf2) | | bit-identical | bit-identical |

Initial physics-frame spread of pt_umoist is 0.994/1.004 (condensate), so 0.989/1.015 is within ~1 % of its bounds.
Cost (`fxf5`, fix on 6 of 8 tracers + DRY, rank-summed wall clock): tracer block 22.8 s in SAMF deep (routine 270 s;
mean nsub 3.69 over 340 k column-steps) and 38.2 s in shallow (routine 310 s; nsub 1.40, 1.9 M column-steps incl.
DRY-only calls) = +8 % / +12 % of the schemes, 0.26 % of the forecast (23,000 rank-s). Run-to-run wall time noise
(204-297 s for identical configs) hides it.

## Task 3. Dry-ratio consistency (patch 03, on patch 02)
What "consistent" means. The write-back keeps each layer's dry mass D_k = dp_k (1 - qv0_k) (dp = prsi(k)-prsi(k+1),
qv0 = physics-step initial vapour, the `q` argument of SAMF and q1(:,:,1) in satmedmfvdifq) and the tracer mass dp_k q_k';
the dycore's dry mole fraction after physics is therefore c' = q'/(1 - qv0). A tracer transport is consistent with this
iff, written for c, (i) its layer masses are D_k and (ii) the net dry-air flux through every interface is zero (D cannot
change). Then a constant c is preserved exactly (every interface carries c0 x zero) and sum D c is conserved (flux form).
SAMF and the PBL instead move q with moist layer masses dp_k; for c = c0 that gives q' = c0 (1 - qv0 - dt L(qv0)) and
c' - c0 = -c0 dt L(qv0)/(1 - qv0): every moist exchange implies a dry-air displacement the host discards.
Implementation (chemistry tracers only): c = q/(1-qv0); every interface flux (updraft, downdraft, compensating, cloud top,
parcel-source subtractions; PBL diffusion and EDMF terms) scaled by the interface dry fraction w_k = (D-fractions of the
two layers)/2; tendencies divided by D (PBL: separate tridiagonal solve with dry masses); result returned as q = c (1-qv0).
No water variable changes (fxe3, fxf5: T, q, qc, dp, u, ps bit-identical). Exactness needs no change to water transport;
the one modelling choice is that all components crossing an interface share w_k (the environment's dry fraction): the
updraft's own dry fraction differs by (q_updraft - q_env), estimated at a few 1e-3 of the convective tracer flux (not
measured). Making each component carry its own dry fraction while keeping D fixed would unbalance the moist compensating
flux, i.e. change how water is transported; that is the part that cannot be done tracer-only.

| pt_udry dry ratio | unfixed | T1 only | DRY only | T1 + DRY |
|---|---|---|---|---|
| 24 h rms dev / max dev (fxe0 / fct1 / fxe3 / fcd1) | 1.07e-3 / 1.22e-2 | 1.07e-3 / 1.24e-2 | 2.3e-5 / 1.2e-3 | 2.3e-5 / 9.8e-4 |
| 24 h sum dMS: SAMF deep / shallow / PBL | +1.51e-6 / +1.6e-7 / -4.3e-8 | +1.43e-6 / +1.5e-7 / -1.3e-8 | -8.9e-11 / -4.3e-11 / -8.8e-10 | -1.2e-10 / -4.8e-11 / -8.6e-10 |
| exactly uniform input every step (fxf6 / fxf4): sum dMS deep / shallow / PBL | +6.3e-7 / +1.1e-7 / +1.5e-7 | | | -1e-32 / -2e-32 / 8e-30 |
| max dev after physics, uniform input | 1.0e-2 | | | 2.0e-14 |
| mass: SAMF + PBL terms | <= 3.6e-18 (tracer agent) | <= 2.4e-18 | <= 1.2e-18 | <= 7.3e-18 |

The remaining spread (rms 2.3e-5 = 0.009 ppm, max 1e-3 = 0.4 ppm of 400 ppm) is created by the dycore (generator 1).

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| # SAMF/PBL passive-tracer transport: SA1 causal check, T1 fix, dry-ratio consistency | title | current | both |
| ## Status (2026-10-17, 21:00 CDT) - tasks 1-4 done | chronological status; generators of structure for trunif | superseded by `## Status` above | `report.history.md` |
| ## Setup | Hercules trees, scripts | archival | `report.history.md` |
| ## Runs (24 h, C96L127, dt 720, 64-bit; all with hook + meters; `$W/rt/<run>`) | run list | archival | `report.history.md` |
| ## Task 1. SA1: causal confirmation and code explanation | SA1 cause, proposal text | current | `report.md` |
| ## Task 2. T1 fix (patch 02; deep + shallow; T, q, u, v, closure untouched) | sub-stepping, donor start, cost | current for sub-stepping; donor start withdrawn (trred, 02b) | `report.md` |
| ## Task 3. Dry-ratio consistency (patch 03, on patch 02) | DRY design and gates | current | `report.md` |
| ## Task 4. Impact on tracers (24 h, ppm-equivalent of a 400 ppm scaling; vs unfixed fxe0; same weather unless noted) | ppm impact, classes | superseded in part by trred (donor rows; +0.2 % cloud water not reproduced) | `report.history.md` |
| ## Open questions | five open items | superseded in part: 1 and 3 answered by trred, 4 by trdyn, 5 by samfinit | `report.history.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
