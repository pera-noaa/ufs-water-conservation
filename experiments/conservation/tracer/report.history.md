*History of `report.md` (tracer), moved verbatim on 18 October 2026. The head is `report.md`.*

# Passive-tracer mass conservation in UFS (C96 control_p8_ugwpv1, 24 h, 64-bit dycore)

## Status (2026-10-17, updated after follow-ups F1–F5 — see section at the end)

24 h relative change of global tracer mass, Σ q·delp·area over total moist air, measured in the model:

| tracer (physics treatment) | base tree (tm2) | base + FV2 (tmf1) | FV2, perturbed IC (tmf2) |
|---|---|---|---|
| pt_dyn_nopbl (dynamics only) | +3.22e-15 | +2.27e-16 | +1.75e-16 |
| pt_cnv (SAMF, generic) | +3.21e-15 | +2.29e-16 | +1.70e-16 |
| pt_plume (zero over most of the globe) | +3.72e-15 | +2.07e-17 | −7.92e-17 |
| pt_umoist (uniform moist, generic) | +2.70e-15 | +2.58e-16 | +2.25e-16 |
| pt_ghg (GHG-like: SAMF chem path + PBL) | +3.16e-15 | +2.37e-16 | +1.82e-16 |
| pt_udry (uniform dry, GHG-like) | +2.72e-15 | +3.00e-16 | +2.67e-16 |
| dry air | +4.3e-17 | +5.6e-17 | +2.5e-17 |

One ulp of the global mass is 2.2e-16 (relative), so the 24 h change is 2 ulp with FV2 and 14 ulp without it.
- No term changes tracer mass beyond round-off. Every dynamics and physics term is below one ulp per step.
- The largest term is a small systematic rounding bias in the dynamics → physics conversion: 27 ulp/day. Candidate
  fix **FV2** (2 lines) removes it (patch below).
- The May drift (+7.2e-6 / 12 h) does not exist in this tree. The in-model meters show the dycore conserves
  tracer mass to below one ulp per step.
- Finding **T1**, a transport defect that conserves mass: SAMF deep convection moves tracers with Courant
  numbers up to 5. A tracer that is not PBL-mixed piles up 100–200× in the lowest layers within 24 h. It is
  reported, not fixed, because the remedy is a change to the scheme's closure.

Open: none blocking. Optional: sub-ulp dycore biases (acoustic loop, remap) were not chased further (see below).

## Setup

- Hercules root `$T = /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/tracer`.
- `$T/base` is an rsync of `$U/p20rt_final/ufs-weather-model` (develop @112b1d46 + water diffs 01–19 + 09b). It has
  no `.git`, build dirs, run dirs or exes, and `diff -rq` shows it identical to the source.
- Builds (`bin/build_full.sbatch`, `bin/build_inc.sbatch`): `compile.sh hercules "-DAPP=ATM
  -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1"`, without `-D32BIT`, so dycore and physics are both 64-bit.
  - control `base/tests/fv3_ctl64.exe` (job 10150038)
  - meters + test hook `tm/tests/fv3_tm.exe`
  - meters + hook + FV2 `tmf/tests/fv3_tmf.exe` (job 10150647)
  - `bin/retool.sh` rebuilds a tree from base with the hook, the meters and the listed fixes.
- Case (`bin/make_rundir.sh`): copied from `$U/rt/wb_m19_di720` (control_p8_ugwpv1, 2021-03-22 06Z, C96L127,
  dt 720 s, layout 3×8, 24 h). Files the script edits are copied as real files, never written through the
  template's symlinks.
  - IC: the template's `gfs_data` plus six tracers (`bin/make_ic.py`, in `$T/ic`).
  - `fscav_aero = "*:0.0"`: SAMF's chemical-tracer scavenging is a deliberate sink, so it is set to 0 for passive tracers.
- Python (`$T/bin`, local `scripts/`):
  - `analyze_tm.py --hl`: per-term table from the meters.
  - `compare_atmf.py`, `global_means.py`: run-to-run comparisons.
  - `statein_check.py`: offline replica of the conversion.
  - `perturb_ic.py`: T × (1 + 1e-7·N(0,1)).

### Which scheme touches which tracer (this tree, p8_ugwpv1, Thompson)
- **Dycore:** every `field_table` tracer (dnats = 0).
  - Advection: `tracer_2d_1L` (z_tracer, hord_tr 8, no nord_tr damping).
  - Remap: kord_tr 9, `fillz` with fill = T.
  - `fv_subgrid_z` (fv_sg_adj 1800).
  - `neg_adj3` touches water only.
- **SAMF deep/shallow:** with `trans_trac` or `satmedmf`, every tracer except the hydrometeors, number
  concentrations, cld_amt, sigma and omega (`CCPP_typedefs.F90` `gfs_interstitial_setup_tracers`, `otsptflag`).
  - Chemistry-type tracers (`"tracer_usage","chemistry"`) take SAMF's chemical path (itc > 0, wet scavenging
    with fscav) only when `trans_aero = cplchm .and. trans_trac`.
- **PBL (satmedmfvdifq):**
  - With Thompson it diffuses qv, qc, qi, qr, qs, qg, ni, nr, o3 and TKE, plus the chemistry tracers when `trans_aero`.
  - **A generic passive tracer is not PBL-mixed in this suite.**
  - `tend_opt_pbl = 2`: the PBL tendency is applied in `GFS_GWD_generic_post` (`tend_opt_gwd = 3`).
- **`fill_gfs`** in `atmosphere_state_update` receives `gq0(:,:,:)` but its dummy argument is `q(im,km)`, so it
  fills sphum only.
- **`nopbl`:** a tracer whose name contains `nopbl` has its physics changes discarded in
  `atmosphere_state_update`. This is UFS's own mechanism for case (a).

| tracer | IC | physics transport | case |
|---|---|---|---|
| pt_dyn_nopbl | structured S | none (`nopbl`) | (a) |
| pt_cnv | structured S | SAMF deep + shallow, generic path | |
| pt_plume | zero outside a box | SAMF, generic path; exercises positivity limiters and fillers | |
| pt_umoist | 1e-6 moist | SAMF, generic path | (c) |
| pt_ghg | structured S | chemistry type + test hook: SAMF chemical path + PBL, as in UFS-Chem | (b) |
| pt_udry | 1e-6·(1−Σwater) | chemistry type + test hook | (c) |

Structure field S (dimensionless; mmr = 1e-6·S), from these parts:
- 2, a constant base;
- a boundary-layer step at p/ps = 0.85 (tanh, width 0.03);
- −0.6 × a stratosphere step at a latitude-dependent tropopause (100–300 hPa);
- 0.5 sin3λ cos²φ, a horizontal wave;
- 0.4 tanh(φ/5°), an interhemispheric step;
- 1.5 min(1, Σcond/1e-4), high in clouds and precipitation;
- 0.5 min(1, qv/0.015), tied to humidity.

Its range is 5e-7 to 6e-6.

**Test hook** (`meters/01_testhook_chem_pbl_UFSATM-ccpp.diff`). This is not a fix. It sets
`trans_aero = (cplchm .or. ntchm > 0) .and. trans_trac` with the matching `nvdiff`, so chemistry tracers get the
cplchm treatment without a chemistry component. It has no effect without chemistry tracers. The meters with the
hook gave bit-identical history to the unmodified control `ctl1` for every field except the two chemistry
tracers (T, q, pt_cnv, pt_umoist: identical=True).

## Meters (`meters/02_meters_ccpp-physics.diff`, `meters/03_meters_fv3.diff`)

`tm_meter.F90` keeps Neumaier double-precision sums of q·dp·area per tracer, plus air and dry air. Rank pairs
(hi, lo) are gathered with `mpp_gather` and summed on root in PE order, so the sums are deterministic. They are
printed as (hi, lo) and read exactly, which resolves about 1e-18 of the mass.

Points:
1. start of `atmosphere_dynamics`;
2. per k_split: before `dyn_core`, after `tracer_2d_1L`, after `Lagrangian_to_Eulerian` (incl. `fillz`);
3. before and after `neg_adj3`;
4. after the p_split loop;
5. after `fv_subgrid_z`;
6. start of `atmosphere_state_update`;
7. physics frame (Σ q·(prsi(k)−prsi(k+1))·area):
   - `qgrs` in;
   - `gq0` out;
   - after `fill_gfs`;
   - after the `nopbl` override;
8. after the write-back loop;
9. after `fv_update_phys`.

Physics slots: the change applied by `GFS_DCNV_generic_post`, `GFS_SCNV_generic_post` and `GFS_GWD_generic_post`
(which applies the surface, PBL and GWD tendencies).

Extras:
- the uniform-tracer change per scheme call (`TQ`);
- the SAMF-deep Courant number (`TC`);
- min and max of the uniform tracers (`TU`).

The meters change no answers, as the bit-identity with `ctl1` above shows. The meter terms telescope exactly to
the total.

## Defects and fixes

### Finding T1 (not a mass defect; not fixed): SAMF deep convection moves tracers with Courant numbers up to 5

**Symptom.** At 24 h:
- The uniform moist tracer pt_umoist (1e-6) reaches 2.16e-4 (216×) in the lowest 2–3 model layers of the
  tropics (e.g. 133.6E 15.4S, 996 hPa), with values near 0 in the same columns.
- pt_cnv reaches 6.3e-4, 110× its initial maximum.
- The unmodified exe gives an identical pt_umoist field (`ctl1`), so this is not caused by the meters.
- Tracers the PBL also mixes stay within ~1 % of their bounds: pt_ghg max 5.05e-6, pt_udry dry ratio 0.988–1.012e-6.
- Mass is conserved; see the tables above.

**Meters** (`tm2`, `tm4`):
- Per-call relative change of the uniform tracer:
  - DCNV post: up to 5e11 (from values driven to ~0), at physics levels 1–5; 2.4 M cell-calls change by > 1 %.
  - SCNV post: up to 1.3e4; 0.3 M cell-calls.
  - PBL: 0.
- Donor-cell Courant number of SAMF deep's explicit environmental (TVD) flux,
  `xmb·dt·g/dp·|η − edto·η_d|`:
  - 3.6–5.0 at every step, always at physics level 2;
  - > 1 in 249 544 of 340 084 convective column-steps (73 %).

**Cause** (`samfdeepcnv.f`).
- `xmbmax = dp(kbcon)/(g·dt)` limits the cloud-base mass flux by the mass of the cloud-base layer only.
- The downdraft detrains into the thin near-surface layers of L127, and the single explicit update
  `ctr = ctr + dellae·xmb·dt2` is unstable there.
- A constant field would be preserved. But in the physics frame the moist-uniform tracer is c/(1 − Σcond), and
  any tracer carries some structure, so anomalies are amplified each step.
- The tsumn/tsump positivity rescaling then zeroes the negative overshoots and rescales the column, which
  conserves mass.
- Water and PBL-mixed tracers are damped by the PBL every step. Generic tracers are mixed by no other scheme
  in this suite.

**Status.** Not fixed: the fix needs sub-stepping or a CFL-respecting `xmbmax`, which changes the closure.

**Implication for UFS-Chem.** A passive tracer should be declared as a chemistry tracer with cplchm (PBL-mixed)
or it will be distorted. The generic-tracer default distorts it.

### Uniform tracers (case c)
- **Dry-uniform tracer (pt_udry, PBL-mixed).** The dry ratio spans −0.9 %/+0.4 % after step 1 (the IC is float32
  and is remapped by `external_ic`) and −1.2 %/+1.2 % at 24 h.
  - The physics mixes tracers per (dry + vapour) mass with fixed layer thickness, while the write-back keeps dry
    mass per layer. Vapour moved by the PBL or convection therefore moves "virtual dry air" that the dycore never
    sees, and a dry-uniform tracer drifts slightly.
  - This is a design property of the moist-frame physics, not a mass defect.
- **Moist-uniform tracer (pt_umoist):** see T1.

## Follow-ups (coordinator, 17 Oct evening)

Diffs (regenerated): `meters/02_meters_ccpp-physics.diff` now also carries the dry-ratio, oscillation and Courant-
histogram meters and `tm_samf_substep` (called only with `meters/04_testhook_samf_substep_ccpp-physics.diff`);
`meters/03_meters_fv3.diff` includes the uniform-reset test hook. FV2 is unchanged and also applies on top of
`$U/cons/energy/fx` (base + FX1 SG1 CP1; dry-run, offset +2 lines). FV2 is a BUG FIX (restores the round trip the code
intends).

### F2. Dry-mole-fraction consistency of pt_udry, per process
(a) Test hook `testhook_uniform_reset.py` sets pt_udry = 1e-6·(1−Σwater) and pt_umoist = 1e-6 exactly at the first
`atmosphere_dynamics` call, i.e. after external_ic's remap and adiabatic init: rms dev at step 1 = 1.1e-17 (exact).
All spread below is generated by the model in 24 h.
(b) Meter (`tm_dry_dyn`, `tm_dry_phys`, `tm_dry_slot`): dev = c_dry/c0 − 1; MS = dry-mass-weighted mean of dev².
In the physics the dry mass of a layer is the one the write-back keeps, D = dp·(1 − qv_in), so the physics points and
slots measure exactly what the dycore will see. `analyze_dry.py`, runs tm5 (base), dev1, tm6 (dt 180), tms1 (SAMF
sub-stepped):

| process (24 h Σ ΔMS) | base | develop | base dt 180 | base, SAMF deep sub-stepped |
|---|---|---|---|---|
| SAMF deep | **+1.51e-6** | +1.53e-6 | +1.39e-6 | +1.46e-6 |
| SAMF shallow | +1.6e-7 | +1.6e-7 | +1.5e-7 | +1.6e-7 |
| PBL (applied in GWD post) | −4.3e-8 | −4.5e-8 | −2.3e-8 | −2.7e-8 |
| dycore advection (dyn_core+tracer_2d) | −4.0e-7 | −4.0e-7 | −3.2e-7 | −3.8e-7 |
| remap | −7.4e-8 | −7.5e-8 | −4.1e-8 | −6.2e-8 |
| statein, write-back, fill_gfs, fv_update_phys, fv_subgrid_z | <1e-11 | <1e-11 | <1e-11 | <1e-11 |
| **rms dev at 24 h / max dev** | **1.07e-3 / 1.22e-2** | 1.08e-3 / 1.22e-2 | 1.08e-3 / 1.22e-2 | 1.07e-3 / 1.23e-2 |

(rms 1.07e-3 ≈ 0.43 ppm of 400 ppm CO2; max 1.2 % ≈ 5 ppm, in convecting columns.) The source is convection; the PBL
and the dycore reduce the spread; the hand-offs contribute nothing (<1e-11). It is independent of SA1 (develop), of
dt (Courant > 1 in 4 % instead of 73 % of column-steps) and of T1 (sub-stepped): it is not a numerical artefact.

(c) Mechanism (code): SAMF's mass fluxes (`eta`, `etad`, environmental subsidence) and satmedmfvdifq's diffusion move
**moist air**: tracers are carried per (dry+vapour) mass, `qgrs`/`gq0`, with layer masses `prsi(k)−prsi(k+1)` held
fixed. For a dry-uniform tracer q = c0(1−qv); a linear transport L with L(1) = 1 gives q' = c0(1 − L(qv)), so
c_dry' = c0(1 − L(qv))/(1 − qv) and dev = (qv − L(qv))/(1 − qv): wherever convection moves vapour up, the transport
implicitly moves dry air down, and with it tracer. `atmosphere_state_update` then keeps each layer's dry mass
`delp·(1−Σq)` — the dry air the physics implicitly moved never moves in the dycore — while the tracer mass `q0·gq0` does.
Hence a dry-uniform tracer becomes non-uniform by the passive-transport increment of qv (up to ~1e-2 in deep
convection). The PBL has the same frame error, but its mixing of c outweighs it (net −4e-8). Microphysics and surface
fluxes change qv only, which (correctly) does not change c_dry in this accounting.
(d) Consistent fix: transport tracers in the physics with **dry** mixing ratio and **dry** mass weights (SAMF:
dry mass fluxes η·(1−qv) at faces and D for layer masses; satmedmfvdifq: tridiagonal with D), converting
q ↔ c = q/(1−qv) in GFS_PBL_generic_pre/post and the convective interstitials. That keeps Σ c·D exactly
(mass-conserving) and a dry-uniform field exactly uniform. Cost: changes to two schemes' tracer solvers plus
interstitials; changes every chemistry tracer's transport by up to ~1 % (it is a PHYSICS CHANGE, not a bug fix).
The cheaper variant — transport c with the existing moist weights — breaks exact mass conservation by O(qv) unless a
fixer is added. A CAM-style dme adjustment does not help: FV3's write-back already holds dry mass and tracer mass,
which is what dme achieves; the inconsistency is inside the transport schemes. Not prototyped (not small).

### F3. T1 red team
- **Causal test** (`testhook_samf_substep.py`, build `tms`, run `tms1` 10151602, dt 720): SAMF deep's tracer update
  replaced by N = ceil(max donor Courant) sub-steps per column (dellae recomputed from the current tracer each
  sub-step; updraft/downdraft values held). 24 h pt_umoist max **216× → 4.4×** (4.39e-6); pt_cnv max 6.3e-4 → 2.3e-5;
  per-call relative change of the uniform tracer in SAMF deep max 5e11 → 0.25, cells > 1 %: 2.44 M → 491. The residual
  4.4× is SAMF shallow (not sub-stepped: max 86×, 13 870 cells > 1 %). The test version is not exactly
  mass-conserving (−2e-5/day, holding the updraft values fixed) — it is a causal test, not a fix.
- dt 180 (`tm6`): column-steps with Courant > 1 fall from 73 % to 4.2 % (max 15.6 where `xmbmax` binds); pt_umoist max
  216× → 62×, cells > 1 % per call 0.29 % → 0.007 %. Consistent dose-response.
- Courant per column-step (each column counted once per step; 340 k convective column-steps in 24 h):
  <0.5: 7 %, 0.5–1: 20 %, 1–2: 57 %, 2–3: 14 %, 3–4: 2.6 %, 4–5: 0.03 %. Max 5.0, always at physics level 2.
- SAMF's own T and qv in levels 1–6 (DCNV increments): columns with ≥ 4 sign alternations — qv 0.5 % (all runs,
  unchanged at dt 180), T 2.7 % (1.4 % at dt 180), against 14–15 % for passive tracers (4–6 % at dt 180 or
  sub-stepped). Max relative increment at k ≤ 5 per call: qv 25 %, T 2.5 %. So T and qv do not show T1's
  oscillation at a comparable level (their profiles are smooth and q1 has its own positivity rescaling); T has a weak
  Courant-dependent component (halves at dt 180). T1 is not widened beyond tracers on this evidence.

### F5. Which configurations PBL-mix a GHG (trans_aero) — and does T1 hit it
`trans_aero = cplchm .and. trans_trac` (develop, base) or `(cplchm .or. cplchp) .and. trans_trac` (UFS-Chem v1
dev-am4); only `"tracer_usage","chemistry"` tracers are added to the PBL list; `trans_trac` defaults to .true.

| configuration | chemistry coupling | GHG declared as chemistry tracer | GHG declared as generic tracer |
|---|---|---|---|
| develop, plain GFS/p8 (cplchm F) | none | not PBL-mixed → **T1** | not PBL-mixed → **T1** |
| develop GOCART (`atmaero_control_p8`: CPLCHM=T, field_table `…GOCART`) | cplchm | PBL-mixed, SAMF chem path → damped | **T1** |
| develop CATChem (`catchem_control`: CPLCHM=T, CPLCAT=T) | cplchm/cplcat | PBL-mixed → damped | **T1** |
| UFS-Chem v1 CATChem (`control_p8_ugwpv1_catchem`, workflow `skip_catchem=false`: CPLCHP=T) | cplchp | PBL-mixed → damped | **T1** |
| UFS-Chem v1 AM4 chem (`field_table_am4`: ch4, co, co2 are `chemistry`; suite `…catchem_gfdlam4` has satmedmfvdifq + samfdeepcnv) | cplchp (inferred: the workflow sets it on the CATChem path; no AM4 run namelist found) | PBL-mixed → damped | — |

"Damped" = T1's oscillation is removed each step by the PBL (pt_ghg and pt_udry stay within ~1 % of their bounds),
but the dry-ratio spread of F2 (±1.2 %) still applies to every PBL-mixed tracer.

## Incident (process)

`make_rundir.sh`'s first version wrote `field_table` through the template's symlink. Between about 13:39 and
13:49 CDT on 17 Oct, that appended test-tracer entries to the shared
`$U/rt/stmp/apera/FV3_RT/rt_3046461/control_p8_ugwpv1_intel/field_table`.
- The file was restored byte for byte from `tests/parm/field_table/field_table_thompson_noaero_tke`
  (`cmp` OK) and its mtime reset.
- The coordinator was told. The coordinator found that the jobs suspected at first (10150310/10150311) belong
  to the MPAS session and do not read that file, and asked the energy agent to check its own jobs from that window.
- The script now copies every file it edits as a real file.
