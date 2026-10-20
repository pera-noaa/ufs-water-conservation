# canopy: E.2 (Noah-MP canopy wetted fraction), TH8/TH9, E.1 (NSST sea spray) as switch-guarded fixes

## Status

All four canopy diffs are in the final series. No red team reviewed this workstream.

| SERIES row | Fix (canopy diff) | Class | Switch: default / all-on | Before → after |
|---|---|---|---|---|
| 42 `42_E2.diff` | Noah-MP canopy wetted fraction (`01`, rebased) | BF, switched | `noahmp_fwet_opt` 0 / 2; option 2 recommended | land canopy evaporation +21.6 % at f24, +35.5 % 0–24 h mean (opt 2, TH8+TH9); global T rms f24 0.159 vs noise 0.139 |
| 16 `16_TH8.diff` | Thompson sedimented precipitation reaches the surface (energy `06` = canopy `02`) | BF | — | TH8 off → on: Thompson water −7.0e-12 → −2.6e-20 kg m-2 s-1; residual +2.3e-6 → −2.1e-12 W m-2 |
| 43 `43_TH9.diff` | Thompson sedimentation actual (`03`) | BF | — (unconditional in `full14`: one diff with TH8, `energy/patches/13_ccpp-thompson_TH8-TH9_unconditional.diff`, cut on fx) | canopy evaporation f06, E2 off: −68.3 % (TH8 alone) → −2.9 % (TH8+TH9); `full14` gates bitwise |
| 44 `44_E1.diff` | NSST sea spray, backward Euler (`04`) | PC | `nst_spray_opt` 0 / 1 | oscillating cells 2 → 0 (24 h), 271 → 2 (10 d); global LH −0.27 (f06), −0.21 (f24) W m-2 |

- TH8 never ships without TH9: alone it is far beyond noise over land.
- The proposal's candidate E.2 diff shadows the module's `cwat`; `01` (row 42) does not.
- Gates, all switches on: restart, 3x8 vs 4x6, and both together, bitwise. All switches off = full10, bitwise (`-no-fma`).
- Open: no tropical cyclone forms on develop, so v1's day-6.4 runaway is not reproduced; `sfc_ocean.F` and the NOAA-EMC/noahmp copy are compile-checked only.

## Current answers

## E.2 Noah-MP canopy wetted fraction (`01_E2_noahmp_fwet_opt.diff`, `noahmp_fwet_opt`, default 0)

**Cause (code).** `fwet` is "wetted or snowed fraction of the canopy" (declaration). precip_heat computes it after
interception (it drives this step's fluxes), canwater after evaporation (it drives the melt/freeze tv reset):
`if (canice > 0) fwet = canice/maxsno else fwet = canliq/maxliq; fwet = min(fwet,1)**0.667`. Its consumers:
- vege_flux: wet-leaf evaporation conductance `cew = min(fwet, canliq*latheav/dt/evpot)*vaie/rb` with the reservoir chosen
  by `tv > tfrz` (liquid) or not (ice), and transpiration from the dry part `ctw = (1-fwet)*(...)`;
- twostream: snow optics weighted by fwet only when `tv <= tfrz`.
The phase is therefore chosen by tv everywhere except in fwet, where any ice wins. maxsno = 6.6(0.27+46/bdfall)(LAI+SAI)
is ~50x maxliq, so a trace of ice gives fwet ~ 0 while the leaves hold liquid: at tv > tfrz the liquid cannot evaporate
(cew -> 0) and the full canopy transpires as if dry. The single-phase logic assumed canice > 0 means a frozen canopy; Noah-MP
holds both phases routinely (rain intercepted onto a canopy with snow; ice melts at a capped rate). NCAR Noah-MP v5
`CanopyHydrologyMod.F90` (L104-108) already changed its copy to use ice only when `CanopyIce >= CanopyLiqWater`, while
`CanopyWaterInterceptMod.F90` (L132-137, the copy that feeds the energy fluxes) keeps the stock switch: upstream recognises
the inconsistency but fixed it only where it does not reach the fluxes.

**Fix.** One function `canopy_wetfrac`, called in both places only when `noahmp_fwet_opt /= 0` (stock lines untouched:
bitwise when 0). 1 = each phase's fill fraction (each capped at 1) weighted by its mass (the proposal's candidate);
2 = the larger fill fraction; 3 = the phase with more mass (v5's CanopyHydrologyMod rule, in both places). For a
single-phase canopy all options equal stock. The NOAA-EMC/noahmp copy (`NOAHMP-interface/noahmp/src`) has the same two
blocks: same edit, module default 0 plus a public setter `noahmp_options_fwet` (no land-component namelist plumbing).
The glacier module has no canopy.

## Runs (24 h, control_p8_ugwpv1 C96L127, dt 720, all final9 switches; -no-fma n0/b1; `$C/runs`)

Noise = p0c - p0 (full10, consv_te 0.999). Land statistics over land==1 cells; `_ave` fields are the 6 h bucket ending at fh.
Logs: `logs/analysis1.txt` (tool `tools/impact.py`, driver `tools/analyze1.sh`).

| gate | runs | result |
|---|---|---|
| all three switches off + TEST hook + spray meter = full10 | q0 vs p0 (n0), -no-fma both | BITWISE 0/2374 (f24 and f06) |
| the gate can fail | q0 vs qF1 | DIFFER 1715/2374 |
| compile: sfc_ocean.F (E1) and NOAA-EMC/noahmp copy (E2), not in any ATM build | job chk (b1 flags/modules) | 0 errors each (stock EMC file also 0) |

### Closure with the switches on

| meter | run | result |
|---|---|---|
| energy frame F + water (mq10 + 01 03 04, FMA) | mF0 (mine off) | water: Thompson -2.6e-20, PBL +4.5e-21 kg m-2 s-1; residual net of declared -2.1e-12 W m-2 (= energy's full9) |
| | mALL (E2 opt1 + TH9 + E1) | water: Thompson -2.3e-20, PBL -2.7e-21; residual +1.6e-11; per-segment gaps PBL 3.2e-13, SAMF <=1e-13, Thompson 1.7e-3 (the known PH1 convention item); surface hand-off (declared) 0.181 -> 0.155 |
| | mT8F1 (TH8 off, E2 opt1) - the meter can fail | Thompson water -7.0e-12 (the TH8 leak), residual +2.3e-6 (= hfus x leak) |
| ensfc2 surface (mopt6 tree + 01, -no-fma) | sF0 (E2 off) = ensfc2's e4MA4 | BITWISE 0/2374 (tree copy valid; E2 off inert on that tree too) |
| | CH1: sF0 / sF1 (E2 opt1) | canopy R_S -3.1e-17 / -3.4e-17; soil R_final4 +2.6e-5 / +2.2e-5 (ensfc2's known remainder) |
| | CH2: sF0c2 / sF2c2 (E2 opt1) | storage-frame R_S -1.2e-15 / +5.8e-16; canwater tv change 0 in both |

- E2 raises the canopy heat "charged but not carried" (evaporation the canopy water could not supply, returned by CMC)
  from 0.022 to 0.059 W m-2: more of the canopy evaporation now hits the cap (the proposal's open point on the cap,
  section 7). It is booked and closes; it does not add a residual.

### With E2 on: noise and rms (logs/analysis2.txt). Noise = same switches with consv_te 0.999.

f06 rms of the difference (land cells), W m-2; ratio to that option's noise in brackets. Means are all within noise.

| comparison | evcw rms | sbsno rms | land LH rms | evcw mean % | sbsno mean % |
|---|---|---|---|---|---|
| noise, E2 opt1 (qF1c-qF1) | 0.187 | 0.029 | 0.219 | -0.002 | +0.009 |
| noise, E2 opt2 (qF2c-qF2) | 0.254 | 0.034 | 0.288 | -0.011 | +0.011 |
| TH8 alone, opt1 | 0.423 (2.3x) | 0.071 (2.5x) | 0.210 (1.0x) | +0.022 | -0.039 |
| TH8 alone, opt2 | 0.248 (1.0x) | 0.058 (1.7x) | 0.212 (0.7x) | +0.014 | -0.017 |
| TH8+TH9, opt1 | 0.179 (1.0x) | 0.031 (1.1x) | 0.231 (1.1x) | +0.012 | +0.001 |
| TH8+TH9, opt2 | 0.121 (0.5x) | 0.019 (0.6x) | 0.184 (0.6x) | +0.001 | -0.001 |

At f24 every TH8 / TH8+TH9 row is within noise (evcw rms 1.47-1.60 vs noise 1.44-1.47; T rms 0.139-0.143 vs 0.139-0.144).

**Verdict on TH9.** With E2, TH8 + TH9 is at noise from the first 6 h on (the proposal's claim holds); TH8 without TH9
leaves first-6-h rms 1.7-2.5x noise in snow sublimation (and 2.3x in canopy evaporation with opt1). TH9 is still needed:
it is also a code-level fix in its own right (flux-form sedimentation moves the R1 placeholder, which is not mass; with TH8
that becomes booked fake precipitation, water closing only because the tendency removes mass that is not there).
TH8 must never ship alone: without TH9 or E2 it is far beyond noise over land (table above).

### E2 forecast impact (its own; TH8 off, or TH8+TH9 on), mean % (f06 | f24)

| option | evcw | trans | sbsno | land LH | t2m (K) | global T rms f24 (noise 0.139) |
|---|---|---|---|---|---|---|
| opt1, TH8 off | +43.1 / +17.2 | -3.1 / -0.5 | -20.9 / -0.8 | +2.7 / +0.6 | -0.033 / -0.016 | 0.153 |
| opt2, TH8 off | +47.6 / +21.1 | -3.2 / -1.0 | -22.8 / -2.2 | +2.1 / +0.7 | -0.044 / -0.024 | 0.155 |
| opt1, TH8+TH9 | +47.5 / +17.0 | -3.4 / -0.1 | -21.9 / -0.6 | +2.9 / +1.0 | -0.034 / -0.013 | 0.157 |
| opt2, TH8+TH9 | +52.0 / +21.6 | -3.5 / -0.6 | -23.8 / -2.1 | +2.3 / +0.9 | -0.045 / -0.023 | 0.159 |

Beyond noise over land (canopy evaporation, sublimation, land LH), small in the global T rms. Same order as the proposal's
candidate measurement (canopy evaporation +20 %, sublimation -14 %), whose t2m -0.09 K was larger; that run also carried
the `cwat` shadowing defect described in the status block.

## E.1 NSST sea spray (`04_E1_nst_spray_implicit.diff`, `nst_spray_opt`, default 0)

**Cause.** `sfc_nst.f90` (and `sfc_ocean.F`, same block) adds `evaps = ca*(qs(t1) - q1)` (ca = conlf ws10^5.4 ru10 bb1
rho hvap) to the latent flux and `bets*cb*(tskin - t1) - (alps-gams)*evaps` to the sensible flux, from the state at the
start of the step; the PBL then applies them as fixed fluxes for the whole step. Per unit lowest-layer mass the spray
alone is a linear relaxation of (t1, q1) with Jacobian x dt
`[[at(bets cb + p ca s), -at p ca], [-aq alps ca s, aq alps ca]]` (at = dt g/(cp dp1), aq = dt g/(hvap dp1),
p = alps - gams, s = dqs/dt1). Forward Euler is unstable when its largest eigenvalue lam > 2 (2dt oscillation).
The meter (`tools/apply_spraymeter.py`, print-only) reports lam per open-water cell.

**Fix.** `nst_spray_opt = 1`: backward Euler of that 2x2 system (qs linearised in t1), i.e. the fluxes of the lowest
layer's end-of-step state under the spray alone; det = 1 + ... > 0 always, so it is unconditionally stable and monotone.
It is a single flux pair handed to the host exactly as before, so the atmosphere receives exactly what is reported
(water and energy exchange conserved by construction; NSST's skin budget never saw the spray, unchanged). New scheme
arguments: `nst_spray_opt`, `prsi` (lowest-layer mass), `con_g`; sfc_ocean also `timestep` (timestep_for_physics).

**Reproduction on current code (full10 + switches, -no-fma; `tools/spr.py`; oscillating = T1 flips sign of its step change
>= 3 steps in a row, each > 0.5 K).** No tropical cyclone forms in 10 days from 2021-03-22 06Z on develop (v1's day-6.4
storm at 73E 12S does not appear; the v1 step-700 restart was deleted). The strongest winds are extratropical storms at
the 30 m/s spray cap, and those oscillate:

| run | cell-steps lam>2 / >5, max lam | oscillating cells | largest dT1 per step | longest flip run | spray latent used / explicit (lam>2) |
|---|---|---|---|---|---|
| 24 h, dt 720, explicit (q0) | 12437 / 707, 13.1 | 2 | 0.96 K | 8 | 1 |
| 24 h, dt 720, implicit (qS1) | 12795 / 736, 13.1 | **0** | - | - | 0.26 |
| 10 d, dt 720, explicit (t10_0) | 118049 / 14201, 17.8 | 271 | 2.68 K | 21 (240E 56S, ws10 30) | 1 |
| 10 d, dt 720, implicit (t10_S1) | 125334 / 15435, 17.4 | 2 (lam 4.7, 11.6) | 0.89 K | 3 | 0.23 |
| 24 h, dt 1440, explicit (d2_0) | 22734 / 4122, 31.1 | 177 | **17.7 K** | 8 | 1 |
| 24 h, dt 1440, implicit (d2_S1) | 23410 / 4325, 31.4 | 10 | 5.0 K | 14 (lam 1.9) | 0.22 |
| 24 h, dt 720, spray off (q_ns, background) | (same cells) | 0 | - | - | - |
| 24 h, dt 1440, spray off (d2_ns, background) | (same cells) | 7 | 3.9 K | 3 | - |

- The 10 cells left in d2_S1 are the same Kamchatka/Okhotsk cluster (149-163E, 51-57N) that oscillates with spray OFF
  at dt 1440 (7 cells, 3.9 K): a non-spray background at the doubled step. Everything spray-driven is gone.
- Instrumentation passive: d2b_0 (b2 = b1 + spray-off meter) vs d2_0 BITWISE; q0 (b1, meter) vs p0 BITWISE.

**24 h impact, qS1 - q0 (noise p0c - p0):** global LH mean -0.27 W m-2 at f06 (noise +0.0004, rms 1.69 vs 0.12),
-0.21 at f24 (noise -0.03; rms 3.33 vs 3.06); open-water LH -0.35 % / -0.29 %; global T rms 0.147 K vs 0.139; ps rms
7.9 vs 7.6 Pa; land within noise. For scale, spray on vs off (q0 - q_ns) is +1.47 / +1.08 W m-2 global LH: the implicit
form delivers about 81 % of the explicit form's spray latent flux globally, and 23-26 % of it in the cells where the
explicit form is unstable (lam > 2), where the explicit flux overshoots the layer's own equilibrium.

**Class: NUMERICAL STABILITY, a PHYSICS CHANGE by the bar** (the spray actually delivered changes beyond noise in
open-water LH). The lowest layer is the reservoir the scheme hands its flux to, so any monotone lowest-layer treatment must
cut the flux to ~1/(1+lam) where lam is large (the proposal's limiter, ~1/lam, was rejected for that); a solve coupled to
the PBL's implicit diffusion would cut less and is the owners' alternative. Default off.

## Gates for all three switches on (b1; all final9 switches + noahmp_fwet_opt 2 + thompson_sed_actual + nst_spray_opt 1)

| gate | runs | result |
|---|---|---|
| restart (12 h + 12 h) | rsA_S vs rsA_R | BITWISE 0/2374 (incl. RESTART files) |
| layout 3x8 vs 4x6 | rsA_S vs rsL_S | BITWISE 0/3452 |
| layout + restart | rsA_S vs rsL_R | BITWISE 0/2374 |
| switches off | q0 vs p0 | BITWISE 0/2374 |

## Reconciliation with the issue draft's larger-fraction numbers (`tools/imp24.py`, land==1)

- The earlier run is `$U/rt/wb_ph_nm2o19` (tree `$U/patched18nm2o19`, exe md5 c187bebc) vs `wb_ph_nm2`. Its fwet edit is a
  clean `max(...)` in both places, with no new local and **no shadowing defect**. But nm2 -> nm2o19 also adds NM10's
  convective-phase block. The fwet-only pair is nm2o1 -> nm2o19, and it gives nearly the same numbers.
- The quoted numbers are **0-24 h means of the four 6 h buckets**, not the 18-24 h bucket (my tables). Recomputed:
  canopy evap +19.1 %, sublimation -13.0 %, land LH -0.44 % (-1.56 % at the f24 bucket), T2m -0.087 K (-0.111 K at f24),
  q2m -0.54 % (-0.83 % at f24). Noise there (wb_ph_ctl_ulp1): -0.29 %, +0.04 %, -0.06 %, +0.000 K, -0.01 %.
- The opposite sign of land LH and q2m (and the small T2m) on full10 is the **base**, not a defect or a window. That run
  was patched18 with stock land/energy options. full10 runs all final9 switches, among them noahmp_canopy_heat 1, the SW/LW
  hand-offs and noahmp_kirchhoff. One check: opt 2 on the full10 exe with all those switches off (z0 -> zF2; TH8 on, TH9 off)
  gives T2m -0.145 K, canopy evap +225 % (TH8's trace ice) and land LH +2.1 % (0-24 h). The switch set damps the T2m response.

Replacement numbers, 0-24 h land means (f24 instant/bucket in brackets), base full10 + all final9 switches + TH8 + TH9:

| | canopy evap | sublimation | land LH | land T2m | land q2m |
|---|---|---|---|---|---|
| opt 1 | +32.1 % (+17.0) | -12.0 % (-0.6) | +1.47 % (+0.96) | -0.018 K (-0.013) | +0.19 % (+0.21) |
| opt 2 | +35.5 % (+21.6) | -14.0 % (-2.1) | +1.23 % (+0.94) | -0.030 K (-0.023) | +0.18 % (+0.22) |
| noise, opt 1 base | +0.07 % (+0.60) | +0.05 % (+0.04) | -0.03 % (-0.07) | +0.001 K (+0.002) | +0.00 % (+0.01) |
| noise, opt 2 base | -0.13 % (+0.08) | +0.05 % (-0.02) | -0.04 % (-0.16) | -0.000 K (+0.000) | -0.01 % (-0.02) |

With TH8 off instead (no TH9), opt 1: +30.1 / -11.8 / +1.27 / -0.020 K / +0.17; opt 2: +33.3 / -13.7 / +1.07 / -0.031 K / +0.16.

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| canopy: E.2 (Noah-MP canopy wetted fraction), TH8/TH9, E.1 (NSST sea spray) as switch-guarded fixes | title | current (same title in the head) | `report.md`, `report.history.md` |
| Status (18 Oct 2026, done) | outcome summary as written | superseded by `## Status` | `report.history.md` |
| E.2 Noah-MP canopy wetted fraction (`01_E2_noahmp_fwet_opt.diff`, `noahmp_fwet_opt`, default 0) | E.2 cause and fix | current | `report.md` |
| Runs (24 h, control_p8_ugwpv1 C96L127, dt 720, all final9 switches; -no-fma n0/b1; `$C/runs`) | run setup, noise, off gate | current | `report.md` |
| Land impact, mean difference in % of the control mean (f06 \| f24); noise in the first row | TH8 alone vs TH8+TH9; E2 options on full10 | current (evidence for TH9; outcome in `## Status`) | `report.history.md` |
| Closure with the switches on | water and energy meters | current | `report.md` |
| With E2 on: noise and rms (logs/analysis2.txt). Noise = same switches with consv_te 0.999. | TH9 verdict | current | `report.md` |
| E2 forecast impact (its own; TH8 off, or TH8+TH9 on), mean % (f06 \| f24) | E2 impact at f06/f24 | current | `report.md` |
| E.1 NSST sea spray (`04_E1_nst_spray_implicit.diff`, `nst_spray_opt`, default 0) | E.1 cause, fix, reproduction, impact | current | `report.md` |
| Gates for all three switches on (b1; all final9 switches + noahmp_fwet_opt 2 + thompson_sed_actual + nst_spray_opt 1) | restart, layout, off gates | current | `report.md` |
| TH8 / TH9 diffs on full10 | TH8/TH9 diffs; TH9 behind a switch | superseded by `## Status` (TH9 unconditional, `full14`) | `report.history.md` |
| Files | patches, tools, Hercules trees, disk | archival | `report.history.md` |
| Reconciliation with the issue draft's larger-fraction numbers (`tools/imp24.py`, land==1) | 0–24 h replacement numbers | current | `report.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
