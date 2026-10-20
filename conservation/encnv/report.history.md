*History of `report.md` (encnv), moved verbatim on 18 October 2026. The head is `report.md`.*

# encnv: SAMF convection (D3a, D3b), GWD (D4, D4n) and the PBL×GWD cross term (D12)

control_p8_ugwpv1, C96, 24 h, dt = 720 s, 64-bit. Physics frame E_P (energy report §1a). Units are W m-2 (24 h mean) unless stated.

## Status (17 Oct 2026, round 2 done)

| item | class | switch | segment residual before → after | where the heat lands |
|---|---|---|---|---|
| D3a SAMF detrained ice without hfus | BUG FIX | none (unconditional) | deep −0.4195 → −8e-14; shallow −0.0179 → −2e-14 | 91 % at 500–200 hPa; max 4.4 K/day |
| D3b SAMF CMT, interface (Boville–Bretherton) form | PHYSICS | `samf_cmt_heat` | deep −0.1191 → +2e-13; shallow −0.0289 → +7e-14 | +0.148 net; layer heating < 0: −0.044; interface D < 0: −0.050 |
| D4 GSL drag heating −ΔKE/cp per layer, after the NGW increment | PHYSICS | `gwd_ke_heat` | GSL term −0.3198 → 0 | 74 % below 850 hPa; max 100–210 K/day |
| D12 PBL×GWD cross term of the joint process-split update | PHYSICS | `gwd_ke_heat` | −0.0663 → 0 | below 850 hPa; max 47 K/day |
| D4n UGWP-v1 NGW net energy source | DESIGN (Ash) | `ngw_heat_opt` 0/1/2 | +0.335 → 0 with option 1 or 2 | see §D4n |

- **Default-off is bitwise identical to fx.** Tree `offchk` (fx + D3B D4 D4N, switches off) matches `$E/runs/fx1` bitwise (atmf000/024, sfcf024).
- **All switches on:** with `ngw_heat_opt` = 1 or 2, every segment closes to round-off. Per-step maxima: GWD |r| 6e-13 (≤ 2.4e-11), deep and shallow ≤ 3e-12 (runs sAll1, sAll2).
- **Red team (round 1):** decomposition 4×6 vs 3×8 is bitwise identical (mallL == mall). The unmetered tree is bitwise identical to the metered one (fxall == mall). The fixes carry no state between steps. The gw-split meter is passive (m0 == fx1). The heat-profile meter is not bitwise passive: it edits samf*.f, and step 1 is identical but the run then diverges at round-off.
- **Open:** D4n option, Ash's decision (§D4n). D12 stays tied to `gwd_ke_heat` (coordinator decision: without consistent GWD heating the cross term does not matter for closure).

## Files
- Patches, applied in order on `$E/fx` (= `$C/fx`):
  - `patches/01_D3A.diff`
  - `02_D3B.diff`
  - `03_D4.diff` (D4 + D12)
  - `04_D4N.diff`
- Tool: `patches/tools/apply_encnv.py <tree> D3A D3B D4 D4N`. Round-1 unconditional versions are `D3B_R1` and `D4_R1`; their diffs are in `patches/round1/`.
- Meters (separate diffs on mfx):
  - `meters/meter_gw_split.diff`: the `EMG` line, split of the GWD segment.
  - `meters/meter_heat_profile.diff`: the `EMZ` lines, per-level heating, printed at step 100.
- Analysis tools in `meters/tools/`:
  - `seg_table.py`: segment residuals and the EMG split.
  - `heat_profile.py`: K/day by band.
  - `impact.py`: T by band, ps, precip.
  - `instrument_*.py`
- Hercules: `$C = $U/cons/encnv`, with `trees/`, `runs/`, `exe/`, `logs/`, `diffs/`, `tools/` (`mktree.sh`, `mkrun.sh`, `mkdiffs.sh`).

## Measured residuals (all runs: `$C/runs/<name>`; `seg_table.py`, `eb_table.py`)

**Round 1** (per-layer forms, unconditional), base m0 = fx1 bitwise:

| run | fixes | GWD r | deep r | shallow r | all physics r | residual total (E_D) |
|---|---|---|---|---|---|---|
| m0 | none (+gw meter) | −0.0494 | −0.5397 | −0.0469 | +0.797 | +2.090 |
| m0c999 | none, consv_te 0.999 | −0.0488 | −0.5400 | −0.0468 | +0.803 | +2.088 |
| mA | D3A | −0.0498 | −0.1191 | −0.0289 | +1.238 | +2.503 |
| mB | D3B_R1 | −0.0499 | −0.4195 | −0.0179 | +0.945 | +2.237 |
| mD | D4_R1 | +0.2669 | −0.5388 | −0.0468 | +1.128 | +2.430 |
| mall | all three | +0.2665 | −8e-14 | −2e-14 | +1.726 | +2.993 |

Round-1 GWD split (m0, meter EMG):

| term | value |
|---|---|
| ΔK of the GWD increment from the effective state | −0.4172 |
| GSL ΔK (from X0) | −0.3194 |
| NGW ΔK (from X0) | −0.0317 |
| NGW heat | +0.3672 |
| PBL×GWD cross term | −0.0662 |
| GSL×NGW cross term | +6e-6 |
| identity check | 6e-17 |

**Round 2** (switches, all builds include D3A), exe mz2 (metered), base s0 = defaults:

| run | namelist | GWD r | deep r | shallow r | all physics r |
|---|---|---|---|---|---|
| s0 | defaults | −0.0501 | −0.1191 | −0.0289 | +1.239 |
| s0c999 | consv_te 0.999 | −0.0496 | −0.1189 | −0.0289 | +1.237 |
| sB | samf_cmt_heat | −0.0502 | +2e-13 | +7e-14 | — |
| sD | gwd_ke_heat | **+0.3328** (= NGW own) | −0.1194 | −0.0289 | — |
| sN1 | ngw_heat_opt 1 | −0.3828 | −0.1192 | −0.0289 | +0.903 |
| sN2 | ngw_heat_opt 2 | −0.3821 | −0.1191 | −0.0289 | +0.906 |
| sAll1 | all, opt 1 | **+6e-13** | +7e-14 | −8e-14 | +1.466 |
| sAll2 | all, opt 2 | **−7e-13** | −2e-14 | +4e-15 | +1.470 |

## Forecast impact, f24 T vs base (mean / rms, K; `impact.py`)

| run | 1100–500 | 500–200 | 200–50 | 50–1 | < 1 hPa | precip rms (mm/day) |
|---|---|---|---|---|---|---|
| noise s0c999 | −8e-4 / 0.177 | −1e-5 / 0.106 | +2e-4 / 0.105 | −2e-4 / 0.109 | −1e-4 / 0.198 | 0.62 |
| mA (D3a) vs m0 | +7e-4 / 0.185 | **+0.016** / 0.124 | +9e-4 / 0.118 | +2e-4 / 0.126 | −3e-4 / 0.232 | 0.70 |
| sB (D3b) | +3e-5 / 0.182 | +0.002 / 0.114 | +4e-4 / 0.113 | −8e-5 / 0.118 | −2e-5 / 0.218 | 0.67 |
| sD (D4+D12) | **+0.0075** / 0.193 | +0.0025 / 0.119 | +5e-4 / 0.113 | +6e-4 / 0.120 | +0.003 / 0.219 | 0.68 |
| sN1 | −7e-4 / 0.181 | −0.008 / 0.117 | −8e-4 / 0.113 | **−0.012** / 0.118 | **−0.125 / 0.504** | 0.67 |
| sN2 | −2e-4 / 0.180 | **−0.009** / 0.116 | −3e-4 / 0.111 | −2e-4 / 0.114 | −0.002 / 0.218 | 0.66 |

All rms values except sN1 above 1 hPa are at the threshold-noise level. The bold means are the systematic signal of each item.

Other budget rows: the PBL residual moves +0.013 with D4 (mD) and +0.026 with all three, against noise of 0.005. This is a stability response to the near-surface D4 heating, not an energy term.

Heating by band (K/day, global mean), round 1 (mallz, all three per-layer forms):

| band | D3a deep | D4 |
|---|---|---|
| 1100–850 hPa | 0 | +1.4e-2 |
| 850–500 hPa | +6e-4 | +1.5e-3 |
| 500–200 hPa | +1.1e-2 | +4e-4 |
| 200–50 hPa | +7e-4 | +2e-4 |
| 1–0.1 hPa | 0 | +2.4e-3 |
| 0.1–0 hPa | 0 | +4.4e-3 |

D3b interface form (sB): +1.1e-3 (1100–850), +1.4e-3 (850–500), +1.2e-3 (500–200), max 10 K/day.

## Other suites and schemes (D3a pattern)
- **Same defect** (T-ramp partition of detrained condensate, liquid-only h, no hfus): SAS `sascnvn.F` 2046-2057 and `shalcnv.F` ~1300.
- **Grell-Freitas** (`cu_gf_driver.F90` 997, 1165) and **C3** (`cu_c3_driver_ccpp.F90` 1334, 1534): the driver re-partitions detrained condensate on 258→273 K without hfus. Their plume models carry their own ice phase (melt_glac, xlf), so consistency is unverified.
- **Not this defect:** Chikira-Sugiyama (splits only combined condensate, carries emelt), RAS (alhf with QIL), nTiedtke (alf with foealfa).
- **No partition** (copies only): GFS_suite_interstitial, cnvc90, GFS_DCNV/SCNV_generic_post.
- **Diagnostics:** the T dtend of D4 is not added to the orographic-GWD dtend when `flag_for_gwd_generic_tend` is false; D12 has no dtend.
