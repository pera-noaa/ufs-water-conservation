# Triage of the conservation fixes not yet posted upstream

## Status (29 October 2026)

- **91 unposted items** in the source documents, after removing everything posted (ccpp-physics #401, #404, #405–#410, #413,
  #414; NCAR/noahmp#274; GFDL_atmos_cubed_sphere#430/#431; WM #3404, #3406; replies on #401, #403, #405, #408).
- **Tiers:** READY 21 · NEEDS A RUN 14 · NEEDS A DECISION 39 · DROP or PARK 17.
- **READY is mostly issues.** 13 of the 21 need no ufsatm/WM slot: 10 round-2 questions, the GFDL issue, the NCAR/TEMPO
  report and the MPAS series. The READY code fixes (FX1, SG1, FV1, INLQ; TH2, TH6, TH7; SAMF32) wait on a slot:
  `dev/emc` plus the #401 answer for FV3, package 2 merging for Thompson, and SAMF32 has no slot at all.
- **Largest READY / NEEDS-A-RUN items.** Their denominators differ, so they cannot be ranked against each other:
  TOPT (+110 to −142 W/m²; non-default `tend_opt` only), GF (−30 % of GF's own precipitation), MYNN (+4.5e-2 kg/m²/day;
  2–3.5 % of precipitation in the MYNN suites; +8.0 W/m² of fill heat), MLM (−1.28 W/m² with `mlm` on), NCAR/TEMPO
  (+0.38 % of TEMPO precipitation, and its sign fix moves TEMPO precipitation −5 %).
- **Largest water item overall:** NM2, where land gains 3–5 % of global precipitation. It is NEEDS A DECISION. HAFS runs
  Noah, so NM2 is clear of the 1d HAFS hold, and whether to split it out of 1d is Ash's call (inferred).
- **Contradictions:** 17, listed under *Flags*. The ones that matter: whether TH8 is held or unconditional, how E.2 is
  classed, whether the MPAS TH6 refill was ever run in a model, and where rap's water loss sits.
- **Method.** This file reads only the documents. "Inferred" marks every judgement the documents do not state. Paths:
  see *Legend*.

## Legend

Citations are `file:line`. **RM** `README.md` · **P** `proposal/post/POSTING.md` · **PH** `proposal/post/POSTING.history.md` (grepped) ·
**r1** `proposal/pr_round1.md` · **d1** `proposal/pr_round1_descriptions.md` · **r2** `proposal/round2_issues.md` ·
**wp** `proposal/water_closure_proposal.md` · **cp** `proposal/conservation_proposal.md` · **pt** `proposal/conservation_patches.md` ·
**ser** `conservation/replay/SERIES.md` · **tr** `conservation/TRACKER.md` · **po** `proposal/patches/ports/README.md` ·
**ti** `proposal/post/tempo_attr/ncar_tempo_issue.md` · **tres** `proposal/post/tempo_attr/results.md` ·
**uc** `conservation/upchk/report.md` · **sr** `proposal/post/samf_returns/README.md`.

The evidence column scores the bar in RM:23-26:
- **C**: a code-level explanation.
- **M**: a meter showing the fix closes exactly its term.
- **F**: a forecast against the unfixed run, within the defect's own signal, judged against the `consv_te` = 0.999 noise
  (global T rms 0.149 K, ps 8.41 Pa; cp:133-134).
- **R**: a red team (restart, decomposition, other suites).

Each is scored y (done), part (partly done), n (not done) or – (does not apply).

## Table

### A. Round-1 leftovers: 1c FV3, 1d surface, 1e Thompson, build, and the dropped Noah-MP fixes

| # | id | scheme / file | fixes | measured size | evidence | blockers | repo | tier |
|---|---|---|---|---|---|---|---|---|
| 1 | FX1 (1c) | `fv_mapz.F90` | `consv_te` fixer weight ≠ the heat capacity it heats | fixer error −5.5e-4 → −3.6e-10 W/m² (cp:151) | C y; M y; F y: T rms 0.148 vs noise 0.149 (cp:151), bitwise in WoFS (r1:186); R part: the whole round is 123/123 reproducible (r1:159), but `do_sat_adj` is exact to first order only (cp:562) | `dev/emc` merge, which is rare (r1:80); the #401 answer (RM:69) | GFDL_atmos_cubed_sphere `dev/emc` | READY |
| 2 | SG1 (1c) | `fv_sg.F90` | `fv_sg` relaxes T, u, v, w separately, losing KE | −1.58e-4 → +3.0e-11 W/m² (cp:152) | C y; M y; F y: sponge only (cp:152), WoFS +0.25 % (r1:186) against WoFS noise 0.18–0.34 % (r1:160); R part, as #1 | as #1 | GFDL `dev/emc` | READY |
| 3 | CP1 (1c) | `atmosphere.F90` `atmosphere_state_update` | physics heating applied to the new layer mass | −8.63e-3 → 3.9e-10 W/m² (cp:153) | C y; M y; F **part**: f24 T rms 0.159 K (cp:153), `regional_wofs_tempo` −0.83 % = 2.4× WoFS noise (r1:186), with no defect-signal argument given (inferred); R part | as #1 | GFDL `dev/emc` (driver) | NEEDS A RUN |
| 4 | FV2 (1c) | `atmosphere.F90` `statein` | tracers divided and multiplied by different thicknesses | tracer +3.07e-15 → 5.2e-17 per day (cp:154) | C y; M y; F part: global T rms 0.148 K is at noise (cp:154), but WoFS −0.43 % is 1.3× noise (r1:186); R part | as #1 | GFDL `dev/emc` (driver) | NEEDS A RUN |
| 5 | FV1 / W19 (1c) | `atmosphere.F90` `prsl` | `prsl` built with the dycore's single-precision gas constant | 4e-8 of evaporation → 2e-16; 32-bit only (wp:59, d1:259) | C y; M y; F y: within noise (po:336), WoFS −0.24 % (r1:186); R part | as #1 | GFDL `dev/emc` (driver) | READY |
| 6 | INLQ (1c) | `sw_core.F90` `d_sw` | `inline_q` damping uses a different `delp` on each side of a PE boundary | tracer mass 1.0–1.9e-9 → 5.9–8.4e-15 per day, with `inline_q` only (cp:160) | C y; M y; F –: bitwise with `inline_q` off, and no RT uses it (cp:160); R y (gates, trdyn) | as #1 | GFDL `dev/emc` | READY |
| 7 | GFDL issue (d1 §2) | issue text for #1–#6 | the GFDL guide asks for an issue before the PR | — | text ready (d1:48-58) | goes with 1c (r1:559-560) | GFDL_atmos_cubed_sphere | READY |
| 8 | NM2 (+09b) (1d) | `GFS_surface_loop_control_part2`, `noahmpdrv` | with `frac_grid`, 24–27 % of land is stepped twice every step | land gains **3–5 % of global precipitation** (wp:48, d1:186) | C y; M y; F y: the bug's own signal (r1:57), land T2m +0.033 K (po:331); R: two forms equivalent within noise (r1:498); HAFS runs Noah, so NM2 never acted there (r1:19) | held with 1d (RM:70); the form, (a) loop control or (b) `iter`, is asked in the PR itself (d1:202) | ccpp-physics (+ NOAA-EMC/noahmp in form b) | NEEDS A DECISION: post it ahead of the sea-ice hold? (inferred) |
| 9 | SI1 (1d) | `sfc_sice.f` | ice stepped twice in 1.9 % of ice column-steps | ≈ −0.010 W/m²; calls 1.0186 → 1.0000 (cp:302) | C y; M y; F part: ice thickness rms 1.7e-3 m vs noise 8e-5 (d1:192), not argued as the defect's signal; R **fails**: with 0b, `hafs_global_1nest_atm` crashed 3/20 vs 0/20 (r1:171) | rerun those HAFS members with the #414 floor (RM:70); the #401 answer; two forms (r1:498) | ccpp-physics | NEEDS A RUN |
| 10 | SI2 (1d) | `sfc_sice.f` `ice3lay` | excess heat divided by Δt a second time | did not fire in the March case (cp:303) | C y; M –; F –; R as #9 | as #9 | ccpp-physics | NEEDS A RUN |
| 11 | FL1 (1d) | `sfc_sice.f` `ice3lay` | flooded snow becomes ice at the layer T, not at −L_i | −7.87e-3 → −1.15e-13 W/m² (cp:307) | C y; M y; F part, as #9; R as #9 | as #9 | ccpp-physics | NEEDS A RUN |
| 12 | QR1 (1d) | `sfc_nst.f90` | `rain` (m per step) used as kg m⁻² s⁻¹ | rain heat flux × 1000/720 at Δt 720 s (d1:190); qrain 0.300 → 0.417 (cp:305) | C y; M y; F y: NSST-internal, noise (cp:305); R as #9 | as #9 | ccpp-physics | NEEDS A RUN |
| 13 | TH2 (1e) | `module_mp_thompson.F90` | settled cloud water not counted; cloud sedimentation not substepped | removes 0.15 % of grid-scale rain (wp:39); `regional_control` reported precipitation +10.9 % (other form +4.8 %) (r1:58) | C y; M y; F y: reported only, 3-D T +0.0008 K (r1:179); R y: in the 37 (r1:159) | package 2 merged first (r1:58); the owners choose the form (posted with both, RM:71); `pr1-thompson_p1` 4afaf48a not compiled on the new base (PH:150) | ccpp-physics | READY |
| 14 | TH6 (1e) | `module_mp_thompson.F90` | clipped condensate deleted; vapour floor filled from nothing | creates 0.002 % (wp:43) | C y; M y; F y (r1:58); R y; edges remain (wp:522-523) | as #13 | ccpp-physics | READY |
| 15 | TH7 (1e) | `module_mp_thompson.F90` | sub-R1 water deleted | removes 2e-8 of precipitation (wp:44) | C y; M y; F y; R y | as #13 | ccpp-physics | READY |
| 16 | SAMF32 (row 25) | UFSATM `ccpp/CMakeLists.txt` | `-DSAMFCNV_32BIT=ON` reached 2 of SAMF's 5 files | the option did nothing; ON: tracer mass ~1e-10 per day; OFF: bitwise (cp:398) | C y; M –; F y: `control_p8_samf_conv32` −0.50 %, −0.0027 K, "SAMF now single precision" (r1:170); R y: in `rt_x0b` and the 37 (r1:17, r1:161) | no slot: ufsatm#1156 says "No ufsatm code change" (`posted/ATM_1156.md`:2), so the repackaging orphaned it (inferred) | NOAA-EMC/ufsatm | READY |
| 17 | NM5 | `module_sf_noahmplsm.F90` | snow without layers under 1e-3 mm deleted | 0.009 % of global precipitation, lost from land (wp:51) | C y; M y; F y (po:336); R part | dropped from round 1: "where truncated water ... goes is a choice" (r1:450); no round-2 text exists (inferred gap); #410 says the thin-snow fix "comes later" (`posted/PR_NM2_410.md`:9) | ccpp-physics (+ NOAA-EMC/noahmp, NCAR v5: wp:590) | NEEDS A DECISION |
| 18 | NM8 | `noahmpdrv`, Noah-MP lsm and glacier | Noah-MP charges its own latent heats, not the host's | the land pays 0.41 % more latent energy than its vapour carries, +0.131 W/m² per land column (wp:54, wp:74) | C y; M y; F y (po:336); R y: run-phase form (po:102-105) | dropped: "Noah-MP's own constants look moderately intentional" (r1:450); kept as `pr1-noahmp-withNM8` | ccpp-physics | NEEDS A DECISION |

### B. Round-2 issues (r2), one question each with a tested patch

The opening condition, "after round-1 track 0b is in review" (r2:5), is met in substance: tracks became packages (P:8),
and all three are in review (inferred).

| # | id | scheme / file | fixes | measured size | evidence | blockers | repo | tier |
|---|---|---|---|---|---|---|---|---|
| 19 | R2-1 T1 (02b) | `samfdeepcnv.f`, `samfshalcnv.f` | explicit TVD tracer update at Courant numbers up to 5 | a non-PBL tracer piles up 100–200× in the lowest layers in 24 h; o3 increment error median 19 % at Courant > 2; negative TKE 13 % → 1.6 % (r2:28-35) | C y; M y: mass 3e-15/day; F part: zonal T ≤ 6 mK, but 9–13 of 72 cells fall outside a 4-member spread where 3.6 are expected (r2:34); R y: red-teamed by trred (cp:263) | "if #401 adopts [option A], re-measure ... before opening" (r2:41-43). #401 went with the `xlamue` floor (#414), not A. Re-measure on #405 + #408 + #414 (inferred) | ccpp-physics | NEEDS A RUN: one C96 24 h metered run plus a 4-member spread on the package-1 head (inferred) |
| 20 | R2-2 TH8 + TH9 with E2 `fwet` | `module_mp_thompson.F90`; Noah-MP `fwet` | sub-threshold surface sedimentation lost; placeholder sediments; any canopy ice hides the liquid | water 7.1e-12 kg/m²/s, energy 2.37e-6 W/m² (cp:280); TH8 alone: canopy evaporation −68 % at f06 (cp:280); E2 opt 1/2: +32/+36 %, land LH +1.5/+1.2 % (r2:62-66) | C y; M y; F y with E2 from 6 h on (cp:281); R y (canopy) | owner questions (r2:68-69); text must be refreshed for #406 | ccpp-physics | READY (issue) |
| 21 | R2-3a NM7 | Noah-MP `canwater` | condensation heat without condensed water | 0.023 W/m² per land column (r2:82) | C y; M y; F y (po:336); R part | owner question (r2:82); "round-1 Noah-MP PR (#TBD)" (r2:77) must now name #409/#410 | ccpp-physics | READY (issue) |
| 22 | R2-3b NM9 | Noah-MP glacier | glacier snow set by assignment; the water goes nowhere | one column −860 mm in 120 days (harness); all snowfall on land ice deleted (r2:83) | C y; M y in the harness only (po:278-286); F n in the model; R part | owner question; a frozen-runoff flux needs an interface change (r2:83, wp:512-514) | ccpp-physics | READY (issue) |
| 23 | R2-3c NM10 / NM10r (17r) | Noah-MP, `noahmpdrv` | `opt_snf = 4` gives convective precipitation the grid-scale frozen fraction | host and Noah-MP disagree on 5.0 % of land convective column-steps, 0.83 % of the mass, 4.9e-3 W/m² (cp:341-343) | C y; M y: 1.2e-10 of frozen mass (cp:344); F y: land means at noise (cp:346); R y: replay (ser:20) | owner question (r2:84); decided internally as PC, unconditional (cp:625) | ccpp-physics | READY (issue) |
| 24 | R2-3d NM11 + CMC (row 35) | Noah-MP | ground vapour charged at `hvap` while it comes from snow ice; three canopy charge mismatches | NM11 0.13–0.61 W/m² over a snow season, up to 78 W/m² in one step (r2:85); CMC 0.0148 → 0 W/m² (cp:306) | C y; M y; F **beyond noise**: snow cover +0.16 % (r2:85), soil T1 +0.010 K vs noise −0.003 (cp:306); R y: full UFS reproducibility (po:21-23) | owner question (route the heat to soil layer 1?) | ccpp-physics | READY (issue) |
| 25 | R2-4 GF | `cu_gf_driver.F90` | shallow-only precipitation unreported; mass basis; floors | −0.137 kg/m²/day = **−30 % of GF precipitation** → 2.5e-16 (r2:99) | C y; M y; F: precipitation +8.9 %, rms 1.0–1.4× noise (r2:100); R y: 44 GF RTs (wp:834) | owner question: unconditional, or `gf_closure` (default off, cp:622) | ccpp-physics | READY (issue) |
| 26 | R2-5 DY1–DY3 (`dyn_te_exact` bits 1–16) | `dyn_core`, `sw_core`, `fv_dynamics` | `d_con` heat ×c_p/c_v; KE about the half-damped wind; Rayleigh at c_v | +0.2905, −0.0195, +6.4e-4 W/m²; fixer −0.570 → −0.304 (r2:115-126) | C y; M y; F y: T 0.153 K (r2:126); R y: dycred, FV3's own `ENG Deficit` (cp:192-195); nwat 7, non-MOIST_CAPPA and MULTI_GASES compile only (cp:559-561) | owner question: bits unconditional? (r2:128-129); natural companion of 1c | GFDL `dev/emc` (also `main`) | READY (issue) |
| 27 | R2-6 R1 | `dcyc2t3`, `GFS_typedefs` | radiative heating applied to a stale layer mass | −7.65e-3 W/m² (Σ\|r\| 2.70e-2) → −8.4e-14 (r2:137-139) | C y; M y; F y (cp:210); R part: SCM and MPAS hosts not tested (cp:564) | sequencing: host fields in SCM, ufsatm and the MPAS host (#397) first (r2:141-143) | ccpp-physics + SCM + ufsatm | READY (issue) |
| 28 | R2-7 TOPT | interstitials, `dcyc2t3` | process-split tendencies dropped for some `tend_opt` combinations | **+110 to −142 W/m²** in the broken combinations → 2.08–3.12 (r2:151-156) | C y; M y; F y: the default (2,3) is bitwise, and fixed (2,1) and (2,2) are at noise (cp:386); R y | overlaps #397 (r2:158-159) | ccpp-physics | READY (issue) |
| 29 | R2-8 MYNN 01 + 01b | `module_bl_mynn.F90` | surface-flux density, dew limiter, filler mass; fill heat counted twice | water +4.5e-2 → 5e-15 kg/m²/day, which is **2–3.5 % of precipitation** in the MYNN suites (wp:787); fill heat +8.0 W/m²; T −0.063 K, ps rms 2.4× noise (r2:167-175) | C y; M y; F: beyond noise, the bug's signal (cp:411); R y: mynnred (cp:418) | after #392 (r2:165); our question "still present in `main`?" (r2:177-178) can be answered by reading `main` ourselves (inferred) | NCAR/MYNN-EDMF | NEEDS A RUN: a code read of NCAR/MYNN-EDMF `main`, no compute (inferred) |
| 30 | R2-9 F3 01b | SAMF, `GFS_typedefs`, `GFS_diagnostics` | SAMF's `wet_dep` is never exported | export matches the meter to 1.3e-11 (cp:257) | C y; M y; F –: no forecast effect (r2:188); R y | feature question: wanted? (r2:188) | ccpp-physics + ufsatm | READY (issue) |

### C. Conservation follow-on options (cp: "the physics changes and options come later", cp:7). All are switched, default off

All are off by default and bitwise when off (cp:130-131). Each was cut on `fx`, `all_full` or `full10`, so each needs
re-anchoring onto `ufs/dev` after the bug fixes merge (pt:229-234). Decided settings: cp:613-635.

| # | id | scheme / file | fixes | measured size | evidence | blockers | repo | tier |
|---|---|---|---|---|---|---|---|---|
| 31 | D1 `dspheat_ke` | `satmedmfvdifq` | dissipative heating ≠ the KE the momentum solve removes | PBL +1.4273 → +1.6e-12 W/m², the largest single gap (cp:35, cp:221); also closes #403's sa3dtke residual (uc:108) | C y; M y; F **beyond**: T2m rms 0.334 vs 0.156 (cp:221); R y | owner judgement; open: ignore `dspfac` when on? (cp:626) | ccpp-physics + ufsatm | NEEDS A DECISION |
| 32 | PBK | `satmedmfvdifq` | filler at constant h_vap, not L_h(T) | +4.8e-5 → 0 W/m² (cp:222) | C y; M y; F noise; R y | whether to propose options | ccpp-physics + ufsatm | NEEDS A DECISION |
| 33 | PBF | `satmedmfvdifq`, `atmosphere.F90` | PBL condensate transport treated as vapour in C1 bit 4 | −0.00485 → 8e-13 W/m² (cp:223) | C y; M y; F in the all-on set; R y | depends on C1 | ccpp-physics + ufsatm + FV3 | NEEDS A DECISION |
| 34 | D3B `samf_cmt_heat` | SAMF | CMT removes KE with no heating | deep −0.1191, shallow −0.0289 W/m² (cp:248) | C y; M y; F noise (+0.002 K); R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 35 | D4 + D12 `gwd_ke_heat` | `ugwpv1_gsldrag`, `GFS_GWD_generic_post` | GSL drag and the PBL×GWD cross term unheated | −0.3198 and −0.0663 W/m² (cp:249) | C y; M y; F beyond noise (cp:626); local 100–210 K/day near the lid; R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 36 | D4n `ngw_heat_opt` | `ugwpv1_gsldrag` | NGW heating from a prescribed flux: a net source | +0.335 W/m² (cp:250) | C y; M y; F beyond noise; option 2 chosen (cp:627); R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 37 | S1 + S1K `samf_kirchhoff` | SAMF (+ encpl 06 export) | SAMF condenses at constant h_vap | remainder deep −0.245, shallow +0.128; S1K gap +0.080 → 1e-13 W/m² (cp:251-252) | C y; M y; F rms at noise, precipitation +0.6 %; R y | owner | ccpp-physics + ufsatm + FV3 | NEEDS A DECISION |
| 38 | K1 `thompson_kirchhoff` | Thompson | own c_p and L(T), with constant L_s, L_f | latent heat −0.14 % / −0.24 % / +1.3 % at 220–250 K (cp:282) | C y; M y; F noise; R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 39 | TFH `thompson_frame_heat` | `mp_thompson` | per-layer heating ≠ the frame-F latent heat | +0.0083 → 9e-13 W/m² (cp:283) | C y; M y; F noise; R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 40 | C1 `cpl_water_energy` bits 1/2/4 | `atmosphere.F90` | water PE, flow work (±R_v·T), sensible enthalpy of moving water | −0.480, −0.620, +1.773 W/m²; together LH −2.04 W/m², precipitation −3.4 % (cp:163-169) | C y; M y; F **beyond**: the largest systematic signal, "no real-model column test" (cp:628); R y: fwred | owner judgement; no forecast improvement shown (cp:628) | GFDL `dev/emc` (driver + model) | NEEDS A DECISION |
| 41 | C8 | `atmosphere.F90` | KE of water mass written at the layer winds | −0.0025 → 0 W/m² (cp:166) | C y; M y; F noise; R y | goes with C1 | GFDL driver | NEEDS A DECISION |
| 42 | D7 + D7S | `atmosphere.F90`, `fv_control` | A→D wind-increment KE ≠ the physics' KE change | −0.0202 KE row → −1e-10 net; D7S peak 0.871 → 0.0131 K/step (cp:161-162) | C y; M y; F noise with D7S, "not recommended without D7S" (cp:161); R y | owner | GFDL | NEEDS A DECISION |
| 43 | DRY (03b) | SAMF, `satmedmfvdifq` | chemistry tracers moved with moist fluxes while the write-back keeps dry mass | uniform dry tracer rms 1.07e-3 → 2.3e-5 (cp:255) | C y; M y; F –: T and q bit-identical; R y: trred | PC for chemistry tracers only, no switch (cp:255) | ccpp-physics | NEEDS A DECISION |
| 44 | DYN v6 `dry_tracer_adv` / `_ic` / `dry_negadj` | FV3, 9 files | water species limited separately; the IC moist/dry basis; `neg_adj` | with DRY: uniform tracer 1.22e-2 → **4.9e-13** max in 24 h (cp:360-361) | C y; M y; F –: weather bitwise, +1.5 % cost (cp:356); R y: off bitwise, 3×8 = 4×6, restart, OpenMP (cp:365-366); regional BC and HAFS moving nest untested (cp:557-558) | owner; `dry_tracer_ic` set per run (cp:630) | GFDL `dev/emc` | NEEDS A DECISION |
| 45 | CH1 / CH2 `noahmp_canopy_heat` | Noah-MP `vege_flux` | canopy heat storage books only the last Newton increment | 0.052 → 3e-17 W/m² (cp:319) | C y; M y; F: CH1 noise-ish (T rms 0.161), CH2 large (t2m +0.27 K) (cp:319); R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 46 | PH1–PH3 `precip_phase_host` | `GFS_MP_generic_post`, Noah-MP | the atmosphere pays no fusion heat for host-classified convective snow | PH1 = h_fus × host convective snow, 0.0725 W/m² (cp:320) | C y; M y; F noise; R y | owner; partly subsumed by NM10r (ser:30) | ccpp-physics + ufsatm | NEEDS A DECISION |
| 47 | SW1 `noahmp_sw_radshare` | Noah-MP | Noah-MP absorbs SW with its own albedo and geometry | −0.093 → 0 W/m² (cp:321) | C y; M y; F **beyond**: land uSW rms 12.1 vs noise 2.1 (cp:321); R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 48 | LW2 `lw_sfc_return` | surfaces | surfaces emit at the current T while the LW uses radiation-time fluxes | closes to 5e-14 W/m² (cp:322) | C y; M y; F beyond: soil T1 +0.12 K (cp:322); R y | owner (LW1 superseded) | ccpp-physics + ufsatm | NEEDS A DECISION |
| 49 | EV1 `sfc_evap_enthalpy` | Noah-MP soil + glacier | frame-F enthalpy of evaporated water | soil term +0.1255 W/m²; applied = booked to 6e-17 (cp:323) | C y; M y; F T rms 0.159 K; R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 50 | AD1 `noahmp_heat_advect` | Noah-MP soil | soil water carries no sensible heat | 0.058 → 1e-14 W/m² (cp:324) | C y; M y; F noise; R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 51 | KF1 `noahmp_kirchhoff` | Noah-MP | melt and freeze at constant h_fus | 0.200 → 2.8e-8 W/m², at step 1 only (cp:325) | C y; M y; F noise; R y | a trade-off: 6 % of h_fus at −10 °C (cp:325) | ccpp-physics + ufsatm | NEEDS A DECISION |
| 52 | EP1 + PL1 `sfc_precip_enthalpy` | `GFS_MP_generic_post`, surfaces, `GFS_restart` | precipitation lands without its frame-F enthalpy, and a step late | PL1 lag −1.2106e-2 → 0 W/m² (cp:328); EP1 removes −1.78e-3 (cp:326) | C y; M y; F noise; R y: one restart field (cp:328) | owner; PL1 folded into EP1 (cp:624) | ccpp-physics + ufsatm | NEEDS A DECISION |
| 53 | AIR1 `noahmp_pore_air` | Noah-MP soil | pore air's heat moves with water, unbooked | 2.4e-3 → 8.5e-15 W/m² (cp:327) | C y; M y; F noise; R y | owner | ccpp-physics + ufsatm | NEEDS A DECISION |
| 54 | E1 `nst_spray_opt` | `sfc_nst`, `sfc_ocean` | explicit sea spray oscillates where the gain > 2 | oscillating cells 271 → 2 in 10 days; LH −0.21 W/m² (noise −0.03) (cp:330) | C y; M –: conserves by construction; F beyond noise; R part: `sfc_ocean` compile only (cp:565) | opt-in (cp:635); owners may prefer a PBL-coupled solve (cp:337-338) | ccpp-physics + ufsatm | NEEDS A DECISION |
| 55 | MYNN04 `mynn_sfc_heat` | MYNN | surface heat applied without 1/Π | 16.72 vs 16.97 W/m² reported (cp:412) | C y; M y; F noise; R y | after #392 | NCAR/MYNN-EDMF | NEEDS A DECISION |
| 56 | MYNN06 `mynn_mix_sl` | MYNN | mixes θ_l, not an energy | θ_l gap 0.47 → 2e-9 W/m² (cp:413) | C y; M y; F rms 1.3–1.5×; R y | opt-in (cp:623); after #392 | NCAR/MYNN-EDMF | NEEDS A DECISION |
| 57 | `dyn_te_exact` bits 32, 64 | `dyn_core`, `fv_mapz` | sponge layers damped with no heat; remap TE change not returned | −1.69e-3 and −0.1144 W/m² (cp:159) | C y; M y; F: fixer −0.417 with 127 (cp:159); R y | design options (cp:633); asked in R2-5 (r2:128-129) | GFDL `dev/emc` | NEEDS A DECISION |
| 58 | MPAS 0010–0014 | MPAS-A | meter, labelled fixer, opt-in layer coupling, dissipative heating | 0012: heating +7.3 % (cp:459-460); 0014: fixer 3.81e5 → 1.31e5 J/m² (cp:466-467) | C y; M y; F beyond: storm stronger (cp:461); R y: 7/12/16 tasks, restart (cp:470-471) | whether MPAS wants instrumentation in-tree (inferred); defaults decided (cp:631) | MPAS-Dev/MPAS-Model | NEEDS A DECISION |

### D. Ports (po; "The ports are not posted", po:3) and the NCAR/TEMPO report

| # | id | scheme / file | fixes | measured size | evidence | blockers | repo | tier |
|---|---|---|---|---|---|---|---|---|
| 59 | NCAR/TEMPO report (owed by #407) | `module_mp_tempo_main.F90` | 1 semi-Lagrangian fallback sign; 2 graupel re-closure; 3 entry density; 4 cloud settling; commit 3 r1 floors | TEMPO creates **+0.377 %** of its precipitation (tres:3). T1 alone 0.58–0.64 % (6–24 h; ti:10, tres:9); graupel 0.86 % at 0–6 h; the sign fix moves grid-scale precipitation **−5 %** (ti:28) | C y; M y: closes to −2e-7 (tres:3); F part: one case, "no TEMPO noise pair" (tres:34-35); R y: still upstream, leave-one-out, alternatives (tres:22-35) | split into a sign-fix issue plus one-line PR, then fixes 2–4 (P:16-17); fix 4 has three forms and commit 3 is a judgement fix (tres:25) | NCAR/TEMPO | READY |
| 60 | TEMPO driver TH5 twin (`ports/TEMPO-driver/0002`) | `mp_tempo.F90/.meta` | driver layer depth from `phii`, not the host's mass | removes 0.011 % of TEMPO precipitation (tres:13); dz check 4.7e-3 → ≤4.7e-16 (po:50) | C y; M y; F n: no TEMPO noise pair (tres:34); R n | left out of #407: "not measured alone in UFS, and it adds a `.meta` argument" (r1:547-548) | ccpp-physics | NEEDS A RUN: one C96 TEMPO run pair (`consv_te` 0.999) (inferred) |
| 61 | MPAS 0001–0009 (Thompson water, scalar transport v2, TH8/TH9) | MPAS-A | the Thompson fixes, monotonic-clip and negative-zeroing transport, TH8/TH9 | ΔW/W 1.3e-3 → −1.6e-16 over 24 h (cp:453) | C y; M y; F: precipitation within noise (po:266); R y: v2 red team passed (po:37), gates bitwise (cp:470-471) | owned by the UFS-Chem-2 session (cp:435); see contradiction F5 | MPAS-Dev/MPAS-Model | READY |
| 62 | WRF Thompson (5 commits) | WRF `module_mp_thompson` | TH2–TH4, TH6 + refill, TH7 noreturn, TH5-WRF, TH2/TH3 completion | mp 8/28/38: +1.5e-2 → +1.4–1.7e-6 of P, supercell 2 h (po:31) | C y; M y; F y (po:203-204); R part: TH6's refill and TH7's noreturn harness-only, "not rerun" (po:10, po:206) | none filed (wp:774-775) | wrf-model/WRF | NEEDS A RUN: one WRF supercell with the refill commits (inferred) |
| 63 | WRF W1, W2 | `module_diffusion_em.F`, `module_big_step_utilities_em.F` | horizontal diffusion not in flux form (W1); surface flux set to the first interior flux (W2) | W1 −1.07e-3 → +9.8e-6 of P; W2 +0.923 → −5.4e-6, idealized no-PBL only (po:33-34, po:115-116) | C y; M y: in-model probes, pre-registered (po:189); F y: within the pre-registered bounds (po:203-204); R n: no restart or decomposition test documented (inferred); 1e-5 left unlocated (po:18) | none filed | wrf-model/WRF | NEEDS A RUN |
| 64 | WRF W3 | WRF theta | the W2 form applied to θ | cold pool θ′ rms 2.06 → 1.60 K (po:114-115) | C y; M y; F beyond | "a separate decision" (po:114) | wrf-model/WRF | NEEDS A DECISION |
| 65 | NM12-EMC (20b) | NOAA-EMC/noahmp `src/` | NM12's companion in the EMC copy | per firing up to 0.16 mm, 8.5 MJ/m² (cp:308) | C y; M –; F –; R n: "not built in any UFS tree" (pt:186) | — | NOAA-EMC/noahmp | NEEDS A RUN: build plus one land-component test (inferred) |
| 66 | NOAA-EMC/noahmp series (`noahmp-emc_develop_D_H_I_K_L`) | NOAA-EMC/noahmp | NM1, NM5, NM6, NM8, NM7, NM9, NM10, 09b | land component Σ residual −5.2e-4 → −8e-13 of ΣP (po:272-273) | C y; M y; F n; R part: NM9 and NM10 harness only (po:278-291) | follows the UFS decisions on NM5, NM6, NM8 and R2-3 (inferred) | NOAA-EMC/noahmp | NEEDS A DECISION |
| 67 | ccpp-physics production branches | GFS.v17, HAFS.v2.2, RRFS.v1, SRW v3, AQM.v7 | the UFS series adapted, plus NM8 run-phase, NM9, NM10 | GFS.v17 R_tot/P +0.24–0.27 % → 0.00 % (po:42) | C y; M y for GFS.v17; F part (po:330); R part: RRFS, AQM and SRW not built (po:43) | whether operations want backports (inferred); carries NM8, which develop dropped (r1:450) | ccpp-physics `production/*` | NEEDS A DECISION |
| 68 | NCAR/noahmp NM5–NM7 issue (`ncar_noahmp_issue_draft.md`) | NCAR Noah-MP v5 | thin snow, canopy truncation, condensation without water | as #17, #21 | text drafted, not posted (po:65) | the same choices as #17 and R2-3a (inferred) | NCAR/noahmp | NEEDS A DECISION |
| 69 | `held/` TH8 + TH9 in every port | each Thompson copy | as R2-2 | as #20 | held "by the user" (po:14-15, po:63) | conflicts with the 18-Oct unconditional decision (F1) | WRF, MPAS, TEMPO, production | NEEDS A DECISION |
| 70 | NM11 port to other copies | every Noah-MP copy | as R2-3d | as #24 | not ported (po:21) | "Porting is the user's call" (po:23) | NCAR, EMC, production | NEEDS A DECISION |

### E. Others' PRs (#403, #390), the #408 early returns, and #401 follow-ups

| # | id | scheme / file | fixes | measured size | evidence | blockers | repo | tier |
|---|---|---|---|---|---|---|---|---|
| 71 | #404 MLM fix | `mfscuq_mlm.f`, `satmedmfvdifq.F` | non-conserving cloud-base smoothing; `−ΔF/dz` without density; `ntsw`/`ntinc` indices | with `mlm` on: **−1.28 W/m²**, +4.39e-4 kg/m²/day; the smoothing alone −0.88 W/m², −6.0e-4 (uc:18-19, uc:29) | C y; M y for the defect; fix "compiles, not yet run in the model" (`issue_390_mlm_body.md`); F n; R n; the meter perturbs the MLM-on run (uc:12) | #404 has no reply (P:50); 40–52 K cold columns untraced (uc:32) | ccpp-physics | NEEDS A RUN: one C96 24 h metered run, `mlm` on and off (uc:114) |
| 72 | #403 `diff3d` mass-weighted fix (`reply_403_3.md` draft) | FV3 `diff3d`, `satmedmfvdifq` | tendencies cancel per area, not per mass | 0.05–2.7 % of the gross; C96 24 h: T −1.5e-3 W/m², `sphum` −1.3e-5 kg/m², o3 +6.8e-9 of its mass (r1:461) | C y; M y for the defect; the fix is untested (uc:114) | Han: diffusion to become optional (PH:149); also unraised: a uniform tracer may get a tendency where `dx` varies, read from the code (r1:461) | ccpp-physics#403 / GFDL#429 (comment) | NEEDS A RUN: one C96 24 h run in the #403 tree (uc:114) |
| 73 | #403 sa3dtke PBL energy | `satmedmfvdifq` with `sa3dtke` | `def_1` production with no KE sink | PBL residual +1.43 → +2.51 W/m² (uc:57); D1 closes it to −1.8e-3 (uc:97, uc:108) | C y; M y; gates bitwise (uc:60-62); attributed to sa3dtke, not to #403's additions (uc:71) | not posted (inferred); the fix is D1, a PC option (#31) | ccpp-physics#403 (comment) | NEEDS A DECISION |
| 74 | SAMF deep early-return deletion / `pending` single exit | `samfdeepcnv.f` | early returns make results depend on the block (CA, progomega, coldpool, MG) | block test: #403 6/11, #408 11/12 identical, 11/11 and 12/12 with `pending` (sr table); physics cost +1.3 % (sr:42) | C y; M –; F y: bit-identical in `control_p8` (sr:35); R n: "not checked in a full UFS RT or a layout test" (sr:43) | Lisa's answer; `reply_408_returns.md` held (P:13-15) proposes a PR of its own after #403 | ccpp-physics | NEEDS A DECISION, then a full RT |
| 75 | #401 follow-ups | SAMF | which of 2a95266's three parts moves precipitation; residual 4–9 K steps at CFL 1–5.4; shallow not floored | — | offered, not run (r1:444); "Not diagnosed" (r1:411-413); "Shallow untouched" (r1:384) | #414 approved; these are investigations, not fixes | ccpp-physics | PARK |

### F. Parked, dropped, or not a fix (kept so nothing is lost)

| # | id | what | size | why | tier |
|---|---|---|---|---|---|
| 76 | NOAA-EMC/noahmp PR §5 (`iter`) | the companion for NM2's form b | — | only for form (b); the PR prefers (a) (d1:202, r1:498) | PARK |
| 77 | RRFS 0cd3e23 09b companion | 09b for RRFS's noahmp pin | — | form b only (po:61) | PARK |
| 78 | SAMFCFL (option A) | CFL cap on the SAMF mass flux | — | a new limit (rule 2; r1:99). Han accepted the floor (r1:384), posted as #414 and approved (P:55). Superseded (inferred) | DROP |
| 79 | NM6 | canopy water ≤ 1e-6 mm deleted | 4e-7 of land precipitation (wp:52) | dropped as a choice (r1:450) and tiny (inferred judgement) | PARK |
| 80 | NP1 | the heat of a melted-out snow layer deleted | did not fire (cp:304) | dropped (r1:73, r1:450); never fired in a test | PARK |
| 81 | E4b `gfdl_mp_host_cp` | GFDL constant-pressure switch | GFDL gap 0.117 → 0.085 W/m² | "tested, not proposed" (cp:426-427, pt:199) | DROP |
| 82 | WRF-tempo | `rho_dry` into TEMPO in WRF, on TEMPO round 2 | +1.17e-2 → +8.4e-7 of P (po:32) | built on TEMPO round 2 with TH8; waits for NCAR/TEMPO (#59) (inferred) | PARK |
| 83 | TEMPO-scheme pin ports (2856696, 881614f, 9adf9ef) | the TEMPO fixes on each host's pin | as #59 | reach UFS or WRF "only when they move their pins" (po:52) | PARK |
| 84 | ufs-MPAS-thompson | ufs-community/MPAS-Model `noaa/develop` | — | "unused inside UFS today" (po:57) | PARK |
| 85 | csawmg | Chikira–Sugiyama suite creates water | +10.5 % of precipitation per 6 h (wp:837-838; po:314) | not located, no fix | PARK |
| 86 | rap R_dyn | water lost outside the metered physics | −6 to −9 % (po:25, po:315) | not localised; see F6 | PARK |
| 87 | FV3 adiabatic | the spatial discretization creates energy | +0.4145 W/m² (cp:525-539) | "Closing it would change the discretization, so we propose nothing" (cp:537-538) | PARK |
| 88 | MYNN residuals | `sfcdif4` leaves NM1 incomplete (wp:517-518); `rhosfc/rho1` on sensible heat and drag (po:318) | — | no patch | PARK |
| 89 | SAMF `cnvtrans` diagnostic | `dtend_*_cnvtrans` always zero | — | a diagnostic gap, requested (wp:527-528, wp:597); no patch | PARK |
| 90 | cold-start IC terrain | the IC is built on unfiltered orography | −0.0024 kg/m² once (wp:524-525) | belongs on the IC side (`USE_GFS_ZS`) | PARK |
| 91 | MPAS logged items; the 9adf9ef sedimentation | condensate zeroing above the top and others (cp:472-474); ice sedimentation applies 1/steps of the flux (po:405) | — | "Logged, not fixed"; inactive here, or "not water" | PARK |

The water proposal's open points on the canopy evaporation cap and frozen-canopy transpiration (wp:507-516, "we propose
none") are now covered by CMC (cp:306), which R2-3d asks about. They are not counted separately (inferred supersession).

## Tiers

**READY (21).**
- **1c: FX1, SG1, FV1, INLQ** (#1, #2, #5, #6). Code, meter and red team done. Each is at noise or bitwise in WoFS
  (r1:186). The slot is the `dev/emc` merge plus the #401 answer (RM:69).
- **GFDL issue** (#7). The text is ready (d1:48-58), and it goes with 1c.
- **1e: TH2, TH6, TH7** (#13–#15). Code, meter, forecast and red team done (r1:58, r1:179). The slot opens once package 2
  merges. Before pushing, a compile of 4afaf48a on the posted base is still owed (PH:150).
- **SAMF32** (#16). Build fix, gated bitwise off. The RT changes only `_conv32` (r1:170). No package holds it.
- **R2-2, R2-3a–d, R2-4, R2-5, R2-6, R2-7, R2-9** (#20–#28, #30). Each is one question with a tested patch. The texts
  still carry `#TBD` and stale references (r2:77, r2:41-43) and need a refresh.
- **NCAR/TEMPO report** (#59). Leave-one-out attribution and red team are done (tres:22-35). Owed since #407 (P:16-17).
- **MPAS 0001–0009** (#61). Bitwise gates and a 24-h closure; another session owns it.

**NEEDS A RUN (14).**
- **CP1, FV2** (#3, #4). WoFS is 2.4× and 1.3× noise with no defect-signal argument. Missing: a WoFS meter run
  attributing the change to the term each fix restores. Cost: one WoFS run pair (inferred).
- **SI1, SI2, FL1, QR1** (#9–#12). Missing: `hafs_global_1nest_atm` members on 0b + sea ice/NSST + the #414 floor
  (RM:70). Cost: a 20-member 6-h HAFS ensemble, about 20 HAFS runs; the original was 20 members (r1:171).
- **TEMPO TH5 twin** (#60). Missing: a TEMPO `consv_te` noise pair. Cost: one C96 run pair.
- **R2-1 T1** (#19). Missing: a re-measure on the package-1 SAMF. Cost: one C96 24 h run plus a 4-member spread.
- **R2-8 MYNN** (#29). Missing: a code read of NCAR/MYNN-EDMF `main`, to answer our own question. Cost: no compute.
- **WRF Thompson refill** (#62). Missing: one WRF supercell run, 2 h.
- **WRF W1, W2** (#63). Missing: WRF restart and decomposition pairs. Cost: two short idealized runs (inferred).
- **NM12-EMC 20b** (#65). Missing: a build plus `datm_cdeps_lnd_gswp3`. Cost: one land-component test.
- **#404 MLM fix** (#71). Missing: the fix run in the model. Cost: one C96 24 h, `mlm` on and off.
- **#403 `diff3d` fix** (#72). Missing: the fix run in the #403 tree. Cost: one C96 24 h.

**NEEDS A DECISION (39).**
- **NM2** (#8). Post it ahead of the sea-ice HAFS hold? HAFS runs Noah (r1:19).
- **NM5, NM8** (#17, #18). Dropped as choices (r1:450), and no round-2 text exists.
- **Options** (#31–#58, 28 rows). All are switched and default off. When and which to propose is the open question.
  Several are beyond noise and need owner judgement: D1, D4, D4n, C1, SW1, LW2, CH2, E1, MPAS 0012/0014.
- **W3** (#64), a separate WRF decision.
- **EMC noahmp series, production backports, NCAR NM5–NM7 issue, `held/` TH8/TH9 in the ports, NM11 ports**
  (#66–#70). Each follows the UFS-side choices.
- **sa3dtke finding on #403** (#73). It is sa3dtke's, not #403's (uc:71), and its fix is an option.
- **SAMF early returns** (#74). Waits on Lisa (P:13-15).

**DROP or PARK (17).** #75 and #76–#91, as listed in sections E and F. They are:
- superseded: SAMFCFL by #414;
- tested and rejected: E4b;
- tiny or never fired: NM6, NP1;
- form-b-only companions;
- pin ports that wait on NCAR/TEMPO;
- unlocated losses: csawmg, rap;
- design or IC-side items with no proposal.

## Flags

### Superseded or withdrawn: do not resurrect

| Item | Replaced by | Source |
|---|---|---|
| Tracks 0b, 0c and their ufsatm/WM bodies | packages 1–3 | P:8, P:65 |
| `ccpp_physics_issue_draft.md` (issues 1–7) | r1, d1, r2 | `ccpp_physics_issue_draft.md`:3-7 |
| E.2 candidate `issue4_noahmp_fwet_mass_weighted.diff` and its numbers | E2 row 42; withdrawn for the `cwat` shadow | cp:578, pt:201 |
| Row 16 TH8 alone; `thompson_sed_actual`; `sfc_precip_t1_carry` | row 43 (TH8 + TH9 unconditional); row 46 | ser:26-28 |
| NM10 (diff 17) | NM10r (17r) | cp:341-348, ser:20 |
| SA1 first form; T1 donor-layer start (02); DRY 03; DYN v1, v5; `dyn_te_exact` v1; MYNN 01b v1; ensfc2 07 and 16; encnv per-layer round-1 D3A, D3B, D4 | final forms | pt:189-198, cp:586, po:391 |
| LW1; SL1 (misattributed) | LW2; SL2, CS1, CB1 | cp:322, cp:594 |
| MPAS tally v1; MPAS dissipative heating v1; MPAS-dynamics v1; TEMPO rounds 1–2 | v2, 0014 v2/v3, `MPAS-conservation` 0005–0007, round 3 | cp:580-581, po:58, po:401-404 |
| GFDL MP mass basis in-module (`pr1-gfdlmp` 919ab856) | the wrapper form in #413 | PH:131 |
| "TH8 is about noise"; "E.1 no fix proposed"; GF "+8.6 %" | corrected | cp:582, cp:602-603 |
| SAMFCFL | the #414 floor (inferred) | r1:384, P:55 |

### Contradictions between documents

| # | Topic | One document says | Another says |
|---|---|---|---|
| F1 | TH8 status | po:14: "TH8 is held (user decision) in every copy except MPAS" (dated 17 Oct, po:3) | pt:21: "row 16 (TH8) is retired into 43, which ships TH8 + TH9 unconditionally"; cp:620: "BUG FIX, unconditional" (18 Oct) |
| F2 | E.2 class | po:16-17: "fixing it moves land beyond noise, so it is issue 4 …, not a fix" | cp:329: "BUG FIX, switched (beyond noise)"; tr:65: "BUG" |
| F3 | Round-1 membership of NM5, NM6, NM8 | wp:6: "`pr_round1.md` (TH1–TH7, NM1–NM6, NM8, FV1, 09b …)" | r1:450: NM8, then NM5, NM6 and the melt-out heat fix "also dropped" |
| F4 | Upstream state | wp:20-21: "None has been reported or fixed upstream" | P:5-21: 8 PRs posted, 4 approved |
| F5 | MPAS TH6 refill and TH7 noreturn in a model | po:10: "Harness only, not yet rerun in a model: … TH6's refill and TH7's noreturn (WRF, MPAS, production)"; po:161: "The MPAS copies are syntax-checked only." | po:56, po:59: `MPAS-conservation` 0001–0004 = `MPAS-thompson/`, which includes "TH6 with its refill; TH7 with noreturn", measured over 24 h (po:38) |
| F6 | Where rap's water goes | po:315: rap "−6.0 / −5.8 / −4.8 % … lost outside the metered physics (R_dyn); not localised" | wp:830: "On 24-h C96 `rap_control`, GF loses 30–34 % of its own precipitation, all in shallow-only columns"; cp:416 closes GF to 2.5e-16 |
| F7 | NM7 size | wp:53: "0.024 W/m² per land column" | r2:82: "0.023 W/m² per land column"; wp:75 "(from −0.023)" |
| F8 | GF precipitation change | wp:789, wp:835: "+8.6 %" | r2:100, cp:416: "+8.9 %"; acknowledged at cp:603 |
| F9 | TEMPO sign-fix size | ti:10: "creates 0.58 %" (6–24 h) | tres:9: "creates ≈ 0.64 %"; explained at tres:32 (leave-one-out from L_3 vs T0 − T1). ti:6's +0.38 % vs #407's +0.33 % is explained at tres:27 |
| F10 | #405 sequencing | r1:25: "#405 merges after #403"; r1:463: "merge after #403" | RM:40: rebase only "if … #403 … merges first"; `posted/PR_XLAMUE_414.md`:7: "Dependencies: None. Pairs with #405" |
| F11 | Status of the descriptions | d1:3: "Drafts, not posted, except §8" | §1 is posted as WM#3404 (P:51); §3.1–3.6 as #406–#410, #413 (P:58-62) |
| F12 | Round-2 opening condition | r2:5: "Open after round-1 track 0b is in review" | P:8: "Tracks 0b/0c are replaced by these packages" |
| F13 | T1's prerequisite | r2:41-43: re-measure "if #401 adopts" option A | #401 went with the `xlamue` floor (#414; P:55) |
| F14 | Posted list in the round-1 header | r1:5: posted PRs "#405 (SA1), #406 (Thompson) and #407 (TEMPO driver)" | P:9-12: #408, #409, #410, #413, #414 also posted |
| F15 | Other suites | po:25: "MYNN-EDMF and GFDL MP v3 fixes proposed" | GFDL MP v3 is posted (#413, P:60); MYNN is only round-2 issue 8 (r2:19) |
| F16 | NM8 across copies | r1:450: NM8 dropped from develop as "a coupling choice" | po:62: the production branches carry "NM8 in the run phase" |
| F17 | 1d count | RM:70: "surface iteration, sea ice, NSST (6)" | d1:182: "Five fixes"; the sixth is 09b (r1:74). Counting only |

**Label collisions** (a hazard when citing):
- **T1** is both SAMF tracer sub-stepping (cp:254) and the TEMPO sign fix (po:88, tres:9).
- **R1** is the radiation fix, the Thompson placeholder (cp:118) and red-team finding R1 (r1:306).
- **C1–C3** are the coupling switch (cp:163), the TEMPO fixes (tres:42-44) and the old letters for TH2–TH4 (po:381-383).
- **M1** is a TEMPO run (tres:45) and the old letter for TH6.
- **D1** is `dspheat_ke` (cp:116) and the old letter D for NM1 (po:387).
- **F1–F5** are TEMPO red-team findings (po:138-142), and F3 is also SAMF wet deposition (cp:256).
- **A, B, F** are #401 fix options (r1:241-343) and also old fix letters (po:381-387).

### Duplicates across documents (one fix, several write-ups)

- **TH8/TH9:** wp:493-503 · cp:280-281 · ser:27 · r2:47-69 · po:14, po:63, po:81-84 · MPAS 0008–0009 (cp:444).
- **E2 `fwet`:** wp:800-813 · cp:329 · r2:55-68 · po:16 · tr:65.
- **NM7, NM9, NM10, NM11:** wp:53-57 · r2:80-85 · cp:341-348 · po:60, po:62, po:107-112.
- **MYNN 01/01b:** wp:815-820 · cp:410-411 · r2:163-178 · po:64, po:312.
- **GF:** wp:828-835 · cp:416 · r2:89-104.
- **DY1–DY3:** cp:155-157 · r2:109-129 · tr:37.
- **R1, TOPT:** cp:210, cp:386 · r2:133-159 · r1:86-92.
- **T1 (02b):** cp:254 · r2:24-43 · tr:74.
- **F3 01b:** cp:257 · r2:182-188.
- **SAMF32:** cp:398 · d1:285-300 · r1:76 · tr:90 · ser:90.
- **TEMPO scheme fixes:** ti (the whole file) · tres · po:51-52 (the `TEMPO-scheme` ports).
- **1c:** d1:48-58, d1:245-267 · r1:80 · cp:151-160 · wp:59.

### Natural ufsatm/WM groupings for later packages (inferred)

The code managers want one ufsatm/WM pair per group (P:5-8).
- **P4, FV3 dycore and driver:** 1c (#1–#6) with the GFDL issue (#7). DY1–DY3 (#26) join once the owners answer R2-5.
  One GFDL `dev/emc` PR. The baseline changes in every FV3 test.
- **P5, surface stepping, sea ice, NSST:** NM2 (#8) and SI1, SI2, FL1, QR1 (#9–#12). The R2-3 answers (#21–#24), NM5
  and NM8 could follow in the same group, or as a Noah-MP follow-on, if the owners want them.
- **P6, microphysics follow-on:** TH2, TH6, TH7 (#13–#15), TH8 + TH9 once `fwet` is settled (#20), and the TEMPO TH5
  twin (#60). Only Thompson and TEMPO tests would change.
- **P7, SAMF follow-on:** T1 (#19), wet-deposition export (#30), the early-return deletion (#74, after #403) and
  SAMF32 (#16, ufsatm only, `_conv32` tests).
- **P8, host fields and interstitials:** R1 (#27, after SCM/ufsatm/MPAS host fields) and TOPT (#28, after #397). Both
  touch `GFS_typedefs` and the interstitials.
- **Other suites:** GF (#25); MLM (#71); MYNN (#29) goes via NCAR/MYNN-EDMF and the #392 submodule, not a ufsatm/WM
  package of ours.
- **Options (#31–#58).** Default off is bitwise in `-no-fma` builds (cp:130-131). Adding statements to physics files
  can still change release-build answers through FMA contraction (cp:138-143; RM:103-104). So even an options-only
  package should expect one baseline change (inferred).

### Out of scope here

- The FMS/spack-stack FPE track (RM:76-81).
- The meters and conservation CI, stages A–C (RM:89-111), which are not fixes.
- The Hercules cleanup (RM:83-87).
- The posted items' open review threads (#407, #409, #410, #413, #430/#431, NCAR#274).
