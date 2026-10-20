# Surface-component energy budgets: control_p8_ugwpv1, C96, 24 h (Noah-MP, NSST, sea ice, hand-off)

## Status

- This workstream is superseded by `ensfc2/`, which recut its diffs and owns the final surface closure (`ensfc2/report.md`).
- Every fix here is in the final series (`replay/SERIES.md`):

| Item | SERIES row | Class | Switch: default / all-on | Before → after (this report) |
|---|---|---|---|---|
| SI1 | 31 | BF | — | ice calls per column-step 1.0186 → 1.0000 |
| SI2, NP1 | 32, 33 | BF | — | did not fire in this March run (meters 0) |
| QR1 | 34 | BF | — | NSST qrain 0.300 → 0.417 W m-2 (×1000/720) |
| CMC | 35 | BF | — | land charged − carried 0.0148 → 0 |
| FL1 | 36 | BF | — | ice3lay residual −7.87e-3 → −1.1e-13 |
| CH1/CH2, PH1–PH3, SW1 | 37 | PC / NC | namelist, default off; all-on as manifest row 37 | CH1: R_S 0.052 → 3e-17 |

- Rows 31–33 are byte-identical to `patches/04–06` here; the series takes them from ensfc2's identical copies. Rows 34–37 are ensfc2's diffs 08–11.
- `patches/07_round2_switchable.diff` (run-time `ESFIX` switches) is not in the series. ensfc2 recut its options as namelist switches (rows 37 and 41).
- Withdrawn: SL1 (misattributed; §5). Dropped: SI3 (the open water is an open boundary).
- No red team.

## Current answers

## 2. Round-1 budgets (base meters ms3; fixed run mx1/mx3 where stated)

| component | dH | own-frame residual | attribution |
|---|---|---|---|
| Noah-MP soil | +11.566 | +10.713 | groundwater +10.20 (aquifer exchange, §9); soilwater +0.290 (water moved without its sensible heat); R_E +0.200 (constant-hfus Kirchhoff in phasechange, 20.7 at step 1, an initial-condition freeze); −canhs +0.052; canopy melt/freeze latent −0.021; snowfall stored at the snow-layer temperature −0.010 (round 1 called this 'layer ops'; see §5); snow latent −0.004; NM11 sice<0 +0.001; PAH clip 2e-4. tsnosoi, erreng and between-call change: 0 (1e-14). |
| Noah-MP glacier | −0.0753 | +0.0071 | All of it is the sensible heat of cold ice exported by the NM9 reset/glacier flow (runoff booked without its sensible heat). Energy solve R_E −1e-14; surface residual 5e-19. |
| Sea ice | −0.713 | −0.0079 | Equal to the snow-ice formation term (−7.868e-3 vs −7.868e-3). SI1: 1.9 % of ice column-steps were stepped twice, booking ≈ −0.010 extra; calls per column-step 1.0186 → 1.0000 with SI1. SI2 and NP1 never fired (meters 0). |
| NSST | warm layer +6.36 | open | dtm_1p +16.3; resets/adjustments −9.9. NSST books 7.08 into the ocean using f_nsol at the old skin T, without spray, with qrain. The atmosphere-side flux differs by +0.068. |

**Hand-off, component − atmosphere (mx3).** The SW water entry (+0.219) and the LH/SH entries depend on SI3 and on sfc_sice's lead fluxes; both are explained in the bullets below the table.

| | land | sea ice | water |
|---|---|---|---|
| SW | −0.573 | −0.219 | +0.219 (SI3) / 0 |
| LW | +0.115 | +0.097 | −0.232 |
| SH, LH | ≤ 7e-8 | see below | ≤ 1e-11 |

- **Icy cells:** sfc_sice overwrites NSST's evap_wat, hflx_wat, tsfc_wat (= tgice) and qss_wat. The atmosphere therefore gets sfc_sice's lead fluxes (composite vs PBL: exact, 0.554615 vs 0.554615). NSST still books its own lead fluxes: LH +0.066 and SH −0.008 more than the atmosphere received.
- **Precipitation phase:** surfaces take hfus × 0.043 more frozen precipitation than the atmosphere released as frozen (§6).
- **PAH:** −0.013 (§7).

**Forecast impact of SI1 + SI2 + NP1 (sf1 vs fx1, f24), against ctlc999 vs ctl64:**
- ice thickness rms 1.7e-3 m (noise 8e-5), mean −5e-5 m;
- weasd over ice rms 0.105 (noise 0.052);
- tisfc, tmp2m, fluxes, global T (0.15 K) and ps: within noise.

**SI2, why it is an error.** The excess lower-layer heat, di·h2·ci·(T2 − tfi) in J m-2, melts h2·ci·(T2 − tfi)/li metres of ice. Dividing again by delt gives m/s, so (1 − 1/720) of that heat is deleted while T2 is still reset to tfi.
**SI2, what triggers it.** The re-split branch h1 > hice/2 (net bottom melt) that leaves the blended T2 above tfi, i.e. thin ice near melting in the melt season (Arctic Jun–Aug, Antarctic Dec–Feb). It did not fire in this March run.

**NP1, why it is an error.** When a snow layer melts out, phasechange sets its T to tfrz and passes the leftover heat to hm(j+1). The j+1 pass only acts on layers with imelt > 0, so with a sub-freezing layer below, that heat is deleted.
**NP1, what triggers it.** A top layer melting out completely within one step over a still-cold layer, e.g. thin new snow under strong sun or warm rain on a cold pack in spring. It did not fire in this run.

## 5. Round-2 candidate fixes: cause, fix, closure, impact

- **Runs.** M0 = metered, switches off. MA = all switches with CH1. MB = CH2 alone.
- **Impact.** 24 h, each switch alone against r0 (s2r, all switches off).
- **Noise.** ctlc999 − ctl64:
  - global T rms 0.149 K;
  - land: tmp2m rms 0.24, mean −0.003 K; tmpsfc rms 0.51; LH rms 4.3 W m-2;
  - ice: icetk rms 8e-5 m.

| tag | code-level cause | minimal fix | closure (meter) | impact vs r0 | class |
|---|---|---|---|---|---|
| QR1 | `sfc_nst.f90` 378, 389: `rain` is lwe m per step (tprcp_wat); qrain and sep use it as kg m-2 s-1 | `rain_rate = 1e3*rain/timestep` in both lines | qrain 0.300 → 0.417 W m-2, exactly ×1000/720. NSST-internal: it changes the skin T, not F_ocn. | noise (T rms 0.158; all surface fields within noise) | BUG FIX |
| CH1 | `vege_flux`: canhs = hcv·dtv/dt books only the last Newton increment. The massless canopy's fluxes then miss its balance by canhs. | drop hcv from the Newton denominator: massless canopy, canhs = 0 | R_S 0.052 → 3e-17 | land tmp2m −0.026 K mean (rms 0.33); land LH −0.09; T rms 0.163 | DESIGN DEFECT; minimal-consistency option; slightly beyond noise over land |
| CH2 | as above; the intent (C. He / G.-Y. Niu) is canopy storage over the step | b −= hcv·(tv − tv_start)/dt; canhs = hcv·(tv_new − tv_start)/dt | storage-frame R_S 7e-16; canwater's ad hoc tv reset then shows +0.56 W m-2 unbooked | land tmp2m +0.35 K mean (rms 1.39); land SH −3.3 W m-2; T rms 0.27 | PHYSICS CHANGE (large). Needs a matching canwater fix (tv change = −hfus·Δm/hcv). |
| CMC | `canwater`: (a) qevac and qsubc are capped by the available canopy water after the energy solve charged fcev; (b) frozen canopy: transpiration is charged at hsub but taken from soil liquid; (c) canopy melt/freeze moves hfus·Δm with no heat (tv reset only) | return (a)+(b) and −hfus·(qmeltc − qfrzc) to the top soil layer through the NM11 lheat path | land charged − carried 0.0148 → 0 (the leftover −0.0025 is my meter's E_ice over-count on NM11's sice<0 path); melt latent −0.021 now balanced by soil heat | noise (soilt1 land +0.008 mean, rms 0.22) | BUG FIX (NM11 precedent) |
| SL1 | combine discards the sensible heat of removed or merged snow layers | send it to the top soil layer | changes only 3e-4. The −0.010 is new snowfall added to cold snow layers at their T: the precipitation carries no sensible heat in the E_P frame, and frame F (precipitation lands at T1, §7) books it. | noise | DROPPED |
| FL1 | `sfc_sice.f` ice3lay snow-ice formation: flooded snow (heat content −li) becomes ice at the layers' temperatures | mix the snow's −li into each layer's heat content (T2 linear, T1 by the layer-1 quadratic) | ice3lay residual −7.87e-3 → −1.1e-13 | icetk mean −2.8e-5 m, rms 1.6e-4 (2× noise); the rest noise | BUG FIX |

**MA (all switches with CH1), Noah-MP soil.** After removing the open/frame terms, what remains is
snowfall stored cold (−0.010), snow latent (−0.004) and NM11's sice<0 path (+0.001). The open/frame terms are
groundwater 10.204, soilwater 0.286 and Kirchhoff 0.200 (§9). Sea ice closes to 1e-13; the glacier's remaining
residual is the frame term in §9.

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| Surface-component energy budgets: control_p8_ugwpv1, C96, 24 h (Noah-MP, NSST, sea ice, hand-off) | title | current | `report.md` and `report.history.md` |
| Status (17 Oct 2026, round 2 measured) | round-1/2 status, accepted fixes, owner decisions | superseded by `## Status` above | `report.history.md` |
| 1. Frames | heat-content frames of the round-1/2 meters | archival | `report.history.md` |
| 2. Round-1 budgets (base meters ms3; fixed run mx1/mx3 where stated) | round-1 budgets; SI1, SI2, NP1 cause, trigger and impact | current (SI1, SI2, NP1); land SW −0.573 superseded by §8 | `report.md` |
| 3. Open-ocean boundary (prescribed SST) | F_ocn definition; SI3 not needed | superseded by ensfc2 `Frame F boundary definitions` | `report.history.md` |
| (§4) | none: the file has no §4 | gap in numbering | — |
| 5. Round-2 candidate fixes: cause, fix, closure, impact | causes and fixes of QR1, CH1, CH2, CMC, SL1, FL1 | current (causes and fixes); closure and impact re-measured in ensfc2; SL1 row withdrawn | `report.md` |
| 6. Precipitation phase at the hand-off | NM10 rule, PH1–PH3 | superseded by ensfc2 `precip_phase_host`, `Precipitation phase: NM10 vs host` and `PH1 temperature` | `report.history.md` |
| 7. Water enthalpy across the surface in encpl's frame F (PAH and evaporation) | evaporation and precipitation enthalpy in frame F | superseded by ensfc2 `Frame F boundary definitions` (EV1) and `Round 4` (EP1) | `report.history.md` |
| 8. SW and LW hand-off | SW1, LW option | superseded by ensfc2 SW1, LW1 and LW2 | `report.history.md` |
| 9. Frame items | aquifer, soil water, glacier, constant-hfus Kirchhoff | superseded by ensfc2 AD1, KF1, AIR1 and the round-4 glacier booking | `report.history.md` |
| 10. Index | runs, builds, meters, fix scripts | archival | `report.history.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
