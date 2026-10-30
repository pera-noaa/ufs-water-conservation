**Title:** `tempo_main` creates and removes water

---

**Describe the bug**
In UFS, TEMPO creates +0.38 % of its own precipitation, 6–24 h into a C96 run, once the driver's mass basis is fixed (ufs-community/ccpp-physics#407, which quotes +0.33 % from an earlier meter). Most of it comes from one sign in `semilagrangian_sedimentation`, which v3 inverted. Of three smaller leaks, one adds to it and two offset part of it:

| | Leak | 6–24 h | 0–6 h |
|---|---|---|---|
| 1 | Semi-Lagrangian fallback sign | creates 0.58 % | creates 0.65 % |
| 2 | Graupel gains not recomputed after the rain and snow limits | creates 0.004 % | creates 0.86 % |
| 3 | Sedimentation uses the density after latent heating | removes 0.12 % | removes 0.12 % |
| 4 | Cloud water settling out of the column isn't counted | removes 0.14 % | removes 0.20 % |

These are percentages of TEMPO's grid-scale precipitation, from an in-model water meter.
- **Each row leaves one fix out** of a build with all the others.
  - For rows 2–4 that build closes to 2e-7.
  - For row 1 it's the build without the `r1`-floor change, because that change pays the floor from vapour and hides row 1. That build leaves 0.001 %.
- **The rows add up.** In the original code, fix 1 alone removes 0.64 %. Rows 2–4 and the driver's layer depth (−0.01 %, ccpp-physics) sum to −0.26 %, which is what the run with only fix 1 measures.
- **What's left.** Fixes 1–4 and the driver fix leave about 0.001–0.003 %, from water at or below `r1`.

Links are to `main` (c62699f). The draft GPU port (#57) carries the same lines.

**1. Fallback sign** ([L1911](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1911)). The piecewise-linear safeguard of Juang and Hong (2010, eq. A4) falls back to piecewise constant where either edge value is negative. Up to v2, TEMPO tested `qpi(k).lt.0.0` ([v2, L3313](https://github.com/NCAR/TEMPO/blob/19eaf25f9cb672846778aa23a6fb453067a03a5d/module_mp_tempo_main.F90#L3313)), as Thompson does. v3.0.0 (#24) changed it to `qpi(k) > 0`. Now it falls back in almost every cell and keeps the linear profile only where the upper edge is negative. Those negatives are then raised to the floor at [L1984](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1984), which creates water.
```fortran
        if(qpi(k) < 0._wp .or. qmi(k) < 0._wp) then
```
This changes forecasts, not only the budget. With `sedi_semi = .true.`, as UFS runs TEMPO, rain and graupel fall as they did in v2. In this run, grid-scale precipitation over 6–24 h is 5 % lower. Always falling back (`qpi = qmi = qa`) also closes the budget (0.001 %), and its precipitation is within 0.6 % of the corrected test's. So the 5 % comes from the cells where v3 keeps a linear profile with a negative upper edge. Constant everywhere is not a way to keep v3's precipitation.

**2. Graupel** ([L1590–1623](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1590-L1623)). As computed, rain–snow and rain–ice collection conserve: `prg_rcs = −(prr_rcs + prs_rcs)` and `prg_rci = pri_rci + prr_rci`. Two steps then limit the losses and leave the graupel gains alone ([`prg_rcs`, L2991](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L2991-L2998); [`prg_rci`, L3339](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L3339)):
- the per-term clamps at L2995–2998;
- `check_over_depletion`, which scales `prr_rci`, `pri_rci`, `prr_rcs` and `prs_rcs`.

The fix recomputes the gains after `check_over_depletion`. Below freezing, the rain limit can leave snow gaining more than the rain it takes, so the fix first caps that gain:
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
The cap puts the whole limit on graupel. Scaling snow's gain by the rain limit would keep the snow–graupel split instead. I ran both: both close to 2e-7, and their precipitation differs by 0.03 %. The leak comes mostly during spin-up.

**3. Density** ([L512](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L512), [L605](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L605), [L633](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L633)). After the tendencies, condensation and rain evaporation, `rho` is recomputed from the heated temperature. Sedimentation then converts between mixing ratio and mass with it. `dz1d` doesn't change during the call, so a new `rho` implies a different layer mass. There are two fixes:
- **Entry density** (what I measured): keep `rho` at the entry density for conversions, and pass the updated density only to `thermo_vars`, for fall speeds and ventilation.
- **Updated depth:** with each new `rho`, set `dz1d` to the layer mass over `rho` and rescale the stored mass and number densities.

In Thompson, both close to rounding in UFS, and their precipitation differs by up to 0.3 % globally and 0.65 % in regional tests.

**4. Cloud settling** ([L810](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L810-L811), [L886](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L886-L887)). Cloud water that settles out of the lowest layer goes into `cloud_precip`. The driver never passes `cloud_precip` out; only `freezing_rain` uses it, so freezing rain can exceed `rain_precip`. Cloud also sediments in a single step where the other species substep, so where `vt·dt > dz` a layer can lose more cloud than it holds. There are three fixes; which to use is your call:
- **Count it:** add `cloud_precip` to `rain_precip` and substep cloud with the same Courant rule. This is what I measured, and it matches how `freezing_rain` already treats it.
- **Separate output:** return it as its own drizzle or fog-deposition output, for the host to add.
- **Don't settle it:** don't let cloud settle out of the lowest layer.

**To Reproduce**
UFS `control_p8_ugwpv1_tempo`, C96, 24 h, with TEMPO 2856696 (UFS's pin). All four patterns are the same in `main`. A meter in `mp_tempo_run` adds each column's water change, in the host's layer mass, to the precipitation the call produced, and sums them area-weighted. This is one case, so the sizes will vary from case to case. I have patches for `main`, one per fix, and can open PRs; fix 1 could go in alone.

**System Environment**
- OS: Rocky Linux 9 (NOAA Hercules)
- Compiler: Intel Fortran Classic, oneAPI 2024.2.1 (spack-stack 1.9.2)
- MPI: Intel MPI 2021.13
- Configure options: UFS `compile.sh`, `-DAPP=ATM -D32BIT=ON`
