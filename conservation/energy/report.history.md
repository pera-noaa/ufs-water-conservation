*History of `report.md` (energy): the whole report as it stood on 18 October 2026, verbatim, headings untouched. The head is `report.md`.*

# UFS total-energy conservation: control_p8 (C96, 24 h, dt = 720 s)

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
| — | encnv 04 D4n | ugwpv1_gsldrag | Ash's decision | ngw_heat_opt (0; 1 or 2) | NGW net source; options 1 and 2 give the same budget to 5e-5 |
| — | NM12 `nm12/patches/20_NM12_…` (20b EMC companion not built) | Noah-MP land + glacier | BUG FIX | — | does not fire at dt 720: C96 bitwise identical |
| — | encpl 04 C1 | atmosphere.F90 | PHYSICS CHANGE | cpl_water_energy (0; bits 1 PE, 2 flow work, 4 sensible) | D2. **Bit 2:** FV3 books ±R_v·T on every vapour mass change at fixed delz, a net sink of −0.62; bit 2 adds +0.62 net (fwred) |
| — | encpl 05 K1 | Thompson | PHYSICS CHANGE | thompson_kirchhoff (.false.) | D5 |
| — | encpl 06 (rebased onto encnv as `accepted/10r_…`, by `patches/tools/rebase_encpl06.py`) | SAMF, Thompson, atmosphere | PHYSICS CHANGE | samf_kirchhoff (.false.) | precipitation-flux export for C1 bits 1/4 + S1 |
| 06 | TH8 `patches/06_ccpp-thompson_count_all_sedimented_precip.diff` | module_mp_thompson | BUG FIX, **ship only with canopy TH9 or E.2** | — | Thompson water leak 6.6e-12 kg m-2 s-1 → 0 (energy +2.4e-6 → 0). Alone it cuts land canopy evaporation −47 % at f24 (canopy, §9.5) |
| 07 | S1K `patches/07_ccpp-samf_kirchhoff_ice_and_initial_T.diff` | samfdeepcnv, samfshalcnv | PHYSICS CHANGE (completes S1) | samf_kirchhoff (.false.) | SAMF deep +0.080 → 5e-14, shallow +0.0028 → 1e-14 |
| 08 | TFH `patches/08_ccpp-thompson_frame_F_heating.diff` | mp_thompson | PHYSICS CHANGE | thompson_frame_heat (.false.) | Thompson +0.0083 → 5e-13 |
| 09 | PBK `patches/09_ccpp-satmedmfvdifq_filler_kirchhoff.diff` | satmedmfvdifq | PHYSICS CHANGE | pbl_kirchhoff (.false.) | PBL filler +4.8e-5 → 0 |
| 10 | C8 `patches/10_fv3-cpl_water_energy_bit8_water_KE.diff` | atmosphere.F90 | PHYSICS CHANGE | cpl_water_energy bit 8 (off) | water-mass KE −0.0025 → 0 |
| 11 | D7S `patches/11_fv3-cpl_ke_smooth.diff` | fv_arrays, fv_control, atmosphere | NUMERICAL CONSISTENCY | cpl_ke_smooth (0; use 32) | D7 max heating 0.87 → 0.013 K/step, still exact |
| 12 | PBF `patches/12_ccpp-fv3-pbl_condensate_flux_export.diff` | satmedmfvdifq, GFS_typedefs, atmosphere | PHYSICS CHANGE (C1 speciation) | acts under cpl_water_energy bit 4 | PBL −0.0049 → 8e-13 |
| — | latent 01a, 01b, 02, 03 (`accepted/12-15`) | SAMF scavenging, wet-deposition export, cmake, tend_opt | owner latent | — | energy-neutral; tend_opt_pbl 1 and 3 close (PBL gap ≤1e-12) |
| — | trdyn 02b, 03b, 04 INLQ, 01_DYN **v6** (`accepted/16, 17, 18c, 18d`; clashes re-anchored by `patches/tools/rebase_trdyn.py`) | SAMF tracer substep, PBL dry chem tracers, sw_core inline_q mass (BUG FIX, bitwise with inline_q off), FV3 dry tracer advection/remap/IC + dry_negadj | owner trdyn | dry_tracer_adv (.false.; on in final) | energy-neutral (chemistry tracers only) |
| — | ensfc2 04 SI1, 05 SI2, 06 NP1 (series prerequisites), 08 QR1, 09 CMC, 10 FL1 (bug fixes), 11 options; not 12 NM10r (pending Ash) | Noah-MP, sea ice, NSST, sfc drivers | owner ensfc2 | noahmp_canopy_heat=1, precip_phase_host, noahmp_sw_radshare, lw_sfc_consistent, sfc_evap_enthalpy, noahmp_heat_advect, noahmp_kirchhoff | surface side; enters the atmosphere budget as declared boundary flux (§9.4) |
| — | ensfc2 r4: 13 SL2, 14 CS1, 15 CB1 (bug fixes), 16 options_r4 (`accepted/24-27`; 13 hunk 8 re-anchored; **16's GFS_MP_generic_post.meta `[tgrs]` standard name fixed to physics_timestep_initial_air_temperature**) | Noah-MP, glacier, sea ice, MP_generic_post | owner ensfc2 | sfc_precip_enthalpy, lw_sfc_return (LW2 replaces LW1), noahmp_pore_air | snow combine / heat capacity; EP1 closes PH1 (§9.6) |
| — | canopy 01 E2, 03 TH9, 04 E1 (`accepted/28-30`; E2 re-anchored next to ensfc2 16; 02 = TH8) | Noah-MP fwet, Thompson sedimentation, NSST spray | owner canopy | noahmp_fwet_opt (all-on 2), thompson_sed_actual, nst_spray_opt (all-on 1) | TH9 neutralises TH8 over land; fwet 2 = +35 % canopy evaporation |
| — | fv3tally 01 dyn_te_exact v2 (`accepted/31`) | dyn_core, fv_dynamics, fv_mapz, sw_core, ... | owner fv3tally: bits 1-16 BUG FIX, 32/64 DESIGN | dyn_te_exact (0; all-on 31) | fixer correction −0.564 → −0.304 W m-2 |
| — | preclag 01 PL1 (`accepted/41`); ensfc2 16b = 16 + integrator meta fix | GFS_MP_generic_post, noahmpdrv, glacier, sea ice, GFS_restart | owner preclag | sfc_precip_t1_carry (all-on T) | precipitation hand-off lag −0.0121 → 0 |
| — | suites 01, 01b, 02, 07 (BUG FIX), 03, 04, 06 (switches), 05, 08 (`accepted/32-40`; 03/04/06 switch hunks re-anchored, REJ stage) | MYNN, GFDL MP v3, GF, satmedmfvdifq, samfdeepcnv | owner suites | gf_closure, mynn_sfc_heat, mynn_mix_sl | in p8: 05 rounding-level, 08 bitwise inert (§9.8) |
| 13 | TH8+TH9 `patches/13_ccpp-thompson_TH8-TH9_unconditional.diff` (on fx; **replaces 06, canopy 02, canopy 03**) | module_mp_thompson | BUG FIX | — (TH9 now unconditional) | Thompson water leak → 0; TH9 removes TH8's land side effect |
| — | PL1 folded into EP1 (`patches/full14/delta_PL1_folded_into_EP1.diff`) | GFS_typedefs, GFS_restart, MP_generic_post, noahmpdrv, sfc_sice | owner preclag | sfc_precip_enthalpy (EP1) | lag 0 with EP1; restart field only with EP1 |
| — | NM10r (`patches/full14/delta_NM10r.diff`; water `patches/water_17r/17r_…` replaces water 17) | noahmpdrv, module_sf_noahmplsm | PHYSICS CHANGE | — (unconditional) | land phase = host to 1.2e-10 of frozen mass (NM10 2.5e-2) |
| — | meters `meters/meter_*.diff` + encpl `meter_r2` (frame F) | | INSTRUMENTATION | — | — |

## Status (18 Oct 2026, final tree full14; integrator)

- **Final tree full14** = full13 + Ash's decisions (§9.9): TH8+TH9 unconditional (`patches/13_…`, cut on fx, replaces energy 06 and canopy 02/03), PL1 folded into EP1, NM10r (water diff `17r`). -no-fma. The replay agent regenerates the verified series from it.
- **Defaults:** every PHYSICS CHANGE / NUMERICAL CONSISTENCY switch is off. Recommended all-on: dyn_te_exact 31, ngw_heat_opt 2, noahmp_fwet_opt 2, MPAS 0014 option 2.
- **Closure (all-on):** residual net of declared terms **+1.6e-12 W m-2**, every scheme gap ≤ 1.2e-12, precipitation lag 0 (EP1).
- **Declared:** hand-off +0.1135, h2ophys +1.44e-5, PH1 ice −1.74e-3.
- **Fixer:** −0.304 W m-2 (ctl64 −0.570).
- **Gates:** restart, 3×8/4×6, meters passive, and default-off vs fx + bug fixes (with TH8+TH9 and NM10r) are all bitwise. **All-on full14 = all-on full13 bitwise.**
- **NM10r** (PHYSICS CHANGE): land phase agrees with the host to 1.2e-10 of frozen mass (NM10: 2.5e-2). Noah-MP water closes to 6.6e-13 mm per column-step. Land impact is at noise in the means; snow rms is 1.2-1.8× noise.
- **Impact vs ctl64:** T 0.28 K, ps 23 Pa, LH −1.9 W m-2; land canopy evaporation +36 % (fwet_opt 2), land LH +1.7 %.
- Details: §9.9 (final), §9.8, §9.7, §9.6, §9.5; patch series above.

### Round-1 24 h global budget (see §7 for current), frame E_D = TE_FV3 + hvap·Wv − hfus·Wi, W m-2, 119 metered steps

| term | base (m3, job 10150601) | + FX1 SG1 CP1 (mfx1, job 10150652) | class |
|---|---|---|---|
| E_D(end) − E_D(start) | +5.1849 | +5.1818 | |
| boundary flux F = rad(TOA − sfc) + SH + LH + hfus·P_ice | +3.1064 | +3.0916 | |
| **residual** | **+2.0785** | **+2.0902** | |
| dycore: consv_te fixer window | −5.526e-4 | **−3.6e-10** | DEFECT FX1, closed |
| dycore: fv_subgrid_z (A-grid TE) | −1.58e-4 (m1) | **+3.0e-11** | DEFECT SG1, closed |
| dycore: other (Rayleigh is inside the fixer window; neg_adj3 +1e-10) | +3.96e-3 | +4.11e-3 | fv_sg heating whose KE loss lands on the D-grid in fv_update_phys (counted below) |
| physics: Σ schemes (dE_P − F) | +0.8024 | +0.7975 | design (table below) |
| coupling: heating injected − physics cp·ΔT·m_p | −8.63e-3 | **+3.9e-10** | DEFECT CP1, closed |
| coupling: delp/q water-mass write (TE) | +1.2998 | +1.3069 | DESIGN D2 (constant-mass physics; §4) |
| coupling: KE_D change − physics KE change | −1.853e-2 | −1.835e-2 | DESIGN (A→D wind mapping) |
| checks: physics vs dycore latent terms; E_P(state-in) − E_P(dycore) | 3e-12; 6e-11 | 1e-12; 0 | round-off |

**Per-scheme residual** r = ΔE_P − F (physics frame §1a), base run m3, W m-2. Σ|r| is the area-integral of the column |r|.

| segment | ΔE_P | F | r | Σ|r| | what r is |
|---|---|---|---|---|---|
| radiation (dcyc2t3) | −103.37 | −103.36 | −7.65e-3 | 2.70e-2 | heating rates (K/s) from the radiation-time delp applied to the current delp. DESIGN, minimal fix R1 proposed |
| surface loop, sfc_diag, interstitials | 0 | 0 | 0 | 0 | no atmospheric state change |
| PBL (satmedmfvdifq) | +106.68 | +105.25 | **+1.4315** | 2.67 | dspheat = TKE ε (≈ +3.7) > mean-flow KE loss (−2.25). DESIGN |
| GWD (GSL drag + UGWP-v1 NGW) | −0.0498 | 0 | −0.0498 | 0.64 | GSL drag removes KE with no heating; NGW heating is parameterised. DESIGN |
| photochem (h2ophys) | +1.4e-5 | 0 | +1.4e-5 | — | qv source with no heat. DESIGN |
| SAMF deep | −0.5391 | 0 | −0.5391 | 0.54 | −0.420 detrained ice without hfus; −0.119 CMT KE loss without heating |
| SAMF shallow | −0.0469 | 0 | −0.0469 | 0.047 | −0.018 ice; −0.029 CMT KE |
| Thompson + MP_post | +1.2329 | +1.2186 | +0.0144 | 0.32 | Thompson's own L(T) and cp_m vs the GFS constants. DESIGN |
| **all physics** | +3.909 | +3.106 | **+0.802** | 3.39 | |

Water closes in every segment to ≤ 1.2e-16 kg m-2 s-1 (|dW − water flux|), which confirms the flux bookkeeping.

### Open items / not yet done
- **R1** (radiation: carry layer flux divergence, or rescale htr by delp_rad/delp_now) is designed but not implemented (D6, −0.0077 W m-2).
- **D1-D5 and D7** need owner decisions. Minimal changes are listed in §4.
- **Not run:** restart test (the fixes are stateless; the argument is in §3); other suites/hosts (argued in §3).
- **Surface components** (Noah-MP, NSST, sea ice) are not energy-metered in this round (D11).
- **Per-process Kirchhoff gaps inside Thompson** are not metered. The per-kg table is in §1a.

**Job and run index** (`$E/runs/*`):

| run | job | what |
|---|---|---|
| ctl64 | 10150221 | control |
| m1 | 10150271 | dycore meters |
| m3 | 10150601 | all meters, base |
| mfx1 | 10150652 | all meters + FX1 SG1 CP1 |
| fx1 | 10150684 | fixes, no meters |
| ctl64L | 10150838 | layout 4×6 |
| mfx1L | 10150839 | metered fixes, layout 4×6 |
| fxsg | 10150804 | SG1 only |
| fxfc | 10150805 | FX1 + CP1 |
| fxfx | 10150948 | FX1 only |
| fxcp | 10150949 | CP1 only |
| ctlc999 | — | consv_te = 0.999 |

Exes are in `$E/exe/`, trees in `$E/{base,meter,mfx,fx,fxsg,fxfc,fxfx,fxcp}`, and build logs in `$E/logs/`.

## 1. Energy definitions, from the code

### 1a. Physics frame (CCPP GFS physics)

**State-in** (`atmosphere.F90:atmos_phys_driver_statein`, ~2200-2262):
- The physics layer mass is m_p = delp·(1 − Σ condensate)/g, i.e. dry air plus vapour.
- Mixing ratios are relative to m_p, so tracer mass q_p·m_p = q_dyn·delp exactly.
- m_p is held **fixed** through all of physics.
- Constants are physcons: con_cp = 1004.6, con_hvap = 2.5e6, con_hfus = 3.3358e5, con_g = 9.80665. They are identical to the FV3 cp_air, hlv, hlf, grav (`EBC` line).

**Physics-frame energy (meter EMS):**

E_P = Σ_k m_p,k [con_cp·T + con_hvap·qv − con_hfus·(qi+qs+qg) + ½(u²+v²)]

Liquid is the reference phase, condensate has no heat capacity, and φ is constant.

**Meter state:** "effective state" X0 + dtp·(pending process-split tendency).

**Boundary fluxes F per segment:**
- **Radiation:** dtp·[xmu·(SW_net,TOA − SW_net,sfc) + LW_up,sfc − LW_dn,sfc − OLR], radiation-time fluxes.
- **PBL:** dtp·(dtsfc1 + dqsfc1).
- **Thompson:** + con_hfus·(snow + ice + graupel) per kg removed.
- Liquid precipitation carries 0.

**Kirchhoff-consistent enthalpy E\* (meter c7):**

E\* = Σ_k [m_d·cp_air·T + m_p·((qv·cp_vap + ql·c_liq + qi·c_ice)·T + Lv00·qv − Li00·qi) + (m_d + W)·K]

- Dry mass m_d is frozen at its value at probe 1.
- The heat capacities are FV3's: cp_vap = 1846, c_liq = 4185.5, c_ice = 1972.
- Lv00 = hvap − (cp_vap − c_liq)·T0 and Li00 = hfus − (c_liq − c_ice)·T0, with T0 = 273.15.
- This is the enthalpy FV3's cvm-based TE becomes once its missing latent reference terms are added. The FV3 fixer energy is cvm·T + φ + K with no latent terms; at constant pressure the enthalpy form applies, and Rm·T is supplied by the delz expansion. That is verified: the fv_update_phys injection equals Σ cpm·ΔT·delp/g to round-off.

**Latent heat each scheme effectively applies per kg of phase change, versus the E\* (FV3) value**

FV3 E\* gives:
- condensation: L_h(T) = hvap − 2339.5·(T − T0)
- deposition: L_s(T) = hvap + hfus − 126·(T − T0)
- freezing: L_f(T) = hfus + 2213.5·(T − T0)

| process | scheme | L applied (J/kg) | gap vs E\* (J/kg) | at 250 K |
|---|---|---|---|---|
| condensation / rain evaporation | SAMF deep & shallow, satmedmfvdifq filler | hvap (const) | +2339.5·(T−T0) | −54 kJ/kg (−2.2 %) |
| detrained ice (T < 263 K ramp) | SAMF | 0 (no hfus) | −L_f(T) | −282 kJ/kg |
| condensation | Thompson | (hvap − 2112·(T−T0))/(1 − 0.113 q) | +227.5·(T−T0) (+ the 0.887/cp_m factor) | −5.3 kJ/kg |
| deposition | Thompson | lsub = hvap + hfus (const) | +126·(T−T0) | −2.9 kJ/kg |
| freezing | Thompson | hfus + 2112·(T−T0) | −101.5·(T−T0) | +2.3 kJ/kg |
| melting (T > T0) | Thompson | hfus (const) | −2213.5·(T−T0) | — |
| sedimentation PE | all | 0 (no φ for condensate in physics) | FV3 removes precipitating water at its layer's φ when delp is rebuilt | see §3 |

**Scheme thermodynamics, from the audit:**

| scheme | what it actually conserves | source |
|---|---|---|
| RRTMG + dcyc2t3 | Σ cp·m·htr = F_net(top) − F_net(sfc) exactly, **for the radiation-time delp**. SW is scaled by xmu each step; LW is frozen between the hourly calls. TOA fluxes are not xmu-scaled in the code (the meter scales them). | radsw_main 1253/1333, radlw_main 2767, dcyc2t3 388/465/507 |
| satmedmfvdifq | s = cp·T + g·z diffused conservatively. Surface heat and moisture enter exactly as dtsfc1 and dqsfc1 (rho_a = del/(g·Δz)). Dissipative heating is the TKE ε of the last of 20 TKE substeps, **not** the mean-flow KE loss. | satmedmfvdifq.F 2445, 2876, 2933, 2059-2071 |
| GSL drag (ls/bl, ss, tofd) | removes KE with **no heating** (gsd_diss_ht_opt = .false.) | drag_suite.F90 422, 543, 1157-1169 |
| UGWP-v1 NGW (do_ugwp_v1 = T, knob_ugwp_doheat = 1) | parameterised heating, not −dKE | cires_ugwpv1_solv2.F90 ~817-858 |
| SAMF deep/shallow | h = cp·T + g·z + hvap·qv conserved by construction. Detrained ice gets **no hfus**. CMT changes KE with **no heating**. | samfdeepcnv.f 3354, 3757; samfshalcnv.f 2288, 2682 |
| Thompson | Cp·(1+0.887·r_v); Lv(T); constant lsub; freezing lsub − Lv(T); constant melting lfus. **Not an exact invariant** of any single E. | module_mp_thompson.F90 2414-2416, 3244, 3400-3411, 4264 |
| h2ophys | changes qv with no heating | module_h2ophys.F90 |

### 1b. Dycore frame (FV3, non-hydrostatic, MOIST_CAPPA + USE_COND)

**TE** (`fv_mapz.F90:compute_total_energy`) = Σ delp/g·[cvm·T + ½(φ_k + φ_k+1) + ½w² + KE_D], where:
- cvm = (1−qv−qc)·cv_air + qv·cv_vap + ql·c_liq + qi·c_ice, with cv_vap = 3·Rv and c_ice = 1972;
- delp is the total mass;
- KE_D is the D-grid KE.

There are no latent-heat terms.

**consv_te = 1 fixer** (Lagrangian_to_Eulerian, last remap):
- te0 is taken at the start of fv_dynamics, before Rayleigh_Super.
- dtmp = Σ(te0 − te)·area / (cv_air·Σ pkz·delp·area).
- The correction is applied as pt ← (pt + dtmp·pkz)/((1+r_vir·qv)(1−qc)), i.e. T gains dtmp·pkz/((1+r_vir·qv)(1−qc)) at heat capacity cvm.
- The energy actually added is therefore Σ cvm/(cv_air(1+r_vir·qv)(1−qc))·cv_air·dtmp·pkz·delp, not Σ(te0 − te). → **FX1.**

**Outside the fixer window:** neg_adj3 (end of fv_dynamics), and fv_subgrid_z (atmosphere_dynamics; fv_sg_adj = 1800, k_bot = n_sponge = 42). fv_subgrid_z's wind increments reach the D-grid only through fv_update_phys's u_dt.

**Coupling** (`atmosphere_state_update`, then `fv_update_phys`, phys_hydrostatic = .true. branch):
- **(i) Water mass write:** delp_new = delp·(1 − Σq_w) + Σ m_p·gq0_w. Water leaving or entering a layer takes that layer's cvm·T + φ + K with it.
- **(ii) Heating:** pt += t_dt·dt·cp_air/cpm(q_new), with delz scaled by T_new/T_old. The meter shows the energy injected equals Σ cp_air·t_dt·dt·delp_new/g to round-off (|Δ| ≤ 4e-9 W m-2 per step). But the physics heated m_p_old, so the excess is Σ cp_air·t_dt·dt·(delp_new − m_p_old)/g. → **CP1.**
- **(iii) Winds:** A-grid increments are mapped to the D-grid. KE_D change ≠ KE_A change (design).

## 2. Meters (instrumentation only; separate diffs in `meters/`)

**`meters/meter_fv3_dycore_coupling.diff`**, generated by `meters/tools/instrument_eb_dyn.py`:
- `eb_state` in fv_mapz.F90 returns rank sums of x·delp·area/g (real(8)) for 12 quantities: IE = cvm·T, PE, KE_D, ½w², KE_A, Wv, Wl, Wi, M, cp_air·T·(1−qc), KE_A·(1−qc), cpm·T.
- They are evaluated at 10 probes:
  1. atmosphere_dynamics start
  2. after fv_dynamics
  3. after fv_subgrid_z
  4. state_update start
  5. after the delp/q write
  6. after fv_update_phys
  7. te0 point
  8. after Rayleigh_Super
  9. after the last remap (fixer applied)
  10. after neg_adj3
- Extras (EBX): te0 by g_sum; the fixer's intended correction; E_Flux; the intended heating Σ cp_air·t_dt·dt·delp/g.
- `mpp_sum` over ranks; one line per probe per step on the root PE (`EBD`, `EBX`).

**`meters/meter_ccpp_physics.diff`**, generated by `meters/tools/instrument_eb_phys.py`:
- 12 probe schemes em_p01..12 plus `energy_meter_common.F90`, inserted in the suite XML after: GFS_suite_interstitial_1, GFS_surface_composites_pre, dcyc2t3, sfc_diag_post, GFS_PBL_generic_post, GFS_GWD_generic_post, GFS_photochemistry_post, GFS_DCNV_generic_post, GFS_SCNV_generic_post, cnvc90, GFS_MP_generic_post, GFS_physics_post.
- **Per column:** E_P components of the effective state, total water, and E\*.
- **Fluxes are captured where they are valid:** radiation at p03, PBL at p05, precipitation at p11. Capgen interstitials are not valid in later groups; a first version that read them at p12 got zeros.
- p12 forms segment differences and residuals. The column-queue offsets are per probe and reset on each new kdt, because CCPP runs all blocks of a group before the next group. Results are reduced with `MPI_Reduce` (lines `EMS`, `EMF`).

**Tables:** `meters/tools/eb_table.py <out>`, plus `eb_check.py` (per-step), `cmp_runs.py` and `cmp_where.py` (run differences).

**Round-off checks (fixed run mfx1, W m-2, 119-step means):**

| check | value |
|---|---|
| fv_update_phys IE+PE vs intended injection, per step | ≤ 3e-9 |
| latent terms, dycore vs physics | 1e-12 |
| physics E_P(state-in) vs dycore-derived E_P | 0 |
| gaps between consecutive probes with no code between | 0 exactly |

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

### Common red team, FX1 + SG1 + CP1
- **Decomposition:** layout 3×8 vs 4×6 is **bitwise identical**, both for the control (ctl64 vs ctl64L) and with the fixes (mfx1 vs mfx1L). Closure holds at round-off on 4×6.
- **Meters stay passive with the fixes:** fx1 (no meters) is bitwise identical to mfx1.
- **Restart:** the fixes carry no state between steps, so restart behaviour is that of the base (not separately run).
- **Response:** f24 differences vs ctl64 (rms T 0.16 K, ps 8.5 Pa) are threshold amplification starting at step 1, mostly from FX1+CP1 (fxfc). The step-1 differences are all levels, max 2.46 K at levels 110-113. Attribution and perturbation control: see §5 (pending runs fxfx, fxcp, ctl consv_te = 0.999).

## 4. Design items: measured, not "fixed". Each needs an owner decision, and changing any of them changes the physics.

After FX1, SG1 and CP1, the 24 h residual is **+2.090 W m-2** (frame E_D). It decomposes into the rows below, which sum to it within 1e-3. Round-off closure of the whole atmosphere is **impossible without changing these designs**.

| # | item | W m-2 (fixed run) | where in the code | minimal change that would close it |
|---|---|---|---|---|
| D1 | PBL dissipative heating = TKE ε (last of 20 substeps, clipped, TKE floors), not the resolved-flow KE loss | **+1.427** (heating ≈ 3.68 vs KE loss 2.25) | satmedmfvdifq.F 2059-2071, 2933 | dspheat heating = −Δ(½|v|²)/cp per layer from the implicit momentum solve, including surface drag (CAM/IFS practice) |
| D2 | Water-mass write at coupling: the physics is constant-mass, and FV3 adds or removes the water mass at each layer's own cvm·T, φ, K. IE +1.81: evaporated vapour gets layer-1 T; precipitation is removed at its condensation layer's T with cv_vap. PE −0.51: precipitation PE removed at condensation height, i.e. the frictional heating by falling hydrometeors is lost. K −0.003. | **+1.307** | atmosphere.F90 1665-1678 (delp rebuild) | an explicit boundary enthalpy + PE flux for E and P, as in CAM's dme_adjust + energy fixer. It changes the surface energy-flux definition. Heating the column by precipitation PE would recover the −0.51. |
| D3a | SAMF detrained ice gets no hfus (liquid-only thermodynamics; T ramp 263→233 K) | −0.438 (deep −0.420, shallow −0.018) | samfdeepcnv.f 3757-3764; samfshalcnv.f 2682-2690 | heat hfus/cp·Δqi at the partition. ~0.44 W m-2 of extra upper-tropospheric heating, so a physics change. |
| D3b | SAMF convective momentum transport: KE loss with no heating | −0.148 (−0.120, −0.029) | samfdeepcnv.f 3363; samfshalcnv.f 2297 | dissipative heating −ΔKE/cp per layer (CAM ZM does this) |
| D4 | GWD: GSL ls/bl/ss/tofd drag removes KE with no heating (gsd_diss_ht_opt = .false.); UGWP-v1 NGW heating is parameterised | −0.049 | drag_suite.F90 422/543; cires_ugwpv1_solv2.F90 | heating = −ΔKE/cp for all drag components |
| D5 | Thompson: own Cp·(1+0.887·r_v) and L(T), constant lsub/lfus. Not an invariant of any single E; vs GFS constants | +0.014 (Σ|r| 0.32) | module_mp_thompson.F90 2414-2416, 3244, 3400-3411 | a trade-off: choosing a Kirchhoff slope changes latent heating by 0.2-2 % at 220-250 K (table §1a) |
| D6 | Radiation: hourly heating rates in K s-1 from the radiation-time delp, applied to the current delp | −0.0077 (Σ|r| 0.027) | radsw_main 1333, radlw_main 2772, dcyc2t3 465/507 | **R1**: store the radiation-time layer mass (or per-layer flux divergence in W m-2) and scale htr by delp_rad/delp_now in dcyc2t3. Closes to round-off by construction; not implemented yet (needs a new persistent field) |
| D7 | A-grid → D-grid wind increments (physics and fv_subgrid_z): KE_D change ≠ KE_A change | −0.018 | fv_update_phys → update_dwinds_phys | none minimal; a D-grid KE-consistent increment mapping, or heating the KE mismatch |
| D8 | fv_subgrid_z heating, whose KE loss is booked on the D-grid in D7 | +0.004 | (bookkeeping of D7) | — |
| D9 | h2ophys: qv source/sink with no heating | +1.4e-5 | module_h2ophys.F90 | — (chemistry) |
| D10 | consv_te fixer: the dycore *gains* 0.570 W m-2 of TE per day of dynamics (remap + d_con + damping) and the fixer removes it, distributed globally by pkz | (exact after FX1) | fv_mapz.F90 | deliberate design; reported |
| D11 | Atmosphere ↔ surface radiation interface: Noah-MP absorbs SW with its own albedo, cosz and 0.7/0.3 split; LW is emitted at current Ts. The atmosphere's LW column uses radiation-time surface fluxes. sfc_sice splits sfcnsw non-additively. | not metered yet (SW: adjsfcnsw = xmu·rad sfc net to 1e-7) | noahmpdrv.F90 1033; module_sf_noahmplsm.F90 1037, 3190; sfc_sice.f 308-312 | surface-component budgets; out of this first round |

### Kirchhoff-consistent enthalpy E\* per segment
The meter's c7 column gives E\*, the FV3-heat-capacity enthalpy. These are not yet process-resolved: the gaps include the definitional sensible enthalpy of water crossing segment boundaries, ~c_l·T·P ≈ 20 W m-2 for SAMF.

| segment | ΔE\* − ΔE_P (W m-2) |
|---|---|
| radiation | −0.264 (cpm vs cp heat capacity) |
| PBL | +41.6 (evaporated water at Lv00 + cp_v·T vs hvap) |
| SAMF deep | −19.46 |
| SAMF shallow | −3.46 |
| Thompson | −13.19 |
| GWD | +3e-5 |

The per-process split (condensation / deposition / freezing / melting inside Thompson; SAMF rain evaporation) is **not** metered. The per-kg gaps are in §1a.

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

### Restart and decomposition test: FX1 + SG1 + CP1 + R1 (exe `fv3_e_fxr.exe`), `$E/mkrestart.sh`

**Setup.**
- `<name>_S`: 24 h straight, writing restart at 12 h.
- `<name>_R`: warm start from S's 12 h restart, 12 → 24 h. Settings follow `tests/tests/control_restart_p8`: warm_start, no external/nggps IC, make_nh = F, mountain = T, na_init = 0, and **nstf_name = 2,0,0,0,0**.
- A first attempt kept nstf_name = 2,1,0,0,0, which re-initialises the NSST profile on restart (systematic SST −0.15 K). That attempt failed identically for the unmodified base, which is why the setting matters.

| comparison | atmf/sfcf 018, 024 | RESTART 24 h (fv_core, fv_tracer, fv_srf_wnd, sfc_data, phy_data) |
|---|---|---|
| rs_fxr_S vs rs_fxr_R (3×8) | 0 of 18 / 0 of 194 variables differ | 0 differ |
| rs_fxr_S vs rs_fxrL_S (4×6 straight) | 0 / 0 | 0 |
| rs_fxr_S vs rs_fxrL_R (4×6 restart from 4×6 12 h) | 0 / 0 | 0 |

Jobs: 10151733/34 (3×8) and 10151855/56 (4×6). All **bit-identical** (value comparison of every numeric variable; the byte-level `cmp` differs only through netCDF metadata).

### D7 (A→D wind-increment KE): evaluated, reported as DESIGN

**Measured.** KE_D change − physics KE change = −0.01858 W m-2 (mfxr). About +0.0041 of the wind change is the fv_subgrid_z increment, which is applied with the physics u_dt, so the A→D mapping proper is ≈ −0.014 W m-2.

**Why not fixed now.** The cleanest energy-consistent option is cell-local heating by (KE_A target − KE_D realised) per D-grid cell and layer, around update_dwinds_phys. But:
- (i) The KE_A target is ambiguous at this point. u_dt mixes fv_subgrid_z increments, whose A-grid KE loss is already heated in fv_sg, with physics increments. A correct target needs the post-dynamics ua copy, i.e. new state passed from atmosphere.F90.
- (ii) It is a per-cell energy fixer of an interpolation error, not the restoration of something the code intends. Under the bar it is a PHYSICS CHANGE.
- A KE-consistent D-grid mapping is not layer-local-small.

**Minimal recipe for later:**
1. Keep ua0/va0 = ua/va at the end of fv_dynamics.
2. Target_k = ½|ua0 + dt·u_dt|² − ½|ua0|² minus the fv_sg KE already heated.
3. Heat pt += (target − ΔKE_D)/cpm with the phys_hydrostatic delz scaling, after update_dwinds_phys.

That is about 40 lines in fv_update_phys plus 2 arrays.

### D9 and D10: how the master budget books them

- **D9, h2ophys:** a declared internal source S_chem = hvap·Δqv from the photochemical water source/sink. It enters the closure as S_chem = +1.4e-5 W m-2, not as a residual. The water budget books the same Δqv as the chemical water source.
- **D10, consv_te fixer:** declared design. The dycore's own TE error over each fv_dynamics call (+0.570 W m-2 created by remap, d_con, damping and transport) is removed by the fixer and redistributed globally, weighted by pkz. The budget books the fixer window as one term. After FX1 it closes to round-off (≤ 2e-10). The applied correction E_Flux (−0.570 W m-2) is reported as information, not as a boundary flux.
- **Closure statement:** E(24 h) − E(0) = ∫F_boundary + S_chem + Σ_design (D1-D8, D11) + round-off, with every term metered.

## 7. Integration (`$E/integrate.sh <tag> <patches...>`) and the master 24 h budget

**Construction.**
- `$E/all_<tag>` = fx (FX1 SG1 CP1) + R1 + the accepted patches in order. `$E/mall_<tag>` is its metered twin (mfx + R1 + the same patches).
- Accepted patches are copied to `$E/accepted/`. The script finds the patch base and the -p level by dry run with fuzz 0, and refuses any patch that does not apply cleanly to both trees.
- R1 is applied before the patches. It touches different files and hunks than FV2, enpbl 04 and D3A (enpbl's GFS_typedefs hunks are in Model, R1's in Radtend), so the result is identical to the requested order fx → FV2 → R1 → enpbl → D3A.

**Gates.**
- Every metered twin is bitwise identical to its plain tree (atmf024).
- enpbl default-off gate: `all_v2` (dspheat_ke = F) vs `all_v1` is **bitwise identical** (atmf006/024, sfcf024).
- FV2: closed terms stay at round-off (fixer 1e-10, CP1 6e-11, R1 4e-13). Design terms move only at threshold-noise level (residual 2.087 → 2.097, vs the ctlc999 spread).

**Master table.** W m-2, 24 h means over 119 metered steps, frame E_D. Physics row = r = ΔE_P − F.

| term | mfx1 (FX1 SG1 CP1) | mfxr (+R1) | mall_v1 (+FV2) | mall_v2k (+enpbl, dspheat_ke = T) | **mall_v3k (+D3A)** | status |
|---|---|---|---|---|---|---|
| dycore fixer window | −3.6e-10 | +1.5e-10 | +1.0e-10 | +2.7e-10 | +1.5e-10 | FX1 closed |
| fv_subgrid_z (A-grid TE) | +3e-11 | — | — | — | — | SG1 closed |
| coupling heating vs physics | +3.9e-10 | +8.1e-11 | +6.2e-11 | −1.1e-10 | +7.2e-11 | CP1 closed |
| radiation (dcyc2t3) | −7.66e-3 | −8.4e-14 | ~1e-13 | −4.3e-13 | +1.1e-12 | R1 closed |
| PBL | +1.427 | +1.43 | +1.43 | +6.0e-13 | −1.6e-12 | enpbl 04 closes it (PHYSICS CHANGE, switch) |
| SAMF deep | −0.540 | −0.54 | −0.54 | −0.540 | **−0.1194** | D3A closes the ice part; left: CMT KE (D3b) |
| SAMF shallow | −0.047 | −0.047 | −0.047 | −0.047 | **−0.0292** | D3A ice part closed; left: CMT KE (D3b) |
| GWD | −0.049 | −0.05 | −0.05 | −0.0501 | −0.0504 | D4 (encnv, pending) |
| Thompson | +0.0139 | +0.014 | +0.014 | +0.0142 | +0.0144 | D5 (encpl K1, pending) |
| photochem (h2ophys) | +1.44e-5 | same | same | same | +1.44e-5 | D9: declared source S_chem |
| coupling: water-mass write | +1.307 | +1.296 | +1.301 | +1.273 | +1.256 | D2 (encpl C1, pending) |
| coupling: KE_D − KE_phys | −0.0183 | −0.0186 | −0.0184 | −0.0200 | −0.0200 | D7: design, ≈ −0.014 net of fv_sg |
| dycore other (fv_sg heat / D-grid KE) | +0.0041 | +0.0041 | +0.0041 | +0.0041 | +0.0041 | D8 (pairs with D7) |
| **residual total** | 2.090 | 2.087 | 2.097 | 0.633 | **1.056** | |

The residual rises from v2k to v3k because D3A adds the missing +0.44 W m-2 of fusion heating. The atmosphere now gains it as it should, and it shows on the coupling side once the scheme term is closed. Coordinator's number for enpbl alone: 0.627; here 0.633, with R1 + FV2 included.

**Remaining residual (v3k, 1.056)** = D2 1.256 + D3b −0.149 + D4 −0.050 + D7/D8 −0.016 + D5 +0.014 + S_chem 1.4e-5. Sum 1.055.

**encpl 04 (cpl_water_energy) and 05 (thompson_kirchhoff): compose check, not integrated.**
- **Textual:** dry-run with fuzz 0 applies cleanly on all_v2 and mall_v2 (offsets only).
- **Semantic, 04 vs CP1/FV2/R1:**
  - Its heating is added to t_dt before the block's write and divided by the same new layer mass dpn the write produces. fv_update_phys injects cp_air·t_dt·dt·delp_new, so its energy is exact and independent of CP1's physics-heating scaling.
  - It uses qp·gq0 exactly as the write does, which is what FV2 makes round-trip exactly.
  - No overlap with R1 (ccpp).
  - It is called inside the existing OMP block loop and touches only its own block's columns.
- **One consequence for the meters:** EBX(4) and the "coupling heating vs physics" row will then include C1's heating. When 04 goes in, I will split that row into the physics part (must stay round-off) and the C1 part (to be compared with D2).

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

### Full-closure demo: `$E/all_full` (all switches on), 24 h, frame F (encpl), W m-2

**Construction.**
- Order: FV2, enpbl 04, D3A, D7, encnv 02-04, NM12, encpl 04, 05, 10r.
- encpl 06 conflicted textually with encnv in the SAMF argument lists, meta tails and the code just before ten_t. `rebase_encpl06.py` re-anchors those hunks verbatim (the arguments go after encnv's).
- Run namelist: dspheat_ke, samf_cmt_heat, gwd_ke_heat, thompson_kirchhoff, samf_kirchhoff and cpl_ke_heating set to T; cpl_water_energy and ngw_heat_opt as per column.

**Gates (release builds).**
- Default-off: all_full with only dspheat_ke = T is bitwise identical to all_v4k (atmf024, sfcf024). This includes NM12 (does not fire) and every new switch off.
- **c7n1 restart** (24 h vs 12 h + restart + 12 h) and **3×8 vs 4×6** (straight and restarted): 0 differing variables in atmf024, sfcf024, fv_core, fv_tracer, sfc_data, phy_data.
- Metered twins are passive (0 differ).
- Note: main reports that release builds can change round-off between trees, so −no-fma is needed for cross-tree bitwise claims. All of mine held bitwise in release anyway.

**Budget.** Totals from `tools/frameF_table.py` (EBD + EMS + encpl EBQ); twin `mallq_full`, jobs 10153235/329/345/432/457.

| term | c7, ngw 1 | c7, ngw 2 | c5, ngw 1 | c5, ngw 2 | c7n1 without S1 |
|---|---|---|---|---|---|
| **RESIDUAL** = ΔE_F − (rad + SH + water boundary enthalpy) | **+0.0836** | **+0.0836** | **−0.534** | **−0.532** | **−0.0383** |
| dycore fixer window | 2e-10 | 5e-10 | −2e-11 | −1e-10 | — |
| fv_sg heat (its KE is in the KE row) | +0.0042 | +0.0041 | +0.0042 | +0.0041 | +0.0042 |
| physics r_P, Σ schemes (physics frame) | +0.1061 | +0.1059 | +0.0988 | +0.0993 | −0.0155 |
| of which SAMF deep / shallow (S1) | +0.241 / −0.121 | +0.241 / −0.121 | +0.240 / −0.131 | +0.241 / −0.131 | ~0 / ~0 |
| of which Thompson (K1) | −0.0146 | −0.0146 | −0.0099 | −0.0100 | −0.0155 |
| radiation, PBL, GWD | ≤1e-12 | ≤1e-12 | ≤4e-10 | ≤8e-13 | ≤1e-12 |
| coupling: S_rem (Kirchhoff remainder) | −0.0200 | −0.0199 | −0.0110 | −0.0116 | −0.0203 |
| coupling: KE (write + update − physics) | −0.0228 | −0.0227 | −0.0224 | −0.0224 | −0.0225 |
| coupling: thermodynamic remainder (incl. D7 heat +0.016) | +0.0161 | +0.0161 | **−0.603** | **−0.601** | +0.0159 |

**Reading.**
- **c5 vs c7.** Without the flow-work bit the remainder is −0.60, which is the −0.62 FV3 net sink on vapour mass changes at fixed delz (fwred). Bit 2 restores it.
- **NGW options 1 and 2** differ by ≤5e-5 W m-2 in every row.
- **S1 attribution (c7n1 with vs without samf_kirchhoff).** S1 adds +0.122 W m-2 of residual. In the physics frame SAMF picks up deep +0.241 and shallow −0.121, but frame F's Kirchhoff term (S_rem, from the net layer water changes) does not move (−0.020 in both). So S1's heating is not the one frame F asks for. Without S1 the full demo leaves −0.038, made of:
  - Thompson K1 physics-frame −0.0155 and S_rem −0.020, which also do not cancel each other;
  - the water-mass KE −0.0025 (KE·dm of water written at layer winds), which no switch heats yet;
  - D7 + fv_sg + KE rows otherwise cancel to −0.0025.
- **For encpl:** reconcile S1/K1 with S_rem: either the meter's S term should use the gross condensate the schemes heat, or S1/K1 should apply L_F(T) to the net layer water change. Also add K·dm to C1.
- **Target** (residual at round-off) is **not yet met:** best case −0.038 W m-2 (c7, no S1), +0.084 with S1.

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

### 9.2 Why samf_kirchhoff added +0.122, and Thompson

Meter v2 on all_full, c7n2 (jobs 10153599/600). Frame-F gap per scheme, W m-2:

| scheme | S1 off | S1 on |
|---|---|---|
| SAMF deep | −0.161 | **+0.080** |
| SAMF shallow | +0.122 | +0.0028 |
| Thompson (K1) | +0.0082 | +0.0083 |
| PBL | −0.0051 | −0.0050 |

- **S1 is right in kind** (L_h(T) on the layer's net condensate ck = net rain production + detrained condensate), but **misses the ice phase**. The ice part of detrained condensate gets D3A's constant hfus plus S1's (cp_v − c_l)(T − T0), while frame F requires L_s(T) = hvap + hfus + (cp_v − c_i)(T − T0).
  - The excess is (c_i − c_l)(T − T0) per kg of detrained ice. For T < T0 that is a heating.
  - Check: D3A's −0.420 W m-2 means 1.26e-6 kg m-2 s-1 of detrained ice. At T0 − T ≈ 30 K, that gives 2213.5·30·1.26e-6 = **0.084**, the measured +0.080. Shallow: 5.4e-8·2213.5·20 = 0.0024, the measured +0.0028.
  - S1 also evaluates L at t1 (the SAMF-entry T) instead of the step-initial T the coupling books.
  - The meter is right and the switch is incomplete. Fix **S1K**: ice fusion at L_f(T_old), and T_old in both terms.
- **Thompson K1** keeps its own process-level formulation: temp(k) inside microphysics, moist-cp factor with an evolving r_v, and the vapour redistribution with no latent term. Its per-layer energy cannot equal Q_k exactly. Fix **TFH** (`thompson_frame_heat`): replace Thompson's heating per layer by Q_k, computed from its own net phase change. That phase change comes from the layer water budget with the exported liquid and ice sedimentation fluxes (vapour flux = remainder) at T_old. K1 then only affects microphysical rates.
- **PBL −0.005:** the condensate filler (vapour↔liquid at hvap), plus PBL cloud-water diffusion treated as vapour in S_cross. Open (measured after S1K/TFH).

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

### 9.4 Final integration: energy r4 + latent + trdyn v5 + ensfc2, everything on

**Trees.**
- `full9` = full6 (all_full + TH8 S1K TFH PBK C8 D7S PBF + latent 01a 01b 02 03) + trdyn 02b, 03b, 01_DYN v5 + ensfc2 04 05 06 08 09 10 11 (not 12). `mq9` is the metered twin.
- Built by `meters/tools/mk9.sh`. trdyn's three hunks that clash with energy edits (PBK/PBF declarations in satmedmfvdifq, the D7/D7S namelist line in fv_control, and in mq the meter-adjacent fv_dynamics use line and L2E call) are re-anchored verbatim by `patches/tools/rebase_trdyn.py`, updated for v5's `dry_negadj` import.
- v4 → v5 adds `dry_negadj` (chemistry tracers follow the dry air that neg_adj moves) and skips `type=diagnostic` tracers. It does not touch water or energy.
- **v5 → 04_INLQ + v6 (trdyn's final set):** `full10`/`mq10` (`meters/tools/mk10.sh`).
  - Both patches touch only sw_core.F90 beyond v5: v6's other hunks are byte-identical to v5's.
  - mk10.sh checks that full9's and mq9's sw_core = the 6-tree + v5, then installs the 6-tree + 04 + v6 (11 lines differ).
  - Check (`logs/final10.txt`, jobs 10155030/031, inline_q off): full10 vs full9 all-on and mq10 vs m9 have **0 of 18 / 0 of 194 variables differing** (atmf024 / sfcf024). Meters passive: 0 differ. The mq10 frame-F table is identical to m9's.
  - Every full9 number below holds for full10.

**Switches** (`runs/final9_switches.sed`):
- gfs_physics_nml: dspheat_ke, samf_cmt_heat, gwd_ke_heat, ngw_heat_opt = 2, thompson_kirchhoff, samf_kirchhoff, thompson_frame_heat, pbl_kirchhoff, noahmp_canopy_heat = 1, precip_phase_host, noahmp_sw_radshare, lw_sfc_consistent, sfc_evap_enthalpy, noahmp_heat_advect, noahmp_kirchhoff.
- fv_core_nml: cpl_ke_heating, cpl_ke_smooth = 32, cpl_water_energy = 15, dry_tracer_adv.

**Master budget, frame F, 24 h, W m-2** (m9, mq9 exe; `tools/frameF_seg.py`, `tools/frameF_table.py`):

| term | round 3 (all_full c7, S1 on) | round 4 (full7, no ensfc2) | **final (full9)** |
|---|---|---|---|
| ΔE_F | | | +5.1188 |
| F_F = rad + SH + water boundary enthalpy (+ PH1 hfus·csnow) | | | +4.9377 |
| declared: surface hand-off, segment 3 (ensfc2 LW1 + EV1) | — | — | **+0.18107** |
| declared: h2ophys S_chem = hvap·ΔWv | (in residual) | +1.4364e-5 | +1.4364e-5 |
| **RESIDUAL net of the declared terms** | **+0.0836** | −1e-11 | **−2.1e-12** |
| dycore fixer window | 2e-10 | −5.7e-10 | −4.7e-10 |
| frame-F gap: radiation | ≤1e-12 | 1.9e-12 | 1.2e-13 |
| frame-F gap: PBL | −0.0050 | −8.4e-13 | −2.1e-13 |
| frame-F gap: GWD | ≤1e-12 | −6.8e-13 | −6.5e-13 |
| frame-F gap: SAMF deep | +0.080 | +4.9e-14 | +1.7e-13 |
| frame-F gap: SAMF shallow | +0.0028 | +9.5e-15 | +1.0e-13 |
| frame-F gap: Thompson (+ MP post) | +0.0083 | +5.3e-13 | +1.7e-3 (PH1 hfus vs L_f(T1), see below) |
| water-mass KE·dm (C8) | −0.0025 unheated | closed | closed |
| A→D KE (D7/D7S) | closed (raw D7) | closed (D7S 2) | closed (D7S 32) |

The scheme-internal rows (r_P +0.199, S_rem −0.022, KE −0.023, R_thermo +0.024, fv_sg +0.004) are bookkeeping between frames. They sum to the residual and are in `logs/final9.txt`.

**PH1 (precip_phase_host) and D3A: no double count.**
- The meter (mq9, `EB_PH1=1`) books csnow = convective rain over tsfc < 273.15. It adds hfus·csnow to the boundary flux F, as asked, and books that water leaving at the surface as ice in the per-segment frame-F correction.
- **m9 (PH1 on):** SAMF deep/shallow gaps are 1.7e-13 / 1.0e-13, so D3A's fusion is on detrained cloud ice, not on rainc. PH1 shows up only in the MP/post segment, where GFS_MP_generic_post heats the lowest layer.
- **m9_noPH (PH1 off, same meter):** the total net residual is −0.07499 W m-2. That is exactly hfus·csnow, declared but not applied (csnow = 2.2e-7 kg m-2 s-1 globally). SAMF stays at −5e-14 / 3e-14. PH1 and D3A act on disjoint water and are each counted once.
- **Total budget:** PH1 is a declared surface→atmosphere flux hfus·csnow, with the convective water leaving as SAMF exported it. It closes to −2.1e-12.
- **The one frame-F subtlety (ensfc2, not fixed here).** If the water is instead taken to leave as snow at the lowest-layer step-initial T1 (the per-segment row), the frame-F latent heat is L_f(T1) = hfus + (c_l − c_i)(T1 − T0), not hfus.
  - PH1's constant hfus then over-heats by (c_l − c_i)(T0 − T1)·csnow = **+1.7e-3 W m-2** (mean T0 − T1 ≈ 3.4 K). That is the "Thompson (+ MP post)" row above.
  - A Kirchhoff PH1, `con_hfus + (c_l − c_i)*(tgrs(i,1) − T0)`, closes it. Whether to use it depends on how Noah-MP books the snow it receives (noahmp_kirchhoff), so it belongs with ensfc2 and is left to them.

**Surface hand-off (segment 3).** +0.18107 W m-2 with all seven ensfc2 options (+0.18199 with PH1 off). This is the LW1 + EV1 lowest-layer heating, booked as a declared boundary flux. It is larger than ensfc2's 0.1615, measured with a different option set.

**Gates, full9** (`logs/final9.txt`; jobs m9 10154773, m9_noPH 10154781, rs9 10154953/954, rsL9 10154961/962):
- Restart (24 h vs 12 + 12), 3×8 vs 4×6, and 4×6 restarted: 0 differing variables in atmf024, sfcf024, fv_core, fv_tracer, sfc_data and phy_data.
- Meters passive (mq9 vs full9): 0 differ.
- Default-off bitwise was not re-run on full9. The energy round-4 switches were checked on full5 (§9.3).

**24 h total change of the whole series** (full9 all-on vs ctl64; noise = ctl64 vs ctlc999):

| field | rms | mean | noise rms |
|---|---|---|---|
| T (K) | 0.293 | −0.013 | 0.149 |
| ps (Pa) | 22.8 | −0.02 | 8.41 |
| LH (W m-2) | 7.65 | **−1.87** | 3.24 |
| T_sfc (K) | 0.763 | +0.059 | — |
| precip (kg m-2 s-1) | 1.6e-5 | −8.5e-7 | — |

The series changes the forecast beyond noise, as round 4 already did (full5: 0.246 / 18.3 / LH −2.0). The systematic LH shift is the C1 bit-2 signal already measured on full5. The T_sfc mean +0.06 K is for the whole series and is not attributed to a switch.

### 9.5 Acceptance items: default-off gate, fixer size, TH8 separability

**Default-off gate on the final tree** (`meters/tools/mkgate10.sh`, `gate10.sh`; `logs/gate10.txt`). Both arms built -no-fma (ensfc2 `tools/nofma.py`).
- gA = full10 (every patch), every switch at its default (off).
- gB = fx (FX1 SG1 CP1) + the switchless bug fixes only: R1, TH8, FV2, D3A, NM12, latent 01a 02 03, trdyn 02b and 04_INLQ, ensfc2 04 SI1, 05 SI2, 06 NP1, 08 QR1, 09 CMC, 10 FL1. All 14 diffs apply at -F0 on fx.
- **gA_off (job 10155178) vs gB_off (10155202): 0 differing variables** in atmf000, atmf024, sfcf024, fv_core, fv_tracer, sfc_data and phy_data.
- So every other patch is bitwise when off. That covers enpbl 04, encnv 02-04, encpl 04/05/06, D7, S1K, TFH, PBK, C8, D7S, PBF, latent 01b, trdyn 03b/v6 and ensfc2 11.
- ensfc2 04-06 (SI1 SI2 NP1) and FV2 are switchless, so they are in the bug-fix arm.

**consv_te fixer, 24 h magnitude** (EBX "fixer intended" = consv·Σ(te0 − te); fv_mapz te_2d = te0 − te, so negative means the dycore gained TE):

| run | fixer correction, W m-2 | meaning |
|---|---|---|
| ctl64 (m3, its metered twin: 0 of 18 / 0 of 194 differ) | −0.5701 | the dycore creates +0.570 W m-2 of TE (remap, d_con, damping); the fixer removes it by a global uniform cooling |
| final all-on (m10) | −0.5635 | same, −1.2 % |

The dycore *gains* energy, it does not lose it. After FX1 the fixer removes exactly that amount (fixer window −4.7e-10). This is design D10.

**TH8 separability** (`accepted/23_energy_06_TH8_…diff`). TH8 reverse-applies at -F0 on full10 and mq10; no later patch depends on its text. m10_nth8 = mq10 − TH8, all-on, job 10155206:

| term | with TH8 (m10) | without TH8 |
|---|---|---|
| Thompson water dW − flux (kg m-2 s-1) | −2.6e-20 | **−7.1e-12** (the leak) |
| RESIDUAL net of declared, W m-2 | −2.1e-12 | **+2.37e-6** |
| every other scheme gap | ≤ 1e-12 | ≤ 6e-13 |
| fixer window | −4.7e-10 | +4.2e-10 |

- The only change is the leak. Its energy is not zero: +2.37e-6 W m-2 = 3.3e5 J kg-1 × 7.1e-12, i.e. hfus per kg. The dropped mass is frozen (rs/rg/ri below R1·rr_min). It vanishes without being booked as ice precipitation, which reads as a gain of hfus per kg.
- Dropping TH8 therefore leaves the total at +2.4e-6 W m-2, not round-off. Canopy's replacement should close both numbers.
- 24 h vs m10: T rms 0.171 K, ps 9.2 Pa, LH 4.1 W m-2 (noise 0.149 / 8.41 / 3.24). These global fields do **not** show TH8's land effect.
- **Canopy agent's measurement (not re-run here; `conservation/canopy/report.md`).** Same -no-fma exe, TH8 env-switched, final9 switches.
  - TH8 alone moves land canopy evaporation evcw −68 % at f06 and −47 % at f24, transpiration +17 % / +9 %, land LH −4.8 % / −1.8 %, and cnwat +34 % / +48 %. The noise is evcw −0.01 % / −0.3 %.
  - Cause: TH8 books the sub-R1·rr_min snow, Noah-MP turns it into trace canopy ice, and stock fwet then hides the canopy liquid (E.2).
  - With TH9 (thompson_sed_actual) or E.2 (noahmp_fwet_opt 1), TH8 is at noise. Closure is the same as here: TH8 off gives a 7.0e-12 leak and +2.3e-6 W m-2.
  - **So TH8 must not ship without TH9 or E.2.** It stays separable for that reason.
- The surface hand-off moves 0.1811 → 0.1577 between these two near-noise trajectories. Its ±0.02 spread covers ensfc2's 0.1615.

### 9.6 Final integration round: full11 = full10 + ensfc2 round 4 + canopy

**Tree** (`meters/tools/mk11.sh`, `mk11b.sh`; all exes -no-fma):
- full11 = full10 + ensfc2 13 SL2, 14 CS1, 15 CB1 (bug fixes), 16 options_r4, then canopy 01 E2, 03 TH9, 04 E1. Canopy 02 is TH8, byte-identical, already in.
- Clashes are re-anchored verbatim by `patches/tools/rebase_r11.py`, one stage per patch, each run right after its patch (patch overwrites `.rej`):
  - **13 hunk 8:** 13 was cut on fx. Its `hc1` declaration sits next to ensfc2 11's `svn, hcpo, hcpn`.
  - **E2:** 7 hunks next to ensfc2 16's new lines, since both were cut on full10. They cover the namelist, the Model% copy, the print, the noahmpdrv argument list, options call and meta tail, and the module_sf_noahmplsm option declarations.
  - **TH9 hunks 1-2:** mq only, next to the Thompson energy-meter lines.
- **Integrator fix to ensfc2 16 (report to ensfc2).** GFS_MP_generic_post.meta declares the new `[tgrs]` with `standard_name = air_temperature`, but that is `gt0`'s name in this table, so capgen aborts on the duplicate. PH1 wants the step-start T1, so it is now `physics_timestep_initial_air_temperature` (Statein%tgrs). No ensfc2 tree on disk contains this argument, so 16 had not been built as delivered.
- mq11 = the same + meter v2 probes regenerated with `EB_PBLFLX=1 EB_PH1=1 EB_LAG=1` (lag meter, below).

**All-on switches** (`runs/final11_switches.sed`): final9's set with LW2 for LW1 (lw_sfc_return = T, lw_sfc_consistent = F), plus:
- sfc_precip_enthalpy (EP1), noahmp_pore_air (AIR1);
- noahmp_fwet_opt = 2, thompson_sed_actual (TH9), nst_spray_opt = 1.

**Precipitation lag meter (EB_LAG).** The atmosphere books step N's precipitation leaving at T1(N), its step-start lowest-layer T. The surface (EP1) books it arriving at step N+1 with that step's T1.
- Probe 12 keeps, per column, P(N)'s heat capacity c_l·P_liq + c_i·P_ice (PH1 snow as ice) and T1(N).
- The next step adds that capacity × (T1(N+1) − T1(N)) × area, global and land-weighted (frland). This is line `EML`.
- A cell-area check guards the column mapping. Only step 1 is unmatched (55,296 columns, no previous step).
- `EML` also carries Σ csnow·(c_l − c_i)(T1 − T0). With `--ep1`, frameF_table books PH1's snow as ice at T1 in F_F, as EP1's surface does.

**Master budget, frame F, 24 h, W m-2** (m11, job 10156103):

| term | full9 (r4 final) | **full11** |
|---|---|---|
| ΔE_F | +5.1188 | +5.1385 |
| declared: surface hand-off, segment 3 | +0.18107 (LW1 + EV1) | **+0.11372** (LW2 replaces LW1's lowest-layer heating; EV1 now incl. glacier) |
| declared: h2ophys S_chem | +1.4364e-5 | +1.4364e-5 |
| declared: PH1 snow leaves as ice at T1 (EP1) | (hfus·csnow in F) | −1.7398e-3 |
| **RESIDUAL net of the declared terms** | −2.1e-12 | **−6.8e-13** |
| fixer window / fixer correction | −4.7e-10 / −0.5635 | +2.6e-10 / −0.5640 |
| frame-F gap: radiation, PBL, GWD | ≤ 7e-13 | ≤ 7e-13 |
| frame-F gap: SAMF deep / shallow | 1.7e-13 / 1.0e-13 | −4.3e-14 / 1.1e-13 |
| frame-F gap: Thompson + MP post | +1.7e-3 (PH1 hfus) | **+1.6e-12** (PH1 uses L_f(T1) under EP1) |
| Thompson water dW − flux (kg m-2 s-1) | −2.6e-20 | −1.5e-20 (TH8 + TH9) |
| **hand-off lag c_w P(N)(T1(N+1) − T1(N)), all surfaces** | not measured | **−1.20e-2** |
| of which land (frland-weighted) | | −2.4e-3 |

- **The PH1 convention gap is closed.** Under EP1, PH1 heats by L_f(T1) and the surface receives the snow as ice at T1. The atmosphere and the surface now use the same frame.
- **The lag is the one term not at round-off.**
  - It is not an atmosphere-budget error: the atmosphere's own budget closes at T1(N).
  - It is a hand-off mismatch of the coupled system. The sign means T1 falls, on average, in the step after precipitation, consistent with rain cooling the layer it falls through (not separately tested).
  - EP1 covers Noah-MP and sea ice. So the part that actually enters a surface budget is the land part (−2.4e-3) plus a sea-ice part I did not separate. The open-ocean remainder is outside EP1.
  - **To close it:** carry the precipitation's enthalpy as the atmosphere booked it, c_l·P_liq·T1(N) and (c_i·T1(N) − Li00)·P_ice, from GFS_MP_generic_post to the surface with tprcp/srflag. Or carry T1(N). It is one 2-D field per phase, and it must be in the restart (as tprcp is) to keep restart bitwise. The surface then books that number instead of c·P·T1(N+1).

**Gates, full11 (-no-fma)** (`logs/final11.txt`; rs11 10156116/117, rsL11 10156147/148, gA11_off 10156168, gB11_off 10156172):
- Restart, 3×8 vs 4×6, and 4×6 restarted: 0 differing variables in atmf024, sfcf024 and the four restart files.
- Meters passive (m11 vs rs11_S): 0 differ.
- **Default-off (gA11_off = full11, every switch off, vs gB11_off = fx + bug fixes incl. ensfc2 13-15): 0 differing** in atmf000, atmf024, sfcf024 and the four restart files.
- The bug-fix arm carries TH8 but not TH9. TH9 is switch-gated (thompson_sed_actual, default F), so it cannot change an off-gate. Neither canopy's 03 diff nor their `apply_th9.py` applies to fx: both are cut on encpl K1 / TFH Thompson text. If Ash makes TH9 unconditional, it needs a version cut on fx before it can go into the bug-fix arm.

**24 h impact, full11 all-on vs ctl64** (noise = ctl64 vs ctlc999):

| field | all-on | noise |
|---|---|---|
| T rms (K) / mean | 0.282 / −0.016 | 0.149 / −0.000 |
| ps rms (Pa) | 22.6 | 8.41 |
| LH rms / mean (W m-2) | 7.62 / −1.86 | 3.24 / −0.03 |
| T_sfc rms (K) | 0.705 | 0.281 |
| **land canopy evaporation evcw, 0-24 h (f24 bucket)** | **+35.7 % (+21.1 %)** | −0.03 % (−0.50 %) |
| land sublimation sbsno | −9.4 % (−4.9 %) | +0.05 % |
| **land LH** | +1.75 % (+1.21 %) | −0.04 % (−0.21 %) |
| land t2m (K) | −0.021 (−0.034) | −0.001 |
| land q2m | +0.52 % | 0.00 % |

Land statistic is canopy's `imp24.py` (land == 1, mean of the four 6 h buckets). For comparison, full9 all-on (TH8 without TH9 or E.2) gave evcw −63 % and land LH −2.2 %. The full11 land change is beyond noise in the other direction; its attribution is in §9.7.

### 9.7 full12 = full11 + fv3tally dyn_te_exact (v2): final tree

**Patch.** `accepted/31_fv3tally_01_fv3-dyn_te_exact_v2.diff` = `$U/cons/fv3tally/patches/01_fv3-dyn_te_exact.v2.diff`, -p1 -F0 clean on full11.
- **Flag:** `01_fv3-dyn_te_exact.diff` is *not* identical to `.v2.diff`. It is 217 content lines different and 31 min older. I used `.v2`.
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
