# encnv: SAMF convection (D3a, D3b), GWD (D4, D4n) and the PBL×GWD cross term (D12)

## Status

- **Outcome:** in the final series as rows 07, 09, 10 and 11. Units W m-2 (24 h mean, frame E_P), control_p8_ugwpv1 C96, dt 720 s.

| item | SERIES row | class | switch default / all-on | segment residual before → after |
|---|---|---|---|---|
| D3a SAMF detrained ice without hfus | 07 `07_D3A.diff` | BF | — (unconditional) | deep −0.4195 → −8e-14; shallow −0.0179 → −2e-14 |
| D3b SAMF CMT, interface form | 09 `09_D3B.diff` | PC | `samf_cmt_heat` F / T | deep −0.1191 → +2e-13; shallow −0.0289 → +7e-14 |
| D4 GSL drag heating | 10 `10_D4.diff` | PC | `gwd_ke_heat` F / T | GSL term −0.3198 → 0 |
| D12 PBL×GWD process-split cross term | 10 (same diff) | PC | `gwd_ke_heat` F / T | −0.0663 → 0 |
| D4n UGWP-v1 NGW net energy source | 11 `11_D4n.diff` | PC | `ngw_heat_opt` 0 / 2 | +0.335 → 0 (option 1 or 2) |

- **All switches on** (sAll1, sAll2): every segment closes to round-off; GWD |r| 6e-13 (per step ≤ 2.4e-11), deep and shallow ≤ 3e-12.
- **Checks:** default off is bitwise identical to fx; 4×6 vs 3×8, unmetered vs metered and the gw-split meter are bitwise; the heat-profile meter is not bitwise passive. No separate red-team report.
- **D4n:** the series and TRACKER.md use option 2 (keep the heating, remove the column's net NGW input at the launch layer); the report leaves the option to Ash (§D4n). D12 stays tied to `gwd_ke_heat`.
- **Note:** the report classes D3b, D4, D12 as PHYSICS and D4n as DESIGN; SERIES classes all four PC.
- **Note:** TRACKER.md gives D3a −0.438 and D3b −0.149; neither is the sum of the report's deep and shallow rows above.

## Current answers

## Code findings

### D3a (BUG FIX): SAMF detrained ice
- **Where:** samfdeepcnv.f ~3750 (inside rn > 0) and samfshalcnv.f ~2676. Detrained condensate `tem = dellal·xmb·dt2` is split into ice `tem·tem1` (tem1 = clip((263.16 − T)/30)) and liquid.
- **Why it is a defect:** the scheme's energy is h = cp·T + g·z + hvap·qv, so all condensate is liquid-referenced. The ice is created without its latent heat of fusion.
- **Fix:** add `hfus` as an argument (latent_heat_of_fusion_of_water_at_0C, after hvap in the argument list and the .meta). Then `new_t1 += hfus/cp·tem·tem1` at the partition.
- **The rn ≤ 0 reset** (new_t1 = to) undoes the heating together with the condensate.

### D3b (PHYSICS, `samf_cmt_heat`): CMT dissipation
- **Where:** samfdeepcnv.f ~3354 and samfshalcnv.f ~2288. The CMT (new_u1 = u1 + xmb·dt2·dellau) conserves column momentum: the layer-1 remainder term is 4e-19 W m-2. It is not KE-conserving.
- **Round 2 replaces the per-layer −ΔKE** with the interface form, as in enpbl's `dspheat_ke`:
  - T_k = −Σ_{j≥k} delp_j·Δu_j (momentum moved down across the interface below layer k);
  - interface dissipation D_k = T_k·(ū_k − ū_{k−1}), with ū the time-centred wind, half to each adjacent layer;
  - layer 1 gets T_1·ū_1;
  - applied at the end of the routine, so reset columns (Δu = 0) get nothing.
- **Exact by summation by parts:** Σ heat = −ΣΔKE.
- **Negative heating vs per-layer −ΔKE (round 1):** the per-layer form had −0.209 of local cooling against +0.148 net, with max 95 K/day. The interface form has −0.044 (layer) and −0.050 (interface D < 0), with max 10 K/day. That is still 25× enpbl's −0.0017, because mass-flux transport moves momentum up-gradient at some interfaces.

### D4 (PHYSICS, `gwd_ke_heat`): GSL drag
- **`gsd_diss_ht_opt` is not a namelist option.** It is a local `logical` hard-set to `.false.` (drag_suite.F90:422; integer 0 at 1635 in drag_suite_psl). Turned on (1157-1169), it heats by `max(eng0 − eng1, 0)/cp`:
  - for the ls + bl increment only (not ss at 1316 or tofd at 1382);
  - clipped at 0;
  - with no cross terms between components.
  It is therefore not −ΔKE.
- **Fix** (ugwpv1_gsldrag_run, before `dudt_gw = Pdudt + dudt_ngw`): `Pdtdt −= Pdu·(ugrs + dtp·dudt_ngw + ½dtp·Pdu)/cp` (and v). This is the KE change of the summed GSL increment taken after the NGW increment, so the GSL×NGW cross term (+6e-6) is included.
- **Model-top peaks** (max |dT/dt| by level, run sD):

  | level | max (K/day) |
  |---|---|
  | 0.62 hPa | 210 |
  | 0.84 hPa | 198 |
  | 1.5 hPa | 198 |
  | 207 hPa | 191 |
  | 0.05 hPa | 157 |

  These are not momentum dumped at the top: drag_suite sets taup(km+1) = taup(km), so the flux leaves through the lid. They come from the mesoscale (ls) GWD breaking in the 50–100 m/s upper-stratosphere/mesosphere jets. The drag is capped only by dtfac_meso (facmeso = 0.5, i.e. at most half the wind removed per step, above plolevmeso = 0.7 hPa). Removing ~15 m/s from 80 m/s in one step is about 1 kJ/kg, about 1 K per step. The global-mean D4 heating up there is small: 4e-3 K/day at 0.1–0 hPa.

### D12 (PHYSICS, `gwd_ke_heat`): process-split cross term
- **Where it happens:** with tend_opt_pbl = 2, the PBL wind tendency is added to the process-split accumulator dudt and nothing is applied. With tend_opt_gwd = 3, GFS_GWD_generic_post applies `gu0 += dtp·(dudt + ten_u)` (case 3). This is the one place where the PBL and GWD increments, both computed from X0, are combined.
- **The cross term:** the KE of the joint update contains dtp²·(dudt·ten_u + dvdt·ten_v), which neither scheme sees.
- **Fix:** `gt0 −= dtp²·(dudt·ten_u + dvdt·ten_v)/cp` in case 3, before dudt is zeroed. This needs `con_cp` and the switch as new arguments of GFS_GWD_generic_post.
- **Size:** −0.0663 (meter e6). It lands below 850 hPa: mean 3.6e-3 K/day, max 47 K/day.
- **Case 1 (immediate apply) needs no D12.**
  - The tend_opt_* switches are hard-coded defaults, not namelist entries (GFS_typedefs.F90:3522-3531).
  - In this suite the only code that applies the process-split accumulator is GFS_GWD_generic_post case 3. GFS_suite_interstitial_1 zeroes it at the start of each step.
  - With tend_opt_gwd = 1 and tend_opt_pbl = 2, the PBL increment is never applied, so there is no cross term (and no PBL).
  - With tend_opt_pbl = 1, GWD's ugrs is gu0 after PBL, so its −ΔKE is exact. Run sT1 (exe mz2t, tend_opt_pbl = tend_opt_gwd = 1, all switches, ngw 1) gives GWD segment r = +3.6e-13 and meter e6 = 0.
  - Caveat: tend_opt_gwd = 1 also drops the pending radiative heating (tend_opt_sw/lwrad = 4). sT1's physics_post segment shows +105 W m-2, so that configuration is not usable in this suite as it stands.

### D4n (DESIGN, Ash's decision): UGWP-v1 NGW is a net energy source

Run s0, 100 steps:
- NGW heating: +0.365.
- KE loss of its own wind increment: 0.033.
- Net source: +0.335 (EMG e3 + e5).

The launched wave energy flux (prescribed launch at 275 hPa) is never taken from the resolved flow. In the code the heating is parameterised:
- dissipation dfdz_v;
- eddy heat flux;
- implicit T diffusion with Prandtl number;
- K·(∂v/∂z)²/cp;
- all clipped (cires_ugwpv1_solv2.F90 760-1002).

Options (`ngw_heat_opt`):
- **0:** as is.
- **1:** dtdt_ngw = −ΔKE_ngw/cp only.
- **2:** keep the heating and remove the column's net NGW input at the launch layer (k as in the solver: first prsl < 275 hPa, minus 1).

Global-mean NGW heating by band (K/day; max local in brackets):

| band | opt 0 | opt 1 | opt 2 |
|---|---|---|---|
| 500–200 hPa | +8.5e-3 (16) | +3.4e-4 (12) | −1.1e-3 (16) |
| 200–50 | +1.1e-3 | +5.9e-4 | +1.1e-3 |
| 50–10 | +7.3e-4 | −7.1e-4 | +7.2e-4 |
| 10–1 | +2.0e-2 | +2.1e-3 | +2.0e-2 |
| 1–0.1 | +0.211 | +0.091 | +0.210 |
| 0.1–0 | +0.454 | +0.261 | +0.453 |

**83 % of the NGW heating (0.30 of 0.365 W m-2) is in 500–200 hPa,** just above the launch level, and almost all of the net source (heating minus own KE loss) is there too.
- Option 2 cancels it there and leaves the stratosphere/mesosphere unchanged.
- Option 1 halves the mesospheric heating (−0.12 K/day at 1–0.1 hPa, −0.19 K/day at 0.1–0 hPa).

f24 T vs s0 (mean / rms, K); noise control s0c999 is in brackets:

| band | opt 1 | opt 2 |
|---|---|---|
| < 1 hPa | **−0.125 / 0.50** (−1e-4 / 0.20) | −0.002 / 0.22 |
| 50–1 hPa | **−0.012** / 0.12 (−2e-4 / 0.11) | −2e-4 / 0.11 |
| 500–200 hPa | −0.008 / 0.12 (−1e-5 / 0.11) | **−0.009** / 0.12 |

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| encnv: SAMF convection (D3a, D3b), GWD (D4, D4n) and the PBL×GWD cross term (D12) | title (and the configuration line under it) | current | `report.md` and `report.history.md` |
| Status (17 Oct 2026, round 2 done) | dated status table and checks | superseded by `Status` | `report.history.md` |
| Files | patches, meters, tools | archival | `report.history.md` |
| Code findings | the five defects and fixes | current | `report.md` |
| D3a (BUG FIX): SAMF detrained ice | fusion heat of detrained ice | current | `report.md` |
| D3b (PHYSICS, `samf_cmt_heat`): CMT dissipation | CMT interface-form heating | current | `report.md` |
| D4 (PHYSICS, `gwd_ke_heat`): GSL drag | GSL drag heating, model-top peaks | current | `report.md` |
| D12 (PHYSICS, `gwd_ke_heat`): process-split cross term | PBL×GWD cross term | current | `report.md` |
| D4n (DESIGN, Ash's decision): UGWP-v1 NGW is a net energy source | NGW options 0/1/2 | current (option 2 adopted in SERIES row 11) | `report.md` |
| Measured residuals (all runs: `$C/runs/<name>`; `seg_table.py`, `eb_table.py`) | segment residuals by run | current (round-2 table; the round-1 per-layer table is superseded by it) | `report.history.md` |
| Forecast impact, f24 T vs base (mean / rms, K; `impact.py`) | T impact by band, heating by band | current | `report.history.md` |
| Other suites and schemes (D3a pattern) | D3a pattern in other schemes | current | `report.history.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
