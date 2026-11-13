# TEMPO water residual, fix by fix

**Status (27 October 2026).** TEMPO's microphysics creates **+0.377 %** of its precipitation in UFS once #407 is applied (C96 `control_p8_ugwpv1_tempo`, 6–24 h). The October port's three scheme commits plus the driver layer-depth fix close it to −2e-7 of precipitation.

The pieces, measured one fix at a time on top of #407:

| Source | Effect on R/P, 6–24 h | 0–6 h | Fix |
|---|---|---|---|
| r1 floors in the hydrometeor updates; negative edges raised to the floor in semi-Lagrangian sedimentation | creates ≈ +0.58 % (P1 → P13) | creates ≈ +0.64 % (P1 → P13) | commit 3 (r1 water to vapour, vapour floor) |
| graupel gains not re-closed after `check_over_depletion` | creates 0.005 % | **creates 0.83 %** (spin-up) | C2 |
| cloud water settling out of the lowest layer, not counted as precipitation | removes 0.14 % | removes 0.18 % | C1 |
| density recomputed after heating, used by sedimentation | removes 0.04 % | removes 0.02 % | C3 |
| driver layer depth from `phii`, not the host's mass (`mp_tempo.F90`, ccpp-physics) | removes 0.011 % (with the port) | removes 0.01 % | TH5 |
| condensate at or below r1 deleted by the final clips | ≤ 0.002 % | ≤ 0.02 % | M1 |

- **Measured in every case.** The graupel, density and layer-depth patterns each change TEMPO's budget in the expected direction.
- **T1**, the semi-Lagrangian fallback sign (`qpi > 0` for `qpi < 0`, against Juang and Hong 2010 eq. A4), is a physics bug as well as a water one. Alone it moves the residual by −0.64 % and TEMPO's grid-scale precipitation by −5 %. With commit 3 in, it changes the budget by < 0.001 %. Report it separately: it changes forecasts.
- Single fixes add nearly linearly. The four in commit 1 predict +0.555 % from their separate changes, and together (P1) they give +0.564 %.

## Red team (27 Oct)

- **Still upstream.** Every pattern is still in NCAR/TEMPO `main` c62699f, and no NCAR/TEMPO issue or PR covers them. That includes T1 (L1911 `qpi(k) > 0`; Thompson's copy of the routine has `qpi(k).lt.0.0`), the floors raised to `limit` (L1808, L1814, L1984), and cloud settling counted only in `cloud_precip`. UFS runs `sedi_semi = .true.`, so the semi-Lagrangian path is live.
- **The largest source has a judgement fix.** Commit 3 pays the r1 leftovers and the sedimentation floor from vapour, with a column vapour floor. That is the class of Thompson's TH6/TH7, which went to phase 1 because each has a second reasonable form. C1 is TH2's class. Only C2, C3 and TH5 (graupel, density, layer depth: the patterns #407 names) and T1 have one answer. The report has to say so.
- **The add-one deltas are conditional.** Each is measured with the other leaks still active, on its own trajectory, so the entries below about 0.01 % (graupel after 6 h, M1, TH5 alone) are not resolved. Leave-one-out from `all` isolates each leak, because the residual left is only that leak. TH5 already is one (0.011 %). Runs L_C1, L_C2, L_C3, L_3 and L_T1 were submitted 27 Oct (build 10305938). M1 cannot be left out: commit 3 rewrites the clips it changes.
- **#407's number is the October meter's.** #407 quotes +0.33 %, from the October split meter's 6-h windows (+0.30…+0.34). This meter gives +0.36…+0.39 per window. Use these in the report.
- **Scope.** One case: C96, 24 h, one start date, one suite. Leak sizes are case dependent. Percentages are of TEMPO's own precipitation.

## Runs

| Run | Code (vs T0) | 0–6 h | 6–12 h | 12–18 h | 18–24 h | 6–24 h | Σ\|R\|/P 6–24 h | P 6–24 h (kg/m²) |
|---|---|---|---|---|---|---|---|---|
| T0 | #407 (bd82d044) + meter | +1.254 | +0.388 | +0.383 | +0.361 | +0.377 | 0.754 % | 0.779 |
| C1 | + cloud settling counted, substepped | +1.430 | +0.520 | +0.508 | +0.531 | +0.520 | 0.620 % | 0.781 |
| C2 | + graupel re-closure (snow cap) | +0.427 | +0.379 | +0.382 | +0.356 | +0.372 | 0.752 % | 0.780 |
| C3 | + entry density (updated only in `thermo_vars`) | +1.270 | +0.418 | +0.420 | +0.418 | +0.419 | 0.701 % | 0.776 |
| M1 | + ≤ r1 condensate to vapour | +1.240 | +0.385 | +0.384 | +0.358 | +0.375 | 0.758 % | 0.778 |
| T1 | + fallback sign | +0.538 | −0.241 | −0.246 | −0.297 | −0.263 | 0.272 % | 0.740 |
| P1 | port commit 1 = C1+C2+C3+M1 | +0.631 | +0.549 | +0.550 | +0.589 | +0.564 | 0.567 % | 0.779 |
| P13 | port commits 1 and 3 | −0.010 | −0.011 | −0.012 | −0.013 | −0.012 | 0.015 % | 0.775 |
| TH5 | + driver layer depth | +1.249 | +0.395 | +0.390 | +0.368 | +0.384 | 0.762 % | 0.781 |
| port | commits 1–3 | −0.010 | −0.010 | −0.011 | −0.012 | −0.011 | 0.015 % | 0.738 |
| all | port + TH5 | −0.00002 | −0.00002 | −0.00002 | −0.00002 | −0.00002 | 0.00002 % | 0.738 |

R/P in % of the microphysics' own precipitation; R = area sum of (host-frame column water change + precipitation) per call.

## Method

- **Tree:** a copy of the 0c RT tree (`rt_w0c`). Physics is at #407's bd82d044, `tempo_v3` at 2856696 (the UFS pin). It is built `-D32BIT=ON` for `FV3_GFS_v17_p8_ugwpv1_tempo`, the same as the RT.
- **Variants:** only `mp_tempo.F90`/`.meta` and `module_mp_tempo_main.F90` differ. The single fixes are split from `../../patches/ports/TEMPO-scheme-2856696/`; diffs are in `variants.diff`.
- **Location on Hercules:** `$U/cons/tp_attr`. Build 10303620; runs 10305347–8 (24 h, 144 compute ranks); tables from `tp_budget.py`.
- **Meter (`TPW`, in `mp_tempo_run`):**
  - It takes Σ_k (q_new − q_in) of vapour and the five condensates, times Δp/g from the host's `prsi`. It adds 1000 × the precipitation the call accumulated, and sums area-weighted per rank.
  - Checked: the inputs are untouched; `prcp` accumulates inside the call; the meter sits after the conversion back.
- **Gate:** T0 reproduces the known positive residual (the October meter gave +0.30…+0.34 %, `../../patches/ports/README.md`). `all` closes to 2e-7. Every step has every rank.
