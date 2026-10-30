# 1c CP1 and FV2: WoFS forecast attribution (triage rows #3, #4)

## Status

- **Run.** One switched executable, 17 × 6-h runs per test on `regional_wofs_tempo` and `regional_wofs`: a ∈ {±1, ±2},
  FV2, a 10-member one-ulp noise ensemble and a repeat control. Build 10327902; runs 10327903/4 (`c0` only, see
  *Deviations*), 10328026/7; analysis 10328028. Dir `$U/cons/r14_1c`; scripts and JSON in `1c_wofs_scripts/`.
- **Gates.** All pass, each with its known-bad. The c0, a = +1 and fv2 arms are bitwise the develop baseline, `w_fv4` and
  `w_fv5`, so the old −0.83 % and −0.43 % are reproduced exactly and are not a build-axis artefact.
- **CP1: F does NOT pass under the pre-registered rule** (E2 passes, E3 fails). The domain-mean precipitation change scales
  with the dose of the restored term: S = −0.52 %/unit, z = −5.0, linear within noise, and both noise nulls fail. E3
  (box co-location) has no power: the noise members alone give |ρ| up to 0.38 (0.54 in `regional_wofs`).
- **FV2: F does NOT pass under the rule, narrowly.** Precipitation is inside 2σ_n on both tests (1.31σ, 0.47σ).
  `regional_wofs` 3-D T rms is 0.03565 K against a noise maximum of 0.03559 K, rank 11 of 11. A max-of-10 leg fails a pure-noise
  change 1 time in 11.
- **The old ratios were one noise draw.** σ_n is 0.33 % (`regional_wofs_tempo`) and 0.27 % (`regional_wofs`), against old
  single samples of 0.34 % and 0.18 %. The fitted CP1 effect is −0.52 ± 0.10 %, so the single −0.83 % includes about −0.3 of noise.
- **Open (Ash's call).** Does the dose response (E2) alone meet "the defect's own signal" for CP1, or is a co-location
  estimator with power needed? For FV2: rerun E4 with a larger noise ensemble, or accept rank 11/11 on one leg as noise?

| test | metric | CP1 Δ(a=+1) | CP1 slope S (z) | fit resid/σ_n | E3 ρ(a=+1) vs max\|ρ_noise\| | FV2 Δ | FV2 T rms vs noise max | σ_n |
|---|---|---|---|---|---|---|---|---|
| `regional_wofs_tempo` | `dprate%` | −0.833 % (2.56σ) | −0.518 (−5.03) | 0.62 | 0.035 vs 0.376 | −0.428 % (1.31σ) | 0.0279 vs 0.0302 K | 0.326 % |
| `regional_wofs` | `dprate%` | −0.588 % (2.18σ) | −0.398 (−4.66) | 0.69 | 0.103 vs 0.536 | −0.127 % (0.47σ) | 0.0356 vs 0.0356 K | 0.270 % |

## Pre-registration (written 2026-10-29 16:06 MDT, before any build or run)

**Question.** In `regional_wofs_tempo` (and `regional_wofs`), is the precipitation change from CP1
(`atmosphere_state_update`: physics heating applied to the new layer mass) the signal of the term it restores, and is
FV2's change (`statein`: tracers divided and multiplied by different thicknesses) within noise?

**What the old numbers are.** `pr1/attr/attr_wofs_table.txt` (rt.sh units, each = develop + one cherry-picked commit,
vs the develop baseline): `regional_wofs_tempo` CP1 (`w_fv4`, 6090bfa0) −0.833 %, FV2 (`w_fv5`, f5278b0a) −0.428 %;
`regional_wofs` −0.588 %, −0.127 %. Noise: one build (`w_noise`, t_dt × (1 + ε) in `fv_update_phys`) −0.339 %,
−0.177 %. Metric: `pr1/rt_screen.py` `dprate%`, cos-lat-weighted domain mean of `prate_ave` in `phyf006.nc`
(`fhzero` = 1, so hour 5–6 mean). Each comparison is two executables, and the noise is one sample per test.

**Noise control.** WoFS runs with `consv_te` = 0 (`input.nml`), so the `consv_te` = 0.999 control (`ctlc999`) cannot
be formed there. The WoFS analogue is the one-ulp heating perturbation used by `w_noise`, here as a 10-member ensemble
inside one executable.

**Design.** One executable (`$U/cons/r14_1c/exe/r14.exe`): develop pins from `pr1/attr/w_fv4`, `atmosphere.F90` =
the pin blob f2654b5e + `r14_patch.py`. Run-time switches, read from the environment:
- `R14_A` = a: t_dt increment × (1 + a (m_phys/δp_new − 1)). a = 0 is develop, a = 1 is CP1.
- `R14_K` = k: t_dt increment × (1 + k ε₃₂), with ε₃₂ = 1.19e-7, one ulp of the 32-bit t_dt (the `w_noise` perturbation).
- `R14_B` = 1: FV2 (both `flip_vc` branches).
- Meter (every run): per column, Σ over steps and levels of c_p ΔT_phys (m_phys − δp_new)/g, the energy CP1 removes
  (J/m²). Kept for 0–6 h, for hour 5–6 (`R14_LAST0` = 500), and at step 1 together with the heating applied.

Per test, 17 runs of 6 h, same inputs as the `rt_w_fv4` RT run (hard links). Changes to `model_configure`:
`output_fh` 6, `write_dopost` off. Runs: c0, c0r (a = 0), a ∈ {−2, −1, +1, +2}, fv2 (B = 1), noise
k ∈ {±1, …, ±5}. Every Δ is relative to c0 from the same executable, so no build-axis or `-no-fma` confound.

**Estimators** (`r14_analyze.py`, fixed now). Δ(x) = 100 (P̄_x − P̄_c0)/P̄_c0, P̄ as `dprate%`. σ_n = RMS of Δ over
the 10 noise members.
- **E1 size**: Δ(a = +1) and |Δ(a = +1)|/σ_n.
- **E2 dose response (CP1)**: S = Σ a Δ(a)/Σ a² over a ∈ {±1, ±2}; z = S/(σ_n/√10); residual r = RMS(Δ(a) − S a).
  **Pass** iff |z| ≥ 3, r ≤ 2 σ_n, and Δ(+1) and Δ(−1) have opposite signs.
- **E3 co-location (CP1)**: on 15 × 15 output-cell (45 km) boxes, ρ(x) = Pearson correlation of the box sums of the
  `prate_ave` difference (x − c0) with the box sums of c0's hour 5–6 meter. Expected sign: positive, because CP1
  removes heat where the physics heats condensate-laden layers. ρ̄_dose = mean over a ∈ {±1, ±2} of ρ(sign(a)·Δ_a).
  **Pass** iff ρ(a = +1) > max_k |ρ(noise k)| and ρ̄_dose > max_k |ρ(noise k)|.
- **E4 FV2 within noise**: |Δ(fv2)| ≤ 2 σ_n and the 3-D T rms difference (dynf006) ≤ the largest noise member's.
  FV2's own term is sub-ulp (tracer 3.07e-15 per day), so its own signal is noise-class, and passing F means
  staying inside the noise.

**Verdict rule.** CP1 F passes iff E2 and E3 both pass on `regional_wofs_tempo` (the row's test); `regional_wofs` is
reported, not gated. FV2 F passes iff E4 passes on both tests.

**Gates** (each with a known-bad):
- G0 reproducibility: c0r is bitwise c0 (`prate_ave`, `tmp`). Known-bad: n+1 and fv2 must not be bitwise c0.
- G1 consumer: the per-run max |f − 1| is 0 for c0/c0r/fv2, |k| ε₃₂ (to 1e-6) for noise, > 1e-4 for doses; every PE
  wrote its meter at step 600. Known-bad: c0 fails the dose criterion.
- G2 meter identity at step 1: e1(a) − e1(c0) = a · r1(c0) to 1e-6 of max |r1|, for a = +1 and −2. Known-bad: a = +2
  tested against 1 · r1 must fail.
- G3 estimator nulls: E2 on noise members relabelled as doses (n∓2, n∓1, n±1, n±2 → −2, −1, +1, +2; again with
  members 3, 4) must fail. E3's ρ̄ on n±1, n±2 must not exceed max |ρ| of the other six members. E4 applied to a = +2
  must fail; if it passes, E4 has no power at CP1's scale and that is reported.
- G-exe: `r14_setup` is in r14.exe and absent from the RT exe.

If a gate fails, the estimators it guards are not reported as a verdict.

## Results

Δ is the % change in domain-mean `prate_ave` (hour 5–6) against c0 from the same executable. T rms is the 3-D `tmp` rms
difference at 6 h, in K.

| run | `regional_wofs_tempo` Δ | T rms | `regional_wofs` Δ | T rms |
|---|---|---|---|---|
| c0r | 0 (bitwise) | 0 | 0 (bitwise) | 0 |
| a = −2 | +1.114 | 0.0279 | +0.921 | 0.0366 |
| a = −1 | +0.526 | 0.0291 | +0.113 | 0.0304 |
| a = +1 (CP1) | −0.833 | 0.0307 | −0.588 | 0.0311 |
| a = +2 | −0.798 | 0.0296 | −0.716 | 0.0386 |
| fv2 | −0.428 | 0.0279 | −0.127 | 0.0356 |
| noise k = +1 … +5 | +0.026, +0.172, −0.118, +0.265, −0.726 | 0.0255–0.0302 | −0.136, −0.336, −0.066, −0.220, +0.342 | 0.0271–0.0356 |
| noise k = −1 … −5 | +0.565, +0.270, +0.077, +0.128, +0.074 | | −0.342, −0.259, −0.231, −0.364, −0.241 | |

- The noise members do not centre on 0: their mean is +0.07 % (tempo) and −0.19 % (NSSL). c0 is itself one draw of the
  chaotic distribution, so every Δ carries c0's own offset. The symmetric dose design cancels that offset in S, because
  Σa = 0. It does not cancel in a single Δ(a = +1), which is why the old one-pair ratios overstate or understate.
- **E2 nulls** (noise members relabelled as doses): tempo z = −0.71 and +0.08, NSSL z = +0.06 and +0.53. All four fail, as
  they must.
- **E3**, signed ρ per dose (a = −2, −1, +1, +2): tempo −0.18, −0.22, +0.04, −0.26, so ρ̄ = −0.16, the opposite of the
  pre-registered sign. NSSL +0.37, −0.14, +0.10, +0.77, so ρ̄ = +0.27. Noise ρ spans −0.36 to +0.38 (tempo) and −0.54
  to +0.22 (NSSL). With the 0–6 h meter instead of hour 5–6 (reported, not gated), ρ(a = +1) is 0.59 and 0.24, but the noise
  members reach 0.69 and 0.51. Both meters mark the storm boxes, where any perturbation moves precipitation, so this
  estimator cannot separate the fix from noise at 45 km. The null check behaves (ρ̄ on n±1, n±2: +0.11 and −0.14).
- **E4 known-bad**: a = +2 fails E4 on both tests (|Δ| 0.80 > 0.65 and 0.72 > 0.54), so E4 can fail at CP1's scale.
- **Meter (c0, cell means, 0–6 h).**

  | test | restored term R (W/m²) | \|R\| (W/m²) | \|R\|/\|physics heating\| | R, hour 5–6 (W/m²) |
  |---|---|---|---|---|
  | tempo | −0.034 | 0.069 | 2.3e-4 | −0.0022 |
  | NSSL | −0.042 | 0.081 | 2.7e-4 | −0.011 |

  Max \|f − 1\| at a = 1 is 7.0e-3 and 7.3e-3, the condensate loading. Post hoc, not gated: the latent equivalent of the
  fitted tempo slope (0.52 % of 2.06e-6 kg m⁻² s⁻¹ × 2.5e6 J/kg) is 0.027 W/m². That is the size of the 0–6 h R but 12×
  the hour 5–6 R, so the two windows do not support a magnitude argument either way.

| gate | `regional_wofs_tempo` | `regional_wofs` | known-bad result |
|---|---|---|---|
| G-exe | `r14_setup` 2 symbols in r14.exe | — | RT exe 0: fails as required |
| G0 c0r bitwise c0 | yes | yes | n+1 and fv2 differ: yes |
| G1 consumer | c0/c0r/fv2 0; noise \|k\| × 1.192e-7 exactly; doses 7.0e-3 to 1.46e-2; 110 PE files, step 600 | same | c0 fails the dose criterion |
| G2 step-1 identity | 2.0e-13 (a = +1), 1.9e-13 (a = −2) | 2.8e-13, 2.9e-13 | a = +2 tested as 1: 1.0, fails |
| G3 nulls | E2 nulls fail; E3 null fails; E4 known-bad fails | same | — |
| Cross-check, not pre-registered | c0 = develop baseline, a = +1 = `w_fv4`, fv2 = `w_fv5`, bitwise (`prate_ave`, `tmp`) | same | — |

## Deviations from the pre-registration

- The first run jobs (10327903/4) ran only c0. `srun` read the here-string that held the run list from stdin.
  `r14_runs2.sb` ran the 16 prepared, never-run dirs with `srun < /dev/null` and skipped any dir that already had output.
  The estimators, labels and switches are unchanged, and the c0 used is the one from the first job.
- The E4 T rms leg is a max-of-10 rank test. Its false-fail rate for a pure-noise change is 1/11 per test. I set it before the
  runs and did not change it. The FV2 failure on `regional_wofs` is exactly that leg.

## Paths and cost

`$U/cons/r14_1c/`: `PREREG.md` (md5 10f9d4cc, uploaded before the build), `scripts/`, `src/atmosphere.r14.F90` +
`.diff`, `exe/r14.exe` (md5 328fde5e), `tmpl/` (hard links to the `rt_w_fv4` RT inputs), `runs/<test>/<label>/`,
`runs/r14_result_<test>.json`, `logs/`. New disk is about 37 GB: 34 runs × (726 MB RESTART + 356 MB history), plus the
2 GB tree. `cons/r14_1c/probe.bin` (50 MB of zeros) is a write test left in place, since the rules allow no deletes.
Local copies: `proposal/runs_29oct/1c_wofs_scripts/` (scripts, `runs/*.json`, `logs/`, `src/atmosphere.r14.diff`).
