# Draft issues (not posted)

> **SUPERSEDED 19 October 2026.** The submission plan is `pr_round1.md`; the texts to post are
> `pr_round1_descriptions.md` (round 1) and `round2_issues.md` (round 2). Where each issue below went: 1 (water) →
> the round-1 PRs; 2 (FV3) → the round-1 GFDL issue and PR; 3 (NSST sea spray) → physics change E1, a later round;
> 4 (canopy wetness) → round 2, issue 2; 5 (MYNN) → round 2, issue 8; 6 (GFDL MP v3) → the round-1 GFDL MP v3 PR;
> 7 (Grell–Freitas) → round 2, issue 4. The numbers below predate later measurements; kept as written.

Seven issues: the main one for ufs-community/ccpp-physics, a short one for the FV3 dycore repository, where one of
the fixes lives, two ccpp-physics issues for things found along the way that are not water-conservation defects and
for which we propose no fix (an instability in the NSST sea-spray term; the wetted fraction of a Noah-MP canopy
holding both ice and liquid), two water defects in schemes outside the GFS v17 suite (MYNN; GFDL microphysics v3),
each with a tested fix, measured by a second session, and one more outside it with a tested candidate that changes
the forecast too much to propose without the owners (Grell–Freitas shallow convection). Text between the lines is ready to paste. Line numbers
are ufs-community/ccpp-physics `ufs/dev` @242a2fc, the commit `ufs-weather-model` `develop` pins.

---

## Issue 1 — ufs-community/ccpp-physics

**Title:** Physics does not conserve total water: +0.25 % of precipitation (SAMF, Thompson, Noah-MP coupling), with tested fixes

**Body:**

### Description

In UFS forecasts with `FV3_GFS_v17_p8_ugwpv1`, the physics creates water at **+0.25 % of precipitation on the first
day at C96** (+0.18 % per day over days 2–10, +0.45 % at C384). The dynamical core conserves water. We traced the error
to sixteen defects in ccpp-physics, plus one in the FV3 driver (filed separately); three more (NM7, NM8, NM11) are in the
energy that goes with the land's water. With the fixes we propose, the model conserves water to better than 10⁻⁶ kg/m² per
6 h, and the physics alone to 5 × 10⁻⁷ of precipitation, measured with in-model water meters every step; with TH8 as
well (held, below), to rounding (10⁻¹⁵).

| Fix | File (L = line on `ufs/dev` @242a2fc) | What goes wrong | Size |
|---|---|---|---|
| SA1 | `samfdeepcnv.f` L2551–2561, L2635–2645; `samfshalcnv.f` L1979–2005, L2040–2050 | cloud-base double-count correction subtracts the TVD-limited flux, not what the updraft took (also for transported tracers) | creates 0.8 % of convective rain |
| TH1 | `mp_thompson.F90` L690–704, L944–957 | humidity converted to mixing ratio with `/(1−q_v)`, back with `/(1+r_v,new)` | removes 0.4 % of grid-scale rain |
| TH2 | `module_mp_thompson.F90` L4044–4057 | cloud water settling out of the lowest layer not counted as precipitation; cloud sedimentation not substepped (unlike the other species), so a thin layer can lose more than it holds | removes 0.15 % of grid-scale rain |
| TH3 | `module_mp_thompson.F90` L3029, L3140–3198 | graupel gains not recomputed after the rate limiters (and the snow gain from rain–snow collection not limited with the rain loss) | creates 0.76 % of grid-scale rain in the first 6 h |
| TH4 | `module_mp_thompson.F90` L3386, L3660, L3743 | density recomputed after latent heating, before sedimentation | removes 0.11 % of grid-scale rain |
| TH5 | `mp_thompson.F90` L716 | layer depth from `phii`, computed before convection heats the column | removes 0.014 % of grid-scale rain |
| TH6 | `module_mp_thompson.F90` L4241–4300, L4310 | hydrometeors clipped at the end of the step are deleted; vapour below 10⁻¹⁰ is floored by creating water | creates 0.002 % |
| TH7 | `module_mp_thompson.F90` L2267–2343, L3322–3339, L6271, L6455 | hydrometeors at or below `R1` deleted on entry, in `semi_lagrange_sedim` (excluded from transport, output floored at `R1`) and after the source/sink terms | removes 2 × 10⁻⁸ of precipitation (not rounding: the same in double precision) |
| TH8 | `module_mp_thompson.F90` L3995, L4090, L4120, L4151 | sedimentation out of the lowest layer counted as precipitation only above `R1·rr_min` | removes 2 × 10⁻⁷ of precipitation |
| NM1 | `noahmpdrv.F90` L1526 | evaporation handed to the atmosphere as latent heat ÷ `con_hvap`, not the water Noah-MP removed (hvap/hsub differ) | atmosphere gains 0.07–0.10 % of global precipitation more than the land loses |
| NM2 | `GFS_surface_loop_control_part2.F90` L50; `noahmpdrv.F90` L953 | with `frac_grid`, coastal (wet and dry) cells are re-flagged for the second surface pass and Noah-MP steps their land again | land gains 3–5 % of global precipitation (24–27 % of land re-stepped) |
| NM3 | `GFS_surface_composites_pre.F90` L274 | with `frac_grid`, `weasd_lnd` (persistent land snow) overwritten with the cell-mean `weasd` every step | coastal snow diluted; thin snow lost |
| NM4 | `GFS_phys_time_vary.fv3.F90` L455–581 | at a cold start, Noah-MP snow layers built from `weasd`/`snowd`, not `weasdl`/`snodl` | 0.29 kg/m² of land snow lost on the first step |
| NM5 | `module_sf_noahmplsm.F90` L947, L2049, L8180 | snow without layers under 10⁻³ mm set to zero, water discarded | 0.009 % of global precipitation |
| NM6 | `module_sf_noahmplsm.F90` L7346, L7355 | canopy water or ice ≤ 10⁻⁶ mm set to zero, water discarded | 4 × 10⁻⁷ of land precipitation |
| NM7 | `module_sf_noahmplsm.F90` L7328, L7334 | negative transpiration heat (`fctr < 0`, 13 % of land column-steps) warms the canopy, but `etran = max(fctr/hvap, 0)` condenses no water | 0.024 W/m² per land column of latent heat with no water (energy, not water) |
| NM8 | `module_sf_noahmplsm.F90` L188–190; `module_sf_noahmp_glacier.F90` L27–29; `noahmpdrv.F90` | Noah-MP charges its own latent heats (2.5104e6, 2.844e6 J/kg) for the water it hands the atmosphere, which carries the host's | the land pays 0.4 % more latent energy than its vapour carries (energy, not water) |
| NM9 | `module_sf_noahmp_glacier.F90` L357, L2653, L3347; `noahmpdrv.F90` L960 | glacier snow set by assignment: reset to 600 mm every call, floored at 0.1 mm, zeroed when thin; the water goes nowhere | all snow and rain on land ice deleted and its sublimation created (one glacier column −860 mm over 120 days) |
| NM10 | `module_sf_noahmplsm.F90` L1094–1104 | with `opt_snf = 4` the microphysics' frozen share of grid-scale precipitation is applied to convective precipitation too | a trace of grid-scale snow turns convective rain on land into snow (phase, not water) |
| NM11 | `module_sf_noahmplsm.F90` L2224 (`energy`), L7169, L7187 (`water`) | the ground's vapour is charged at `hvap` when `tg` is above freezing, but taken from (or added to) the snow ice whenever there is snow | on thawing snow the land creates `hfus` per kg sublimated: 0.13–0.61 W/m² over a snow season, up to 78 W/m² per step (energy) |

NM10 is not a water defect: it is the Noah-MP phase rule that TH8 exposed. SA1 and TH1–TH8 change the
atmosphere's budget. NM1–NM9 and NM11 are at the land–atmosphere hand-off or inside the land model, which an
atmosphere-only budget cannot see.

### How we measured

- Regression cases `control_p8_ugwpv1` (C96, 24 h and 240 h) and `control_c384` (24 h), Intel, `-D32BIT=ON`, on
  current `develop` @112b1d46 and on UFS-Chem v1 (He et al. 2026, an older UFS).
- Global budgets from the output with exact cell areas, the per-process `dtend` diagnostics, and diagnostic builds
  with in-model water meters: the whole physics every step, Thompson stage by stage, the dynamical core, the
  land–atmosphere hand-offs, and Noah-MP's own storage terms. The meters change no answers.
- A second team compared 24-h forecasts with and without each fix against the spread of bit-perturbed initial
  conditions: most fixes are within it; SA1 slightly warms the lowest layers, and NM1–NM4 and NM11 change land fields
  beyond it, as expected from what they fix.
- Each fix was built and run separately. `develop` + all fixes closes the C96 budget to 0.00000 kg/m² per 6 h in
  every window; with SA1 and TH1–TH4 only, −0.005 % of precipitation, and with SA1, TH1–TH4 and NM1 −0.006 % per day over 10 days, without drift.

### Solution

We have a tested fix for each, as one commit per fix against `ufs/dev` (and the same series against NCAR `main`), and
are happy to open PRs. One is held: booking all of the flux (TH8) also books a trace of Thompson's `R1` placeholder,
which settles as if it were mass (we have a fix for that too), and genuine traces of snow that land on a Noah-MP
canopy as trace ice, which hides the canopy's water (issue 4). TH8 waits for that. Most fixes are a few lines. NM2
needs the same optional argument in NOAA-EMC/noahmp's copy of the Noah-MP driver, which its land component compiles
against; we have that change too. They change answers, so baselines will change. A detailed write-up with the evidence
for each is available.

### Related

- Owners (ccpp-physics `CODEOWNERS`): SA1 @JongilHan66, @lisa-bengtsson (SAMF); TH1–TH9 @gthompsnWRF, @RuiyuSun,
  @AndersJensen-NOAA (Thompson); NM1, NM2, NM5–NM11 @barlage, @cenlinhe (Noah-MP); NM3 and NM4 are in the
  `GFS_surface_composites_pre` and `GFS_phys_time_vary.fv3` interstitials, which have no scheme owner. Reviewers on
  every file: @grantfirl, @rhaesung, @Qingfu-Liu, @dustinswales. NM2's companion in NOAA-EMC/noahmp
  (`drivers/ccpp/noahmpdrv.F90`, no `CODEOWNERS`; most commits by Ufuk Turuncoglu and Tseganeh Gichamo).
- NCAR/ccpp-physics#582 (Noah-MP should use host constants): NM8 does this for the three latent heats.
- NM9 books glacier ice as negative subsurface runoff (`drain`), which hosts read as liquid; a frozen-runoff flux would
  close the energy too.
- The same Thompson defects (TH2–TH4, TH6) exist in the WRF and MPAS copies and in TEMPO; TH1 also in TEMPO's CCPP driver.
  NM5, NM6 and NM7 are also in NOAA-EMC/noahmp, and NM6 and NM7 in NCAR/noahmp v5.
- The FV3 driver part is filed at NOAA-GFDL/GFDL_atmos_cubed_sphere (issue 2 below).
- Other suites, measured but not located: `FV3_GFS_v16_csawmg` (Chikira–Sugiyama convection, Morrison–Gettelman
  microphysics) creates about +10.5 % of precipitation per 6 h in a 24-h C96 forecast, with or without these fixes. We
  have not traced it further. `FV3_RAP` loses 2–7 %; that is Grell–Freitas shallow convection (issue 7).

*The code analysis was done with the help of an AI coding assistant (Claude); every defect was confirmed by building
and running the model, and every fix was tested on current `develop`.*

---

## Issue 2 — NOAA-GFDL/GFDL_atmos_cubed_sphere (`dev/emc`)

**Title:** UFS driver: physics layer pressure built with the dycore's single-precision `rdgas`

**Body:**

`atmos_phys_driver_statein` (`driver/UFS/atmosphere.F90` @71ff473, L2298) gives the physics the layer pressure
`prsl = dm·rTv/Δφ` with `rTv = rdgas·T·(1 + zvir·q)`. The physics turns `prsl` back into density with its own
`con_rd` (the boundary layer's `ρ_a`, Noah-MP's `density`). In a 32-bit build `rdgas` is single precision
(287.04998779 for 287.05), so that density is 4.25 × 10⁻⁸ smaller than the layer's actual mass per volume `dm/Δφ`.
The boundary layer adds surface evaporation as `evap·del/(g·dz)` but books it, and Noah-MP debits it, as `evap·ρ_a`:
the atmosphere receives 4 × 10⁻⁸ of evaporation more than the land loses.

**Low priority.** The effect is bookkeeping, about 3 × 10⁻⁸ kg/m² per 6 h, but it is the last mismatch between the
water the land loses and the water the atmosphere gains, and closing it lets the budget close to rounding.

**One way to fix it** (tested, one commit): compute `rTv` with `con_rd` and `con_fvirt` from `physcons` (the driver
already uses `GFS_typedefs`, which uses `physcons`). This closes the hand-off to 5 × 10⁻¹⁶ of evaporation over a
24-h C96 run (`control_p8_ugwpv1`, 32-bit). The forecast change is within the spread of bit-perturbed initial
conditions. 64-bit builds should be bit-identical (both gas constants are 287.05 in double precision; not run), so
only 32-bit baselines change. In hydrostatic runs (or with
`use_hydro_pressure`) the same `rTv` builds `phii`, so the fix moves the geopotential by the same 4 × 10⁻⁸ and leaves
`prsl` unchanged; that is consistent too. The `MULTI_GASES` branch is not changed.

**You may prefer another way.** After this change the `prsl` handed to the physics differs from the dycore's own
pressure by 4 × 10⁻⁸. The physics could instead use the dycore's constants, or the two could share one set; the
dycore's single-precision `grav` also differs from `con_g` (by 1.65 × 10⁻⁸), with no water effect we can measure.
Any of these closes the water; ours touches the fewest lines. It could also be bundled with other `dev/emc` driver
changes rather than go in on its own.

Owners: the repository has no `CODEOWNERS`. `dev/emc` pull requests are merged by @vithikashah001 and approved by
@lharris4 and @JosephMouallem; most recent commits to `driver/UFS/atmosphere.F90` are by @dustinswales.

*Found with the help of an AI coding assistant (Claude); confirmed by building and running the model.*

---

## Issue 3 — ufs-community/ccpp-physics (NSST sea spray)

**Title:** Sea-spray term (`lseaspray`) is explicit and overshoots in tropical-cyclone winds: 2Δt oscillation and blow-up in the lowest layer

**Body:**

### Description

With `lseaspray = .true.` (the GFS v17 P8 default), `sfc_nst.f90` (L640–663 on `ufs/dev` @242a2fc; `sfc_ocean.F`
L236–259 has the same code) adds a spray evaporation and sensible-heat term:

```
evaps   = conlf*ws10**5.4*ru10*bb1 * rho_a*hvap*(qss1 - q0)    ! qss1 = qs(t1), ws10 capped at ws10cr = 30 m/s
evap    = evap + alps*evaps
hflx    = hflx + bets*hflxs - (alps - gams)*evaps
```

The flux is computed from the lowest layer's state at the start of the step and applied over the whole step. In
tropical-cyclone winds it is far too large for that: in a C96 L127 run (lowest layer about 22 m, dt = 720 s, 10-m wind at
the 30 m/s cap) the spray term alone would relax the layer's saturation deficit in about 180 s, a gain of about 14 per
step, and still more than 2 after the boundary layer's implicit mixing spreads it upward. The lowest layer then
oscillates every other step:

1. A warm, subsaturated step gets a large spray flux; the boundary-layer tendency cools the lowest layer by 1–5 K and
   moistens it past saturation.
2. Thompson microphysics condenses the excess and heats the layer back.
3. The next step starts cool and near saturation: spray is about 0, and the bulk sensible flux warms the layer by about
   2 K. The cycle repeats.

When the layer becomes warmer than the sea surface, the deficit `qs(t1) − q1` and the spray grow together and the layer
runs away: in one eyewall column the boundary-layer tendency went −4.8, −5.3, −6.5, −13, −48 K per step while Thompson
returned +4.9, +5.4, +8.6, +27, +94 K, and the run stopped with NaN a few steps later (lowest-layer temperature
above 400 K; `fpvs` beyond boiling gives `qss1` > 1).

### How we found and checked it

UFS-Chem v1 (an older UFS, He et al. 2026), `control_p8_ugwpv1` C96 extended to 10 days from 2021-03-22 06Z, Intel,
32-bit: a blow-up at step 771 (day 6.4) in the eyewall of a model cyclone near 73E, 12S. Metered per-scheme tendencies
in the lowest layer, from the same restart at step 700:

| Run | Lowest layer |
|---|---|
| as is | oscillation grows, NaN at step 771 |
| `lseaspray = .false.` | no oscillation (boundary-layer change ≤ 0.7 K per step) |
| dt = 360 s | oscillation bounded (±1–2 K per step) |

- The excess surface evaporation equals the spray formula at the 30 m/s cap on every step, and the predicted spray
  sensible flux matches the measured one (−0.81 vs −0.78 K m/s at one step, −1.68 vs −1.78 at another).
- Radiation, gravity-wave drag, convection and the dynamical core change the lowest layer by less than 0.5 K per step
  during the onset; deep convection switching on and off every other step is a consequence, not the cause.
- The same physics with our unrelated water-conservation changes reverted oscillates the same way; whether a run blows
  up is chaotic (a 10⁻¹² perturbation of one column's temperature at step 1 changes it).
- The code is identical on `ufs/dev`; we have not yet reproduced the oscillation on current `develop`.

### Possible remedies (not tested as proposals)

- Couple the spray fluxes implicitly with the boundary layer's tridiagonal solve, as the bulk fluxes effectively are
  through the exchange coefficients, or substep them.
- Evaluate the deficit at the sea-surface (or droplet) temperature rather than the air temperature, which keeps the
  spray from growing once the air is warmer than the sea.
- A limiter that stops one step's spray from taking the layer past saturation removes the oscillation, but in our
  cyclone it cut spray about tenfold, so we do not propose it.

### Related

- Owners: @XuLi-NOAA (`sfc_nst`), @HelinWei-NOAA (`sfc_ocean`).
- Not a water-conservation defect: the water the spray adds is booked as surface evaporation.

*Found with the help of an AI coding assistant (Claude); confirmed by building and running the model.*

---

## Issue 4 — ufs-community/ccpp-physics (Noah-MP canopy wetness)

**Title:** Noah-MP: any canopy ice sets the canopy's wetted fraction from the ice alone, hiding the liquid

**Body:**

### Description

`module_sf_noahmplsm.F90` computes the canopy's wetted fraction twice per step, in `precip_heat` (L1389) and in
`canwater` (L7378), on `ufs/dev` @242a2fc:

```
      if(canice.gt.0.) then
           fwet = max(0.,canice) / max(maxsno,1.e-06)
      else
           fwet = max(0.,canliq) / max(maxliq,1.e-06)
      endif
      fwet = min(fwet, 1.) ** 0.667
```

With any canopy ice at all, the liquid is ignored. Because the ice capacity `maxsno` is about 50 times the liquid
capacity `maxliq`, a canopy holding 0.4 mm of liquid and 10⁻¹⁵ mm of ice is treated as nearly dry: canopy
evaporation stops (`cew`, `vege_flux` L4246–4253) and transpiration takes the whole canopy (`ctw`, L4255). `fwet` also
sets the canopy temperature during melt and freeze (L7393, L7400) and the snow optical fraction in `twostream`
(L3615–3617).

### What we measured

- Single-column `noahmpdrv_run` harness, two days, dt = 600 s: a tropical column with 0.4 mm of canopy liquid and a
  trace of canopy ice evaporated 4 % less than the same column without the trace.
- Taking the larger of the two fill fractions, `fwet = max(canice/maxsno, canliq/maxliq)`, removes the switch: the
  two phases occupy the same leaves (rain on intercepted snow, meltwater within it, a freezing film), so the larger
  footprint sets the wetted area. Their sum gives nearly the same result.
- But in 24-h C96 forecasts (`control_p8_ugwpv1`, GFS v17 P8) that change moves the land far beyond the spread of
  bit-perturbed initial conditions (land, 0–24 h means): canopy evaporation +19 %, snow sublimation −13 %, land latent
  heat −0.44 %, land 2-m temperature −0.09 K, land 2-m humidity −0.5 %, with signals in the lowest model levels and at
  500 hPa.
- Mixed-phase canopies are common: 45–48 % of wet-canopy steps in the March case. On those steps `fwet` averages
  0.09 today, against 0.58 from the liquid alone, so the switch is not a rare trace effect.
- A continuous form that keeps single-phase canopies exactly as today, each phase's fill fraction weighted by its
  share of the canopy water,

  ```
        cantot = max(0.,canice) + max(0.,canliq)
        if(cantot.gt.0.) then
             fwet = ( max(0.,canice) * min(max(0.,canice) / max(maxsno,1.e-06), 1.)   &
                    + max(0.,canliq) * min(max(0.,canliq) / max(maxliq,1.e-06), 1.) ) / cantot
        else
             fwet = 0.
        endif
        fwet = min(fwet, 1.) ** 0.667
  ```

  moves `fwet` on mixed steps to 0.51–0.54 and the forecast about as much as the larger-fraction form. (Impacts
  measured with an earlier version of this diff are withdrawn: it declared a local `cwat`, shadowing Noah-MP's
  specific heat of water. A clean re-measurement of both forms, on a base with other land options changed, gives
  canopy evaporation +32 to +36 % and land latent heat +1.2 to +1.5 %, 0–24 h means.) Water still closes.

### Why an issue, not a PR

Removing the switch is plausibly more physical, but it changes land-surface behaviour enough to need evaluation
against observations, which we have not done. NCAR's Noah-MP v5 already moved part of the way: `CanopyHydrologyMod.F90`
(L104–108) uses the phase with more mass, while `CanopyWaterInterceptMod.F90` (L132–137) keeps the original switch.
We would like the Noah-MP owners' view on the intended treatment of a mixed-phase canopy, and on the blend above.
With it, the fix in issue 1 that counts all surface sedimentation in Thompson (held, TH8) no longer changes the land
beyond noise; without it, TH8's genuine traces of snow become canopy ice that hides the liquid.

### Related

- Owners: @barlage, @cenlinhe.
- Found while tracing a land-evaporation change caused by a trace of grid-scale snow (fix NM10 in issue 1 handles the
  precipitation-phase side).

*Found with the help of an AI coding assistant (Claude); confirmed by building and running the model.*

---

## Issue 5 — ufs-community/ccpp-physics (MYNN surface moisture flux)

**Title:** MYNN-EDMF adds more surface moisture than the surface scheme removes (+2 to +3.5 % of precipitation in the MYNN suites)

**Body:**

### Description

In 24-h C96 forecasts the suites with the MYNN-EDMF boundary layer create water: +2 to +3.5 % of precipitation per
6 h (`FV3_GFS_v17_p8` with MYNN, `FV3_HRRR`, `FV3_RRFS_v1beta`, `FV3_RRFS_v1nssl`), against 0.00 % for the same
model with the GFS v17 P8 suite after the fixes in issue 1. Two defects in `module_bl_mynn.F90` (`ufs/dev` @242a2fc)
explain it:

1. **The surface flux is scaled by the wrong density.** The driver sets the kinematic flux `flqv = qfx/rho1(kts)`
   (L1069), but `mynn_tendencies` adds it as `rhosfc*flq`, `rhosfc*flqc` and `rhosfc*qvflux` (L4391, L4456, L4521),
   with `rhosfc = psfc/(R_d*(tk(kts)+p608*qv(kts)))` (L4137). The water added is `rhosfc/rho1` times the evaporation
   handed in. `rhosfc` also has a typo: `tk + p608*qv` should be `tk*(1 + p608*qv)`. Net: +0.85 % of evaporation.
2. **The dew limiter zeroes all dew.** For a downward vapour flux, `qvflux = max(qvflux, min(0.9*sqv(kts) - 1e-8,
   0.0)/dtz(kts))` (L4514) gives 0 whenever `sqv(kts)` > 1.1 × 10⁻⁸, i.e. always. The atmosphere loses no vapour to
   dew while the surface scheme books it as removed: +0.55 to +0.9 % of evaporation. The comment ("do not allow
   specified surface flux to reduce qv below 1e-8 kg/kg") suggests `-max(0.9*sqv(kts) - 1e-8, 0.0)/dtz(kts)` was
   intended.

### Fix (tested)

Use `rho(kts)`, the density the driver divided by, in the three surface sources, and the intended limiter. With both,
`FV3_GFS_v17_p8` with MYNN closes to 0.00 % of precipitation per 6 h; `FV3_HRRR` and `FV3_RRFS_v1beta` are within
−0.03 to −0.10 %, the known bias of the per-scheme diagnostic (`FV3_RRFS_v1nssl` keeps NSSL microphysics residuals).
Not changed: the same `rhosfc/rho1` factor multiplies the sensible-heat flux and the momentum drag (energy and
momentum, not water).

### Also worth a look

`mynnedmf_wrapper.F90` (L627–632) clips the incoming moisture flux to [−2 × 10⁻⁴, 5 × 10⁻⁴] kg m⁻² s⁻¹; where it
binds, the atmosphere receives a different flux from the one the surface removed. We did not measure how often.

### Related

- Owner: @joeolson42.
- Forecast impact of the fix not yet assessed.

*Found with the help of an AI coding assistant (Claude); confirmed by building and running the model.*

---

## Issue 6 — ufs-community/ccpp-physics (GFDL microphysics v3 mass basis)

**Title:** GFDL microphysics v3 (CCPP): species returned per (dry air + new vapour) while the host rebuilds mass from the old thickness

**Body:**

### Description

`gfdl_cloud_microphys_v3_mod.F90` (`ufs/dev` @242a2fc) converts the host's specific ratios to mixing ratios with
`1/(1 − qv)` (L973–985) and back with `1/(1 + qv_new)` (L1218–1232), returning an updated `delp` that makes the pair
consistent. The CCPP driver `gfdl_cloud_microphys_v3.F90` keeps `delp` in a local array (L174, L240, L263), so the
host never sees it: FV3 rebuilds each species' mass as the pre-physics thickness × the returned value, and every
species comes back scaled by (m_d + m_v,old)/(m_d + m_v,new). Net condensation creates water; net evaporation removes
it. This is the same defect as Thompson's fix TH1 in issue 1; GFDL microphysics v1 does it right.

### Measured (24-h C96, `FV3_GFS_v17_p8` with GFDL MP v3)

The suite's total is −0.3 % of precipitation per 6 h, with the microphysics at −1.0 % of grid-scale precipitation.
Converting back with the input humidity (`con_r8 = 1/(1 − qv(i,k))` in the non-inline branch) closes the suite to
0.00 %. The same correction could instead go in the CCPP driver, rescaling the returned species by the returned
`delp` over the host's; that leaves the scheme module unchanged for other hosts.

### Related

- Owner: @RuiyuSun.
- Forecast impact of the fix not yet assessed.

*Found with the help of an AI coding assistant (Claude); confirmed by building and running the model.*

---

## Issue 7 — ufs-community/ccpp-physics (Grell–Freitas shallow precipitation)

**Title:** Grell–Freitas: shallow-only columns apply the shallow drying but report no precipitation

**Body:**

### Description

In `cu_gf_driver.F90` (`ufs/dev` @242a2fc) a column with shallow convection gets `cutens = 1` (L699), and its shallow
tendencies are always applied to vapour (L951) and condensate (L993). But `raincv` includes the shallow precipitation
`cutens*prets` only when deep convection is active (L1034, `pret > 0`); otherwise it holds only the mid-level term
(L1037). In shallow-only columns the water the shallow scheme removes leaves the run: it is in no precipitation field
(`raincv`, `rainc`, `tprcp`, the buckets, or `raincprv` for RUC).

### What we measured

24-h C96 `rap_control` (`FV3_RAP`), with water metered inside the model on unmodified `develop` (metered output
byte-identical to unmetered):

- The dynamical core and the physics→dynamics hand-off close to 10⁻⁶ kg/m² per 6 h; the physics loses 2–7 % of
  precipitation per 6 h.
- Grell–Freitas loses 0.036–0.040 kg/m² per 6 h (30–34 % of its own precipitation) after the first window. Shallow-only
  columns account for all of it (−0.038 to −0.042); deep columns gain +0.002–0.003.
- MYNN's surface-flux gain (issue 5, +0.012 per 6 h) partly hides it; with the issue 5 fix the suite loses 5–9 %.

### Why the obvious patch is wrong

Adding `cutens*prets` to `raincv` in the `pret <= 0` branch would overshoot. In shallow-only columns `prets` is
0.054–0.064 kg/m² per 6 h, while the tendencies remove 0.038–0.042, so that fix would turn the loss into a gain of
0.010–0.022. `cu_gf_sh.F90` is not consistent with itself: `pre` sums `pwo(k)*xmb` over levels (L999), while the
vapour tendency removes `0.5*(pwo(k)+pwo(k+1))*g/dp` (L821), and the scheme mixes mixing ratios with specific
humidity.

### A tested candidate

Take the shallow precipitation from the water GF's applied tendencies actually remove, in the host's layer mass
(adds `prsi` to `cu_gf_driver_run`; GF has no caller outside the CCPP caps):

- shallow-only columns: `raincv` = −Σ (`ten_q(ntqv)` + `dcliw` + `dclcw`)·dt·Δp/g;
- deep columns: the shallow part of the applied update replaces `cutens*prets`; mid columns unchanged;
- floored at zero.

On `rap_control` (24-h C96, metered; metered output byte-identical to unmetered), GF's residual falls from −0.036 to
−0.040 kg/m² per 6 h to +0.004–0.005. What remains is the floor: in 3.7 % of shallow-only column-steps the applied
tendencies add water (net moistening, cause not diagnosed; −0.45 mm at most in one step), and reporting it as
negative rain would send negative precipitation to RUC. Without the floor the shallow-only class closes to 10⁻¹⁶;
applied to every GF column (deep and mid included) GF closes to 10⁻¹⁶.

It changes the forecast well beyond the spread of bit-perturbed initial conditions, because the water that used to
vanish now falls: global precipitation +8.6 % (convective +34 %), land latent heat +0.3 W/m², RUC top-layer soil
moisture +1 × 10⁻³ m³/m³ (37× noise), land 2-m temperature −0.01 K at 12 h; atmospheric temperature, humidity and
precipitable water stay within noise. All 44 `rt.conf` tests on GF suites (Intel and GNU, debug and 32-bit physics
included) run to completion with no floating-point errors; decomposition, threading and restart stay bit-reproducible;
baselines change. That size of change in `FV3_RAP` precipitation needs the owners' judgement, and a decision on net
moistening, before it can be a PR.

### Related

- Owner: @haiqinli (CODEOWNERS for `CONV/Grell_Freitas/cu_gf*`); RUC land, which receives the rain: @tanyasmirnova.
- The deep branch has the same `prets` inconsistency, with the opposite sign (the small gain in deep columns).

*Found with the help of an AI coding assistant (Claude); confirmed by building and running the model.*

---
