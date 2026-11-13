# Pre-registration: FV2 E4 rerun with a 50-member noise ensemble (written 2026-11-12, before any new run)

**Why.** In the 29 Oct test (`../1c_wofs.md`) FV2 failed E4 on `regional_wofs` by one leg: 3-D T rms 0.03565 K against a
noise maximum of 0.03559 K, rank 11 of 11. That leg is a max-of-10 rank test, which fails a pure-noise change 1 time
in 11. Ash asked for the rerun with a larger noise ensemble.

**Runs.** Same executable (`exe/r14.exe`, md5 328fde5e), same templates, same switches. 40 new noise members per test,
`R14_K` = k for k ∈ {±6, …, ±25} (labels `n+6` … `n-25`), 6 h each, prepared and run by `r14_runs3.sb` exactly as
`r14_runs2.sb` ran the originals (`srun < /dev/null`, 2 nodes each, 6 at a time). All other runs (c0, fv2, doses,
k = ±1…±5) are reused unchanged. Noise set N = 50 per test.

**Estimator E4b** (`r14_e4b.py`, fixed now). Δ and T rms as before, against the same c0.
- σ₅₀ = RMS of Δ over the 50 noise members.
- Leg 1: |Δ(fv2)| ≤ 2 σ₅₀.
- Leg 2: m = number of noise members with T rms ≥ T rms(fv2); rank p = (1 + m)/(N + 1). Pass iff p > 0.05, i.e. m ≥ 2.
  False-fail rate for an exchangeable noise-class change: 2/51 = 3.9 %.
- **FV2 passes iff E4b passes on both tests.** The original E4 (first 10 members) is recomputed and reported for
  continuity, not gated.

**Gates** (each with a known-bad):
- G0: c0 and fv2 are the 29 Oct files (unchanged); every new run rc = 0 with `phyf006.nc` and `dynf006.nc`.
- G1: every new member's max |f − 1| = |k| ε₃₂ to 1e-6 relative; all PEs wrote the meter at step 600. Known-bad: c0 fails it.
- G3 power: E4b on a = +2 must fail on both tests; if it passes, E4b has no power at CP1's scale and that is reported
  instead of a verdict.
- G3 null: leave-one-out E4b on each noise member against the other 49 (σ from the 49, pass iff m ≥ 2 of 49). The
  failing fraction is reported; above 15 % on either test means the members are not exchangeable and no verdict is given.

**Reported, not gated.** Exchangeability of the larger perturbations: medians of T rms and |Δ| for |k| ≤ 5 vs |k| ≥ 6
(Mann–Whitney p). CP1's E2 slope z recomputed with σ₅₀ (the CP1 question stays Ash's call).
