# D1: satmedmfvdifq dissipative heating vs the resolved-flow KE loss (control_p8 C96, 24 h, dt 720 s)

## Status

- **Outcome:** in the final series as row 06 `06_D1_dspheat_ke.diff` (this folder's `patches/04_ccpp-satmedmfvdifq_dspheat_ke.diff`), class PC, switch `dspheat_ke`, default `.false.` / all-on `.true.` (with `dspheat = .true.`).
- **Cause:** the TKE-ε heating exceeds the KE loss of the scheme's own momentum solve. The excess is TKE floors, shear production from the old winds, TKE gained outside the scheme, net buoyancy and the last-substep choice (§2).
- **Fix:** with the switch on, the heating is the KE loss of the implicit momentum solve in the Boville–Bretherton (2003) / CAM interface form. The column sum equals the column KE loss exactly (§3).
- **Checks:** off is bitwise identical to fx1; the meter is passive; 3×8 vs 4×6 is bitwise with the switch on; restart not run (stateless). No separate red-team report; §5 holds the report's own checks.

| quantity (W m-2 unless stated) | before | after |
|---|---|---|
| PBL segment residual | +1.4273 | +1.6e-12 (max per step 2.8e-11) |
| whole-atmosphere 24 h residual, frame E_D | +2.090 | +0.627 |
| dissipative heating applied | 3.677 (TKE ε, last substep) | 2.2511 (= −ΔKE) |
| layer heating < 0 | −0.62 (per-layer −ΔKE form) | −0.0017 |
| land T2m, day / night (K; noise +0.0001 / +0.0004) | — | −0.073 / −0.038 |
| ocean SH, day / night | — | −0.72 / −0.74 |

- **Open:** closure needs dspfac = 1 (the PBL residual is exactly (dspfac − 1) × the dissipation); whether dspfac is ignored when `dspheat_ke` is on is an owner decision. The scheme's T↔qv exchange at hvap (energy-neutral in E_P) is not chased.
- **Note:** TRACKER.md gives D1 as +1.43 → 1e-12; the report's after value is +1.6e-12.

## Current answers

## 2. TKE and KE budget, measured (run mpbl0 = default; bitwise = fx1; W m-2, 120 PBL steps)

| term | W m-2 |
|---|---|
| shear production P_s (incl. EDMF momentum terms) | 2.794 |
| of which the surface-layer term (k = 1) | 0.151 |
| buoyancy production P_b (net; > 0 part +0.667, < 0 part −0.727) | −0.060 |
| TKE floor in substeps (tkmnz), injected | 0.862 |
| TKE floor at entry (tkmin) | 1e-10 |
| ε removed by the clip | 0.005 |
| ε mean over the 20 substeps | 3.721 |
| **ε of the last substep (heated)** | **3.677** |
| dTKE/dt local (P − ε + floors) | −0.125 |
| dTKE/dt transport (diffusion + MF + borrowing) | 7e-19 |
| TKE storage over 24 h (content step 3 → step 120) | +0.005 |
| **−ΔKE of the momentum solve** | **2.248** |
| of which surface-stress work, implicit (u_new) / explicit (u_old) | 1.124 / 1.213 |
| identity P − ε_mean + floors − dTKE_local | 3e-15 |

**Excess decomposition**, exact: ε_last − (−ΔKE) = [P_s − (−ΔKE)] + P_b + floors − dTKE_local + (ε_last − ε_mean).

| part | W m-2 | what it is |
|---|---|---|
| floors (tkmnz) | +0.862 | TKE from nothing, dissipated as heat; never left the resolved flow |
| shear-production overshoot | +0.546 | K·S² from old winds exceeds the KE the implicit solve removes. Interior P_s 2.64 vs surface-layer term 0.15, while the surface stress work is 1.12 |
| TKE gained outside the scheme | +0.125 | each PBL call ends 90 J m-2 below its entry content; the TKE is regained before the next call (dycore/other) |
| buoyancy, net | −0.060 | gross +0.667 converted from enthalpy that the s-solve never removes |
| last substep vs mean | −0.044 | |
| **total** | **1.429** | EMS PBL residual +1.4273 (EMS covers 119 steps) |

## 3. The energy-consistent option (patch 04)

**Round 1 (superseded): per-layer −Δ(½|v|²).** Closed to 2e-13 W m-2, but the local form includes KE flux convergence:
level 1 got only 0.05 W m-2 and layers with net KE import were cooled (Σ local cooling −0.62 W m-2).

**Round 2 (current): Boville–Bretherton / CAM interface form.** With Δu = ten_u·dt, ū = u + ½Δu, layer pressure
thickness del_k (1 = lowest):
- T_k = −Σ_{j≥k} del_j Δu_j is the momentum moved down across the interface below layer k. It is built from the
  solution, so it includes the implicit diffusion and the explicit EDMF transfers. T_1 is the momentum given to the surface.
- Interface dissipation D_k = T_k·(ū_k − ū_{k−1}) (u and v summed). It goes half to each adjacent layer.
  The surface work T_1·ū_1 goes all to layer 1.
- Summation by parts gives Σ_k Q_k = −Σ_k del_k ū_k Δu_k = −Σ_k del_k Δ(½u²) **exactly**: the column sum equals the
  column KE loss.
- Heating: ten_t += dspfac·Q_k/(cp·del_k·dt). `dtend` is updated the same way.
- Code: satmedmfvdifq.F ≈3029-3078; old branch guarded by `.not. dspheat_ke` (2936).

| check (run) | value |
|---|---|
| PBL segment r (mbb1) | +1.6e-12 W m-2, Σ|r| 1.7e-9, max per step 2.8e-11 |
| heating applied = −ΔKE (mbb1) | 2.2511 = 2.2511 |
| whole-atmosphere residual (mbb1, frame E_D) | +0.627 (was +2.090); physics Σ −0.632 |
| B&B layer heating < 0 | −0.0017 |
| interface D < 0 (all) / diffusive part | −0.0042 / −0.0037 |
| interface D from the EDMF mass-flux transfer (net) | +0.051 |
| dspfac = 0.5 (mbbf): r vs (dspfac−1)·D | −1.12357 vs −1.12366 (difference = 119- vs 120-step windows) |

**Where the heating is negative and why.** D_k = T_k·Δū_k is negative where the momentum transfer T_k opposes the
time-centred shear Δū. Two cases:
- The implicit shear changes sign within the step at an interface. In the multi-level backward-Euler solve,
  neighbouring layers can overshoot, and the explicit EDMF terms change u. This accounts for −0.0037.
- EDMF counter-gradient transfer, which can create KE. Its net contribution is +0.051 W m-2 of dissipation.

A strictly non-negative variant is available if wanted: clip D < 0 and rescale the positive D in the column. That stays
exact wherever the column KE loss is ≥ 0.

**dspfac.** Kept as a multiplier (existing knob semantics). Closure in E_P holds only for dspfac = 1. Otherwise the PBL
residual is exactly (dspfac − 1)·Σ D, so the closed frame is E_P + (1 − dspfac)·∫D dt.

**TKE is not part of E.** Its production is not drawn from the resolved flow or the enthalpy, its floors inject it, and
its storage is 0.005 W m-2. Counting it would close nothing.

## 5. Red team

- **Default unchanged.** pbl0, bb0, mpbl0 and mbb0 are bitwise identical to fx1 (6 tiles, atmf024 + sfcf024).
- **Meter passive.** mbb1 = bb1 and mpbl1 = pbl1, bitwise.
- **Decomposition.** bb1 = bb1L (4×6), bitwise.
- **Restart.** Not run. The heating uses only within-step quantities and adds no persistent field.
- **Other suites/branches.** Default off, so nothing changes. The switch is independent of the tte_edmf and sa3dtke
  branches; it uses only ten_u/ten_v.
- **use_oceanuv = .true.** The implicit drag in the solve damps the wind toward 0, not toward the current. The surface
  work is computed in the ground frame, so the work done on the ocean is heated into the atmosphere. Not exercised here.
- **Patch reproducibility.** `$E/fx` + patch 04 reproduces `$D/fx` byte for byte.

## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| D1: satmedmfvdifq dissipative heating vs the resolved-flow KE loss (control_p8 C96, 24 h, dt 720 s) | title | current | `report.md` and `report.history.md` |
| Status (17 Oct 2026, round 2 done) | dated status, run directories | superseded by `Status` | `report.history.md` |
| 1. The code (satmedmfvdifq.F, fx-tree line numbers) | where ε heating is computed | current | `report.history.md` |
| 2. TKE and KE budget, measured (run mpbl0 = default; bitwise = fx1; W m-2, 120 PBL steps) | TKE budget, excess decomposition | current | `report.md` |
| 3. The energy-consistent option (patch 04) | B&B interface form, closure checks | current (its round-1 paragraph is superseded by round 2 in the same section) | `report.md` |
| 4. Forecast impact | impact vs fx1 | current | `report.history.md` |
| Heating profile (W m-2 of global area; old = TKE ε, from mbb1) | heating by level and category | current | `report.history.md` |
| Surface fields, B&B (bb1) | surface-field impact | current | `report.history.md` |
| PBL temperature profile, B&B (bb1 − fx1, K; control ≤ 2e-3 at every level) | PBL T impact | current | `report.history.md` |
| Round 1 for comparison: per-layer form (pbl1) | per-layer form impact | superseded by `3. The energy-consistent option (patch 04)` (round 2) | `report.history.md` |
| 5. Red team | default, meter, layout, restart checks | current | `report.md` |
| 6. Other PBL schemes (note only) | dissipative heating in other PBL schemes | current | `report.history.md` |
| 7. Jobs and runs (`$D/runs`) | runs and builds | archival | `report.history.md` |

History: [`report.history.md`](report.history.md) holds everything not above, verbatim.
