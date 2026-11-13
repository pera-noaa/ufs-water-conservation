*History of `report.md` (ensfc2), moved verbatim on 18 October 2026. The head is `report.md`.*

# ensfc2: surface energy closure, round 3 (clean bug-fix diffs, namelist options, full closure)

## Status (18 Oct 2026, round 4 done)

- Diffs on energy/fx, in order: 04-06, 08-11 (round 3, with the integrator), NM12 (water diff 20), 13_sfc_SL2, 14_sfc_CS1, 15_sfc_CB1 (bug fixes), 16_sfc_options_r4 (EP1, LW2, AIR1, glacier EV1, PH1 at L_f(T1)). 12_sfc_NM10r is for Ash to decide.
- Final closure (e5MA2, everything on with LW2): every surface term is at round-off or is a declared frame item. Soil total is 4.3e-8 W m-2, all of it at kdt = 1 (initial state); later steps are ~1e-10 per step (absolute-heat differencing). Glacier 6e-16; sea ice 1e-13; hand-off terms ≤ 5e-14 (table in "Round 4 final closure").
- Gates, all BITWISE with -no-fma: switches off = bug-fix build; bug fixes under restart and 3x8/4x6 layout; all switches on (LW2) under restart and layout.
- Recommendation: LW2 over LW1. Land t2m -0.03 K vs +0.21 K; global T rms 0.176 vs 0.201.
- Builds: bfx5n (bug fixes), opt5n (options), mopt10 (metered; exe fv3_e2_mopt12/13/14 add debug meters). Runs: e5*. Closure tools: es2_check.py, gl.py, perstep.py.
- Round 3 status and tables follow; round-4 sections are at the end.

## Gates (all builds -no-fma; `tools/bitcmp.py`: every variable of atmf024/sfcf024 x 6 tiles + 24 h RESTART files, 2374 variables)

| gate | runs | result |
|---|---|---|
| options off = no option code | e2O0, e2O0c, e2O0d (each options build, defaults) vs e2B0 (bfxn) | BITWISE 0/2374 (all three) |
| restart, bug-fix build | e2B0 vs e2BR_R (12 h + warm start + 12 h) | BITWISE |
| layout, bug-fix build | e2B0 (3x8) vs e2BL (4x6) | BITWISE |
| restart, all options on | e2OAR_S vs e2OAR_R; and e2OA4 vs e2OAR_S | BITWISE, BITWISE |

## Bug fixes: closure (metered e2MO0 = bug fixes + D3A, switches off) and impact (e2B0 vs e2F0, both -no-fma)

Noise = ctlc999 - ctl64 (energy/runs): global T rms 0.149 K; land t2m -0.003/0.238 K (mean/rms), LH 4.3, SH 3.5 W m-2 rms; icetk 8e-5 m rms; weasd ice 0.05.

| fix | term | closure | impact (B0 - F0) |
|---|---|---|---|
| QR1 | NSST qrain | 0.300 -> 0.417 W m-2, exactly x1000/720 (round 2, same arithmetic) | NSST-internal, noise |
| CMC | canopy charged - carried 0.0148 | returned to soil; soil latent identity leaves only canopy melt latent (-0.0205, now soil heat) + meter NM11 over-count (see remaining) | soilt1 land +0.010 K mean (noise -0.003; rms 0.21 vs 0.18) |
| FL1 | ice3lay -7.87e-3 | -1.15e-13 | icetk rms 1.7e-3 m (noise 8e-5) with SI1; weasd ice rms 0.10 (0.05) |
| SI1 SI2 NP1 | as round 1 | as round 1 | |
| all six | | | T rms 0.158 K; every other surface field within noise |

## Options: closure in the all-on metered run e2MOA4 (W m-2 global, 119 steps)

| item | stock term | with option | closure check |
|---|---|---|---|
| CH1 | -canhs 0.0523 | R_S -2.6e-17 | |
| CH2 (e2MOB4) | massless-frame R_S = -canhs = -0.508 (canopy storage) | storage-frame R_S -2.2e-16; canwater tv change 0 | |
| PH1+PH2+PH3 | surfaces take hfus x 0.0049 (soil) + 3.3e-4 (glacier) more frozen than the host | soil received = srflag P to 1.3e-13; glacier 0; PH1 heating = hfus x host convective snow 0.07254 exactly | SAMF residuals = their KE term only (deep -0.11961 = dK, shallow -0.028963 = dK), so D3a pays only detrained ice; PH1 appears only in the MP segment |
| SW1 | landfrac=1 cells fsa - atm -0.093 | -6.3e-3 in cells with landfrac >= 0.999 (meter set); 0 by construction where landfrac = 1 (1361 of 7570 such cells have 0.999 <= landfrac < 1 and use the mixed rule) | soil fsa 39.422 vs A 39.403 |
| LW1 | radiation-time vs booked net LW | heating applied +0.03606 = booked - radiation (8e-14) | surface-loop segment r = LW1 + EV1 = 0.16152 exactly |
| EV1 | frame-F evaporation enthalpy (soil) +0.1255 | applied = booked (2.8e-17) | |
| AD1 | soilwater internal +0.0582 (MO0: inter-layer +0.0491, infiltration source T -0.0091) | soilwater+groundwater after booking boundary water at its T: -1.2e-14 | bottom imbalance 1e-20 kg |
| KF1 | R_E +0.2002 | 2.8e-8 | |
| aquifer | +10.20 | booked at bottom-layer T; the round-2 remainder 2.4e-3 = pore air (Noah-MP cpair*(smcmax-smc), cpair used as J m-3 K-1) displaced by aquifer water: -2.448510e-3 vs -2.448510e-3 (1.9e-14, e2MO0) | |
| FL1/SI1 | ice3lay | -1.14e-13 | |

## Options: forecast impact, each switch alone vs e2O0c (24 h, land = land==1, mean/rms), noise = ctlc999 - ctl64

| run | global T rms (K) | land t2m | land SH | land LH | land uSW | other | class / verdict |
|---|---|---|---|---|---|---|---|
| noise | 0.149 | -0.003/0.238 | -0.06/3.45 | -0.06/4.30 | -0.03/2.10 | soilt1 -0.003/0.18 | |
| CH1 | 0.161 | -0.015/0.310 | +0.10/4.04 | -0.04/4.72 | +0.01/2.40 | uLW -0.11 | DESIGN DEFECT, minimal consistency; slightly beyond noise over land |
| CH2 | 0.254 | +0.270/1.221 | -3.61/18.7 | -0.41/13.1 | +0.29/5.40 | uLW +1.60 | PHYSICS CHANGE, large |
| PH | 0.149 | +0.016/0.294 | -0.03/3.85 | +0.05/4.88 | -0.02/2.70 | | PHYSICS (missing term); noise |
| SW1 | 0.175 | +0.042/0.523 | +0.04/5.90 | -0.06/5.81 | -0.78/12.1 | tsfc rms 1.0 | NUMERICAL CONSISTENCY; beyond noise |
| LW1 | 0.199 | +0.214/0.741 | -0.59/6.04 | +0.10/6.65 | +0.04/3.85 | | NUMERICAL CONSISTENCY; beyond noise (all the LW the surface emits beyond the radiation's assumption goes into one layer; a Jacobian spread over the column and TOA, as RRTMGP use_LW_jacobian, would be gentler) |
| EV1 | 0.159 | +0.031/0.300 | -0.05/4.31 | +0.09/5.15 | +0.05/2.50 | | PHYSICS (frame F, missing term); slightly beyond noise |
| AD1 | 0.148 | +0.001/0.255 | -0.02/3.71 | -0.05/4.32 | +0.03/2.11 | soilt1 -0.010/0.23 | PHYSICS (missing term); noise |
| KF1 | 0.147 | +0.005/0.249 | +0.04/3.86 | +0.05/4.72 | +0.03/2.09 | soilt1 -0.014/0.19 | PHYSICS trade-off (changes cold-soil freezing heat by (c_w-c_i)(T-tfrz)/hfus, 6 % at -10 C); noise in 24 h |
| all (CH1) e2OA4 | 0.212 (mean +3.6e-3) | +0.260/0.878 | -0.75/7.12 | +0.03/7.54 | -0.81/12.0 | | dominated by LW1 and SW1 |

## Remaining, not at round-off

| item | W m-2 | why |
|---|---|---|
| Noah-MP soil after all booking (e2MOA4/5) | +3.9e-4 | -0.0227 before = canopy melt/freeze latent CMC returns as soil heat (-0.02069, internal; the es_table B counts lheat as a boundary flux) + the meter booking frozen-ground evaporation as ice where NM11 took liquid (+0.00243, meter artefact). The +3.9e-4 left sits in the snowwater segment: snow-layer combination/removal (round-2 SL1, 3e-4) and layerless snow moved to soil ice at T1. The snowh2o sice<0 path (liquid sublimated at hsub with nothing returned) did not fire (2.5e-23) |
| precipitation stored in snow layers at layer T | -0.0108 | booked here as an import at the layer T; frame F's PAH assumes tg, so the hand-off of precipitation enthalpy (PAH constants, clip, canopy) is still booking, as round 2 §7 |
| glacier | +0.0074 | sensible heat of cold ice exported by the NM9 glacier flow; book with the runoff at its T |
| land-SW in 0.999 <= landfrac < 1 cells | -6.3e-3 | those cells use the radiation-time land share; the open-water remainder takes the difference by the F_ocn definition |
| LH, mixed (icy) cells | +0.065 | NSST books its own lead fluxes; the atmosphere gets sfc_sice's; open boundary, F_ocn uses the atmosphere side |
| KF1 | 2.8e-8 | small; not chased |
