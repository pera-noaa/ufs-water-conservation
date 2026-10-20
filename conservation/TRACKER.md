# Conservation follow-on: item tracker

## Status

- **Total energy**, C96 24 h, every switch on (`full14`, the final tree): +1.6 × 10⁻¹² W/m² net of declared boundary and source
  terms; every scheme gap ≤ 1.2 × 10⁻¹² W/m². The FV3 `consv_te` fixer removes 0.304 W/m², down from 0.570.
- **Passive-tracer mass:** about 3 × 10⁻¹⁵ per day. A tracer that starts uniform in dry mixing ratio stays uniform to
  4.9 × 10⁻¹³ max at 24 h.
- **Reproducibility:** every gate is bitwise (restart, 3×8 vs 4×6, switches off, meters passive; `-no-fma` builds).
  All-on `full14` is bitwise identical to `full13`. The 55-diff series reproduces `full14` byte for byte, all-on and
  default-off (`replay/`).
- **Open:**
  - Hercules cleanup: canopy `runs/` (288 GB) deleted 18 Oct; the regression baselines (564 GB) and canopy build trees
    (4.8 GB) are approved for deletion, pending a run by Ash.
  - Upstream submission: round 1 = 37 fixes in three tracks, each its own WM PR (`../proposal/pr_round1.md`): 1a global
    conservation (24: SAMF + PBL, Noah-MP, sea ice/NSST, GFDL MP, SAMF32 build), 1b microphysics (7: Thompson, TEMPO),
    1c dycore (6: FV3). The 37 together: answers change only, reproducibility 123/123 bitwise, 188 of 188 changed tests
    screened. 1b's regional precipitation changes (−4 to +11 %) are the fixes' own signal (attributed to fix and part).
    1a global P8 check: only SAMF + PBL exceeds noise (+0.002 to +0.006 K, its ice-fusion heat). But 1a alone crashes
    `hafs_global_1nest_atm` in 2 of 3 members (RT member included); the 37 do not. Open. SA1 held with the SAMF instability issue to
    @JongilHan66 (`pr_round1_descriptions.md` §8). Round-2 issues drafted (`../proposal/round2_issues.md`). Nothing posted.
- Proposal: `../proposal/conservation_proposal.md`; manifest: `../proposal/conservation_patches.md`.
- History of this file (every row as it evolved): `TRACKER.history.md`.

## Items

Class: BUG = bug fix, unconditional; PHYS = physics change; NUM = numerical consistency. Switches default to off.
The recommended setting is the one used in the all-on runs.

### Energy, FV3 dycore and coupling

| Item | What was wrong | Outcome | Class | Switch (recommended) | Report |
|---|---|---|---|---|---|
| FX1 | `consv_te` fixer weight | fixer window −5.5e-4 → ±3e-10 W/m² | BUG | — | `energy/` |
| SG1 | `fv_sg` relaxation not energy-conserving | −1.6e-4 → 3e-11 | BUG | — | `energy/` |
| CP1 | coupling heating at the wrong mass | −8.6e-3 → ±4e-10 | BUG | — | `energy/` |
| C1 | coupling of the water mass change: PE, flow work (±R_v·T at fixed δz, net −0.62), sensible heat, KE | closes to round-off; bit 2 is LH −1.9 W/m², precipitation −3.4 % (all bits) | PHYS | `cpl_water_energy` (all bits) | `encpl/`, `fwred/`, `energy/` |
| D7 | A→D-grid wind-increment KE (−0.016) | 1e-10; flux-form smoothing, peak 0.87 → 0.013 K/step | NUM | `cpl_ke_heating`, `cpl_ke_smooth` (32) | `energy/` |
| DY1–DY3 | `d_con` heat applied ×cp/cv (+0.29); KE taken about the half-damped wind (−0.02); Rayleigh_Super cv/grid/pkz (+6e-4) | fixer −0.570 → −0.304; red-teamed (ratio 1.4010 replay, 1.4007 model) | BUG | `dyn_te_exact` (31; 127 adds design options) | `fv3tally/`, `dycred/` |
| FV-adiabatic | +0.41 W/m² created by the adiabatic dynamics (spatial discretization) | open by design; removed by the fixer | — | — | `fv3tally/` |

### Energy, physics

| Item | What was wrong | Outcome | Class | Switch (recommended) | Report |
|---|---|---|---|---|---|
| R1 | radiative heating at the stale mass | −7.7e-3 → 1e-13 | BUG | — | `energy/` |
| D1 | PBL dissipative heating vs the resolved KE it removes | +1.43 → 1e-12; land T2m −0.07 K | PHYS | `dspheat_ke` | `enpbl/` |
| PBK, PBF | PBL filler Kirchhoff; condensate flux at c_l/c_i | PBK +4.8e-5 → 0; PBF −0.0049 → 8e-13 | PHYS | `pbl_kirchhoff`; `cpl_water_energy` bit 4 | `energy/` |
| D3a | SAMF detrained ice without fusion heat | deep −0.4195, shallow −0.0179 → ≤ 1e-13 | BUG | — | `encnv/` |
| D3b, D4, D12 | SAMF momentum-transport heating; GSL drag heating; PBL×GWD cross term | D3b deep −0.1191, shallow −0.0289; D4 −0.3198; D12 −0.0663 → round-off | PHYS | `samf_cmt_heat`, `gwd_ke_heat` | `encnv/` |
| D4n | non-orographic GWD net source +0.335 | closed | PHYS | `ngw_heat_opt` (2) | `encnv/` |
| S1K | SAMF Kirchhoff incomplete (ice, start-of-step T) | deep +0.080, shallow +0.003 → 1e-13 | PHYS | `samf_kirchhoff` | `energy/` |
| TFH, K1 | Thompson heating in the model's energy frame | +0.0083 → 9e-13 | PHYS | `thompson_frame_heat`, `thompson_kirchhoff` | `energy/`, `encpl/` |
| TH8 + TH9 | Thompson sub-threshold surface sedimentation lost (water 7e-12 kg/m²/s, energy 2.3e-6 W/m²); placeholder sedimenting | closes; TH8 alone is beyond noise over land (canopy evaporation −68 %), so both ship as one unconditional diff | BUG | — | `canopy/`, `energy/` |
| TOPT | `tend_opt` combinations drop R, PBL or GWD tendencies (+110…−142 W/m²) | every combination applies each once; option 4 is an error | BUG | — | `latent/` |

### Energy, surface (Noah-MP, NSST, sea ice)

| Item | What was wrong | Outcome | Class | Switch (recommended) | Report |
|---|---|---|---|---|---|
| SI1, SI2, NP1, QR1, CMC, FL1 | sea-ice layer melt and stepping (SI1, SI2); melted-out snow layer heat (NP1); NSST rain read as a rate (QR1); canopy water heat (CMC); snow-ice formation (FL1) | each closes to round-off | BUG | — | `ensfc/`, `ensfc2/` |
| SL2, CS1, CB1 | snow-layer combine T, snow heat capacity from capped fractions, `combo` per-m³ capacities | soil 3.9e-4 → 4.3e-8 (3.6e-8 of it the step-1 initial state; later steps ~1e-10 each) | BUG | — | `ensfc2/` |
| NM12 | snow-layer combine loses water when a layered pack melts out | fix `isnow < -1`; rare at dt 720 s (1 firing in 2e5 melt-out-prone calls; 0 in 1e6 random calls) | BUG | — | `nm12/` |
| CH1/CH2, PH1–3, SW1, LW2, EV1, AD1, KF1, AIR1, EP1 | surface energy options | each closes its term to round-off | PHYS/NUM | see `ensfc2/` (LW2 over LW1) | `ensfc2/` |
| PL1 | precipitation booked at the next step's T1 (−0.0121) | 0 (exact); folded into EP1 | BUG of EP1 | `sfc_precip_enthalpy` | `preclag/` |
| NM10r | Noah-MP phase rule vs the host's (5 % of land convective column-steps disagree) | series row 57; water diff 17r; land phase = host to 1.2e-10 of frozen mass (NM10 2.5e-2); land means at noise | PHYS | — (unconditional) | `ensfc2/`, `energy/` |
| E.2 | Noah-MP canopy wetted fraction hidden by any ice | closes; land canopy evaporation +36 % with option 2 | BUG | `noahmp_fwet_opt` (2; default 0) | `canopy/` |
| E.1 | NSST sea-spray explicit instability | oscillating cells 271 → 2 over 10 days; LH −0.21 W/m² | PHYS | `nst_spray_opt` (1) | `canopy/` |

### Passive tracers

| Item | What was wrong | Outcome | Class | Switch (recommended) | Report |
|---|---|---|---|---|---|
| SA1 (tracer) | develop's SAMF deep loses 2 %/day of non-PBL tracers | 1e-18 with SA1 (water diff 01) | BUG | — | `trsamf/` |
| FV2 | statein layer mass | 3e-15 → 2e-16 per day | BUG | — | `tracer/` |
| T1 (02b) | SAMF tracer update at Courant up to 5 | sub-stepped (o3 and TKE included); red-teamed | BUG | — | `trsamf/`, `trred/` |
| DRY (03b) | SAMF/PBL moist-basis transport vs dry write-back | uniform rms 1.07e-3 → 2.3e-5 | PHYS | — | `trsamf/` |
| DYN (v6) | FV3 water species limited separately; IC moist/dry; neg_adj | uniform 24 h max 9.8e-4 → 4.9e-13 | PHYS | `dry_tracer_adv`, `dry_tracer_ic` | `trdyn/` |
| INLQ | `inline_q` damping mass differs across PEs | mass 1–2e-9 → ≤ 8.4e-15 per day | BUG | — | `trdyn/` |
| F3 | SAMF scavenging booking off by one level; deposition never exported | (atm + deposition) −7.4e-4 → 3e-15 (2.4e-16 with FV2) | BUG + NUM | — (`cnv_wetdep` output) | `latent/` |

### Other suites and build

| Item | What was wrong | Outcome | Class | Switch (recommended) | Report |
|---|---|---|---|---|---|
| E.3 MYNN | surface-flux density, dew limiter always 0, filler weights; latent heat counted twice (+8.0 W/m²) | water → −5.5e-15; red-teamed | BUG | — | `suites/`, `mynnred/` |
| MYNN options | surface heat 1/Π; mixing θ_l vs static energy | close | NUM, PHYS | `mynn_sfc_heat`, `mynn_mix_sl` | `suites/` |
| E.4 GFDL MP v3 | mass basis (as TH1); sedimentation heat capacity of rain | water → −9.3e-16 | BUG | — | `suites/` |
| E.5 GF | shallow-only precipitation unreported, basis, closure | water → +2.5e-16; precipitation +8.9 % | BUG + NUM | `gf_closure` | `suites/` |
| PBL05 | satmedmfvdifq surface flux by ρ_a·Δz₁ (zero in p8 by construction) | 2.6e-8 → −3.6e-16 (GFDL suite) | NUM | — | `suites/`, `energy/` |
| SAMF08 | SAMF early return before the CA trigger (layout-dependent) | 3×8 = 4×6 bitwise | BUG | — | `suites/` |
| SAMF32 | the 32-bit SAMF build option reached 2 of 5 files | 5 of 5 | BUG (build) | — | `latent/` |

### MPAS (UFS-Chem-2 session)

| Item | Outcome | Switch (recommended) | Report |
|---|---|---|---|
| water, dry mass | 0 and −1.6e-16 | — | `mpas/` |
| physics and coupling energy | 0 with option B | `config_mp_energy_coupling` (stock default) | `mpas/` |
| dycore | 65 % explicit dissipation (design), 35 % open; fixer 3.81e5 → 1.31e5 J/m² with heating | `config_dissipative_heating` (2; default 0) | `mpas/` |

### Not defects

| Item | Finding | Report |
|---|---|---|
| SAMF-uninit | no uninitialised read; the step-1 divergence was ifort FMA contraction (use `-no-fma` for bitwise claims) | `samfinit/` |
| F2 / uniform structure | five generators located; all fixed above (DRY, DYN) | `trunif/` |
| Declared terms | surface hand-off (EV1 + LW2, +0.1135 in `full13`; run-specific), h2ophys (+1.44e-5), snow leaving as ice (−1.74e-3), ocean and runoff boundaries | `energy/`, `ensfc2/` |
| Design gaps left | GF two ice treatments (−0.26), GFDL MP v3 own constants (−0.03) | `suites/` |
