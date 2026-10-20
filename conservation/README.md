# Energy and passive-tracer conservation in UFS

Follow-on to the water closure (`../proposal/water_closure_proposal.md`). Goal: machine-precision conservation of total
energy and passive-tracer mass over a 24-h forecast, with the same standard of fix as the water work.

## Status

| Quantity (C96 L127, dt 720 s, 24 h, `FV3_GFS_v17_p8_ugwpv1`, every switch on) | Result |
|---|---|
| Total energy, residual net of declared boundary and source terms (`full14`) | +1.6 × 10⁻¹² W/m² |
| Largest single scheme gap | ≤ 1.2 × 10⁻¹² W/m² |
| FV3 `consv_te` fixer correction | −0.304 W/m² (control −0.570) |
| Passive-tracer mass | ≈ 3 × 10⁻¹⁵ per day |
| Uniform dry tracer, 24-h max deviation | 4.9 × 10⁻¹³ |
| Gates (restart, 3×8 vs 4×6, switches off, meters passive), `-no-fma` builds | bitwise |
| Diff series (55 diffs) replayed on the base vs `full14` | identical; 24-h runs, all-on and default-off, byte-identical |

The final tree is `full14` (all-on bitwise identical to `full13`). Open: the regression baselines (564 GB) and canopy
build trees (4.8 GB) on Hercules are approved for deletion, pending a run by Ash; canopy `runs/` is deleted.
Submission: round 1 (38 bug fixes, nothing posted) in `../proposal/pr_round1.md`. Every item, with its outcome, class and switch: `TRACKER.md`.

## Documents

| File | What it is |
|---|---|
| `../proposal/conservation_proposal.md` | the proposal (draft, not posted); Part V of the SEWG packet |
| `../proposal/pr_round1.md` | submission plan, round 1: PRs, branches, checks, procedure |
| `../proposal/pr_round1_descriptions.md`, `../proposal/round2_issues.md` | issue and PR texts, round 1; issue drafts, round 2 |
| `../proposal/conservation_patches.md` | patch manifest |
| `replay/SERIES.md` | the verified apply order; `replay/apply_series.sh`, per-repository diffs in `replay/repo_diffs/` |
| `TRACKER.md` | one row per item, current state |
| `AGENT_RULES.md` | rules every agent in this project followed |
| `*.history.md` | earlier versions, verbatim |

## Workstreams

Each folder has a `report.md` (status first) and, where it got long, a `report.history.md` with the full record.
Hercules work for each is in `$U/cons/<folder>` (`$U = /work2/noaa/co2/ash/ufs-chem-v1/upstream`).

| Folder | Subject |
|---|---|
| `energy/` | integrator: total-energy meter, master budget, final trees `full10`–`full14` |
| `tracer/` | passive-tracer mass meters, develop control, FV2 |
| `trunif/` | where structure in uniform tracer fields comes from |
| `trsamf/`, `trred/` | SAMF tracer sub-stepping and dry write-back; red team |
| `trdyn/` | FV3 dry-consistent tracer transport and IC, `inline_q` mass fix |
| `enpbl/` | PBL dissipative heating (`dspheat_ke`) |
| `encnv/` | SAMF and GWD heating (D3a, D3b, D4, D12, D4n) |
| `encpl/`, `fwred/` | physics–dycore coupling of water mass and energy; red team of the flow-work term |
| `ensfc/`, `ensfc2/` | surface energy: Noah-MP, NSST, sea ice |
| `nm12/` | Noah-MP snow-layer combine melt-out water loss |
| `preclag/` | precipitation enthalpy hand-off lag |
| `latent/` | SAMF scavenging booking and export, SAMF32 build option, `tend_opt` paths |
| `canopy/` | Noah-MP canopy wetted fraction (E.2), TH8/TH9, NSST sea spray (E.1) |
| `suites/`, `mynnred/` | MYNN-EDMF, GFDL MP v3, Grell–Freitas; red team |
| `fv3tally/`, `dycred/` | FV3 dycore energy per term, `dyn_te_exact`; red team |
| `samfinit/` | suspected uninitialised read (none; FMA contraction) |
| `replay/` | reproduces the tested tree from the diff series |
| `mpas/` | MPAS-A (owned by the UFS-Chem-2 session) |

Rules that held throughout: fixes are classed bug fix / physics change / numerical consistency; behaviour changes are
behind switches that default to off and are bitwise when off; every gate is shown able to fail; claims of a core
defect get an independent red team; cross-build bitwise claims use `-no-fma`.
