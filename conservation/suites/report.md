# Suites: E.3 MYNN-EDMF, E.4 GFDL MP v3, E.5 Grell–Freitas — water, passive tracer and energy in their own suites

## Status

Nine suites diffs are in the final series as rows 47–55. The tested E4b switch (`gfdl_mp_host_cp`) is not proposed.

| SERIES row | Fix (suites diff) | Class | Switch: default / all-on | Before → after | 24 h impact (area/mass-weighted) |
|---|---|---|---|---|---|
| 47 `47_MYNN01.diff` | MYNN surface flux density, dew limiter, filler mass (`01`) | BF / NC | — | water +4.53e-2 → −5.5e-15 kg m-2/day | p8: LH +0.56, T2m −0.021 K |
| 48 `48_MYNN01b.diff` | MYNN `moisture_check` latent heat counted twice (`01b`) | BF | — (unconditional) | +8.0 W m-2 spurious heat → 0 | p8: T −0.063 K, LH +3.12, ps rms 2.37× |
| 49 `49_GFDL02.diff` | GFDL MP v3 mass basis (`02`) | BF | — | water −8.39e-3 → −9.3e-16 | T +0.001 K, precip +0.16 % |
| 50 `50_GF03.diff` | GF water closure (`03`) | BF + NC | `gf_closure` F / T; opt-in, default off | water −1.37e-1 → +2.5e-16 | precip +8.9 %, SH −0.10, T −0.011 K |
| 51 `51_MYNN04.diff` | MYNN surface heat flux θ (`04`) | NC | `mynn_sfc_heat` F / T | SH applied = reported | at noise (0.9–1.2×) |
| 52 `52_PBL05.diff` | satmedmfvdifq surface flux layer mass (`05`) | NC | — | water +2.6e-8 → −3.6e-16 | at noise (1.0×) |
| 53 `53_MYNN06.diff` | MYNN static-energy mixing (`06`) | PC | `mynn_mix_sl` F / T; opt-in, default off | θl-energy 0.47 → 2e-9 W m-2 | p8: SH −0.68, LH +1.75, T2m +0.068 K |
| 54 `54_GFDL07.diff` | GFDL MP v3 rain sedimentation heat capacity (`07`) | BF | — | own-frame + PE gap +0.20 → −0.007 W m-2 | T −0.003 K |
| 55 `55_SAMF08.diff` | SAMF deep CA-trigger early return (`08`) | BF | — | p8_mynn 3×8 ≠ 4×6 → bitwise | below noise (0.3–0.7×) |

- Red team (`mynnred/`): 01, 01b, 02 and 04 CONFIRMED; its corrections are folded in (§10.4).
- Final gates (x10/m10, `-no-fma`): meters passive, switches off inert, 3×8 = 4×6, restart 12+12: 0 differ (§10.5).
- Passive tracers: no defect in these schemes (§6).
- Left by design: GF −0.26 W m-2 (two ice partitions); GFDL MP v3 −0.007 W m-2 in its own frame, −0.021 from its own constants (§10.2).
- Note: the impacts above are the patch table's area/mass-weighted values (as TRACKER for gf_closure); §3–§5 give unweighted values: gf_closure precip +8.6 % and T −0.006 K (§5), 01b T −0.049 K and 01 LH +0.59 (§3), 02 precip +0.15 % (§4).

## Current answers

## 3. E.3 MYNN-EDMF (`FV3_GFS_v17_p8_mynn`; also `FV3_RAP`)
Causes (code):
- **(a) density mismatch.** The driver makes the surface fluxes kinematic with `rho1(kts)` (`flqv = qfx/rho1(kts)`,
  `flt = hfx/(rho1(kts)*cpm)`); `mynn_tendencies` multiplies them back by `rhosfc = psfc/(R_d*(tk+p608*qv))` (another
  density, with a typo) in the qv, sqw, sqc, thl and drag rows: +0.85 % of E. Fix: `rhosfc = rho(kts)` (one line; also
  makes heat and drag consistent with what the wrapper reports as dtsfc1/dusfc1).
- **(b) dew limiter.** `max(qvflux, min(0.9*sqv-1e-8,0)/dtz)` is 0 whenever sqv > 1.1e-8: every downward vapour flux is
  zeroed in the atmosphere while the surface books it: +0.67 % of E. Fix: `-max(0.9*sqv-1e-8,0)/dtz`, the bound its
  comment describes. It did not bind in any fixed run (cut = 0).
- **(c) column filler weights.** `moisture_check` claims to "fully preserve column moisture" but borrows with MYNN's
  interpolated `delp`, while the solver conserves ρ·dz: +3.9e-7 kg m-2/day (p8), −1.3e-10 (rap). Fix: pass ρ·dz.
- **(d) density for the solver.** ρ = prsl/(R_d·T·(1+p608·q)) with the host's nonhydrostatic dz is not exactly Δp/g:
  rare events up to 5.6e-13 kg m-2 in one step. Fix: ρ = Δp/(g·dz) in the wrapper (ρ·dz = host layer mass). Impact
  alone at noise (T rms 0.99×, LH 1.03×).
- **(e) energy, 01b.** `moisture_check(... sqv2, sqc2, sqi2, sqs2, thl, ...)` fills negative condensate from vapour and
  adds xlvcp/Π·dqc to its `th` argument, which is θl; `Dth = (thl + xlvcp/Π·sqc2 + xlscp/Π·sqi2 − th)/dt` then counts
  the filled condensate's latent heat a second time. Measured: filler heat 6.93e5 J m-2/day = **8.02 W m-2**, fill
  0.277 kg m-2/day (heat = hvap × fill exactly). Fix: give `moisture_check` a scratch copy (θl is conserved by a
  vapour↔condensate exchange). After: filler heat ≤ 1e-7 J m-2/day.
- **(f) energy, 04 (switch).** The surface sensible heat is applied as the θ flux `hfx/(ρ·cpm)`: no 1/Π, and cpm
  where the host and the land use cp. The atmosphere gets 16.72 W m-2 vs 16.97 reported (p8). `mynn_sfc_heat=.true.`:
  `flt = hfx/(ρ·cp·Π1)`, SH solved = reported exactly. A switch because `flt` also feeds the surface-layer stability
  (rmol, fltv).
- Checked and clean: wrapper flux clip (qfx ∈ [−2e-4, 5e-4], hfx ∈ [−500, 1200]: 1.5e-5 area-weighted events/day p8,
  5e-5 rap), top boundary row, mass-flux terms in water (ρdz frame closes to 1e-15).

Gate (24 h, kg m-2/day; energy W m-2):

| run | MYNN rW | rW/E | max step | rE_P | dKE | SH applied / reported | tracer Δ (u, s) |
|---|---|---|---|---|---|---|---|
| p8_mynn unfixed (m1) | +4.53e-2 | 1.5e-2 | 4.2e-4 | +11.52 | −2.23 | 16.72 / 16.86 | 0, 0 |
| p8_mynn 01+01b+02 (mf6) | −4.8e-15 | −1.6e-15 | 7.3e-16 | +2.22 | −2.25 | 16.72 / 16.97 | 0, 0 |
| p8_mynn + 04 (mf6s) | −4.8e-15 | −1.6e-15 | 7.9e-16 | +2.48 | −2.25 | 16.97 / 16.97 | 0, 0 |
| rap unfixed (m1) | +4.70e-2 | 1.6e-2 | 1.8e-4 | +11.52 | −2.27 | 19.81 / 20.03 | 0, 0 |
| rap fixed, off / 04 on (mf6 / mf6cs) | −5.0e-15 / −1.1e-15 | ~1e-15 | 6e-16 | +2.17 / +2.49 | −2.29 | 19.90/20.22; 20.10/20.10 | 0, 0 |

Remaining MYNN frame-P energy (design, not fixed): in p8 after 01–01b the thermal 2.22 W m-2 ≈ −ΔKE (2.25), net ≈ 0;
split: dissipative heating 1.94 (TKE → heat, `dheat_opt = 1`), θl- rather than enthalpy-mixing (Σρdz·cp·Π·Δθl of the
diffusion + mass-flux operators) +0.40, SH −0.25 (04). TKE and surface drag work are not in E_P, so this frame cannot
close for a TKE scheme without a KE/TKE accounting decision (same question as enpbl's D1).

Impact (24 h; rms and global-mean difference; noise = ctl vs consv_te 0.999 of the same suite):

| change | T rms (noise) | T mean | LH mean (W m-2) | SH mean | T2m mean | PW mean | ps rms ratio |
|---|---|---|---|---|---|---|---|
| 01 p8 | 0.244 (0.223) | −0.003 | +0.59 (−0.04) | +0.05 | −0.021 | −0.019 | 1.17 |
| 01 rap | 0.187 (0.167) | −0.004 | +0.48 (−0.04) | −0.03 | −0.018 | −0.014 | 0.98 |
| 01b p8 | 0.357 (0.223) | −0.049 | +3.19 | +0.46 | −0.048 | +0.069 | 2.42 |
| 01b rap | 0.307 (0.167) | −0.042 | +3.78 | +0.63 | −0.064 | +0.032 | 2.17 |
| 04 p8 | 0.231 (0.223) | +0.002 | +0.08 | −0.008 | −0.002 | −0.001 | 1.12 |
| 04 rap (on top of 03) | 0.174 (0.167) | +0.003 | +0.06 | −0.005 | −0.004 | 0.000 | 0.94 |

Classes: 01 BUG FIX (a, b, c), (d) NUMERICAL CONSISTENCY kept in 01 because it is at noise; 01b BUG FIX; 04 NUMERICAL
CONSISTENCY (energy).

## 4. E.4 GFDL MP v3 (`FV3_GFS_v16_gfdlmpv3`, control_iovr4_gfdlmpv3, `do_sat_adj = .true.`)
Cause: `mpdrv` converts in with 1/(1 − qv_in) (dp = delp·(1 − qv_in)) and back with 1/(1 + qv_new); the CCPP driver
keeps the returned `delp` local and the host rebuilds mass as input Δp × returned ratio, so the host's species mass is the true
mass × 1/[(1 − qv_in)(1 + r_v,new)] — TH1. Fix (02): in the non-inline branch convert back with
`con_r8 = 1/(1 − qv(i,k))` (input humidity). One line; the inline branch (FV3 updates delp) is untouched. The PR carries it in the
CCPP wrapper instead (02w, `fixes/02w_E4_gfdlmp_v3_mass_basis_wrapper_v9.diff`): rescale the returned species by
`delp_out/delp_in`, GFDL's module unchanged. Same species to 8e-16 per call (column test, `proposal/post/gfdl_wrap/`); the
final tz → pt conversion's heat capacity then uses GFDL's basis (≤ 2e-5 K per call). Meters: trees `gA` (02 + 07) and
`gW` (02w + 07), runs `gA_gfdl`, `gW_gfdl` (24 h): MP water rW/P 1.6e-15 (gA), 1.5e-14 (gW); GFDL frame + water PE
−0.0075, −0.0070 W m-2; gW vs gA against the consv_te 0.999 pair: rms ratios 0.96–1.16, means within noise. The 02 impact
row holds for 02w. Also measured
and clean here: rainmin zeroing and settled cloud water `water0` (not in prcp0) are 0 in this case (P before zeroing =
P booked exactly); they would leak if active.

| run | MP rW (kg m-2/day) | rW/P_MP | max step | scheme-frame ΔW + P | rE_P (W m-2) | tracer Δ |
|---|---|---|---|---|---|---|
| unfixed (m0) | −8.39e-3 | −1.03e-2 | 1.6e-4 | 0 | −0.129 | 0, 0 |
| fixed (mf6) | −1.05e-15 | 1.3e-15 | 7.7e-17 | 0 | +0.117 | 0, 0 |

Energy (design, not fixed): in the CCPP host GFDL MP v3 uses its own thermodynamics (moist cv / constant volume with
`hydrostatic=.false.`, T-dependent latent heats, condensate heat capacity), not the GFS frame. A tested switch passing
constant-pressure thermodynamics (`not_proposed/E4b…`) only reduces the gap 0.117 → 0.085 W m-2, so cv is not the main
term; not proposed. Attribution needs the energy agents' frame-F S_cross for falling precipitation.
Impact (02, 24 h): rms ratios 1.04–1.28 (T 1.12, ps 1.10, precip 1.28); all means within noise except precipitation
+4.4e-8 kg m-2 s-1 (+0.15 %). Class: BUG FIX. Untested sharer: HAFS `FV3_HAFS_v1_gfdlmpv3_tedmf` (not built here).

## 5. E.5 Grell–Freitas (`FV3_RAP`, rap_control)
Causes (code, measured by column class):
- **(a)** `raincv` includes `cutens·prets` only when `pret > 0`. In shallow-only columns the applied tendencies remove
  0.281 kg m-2/day but 0.126 is reported (the mid-level part only).
- **(b) mass basis.** GF converts q → r = q/(1 − q) and back with r/(1 + r): the host's vapour change is Δr·(1+r)^-2
  while GF's heating and its condensate (added to cliw/clcw directly) use Δr; water and frame-P energy inconsistent at
  ~2r.
- **(c)** GF shallow is not consistent with itself: in its own dp frame the tendencies remove 0.321 vs pre·dt = 0.329
  (−2.5 %): precipitation is Σ pwo over levels, the vapour tendency removes ½(pwo(k)+pwo(k+1))·g/dp on interpolated
  `po_cup` interfaces. Hence adding `cutens·prets` overshoots (0.126 + 0.237 = 0.363 vs 0.281 removed).
- **(d)** floors (qv ≥ 1e-16, cliw/clcw ≥ 0) are a small extra source.

Fix (03, switch `gf_closure`, default .false.): apply GF's vapour increment on its own basis (`new_q = q + (r_new −
r_in)`; untouched columns stay bitwise); `raincv` = the water the applied tendencies (ten_q, dcliw, dclcw) remove, in host
layer mass (`prsi` added), in every GF column; where they would add water instead (net moistening), the positive
increments are scaled down to zero net (1.4 column-steps per column per day = 0.5 % of column-steps; water cut
1.1e-2 kg m-2/day = 1.7 % of GF's precipitation). Never negative rain; exact closure.

| run | GF rW (kg m-2/day) | rW/P_GF | max step | shallow-only / deep / other rW | rE_P (W m-2) | dKE | tracer Δ |
|---|---|---|---|---|---|---|---|
| unfixed (m1) | −1.370e-1 | −0.30 | 5.9e-4 | −0.155 / +0.010 / +0.008 | +1.171 | −0.112 | 0, 0 |
| 01+01b+02, closure off (mf6) | −1.513e-1 | −0.34 | 6.9e-4 | −0.168 / +0.009 / +0.008 | +1.264 | −0.110 | 0, 0 |
| closure on (mf6c) | +2.8e-16 | −4.3e-16 | 4.3e-17 | 0 / 0 / 0 | −0.256 | −0.110 | 0, 0 |
| closure + 04 (mf6cs) | −1.3e-17 | 1.9e-17 | 4.4e-17 | 0 / 0 / 0 | −0.255 | −0.110 | 0, 0 |

Energy (design, not fixed): with closure the GF frame-P gap is −0.26 W m-2 = −0.67 (−hfus·ΔW_ice: the driver partitions
detrained/transported condensate into ice by temperature (tcr) with no fusion heat; shallow and mid have no ice phase)
+0.11 (KE → heat, = dKE) +0.30 (deep updraft's own freezing/melting heat with a different partition, p_liq_ice; dp_GF
vs host). A fix needs one ice partition with its heat (D3A-like); owners' decision, not done here.
Impact (03 on vs off, rap 24 h): precipitation +1.85e-6 kg m-2 s-1 (**+8.6 %**), convective bucket +2.9e-6, SH −0.10 W
m-2, T −0.006 K; rms 1.0–1.4× noise. The water that used to vanish now falls. Class: BUG FIX (a) + NUMERICAL CONSISTENCY
(b, closure diagnosis, fixer); behind the switch because of its size: ASH DECIDES.
Untested GF paths: chemistry transport/wet scavenging (`rrfs_sd`), other GF suites (`FV3_HRRR_gf`), OpenACC build.

## 6. Passive tracers (all suites)
- MYNN (`mix_chem` off), GF (generic tracers not transported) and GFDL MP v3 never touch `pt_u`/`pt_s`: their segment
  change of tracer mass and of Σ m·|q_u − 1e-6| is exactly 0, unfixed and fixed.
- 24 h global tracer mass: DYN+coupling 2–5e-16, physics ≤ 3e-18 (SAMF). Uniform-tracer deviation grows only in SAMF
  (−2.7e-7 of the L1 measure) and the dycore (+5e-6) — other agents' items (trsamf, trdyn).
- No tracer defect in these schemes. Not exercised: MYNN smoke/chem mixing, GF chem transport.

## 10. Round 2 (coordinator items 1–3 and mynnred corrections)

### 10.1 p8_mynn decomposition → fix 08 (BUG FIX, SAMF deep)
- Hunt: hourly output: first difference between 9 and 10 h; layout-independent per-probe column hashes (meter SMH,
  integer sums of transfer(x), order-independent): first difference at step 46, probe 5 (after GFS_DCNV_generic_post);
  probes 1–4 identical. Per-column dump: one column, 127.77E 13.44N. All 22 column inputs of samfdeepcnv hashed at
  entry: identical in both layouts. `-init=zero,arrays` on samfdeepcnv: identical to the default build and still
  layout-dependent (not an uninitialised read). Checkpoints inside samfdeepcnv: in 3×8 the column's block returned at
  the first `if(totflg) return` (no column convective); in 4×6 its block did not return and the CA trigger
  (`if (ca_deep(i) > nthresh) cnvflg(i) = .true.`, after that return) turned the column on.
- Cause: the CA trigger re-enables columns after cuts (6 places); early returns placed before a re-enable make the
  column's convection depend on its block's other columns. Fix: `caon(i)` (CA trigger on for the column); the six
  early returns that precede a re-enable do not return while any `caon` column remains. Later returns unchanged.
- Gate: unfixed p8_mynn 3×8 vs 4×6: 90/126 atmf024 variables differ; fixed: 0 of 126/1176/1138 (atmf, sfcf, restart),
  default and all-on. Also bitwise: RAP all-on, gfdlmpv3. Impact below noise (rms 0.3–0.7×).
- Shared: control_p8 (GFS v17, `do_ca`/`ca_trigger` on) has the same code path; it was not hit in the energy agents'
  24 h test, but the dependence is latent there.

### 10.2 Design energy gaps
- **MYNN θl-mixing (+0.47 W m-2, θ- rather than enthalpy-weighted):** closable. Opt-in 06 `mynn_mix_sl`: the thl
  tridiagonal solves s_l/cp = Π·θl + g z/cp (same matrix; plume fluxes converted at interfaces; sources as temperature
  tendencies; conservative top row). θl-equation energy gap Σρdz·cp·Π·Δθl − SH − dissipative heating: 0.47 → 2.3e-9 W m-2
  (p8), 5.4e-10 (rap). MYNN frame-P thermal = SH + LE + dissipative heating exactly; the remaining "gap" is the TKE
  dissipation heating (2.21 W m-2) against the mean-flow KE loss (−2.27): a TKE/KE accounting choice (as enpbl D1),
  not a defect. PHYSICS CHANGE: SH −0.68, LH +1.75 W m-2, T2m +0.068 K, rms 1.3–1.5× noise.
- **GFDL MP v3 (+0.12 frame P; 0.085 with constant-pressure thermodynamics):** meter in frame F (FV3 constants) and
  in GFDL's own constants, with/without the potential energy of the water mass (SMX 44/45/47/48):

  | | frame F | frame F + water PE | GFDL frame + PE |
  |---|---|---|---|
  | 02 only | +0.79 | +0.18 | +0.20 |
  | 02 + 07 | +0.58 | −0.028 | −0.007 |

  `sedi_heat` turns the potential energy of falling hydrometeors into heat (+0.61 W m-2): physical, a frame term
  (FV3's energy counts water PE; the GFS frame P does not). `terminal_fall` passed the ICE heat capacity for rain's
  heat exchange (`call sedi_heat(..., c_ice)` for every species): fix 07 passes c_liq for rain and cloud water
  (0.21 W m-2). What remains: −0.007 W m-2 in GFDL's own frame (w-sedimentation KE is not in the meter) and −0.021 from
  GFDL's own constants (c_liq 4218 vs 4185.5, c_ice 2106 vs 1972, tice 273.16). Frame P cannot close for a Kirchhoff,
  condensate-heat-capacity scheme. The constant-pressure switch (E4b) does not help: `sedi_heat` keeps cv_air/cv_vap
  hard-coded (gap −0.15 with it). Inherent to GFDL's constants beyond that; stopped.
- **GF (−0.26 W m-2):** inherent. The deep updraft freezes condensate with its own partition (p_liq_ice) and heats;
  the driver re-partitions all detrained and fct-transported condensate into ice by temperature (tcr) with no heat;
  shallow and mid have no ice phase. Exact closure needs one partition with its heat across cu_gf_deep, cu_gf_sh and
  the driver (restructuring); stopped.

### 10.3 satmedmfvdifq water residual → fix 05 (NUMERICAL CONSISTENCY)
- Not a tracer-index mismatch (GFDL vdftra/ten_q mapping checked: 1 qv, 2 ql, 3 qi, 4 qr, 5 qs, 6 qg, 7 o3). Cause:
  the surface sources are `dtdz1·evap`, `dtdz1·heat` (and the drag) with dtdz1 = dt2/(zi(2)−zi(1)) while the fluxes were
  made kinematic with rho_a: applied/reported = del(1)/(g·rho_a·Δz1) − 1 = the nonhydrostatic dz deviation, 8e-9.
  Fix: dtdz1 = dt2·rho_a·g/del(1). Water 2.6e-8 → −3.6e-16 kg m-2/day; impact at noise.

### 10.4 mynnred corrections
- 01b v2: `moisture_check` moved after the Dth formula, with a scratch θ; its dth increment carries the latent heat of
  every fill (liquid, ice, SNOW) once. Gate with a forced snow fill (test hook `SM_HOOK_SNOW`: sqs2(kts) −1e-7 before
  the call), step 1, MYNN frame-P residual hook − no hook: v1 −3.590e15 J = L_s × fill (1.267e9 kg); v2 +6.6e5 J
  (2e-10 of it). Liquid/ice: identical to v1 (impact v2 vs v1 at noise).
- 01(d): hfx/qfx (hence dtsfc1/dqsfc1) now use the surface schemes' ideal-gas density; ρ = Δp/(g dz) only in the solver.
  SMX 46 (qflx·ρ_ideal) = SMX 01 (reported) = SMX 03 (applied), exactly.
- SMX 40 (heat moisture_check puts into θl) is zero by construction after 01b: not a gate. SMX 41 now includes snow.
  The 01b gate is the frame-P MYNN energy row.
- Impacts are now area- and mass-weighted (mynnred's impact_aw.py).
- 02 wording: the host's species mass = true mass × 1/[(1 − qv_in)(1 + r_v,new)].
- For issue text: NCAR/MYNN-EDMF since ebd5d2d (Feb 2025) builds Dth in its FLAG_QI branch from the INPUT sqc/sqi, so
  the fill is counted once there and a scratch copy would drop it; the ELSE branch, the CCPP copy and the MMM/MPAS copy
  still double count. 01b v2 (move the call after Dth) is correct for both forms.

### 10.5 Final gates (x10/m10, -no-fma)
- Meters passive: x10 vs m10, 3 suites, all switches on: 0 differ.
- Switches off: inert (fx6 vs fxa6 round 1; 06 off: r2x_p8 vs fxa6_p8 0 differ).
- 3×8 = 4×6: p8_mynn default and all-on, RAP all-on, gfdlmpv3: 0 differ.
- Restart 12+12 and 4×6 (rs10p p8_mynn all-on, rs10r RAP all-on; jobs 10157084/085): 0 differ in atmf024, sfcf024, RESTART.
- Debug-only tools (not deliverables): `tools/dbg_samf.py`, `dbg_samf2.py`, `dbg_cmake.py`, `cmp_dump.py`,
  `cmp_samfdbg.py`, `cmp_samfcp.py`, `find_target.py`, `cmp_smh.py`.
- Round-2 jobs: builds 10156489, 10156494/509/514 (dh), 10156648, 10156704 (dg), 10156754 (di), 10156756 (m9),
  10156832 (dg2), 10156887 (dg3), 10156950 (x10/m10); runs 10156431, 10156442, 10156547, 10156579, 10156600, 10156649,
  10156724, 10156741, 10156769, 10156834, 10156877, 10156924, 10157001, 10157020; red team 10157084, 10157085.

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| Suites: E.3 MYNN-EDMF, E.4 GFDL MP v3, E.5 Grell–Freitas — water, passive tracer and energy in their own suites | title | current (same title in the head) | `report.md`, `report.history.md` |
| Status (18 Oct 2026, round 2 done) | summary, patch table, series order, meters | superseded by `## Status` | `report.history.md` |
| 1. Setup | trees, cases, tools | archival | `report.history.md` |
| 2. The meter (`meters/`) | probes, residual definitions, meter validity | archival | `report.history.md` |
| 3. E.3 MYNN-EDMF (`FV3_GFS_v17_p8_mynn`; also `FV3_RAP`) | MYNN causes (a)–(f), gate, impact | current; fix (e) is v2 and (d) and impacts are corrected by 10.4 | `report.md` |
| 4. E.4 GFDL MP v3 (`FV3_GFS_v16_gfdlmpv3`, control_iovr4_gfdlmpv3, `do_sat_adj = .true.`) | mass-basis cause, fix 02, gate, impact | current; energy gap superseded by 10.2 (fix 07) | `report.md` |
| 5. E.5 Grell–Freitas (`FV3_RAP`, rap_control) | GF causes, fix 03, gate, impact | current | `report.md` |
| 6. Passive tracers (all suites) | tracer mass in these schemes | current | `report.md` |
| 7. Gates (all -no-fma, 24 h, atmf024 + sfcf024 + RESTART, every numeric variable) | round-1 gates | superseded by 10.5 Final gates (x10/m10, -no-fma) | `report.history.md` |
| 8. Out-of-scope observations | satmedmfvdifq residual, h2ophys, p8_mynn layout | superseded by 10.1 and 10.3 | `report.history.md` |
| 9. Jobs | job IDs, run directories | archival | `report.history.md` |
| Log (as it happens) | round-1 lab notebook | archival | `report.history.md` |
| 10. Round 2 (coordinator items 1–3 and mynnred corrections) | parent of 10.1–10.5 | current | `report.md` |
| 10.1 p8_mynn decomposition → fix 08 (BUG FIX, SAMF deep) | fix 08 | current | `report.md` |
| 10.2 Design energy gaps | MYNN 06, GFDL 07, GF gap | current | `report.md` |
| 10.3 satmedmfvdifq water residual → fix 05 (NUMERICAL CONSISTENCY) | fix 05 | current | `report.md` |
| 10.4 mynnred corrections | 01b v2, 01(d), weighting, 02 wording | current | `report.md` |
| 10.5 Final gates (x10/m10, -no-fma) | final gates, round-2 jobs | current | `report.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
