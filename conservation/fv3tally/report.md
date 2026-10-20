# fv3tally: where FV3's +0.57 W m-2 of dycore energy comes from (control_p8_ugwpv1, C96L127, dt 720 s, 24 h)

## Status

- **Outcome:** in the final series as row 45 `45_dyn_te_exact_v2.diff` (this folder's `patches/01_fv3-dyn_te_exact.diff`, v2), fv_core_nml `dyn_te_exact`, default 0 / all-on 31 (127 adds the design options). SERIES class: bits 1–16 BF, bits 32 and 64 PC (the report calls them DESIGN options).
- **Defects** DY1, DY2, DY3 (the report's D1–D3): the `d_con` heat applied at cp/cv times its KE estimate; the KE estimate taken about the half-damped wind; Rayleigh_Super heat (A-grid KE at cv_air, stale pkz). Red team (`dycred/`): all three confirmed as bug fixes; DY1 ratio 1.4010 (offline replay), 1.4007 (model).

| term (W m-2, 24 h, FV3's own TE) | ctl64 | all-on | class | bit |
|---|---|---|---|---|
| DY1 `d_con` heat ×cp/cv | +0.2905 | +0.2788 | BF | 1 |
| DY2 KE estimate minus KE removed | −0.0195 | −0.0186 | BF | 16 |
| DY3 Rayleigh net | +6.42e-4 | +6.42e-4 | BF | 8 |
| sponge damping not heated (k = 1, 2) | −1.69e-3 | −1.70e-3 | design | 32 |
| vertical remap | −0.1143 | −0.1119 | design | 64 |
| adiabatic dynamics + transport | +0.4145 | +0.4162 | design, open | — |
| sum = TE created in the fixer window | +0.5701 | +0.5632 | | |

| consv_te fixer (W m-2; 31 and 127 are v2 unless marked) | bits 0 | 31 | 127 |
|---|---|---|---|
| all-off config | −0.5689 | −0.2969 | −0.4129 |
| all-on config | −0.5632 | −0.3030 | −0.4162 (v1) |

- **Gates (v2, -no-fma):** bits 0 bitwise vs gA_off; restart 24 vs 12+12 and 3×8 vs 4×6 bitwise with 127, all-on; known-bad differs; non-MOIST_CAPPA and MULTI_GASES builds compile. Impact of 31 is at noise level except a cooling above 1 hPa.
- **Open:** the adiabatic remainder is a property of the spatial discretization, not exact-able without changing it; the consv_te fixer stays on and removes it.
- **Note:** TRACKER.md gives the fixer as −0.570 → −0.304, which matches no row of this report (closest: all-on v2 −0.5632 → −0.3030).

## Current answers

## Round 1 measurements (tally on, 24 h, W m-2; jobs t_off 10155449, t_on 10155450)

Meter passive: t_off (mt exe, FV3_ETALLY=1) vs energy's gA_off (gA exe = full10 -no-fma, no meter): 0 of 18 / 0 of 194
variables differ in atmf000/006/012/024 and sfcf012/024; 0 differ in fv_core, fv_tracer, fv_srf_wnd, sfc_data, phy_data
restarts at 24 h.

Self-checks: the code's own heat_source (raw, k ≥ 3) = my d_sw reconstruction Huv + Hw to 2e-6 relative; del2_cubed
conserves it (smo = raw); fixer window net −4e-13 / +6e-13 (FX1 exact); L2E exit and post-L2E probes 3e-10.

### Per-term tally, 24 h, W m-2 (+ = FV3 TE gained), FV3's own TE (MOIST_CAPPA cvm, as fv_mapz)

ctl64 = energy's base source + meter (`mt0`, release; t_ctl job 10155463, atmf024/sfcf024 bitwise vs energy's ctl64).
all-on = full10 + meter (`mt`, -no-fma) with `final9_switches.sed` (t_on 10155450). The full10 all-off run (t_off
10155449) agrees with ctl64 to 3 digits in every row.

| term | ctl64 | all-on | class |
|---|---|---|---|
| Rayleigh_Super: D-grid KE removed | −1.619e-3 | −1.620e-3 | |
| Rayleigh_Super: heat (A-grid KE at cv_air, then ×cp/cv by the stale pkz, see D3) | +2.261e-3 | +2.263e-3 | |
| **Rayleigh net** | **+6.42e-4** | **+6.42e-4** | DEFECT D3 |
| damping KE removed, divergence (nord 2 del-6 d4_bg + Smagorinsky dddmp), k ≥ 3 | −0.7303 | −0.7008 | DESIGN (returned by d_con) |
| damping KE removed, vorticity (vtdm4), k ≥ 3 | −0.01422 | −0.01377 | DESIGN (returned by d_con) |
| damping KE removed, w (damp_w) | −1.1e-6 | −1.0e-6 | DESIGN (returned by d_con) |
| damping KE removed, sponge k = 1, 2 (d2_bg_k1/k2 divergence + vorticity) | −1.69e-3 | −1.70e-3 | DESIGN: d_con_k = 0 there |
| d_con heat applied | +1.0155 | +0.9747 | |
| of which: the code's KE estimate (heat_source) | +0.7250 | +0.6959 | |
| of which: ×cp/cv from heating pt at fixed delz with 1/cv_air | **+0.2905** | **+0.2788** | DEFECT D1 |
| estimate minus KE actually removed at k ≥ 3 | **−0.0195** | **−0.0186** | DEFECT D2 |
| adiabatic dynamics + transport (dyn_core + tracer_2d, net of the damping KE) | +0.4145 | +0.4162 | DESIGN / OPEN |
| vertical remap total | −0.1143 | −0.1119 | DESIGN |
| remap: PE (delz remapped as specific volume) | −0.0636 | −0.0626 | |
| remap: horizontal KE (u, v remapped, KE not heated) | −0.0522 | −0.0521 | |
| remap: IE (T in log p, q) | +1.4e-3 | +2.8e-3 | |
| remap: w KE | −2.8e-7 | −2.6e-7 | |
| **sum = dycore TE created inside the fixer window** | **+0.5701** | **+0.5632** | |
| consv_te fixer | −0.5707 | −0.5632 | |
| window net (fixer − created) | −5.5e-4 (FX1 not in ctl64) | +6e-13 | |
| neg_adj3 / dry_negadj (after the fixer) | 1.7e-10 | 2.9e-10 | round-off |
| fv_subgrid_z (outside fv_dynamics; energy SG1) | — | +3e-11 (energy) | SG1 closed |

The dyn_core and tracer_2d probes are only meaningful together: dyn_core moves mass with q held, and tracer_2d then
updates q at fixed virtual potential temperature (dyn_core alone −1.488 / −1.351, tracer_2d +1.156 / +1.051).

## Fixes: `patches/01_fv3-dyn_te_exact.diff` (fv_core_nml `dyn_te_exact`, integer bits, default 0)

| bit | what | file | class | closes (W m-2, full10 all-off config) |
|---|---|---|---|---|
| 1 | D1: d_con heat applied at cvm and fixed delz: pt ← pt·(1+ΔT/T)^(1−κ), ΔT = heat/(cvm·delp) (was pt + heat/(cv_air·delp·pkz), which heats ΔT/(1−κ) = cp/cv × as much) | dyn_core.F90 | BUG FIX | +0.2905 → 0 |
| 2 | sponge layers (d_con_k = 0): the w-damping heat was J/kg where dyn_core expects delp·J/kg | sw_core.F90 | BUG FIX (immaterial here) | 1e-12 → exact |
| 4 | w-damping heat from the w the damping is added to (after advection), not w before advection | sw_core.F90 | BUG FIX (immaterial here) | 6e-9 → exact |
| 8 | D3: Rayleigh_Super heat = the D-grid KE it removes (KE_D·(1−u2f²) + w part) at cvm; pkz refreshed after the heating so the T→θ conversion keeps T (stale pkz multiplied the Rayleigh heat by cp/cv) | fv_dynamics.F90 | BUG FIX | +6.42e-4 → 1.5e-13 |
| 16 | D2: d_con's KE estimate = KE(u_f − du) − KE(u_f) with u_f the final wind (was evaluated about the half-damped wind, after divergence damping and before vorticity damping) | sw_core.F90 | BUG FIX | −0.0195 → exact |
| 32 | heat the sponge-layer (k = 1, 2) damping too (d_con_k = d_con) | dyn_core.F90 | DESIGN option | −1.69e-3 → −4.2e-5 (delt cap at k = 1) |
| 64 | vertical remap: return each column's TE change as a uniform ΔT at fixed delz | fv_mapz.F90 | DESIGN option | −0.1144 → −3e-10 |

Recommended: `dyn_te_exact = 31` (the five bug fixes). 32 and 64 are design options; 127 = everything.

Measured (mfx = full10 + fix + meter, -no-fma, all-off config, 24 h; jobs mfx_d31 10155603, mfx_d127 10155618):

| quantity | 0 (t_off) | 31 | 127 |
|---|---|---|---|
| Rayleigh net (RAY + CONV) | +6.42e-4 | +1.5e-13 | +1.8e-13 |
| d_con heat applied | +1.01644 | +0.745302 | +0.746220 |
| KE removed by damping it should return (k ≥ 3 for 0/31, all k for 127) | 0.74513 | 0.745302 (= applied to 1e-7 relative) | 0.746261 (applied + cap 4.2e-5) |
| remap | −0.11450 | −0.11443 | −3.0e-10 |
| adiabatic dynamics + transport | +0.4132 | +0.4133 | +0.4133 |
| **consv_te fixer** | **−0.5689** | **−0.2972** | **−0.4131** |
| fixer window net | −4e-13 | +6e-14 | +8e-13 |

All-on config (final9 switches; mfx_on31 10155628, mfx_on127 10155642): fixer −0.5632 (0) → −0.3032 (31) → −0.4162 (127);
adiabatic remainder +0.4168 in both; d_con applied = KE removed to 1e-7 relative; Rayleigh 5e-15; remap (127) −3.0e-10.

## v2 of the fix (dycred corrections), regate on full10, -no-fma

Changes from v1:
- **Bit 1:** the heat capacity comes from `moist_cv`, imported from fv_mapz_mod, so hail (nwat = 7) and the nwat = 2
  convention are FV3's own. The condensate in T = pt·pkz/((1+zvir·qv)(1−qc)) is the advected `q_con`. In
  non-MOIST_CAPPA builds κ = akap and cv = cv_air, matching compute_total_energy there; without USE_COND, qc = 0.
- **Bit 8:** Rayleigh uses `moist_cv`, or cv_air in non-MOIST_CAPPA builds. The pkz refresh repeats fv_dynamics' own
  pkz expression for every branch: MOIST_CAPPA, non-MOIST_CAPPA, and moist_phys = F.
- **fv_control FATAL:** bits 1, 8 and 64 with MULTI_GASES; bit 64 without MOIST_CAPPA, with hydrostatic, or with
  kord_tm ≥ 0. Nothing is a silent no-op any more. Bits 2 and 4 act only on non-hydrostatic w, and the hydrostatic
  d_con branch is already exact (heat/cp at fixed p), so those combinations need no FATAL.

| gate | runs | result |
|---|---|---|
| bits 0 = bitwise | fx2_off (10156089) vs gA_off | 0 differ: atmf000, atmf024, sfcf024, fv_core, fv_tracer, sfc_data, phy_data |
| closure, bits 31, all-off | mfx2_d31 (10156090) | d_con applied 0.745901 = KE removed (k ≥ 3) 0.745901; Rayleigh −8e-14; CONV 3e-13; fixer −0.2969 (v1 −0.2972) |
| closure, bits 31, all-on | mfx2_on31 (10156110) | applied 0.714907 = removed 0.714906; Rayleigh 3e-14; fixer −0.3030 (v1 −0.3032) |
| closure, bits 127 | mfx2_d127 (10156111) | remap −3.0e-10; fixer −0.4129 (v1 −0.4131) |
| v2 vs v1, p8 | fx2_d31 vs fx_d31 (10156119) | not bitwise (q_con vs q-derived qc; moist_cv order) but at noise: T rms 0.148 vs noise 0.145, ps 8.23 vs 8.13, LH 3.24 vs 3.08 |
| restart 24 vs 12+12, 127, all-on | rs2_S/R (10156120/21) | 0 differ (atmf024, sfcf024, 5 restart files) |
| 3×8 vs 4×6, straight and restarted | rsL2_S/R (10156140/41) | 0 differ |
| known-bad | rs2_S vs mfx2_on31 | 15 of 18 differ |
| compile, non-MOIST_CAPPA (-DHYDRO=ON) | hyd2 (10156018) | builds, rc 0 (no -DMOIST_CAPPA on the compile lines) |
| compile, -DMULTI_GASES=ON | mg2 (10156019) | builds, rc 0 |

Not run: a non-hydrostatic run of the dry branch (a HYDRO build is hydrostatic-only), and an nwat = 7 (NSSL) run (no
NSSL suite in this build, and no case inputs). The dry and hail branches are therefore compile-checked only.
`meters/meter_fv3tally_on_fix.diff` is regenerated against v2.

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| fv3tally: where FV3's +0.57 W m-2 of dycore energy comes from (control_p8_ugwpv1, C96L127, dt 720 s, 24 h) | title | current | `report.md` and `report.history.md` |
| Status (18 Oct 2026, done) | dated status, v1 and v2 summaries | superseded by `Status` | `report.history.md` |
| Round 1 measurements (tally on, 24 h, W m-2; jobs t_off 10155449, t_on 10155450) | meter passivity, self-checks | current | `report.md` |
| Per-term tally, 24 h, W m-2 (+ = FV3 TE gained), FV3's own TE (MOIST_CAPPA cvm, as fv_mapz) | where the +0.57 comes from | current | `report.md` |
| Fixes: `patches/01_fv3-dyn_te_exact.diff` (fv_core_nml `dyn_te_exact`, integer bits, default 0) | the seven bits, v1 closure numbers | current (closure numbers are v1; v2 values in `v2 of the fix (dycred corrections), regate on full10, -no-fma`) | `report.md` |
| Gates (all -no-fma; `fx` = gA + fix, `mfx` = fx + meter) | v1 gates and v1 impact | superseded by `v2 of the fix (dycred corrections), regate on full10, -no-fma` (gates); impact table is v1's | `report.history.md` |
| Sensitivity of the adiabatic remainder (mt exe, all-off config, tally on; 10155716, 10155724 and the two after) | remainder vs time steps and hord_tr | current | `report.history.md` |
| Code notes (why each row is what it is) | code reasons for each row | current (confirmed by `dycred/report.md`) | `report.history.md` |
| Files | patch, meters, tools | archival | `report.history.md` |
| v2 of the fix (dycred corrections), regate on full10, -no-fma | v2 changes and regate | current | `report.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
