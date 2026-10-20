# UFS total-energy conservation: control_p8 (C96, 24 h, dt = 720 s)

## Status

The final tree is `full14` = `full13` + the decided changes (§9.9); every build is `-no-fma`. All-on `full14` is
bitwise identical to all-on `full13`, so the `full13` budget numbers hold for it.

| 24 h, frame F, every switch on | Value |
|---|---|
| Residual net of the declared terms | **+1.6e-12 W m-2** |
| Scheme frame-F gaps (radiation, PBL, GWD, SAMF, Thompson + MP post) | ≤ 1.2e-12 W m-2 |
| Declared: surface hand-off / S_chem / PH1 snow as ice at T1 | +0.1135 / +1.44e-5 / −1.74e-3 W m-2 |
| `consv_te` fixer correction | **−0.304 W m-2** (ctl64 −0.5701) |
| Precipitation hand-off lag, as the surfaces book it | 0 (EP1, with PL1 folded in) |
| NM10r: land frozen precipitation vs the host's srflag·P | 1.2e-10 (NM10: 2.5e-2) |

- **Gates (`full14`):** restart 24 h vs 12 + 12, 3×8 vs 4×6 (straight and restarted), meters passive, and every switch off vs the bug-fix arm gB14 (fx + bug fixes, with TH8 + TH9 unconditional and NM10r): 0 differing variables in every file.
- **Defaults (settled):** every PHYSICS CHANGE and NUMERICAL CONSISTENCY switch is off. Recommended all-on settings: `dyn_te_exact` 31, `ngw_heat_opt` 2, `noahmp_fwet_opt` 2, MPAS 0014 option 2.
- **`full14` changes:** TH8 + TH9 unconditional (`patches/13_…`, cut on fx; replaces energy 06 and canopy 02/03); PL1 folded into EP1 (`sfc_precip_t1_carry` removed); NM10r, a PHYSICS CHANGE (water diff 17r replaces 17).
- **Impact, all-on vs ctl64:** T rms 0.28 K, ps 22.6 Pa, LH mean −1.89 W m-2; land canopy evaporation +35.6 % (`noahmp_fwet_opt` = 2), land LH +1.73 %. Noise: 0.149 K / 8.41 Pa / 3.24 W m-2.
- **Left by design:** the dycore's own TE gain, removed by the fixer (D10), and the declared boundary terms above.
- The replay agent regenerates the verified series from `full14`.

## Current answers

Kept in full, verbatim, with their original headings and numbers.

## Patch series (integration order on `$E/base`; `$E/all_full` = everything, `$E/mall_full`/`mallq_full` metered twins)

The "residual it closes" column is the residual before → after, in W m-2.

| # | patch | file(s) | class | switch (default) | residual it closes |
|---|---|---|---|---|---|
| 01 | FX1 `patches/01_fv3-fv_mapz_consv_te_fixer_weight.diff` | fv_mapz.F90 | BUG FIX | — | consv_te fixer window −5.5e-4 → ±3e-10 |
| 02 | SG1 `patches/02_fv3-fv_sg_relax_total_energy.diff` | fv_sg.F90 | BUG FIX | — | fv_subgrid_z −1.6e-4 → 3e-11 |
| 03 | CP1 `patches/03_fv3-atmosphere_state_update_heating_mass.diff` | atmosphere.F90 | BUG FIX | — | coupling heating −8.6e-3 → ±4e-10 |
| — | FV2 `tracer/patches/01_FV2_…` | atmosphere.F90 statein | BUG FIX | — | tracer round trip. Energy-neutral |
| 04 | R1 `patches/04_ccpp-dcyc2t3_radiative_heating_current_mass.diff` | dcyc2t3, GFS_typedefs | BUG FIX | — | radiation −7.7e-3 → 1e-13 |
| — | enpbl 04 `enpbl/patches/04_ccpp-satmedmfvdifq_dspheat_ke.diff` | satmedmfvdifq | PHYSICS CHANGE | dspheat_ke (.false.) | PBL +1.43 → 1e-12 |
| — | encnv 01 D3A | samfdeep/shal | BUG FIX | — | SAMF ice −0.438 → 1e-13 |
| 05 | D7 `patches/05_fv3-cpl_ke_heating_option.diff` | fv_arrays, fv_control, atmosphere | NUMERICAL CONSISTENCY | cpl_ke_heating (.false.) | A→D KE −0.016 (net of fv_sg) → 1e-10. Noisy locally: §8, not recommended |
| — | encnv 02 D3B | samfdeep/shal | PHYSICS CHANGE | samf_cmt_heat (.false.) | SAMF CMT −0.149 → ≤7e-13 |
| — | encnv 03 D4 + D12 | ugwpv1_gsldrag, GFS_GWD_generic_post | PHYSICS CHANGE | gwd_ke_heat (.false.) | GWD −0.050 → ≤9e-13 |
| — | encnv 04 D4n | ugwpv1_gsldrag | PHYSICS CHANGE | ngw_heat_opt (default 0; recommended 2) | NGW net source; options 1 and 2 give the same budget to 5e-5 |
| — | NM12 `nm12/patches/20_NM12_…` (20b EMC companion not built) | Noah-MP land + glacier | BUG FIX | — | does not fire at dt 720: C96 bitwise identical |
| — | encpl 04 C1 | atmosphere.F90 | PHYSICS CHANGE | cpl_water_energy (0; bits 1 PE, 2 flow work, 4 sensible) | D2. **Bit 2:** FV3 books ±R_v·T on every vapour mass change at fixed delz, a net sink of −0.62; bit 2 adds +0.62 net (fwred) |
| — | encpl 05 K1 | Thompson | PHYSICS CHANGE | thompson_kirchhoff (.false.) | D5 |
| — | encpl 06 (rebased onto encnv as `accepted/10r_…`, by `patches/tools/rebase_encpl06.py`) | SAMF, Thompson, atmosphere | PHYSICS CHANGE | samf_kirchhoff (.false.) | precipitation-flux export for C1 bits 1/4 + S1 |
| 06 | TH8 `patches/06_ccpp-thompson_count_all_sedimented_precip.diff` | module_mp_thompson | BUG FIX; **superseded by row 13** (TH8 + TH9 in one diff) | — | Thompson water leak 6.6e-12 kg m-2 s-1 → 0 (energy +2.4e-6 → 0). Alone it cuts land canopy evaporation −47 % at f24 (canopy, §9.5) |
| 07 | S1K `patches/07_ccpp-samf_kirchhoff_ice_and_initial_T.diff` | samfdeepcnv, samfshalcnv | PHYSICS CHANGE (completes S1) | samf_kirchhoff (.false.) | SAMF deep +0.080 → 5e-14, shallow +0.0028 → 1e-14 |
| 08 | TFH `patches/08_ccpp-thompson_frame_F_heating.diff` | mp_thompson | PHYSICS CHANGE | thompson_frame_heat (.false.) | Thompson +0.0083 → 5e-13 |
| 09 | PBK `patches/09_ccpp-satmedmfvdifq_filler_kirchhoff.diff` | satmedmfvdifq | PHYSICS CHANGE | pbl_kirchhoff (.false.) | PBL filler +4.8e-5 → 0 |
| 10 | C8 `patches/10_fv3-cpl_water_energy_bit8_water_KE.diff` | atmosphere.F90 | PHYSICS CHANGE | cpl_water_energy bit 8 (off) | water-mass KE −0.0025 → 0 |
| 11 | D7S `patches/11_fv3-cpl_ke_smooth.diff` | fv_arrays, fv_control, atmosphere | NUMERICAL CONSISTENCY | cpl_ke_smooth (0; use 32) | D7 max heating 0.87 → 0.013 K/step, still exact |
| 12 | PBF `patches/12_ccpp-fv3-pbl_condensate_flux_export.diff` | satmedmfvdifq, GFS_typedefs, atmosphere | PHYSICS CHANGE (C1 speciation) | acts under cpl_water_energy bit 4 | PBL −0.0049 → 8e-13 |
| — | latent 01a, 01b, 02, 03 (`accepted/12-15`) | SAMF scavenging, wet-deposition export, cmake, tend_opt | owner latent | — | energy-neutral; tend_opt_pbl 1 and 3 close (PBL gap ≤1e-12) |
| — | trdyn 02b, 03b, 04 INLQ, 01_DYN **v6** (`accepted/16, 17, 18c, 18d`; clashes re-anchored by `patches/tools/rebase_trdyn.py`) | SAMF tracer substep, PBL dry chem tracers, sw_core inline_q mass (BUG FIX, bitwise with inline_q off), FV3 dry tracer advection/remap/IC + dry_negadj | owner trdyn | dry_tracer_adv (.false.; on in final) | energy-neutral (chemistry tracers only) |
| — | ensfc2 04 SI1, 05 SI2, 06 NP1 (series prerequisites), 08 QR1, 09 CMC, 10 FL1 (bug fixes), 11 options; 12 NM10r in the NM10r row below | Noah-MP, sea ice, NSST, sfc drivers | owner ensfc2 | noahmp_canopy_heat=1, precip_phase_host, noahmp_sw_radshare, lw_sfc_consistent, sfc_evap_enthalpy, noahmp_heat_advect, noahmp_kirchhoff | surface side; enters the atmosphere budget as declared boundary flux (§9.4) |
| — | ensfc2 r4: 13 SL2, 14 CS1, 15 CB1 (bug fixes), 16 options_r4 (`accepted/24-27`; 13 hunk 8 re-anchored; **16's GFS_MP_generic_post.meta `[tgrs]` standard name fixed to physics_timestep_initial_air_temperature**) | Noah-MP, glacier, sea ice, MP_generic_post | owner ensfc2 | sfc_precip_enthalpy, lw_sfc_return (LW2 replaces LW1), noahmp_pore_air | snow combine / heat capacity; EP1 closes PH1 (§9.6) |
| — | canopy 01 E2, 04 E1 (`accepted/28-30`; E2 re-anchored next to ensfc2 16; 02 TH8 and 03 TH9 superseded by row 13) | Noah-MP fwet, Thompson sedimentation, NSST spray | owner canopy | noahmp_fwet_opt (all-on 2), nst_spray_opt (all-on 1) | TH9 neutralises TH8 over land; fwet 2 = +35 % canopy evaporation |
| — | fv3tally 01 dyn_te_exact v2 (`accepted/31`) | dyn_core, fv_dynamics, fv_mapz, sw_core, ... | owner fv3tally: bits 1-16 BUG FIX, 32/64 DESIGN | dyn_te_exact (0; all-on 31) | fixer correction −0.564 → −0.304 W m-2 |
| — | preclag 01 PL1 (`accepted/41`); ensfc2 16b = 16 + integrator meta fix | GFS_MP_generic_post, noahmpdrv, glacier, sea ice, GFS_restart | owner preclag | folded into sfc_precip_enthalpy (PL1 row below) | precipitation hand-off lag −0.0121 → 0 |
| — | suites 01, 01b, 02, 07 (BUG FIX), 03, 04, 06 (switches), 05, 08 (`accepted/32-40`; 03/04/06 switch hunks re-anchored, REJ stage) | MYNN, GFDL MP v3, GF, satmedmfvdifq, samfdeepcnv | owner suites | gf_closure, mynn_sfc_heat, mynn_mix_sl | in p8: 05 rounding-level, 08 bitwise inert (§9.8) |
| 13 | TH8+TH9 `patches/13_ccpp-thompson_TH8-TH9_unconditional.diff` (on fx; **replaces 06, canopy 02, canopy 03**) | module_mp_thompson | BUG FIX | — (TH9 now unconditional) | Thompson water leak → 0; TH9 removes TH8's land side effect |
| — | PL1 folded into EP1 (`patches/full14/delta_PL1_folded_into_EP1.diff`) | GFS_typedefs, GFS_restart, MP_generic_post, noahmpdrv, sfc_sice | owner preclag | sfc_precip_enthalpy (EP1) | lag 0 with EP1; restart field only with EP1 |
| — | NM10r (`patches/full14/delta_NM10r.diff`; water `patches/water_17r/17r_…` replaces water 17) | noahmpdrv, module_sf_noahmplsm | PHYSICS CHANGE | — (unconditional) | land phase = host to 1.2e-10 of frozen mass (NM10 2.5e-2) |
| — | meters `meters/meter_*.diff` + encpl `meter_r2` (frame F) | | INSTRUMENTATION | — | — |

## 3. Defects found and fixed (patches in `patches/`, applied in this order to `$E/base`)

All three are column-local or reuse existing global sums, add no state, and are restricted to the configuration branch they correct.

### FX1: `01_fv3-fv_mapz_consv_te_fixer_weight.diff` (fv_mapz.F90, Lagrangian_to_Eulerian)

**Cause.** The consv_te fixer computes the global TE deficit with cvm·T. It converts the deficit to a temperature increment with weight cv_air·Σ pkz·delp. It then applies the increment as pt += dtmp·pkz, followed by division by (1+r_vir·qv)(1−qc), at heat capacity cvm. The energy actually added is therefore the intended amount times the mass-weighted cvm/(cv_air·(1+r_vir·qv)(1−qc)).

**Measured.** The fixer window (te0 → after fix) left −5.53e-4 W m-2. That is +9.6e-4 of the correction, stable every step (job 10150271).

**Fix.** In the non-hydrostatic MOIST_CAPPA + USE_COND branch, weight zsum1 by exactly that factor (the same moist_cv and qc the update uses).

**After.** −3.6e-10 W m-2, |per step| ≤ 3e-9 (mfx1, job 10150652): round-off.

**Red team.**
- Hydrostatic and non-MOIST_CAPPA branches are untouched.
- consv_te < 1 now restores exactly the requested fraction.
- E_Flux is unchanged (it uses te only).
- **Caveat:** with do_sat_adj = .true. (GFDL fast saturation adjustment between the te loop and the pt update), q changes in between. The weights then use pre-adjustment q: still exact to first order, but not to round-off. Not exercised by control_p8.

### SG1: `02_fv3-fv_sg_relax_total_energy.diff` (fv_sg.F90, GFS_PHYS fv_subgrid_z, non-hydrostatic, nwat = 6)

**Cause.** The 2Δz filter mixes q, u, v, w and total energy te = cvm·T + gz + ½|v|² conservatively. It then relaxes toward the mixed state by fra = dt/tau, which is 0.4 for fv_sg_adj = 1800. The relaxation is applied separately to T, u, v, w and q. Kinetic energy is quadratic, and cvm·T is bilinear, so the relaxed state loses fra·(1−fra)·δ²/2 per unit mass.

**Measured.** A-grid TE −1.58e-4 W m-2. The heating was +3.948e-3 against a KE loss of −4.106e-3 (job 10150271).

**Fix.** Relax te with the other fields, and diagnose T from it with the relaxed cvm.

**After.** +3.0e-11 W m-2 (mfx1): round-off.

**Red team.**
- The fix acts only where mixing happened, i.e. in the sponge: k_bot = n_sponge = 42.
- **One-step signal:** max |ΔT| 9.6e-3 K, rms 4.4e-5 K, levels 0-46 only (run fxsg vs ctl64, atmf000).
- The hydrostatic branch and nwat ≠ 6 have the same issue and are left as is (minimal diff).

### CP1: `03_fv3-atmosphere_state_update_heating_mass.diff` (atmosphere.F90, atmosphere_state_update)

**Cause.** The physics heats its own layer mass m_p = prsi(k) − prsi(k+1), which excludes condensate. Radiative heating is flux divergence/(cp·m_p), and the PBL surface heat is dtsfc1·dt/(cp·m_p) exactly. fv_update_phys applies t_dt·cp_air/cpm to the new total delp. The meter shows the dycore then receives exactly Σ cp_air·t_dt·dt·delp_new/g. So each physics joule arrives multiplied by delp_new/m_p,old.

**Measured.** Coupling heating minus the physics cp·ΔT·m_p = −8.63e-3 W m-2 (job 10150601).

**Fix.** Scale the physics part of t_dt by qp/delp_new, where qp = m_p,old, computed where both are known (the existing block loop).

**After.** +3.9e-10 W m-2 (mfx1): round-off. Radiation's column energy is now exactly the radiative flux divergence in the dycore.

**Red team.**
- IAU temperature increments are not scaled; they are added before the loop.
- The hydrostatic and phys_hydrostatic = .false. branches inject cpm- or cvm-based energy on the same delp, so the scaling is equally right there.

## 5. Response of the forecast to the fixes ("no change beyond the defect's own signal")

All runs: 24 h, C96, `$E/runs/<name>`; differences vs ctl64 over 6 tiles.

| run | fixes | step-1 (atmf000) T: max / rms (K) | where | f24 T rms (K) | f24 ps rms (Pa) | f24 LH rms (W m-2) |
|---|---|---|---|---|---|---|
| ctl64L | none, layout 4×6 | 0 / 0 | — | 0 | 0 | 0 |
| fxcp | CP1 | 0.043 / 1.4e-4 | cloudy layers only; u, v, precip unchanged at step 1 | 0.159 | 8.55 | 3.47 |
| fxsg | SG1 | 9.6e-3 / 4.4e-5 | levels 0-46 (sponge) | — | — | — |
| fxfx | FX1 | 2.46 / 2.4e-3 | all levels; max at levels 110-114 | 0.148 | 8.31 | 3.35 |
| **ctlc999** | **none, consv_te = 0.999 (control perturbation of the same size as FX1)** | **2.46 / 2.4e-3** | **same points** | **0.149** | **8.41** | **3.24** |
| fx1 | FX1 + SG1 + CP1 | 2.46 / 2.4e-3 | all | 0.158 | 8.51 | 3.46 |

- **CP1 and SG1:** at step 1 they change only what they target, by the size of their own term.
- **FX1:** shifts the global fixer increment by ~1e-3 of itself (~1e-7 K). The model's step-1 thresholds (convection and PBL triggers) amplify that to K-scale local differences. A namelist perturbation of the fixer by the same 0.1% (ctlc999) produces the **same** step-1 pattern and the same 24 h statistics. So FX1's footprint is that of any 0.1% fixer perturbation.
- By 24 h every variant is at the same threshold-noise level (T rms ≈ 0.15 K).
- **Global means at f24** move by ≤ 3e-4 K (T) and ≤ 0.04 Pa (ps), within the ctlc999 spread.

## 6. Round 2

### R1: `04_ccpp-dcyc2t3_radiative_heating_current_mass.diff` (dcyc2t3.f/.meta, GFS_typedefs.F90/.meta). BUG FIX

**Cause.** RRTMG returns heating rates htr = ΔF_net·g/(cp·dp_rad) for the layer masses at the radiation call (hourly). dcyc2t3 applies the same K/s on the 4 following steps, while dp keeps changing (dynamics and water). So the column receives Σ cp·htr·dp_now/g ≠ the radiative flux divergence.

**Measured.** −7.65e-3 W m-2 (Σ|r| 2.70e-2), job 10150601.

**Fix.**
- Two new Radtend fields, dpsw and dplw: the layer pressure thickness at the last SW / LW call.
- dcyc2t3 sets them itself when lsswr / lslwr (the radiation group runs earlier in the same step on the same Statein%prsi).
- It scales swh·xmu by dpsw/dp_now and hlw by dplw/dp_now, including the LW-Jacobian branch and the dtend diagnostics.
- The fields are zero until the first call, and the guard then uses factor 1.

**Least state.** Two 2-D persistent fields (im × levs), one per radiation type, because fhswr ≠ fhlwr is allowed. No other scheme reads them.

**Restart.** Not needed in the restart file. htrsw and htrlw are not in the restart either; the model relies on radiation being called on the first step after a restart (kdt = 61 here, mod(61, 5) = 1), and dcyc2t3 refreshes dpsw/dplw on that same step. Same lifecycle and same assumption as the base.

**After.** r = −8.4e-14 W m-2, Σ|r| 1.7e-9 W m-2 (mfxr, job 10151879): round-off by construction.

**Signal.** At step 1 the rescaling factors are exactly 1 (x/x). atmf000 differs only in the last bits of graupel and rain (rel ≤ 9e-11), from the rebuilt module layout; T and winds are identical. f24 vs fx1: T rms 0.149 K, ps rms 8.07 Pa, the same as the ctlc999 threshold-noise control (0.149 K, 8.41 Pa).

**Other hosts.** The SCM and MPAS hosts use their own GFS_typedefs copies and would need the same two fields (an upstream PR must carry them). Not tested here.

### D9 and D10: how the master budget books them

- **D9, h2ophys:** a declared internal source S_chem = hvap·Δqv from the photochemical water source/sink. It enters the closure as S_chem = +1.4e-5 W m-2, not as a residual. The water budget books the same Δqv as the chemical water source.
- **D10, consv_te fixer:** declared design. The dycore's own TE error over each fv_dynamics call (+0.570 W m-2 created by remap, d_con, damping and transport) is removed by the fixer and redistributed globally, weighted by pkz. The budget books the fixer window as one term. After FX1 it closes to round-off (≤ 2e-10). The applied correction E_Flux (−0.570 W m-2) is reported as information, not as a boundary flux.
- **Closure statement:** E(24 h) − E(0) = ∫F_boundary + S_chem + Σ_design (D1-D8, D11) + round-off, with every term metered.

## 8. Round 3

### D7 option: `05_fv3-cpl_ke_heating_option.diff` (fv_core_nml `cpl_ke_heating`, default .false.). NUMERICAL CONSISTENCY, small physics change

**Target.** The KE the total A-grid increments imply, per cell and layer:
- the fv_subgrid_z part, ½|ua_sg|² − ½|ua_sg − dt·u_dt_sg|², on the old delp;
- plus the physics part, ½|gu0|² − ½|ugrs|², on the physics mass;
- divided by delp_new.

**Heat.** Target minus the D-grid KE change realised by update_dwinds_phys (compute_total_energy's KE_D, per cell). It is applied after fv_update_phys at constant pressure, the same way fv_update_phys heats (cpm with delz scaling; cvm or hydrostatic branches mirrored).

**Gate.** With the switch off, all_v4k is bitwise identical to all_v3k (atmf024, sfcf024).

**Closure** (mall_v4kd, job 10152397). The KE row (−0.02018) + D7 heating (+0.01606) + fv_sg heating (+0.00411) = **−1.0e-10 W m-2**, round-off. The total residual moves 1.056 → 1.073, i.e. within threshold noise.

**Size per cell.** One-step T change (atmf000, D7 on vs off; u, v, ps and fluxes identical at step 1):
- max 0.87 K/step (≈ 105 K/day locally), rms 2.5e-3 K/step (0.30 K/day);
- global mean +1.3e-5 K/step;
- maxima at levels 63 and 2.
- So it is mostly ± dipoles. The A→D mapping moves KE between neighbouring cells, and per-cell heating turns that local redistribution into heating/cooling pairs. Only the global net (−0.016 W m-2) is a true energy error.

**Impact at f24 vs D7 off:** T rms 0.167 K, ps 8.81 Pa, LH 3.68 W m-2. The ctlc999 noise control gives 0.149 K / 8.41 Pa / 3.24.

**Verdict.** It closes the term exactly. The local heating is noisy, so it is **not recommended for the proposal**; keep it as a demo option. A smoother target (e.g. KE target and realised change both on the D-grid edges) would need a D-grid formulation, not a layer-local one.

## 9. Round 4: frame, Kirchhoff consistency, water-mass KE, smooth D7

### 9.1 Which accounting is right (derivation)

**The model's energy is FV3's.** E_F = Σ delp/g·[cvm·T + φ + K] + Lv00·Wv − Li00·Wi, where cvm uses c_vap = 3R_v, c_liq and c_ice (frame F).
- Lv00 = hvap − (cp_v − c_l)·T0 and Li00 = hfus − (c_l − c_i)·T0 are the only constant references that make phase changes conserve this TE with FV3's own heat capacities. With those constants:
  - e_v − e_l = L_e(T);
  - h_v − h_l = hvap + (cp_v − c_l)(T − T0) =: L_h(T);
  - e_l − e_i = hfus + (c_l − c_i)(T − T0) =: L_f(T).
- The physics frame E_P (con_cp, constant hvap/hfus, condensate without heat capacity) is the GFS schemes' bookkeeping, not the model's energy. Closing E_P does not close E_F.
- The physics meter therefore stays as a scheme-internal check. The **budget is frame F**.

**What the coupling books.** With CP1, fv_update_phys injects exactly the physics' con_cp·ΔT·m_p. The write books every water mass change dm_w at the layer's **step-initial T** (pt before update = tgrs), with c_w·T + φ + K.

**Exact frame-F requirement**, for a net phase change in layer k:
- **Heating:** Q_k = L_h(T_old,k)·(vapour condensed/deposited) + L_f(T_old,k)·(water frozen). That is the Kirchhoff latent heat at the step-initial T.
- **Water falling or rising between layers** must exchange c_w·ΔT. That is C1 bit 4, S_cross.
- **The other coupling terms:**
  - R_v·T on every vapour mass change at fixed delz is C1 bit 2;
  - water PE is C1 bit 1;
  - water KE is bit 8 (new).

**Per-scheme meter (meter v2, `meters/tools/instrument_eb_phys2.py`).** It adds c8 = Σ m·[qv(Lv00 + cp_v·T_old − hvap) + ql·c_l·T_old + qi(c_i·T_old − Li00 + hfus)] per probe, and the frame-F boundary corrections at T1, giving:
- r_F = r_P + Δc8 − (boundary water enthalpy at T1 − physics booking);
- S_cross per segment, from the segment's net layer water changes and the scheme's exported precipitation fluxes (pflx_dc/sc/mpl/mpi; the remainder is vapour, cp_v; encpl's speciation);
- **gap = r_F − S_cross**, the scheme's frame-F inconsistency that is not the coupling's job.

Σ gap + (coupling KE) reproduces the frame-F total residual (`frameF_seg.py`, `frameF_table.py`).

### 9.3 New fixes and options, round 4

Patches `06`-`12` are in `patches/`. They apply in order on all_full (= fx + R1 + FV2 + enpbl + encnv + NM12 + encpl). A plain tree uses `patches/tools/apply_fixes.py <tree> TH8 S1K TFH PBK C8 D7S PBF`.

| id | patch | class | switch (default) | closes |
|---|---|---|---|---|
| TH8 | `06_ccpp-thompson_count_all_sedimented_precip.diff` | BUG FIX (water leak: precipitation below R1·rr_min not counted although its mass left the lowest layer) | — | Thompson frame-F gap −5.6e-6 → 9e-13 (with TFH); water dW − flux 6.6e-12 → 0 |
| S1K | `07_ccpp-samf_kirchhoff_ice_and_initial_T.diff` | PHYSICS CHANGE, completes encpl S1 | samf_kirchhoff | SAMF deep +0.080 → 1e-13, shallow +0.0028 → −6e-15 |
| TFH | `08_ccpp-thompson_frame_F_heating.diff` | PHYSICS CHANGE | thompson_frame_heat (.false.) | Thompson frame-F gap → 9e-13 |
| PBK | `09_ccpp-satmedmfvdifq_filler_kirchhoff.diff` | PHYSICS CHANGE | pbl_kirchhoff (.false.) | filler part of the PBL gap (+4.8e-5) |
| PBF | `12_ccpp-fv3-pbl_condensate_flux_export.diff` | PHYSICS CHANGE (C1 speciation) | acts under cpl_water_energy bit 4 | PBL condensate transport at c_l/c_i in bit 4: PBL gap −0.00485 → 8e-13 |
| C8 | `10_fv3-cpl_water_energy_bit8_water_KE.diff` | PHYSICS CHANGE | cpl_water_energy bit 8 | KE of written water mass (−0.0025) |
| D7S | `11_fv3-cpl_ke_smooth.diff` | NUMERICAL CONSISTENCY | cpl_ke_smooth (0) | D7 heating smoothed in flux form (exactly conservative) |

**Gates, round-4 tree full5** (all switches on; jobs in `logs/final_full5.txt`):
- Restart (24 h vs 12+12), 3×8 vs 4×6 (straight and restarted), and meters passive: **0 differing variables in all 20 comparisons** (atmf024, sfcf024, fv_core, fv_tracer, sfc_data, phy_data).

**Impact of each new switch** (turned off one at a time vs all on). f24 rms T (K) / ps (Pa) / LH (W m-2) and the systematic mean where notable.

| switch | rms T | rms ps | rms LH | mean shift |
|---|---|---|---|---|
| noise (ctl64 vs ctlc999) | 0.149 | 8.41 | 3.24 | — |
| TFH | 0.143 | 7.73 | 3.01 | — |
| PBK | 0.151 | 7.98 | 3.24 | — |
| C8 | 0.145 | 7.70 | 3.06 | — |
| D7S vs raw D7 | 0.161 | 8.70 | 3.49 | — |
| D7 off | 0.152 | 8.22 | 3.31 | — |
| S1 (samf_kirchhoff) | 0.161 | 8.47 | 3.37 | **mean LH +0.16 W m-2, ps −0.14 Pa** |
| all switches off | **0.246** | **18.3** | **7.06** | **mean LH −2.0 W m-2** (flow-work bit) |

- All single switches are at the noise level. The combined set changes the forecast beyond noise; most of it is C1 bit 2 (encpl: LH −2.0 W m-2, precipitation −3.4 %).
- TH8: default-off build vs full_off is at f0 identical in T, with precipitation +3.7e-7 max (the counted leak). At f24 T rms is 0.173 / ps 9.5 (TH8 + FMA), about noise.

**D7S local heating** (step-1 T increment, D7 on vs off):

| variant | max (K/step) | rms (K/step) | mean (K/step) |
|---|---|---|---|
| raw per-cell D7 | 0.871 | 2.5e-3 | +1.3e-5 |
| D7S, 2 passes | 0.212 | 6.0e-4 | +1.3e-5 |

| D7S, 8 passes | 0.0248 | 2.2e-4 | +1.3e-5 |
| D7S, 32 passes | **0.0131** | 1.4e-4 | +1.3e-5 |

- The mean is unchanged (the smoother is flux-form, so the global heating is exact). 32 passes cut the peak 66× (0.013 K/step ≈ 1.6 K/day), which is below the PBL/convective tendencies at those points. **Use cpl_ke_smooth = 32.**
- 24 h impact vs the 2-pass all-on run (full7): D7 off 0.153 / 8.05 / 3.12; s8 0.151 / 7.95 / 3.14; s32 0.152 / 7.97 / 3.19 (rms T K / ps Pa / LH W m-2), all at the ctlc999 noise (0.149 / 8.41 / 3.24).
- Cost: one halo update per pass on one 3-D array.

### 9.7 full12 = full11 + fv3tally dyn_te_exact (v2): final tree

**Patch.** `accepted/31_fv3tally_01_fv3-dyn_te_exact_v2.diff` = `$U/cons/fv3tally/patches/01_fv3-dyn_te_exact.v2.diff`, -p1 -F0 clean on full11.
- **Flag:** `01_fv3-dyn_te_exact.diff` is *not* identical to `.v2.diff`. It is 217 content lines different and 31 min older. I used `.v2`.
  Resolved: on Hercules the stale copy is kept as `01_fv3-dyn_te_exact.stale_0552.diff`; both names now hold `.v2` (md5 ddc59580), locally and on Hercules.
- In mq12, fv_dynamics hunks 1-2 sit next to the dycore meter probe after the Rayleigh call. `rebase_r11.py DTE` re-anchors them with text taken from the diff: the probe stays right after the call, and the new pkz block follows it. pkz is not part of the energy.
- mq12 − full12 is meter lines only, the same counts as mq11 − full11.
- **Switch:** fv_core_nml `dyn_te_exact`. All-on uses 31 (bits 1-16, bug fixes); one run uses 127 (+ sponge heat 32, remap ΔT 64, design).

**Master budget, frame F, 24 h, W m-2** (m12 = all-on with 31, job 10156218; m12_127, job 10156219):

| term | full11 (dyn_te_exact 0) | **full12, 31** | full12, 127 |
|---|---|---|---|
| **consv_te fixer correction** (dycore TE gain it removes) | −0.5640 | **−0.3038** | −0.4174 |
| ctl64 for reference | −0.5701 | | |
| fixer window (exactness) | +2.6e-10 | −2.5e-11 | −7.4e-11 |
| declared: surface hand-off, seg 3 | +0.11372 | +0.11359 | +0.11379 |
| declared: S_chem | +1.4364e-5 | +1.4364e-5 | +1.4365e-5 |
| declared: PH1 snow as ice at T1 | −1.740e-3 | −1.745e-3 | −1.747e-3 |
| **RESIDUAL net of the declared terms** | −6.8e-13 | **+4.0e-11** | +3.1e-11 |
| scheme frame-F gaps (rad, PBL, GWD, SAMF, Thompson) | ≤ 1.6e-12 | ≤ 1.6e-12 | ≤ 1.5e-12 |
| hand-off lag, all surfaces (not in the atmosphere budget) | −1.20e-2 | −1.20e-2 | −1.20e-2 |

- dyn_te_exact = 31 halves what the fixer has to remove (−0.57 → −0.30), matching fv3tally (−0.30). 127 gives −0.42 (fv3tally −0.41).
- The residual stays at the fixer window's round-off level (a few 1e-11). Every term is at round-off or declared, except the hand-off lag (§9.6), which is outside the atmosphere's budget.

**Gates, full12 (-no-fma)** (`logs/final12.txt`; rs12 10156243/244, rsL12 10156269/270, gA12_off 10156300):
- Restart, 3×8 vs 4×6, and 4×6 restarted, all-on with 31: 0 differing variables in all 6 files.
- Meters passive (m12 vs rs12_S): 0 differ.
- **Default-off (full12, every switch off incl. dyn_te_exact = 0) vs bug-fix arm gB11_off: 0 differing** in all 7 files.

**24 h impact, full12 all-on vs ctl64** (noise: T 0.149 K, ps 8.41 Pa, LH 3.24 W m-2):
- **Global:** T rms 0.281 K (mean −0.019), ps 22.4 Pa, LH rms 7.51 W m-2 (mean −1.91), T_sfc 0.702 K, precipitation mean −8.4e-7 kg m-2 s-1.
- **dyn_te_exact = 31 alone** (rs12_S vs rs11_S): T 0.153 K, ps 7.87 Pa, LH 3.20 W m-2, which is noise.
- **Land, 0-24 h (f24 bucket), imp24.py:**

| contrast | evcw | sbsno | land LH | t2m (K) |
|---|---|---|---|---|
| all-on vs ctl64 | **+35.5 %** (+20.8) | −9.3 % | **+1.69 %** (+0.92) | −0.020 |
| all-on with noahmp_fwet_opt = 0 vs ctl64 (job 10156346) | +0.19 % (−0.12) | +5.2 % | +0.66 % | +0.010 |
| fwet_opt 2 vs fwet_opt 0 | +35.2 % (+21.0) | −13.8 % | +1.02 % | −0.029 |
| noise (ctlc999 vs ctl64) | −0.03 % (−0.50) | +0.05 % | −0.04 % | −0.001 |

- **Attribution:** the land canopy evaporation change is entirely `noahmp_fwet_opt = 2`, canopy's E.2 option (a physics choice, not a closure term). With stock fwet, TH8 + TH9 leave evcw at noise (+0.19 %). TH9 removes TH8's −63 % (full9).
- The remaining land LH +0.66 % and sbsno +5 % with fwet 0 come from the rest of the series (ensfc2 options, E1, EP1, AIR1, ...) and are not attributed further.
- Whether fwet_opt 2 (vs 1) is wanted is canopy's and Ash's call. It is the one land signal well beyond noise.

### 9.8 full13 = full12 + preclag PL1 + suites 01-08 (final tree)

**Tree** (`meters/tools/mk13.sh`; all -no-fma):
- full13 = full12 + preclag `01_PL1_sfc_precip_t1_carry` + suites 01, 01b, 02, 03, 04, 05, 06, 07, 08 (`accepted/32-41`). The suites set is the one in `conservation/suites/patches`, byte-identical to the newest `suites/fixes/*_v6-v8`.
- `$U/cons/suites/patches` does not exist, and "01b v2" is mynnred's name for the current 01b (file v8).
- ensfc2 16b = 16 + exactly the integrator metadata fix already in full11 (content diff = that one line), so nothing changes.
- **Clashes:** the switch hunks of suites 03/04/06 in GFS_typedefs.F90 (namelist line, Model% copy) sit next to canopy TH9's new line. `rebase_r11.py REJ` applies each `.rej` hunk verbatim, one patch at a time.
- **mq13:** probes regenerated, then preclag's `meter_PL1_lag_v2.diff` applied on top. It moves the lag term to probe 1 of N+1, booked at the T1 the surfaces actually use.
- **All-on adds:** sfc_precip_t1_carry, gf_closure, mynn_sfc_heat, mynn_mix_sl. The last three are inert in p8, which calls neither GF nor MYNN.

**Master budget, frame F, 24 h, W m-2** (m13, job 10157244):

| term | full12 | **full13** |
|---|---|---|
| **RESIDUAL net of the declared terms** | +4.0e-11 | **+1.6e-12** |
| scheme frame-F gaps | ≤ 1.6e-12 | ≤ 1.2e-12 |
| declared: surface hand-off / S_chem / PH1 ice | +0.1136 / 1.44e-5 / −1.75e-3 | +0.1135 / 1.44e-5 / −1.74e-3 |
| consv_te fixer correction (fixer window) | −0.3038 (−2.5e-11) | −0.3040 (+1.4e-10) |
| **precipitation hand-off lag, as the surfaces book it** | −1.20e-2 | **0** (land 0, sea ice 0) |
| lag if booked at T1(N+1) (pre-PL1 definition) | | −1.21e-2 |
| surface vs atmosphere precipitation heat capacity Σ\|c·tprcp − c·P(N)\| / Σ c·P(N) | | 7.2e-12 |
| PBL water dW − flux (kg m-2 s-1) | ~1e-20 | +1.0e-20 |

**Every term is now at round-off or declared.** PL1 closes the lag exactly: the surfaces book step N's precipitation at the T1 it fell at, carried in the restart (phy_data gains one variable).

**Gates, full13** (`logs/final13.txt`; rs13 10157338/339, rsL13 10157364/365, gA13_off 10157389, gB13_off 10157391):
- Restart, 3×8 vs 4×6, and 4×6 restarted, all-on: 0 differing variables in all 6 files.
- Meters passive: 0 differ.
- **Default-off** (full13, every switch off) **vs bug-fix arm gB13** (gB11 + suites 01 01b 02 05 07 08): 0 differing in atmf000/006/024, sfcf006/024 and the 4 restart files.

**Suites 05 (satmedmfvdifq, dtdz1 = dt2·ρ_a·g/del) in p8: it changes p8, but only in the last bit.**
- **A/B** (gB13 vs gB13n05, job 10157414, every switch off):
  - at f000, after the first physics step: T and q identical; cloud water/ice differ by ≤ 7e-18 and rain/graupel mixing ratio by ≤ 4e-10 (Thompson thresholds amplifying the last bit);
  - at f06: T rms 0.036 K;
  - at f24: T rms 0.146 K, ps 8.1 Pa, which is noise (0.149 / 8.41). That is chaotic growth of a rounding difference.
- **Why the term is zero in p8.** The host builds statein `prsl = delp·rTv/Δφ` with rTv = con_rd·T·(1 + con_fvirt·max(1e-10, qv)) and Δφ from FV3's delz. satmedmfvdifq's `rho_a = prsl/(rd·t1·(1 + fv·max(q1, 1e-8)))`, with t1 = gt0 and q1 = vdftra. In p8, nothing modifies either between the start of physics and the PBL: the schemes before it are radiation, dcyc2t3 (tendencies only) and the surface schemes. So ρ_a·(zi2 − zi1)·g/del ≡ 1 algebraically.
  - Old and new dtdz1 differ only by rounding, except in columns where qv1 < 1e-8 or the host's prsl monotonicity clip fires.
- **Not a meter blind spot.** The PBL water meter compares the applied lowest-layer water change with exactly ρ_a·evap (dqsfc1/hvap). Any failure of the identity is precisely what it measures. It reads 4.5e-21 (full10) and 1.0e-20 kg m-2 s-1 (full13), i.e. relative 3e-16 of evaporation.
- **suites is right that the code is in control_p8. The term it fixes is zero there by construction.** Their 2.6e-8 kg m-2/day in the GFDL v16 case must come from one of the exceptions: qv < 1e-8, the clip, or t1/q1 ≠ the statein state. Their case differs from ours by do_sat_adj = T (fv_sat_adj) and lsm_noah. I have not identified which exception; that is for suites to check.
- 05 is harmless in p8 and keeps the identity exact where it fails. It is a NUMERICAL CONSISTENCY fix, at noise.

**Suites 08 (samfdeepcnv early return before the CA trigger) in p8: inert in our run.**
- control_p8 does run with do_ca = T, ca_sgs = T, ca_trigger = T.
- **A/B** (gB13 vs gB13n08, job 10157416): **bitwise identical** in all 9 files. In this 24 h C96 case, no block had zero deep-convective columns while a CA cell could re-enable one, so the early return never discarded a CA trigger.
- Our 3×8 = 4×6 gates therefore passed because the triggering case did not arise in this run, not because the old code is decomposition-safe. suites hit it at step 46 in p8_mynn. Without 08, another date or a longer run can lose reproducibility. 08 removes the dependence.

**24 h impact, full13 all-on vs ctl64** (noise 0.149 K / 8.41 Pa / 3.24 W m-2):
- **Global:** T rms 0.282 K (mean −0.019), ps 22.6 Pa, LH rms 7.46 W m-2 (mean −1.89), T_sfc 0.710 K.
- **full13 vs full12:** T 0.142 K, ps 8.0 Pa, LH 3.05 W m-2, which is noise. Land: evcw +0.12 %, LH +0.04 %, also noise.
- **Land vs ctl64** (imp24.py, 0-24 h): canopy evaporation **+35.6 %** (all noahmp_fwet_opt = 2, §9.7), sbsno −9.3 %, **land LH +1.73 %**, t2m −0.020 K.

### 9.9 full14 = full13 + Ash's decisions (final tree for the replay)

**Defaults (settled).** Every PHYSICS CHANGE and NUMERICAL CONSISTENCY switch defaults off. Recommended all-on settings: dyn_te_exact = 31, ngw_heat_opt = 2, noahmp_fwet_opt = 2, and MPAS 0014 option 2.

**The three changes** (`meters/tools/mk14.sh`; edits by `patches/tools/edits14.py`; all -no-fma):

1. **TH9 unconditional, with TH8.**
   - The `thompson_sed_actual` switch is gone: namelist, Model%, typedefs/meta, and the mp_thompson argument and meta.
   - Energy TH8 (`if (.true.)` form) is replaced by the water proposal's held TH8 (the same change, without the dead `if`). Canopy 03 is reversed by content and held TH9 applied.
   - **`patches/13_ccpp-thompson_TH8-TH9_unconditional.diff`** is cut on **fx** (one file, module_mp_thompson.F90). Its +/− lines are exactly held TH8 + held TH9. It **replaces energy 06 (TH8), canopy 02 (= TH8) and canopy 03 (TH9 behind the switch)**, and goes in the bug-fix arm.
   - Series delta from full13: `patches/full14/delta_TH8-TH9_unconditional.diff`.
2. **PL1 folded into EP1.**
   - The `sfc_precip_t1_carry` switch is gone. GFS_MP_generic_post, noahmpdrv and sfc_sice use their existing `sfc_precip_enthalpy` argument (the duplicate argument, declaration and meta are dropped).
   - GFS_restart writes `tprcp_t1` only when `Model%sfc_precip_enthalpy`. Delta: `patches/full14/delta_PL1_folded_into_EP1.diff`.
   - The metered tree's lag probe (preclag meter) now reads EP1's flag.
3. **NM10r.** Noah-MP soil takes the host's convective-phase decision (srflag) always. That is ensfc2's PH2 without the `precip_phase_host` gate; PH1 (atmosphere pays) and PH3 (glacier) stay under the switch.
   - Series delta: `patches/full14/delta_NM10r.diff` (noahmpdrv condition plus comments).
   - **Standalone water diff `patches/water_17r/17r_NM10r_noahmp_precip_phase.diff`** = NM10 + NM10r, cut against develop @112b1d46 (ccpp-physics 242a2fc) + water diffs 01-16. It applies -F0 there, and 18 (NM11) applies -F0 after it (`mk17r.sh`). It replaces water diff 17 in the proposal.
   - The bug-fix arm takes ensfc2's `12_sfc_NM10r.diff` as cut (on fx).

**Classification of NM10r: PHYSICS CHANGE.** NM10 decides convective phase with the lowest-layer air temperature (sfctmp < tfrz); the host decides with the skin temperature (tsfc < 273.15). Both are physical criteria, and water mass closes either way: Noah-MP errwat and the atmosphere water rows are identical with and without it. NM10r removes an inconsistency between what the land receives and what the host's srflag books (2.5 % of land frozen-precipitation mass, below). It does so by choosing the host's criterion, so it can be read as a choice, not only as a bug fix.

**Master budget, frame F, 24 h, all-on (m14 = mq14, job 10158200)**, with EP1 on, which now includes the PL1 behaviour:
- residual net of declared terms **+1.6e-12 W m-2**; scheme gaps ≤ 1.2e-12;
- declared: hand-off +0.1135, S_chem +1.44e-5, PH1 ice −1.74e-3;
- precipitation lag as the surfaces book it **0** (−0.0121 if booked at T1(N+1));
- fixer −0.304 W m-2.
These are identical to full13 to every printed digit, because all-on full14 is bitwise full13 (below).

**Land meter** (`meters/tools/instrument_land14.py`, diagnostic `instrument_land14b.py`; `logs/land14.txt`; all-off runs, where NM10r acts):

| | **NM10r** (m14b_off, job 10158474) | NM10 control, known-bad (m14bn_off, NM10r reverted, job 10158475) |
|---|---|---|
| frozen received vs host srflag·P, Σ\|diff\| / Σ host frozen | **1.2e-10** | **2.5e-2** |
| soil column-steps with precipitation / differing > 1e-3 P | 748,351 / 39,358 | 748,394 / 51,195 |
| Noah-MP total prcp vs host P | 6.1e-17 (0 columns > 1e-9) | 6.1e-17 |
| Noah-MP errwat, mean \|errwat\| per column-step | 6.6e-13 mm | 6.6e-13 mm |
| meter passive (m14b_off vs m14_off) | 0 of 194 differ | |

- **Phase agreement: 100 % by mass, to 1.2e-10.** NM10 disagrees with the host on 2.5 % of the frozen mass, and the meter sees it, so the check can fail.
- The 39k column-steps that still differ under NM10r carry on average ~2e-9 of a typical precipitating column's frozen amount. That is consistent with GFS_MP_generic_post leaving srflag = 0 ("rain") when total precipitation ≤ rainmin, while trace microphysics snow still reaches Noah-MP. It is the host's trace-precipitation convention on the grid-scale part, not a phase decision; NM10 and NM10r do not touch it.
- **Water closure:** Noah-MP's own water balance closes to 6.6e-13 mm per column-step. The atmosphere's physics water rows close to ≤ 3e-20 kg m-2 s-1 (PBL, Thompson), and the whole-physics row equals the h2ophys source (5.7e-12). Both are unchanged by NM10r.

**Gates, full14 (-no-fma)** (`logs/final14.txt`; rs14 10158238/239, rsL14 10158262/263, gA14_off 10158291, gB14_off 10158322, gB14x_off 10158333):
- Restart, 3×8 vs 4×6 (straight and restarted), all-on: 0 differing variables in all 6 files. phy_data has 25 variables all-on (tprcp_t1 with EP1) and 24 off.
- Meters passive: 0 differ.
- **Default-off vs bug-fix arm gB14** (fx + bug fixes with TH8+TH9 unconditional and NM10r): 0 differing in all 7 files. With EP1 off, full14 is bitwise to a tree with no PL1 code at all.
- **All-on full14 vs all-on full13: bitwise** in all 6 files. The three changes are exact re-expressions of what full13 all-on ran: TH9 on, PL1 on, PH2 on.

**24 h impact.**
- **NM10r A/B** (gB14_off vs gB14x_off, every switch off), land with imp_land14.py, 0-24 h:
  - evcw +0.16 % (noise −0.03 %); land LH −0.01 % (−0.04 %); T2m 0.000 K (−0.001); q2m +0.00 %;
  - SWE mean −0.003 % (rms 0.095 vs noise 0.054 kg m-2); depth rms 7.9e-4 vs 4.4e-4 m; accumulated snowfall rms 0.091 vs 0.078; snow cover rms 0.94 vs 0.54 %;
  - global: T 0.147 K, ps 8.2 Pa, LH 3.4 W m-2 (noise 0.149 / 8.41 / 3.24).
  - Means are at noise; the snow fields' rms is 1.2-1.8× noise, as expected from changing the phase of ~2.5 % of land frozen precipitation.
- **full14 all-on vs ctl64:**
  - global: T rms 0.28 K, ps 22.6 Pa, LH mean −1.89 W m-2;
  - land: evcw +35.6 % (noahmp_fwet_opt = 2), LH +1.73 %, T2m −0.020 K, SWE −0.06 %, snow depth −0.29 %, snowfall −0.9 %, snow cover −1.2 %. These are the same as full13, since the runs are bitwise.

## Section register

Every heading of the original, in order. "History" is the whole original, verbatim.

| Section | Subject | Status | Lives in |
|---|---|---|---|
| # UFS total-energy conservation: control_p8 (C96, 24 h, dt = 720 s) | title | current | `report.md` and `report.history.md` |
| ## Patch series (integration order on `$E/base`; …) | every patch, class, switch, residual it closes | current | `report.md` |
| ## Status (18 Oct 2026, final tree full14; integrator) | integrator status | superseded by the new `## Status` | `report.history.md` |
| ### Round-1 24 h global budget (see §7 for current) … | base and fx budget, frame E_D, per-scheme residuals | superseded by §7, then §9.4–§9.9 | `report.history.md` |
| ### Open items / not yet done | round-1 open items (R1, D1–D7, restart, surfaces) | superseded: all done (§6, §8, §9) | `report.history.md` |
| ## 1. Energy definitions, from the code | E_P and FV3 TE definitions | current (reference); budget frame is F (§9.1) | `report.history.md` |
| ### 1a. Physics frame (CCPP GFS physics) | E_P, per-kg latent heats, scheme audit | current (reference); E\* (meter c7) superseded by meter v2 (§9.1) | `report.history.md` |
| ### 1b. Dycore frame (FV3, non-hydrostatic, MOIST_CAPPA + USE_COND) | TE, fixer, coupling | current (reference) | `report.history.md` |
| ## 2. Meters (instrumentation only; separate diffs in `meters/`) | dycore and physics meters | current (reference); physics meter v2 in §9.1 | `report.history.md` |
| ## 3. Defects found and fixed (…) | FX1, SG1, CP1 | current | `report.md` |
| ### FX1: … | consv_te fixer weight | current | `report.md` |
| ### SG1: … | fv_sg total energy | current | `report.md` |
| ### CP1: … | state-update heating mass | current | `report.md` |
| ### Common red team, FX1 + SG1 + CP1 | layout, passive, restart argument | superseded by the gates of §9.8, §9.9 | `report.history.md` |
| ## 4. Design items: measured, not "fixed". … | D1–D11 table, +2.090 decomposition | superseded: D1 enpbl, D2 C1, D3a/D3b/D4 encnv, D5 K1/TFH, D6 R1 (§6), D7 §8/§9.3, D11 ensfc/ensfc2; D9, D10 booked in §6 | `report.history.md` |
| ### Kirchhoff-consistent enthalpy E\* per segment | E\* gaps per segment | superseded by §9.1, §9.2 | `report.history.md` |
| ## 5. Response of the forecast to the fixes (…) | step-1 and 24 h response; the ctlc999 noise control | current | `report.md` |
| ## 6. Round 2 | parent heading | current (parent) | `report.md` and `report.history.md` |
| ### R1: … BUG FIX | radiation heating at current mass | current | `report.md` |
| ### Restart and decomposition test: FX1 + SG1 + CP1 + R1 … | fxr restart and layout | superseded by the gates of §9.8, §9.9 | `report.history.md` |
| ### D7 (A→D wind-increment KE): evaluated, reported as DESIGN | D7 not fixed, recipe | superseded by §8 (D7 option) and §9.3 (D7S) | `report.history.md` |
| ### D9 and D10: how the master budget books them | S_chem declared, fixer as design | current | `report.md` |
| ## 7. Integration (…) and the master 24 h budget | integrate.sh, master table to mall_v3k | superseded by §9.4–§9.9 (construction notes archival) | `report.history.md` |
| ## 8. Round 3 | parent heading | current (parent) | `report.md` and `report.history.md` |
| ### D7 option: `05_fv3-cpl_ke_heating_option.diff` … | D7 closure; raw per-cell heating noisy | current (use with D7S, §9.3) | `report.md` |
| ### Full-closure demo: `$E/all_full` … | all_full frame-F budget +0.0836 | superseded by §9.2–§9.9 | `report.history.md` |
| ## 9. Round 4: frame, Kirchhoff consistency, water-mass KE, smooth D7 | parent heading | current (parent) | `report.md` and `report.history.md` |
| ### 9.1 Which accounting is right (derivation) | frame F, exact coupling requirement, meter v2 | current | `report.md` |
| ### 9.2 Why samf_kirchhoff added +0.122, and Thompson | diagnosis behind S1K and TFH | current reasoning; its gaps closed by §9.3 | `report.history.md` |
| ### 9.3 New fixes and options, round 4 | TH8, S1K, TFH, PBK, PBF, C8, D7S; per-switch impact | current, except "TH8 … about noise" (superseded by §9.5) and TH8 shipping alone (superseded by §9.9) | `report.md` |
| ### 9.4 Final integration: energy r4 + latent + trdyn v5 + ensfc2, everything on | full9/full10 budget, gates, PH1 vs D3A | superseded by §9.6–§9.9; the PH1/D3A disjointness still holds | `report.history.md` |
| ### 9.5 Acceptance items: default-off gate, fixer size, TH8 separability | full10 off-gate, fixer −0.5701/−0.5635, TH8 leak | superseded by §9.9 (gates, TH8 + TH9 unconditional); ctl64 fixer −0.5701 still current | `report.history.md` |
| ### 9.6 Final integration round: full11 = full10 + ensfc2 round 4 + canopy | full11 budget, lag meter, gates, impact | superseded by §9.7–§9.9 (lag closed by PL1, §9.8) | `report.history.md` |
| ### 9.7 full12 = full11 + fv3tally dyn_te_exact (v2): final tree | dyn_te_exact 31 vs 127, fwet attribution | current for the fixer (31 vs 127) and land attribution; "final tree" and the file flag superseded by §9.8, §9.9 | `report.md` |
| ### 9.8 full13 = full12 + preclag PL1 + suites 01-08 (final tree) | full13 budget, gates, suites 05 and 08 in p8, impact | current (all-on full14 = full13); "final tree" superseded by §9.9 | `report.md` |
| ### 9.9 full14 = full13 + Ash's decisions (final tree for the replay) | TH9, PL1 fold, NM10r; budget, land meter, gates, impact | current | `report.md` |

History: [`report.history.md`](report.history.md) holds the whole original report, verbatim.
