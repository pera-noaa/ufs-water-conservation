# Proposal: closing the energy and passive-tracer budgets in UFS

*Draft for the FV3 `dev/emc` maintainers, the CCPP physics maintainers and the owners of SAMF, satmedmfvdifq, UGWP-v1
and GSL drag, Thompson, Noah-MP, NSST, the CICE sea-ice scheme, MYNN-EDMF, GFDL microphysics v3 and Grell–Freitas,
and the MPAS-A developers. Follow-on to `water_closure_proposal.md`. Ash Pera (NOAA GML / CIRES) with Lori Bruhwiler, 18 October 2026.
Not yet posted. Submission is by owner, in rounds: the unconditional bug fixes in `pr_round1.md`, the bugs that need
an owner's decision in `round2_issues.md`; the physics changes and options come later. The diffs, their apply order and target
repositories are in `conservation_patches.md`. Every number is from a report under `conservation/`, named under each
table.*

## Summary

**The problem.** With the water fixes in place (diffs 01–19 + 09b of the water proposal), a 24-h C96 forecast with
`FV3_GFS_v17_p8_ugwpv1` still does not conserve total energy or keep passive tracers consistent:
- the atmosphere's 24-h energy budget leaves **+2.08 W/m²** unexplained (frame E_D, base tree);
- FV3's `consv_te` fixer removes **0.570 W/m²** that the dynamical core creates;
- on `develop`, SAMF deep convection destroys **2 % per day** of a convectively transported generic tracer (fixed by
  water diff 01, SA1);
- a tracer that starts uniform in dry mixing ratio develops structure of **0.4 ppm rms, 5 ppm max** (CO2-equivalent
  at 400 ppm) in 24 h;
- SAMF's booked wet deposition misses **7.4 × 10⁻⁴** of a scavenged tracer's mass per day (fscav 0.5; shallow
  convection under-books by 1.5 %), and the deposition is never exported.

**What we propose.** Each defect is explained in the code, closed by an in-model meter and red-teamed. Each fix is a
bug fix, a physics change or a numerical-consistency change (Method). Every switch is bitwise inert when off. The
diffs touch the FV3 dycore and its UFS driver, ccpp-physics (SAMF, satmedmfvdifq, UGWP-v1/GSL drag, Thompson,
Noah-MP, NSST, sea ice, MYNN-EDMF, GFDL MP v3, Grell–Freitas, the interstitials), the UFSATM data and build files,
NOAA-EMC/noahmp, and MPAS-A.

**The result** (C96, 24 h, dt 720 s, every switch on, final tree `full13`; section 12):

| Quantity (unit) | Before | After | Source |
|---|---|---|---|
| Total energy, 24-h residual net of declared boundary and source terms (W/m²) | +2.08 (frame E_D, base) | **+1.6 × 10⁻¹²** (frame F) | energy §1, §9.8 |
| Largest single scheme gap (W/m²) | +1.43 (PBL) | ≤ 1.2 × 10⁻¹² | energy §1, §9.8 |
| FV3 `consv_te` fixer correction, the dycore energy it removes (W/m²) | −0.570 | **−0.304** (`dyn_te_exact` = 31) | energy §9.5, §9.8 |
| Passive-tracer mass, 24 h (fraction of initial mass) | `develop`: −2.1 × 10⁻² (generic convected tracer); water set: +3.2 × 10⁻¹⁵ | **~3 × 10⁻¹⁵/day**; 2 × 10⁻¹⁶ with FV2; every term below one ulp per step | tracer, trsamf, latent §4 |
| Tracer + SAMF wet deposition, fscav 0.5 (fraction of initial mass) | −7.4 × 10⁻⁴ | +3.0 × 10⁻¹⁵ (2.4 × 10⁻¹⁶ with FV2) | latent §1, §4 |
| Uniform dry tracer, 24-h deviation, rms / max (dry mixing ratio, relative) | 1.07 × 10⁻³ / 1.22 × 10⁻² | 3.7 × 10⁻¹⁴ / **4.9 × 10⁻¹³** | trunif, trdyn |
| Precipitation enthalpy hand-off to the surfaces (W/m²) | −1.21 × 10⁻² | 0 (exact) | preclag |
| Noah-MP soil / glacier / sea-ice energy, own frame (W/m²) | +10.71 (+10.20 of it aquifer exchange, later booked as a boundary term) / +0.0071 / −0.0079 | 4.3 × 10⁻⁸ (3.6 × 10⁻⁸ of it the step-1 initial state) / 6 × 10⁻¹⁶ / −1.1 × 10⁻¹³ after booking the declared items | ensfc §2, ensfc2 |
| MYNN, GF, GFDL MP v3, satmedmfvdifq water, own suites (kg/m²/day) | +4.5 × 10⁻², −1.4 × 10⁻¹, −8.4 × 10⁻³, +2.6 × 10⁻⁸ | −5.5 × 10⁻¹⁵, +2.5 × 10⁻¹⁶, −9.3 × 10⁻¹⁶, −3.6 × 10⁻¹⁶ | suites |
| MPAS-A supercell, 24 h, energy ΔE/E (with the opt-in layer coupling and the labelled fixer) | −4.3 × 10⁻⁴ | +1.9 × 10⁻¹⁶ | mpas §9 |

The final tree is `full14`: `full13` with TH9 unconditional, PL1 folded into `sfc_precip_enthalpy` and NM10r adopted.
All-on, it is bitwise identical to `full13`, so every all-on number above holds for it. Its gates (restart, 3×8 vs 4×6,
meters passive, switches off vs `fx` + bug fixes) are bitwise.

**Gates** (final tree, both arms built with `-no-fma`; energy §9.8):

| Gate | Result |
|---|---|
| Restart: 24 h straight vs 12 h + restart + 12 h, every switch on | bitwise (atmf024, sfcf024, fv_core, fv_tracer, sfc_data, phy_data) |
| Layout 3×8 vs 4×6, straight and restarted | bitwise |
| Meters passive (metered vs plain tree) | bitwise |
| Every switch off vs fx + the unconditional bug fixes only | bitwise (atmf000/006/024, sfcf006/024, 4 restart files) |
| Each gate can fail | known-bad cases differ (fv3tally 15 of 18 variables; canopy 1715/2374; MPAS heating on vs off) |

**Impact.** One at a time, the unconditional bug fixes are at noise (a 0.1 % perturbation of the `consv_te` fixer;
Method), except where the area tables say otherwise. With every switch on, the forecast changes beyond noise: T rms
0.282 K, ps 22.6 Pa, LH rms 7.46 W/m² and mean −1.89 W/m² (the flow-work bit of `cpl_water_energy`), land canopy
evaporation +35.6 % and land latent heat +1.73 % (`noahmp_fwet_opt` = 2). The decided settings are in section 15.

**Why it matters to us.** NOAA's UFS-Chem reanalysis group plans multi-decade runs with prognostic CO2, CH4 and SF6.
A uniform tracer must stay uniform, and a tracer's mass must change only by its sources, sinks and deposition. The
energy budget must close for the model's temperature and precipitation drift to be attributable. CAM heats the
kinetic energy its momentum transport removes (Boville and Bretherton 2003); this proposal does the same for UFS, and
books the enthalpy of water crossing the surface in FV3's own energy.

## Method

**Case.** `control_p8_ugwpv1`, 2021-03-22 06Z, C96L127, dt 720 s, layout 3×8, 24 h. Base tree `develop` @112b1d46 +
water diffs 01–19 + 09b (`$U/p20rt_final`), built with a 64-bit dycore. Every fix applies on `fx` = base + FX1 SG1 CP1
(the first three energy fixes, no meters). Other suites run in their own RT cases (section 10); MPAS-A runs a
supercell (section 11).

**Energy: frame F.** The model's energy is FV3's own total energy plus the latent terms that make phase changes
conserve it with FV3's heat capacities (energy §9.1; encpl):

E_F = Σ δp/g · [c_vm·T + φ + K] + L_v00·W_v − L_i00·W_i, with L_v00 = h_vap − (c_pv − c_l)·T0, L_i00 = h_fus − (c_l − c_i)·T0, T0 = 273.15 K.

- c_vm is FV3's moist heat capacity (MOIST_CAPPA, USE_COND). Then e_v − e_l = L_e(T), h_v − h_l = L_h(T) and
  e_l − e_i = L_f(T), the Kirchhoff latent heats.
- Water crosses the surface at the lowest layer's temperature T1 and at φ_s: evaporation brings h_v(T1) + φ_s,
  precipitation takes h_w(T1) + φ_s.
- The GFS schemes keep their own bookkeeping (E_P: c_p·T + h_vap·q_v − h_fus·q_ice + K, constant latent heats,
  condensate without heat capacity). E_P is kept as a scheme-internal check; closing E_P does not close E_F.
- The budget: ΔE_F = radiation + sensible heat + water boundary enthalpy + declared terms + round-off. The declared
  terms are in section 13.
- The coupling is framed as in Lauritzen et al. (2018, 2022) and Lauritzen and Williamson (2019): dry-mass
  coordinate, condensate loading, and thermodynamics that differ between the parameterizations and the host.
  Lauritzen et al. (2022, §4.5.2) cover FV3's c_p/c_v rescaling of physics heating but not the R_v·T term of
  section 1 (fwred), so they neither support nor contradict it.
- The dissipative heating of momentum transport follows the interface form of Boville and Bretherton (2003), as in
  CAM.

**Meters.** Instrumentation only, in separate diffs, never part of a fix (`conservation_patches.md`, part C).
- Dycore and coupling: 12 global quantities (c_vm·T, PE, D-grid and A-grid KE, ½w², water species, mass) at 10
  probes per step, plus the fixer's intended correction (energy §2). The FV3 tally adds per-term probes inside
  `fv_dynamics`, `dyn_core`, `d_sw` and `fv_mapz` (fv3tally).
- Physics: 12 probe schemes in the suite. Each stores, per column, the effective state (state + dt × pending
  process-split tendency), E_P, the frame-F correction and total water. Fluxes are captured where they are valid
  (radiation after `dcyc2t3`, PBL after `GFS_PBL_generic_post`, precipitation after `GFS_MP_generic_post`). Per
  segment: gap = r_F − S_cross, the scheme's frame-F inconsistency that is not the coupling's job (energy §9.1).
- Surfaces: Noah-MP soil, glacier, sea ice and NSST heat content in each component's own frame, and every hand-off
  flux against what the atmosphere books (ensfc §1; ensfc2).
- Tracers: double-precision Neumaier (hi, lo) sums of q·δp·area per tracer, gathered and added on the root in rank
  order, so they are deterministic and resolve about 10⁻¹⁸ of the mass (tracer). The suite meters also add per-rank
  sums in rank order (suites §2); MPAS uses fixed-point reproducing sums (mpas §5).
- **Shadow tracers** (trunif): four extra tracers reset to exact uniformity before every process, plus one tagged
  tracer per generator that carries only that generator's increments. A run with them is bitwise identical to the run
  without them in every 17-digit mass line.

**Labels** follow `conservation/TRACKER.md` and `conservation/replay/SERIES.md`.
- **DY1–DY3** are the FV3 dycore defects the tally found (the fv3tally report's D1–D3).
- **D1–D12** are the energy report's design items: D1 PBL dissipative heating (`dspheat_ke`), D2 the coupling's
  water-mass write (fixed by C1), D3a/D3b SAMF, D4/D4n/D12 gravity-wave drag, D7 the A→D wind mapping.
- **R1** is the radiation fix. Thompson's placeholder is written "the R1 placeholder value (10⁻¹²)".
- **PBL05** and **SAMF08** are suites 05 and 08.

**Classification.** Each change is in one class:
- **BUG FIX**: restores what the code intends. Unconditional, unless it changes the forecast beyond noise and an owner
  must judge it (then switched, and listed in section 15).
- **PHYSICS CHANGE**: adds a missing physical term or changes a design choice. Always behind a switch, default off,
  with its forecast impact measured. The reports' "PHYSICS CORRECTION" (C1 bit 2), "NUMERICAL STABILITY" (E1) and
  "DESIGN option" (`dyn_te_exact` bits 32, 64) are in this class.
- **NUMERICAL CONSISTENCY**: makes two parts of the code agree on a quantity they share (a density, a heat capacity,
  a layer mass). Unconditional when it is at noise, switched otherwise.

**Switches.** Every new switch defaults to the stock behaviour. The whole set off is bitwise identical to `fx` + the
unconditional bug fixes (energy §9.5–§9.8). The all-on switch set is in energy §9.4, §9.6 and §9.8.

**Noise control.** A change is "at noise" when its 24-h difference from the unfixed run is within the difference
made by `consv_te` = 0.999 instead of 1 (run `ctlc999`): T rms 0.149 K, ps 8.41 Pa, LH 3.24 W/m². Convection and
microphysics thresholds amplify any last-bit change into K-scale local differences within one step (energy §5), so
pointwise differences are compared with this control, not with zero.

**`-no-fma`** (samfinit). Metered and unmetered builds diverged from step 1, first seen in SAMF deep. Debug builds
(`-check all -init=snan,arrays -ftrapuv -fpe0`) trapped nothing, and with `-no-fma` the two trees are bitwise
identical at every probe. The cause is the release flags (`-O3 -fp-model precise -march=core-avx2`): ifort contracts
multiply-adds, and adding any statement to a physics file changes which ones it fuses. A flux then moves by about
1 ulp, the PBL is the first scheme to read it (probe 5), and SAMF's triggers make it visible. There is no
uninitialised read. **The final-tree gates (switch off, meter passive, restart, layout) compare `-no-fma` builds**
(`samfinit/tools/nofma.py` patches `cmake/IntelMixed.cmake`). Comparisons within one executable (namelist or
environment switches) need neither; any other comparison of two executables is judged against the noise control.

## 1. FV3 dynamical core and its coupling to the physics

| Fix | Where | What goes wrong | Before → after (W/m², 24 h, unless stated) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| FX1 | `fv_mapz.F90` (`Lagrangian_to_Eulerian`) | the `consv_te` fixer converts its global deficit to a T increment with weight c_v,air·Σpkz·δp but applies it at c_vm: it delivers the intended energy × the mass-weighted c_vm/(c_v,air(1+r_vir q_v)(1−q_c)) | fixer window −5.5 × 10⁻⁴ → −3.6 × 10⁻¹⁰ | BUG FIX | — | same step-1 pattern and 24-h statistics as `ctlc999` (T rms 0.148 vs 0.149 K) |
| SG1 | `fv_sg.F90` (`fv_subgrid_z`, non-hydrostatic, nwat = 6) | the 2Δz filter mixes total energy conservatively, then relaxes T, u, v, w, q separately: KE is quadratic, so the relaxed state loses fra(1−fra)δ²/2 | −1.58 × 10⁻⁴ → +3.0 × 10⁻¹¹ | BUG FIX | — | sponge only (levels 0–46); step-1 max 9.6 × 10⁻³ K |
| CP1 | `atmosphere.F90` (`atmosphere_state_update`) | the physics heats its own layer mass (dry air + vapour); `fv_update_phys` applies the same tendency to the new total δp, so each joule arrives × δp_new/m_p | coupling heating −8.63 × 10⁻³ → +3.9 × 10⁻¹⁰ | BUG FIX | — | step 1: cloudy layers only, max 0.043 K; f24 T rms 0.159 K |
| FV2 | `atmosphere.F90` (`atmos_phys_driver_statein`) | tracers are divided by `prsl` into the physics and multiplied by `prsi(k) − prsi(k+1)` on the way back; the running sum drops corrections below half an ulp of 10⁵ Pa, always the same sign | tracer conversion +3.07 × 10⁻¹⁵ → +5.2 × 10⁻¹⁷ per day (24-h totals 14× smaller); energy-neutral | BUG FIX | — | T rms 0.148 K vs 0.155 for a 10⁻⁷ T perturbation |
| DY1 | `dyn_core.F90` (non-hydrostatic heat block) | `d_con` heat is added as `dtmp/pkz` to the density potential temperature at fixed δz, with 1/c_v,air: the realised ΔT is dtmp/(1−κ), c_p/c_v times the KE it returns | +0.2905 → 0 | BUG FIX | `dyn_te_exact` bit 1 (0) | bits 31 together: T 0.153 K, ps 7.87 Pa, LH 3.20 (noise); −0.017 K above 1 hPa |
| DY2 | `sw_core.F90` (`d_sw`) | the KE estimate is taken about the half-damped wind (after divergence damping, before vorticity damping) | −0.0195 → exact | BUG FIX | bit 16 | in bits 31 |
| DY3 | `fv_dynamics.F90` (`Rayleigh_Super`) | heats the A-grid KE at c_v,air while TE loses the D-grid KE; the stale pkz then multiplies the heat by c_p/c_v | +6.42 × 10⁻⁴ → 1.5 × 10⁻¹³ | BUG FIX | bit 8 | in bits 31 |
| bits 2, 4 | `sw_core.F90` | sponge-layer w-damping heat returned in J/kg where δp·J/kg is expected; w-damping heat about the pre-advection w | 10⁻¹², 6 × 10⁻⁹ → exact | BUG FIX (immaterial in p8) | bits 2, 4 | in bits 31 |
| bits 32, 64 | `dyn_core.F90`, `fv_mapz.F90` | sponge layers k = 1, 2 are damped with no heat; the vertical remap's TE change is not returned | −1.69 × 10⁻³ → −4.2 × 10⁻⁵; −0.1144 → −3 × 10⁻¹⁰ | PHYSICS CHANGE (design options) | bits 32, 64 | fixer −0.417 with 127, vs −0.304 with 31 |
| INLQ | `sw_core.F90` (`d_sw`, `inline_q`) | the del-n damping of tracers is weighted by the post-update δp on a PE's own cells and the pre-update δp in its halo, so two PEs add different fluxes on the same face | with `inline_q`: tracer mass 1.0–1.9 × 10⁻⁹ → 5.9–8.4 × 10⁻¹⁵ per day; dry air −8.6 × 10⁻¹² → 5.1 × 10⁻¹⁷ | BUG FIX | — (acts only with `inline_q`) | `inline_q` off: bitwise; no RT uses `inline_q` |
| D7 | `atmosphere.F90`, `fv_arrays.F90`, `fv_control.F90` | the A-grid → D-grid mapping of wind increments changes KE by a different amount than the physics did | KE row −0.0202 + D7 heat +0.0161 + `fv_sg` heat +0.0041 = −1.0 × 10⁻¹⁰ | NUMERICAL CONSISTENCY | `cpl_ke_heating` (.false.) | per cell: max 0.87 K/step; f24 T 0.167 K. Not recommended without D7S |
| D7S | same | D7's heating smoothed by a flux-form (exactly conservative) 5-point filter | peak 0.871 → 0.0131 K/step (32 passes), mean unchanged | NUMERICAL CONSISTENCY | `cpl_ke_smooth` (0; use 32) | 0.152 K / 7.97 Pa / 3.19 (noise) |
| C1 bit 1 | `atmosphere.F90`, `fv_arrays.F90`, `fv_control.F90` | water potential energy: precipitation is removed at the height it formed, so the frictional heating of falling water (Pauluis et al. 2000) is lost | net PE −0.480 (gross +1.47, lifted vapour −0.99) → applied | PHYSICS CHANGE (missing term) | `cpl_water_energy` bit 1 (0) | +0.02 K, precipitation +0.8 % |
| C1 bit 2 | same | **flow work**: FV3 applies the physics' isobaric latent heat h_vap at fixed δz, so every vapour mass change is booked with ±R_v·T too much (+R_v·T where vapour condenses aloft, −R_v·T where it enters the PBL) | net −0.620 → 0 | PHYSICS CHANGE (coupling convention) | bit 2 | −0.06 K mid / +0.05 K low troposphere; LH −1.97 W/m² |
| C1 bit 4 | same | sensible enthalpy of water moving between layers and across the surface | +1.773 → applied | PHYSICS CHANGE (missing term) | bit 4 | −0.04 K, LH −0.31, precipitation −1.3 % |
| C8 | `atmosphere.F90` | the KE of water mass written at the layer winds | −0.0025 → 0 | PHYSICS CHANGE | bit 8 | 0.145 K / 7.70 Pa / 3.06 (noise) |
| S1 export (encpl 06) | SAMF, Thompson, `atmosphere.F90` | bits 1 and 4 need each scheme's precipitation flux by species; S1 (section 4) | — (enables the terms above) | PHYSICS CHANGE | acts under bits 1, 4 and `samf_kirchhoff` | — |

C1 with bits 1 + 2 + 4 closes the coupling's thermodynamic term to −1.4 × 10⁻¹² W/m² and moves LH by −2.04 W/m² and
precipitation by −3.4 % (encpl). The `consv_te` fixer moves by only 0.006 W/m² between bits 0 and 7.

**Flow work.** Derived by encpl and confirmed independently by fwred in a 1-D compressible column with acoustic
relaxation (energy drift 0.6 J/m²): 1 g/kg condensed at 747 hPa warms the isobaric truth by 2.474 K, the fixed-volume
path with L_e by 2.471 K, and FV3's path by 2.596 K, an excess of 1.257 × 10⁵ J/kg (R_v·T0 = 1.261 × 10⁵). The
R_v·T is work the overlying column does on the layer as its gas shrinks. FV3 never shrinks δz at the write, so the
dynamics releases that work a second time. `phys_hydrostatic = .true.` has the same excess; the hydrostatic dycore
does not. GFDL MP's non-hydrostatic latent heat has a constant +R_v·T_ice (1.26 × 10⁵ J/kg) offset. MPAS's stock
coupling is consistent (mpas §2).

**Where FV3's +0.57 W/m² comes from** (fv3tally; control, 24 h):

| Term | Control (W/m²) | Class |
|---|---|---|
| `d_con` heat returned at c_p/c_v × the KE it estimates | +0.2905 | DEFECT (DY1), bit 1 |
| KE estimate below the KE removed | −0.0195 | DEFECT (DY2), bit 16 |
| Rayleigh net | +6.42 × 10⁻⁴ | DEFECT (DY3), bit 8 |
| adiabatic dynamics + tracer transport, net of damping | +0.4145 | OPEN (spatial discretization; section 13) |
| vertical remap (PE −0.064, KE −0.052) | −0.1143 | DESIGN (bit 64 option) |
| sponge damping not heated | −0.0017 | DESIGN (bit 32 option) |
| **sum = −fixer** | **+0.5701** | |

The red team (dycred) confirmed DY1–DY3 without the meter, from FV3's own `ENG Deficit` print: unfixed/bit-1 applied
heat = 1.4007 at every step, the 24-h DY1 term +0.2911, DY2's algebra exact to 5 × 10⁻¹¹, and DY3 +4.9 to +8.2 × 10⁻⁴
per step. The same heat block is in GFDL `origin/main` 8b94b9f. The FV3 technical description (Harris et al. 2021)
intends ΔT = ΔK/c_v and treats p^κ as fixed, which at fixed δz is wrong (dycred). Version 2 of the fix:
- takes the heat capacity from `moist_cv`, so hail (nwat = 7) and the nwat = 2 convention are FV3's own;
- takes the condensate from the advected `q_con`;
- covers the non-MOIST_CAPPA branch;
- stops with FATAL where a bit cannot act: bits 1, 8, 64 with MULTI_GASES; bit 64 without MOIST_CAPPA, hydrostatic
  or `kord_tm` ≥ 0.

In p8, v2 is at noise against v1.

Sources: energy §3, §6, §8, §9.3, §9.7; fv3tally; dycred; encpl; fwred; tracer (FV2); trdyn round 4 (INLQ).

## 2. Radiation

| Fix | Where | What goes wrong | Before → after (W/m², 24 h) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| R1 | `dcyc2t3.f/.meta`, `GFS_typedefs.F90/.meta` | RRTMG's hourly heating rates are per the radiation-time layer mass; `dcyc2t3` applies the same K/s for the next 4 steps while δp changes | −7.65 × 10⁻³ (Σ\|r\| 2.70 × 10⁻²) → −8.4 × 10⁻¹⁴ | BUG FIX | — | step-1 factor exactly 1; f24 T rms 0.149 K, ps 8.07 Pa vs fx1 (noise 0.149 / 8.41) |

The fix stores the layer pressure thickness at the last SW and LW call (two new `Radtend` fields, `dpsw`, `dplw`) and
scales the heating by δp_rad/δp_now, including the LW-Jacobian branch and the `dtend` diagnostics. The fields need no
restart entry: radiation runs on the first step after a restart, which refreshes them. The SCM and MPAS hosts carry
their own `GFS_typedefs` and need the same two fields (not tested). Source: energy §6.

## 3. Boundary layer

| Fix | Where | What goes wrong | Before → after (W/m², 24 h, unless stated) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| D1 `dspheat_ke` | `satmedmfvdifq.F/.meta`, `GFS_typedefs` | the dissipative heating is the TKE dissipation of the last of 20 substeps (3.677 W/m²), not the KE the momentum solve removes (2.248): TKE floors +0.862, shear production from the old winds +0.546, TKE gained outside the scheme +0.125, buoyancy −0.060, last substep −0.044 | PBL +1.4273 → +1.6 × 10⁻¹² | PHYSICS CHANGE | `dspheat_ke` (.false.) | land PBL −0.08 to −0.15 K; land T2m −0.073 K (day), −0.038 K (night); ocean SH −0.72 W/m²; T2m rms 0.334 vs 0.156 |
| PBK | `satmedmfvdifq.F/.meta`, `GFS_typedefs` | the condensate filler (vapour ↔ cloud water) at constant h_vap, not L_h(T) | +4.8 × 10⁻⁵ → 0 | PHYSICS CHANGE | `pbl_kirchhoff` (.false.) | 0.151 K / 7.98 Pa / 3.24 (noise) |
| PBF | `satmedmfvdifq.F/.meta`, `GFS_typedefs`, `atmosphere.F90` | PBL condensate transport is treated as vapour in C1 bit 4 | PBL gap −0.00485 → 8 × 10⁻¹³ | PHYSICS CHANGE | acts under `cpl_water_energy` bit 4 with `pbl_kirchhoff` | in the all-on set |
| PBL05 | `satmedmfvdifq.F` | surface sources applied with dt/(z_i2 − z_i1) while the fluxes were made kinematic with ρ_a: applied/reported − 1 = the non-hydrostatic δz deviation | GFDL v16 suite water +2.6 × 10⁻⁸ → −3.6 × 10⁻¹⁶ kg/m²/day; in p8 zero by construction | NUMERICAL CONSISTENCY | — | at noise; in p8 a last-bit change (f24 T 0.146 K) |

`dspheat_ke` uses the Boville–Bretherton (2003) interface form. The momentum moved across each interface, T_k, times
the time-centred shear there, heats the two adjacent layers; the surface stress work heats layer 1. Summation by parts
makes the column heating equal the column KE loss exactly. Layers with negative heating total −0.0017 W/m² (0.08 % of
the dissipation); the round-1 per-layer form had −0.62 and was dropped. The heating moves from the upper PBL into
layer 1: land loses 74 % of its dissipative heating, ocean 22 %. Closure needs `dspfac` = 1; otherwise the residual is
exactly (dspfac − 1) × the dissipation. With the time-split PBL (`tend_opt_pbl` 1 or 3, section 8) the stock PBL term
is +2.41 W/m² instead of +1.43 (latent); in the integrated tree energy reports the PBL gap ≤ 10⁻¹² W/m² for those
options (energy patch table).

**PBL05 in p8.** The host builds `prsl` from the same gas law and δz that satmedmfvdifq uses for ρ_a, and nothing
modifies T or q_v before the PBL, so ρ_a·Δz₁·g/δp ≡ 1 and the old and new expressions differ only in rounding. The PBL
water meter reads 1.0 × 10⁻²⁰ kg/m²/s, 3 × 10⁻¹⁶ of evaporation, so it is not blind to the term. The suite where
suites measured 2.6 × 10⁻⁸ differs by `do_sat_adj` = T and `lsm_noah`; which exception to the identity fires there is
not identified (energy §9.8).

Sources: enpbl; energy §9.3, §9.8; suites §10.3.

## 4. Convection (SAMF), with the gravity-wave-drag heating that shares its switches

| Fix | Where | What goes wrong | Before → after (W/m², 24 h, unless stated) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| D3A | `samfdeepcnv.f/.meta`, `samfshalcnv.f/.meta` | detrained condensate is split into ice by a T ramp (263 → 233 K) with no heat of fusion: the scheme's energy is liquid-referenced | deep −0.4195 → −8 × 10⁻¹⁴, shallow −0.0179 → −2 × 10⁻¹⁴ | BUG FIX | — | +0.016 K at 500–200 hPa (noise −1 × 10⁻⁵); 91 % of the heat at 500–200 hPa, max 4.4 K/day |
| D3B | same + `GFS_typedefs` | convective momentum transport conserves momentum, not KE: KE removed with no heating | deep −0.1191 → +2 × 10⁻¹³, shallow −0.0289 → +7 × 10⁻¹⁴ | PHYSICS CHANGE | `samf_cmt_heat` (.false.) | +0.002 K at 500–200 hPa (noise); max 10 K/day |
| D4 + D12 | `ugwpv1_gsldrag.F90/.meta`, `GFS_GWD_generic_post.F90/.meta`, `GFS_typedefs` | GSL drag removes KE with no heating (`gsd_diss_ht_opt` is a local `.false.`, and when on it heats only the ls + bl part, clipped at 0); the PBL × GWD cross term of the joint process-split update is heated by neither | GSL −0.3198 → 0; cross term −0.0663 → 0 | PHYSICS CHANGE | `gwd_ke_heat` (.false.) | +0.0075 K at 1100–500 hPa; local max 100–210 K/day near the lid (mesospheric drag) |
| D4n | `ugwpv1_gsldrag.F90/.meta`, `GFS_typedefs` | UGWP-v1 NGW heating (+0.365 W/m²) is parameterised from a prescribed launch flux, not taken from the resolved flow: net source +0.335 | +0.335 → 0 (option 1 or 2) | PHYSICS CHANGE | `ngw_heat_opt` (0; 1 = −ΔKE only, 2 = remove the column's net input at the launch layer) | option 1: −0.125 K above 1 hPa; option 2: −0.009 K at 500–200 hPa |
| S1 | encpl 06 (SAMF part) | SAMF heats condensation at constant h_vap; frame F needs L_h(T) | SAMF Kirchhoff remainder deep −0.245, shallow +0.128 | PHYSICS CHANGE | `samf_kirchhoff` (.false.) | rms at noise; mean LH +0.16 to +0.22 W/m², precipitation +0.6 % |
| S1K | `samfdeepcnv.f/.meta`, `samfshalcnv.f/.meta` | S1 misses the ice phase (detrained ice needs L_s(T)) and evaluates L at the SAMF-entry T instead of the step-initial T the coupling books | frame-F gap deep +0.080 → 1 × 10⁻¹³, shallow +0.0028 → −6 × 10⁻¹⁵ | PHYSICS CHANGE | `samf_kirchhoff` | in S1 |
| SA1 (tracers) | water diff 01 | the cloud-base correction subtracts a flux-limited value, not what the updraft took | `develop`: generic tracer −2.02 × 10⁻²/day, PBL-mixed GHG-like +1.39 × 10⁻⁵/day → ≤ 1.3 × 10⁻¹⁸ (fraction of mass) | BUG FIX | — (already proposed) | — |
| T1 (02b) | `samfdeepcnv.f`, `samfshalcnv.f` | the explicit TVD tracer update runs at Courant numbers up to 5; a non-PBL-mixed tracer piles up 100–200× in the lowest layers in 24 h | sub-stepped to donor Courant ≤ 0.5: removes the o3 one-step increment error (19 % median at Courant > 2) and TKE < 0 (13 % → 1.6 % of those columns); mass 3 × 10⁻¹⁵ | BUG FIX | — | changes o3 and TKE: zonal T ≤ 6 mK; 9–13 of 72 cells outside a 4-member spread (3.6 expected); o3 global mean −1.2 × 10⁻⁶ |
| DRY (03b) | `samfdeepcnv.f`, `samfshalcnv.f`, `satmedmfvdifq.F/.meta` | chemistry tracers are moved with moist-air fluxes while the write-back keeps each layer's dry mass, so the dry air "moves" where vapour went | uniform dry tracer, 24 h rms 1.07 × 10⁻³ → 2.3 × 10⁻⁵ (the rest is FV3, section 7); per step uniform to 2 × 10⁻¹⁴ | PHYSICS CHANGE (chemistry tracers only) | none: acts only on `chemistry` tracers with `trans_aero` | T, q bit-identical |
| F3 (01a) | `samfdeepcnv.f`, `samfshalcnv.f` | wet deposition booked with η(k−1), loss uses η(k); the borrowing branch zeroes `wet_dep` before adding it back, so deposition is erased and the tracer left negative | tracer + deposition, fscav 0.5: −7.42 × 10⁻⁴ → +3.0 × 10⁻¹⁵ per day; column residual / deposition deep 2.0 × 10⁻³ → 6 × 10⁻¹⁶, shallow 1.5 × 10⁻² → 1 × 10⁻¹⁵ | BUG FIX | — | fscav 0: byte-identical; prognostic fields unchanged in 24 h (no borrowing event) |
| F3 (01b) | SAMF, `GFS_typedefs`, `GFS_diagnostics.F90` | `wet_dep` is never exported (`Coupling%wetdpc_flux` is GF/rrfs_sd only; GOCART exchanges no deposition) | new bucket `cnv_wetdep_<tracer>`: export = meter to 1.3 × 10⁻¹¹ / 4.8 × 10⁻¹¹ | NUMERICAL CONSISTENCY (diagnostic) | — | none on the forecast |
| SAMF08 | `samfdeepcnv.f` | six early returns sit before the cellular-automaton trigger can re-enable a column, so a column's convection depends on the other columns in its block | `control_p8_mynn` 3×8 vs 4×6: 90/126 atmf024 variables differ → 0 | BUG FIX (reproducibility) | — | below noise (rms 0.3–0.7×); inert in our `control_p8` 24 h |

- **D3A and PH1 (section 6) are disjoint.** D3A pays fusion for detrained cloud ice, which stays in the atmosphere;
  PH1 pays it for convective precipitation the host classifies as snow. With both on, the SAMF segments' residual is
  exactly their KE term, and PH1's heating is exactly h_fus × host convective snow (0.07254 W/m²; ensfc2).
- **T1's donor-layer parcel start** was dropped by the red team (trred). It applies only where sub-stepping happens,
  widens the gap between tracer and q_v transport (0.10 → 0.17 of the increment) and changes nothing for PBL-mixed
  tracers (rms 2.355 × 10⁻⁵ vs 2.353 × 10⁻⁵). 02b keeps the interface-mean start.
- **T1 also sub-steps o3 and TKE**, which SAMF transports (section 15).
- **DRY's approximation** (environment dry fraction for the updraft): increment change 2.0 × 10⁻³ median, 7.7 × 10⁻³
  max; mass and uniformity exact either way (trred).
- **The F3 borrowing branch** is reached by a plume-shaped chemistry tracer about 847 times a day in shallow
  convection without any test hook (latent).
- **SAMF08** is latent in `control_p8`, which runs `do_ca`, `ca_sgs` and `ca_trigger`: our 3×8 = 4×6 gates passed
  because the case did not arise in 24 h (energy §9.8).

Sources: encnv; encpl; energy §9.2, §9.3, §9.8; trsamf; trred; trdyn; latent §1, §4; suites §10.1; tracer F1.

## 5. Microphysics (Thompson)

| Fix | Where | What goes wrong | Before → after (W/m², 24 h, unless stated) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| TH8 | `module_mp_thompson.F90` | sedimentation out of the lowest layer is counted as precipitation only above (the R1 placeholder value)·rr_min, although its mass has left | water 7.1 × 10⁻¹² kg/m²/s → 0; energy +2.37 × 10⁻⁶ (h_fus per kg: the dropped mass is frozen) → 0 | BUG FIX, **only with TH9 or E2** | — | alone: land canopy evaporation −68 % (f06), −47 % (f24) |
| TH9 | `module_mp_thompson.F90` | flux-form ice and snow sedimentation moves the R1 placeholder value (10⁻¹²) for an absent species as if it were mass; with TH8 that becomes booked fake precipitation | removes TH8's land signal: TH8 + TH9 with stock fwet, f06 canopy evaporation −2.9 %, sublimation +1.3 % (noise −0.01 %, −0.00 %) | BUG FIX | — (unconditional; one diff with TH8, cut on `fx`, the water proposal's TH8 + TH9) | with E2 on, TH8 + TH9 at noise from 6 h (rms 0.5–1.1× noise) |
| K1 | `module_mp_thompson.F90`, `mp_thompson.F90/.meta`, `GFS_typedefs` | Thompson's own c_p(1 + 0.887 r_v) and L(T) with constant L_s, L_f | changes Thompson's latent heat at 220–250 K by −0.14 % (deposition), −0.24 % (condensation), +1.3 % (freezing) | PHYSICS CHANGE | `thompson_kirchhoff` (.false.) | noise |
| TFH | `mp_thompson.F90/.meta`, `GFS_typedefs` | Thompson's per-layer heating (its own T, moist c_p, vapour redistribution) cannot equal the frame-F latent heat of its net phase change | Thompson frame-F gap +0.0083 → 9 × 10⁻¹³ | PHYSICS CHANGE | `thompson_frame_heat` (.false.) | 0.143 K / 7.73 Pa / 3.01 (noise) |

TH8 and TH9 are the water proposal's held fixes (its section 7). TH8 sends traces of sub-threshold snow to Noah-MP,
where any canopy ice hides the canopy's liquid (E2, section 6). Over land TH8 alone is far beyond noise (section 14).
TH9 is still needed with E2: without it, first-6-h snow sublimation is 1.7–2.5× noise. TH9 is unconditional and
ships with TH8.

Sources: energy §9.3, §9.5; canopy; encpl.

## 6. Surface: Noah-MP, NSST and sea ice

The surfaces enter the atmosphere's budget as boundary fluxes. Each component's own budget (Noah-MP: Niu et al.
2011) was metered (ensfc §1) and closed (ensfc2). Area fractions: soil 0.245, glacier 0.031, sea ice 0.0365, open
water 0.687.

**Bug fixes.**

| Fix | Where | What goes wrong | Before → after (W/m², global, unless stated) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| SI1 | `sfc_sice.f/.meta` | sea ice is stepped on every surface iteration: 1.9 % of ice column-steps were stepped twice | ≈ −0.010; calls per column-step 1.0186 → 1.0000 | BUG FIX | — | with SI2, NP1: ice thickness rms 1.7 × 10⁻³ m (noise 8 × 10⁻⁵), weasd over ice rms 0.105 (0.052); rest noise |
| SI2 | `sfc_sice.f` (`ice3lay`) | the excess lower-layer heat is divided by Δt a second time, deleting (1 − 1/720) of it while T2 is still reset | did not fire (March); thin ice near melting | BUG FIX | — | — |
| NP1 | `module_sf_noahmplsm.F90` (`phasechange`) | the heat of a snow layer that melts out is deleted when the layer below is sub-freezing | did not fire | BUG FIX | — | — |
| QR1 | `sfc_nst.f90` | `rain` (water depth per step) used as kg m⁻² s⁻¹ in qrain and sep | qrain 0.300 → 0.417 (× 1000/720) | BUG FIX | — | NSST-internal; noise |
| CMC | `module_sf_noahmplsm.F90` (`canwater`) | canopy evaporation capped after the energy solve charged it; frozen-canopy transpiration charged at h_sub but taken from soil liquid; canopy melt/freeze moves h_fus·Δm with no heat | land charged − carried 0.0148 → 0 (returned to the top soil layer, the NM11 path) | BUG FIX | — | soil T1 land +0.010 K (noise −0.003) |
| FL1 | `sfc_sice.f` (`ice3lay`) | flooded snow (heat content −L_i) becomes ice at the layers' temperatures | −7.87 × 10⁻³ → −1.15 × 10⁻¹³ | BUG FIX | — | with SI1: ice thickness rms 1.7 × 10⁻³ m |
| NM12 | `module_sf_noahmplsm.F90`, `module_sf_noahmp_glacier.F90` (`combine`) | when a ≥ 2-layer pack melts out in one step the bottom layer is merged into an inactive slot: the test uses the entry layer count `isnow_old < -1`, not the current `isnow < -1` (NCAR/noahmp#47) | per firing: water −0.10 to +0.16 mm, energy −1.1 to −8.5 MJ/m² → water ≤ 2.2 × 10⁻¹² mm | BUG FIX | — | fires 5 × 10⁻⁶ per call of melt-out-prone packs at 720 s, 1.7 × 10⁻² at 3600 s; C96 24 h bitwise |
| SL2 | both Noah-MP modules (`combine`) | a thin layer merged by mass keeps the receiver's T; snow that stops being layered drops its layers' sensible heat; truncated bulk snow changes soil-1 ice at T1 | with CS1, CB1: soil 3.9 × 10⁻⁴ → 4.3 × 10⁻⁸ (all at step 1, initial state) | BUG FIX | — | with CS1, CB1, NM12: T rms 0.147 K; land fields noise |
| CS1 | both (`csnow`) | snow heat capacity from capped volume fractions, so mass crossing the caps changes the layer heat | (in SL2) | BUG FIX | — | (in SL2) |
| CB1 | both (`combo`) | J m⁻³ K⁻¹ capacities used per kg; branches set T = tfrz or drop h_fus·w_liq without a phase change | (in SL2) | BUG FIX | — | (in SL2) |

All bug fixes together: T rms 0.156 K; every surface field at noise except the ice fields above (ensfc2).

**Options** (`gfs_physics_nml`; off = bitwise).

| Fix | Where | What goes wrong | Before → after (W/m², global) | Class | Switch (default) | Impact vs noise (24 h, land) |
|---|---|---|---|---|---|---|
| CH1 / CH2 | Noah-MP (`vege_flux`) | `vege_flux` books only the last Newton increment of canopy heat storage | 0.052 → 3 × 10⁻¹⁷ (CH1); storage frame 7 × 10⁻¹⁶ (CH2) | CH1 NUMERICAL CONSISTENCY; CH2 PHYSICS CHANGE | `noahmp_canopy_heat` (0; 1 massless canopy, 2 heat storage over the step) | CH1: T rms 0.161, t2m −0.015 K; CH2: T rms 0.254, t2m +0.27 K, SH −3.6 W/m² (large) |
| PH1–PH3 | `GFS_MP_generic_post`, Noah-MP soil and glacier | the atmosphere pays fusion for the convective snow the host classifies (PH1); Noah-MP soil (PH2) and glacier (PH3) take the host's phase decision | surfaces receive host srflag·P to 1.3 × 10⁻¹³; PH1 = h_fus × host convective snow (0.0725) exactly | PHYSICS CHANGE (missing term) | `precip_phase_host` (.false.) | noise |
| SW1 | Noah-MP | Noah-MP absorbs SW with its own albedo, cos z and band split, not the radiation's | −0.093 → 0 where landfrac = 1 (−6.3 × 10⁻³ in 0.999 ≤ landfrac < 1) | NUMERICAL CONSISTENCY | `noahmp_sw_radshare` (.false.) | T rms 0.175; land uSW −0.78 W/m², rms 12.1 (noise 2.1) |
| LW1 → LW2 | surfaces, lowest layer | surfaces emit at their current T while the atmosphere's LW uses radiation-time fluxes. LW1 gives the difference to the lowest layer; LW2 keeps it in the land, which sends it out next step through its own energy balance | both close to round-off (LW2: 5 × 10⁻¹⁴) | NUMERICAL CONSISTENCY | `lw_sfc_consistent` → `lw_sfc_return` (.false.) | LW1: T rms 0.201, t2m +0.21 K; **LW2**: 0.176, t2m −0.034 K, soil T1 +0.12 K |
| EV1 | Noah-MP soil + glacier | frame-F enthalpy of evaporated water (latent charged, the water's content where it leaves, vapour at T1) | applied = booked to 6 × 10⁻¹⁷ (soil term +0.1255) | PHYSICS CHANGE (frame F) | `sfc_evap_enthalpy` (.false.) | T rms 0.159, t2m +0.027 K |
| AD1 | Noah-MP soil | soil water moved between layers carries no sensible heat | 0.058 → 1 × 10⁻¹⁴ | PHYSICS CHANGE | `noahmp_heat_advect` (.false.) | noise |
| KF1 | Noah-MP | freezing and melting at constant h_fus while the heat capacity changes | 0.200 → 2.8 × 10⁻⁸ (at step 1 only) | PHYSICS CHANGE (trade-off: 6 % of h_fus at −10 °C) | `noahmp_kirchhoff` (.false.) | noise |
| EP1 | `GFS_MP_generic_post`, surfaces | precipitation lands with its frame-F enthalpy (liquid c_l, frozen c_i^F with FV3's c_ice); PH1 then releases L_f(T1) instead of h_fus | target = PAH + stored + applied to 10⁻¹⁶; the PH1 overheating −1.78 × 10⁻³ removed | PHYSICS CHANGE | `sfc_precip_enthalpy` (.false.) | noise (soil T1 +0.019 K) |
| AIR1 | Noah-MP soil | water filling or leaving soil pores takes the pore air's heat with it (c_pair used as J m⁻³ K⁻¹); nothing books it | 2.4 × 10⁻³ → 8.5 × 10⁻¹⁵ | PHYSICS CHANGE (model inconsistency) | `noahmp_pore_air` (.false.) | noise |
| PL1 | `GFS_MP_generic_post`, Noah-MP, sea ice, `GFS_restart` | the surfaces book step N's precipitation at step N+1's T1, the atmosphere exported it at T1(N) | hand-off lag −1.2106 × 10⁻² → 0 (land −2.41 × 10⁻³ → 0); one restart field, written only with EP1 | BUG FIX of the EP1 option (acts only with EP1) | `sfc_precip_enthalpy` (no switch of its own; with EP1 off the tree is bitwise to one without PL1) | noise (T rms 0.139 K, land LH +0.06 %) |
| E2 | Noah-MP (`fwet`; ccpp and NOAA-EMC/noahmp copies) | `fwet` picks the canopy phase by "any ice" while every consumer uses T_v; the ice capacity is ~50× the liquid's, so a trace of ice hides the liquid and stops canopy evaporation | canopy R_S 3 × 10⁻¹⁷; atmosphere water 2 × 10⁻²⁰; energy 1.6 × 10⁻¹¹ | BUG FIX, switched (beyond noise) | `noahmp_fwet_opt` (0; 1 mass-weighted, 2 larger fraction, 3 dominant phase as Noah-MP v5, He et al. 2023) | 0–24 h on full10, opt 1 / 2: canopy evaporation +32 / +36 %, land LH +1.5 / +1.2 %; global T rms 0.153–0.159 (noise 0.139) |
| E1 | NSST (`sfc_nst`, `sfc_ocean`) | NSST's sea-spray fluxes are explicit; where the gain λ > 2 the lowest layer flips every other step | oscillating cells in 10 days 271 → 2; conserves by construction (one flux pair) | PHYSICS CHANGE (numerical stability) | `nst_spray_opt` (0; 1 backward Euler with the lowest layer) | global LH −0.21 W/m² (noise −0.03), open-water LH −0.29 % |

- **E2's options.** A candidate diff in the water proposal declared a local `cwat` that shadows Noah-MP's specific
  heat of water; its numbers are withdrawn (section 14). 01 avoids it. Option 2 is recommended because it is
  monotone: adding water never lowers `fwet`. On full10, 0–24 h: opt 1 +32.1 % / LH +1.47 %; opt 2 +35.5 % / +1.23 %;
  opt 3 within a few per cent of opt 2 (f06/f24 buckets). In `full13` all-on (opt 2) vs control, t2m −0.020 K.
- **E1 cuts the spray latent flux.** It delivers 81 % of the explicit form's spray latent flux globally, and 23–26 % in
  the cells where the explicit form is unstable, where that form overshoots the layer's own equilibrium. A solve coupled
  to the PBL's implicit diffusion would cut less; that is the owners' alternative. There is no tropical cyclone on
  current `develop` from this date, so the water proposal's day-6.4 runaway is not reproduced.
- **NM12's EMC companion (20b)** for NOAA-EMC/noahmp is not built. Noah-MP v5 already tests the current layer count.
- **NM10r** (revised water diff 17): Noah-MP takes the host's convective-phase decision unconditionally. NM10's
  `sfctmp < tfrz` and the host's `tsfc < 273.15` disagree on 5.0 % of land column-steps with convective
  precipitation, 0.83 % of its mass; net extra frozen on land h_fus × 1.45 × 10⁻⁸ = 4.9 × 10⁻³ W/m² (ensfc2 12).
  In `full14` the land receives the host's frozen fraction to 1.2 × 10⁻¹⁰ of frozen mass (NM10: 2.5 × 10⁻²). Noah-MP's
  water balance closes to 6.6 × 10⁻¹³ mm per column-step and the atmosphere water rows to ≤ 3 × 10⁻²⁰ kg/m²/s, both
  unchanged by NM10r. Land means are at noise (canopy evaporation +0.16 %, LH −0.01 %, T2m 0.000 K); snow-field rms is
  1.2–1.8× noise. It is a physics change: it picks the host's skin-temperature criterion over NM10's lowest-layer air
  temperature. Water diff 17r is cut on `develop` + water 01–16; 18 applies after it.

Sources: ensfc; ensfc2; nm12; preclag; canopy; energy §9.4, §9.6, §9.7.

## 7. Tracer transport in FV3

| Fix | Where | What goes wrong | Before → after (relative deviation of a uniform dry tracer, unless stated) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| `dry_tracer_adv` (DYN v6) | `fv_tracer2d.F90`, `fv_mapz.F90`, `sw_core.F90`, `dyn_core.F90`, `fv_dynamics.F90`, `fv_nesting.F90`, `fv_arrays.F90`, `fv_control.F90`, `atmosphere.F90` | the hord_tr 8 limiter and the remap act on each water species separately, so Σ A(w_i) ≠ A(Σ w_i): a tracer uniform in dry ratio is not carried with the dry air the limited water fluxes imply | per call: advection 1.8 × 10⁻⁴ → 6.7 × 10⁻¹⁶, remap 1.6 × 10⁻⁴ → 1.2 × 10⁻¹³; also `tracer_2d` with `nord_tr`, nested grids and `inline_q` | PHYSICS CHANGE (chemistry tracers only) | `dry_tracer_adv` (.false.) | weather bitwise; +1.5 % cost |
| `dry_negadj` (DYN v6) | `fv_tracer2d.F90` | `neg_adj2/3/4` borrow water between layers at fixed δp, which moves dry air with no tracer flux (active only where water goes negative: with `nord_tr` damping or `inline_q`) | 2.3 × 10⁻⁷ → 4.4 × 10⁻¹⁶ per call; 24-h max deviation with `nord_tr` 1.8 × 10⁻⁹ → 4.9 × 10⁻¹³, with `inline_q` 1.25 × 10⁻¹⁰ → 5.1 × 10⁻¹³ | PHYSICS CHANGE | with `dry_tracer_adv` | weather bitwise |
| `dry_tracer_ic` (DYN v6) | `atmosphere.F90` | the IC's remap and adiabatic initialisation treat a chemistry tracer as a moist ratio | IC deviation 3.4 × 10⁻⁴ → 2.2 × 10⁻¹⁶ (max) | PHYSICS CHANGE (input convention: IC fields are dry ratios) | `dry_tracer_ic` (.false.) | reinterprets a structured GHG field: 2.1 ppm rms, 12.5 max (section 15) |

End to end (02b + 03b + v6, both switches, dry IC): a tracer uniform in dry ratio stays uniform to 3.7 × 10⁻¹⁴ rms
and **4.9 × 10⁻¹³** max in 24 h, from 1.07 × 10⁻³ / 1.22 × 10⁻² without any of the three; tracer mass stays at
3 × 10⁻¹⁵ per day. Both switches act only on `"tracer_usage","chemistry"` tracers, and `type=diagnostic` tracers are
excluded.

**Gates** (trdyn): off = bitwise (all 2520 17-digit mass lines, atmf024, restart); on = water, T, u, o3, TKE and
generic tracers bitwise; 3×8 = 4×6; restart bitwise; OpenMP 2 threads = 1. With the 32-bit dycore the deviation is
1.0 × 10⁻⁶ rms (from 2.4 × 10⁻⁵), the float32 floor. Nested grid (32-bit, 3 h): parent 6.6 × 10⁻⁴ → 5.0 × 10⁻⁶, nest
7.8 × 10⁻⁴ → 7.7 × 10⁻⁶ with no boundary signature; the nest test found a stale first boundary condition under
`dry_tracer_ic`, now fixed. In GOCART's `atmaero_control_p8_rad` (32-bit) the switch is off-bitwise and on at the noise
of a `consv_te` 0.999 perturbation (T 0.169 vs 0.176 K, burdens 5 × 10⁻⁵ to 3.6 × 10⁻³ vs 4 × 10⁻⁵ to 3.7 × 10⁻³);
a uniform test tracer cannot be carried there, because GOCART overwrites chemistry tracers it does not know.
`FILL2D` (compiled only with `-DFILL2D`, in no UFS build) stops with FATAL under the switch.

**Who generates the structure** (trunif; tag tracers, 24-h rms / max of the uniform dry tracer): SAMF deep
1.04 × 10⁻³ / 1.31 × 10⁻², SAMF shallow 2.6 × 10⁻⁴ / 5.1 × 10⁻³, PBL 1.8 × 10⁻⁴ / 7.0 × 10⁻³ (all three fixed by
DRY, section 4), FV3 advection 2.2 × 10⁻⁵ / 1.2 × 10⁻³ and remap 5.1 × 10⁻⁶ / 4.5 × 10⁻⁴ (fixed here), IC once
(fixed here). Every scheme preserves a constant in its own basis; the structure comes from moving one tracer in two
bases.

Sources: trdyn (rounds 1–4); trunif; tracer.

## 8. Tendency application (TOPT) and gravity-wave drag

| Fix | Where | What goes wrong | Before → after (W/m², 24 h) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| TOPT (latent 03) | `GFS_suite_interstitial_3.F90/.meta`, `GFS_GWD_generic_post.F90`, `GFS_PBL_generic_post.F90`, `mynnedmf_wrapper_post.F90`, `dcyc2t3.f` | the process-split sum (radiation R, PBL P, GWD G) is applied only by a scheme with option 3, and nothing checks that one follows a 2: base drops tendencies for (`tend_opt_pbl`, `tend_opt_gwd`) = (1,1), (1,2), (2,1), (2,2), (3,2); option 4 silently discards; `suite_FV3_HRRR_gf_nogwd` never applies R or P with the default options | broken combinations +110 to −142 → 2.08–3.12 (default 2.090); `GFS_suite_interstitial_3` applies a pending sum once; option 4 → CCPP error | BUG FIX | — | default (2,3) bitwise; fixed (2,1), (2,2) at noise of the default |

The `tend_opt_*` options are `gfs_physics_nml` entries (an earlier note said they were hard-coded; section 14). The
PBL × GWD cross term of the default process-split update (D12) is in section 4. Combinations with `tend_opt_pbl` 1 or
3 differ from the default by 0.21 K and 14.6 Pa, also in the combinations base already handles correctly: time-split
PBL is a different physics configuration, not a defect. Not covered: deep, shallow or MP option 2 after the flush
point, and SW/LW options other than 4. Option 4 is an error, not a warning (section 15). Source: latent §3.

## 9. Build: SAMF single precision

| Fix | Where | What goes wrong | Before → after (files built single precision) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| SAMF32 (latent 02) | `UFSATM/ccpp/CMakeLists.txt` | `-DSAMFCNV_32BIT=ON` filters the scheme files only, but `mo_conv_kind.F90`, `progsigma_calc.f90` and `progomega_calc.f90` are capgen dependencies: `conv_wp` stayed 8-byte and the option did nothing | files with `-real-size 32 -DSAMFCNV_USE_SP`: 2 → 5; configure stops if only some are found | BUG FIX (build) | — (acts only with `-DSAMFCNV_32BIT=ON`) | OFF: flags identical, run bitwise. ON: C96 24 h runs, tracer mass ~10⁻¹⁰/day (single-precision round-off) |

Source: latent §2.

## 10. Other suites: MYNN-EDMF, GFDL MP v3, Grell–Freitas

These are the water proposal's Appendix E.3–E.5, now fixed. Cases: `control_p8_mynn` and `rap_control` (MYNN, GF),
`control_iovr4_gfdlmpv3` (GFDL MP v3), C96L127, 24 h, 64-bit dycore, `-no-fma`, each with its own `consv_te` 0.999
noise control. Impacts are area- and mass-weighted.

| Fix | Where | What goes wrong | Before → after (kg/m²/day, unless stated) | Class | Switch (default) | Impact vs noise |
|---|---|---|---|---|---|---|
| MYNN 01 | `module_bl_mynn.F90`, `mynnedmf_wrapper.F90` | (a) surface fluxes made kinematic with ρ(k=1) but multiplied back by a surface density with a typo (+0.85 % of E); (b) the dew limiter is always 0 (+0.67 % of E); (c) the column filler weights by MYNN's interpolated δp, the solver conserves ρ·dz; (d) ρ = Δp/(g·dz) in the solver | water +4.53 × 10⁻² → −5.5 × 10⁻¹⁵ (p8_mynn); RAP +4.70 × 10⁻² → −5 × 10⁻¹⁵ | BUG FIX (a–c), NUMERICAL CONSISTENCY (d) | — | p8: LH +0.56 W/m², T2m −0.021 K, ps rms 1.19× |
| MYNN 01b | `module_bl_mynn.F90` | `moisture_check` adds the latent heat of filled condensate to θ_l, then `Dth` counts it again | +8.0 W/m² spurious heat (= h_vap × fill, 0.28 kg/m²/day) → 0 | BUG FIX (energy) | — | p8: T −0.063 K, LH +3.12, SH +0.42 W/m², ps rms 2.37× |
| MYNN 04 | `module_bl_mynn.F90`, `mynnedmf_wrapper.F90/.meta`, `GFS_typedefs` | surface sensible heat applied as a θ flux without 1/Π and with c_pm: 16.72 vs 16.97 W/m² reported | applied = reported | NUMERICAL CONSISTENCY | `mynn_sfc_heat` (.false.) | noise (0.9–1.2×) |
| MYNN 06 | `module_bl_mynn.F90`, `mynnedmf_wrapper.F90/.meta`, `GFS_typedefs` | MYNN mixes θ_l, not an energy | θ_l-equation gap 0.47 → 2 × 10⁻⁹ W/m² | PHYSICS CHANGE | `mynn_mix_sl` (.false.) | p8: SH −0.68, LH +1.75 W/m², T2m +0.068 K, rms 1.3–1.5× |
| GFDL 02 | `gfdl_cloud_microphys_v3_mod.F90` | converts in with 1/(1 − q_v,in) and back with 1/(1 + q_v,new) (as TH1): the host's species mass is the true mass × 1/[(1 − q_v,in)(1 + r_v,new)] | MP water −8.39 × 10⁻³ → −9.3 × 10⁻¹⁶ (−1.03 % of MP precipitation) | BUG FIX | — | T +0.001 K, precipitation +0.15 %, rms 1.1–1.3× |
| GFDL 07 | `gfdl_cloud_microphys_v3_mod.F90` (`terminal_fall`) | rain and cloud-water sedimentation exchange heat with the ice heat capacity | own frame + water PE: +0.20 → −0.007 W/m² (the fix is 0.21) | BUG FIX (energy) | — | T −0.003 K, rms 1.1–1.3× |
| GF 03 | `cu_gf_driver.F90/.meta`, `GFS_typedefs` | (a) shallow-only columns dry the air but report no precipitation; (b) the vapour increment is applied on a different mass basis; (c) GF shallow is not consistent with itself (−2.5 %); (d) floors | GF water −1.37 × 10⁻¹ (−30 % of its precipitation) → +2.5 × 10⁻¹⁶ | BUG FIX (a) + NUMERICAL CONSISTENCY (b–d) | `gf_closure` (.false.) | precipitation +8.9 % (+1.9 × 10⁻⁶ kg/m²/s; convective bucket +2.9 × 10⁻⁶ kg/m²/s), SH −0.10, T −0.011 K, rms 1.0–1.4× |

- **01b.** The red team (mynnred) reproduced `Dth` exactly with the real `moisture_check`; the forecast cooling is
  what 8 W/m² for 24 h predicts. Version 2 moves the call after `Dth` with a scratch θ, so a snow fill is counted
  once too. NCAR/MYNN-EDMF since ebd5d2d (February 2025) builds its FLAG_QI `Dth` from the input condensate, so there
  the fill is counted once; the CCPP copy and the MMM/MPAS copy still double count. v2 is correct for both forms.
  01b has the largest unconditional impact in the series.
- **Tracers.** MYNN (`mix_chem` off), GF (generic tracers not transported) and GFDL MP v3 never touch the passive
  test tracers.
- **Gates.** All gates are bitwise, including `p8_mynn` 3×8 = 4×6 (with SAMF08).
- **Tested, not proposed.** A constant-pressure GFDL switch (`not_proposed/E4b`) reduces the GFDL gap only from
  0.117 to 0.085 W/m², because `sedi_heat` keeps c_v hard-coded.
- **Untested.** GF chemistry transport and wet scavenging (`rrfs_sd`), `FV3_HRRR_gf`, the OpenACC build, and HAFS
  `FV3_HAFS_v1_gfdlmpv3_tedmf`.

Sources: suites; mynnred.

## 11. MPAS-A

Summary of `conservation/mpas/report.md` (another session's work). Case: MPAS-A (Skamarock et al. 2012) @aa6d8cd69,
supercell (init case 5), 84 × 84 doubly periodic 2-km hexes, 40 levels, 20-km lid, double precision, dt 12 s,
Thompson, no surface fluxes or radiation, 24 h, 16 tasks. The deliverable is 14 patches in
`proposal/patches/ports/MPAS-conservation/`:

| Patches | Content | Class | Switch (default) |
|---|---|---|---|
| 0001–0004 | Thompson water closure (= `MPAS-thompson/`) | BUG FIX | — |
| 0005–0007 | scalar transport: positive-definite upwind, `config_positive_definite`, column-local guard | BUG FIX | — |
| 0008–0009 | TH8, TH9 (in the MPAS series only; held for UFS and other copies) | BUG FIX | — |
| 0010 | Thompson sedimentation export | INSTRUMENTATION | — |
| 0011 | energy and water meter, reproducing sums, restart totals | INSTRUMENTATION | `config_energy_meter` |
| 0012 | layer-local microphysics energy coupling (option B) | PHYSICS CHANGE, opt-in | `config_mp_energy_coupling` (`'stock'`) |
| 0013 | reproducible global energy fixer | FIXER (labelled), not a fix | `config_energy_fixer` (off) |
| 0014 | dissipative heating: KE removed by explicit diffusion and damping returned as heat | PHYSICS CHANGE, opt-in | `config_dissipative_heating` (0; 1 local work, 2 positive-definite) |

| Quantity, 24 h (relative) | Stock | Series + layer coupling + fixer |
|---|---|---|
| ΔW/W | 1.3 × 10⁻³ | −1.6 × 10⁻¹⁶ |
| ΔM_d/M_d | ≤ 7 × 10⁻¹⁵ | 0 (exact) |
| ΔE/E | −4.3 × 10⁻⁴ (with TH8/TH9, stock coupling, no fixer) | +1.9 × 10⁻¹⁶ (by construction) |

- **Stock MPAS latent heating is consistent** with MPAS's energy: it heats at constant volume with (L − R_v·T)/c_v,d,
  unlike FV3 (section 1).
- **Option B** adds the frictional heating of falling water (6.4 points; Pauluis et al. 2000, Makarieva et al. 2013)
  and a Kirchhoff-slope term (0.9 points): E-consistent heating is 7.3 % larger than Thompson's. The storm is stronger
  beyond noise (peak w +4.05 m/s, cold-pool area +169 km², updraft volume +40 km³, without the fixer) and
  precipitation is within noise.
- **The dycore residual** (−3.78 × 10⁵ J/m²) splits into:
  - explicit diffusion and damping that return no heat, −2.48 × 10⁵ (65 %, DESIGN);
  - a remainder, −1.31 × 10⁵ (35 %, OPEN), the net error of the energy-conserving operators.
- **0014 option 2** (positive-definite, each term rescaled per step to its exact work):
  - the fixer falls from 3.81 × 10⁵ to 1.31 × 10⁵ J/m²;
  - local heating min 0, rms peak 4.9 K/day;
  - peak w +1.03 m/s, w99.9 +1.19 m/s and cold-pool area +97 km² beyond noise; precipitation within noise.
- **Gates.** All pass bit-identically: default namelist vs the series without 0012/0014, straight and at 7 tasks,
  restart 12 + 12 h (8 checks); 0014 on at 16 vs 7 tasks and across restart. Known-bad cases fail as they must.
- **Logged, not fixed** (inactive in this configuration): condensate zeroing above `config_microphysics_top`,
  non-flux-form vertical θ mixing, the Kessler top-layer `rdzk`, LBC operator precedence, `precipw` density, odd
  `number_of_sub_steps`, and the IAU/LBC density mismatch.

Source: mpas (§1–§10).

## 12. Results: the final 24-h energy budget

Frame F, 24-h means, C96, every switch on (`full13`, metered twin `mq13`, job 10157244; energy §9.8):

| Term | Value (W/m², unless stated) |
|---|---|
| **Residual net of the declared terms** | **+1.6 × 10⁻¹²** |
| Scheme frame-F gaps: radiation, PBL, GWD, SAMF deep and shallow, Thompson + MP post | each ≤ 1.2 × 10⁻¹² |
| Declared terms (surface hand-off, h2ophys, PH1 snow as ice) | section 13 |
| `consv_te` fixer correction (fixer window exactness) | −0.3040 (+1.4 × 10⁻¹⁰) |
| Surface vs atmosphere precipitation heat capacity, Σ\|Δ\|/Σ | 7.2 × 10⁻¹² |
| PBL water, dW − flux | +1.0 × 10⁻²⁰ kg/m²/s |

**Residual by integration stage** (energy §1, §7, §8, §9.4–§9.8):

| Tree | Residual (W/m²) | Frame |
|---|---|---|
| base | +2.0785 | E_D |
| + FX1 SG1 CP1 | +2.090 | E_D |
| + R1, FV2, `dspheat_ke` | +0.633 | E_D |
| + D3A | +1.056 (D3A adds the missing 0.44 of fusion heating, which then shows on the coupling side) | E_D |
| all switches of rounds 1–3 (`all_full`, C1 = 7) | +0.0836 | F |
| `full9` (+ energy round 4, latent, trdyn, ensfc2 rounds 1–3) | −2.1 × 10⁻¹² | F |
| `full11` (+ ensfc2 round 4, canopy) | −6.8 × 10⁻¹³ | F |
| `full12` (+ `dyn_te_exact` 31) | +4.0 × 10⁻¹¹ | F |
| `full13` (+ PL1, suites 01–08) | **+1.6 × 10⁻¹²** | F |
| `full14` (TH9 unconditional, PL1 folded, NM10r; all-on bitwise to `full13`) | **+1.6 × 10⁻¹²** | F |

Each surface's own budget closes separately (ensfc2, e5MA2; values in the Summary and section 6). Noah-MP soil is
4.33 × 10⁻⁸ W/m², of which 3.56 × 10⁻⁸ comes from step 1 (the initial state); later steps are ~10⁻¹⁰ each, the
round-off of differencing ~10⁸ J/m² of column heat.

## 13. What remains

**Declared terms, and why each is not a defect.**

| Term | Size (W/m²) | Why it is declared |
|---|---|---|
| Surface hand-off (LW2 + EV1 heating of the lowest layer) | +0.1135 (run-dependent; 0.117 in ensfc2's run) | the LW and evaporation enthalpy the surfaces book beyond what the radiation and the PBL deliver, applied by `GFS_surface_composites_post`; an identity, closed to 10⁻¹³ in every run, not a number to match |
| h2ophys, S_chem = h_vap·ΔW_v | +1.44 × 10⁻⁵ | a deliberate photochemical water source with no heat; the water budget books the same source |
| PH1 snow leaves as ice at T1 (EP1) | −1.74 × 10⁻³ | the atmosphere pays L_f(T1) for convective snow, which the surface receives as ice at T1 (same frame on both sides) |
| Open ocean, F_ocn | ~+6.6 into the prescribed ocean | prescribed SST is an open boundary; NSST is a diagnostic skin. F_ocn is defined from the atmosphere side, so it closes by definition |
| Runoff and the glacier flow at their own T | glacier flow +0.0074 before booking | water leaving the land carries its sensible heat out through an open boundary |
| SW in 0.999 ≤ landfrac < 1 cells | −6.1 to −6.3 × 10⁻³ | those cells use the radiation-time land share; the open-water remainder takes the difference by F_ocn's definition |
| Noah-MP initial state | 3.6 × 10⁻⁸ at step 1 | KF1 and the snow fixes act once on the cold-start state |
| `consv_te` fixer | section 12 | FV3 still creates this much energy (below); the fixer removes it exactly (window 10⁻¹⁰). It stays on |

**FV3's adiabatic +0.41 W/m² (OPEN).** Dynamics plus tracer transport, net of the damping KE, create +0.4145 W/m²
(fv3tally). The term does not converge with any time step and barely moves with the tracer scheme:

| Change | Adiabatic remainder (W/m²) |
|---|---|
| none | +0.4132 |
| acoustic step halved (`n_split` 8) | +0.3984 |
| remap every 180 s | +0.4099 |
| `dt_atmos` 360 s | +0.4074 |
| `hord_tr` 5 | +0.4251 |

It is a property of the spatial discretization: the D-grid KE that `compute_total_energy` counts is not the KE that
the vector-invariant momentum equation and the pressure-gradient work exchange with internal and potential energy.
Closing it would change the discretization, so we propose nothing. The vertical remap's −0.114 is design; bit 64
returns it.

**Inherent scheme gaps in other suites** (suites §10.2):
- **Grell–Freitas, −0.26 W/m² (frame P, with `gf_closure`).** The deep updraft freezes condensate with its own
  partition and heat; the driver re-partitions detrained and transported condensate into ice by temperature with no
  heat; shallow and mid convection have no ice phase. One partition with its heat across `cu_gf_deep`, `cu_gf_sh` and
  the driver would close it. That is a restructuring for the owners.
- **GFDL MP v3, −0.028 W/m²** in frame F with water PE (−0.007 in GFDL's own frame, where w-sedimentation KE is not
  metered). The rest is GFDL's own constants (c_liq 4218 vs 4185.5, c_ice 2106 vs 1972, tice 273.16).
- **MYNN.** The remaining frame-P "gap" is TKE-dissipation heating (2.21 W/m²) against the mean-flow KE loss (−2.27):
  a TKE/KE accounting choice, the same question as `dspheat_ke`.

**MPAS.** The dycore remainder of −1.31 × 10⁵ J/m² (35 %) is OPEN and closed only by the labelled fixer.

**Untested paths.**

| Path | Status | Source |
|---|---|---|
| Regional FV3 (`dry_tracer_adv` BC handling) | untested: `regional_control` uses MYNN, no DRY physics, and its BC files carry no chemistry tracers | trdyn |
| HAFS moving nest | untested | trdyn |
| NSSL (nwat = 7) runs of `dyn_te_exact` v2 | compile only (no NSSL suite or inputs in this build) | fv3tally, dycred |
| Non-MOIST_CAPPA (dry-branch) non-hydrostatic run of `dyn_te_exact` | compile only (`-DHYDRO=ON` builds are hydrostatic) | fv3tally |
| MULTI_GASES with `dyn_te_exact` | compile only; bits 1, 8, 64 stop with FATAL | fv3tally |
| FX1 with `do_sat_adj` = .true. | exact to first order only (weights use pre-adjustment q); not exercised by `control_p8` | energy §3 |
| `dspheat_ke` with `use_oceanuv` | the surface work is computed in the ground frame; not exercised | enpbl §5 |
| R1 in the SCM and MPAS hosts | need the two new `Radtend` fields; not tested | energy §6 |
| NSST `sfc_ocean.F`, the NOAA-EMC/noahmp copies (E2, NM12 20b) | compile only, or not built (20b) | canopy, nm12 |
| GF chemistry transport (`rrfs_sd`), `FV3_HRRR_gf`, OpenACC; HAFS GFDL MP v3 | untested | suites |
| TOPT: deep/shallow/MP option 2 after the flush point; SW/LW options other than 4 | not covered by the fix | latent §3 |
| Meters with more than one OpenMP thread | meter accumulators are not thread-safe; the model is | trdyn |
| `neg_adj3` under `nord_tr` or `inline_q` without `dry_tracer_adv` | water-only fixer moves dry air with no tracer flux (2.3 × 10⁻⁷ per call); fixed only under the switch | trdyn |

## 14. Corrections

Claims made earlier in this work, or in the water proposal and its issue drafts, that were later withdrawn or
corrected. The current numbers are the ones above.

| What was claimed | What is right | Source |
|---|---|---|
| Water proposal E.2: the mass-weighted canopy wetted-fraction candidate (`candidates/issue4_*`) and the impacts measured with it | the candidate declares a local `cwat` that shadows Noah-MP's specific heat of water, so `precip_heat` reads an uninitialised local; its numbers are **withdrawn**. The issue draft's larger-fraction numbers are real (a clean edit) but were 0–24 h means of four 6-h buckets, not the f24 bucket, on a stock-option base: canopy evaporation +19.1 %, sublimation −13.0 %, land LH −0.44 %, T2m −0.087 K. On the all-switch base the sign of land LH differs (+1.2 to +1.5 %) | canopy |
| Water proposal: NM10 follows "the host's own rule (L495–516)" | L495–516 is the Morrison–Gettelman branch (T850). The Thompson branch is L466–483 (`tsfc < 273.15`); NM10 uses `sfctmp < tfrz`. Proposal text corrected 17 October; NM10r is adopted (sections 6, 15) | ensfc §6, TRACKER |
| MPAS: explicit dissipation is 88 % of the storm's dycore energy loss (79 % thermal), remainder 4.4 × 10⁴ J/m² | **withdrawn**: the v1 tally took w and θ_m snapshots before `w_dissipation_3d` and `scalar_dissipation_3d_les`, which zero their tendency first, so it counted w·(D_now − D_prev). v2: explicit −2.48 × 10⁵ (65 %), remainder −1.31 × 10⁵ (35 %) | mpas §4 |
| MPAS dissipative heating v1 | **withdrawn** (same snapshot error; ±1000s of K/day, S_liq 0.04 → 2.25); replaced by 0014 v2/v3 | TRACKER |
| "TH8 is about noise" (T rms 0.173 K, ps 9.5 Pa at f24) | that was the global T rms only. Over land TH8 alone moves canopy evaporation −68 % (f06) and −47 % (f24); it ships only with TH9 or E2 | energy §9.3, §9.5; canopy |
| `tend_opt_*` are hard-coded defaults, not namelist entries | they are `gfs_physics_nml` entries (GFS_typedefs L4236–4239), reachable from `input.nml` | encnv D12, latent |
| SAMF32 has no effect because of CMake directory scope | the filter searched `SCHEME_FORTRAN_FILES` only; the three missing files are capgen dependencies. The target is created in the same CMakeLists | trred, latent |
| MYNN 01b impact: T −0.049 K, LH +3.19 W/m², ps rms 2.42× noise | those were unweighted grid means; area/mass-weighted: **T −0.063 K, LH +3.12 W/m², ps rms 2.37×** (RAP: unweighted T −0.042, mass-weighted −0.049) | mynnred, suites §3, §10.4 |
| MYNN 01b v1 (scratch copy before the call) | drops the heat of a snow fill (snow is not in `Dth`); v2 moves the call after `Dth` | mynnred, suites §10.4 |
| GFDL MP v3 species "scaled by (1 − q_v,in)(1 + q_v,new)" | the host's mass is the true mass × 1/[(1 − q_v,in)(1 + r_v,new)], the inverse | mynnred |
| Flow work creates energy | it is ±R_v·T on every vapour mass change; the net is a **sink** of −0.62 W/m², so bit 2 adds +0.62 and moves heat from the mid-troposphere into the PBL. −3.4 % precipitation is the all-bits result; bit 2 alone gives LH −1.97 W/m² | fwred, encpl |
| Coupling Kirchhoff remainder +0.665 W/m² | that used a heat-capacity heuristic; measured with species fluxes it is −0.013 | encpl |
| `samf_kirchhoff` (S1) closes SAMF in frame F | it added +0.122 W/m² of residual: it misses the ice phase and uses the SAMF-entry T. Completed by S1K | energy §9.2 |
| Per-layer −ΔKE heating (round 1 of `dspheat_ke` and of D3B) | cools layers that import KE (−0.62 W/m² for the PBL; −0.209 against +0.148 net for CMT, max 95 K/day); replaced by the interface form (D4 keeps the per-layer form) | enpbl §3, encnv |
| Raw per-cell D7 heating | noisy (max 0.87 K/step); use with D7S, 32 passes | energy §8, §9.3 |
| Surface round 1: land SW hand-off error −0.573 W/m² | compared the land's absorption with the cell-mean net SW, which includes water's albedo in coastal cells; the real land interface error is −0.156 | ensfc §8 |
| SL1: snow-layer combination loses −0.010 W/m² | misattributed: it is new snowfall added to cold layers at their T; SL1 dropped. The real snow-layer defects are SL2, CS1, CB1 | ensfc §5, ensfc2 |
| Uniform tracers: the −0.9 %/+0.4 % after step 1 come from the IC | they come from step 1's SAMF deep and shallow; the IC leaves max 9.0 × 10⁻⁵ (`external_ic`) and 3.4 × 10⁻⁴ (`adiabatic_init`) | trunif |
| PBL05: the same defect in `control_p8`, where the p8 meter should have seen it | the code is in `control_p8`, but the term is zero there by construction; PBL05 is a last-bit change in p8 | energy §9.8 |
| The 3×8 = 4×6 gates show `control_p8` is decomposition-safe | they passed because the CA early-return case did not arise in 24 h; SAMF08 removes the dependence | energy §9.8 |
| ensfc2 16 as delivered | its `GFS_MP_generic_post.meta` `[tgrs]` used `air_temperature` (`gt0`'s name), a capgen duplicate; 16b uses `physics_timestep_initial_air_temperature`. 16 had not been built as delivered | energy §9.6, preclag |
| ensfc2: PH1's T1 is `save_t` (before the MP tendencies) | the built and metered T1 is the step-start `tgrs(:,1)`, the consistent one | preclag |
| `dyn_te_exact` v1 | v2: `moist_cv` and `q_con`, the non-MOIST_CAPPA branch, FATAL where a bit cannot act. At noise against v1 in p8 | dycred, fv3tally |
| `dry_tracer_ic` v3 | under nesting the parent sent c/(1 − Σw) as the first boundary condition; fixed in v4 | trdyn round 2 |
| Water proposal E.1: no fix proposed (a limiter cuts cyclone spray tenfold) | the backward-Euler option E1 is proposed, behind `nst_spray_opt` | canopy |
| Water proposal E.5: global precipitation +8.6 % with the GF candidate | the final `gf_closure` gives +8.9 % (+1.9 × 10⁻⁶ kg/m²/s) in suites' patch table; the same report's §5 text still says +8.6 % (+1.85 × 10⁻⁶). We cite +8.9 % | suites |

**Discrepancies between sources, not resolved here.**
- **S1K and TFH closures.** energy's patch table gives deep 5 × 10⁻¹⁴, shallow 1 × 10⁻¹⁴ (S1K) and Thompson 5 × 10⁻¹³
  (TFH); its §9.3 gives 1 × 10⁻¹³, −6 × 10⁻¹⁵ and 9 × 10⁻¹³. All are round-off; the final-tree gaps are ≤ 1.2 × 10⁻¹²
  either way.
- **The `dyn_te_exact` diff.** energy §9.7 says `01_fv3-dyn_te_exact.diff` on Hercules differed from `.v2.diff` when
  it integrated, and used `.v2`. The two local copies are now byte-identical (md5 ddc59580…).
- **The control fixer.** fv3tally's all-off control gives −0.5689 W/m², energy's ctl64 −0.5701.

## 15. Decisions

Decided 18 October 2026: every recommendation is adopted. Physics-change and numerical-consistency switches default
to off; the recommended setting is the one used in the all-on runs. Items 1, 5 and 6 are built and verified in `full14`.

| # | Item | Decided setting | Basis | Source |
|---|---|---|---|---|
| 1 | TH9 | BUG FIX, unconditional, one diff with TH8, cut on `fx` | section 5; TH8 + TH9 with stock fwet at f24: +0.2 % | canopy |
| 2 | `noahmp_fwet_opt` (E2) | default 0 (stock), for the Noah-MP owners to change; option 2 recommended | section 6; the one land signal well beyond noise | canopy, energy §9.7 |
| 3 | `gf_closure` | opt-in, default off; the owners judge the precipitation change | section 10; unfixed, GF loses 30 % of its own precipitation | suites |
| 4 | `mynn_mix_sl` | PHYSICS CHANGE, opt-in, default off | section 10 | suites |
| 5 | PL1 | folded into `sfc_precip_enthalpy` | section 6 | preclag |
| 6 | NM10r | PHYSICS CHANGE, unconditional; adopted as revised water diff 17r (ensfc2 12) | section 6 | ensfc2 |
| 7 | `dspheat_ke` and the other physics-change defaults | all default off. Also open: whether `dspfac` should be ignored when `dspheat_ke` is on | sections 3–6. Every other energy switch alone is at noise (TFH, PBK, C8, D7S, S1: rms 0.143–0.161 K vs 0.149), except `gwd_ke_heat`, `ngw_heat_opt`, `noahmp_canopy_heat` 2, `noahmp_sw_radshare` and `lw_sfc_return` | energy, enpbl, ensfc2 |
| 8 | `ngw_heat_opt` | option 2 (default 0) | section 4; 83 % of the NGW heating is at 500–200 hPa; option 2 leaves the stratosphere unchanged | encnv, TRACKER |
| 9 | `cpl_water_energy`, including the flow-work bit 2 | PHYSICS CHANGE, opt-in, default 0 | section 1; the largest systematic signal of the all-on set. A forecast improvement is not shown; there is no real-model column test | fwred |
| 10 | `tend_opt` option 4 | CCPP error (clean abort in 25–112 s), not a warning | section 8; option 4 discards R, P or G with no scheme applying them; for PBL the surface fluxes leave the surface and never reach the air. A warning would keep 4 as a deliberate switch-off | latent |
| 11 | `dry_tracer_ic` | opt-in, default off; set per run to match the IC files | section 7; advection alone moves a structured GHG field 0.056 ppm rms | trdyn |
| 12 | MPAS 0012 and 0014 | both opt-in: 0012 default `'stock'`, 0014 default 0, option 2 recommended | section 11 | mpas |
| 13 | MYNN 01b | BUG FIX, unconditional | section 10 | suites, mynnred |
| 14 | `dyn_te_exact` | 31 (the bug-fix bits; default 0); 127 adds the design options | section 1 | fv3tally |
| 15 | T1 sub-stepping of o3 and TKE | included (decided 17 October) | section 4 | trsamf, trred |
| 16 | E1 `nst_spray_opt` | stays in the proposal: opt-in, default 0, option 1 | section 6 | canopy |

## References

- Boville, B. A., and C. S. Bretherton, 2003: Heating and kinetic energy dissipation in the NCAR Community Atmosphere
  Model. J. Climate, 16, 3877–3887, doi:10.1175/1520-0442(2003)016<3877:HAKEDI>2.0.CO;2.
- Harris, L., et al., 2021: A scientific description of the GFDL finite-volume cubed-sphere dynamical core. NOAA Tech.
  Memo. OAR GFDL 2021-001 (the `d_con` heating equation, cited by dycred).
- He, C., et al., 2023: Modernizing the open-source community Noah with multi-parameterization options (Noah-MP)
  land surface model (version 5.0). GMD, 16, 5131–5151, doi:10.5194/gmd-16-5131-2023.
- Lauritzen, P. H., et al., 2018: NCAR release of CAM-SE in CESM2.0. JAMES, 10, 1537–1570, doi:10.1029/2017MS001257.
- Lauritzen, P. H., and D. L. Williamson, 2019: JAMES, 11, 1309–1328, doi:10.1029/2018MS001549.
- Lauritzen, P. H., et al., 2022: JAMES, 14, e2022MS003117, doi:10.1029/2022MS003117 (thermodynamics and conservation
  in Earth system models; §4.5.2, the c_p/c_v rescaling).
- Makarieva, A. M., et al., 2013: The key physical parameters governing frictional dissipation in a precipitating
  atmosphere. J. Atmos. Sci., 70, 2916–2929, doi:10.1175/JAS-D-12-0231.1.
- Niu, G.-Y., et al., 2011: The community Noah land surface model with multiparameterization options (Noah-MP): 1.
  J. Geophys. Res., 116, D12109, doi:10.1029/2010JD015139.
- Pauluis, O., V. Balaji, and I. M. Held, 2000: Frictional dissipation in a precipitating atmosphere. J. Atmos. Sci.,
  57, 989–994, doi:10.1175/1520-0469(2000)057<0989:FDIAPA>2.0.CO;2.
- Skamarock, W. C., et al., 2012: A multiscale nonhydrostatic atmospheric model using centroidal Voronoi tesselations
  and C-grid staggering. Mon. Wea. Rev., 140, 3090–3105, doi:10.1175/MWR-D-11-00215.1.
- Water closure proposal: `proposal/water_closure_proposal.md` (15 October 2026), diffs 01–19 + 09b.

The DOIs of He, Lauritzen, Makarieva, Niu, Pauluis and Skamarock are as checked in
`proposal/patches/ports/references.md` (record or abstract level). Harris et al. (2021) is cited as in the water
proposal. Boville and Bretherton (2003) and the Pauluis et al. (2000) title, volume and pages were checked against
citing records on 18 October 2026.
