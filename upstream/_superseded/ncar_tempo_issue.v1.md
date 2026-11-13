**Title:** `tempo_main` creates and removes water

---

**Describe the bug**
In UFS, TEMPO creates water: +0.38 % of its own precipitation, 6–24 h into a C96 run, once the driver's mass basis is fixed (ufs-community/ccpp-physics#407). Most of that comes from one sign in `semilagrangian_sedimentation`. Three smaller leaks offset part of it. I isolated each one with an in-model water meter, leaving its fix out of a build that otherwise closes to rounding:

| | Leak | 6–24 h | 0–6 h |
|---|---|---|---|
| 1 | Semi-Lagrangian fallback sign | creates 0.64 % | creates 0.72 % |
| 2 | Graupel gains not rescaled by `check_over_depletion` | creates 0.004 % | creates 0.86 % |
| 3 | Sedimentation uses the density after latent heating | removes 0.12 % | removes 0.12 % |
| 4 | Cloud water settling out of the column isn't counted | removes 0.14 % | removes 0.20 % |

These are percentages of TEMPO's grid-scale precipitation. The rows add up: with fix 1 applied, 2–4 and the driver's layer depth (−0.01 %, ccpp-physics) sum to −0.26 %, which is what the run measures. Links are to `main` (c62699f).

**1. Fallback sign** ([L1911](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1911)). The piecewise-linear safeguard of Juang and Hong (2010, eq. A4) falls back to piecewise constant where either edge value is negative. TEMPO tests `qpi(k) > 0`, while Thompson's copy tests `qpi(k).lt.0.0` ([ccpp-physics L6351](https://github.com/ufs-community/ccpp-physics/blob/9b65688ca82fad3f87801799f82d30ba7fe00007/physics/MP/Thompson/module_mp_thompson.F90#L6351)). As a result it falls back in almost every cell and keeps the linear profile only where the upper edge is negative. Those negatives are then raised to the floor at [L1984](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1984), which creates water.
```fortran
        if(qpi(k) < 0._wp .or. qmi(k) < 0._wp) then
```
This changes forecasts, not only the budget. With `sedi_semi = .true.`, as UFS runs TEMPO, rain and graupel fall with the published piecewise-linear profile, and grid-scale precipitation over 6–24 h is 5 % lower.

**2. Graupel** ([L1590–1623](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1590-L1623)). `check_over_depletion` scales down the rain and ice lost to rain–ice collection (`prr_rci`, `pri_rci`), and the rain and snow lost to rain–snow collection (`prr_rcs`, `prs_rcs`). It doesn't scale the graupel they make (`prg_rci`, [L3339](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L3339); `prg_rcs`, [L2991](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L2991-L2998)), so whenever a limiter acts, graupel is created. The fix recomputes the gains after the limiters, after first capping snow's gain from rain–snow collection at the rain it takes, so that `prg_rcs` can't go negative:
```fortran
      if (temp(k) < t0 .and. tend%prs_rcs(k) > -tend%prr_rcs(k)) tend%prs_rcs(k) = -tend%prr_rcs(k)
      ...
      tend%prg_rci(k) = tend%pri_rci(k) + tend%prr_rci(k)
      tend%pbg_rci(k) = meters3_to_liters*tend%prg_rci(k)/rho_g(nrhg)
      if (temp(k) < t0) then
        tend%prg_rcs(k) = -(tend%prr_rcs(k) + tend%prs_rcs(k))
        tend%pbg_rcs(k) = meters3_to_liters*tend%prg_rcs(k)/rho_g(nrhg)
      endif
```
It's mostly a spin-up leak.

**3. Density** ([L512](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L512), [L605](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L605), [L633](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L633)). After the tendencies, condensation and rain evaporation, `rho` is recomputed from the heated temperature, and sedimentation converts between mixing ratio and mass with it. `dz1d` doesn't change during the call, so a new `rho` implies a different layer mass. Keeping `rho` at the entry density, and passing the updated density only to `thermo_vars` for fall speeds and ventilation, closes it.

**4. Cloud settling** ([L810](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L810-L811), [L886](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L886-L887)). Cloud water that settles out of the lowest layer goes into `cloud_precip`, which feeds only the freezing-rain diagnostic, so it leaves the column uncounted. Cloud also sediments in a single step where the other species substep, so where `vt·dt > dz` a layer can lose more cloud than it holds. One fix adds `cloud_precip` to `rain_precip` and substeps cloud with the same Courant rule. Another is not to let cloud settle out of the lowest layer. That choice is yours.

**To Reproduce**
UFS `control_p8_ugwpv1_tempo`, C96, 24 h, with TEMPO 2856696 (UFS's pin). All four patterns are the same in `main`. A meter in `mp_tempo_run` adds each column's water change, in the host's layer mass, to the precipitation the call produced, and sums them area-weighted. This is one case, so the sizes will vary from case to case. I have patches for `main`, one per fix, and can open PRs.

**System Environment**
- OS: Rocky Linux 9 (NOAA Hercules)
- Compiler: Intel Fortran Classic, oneAPI 2024.2.1 (spack-stack 1.9.2)
- MPI: Intel MPI 2021.13
- Configure options: UFS `compile.sh`, `-DAPP=ATM -D32BIT=ON`
