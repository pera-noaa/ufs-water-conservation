# Is moisture conserved in UFS-Chem v1? Code audit and measured budget

Code: Jian He's `dev-am4` (ccpp-physics `f70b191`, fv3atm `a5c4305`, dycore `d4838c3`); suite `FV3_GFS_v17_p8_ugwpv1`
(Thompson, `satmedmfvdifq`, SAMF deep + shallow, Noah-MP, `h2ophys`); case `control_p8_ugwpv1` (24 h, C96 L127,
2021-03-22 06Z, dt 720 s). "Conserved" means total water Σq·Δp/g over the six species changes only by surface
evaporation, surface precipitation or a documented deliberate source. Line numbers below are in this snapshot; the
`ufs/dev` equivalents are in the proposal's Appendix B.

## Status (15 October 2026)

- **Dry air, the dynamical core and the physics → dynamics update conserve water**, measured exactly: in-model meters
  around `fv_dynamics` (incl. `neg_adj3`), `fv_subgrid_z`, the update write (incl. `fill_gfs`) and `fv_update_phys`
  change water by < 3 × 10⁻⁷ kg/m² per step (32-bit round-off; ~10⁻¹² in 64-bit; `fill_gfs` and `fv_update_phys` never
  fired, so their meters show inactivity), and R_dyn = 0 to 10⁻⁶ per window
  (`wb_herc_wbfzcpd`, `wbfzcpd64`, `wbctlp`).
- **The physics does not.** Unmodified, it adds +0.25–0.29 % of precipitation per 6 h at C96 (+0.45 % at C384 on
  current upstream): SAMF creates ~0.8 % of convective rain (SA1); Thompson removes ~0.67 % of grid-scale precipitation
  (TH1–TH4).
- **Proposed set (01–19, + 09b in NOAA-EMC/noahmp; final19 = the same without NM11):** SA1, TH1–TH7, NM1–NM11, FV1; **TH8 held** with its
  placeholder fix TH9 (`proposal/patches/held/`). Final tree `$U/patched19` (all 12 changed physics files byte-identical
  to `water/all`) and metered `patched19m`: 24 h total 0.00000 per window after the first at dt_inner 720 and 150
  (`wb_m19_di720`, `_di150`); metered physics R −5.50e-7 / −2.47e-7 kg/m² per 24 h, one-signed, max column 2.2e-4 /
  3.0e-4 (the sub-threshold surface sedimentation TH8 counts); BL added − booked 1.5e-11 / 1.6e-16 of E; metered
  atmf024 byte-identical; forrtl 0; no "negative qv". 10 d (`wb_d10_m19`) 0.00000 days 2–10, C384 (`wb_c384_m19`) 0.00000 after the first window; vs develop only the
  per-fix signals (canopy evap +10 %, sublimation +5.7 %, precip −0.7 %); full suite
  `rt_full19`: 54/54 compiles, 17 PASS, 180 BASELINE, 8 not completed (6 /work2 I/O, 2 atm-lnd without 09b; with 09b
  `control_p8_atmlnd`, `_debug`, `cpld_control_p8_lnd` complete), 29 restart/decomp not started (parents change
  baselines), no PT range violations (rt_full17 had 9). Triage `$U/triage_apera/`. **Final tree 01–19 + 09b
  (`$U/p20rt_final`), reproducibility:** baselines from the tree (job 10125027, `-c`: 165 PASS, 0 fail, incl. the 5
  former I/O tests and 3 land tests), compare (10127943, `-m`: 222 PASS, 0 not identical, 12 infra failures) and retry
  (10130763: 15/15) = **234/234 PASS**, incl. 34 restart, 17 decomp, 14 threads, 1 MPI; no crash/NaN/FPE/FATAL/PT in
  any run dir. Private baselines `$U/p20rt_suite/stmp/apera/FV3_RT/REGRESSION_TEST` (564 GB, delete when done).
- **With TH8 as well** (the earlier final tree `patched18` = 01–18 with earlier NM2/NM4/NM8 forms and no NM10): physics R
  −9.68e-15 / −7.84e-15 kg/m² per 24 h (max column 1.9e-13 / 2.2e-13), 10 d 0.00000 every day, C384 0.00000. Older
  upstream builds (`patched17*`) carried SA1's first form. Earlier stages: with SA1 and TH1–TH4 the total is −0.005 % of
  precipitation at C96 upstream (−0.003 % on v1; −0.006 % per day over 10 days, no drift) and −0.001 % at C384; NM1
  closes the land–atmosphere hand-off exactly (+0.07–0.10 % → 0). With SA1, TH1–TH4, TH5, TH6 and NM1 (`wb_herc_wbfzdm`) the whole
  model closes to < 10⁻⁶ kg/m² per 6 h; the earlier +1 × 10⁻⁵ was TH5 using the host's gas constants for Thompson's ρ.
  Fix SA1 does not change how often SAMF's negative borrowing acts (~0.03 % of deep-convecting columns either way).
- **Regression fixes found by the suite:** NM4 built zero-water snow layers from old-format coupled ICs (guard added);
  NM8's and NM2's new `noahmpdrv` arguments broke atm-lnd builds, where NOAA-EMC/noahmp's stale driver copy calls the
  ccpp-physics routine positionally (NM8 moved to the run phase; NM2 optional + companion 09b). Unmodified develop passes
  all 12 tests that crashed. CCPP optional args are passed by pointer, so host parameters cannot be optional targets.
- **Not posted.** None of these is fixed or reported upstream. Diffs in `proposal/patches/`, named by number and
  label in application order (01 SA1 … 07 TH7, 08 NM1 … 17 NM10, 18 NM11, 19 FV1 in GFDL_atmos_cubed_sphere `dev/emc`; 09b
  NM2's NOAA-EMC/noahmp companion; held/TH8, held/TH9). Issues 3–7 drafted (NSST spray, Noah-MP canopy wetness, MYNN,
  GFDL MP v3, Grell–Freitas shallow precipitation: `FV3_RAP` −2 to −7 % of P per 6 h; candidate
  `proposal/patches/candidates/issue7_*` closes GF to its 0 floor but adds +8.6 % global precip). Issue 4 candidate
  (mass-weighted fwet blend, `$U/patches/test/issue4_blend.diff`): makes TH8+TH9 within noise, but alone moves the land
  as much as the max form (canopy evap +20 % ×77, T2m −0.09 K): 45 % of wet-canopy steps are mixed-phase. Labels were renamed by home on 15 Oct (was → now: A→SA1, B→TH1, C1–C3→TH2–TH4, M4→TH5, M1→TH6,
  M5→TH7, M2→TH8, 13a→TH9, D–I→NM1–NM6, L→NM7, K→NM8, N→NM9, O→NM10, J→FV1); diff numbers in the dated entries below
  are the old ones.
- **Other hosts:** TH2–TH4 are in the Thompson scheme itself (also in WRF, MPAS, TEMPO); TH1 and NM1 are CCPP-interface
  defects (WRF/MPAS pass dry mixing ratios; NCAR's Noah-MP drivers pass the water mass flux). Proposal Appendix C.
- **Output `dpres` is delp·(1 − condensate)** (`fv_nggps_diag.F90`, GFS_PHYS), the physics' dry+vapour thickness;
  tracers are per total mass. W = Σq·dpres/g produced a spurious "dynamics loss" (−3…−6 × 10⁻⁵ kg/m² per 6 h,
  +1 × 10⁻⁴ in the first window). All budgets re-run with W from dpres/(1 − condensate) (`reanalysis_fixW/` on
  Hercules); totals moved by ≤ 0.006 % of P, per-scheme columns by up to −0.04 % of P_grid.
- **TH3 is mostly a spin-up fix:** −0.76 % of grid-scale precipitation in the first 6 h of a cold start, about −0.03 %
  after; column meter and host budget agree on its 24-h effect (−0.22 %, −0.21 %).
- **The per-scheme split resolves differences between builds, not absolute levels below ~10⁻⁴ kg/m² per 6 h**
  (6/3/2/1-h thickness: R_mp −0.17 → −0.11 % of P_grid, split "dynamics" +1.2 → −1.4 × 10⁻⁴ where the truth is 0).
- **Microphysics, by in-model meters:** driver meter = column meter + 0.0035 % of P_grid in the first-TH5 builds, which is
  exactly the 3.5 × 10⁻⁵ gas-constant mismatch. With SA1 and TH1–TH4 about −0.01 % (column +0.002 %, stale `dz` −0.014 %),
  matching the exact SA1 and TH1–TH4 total (−0.003 % of P); with SA1 and TH1–TH4 + TH5 (Thompson's constants) + TH6, < 10⁻⁶ kg/m² per 6 h.
- **Cold start, traced** (`coldstart_trace.py`, offline replica, matches the model's post-IC totals to 2 × 10⁻⁵): the IC
  surface is `orog_raw` exactly, the model runs on `orog_filt` (up to 500 m apart), so `remap_scalar` re-fits ps on
  model terrain (−1.7 Pa mean, `PS_diff`): −0.0024 kg/m². Top layer −3 × 10⁻⁷; `delp`/(1 − cond) is a basis change
  (true IC water = Σ q·delp/(1 − cond), +0.0006 over the stored-basis figure); adiabatic init ≈ +0.0003. Fix on the IC
  side (`orog_filt`) or `USE_GFS_ZS`.
- **NM1 verified exactly** (`wb_herc_wbfzl` without, `wbfzdl` with; land meters): atmosphere receives − land debits =
  +4.5…+6.9 × 10⁻⁴ kg/m² per 6 h without NM1, 0 to machine precision with NM1; Noah-MP `density` ≡ PBL `ρ_a`; PBL adds what
  it books to 4 × 10⁻⁸. Precipitation hand-off exact (Noah-MP `prcp` = host `tprcp` to 10⁻¹⁶, one step late). Noah-MP
  is excluded from the second surface iteration, so no double stepping.
- **Land (Noah-MP storage meter, `wb_herc_wbfzdn*`):** two host-side defects.
  NM2: `GFS_surface_loop_control_part2` re-flags coastal (wet and dry) cells for the second surface pass and
  `noahmpdrv` re-steps their land from the updated state, no restore: 24–27 % of land re-stepped every step, land gains
  +3.3–5.3 % of global P (`wbfzdnq`). NM3: `GFS_surface_composites_pre` overwrites persistent `weasdl` with the cell-mean
  `weasd` each step; Noah-MP rebuilds layered snow (its +3.7 kg/m² per 6 h `errwat`), thin snow is lost. With NM2 + NM3
  (`wbfzdnef`) `errwat` = −6 × 10⁻⁵ kg/m² per 6 h globally, between-call changes 0, glacier exact.
  NM4: `GFS_phys_time_vary_init` builds Noah-MP's snow layers from the cell-mean `weasd`/`snowd`, not `weasdl`/`snodl`;
  Noah-MP rebuilds its total from the layers on step 1: −0.29 kg/m² global mean (`wbfzdnefx`), 0 with NM4 (`wbfzdnefg`).
  NM5: Noah-MP zeroes snow without layers at `sneqv <= 1e-3` mm (`energy`, `snowh2o`, end of `noahmp_sflx`) without
  passing it on; canopy ice drip (`precip_heat`) lands ~1e-4 mm per step on snow-free ground, and `snowh2o` deleted
  it: the whole steady `errwat` (−15.6 mm summed over 1.77 M soil column-steps; WBK meter: 15.60 mm in `snowh2o`,
  0.02 in `energy`, 0 at the end). NM5 puts it in soil layer 1 as ice: `errwat` −0.014 mm, no column-step ≥ 10⁻⁴ mm, land
  within-call balance 0.00000 mm per 6 h (`wbfzdnefj`). The −0.014 mm (4 × 10⁻⁷ of land P) is NOT rounding:
  all negative, 10⁴ × double eps on stored water; the 326 worst column-steps (`wbfzdnefk`, WBX > 1e-7) all have
  aquifer exchange, 290 at zwt = 2.50 m — selection effects (wa changes everywhere; 2.5 m is the common zwt).
  NM6: `canwater` zeroes `canliq`/`canice` <= 1e-6 mm (ufs/dev L7346, L7355; v1 L7328, L7337) with no flux; the deleted
  canopy water (WBC meter, `instrument_wb_noahmpc.py`) = 0.0141 mm vs errwat −0.0141, every snow state to 1e-4, on 5 %
  of column-steps. Fix NM6 (final) returns it from `canwater` (qcanl, qcani) and `water()` adds it to qrain/qsnow/snowhin:
  no phase change, energy-neutral, independent of NM1; errwat −3.1e-9 mm in 6 h (`dev_epq`). The first version (via
  `ecan`, `apply_noahmp_i_ecan_patch.py`) gave −1.1e-8 mm in 24 h (`dev_noahmpci24`) but left the latent heat unpaid
  (≤ 3.5e-3 W/m² at a point, ~3e-5 W/m² land mean; the agent's "< 4e-6 W/m²" was off by 1000). Fast dev path
  `variants/wbdev`. Not the 0.001 literal (≤ 1e-3 mm, cancels).
- **Physics in double precision** (`instrument_wb_ep.py`, `ep_meter_budget.py`; per step and column, physics water vs
  E added by the PBL, P reported, h2ophys): −1.46e-7 kg/m² per 6 h with SA1, TH1–TH6 and NM1–NM6 (`dev_epq`), 93 % in Thompson
  sedimentation = TH8: `r(kts) > R1·rr_min` gates only the precipitation count, the flux always leaves. With TH8
  (`dev_epm2`) −1.56e-8 (2e-8 of P), max column 1.7e-8; WBT total = R to 3 digits, rest = Thompson entry clip
  (−9.2e-9) + sedimentation (−6.3e-9). NOT rounding: upstream (double-precision Thompson, `develop` + 01–14,
  `$U/rt/wb_ups_m14m2`) −1.54e-8/6 h, −6.03e-8/24 h. Three R1 deletions: entry else-branches L2267/2294/2323/2334/2343
  (−9.2e-9), semi_lagrange_sedim exclusion L6271 + `max(qn,R1)` floor L6455 (gross 8.6e-6 per 6 h each way, net −6.1e-9),
  rain qrten overwrite L3322–3339 (−1.6e-10). **TH7** (diff 07; to vapour with latent heat; `rql = qn + (rql − qq)`;
  nr floor R2 in caller; `apply_thompson_m5_patch.py` = diff 07 byte-for-byte): upstream 01–14 + TH7 (`wb_ups_m14mf2`)
  R −4.0e-15/24 h, max column 2e-13, negatives at exit unchanged 1.87e-5 vs 1.88e-5, forrtl 0, metered vs unmetered
  atmf024 byte-identical. v1 (single-precision Thompson) all fixes + NM7 + TH7 (`dev_m5`): R −6.19e-8 → −4.26e-15/24 h,
  max column 1.9e-8 → 9.3e-13, R_dyn ≤ 1e-6/window, total 0.00000/window, errwat −1.18e-8 mm, forrtl 0. The earlier "thresholds not needed" test
  resolved only 1e-5. PBL added 4.11e-8 of E more than it booked (+3.1e-8 kg/m²/6 h) = FV1: the FV3 driver builds prsl = dm·rTv/Δφ with
  the dycore's `rdgas` (float32 287.04998779 in a 32-bit build) and the PBL/Noah-MP divide by `con_rd` (287.05):
  predicted 4.25e-8. rTv with con_rd, con_fvirt → 1.6e-16 (`dev_eprtv`, 6 h), 4.9e-16 (`dev_epj`, 24 h). Final 24 h, all fixes
  (SA1–NM8, `dev_m5`): physics R −4.3e-15 kg/m² (1.5e-15 of P), Noah-MP errwat −1.2e-8 mm, R_dyn ≤ 1e-6 per window. First meter build
  read 1/12 of E and P: CCPP runs each scheme over all 12 blocks per rank before the next, so module hand-offs need
  per-step queues.
- **NM8 (energy side of NM1):** Noah-MP charged hvap 2.5104e6 / hsub 2.844e6, the atmosphere's vapour carries con_hvap /
  con_hvap+con_hfus: land paid +0.131 W/m² per land column more (0.41 % of 31.8 W/m² latent; `instrument_wb_noahmpg.py`,
  `dev_k0`). NM8 = latent heats from the host in noahmpdrv_init (diff 15): exactly 0 (`dev_k1`), water unchanged. Left:
  Noah-MP's own water vs latent heat, −0.0228 W/m² (`dev_k2`): transpiration −0.0240 = Σ min(fctr,0) exactly (fctr < 0 on
  13 % of column-steps, etran = max(fctr/hvap,0), L7328/7334; same in v5 CanopyHydrologyMod L75/81; CTSM: no
  transpiration when efpot ≤ 0, rpp = 1 dew); canopy cap +0.0012 (1 %: cap L4269 before the tv solve L4280, linear
  update L4284 re-exceeds it; CTSM moves the excess to sensible heat); ground 0. **NM7** (diff 14; dew/frost from fctr<0,
  energy solve unchanged; `apply_noahmp_l_patch.py`, `dev_l1`): total −0.0228 → +0.0013 W/m² (= the cap term; the
  WBG split books the new dew under canopy, so canopy +0.0240 offsets transp −0.0226), errwat −1.22e-8 mm (k2 −1.21e-8),
  physics R −6.19e-8, BL gap −1.6e-16 of E, forrtl 0; ~8e-4 mm/day dew over land; with TH7 too
  (`dev_m5`) +0.0012. The canopy cap is documented only (no fix proposed: both obvious fixes change the energy partition).
- **Negative hydrometeors at Thompson's exit** (slot 9, TH6 returns them to vapour; agent, upstream `develop` + 01–17,
  `$U/rt/wb_neg_m17n2`, meter answer-neutral 98/98 files): 2.21e-5 kg/m² per 24 h (65 % at kdt 1, cold-start cloud
  water in the IC), 83 % qc = cloud sedimentation in one full DT (`vtck·DT > dz`, 2096 layers/24 h, over ocean; L4044–4057,
  other species substep L3808/3873/3922/3950), 17 % qg = diff 03's `prg_rcs = −(prr_rcs + prs_rcs)` going negative when the
  rain limiter scales prr_rcs but not a positive prs_rcs (6.6e-6 across 2294 layers). Folded into diff 03 (user, 14 Oct):
  cloud substepping by the Courant rule (one-substep control bit-identical) + cap `prs_rcs ≤ −prr_rcs` below T_0
  (`apply_thompson_c_neg_patch.py`, v1 `apply_thompson_c_neg_v1.py`): 2.21e-5 → 1.26e-8, worst −4.1e-3 → −1.5e-10 kg/kg,
  physics R −5.7e-15, forrtl 0; ΔP within a noise control (`rcsnoise`). TEMPO v3.2.5 also sediments cloud in one step.
- **Glacier, fix NM9** (diff 16; UFS-Chem-2's harness compiles the real `noahmpdrv_run`, `$SCR/redteam/noahmp/`): ufs/dev
  `snowwater_glacier` resets the pack to 3 layers, 600 mm ice, no liquid, on every call (L2653; 720/720 calls), so all
  glacier snowfall and rain is deleted (−26 mm on a 26 mm/day day), sublimation created (+0.4–0.47 mm/day), melt never
  runs off, refreeze free (16–45 W/m² of melt latent heat on 276–280 K days); one column −860 mm/120 d; glacier `errwat`
  = −(P−E−R) every call. `noahmpdrv` L960 floors glacier `weasd` at 0.1 mm every call (NOAA-EMC NUOPC: init only): where
  no reset (EMC develop, RRFS v1, SRW v3, AQM v7) it creates +2.3–2.6 mm/day (`iopt_gla` 2) / 5.9 (1) on a melting
  glacier. Thin-snow sites L357, L3347 (dead code under the reset). NM9 books all four (reset liquid → ponding2, ice →
  snoflow; layerless `qrain*dt` → ponding2; floor → −drain; end truncation → runsub; `snowh2o` → ponding2): every case
  ≤ 2.4e-13 mm, soil bit-identical. User (14 Oct): keep the reset, ice in `drain` with `FIXME` comments (`drain` read as
  liquid downstream; a frozen-runoff field is deferred). **v1 has no reset** (only the floor, noahmpdrv L740, and the
  two truncations). Model (v1): WBZ (`dev_m5z`, 24 h) and WBZ+WBGF (`dev_gfn10`, 10 d, 1315 glacier columns) 0 events;
  forced zero-snow start (`dev_gff10`, all 1315 glacier points sheleg = snwdph = 0): WBGF 278 events, +6.45 mm summed
  over columns (≈ 0.005 mm per glacier column in 10 d), none on step 1; WBZ end site 9 events, 0.60 mm (booked by the
  glacier thin-snow lines in `wbdev`), `snowh2o` 0.
- **Forecast impact** (UFS-Chem-2's red team; 24 h C96 vs 9 bit-perturbed IC pairs, ≥ 3× noise max; `$U/redteam_impact`):
  within noise TH1, TH4, TH5/TH6, NM5, NM6, FV1, NM8, TH7+NM7, TH2/TH3 completion, TH5 inner loop; beyond: SA1 first form (k=1–5 +0.010–0.014
  K), NM1 (host LH over snow −4.2 %, ×19; sublimation −12 %), NM2 (land T2m +0.033 K, coast +0.040 K, canopy evap +10 %), NM3
  (land SWE −0.45 kg/m², glacier −2.85, sublimation +5 %), NM4 (land SWE +0.69), TEMPO T1 (grid P −5 %, tropics −15…−19 %),
  and **TH8** (land canopy evap −39 % ×124, land LH −2.2 % = −0.75 W/m², tropical land snow cover 0.02 → 0.69 %, persists
  10 d). TH8 mechanism (code, ufs/dev): ice/snow flux-form sedimentation transports the R1 placeholder (empty layer
  inherits `vtsk(k+1)`, L3950; ice L3903; in-loop `max(R1,…)`), TH8 books the trace as grid-scale snow, Noah-MP
  `opt_snf=4` `fpice = prcp_frozen/prcpnonc` (L1094–1104) → 1 and is applied to convective rain too. Candidate source fix
  (extend TH7's floor start to the flux-form branches) under test (agent, `patched18ph`/`patched18nm2`). NM1's message
  reworded (host LH output changes; Noah-MP's flux does not).
- **NM10** (diff 17, user 14 Oct; written by UFS-Chem-2, split by the user 15 Oct): `atm` applies the microphysics fpice
  to grid-scale only, convective = snow if sfctmp < tfrz (host `srflag` rule, `GFS_MP_generic_post` L495–516, uses
  tsfc). Within noise alone (`wb_ph_nm2o1`). The canopy `fwet` part (ice-only whenever canice > 0, L1389/L7378; max of
  fill fractions tested, sum ≈ same) moved the 24-h land beyond noise (canopy evap +18 %, sublimation −13 %, T2m −0.11 K,
  q2m −0.9 %; `wb_ph_nm2o19` vs `wb_ph_nm2`), so it is issue 4 in the drafts, not a fix. TH8 test (agent,
  `$U/patched18ph`, `summary_ph*.txt`): Thompson placeholder fix (`fix_thompson_placeholder_sedim.py`) removes ~95 % of
  TH8's land signal (residual canopy evap −2.6 % ×10 from real upwind-diffusion traces); fix + full NM10 makes TH8 within
  noise; fix + phase-only NM10 (build 8, `wb_ph_pho1` vs `wb_ph_nm2o1`): within noise 6–24 h, but 0–6 h canopy evap
  −2.4 % ×11, sublimation +1.1 % ×14, carried by the fwet trace switch (canopy-ice steps +5.5 %, trace-ice-hides-liquid
  +6.3 %); phase channel identical. **User (15 Oct): hold TH8 with TH9** (`patches/held/`); TH8 dropped from all four
  branches by rebase (clean), TH7 and NM10 messages reworded. Final set `$U/patches/final19/` (01–12, 14–19); final tree
  `patched19`/`patched19m` and rt_full19 being built and run.
- **Other red-team findings, documented, not fixed:** sublimation/frost at hvap when tg > 0 °C with snow (0.13–0.61 W/m²
  over 120 d, 35–78 W/m² single calls; LH/con_hvap exceeds NM1's flux by 0.75–2.7 % over 120 d); canopy cap 0.053 W/m²
  forest mean (≈ 40× the land mean), ≤ 65 W/m² per call; MYNN surface layer (`iopt_sfc=4`) still derives qfx from LH; NM5
  pushes smc(1) past porosity only for implausible host SWE with depth ≤ 1e-6 m, and negative host SWE is still
  created; glacier `waxy` = 4900 set by `GFS_phys_time_vary`, zeroed on call 1 (bookkeeping); TH6 refill draws condensate
  only from the same layer (vapour-free columns still floored); TH7 entry exchange latent heat unpaid where no vapour
  (< 40 J/m²). Production RRFS v1 / SRW v3 / AQM v7 predate ccpp-physics 3fe1f187 (2025-05-08): glacier ecan/etran
  `undefined`, so NM1 there needs the zeroing (folded into their ports).
- **Passive tracers** (agent, `$V/wbtr`, `wbtr64`, `wbtrctl`; `instrument_tr.py`, `tr_meter_budget.py`; runs
  `$R/wb_herc_tr_*`; v1 wbfinal = 14 fixes): trpa (profile) and trpb (3-D: gradient, wave-2, plumes). Physics with SA1
  1e-18 of M; without SA1 SAMF deep −4.4e-6 (trpa) / +5.9e-7 (trpb) per 24 h → −0.28 / +0.041 %/yr over 10 days, persistent
  (98 % / 80 % of steps one sign); fv_dynamics ≤ 1e-4 %/yr, random sign (remap frame switch, unbiased); 32-bit
  physics → dycore write-back −0.7e-3…−4.1e-3 %/yr, 0 % of steps positive, gone in 64-bit (±5e-15); fillz,
  fv_update_phys never act. Stock v1 does not PBL-diffuse tracers beyond the standard 10 (`nvdiff` stays 10; agent forced
  nvdiff = ntrac). wbfinal 10-day runs (with and without tracers) blow up at step 771 (T_sfc 31,000 K, 73E 12.8S); v1
  unmodified, v1 + all 17 (`dev_m5d10`) and upstream + all 17 (`wb_d10_m17`) run 10 days.
- **Step-771 blow-up explained** (agent, `$V/wbosc*`, runs `$R/wb_herc_osc*`, reports `$V/wbosc/logs/rep_*_L1.txt`):
  NSST sea-spray (`lseaspray`, `conlf·ws10^5.4·(qs(T1)−q1)`, ws10 at the 30 m/s cap) is explicit on a 22 m layer, with a
  gain of ~14 per 720 s step, giving a 2Δt layer-1 oscillation in a TC eyewall (73.3E 12.8S). Thompson condenses the
  overshoot, and the layer runs away once T1 exceeds the SST (PBL −48 K / Thompson +94 K at step 737). From the step-700
  restart: unmodified v1 oscillates ±2–4.5 K with no runaway to step 800; spray off is clean; dt 360 s is bounded. Perturbing
  T by 1e-12 at step 1 flips crash/no-crash. SA1's kb heating averages 0.064 K/step in the cluster vs 0.067 in the box,
  i.e. not implicated. A saturation cap on spray (`osc_apply_spray_limit.py`) cures it but cuts spray ~10×, so it is
  not proposed. TH5's depth matches the geopotential depth (22.07 m).
- **Daily jump, explained** (agent, `$V/wbgc`, `instrument_wb_gc*.py`): v1 10-day R jumped at kdt = 120n+1 (+1.4e-6,
  one column 1.15e-2). gcycle with NSST resets sea-ice `tisfc` ~245 → 273 K (`sfcsub.F` 2494–2503) → sublimation pulse
  into an ~18 m, 250 K lowest layer (Hudson/Ungava Bay ice) → single-pass cloud sedimentation at Courant ~1.8 overdraws
  qc → TH7 exchange empties qv → `qv1d = MAX(1e-10, …)` creates water. Fixed by diff 03's cloud substepping:
  `dev_c3nd10` R −8.8e-14/10 d, max column 2.4e-13; upstream `d10_m17c` 0.00000 every day. The tisfc reset itself is
  not a water leak; not proposed.
- **Tracer write-back bias, explained** (agent, `$V/wbwb`, `instrument_wbb*.py`): round-to-nearest in the four
  `atmosphere_state_update` statements (v1 `fvGFS/atmosphere.F90` L1626 real*4 dry mass `delp*(1-Σq)+qt`, L1628 delp
  store, L1629 `q = qwat/q0`; upstream `driver/UFS` L1674/1676/1677, same code). Coherent only in the top ~40
  pure-pressure layers (same delp float everywhere, steady stratosphere, sub-ulp physics tendencies): per step −9.4e-10
  (trpa) / −3.1e-10 (trpb) of M, mostly from the delp store (−8.9e-10 / −3.6e-10); troposphere dithers out. Sign is configuration-dependent
  (stock-PBL run: trpb +7.3e-11, 100 % positive). Water: same mechanism, ~3e-10 kg/m² per 6 h, negligible. Fixes
  tried: divide by stored delp (bias flips sign, same size), real*8 dry mass (worse, touches delp). No minimal fix;
  64-bit removes it.
- **Resolved since:** SA1's deep cloud-base heating (+0.07 K per convecting column-step at kb) → SA1 (cloud-base face
  carries qo/ctro; red team ~12k soundings ≤ 3e-15); TH5 with dt_inner < dtp → depth per inner step from host dry mass
  (`dm`), di150 R +1.6e-15; qr negatives → floor start (diff 07), 1.2e-8 → 1e-17 per day; vapour floor → refill (diff 06)
  + no early return below the floor (diff 07): red-team F1 columns +0.77–1.52 kg/m² → ≤ 4e-15, neighbour fixer 46 → 0.
- **Open:** TH8 (above); final `patched18` runs and regression suite; BL added − booked gap (7.5e-9 over 10 d) and May's
  drift (deferred); nvdiff in UFS-Chem's config.

## Where water is not conserved

Line numbers in the v1 snapshot (`ufs/dev` equivalents: proposal Appendix B). Sizes are without the fix.

| | Location (v1 snapshot) | Effect | Fix and result |
|---|---|---|---|
| SA1 | SAMF deep `samfdeepcnv.f:2378-2389` (kb, jmin), tracers `:2463-2472`; shallow `samfshalcnv.f:1818-1841` | cloud-base "double counting" correction subtracts the flux-limited `tem1` while the updraft took `qo(kb)` (`:1510`, `:2016`) | cloud-base face carries `qo` (SA1), subtraction uses it; convection +0.78 % → 0.00 % of convective rain, layer kb unchanged |
| TH1 | `mp_thompson.F90:574-581` (÷(1−q_v,old)), `:783-790` (÷(1+r_v,new)); host rebuilds mass as pre-physics (dry + vapour) thickness × q (`atmosphere.F90:1616`, basis `:2141-2180`) | each species scaled by (m_d+m_v,old)/(m_d+m_v,new) | convert back with the input `spechum`; Thompson −0.67 % → −0.30 % |
| TH2 | `module_mp_thompson.F90:4049` | cloud water settling out of the lowest layer not counted as precipitation; cloud sedimentation in one full DT (others substep) | count it, substep it; → −0.15 % |
| TH3 | `:3030`, `:3151-3197` | rain–ice and cold rain–snow collection rescaled without re-closing graupel (a source, mostly during spin-up) | re-close after the limiters, snow gain capped at the rain loss; with TH2 → −0.18 % (6–24 h); −0.76 % of P_grid in 0–6 h |
| TH4 | `:3388`, `:3664`, `:3747` | `rho` recomputed after latent heating; sedimentation then runs in a frame ~ΔT/T off the host's layer mass | keep the entry density for mass; → −0.07 % (split); total −0.003 % of P |
| TH5 | driver `mp_thompson.F90:600` | `dz` from `phii`, computed before convection heats the column | `dz` from `prsi` with Thompson's ρ: +0.014 % of P_grid → 0 |
| TH6 | `:4226-4294`; vapour floor `MAX(1e-10, …)` | end-of-step clips and floors (≤ 10⁻¹² → 0); vapour floored by creating water | exchange with vapour; refill the vapour floor from the layer's condensate, then column vapour: +0.002 % → 0 |
| TH7 | `:2248-2324` (entry), `:3341` (leftover rain), `:6273, 6457` (`semi_lagrange_sedim`) | water ≤ R1 deleted | to vapour; physics −6.2e-8 → −4.3e-15 kg/m² per 24 h |
| TH8 | `:3993, 4087, 4116, 4146` | lowest-layer sedimentation counted as precipitation only above `R1·rr_min` | count all: physics −1.46e-7 → −1.6e-8 kg/m² per 6 h; **on hold** (placeholder trace → Noah-MP snow) |
| NM1 | `noahmpdrv.F90:1254` evap = LH/2.5e6; land debits LH/2.5104e6 or LH/2.844e6 (`module_sf_noahmplsm.F90:186-187, 869, 2208-2226, 7310-7316`) | atmosphere gains 1.0042× the water unfrozen land loses, 1.138× over frozen ground or canopy | pass `ecan+etran+edir`; gap → 0.00 % |
| NM2 | `GFS_surface_loop_control_part2.F90:50`; `noahmpdrv.F90:697` | with frac_grid, coastal land stepped twice per step | land once per step: +3–5 % of global P → 0 |
| NM3 | `GFS_surface_composites_pre.F90:229` | land snow overwritten with the cell mean every step | keep `weasd_lnd` |
| NM4 | `GFS_phys_time_vary.fv3.F90:487, 599` | cold-start snow layers from cell-mean `weasd` | `weasdl`/`snodl`: −0.29 kg/m² → 0 |
| NM5 | `module_sf_noahmplsm.F90:945, 2045, 8162` | thin snow without layers deleted | to soil ice: errwat −15.6 mm → −0.014 mm |
| NM6 | `:7328, 7337` (`canwater`) | canopy water ≤ 1e-6 mm deleted | to the ground with rain/snow: → −1.2e-8 mm |
| NM7 | `:7312, 7320` (`canwater`) | negative transpiration heat with no water (energy) | dew/frost: −0.023 → +0.0012 W/m² (canopy cap left) |
| NM8 | `module_sf_noahmplsm.F90:193-195`; glacier `:23-25` | Noah-MP's own latent heats (energy) | host constants: +0.131 W/m² → 0 |
| NM9 | ufs/dev `module_sf_noahmp_glacier.F90:2653` (reset), `:357`, `:3347`; `noahmpdrv.F90:960` (floor) | glacier snow set by assignment | book as runoff: −860 mm/120 d → 2.4e-13 (harness); ice in `drain` (FIXME) |
| NM10 | ufs/dev `module_sf_noahmplsm.F90:1094-1104` | grid-scale fpice applied to convective precipitation | convective phase by temperature (phase, not water); `fwet` switch → issue 4 |
| FV1 | `fvGFS/atmosphere.F90:2241` | prsl with float32 `rdgas` | `con_rd`, `con_fvirt`: PBL gap 4.1e-8 → 5e-16 of E |
| — | `h2ophys.f:125-129` | deliberate relaxation to a zonal climatology above 100 hPa | by design; ≲ 10⁻⁴ of column water |

## Conservative (code)

- **Dry air:** the physics update rebuilds delp as old dry mass + new water mass (`atmosphere.F90:1625-1629`).
- **Physics → dycore:** every advected tracer is returned as mass and divided by the new delp, so a tracer the physics
  leaves alone keeps its mass (`:1616, 1629`). `fv_update_phys`'s delp branch is not executed (no `q_dt`).
- **Dycore:** flux-form horizontal transport; the `kord_tr=9` remap conserves q·delp; `fillz`, `neg_adj3` and
  `fill_gfs` conserve the column; `consv_te` changes temperature only. No dry-pressure transport switch exists.
- **PBL** (`satmedmfvdifq`): implicit diffusion, mass-flux updraft/downdraft and subsidence are flux-form; all six
  species are diffused; the only boundary exchange is surface vapour; negative fixes borrow within the column.
- **Interstitials:** copies and linear updates only.

## Relevance to the GHG work

- Measured with passive tracers (status, above): with fix SA1 the physics conserves tracer mass to 10⁻¹⁸; without it
  SAMF deep changes it by −0.28 or +0.04 %/yr depending on the profile, the size of May's +0.25–0.65 %/yr (different
  FV3 branch). v1's dycore ≤ 10⁻⁴ %/yr; the 32-bit write-back −0.001 to −0.004 %/yr, one-signed.
- Open for UFS-Chem's own configuration: the write-back bias and whether added tracers are PBL-mixed (`nvdiff`).

## Where things are

- Proposal, diffs and scripts: `proposal/`. Literature and upstream status: `water_closure_references.md`.
- Hercules runs: `/work2/noaa/co2/ash/ufs-chem-v1/rt/wb_herc_*` (v1 snapshot variants) and
  `/work2/noaa/co2/ash/ufs-chem-v1/upstream/rt/wb_*` (upstream, C96 and C384). Variant source trees:
  `/work2/noaa/co2/ash/ufs-chem-v1/variants/` (snapshot; `wbdev` = the fast dev tree, `wbtr*` tracers) and
  `…/upstream/patched*/` (upstream: `patched18` = develop + final 01–18 (`patches/final18/`), `patched18m` metered,
  `patchedrt18` regression tree; older `patched17*` carry SA1's first form). Final runs `…/upstream/rt/wb_m18*`,
  `wb_d10_m18`, `wb_c384_m18`. SCM build: `/work2/noaa/co2/ash/ufs-chem-v1/scm/`.
