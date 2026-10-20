# Uniform-tracer structure: which process generates it (trunif)

## Status

trunif is a diagnosis and produced no patch in the series. From an exactly uniform state, five processes create dry-ratio structure; IC processing adds a one-off.

| Generator | Class | 24 h tag rms / max | Fixed by (SERIES) |
|---|---|---|---|
| SAMF deep | a (moist transport vs dry write-back) | 1.04e-3 / 1.31e-2 | row 28 `28_DRY_03b.diff`, PC, no switch |
| SAMF shallow | a | 2.6e-4 / 5.1e-3 | row 28 |
| PBL | a | 1.8e-4 / 7.0e-3 | row 28 |
| dycore advection | c (water species limited separately) | 2.2e-5 / 1.2e-3 | row 30 `30_DYN_v6.diff`, PC, `dry_tracer_adv` F / T |
| remap | c | 5.1e-6 / 4.5e-4 | row 30 |
| IC: external_ic / adiabatic_init | d | once: max 9.0e-5 / 3.4e-4 | row 30 `dry_tracer_ic` F / F (off in the all-on run) |
| all (pt_udry) | | 1.07e-3 / 1.22e-2 | TRACKER: DRY rms 1.07e-3 → 2.3e-5; DYN max 9.8e-4 → 4.9e-13 |

- Every scheme preserves a constant in its own basis: physics ≤ 2.2e-14 per call (Courant up to 5 included), dycore ≤ 4.4e-16.
- The 216× of a moist-uniform tracer is a basis effect (class a) amplified by T1 (class b); T1 is fixed by row 27 `27_T1_02b.diff` (BF, unconditional).
- The shadow and tag runs are bit-identical to the tracer agent's `tm5`, so the meters feed back into nothing.
- Correction to `tracer/report.md` "Uniform tracers": the −0.9 %/+0.4 % after step 1 is step 1's SAMF deep (+shallow), not the IC.
- Note: "Minimal fixes" (history) and SERIES row 28 call the dry transport a PHYSICS CHANGE / PC; TRACKER lists DRY (03b) as NUM.

## Current answers

## Result: who generates dry-ratio structure
Per-call max and 24 h generated MS come from the shadow `sh_d` (`sh1_sh_analysis.txt`). The 24 h contribution is
the tag tracer that carries only that generator's increments (`tg1_TG.txt`, step 120). The sum over tags reproduces
pt_udry to rms 3.4e-5 (3 %).

| process | where (line) | class | per-call max: median / max | Σ24h MS generated | 24 h tag rms / max |
|---|---|---|---|---|---|
| SAMF deep | samfdeepcnv.f `ctr = ctr + dellae*xmb*dt2` (moist fluxes eta/etad, fixed `del`) + atmosphere.F90 write-back `q0 = delp*(1-Σq(1:nwat)) + qt` | a | 9.1e-3 / 1.1e-2 (phys k≈7, 981 hPa) | 6.5e-7 | **1.04e-3 / 1.31e-2** |
| SAMF shallow | samfshalcnv.f analogous update + write-back | a | 4.1e-3 / 6.4e-3 | 1.4e-7 | 2.6e-4 / 5.1e-3 |
| PBL | satmedmfvdifq `tridin` (K-diffusion + EDMF, moist weights) + write-back | a | 3.5e-3 / 5.2e-3 (k=1) | 1.5e-7 | 1.8e-4 / 7.0e-3 |
| dycore advection | fv_tracer2d `tracer_2d_1L` → `fv_tp_2d` (hord_tr 8) once per water species and once per tracer | c | 1.05e-4 / 1.8e-4 (≈780 hPa) | 2.0e-10 | 2.2e-5 / 1.2e-3 |
| remap | fv_mapz `mapn_tracer`/`scalar_profile` (kord_tr 9) per species, then `fillz` | c | 9.8e-5 / 1.5e-4 | 3.9e-11 | 5.1e-6 / 4.5e-4 |
| IC: external_ic | `remap_scalar`: `mappm` (kord 8, iv 0) per species + fillq/fillz | d | once: rms 2.6e-7, max 9.0e-5 | | (reset by hook) |
| IC: adiabatic_init (na_init 1) | 4 × `fv_dynamics` (fwd, bwd, bwd, fwd); q not restored | d (c inside) | once: rms 4.9e-6, max 3.4e-4 | | (reset by hook) |
| all (pt_udry) | | | | | 1.07e-3 / 1.22e-2 |

No generation (per-call max of the dry shadow): neg_adj3 0 (it only converts between phases); fv_subgrid_z 4e-16;
statein 9e-16; MP + fill_gfs + nopbl 0; write-back 5e-14; fv_update_phys 0; all gaps between metered points 0.

## Causal tests
- **Physics (SAMF deep, shallow, PBL).** The sh_v shadow carries qv_in as a passive tracer through the same call, so
  L(qv_in) is known. In every cell and step, dev_dry = (qv_in − L(qv_in))/(1 − qv_in) to ≤ 2.9e-15 (deep), 1.5e-15
  (shallow), 2.3e-14 (PBL); see column "resid".
  - So the departure is the vapour moved as a passive tracer. The scheme moves tracer c0(1−qv) with the moist-air
    fluxes, which implies the dry air moved: down where vapour went up.
  - The write-back keeps each layer's dry mass D = dp(1−qv_in), so the dycore never sees that motion while the tracer
    mass moves.
  - Nothing else contributes: no failure to preserve constants, no limiter, no positivity rescaling. tsumn/tsump never
    fire on these fields.
  - Independent check: trsamf's dry transport (fxe3) removes these terms (deep +1.51e-6 → −8.9e-11 ΔMS).
- **Dycore advection.** The tracer's own limiter is affine-invariant: A(c0(1−Σw)) = c0(1 − A(Σw)) to 7.6e-16, where sh_v
  advects Σw as one field. The whole departure is therefore Σ_i A(w_i) ≠ A(Σ_i w_i): the hord_tr 8 limiter acts on each
  water species separately.
- **Remap.** Mostly the same mechanism. A small part is not explained by it: max 5.9e-5, MS 0.1 % of the remap term. My
  candidate for that part, not verified, is the iv=0 positivity clauses in `scalar_profile` (`max(0.,q)` at local minima,
  top/bottom `a4=max(0.,…)`, `cs_limiters(...,0)`), which act on water near zero but not on the tracer.
- **IC.** SI1 is printed right after fv_restart and SI2 right after adiabatic_init. SI3, at the first dynamics call,
  equals SI2.

## Why SAMF preserves a constant (line level; the in-model test covers every column-step, so no offline replay was needed)
- **Updraft and downdraft.** For a constant c, `ecko = ((1-tem)*ecko(k-1) + tem*(ctro(k)+ctro(k-1)))/(1+tem)` gives
  ecko = c. The same holds for ecdo, and ercko = ecko.
- **dellae is in flux form.** The updraft/downdraft term `-eta(k)*ercko(k) + eta(k-1)*ecko(k-1)`, the TVD environmental
  flux divergence `flxtvd(k)-flxtvd(k-1)` (tem1 = c when ctr is constant, since phkp multiplies a zero difference), the
  cloud-base corrections at kb/jmin (SA1), the k=1 downdraft source and the cloud-top source all cancel exactly for a
  constant, whatever η is.
  - So discrete continuity of η, Courant > 1 and dp weights do not matter for a constant.
- **Positivity.** The tsumn/tsump rescaling is inactive for positive fields.
- **Chemistry path.** The itc chemistry path with fscav=0 is identical to the generic path.
- **Precipitation.** It removes water at fixed physics dp and does not touch tracer mixing ratios. Because the
  write-back keeps D and the tracer mass, the dry ratio is unchanged (measured 0 for MP + write-back).

## Uniform MOIST tracer (pt_umoist, the 216×)
- **Dycore.** Advection and remap preserve a moist-uniform field exactly (≤ 4.4e-16).
- **Physics.** In the physics basis (dry + vapour; condensate excluded) a moist-uniform field is c0(1+Σcond), not a
  constant. SAMF and the PBL transport that condensate-shaped structure: per-call max 4.7e-3 (deep), 2.4e-3 (shallow),
  4.2e-3 (PBL, for a PBL-mixed tracer). This is a basis effect (class a).
- **T1 amplifies it.** SAMF deep's explicit update at Courant up to 5 grows this structure (class b, a numerical
  defect). It does not create it: the physics-basis constant is preserved to 2.2e-15.
- **Physical part.** Moist mmr is not an invariant when water precipitates out, so part of any moist departure is
  correct physics. The invariant to test against is the dry ratio.

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| Uniform-tracer structure: which process generates it (trunif) | title | current | `report.md` (and top of `report.history.md`) |
| Status (2026-10-17, done) | dated status | superseded by Status (head) | `report.history.md` |
| Result: who generates dry-ratio structure | generator table, per-call and 24 h | current | `report.md` |
| Causal tests | shadow and limiter tests per generator | current | `report.md` |
| Why SAMF preserves a constant (line level; the in-model test covers every column-step, so no offline replay was needed) | SAMF constant preservation, line level | current | `report.md` |
| Uniform MOIST tracer (pt_umoist, the 216×) | moist-uniform tracer: basis effect plus T1 | current | `report.md` |
| Minimal fixes (none implemented here) | proposed remedies per class | superseded by SERIES rows 27, 28, 30 | `report.history.md` |
| Method | shadow tracers, reset points, tags | archival | `report.history.md` |
| Files | scripts, meter diff, results, Hercules paths | archival | `report.history.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
