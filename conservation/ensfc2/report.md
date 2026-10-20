# ensfc2: surface energy closure, round 3 (clean bug-fix diffs, namelist options, full closure)

## Status

- Every surface bug fix is in the final series (`replay/SERIES.md`); ensfc's diffs travel as this directory's copies:

| SERIES row | Diff here | Items | Class | Switch: default / all-on |
|---|---|---|---|---|
| 31–36 | 04–06, 08–10 | SI1, SI2, NP1 (ensfc), QR1, CMC, FL1 | BF | — |
| 37 | 11 (`37_sfc_options_r3`) | CH1/CH2, PH1–3, SW1, LW1, EV1, AD1, KF1 | PC / NC | 7 switches, default off; all-on as manifest row 37 (LW2 replaces LW1) |
| 38–40 | 13 (rebased), 14, 15 | SL2, CS1, CB1 | BF | — |
| 41 | 16 as `16b` (one meta line fixed) | EP1, LW2, AIR1, EV1 glacier, PH1 at L_f(T1) | PC | `sfc_precip_enthalpy`, `lw_sfc_return`, `noahmp_pore_air` F / T |
| 12 | nm12's NM12 (SL2 needs it for context) | NM12 | BF | — |
| — | 12_sfc_NM10r | NM10r | — | adopted as water diff 17r (`energy/patches/water_17r/`); in `full14`: land frozen fraction = host to 1.2e-10 (NM10 2.5e-2), Noah-MP water 6.6e-13 mm, land means at noise (energy §9.9) |

| Closure, W m-2 (e5MA2) | Before round 4 | Final |
|---|---|---|
| Noah-MP soil / glacier | 3.9e-4 / +0.0074 | 4.33e-8 (3.56e-8 at kdt = 1) / 6e-16 |
| sea ice / aquifer | -1.1e-13 / 2.4e-3 | -1.1e-13 / 8.5e-15 (AIR1, e5MO02) |
| hand-off LW / EV / PH | | 5e-14 / 6e-17 / 1.5e-13 |

- Gates bitwise (-no-fma): options off = bug-fix build; restart and 3x8/4x6 layout for the bug fixes and for all-on (LW2).
- No red team. PL1 (row 46, `preclag/`) is the bug fix of EP1; `full14` folds it into `sfc_precip_enthalpy`.

## Current answers

## Option switches (gfs_physics_nml, all default off; `patches/11_sfc_options.diff`)

| switch | items |
|---|---|
| `noahmp_canopy_heat` = 0/1/2 | CH1 massless canopy / CH2 heat storage over the step (+ canwater keeps tv; melt latent to soil via CMC) |
| `precip_phase_host` | PH1 (GFS_MP_generic_post pays hfus for the host's convective snow, lowest layer, physics mass) + PH2 (Noah-MP soil takes that decision, from srflag) + PH3 (glacier frozen fraction = srflag) |
| `noahmp_sw_radshare` | SW1 soil + glacier: landfrac = 1 cells absorb the cell net SW (adjsfcnsw); other cells radiation-time land albedo x this step's band fluxes; twilight (Noah-MP fsa = 0) goes to the ground |
| `lw_sfc_consistent` | LW1: surfaces report booked upward LW (Noah-MP lwdn + fira; sea ice: its linearised non-solar flux less the SH and LH the atmosphere gets); composites_post heats the lowest layer by sum frac x (booked net up) - radiation-time net up. rrtmg_lw_post now also fills the radiation-time upward LW (RRTMGP already did) |
| `sfc_evap_enthalpy` | EV1: Noah-MP soil columns report E x [(latent charged - hvap) + land water content where it leaves + c_l(tfrz-T0) - cp_v(T1-T0)] (frame F), composites_post heats the lowest layer by txl x that |
| `noahmp_heat_advect` | AD1: soil water moved between layers carries c_w T_upstream (internal fluxes from per-layer mass change minus booked boundary flows); infiltration at its source T (rain tg, melt/drip tfrz, snow-bottom outflow at the bottom snow layer T); snow percolation carries the source layer T |
| `noahmp_kirchhoff` | KF1: phasechange heats the remainder into the layer at its new composition = L_f(T) = hfus + (c_w - c_i)(T - tfrz) with Noah-MP's own heat capacities |

## Precipitation phase: NM10 vs host (e2MO0, soil columns, 24 h)

- Convective precipitation on land: NM10's sfctmp < tfrz and the host's tsfc < 273.15 disagree in 5.0 % of land column-steps with convective precipitation (5.7 % in e2MOA4), 0.83 % of its mass.
- T1 says snow / host says rain: 2.30e-8 kg m-2 s-1; T1 rain / host snow: 8.5e-9; net extra frozen on land hfus x 1.45e-8 = 4.9e-3 W m-2 (= the soil frozen-receipt excess, exactly).
- `patches/12_sfc_NM10r.diff` makes Noah-MP take the host decision unconditionally (PH2 code without the switch). Whether to revise water diff 17: Ash decides; it needs the water closure re-verified.
- PH1 vs D3a: no double count. D3a pays hfus for SAMF condensate detrained as cloud ice (stays in the atmosphere; Thompson books it frozen later). PH1 pays for convective precipitation that leaves the column and that the host classifies as snow; that decision exists only in GFS_MP_generic_post, after SAMF, so PH1 stays there (moving it into SAMF would duplicate the tsfc rule in deep and shallow). Meter: with D3A + PH1, the SAMF segments' residual is exactly their KE term (latent closed), the PH1 heating is exactly hfus x host convective snow (0.07254 W m-2) and appears only in the MP segment, and the surfaces receive exactly srflag x P frozen.

## Frame F boundary definitions

- **Land evaporation (EV1).** Per kg evaporated the land loses (latent charged - hvap) + the water's content where it leaves (liquid c_w (T_layer - tfrz) for transpiration from layer k and soil evaporation from layer 1; ice c_i (T - tfrz) for snow/soil-ice sublimation, with the liquid deficit at c_w; canopy water at tfrz, i.e. 0) + c_l (tfrz - T0); the vapour carries hvap + cp_v (T1 - T0). The difference heats the lowest layer. Soil value +0.1255 W m-2 (e2MOA4). Round 2's +0.259 used the evaporating skin T (tv, tg); the land actually loses transpired water at the root-layer T, which is the right T for closure. Glacier columns not included (glacier E ~2e-9 kg m-2 s-1).
- **Ocean (prescribed SST, open boundary), per cell, W m-2, positive into the ocean:**
  F_ocn = SW_cell - txl fsa_land - txi sneti (SW remainder)
        - txo (adjsfculw_water - adjsfcdlw) (LW as booked; with LW1 the atmosphere receives exactly this, without LW1 use the radiation-time remainder -(sfculw - sfcdlw)_rad + txl netLW_land + txi netLW_ice)
        - SH_o - LH_o (open-water parts of the composite the PBL applies; in icy cells sfc_sice's lead fluxes)
        - E_o cp_v (T1 - T0) + P_liq,o c_l (T1 - T0) + P_froz,o (c_i (T1 - T0) - hfus) (water crossing at T1, frame F, relative to liquid at T0).
  The evaporation term E_o cp_v (T1 - T0) with E_o (T1 - T0) = 6.61e-4 kg m-2 s-1 K (round 2) is 1.22 W m-2 globally; with the LH it makes the ocean supply h_v(T1) per kg, so the global budget closes by definition. NSST's own f_nsol, qrain and warm-layer resets are internal to its diagnostic skin.

# Round 4 (18 Oct): every bug fixed, closure to round-off

Diffs (local `patches/`, Hercules `$S2/patches/`), applied in this order on energy/fx: 04-06, 08-11, NM12
(`20_NM12_noahmp_combine_melt_out.diff`, water series), 13, 14, 15, 16. The sequence reproduces the built trees
(checked against the chain). 13 needs NM12 (context); 14-16 apply on fx alone.

| diff | class | cause | fix |
|---|---|---|---|
| 13_sfc_SL2 | BUG FIX | combine: a thin layer merged by mass kept the receiver's T (its sensible heat lost/created); snow that stops being layered (melt-out, depth < 0.025 m) dropped its layers' sensible heat; truncated bulk snow and over-sublimated snow changed soil-1 ice at T1 | mix sensible heat into the receiver; give un-layered snow's heat to the top soil (glacier: top ice) layer; soil ice gained/lost at tfrz. Soil and glacier copies |
| 14_sfc_CS1 | BUG FIX | csnow: snow heat capacity from capped volume fractions (liquid beyond pore space, ice beyond solid density had none), so mass crossing the caps changed the layer heat | per-mass capacity cice/denice*snice + cwat/denh2o*snliq (fractions stay capped for porosity/conductivity). Located with a per-column breakdown: after SL2 every remaining column residual sat in the snowwater segment |
| 15_sfc_CB1 | BUG FIX | combo: cice, cwat (J m-3 K-1) used as per-kg capacities; branches set T = tfrz or dropped hfus*wliq without changing phase | per-kg capacities, one formula T = tfrz + (h - hfus wliq)/C; phasechange settles phases |
| 16_sfc_options_r4 | options | see below | |

Switches added (gfs_physics_nml, default off; off = bitwise, checked):

| switch | item | what |
|---|---|---|
| `sfc_precip_enthalpy` | EP1 (item 3) | precipitation lands with its frame-F enthalpy: per kg above its latent, c_l (T1 - tfrz) liquid, c_i^F (T1 - T0) - c_l (tfrz - T0) frozen (c_l = con_cliq, c_i^F = FV3 c_ice 1972). Noah-MP soil: what PAH and the stored water's content (snow layers, new layer, rain infiltrated at tg) do not supply heats the top layer; glacier: same (no PAH); sea ice: snowfall (stored at -li) gets the frame-F content incl. hfus - li in ice layer 1. With it on, PH1 releases L_f(T1) = hfus + (c_l - c_i)(T1 - T0) (T1 = lowest layer before the MP tendencies) instead of hfus |
| `lw_sfc_return` | LW2 (item 4) | the land keeps the LW it emits beyond the radiation-time land emission (stored at each radiation call): top layer += (fira - (ulw_rad - dlw_rad)) dt; its SEB sends it out next step through its own Jacobian (LW, SH, LH, G). The lowest layer gets only the remainder (sea ice linearisation, composite) |
| `noahmp_pore_air` | AIR1 (item 5) | water entering/leaving soil pores no longer takes the pore air's heat with it |
| `sfc_evap_enthalpy` (round 3) | EV1 glacier (item 2) | glacier columns now included |

Item 5, pore air: a model inconsistency, not a meter choice. Noah-MP's prognostic soil heat capacity includes
cpair*(smcmax - smc) (cpair = 1004.64 J kg-1 K-1 used as J m-3 K-1); the soil temperature equation conserves that
heat (tsnosoi closes to 1e-15 with it), but when water fills or leaves pores at fixed T the air's share disappears
with no flux anywhere (the air exchange with the atmosphere is not coupled). Measured -2.4487e-3 W m-2 at the aquifer
(= the round-2 remainder to 2e-14), -2.69e-3 in total. AIR1 keeps it in the soil layer.

Item 2, glacier +0.0074: the cold snow the 600 mm reset removes/adds (NM9 glacier flow) leaves at its layer T; booked
as a glacier-flow export (the reset's sensible content change), a declared open-boundary term like runoff.

## Round 4 gates (builds -no-fma, bitcmp 2374 variables)

| gate | runs | result |
|---|---|---|
| options off = bug-fix build | e5O0 (opt5n defaults) vs e5B0 (bfx5n) | BITWISE (also e4O0 vs e4B0) |
| bug fixes restart / layout | e5B0 vs e5BR_R / e5BL | BITWISE / BITWISE |
| all on (LW2) restart / layout | e5OA vs e5OAR_R / e5OAL | BITWISE / BITWISE |

## Round 4 impact, 24 h, each vs its off run (land mean/rms); noise ctlc999 - ctl64: T rms 0.149, t2m_L -0.003/0.238, SH_L 3.45, LH_L 4.30, soilt1 0.18

| run | T rms | t2m_L | SH_L | LH_L | other |
|---|---|---|---|---|---|
| bug fixes NM12+SL2+CS1+CB1 (e5B0 - e2B0) | 0.147 | +0.003/0.246 | +0.03/3.55 | +0.01/4.21 | noise |
| all bug fixes (e5B0 - e2F0) | 0.156 | +0.000/0.257 | +0.02/4.01 | +0.03/4.78 | soilt1 +0.010; icetk/weasd over ice (round 3) |
| EP1 | 0.150 | +0.004/0.267 | +0.02/4.12 | +0.08/4.50 | soilt1 +0.019; noise |
| LW2 | 0.176 | -0.034/0.386 | +0.22/5.20 | +0.04/5.40 | uLW -0.26, soilt1 +0.12/0.62 |
| LW1 | 0.201 | +0.210/0.745 | -0.56/5.94 | +0.19/6.21 | |
| AIR1 | 0.148 | -0.004/0.245 | -0.04/3.86 | -0.05/4.44 | noise |
| EV1 (soil + glacier) | 0.159 | +0.027/0.306 | -0.09/4.56 | +0.18/5.01 | |
| PH (L_f(T1) form) | 0.149 | +0.011/0.299 | -0.06/3.90 | +0.02/4.29 | noise |
| all on, LW2 (e5OA) | 0.195 | +0.022/0.600 | +0.01/6.34 | +0.14/5.87 | uSW -0.88 (SW1), soilt1 +0.15 |
| all on, LW1 (e5OA1) | 0.215 | +0.268/0.882 | -0.76/6.92 | +0.13/6.80 | |

**LW recommendation: LW2.** Both close to round-off. LW1 gives every within-hour change of land LW emission to the
lowest atmospheric layer, which the radiation would have spread through the column and partly to space; it warms land
t2m by +0.21 K in 24 h. LW2 leaves the atmosphere's LW at the radiation's own value and returns the land's excess to
the land, whose energy balance then disperses it through its Jacobian (LW, SH, LH, G) at the next step: air t2m within
noise in the mean (-0.03 K), the signal moves into the top soil (+0.12 K) and land SH (+0.2 W m-2). It is the land-side
analogue of a radiation Jacobian adjustment with the atmosphere frozen at radiation time. Sea ice and the composite
remainder still go to the lowest layer (they are small: LW applied -0.0127 W m-2 in e5MA).

## PH1 temperature (integrator, 18 Oct)

Noah-MP with EP1 books frozen precipitation at c_i^F (T1 - T0) - hfus (frame F), so the atmosphere must release
L_f(T1) = hfus + (c_l - c_i)(T1 - T0) per kg, not hfus. PH1 now uses L_f(T1) when sfc_precip_enthalpy is on (c_l = con_cliq,
c_i = 1972; T1 = lowest layer before GFS_MP_generic_post applies its tendencies, save_t), and hfus when it is off (the
stock surface books no sensible content for precipitation, so frozen precipitation at T0 is the consistent frame).
KF1 is the land-internal counterpart with Noah-MP's own capacities. e5MA: hfus x host convective snow 0.072798,
applied 0.071018, difference -1.780e-3 = the integrator's overheating, now removed.
Caveat (declared): the surface receives step N's precipitation at step N+1 with that step's T1 (sfctmp). The
atmosphere books it at step N's T1. The lag term c P (T1(N+1) - T1(N)) is a hand-off frame item until one side
stores the other's T1. It is not metered here.

The surface hand-off heating (LW + EV in GFS_surface_composites_post) closes per run, as an identity: in every metered
run the surface-loop segment residual equals the applied heating to 1e-13. The values are run-specific: 0.16152 in
e2MOA4 (LW1 + EV1, round 3), 0.11705 in e5MA (LW2 + EV1 incl. glacier). The integrator's 0.1811 is its own run's value,
with a different build and trajectory; the identity, not the number, is what must match.

## Round 4 final closure (e5MA2: all bug fixes 04-15 + NM12, all switches on with LW2, + D3A; metered build mopt10 + r4e)

e5MA2 is bitwise equal to e5MA, so the added meter is passive.

| component | before round 4 | final | note |
|---|---|---|---|
| Noah-MP soil, total | 3.9e-4 (e2MOA5) | 4.33e-8 | step 1 contributes 3.56e-8: initial state, energy step 2.82e-8 in 42 columns at kdt = 1 only. Steps 2-119 sum to 7.7e-9, about 1e-10 per step, which is the round-off of differencing absolute column heat (about 1e8 J m-2 per column) |
|  energy step (KF1) | 0.200 / 2.8e-8 | 2.8e-8 at kdt = 1, then 1e-15 per step | kdt = 1 initial-state only |
|  canopy (CH1) | 0.052 | -2.6e-17 | |
|  soil water (AD1, AIR1) | 0.058 | 1e-14 | |
|  snow layers | 3.9e-4 (SL1) | in the total above | NM12 alone does not change it (it fires about never at dt 720 s). SL2 + CB1 closed it. The 2.56e-5 left after them was this meter's own booking error: snowmelt leaving the snow bottom was booked as a soil import. It is internal; only its runoff share is a boundary export. With that corrected, 4.3e-8. CS1's own term was not isolated (≤ 3e-7) |
|  precipitation (EP1) | 0.0108 (booking) | applied; target = PAH + stored + applied to 1e-16 | |
|  LW2 kept | | land kept = cells' exclusion to 2e-17 | |
| Noah-MP glacier | +0.0074 | 6e-16 | after booking: the reset's content change (glacier flow export), precipitation stored + EP, LW2, sublimated snow content |
| sea ice | -1.1e-13 | -1.1e-13; EP heat = post-ice3lay dH to 5e-13 | |
| aquifer | 2.4e-3 unattributed | pore air, to 8.5e-15 (e5MO02); AIR1 keeps it | |
| hand-off LW (LW2) | | booked - radiation - land kept - applied: 5e-14 | |
| hand-off EV (soil + glacier) | | applied = booked to 6e-17 | |
| hand-off PH | | land and glacier receive host srflag P to 1.5e-13; PH1 = L_f(T1) x host convective snow | |
| hand-off SW (SW1) | | 0 where landfrac = 1; -6.1e-3 in 0.999 ≤ landfrac < 1 cells (mixed rule, ocean remainder) | declared F_ocn |
| surface-loop segment (eb_table) | | r = LW + EV heating exactly (0.11705 in e5MA) | |

Declared frame items (not round-off by construction): the ocean F_ocn (prescribed SST), runoff and glacier flow
leaving at their temperature, the precipitation T1 lag between the atmosphere's step N and the surface's step N+1,
and the kdt = 1 initial-state 3.6e-8.

Process note: three times my job queue submitted a batch of runs within a minute, so more than 2 of my jobs were
queued at once: the counter's job-name pattern did not match the new run prefixes, and once a stale TREE_DONE line
started the queue early. Fixed the pattern to `^e[0-9]`; the failed submissions were deleted and rerun in sequence.

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| ensfc2: surface energy closure, round 3 (clean bug-fix diffs, namelist options, full closure) | title | current | `report.md` and `report.history.md` |
| Status (18 Oct 2026, round 4 done) | diff order, closure summary, LW2 recommendation, builds | superseded by `## Status` above | `report.history.md` |
| Option switches (gfs_physics_nml, all default off; `patches/11_sfc_options.diff`) | round-3 switches (SERIES row 37) | current | `report.md` |
| Gates (all builds -no-fma; `tools/bitcmp.py`: every variable of atmf024/sfcf024 x 6 tiles + 24 h RESTART files, 2374 variables) | round-3 gates | superseded by `Round 4 gates` | `report.history.md` |
| Bug fixes: closure (metered e2MO0 = bug fixes + D3A, switches off) and impact (e2B0 vs e2F0, both -no-fma) | QR1, CMC, FL1 closure and impact | superseded by `Round 4 impact` and `Round 4 final closure` (the icetk/weasd impact cited there as "round 3" is here) | `report.history.md` |
| Options: closure in the all-on metered run e2MOA4 (W m-2 global, 119 steps) | round-3 option closure | superseded by `Round 4 final closure` | `report.history.md` |
| Options: forecast impact, each switch alone vs e2O0c (24 h, land = land==1, mean/rms), noise = ctlc999 - ctl64 | round-3 impact per switch | superseded by `Round 4 impact` for LW1, EV1, PH and all-on; the CH1, CH2, SW1, AD1 and KF1 rows were not re-run | `report.history.md` |
| Precipitation phase: NM10 vs host (e2MO0, soil columns, 24 h) | NM10 vs host rule, NM10r, PH1 vs D3a | current; NM10r adopted as water diff 17r, verified in `full14` (energy §9.9) | `report.md` |
| Frame F boundary definitions | land evaporation (EV1), ocean F_ocn | current (glacier EV1 added in `Round 4`) | `report.md` |
| Remaining, not at round-off | round-3 residuals | superseded by `Round 4 final closure` | `report.history.md` |
| Round 4 (18 Oct): every bug fixed, closure to round-off | diff order, SL2, CS1, CB1, round-4 switches, pore air, glacier | current | `report.md` |
| Round 4 gates (builds -no-fma, bitcmp 2374 variables) | final gates | current | `report.md` |
| Round 4 impact, 24 h, each vs its off run (land mean/rms); noise ctlc999 - ctl64: T rms 0.149, t2m_L -0.003/0.238, SH_L 3.45, LH_L 4.30, soilt1 0.18 | final impact, LW2 recommendation | current | `report.md` |
| PH1 temperature (integrator, 18 Oct) | PH1 at L_f(T1), hand-off identity | current; the T1-lag caveat is PL1 (SERIES row 46) | `report.md` |
| Round 4 final closure (e5MA2: all bug fixes 04-15 + NM12, all switches on with LW2, + D3A; metered build mopt10 + r4e) | final closure, declared frame items | current | `report.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
