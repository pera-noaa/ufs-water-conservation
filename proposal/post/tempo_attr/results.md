# TEMPO water residual, fix by fix

**Status (27 October 2026).** Once #407 is applied, TEMPO's microphysics creates **+0.377 %** of its precipitation in UFS (C96 `control_p8_ugwpv1_tempo`, 6–24 h). The October port's three scheme commits plus the driver layer-depth fix close it to −2e-7 of precipitation.

Each leak isolated: every other fix in, this one left out (leave-one-out from `all`):

| Leak | 6–24 h | 0–6 h | Fix | One answer? |
|---|---|---|---|---|
| semi-Lagrangian fallback sign (`qpi(k) > 0` for `< 0`): negative edges are raised to the floor | **creates ≈ 0.64 %** | creates ≈ 0.72 % | T1 | yes (Juang and Hong 2010 eq. A4; Thompson's copy) |
| graupel gains not re-closed after `check_over_depletion` | creates 0.004 % | **creates 0.86 %** | C2 | yes |
| cloud water settling out of the lowest layer, counted only in `cloud_precip` | removes 0.137 % | removes 0.199 % | C1 | no (Thompson's TH2 class) |
| density recomputed after heating, used by sedimentation | removes 0.118 % | removes 0.120 % | C3 | yes |
| driver layer depth from `phii`, not the host's mass (`mp_tempo.F90`, ccpp-physics) | removes 0.011 % | removes 0.010 % | TH5 | yes |
| r1 leftovers and floors, with T1 fixed | creates 0.001 % | creates 0.001 % | commit 3 | no (TH6/TH7 class) |

- **The pieces add up.** The five isolated leaks other than T1 sum to −0.261 % (6–24 h) and +0.533 % (0–6 h). The run with only T1 fixed measures −0.263 % and +0.538 %. T1's share is T0 minus that run.
- **T1 is the main source and changes forecasts.** Fixing it lowers TEMPO's grid-scale precipitation by 5 %: rain and graupel then fall with the published piecewise-linear profile. With commit 3 in it has no water effect (L_T1 = all), because commit 3 pays the floor from vapour.
- **Graupel is a spin-up leak**, as in Thompson (+0.76 % in the first 6 h there).
- **#407 names graupel, density and layer depth.** All three leak, all have one answer, and none is the main source. Density is 3× what the add-one runs suggested.
- M1 (≤ r1 condensate deleted by the final clips) cannot be isolated: commit 3 rewrites those clips. Added alone to #407 it changed the residual by 0.002 %.

## Red team (27 Oct)

- **Still upstream.** Every pattern is still in NCAR/TEMPO `main` c62699f, and no NCAR/TEMPO issue or PR covers them. That includes T1 (L1911 `qpi(k) > 0`; Thompson's copy of the routine has `qpi(k).lt.0.0`), the floors raised to `limit` (L1808, L1814, L1984), and cloud settling counted only in `cloud_precip`. UFS runs `sedi_semi = .true.`, so the semi-Lagrangian path is live.
- **Judgement fixes.** Commit 3 pays the r1 leftovers and the sedimentation floor from vapour, and C1 counts settled cloud as precipitation. These are the classes of Thompson's TH6/TH7 and TH2 (phase 1 there: a second reasonable form). Once T1 is fixed, commit 3 is worth 0.001 %.
- **Attribution method.** Leave-one-out from the closed run isolates each leak, because the residual left is only that leak. The first, add-one attribution (each fix alone on #407) measured each fix with the others still active. It put density at 0.04 % and the floors at 0.58 %; the add-one rows are kept in *Runs*.
- **#407's number is the October meter's.** #407 quotes +0.33 %, from the October split meter's 6-h windows (+0.30…+0.34). This meter gives +0.36…+0.39 per window.
- **Origin of T1.** TEMPO had `qpi(k).lt.0.0` through v2 (19eaf25f, L3313); v3.0.0 (e41f020b, NCAR/TEMPO#24, Feb 2026) inverted it. The open draft GPU port (NCAR/TEMPO#57) carries the inverted line. No other open PR touches these sites.
- **Graupel, a second source.** The per-term clamps on `prr_rcs`, `prs_rcs`, `prg_rcs` (main L2995–2998) also break `prg_rcs = −(prr_rcs + prs_rcs)`; C2's recomputation after the limiters covers both.
- **Cloud settling.** `cloud_precip` never leaves `tempo_main` except through `freezing_rain`, so freezing rain can exceed `rain_precip`: counting it as rain (C1) matches that diagnostic.
- **Alternatives (X_* runs, 28 Oct).**
  - T1, leave-one-out from L_3: creates 0.576 % (6–24 h) and 0.647 % (0–6 h); T0 − T1 gives 0.64.
  - Always piecewise constant closes like the corrected test, with P −0.6 % against it, so v3's +5.4 % comes from the cells where the inverted test keeps a linear profile; it is not a way to keep v3 precipitation.
  - C2 proportional scaling: closes to 2e-7 like the cap, with P +0.03 %. There is no TEMPO noise pair.
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
| L_C1 | all − C1 | −0.199 | −0.120 | −0.121 | −0.166 | −0.137 | 0.137 % | 0.738 |
| L_C2 | all − C2 | +0.861 | +0.000 | +0.000 | +0.011 | +0.004 | 0.004 % | 0.739 |
| L_C3 | all − C3 | −0.120 | −0.111 | −0.113 | −0.129 | −0.118 | 0.121 % | 0.740 |
| L_3 | all − commit 3 (= P1 + T1 + TH5) | +0.001 | +0.001 | +0.001 | +0.001 | +0.001 | 0.001 % | 0.738 |
| L_T1 | all − T1 (= P13 + TH5) | −0.00002 | −0.00002 | −0.00001 | −0.00001 | −0.00002 | 0.00002 % | 0.774 |
| X_T1inv | L_3 with T1 reverted (main's test) | +0.647 | +0.563 | +0.560 | +0.601 | +0.576 | 0.576 % | 0.7775 |
| X_T1c | L_3 with the fallback always taken (piecewise constant) | +0.001 | +0.001 | +0.001 | +0.001 | +0.001 | 0.001 % | 0.7335 |
| X_C2p | all, snow's rain–snow gain scaled by the limited rain instead of capped | −0.00002 | −0.00002 | −0.00002 | −0.00002 | −0.00002 | 0.00002 % | 0.7386 |

R/P in % of the microphysics' own precipitation; R = area sum of (host-frame column water change + precipitation) per call.

## Method

- **Tree:** a copy of the 0c RT tree (`rt_w0c`). Physics is at #407's bd82d044, `tempo_v3` at 2856696 (the UFS pin). It is built `-D32BIT=ON` for `FV3_GFS_v17_p8_ugwpv1_tempo`, the same as the RT.
- **Variants:** only `mp_tempo.F90`/`.meta` and `module_mp_tempo_main.F90` differ. The single fixes are split from `../../patches/ports/TEMPO-scheme-2856696/`; diffs are in `variants.diff`. The leave-one-out sources are built by `tp_loo.sh`/`tp_loo2.sh` on Hercules. Each is gated to differ from `all` by exactly its fix; C3 is reverted by substitution, because commit 3's context moved its hunks.
- **Location on Hercules:** `$U/cons/tp_attr`. Builds 10303620 and 10305938 (leave-one-out); runs 10305347–8 and 10306256 (24 h, 144 compute ranks); tables from `tp_budget.py`.
- **Meter (`TPW`, in `mp_tempo_run`):**
  - It takes Σ_k (q_new − q_in) of vapour and the five condensates, times Δp/g from the host's `prsi`. It adds 1000 × the precipitation the call accumulated, and sums area-weighted per rank.
  - Checked: the inputs are untouched; `prcp` accumulates inside the call; the meter sits after the conversion back.
- **Gate:** T0 reproduces the known positive residual (the October meter gave +0.30…+0.34 %, `../../patches/ports/README.md`). `all` closes to 2e-7. Every step has every rank.
