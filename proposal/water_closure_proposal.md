# Proposal: closing the total-water budget in UFS physics

*Draft for the CCPP physics maintainers, the SAMF, Thompson and Noah-MP scheme owners, and the FV3 `dev/emc`
maintainers. Ash Pera (NOAA GML / CIRES) with Lori Bruhwiler, 15 October 2026. Not yet posted. The investigation in the
order it happened is in `water_closure_proposal.history.md`. Submission is by owner, in rounds: `pr_round1.md` (SA1,
TH1–TH7, NM1–NM6, NM8, FV1, 09b, re-cut on current heads) and `round2_issues.md` (TH8, NM7, NM9, NM10/17r, NM11).*

## Summary

**The problem.** In a UFS forecast with the GFS v17 P8 physics (`FV3_GFS_v17_p8_ugwpv1`), the physics creates water:
**+0.25 % of precipitation on the first day at C96**, +0.18 % per day over days 2–10, and **+0.45 % at C384**. The
dynamical core conserves water; the physics and its coupling to the land model do not.

**The cause.** Twenty-one small defects, each measured in the model, each with a tested fix:
- **17 lose or create water:** SA1, TH1–TH8, NM1–NM6, NM9 and FV1;
- **3 lose or create the energy that goes with the land's water:** NM7, NM8 and NM11;
- **1 gives precipitation the wrong phase:** NM10.

All are in current upstream code: ccpp-physics `ufs/dev`, except FV1, which is in the FV3 `dev/emc` driver. None has
been reported or fixed upstream.

**What we propose.** Twenty of the fixes, as 19 diffs (TH2 and TH3 share one), plus a companion change in
NOAA-EMC/noahmp (09b). **TH8 is held**, with the placeholder fix TH9 that goes with it. TH8 is right for Thompson, but
it sends traces of snow to Noah-MP, where any canopy ice hides the canopy's liquid (section 7, Appendix E.2). The
conservation follow-on (`conservation_proposal.md`) proposes TH8 with TH9 made unconditional, together with a
switch for the Appendix E.2 wetted fraction.

Five more problems turned up along the way: an instability in NSST's sea-spray term, the wetted fraction of a
mixed-phase Noah-MP canopy, and water defects in MYNN-EDMF, GFDL microphysics v3 and Grell–Freitas shallow
convection. They are not part of this proposal and are reported separately (Appendix E).

| Fix | Where | What goes wrong | Size without the fix | Diff |
|---|---|---|---|---|
| **Convection (SAMF)** | | | | |
| SA1 | `samfdeepcnv.f`, `samfshalcnv.f` | the cloud-base correction subtracts a flux-limited value, not what the updraft took | creates **0.8 % of convective rain**; also changes convectively transported tracers | 01 |
| **Thompson microphysics** | | | | |
| TH1 | `mp_thompson.F90` | humidity converted in and out with different denominators | removes **0.4 % of grid-scale rain** | 02 |
| TH2 | `module_mp_thompson.F90` | cloud water settling out of the lowest layer is not counted as precipitation; cloud sedimentation is not substepped, so a thin layer can lose more than it holds | removes 0.15 % of grid-scale rain | 03 |
| TH3 | `module_mp_thompson.F90` | graupel gains not recomputed after the rate limiters | creates 0.76 % of grid-scale rain in the first 6 h, 0.03 % after | 03 |
| TH4 | `module_mp_thompson.F90` | density recomputed after latent heating, before sedimentation | removes 0.11 % of grid-scale rain | 04 |
| TH5 | `mp_thompson.F90` | layer depth taken from heights computed before convection | removes 0.014 % of grid-scale rain | 05 |
| TH6 | `module_mp_thompson.F90` | hydrometeors clipped at the end of the step are deleted, and vapour below its floor is topped up from nothing | creates 0.002 % | 06 |
| TH7 | `module_mp_thompson.F90` | hydrometeors at or below the `R1` threshold deleted on entry, in semi-Lagrangian sedimentation and after the source/sink terms | removes 2 × 10⁻⁸ of precipitation | 07 |
| TH8 | `module_mp_thompson.F90` | sedimentation out of the lowest layer counted as precipitation only above a threshold | removes 2 × 10⁻⁷ of precipitation | held |
| **Noah-MP land model and its coupling** | | | | |
| NM1 | `noahmpdrv.F90` | evaporation handed to the atmosphere as latent heat ÷ a different constant | atmosphere gains **0.07–0.10 % of global precipitation** more than the land loses | 08 |
| NM2 | `GFS_surface_loop_control_part2.F90`, `noahmpdrv.F90` | with `frac_grid`, coastal land is stepped twice per time step | land gains **3–5 % of global precipitation** | 09 |
| NM3 | `GFS_surface_composites_pre.F90` | coastal land snow overwritten every step with the cell mean | thin coastal snow lost | 10 |
| NM4 | `GFS_phys_time_vary.fv3.F90` | cold-start snow layers built from the cell-mean snow | **0.29 kg/m²** of land snow lost on the first step | 11 |
| NM5 | `module_sf_noahmplsm.F90` | snow without layers under 10⁻³ mm deleted | removes 0.009 % of global precipitation from the land | 12 |
| NM6 | `module_sf_noahmplsm.F90` | canopy water or ice at or below 10⁻⁶ mm deleted | removes 4 × 10⁻⁷ of land precipitation | 13 |
| NM7 | `module_sf_noahmplsm.F90` | negative transpiration heat (condensation) warms the canopy but no water condenses | Noah-MP's latent energy exceeds its water's by 0.024 W/m² per land column (energy, not water) | 14 |
| NM8 | `module_sf_noahmplsm.F90`, `module_sf_noahmp_glacier.F90`, `noahmpdrv.F90` | Noah-MP charges its own latent heats (2.5104e6, 2.844e6 J/kg), not the host's | the land pays 0.4 % more latent energy than its vapour carries (energy, not water) | 15 |
| NM9 | `module_sf_noahmp_glacier.F90`, `noahmpdrv.F90` | glacier snow is set by assignment: reset to 600 mm every call, floored at 0.1 mm, truncated when thin; the water added or removed goes nowhere | all snow and rain on land ice deleted, its sublimation created (a glacier column −860 mm in 120 days, single-column harness) | 16 |
| NM10 | `module_sf_noahmplsm.F90` | with `opt_snf = 4` the microphysics' frozen fraction of grid-scale precipitation is applied to convective precipitation too | a trace of grid-scale snow turns convective rain on land into snow (not water: phase) | 17 |
| NM11 | `module_sf_noahmplsm.F90` | the ground's latent heat follows the ground temperature, but its vapour comes from the snow ice whenever there is snow | on thawing snow the land creates the fusion heat of the ice it sublimates: 0.13–0.61 W/m² over a snow season, up to 78 W/m² in one step (energy, not water) | 18 |
| **FV3 driver** | | | | |
| FV1 | FV3 `driver/UFS/atmosphere.F90` | the physics' layer pressure built with the dycore's single-precision gas constant | atmosphere gains 4 × 10⁻⁸ of evaporation more than the land loses | 19 |

Labels name each fix's home: SA (SAMF), TH (Thompson), NM (Noah-MP and its coupling), FV (FV3 driver); the diff
numbers follow the same order. Earlier drafts used A–O, C1–C3 and M1–M5 (mapping in Appendix A). Sections 1–4 give
line numbers.

**The result**, with the proposed fixes (C96, 24 h; section 6):

| Part | Residual | / precipitation |
|---|---|---|
| Physics, every step and column, double precision (upstream `develop` + all proposed diffs) | −5.5 × 10⁻⁷ kg/m² in 24 h before NM11, −5.4 × 10⁻⁷ with it; one-signed; largest column 2 × 10⁻⁴: Thompson's sub-threshold surface sedimentation, which the held TH8 counts | 5 × 10⁻⁷ |
| The same with TH8 as well | −1 × 10⁻¹⁴ kg/m² in 24 h (v1 snapshot: −4 × 10⁻¹⁵); largest column 2 × 10⁻¹³ | 10⁻¹⁵ (rounding) |
| Dynamical core and physics → dynamics update | < 3 × 10⁻⁷ kg/m² per step, both signs (32-bit rounding; ~10⁻¹² in 64-bit) | < 10⁻⁶ per 6 h |
| Land → atmosphere evaporation (NM1, FV1) | 5 × 10⁻¹⁶ of evaporation | — |
| Land → atmosphere precipitation | exact (10⁻¹⁶) | — |
| Land → atmosphere latent energy (NM8) | 0 W/m² (from +0.131 W/m² per land column, 0.41 % of land latent heat) | — |
| Noah-MP's own water vs latent heat (NM7) | +0.0012 W/m² per land column (from −0.023), the canopy evaporation cap (section 7) | 4 × 10⁻⁵ of land latent heat |
| Noah-MP's own water check | −1.2 × 10⁻⁸ mm summed over 1.77 million land column-steps | rounding |
| Current upstream `develop` + all diffs, total budget | 0.00000 kg/m² per 6 h in every window | < 7 × 10⁻⁶ |

**Why it matters to us.** NOAA's UFS-Chem reanalysis group plans multi-decade runs with prognostic CO2, CH4 and SF6.
Water closure is a standing requirement for reanalysis budgets (Zhang et al. 2018 for E3SM; Becker et al. 2022 for
the IFS). Fix SA1 also applies to every tracer SAMF transports. With two passive tracers in the v1 snapshot (meters
inside the model, 10 days), deep convection without SA1 changed a tracer's global mass by −0.28 %/yr or +0.04 %/yr,
depending on its vertical profile, persistently; with SA1 the physics conserves tracer mass to 10⁻¹⁸. On `develop`
(64-bit, 24 h, C96) the size depends on whether the PBL also mixes the tracer: +1.4 × 10⁻⁵ per day (~0.5 %/yr) for a
PBL-mixed GHG-like tracer, but −2 % per day for a tracer the PBL does not mix, whose cloud-base profile keeps local
extrema where the limiter switches off. SA1 alone brings both to 10⁻¹⁸. The whole model then conserves tracer mass to
about 2 × 10⁻¹⁶ per day; the dynamical core conserves it to below one rounding unit per step.

## 1. Convection: fix SA1

**The defect.** In `samfdeepcnv.f` (`ufs/dev` line numbers):
1. The updraft starts at cloud base `kb` with the environment's value, `qcko(i,kb) = qo(i,kb)` (L1622); the downdraft
   starts at `jmin` with `qrcdo(i,jmin) = qo(i,jmin)`.
2. The compensating-subsidence flux at each interface uses the TVD-limited value `tem1` (NCAR/ccpp-physics#754, 2021).
3. To avoid counting the cloud-base flux twice, the code subtracts it in advance (L2551–2561), using `eta·tem1` and
   `edto·etad·tem1`. But the updraft removed `eta·qo(kb)`. Wherever the limiter is active, the difference is water
   created or destroyed:

   ΔW = xmb·Δt·[η(k_b)·(qo(k_b) − tem1(k_b)) + edto·η_d(j_min)·(qo(j_min) − tem1(j_min))]

The tracer loop repeats this with `ctro` (L2635–2645). `samfshalcnv.f` has the equivalent at `kb` (L1979–2005, tracers
L2040–2050).

**The fix** (diff 01). In both schemes the cloud-base face of the TVD flux carries what the updraft takes,
`eta·qo(kb)` (deep also `edto·etad·qo(jmin)`; tracers `ctro`), and deep's double-count subtraction uses the same values.
Layer `kb` is then unchanged and `kb+1` loses what the updraft took, as in SAMF's moist static energy budget. Changing
only deep's subtraction would instead heat layer `kb`, by 0.07 K per convecting column-step on average (up to 1.35 K).
An untested alternative is to start the updraft from the limited value (`qcko(kb) = tem1`).

**Measured.**
- Single column, unmodified Fortran, dt = 720 s: all seven cases created water, 0.05 % of rain on smooth profiles and
  4 % (deep) and 23 % (shallow) on jagged ones. A red-team harness (about 12,000 synthetic L127 soundings) found a median
  of 3.5–8.7 % and a maximum of 33 %. With the fix every case closes to ≤ 2 × 10⁻¹⁴ kg/m² (tracers ≤ 6 × 10⁻¹⁷), with
  column moist static energy closed.
- Full model: the convection residual falls from +0.78 % to 0.00 % of convective rain at C96 (v1), and at C384 from
  +0.97 % to within the per-scheme split's resolution (`develop`; section 6).
- Negative-value borrowing (Han et al. 2022) is needed as often with the fix as without (97 of 327 916 and 104 of
  330 557 deep-convecting column-steps, 24 h at C96).

**Questions for the SAMF owners.**
1. Was `tem1` here intentional, for example to keep the cloud-base layer positive?
2. Are there other places where a TVD-limited flux meets an exact parcel source? Our single-column budget closes to
   round-off after this fix, which suggests not.
3. Do you prefer this form to starting the updraft from the limited value?

## 2. Thompson microphysics: fixes TH1–TH7 (and TH8, held)

Line numbers are `ufs/dev`. Measured effects are on the v1 snapshot at C96, as percentages of grid-scale
precipitation (P_grid), each relative to the build before it.

**TH1, mass basis** (diff 02, `mp_thompson.F90`). FV3 passes the physics its tracers per (dry air + vapour), and
rebuilds each species' mass afterwards as the pre-physics thickness × the returned value (`atmosphere.F90`, `dev/emc`,
L1659–1677). `mp_thompson.F90` converts to mixing ratios with `/(1 − q_v)` (L690–704) but back with `/(1 + r_v,new)`
(L944–957), so every species comes back scaled by (m_d + m_v,old)/(m_d + m_v,new): net condensation creates water, net
evaporation removes it. **Fix:** convert back with `×(1 − spechum)`, the unchanged input both ways, as GFDL
microphysics does (Zhou, Harris and Chen 2022, §2.4). **Measured:** −0.67 % → −0.30 % of P_grid. TEMPO's CCPP driver
has the same conversion; WRF and MPAS pass dry mixing ratios, so TH1 cannot occur there.

**TH2, fog settling** (diff 03, L4044–4057). The cloud-water sedimentation loop moves `sed_c(kts)` out of the lowest
layer but never adds it to a precipitation total, though the water really leaves (fog and drizzle deposition). The
loop also takes one full time step, while the other species are substepped so that no layer's outflow exceeds its
content (L3808, 3873, 3922, 3950). Where `vtck·DT > dz` (the lowest L127 layer is about 20 m thick), a layer loses more
cloud than it holds, and zeroing the negative creates water. **Fix:** count `sed_c(kts)` in `pptrain`, and substep
cloud sedimentation by the same rule; with one substep the result is bit-identical. **Measured:** −0.30 % → −0.15 % of
P_grid. Over ten days the single-step sedimentation also created water: the daily surface cycling reset sea-ice skin
temperature by up to 27 K, the sublimation pulse into a thin lowest layer over Hudson and Ungava Bays drove cloud
Courant numbers near 2, and the vapour floor created up to 1.2 × 10⁻² kg/m² in a column. With the substepping the
10-day physics residual is −8.8 × 10⁻¹⁴ kg/m².

**TH3, graupel after the rate limiters** (diff 03). Rain collecting snow below 0 °C conserves water by construction,
`prr_rcs + prs_rcs + prg_rcs = 0`, until the clips (L2796–2798) and limiters (L3140–3176) rescale `prr_rcs` and
`prs_rcs` but not `prg_rcs`; `prg_rci` (L3029) is likewise not recomputed after them (L3189–3198). **Fix:** recompute
both graupel gains after the limiters, with the snow gain from this collection capped at the rain lost to it.
**Measured:** a source of 0.76 % of P_grid in the first 6 h of a cold start, about 0.03 % after. We have not tested
whether analysis increments in a cycled system cause similar bursts.

With TH2 and TH3, the negative hydrometeors Thompson leaves at the end of the step (which TH6 repays from vapour) fall
from 2.2 × 10⁻⁵ to 1.3 × 10⁻⁸ kg/m² over 24 h, and the most negative layer from −4.1 × 10⁻³ to −1.5 × 10⁻¹⁰ kg/kg.

**TH4, sedimentation density** (diff 04). Thompson's entry density `rho = 0.622·p/(R·T·(qv+0.622))` times dz is the
host's dry-air layer mass, but it recomputes `rho` from the updated temperature three times before sedimentation
(L3386, L3660, L3743), so each kilogram that falls out removes about 1 + ΔT/T kilograms of host water. **Fix:** use the
entry density for all mass conversions and the updated one only for fall speeds and viscosity. **Measured:** −0.18 % →
−0.07 %.

**TH5, layer depth from the host's layer mass** (diff 05, `mp_thompson.F90` + `.meta`). The driver takes `dz` from
`phii` (L716), computed before convection heats the column, so ρ·dz drifts from the host's layer mass. **Fix:** pass
`prsi` (already in UFSATM and SCM metadata) and set the depth from the host's dry-air layer mass and Thompson's own
entry density, at every inner step (`dt_inner` < `dt_atmos`, the regression suite's default). **Measured:** removes
0.014 % of P_grid; with five inner steps, a depth fixed for the whole step lost 0.026 % of precipitation over 24 h. On
the v1 snapshot ρ must use Thompson's own gas constants (287.04, 0.622); upstream Thompson takes the host's.

**TH6, clipped condensate and the vapour floor** (diff 06). Hydrometeors that end the step negative or below `R1` are
deleted (L4241–4300), and vapour is floored at 10⁻¹⁰ (L4310), creating whatever is missing. **Fix:** exchange clipped
hydrometeors with vapour, with the matching latent heat; refill vapour below the floor first from the same layer's
condensate, then from the column's other vapour, mass-weighted. **Measured:** removes a 0.002 % source. In a red-team
harness that compiles the real driver, five columns that the floor and the driver's neighbour-average fixer had given
+0.77 to +1.52 kg/m² close to ≤ 4 × 10⁻¹⁵ kg/m².

**TH7, water at the `R1` threshold** (diff 07). Thompson treats hydrometeors at or below `R1` = 10⁻¹² as absent and
deletes them in three places: on entry (L2267, 2294, 2323, 2334, 2343); in semi-Lagrangian sedimentation
(`semi_lagrange_sedim`, L6271, 6455), which leaves such inputs out of the transport and floors its output at `R1`; and
after the source/sink terms, where leftover rain ≤ `R1` is discarded (L3322–3339). **Fix:** on entry and for the
leftover rain, the water goes to vapour with its latent heat, as in TH6; `semi_lagrange_sedim` returns the mass it did
not transport and no longer floors its output; and layers held at the `R1` placeholder start sedimentation from their
actual content. **Measured** upstream, where Thompson is double precision (24 h): the physics' residual falls from
−6.0 × 10⁻⁸ to −4.0 × 10⁻¹⁵ kg/m², the largest column from 1.6 × 10⁻⁸ to 2 × 10⁻¹³; the same on the single-precision
v1 snapshot.

**TH8, surface precipitation thresholds** (held: `held/TH8_*.diff`). The sedimentation flux out of the lowest layer
always leaves the column, but is added to surface precipitation only when the water left in that layer exceeds
`R1·rr_min` (L3995, 4090, 4120, 4151). **Fix:** count all of it. **Measured:** the physics' residual falls from
−1.46 × 10⁻⁷ to −1.6 × 10⁻⁸ kg/m² per 6 h, the largest column from 1.3 × 10⁻⁴ to 1.7 × 10⁻⁸. Why it is held: section 7.

**Other hosts.** TH2–TH4 and TH6 are in the scheme itself, so they are also in the WRF and MPAS copies and in TEMPO
(Appendix C). Becker et al. (2022) found IFS clipping errors grow with resolution (4.6–10.7 % of precipitation at
9–4 km); at C384 the fixed total is still −0.001 %.

## 3. Noah-MP and its coupling: fixes NM1–NM11

We metered Noah-MP's own water every step: canopy, snow, soil and aquifer water as the driver receives and returns
them, with precipitation, evapotranspiration and runoff. Noah-MP's `errwat` check (computed, never acted on) was
+3.7 kg/m² per 6 h globally, and storage changed between calls, where nothing should touch it. NM1–NM6 explain all of
it. NM1 affects the atmosphere; NM2–NM6 affect only the land, which an atmosphere budget cannot see.

**NM1, evaporation handed over as latent heat** (diff 08, `noahmpdrv.F90` L1526). The driver gives the atmosphere
`evap = latent_heat/ρ/con_hvap`, but Noah-MP removed the water with its own latent heats (`hvap = 2.5104e6`, and
`hsub = 2.844e6` whenever ground or canopy is frozen; `module_sf_noahmplsm.F90` L188–189). The atmosphere receives
0.4 % more water than unfrozen land loses, 14 % more over frozen surfaces. **Fix:** pass the water flux Noah-MP
computes, `(ecan + etran + edir)/ρ`, as NCAR's own Noah-MP drivers (WRF, HRLDAS, MPAS, LIS) do. The host's latent-heat
output, derived from `evap`, then follows the water and is up to 12 % lower over sublimating surfaces; Noah-MP's own
latent heat flux is unchanged. **Measured:** the atmosphere received +4.5 to +6.9 × 10⁻⁴ kg/m² per 6 h more than the land
lost (+0.07 to +0.10 % of global precipitation); with the fix, 0 to machine precision apart from FV1. Older trees,
including the v1 snapshot, set glacier canopy evaporation and transpiration to `undefined` (9.99 × 10²⁰); there NM1 also
needs them zeroed, as `ufs/dev` does since ccpp-physics 3fe1f187.

**NM2, coastal land stepped twice** (diff 09). `GFS_surface_loop_control_part2` (L50) re-flags a point for the second
surface pass when `(dry .and. lsm /= lsm_noahmp) .or. (wet .and. nstf_name1 > 0)`. With `frac_grid` a coastal cell is
both dry and wet, so the second clause re-flags it, and `noahmpdrv` (L953) tests only `flag_iter .and. dry`: Noah-MP
steps the land again from its already-updated state (unlike Noah and RUC, it does not save and restore its state).
**Fix:** pass the CCPP loop counter (an optional trailing argument) and compute land on the first pass only;
NOAA-EMC/noahmp's copy of the driver interface needs the same declaration (diff 09b). **Measured:** 24–27 % of the land
was stepped twice every step, receiving each step's rain twice:

| Window | Precipitation added again | Evapotranspiration debited again | Land water created | / global P |
|---|---|---|---|---|
| 6–12 h | 0.051 kg/m² | 0.026 | +0.022 | +3.3 % |
| 12–18 h | 0.049 | 0.012 | +0.036 | +5.2 % |
| 18–24 h | 0.054 | 0.015 | +0.038 | +5.3 % |

Any configuration with `frac_grid` and NSST is affected, including this suite.

**NM3, coastal land snow overwritten** (diff 10). `GFS_surface_composites_post` (L105) sets the cell-mean snow
`weasd = txl·weasd_lnd + txi·weasd_ice`, and next step `GFS_surface_composites_pre` (L274) sets `weasd_lnd = weasd` for
every land model except RUC. With `frac_grid`, `weasd_lnd` is the persistent land value, so coastal snow is diluted
every step and thin snow is lost, about 0.005 mm per land column per 6 h (Noah-MP's rebuild of its layers from it was
the +3.7 kg/m² `errwat`). **Fix:** with `frac_grid`, keep `weasd_lnd`, as RUC does.

**NM4, cold-start snow layers from the wrong snow** (diff 11). At a cold start Noah-MP is given the land snow `weasdl`,
but `GFS_phys_time_vary_init` builds its snow layers from the cell-mean `weasd` and `snowd` (L455, L469, L525–533,
L581), and on its first step Noah-MP rebuilds its total from the layers. **Measured:** 0.29 kg/m² of land snow lost as a
global mean. **Fix:** use `weasdl` and `snodl`. Where the initial state has snow depth but no snow water, no layers are
built: a small land fraction can otherwise turn a trace of cell-mean depth into massless layers, a divide by zero on
the first step.

**NM5, thin snow deleted** (diff 12). Noah-MP zeroes snow without layers when `snowh <= 1e-6` m or `sneqv <= 1e-3` mm
(L947, L2049, L8180), and the water goes nowhere. Ice dripping off a frosted canopy reaches snow-free ground as about
10⁻⁴ mm per step and was deleted every step. **Measured:** 15.6 mm in 124,000 events, the whole of the −15.6 mm `errwat`
summed over 1.77 million column-steps in 24 h. **Fix:** put the truncated snow in the top soil layer as ice, as
`snowh2o` already does with excess sublimation.

**NM6, canopy water deleted** (diff 13). `canwater` zeroes canopy liquid or ice at or below 10⁻⁶ mm (L7346, L7355), on
about 5 % of land column-steps. **Measured:** the deleted water equals the remaining `errwat` (−0.0141 mm) to 1 part in
10⁴. **Fix:** `canwater` returns the truncated water, and `water()` adds it to the rain and snowfall reaching the
ground; nothing changes phase, so no energy is created.

**NM7, condensation without water** (diff 14). The canopy energy solve (`vege_flux`) can return a negative
transpiration heat flux, `fctr < 0`: condensation through the stomatal pathway, on 13 % of land column-steps.
`canwater` takes `etran = max(fctr/hvap, 0)` (L7328, L7334), so that latent heat warms the canopy but no water
condenses. **Measured:** after NM8, Noah-MP's latent energy exceeded that of its water by 0.024 W/m² per land column,
exactly Σ min(`fctr`, 0). **Fix:** add `|min(fctr/hvap, 0)|` to the canopy dew (`fctr/hsub` to the frost on a frozen
canopy); the energy solve is unchanged. The land's water–energy mismatch falls from −0.0228 to +0.0013 W/m²; the
remainder is the canopy evaporation cap (section 7). NCAR's Noah-MP v5 has the same clip. CTSM avoids the case inside
its energy solve, which changes the energy solution, so we did not take that route.

**NM8, latent heats from the host** (diff 15; cf. NCAR/ccpp-physics#582). Noah-MP charges the land its own latent heats
(L188–190 and the glacier copies), but after NM1 the water enters the atmosphere carrying the host's (`con_hvap` from
liquid, `con_hvap + con_hfus` from ice). **Measured:** the land paid +0.131 W/m² per land column more than its vapour
carries (0.41 % of land latent heat, one-signed). **Fix:** `hvap`, `hsub` and `hfus` become module variables, set at
the start of `noahmpdrv_run` from the `con_hvap` and `con_hfus` it already receives, so no interface changes (why that
matters: `patches/README.md`). The gap is then exactly 0; Noah-MP's other constants are untouched.

**With NM1–NM6** (v1 snapshot, metered):

| | Before NM2–NM6 | NM2–NM4 | NM2–NM5 | NM2–NM6 |
|---|---|---|---|---|
| Noah-MP `errwat`, global | +3.7 kg/m² per 6 h | −6 × 10⁻⁵ kg/m² per 6 h | | |
| `errwat` summed over 1.77 M soil column-steps, 24 h | | −15.6 mm | −0.014 mm | −1.2 × 10⁻⁸ mm (rounding) |
| column-steps with \|`errwat`\| ≥ 10⁻⁷ mm | | | 326 | 0 |
| storage change between calls | nonzero | 0.00000 | 0.00000 | 0.00000 |

The precipitation hand-off is exact (10⁻¹⁶). On glacier points `errwat` is zero throughout, but it cannot see the
glacier code's own assignments (NM9).

**NM9, glacier snow set by assignment** (diff 16, `module_sf_noahmp_glacier.F90`, `noahmpdrv.F90`). UFS runs glaciers
with `iopt_gla = 2`: the ice beneath the snow is an unlimited, untracked reservoir, and glacier flow (`snoflow`, added to
the subsurface runoff `runsub`) moves water between it and the snow. Four places set the snow instead:
- `snowwater_glacier` resets the snowpack to 600 mm of ice on every call (L2653): all snowfall and rain on land ice is
  deleted, sublimation is created, and meltwater refreezes for free;
- `noahmpdrv` floors glacier snow at 0.1 mm on every call (L960);
- thin snow without layers is zeroed at the end of `noahmp_glacier` (L357) and in `snowh2o_glacier` (L3347), as in NM5.

**Fix:** keep every assignment and book its water as runoff: the reset's liquid as surface runoff and its ice change as
glacier flow, the floor's added snow as negative subsurface runoff (`drain`), the truncations as glacier flow or surface
runoff. Glacier behaviour is unchanged, and soil points are bit-for-bit unchanged. **Measured** in a harness that
compiles the real `noahmpdrv_run` (red team, both `iopt_gla`):

| Case | Without NM9 | With NM9 |
|---|---|---|
| a 26 mm/day snow day | all 26 mm deleted | 25.98 mm booked as glacier flow |
| sublimation | 0.47 mm/day created | 0 |
| one glacier column, 120 days | −860 mm | −2.4 × 10⁻¹³ mm |
| 60-day melt seasons | −8 to −33 mm | ≤ 1.1 × 10⁻¹³ mm per call |
| 0.1 mm floor, melting glacier without the reset | +2.3 to +5.9 mm/day | 0 |

The v1 snapshot has the floor and the truncations but no reset; in a 10-day C96 run from March none of them fires
(started with every glacier snow-free, the floor creates 0.005 mm per glacier column in 10 days). **Energy:** the host
reads `drain` as liquid, but over land ice it now carries glacier ice (section 7).

**NM10, the phase of precipitation** (diff 17). Not a water leak: with `opt_snf = 4` (this suite), `atm` (L1094–1104)
sets the snow fraction to the microphysics' frozen share of grid-scale precipitation and applies it to convective
precipitation too. A trace of grid-scale snow turns convective rain into snow; with no grid-scale precipitation,
convective snow falls as rain. **Fix:** the microphysics' fraction applies to grid-scale precipitation only; convective
precipitation is snow when the lowest-layer air temperature `sfctmp` is below `tfrz`. This is close to, but not the
same as, the host's rule for `srflag` with Thompson (`GFS_MP_generic_post` L466–483: surface temperature `tsfc` below
273.15 K; the L495–516 rule cited in earlier drafts is the MG branch, which uses T850), so near freezing Noah-MP and the
host can still disagree on the phase (energy follow-on, `conservation/ensfc/report.md`, fix PH2). Without
convective precipitation the result is bit-identical. **Measured:** cold convective snow that fell as rain builds
7.8 mm of snow in two days in the single-column harness; water and energy closure are unchanged over 48,000 random
calls; 24-h C96 forecasts change within noise. The canopy wetted-fraction switch found alongside is Appendix E.2.

**NM10 revised (17r).** The energy follow-on (`conservation_proposal.md` section 6, NM10r) replaces 17 with 17r:
Noah-MP takes the host's convective-phase decision (`srflag`), so the land and the host agree on the phase, to
1.2 × 10⁻¹⁰ of land frozen-precipitation mass in a 24-h C96 run (2.5 × 10⁻² with 17). Water closure is unchanged
(Noah-MP 6.6 × 10⁻¹³ mm per column-step) and land means are at noise. It is a physics change: it adopts the host's
skin-temperature criterion. 17r is cut on `develop` + 01–16 and 18 applies after it
(`patches/revised/17r_NM10r_noahmp_precip_phase.diff`). The regression and reproducibility results in this proposal
were measured with 17.

**NM11, the latent heat of the ground's vapour** (diff 18). `energy` (L2224) charges the ground's vapour flux at `hvap`
when `tg` is above freezing, but `water` takes that vapour from the snow ice (`qsnsub`, L7169), or puts frost onto it
(`qsnfro`), whenever there is snow. On thawing snow the land therefore pays `hvap` for ice and creates `hfus` per
kilogram. **Measured** in the single-column harness: 0.13–0.61 W/m² over a 120-day snow season, up to 78 W/m² in one
call. **Fix:** `latheag = hsub` whenever there is snow; where the phase moved still differs from the one charged (snow
melting out within the step, or frozen ground giving up liquid), `water` returns the difference to the top soil layer
as heat. The ground's latent-energy error is then zero to output precision (≤ 3 × 10⁻⁵ W/m² per call), with returns of
0.004–0.014 K per call on average; water is unchanged.

## 4. FV3 driver: fix FV1

**The defect.** `atmos_phys_driver_statein` (`driver/UFS/atmosphere.F90`, `dev/emc` @71ff473, L2298) gives the
physics the layer pressure `prsl = dm·rTv/Δφ` with `rTv = rdgas·T·(1 + zvir·q)`, using the dycore's constants. The
physics turns `prsl` back into density with its own `con_rd` (the boundary layer's `ρ_a`, Noah-MP's `density`). In a
32-bit build `rdgas` is single precision (287.04998779 for 287.05), so that density is 4.25 × 10⁻⁸ smaller than the
layer's actual mass per volume, `dm/Δφ`. The boundary layer adds `evap·del/(g·dz)` of water but books `evap·ρ_a`,
which is also what Noah-MP debits after fix NM1: the atmosphere receives 4 × 10⁻⁸ of the surface evaporation more than
the land loses.

**The fix** (diff 19, a different repository: NOAA-GFDL/GFDL_atmos_cubed_sphere `dev/emc`): compute `rTv` with the
physics' `con_rd` and `con_fvirt` (`use physcons`, after the `OVERLOAD_R4` block so that both builds see it).
**Measured:** added minus booked falls from +4.11 × 10⁻⁸ of evaporation (+3.1 × 10⁻⁸ kg/m² per 6 h) to 5 × 10⁻¹⁶ over
24 h.
The `MULTI_GASES` branch (`rdgas·T·virq_max`) is not compiled here and is unchanged. In 64-bit builds FV1 should change
nothing (the constants agree in double precision; not run). It does not address the dycore's single-precision `grav`, which differs from `con_g` by 1.65 × 10⁻⁸; our
meters show no water effect from that at their 10⁻⁶ kg/m² per window resolution.

## 5. How we measured

**Code.**
- UFS-Chem v1 (Jian He's `dev-am4`, the code behind He et al. 2026): ccpp-physics `f70b191` (2024), FV3 driver
  `a5c4305`, dycore `d4838c3`. All fixes were developed and first measured here.
- Current upstream: `ufs-weather-model` `develop` @112b1d46, with ccpp-physics `ufs/dev` @242a2fc and
  GFDL_atmos_cubed_sphere `dev/emc` @71ff473. The defects are line-for-line the same (Appendix B), and the budget
  results of section 6 were repeated there, as were the physics-closure and Thompson meters (for TH7). The other
  in-model meters, the single-column tests and the thickness tests are v1 only.

**Cases.** Regression-suite cases with `FV3_GFS_v17_p8_ugwpv1`, from 2021-03-22 06Z, built with
`-DAPP=ATM -D32BIT=ON` (Intel) on MSU Hercules: `control_p8_ugwpv1` (C96 L127, dt = 720 s, 24 h and 240 h) and
`control_c384` (C384 L127, dt = 300 s, 24 h). One start date, one suite, atmosphere only, no cycling or IAU, OpenMP
threads = 1, plus one 64-bit meter build.

**Total budget.** Global means on the native grid with exact cell areas: residual = ΔW − (E − P)·Δt per window, with
W = Σ q·Δp/g over the six water species (Δp = `dpres`/(1 − Σ condensate), pitfall 6), E = `lhtfl_ave`/hvap (exactly
what the boundary layer adds; it reports `dqsfc = ρ·hvap·evap`) and P = `prateb_ave`.

**Per-scheme split.** With `ldiag3d = qdiag3d = .true.`, each scheme's column water tendency (`dtend_*`, integrated
over `dpres`) against its own boundary flux: boundary layer against E, convection against convective rain,
microphysics against grid-scale rain. The split's absolute levels are uncertain by about 10⁻⁴ kg/m² per 6 h
(pitfall 5); we use it for differences between builds.

**In-model meters** (diagnostic builds, Appendix A), all accumulated in double precision every step:
- **Whole physics:** Σ (q_new − q_old)·Δp/g over the six species at the end of each physics step.
- **Physics closure:** per column and step, that change against the evaporation the boundary layer adds, the
  precipitation the physics reports and the deliberate `h2ophys` source. It also records what the boundary layer adds
  against what it books.
- **Dynamical core:** around `fv_dynamics` (and `neg_adj3`), `fv_subgrid_z`, the physics → dynamics update
  (and `fill_gfs`) and `fv_update_phys`.
- **Thompson:** its column routine stage by stage, and the whole driver call in the host's variables.
- **Land:** the evaporation and precipitation hand-offs on both sides; Noah-MP's storage terms in and out of each call,
  `errwat` by surface state, and meters at each truncation site.

The meters change no answers (builds that differ only in meters are bit-identical), and they can fail: on the
unmodified build the physics meter reports the +0.26–0.29 % source.

## 6. Results

**Per fix, v1 snapshot, C96**, kg/m² per 6 h averaged over 6–24 h, and percentages of the matching precipitation:

| Build | Convection | Microphysics | Total / P |
|---|---|---|---|
| unmodified | +0.0035 (+0.78 % of P_conv) | −0.0017 (−0.67 % of P_grid) | +0.27 % |
| SA1 | +0.00002 (0.00 %) | −0.0017 | −0.22 % |
| TH1 | +0.0035 | −0.0007 (−0.30 %) | +0.41 % |
| SA1 + TH1 | +0.00002 | −0.0007 | −0.09 % |
| SA1 + TH1 + TH2 | +0.00002 | −0.0004 (−0.15 %) | −0.03 % |
| SA1 + TH1 + TH3 | +0.00002 | −0.0008 (−0.33 %) | −0.10 % |
| SA1 + TH1–TH3 | +0.00002 | −0.0004 (−0.18 %) | −0.04 % |
| SA1 and TH1–TH4 | +0.00002 | −0.0002 (−0.07 %) | −0.003 % |

The totals are exact; the per-scheme columns come from the split (pitfall 5). Two builds that differ only in the land
flux (with and without NM1) agree to 1 × 10⁻⁵ kg/m² per window: our floor for differences between builds.

**Exact closure with the meters**, v1 snapshot, C96:

| Build | Physics residual | Dynamics + update (R_dyn) | Total / P |
|---|---|---|---|
| unmodified | +0.0020, +0.0019, +0.0018 kg/m² per window | 0.000000 | +0.29, +0.27, +0.26 % |
| SA1, TH1–TH4, TH5, TH6 and NM1 | 0.000000 at 6 decimals | ≤ 0.000001 | 0.000 % |
| all of SA1, TH1–TH6 and NM1–NM6, double-precision physics meter | −1.46 × 10⁻⁷ kg/m² per 6 h | | 2 × 10⁻⁷ |
| + TH8 (held), FV1, NM8, 24 h | −1.6 × 10⁻⁸ kg/m² per 6 h | ≤ 0.000001 per window | 2 × 10⁻⁸ |
| + NM7, TH7, 24 h (every fix, TH8 included) | −4.3 × 10⁻¹⁵ kg/m² in 24 h | ≤ 0.000001 per window | 1.5 × 10⁻¹⁵ |

R_dyn is zero to 10⁻⁶ kg/m² in every window in 32- and 64-bit builds. Each meter inside the dynamical core changes water
by less than 3 × 10⁻⁷ kg/m² per step in 32-bit (rounding, both signs) and about 10⁻¹² in 64-bit. `fill_gfs` and
`fv_update_phys` never fired, so their meters show inactivity, not conservation.

**Current upstream `develop`:**

| Case | Build | Convection | Microphysics | Total / P |
|---|---|---|---|---|
| C96 | unmodified | +0.0035 (+0.81 %) | −0.0018 (−0.68 %) | +0.25 % |
| C96 | + SA1, TH1–TH4 | +0.0001 (+0.03 %) | −0.0002 (−0.07 %) | −0.005 % |
| C96 | + SA1, TH1–TH4, NM1 | +0.0001 (+0.03 %) | −0.0002 (−0.07 %) | −0.005 % |
| C96 | every cumulative build to all proposed diffs | | | 0.00000 kg/m² per 6 h |
| C384 | unmodified | +0.0047 (+0.97 %) | −0.0011 (−0.38 %) | +0.45 % |
| C384 | + SA1, TH1–TH4 | +0.0003 (+0.05 %) | −0.0003 (−0.09 %) | −0.001 % |
| C384 | + all diffs (and with TH8 as well) | | | 0.00000 kg/m² per 6 h |

The per-scheme columns are biased by a few hundredths of a percent (pitfall 5), and on `develop` convection is the
total minus the other schemes (section 7), so the small residuals in the fixed rows are not resolved.

Every cumulative build, adding one fix at a time, compiles and runs the C96 case to 24 h with a total of
0.00000 kg/m² in every window after the first. The final tree, `develop` + the diffs as published:

| Final tree | Runs | Total budget | Physics' residual over 24 h (physics-closure meter) |
|---|---|---|---|
| diffs 01–17 and 19 (before NM11) | 24 h at `dt_inner` = 720 s and 150 s; 10 days; C384 | 0.00000 kg/m² in every window and every day | −5.5 × 10⁻⁷ and −2.5 × 10⁻⁷ kg/m² (720 s, 150 s), one-signed; largest column 2–3 × 10⁻⁴ |
| the same with TH8 (an earlier final tree) | the same | 0.00000 | −9.7 × 10⁻¹⁵ and −7.8 × 10⁻¹⁵ kg/m²; largest column 2.2 × 10⁻¹³ |
| diffs 01–19 (with NM11) | 24 h | unchanged | −5.4 × 10⁻⁷ kg/m² |

Without TH8, the residual is the sub-threshold sedimentation out of the lowest layer. The metered output is
byte-identical to the unmetered one.

**Ten days** (`develop`, C96, 24-hour windows, total only; pitfall 4):

| Build | Residual per day, days 2–10 | / P | Range over the days | Accumulated |
|---|---|---|---|---|
| unmodified | +0.0055 kg/m² | +0.18 % | +0.15 to +0.22 % | +0.050 kg/m² |
| + SA1, TH1–TH4, NM1 | −0.00017 kg/m² | −0.006 % | −0.008 to −0.005 % | −0.0016 kg/m² |
| + all diffs (and with TH8 as well) | 0.00000 kg/m² | 0.000 % | 0.00000 every day | < 5 × 10⁻⁵ kg/m² |

The fixed residual does not drift. The unmodified error is smaller after day 1 but does not decay further. At C384 most
of the larger total is convection, but C384 also has a shorter time step, so this is not a clean resolution
dependence. Global precipitation changes by at most 0.5 % per window between builds.

**Forecast impact.** The red team compared 24-h C96 forecasts with and without each fix against nine pairs of
bit-perturbed initial conditions; a change counts only above three times the noise maximum and when it is coherent
across related fields.

| Fix | Change beyond noise |
|---|---|
| TH1–TH4, TH5 (with its inner steps), TH6, TH7, NM5–NM8, NM10, FV1 | none |
| SA1 (first form, without the cloud-base face) | lowest five layers +0.010 to +0.014 K, q −0.03 to −0.06 % |
| NM1 | host latent-heat output over snow-covered land −4.2 % (19× noise), up to −12 % where sublimation dominates |
| NM2 | land 2-m temperature +0.033 K (6×), coasts +0.040 K with skin temperature unchanged; land q2m +0.17 %; canopy evaporation +10 % (27×) |
| NM3 | land snow −0.45 kg/m² (−0.6 %), glacier snow −2.85 kg/m² in 24 h; sublimation +5 % (48×) |
| NM4 | land snow +0.69 kg/m²; glacier latent heat +2.4 % |
| NM11 | over snow-covered land: snow cover +0.16 % (8×), ground heat flux +0.15 W/m² (6×), melt heat −1.2 % (4×), snow depth +0.04 % (4×); land latent heat, 2-m temperature and humidity within noise |
| TH8 (held) | land canopy evaporation −39 % (124×), land latent heat −2.2 % (−0.75 W/m²), tropical land snow cover 0.02 → 0.69 %; still −0.7 to −1.1 W/m² at 10 days (section 7) |

The final tree before NM11 against `develop` shows only these signals: land canopy evaporation +10 % (NM2), snow
sublimation +5.7 % and snow depth +1.8 % (NM3, NM4), land latent heat −0.5 %, land 2-m temperature +0.03 K, and global
precipitation −0.7 % (SA1's final form; not isolated from changes to TH5 and TH7). Forecast skill against
observations, other start dates and cycled runs were not assessed.

## 7. What remains

What is held, what is still open on the proposed fixes, and what we did not measure. Problems that need their owners
rather than a fix from us are in Appendix E.

**Held.**

- **TH8, with the placeholder fix TH9** (`patches/held/`). Thompson keeps an absent species at a placeholder `R1` =
  10⁻¹² and gives an empty layer the fall speed of the layer above (L3903, L3950), so in flux-form ice and snow
  sedimentation the placeholder settles as if it were mass and is re-created every substep. TH8 books the trace that
  reaches the surface as grid-scale snow, which Noah-MP then applied to convective rain (fixed by NM10). TH9 stops the
  placeholder sedimenting and removes about 95 % of TH8's land signal. What remains is genuine traces of snow (10⁻¹⁴ to
  10⁻⁸ mm/day) that the old threshold discarded; on the canopy they become trace ice, which hides the canopy's liquid
  (Appendix E.2). With TH9 and NM10, TH8 is within noise from 6 h on, but not in the first 6 h (land canopy evaporation
  −2.4 %, 11× noise; snow sublimation +1.1 %, 14×). With the mass-weighted wetted fraction of Appendix E.2 it is within
  noise throughout, so TH8 and TH9 wait for that change. Without TH8 the physics deletes the sub-threshold sedimentation
  (section 6). TH8 and TH9 (unconditional) are now proposed in `conservation_proposal.md` (section 5), where TH8 also
  closes 2.4 × 10⁻⁶ W/m² of energy.

**Open points on the proposed fixes.**

- **Noah-MP's canopy evaporation cap** (energy; +0.0012 W/m² per land column after NM7 and NM8). `vege_flux` caps
  canopy evaporation at the water on the leaves before solving the canopy temperature (L4269–4271), but the flux update
  after the solve (L4284) can exceed the cap, and `canwater` evaporates only what is there. Both obvious fixes (CTSM's
  transfer of the excess to sensible heat, or re-capping after the solve) change the energy partition, so we propose
  none. Locally it is larger: 0.053 W/m² as a forest mean over 120 days, up to 65 W/m² in one call (red team).
- **Glacier ice in `drain`** (energy). After NM9 the subsurface runoff over land ice carries glacier ice, but hosts and
  couplers read it as liquid. Closing the energy needs a frozen-runoff flux in the CCPP interface, the host and the
  couplers (the code marks it `FIXME`).
- **Frozen-canopy transpiration** (energy) is charged at `hsub`, though the water is liquid soil water. NM11 does not
  cover it, nor shortfalls inside `snowh2o` and `combine` (none occurred in any test).
- **MYNN surface layer** (`sfcdif4`, not in this suite) still derives the moisture flux from latent heat, so NM1 is
  incomplete there.
- **NM5 with implausible host input** (a large snow amount with a depth ≤ 10⁻⁶ m) can push the top soil layer's ice
  past porosity; realistic truncations change it by at most 2.5 × 10⁻⁵ m³/m³. Negative snow from the host is still
  created into water.
- **Thompson's remaining edges** (red team): a column with no vapour at all can still be floored after TH6's refill,
  and TH7's entry exchange leaves latent heat unpaid where no vapour exists to pay it (under 40 J/m²).
- **The cold start** removes 0.0024 kg/m² once, because the initial condition is built on unfiltered terrain (pitfall
  2); the fix belongs on the initial-condition side.
- **A deliberate source:** `h2ophys` (+1.2 × 10⁻⁷ kg/m² per 6 h), which the meters count separately.
- **A diagnostic gap on `develop`:** with SAMF, `dtend_liq_wat_cnvtrans` and `dtend_ice_wat_cnvtrans` are always zero
  (`GFS_suite_interstitial_4`), so the upstream convection split is computed by difference.

**Not measured, and outside UFS.**

- **Not measured:** sea ice, lakes, other suites, coupled configurations, OpenMP threads > 1 (the meters assume one),
  cycled runs and analysis increments.
- **WRF and MPAS dynamics** (Appendix D): once Thompson is fixed, four transport and diffusion operators in those hosts
  still change total water. None of them is in UFS.

## 8. Pitfalls for anyone repeating this

1. **`prate_ave` and `cprat_ave` average since forecast start** (`time_avg_kind = 'full'`). Per-window values are
   `prateb_ave` and `cpratb_ave`.
2. **`atmf000` is written after the first time step**, but the first flux bucket includes that step, which rains out a
   0.043 kg/m² cold-start burst. A budget starting from `atmf000` shows a spurious +0.023 kg/m² in the first window.
   From the initial condition instead, none of the first window's residual is in the physics or dynamics; it is all in
   the cold-start initialisation, which we replicated offline column by column (to 2 × 10⁻⁵ kg/m²):
   - the IC's surface is the raw orography (`orog_raw`); the model runs on `orog_filt`, up to 500 m different, so
     `remap_scalar` (`USE_GFS_ZS` undefined) re-fits each column's surface pressure: −1.7 Pa mean, **−0.0024 kg/m²**;
   - dropping the IC's top layer removes 3 × 10⁻⁷; the `delp`/(1 − condensate) rescaling creates nothing;
   - the adiabatic initialisation adds back about +0.0003.
   Build the IC on the model's filtered orography, or compile with `USE_GFS_ZS`. All results use the windows after the
   first.
3. **FV3 writes `gfs_phys` 3-D diagnostics (`dtend_*`) to the `sfcf` files**, whatever the diag_table says.
4. **The per-scheme split needs short windows.** Over 24 h, surface-pressure changes make the thickness averaging off by
   about 0.3 % of each scheme's flux. The 10-day check reports the total only.
5. **The per-scheme split is biased, not just noisy.** Re-integrating one build over 6-, 3-, 2- and 1-hour
   thicknesses moved the microphysics residual from −0.17 % to −0.11 % of P_grid and the split's "dynamics" from
   +1.2 × 10⁻⁴ to −1.4 × 10⁻⁴ kg/m², where the meters show zero. In 24-h windows a fully fixed build reads −0.2 to −0.3 %
   of P_grid every day while the total is 0.00000, and a synthetic, exactly conserving model with only a 0.1 %
   semidiurnal thickness tide gives ±0.03–0.06 % (an independent check by a second session). Totals are unaffected; per-scheme
   residuals below about 0.05 %, and build differences below about 5 × 10⁻⁵ kg/m² per 6 h, are not resolved. The
   in-model meters are the absolute reference.
6. **The output `dpres` is not the dynamical core's layer thickness.** With GFS physics it is `delp·(1 − Σ condensate)`
   while the tracers are per total mass. Use `dpres`/(1 − Σ condensate) for W, or a spurious "dynamics" loss of
   3–6 × 10⁻⁵ kg/m² per 6 h appears.
7. **CCPP runs each scheme over all of a rank's blocks before the next scheme.** A meter that hands values from one
   scheme to a later one through a module array must queue them by block, or it sees only the last block.
8. **Glacier `waxy` is bookkeeping.** `GFS_phys_time_vary` sets the aquifer water `waxy` to 4900 mm on glaciers and the
   driver zeroes it on the first call, so a land meter that counts `waxy` shows −4900 mm per glacier column once.

## 9. Suggested test plan

1. Apply diffs 01–18 to `ufs/dev` (08 and 14–18 once the Noah-MP owners have weighed in), 09b to
   NOAA-EMC/noahmp with NM2, and 19 to `dev/emc`, build, and run the regression suite. Baselines will change: the fixes change answers, and NM2 changes the
   land state of a quarter of the land.
2. Add a water-budget check to one regression test: the whole-physics meter (no `dtend` output needed) and, for
   attribution, `ldiag3d`/`qdiag3d` with the per-scheme closure. Our scripts take a run directory and print the tables
   of section 6 (Appendix A).
3. Confirm forecast neutrality on the standard verification (e.g. a 10-day cycled comparison).
4. Repeat the budget at C768 or a convection-permitting resolution, where Becker et al. (2022) found clipping errors
   grow.

## 10. Requests

- **SAMF owners** (@JongilHan66, @lisa-bengtsson): fix SA1, including the tracer loops, and the three questions in
  section 1.
- **Thompson / TEMPO owners** (@gthompsnWRF, @RuiyuSun, @AndersJensen-NOAA): fixes TH1, TH2–TH4, TH5, TH6 and TH7; TH8 with
  the placeholder fix TH9, held until Noah-MP's canopy wetness is settled (section 7). TH2–TH4 and TH6 also apply to the WRF and MPAS copies and to
  TEMPO; TH1 also applies to TEMPO's CCPP driver.
- **Noah-MP owners** (@barlage, @cenlinhe): fix NM1, and whether `evap` should carry the mass flux or the energy side
  should switch to host constants (NCAR/ccpp-physics#582); fix NM2, and whether Noah-MP should instead save and restore
  its state for the second pass; fixes NM5 and NM6, which NOAA-EMC/noahmp and NCAR's Noah-MP v5 also need; fix NM8, #582's
  approach for the three latent heats; fix NM7, or whether you prefer CTSM's treatment of condensation in the energy
  solve; fix NM9, and whether the 600 mm reset should stay; fix NM10; fix NM11, or whether you prefer to move the snow's
  sublimation ahead of its melt; a frozen-runoff flux for glacier ice; and the canopy evaporation cap and frozen-canopy transpiration's
  latent heat (section 7). The wetted fraction of a mixed-phase canopy is a separate issue (Appendix E.2).
- **CCPP physics** (@grantfirl, @rhaesung, @dustinswales): fixes NM2, NM3 and NM4 in the surface loop control, composites
  and cold-start initialisation; a water-budget regression check; documentation of `prate_ave` vs `prateb_ave`;
  restoring the SAMF condensate `cnvtrans` diagnostic.
- **FV3 `dev/emc` maintainers** (merged by @vithikashah001, approved by @lharris4 and @JosephMouallem; the UFS driver
  mostly by @dustinswales): fix FV1. Longer term (@lharris4, @linjiongzhou), a dry-mass tracer-transport option for
  long chemistry and greenhouse-gas runs; CAM-SE's dry-mass coordinate is the precedent (Lauritzen et al. 2018).

The separate issues in Appendix E have their own owners, listed there.

Routing, reviewers and the PR chain for each fix: `patches/README.md`.

## References

- Becker, T., et al., 2022: ECMWF Newsletter 172 (water conservation in the IFS).
- Diamantakis, M., and J. Flemming, 2014: Global mass fixer algorithms for conservative tracer transport in the ECMWF
  model. GMD, 7, doi:10.5194/gmd-7-965-2014.
- Han, J., F. Yang, R. Montuoro, W. Li, and R. Sun, 2022: NCEP Office Note 506, doi:10.25923/5051-3r70 (SAMF TVD
  mass flux and negative-tracer removal).
- Harris, L., et al., 2021: A scientific description of the GFDL finite-volume cubed-sphere dynamical core. NOAA Tech.
  Memo. OAR GFDL 2021-001, §9.1.
- He, J., et al., 2026: Incorporating gas-phase chemistry into the Unified Forecast System (UFS) for global air
  quality applications. JAMES, doi:10.1029/2025MS005299.
- Lauritzen, P. H., et al., 2018: NCAR release of CAM-SE in CESM2.0. JAMES, 10, doi:10.1029/2017MS001257.
- Takacs, L. L., M. J. Suárez, and R. Todling, 2016: Maintaining atmospheric mass and water balance in reanalyses.
  QJRMS, 142, doi:10.1002/qj.2763.
- Zhang, K., et al., 2018: GMD, 11, doi:10.5194/gmd-11-1971-2018 (water conservation in E3SM).
- Zhou, L., L. Harris, and J.-H. Chen, 2022: The GFDL cloud microphysics parameterization. NOAA Tech. Memo. OAR GFDL
  2022-02, §2.4.

## Appendix A — patches and scripts

Diffs 01–18 are against ufs-community/ccpp-physics `ufs/dev` @242a2fc, the commit pinned by `ufs-weather-model`
`develop` @112b1d46 (2026-10-08), and apply in order. Each file is named by its number and fix label, grouped by home:
SA (SAMF), TH (Thompson), NM (Noah-MP and its coupling), FV (FV3 driver). 09b is NM2's companion in NOAA-EMC/noahmp
`develop` @2c7b3bc; 19 is FV1, against NOAA-GFDL/GFDL_atmos_cubed_sphere `dev/emc` @71ff473 (also the UFSATM pin). The
held TH8 and TH9 are in `held/`; TH9 applies after TH8. `git format-patch` series of the same changes, one commit per
fix, are in `patches/git/`.

| Diff | Fix | File |
|---|---|---|
| `01_SA1_samf_cloud_base_double_count.diff` | SA1 | `samfdeepcnv.f`, `samfshalcnv.f` (added lines fit within column 72) |
| `02_TH1_thompson_mass_basis.diff` | TH1 | `mp_thompson.F90` |
| `03_TH2-TH3_thompson_settling_and_graupel_closure.diff` | TH2, TH3 | `module_mp_thompson.F90` |
| `04_TH4_thompson_sedimentation_density.diff` | TH4 | `module_mp_thompson.F90` |
| `05_TH5_thompson_layer_depth_from_host_mass.diff` | TH5 | `mp_thompson.F90`, `mp_thompson.meta` |
| `06_TH6_thompson_clipped_condensate_and_vapour_floor.diff` | TH6 | `module_mp_thompson.F90` |
| `07_TH7_thompson_r1_to_vapour.diff` | TH7 | `module_mp_thompson.F90` |
| `08_NM1_noahmp_water_flux.diff` | NM1 | `noahmpdrv.F90` |
| `09_NM2_noahmp_single_step_per_timestep.diff` | NM2 | `noahmpdrv.F90`, `noahmpdrv.meta` |
| `09b_NM2-EMC_noahmp-emc_driver_iter.diff` | NM2's companion (NOAA-EMC/noahmp `develop` @2c7b3bc) | `drivers/ccpp/noahmpdrv.F90`, `.meta` |
| `10_NM3_frac_grid_land_snow_persistent.diff` | NM3 | `GFS_surface_composites_pre.F90` |
| `11_NM4_noahmp_snow_init_from_land_snow.diff` | NM4 | `GFS_phys_time_vary.fv3.F90`, `.meta` |
| `12_NM5_noahmp_thin_snow_to_soil.diff` | NM5 | `module_sf_noahmplsm.F90` |
| `13_NM6_noahmp_canopy_truncation_to_ground.diff` | NM6 | `module_sf_noahmplsm.F90` |
| `14_NM7_noahmp_negative_transpiration_to_canopy_dew.diff` | NM7 | `module_sf_noahmplsm.F90` |
| `15_NM8_noahmp_latent_heats_from_host.diff` | NM8 | `module_sf_noahmplsm.F90`, `module_sf_noahmp_glacier.F90`, `noahmpdrv.F90` |
| `16_NM9_noahmp_glacier_book_snow_changes.diff` | NM9 | `module_sf_noahmp_glacier.F90`, `noahmpdrv.F90` |
| `17_NM10_noahmp_precip_phase.diff` | NM10 (revised: `revised/17r_NM10r_noahmp_precip_phase.diff`) | `module_sf_noahmplsm.F90` (17r also `noahmpdrv.F90`) |
| `18_NM11_noahmp_ground_vapour_latent_heat.diff` | NM11 | `module_sf_noahmplsm.F90` |
| `19_FV1_fv3_prsl_with_physics_gas_constants.diff` | FV1 | `driver/UFS/atmosphere.F90` (GFDL_atmos_cubed_sphere) |
| `held/TH8_thompson_count_all_surface_sedimentation.diff`, `held/TH9_thompson_placeholder_not_sedimented.diff` | TH8 and TH9 (held) | `module_mp_thompson.F90` |

**Earlier labels.** Drafts before 15 October named the fixes in the order we found them:

| Now | SA1 | TH1 | TH2 | TH3 | TH4 | TH5 | TH6 | TH7 | TH8 | TH9 | NM1 | NM2 | NM3 | NM4 | NM5 | NM6 | NM7 | NM8 | NM9 | NM10 | NM11 | FV1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Was | A | B | C1 | C2 | C3 | M4 | M1 | M5 | M2 | 13a | D | E | F | G | H | I | L | K | N | O | (new) | J |

**Verified on MSU Hercules** (Intel, `-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1 -D32BIT=ON`):
- the unmodified `develop` clone passes `control_p8_ugwpv1` (`develop-20260921` baseline) and `control_c384`;
- every cumulative build, one fix at a time, compiles with 0 errors and runs the C96 case to 24 h;
- the final tree, `develop` + the diffs as published, is byte-identical to the `all` git series (the changed physics
  files) and runs the C96 case at both `dt_inner`, metered and unmetered, to 240 h, and the C384 case;
- the full regression suite (Intel and GNU) against `develop-20260921`: 54/54 compiles; every completed test passes or
  changes only baselines, as the fixes change answers by design;
- the same suite on the final tree (diffs 01–19 with 09b) against baselines made from that tree: all 234 tests pass,
  bit for bit, including all 34 restart, 17 decomposition, 14 threading and the MPI tests, which cannot be checked
  against `develop`'s baselines. Nothing crashes, traps a floating-point exception or leaves the temperature range
  anywhere (an earlier diff set had nine such violations). Runs that hit Hercules file-system or scheduler errors were
  retried and passed. Without 09b the land-component tests crash;
- the CCPP single-column model (`ccpp-scm` `main` 4ea4c5e, capgen, Intel ifx): the NCAR `main` series builds for all
  57 suites, release and bounds-checked (SA1 as a hand port); the `.meta` changes pass the validator and capgen (also
  UFSATM's capgen check, where every generated `noahmpdrv_run` call passes `iter` by keyword); the ARM SGP and GABLS3
  cases run with the GFS v17 and HRRR suites with no NaN and no new `-warn all` warnings.

**Scripts** in `scripts/` (Python 3 with numpy and netCDF4; each takes run directories as arguments):

| Scripts | What they do |
|---|---|
| `water_budget_by_scheme.py`, `water_budget_native.py` | total and per-scheme budget per window (section 6) |
| `column_mapping_check.py`, `land_atm_water_closure.py`, `noahmp_qfx_excess.py`, `water_jump_series.py`, `coldstart_trace.py` | per-column checks, the offline land–atmosphere gap (NM1), the first hours and the cold start (pitfall 2) |
| `apply_*.py`, `mk_upstream_*.py`, `fix_*.py` | write the fixes into the v1 snapshot or a `ufs/dev` tree (file names use the earlier labels) |
| `instrument_wb_*.py`, with `*_meter_budget.py`, `noahmp_balance.py`, `iter2_budget.py`, `wb_meter_report_ups.py`, `osc_report.py` | insert the in-model meters of section 5 into diagnostic builds, and report them |

The meters are for diagnostic builds only: they accumulate in module variables and assume one OpenMP thread.

## Appendix B — location of each defect in current upstream

| Fix | `ufs/dev` @242a2fc (FV1: FV3 `dev/emc`) | NCAR `main` @f601ce9 |
|---|---|---|
| SA1, deep | `samfdeepcnv.f` L1622, L2551–2561 (water), L2635–2645 (tracers) | identical logic, shifted lines |
| SA1, shallow | `samfshalcnv.f` L1979–2005, L2040–2050 | identical |
| TH1 | `mp_thompson.F90` L690–704, L944–957; FV3 `atmosphere.F90` L1659–1677 | same |
| TH2, TH3 | `module_mp_thompson.F90` L3029, 3140–3198, 4044–4057 (single-step cloud sedimentation; other species substep at L3808, 3873, 3922, 3950) | same |
| TH4 | `module_mp_thompson.F90` L3386, 3660, 3743 | same |
| TH5 | `mp_thompson.F90` L716 | same |
| TH6 | `module_mp_thompson.F90` L4241–4300 | same |
| TH7 | `module_mp_thompson.F90` L2267, 2294, 2323, 2334, 2343 (entry); L3322–3339 (leftover rain); L4007, 4163, 6271, 6455 (`semi_lagrange_sedim`) | same (series applies unchanged) |
| TH8 | `module_mp_thompson.F90` L3995, 4090, 4120, 4151 | same |
| NM1 | `noahmpdrv.F90` L1526; `module_sf_noahmplsm.F90` L188–189 | same; NCAR/ccpp-physics#582 open |
| NM2 | `GFS_surface_loop_control_part2.F90` L50; `noahmpdrv.F90` L953 | not checked |
| NM3 | `GFS_surface_composites_pre.F90` L274; `GFS_surface_composites_post.F90` L105 | not checked |
| NM4 | `GFS_phys_time_vary.fv3.F90` L455, L469, L525–533, L581 | not checked |
| NM5 | `module_sf_noahmplsm.F90` L947, L2049, L8180 | byte-identical file |
| NM6 | `module_sf_noahmplsm.F90` L7346, L7355 | byte-identical file |
| NM7 | `module_sf_noahmplsm.F90` L7328, L7334 (`canwater`) | byte-identical file |
| NM8 | `module_sf_noahmplsm.F90` L188–190; `module_sf_noahmp_glacier.F90` L27–29; `noahmpdrv.F90` `noahmpdrv_run` | same |
| NM9 | `module_sf_noahmp_glacier.F90` L357, L2653, L3347; `noahmpdrv.F90` L960, L1349 | byte-identical files |
| NM10 | `module_sf_noahmplsm.F90` L1094–1104 (`atm`) | byte-identical file |
| NM11 | `module_sf_noahmplsm.F90` L2224 (`energy`), L7169, L7187 (`water`) | byte-identical file |
| FV1 | GFDL_atmos_cubed_sphere `dev/emc` @71ff473 `driver/UFS/atmosphere.F90` L2298 | n/a (`main` has no UFS driver) |

Every series also applies with `git am` to NCAR `main`; there SA1 is a hand port (NCAR `main` lacks the
single-precision SAMF rewrite, ufs-community/ccpp-physics#384); it compiles and runs in the CCPP single-column model.

## Appendix C — the same code in other upstreams and hosts

A read-only survey (13–14 October 2026) of the other copies we could find.

| | UFS `ufs/dev` = NCAR `main` | TEMPO | WRF | MPAS |
|---|---|---|---|---|
| **SA1** SAMF cloud base | present since NCAR/ccpp-physics#754 (2021) | n/a | n/a | n/a |
| **TH1** mass basis | present | present (CCPP driver `mp_tempo.F90` L437–455, L532–549) | cannot occur: dry mixing ratios passed | cannot occur |
| **TH2** fog settling | present | counted only in the freezing-rain diagnostic | present (L3824–3836) | present (L3443–3455) |
| **TH3** graupel re-closure | present | present (`check_over_depletion` L1649–1673) | present (L2940–2950) | present (L2656–2666) |
| **TH4** density recomputed before sedimentation | 3 sites | 4 sites | 3 sites | 3 sites |
| cloud sedimentation in one step (TH2) | yes | yes (`substeps_sedi = 1`, `module_mp_tempo_main.F90` v3.2.5 L805–814) | not surveyed | not surveyed |
| ρ·dz vs host layer mass (TH5) | `dz` from `phii`, before convection | same driver pattern | geometric `dz8w` | fixed `zgrid` |
| **TH6** clips | zeroed | zeroed | zeroed | zeroed |
| **NM1** Noah-MP water flux | latent heat ÷ `con_hvap` | — | mass flux (`QFX`) | mass flux |
| **NM5** thin snow deleted | at `sneqv <= 1e-3` mm | — | NCAR/noahmp v5: at 1e-6 mm (`SnowWaterMainMod.F90` L176, `SnowpackHydrologyMod.F90` L96) | as WRF |
| **NM6** canopy water deleted | at ≤ 1e-6 mm | — | NCAR/noahmp v5: identical (`CanopyHydrologyMod.F90` L92, L101) | as WRF |
| **NM7** condensation without water | `etran = max(fctr/hvap, 0)` | — | NCAR/noahmp v5: identical (`CanopyHydrologyMod.F90` L75, L81) | as WRF |
| **NM9** glacier snow set by assignment | 600 mm reset every call, 0.1 mm floor, two truncations | — | NCAR/noahmp v5: the truncations (`SnowWaterMainGlacierMod.F90` L176–179, `SnowpackHydrologyGlacierMod.F90` L106–109) | as WRF |
| **NM10** precipitation phase | grid-scale frozen fraction applied to all precipitation | — | NCAR/noahmp v5: the same rule | as WRF |
| **NM11** ground vapour's latent heat | `latheag` from `tg` only; snow sublimates whenever present | — | NCAR/noahmp v5: the same split (`PsychrometricVariableMod.F90` L50, `WaterMainMod.F90` L139); also in NOAA-EMC/noahmp and the production branches (survey in `ports/`) | as WRF |

- **TH2–TH4 and TH6 belong to the scheme**, so their fixes apply to every host. No copy has a water fixer. TH7 and TH8
  were not surveyed in the other copies.
- **TH1 belongs to the CCPP interface**, so it survives a switch to TEMPO unless TEMPO's CCPP driver is fixed too.
- **NM1 belongs to the CCPP port of Noah-MP.** Every NCAR/noahmp driver (WRF, HRLDAS, MPAS, LIS, ERF;
  `drivers/*/WaterVarOutTransferMod.F90` L59–64) passes the water mass flux. The latent-heat form is in ccpp-physics
  and in NOAA-EMC/noahmp, which also has NM5, NM6 and NM8, and sets glacier canopy fluxes to `undefined`.
- **FV3 coupling.** `dev/emc` and `main` both pass the dry + vapour basis and rebuild `delp` from old dry mass; SHiELD's
  in-line GFDL microphysics converts on a dry basis and holds dry mass exactly. GFDL's in-line `sa_sas`/`sa_aamf` have
  no TVD and no cloud-base subtraction.
- **MPAS only:** condensate above `config_microphysics_top` (default 45 km) is zeroed each step while vapour is left
  alone (`mpas_atmphys_interface.F` L936–946, L999–1003).

Commits read: ufs-community/ccpp-physics `ufs/dev` c7dc705; NCAR/ccpp-physics `main` f601ce9; NCAR/TEMPO `main`
c62699f; wrf-model/WRF `develop` 1086c86; MPAS-Dev/MPAS-Model `develop` aa6d8cd; NCAR/noahmp `master` 1a6225b;
NOAA-EMC/noahmp `develop` 2c7b3bc; NOAA-GFDL/GFDL_atmos_cubed_sphere `dev/emc` 71ff473 and `main` 8b94b9f. Not checked:
the CCPP single-column model, HAFS forks, MPAS's `physics_mmm` tree, the TH4 convection scheme.

## Appendix D — water created or lost by the WRF and MPAS dynamics

We ported the Thompson fixes to WRF (`release-v4.8.1` 315a8319, `em_quarter_ss`) and MPAS (`develop` aa6d8cd, 2-km
doubly periodic mesh, double precision) and ran an idealized supercell in each: no surface fluxes, 2 h. Once the scheme
closed (the microphysics adds 1.7 × 10⁻⁶ of precipitation in WRF, ≤ 10⁻¹⁵ kg/m² in MPAS), both hosts still changed
total water, through four operators:

| | Operator | Domain change / precipitation |
|---|---|---|
| W1 | WRF `horizontal_diffusion_s` (`diff_opt=2`; `module_diffusion_em.F` L3711–3999): each column's flux divergence is weighted by its own ρ·dz, so the domain sum does not telescope | −1.07 × 10⁻³ with TKE K, as the test case ships; 40 times smaller with constant K |
| W2 | WRF `vertical_diffusion_mp` (`diff_opt=1` without a PBL scheme, so idealized runs only; `module_big_step_utilities_em.F` L3192–3281): the surface flux is set to the first interior flux | +0.93 (water created) |
| MP1 | MPAS monotonic scalar transport's final clip (`mpas_atm_time_integration.F` L5774), which binds where the vertical Courant number exceeds 1 | +3.8 × 10⁻⁵ at dt = 12 s; 10⁻¹⁵ at dt = 8 s |
| MP2 | MPAS `atm_srk3` zeroes negative water species before the physics (L2797–2799) | +0.7 with `config_monotonic=.false.`; nothing with the limiter on |

WRF's real-data path (`diff_opt=1`, mass-weighted flux form) and WSM3 conserve. Without its positive-definite limiter
(`moist_adv_opt=0`), clipping by the physics creates 4.4 % of precipitation in WRF. Fixes for all four are being tested
in the same cases; nothing has been filed. Full tables and scripts: `patches/ports/README.md`.

## Appendix E — separate issues found along the way

These are not part of the proposal. Each is drafted as its own issue (`ccpp_physics_issue_draft.md`, issues 3–7).
E.1 and E.2 are in the GFS v17 suite; E.3–E.5 are in schemes outside it, measured in their own suites. Line numbers
are `ufs/dev` @242a2fc.

| | Scheme | What goes wrong | Size | Status | Owners |
|---|---|---|---|---|---|
| E.1 | NSST sea spray | spray fluxes applied explicitly; the lowest layer oscillates every other step in cyclone winds | blew up one 10-day C96 run at day 6.4 | no fix proposed | @XuLi-NOAA, @HelinWei-NOAA |
| E.2 | Noah-MP canopy wetted fraction | any canopy ice sets the wetted fraction from the ice alone, hiding the liquid | 45–48 % of wet-canopy steps | tested candidate; changes the land forecast beyond noise | @barlage, @cenlinhe |
| E.3 | MYNN-EDMF | surface moisture flux scaled by the wrong density, and the dew limiter zeroes all dew | creates 2–3.5 % of precipitation in the MYNN suites | tested fix | @joeolson42 |
| E.4 | GFDL microphysics v3 | species returned on a different mass basis from the one the host rebuilds (as TH1) | removes 1.0 % of grid-scale precipitation | tested fix | @RuiyuSun |
| E.5 | Grell–Freitas shallow convection | shallow-only columns dry the air but report no precipitation | GF loses 30–34 % of its precipitation | tested candidate; global precipitation +8.6 % | @haiqinli; RUC land @tanyasmirnova |

**E.1 NSST sea spray.** The day-6.4 blow-up in one 10-day v1 run is an existing instability. NSST's sea-spray term
(`sfc_nst.f90` L640–663, `lseaspray = .true.`, the P8 default; the same code in `sfc_ocean.F`), proportional to
`qs(T1) − q1`, is applied explicitly. In the eyewall of a C96 cyclone (10-m wind at the 30 m/s spray cap, a 22-m lowest
layer, a 720-s step) its gain is about 14 per step: the lowest layer flips by 2–5 K every other step, Thompson condenses
the overshoot, and once T1 exceeds the SST the layer runs away. From the same restart, the oscillation disappears with
spray off and stays bounded at half the time step; whether a run crashes is chaotic. A limiter cuts cyclone spray
about tenfold, so we propose no fix; the owners could solve the spray fluxes implicitly with the boundary layer, or
substep them. It is not a water defect, and we have not reproduced it on current `develop`.

**E.2 Noah-MP canopy wetted fraction.** `precip_heat` (L1389) and `canwater` (L7378) compute `fwet` from the ice alone
whenever there is any canopy ice. The ice capacity is about 50 times the liquid capacity, so a trace of intercepted
snow hides the liquid: canopy evaporation stops and transpiration takes the whole canopy. 45–48 % of wet-canopy steps
hold both phases; on those `fwet` averages 0.09, against 0.58 from the liquid alone, so there is no narrow fix. A
mass-weighted blend of the two fill fractions (the same as today for a single-phase canopy) raises it to 0.51–0.54.
The candidate diff first used for this (`patches/candidates/issue4_noahmp_fwet_mass_weighted.diff`) declared a local
`cwat` that shadows Noah-MP's specific heat of water, so the impacts measured with it are withdrawn. With stock land
options, taking the larger fraction (a clean edit) changes the 24-h forecast well beyond noise (land, 0–24 h means):
canopy evaporation +19 %, sublimation −13 %, land latent heat −0.44 %, land 2-m temperature −0.09 K, q2m −0.5 %. With
the conservation follow-on's land and energy options on (`conservation/canopy/patches/01_E2_noahmp_fwet_opt.diff`,
`noahmp_fwet_opt` 1 blend / 2 larger fraction), canopy evaporation +32 to +36 % and land latent heat +1.2 to +1.5 %.
Water and energy still close. With it, TH8 and TH9 are within noise from 6 h. It is a behaviour change for
the owners to evaluate against observations. NCAR's Noah-MP v5 uses the phase with more mass in one of the two places
(`CanopyHydrologyMod.F90` L104–108) and keeps the switch in the other (`CanopyWaterInterceptMod.F90` L132–137).

**E.3 MYNN-EDMF surface moisture flux.** The MYNN suites (`FV3_GFS_v17_p8` with MYNN, `FV3_HRRR`, `FV3_RRFS_v1beta`,
`FV3_RRFS_v1nssl`) create +2 to +3.5 % of precipitation per 6 h in 24-h C96 forecasts. In `module_bl_mynn.F90` the
driver divides the surface moisture flux by `rho1(kts)` (L1069), but `mynn_tendencies` multiplies it by a surface
density `rhosfc` (L4137, which also has a typo; used at L4391, L4456, L4521): +0.85 % of evaporation. The dew limiter
(L4514) zeroes every downward vapour flux: +0.55 to +0.9 %. **Fix (tested):** use `rho(kts)`, and the limiter its
comment describes; `FV3_GFS_v17_p8` with MYNN then closes to 0.00 %. Forecast impact not assessed.

**E.4 GFDL microphysics v3 mass basis.** The same defect as TH1: `gfdl_cloud_microphys_v3_mod.F90` converts in with
`1/(1 − qv)` (L973–985) and out with `1/(1 + qv_new)` (L1218–1232), and the CCPP driver keeps the updated `delp` that
would reconcile them in a local array (L174, L240, L263). The suite loses 0.3 % of precipitation per 6 h, the
microphysics 1.0 % of grid-scale precipitation. **Fix (tested):** convert back with the input humidity, in the scheme or
in the CCPP driver; the suite then closes to 0.00 %. Forecast impact not assessed.

**E.5 Grell–Freitas shallow precipitation.** In `cu_gf_driver.F90` the shallow tendencies are always applied (L951,
L993), but `raincv` includes the shallow precipitation only when deep convection is active (L1034). On 24-h C96
`rap_control`, GF loses 30–34 % of its own precipitation, all in shallow-only columns. Adding the scheme's own shallow
precipitation overshoots, because `cu_gf_sh.F90` computes it differently from the tendencies it applies. A tested
candidate (`patches/candidates/issue7_gf_shallow_precip_from_tendencies.diff`) reports the water the applied
tendencies remove, floored at zero (3.7 % of shallow-only column-steps are net moistening). GF then closes to
+0.004–0.005 kg/m² per 6 h, all 44 GF regression tests run with reproducibility intact, and global precipitation rises
8.6 % (convective +34 %): a change that needs the owners' judgement.

**Not located.** `FV3_GFS_v16_csawmg` (Chikira–Sugiyama convection, Morrison–Gettelman microphysics) creates about
+10.5 % of precipitation per 6 h in a 24-h C96 forecast, with or without these fixes. We have not traced it.

