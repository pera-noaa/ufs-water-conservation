# mynnred — red team of suites' MYNN-EDMF (01, 01b, 04) and GFDL MP v3 (02) claims

## Status (18 Oct 2026, done)
| claim | verdict | decisive evidence | correction |
|---|---|---|---|
| 01b moisture_check latent heat double count, +8.0 W m-2 | **CONFIRMED** (BUG FIX) | code trace; dump run bitwise = suites' ctl; fill 0.2776 kg m-2/day (p8), 0.2782 (rap), heat 8.03 / 8.05 W m-2 = L·fill to 1e-12; offline replay (Python + gfortran driver calling the real moisture_check) reproduces the model's Dth with error 0 and gives E_fill = L·fill (unfixed), 0 (01b); forecast cooling −0.063 K (mass-weighted) = what 8 W m-2 for 24 h predicts (−0.069 + SH/precip feedback) | fix drops the heat of a SNOW fill (snow not in Dth; Thompson pipes Dqs to the host): 0 in p8_mynn and rap (no snow/ice fills, no negative host input), but make it complete — add xlscp/Π·(sqs2−sqs) to Dth, or call moisture_check after Dth with a scratch θ and keep its dth increment (the alternative the code comment describes). Impact numbers are unweighted grid means: area/mass-weighted T −0.063 K (not −0.049), LH +3.12, ps rms 2.37×. Issue text must note NCAR/MYNN-EDMF HEAD diverged (ebd5d2d, Feb 2025: FLAG_QI Dth uses input sqc/sqi, fill counted once there; scratch copy would be wrong there); MMM/MPAS copy has the same double count as CCPP |
| 01(a) rhosfc density + typo, +0.85 % of E | CONFIRMED | code; E-weighted rhosfc/rho1 − 1 = 0.858 % from history output | none (also moves momentum drag −0.7 %, to match dusfc1) |
| 01(b) dew limiter always 0 | CONFIRMED | min(0.9·sqv−1e-8, 0) = 0 for sqv > 1.1e-8; comment says limiter; dew/E ≥ 0.58 % from 6-h means (lower bound; suites 0.55–0.7 %); same in NCAR, MMM, develop | none |
| 01(c) filler weights by MYNN's interpolated delp | CONFIRMED | delp(k) = interpolated interface differences (L4143–4157), solver conserves ρ·dz | none |
| 01(d) ρ = Δp/(g·dz) | CONFIRMED as NUMERICAL CONSISTENCY | FV3 builds prsl = Δp·rTv/Δφ, so the ideal-gas ρ already equals Δp/(g dz) except where the monotonicity clamp binds (rare) | note: rho(i,1) also converts hflx/qflx to hfx/qfx, so (d) moves the atmosphere's flux off the surface scheme's own ρ by the same rare amount; the meter's E (PBL report) cannot see that |
| 04 SH without 1/Π, cpm vs cp | CONFIRMED (NUMERICAL CONSISTENCY) | host applies cp·Π·Δθ (dtdt = RTHBLTEN·exner), hfx = ρ·cp·hflx: applied/reported = Π1/(1+0.84 q1) = 0.9851 SH-weighted (suites 16.72/16.97 = 0.9853); 1/Π1 is the energy-exact factor (1/Π_sfc would be the θ-at-surface one, ~0.03 % apart) | none |
| 02 GFDL MP v3 mass basis | CONFIRMED | non-inline input r = q/(1−qv_in), dp = delp(1−qv_in); fix returns delp_in and q = r(1−qv_in): exact inverse (to 1 ulp), q·delp = r·dp also for a caller that uses the returned delp; cld_sat_adj (same flag) has no caller in UFS | report says species "scaled by (1−qv_in)(1+qv_new)"; host/true is the inverse (draft 6 has it right). delp passed on to the refl diagnostic (driver L369) now = input delp |
| meters | can fail | water rW +4.5e-2 unfixed → 1e-15; frame-P rE_P 11.52 → 2.22; my cmp_bit check: d1 vs fxa6 90/126 differ | SMX(40) "filler heat" is ΔΘl inside moisture_check: zero by construction after 01b (not a gate); SMX(41) counts liquid+ice only (blind to snow) — the frame-P energy row is the real gate |

Jobs: build 10156466; runs 10156508 (d1_p8), 10156545 (d1_rap). All mine, all done.

## Log
- 01b code: moisture_check(…, th=thl, …) does thl += xlvcp/Π·dqc2 + xlscp/Π·(dqi2+dqs2) and sqc2 += dqc2;
  Dth = (thl + xlvcp/Π·sqc2 + xlscp/Π·sqi2 − th)/dt then counts liquid/ice fills twice. moisture_check's own dth
  increment is discarded (Dth overwritten). thl is not used after mynn_tendencies (driver recomputes per column).
- 01b CAVEAT found: snow. sqs2 = sqs (snow not mixed), Dth has no snow term (`!+sqs(k)`), but Thompson sets FLAG_QS
  and rqsblten = Dqs, which includes moisture_check's snow fill. Unfixed: snow-fill heat enters once via thl
  (correct). With the 01b scratch copy it is dropped. Size depends on whether qgrs_snow < 0 ever reaches MYNN.
- Upstream: NCAR/MYNN-EDMF (WRF submodule 8f8e8b5, 2026-05-24) has the same moisture_check(…thl…) call, but since
  ebd5d2d (2025-02-21, "temperature tendency tests") its FLAG_QI Dth uses the INPUT sqc/sqi, not sqc2/sqi2: there
  the fill is counted once (via thl) and the 01b scratch copy would remove it. ELSE branch still uses sqc2.
  MMM bl_mynn_subroutines (MPAS) still uses sqc2/sqi2 (+sqs) -> same double count as CCPP.
  rhosfc typo and dew limiter identical in NCAR, MMM and develop.
- Independent area/mass-weighted impact (my impact_aw.py, C96 grid areas, dpres weights; noise = ctl vs c999):
  01b (fxa6_p8 vs fxw6_p8): T −0.0630 K (mass-weighted; suites' unweighted −0.049), LH +3.12, SH +0.42 W m-2,
  T2m −0.045 K, PW +0.069, ps rms 2.37× noise (suites 2.42). Energetic cross-check: removing 8.02 W m-2 for 24 h
  over ps/g = 10063 kg m-2 cools by 6.93e5/(1004.6·10063) = 0.0686 K; + SH (+0.42) and extra precipitation
  latent heat (+0.27 W m-2) gives −0.063 K: the forecast cooling is what the claimed 8 W m-2 predicts.
  01 (fxw6 vs ctl): T −0.002, LH +0.56, T2m −0.021, ps rms 1.19×: matches suites.
- Dump run d1_p8 (job 10156508, exe t1 md5 315a89fa = full10 + no-fma + passive dump): bitwise equal to suites'
  ctl_p8_mynn (atmf024 0/126, sfcf024 0/1176 differ), so the dump describes their unfixed control exactly.
  144 ranks, 6.624e6 column-steps: liquid fill in 25.0 % of column-steps, ice 0, snow 0, host-input negatives 0.
  Column-mean fill 0.2776 kg m-2 day-1 (suites 0.277); heat moisture_check puts into thl: 8.032 W m-2 = L·fill to
  1e-12 (suites 8.02).
- Offline replay on 12 dumped real columns (ranks 0–3), two independent ways: Python transcription
  (tools/replay_mc.py) and a standalone gfortran driver calling the REAL module_bl_mynn::moisture_check
  (tools/mc_driver.f90, pristine full10 module). Both reproduce the model's thl, sqv2..sqs2, Dqv..Dqs and Dth with
  max error 0. Frame-P energy of the fill (tendencies with fill minus without): unfixed = L·fill (ratio
  1 ± 3e-11), 01b scratch copy = 0 (|E| ≤ 7e-9 J m-2 per column-step).
- RAP dump (d1_rap, job 10156545, bitwise = suites ctl_rap): fill 0.2782 kg m-2/day, heat 8.05 W m-2 = L·fill,
  ice/snow fills 0, host negatives 0.
- 01(a) E-weighted rhosfc/rho1 − 1 = 0.858 %; 01(b) dew/net E 0.583 % from 6-h mean LH (lower bound).
- 04 SH-weighted Π1/(1+0.84 q1) = 0.98512.
- 02: cld_sat_adj calls mpdrv with do_inline_mp=.false. but has no caller in UFSATM.
