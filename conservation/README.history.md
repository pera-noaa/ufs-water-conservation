# Energy and passive-tracer conservation in UFS (follow-on to the water closure)

Goal (Ash, 17 Oct 2026): UFS-Chem conserves total energy and passive-tracer mass to machine precision over a 24 h run,
by fixes of the same standard as the water set (01–19 + 09b): each defect explained in the code, closed by a meter,
red-teamed, no change beyond its own signal. Regression suite not required for this stage.

| work | report | candidate diffs | Hercules root |
|---|---|---|---|
| passive tracer mass | `tracer/report.md` | `tracer/patches/` | `$U/cons/tracer` |
| total energy | `energy/report.md` | `energy/patches/` | `$U/cons/energy` |

`$U` = `/work2/noaa/co2/ash/ufs-chem-v1/upstream`. Base tree: `$U/p20rt_final/ufs-weather-model`
(develop @112b1d46 + 01–19 + 09b), built with a 64-bit dycore. Case: `control_p8` C96, 24 h, dt 720 s.
Meters are instrumentation, kept apart from fix diffs. Nothing is posted upstream.

## Round 2 (17 Oct, after the first breakdowns)

| agent | items | local folder |
|---|---|---|
| tracer | done: develop control, dry-ratio per process, T1 causal, May drift explained, PBL-mixing table | `tracer/` |
| trunif | DIAGNOSIS (Ash, 17 Oct): where structure in uniform fields is generated — shadow tracer reset to uniform before each process; offline SAMF replay bisecting the tracer update; dycore limiters; external_ic remap | `trunif/` |
| trsamf | SA1-only confirmation of develop's 2 %/day SAMF tracer loss; T1 tracer sub-stepping; dry-mixing-ratio transport in SAMF/PBL | `trsamf/` |
| energy | done: full13 +1.6e-12 W/m² all-on, all gates bitwise (final integrated tree) |
| replay | done: series reproduces full13 byte-for-byte; per-repo diffs | `replay/` |
| writer | done: `proposal/conservation_proposal.md`, `proposal/conservation_patches.md` | `../proposal/` |
| preclag | done: lag closed exactly (01_PL1); 16b meta fix | `preclag/` |
| fv3tally | done (v2): D1/D2/D3 d_con/Rayleigh heating defects, fixer −0.57 → −0.30; +0.41 adiabatic OPEN | `fv3tally/` |
| dycred | done: D1–D3 CONFIRMED; fix generality corrections (moist_cv, dry branch) | `dycred/` | `energy/` |
| encnv | D3a SAMF detrained ice hfus; D3b SAMF CMT heating; D4 GWD drag heating | `encnv/` |
| enpbl | D1 PBL dissipative heating vs resolved KE loss | `enpbl/` |
| encpl | D2 coupling water-mass enthalpy/PE (frame per Lauritzen et al. 2022); D5 Thompson Kirchhoff | `encpl/` |
| ensfc | surface energy: Noah-MP, NSST, sea ice, D11 hand-off | `ensfc/` |
| UFS-Chem-2 (other session) | MPAS water, dry mass, energy | `mpas/report.md` |
| nm12 | done: Noah-MP snow-layer combine melt-out water/energy loss; fix `isnow < -1` (diffs 20/20b) | `nm12/` |
| fwred | red team of encpl flow work (bit 2) | `fwred/` |
| trdyn | done (04_INLQ + v6 + 02b/03b): FV3 dry-consistent tracer advection/remap (`dry_tracer_adv`) and dry IC (`dry_tracer_ic`); uniform tracer 24 h max 4.6e-13 | `trdyn/` |
| trred | done: 02 sub-step keep, donor start drop; 03 sound; latent F3 (scavenging booking index), SAMF32 build flag | `trred/` |
| samfinit | done: no uninitialized read; step-1 divergence is ifort FMA contraction (use -no-fma for bitwise-inert checks) | `samfinit/` |
| ensfc2 | done: diffs 08–16, surface closes to round-off (soil 4.3e-8 initial state) | `ensfc2/` |
| latent | done: F3 SAMF scavenging booking + wet-deposition export; SAMF32 CMake flag; TOPT tend_opt combinations | `latent/` |
| canopy | done: 01 E.2 fwet opt, 03 TH9, 04 E.1 spray; reconciling larger-fraction numbers | `canopy/` |
| suites | done: series 01–08 (MYNN, GFDL v3, GF, satmedmfvdifq, SAMF CA decomposition) | `suites/` |
| mynnred | done: all CONFIRMED; 01b needs snow-fill completion | `mynnred/` |

Shared rules: `AGENT_RULES.md`. Each change is classed BUG FIX or PHYSICS CHANGE; physics changes go to Ash with impact numbers.
