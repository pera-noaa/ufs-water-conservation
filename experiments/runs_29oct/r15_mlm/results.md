# #404 MLM fix: results of the pre-registered checks (PREREG.md + addendum)

**Status.** Final tree `src_fin` = WM 3d0703d2 (develop 560345cc + package 1: #405, #408, #414) + `fix_v3.diff` (= `fix_v2` + `guard5.diff`) + `index_fix_{ufsatm,ccpp-physics}.diff`. Hercules `R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/r15_mlm`.

| check | result |
|---|---|
| 1 robustness, first pass on `src_f` (rt_c 10450836) | **failed**: `control_debug_p8` Intel and GNU trap, floating invalid at `mfscuq_mlm.f` L311 (= `ufs/dev` L301, 0/0 mean) → `guard5.diff` |
| gate `src_fin` vs `src_f` `control_p8` Intel, `mlm` on | bitwise: 147 of 147 files identical (`rt_fin/.../rt_3626889/control_p8_intel` vs `rt/.../rt_3564876/control_p8_intel`) |
| 1 rerun on `src_fin`, `rt.sh -c` (10451358) | `control_p8` and `control_debug_p8`, Intel and GNU: SUCCESS, no trap |
| 1 rerun, `rt.sh -m` (10451359) | `control_p8`, `control_restart_p8`, `control_decomp_p8`, `control_2threads_p8` (Intel): SUCCESS |
| 2 forecast impact (F 10451360, G 10451361, noise 10451362–71) | every metric beyond noise (table below); pre-registered expectation (global means within noise) **wrong** |
| 3 PBL water residual | attributed: old `dtdz1` surface-flux line, replaced by package 1; on develop the PBL closes (−8.7e-14). See `trace.md` |
| 4 index fix | premise wrong (P8 indices coincide); defect reproduced with an added tracer, fix tested (`index.md`) |

## Check 2: forecast impact (`fi_analyze.py runs`, `runs/fi_result.json`)

F = `src_f` exe (md5 3fc33c32), G = `src_g` guards only (52dd51f0); namelists identical (`mlm` on, `consv_te` 1); noise = G with `consv_te` 0.999 … 0.990, nothing else differs. Global cos-lat means at 24 h. Ratio = |Δ| / rms of the 10 noise Δ.

| metric | G | Δ = F − G | max noise |Δ| | ratio |
|---|---|---|---|---|
| precipitation rate, last 6 h (kg/m²/s) | 3.21e-5 | −2.343e-7 | 5.05e-8 | 10.1 |
| precipitable water (kg/m²) | 24.41 | +0.00894 | 0.00468 | 4.3 |
| 2-m T (K) | 286.7 | +0.00377 | 0.00205 | 4.0 |
| PBL height (m) | 671.8 | −4.92 | 0.553 | 15.0 |
| low cloud (%) | 34.04 | −1.178 | 0.241 | 8.4 |
| 3-D T rms vs G (K) | | 0.174 | 0.165 | 1.06 |
| 3-D q rms vs G (kg/kg) | | 1.058e-4 | 9.79e-5 | 1.09 |

Not attributed among the fix's parts (density, layer-thickness index, smoothing). The 3-D rms is dominated by the perturbation growth (ratio ~1).

## Check 3 by-product: negative condensate (from `trace.md`, raw tables `trace/logs/table{1,2}.txt` re-read 12 Nov)

The MLM leaves −0.1361 kg/m²/day of negative water with the fix (`m_on` P09) and −0.1408 with the guards only (`g_on` P09). Thompson's entry clip (`module_mp_thompson.F90` L2267/L2294/L2334 at `ufs/dev` 7ab37e41, `else qc1d(k) = 0.0` for q ≤ R1 = 1e-12) turns the −0.1007 that reaches it into +0.1007 kg/m²/day of water, 100.9 % of the MLM-induced change in the microphysics residual. Not fixed; a one-step flux limiter in `mfscuq_mlm.f` is implied, not built.
