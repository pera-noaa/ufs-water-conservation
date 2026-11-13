# MPAS-A water, dry-mass and energy conservation: supercell, 24 h

## Status

- **Answer.** With the MPAS-conservation series MPAS-A conserves dry mass exactly, water to round-off, and physics +
  coupling energy genuinely (E as §1). Of the dycore's energy loss, 65 % is KE removed by explicit diffusion and
  damping with no heat returned (DESIGN); 35 % is **OPEN** (advection, PGF, buoyancy, acoustic steps; §4). A
  labelled, reproducible fixer (0013) closes both (§9).
- **Opt-in, default stock** (stock latent heating is consistent, §2): 0012 layer coupling (option B; Ash's decision)
  and 0014 dissipative heating (option 2 recommended) strengthen the storm beyond noise; precipitation does not (§6, §10).
- **Where the fix went:** [`MPAS-conservation/`](../../../patches/ports/MPAS-conservation/README.md), 14 patches
  for MPAS-Dev `develop` aa6d8cd69, every gate passing (§8). Not posted. TH8/TH9 are in this series; for UFS they are one unconditional diff in round 2.

| 24 h | stock | 0001–0007 | + TH8/TH9 (0008–0009) | + 0012 layer + 0013 fixer |
|---|---|---|---|---|
| ΔW/W | 1.3e-3 | ~1e-9 (−4.7e-8 kg/m²) | 2.2e-15 | −1.6e-16 |
| ΔMd/Md | ≤7e-15 | ≤7e-15 | ≤7e-15 | 0 (exact) |
| ΔE/E | — | — | −4.3e-4 | +1.9e-16 |
| fixer ΔE, J/m²: 0014 off / option 2 | | | | 3.81e5 / 1.31e5 |

Case: supercell (init case 5), 84×84 doubly periodic 2 km hexes, 40 levels, 20 km lid, double precision, dt 12 s,
Thompson, no surface fluxes or radiation, 24 h, 16 tasks; the storm lives ~8 h. Hercules: `$R/e24/` (`$R = /work2/noaa/co2/ash/ufs-chem-v1/upstream/mpas`).

## Current answers

## 1. Energy definition (the model's own)

E = IE + PE + KEh + KEw + Lv0·Wv − Lf0·(Wi + Pice) [+ g·z_sfc·P], per unit area, with IE = cv_d·T_m·dm,
T_m = θ_m·exner(ρ_zz, θ_m) (the EOS MPAS integrates), PE = (1+qt)·g·z_mid·dm, KE = (1+qt)·K·dm (Ringler cell KE
plus interface w²/2), dm = ρ_zz/rdzw. Liquid is the zero; vapour Lv0 = 2.0587e6, ice −Lf0 = −3.34e5. Condensate
carries no heat capacity; vapour's is cv_d·Rv/Rd = 1154 J/kg/K (MPAS's θ_m). Precipitation leaves with zero energy
(ice −Lf0).

## 7. Classification

| change (series patches) | class | effect, 24 h |
|---|---|---|
| Thompson 0001–0004, dynamics v2 0005–0007 | BUG FIX (water) | ΔW/W 1.3e-3 → 1e-9 |
| TH8/TH9 0008–0009 (in the MPAS series; UFS and other copies: round 2) | BUG FIX (water) | 1e-9 → 2e-15 |
| sedimentation export 0010, meter 0011 | INSTRUMENTATION | bit-identical when off |
| layer-local coupling 0012 (option B) | PHYSICS CHANGE (frictional heating of falling water, E's latent heats), opt-in | §6; default stays stock (option A), Ash's decision; §6 is the justification for offering it |
| global energy fixer 0013 | FIXER (labelled), not a fix | reproducible |
| dissipative heating 0014 | PHYSICS CHANGE (KE removed by explicit diffusion and damping returned as heat; option 1 local work, option 2 positive-definite), opt-in | §10; fixer −65 %; stronger updrafts |

Inactive defects logged, not fixed (inactive in this configuration): condensate zeroing above config_microphysics_top
deletes water and latent heat; vertical θ mixing not in flux form (v_theta_eddy_visc2 > 0); Kessler top-layer rdzk on
stretched grids; LBC operator precedence; precipw uses rho_p/(1+qv) on an already-dry density; odd
number_of_sub_steps; IAU/LBC density mismatch with rho_zz_int.

## 9. Closure statement (24 h supercell, 16 tasks; with the series and switches layer + fixer)

| quantity | 24 h change | nature |
|---|---|---|
| dry mass | 0 (exact) | genuine |
| water | −1.6e-16 relative | genuine (needs TH8/TH9) |
| energy, physics + coupling | 0 to 1e-7 J/m²; gate ≤ 9e-6 J/m² per column-step | genuine (option B) |
| energy, dycore: KE removed by explicit diffusion and damping (per-term, §4) | −2.48e5 J/m² (65 % of the dycore's −3.78e5) | DESIGN: dissipation without heating, closed by the labelled fixer; returned as heat with the opt-in 0014 (§10) |
| energy, dycore: remainder (advection, PGF, buoyancy, acoustic steps) | −1.31e5 J/m² (35 %) | **OPEN: not split further, closed by the fixer** |
| energy, total with the fixer | +1.9e-16 relative | by construction |


## Section register

| Section | Subject | Status | Lives in |
|---|---|---|---|
| Status (18 Oct 2026) | case, closure, Ash's 0012 decision, deliverable | superseded by Status (head) | `report.history.md` |
| §1 Energy definition (the model's own) | E, its terms and zero | current | `report.md` |
| §2 Per-process budget (meter, stock coupling, no fixer) | ΔE by process; stock latent heating consistent; option B = Pauluis + Kirchhoff-slope terms | current (evidence) | `report.history.md` |
| §3 Layer-local coupling (option B) and the Hpe check | option B construction, column gate, Hpe sanity table | current (evidence) | `report.history.md` |
| §4 Dycore residual | variants, dry thermals, per-term tally v2: explicit 65 % DESIGN, remainder 35 % OPEN | current; its v1 tally (88 % / 79 %, jobs 10153199, 10153200) withdrawn, corrected in place by v2 | `report.history.md` |
| §5 Reproducible fixer (v4) | fixed-point sums; decomposition and restart gates | current (evidence) | `report.history.md` |
| §6 Option-B impact against noise | storm measures against noise controls; why 0012 is offered | current (evidence) | `report.history.md` |
| §7 Classification | class per patch; inactive defects logged | current | `report.md` |
| §8 Deliverable: `patches/ports/MPAS-conservation/` | 14 patches, generators, gates | current (evidence); the series README repeats the gates | `report.history.md` |
| §9 Closure statement | 24 h closure per quantity | current | `report.md` |
| §10 Dissipative heating (0014, opt-in) | options 1 and 2, densities, impact, gates | current; option 2 recommended, option 1 kept for comparison | `report.history.md` |

History: [`report.history.md`](report.history.md) holds the previous text verbatim, §1–§10 included.
