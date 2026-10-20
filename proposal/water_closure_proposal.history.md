> **History.** Two archived full texts of `water_closure_proposal.md`, each kept verbatim: as of 14 October 2026, before the restructure; and (after the rule below) as of 15 October 2026, before it was cut by 20 %. The current document is `water_closure_proposal.md`.

# Proposal: closing the total-water budget in UFS physics

*Draft for the CCPP physics maintainers and the SAMF, Thompson and Noah-MP scheme owners. Ash Pera (NOAA GML / CIRES)
with Lori Bruhwiler, 13 October 2026. Not yet posted.*

## Summary

**The problem.** In a UFS forecast with the GFS v17 P8 physics, the physics creates water: **+0.25 % of precipitation
on the first day at C96** (+0.18 % per day over days 2–10, with no further decay) **and +0.45 % at C384**. We found four
defects on the atmosphere's side (A–D), three in how the host handles the Noah-MP land model (E–G) and two in Noah-MP
itself (H, I), measured each with the model's own diagnostics and with in-model water meters, and wrote and tested a small
fix for each:

| | Where | What goes wrong | Size | Fix |
|---|---|---|---|---|
| A | SAMF deep and shallow convection | at cloud base, the code subtracts a flux-limited value instead of what the updraft actually took | creates **+0.8 % of convective rain** (+1.0 % at C384) | diff 01, 6 lines |
| B | Thompson microphysics driver | converts humidity in and out with different denominators | removes **0.4 % of grid-scale rain** | diff 02, 16 denominators |
| C | Thompson microphysics | uncounted fog settling (C1); graupel not re-balanced after rate limiters (C2); sedimentation in a frame that drifts from the host's layer mass (C3) | removes most of the remaining **0.3 %** of grid-scale rain | diffs 03 and 05, 11 lines |
| D | Noah-MP land → atmosphere | water flux computed from latent heat with a different constant from the one the land model used | adds **+0.07 to +0.10 % of global precipitation** | diff 04, 1 line |
| E | surface iteration loop + Noah-MP | with the fractional grid, low-wind coastal land is stepped twice per time step, from its already-updated state | land gains **+3 to +5 % of global precipitation** (a quarter of the land is re-stepped every step); the atmosphere does not see it | diff 08, 3 lines |
| F | surface composites | coastal land snow is overwritten every step with the cell-mean composite | thin coastal snow is lost; Noah-MP undoes it for layered snow, which swamps its own water check | diff 09, 1 line |
| G | Noah-MP cold start | snow layers are built from the cell-mean snow, not the land snow Noah-MP is given | the first step deletes **0.29 kg/m² of land snow** (global mean) on snowy coasts and glacier margins | diff 10, 9 lines and 2 metadata entries |
| H | Noah-MP snow physics | snow under 10⁻³ mm without layers is set to zero, and the water goes nowhere; ice dripping off the canopy lands in exactly that range every step | removes **−0.009 % of global precipitation** from the land, 99.9 % of Noah-MP's remaining water-check error | diff 11, 3 lines |
| I | Noah-MP canopy water | canopy liquid or ice at or below 10⁻⁶ mm is set to zero, and the water goes nowhere; light interception often leaves exactly that much | removes **4 × 10⁻⁷ of land precipitation**, all of what H leaves | diff 12, 27 lines |

**The result.**
- **Atmosphere.** With A–C the residual falls from +0.25 % to **−0.005 % of precipitation at C96** on current upstream
  `develop`, and stays there for 10 days (−0.006 % per day, no drift). At C384 it falls from +0.45 % to **−0.001 %**.
- **Exact, inside the model.** Water meters in the physics and the dynamical core account for every step. With A–D
  plus three further Thompson changes (M4, M1, M2; section 5) the whole model conserves water to better than
  10⁻⁶ kg/m² per 6 h (0.000 % of precipitation). A double-precision meter that closes the physics against its own
  surface fluxes every step puts the physics at −1.6 × 10⁻⁸ kg/m² per 6 h (2 × 10⁻⁸ of precipitation). With A–C alone, the small remainder is Thompson's stale layer depth, which M4
  removes. The dynamical core and the physics→dynamics update conserve water to round-off, in 32- and 64-bit builds.
- **Land–atmosphere.** With D the atmosphere receives exactly the water the land model debits, to machine precision
  (in-model meters, section 6). An atmosphere-only budget cannot see this hand-off.
- **Land.** E–I take Noah-MP's own water check from a global +3.7 kg/m² per 6 h to rounding: −1.1 × 10⁻⁸ mm summed
  over 1.77 million land column-steps (against −15.6 mm with E–G and −0.014 mm with E–H), and land water changes only
  inside Noah-MP (section 7).
- **All thirteen diffs on current upstream** (`develop` + 01–13, C96): the total closes to 0.00000 kg/m² in every window
  after the first.

**Upstream status.** None of A–I is fixed upstream (ccpp-physics `ufs/dev` @242a2fc and NCAR `main` @f601ce9,
13 October 2026; E and F checked on `ufs/dev` only), and we found no issue or PR reporting them. H and I are also in
NOAA-EMC/noahmp; NCAR's Noah-MP v5 has I unchanged and deletes snow (H) at 10⁻⁶ mm. C1–C3 are in the Thompson scheme itself, so they also
affect its WRF and MPAS copies and its successor TEMPO. B and D come from the CCPP interfaces: WRF and MPAS pass
Thompson dry mixing ratios, and NCAR's own Noah-MP drivers already pass the water flux that fix D adopts (Appendix C).

**Why it matters to us.** NOAA's UFS-Chem reanalysis group plans multi-decade runs with prognostic CO2, CH4 and SF6.
Fix A also applies to every tracer that SAMF transports; whether its per-step tracer error (about 5 × 10⁻⁷ of the
column on smooth profiles, section 3) has a consistent sign, and so accumulates over decades, is what our planned
passive-tracer test will measure. Water closure is also a standing requirement for reanalysis budgets (Zhang et al. 2018 for E3SM; Becker et
al. 2022 for the IFS).

## 1. How we measured

**Code.**
- UFS-Chem v1 (Jian He's `dev-am4`, the code behind He et al. 2026, JAMES): ccpp-physics `f70b191` (2024), FV3 driver
  `a5c4305`, dycore `d4838c3`. All fixes were developed and first measured here.
- Current upstream: `ufs-weather-model` `develop` @112b1d46 with ccpp-physics `ufs/dev` @242a2fc. The defects are
  line-for-line the same (Appendix B), and the defect and fix measurements of section 2 were repeated here. The
  in-model meters, M4/M1, the C2 spin-up result, the single-column tests and the thickness tests are v1-only.

**Cases.** Regression-suite cases with suite `FV3_GFS_v17_p8_ugwpv1`, starting 2021-03-22 06Z, built with
`-DAPP=ATM -D32BIT=ON` (Intel) on MSU Hercules:
- `control_p8_ugwpv1`: C96 L127, dt = 720 s, run to 24 h, and to 240 h for the 10-day check;
- `control_c384`: C384 L127, dt = 300 s, run to 24 h.

**Scope.** One start date, one suite, atmosphere-only (no coupled ocean or chemistry suites), no cycling or IAU, 24 h
(10 days at C96, totals only), Intel with a 32-bit dynamical core (plus one 64-bit meter build), and OpenMP threads = 1.

**Budgets.** Global means on the native cubed-sphere grid with exact cell areas.
- **Total:** for each window, residual = ΔW − (E − P)·Δt, where
    - W is the column total of all six water species, Σ q·Δp/g, with Δp the full layer thickness, `dpres`/(1 − Σ
      condensate) (pitfall 6);
    - E = `lhtfl_ave`/hvap, which is exactly the evaporation `satmedmfvdifq` adds (it reports `dqsfc = ρ·hvap·evap`);
    - P = `prateb_ave`.
- **Per scheme:** with `ldiag3d = qdiag3d = .true.`, each scheme's column water tendency (`dtend_<species>_<process>`,
  integrated over the physics mass basis, which is `dpres`) is compared with that scheme's own boundary flux:
    - boundary layer against E;
    - convection (`qv_deepcnv + qv_shalcnv` plus condensate `cnvtrans`) against convective rain `cpratb_ave`;
    - microphysics against grid-scale rain, `prateb_ave − cpratb_ave`;
    - everything else against zero.
- **In-model meters** (diagnostic builds, Appendix A): exact water accounting at every step of the whole physics, of
  Thompson's column routine and driver, and of each part of the dynamical core and the physics→dynamics update.
- **Land–atmosphere hand-off (D):** exactly, with in-model meters on both sides (section 6); and offline, over land
  cells where `lhtfl` is the Noah-MP flux, the vapour the atmosphere receives (`lhtfl_ave`/hvap) against the water
  Noah-MP debits (its latent-heat components `evbs`, `evcw`, `trans` and `sbsno`, each converted with Noah-MP's own
  `hvap` or `hsub`).

**Validation.** The per-process diagnostics map to the right columns: the boundary-layer residual has median
10⁻⁴ kg/m² over all columns (correlation with E 1.0000), and microphysics column water loss correlates with grid-scale
precipitation at 1.0000. These correlations confirm the mapping; they cannot detect defects of 0.1–1 %, which is what
the global budgets and meters are for. Dry surface pressure is constant to 10⁻⁴ hPa after initialisation (pitfall 2).

### Pitfalls for anyone repeating this

1. **`prate_ave` and `cprat_ave` average since forecast start** (`time_avg_kind = 'full'`; `totprcp` is zeroed only
   at init). The per-window values are `prateb_ave` and `cpratb_ave`.
2. **`atmf000` is written after the first time step** in a cold start, but the first flux bucket includes that step.
   Here the first step rains out a 0.043 kg/m² cold-start burst, so a budget starting from `atmf000` shows a spurious
   +0.023 kg/m² in the first window. Measured from the initial condition (`gfs_data`) instead, the meters put none of
   the first window's residual in the physics (+1 × 10⁻⁵, step 1 included) or the dynamics; it is all in the cold-start
   initialisation, which we replicated offline column by column (it matches the model's printed post-IC totals to
   2 × 10⁻⁵ kg/m²):
   - **The IC was built on different terrain.** Its surface height is the raw orography (`orog_raw`) exactly; the
     model runs on the filtered orography (`orog_filt`), up to 500 m different. `remap_scalar` (`external_ic.F90`;
     `USE_GFS_ZS` undefined) therefore re-derives each column's surface pressure hydrostatically on the model's
     terrain and remaps onto it, adding or removing near-surface air: mean surface pressure −1.7 Pa (the model's
     `PS_diff` print), column water **−0.0024 kg/m²**.
   - Dropping the IC's top layer (`external_eta`) removes 3 × 10⁻⁷.
   - Rescaling `delp` by 1/(1 − condensate) converts the IC's dry-plus-vapour `delp` to FV3's total and creates nothing
     (pitfall 6 again: water from `gfs_data` must be Σ q·`delp`/(1 − condensate)).
   - The adiabatic initialisation (`na_init = 1`) adds back about +0.0003; neither `na_init = 0` nor
     `nudge_qv = .false.` removes the loss.
   The fix is on the IC side: build the IC on the model's filtered orography, or compile with `USE_GFS_ZS` to keep the
   IC's terrain. All results below use the windows after the first.
3. **FV3 writes `gfs_phys` 3-D diagnostics (`dtend_*`) to the `sfcf` files**, whatever the diag_table says.
4. **The per-scheme split needs short windows.** Each scheme's mean tendency is integrated over the mean of the
   window's start and end layer thicknesses. Over 24 hours, surface-pressure changes make that off by about 0.3 % of
   each scheme's flux (the boundary layer then shows −0.0004 kg/m² per day instead of ±2 × 10⁻⁵ per 6 h). The total
   budget uses exact snapshots and buckets, so the 10-day check reports the total only.
5. **Even 6-hour windows leave the split's absolute levels uncertain by about 10⁻⁴ kg/m² per 6 h.** We re-ran one
   build with hourly output (`fhzero = 1`) and integrated the same tendencies over 6-, 3-, 2- and 1-hour thickness
   means. The microphysics residual moved from −0.17 % through −0.12 % and −0.11 % to −0.11 % of grid-scale
   precipitation, convection from 0.00 % to +0.02 % of convective rain, and the split's "dynamics" from +1.2 × 10⁻⁴ to
   −1.4 × 10⁻⁴ kg/m² per 6 h, where the exact meters show zero. The totals are unaffected, and so are differences
   between builds (C2's effect agrees to 10⁻⁵ kg/m²). The split's "dynamics" moves away from zero at the finest
   interval, so thickness averaging is not its only error. We therefore use the split for differences between builds
   and for leftovers well above 10⁻⁴ kg/m², and in-model meters for absolute levels.
6. **The output `dpres` is not the dynamical core's layer thickness.** With GFS physics, `fv_nggps_diag.F90` writes
   `delp·(1 − Σ condensate)`, the dry-air-plus-vapour thickness the physics uses, while the water tracers are written
   per total mass. W = Σ q·`dpres`/g therefore misses about Σ q·condensate·Δp/g, which changes as clouds form and rain
   out. In our runs it showed up as a spurious "dynamics" loss of 3–6 × 10⁻⁵ kg/m² per 6 h (−0.005 % of
   precipitation, or −0.25 % of atmospheric water per year) and a +1 × 10⁻⁴ gain in the first window. Use
   `dpres`/(1 − Σ condensate) for W and `dpres` itself for physics tendencies.

## 2. Measured results

All values are global means in kg/m² per 6-hour window, averaged over the 6–24 h windows. A positive residual means
water is created. Percentages are of the matching precipitation: convective rain (P_conv) for convection, grid-scale
rain (P_grid) for microphysics, all precipitation (P) for the total.

**UFS-Chem v1, C96, each fix built and run separately:**

| Build | Convection residual | Microphysics residual | Total / P |
|---|---|---|---|
| unmodified | +0.0035 (+0.78 % of P_conv) | −0.0017 (−0.67 % of P_grid) | +0.27 % |
| A | +0.00002 (0.00 %) | −0.0017 | −0.22 % |
| B | +0.0035 | −0.0007 (−0.30 %) | +0.41 % |
| A + B | +0.00002 | −0.0007 | −0.09 % |
| A + B + C1 | +0.00002 | −0.0004 (−0.15 %) | −0.03 % |
| A + B + C2 | +0.00002 | −0.0008 (−0.33 %) | −0.10 % |
| A + B + C1 + C2 | +0.00002 | −0.0004 (−0.18 %) | −0.04 % |
| **A + B + C1 + C2 + C3** | +0.00002 | **−0.0002 (−0.07 %)** | **−0.003 %** |

Unmodified, the total is +0.29, +0.27 and +0.26 % of precipitation in the three windows. The totals are exact. The
per-scheme columns come from the split, whose absolute levels are uncertain by about 10⁻⁴ kg/m² (pitfall 5), so the
leftovers in the last row are not resolved; the meters below measure them.

**Noise floor for differences between builds.** Builds that differ only in diagnostics are bit-identical, so the
meters do not perturb the runs. A–C with and without D (which changes only the land flux, so the trajectories diverge:
precipitation 0.67780 against 0.67685 kg/m² in a window) agree in total and microphysics residual to 1 × 10⁻⁵ kg/m² per
window. That is our floor for build-to-build differences; it rests on this one pair.

**Exact physics/dynamics split** (v1 snapshot, C96; in-model meters, per window 6–12, 12–18, 18–24 h). A meter at
the end of every physics step sums Σ (q_new − q_old)·Δp/g over the six water species in each column. Then
R_phys = meter − (E − P)·Δt, and R_dyn = ΔW − meter covers the dynamical core and the physics→dynamics update. Both are
exact; no tendency output or thickness averaging is involved.

| Build | R_phys, kg/m² per 6 h | R_dyn, kg/m² per 6 h | Total / P |
|---|---|---|---|
| unmodified | +0.0020, +0.0019, +0.0018 | 0.000000 | +0.29, +0.27, +0.26 % |
| A–C + M4 + M1, M4 with the host's gas constants | +0.000008, +0.000009, +0.000010 | 0.000000 | +0.001 % |
| **A–D + M4 + M1** | **0.000000, −0.000000, 0.000000** | **≤ 0.000001** | **0.000 %** |

- **The meter can fail.** On the unmodified build it reports the +0.26–0.29 % physics source. The per-scheme split
  agrees to 1–1.6 × 10⁻⁴ kg/m² per window, its own error (pitfall 5).
- **With all fixes the physics conserves**, to better than 10⁻⁶ kg/m² per 6 h. The +1 × 10⁻⁵ in the middle row is
  M4 computing Thompson's density with the host's gas constants instead of Thompson's (section 5): 3.5 × 10⁻⁵ of
  grid-scale precipitation, which matches it window by window.
- **The dynamics and the physics→dynamics update conserve water.** R_dyn is zero to 10⁻⁶ kg/m² in every window,
  including the first, in both 32-bit (`-D32BIT=ON`) and 64-bit builds. Further meters inside the dynamical core
  (`fv_dynamics`, and within it `neg_adj3`; `fv_subgrid_z`; the update that writes the physics back, including
  `fill_gfs`; `fv_update_phys`) each change water by less than 3 × 10⁻⁷ kg/m² per step in 32-bit (round-off of both
  signs) and about 10⁻¹² in 64-bit, and together they account for the snapshot changes to 3 × 10⁻⁸ kg/m². In 64-bit the
  `fv_dynamics` and hand-off meters carry equal and opposite offsets of 8 × 10⁻¹³ per step, an artefact of where the
  meters sit. `fill_gfs` and `fv_update_phys` never changed water in these runs, so their meters show they were
  inactive, not that they conserve; that rests on the code.
- The first window is left out because R_phys there carries pitfall 2.

**Current upstream `develop`:**

| Case | Build | Convection residual | Microphysics residual | Total / P |
|---|---|---|---|---|
| C96 | unmodified | +0.0035 (+0.81 %) | −0.0018 (−0.68 %) | +0.25 % |
| C96 | + diffs 01–03 | +0.0001 (+0.03 %) | −0.0005 (−0.18 %) | −0.05 % |
| C96 | + diffs 01–03, 05 | +0.0001 (+0.03 %) | −0.0002 (−0.07 %) | **−0.005 %** |
| C96 | + diffs 01–05 | +0.0001 (+0.03 %) | −0.0002 (−0.07 %) | **−0.005 %** |
| C384 | unmodified | +0.0047 (+0.97 %) | −0.0011 (−0.38 %) | +0.45 % |
| C384 | + diffs 01–03, 05 | +0.0003 (+0.05 %) | −0.0003 (−0.09 %) | **−0.001 %** |

**Ten days** (`develop`, C96, 240 h, 24-hour windows, total budget only; see pitfall 4):

| Build | Residual per day, days 2–10 | / P | Range over the days | Accumulated over days 2–10 |
|---|---|---|---|---|
| unmodified | +0.0055 kg/m² | +0.18 % | +0.15 to +0.22 % | +0.050 kg/m² |
| + diffs 01–05 | −0.00017 kg/m² | −0.006 % | −0.008 to −0.005 % | −0.0016 kg/m² |

What the tables show:
- **The defects and fixes reproduce on current code**, to within a few hundredths of a percent of the v1 snapshot
  (+0.25 % against +0.27 % unmodified, −0.005 % against −0.003 % with A–C).
- **The fixed residual is stable.** Over ten days it stays close to the 24-hour result (−0.00003 kg/m² per 6 h ≈
  −0.00013 per day) and does not drift. The unmodified error is smaller after the first day (+0.18 % per day over
  days 2–10, against +0.25–0.29 % per 6-hour window on day 1) but does not decay further.
- **The convective error is larger at C384** (+0.97 % of convective rain, against +0.81 % at C96) and is most of the
  larger C384 total. C384 also uses a shorter time step (300 against 720 s), and upstream convection is computed by
  difference, so this is not a clean resolution dependence. The microphysics loss is smaller at C384 (−0.38 % against
  −0.68 %).
- **In the fixed rows the per-scheme leftovers are not resolved.** They are about 10⁻⁴ kg/m² and opposite in sign, the
  size of the split's own error (pitfall 5), and the exact totals are −0.005 % and −0.001 %. Upstream, convection is
  computed by difference (next bullet), so it inherits the microphysics column's error.
- **A diagnostic gap on `develop`.** With SAMF, `dtend_liq_wat_cnvtrans` and `dtend_ice_wat_cnvtrans` are always zero,
  and the detrained condensate (≈ 0.3 kg/m² per 6 h) appears in no `dtend`. `GFS_suite_interstitial_4` now builds
  `cnvtrans` from per-scheme deep/shallow condensate tendencies, which only Grell–Freitas and C3 convection fill. The
  upstream convection column is therefore total − microphysics − boundary layer.
- **Global precipitation changes little.** It differs by at most 0.5 % per window between builds. We have not run
  forecast verification, and D does change the physics over frozen surfaces (section 6).

## 3. Fix A — SAMF cloud-base double count (deep and shallow, water and tracers)

**The defect.** In `samfdeepcnv.f` (ufs/dev line numbers):
1. The updraft starts at cloud base `kb` with the environment's value, `qcko(i,kb) = qo(i,kb)` (L1622); the downdraft
   starts at `jmin` with `qrcdo(i,jmin) = qo(i,jmin)`.
2. The compensating-subsidence flux at each interface uses the TVD-limited value `tem1` (introduced by
   NCAR/ccpp-physics#754, 2021).
3. To avoid counting the cloud-base flux twice, the code subtracts it in advance ("subtract the double counting change
   rates at jmin+1 & kb beforehand", L2551–2561), using `eta·tem1` and `edto·etad·tem1`.

But the updraft actually removed `eta·qo(kb)`. Wherever the limiter is active (`tem1 ≠ qo`), the difference is water
created or destroyed:

ΔW = xmb·Δt·[η(k_b)·(qo(k_b) − tem1(k_b)) + edto·η_d(j_min)·(qo(j_min) − tem1(j_min))]

The tracer loop repeats this with `ctro` (L2635–2645). `samfshalcnv.f` has the equivalent at `kb` (L1979–2005, tracers
L2040–2050): its flux-divergence loop starts above `kb`, so the cloud-base flux must equal what the updraft takes.

**The fix** (diff 01): in deep convection subtract `qo(kb)` and `qo(jmin)` (tracers: `ctro`); in shallow convection
set the cloud-base TVD flux to `eta·qo(kb)` (tracers: `eta·ctro(kb)`). These are different choices:
- **Deep** keeps the limited cloud-base flux `eta·tem1` and debits layer kb by what the updraft took, `eta·qo`.
- **Shallow** replaces the cloud-base flux itself with the unlimited `eta·qo(kb)`, so the correction lands in layer
  kb+1, where the limiter's positivity protection is then removed.
- **An alternative** for both is to start the updraft from the limited value (`qcko(kb) = tem1`) and keep the
  subtraction as it is. We have not tested it.

**Evidence.**
- **Single column**, unmodified Fortran, dt = 720 s: +7 to 8 × 10⁻⁴ kg/m² per step on smooth profiles (0.05 % of
  rain), and up to 4 % of rain (deep) or 23 % (shallow) on jagged humidity profiles. All seven cases created water.
  With the fix every case closes to ≤ 2 × 10⁻¹⁴ kg/m².
- **Full model:** the convection residual drops from +0.0035 to +0.00002 kg/m² per 6 h at C96, and from +0.0047 to
  +0.0003 at C384 (by difference; section 2).
- **Tracers:** about 5 × 10⁻⁷ relative column change per convective step on a smooth tracer profile, and none on a
  linear one (where the limiter returns `qo`).

**Questions for the SAMF owners.**
1. Was `tem1` here intentional, for example to keep the cloud-base layer positive? The fix does not affect positivity
   in practice. The scheme's negative-value borrowing step (Han et al. 2022, Eqs. 10–11) still runs, and we counted how
   often it acts: over 24 h at C96 it was needed in 104 of 330 557 deep-convecting column-steps without the fix
   (0.25 kg/m² borrowed in total) and 97 of 327 916 with it (0.28 kg/m²). Shallow convection needed it once.
2. Are there other places where a TVD-limited flux meets an exact parcel source (detrainment levels, cloud top)? Our
   single-column budget closes to round-off after this fix, which suggests not, at least for these test profiles.
3. Which of the three forms above do you prefer? Deep and shallow should probably use the same one.

## 4. Fix B — Thompson mass basis

**The defect.**
1. FV3 passes physics its tracers as mass per (dry air + vapour): condensate is removed from each layer's thickness
   (`atmosphere.F90` L2207, L2234, `dev/emc`).
2. After physics it rebuilds each species' mass as that same pre-physics thickness × the returned value
   (L1659–1677).
3. `mp_thompson.F90` converts to mixing ratios with `/(1 − q_v)` (ufs/dev L690–704). With fix B the round trip is
   exact. The `spechum` it uses is the vapour after the boundary layer and convection, not the start-of-physics vapour
   that defines the host's basis, so these are not the true dry mixing ratios; mass conservation is unaffected.
4. It converts back with `/(1 + r_v,new)` (L944–957), i.e. per (dry air + *new* vapour).

So every species comes back scaled by (m_d + m_v,old)/(m_d + m_v,new): net condensation creates water and net
evaporation removes it. In this case Thompson's net vapour change is positive (it evaporates much of the detrained
convective condensate), so the error is a sink.

**The fix** (diff 02): convert back with `×(1 − spechum)`, using the scheme's unchanged input `spechum`, and use that
same `spechum` in the forward conversion. The returned values are then on whatever basis the host supplied, and the
host's mass rebuild is exact. Using the input `spechum` both ways should also keep it exact when the scheme
sub-cycles (`dt_inner < dtp`); that is untested, since `dt_inner` equals the physics step in all our runs. GFDL microphysics already does the equivalent (Zhou, Harris and Chen 2022, §2.4: "air mass is
exactly conserved"), following Harris et al. (2021) Eq. 9.5.

**Evidence.** The microphysics residual falls from −0.0017 to −0.0007 kg/m² per 6 h, about 55 %. The only later users
of the returned humidity in this suite (`GFS_MP_generic_post` tendency diagnostics) take differences against the saved
input, so they become more consistent, not less.

**Other hosts.** TEMPO's CCPP driver (`mp_tempo.F90` L437–455, L532–549) has the same conversion. WRF and MPAS pass
Thompson dry mixing ratios directly, so B cannot occur there (Appendix C).

## 5. Fix C — Thompson's own bookkeeping

After fix B, Thompson still removes 0.30 % of grid-scale precipitation. We built and measured three fixes in
`module_mp_thompson.F90` (ufs/dev line numbers; C1 and C2 in diff 03, C3 in diff 05).

**C1, fog settling.** The cloud-water sedimentation loop (L4044–4057) moves `sed_c(kts)` out of the lowest layer, but
unlike rain, ice, snow and graupel (L3996, 4091, 4121, 4152) it never adds it to a precipitation total. The fix adds
`pptrain = pptrain + sed_c(kts)*DT`. The water really does leave the atmosphere (fog and drizzle deposition), so this
corrects the accounting, not the physics.
**Measured: −0.30 % → −0.15 % of grid-scale precipitation.**

**C2, graupel after the rate limiters.**
- Rain collecting snow below 0 °C conserves water by construction, `prr_rcs + prs_rcs + prg_rcs = 0`, until the clips
  at L2796–2798. Those clips, and the ice, rain and snow limiters (L3140–3176), rescale `prr_rcs` and `prs_rcs` but not
  `prg_rcs`.
- Likewise `prg_rci = pri_rci + prr_rci` is set at L3029, before the ice and rain limiters rescale its terms, and is not
  recomputed in the re-closure block (L3189–3198).
- The fix recomputes both graupel gains after the limiters.

**Measured: C2 matters mostly while the model spins up.**
- In the first 6 hours of a cold start, C2 removes a source of 0.76 % of that window's grid-scale precipitation
  (0.0019 kg/m², v1 snapshot with C1 and M4).
- After that it removes about 0.03 %. The tables in section 2 average the 6–24 h windows, so they show only this
  (−0.33 % vs −0.30 %).
- Over the full 24 hours the column-routine meter (below) and the host budget agree on C2's effect: −0.22 % and
  −0.21 % of grid-scale precipitation.
- The spin-up source presumably arises because the rate limiters act most while the initial hydrometeor fields adjust.
  We have not tested whether analysis increments in a cycled system produce similar bursts.

**C3, sedimentation density** (diff 05).
- Thompson converts each hydrometeor to a mass density with `rho = 0.622·p/(R·T·(qv+0.622))`, evaluated at entry.
  That density times dz equals the host's dry-air layer mass to within about 10⁻⁴, so `Σ q·rho·dz` is the host's
  column water.
- But Thompson recomputes `rho` from the *updated* temperature three times before sedimentation (L3386 after the source
  terms, L3660 after the saturation adjustment, L3743 after rain evaporation) and sediments in that frame.
- Latent heating lowers `rho` by about ΔT/T, so every kilogram that falls out of the column in Thompson's frame removes
  about 1 + ΔT/T kilograms of host water.
- The fix keeps the entry density for all mass conversions. At the first recompute it uses the updated density
  (`rhon`) for fall speeds and viscosity; the rain-evaporation block (`orho`, `rhof`, `vsc2`, `rvs`) and the
  pre-sedimentation `rhof` now use the entry density. The physics changes only through these, by less than 0.1 % in
  density. Computing `rhon` at those sites too would keep them as they were; we have not tested that variant.

**Measured: −0.18 % → −0.07 % of grid-scale precipitation.** Fixing only the first recompute gave −0.13 %, so the
saturation-adjustment step, where the heating is largest, carries most of the error.

**M2, surface precipitation thresholds (diff 13).** The sedimentation flux out of the lowest layer always leaves the
column, but it is added to the surface precipitation only when the water left in that layer exceeds `R1·rr_min`
(L3995, 4090, 4120, 4151, for rain, ice, snow and graupel). Below the threshold the water is deleted. We first judged
these thresholds not needed, because removing them changed the residual by less than 10⁻⁵ kg/m², the resolution of
that test. A double-precision meter (Appendix A) that closes the physics' column water against its own evaporation,
precipitation and `h2ophys` source every step and column then found a one-signed loss of 1.46 × 10⁻⁷ kg/m² per 6 h,
93 % of it in Thompson's sedimentation stage. Counting every flux out of the lowest layer as precipitation takes it
to −1.6 × 10⁻⁸ kg/m² per 6 h (2 × 10⁻⁸ of precipitation), and the largest column residual from 1.3 × 10⁻⁴ to
1.7 × 10⁻⁸ kg/m². The rest is inside Thompson's column routine, which in the v1 snapshot computes in single precision:
−9 × 10⁻⁹ where it treats hydrometeors at or below `R1` as absent on entry, −6 × 10⁻⁹ in sedimentation.

**What remains, and two further changes (M4, M1).** After A–C the host split shows microphysics losing 0.07 % of
grid-scale precipitation. That is at the split's resolution (pitfall 5), so we measured inside the model with two
meters (Appendix A), both summing every column at every call over the 24-hour run:
- **Column routine.** Thompson's column routine, accounted stage by stage (entry clip, source and sink terms,
  condensation, sedimentation, final clips) in the host's dry-air mass frame. With A–C every stage closes, and the
  routine as a whole conserves to +0.002 % of its precipitation. That small source comes from zeroing negative
  hydrometeors at the end of the step (L4241–4300).
- **Driver.** The whole driver call (`mp_thompson.F90`, conversions included), in the host's own variables:
  Σ (q_v + condensate)·Δp/g before and after, plus precipitation. In the two builds where we ran both meters (both
  with the first version of M4), the driver meter equals the column meter plus 0.0035 % of grid-scale precipitation.
  That is exactly the 3.5 × 10⁻⁵ gas-constant mismatch described under M4; the driver's conversions add nothing.
  Nothing else between `GFS_MP_generic_pre` and `GFS_MP_generic_post` changes moisture, so this is also what the host's
  `dtend_*_mp` sees.

The two changes:
- **M4, layer depth from the host's layer mass.** The driver takes `dz` from `phii`, which `get_phi_fv3` computes
  before deep and shallow convection run. Convective heating then leaves Thompson's ρ·dz slightly off the host's layer
  mass. M4 passes the host's interface pressures (`prsi`, an extra argument in `mp_thompson.meta`) and sets
  `dz = Δp·(1 − q_v)/(g·ρ_T)`, with ρ_T Thompson's own entry density, `0.622·p/(287.04·T·(r_v + 0.622))`, so Thompson's
  ρ·dz is exactly the host's dry-air mass in each layer. The constants matter: built with the driver's ρ, which uses
  the host's `con_rd = 287.05` and `con_eps`, ρ·dz comes out 3.5 × 10⁻⁵ too large and sedimentation creates that
  fraction of grid-scale precipitation. The driver meter needs `prsi`,
  so it runs only in M4 builds.
- **M1, clipped condensate returned to vapour.** Instead of deleting hydrometeors that end the step negative or below
  `R1`, M1 exchanges them with vapour (with the matching latent heat), so the final clip conserves water.

Measured on the v1 snapshot (C96). The column meter sums columns unweighted; the split and the total are area-weighted
global means:

| Build | Column-routine meter, 0–24 h (% of its precipitation) | Host split, microphysics, 6–24 h (6-hour thickness) | Total / P, 6–24 h |
|---|---|---|---|
| A–C | +0.002 % | −0.067 % of P_grid | −0.003 % |
| A–C + M4 (host's gas constants) | +0.002 % | −0.053 % | +0.001 % |
| A–C + M4 + M1 (host's gas constants) | 0.000 % | −0.055 % | +0.001 % |
| A–D + M4 + M1 (Thompson's gas constants) | −0.0000 % | not run | 0.000 % |

- **M4 moves the host microphysics residual by +0.014 % of grid-scale precipitation.** That is a difference between
  builds, which the split does resolve. Before M4, Thompson's stale layer depth turned its own conservation into a small
  loss of host water.
- **Combining the meters with that difference:** with A–C, microphysics conserves to about −0.01 % of grid-scale
  precipitation (+0.002 % in the column, −0.014 % from the stale depth). That matches the exact total for A–C,
  −0.003 % of all precipitation (−0.009 % of grid-scale), since the rest of the model conserves. With M4 (Thompson's
  gas constants) and M1 the whole physics closes to better than 10⁻⁶ kg/m² per 6 h.
- **M1 removes the clip loss** (+0.002 %), too small for any budget to see; M2 (above) removes the last loss the
  double-precision meter can see.
- **Diffs.** M4 is diff 06 and M1 diff 07 against `ufs/dev`. Upstream Thompson takes `R` and `RoverRv` from the host
  (`con_rd`, `con_eps`), so there M4 divides by the driver's own `rho`, which is Thompson's density; the gas-constant
  mismatch exists only in the v1 snapshot. With diffs 01–07 the C96 total is 0.00000 kg/m² per 6 h (−0.00003 with
  01–05). M4 adds `prsi` to `mp_thompson.meta`.

The IFS experience (Becker et al. 2022: clipping "effectively adds condensate mass", 4.6–10.7 % of precipitation at
9–4 km, reduced to about 0.1 % by fixers) suggests clips matter more at higher resolution. We do not see that at C384
yet: its fixed total is −0.001 %, against −0.005 % at C96.

**Other hosts.** C1–C3 are in the scheme itself, so they are also present in the WRF and MPAS copies of Thompson and
in TEMPO, which counts settled cloud water only in its freezing-rain diagnostic (Appendix C).

## 6. Fix D — Noah-MP water flux to the atmosphere

**The defect.**
- `noahmpdrv.F90` (ufs/dev L1526) gives the atmosphere `evap = latent_heat_total/ρ/con_hvap`, using the host's
  2.5 × 10⁶ J/kg.
- Noah-MP removes the water from the land with its own latent heats (`module_sf_noahmplsm.F90` L188–189:
  `hvap = 2.5104e6`, `hsub = 2.844e6`), switching to `hsub` for ground, canopy and transpiration fluxes whenever the
  ground or canopy is below freezing (`latheag`, `latheav`, L2211–2223).
- So the atmosphere receives 0.4 % more water than unfrozen land loses, and 14 % more over frozen surfaces. A quarter
  to a half of the global effect is the hvap mismatch; the rest is snow sublimation (4–11 % of land latent heat in this
  March case).
- An atmosphere-only budget cannot see this, because the boundary layer closes on whatever `evap` it is given.

**The fix** (diff 04): pass the water flux Noah-MP already computes, `(ecan + etran + edir)/ρ`, as `evap`, and keep
latent heat for the energy coupling. Water then closes between land and atmosphere: Noah-MP's air density and the
boundary layer's are computed identically, and the meters below confirm the closure to machine precision.
- **This changes the physics, not only the bookkeeping.** Latent heat is unchanged, but the water flux over snow and
  frozen ground falls by up to 12 % (hvap/hsub), so the atmosphere is moistened less there.
- This is what NCAR's own Noah-MP drivers already do: the WRF, HRLDAS, MPAS and LIS drivers all hand the atmosphere
  `QFX` = canopy + ground evaporation + transpiration. The latent-heat form exists only in the CCPP port (ccpp-physics,
  and NOAA-EMC/noahmp's CCPP driver and NUOPC land component; Appendix C).
- The latent-heat constants still differ on the energy side; that is tracked in NCAR/ccpp-physics#582 ("use host
  constants").
- E3SM found the same class of error: a surface moisture flux re-derived from latent heat "ignoring the distinction
  from sublimation" (Zhang et al. 2018).

**Evidence.** The land–atmosphere gap (section 1) per 6-hour window, as a percentage of global precipitation:

| Window | v1 snapshot, A–C | v1 snapshot, A–D | `develop` + 01–03, 05 | `develop` + 01–05 |
|---|---|---|---|---|
| 0–6 h | +0.11 % | −0.06 % | +0.13 % | −0.07 % |
| 6–12 h | +0.05 % | −0.02 % | +0.07 % | −0.02 % |
| 12–18 h | +0.05 % | +0.02 % | +0.07 % | +0.03 % |
| 18–24 h | +0.07 % | −0.01 % | +0.09 % | +0.00 % |

- **This offline estimate cannot verify D.** After the fix it scatters by up to ±0.07 % in both directions, because it
  re-derives the land's loss from latent-heat components (frozen ground outside the snowpack at `hvap` rather than
  `hsub`). The in-model meters below do verify it.
- **Measured exactly, the fix closes the hand-off.** In-model meters (v1 snapshot with A–C + M4 + M1; Appendix A) sum,
  every step and over every land fraction, the water Noah-MP debits (`ecan + etran + edir`) and the water the boundary
  layer adds for it (`evap_lnd·ρ_a·Δt`, as `satmedmfvdifq` books it). Without the fix the atmosphere receives
  +4.5 to +6.9 × 10⁻⁴ kg/m² per 6 h more than the land loses (+0.07 to +0.10 % of global precipitation). With the fix
  the difference is 0 to machine precision in every window. Noah-MP's `density` and the boundary layer's `ρ_a` are
  identical. The boundary layer adds 4.1 × 10⁻⁸ more water than it books (+3.1 × 10⁻⁸ kg/m² per 6 h globally,
  one-signed, measured with the double-precision meter of section 5); we have not traced it.
- **The precipitation hand-off is exact too.** Noah-MP's own precipitation (`prcp`, convective plus grid-scale rates)
  equals the host's `tprcp` to 10⁻¹⁶. It arrives one step late, which moves up to 10⁻³ kg/m² across a window
  boundary but nets to zero.
- **The atmosphere budget is unchanged** at −0.005 % of precipitation; the boundary layer closes on the new `evap`.
- **A land storage budget** (soil moisture + snow + canopy water) cannot close in absolute terms, because Noah-MP's
  aquifer storage (`iopt_run = 1`) is not in the output. Its change between runs with and without the fix
  (0.0003–0.0012 kg/m² per window) matches the change in the gap.
- **Per call, not per step, until E is fixed.** These meters compare the atmosphere with the last Noah-MP call of each
  step. Where the land is stepped twice (E, section 7) it debits evapotranspiration twice and receives precipitation
  twice, while the atmosphere exchanges each once.
- **The v1 snapshot needed one extra edit.** Its glacier branch sets canopy evaporation and transpiration to
  `undefined` (9.99 × 10²⁰), so they must be zeroed there. `ufs/dev` already sets them to 0.0 (L1186–1187), so diff 04
  needs nothing more.

## 7. Fixes E–I — Noah-MP's land water

We metered Noah-MP's own water every step (Appendix A): canopy, snow, soil and aquifer water as the driver receives them
and as it returns them, with precipitation, evapotranspiration and runoff. Its `errwat` check (computed, never acted on)
was +3.7 kg/m² per 6 h globally, and storage changed *between* calls, where nothing should touch it. Two host-side
defects explain both (E, F). A third (G) acts once, at a cold start, and two in Noah-MP's own physics (H, I) account for
everything that remained.

**E, land stepped twice.**
- The surface schemes run in a two-pass loop. `GFS_surface_loop_control_part2` (ufs/dev L50) re-flags a point for the
  second pass when `(dry .and. lsm /= lsm_noahmp) .or. (wet .and. nstf_name1 > 0)`: Noah-MP land is meant to be
  excluded. With `frac_grid` a coastal cell is both `dry` and `wet`, so the second clause re-flags it, and
  `noahmpdrv` (L953) tests only `flag_iter .and. dry`.
- Noah-MP then steps the land again from the state the first pass already updated. Noah and RUC save and restore their
  state for the second pass (`flag_guess`); `noahmpdrv` has no such code.
- **Fix** (diff 08): pass the CCPP loop counter and compute land on the first pass only.

| Window | Precipitation added to land again | Evapotranspiration debited again | Net land water created | / global P |
|---|---|---|---|---|
| 6–12 h | 0.051 kg/m² | 0.026 | +0.022 | +3.3 % |
| 12–18 h | 0.049 | 0.012 | +0.036 | +5.2 % |
| 18–24 h | 0.054 | 0.015 | +0.038 | +5.3 % |

About a quarter of the land area (24–27 %) is re-stepped every time step: low-wind coastal cells, whose land then runs
its physics at twice the model's speed. The atmosphere's budget does not see this, because it exchanges water with the
final pass only (and stays at 0.000000 with or without the fix). This affects any configuration with `frac_grid` and
NSST, which includes this GFS v17 suite.

**F, coastal land snow overwritten.**
- `GFS_surface_composites_post` (L105) sets the cell-mean snow `weasd = txl·weasd_lnd + txi·weasd_ice`. On the next
  step `GFS_surface_composites_pre` (L274) sets `weasd_lnd = weasd` for every land model except RUC. But with
  `frac_grid` `weasd_lnd` is the persistent land value (`Sfcprop%weasdl`, initialised at a cold start by dividing out
  the land and ice fractions), so coastal land snow is diluted every step.
- Noah-MP rebuilds its snow total from its own snow layers, so layered snow comes back. That rebuild is what swamped
  `errwat`: +16 mm per land column per 6 h in, −16 mm per 6 h out. Thin snow without layers is not rebuilt, and is lost
  (about 0.005 mm per land column per 6 h).
- **Fix** (diff 09): with `frac_grid`, keep `weasd_lnd` (as RUC already does).

**With E and F** (v1 snapshot, A–F + M4 + M1, metered):
- Noah-MP's `errwat` falls to −5 to −7 × 10⁻⁵ kg/m² per 6 h globally (−0.009 % of precipitation), and is exactly 0 on
  glacier points.
- Every storage term changes by exactly 0 between calls.
- The remainder, −0.00025 mm per land column per 6 h at soil points, is inside Noah-MP's own physics (H below).

**G, cold-start snow layers built from the wrong snow.**
- At a cold start fv3atm derives the land snow `weasdl = weasd/(landfrac + fice·(1−landfrac))`, and `noahmpdrv` is
  given `weasdl`. But `GFS_phys_time_vary_init` builds Noah-MP's snow layers (`snicexy`) from the cell-mean `weasd` and
  `snowd`.
- On its first step Noah-MP rebuilds its snow total from the layers, so coastal and glacier land loses
  `weasdl − weasd` at once: **0.29 kg/m² as a global mean** (about 1 kg/m² per unit land area, in about 3700 snowy
  coastal columns and the glacier margins). Only the land sees it; the atmosphere's budget does not.
- **Fix** (diff 10): use `weasdl` and `snodl` in the Noah-MP initialisation block. The first-step loss is then 0.

**H, thin snow deleted.**
- Noah-MP sets snow without layers to zero when `snowh <= 1e-6` m or `sneqv <= 1e-3` mm, in three places (`energy`,
  `snowh2o`, and the end of `noahmp_sflx`), and the water goes nowhere.
- Ice dripping off the canopy (`precip_heat`) reaches the ground as about 10⁻⁴ mm of snowfall per step, so on
  snow-free ground under a frosted canopy `snowh2o` deleted it every step. A meter at each site found 15.60 mm moved in
  124,000 events in `snowh2o`, 0.02 mm in `energy` and none at the end of `noahmp_sflx`: the whole of the −15.6 mm
  that `errwat` summed over the run.
- **Fix** (diff 11): add the truncated snow to the top soil layer as ice, as `snowh2o` already does with excess
  sublimation. Snow with layers is unchanged. Glacier points need no fix (their balance is already 0.00000).

**I, canopy water deleted.**
- After H, `errwat` still summed to −0.014 mm (4 × 10⁻⁷ of land precipitation). It was negative in every snow state,
  and 10⁴ times what double-precision rounding of the stored water could give, so not rounding.
- `canwater` sets canopy liquid and canopy ice to zero when either is at or below 10⁻⁶ mm (`ufs/dev` L7346, L7355),
  and the water goes nowhere. Light rain or snow intercepted by the canopy often leaves exactly that much after
  evaporation and dew, so it vanished on about 5 % of land column-steps.
- A meter of the deleted water accounts for the whole of `errwat` in every snow state, to better than 1 part in 10⁴
  (0.0141 mm deleted against −0.0141 mm `errwat`). Glacier points, which have no canopy, already closed.
- **Fix** (diff 12): `canwater` returns the truncated liquid and ice, and `water()` adds them to the rain and snowfall
  reaching the ground (the ice at the fresh-snow density). There is no phase change, so no latent heat is created or
  lost, and the fix does not depend on D.
- We first tried evaporating the water through `ecan`. That closes the water too, but hands the atmosphere vapour
  whose latent heat the canopy never paid: up to 3.5 × 10⁻³ W/m² at a point for one step, about 3 × 10⁻⁵ W/m² over
  land.

**With E–I** (v1 snapshot, A–I + M4 + M1, metered, C96, 24 h; the E–I column used the first, `ecan`, version of I.
The final version gives the same over 6 h: −3.1 × 10⁻⁹ mm against −2.8 × 10⁻⁹ mm, and −2.5 × 10⁻³ mm without I):

| | E–G | E–H | E–I |
|---|---|---|---|
| `errwat` summed over 1.77 M soil column-steps | −15.6 mm | −0.014 mm | −1.1 × 10⁻⁸ mm |
| column-steps with \|`errwat`\| ≥ 10⁻⁴ mm | 37,110 | 0 | 0 |
| column-steps with \|`errwat`\| ≥ 10⁻⁷ mm | — | 326 | 0 |
| land balance within calls, soil points, mm per column per 6 h | −0.00023 to −0.00030 | 0.00000 | 0.00000 |
| storage change between calls | 0.00000 | 0.00000 | 0.00000 |

- The atmosphere still closes to 0.000000, and on current upstream with diffs 01–13 to 0.00000 kg/m² per 6 h.

## 8. Suggested test plan

1. Apply diffs 01–03 and 05–13 to `ufs/dev` (and 04 once the Noah-MP owners have weighed in), build, and run the
   regression suite. Baselines will change, since the fixes change answers; E changes the land state at a quarter of
   the land.
2. Add a water-budget check to one regression test: the whole-physics meter (exact, no `dtend` output needed) and, for
   attribution, `ldiag3d`/`qdiag3d` with the per-scheme closure above. Our scripts take a run directory and print the
   tables in sections 2 and 6 (Appendix A).
3. Confirm forecast neutrality on the standard verification (e.g. a 10-day cycled comparison). A–C change mass
   bookkeeping; D changes the water flux over frozen surfaces, and E the land physics of low-wind coastal cells.
4. Repeat the budget at C768 or a convection-permitting resolution, where Becker et al. (2022) found clipping errors
   grow. At C384 they have not grown yet, and A–C close the budget there too.

## 9. Requests

- **SAMF owners** (@JongilHan66, @lisa-bengtsson): review fix A, including the tracer loops.
- **Thompson / TEMPO owners** (@gthompsnWRF, @RuiyuSun, @AndersJensen-NOAA): review fixes B and C, and say whether
  M4 (diff 06, layer depth from the host's mass), M1 (diff 07, clips returned to vapour) and M2 (diff 13, all
  sedimentation out of the lowest layer counted as precipitation) are acceptable. C1–C3 also apply to
  the WRF and MPAS copies and to TEMPO; B also applies to TEMPO's CCPP driver.
- **Noah-MP owners** (@barlage, @cenlinhe): review fix D, and say whether `evap` should carry the mass flux or the
  energy side should switch to host constants (NCAR/ccpp-physics#582); review fix E (land stepped twice in coastal
  cells) and say whether Noah-MP should instead save and restore its state for the second pass, as Noah and RUC do;
  review fixes H and I (thin snow to the soil and truncated canopy water to evaporation, rather than deleted), which
  NOAA-EMC/noahmp and NCAR's Noah-MP v5 would also need.
- **CCPP physics** (@grantfirl, @rhaesung, @dustinswales): fixes E, F and G in the surface loop control, composites
  and cold-start initialisation (the second-pass flag for coastal cells; `weasd_lnd` with `frac_grid`; Noah-MP's snow
  layers from `weasdl`); a water-budget regression check; documentation of
  `prate_ave` vs `prateb_ave`; restoring the SAMF condensate `cnvtrans` diagnostic, which is zero on `develop`
  (section 2).
- **FV3 / GFDL** (@lharris4, @linjiongzhou): longer term, a dry-mass tracer-transport option for long chemistry and
  greenhouse-gas runs. CAM-SE's move to a dry-mass coordinate is the precedent (Lauritzen et al. 2018). No such option
  exists in the UFS driver today.

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

Thirteen diffs in `patches/`, against `ufs-community/ccpp-physics` `ufs/dev` @242a2fc, the commit pinned by
`ufs-weather-model` `develop` @112b1d46 (2026-10-08). 01–05 touch separate code and apply in any order; 06–13 were
generated on top of 01–05 and apply in order (06 and 07 touch the Thompson files that 02, 03 and 05 change).

| Diff | Fix | File |
|---|---|---|
| `01_samf_cloud_base_double_count.diff` | A | `samfdeepcnv.f`, `samfshalcnv.f` (added fixed-form lines fit within column 72) |
| `02_thompson_mass_basis.diff` | B | `mp_thompson.F90` |
| `03_thompson_settling_and_graupel_closure.diff` | C1, C2 | `module_mp_thompson.F90` |
| `04_noahmp_water_flux.diff` | D | `noahmpdrv.F90` |
| `05_thompson_sedimentation_density.diff` | C3 | `module_mp_thompson.F90` |
| `06_thompson_layer_depth_from_host_mass.diff` | M4 | `mp_thompson.F90`, `mp_thompson.meta` |
| `07_thompson_clipped_condensate_to_vapour.diff` | M1 | `module_mp_thompson.F90` |
| `08_noahmp_single_step_per_timestep.diff` | E | `noahmpdrv.F90`, `noahmpdrv.meta` |
| `09_frac_grid_land_snow_persistent.diff` | F | `GFS_surface_composites_pre.F90` |
| `10_noahmp_snow_init_from_land_snow.diff` | G | `GFS_phys_time_vary.fv3.F90`, `GFS_phys_time_vary.fv3.meta` |
| `11_noahmp_thin_snow_to_soil.diff` | H | `module_sf_noahmplsm.F90` |
| `12_noahmp_canopy_truncation_to_ground.diff` | I | `module_sf_noahmplsm.F90` |
| `13_thompson_count_all_surface_sedimentation.diff` | M2 | `module_mp_thompson.F90` |

Verified on MSU Hercules (13 October 2026), all builds with `-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1 -D32BIT=ON` (one meter build also in 64-bit)
(Intel):
- the unmodified `develop` clone passes `control_p8_ugwpv1` (`develop-20260921` baseline) and `control_c384`;
- all five diffs apply cleanly, alone and together, and every combination built (01–03; 01–03 + 05; all five)
  compiles with 0 errors;
- every combination runs the C96 case to 24 h. Unmodified `develop` and `develop` + 01–05 also run it to 240 h, and
  unmodified `develop` and `develop` + 01–03 + 05 run the C384 case to 24 h (9 nodes, 15 min each);
- 06–13 apply in order on top of 01–05; `develop` + 01–07, + 01–08, + 01–09, + 01–10, + 01–11, + 01–12 and + 01–13
  build and run the C96 case to 24 h.

Scripts in `scripts/` (Python 3 with numpy and netCDF4; each takes run directories as arguments):

| Script | What it does |
|---|---|
| `water_budget_by_scheme.py` | per-scheme and total budget per window (section 2); any cubed-sphere resolution; window length and end from `WB_WINDOW` and `WB_END` (hours, default 6 and 24); `WB_BUCKET` (= `fhzero`) and `WB_THICK` for the thickness-interval test, `WB_UNWEIGHTED` to count columns as the meters do (pitfall 5) |
| `water_budget_native.py` | total budget only, without `dtend` diagnostics (C96) |
| `column_mapping_check.py` | per-column boundary-layer closure, which confirms the 3-D and 2-D diagnostics share columns (section 1) |
| `land_atm_water_closure.py` | land–atmosphere gap and land storage budget (section 6; C96) |
| `noahmp_qfx_excess.py` | size and composition of D from one run, hvap vs sublimation (C96) |
| `water_jump_series.py` | budget at every output time in the first hours (pitfall 2) |
| `apply_water_patches.py`, `apply_thompson_c_patches.py`, `apply_thompson_c34_patches.py`, `apply_noahmp_d_patch.py` | apply A–D to the v1 snapshot, whose line numbers differ from `ufs/dev` |
| `mk_upstream_c3_diff.py` | writes fix C3 into a `ufs/dev` `module_mp_thompson.F90` (to generate diff 05) |
| `apply_thompson_m_patches.py` | apply M4 (`z`) or M4 + M1 (`zc`) to the v1 snapshot (section 5) |
| `apply_thompson_m2_patch.py` | apply M2 (v1 snapshot or `ufs/dev`; generates diff 13) |
| `instrument_wb_ep.py`, `ep_meter_budget.py` | diagnostic builds only: closes the physics' column water against the evaporation the boundary layer adds, the precipitation reported and the `h2ophys` source, every step and column, in double precision; also what the boundary layer adds vs books (section 5, M2) |
| `instrument_wb.py` | diagnostic builds only: Thompson stage-by-stage water accounting and SAMF negative-borrowing counters, printed at finalize (section 5; section 3, question 1) |
| `instrument_wb_phys.py` | diagnostic builds only: whole-physics water meter in `GFS_physics_post` (adds `qgrs`, `gq0`, `prsi`, `cell_area`, `kdt` and the water tracer indices to its metadata), printed every step (section 2) |
| `phys_meter_budget.py` | exact R_phys and R_dyn per window from that meter and the snapshots (section 2) |
| `instrument_wb_dyn.py` | diagnostic builds only: water meters around `fv_dynamics` (and `neg_adj3` within it), `fv_subgrid_z`, the physics→dynamics update (and `fill_gfs`) and `fv_update_phys`, printed every step (section 2) |
| `instrument_wb_land.py`, `land_meter_budget.py` | diagnostic builds only: land↔atmosphere evaporation and precipitation hand-off meters, Noah-MP's `errwat`, and the boundary layer's booked vs added surface water (section 6) |
| `dyn_meter_budget.py` | splits R_dyn into those pieces per window and per step, and checks they add up to the snapshot change (section 2) |
| `mk_upstream_m_diffs.py` | writes M4 (`m4`) or M1 (`m1`) into a `ufs/dev` tree (to generate diffs 06, 07) |
| `apply_noahmp_e_patch.py`, `apply_composites_f_patch.py` | apply E or F (v1 snapshot or `ufs/dev`; generate diffs 08, 09) |
| `instrument_wb_noahmp.py`, `noahmp_balance.py` | diagnostic builds only: Noah-MP storage terms in and out of every call, fluxes and `errwat`, by soil and glacier points; within-call and between-call balance per window (section 7) |
| `instrument_wb_iter2.py`, `iter2_budget.py` | diagnostic builds only: what the second surface pass adds to Noah-MP land (section 7, E) |
| `apply_noahmp_g_patch.py`, `apply_noahmp_h_patch.py`, `apply_noahmp_i_patch.py` | apply G, H or I (v1 snapshot or `ufs/dev`; generate diffs 10–12) |
| `instrument_wb_noahmpx.py` | diagnostic builds only: Noah-MP's `errwat` by surface state and size, with every storage term for the largest columns (section 7) |
| `instrument_wb_noahmpf.py` | diagnostic builds only: splits that residual into before, inside and after Noah-MP's `water()` (section 7, H) |
| `instrument_wb_noahmph.py` | diagnostic builds only, after H: count and amount moved at each of H's three sites (section 7, H) |
| `instrument_wb_noahmpc.py` | diagnostic builds only: the canopy water deleted in `canwater`, by snow state, next to `errwat` (section 7, I) |
| `instrument_wb_driver.py` | diagnostic builds only: host-frame water meter around the whole Thompson driver call, printed next to the column meter (section 5; needs M4) |

The meters accumulate in module variables and assume one OpenMP thread (all runs here); a threaded regression check
would need reductions.

## Appendix B — location of each defect in current upstream

| Defect | `ufs/dev` @242a2fc | NCAR `main` @f601ce9 |
|---|---|---|
| A, deep | `samfdeepcnv.f` L1622, L2551–2561 (water), L2635–2645 (tracers) | identical logic, shifted lines |
| A, shallow | `samfshalcnv.f` L1979–2005, L2040–2050 | identical |
| B | `mp_thompson.F90` L690–704, L944–957; FV3 `dev/emc` `atmosphere.F90` L1659–1677 | same |
| C1, C2 | `module_mp_thompson.F90` L3029, 3140–3198, 4044–4057; clips L4241–4300 | same |
| C3 | `module_mp_thompson.F90` L3386, 3660, 3743 | same |
| M2 | `module_mp_thompson.F90` L3995, 4090, 4120, 4151 | same |
| D | `noahmpdrv.F90` L1526; `module_sf_noahmplsm.F90` L188–189 | same; NCAR/ccpp-physics#582 open |
| E | `GFS_surface_loop_control_part2.F90` L50; `noahmpdrv.F90` L953 | not checked |
| F | `GFS_surface_composites_pre.F90` L274; `GFS_surface_composites_post.F90` L105 | not checked |
| G | `GFS_phys_time_vary.fv3.F90` Noah-MP initialisation: L455, L469 (`sneqvoxy`), L525–533 (snow depth, glacier 600 mm), L581 (`snicexy`) | not checked |
| H | `module_sf_noahmplsm.F90` L947 (`noahmp_sflx`), L2049 (`energy`), L8180 (`snowh2o`) | same file, byte-identical |
| I | `module_sf_noahmplsm.F90` L7346, L7355 (`canwater`) | same file, byte-identical |

`ufs/dev` and NCAR `main` are byte-identical for every file of A–D, and `ufs/dev` HEAD (c7dc705, 13 October 2026)
matches the UFSATM pin for all of them.

## Appendix C — the same code in other upstreams and hosts

A read-only survey (13 October 2026) of every other copy we could find of the code behind A–D.

| | UFS `ufs/dev` = NCAR `main` | TEMPO | WRF | MPAS |
|---|---|---|---|---|
| **A** SAMF cloud base | present since NCAR/ccpp-physics#754 (commit ed3768b, 2021) | n/a | n/a | n/a |
| **B** mass basis | present (`mp_thompson.F90`) | present (CCPP driver `mp_tempo.F90` L437–455, L532–549) | **cannot occur**: dry mixing ratios passed (`module_microphysics_driver.F` L1177ff) | **cannot occur** (`mpas_atmphys_interface.F` L660–662) |
| **C1** fog settling | present | partial: counted only in the freezing-rain diagnostic, not in precipitation | present (L3824–3836) | present (L3443–3455) |
| **C2** graupel re-closure | present | present (`check_over_depletion` L1649–1673) | present (L2940–2950) | present (L2656–2666) |
| **C3** density recomputed before sedimentation | 3 sites | 4 sites | 3 sites | 3 sites |
| ρ·dz vs host layer mass | `dz` from `phii`, before convection | same driver pattern | geometric `dz8w`; host dry density not passed | fixed `zgrid`; host dry density not passed |
| clips | zeroed, not returned to vapour | zeroed | zeroed | zeroed |
| **D** Noah-MP water flux | LH ÷ `con_hvap` | — | **mass flux** (`QFX` = canopy + ground evaporation + transpiration) | **mass flux** |
| **H** thin snow deleted | at `sneqv <= 1e-3` mm, 3 sites | — | NCAR/noahmp v5 (WRF, MPAS): at `SnowWaterEquiv <= 1e-6` mm (`SnowWaterMainMod.F90` L176, `SnowpackHydrologyMod.F90` L96) | same as WRF |
| **I** canopy water deleted | at `canliq`, `canice` <= 1e-6 mm | — | NCAR/noahmp v5: identical (`CanopyHydrologyMod.F90` L92, L101) | same as WRF |

- **C1–C3 belong to the scheme**, so their fixes apply to every host. No copy has a water fixer.
- **B belongs to the CCPP interface.** FV3 hands physics mass per (dry air + vapour), and the CCPP drivers'
  conversions do not round-trip on that basis. TEMPO's CCPP driver repeats Thompson's conversion, so B survives a
  switch to TEMPO unless its driver is fixed too.
- **D belongs to the CCPP port of Noah-MP.**
    - Every NCAR/noahmp driver (WRF, HRLDAS, MPAS, LIS, ERF; `drivers/*/WaterVarOutTransferMod.F90` L59–64) passes the
      water mass flux, as diff 04 does.
    - The latent-heat form is in the ccpp-physics copy, which UFS compiles for the in-atmosphere land model, and in
      NOAA-EMC/noahmp's CCPP driver and NUOPC land component (built only for apps with a separate land component).
    - NOAA-EMC/noahmp's CCPP driver also still sets glacier canopy evaporation and transpiration to `undefined`
      (9.99 × 10²⁰), so diff 04 there would need them zeroed, as `ufs/dev` already does.
- **FV3 coupling.** `dev/emc` (`driver/UFS`) and `main` (`driver/SHiELD`) both pass the dry + vapour basis and
  rebuild `delp` as old dry mass + Σ(physics thickness × returned q). SHiELD's in-line GFDL microphysics instead
  converts on a dry basis that includes all condensate, and holds dry mass exactly. `main` has no UFS driver. The only
  fixers reachable from UFS act at initialisation or inside the IAU window.
- **SAMF elsewhere.** GFDL's in-line `sa_sas`/`sa_aamf` (SHiELD) have no TVD and no cloud-base subtraction, so A as such
  is absent there. The `hwrf_samfdeep` switch does not bypass the moisture TVD.
- **The zeroed `cnvtrans` diagnostic** (section 2) is the same on both ccpp-physics branches.
- **MPAS only:** condensate above `config_microphysics_top` (default 45 km, where there is essentially none) is zeroed
  each step while vapour is left alone (`mpas_atmphys_interface.F` L936–946, L999–1003; added October 2025).

Commits read: ufs-community/ccpp-physics `ufs/dev` c7dc705; NCAR/ccpp-physics `main` f601ce9; NCAR/TEMPO `main`
c62699f (ccpp-physics pins `tempo_v3` at 2856696, same structure); wrf-model/WRF `develop` 1086c86; MPAS-Dev/MPAS-Model
`develop` aa6d8cd; NCAR/noahmp `master` 1a6225b; NOAA-EMC/noahmp `develop` 2c7b3bc (the ufs-weather-model
`NOAHMP-interface` pin); NOAA-GFDL/GFDL_atmos_cubed_sphere `dev/emc` 71ff473 and `main` 8b94b9f. Not checked: the
CCPP single-column model, HAFS forks, MPAS's `physics_mmm` tree, the C3 convection scheme.


---

> **History.** Full text of `water_closure_proposal.md` as of 15 October 2026, before it was cut by 20 %; kept verbatim.

# Proposal: closing the total-water budget in UFS physics

*Draft for the CCPP physics maintainers, the SAMF, Thompson and Noah-MP scheme owners, and the FV3 `dev/emc`
maintainers. Ash Pera (NOAA GML / CIRES) with Lori Bruhwiler, 15 October 2026. Not yet posted. The investigation in the
order it happened is in `water_closure_proposal.history.md`.*

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
it sends traces of snow to Noah-MP, where any canopy ice hides the canopy's liquid (section 7, Appendix E.2).

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
depending on its vertical profile, persistently; with SA1 the physics conserves tracer mass to 10⁻¹⁸. The dynamical core
changed it by at most 10⁻⁴ %/yr.

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
L2040–2050): its flux-divergence loop starts above `kb`, so the cloud-base flux must equal what the updraft takes.

**The fix** (diff 01). In both schemes the cloud-base face of the TVD flux carries what the updraft takes,
`eta·qo(kb)` (deep also `edto·etad·qo(jmin)` at `jmin`; tracers `ctro`), and deep's double-count subtraction uses the
same values. Layer `kb` is then unchanged and `kb+1` loses what the updraft took, as in SAMF's moist static energy
budget, which has no updraft term at or below `kb`. Changing only deep's subtraction would alter q at `kb` but not h,
i.e. heat layer `kb`: by 0.07 K per convecting column-step on average (up to 1.35 K) in our runs; in this form the
direct change at `kb` is zero to round-off per unit mass flux (it can still shift by about 10⁻³ K through the closure
or rain evaporation). An untested alternative is to start the updraft from the limited value
(`qcko(kb) = tem1`).

**Measured.**
- Single column, unmodified Fortran, dt = 720 s: +7 to 8 × 10⁻⁴ kg/m² per step on smooth profiles (0.05 % of rain), 4 %
  of rain (deep) and 23 % (shallow) on two jagged humidity profiles; all seven cases created water. Fixed: every case
  closes to ≤ 2 × 10⁻¹⁴ kg/m² (double precision; about 10⁻⁶ kg/m² in the single-precision SAMF build). An independent
  harness (a second session, about 12,000 synthetic L127 soundings, deep and shallow) found the unfixed residual has a
  median of 3.5–8.7 % of rain and a maximum of 33 %, and the fix closes every case to ≤ 3 × 10⁻¹⁵ kg/m², tracers to
  ≤ 6 × 10⁻¹⁷, with column moist static energy closed and negative-value borrowing unchanged.
- Full model: the convection residual falls from +0.78 % to 0.00 % of convective rain at C96 (v1), and at C384 from
  +0.97 % to within the per-scheme split's resolution (`develop`, where convection is computed by difference; section 6,
  pitfall 5).
- Tracers: about 5 × 10⁻⁷ relative column change per convective step on a smooth profile, none on a linear one.
- Negative-value borrowing (Han et al. 2022, Eqs. 10–11) is needed equally often with and without the fix: 104 of
  330 557 deep-convecting column-steps without it, 97 of 327 916 with it, over 24 h at C96.

**Questions for the SAMF owners.**
1. Was `tem1` here intentional, for example to keep the cloud-base layer positive?
2. Are there other places where a TVD-limited flux meets an exact parcel source? Our single-column budget closes to
   round-off after this fix, which suggests not, at least for our test profiles.
3. Deep and shallow now use the same form. Do you prefer it to starting the updraft from the limited value?

## 2. Thompson microphysics: fixes TH1–TH7 (and TH8, held)

Line numbers are `ufs/dev`. Measured effects are on the v1 snapshot at C96, as percentages of grid-scale
precipitation (P_grid), each relative to the build before it.

**TH1, mass basis** (diff 02, `mp_thompson.F90`).
- FV3 passes physics its tracers per (dry air + vapour), and rebuilds each species' mass afterwards as the same
  pre-physics thickness × the returned value (`atmosphere.F90`, `dev/emc`, L1659–1677).
- `mp_thompson.F90` converts to mixing ratios with `/(1 − q_v)` (L690–704) but back with `/(1 + r_v,new)` (L944–957),
  i.e. per (dry air + *new* vapour). Every species comes back scaled by (m_d + m_v,old)/(m_d + m_v,new): net
  condensation creates water, net evaporation removes it.
- **Fix:** convert back with `×(1 − spechum)`, using the scheme's unchanged input `spechum` both ways; the host's mass
  rebuild is then exact. GFDL microphysics already does the equivalent (Zhou, Harris and Chen 2022, §2.4).
- **Measured:** −0.67 % → −0.30 % of P_grid.
- TEMPO's CCPP driver (`mp_tempo.F90` L437–455, L532–549) has the same conversion; WRF and MPAS pass dry mixing
  ratios, so TH1 cannot occur there.

**TH2, fog settling** (diff 03, L4044–4057).
- The cloud-water sedimentation loop moves `sed_c(kts)` out of the lowest layer but never adds it to a precipitation
  total. The water really leaves the atmosphere (fog and drizzle deposition).
- The loop also takes one full time step, while rain, ice, snow and graupel are substepped so that no layer's outflow
  exceeds its content (L3808, 3873, 3922, 3950). Where `vtck·DT > dz` (the lowest L127 layer is about 20 m thick,
  DT = 720 s; almost all over ocean, where droplets are larger), a layer loses more cloud than it holds. Upstream then
  zeroes the negative, creating water.
- **Fix:** count `sed_c(kts)` in `pptrain`, and substep cloud sedimentation with the same rule as the other species.
  With one substep the arithmetic is unchanged: a build forced to one substep is bit-identical to the unfixed one.
- **Measured:** −0.30 % → −0.15 % of P_grid.

**TH3, graupel after the rate limiters** (diff 03).
- Rain collecting snow below 0 °C conserves water by construction, `prr_rcs + prs_rcs + prg_rcs = 0`, until the clips
  at L2796–2798 and the limiters (L3140–3176) rescale `prr_rcs` and `prs_rcs` but not `prg_rcs`. Likewise
  `prg_rci = pri_rci + prr_rci` is set at L3029, before the limiters rescale its terms, and not recomputed in the
  re-closure block (L3189–3198).
- **Fix:** recompute both graupel gains after the limiters, `prg_rcs = −(prr_rcs + prs_rcs)` below 0 °C, after capping
  the snow gain from this collection at the rain lost to it, so the graupel gain cannot go negative where the rain
  limiter has reduced the rain loss.
- **Measured:** a source of 0.76 % of P_grid in the first 6 h of a cold start (0.0019 kg/m²), about 0.03 % after; over
  24 h the column meter and the host budget agree on its effect (−0.22 % and −0.21 %). We have not tested whether
  analysis increments in a cycled system cause similar bursts.

**Over ten days** the single-step cloud sedimentation also created water: when the daily surface cycling (`fhcyc` =
24 h, with NSST) resets sea-ice skin temperature by up to 27 K, the sublimation pulse into a thin, cold lowest layer
over ice-covered Hudson and Ungava Bays drove cloud sedimentation to Courant numbers near 2, and the vapour floor then
created up to 1.2 × 10⁻² kg/m² in a column (+1.4 × 10⁻⁶ kg/m² globally over 10 days on the v1 snapshot). With the
substepping the 10-day physics residual is −8.8 × 10⁻¹⁴ kg/m² and no column exceeds 2.4 × 10⁻¹³.

**Negative hydrometeors after TH2 and TH3.** Without the substepping and the cap, Thompson left 2.2 × 10⁻⁵ kg/m² of
negative hydrometeors at the end of the step over 24 h (83 % cloud water, 17 % graupel; most of it in the first two
steps, from lowest-layer cloud water of up to 1.1 × 10⁻³ kg/kg in the initial state), which TH6 repays from vapour.
With them, 1.3 × 10⁻⁸ kg/m², and the most negative layer goes from −4.1 × 10⁻³ to −1.5 × 10⁻¹⁰ kg/kg (upstream
`develop` + all diffs, then including TH8). The physics' water still closes to rounding, and the 24-h precipitation
change is within the spread of a noise-only control.

**TH4, sedimentation density** (diff 04). Thompson converts hydrometeors to mass densities with its entry density
`rho = 0.622·p/(R·T·(qv+0.622))`, which times dz is the host's dry-air layer mass. But it recomputes `rho` from the
updated temperature three times before sedimentation (L3386, L3660, L3743), and latent heating lowers it by about
ΔT/T, so each kilogram that falls out in Thompson's frame removes about 1 + ΔT/T kilograms of host water. Fix: keep
the entry density for all mass conversions, and use the updated density only for fall speeds and viscosity at the
first recompute. **Measured:** −0.18 % → −0.07 %.

**TH5, layer depth from the host's layer mass** (diff 05, `mp_thompson.F90` + `.meta`). The driver takes `dz` from
`phii` (L716), computed before deep and shallow convection heat the column, so Thompson's ρ·dz drifts from the host's
layer mass. Fix: pass `prsi` (already in UFSATM and SCM metadata) and set `dz = Δp·(1 − q_v)/(g·ρ)`, with ρ Thompson's
own entry density. When Thompson takes several inner steps (`dt_inner` < `dt_atmos`, the regression suite's default),
`mp_gt_driver` loops over them with the depth fixed while the density follows the updated temperature, so the driver
passes the host's dry-air layer mass and `mp_gt_driver` sets the depth from it at every inner step. **Measured:**
removes 0.014 % of P_grid; with five inner steps a depth fixed for the whole step lost 7.1 × 10⁻⁴ kg/m² over 24 h
(−0.026 % of precipitation), and with the per-step depth the physics closes to 1.6 × 10⁻¹⁵. On the v1 snapshot ρ must use Thompson's gas constants
(287.04, 0.622): with the host's `con_rd` and `con_eps`, ρ·dz is 3.5 × 10⁻⁵ too large. Upstream Thompson takes its
constants from the host, so the driver's own `rho` is consistent there.

**TH6, clipped condensate and the vapour floor** (diff 06). Hydrometeors that end the step negative or below `R1` are
deleted (L4241–4300), and vapour is floored at 10⁻¹⁰ (L4310), which creates whatever is missing. Fix: exchange the
clipped hydrometeors with vapour, with the matching latent heat. Vapour left below the floor is refilled first from the
same layer's condensate (with its latent heat, number concentrations scaled with mass), then from the column's other
vapour, mass-weighted; only a column with no vapour to spare is still floored. **Measured:** removes a 0.002 % source.
In a harness that compiles the real driver (a second session's red team), five columns that the floor and the driver's
neighbour-average fixer had given +0.77 to +1.52 kg/m² close to ≤ 4 × 10⁻¹⁵ kg/m² with the refill and TH7's last
part, and the fixer no longer fires anywhere in its attack set (from 46 times).

**TH7, water at the `R1` threshold** (diff 07). Thompson treats hydrometeors at or below `R1` = 10⁻¹² as absent, and
deletes them in three places:
- *on entry* (L2267, 2294, 2323, 2334, 2343): condensate with q ≤ `R1` is set to zero and returned to the host that
  way;
- *in semi-Lagrangian sedimentation* (`semi_lagrange_sedim`, used for rain and graupel with `sedi_semi`; L6271, 6455):
  inputs ≤ `R1`, including the `R1` placeholders for absent species, are left out of the transport and the output is
  floored at `R1`, so rain falling into an empty layer is booked `R1` short and a layer that empties is left at `R1`
  (8.6 × 10⁻⁶ kg/m² per 6 h each way, net −6 × 10⁻⁹);
- *after the source/sink terms* (L3322–3339): where the rain left is ≤ `R1`, `qrten = −qr1d/dt` discards the rain
  those terms made.

Fix: on entry and for the leftover rain, the water goes to vapour with its latent heat, as in TH6;
`semi_lagrange_sedim` returns the mass it did not transport unchanged and no longer floors its output (the rain-number
floor `R2` moves to the caller), and layers that Thompson holds at the `R1` placeholder before rain and graupel
sedimentation start from their actual content, so the placeholder is not transported as mass (without that,
1.2 × 10⁻⁸ kg/m² per day of negative rain; with it, 10⁻¹⁷). Later uses of rain and graupel density are already guarded by `> R1`. A column whose entry exchange leaves vapour
below the floor no longer takes Thompson's no-microphysics early return, so the refill (TH6) handles it instead of the
driver's neighbour-average fixer; other columns are unchanged. **Measured**
upstream, where Thompson is double precision (`develop` with the fixes before it, TH8 included, 24 h): the physics' residual falls from −6.0 × 10⁻⁸ to
−4.0 × 10⁻¹⁵ kg/m² (entry −3.5 × 10⁻⁸, sedimentation −2.5 × 10⁻⁸, leftover rain −5 × 10⁻¹⁰), and the largest
single-column residual from 1.6 × 10⁻⁸ to 2 × 10⁻¹³. The sedimentation change creates no new negative hydrometeors
(same amount at the end of the step with and without it). On the v1 snapshot, where Thompson computes in single precision, the loss was the same size, and the fix closes it the same
way: −6.2 × 10⁻⁸ → −4.3 × 10⁻¹⁵ kg/m² over 24 h, largest column 1.9 × 10⁻⁸ → 9 × 10⁻¹³ (all other fixes applied).

**TH8, surface precipitation thresholds** (held: `held/TH8_*.diff`). The sedimentation flux out of the lowest layer always leaves the
column, but it is added to the surface precipitation only when the water left in that layer exceeds `R1·rr_min`
(L3995, 4090, 4120, 4151: rain, ice, snow, graupel). Below the threshold the water is deleted. Fix: count all of it.
**Measured** with the double-precision physics meter (section 6): the physics' residual falls from −1.46 × 10⁻⁷ to
−1.6 × 10⁻⁸ kg/m² per 6 h, and the largest single-column residual from 1.3 × 10⁻⁴ to 1.7 × 10⁻⁸ kg/m². An earlier test
had found these thresholds harmless, but it could resolve only 10⁻⁵ kg/m². **Held** (section 7).

**Other hosts.** TH2–TH4 and TH6 are in the scheme itself, so they are in the WRF and MPAS copies of Thompson and in TEMPO
(Appendix C). Becker et al. (2022) found IFS clipping errors grow with resolution (4.6–10.7 % of precipitation at
9–4 km); at C384 the fixed total is still −0.001 %.

## 3. Noah-MP and its coupling: fixes NM1–NM11

We metered Noah-MP's own water every step (Appendix A): canopy, snow, soil and aquifer water as the driver receives and
returns them, with precipitation, evapotranspiration and runoff. Noah-MP's `errwat` check (computed, never acted on)
was +3.7 kg/m² per 6 h globally, and storage changed between calls, where nothing should touch it. NM1–NM6 explain all of
it. NM1 affects the atmosphere; NM2–NM6 affect only the land, which an atmosphere budget cannot see.

**NM1, evaporation handed over as latent heat** (diff 08, `noahmpdrv.F90` L1526).
- The driver gives the atmosphere `evap = latent_heat/ρ/con_hvap`, with the host's 2.5 × 10⁶ J/kg. Noah-MP removed the
  water with its own latent heats (`module_sf_noahmplsm.F90` L188–189: `hvap = 2.5104e6`, `hsub = 2.844e6` whenever
  ground or canopy is frozen). The atmosphere receives 0.4 % more water than unfrozen land loses, 14 % more over frozen
  surfaces.
- **Fix:** pass the water flux Noah-MP computes, `(ecan + etran + edir)/ρ`, and keep latent heat for the energy
  coupling. This is what NCAR's own Noah-MP drivers (WRF, HRLDAS, MPAS, LIS) already do. It changes the physics: the
  water flux over snow and frozen ground falls by up to 12 %. The latent-heat constants then still differ on the
  energy side; fix NM8 removes that.
- **Measured** with in-model meters on both sides: the atmosphere received +4.5 to +6.9 × 10⁻⁴ kg/m² per 6 h more than
  the land lost (+0.07 to +0.10 % of global precipitation); with the fix, 0 to machine precision apart from FV1.
- `ufs/dev` already zeroes glacier canopy evaporation and transpiration (L1186–1187, since ccpp-physics 3fe1f187,
  May 2025). Older trees, including the v1 snapshot, set them to `undefined` (9.99 × 10²⁰), so NM1 there needs the
  zeroing too, or every glacier point hands the atmosphere about 2 × 10²¹ mm of evaporation.
- NM1 changes the host's latent-heat output, which is derived from `evap` (ρ·`con_hvap`·`evap`): over sublimating
  surfaces it now follows the water and is up to 12 % lower. Noah-MP's own latent heat flux is unchanged.

**NM2, coastal land stepped twice** (diff 09). `GFS_surface_loop_control_part2` (L50) re-flags a point for the second
surface pass when `(dry .and. lsm /= lsm_noahmp) .or. (wet .and. nstf_name1 > 0)`. With `frac_grid` a coastal cell is
both dry and wet, so the second clause re-flags it, and `noahmpdrv` (L953) tests only `flag_iter .and. dry`. Noah-MP
then steps the land again from its already-updated state; unlike Noah and RUC it does not save and restore its state.
**Fix:** pass the CCPP loop counter (an optional trailing argument) and compute land on the first pass only. NOAA-EMC/noahmp's
land component calls this routine against its own copy of the driver's interface, so the same declaration goes into
that copy (diff 09b), or the land component's call leaves the counter undefined. **Measured:** 24–27 % of the land
(low-wind coastal cells) was stepped twice every step, receiving each step's rain twice:

| Window | Precipitation added again | Evapotranspiration debited again | Land water created | / global P |
|---|---|---|---|---|
| 6–12 h | 0.051 kg/m² | 0.026 | +0.022 | +3.3 % |
| 12–18 h | 0.049 | 0.012 | +0.036 | +5.2 % |
| 18–24 h | 0.054 | 0.015 | +0.038 | +5.3 % |

Any configuration with `frac_grid` and NSST is affected, including this GFS v17 suite.

**NM3, coastal land snow overwritten** (diff 10). `GFS_surface_composites_post` (L105) sets the cell-mean snow
`weasd = txl·weasd_lnd + txi·weasd_ice`; next step `GFS_surface_composites_pre` (L274) sets `weasd_lnd = weasd` for
every land model except RUC. With `frac_grid`, `weasd_lnd` is the persistent land value (`Sfcprop%weasdl`), so coastal
snow is diluted every step. Noah-MP rebuilds layered snow from its layers (that rebuild was the +3.7 kg/m² `errwat`);
thin snow is lost, about 0.005 mm per land column per 6 h. **Fix:** with `frac_grid`, keep `weasd_lnd`, as RUC does.

**NM4, cold-start snow layers from the wrong snow** (diff 11). At a cold start Noah-MP is given the land snow
`weasdl = weasd/(landfrac + fice·(1−landfrac))`, but `GFS_phys_time_vary_init` builds its snow layers from the
cell-mean `weasd` and `snowd` (L455, L469, L525–533, L581). On its first step Noah-MP rebuilds its total from the
layers. **Measured:** 0.29 kg/m² of land snow lost as a global mean (about 1 kg/m² per unit land area, on snowy coasts
and glacier margins). **Fix:** use `weasdl` and `snodl`; the first-step loss is then 0. Where the initial state has
snow depth but no snow water, no layers are built: dividing by a small land fraction can otherwise turn a trace of
cell-mean depth into massless layers (0.058 mm → 15 cm at a land fraction of 3.9 × 10⁻⁴ in the coupled regression
cases), whose zero heat capacity is a divide by zero on the first step.

**NM5, thin snow deleted** (diff 12). Noah-MP zeroes snow without layers when `snowh <= 1e-6` m or `sneqv <= 1e-3` mm,
in `noahmp_sflx` (L947), `energy` (L2049) and `snowh2o` (L8180), and the water goes nowhere. Ice dripping off a frosted
canopy reaches snow-free ground as about 10⁻⁴ mm per step and was deleted every step. **Measured:** 15.60 mm moved in
124,000 events in `snowh2o`, 0.02 mm in `energy`: the whole of the −15.6 mm `errwat` summed over 1.77 million
column-steps in 24 h. **Fix:** put the truncated snow in the top soil layer as ice, as `snowh2o` already does with
excess sublimation.

**NM6, canopy water deleted** (diff 13). `canwater` zeroes canopy liquid or ice at or below 10⁻⁶ mm (L7346, L7355), and
the water goes nowhere; light interception often leaves exactly that much, so it vanished on about 5 % of land
column-steps. **Measured:** the deleted water (0.0141 mm) equals the remaining `errwat` (−0.0141 mm) in every snow state
to 1 part in 10⁴. **Fix:** `canwater` returns the truncated liquid and ice, and `water()` adds them to the rain and
snowfall reaching the ground (the ice at fresh-snow density). Nothing changes phase, so no energy is created.
Evaporating the water through `ecan` instead would also close the water but leave its latent heat unpaid (up to
3.5 × 10⁻³ W/m² at a point for one step).

**NM7, condensation without water** (diff 14). The canopy energy solve (`vege_flux`) can return a negative transpiration
heat flux, `fctr < 0`: vapour condensing through the stomatal pathway, on 13 % of land column-steps. `canwater` takes
`etran = max(fctr/hvap, 0)` (L7328, frozen canopy L7334), so the latent heat of that condensation warms the canopy but
no water condenses. **Measured** with the same latent-energy meter, after NM8: Noah-MP's latent energy exceeded the latent
energy of its water by 0.024 W/m² per land column (about 0.007 W/m² as a global mean), and that term equalled
Σ min(`fctr`, 0) exactly. **Fix:** add `|min(fctr/hvap, 0)|` to the canopy dew `qdewc` (`fctr/hsub` to the frost
`qfroc` on a frozen canopy). The energy solve is unchanged; only the water follows it, through Noah-MP's existing dew
pathway, about 8 × 10⁻⁴ mm/day over land. The land's total water–energy mismatch falls from −0.0228 to +0.0013 W/m²; the
remainder is the canopy evaporation cap (section 7). Water closure is unchanged. NCAR's Noah-MP v5 has the same clip
(`CanopyHydrologyMod.F90` L75, L81). CTSM avoids the case inside its energy solve instead: with potential evaporation
≤ 0 it sets transpiration to zero and puts all condensation on the leaf (`CanopyFluxesMod.F90`, `master` be1aff2,
L1232–1246). That changes the energy solution, so we did not take it.

**NM8, latent heats from the host** (diff 15; cf. NCAR/ccpp-physics#582). Noah-MP charges the land its own latent heats
for the water it evaporates or sublimates (`hvap = 2.5104e6`, `hsub = 2.844e6` J/kg, `module_sf_noahmplsm.F90`
L188–190 and the glacier copies), but after NM1 that water enters the atmosphere carrying the host's: `con_hvap` =
2.5 × 10⁶ from liquid, `con_hvap + con_hfus` = 2.83358 × 10⁶ from ice. **Measured** with a meter of the land's latent
energy against the latent energy of the water it hands over: the land paid +0.131 W/m² per land column more than its
vapour carries (0.41 % of the 31.8 W/m² land latent heat flux, one-signed; about 0.04 W/m² as a global mean).
**Fix:** `hvap`, `hsub` and `hfus` become module variables, set at the start of `noahmpdrv_run` from the `con_hvap`
and `con_hfus` it already receives, so no interface changes. (NOAA-EMC/noahmp's land component calls the driver's
routines positionally, and in atmosphere–land builds those calls reach this driver, so new arguments would shift.) The gap is then exactly 0, and water is unchanged. This
is #582's approach for the three latent heats only; Noah-MP's other constants (gravity, specific heats) are untouched.

**With NM1–NM6** (v1 snapshot, metered):

| | Before NM2–NM6 | NM2–NM4 | NM2–NM5 | NM2–NM6 |
|---|---|---|---|---|
| Noah-MP `errwat`, global | +3.7 kg/m² per 6 h | −6 × 10⁻⁵ kg/m² per 6 h | | |
| `errwat` summed over 1.77 M soil column-steps, 24 h | | −15.6 mm | −0.014 mm | −1.2 × 10⁻⁸ mm (rounding) |
| column-steps with \|`errwat`\| ≥ 10⁻⁷ mm | | | 326 | 0 |
| storage change between calls | nonzero | 0.00000 | 0.00000 | 0.00000 |

The precipitation hand-off is exact: Noah-MP's `prcp` equals the host's `tprcp` to 10⁻¹⁶ (one step late, which nets to
zero). On glacier points `errwat` is zero throughout, but it cannot see the glacier code's own assignments (NM9).

**NM9, glacier snow set by assignment** (diff 16, `module_sf_noahmp_glacier.F90`, `noahmpdrv.F90`). UFS runs glaciers
with `iopt_gla = 2`: the ice beneath the snow is an unlimited, untracked reservoir, and glacier flow (`snoflow`, added
to the subsurface runoff `runsub`) is how the module moves water between the snow and that ice. Four places set the
snow instead:
- `snowwater_glacier` ends by resetting the snowpack to three layers of ice totalling 600 mm, with no liquid, on every
  call (L2653). All snowfall and rain on land ice is deleted, sublimation is created, meltwater never runs off, and
  the reset refreezes meltwater for free.
- `noahmpdrv` floors glacier snow at 0.1 mm on every call (L960). NOAA-EMC/noahmp's NUOPC component does this only at
  initialisation.
- Thin snow without layers is zeroed at the end of `noahmp_glacier` (L357, after `error_glacier`) and in
  `snowh2o_glacier` (L3347), as in NM5.

**Fix:** keep every assignment and book its water. The reset's liquid leaves as surface runoff and its ice change as
glacier flow, and rain on snow without layers, which the caller adds only afterwards, leaves as surface runoff. The
floor's added snow is booked as negative subsurface runoff (`drain`). The end-of-glacier truncation is glacier flow;
the `snowh2o_glacier` one, which cannot reach `runsub`, is surface runoff. Glacier behaviour is unchanged.
**Measured** in a harness that compiles the real `noahmpdrv_run` one column at a time (red team, both `iopt_gla`):

| Case | Without NM9 | With NM9 |
|---|---|---|
| a 26 mm/day snow day | all 26 mm deleted | 25.98 mm booked as glacier flow |
| sublimation | 0.47 mm/day created | 0 |
| one glacier column, 120 days | −860 mm | −2.4 × 10⁻¹³ mm |
| 60-day melt seasons | −8 to −33 mm | ≤ 1.1 × 10⁻¹³ mm per call |
| 0.1 mm floor, melting glacier without the reset | +2.3 to +5.9 mm/day | 0 |

Soil points are bit-for-bit unchanged. The v1 snapshot has the floor and the truncations but no reset (NM9 applies there
without its reset part); in a 10-day C96 run from March (1315 glacier columns) none of them fires. Started with every
glacier snow-free, the floor fires 278 times in 10 days and creates 6.5 mm summed over the columns (0.005 mm per
glacier column), and the end-of-glacier truncation fires 9 times (0.6 mm). On `ufs/dev` the reset acts on every
call. **Energy:** the host and couplers read `drain` as
liquid, but over land ice it now carries glacier ice and goes negative where the glacier supplies it. Read as ice, the
reset leaves 0.02–0.4 W/m² of sensible heat unbalanced; read as liquid, its free refreeze is only relabelled (8–26 W/m²
over a melt season). The interface has no frozen-runoff flux; the code marks the ice terms `FIXME` (section 7).

**NM10, the phase of precipitation** (diff 17, `module_sf_noahmplsm.F90`). Not a water leak: Noah-MP conserves water
either way, but `atm` (L1094–1104, `opt_snf = 4`, this suite) sets the snow fraction `fpice = prcp_frozen/prcpnonc`,
the microphysics' frozen share of grid-scale precipitation, and applies it to all precipitation, convective included.
Where grid-scale precipitation is only a trace of snow, `fpice` = 1 and convective rain falls as snow; with no
grid-scale precipitation, convective snow falls as rain. **Fix:** the microphysics' fraction applies to grid-scale
precipitation only, and convective precipitation is snow below freezing, the host's own rule for its snow fraction
`srflag` (`GFS_MP_generic_post` L495–516, with the skin temperature; Noah-MP's `atm` has the air temperature); the
fresh-snow density is blended by mass. Without convective precipitation the result is bit-for-bit unchanged.
**Measured:** cold convective snow with no grid-scale precipitation, which fell as rain, builds 7.8 mm of snow in two
days in the single-column harness; water and energy closure are unchanged over 48,000 random calls; in 24-h C96
forecasts the change is within the noise of bit-perturbed initial conditions on every land and atmosphere metric
checked. A second switch, in the canopy's wetted fraction, is reported separately (Appendix E.2).

**NM11, the latent heat of the ground's vapour** (diff 18, `module_sf_noahmplsm.F90`). `energy` (L2224) charges the
ground's vapour flux at `hvap` when `tg` is above freezing, but `water` takes that vapour from the snow ice (`qsnsub`,
L7169) and puts frost onto it (`qsnfro`) whenever there is snow. On thawing snow the land therefore pays `hvap` for
ice and creates `hfus` per kilogram, and the reverse for frost. **Measured** in the single-column harness: 0.13–0.61
W/m² over a 120-day snow season, up to 78 W/m² in one call. **Fix:** `latheag = hsub` whenever there is snow. Where
the phase moved still differs from the one charged (the snow melts out within the step, or frozen ground runs out of
soil ice and gives up liquid, which was already the case), `water` returns the difference to the top soil layer's
temperature, with `thermoprop`'s heat capacity. The ground's latent-energy error is then zero to output precision
(≤ 3 × 10⁻⁵ W/m² per call) over seasons, random columns and columns built to melt out, with returns of 0.004–0.014 K
per call on average (0.14 K at most); water is unchanged. Not covered: shortfalls inside `snowh2o` and `combine`
(none occurred in any test) and transpiration from a frozen canopy (section 7).

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

The totals are exact; the per-scheme columns come from the split, so the last row's leftovers are below its
resolution. SA1 and TH1–TH4 with and without NM1 (which changes only the land flux, so the trajectories diverge) agree in total and
microphysics residual to 1 × 10⁻⁵ kg/m² per window: our floor for differences between builds, from this one pair.

**Exact closure with the meters**, v1 snapshot, C96:

| Build | Physics residual | Dynamics + update (R_dyn) | Total / P |
|---|---|---|---|
| unmodified | +0.0020, +0.0019, +0.0018 kg/m² per window | 0.000000 | +0.29, +0.27, +0.26 % |
| SA1, TH1–TH4, TH5, TH6 and NM1 | 0.000000 at 6 decimals | ≤ 0.000001 | 0.000 % |
| all of SA1, TH1–TH6 and NM1–NM6, double-precision physics meter | −1.46 × 10⁻⁷ kg/m² per 6 h | | 2 × 10⁻⁷ |
| + TH8 (held), FV1, NM8, 24 h | −1.6 × 10⁻⁸ kg/m² per 6 h | ≤ 0.000001 per window | 2 × 10⁻⁸ |
| + NM7, TH7, 24 h (every fix, TH8 included) | −4.3 × 10⁻¹⁵ kg/m² in 24 h | ≤ 0.000001 per window | 1.5 × 10⁻¹⁵ |

The dynamics side: R_dyn is zero to 10⁻⁶ kg/m² in every window in both 32- and 64-bit builds. The individual meters
inside the dynamical core each change water by less than 3 × 10⁻⁷ kg/m² per step in 32-bit (rounding of both signs)
and about 10⁻¹² in 64-bit, and together account for the snapshot changes to 3 × 10⁻⁸ kg/m². `fill_gfs` and
`fv_update_phys` never changed water in these runs, so their meters show they were inactive, not that they conserve.

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

The per-scheme columns come from the split (pitfall 5), which is biased by a few hundredths of a percent of each
scheme's precipitation in 6-h windows (more in longer ones) while the total is exact; on `develop`, where the SAMF
condensate-transport diagnostics are zero, convection is the total minus the other schemes and carries that bias. So
the small residuals in the fixed rows (+0.03 %, +0.05 %, −0.07 %, −0.09 %) are not resolved.

Every cumulative build, adding one fix at a time, compiles and runs the C96 case to 24 h with a total of
0.00000 kg/m² in every window after the first (those builds carried SA1's first form). The final tree, `develop` + the
diffs exactly as published:

| Final tree | Runs | Total budget | Physics' residual over 24 h (physics-closure meter) |
|---|---|---|---|
| diffs 01–17 and 19 (before NM11) | 24 h at `dt_inner` = 720 s and 150 s; 10 days; C384 | 0.00000 kg/m² in every window and every day | −5.5 × 10⁻⁷ and −2.5 × 10⁻⁷ kg/m² (720 s, 150 s), one-signed; largest column 2–3 × 10⁻⁴ |
| the same with TH8 (an earlier final tree) | the same | 0.00000 | −9.7 × 10⁻¹⁵ and −7.8 × 10⁻¹⁵ kg/m²; largest column 2.2 × 10⁻¹³ |
| diffs 01–19 (with NM11) | 24 h | unchanged | −5.4 × 10⁻⁷ kg/m² |

The residual without TH8 is the sub-threshold sedimentation out of the lowest layer, which Thompson deletes and TH8
would count. Before NM11, the boundary layer adds what it books to 1.5 × 10⁻¹¹ of evaporation, and the metered output
is byte-identical to the unmetered one.

**Ten days** (`develop`, C96, 24-hour windows, total only; pitfall 4):

| Build | Residual per day, days 2–10 | / P | Range over the days | Accumulated |
|---|---|---|---|---|
| unmodified | +0.0055 kg/m² | +0.18 % | +0.15 to +0.22 % | +0.050 kg/m² |
| + SA1, TH1–TH4, NM1 | −0.00017 kg/m² | −0.006 % | −0.008 to −0.005 % | −0.0016 kg/m² |
| + all diffs (and with TH8 as well) | 0.00000 kg/m² | 0.000 % | 0.00000 every day | < 5 × 10⁻⁵ kg/m² |

- The defects and fixes reproduce on current code to within a few hundredths of a percent of the v1 snapshot.
- The fixed residual does not drift over ten days; with all diffs it is zero at 10⁻⁵ kg/m² every day. The unmodified
  error is smaller after day 1 but does not decay further.
- The convective error is larger at C384, and most of the larger C384 total. C384 also uses a shorter time step, so
  this is not a clean resolution dependence.
- Global precipitation changes by at most 0.5 % per window between builds.

**Forecast impact.** An independent red team (a second session) compared 24-h C96 forecasts with and without each
fix against a noise floor from nine pairs of bit-perturbed initial conditions. A change counts only above three
times the noise maximum and when it is coherent across related fields. Unperturbed reruns and meter-only builds
differ by exactly zero.

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

SA1's final form against its first form changes precipitation by −0.57 % (4×), but that pair also differs in
TH5's inner steps and TH7's floor start; SA1 alone has not been isolated. The final tree before NM11 against `develop` shows only these
signals: land canopy evaporation +10 % (NM2), snow sublimation +5.7 % and snow depth +1.8 % (NM3, NM4), land latent
heat −0.5 %, land 2-m temperature +0.03 K, global precipitation −0.7 % (SA1's final form). Forecast skill against
observations, other start dates and cycled runs were not assessed.

## 7. What remains

What is held, what is still open on the proposed fixes, and what we did not measure. Problems found along the way
that need their owners rather than a fix from us, such as the NSST sea-spray instability and the wetted fraction of a
mixed-phase Noah-MP canopy, are in Appendix E.

**Held.**

- **TH8 is held, with a fix for Thompson's placeholder** (`patches/held/TH8_*.diff`, `TH9_*.diff`). Thompson
  keeps an absent species at a placeholder `R1` = 10⁻¹² and gives an empty layer the fall speed of the layer above
  (`vtsk(k) = vtsk(k+1)`, L3950; ice L3903), so in the flux-form ice and snow sedimentation the placeholder settles as
  if it were mass, and the in-loop `max(R1, …)` re-creates it every substep. TH8 books the trace that reaches the surface
  as grid-scale snow. With `opt_snf = 4`, Noah-MP's `atm` (L1094–1104) sets its frozen fraction to that snow divided by
  the grid-scale precipitation and applies it to all precipitation, convective included; where the grid-scale part is
  only the trace, the fraction is 1 and convective rain reaches the land as snow (forecast impact in section 6). The
  Noah-MP side is fixed by NM10 (section 3). The Thompson side (TH9) extends TH7's treatment of the placeholder to the
  flux-form branches, so the placeholder is not sedimented; it removes about 95 % of TH8's land signal. What remains is
  genuine traces of snow (10⁻¹⁴ to 10⁻⁸ mm/day from upwind numerical diffusion) that the old threshold discarded. On
  the canopy they become trace ice, which hides the canopy's liquid (Appendix E.2). With TH9 and NM10, TH8 against TH8
  reverted is within noise from 6 h on but not in the first 6 h: land canopy evaporation −2.4 % (11× noise), snow
  sublimation +1.1 % (14×). With the mass-weighted wetted fraction (Appendix E.2), TH8 and TH9 are within noise (canopy
  evaporation +0.08 %, sublimation −0.03 % in the first 6 h; one row at 4×), so they wait for that change.
  Without TH8 the physics deletes the sub-threshold sedimentation again (section 6).

**Open points on the proposed fixes.**

- **Noah-MP's canopy evaporation cap** (energy only; +0.0012 W/m² per land column after NM8 and NM7, 1 % of land
  column-steps). `vege_flux` caps canopy evaporation at the water on the leaves before solving the canopy temperature
  (L4269–4271), but the linearised flux update after the solve (L4284) can take it back above the cap, and `canwater`
  then evaporates only what is there. NCAR's Noah-MP v5 has the same structure; CTSM adds the excess energy to the
  sensible heat flux. We propose no fix: both obvious ones (CTSM's transfer, or re-capping after the solve) change the
  energy partition, and we cannot show either is an improvement. The global land mean hides its size where it acts:
  a red-team harness found 0.053 W/m² as a forest mean over 120 days, and up to 65 W/m² in a single call.
- **Glacier ice in `drain`** (energy). After NM9, the subsurface runoff over land ice carries glacier ice, negative where
  the glacier supplies it, but the host and couplers read it as liquid (section 3). The code marks it `FIXME`. Closing
  the energy needs a frozen-runoff flux in the CCPP interface, the host and the couplers.
- **Latent heat of frozen-canopy transpiration** (energy). Below freezing the canopy's transpiration is charged at
  `hsub`, though the water transpired is liquid soil water. NM11, which fixed the ground's sublimation and frost on
  snow, does not cover it, nor the shortfalls inside `snowh2o` and `combine` when snow sublimates past what is left
  (none occurred in any test).
- **The surface layer with MYNN** (`iopt_sfc = 4`, not in this suite) still derives the moisture flux from latent heat
  (`evap/con_hvap` for `sfcdif4`), so NM1 is incomplete there.
- **NM5 with implausible host input.** If the host hands Noah-MP a large snow amount with a depth ≤ 10⁻⁶ m, NM5 can push
  the top soil layer's ice past porosity (water is conserved); realistic truncations of ≤ 10⁻³ mm change it by at most
  2.5 × 10⁻⁵ m³/m³. Negative snow from the host is still created into water.
- **Thompson's remaining edges** (red team). A column with no vapour at all can still be floored after TH6's refill,
  which draws condensate only from the same layer. TH7's entry exchange leaves latent heat unpaid where no vapour exists
  to pay it (under 40 J/m² in the red team's tests).
- **The cold start** (pitfall 2) removes 0.0024 kg/m² once, because the initial condition is built on unfiltered
  terrain. It is fixed on the initial-condition side, not in the model code.
- **Deliberate sources:** `h2ophys` relaxes stratospheric water vapour towards climatology (+1.2 × 10⁻⁷ kg/m² per 6 h
  here); the meters account for it separately.
- **A diagnostic gap on `develop`:** with SAMF, `dtend_liq_wat_cnvtrans` and `dtend_ice_wat_cnvtrans` are always zero
  (`GFS_suite_interstitial_4` fills them only for Grell–Freitas and TH4), so the upstream convection split is computed
  by difference.

**Not measured, and outside UFS.**

- **Not measured:** the snow budget on sea ice, lakes, other suites and coupled configurations, OpenMP threads > 1 (the
  meters assume one thread), cycled runs and analysis increments.
- **Host dynamics in WRF and MPAS** (outside the physics, in scope; fixes in progress; Appendix D). Once Thompson is fixed, four transport and
  diffusion operators in those dynamical cores still change total water, and none of them is in UFS:
  - WRF's `diff_opt=2` horizontal scalar diffusion loses 0.1 % of precipitation in a supercell;
  - WRF's no-PBL vertical moisture diffusion creates water;
  - MPAS's monotonic transport clip creates 3.8 × 10⁻⁵ of precipitation wherever the vertical Courant number exceeds 1;
  - MPAS's pre-physics zeroing of negative scalars creates water when the limiter is off.

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
| `17_NM10_noahmp_precip_phase.diff` | NM10 | `module_sf_noahmplsm.F90` |
| `18_NM11_noahmp_ground_vapour_latent_heat.diff` | NM11 | `module_sf_noahmplsm.F90` |
| `19_FV1_fv3_prsl_with_physics_gas_constants.diff` | FV1 | `driver/UFS/atmosphere.F90` (GFDL_atmos_cubed_sphere) |
| `held/TH8_thompson_count_all_surface_sedimentation.diff`, `held/TH9_thompson_placeholder_not_sedimented.diff` | TH8 and TH9 (held) | `module_mp_thompson.F90` |

**Earlier labels.** Drafts before 15 October named the fixes in the order we found them:

| Now | SA1 | TH1 | TH2 | TH3 | TH4 | TH5 | TH6 | TH7 | TH8 | TH9 | NM1 | NM2 | NM3 | NM4 | NM5 | NM6 | NM7 | NM8 | NM9 | NM10 | NM11 | FV1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Was | A | B | C1 | C2 | C3 | M4 | M1 | M5 | M2 | 13a | D | E | F | G | H | I | L | K | N | O | (new) | J |

**Verified on MSU Hercules** (Intel, `-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1 -D32BIT=ON`):
- the unmodified `develop` clone passes `control_p8_ugwpv1` (`develop-20260921` baseline) and `control_c384`;
- every cumulative build, one fix at a time, compiles with 0 errors and runs the C96 case to 24 h; unmodified,
  + SA1, TH1–TH4 and NM1, and the earlier final trees also run to 240 h and the C384 case;
- the final tree before NM11, `develop` + diffs 01–17 and 19 as published, is byte-identical to the `all` git
  series (the 12 changed physics files) and runs the C96 case to 24 h at `dt_inner` = 720 s and 150 s, metered and
  unmetered, to 240 h and the C384 case; the earlier final tree with TH8 also ran to 240 h and the C384
  case, and the cumulative builds before it carried SA1's first form; every series applies with `git am` on its base (and on NCAR/ccpp-physics `main`);
- the full regression suite (288 tasks, Intel and GNU) on the final tree: 54/54 compiles, 17 pass and 180 change only baselines; of 8 runs that did not complete, 6 hit /work2 input/output errors on both attempts (infrastructure; one of them, the land debug test, completed separately with 09b) and 2 are the land-component tests that need 09b, which ran to completion with 09b separately (`control_p8_atmlnd`, its debug build, `cpld_control_p8_lnd`); no temperature-range violations (the earlier diff set had nine); the 29 restart and decomposition tests that compare against their parent did not start, because the parents change baselines;
- in the CCPP single-column model (`ccpp-scm` `main` 4ea4c5e, capgen, Intel ifx), the final NCAR `main` series builds
  with 0 errors for all 57 suites in release and bounds-checked builds (SA1's hand port included; the debug build's
  link fails identically without the patches), and the `.meta` changes pass the framework's validator and capgen,
  as they do in the UFSATM capgen check with the `ufs/dev` series; every generated `noahmpdrv_run` call passes
  `iter=ccpp_loop_counter` by keyword; the patched SCM runs the ARM SGP and GABLS3 (Noah-MP) cases to completion with
  the GFS v17 and HRRR suites, release and bounds-checked, with no NaN; `-warn all` shows no new warnings.

**Scripts** in `scripts/` (Python 3 with numpy and netCDF4; each takes run directories as arguments):

| Script | What it does |
|---|---|
| `water_budget_by_scheme.py` | total and per-scheme budget per window (section 6); `WB_WINDOW`, `WB_END`, `WB_BUCKET`, `WB_THICK`, `WB_UNWEIGHTED` |
| `water_budget_native.py` | total budget only, without `dtend` diagnostics |
| `column_mapping_check.py` | per-column boundary-layer closure (diagnostics map to the right columns) |
| `land_atm_water_closure.py`, `noahmp_qfx_excess.py` | offline land–atmosphere gap and the composition of NM1 |
| `water_jump_series.py`, `coldstart_trace.py` | the first hours, and an offline replica of the cold-start initialisation (pitfall 2) |
| `apply_water_patches.py`, `apply_thompson_c_patches.py`, `apply_thompson_c34_patches.py`, `apply_noahmp_d_patch.py`, `apply_thompson_m_patches.py` | apply SA1, TH1–TH6 and NM1 to the v1 snapshot |
| `mk_upstream_c3_diff.py`, `mk_upstream_m_diffs.py` | write TH4, TH5, TH6 into a `ufs/dev` tree (diffs 04–06) |
| `apply_noahmp_e_patch.py`, `apply_composites_f_patch.py`, `apply_noahmp_g_patch.py`, `apply_noahmp_h_patch.py`, `apply_noahmp_i_patch.py`, `apply_thompson_m2_patch.py`, `apply_fv3_j_patch.py`, `apply_noahmp_k_patch.py`, `apply_thompson_m5_patch.py`, `apply_noahmp_l_patch.py`, `apply_noahmp_glacier_n_patch.py` (with `apply_noahmp_h_glacier_patch.py`) | apply NM2–NM9, TH7, TH8 and FV1 to either tree |
| `apply_samf_a2_patch.py`, `apply_thompson_c_neg_patch.py` (`_v1.py`), `apply_thompson_m4_inner_patch.py`, `apply_thompson_qv_floor_patch.py`, `fix_thompson_negr_rain_floor.py`, `apply_thompson_m5_noreturn_patch.py` | the final parts of SA1 (cloud-base face), TH2–TH3 (cloud substepping, snow-gain cap), TH5 (depth per inner step), TH6 (vapour refill) and TH7 (placeholder floor start, no early return) |
| `instrument_wb_phys.py`, `phys_meter_budget.py` | whole-physics meter; exact physics/dynamics split per window |
| `instrument_wb_ep.py`, `ep_meter_budget.py` | physics closure per step and column against E, P and `h2ophys`, and the boundary layer's added vs booked water |
| `instrument_wb_dyn.py`, `dyn_meter_budget.py` | meters inside the dynamical core and the physics → dynamics update |
| `instrument_wb.py`, `instrument_wb_driver.py` | Thompson column routine by stage, and the whole driver call; SAMF negative-borrowing counters |
| `instrument_wb_land.py`, `land_meter_budget.py` | land ↔ atmosphere evaporation and precipitation hand-offs |
| `instrument_wb_noahmp.py`, `noahmp_balance.py`, `instrument_wb_iter2.py`, `iter2_budget.py` | Noah-MP storage in and out of each call, and what the second surface pass adds (NM2) |
| `instrument_wb_noahmpx.py`, `instrument_wb_noahmpf.py`, `instrument_wb_noahmph.py`, `instrument_wb_noahmpc.py` | `errwat` by state and size, split around `water()`, and meters at the NM5 and NM6 sites |
| `instrument_wb_noahmpg.py` | the land's latent energy against the latent energy of the water it hands the atmosphere, split into the constants (NM8) and Noah-MP's own water–energy consistency (NM7, canopy cap) |
| `instrument_wb_phys_ups.py`, `instrument_wb_ep_ups.py`, `instrument_wb_ups.py`, `instrument_wb_ups_rten.py`, `wb_meter_report_ups.py` | the whole-physics, physics-closure and Thompson stage meters ported to `ufs/dev` (Thompson split by species, the semi-Lagrangian terms and the leftover-rain overwrite: TH7) |
| `instrument_wb_glacier_z.py`, `instrument_wb_glacier_floor.py` | meters at the two glacier thin-snow truncations and at the driver's glacier floor (NM9) |
| `instrument_wb_osc_meter.py`, `instrument_wb_osc_pert.py`, `osc_report.py` | per-scheme lowest-layer tendencies and a run-time temperature perturbation (the sea-spray instability, Appendix E.1) |

The `instrument_*` scripts are for diagnostic builds only. The meters accumulate in module variables and assume one
OpenMP thread; a threaded regression check would need reductions.

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

- **TH2–TH4 and TH6 belong to the scheme**, so their fixes apply to every host. No copy has a water fixer. TH8 and TH7 were not
  surveyed in the other copies (TH7's sedimentation part is in `semi_lagrange_sedim`, a UFS addition).
- **TH1 belongs to the CCPP interface.** TEMPO's CCPP driver repeats Thompson's conversion, so TH1 survives a switch to
  TEMPO unless its driver is fixed too.
- **NM1 belongs to the CCPP port of Noah-MP.** Every NCAR/noahmp driver (WRF, HRLDAS, MPAS, LIS, ERF;
  `drivers/*/WaterVarOutTransferMod.F90` L59–64) passes the water mass flux. The latent-heat form is in ccpp-physics and
  in NOAA-EMC/noahmp's CCPP driver and NUOPC land component; the latter also sets glacier canopy evaporation and
  transpiration to `undefined`. NOAA-EMC/noahmp also has NM5 and NM6 (`src/module_sf_noahmplsm.F90` L945, L2047, L8162;
  L7328, L7337) and the same latent-heat constants (NM8).
- **FV3 coupling.** `dev/emc` (`driver/UFS`) and `main` (`driver/SHiELD`) both pass the dry + vapour basis and rebuild
  `delp` as old dry mass + Σ(physics thickness × returned q). SHiELD's in-line GFDL microphysics converts on a dry basis
  and holds dry mass exactly. The only fixers reachable from UFS act at initialisation or in the IAU window.
- **SAMF elsewhere.** GFDL's in-line `sa_sas`/`sa_aamf` (SHiELD) have no TVD and no cloud-base subtraction.
- **MPAS only:** condensate above `config_microphysics_top` (default 45 km) is zeroed each step while vapour is left
  alone (`mpas_atmphys_interface.F` L936–946, L999–1003; added October 2025).

Commits read: ufs-community/ccpp-physics `ufs/dev` c7dc705; NCAR/ccpp-physics `main` f601ce9; NCAR/TEMPO `main`
c62699f; wrf-model/WRF `develop` 1086c86; MPAS-Dev/MPAS-Model `develop` aa6d8cd; NCAR/noahmp `master` 1a6225b;
NOAA-EMC/noahmp `develop` 2c7b3bc; NOAA-GFDL/GFDL_atmos_cubed_sphere `dev/emc` 71ff473 and `main` 8b94b9f. Not checked:
the CCPP single-column model, HAFS forks, MPAS's `physics_mmm` tree, the TH4 convection scheme.

## Appendix D — water created or lost by the WRF and MPAS dynamics

We ported the Thompson fixes to WRF and MPAS and ran each in an idealized supercell: doubly periodic, no surface
fluxes, 2 h. Once the scheme closed, both hosts still changed total water. The meters put the remainder in the
dynamics, not in the microphysics or its coupling.

**Meters.**
- **Domain:** total water in the host's dry-air mass plus accumulated surface precipitation.
- **Microphysics:** water before and after each microphysics call, in the host's frame. In MPAS a second meter covers
  `microphysics_from_MPAS` → `mp_gt_driver` → `microphysics_to_MPAS`.
- **Clips:** a third meter counts the water each MPAS clip adds.
- **Perturbation check:** in MPAS the instrumented runs are bit-identical to the plain run (checked in every run). In
  WRF this was not checked.
- **Fractions:** all are of the precipitation over the run.

**WRF** (wrf-model/WRF `release-v4.8.1` 315a8319, `em_quarter_ss`; Thompson with the ported fixes, including the
host-density layer mass; microphysics +1.7 × 10⁻⁶):

| configuration | domain change / P |
|---|---|
| `diff_opt=2`, `km_opt=2` (TKE K), as the test case ships | −1.07 × 10⁻³ |
| the same, `mix_full_fields=.false.` | −1.03 × 10⁻³ |
| the same, `moist_adv_opt=2` (monotone) | −1.05 × 10⁻³ |
| `diff_opt=2`, `km_opt=1` (constant K) | −2.7 × 10⁻⁵ |
| `diff_opt=0` | −1.8 × 10⁻⁶ |
| `diff_opt=1`, `km_opt=4`, no PBL scheme | +0.93 (water created) |
| `diff_opt=1`, `km_opt=4`, `kvdif=0` (the routine below switched off) | +1.2 × 10⁻⁶ |
| `moist_adv_opt=0` (no positive-definite limiter) | +4.4 × 10⁻² |
| WSM3 (`mp_physics=3`), `diff_opt=1`, `km_opt=4`, `kvdif=0` | −5.5 × 10⁻⁷ |

- **W1. `horizontal_diffusion_s` does not conserve mass** (`dyn_em/module_diffusion_em.F` L3711–3999; used with
  `diff_opt=2`).
  - The tendency (L3978) weights each column's flux divergence by that column's own `g/(dnw·rdzw)`, its ρ·dz per unit
    η. The coordinate-slope terms are not in flux form either, so the domain sum does not telescope.
  - With TKE eddy diffusivity in a storm it loses 0.1 % of precipitation; with constant K the loss is 40 times smaller.
    Vertical scalar diffusion telescopes and conserves.
- **W2. `vertical_diffusion_mp` creates water** (`dyn_em/module_big_step_utilities_em.F` L3192–3281). WRF calls it for
  qv when `diff_opt=1` and `bl_pbl_physics=0` (`dyn_em/module_em.F` L1393–1397).
  - It sets the surface flux equal to the flux at the first interior interface (`vflux(i,0)=vflux(i,1)`, L3265), so the
    ground becomes a moisture source.
  - Its 1/α weighting does not telescope either.
  - It is reached only without a PBL scheme, i.e. in idealized runs.
- **The real-data path conserves.** `diff_opt=1` horizontal diffusion is mass-weighted flux form and closes. So does
  WSM3, the microphysics of the ARL WRF that drives CT-L's HYSPLIT footprints.
- **Untested:** WRF's classic Noah land model (also in ARL's WRF) needs a real-data case; we did not run one.
- **The positive-definite limiter is necessary:** without it (`moist_adv_opt=0`), clipping by the physics creates 4.4 %
  of precipitation.

**MPAS** (MPAS-Dev/MPAS-Model `develop` aa6d8cd; supercell `config_init_case=5` on an 84 × 84 doubly periodic 2 km mesh,
double precision; Thompson with the ported fixes, including the host-density layer mass):

| run | domain change / P at 2 h |
|---|---|
| Kessler | −6.5 × 10⁻¹⁵ |
| Thompson, original | +1.97 × 10⁻² |
| Thompson, fixed, dt = 12 s | +3.8 × 10⁻⁵ (microphysics and coupling ≤10⁻¹⁵ kg/m²) |
| Thompson, fixed, dt = 8 s | ≤7 × 10⁻¹⁵ kg/m² |
| Thompson, fixed, `config_monotonic=.false.` | +0.7 (water created) |

- **MP1. The monotonic scalar transport's final clip creates water where the vertical Courant number exceeds 1**
  (`scalars_new = max(0, scalar_new)`, `src/core_atmosphere/dynamics/mpas_atm_time_integration.F` L5774, at the end of
  `atm_advance_scalars_mono_work`).
  - Above Courant number 1 the upwind part of the flux-corrected transport is no longer positive-definite, so the clip
    binds. Its water equals the domain residual at every 10-minute output, to all printed digits.
  - Thompson's 48 m/s updrafts reach 1.07–1.17 at dt = 12 s and 500 m layers. Kessler's storm stays below 0.96.
  - At dt = 8 s (at most 0.78) the run closes to roundoff.
- **MP2. `atm_srk3` zeroes negative water species before the physics** (L2797–2799, commented "for now").
  - It adds nothing while the monotonic limiter is on.
  - With `config_monotonic=.false.` it creates 1.40 kg/m² (0.7 of precipitation), while the microphysics adds
    1.3 × 10⁻⁹ kg/m².

**What these mean.**
- **None of the four is in UFS**, whose FV3 dynamics we measured separately (§6).
- **They are host properties, and they are in scope.** Without them fixed, a scheme-side fix closes water in WRF and MPAS
  only in configurations that avoid them.
- **Fixes in progress:**
  - W1: a flux-form horizontal diffusion with face-weighted mass;
  - W2: a zero surface flux and a telescoping tendency;
  - MP1 and MP2: a column-conserving fixer after the clips, and/or substepping the vertical transport so its Courant
    number stays below 1.
- **Status:** being implemented and tested in the same supercell cases; nothing has been filed upstream.
- **Full tables and scripts:** `patches/ports/README.md`.

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

### E.1 NSST: the sea-spray term is explicit

The day-6.4 blow-up in one 10-day v1 run is an existing instability, not a fix. It is in NSST's sea-spray term
(`sfc_nst.f90` L640–663, `lseaspray = .true.`, the P8 default), in the eyewall of a C96 tropical cyclone near 73E, 12S
where the 10-m wind reaches the spray cap of 30 m/s. The spray evaporation, proportional to `qs(T1) − q1`, is applied
explicitly to a 22-m layer over a 720-s step with a gain of about 14 per step. The lowest layer flips by 2–5 K every
other step, and Thompson condenses the overshoot. Once T1 exceeds the SST, the deficit and the spray grow together
until the layer runs away.

| From the same day-5.8 restart | Lowest layer |
|---|---|
| unmodified v1 physics | the same two-step oscillation, bounded to day 6.7 |
| spray off | no oscillation |
| half the time step | bounded oscillation |

A one-column perturbation of 10⁻¹² at step 1 changes whether the run crashes, so the crash is one chaotic
realisation. A limiter that keeps a spray step from saturating the layer removes the oscillation but cuts cyclone
spray about tenfold, so we propose no fix. The remedy belongs to the NSST owners: solve the spray and bulk fluxes
implicitly with the PBL, or substep them. `sfc_ocean.F` (L236–259) has the same code. Not a water defect: the water
the spray adds is booked as surface evaporation. We have not reproduced the oscillation on current `develop`.

### E.2 Noah-MP: the wetted fraction of a canopy holding both ice and liquid

`precip_heat` (L1389) and `canwater` (L7378) compute `fwet` from the ice alone whenever there is any canopy ice. The ice
capacity is about 50 times the liquid capacity, so a trace of intercepted snow hides the liquid: canopy evaporation
stops and transpiration takes the whole canopy. `fwet` also sets the canopy's evaporation and transpiration
conductances, its temperature during melt and freeze, and its snow optical fraction.

- **It is common.** 45–48 % of wet-canopy steps hold both phases, and on those the wetted fraction today averages 0.09,
  against 0.58 from the liquid alone. So there is no narrow fix.
- **Taking the larger of the two fill fractions** removes the switch (the phases share leaves), but changes the 24-h
  C96 forecast well beyond noise: land canopy evaporation +18 %, snow sublimation −13 %, land 2-m temperature
  −0.11 K, land humidity −0.9 %, reaching the lowest model levels.
- **A mass-weighted blend** of the two fill fractions (`patches/candidates/issue4_noahmp_fwet_mass_weighted.diff`;
  continuous, and the same as today for a single-phase canopy) moves the mixed-phase `fwet` to 0.51–0.54 and the
  forecast as much: canopy evaporation +20 %, sublimation −14 %, land 2-m temperature −0.09 K, q2m −0.8 %. Water still
  closes. With it, the held TH8 and TH9 no longer change the land beyond noise.

This is a land-surface behaviour change for the Noah-MP owners to evaluate against observations, not a sure
improvement. NCAR's Noah-MP v5 uses the phase with more mass in `CanopyHydrologyMod.F90` (L104–108) and keeps the switch
in `CanopyWaterInterceptMod.F90` (L132–137).

### E.3 MYNN-EDMF: more surface moisture added than the surface scheme removes

In 24-h C96 forecasts the MYNN suites (`FV3_GFS_v17_p8` with MYNN, `FV3_HRRR`, `FV3_RRFS_v1beta`, `FV3_RRFS_v1nssl`)
create +2 to +3.5 % of precipitation per 6 h. Two defects in `module_bl_mynn.F90` explain it:
1. **Density.** The driver sets the kinematic flux `flqv = qfx/rho1(kts)` (L1069), but `mynn_tendencies` adds it as
   `rhosfc*flq` (L4391, L4456, L4521), with `rhosfc` from the surface pressure (L4137, which also has a typo:
   `tk + p608*qv` for `tk*(1 + p608*qv)`). Net: +0.85 % of evaporation.
2. **Dew.** The limiter at L4514 gives 0 for any downward vapour flux whenever `sqv(kts)` > 1.1 × 10⁻⁸, i.e. always, so
   the atmosphere loses no vapour to dew while the surface scheme books it as removed: +0.55 to +0.9 % of evaporation.

**Fix (tested):** use `rho(kts)` in the three surface sources, and the limiter the comment describes. `FV3_GFS_v17_p8`
with MYNN then closes to 0.00 %; `FV3_HRRR` and `FV3_RRFS_v1beta` are within −0.03 to −0.10 %, the per-scheme split's
bias. The same factor also multiplies the sensible-heat flux and the momentum drag (not changed). Also worth a look:
`mynnedmf_wrapper.F90` (L627–632) clips the incoming moisture flux. The surface layer with MYNN (`sfcdif4`) also
derives the moisture flux from latent heat (section 7). Forecast impact not assessed.

### E.4 GFDL microphysics v3: the same mass-basis defect as TH1

`gfdl_cloud_microphys_v3_mod.F90` converts to mixing ratios with `1/(1 − qv)` (L973–985) and back with
`1/(1 + qv_new)` (L1218–1232), returning an updated `delp` that would make the pair consistent. The CCPP driver keeps
that `delp` in a local array (L174, L240, L263), so FV3 rebuilds each species' mass from the pre-physics thickness, and
net condensation creates water. In 24-h C96 forecasts with `FV3_GFS_v17_p8` and GFDL MP v3 the suite's total is
−0.3 % of precipitation per 6 h, with the microphysics at −1.0 % of grid-scale precipitation. **Fix (tested):** convert
back with the input humidity; the suite then closes to 0.00 %. The correction could instead go in the CCPP driver,
leaving the scheme unchanged for other hosts. GFDL microphysics v1 does it right. Forecast impact not assessed.

### E.5 Grell–Freitas: shallow convection without its precipitation

In `cu_gf_driver.F90` a column with shallow convection always has its shallow tendencies applied (L951, L993), but
`raincv` includes the shallow precipitation only when deep convection is active (L1034). In shallow-only columns the
water the shallow scheme removes is in no precipitation field.

- **Measured** (24-h C96 `rap_control`, metered, output byte-identical to unmetered): GF loses 0.036–0.040 kg/m² per
  6 h, 30–34 % of its own precipitation, all in shallow-only columns. `FV3_RAP` loses 2–7 % of precipitation; MYNN's
  gain (E.3) partly hides it.
- **The obvious patch overshoots.** Adding the shallow scheme's own precipitation, `prets`, turns the loss into a gain
  of 0.010–0.022, because `cu_gf_sh.F90` computes it differently from the tendencies it applies.
- **A tested candidate** (`patches/candidates/issue7_gf_shallow_precip_from_tendencies.diff`) takes the shallow
  precipitation from the water GF's applied tendencies remove, in the host's layer mass, floored at zero. GF's
  residual falls to +0.004–0.005 kg/m² per 6 h; what remains is the floor (3.7 % of shallow-only column-steps are net
  moistening, cause not diagnosed).
- **It changes the forecast well beyond noise**, because the water that used to vanish now falls: global precipitation
  +8.6 % (convective +34 %), RUC top-layer soil moisture 37 times the noise. All 44 regression tests on GF suites run
  to completion, and decomposition, threading and restart stay bit-reproducible.

That size of change needs the owners' judgement, and a decision on net moistening, before it can be a PR.

### Not located

`FV3_GFS_v16_csawmg` (Chikira–Sugiyama convection, Morrison–Gettelman microphysics) creates about +10.5 % of
precipitation per 6 h in a 24-h C96 forecast, with or without the fixes in this proposal. We have not traced it.
