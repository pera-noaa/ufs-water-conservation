*History of `report.md` (enpbl), moved verbatim on 18 October 2026. The head is `report.md`.*

# D1: satmedmfvdifq dissipative heating vs the resolved-flow KE loss (control_p8 C96, 24 h, dt 720 s)

## Status (17 Oct 2026, round 2 done)

- **Explained.** TKE-ε heating (3.677 W m-2) exceeds the resolved-KE loss of the scheme's own momentum solve (2.248) by
  **1.429 W m-2**. The excess is TKE floors (0.862), shear production from the old winds above the actual KE loss (0.546),
  TKE gained outside the scheme (0.125), net buoyancy (−0.060) and the last-substep choice (−0.044). Table in §2.
- **Patch** `patches/04_ccpp-satmedmfvdifq_dspheat_ke.diff` (applies on `$E/fx`). New namelist switch `dspheat_ke`,
  default `.false.` (unchanged model). With `dspheat = dspheat_ke = .true.`, the dissipative heating is the KE loss of the
  implicit momentum solve in the Boville–Bretherton (2003) / CAM interface form (§3). Class: **PHYSICS CHANGE**.
- **Closure.** PBL segment residual +1.4273 → **+1.6e-12 W m-2** (max per step 2.8e-11). Whole-atmosphere 24 h residual
  (frame E_D) +2.090 → **+0.627 W m-2**.
- **Sign.** B&B layer heating < 0 totals −0.0017 W m-2 (0.08 % of the dissipation); the per-layer −ΔKE form (round 1) had −0.62.
- **Checks.** Default off: bitwise identical to fx1. Metered vs unmetered: bitwise. Layout 3×8 vs 4×6: bitwise (switch on).
  Restart not run (stateless).
- **Impact (§4).** Land PBL cools 0.08–0.15 K, land T2m −0.07 K (day) / −0.04 K (night). Ocean layer 1 warms +0.03 K,
  ocean SH −0.7 W m-2, LH +0.2, 10 m wind +0.01 m/s. PBL height change is within noise. Noise control (fx1c999) means are
  ≤ 1e-3 K for the same quantities.
- **dspfac.** Closure needs dspfac = 1. For dspfac ≠ 1 the PBL residual is exactly (dspfac − 1) × the dissipation
  (measured with dspfac = 0.5: −1.1236 vs −0.5 × 2.2473).
- **Open.** The scheme also moves 2.66 W m-2 between T and qv at hvap (energy-neutral in E_P); not chased. Whether
  dspfac should be ignored when `dspheat_ke` is on is an owner decision.

Dirs: Hercules `$D = $U/cons/enpbl` (`fx` = `$E/fx` + 04; `mfx` = `$E/mfx` + 04 + PBL meter; `runs/`, `exe/`, `logs/`,
`tools/`, `diffs/`). Local: this folder: `patches/`, `meters/meter_pbl_tke.diff`, `meters/tools/` (`instrument_pbl.py`,
`pbl_table.py`, `ems_seg.py`, `impact.py`, `mkrun.sh`, `fix_endif.py`), `meters/results/` (raw tables).

## 1. The code (satmedmfvdifq.F, fx-tree line numbers)

- TKE lives at layer centres k = 1..km−1. Production (≈1890-2030): P = buop + shrp. buop = −K_h·N² averaged from
  interfaces k−1, k, plus the EDMF up/downdraft buoyancy flux. shrp = K_m·S² from the **old** winds, averaged from
  interfaces, plus the EDMF momentum terms. At k = 1 the lower half is the surface-layer term u*³φm/(κ z1).
- Local step (≈2062-2075): 20 substeps of dt/20. ε = ce0·e^{3/2}/l, clipped to [0, P + e/dtn]; e += dtn(P − ε);
  e = max(e, tkmnz). tkmnz is the TKE implied by the background diffusivity xkzmo, ≥ tkmin = 1e-9, ≤ 0.2.
  At entry e = max(q_tke, tkmin).
- `diss` is overwritten every substep, so the heating (`ten_t += dspfac·diss/cp`, ≈2936) uses the **last** substep's ε.
- None of P is drawn from the resolved flow or from the enthalpy. The momentum solve and the s = cpT + gz solve are
  conservative on their own (surface fluxes aside). ε heating is therefore a pure source in E_P except where it happens
  to equal the KE loss.

## 4. Forecast impact

Runs compared against fx1 (= bb0 = pbl0 = mbb0, bitwise). Noise control is fx1c999 (fx1 exe, consv_te = 0.999).
Area-weighted means over fh 6-24. Day = local solar time 08-16, night = 20-04. Format: **test − fx1 | fx1c999 − fx1**.

### Heating profile (W m-2 of global area; old = TKE ε, from mbb1)

| levels (1 = lowest; ~height) | old ε | per-layer −ΔKE | B&B |
|---|---|---|---|
| 1 (10 m) | 0.282 | 0.052 | **1.230** |
| 2-3 (30-55 m) | 0.289 | 0.168 | 0.191 |
| 4-6 (80-130 m) | 0.204 | 0.276 | 0.113 |
| 7-10 (160-260 m) | 0.257 | 0.388 | 0.086 |
| 11-15 (300-470 m) | 0.518 | 0.455 | 0.079 |
| 16-20 (520-740 m) | 0.607 | 0.310 | 0.077 |
| 21-30 (0.8-1.6 km) | 0.750 | 0.230 | 0.160 |
| 31-45 | 0.351 | 0.162 | 0.150 |
| 46-127 | 0.254 | 0.210 | 0.166 |
| **total** | **3.512** | **2.251** | **2.251** |

By category (old → new; per-layer and B&B share column totals):

| category | old | new |
|---|---|---|
| land-day | 0.510 | 0.142 |
| land-night | 0.411 | 0.098 |
| sea-day | 1.341 | 1.035 |
| sea-night | 1.250 | 0.976 |

Land loses 74 % of its dissipative heating and ocean 22 %. B&B moves the heat from the upper half of the PBL (levels 11-30)
into level 1, mostly over the ocean (sea level 1: 0.25 → 1.15).

### Surface fields, B&B (bb1)

| field | all | land-day | land-night | sea-day | sea-night | rms f024 test / ctl |
|---|---|---|---|---|---|---|
| T2m (K) | +0.0075 / +0.0001 | **−0.073** / +0.0001 | **−0.038** / +0.0004 | **+0.029** / +0.0001 | **+0.030** / −0.0003 | 0.334 / 0.156 |
| T_sfc (K) | −0.007 / +0.0001 | −0.040 / +0.001 | −0.029 / −0.0002 | +0.002 / −0.0004 | +0.003 / −0.0001 | 0.460 / 0.258 |
| SH (W m-2) | **−0.53** / −0.003 | +0.22 / +0.02 | −0.06 / −0.004 | **−0.72** / −0.005 | **−0.74** / −0.004 | 4.0 / 1.9 |
| LH (W m-2) | +0.15 / +0.001 | −0.09 / −0.005 | +0.01 / −0.007 | +0.21 / +0.03 | +0.20 / −0.02 | 4.3 / 3.4 |
| PBL height (m) | +1.9 / −0.2 | +0.2 / −0.7 | +3.7 / −0.02 | +1.1 / +0.005 | +2.1 / −0.3 | 92 / 69 |
| 10 m wind (m/s) | +0.010 / −0.0001 | −0.005 / +0.001 | +0.013 / −0.001 | +0.012 / +0.001 | +0.011 / +0.00001 | 0.27 / 0.15 |

### PBL temperature profile, B&B (bb1 − fx1, K; control ≤ 2e-3 at every level)

| level (height) | land-day | land-night | sea-day | sea-night |
|---|---|---|---|---|
| 1 (10 m) | −0.083 | −0.044 | +0.032 | +0.034 |
| 2 (32 m) | −0.114 | −0.064 | +0.001 | +0.002 |
| 5 (105 m) | −0.128 | −0.088 | −0.001 | +0.0004 |
| 10 (260 m) | −0.149 | −0.114 | −0.005 | −0.004 |
| 15 (470 m) | −0.151 | −0.118 | −0.008 | −0.008 |
| 20 (740 m) | −0.133 | −0.102 | −0.016 | −0.014 |
| 25 (1.1 km) | −0.096 | −0.075 | −0.017 | −0.020 |

### Round 1 for comparison: per-layer form (pbl1)

| field | all | land-day | land-night | sea-day | sea-night |
|---|---|---|---|---|---|
| T2m (K) | −0.023 | −0.115 | −0.075 | +0.003 | +0.003 |
| SH (W m-2) | +0.04 | +0.67 | +0.18 | −0.11 | −0.06 |
| LH (W m-2) | −0.05 | −0.18 | −0.06 | −0.02 | −0.02 |
| PBL height (m) | +0.9 | −0.9 | +1.2 | +1.0 | +0.8 |
| 10 m wind (m/s) | −0.004 | −0.012 | +0.0005 | −0.002 | −0.003 |

PBL T for the per-layer form: land −0.13 to −0.15 K (day) and −0.08 to −0.11 K (night) through the lowest 1 km;
ocean +0.01 K below 500 m.

## 6. Other PBL schemes (note only)

| scheme | dissipative heating | relation to −ΔKE |
|---|---|---|
| satmedmfvdif (`satmedmfvdif.F` 1165-1181, 1424-1431) | `dspheat`: ε of the last TKE substep, clipped | same pattern as D1 |
| satmedmfvdifq_can (canopy variant) | same code as satmedmfvdifq | same as D1 |
| hedmf (`hedmf.f` 1312-1345) | diss = K_m S² − g/θ K_h N², plus a layer-1 term ½(g/θ·H + τ|v|/z1 + diss), × 0.5 (0.7 hurricane) | not −ΔKE; includes buoyancy |
| MYNN-EDMF (`module_bl_mynn.F90` 334, 1224-1233) | `dheat_opt = 1` hard-wired: q^{3/2}/(B1 l)/cp, cap 0.002 K/s, × exp(−10⁴/p) | TKE-based |
| YSU (`ysuvdif.F90`) | none | KE loss is an energy sink |
| saYSU / Shinhong (`shinhongvdif.F90`) | none | KE loss is a sink |

## 7. Jobs and runs (`$D/runs`)

| run | exe | what |
|---|---|---|
| mpbl0 / mpbl1 | p_mfx (round 1) | metered, switch off / per-layer form |
| pbl0 / pbl1 / pbl1L | p_fx (round 1) | unmetered off / per-layer / per-layer at 4×6 |
| mbb0 / mbb1 / mbbf | bb_mfx | metered off / B&B / B&B with dspfac 0.5 |
| bb0 / bb1 / bb1L | bb_fx | unmetered off / B&B / B&B at 4×6 |
| fx1c999 | `$E/exe/fv3_e_fx1.exe` | noise control, consv_te = 0.999 |

Builds: 10151627/8 (round 1), 10151790/1 (round 2; 10151784/5 failed on a duplicated ENDIF, fixed by
`fix_endif.py`; runs 10151788/9 mistakenly started with the old exes were cancelled and deleted).
