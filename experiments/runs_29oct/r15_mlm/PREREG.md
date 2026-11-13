# Pre-registration: the four open checks on the #404 MLM fix (written 2026-11-12, before any build)

Base: `meterproto/src_plain` (ufs-weather-model 3d0703d2 = develop + package 1; ccpp-physics 44defba3, where
`mfscuq_mlm.f` equals `ufs/dev` 9b65688c). Trees on Hercules `$U/cons/r15_mlm/`:
- `src_f`: + `post/issue_404_fix_v2.diff` (the posted fix + the two guards);
- `src_g`: + the two guards only (the "unfixed but does not crash" arm);
- `src_i` (later): `src_f` + the ufsatm index fix (`ntswx`, `ntincx`).
`mlm = .true.` everywhere below unless stated (namelist; RT via `parm/global_control.nml.IN` in `src_f` only).

## 1. Robustness (rt.sh on `src_f`, private baselines)
`rt.sh -c`: `control_p8` Intel and GNU, `control_debug_p8` Intel and GNU (bounds checking).
`rt.sh -m`: `control_restart_p8`, `control_decomp_p8`, `control_2threads_p8` (Intel) against that `control_p8`.
**Pass:** every test completes; debug runs raise no bounds/FPE trap; restart, decomposition and threads PASS (bitwise, as
for develop). **Known-good/bad:** the same `-m` tests on develop are PASS in the 20261028 baselines; a bounds-check
build of the *unguarded* fix (`r14_mlm` debug, 29 Oct) trapped at `b(i,0)`, so the debug build can fail.

## 2. Forecast impact (plain Intel builds, C96 `control_p8`, 24 h, gaussian output)
Arms: F = `src_f`, G = `src_g`, `consv_te` = 1. Noise: G with `consv_te` = 0.999, 0.998, …, 0.990 (N = 10).
Metrics at 24 h, global area-weighted: precipitation rate (last 6 h), precipitable water, 2-m T, PBL height, low cloud;
and 3-D rms difference from G of T and specific humidity.
**Estimator:** Δ = F − G; noise Δ_m = G_m − G. A metric is **beyond noise** iff |Δ| > max_m |Δ_m| (false rate 1/11) —
also reported as |Δ|/σ_n. **Expected:** the defect's own budget signal (+4.6e-4 kg/m² water per day, −1.26 W/m²) is far
below noise in global means, so global means within noise; the 3-D rms may exceed noise because the fix also changes the
discretisation (layer-thickness index, smoothing). Reported, not a pass/fail on the fix.

## 3. The 2.6e-9 kg/m² per day PBL water residual (fix on)
Localise with the budget-meter hook (per scheme), then probes inside `satmedmfvdifq`. Hypothesis written now: negative
values created by the MLM tendencies and clipped later (a one-signed source). **Done** when the residual is attributed to a
named statement to ≤ 1 % of itself, or the hypothesis is refuted with the probe that refutes it.

## 4. Index fix (ufsatm + `satmedmfvdifq.meta`)
`ntsw`/`ntinc` index the vertical-diffusion arrays but are full-tracer indices. P8 (Thompson, no aerosol): vdiff order
qv qc qi qr qs qg inc rnc oz, full order … ice_nc = 8, so `ntinc` = 8 picks rain number (slot 7 is ice number); `ntsw` = 5
coincides. **Pass:** `mlm` off bitwise unchanged (`control_p8`); `mlm` on: `ntincx` = 7, `ntswx` = 5 printed, answers change
(rain number no longer MLM-mixed), MLM column water/energy still closed.

## Addendum (12 Nov, before the final-tree runs)
Check 1 failed on `src_f`: `control_debug_p8` (Intel, `mlm` on) traps "floating invalid" at `mfscuq_mlm.f` L311, step 3
(`levs = mlmt − mlmb + 1` is 0 in inactive columns; also in develop). Check 4's premise was wrong (P8 indices coincide;
`index.md`). Final tree `src_fin` = `src_f` + `guard5.diff` (the mean division only where `cnvflg`; every use of the means is
under `cnvflg`) + the index fix. **Gate:** `src_fin` `control_p8` (`mlm` on, release) bitwise = `src_f`'s. Check 1 is rerun in
full on `src_fin` (`rt.sh -c` then `-m`, same confs, `dprefix` `rt_fin`). Check 2 (forecast impact) uses the `src_f` executable
for F, valid for `src_fin` if the gate passes.
