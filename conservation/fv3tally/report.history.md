*History of `report.md` (fv3tally), moved verbatim on 18 October 2026. The head is `report.md`.*

# fv3tally: where FV3's +0.57 W m-2 of dycore energy comes from (control_p8_ugwpv1, C96L127, dt 720 s, 24 h)

## Status (18 Oct 2026, done)

- **Where the +0.57 W m-2 comes from** (ctl64 / all-on, 24 h, FV3's own TE): d_con heat returned at cp/cv times the
  KE it estimates, **+0.290 / +0.279** (DEFECT D1); adiabatic dynamics + transport **+0.414 / +0.416** (DESIGN, spatial
  discretization: same to ±3 % at half the acoustic step, half the remap step, half dt_atmos, or hord_tr 5); vertical
  remap **−0.114 / −0.112** (DESIGN); d_con's KE estimate below the KE actually removed, **−0.0195 / −0.0186** (DEFECT D2);
  sponge damping not heated, −0.0017 (DESIGN); Rayleigh net +6.4e-4 (DEFECT D3). Sum +0.5701 / +0.5632 = −fixer.
- **Fixed** in `patches/01_fv3-dyn_te_exact.diff` (fv_core_nml `dyn_te_exact`, bits, default 0, bitwise when 0):
  1 D1, 2 sponge w-heat units, 4 w-heat on the damped w, 8 D3, 16 D2 (all BUG FIX); 32 sponge heating and 64 remap
  column TE (DESIGN options). Each closes its term to ≤ 3e-10 W m-2 in the meter (bit 32: the code's delt cap at
  k = 1 withholds 4e-5).
- **Fixer size:** ctl-like −0.569 → **−0.297** with 31 (all-on −0.563 → −0.303); with every exact-able term exact
  (127) **−0.413 / −0.416** = the adiabatic-dynamics remainder (the remap sink no longer offsets it). The fixer stays on.
- **Gates (-no-fma):** bits 0 bitwise vs gA_off; meter passive (on vs off, fix on and off); restart 24 vs 12+12 and
  3×8 vs 4×6 bitwise with 127, all-on; known-bad differs. Impact of 31 at 24 h: T rms 0.159 K vs noise 0.145, ps 8.56
  vs 8.13 Pa, LH 3.53 vs 3.08 W m-2; systematic part −0.017 K above 1 hPa.
- **Open:** the +0.41 W m-2 adiabatic remainder (dyn_core + tracer_2d net of damping): not split further, not
  exact-able without changing the discretization; the consv_te fixer removes it.

- **v2 (dycred review)** `patches/01_fv3-dyn_te_exact.diff` (= `.v2.diff`; v1 kept as `.v1.diff`): moist_cv heat
  capacity and q_con condensate; bits 1 and 8 also in the non-MOIST_CAPPA / non-USE_COND branch; FATAL for bits 1, 8,
  64 under MULTI_GASES and for bit 64 without MOIST_CAPPA, hydrostatic, or kord_tm ≥ 0. Regated (§ v2 below).

Hercules: `$U/cons/fv3tally` (trees mt, mt0, fx, mfx, fx2, mfx2, hyd2, mg2; `runs/`, `logs/`, `exe/`, `tools/`). Local: this folder.

## Gates (all -no-fma; `fx` = gA + fix, `mfx` = fx + meter)

| gate | runs | result |
|---|---|---|
| switches off = bitwise | fx_off (10155578) vs energy's gA_off | 0 of 18 / 0 of 194 (atmf000, atmf024, sfcf024); 0 differ in fv_core, fv_tracer, sfc_data, phy_data at 24 h |
| switches off + meter | mfx_off (10155579) vs gA_off | same: 0 differ everywhere |
| meter passive, fix on | mfx_d31 vs fx_d31 (10155673); mfx_on127 vs rs_S | 0 of 18 / 0 of 194 |
| restart 24 h vs 12 + 12, bits 127, all-on | rs_S vs rs_R (10155687/88) | 0 differ: atmf024, sfcf024, fv_core, fv_tracer, fv_srf_wnd, sfc_data, phy_data |
| 3×8 vs 4×6, straight and restarted | rs_S vs rsL_S, rsL_R | 0 differ (same files) |
| known-bad (the gate can fail) | rs_S vs mfx_on31 (bits 32, 64 off) | 15 of 18 differ |

**Impact, 24 h, all-off config, bits 31 vs 0** (fx_d31 vs fx_off; noise = fx_c999 consv_te 0.999 vs fx_off, same exe):

| field | bits 31 | noise |
|---|---|---|
| T rms (K), all levels | 0.159 | 0.145 |
| ps rms (Pa) | 8.56 | 8.13 |
| LH rms (W m-2) | 3.53 | 3.08 |
| T mean, 0–1 hPa | −0.017 K | −0.0001 K |
| T mean, other pressure bands | ≤ 0.0025 K | ≤ 0.0003 K |

At 6 h the signal is clearer (T rms 0.065 vs 0.038): it is the 29 % smaller d_con heating where the damping is strong,
compensated by a fixer cooling about half as large. 10 % above noise at 24 h; the only systematic mean change is the
−0.017 K cooling above 1 hPa.

## Sensitivity of the adiabatic remainder (mt exe, all-off config, tally on; 10155716, 10155724 and the two after)

| run | change | adiabatic remainder | remap | fixer |
|---|---|---|---|---|
| t_off | — | +0.4132 | −0.1145 | −0.5689 |
| s_ns8 | n_split 4 → 8 (acoustic step 45 s) | +0.3984 | −0.1070 | −0.5652 |
| s_ks4 | k_split 2 → 4, n_split 4 → 2 (remap every 180 s) | +0.4099 | −0.1013 | −0.5787 |
| s_dt360 | dt_atmos 720 → 360 | +0.4074 | −0.0886 | −0.5946 |
| s_tr5 | hord_tr 8 → 5 (= hord_tm) | +0.4251 | −0.1144 | −0.5834 |

The remainder does not converge with any time step and barely moves with the tracer scheme: it is a property of the
spatial discretization (the D-grid KE that compute_total_energy counts is not the KE the vector-invariant momentum
equation and the pressure-gradient work exchange with IE + PE). It is steady through the day (3-hourly +0.39 to +0.45).
The remap sink shrinks as the remap step shrinks.

## Code notes (why each row is what it is)

- **D1** (dyn_core.F90, non-hydrostatic heat block): dtmp = heat_source/(cv_air·delp); pt += dtmp/pkz. pt is the
  density potential temperature and delz is held, so T ∝ pt^(1/(1−κ)) and ΔT = dtmp/(1−κ) = heat·cp/(cv·cv·delp).
  The hydrostatic branch (heat/cp at fixed pressure) is right; only the non-hydrostatic one over-heats. Meter: applied
  = 1.4007 × the smoothed heat_source, 0 capped cells.
- **D2** (sw_core.F90, d_sw heat): fy = u after divergence damping (added through ke) but before vorticity damping, used
  as the pre-damping wind: H = KE(u_f − b) − KE(u_f + a) instead of KE(u_f − a − b) − KE(u_f) (a: divergence, b:
  vorticity increment), short by ≈ Σa² + ab.
- **D3** (fv_dynamics.F90): Rayleigh_Super heats ½|ua|²(1−u2f²)/cv_air (A-grid KE) while TE loses the D-grid KE at
  cvm; pkz was computed before Rayleigh_Super and the T → θ conversion after it uses that stale pkz, which turns the
  heat into θ at fixed delz and multiplies it by cp/cv again (CONV row = 0.400 × the Rayleigh heat).
- **sponge layers** (k = 1, 2, d2_bg_k2 > 0 branch): d_con_k = 0 by design; d_sw then returns the w-damping heat in
  J/kg (not ×delp) and dyn_core divides it by delp (bit 2). 1e-12 W m-2 here.
- **remap** (fv_mapz.F90, kord_tm = −9): density T is remapped in log p, delz as specific volume, u, v, w by mass;
  nothing in this FV3 version remaps TE in the non-hydrostatic branch, so the remap's −0.11 (PE −0.064, KE −0.052) is
  by design. Bit 64 returns it as a uniform ΔT per column.
- **fv_subgrid_z / 2dz filter:** outside fv_dynamics and the fixer window; closed by energy SG1 (+3e-11).

## Files

- `patches/01_fv3-dyn_te_exact.diff` — the fix (fv_arrays, fv_control, dyn_core, sw_core, fv_dynamics, fv_mapz); applies
  with `patch -p1 -F0` in `$E/full10/ufs-weather-model`.
- `meters/meter_fv3tally.diff` — the tally on full10 (new `fv_etally.F90`, probes in fv_dynamics, dyn_core, sw_core,
  fv_mapz, CMakeLists); `meters/meter_fv3tally_on_fix.diff` the same on full10 + fix (the two diffs touch adjacent
  lines, so they do not stack with -F0); `meters/instrument_tally.py` inserts it by anchors into either tree.
  Env `FV3_ETALLY=1` turns it on; lines `ETL` (per step, J m-2) and `ETS` (running sum) on PE 0.
- `tools/etable.py` (24 h table), `series.py`, `cmpall.py`, `rmsdiff.py`, `tprof.py`, `mkrun.sh`, `mkrestart.sh`,
  `mkmt.sh`, `mkfx.sh`, `runs1.sh`, `runs2.sh`, `put.sh` (chunked upload via broker).
