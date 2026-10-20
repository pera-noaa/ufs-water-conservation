# MPAS-conservation: water, dry mass and energy for MPAS-Dev `develop` aa6d8cd69

**Status.** Nothing is posted. The 14 patches apply with `git am` to aa6d8cd69. Each one can be taken alone, in
order. 0011–0014 are behind `&nhyd_model` switches; with every switch at its default the forecast is bit-identical
to 0001–0009.

0012 and 0014 are opt-in PHYSICS CHANGES whose defaults keep stock behaviour. For 0012 that is Ash's decision: the
default stays option A (stock coupling).

Over 24 h in the supercell with 0001–0013 and `layer` + fixer:
- water −1.6e-16 relative;
- dry mass 0;
- energy +1.9e-16 relative.

Physics and coupling close genuinely. The fixer closes the dycore residual. 65 % of that residual is explicit
diffusion and damping removing KE without heating (design), which 0014 can return as heat. The other 35 % is
open.

Measurements: `../../../../conservation/mpas/report.md` (0012 impact §6, 0014 §10).

| patch | label | what it changes |
|---|---|---|
| 0001 | BUG FIX | Thompson water budget: settling, graupel re-closure, sedimentation density, clips (TH2–TH4) |
| 0002 | BUG FIX | Thompson: water at or below R1 goes to vapour instead of being deleted (TH6, TH7) |
| 0003 | BUG FIX | Thompson: substepped cloud sedimentation; snow gain from rain-snow collection capped (TH2/TH3 completion) |
| 0004 | BUG FIX | Thompson: layer mass from MPAS's dry-air density (TH5-MPAS) |
| 0005 | BUG FIX | monotonic scalar transport: upwind step kept positive definite (Skamarock 2006 renormalisation) |
| 0006 | BUG FIX | `config_positive_definite` implemented for scalar transport |
| 0007 | BUG FIX | scalar transport and physics guard: round-off negatives removed without adding mass, column-local |
| 0008 | BUG FIX | Thompson: all sedimentation out of the lowest layer counted as precipitation (TH8) |
| 0009 | BUG FIX | Thompson: the R1 placeholder not sedimented as mass (TH9) |
| 0010 | INSTRUMENTATION | Thompson exports the applied sedimentation per layer (read only by 0012) |
| 0011 | INSTRUMENTATION | `config_energy_meter`: EB budget lines; reproducing global sums; restart totals; test-only heating/cooling switches |
| 0012 | PHYSICS CHANGE, opt-in | `config_mp_energy_coupling = 'layer'` (default `'stock'`): layer-local constant-volume coupling with E's latent heats plus the frictional heating of falling water (option B) |
| 0013 | FIXER | `config_energy_fixer`: uniform ΔT per step restores the run's initial E net of precipitation; reproducible across decompositions and restarts |
| 0014 | PHYSICS CHANGE, opt-in | `config_dissipative_heating` (default 0): KE removed by u del2/del4/vertical diffusion, w diffusion, divergence damping and the w absorbing layer returned as heat (the MPAS analogue of FV3's d_con). 2 (recommended) = positive-definite dissipation in summation-by-parts form, rescaled per step to the work; 1 = local work (signed), for comparison. Reproducible, restart-safe |

TH8 and TH9 (0008–0009) are in this series on the user's instruction for MPAS. They **remain held for UFS** and every
other copy (`../held/`).

The subject lines of 0001–0013 read `n/13` because they were exported before 0014 existed. Their content is identical
to a 14-patch export.

| gate | result |
|---|---|
| `git am` on fresh aa6d8cd69 through 0011, 0012, 0013; builds | PASS (job 10152081) |
| 0011, 0012, 0013 with their switches off vs 0001–0009 (closure.nc, 24 h) | PASS bit-identical, each |
| default namelist, 0012 and 0014 each vs 0001–0011: closure.nc straight and at 7 tasks; 24 h restart file straight and after 12 h + 12 h | PASS bit-identical, all 8 (job 10153963); known-bad heating on vs off FAILS |
| 0013 with `layer` + fixer + meter vs the release candidate | PASS bit-identical |
| 0012 with `layer` alone (meter on): microphysics + coupling ΔE over 24 h | 0 (−7.1832e5 + 7.1832e5 J/m²) |
| release candidate (= 0001–0013 less the test cooling): meter on vs off | PASS bit-identical |
| v4 (the same energy code without the EF columns and test switches): 16 vs 7 vs 12 tasks; straight vs 12 h + 12 h restart | PASS bit-identical |
| 0014 (v3, as delivered) default vs 0001–0011: closure.nc straight and at 7 tasks; 24 h restart straight and after 12 h + 12 h | PASS bit-identical, all 4 (job 10155426) |
| 0014 switch 0 with `layer` + fixer + meter vs 0013 | PASS bit-identical (job 10155426) |
| 0014 option 2: 16 vs 7 tasks; straight vs 12 h + 12 h restart | PASS bit-identical, both (job 10155425); known-bad option 2 vs 1 FAILS |
| 0014 option 1: 16 vs 7 tasks; straight vs 12 h + 12 h restart | PASS bit-identical, both (v2 build, job 10153970; v3's option 1 is the same algorithm, within noise of it) |
| 0014 on: heating closure per step; fixer with vs without heating | ≤1.4e-6 J/m²; 1.31e5 vs 3.81e5 J/m² over 24 h |
