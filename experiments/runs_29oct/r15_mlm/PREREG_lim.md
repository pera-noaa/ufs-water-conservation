# Pre-registration: MLM positivity limiter (written 2026-11-12, before any build)

> **SHELVED 12 November 2026, never built.** Whether to limit MLM condensate fluxes is left to the scheme owner in #404; rerun only if Lisa asks.

**Why.** `trace.md`: with `mlm` on, the MLM leaves −0.136 kg/m²/day of negative water (98 % cloud water), Thompson zeroes
the −0.1007 that reaches it, creating +0.1007 kg/m²/day of water. Fix v3 does not touch it.

**Change** (`apply_lim.py`, `mfscuq_mlm.f` + one argument in `satmedmfvdifq.F`):
1. `mlm_flxlim`: for qv, qc, qi, qs and ice number, each interface flux is scaled by r of the layer it leaves, r = min(1,
   available / outgoing), available = max(q1 + delt·rtg_entry, 0)·del/g, outgoing = delt·Σ ρ·max(outward flux, 0). A flux
   is scaled whole, so column sums are unchanged; no layer can export more than it holds (unit test, 2000 random columns:
   min q −3e-20 vs −0.11 unlimited; mass change / gross 7e-18).
2. Cloud-base smoothing of qv and qc: the increment is clipped so none of the three layers goes below 0. T unchanged.
Where no limit binds the arithmetic is unchanged.

**Trees** (Hercules `R=…/cons/r15_mlm`): `src_lim` = `src_fin` + `apply_lim.py` (RT, forecast); `trace/src_kL` =
`trace/src_k` (fix_v2 + probes, stages 1–3) + `apply_lim.py` (budgets).

## Tests and pass criteria
| # | test | pass |
|---|---|---|
| L1 | `kL_on` P09 (negative water after the MLM tendency, 24 h) | \|P09\| ≤ 1e-10 kg/m²/day (known-bad: `k_on` −0.136) |
| L2 | `kL_on` MLM water change P01; PBL-family residual | \|P01\| ≤ 1e-15, \|fam_pbl res\| ≤ 1e-12 (as `m_on`: 4e-20, −8.7e-14) |
| L3 | negatives entering Thompson (M02–M06), MP-family residual on − off | **target of the change:** M02–M06 ≥ −0.01 (≥ 90 % removed) and fam_mp(`kL_on`) − fam_mp(`m_off`) < 0.01 (from 0.0998). Not guaranteed: the limit uses q1, but the MLM tendency is added to the solver's result f2, so negatives can remain where diffusion lowered a layer below q1. Reported either way. |
| L4 | `mlm` off bitwise: `kL_off` vs `m_off` (`mp_compare.py bitcmp`) | 0 differences; comparator can fail: `kL_on` vs `k_on` differ |
| L5 | `rt.sh -c` on `src_lim` (c.conf: `control_p8`, `control_debug_p8`, Intel + GNU, `mlm` on), then `-m` (restart, decomp, 2 threads) | every run completes, no trap; `-m` PASS |
| L6 | forecast impact: L = `src_lim` exe vs F = `src_f` exe, `consv_te` 1, 24 h, `fi_analyze` metrics | reported, not pass/fail. Noise: the 10 `consv_te` G members (spread about G, used as the spread about F) |
Also reported: MLM gross water flux (P11) `kL_on` vs `k_on`, the share of MLM transport the limiter removes.

If L1 or L2 fails the limiter is wrong. If L3 fails, the remaining negatives are attributed with the stage-3 layer probes
before anything is posted.
