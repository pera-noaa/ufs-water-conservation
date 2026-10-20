# MPAS-A water, dry-mass and energy conservation: supercell, 24 h

## Status (18 Oct 2026)

- **Case.** MPAS-A at aa6d8cd69, supercell (init case 5), 84×84 doubly periodic 2 km hexes, 40 levels, 20 km lid,
  double precision, dt 12 s, Thompson, no surface fluxes or radiation, 24 h, 16 tasks. Storm lives ~8 h.
- **Closure with the series, layer coupling and the fixer (§9).** Dry mass is exact. Water closes to round-off; this
  needs TH8/TH9, which are in the MPAS series on the user's instruction and held everywhere else. Physics and coupling
  energy close genuinely. The dycore residual is closed by the labelled, reproducible fixer. A per-term tally (§4)
  puts 65 % of it in KE removed by explicit diffusion and damping with no heat returned (design); the remaining 35 %,
  the net error of the energy-conserving operators, is **OPEN**.
- **Without the fixer, stock coupling:** E falls by 4.3e-4 in 24 h, split between dycore and microphysics (§2).
- **Stock MPAS latent heating is consistent (§2).** Option B (layer coupling, 0012) adds the frictional heating of
  falling water (Pauluis et al. 2000; §3) and a Kirchhoff-slope term; it strengthens the storm and leaves
  precipitation within noise (§6). **Ash's decision: 0012 is opt-in, default stock (option A).**
- **Dissipative heating (0014, opt-in, §10)** returns the tallied KE as heat: option 2 (recommended) as
  positive-definite dissipation rescaled to the work, option 1 as the signed local work. The fixer falls from 3.81e5 to 1.31e5 J/m², which is the
  §4 remainder. The updrafts strengthen beyond noise; precipitation does not change.
- **Deliverable:** `proposal/patches/ports/MPAS-conservation/`, 14 labelled patches; every gate passes (§8).
- Hercules: `$R/e24` (`$R = /work2/noaa/co2/ash/ufs-chem-v1/upstream/mpas`). Generators and scripts: `$R/e24/*.py`.

| quantity, 24 h | stock | fix (ports + v2 dynamics) | + held TH8/TH9 | + layer coupling + fixer (v4) |
|---|---|---|---|---|
| ΔW/W | 1.3e-3 | ~1e-9 (−4.7e-8 kg/m²) | 2.2e-15 | −1.6e-16 |
| ΔMd/Md | ≤7e-15 | ≤7e-15 | ≤7e-15 | 0 (exact) |
| ΔE/E | — | — | −4.3e-4 | +1.9e-16 |

## 1. Energy definition (the model's own)

E = IE + PE + KEh + KEw + Lv0·Wv − Lf0·(Wi + Pice) [+ g·z_sfc·P], per unit area, with IE = cv_d·T_m·dm,
T_m = θ_m·exner(ρ_zz, θ_m) (the EOS MPAS integrates), PE = (1+qt)·g·z_mid·dm, KE = (1+qt)·K·dm (Ringler cell KE
plus interface w²/2), dm = ρ_zz/rdzw. Liquid is the zero; vapour Lv0 = 2.0587e6, ice −Lf0 = −3.34e5. Condensate
carries no heat capacity; vapour's is cv_d·Rv/Rd = 1154 J/kg/K (MPAS's θ_m). Precipitation leaves with zero energy
(ice −Lf0).

## 2. Per-process budget (meter, 7200 steps, J/m²; with TH8/TH9, stock coupling, no fixer: run `final_meter`)

| process | ΔE | ΔIE | ΔPE | ΔKE |
|---|---|---|---|---|
| dynamics + transport | −3.67e5 | −1.92e6 | +1.65e6 | −9.6e4 |
| pre-physics guard | 0 | 0 | 0 | 0 |
| microphysics (Thompson, stock coupling) | −6.96e5 | +9.15e6 | −6.07e5 | −1.6e3 |
| gaps between steps | 0 | | | |
| **total** | **−1.06e6** | | | |

Microphysics: Thompson heats at constant π with its own L(T)/cp, and MPAS turns that into constant-volume heat at
fixed ρ_d, (L − R_v·T)/cv_d per kg condensed. That stock path is **consistent, not a defect**. The UFS encpl 1-D
column derivation (`../encpl/report.md`) reproduces it to 2e-6. FV3's path, by contrast, delivers hvap + R_v·T, 5 %
too much. E-consistent heating would be 7.3 % larger than Thompson's in this run (X, §3):
- 6.4 points are the missing frictional heating of falling water (Hpe, §3);
- 0.9 points are the latent heats' temperature dependence. Thompson's L(T) slope is cpv − cl = −2112 J/kg/K, against
  E's +1154 from MPAS's θ_m heat capacities (vapour cv_d·Rv/Rd, condensate none). This term is about the size of E's
  fusion term (8.9e4 J/m²); the meter does not separate it from the fusion heat.

Option B therefore adds the Pauluis term plus this Kirchhoff-slope term. It does not correct an R_v·T error.

## 3. Layer-local coupling (option B) and the Hpe check

Each layer's T_m from its own phase changes at constant volume with E's latent heats, plus Hpe (PE released by
sedimentation inside the layer) and Hke. Gate: column ΔE + precipitation term = 0 exactly when the column's water
closes; max |Rcol| = 8.9e-6 J/m² (v4, n16). The 24-h totals by process are in §6.

**Hpe sanity check** (run `f4h_lf`; its closure.nc is bit-identical to f4_lf_n16, so the extra diagnostics are passive):

| quantity, 24 h domain mean | value |
|---|---|
| gross condensation C (sum of positive per-layer, per-step vapour loss; a lower bound) | 11.09 kg/m² |
| surface precipitation P | 4.435 kg/m² |
| precipitation efficiency P/C | ≤ 0.40 |
| Hpe | 6.275e5 J/m² |
| mean fall height per gross kg, Hpe/(g·C) | 5.77 km |
| per surface kg, Hpe/(g·P) | 14.4 km |
| falling mass × interfaces crossed | 130.2 kg/m² |
| Hpe/(g · crossings) | 491.5 m (mean level spacing 500 m) |
| Hpe / (Lv0·P); Hpe / (Lv0·C) | 6.9 %; 2.75 % |

The inflow and outflow counting is right: each crossing releases g·(half a layer above + half below), and the mean
spacing comes back. Pauluis, Balaji & Held (2000) estimate 2–4 W/m² in the tropics, about 2–3 % of the latent heating.
Makarieva et al. (2013) revise that to 1–2 W/m². Per gross kg this supercell is in that range (2.75 %). Per net kg it
is 2.5× higher, because 60 % of the condensate evaporates after falling part of the way. The meter's independent
microphysics ΔPE (−6.28e5) matches Hpe.

## 4. Dycore residual

| variant | dyn ΔE (J/m²) | dyn ΔE / latent heating |
|---|---|---|
| base (final_meter) | −3.67e5 | 4.0 % |
| layer coupling | −3.78e5 | 4.1 % |
| coef_3rd_order 0 | −4.51e5 | 4.4 % |
| no del4 | −3.06e5 | |
| no w damping (config_xnutr 0) | −3.38e5 | |
| no divergence damping | −3.57e5 | |
| dt 6 | −3.89e5 | |
| lagged diabatic forcing off | −3.11e5 | 4.1 % |
| microphysics off (no storm) | −372 | |

Water loading, from the meter's dry/water split (f4_lf_n16, J/m²): ΔIE −2.09e6, Δ dry PE +1.24e6,
Δ dry KE −1.0e5, Δ water PE +5.60e5, Δ water KE +1.5e3, Δ latent 0. Residual with E as defined −3.81e5; without
water's KE −3.82e5; with water carrying neither PE nor KE −9.42e5. Water loading in E is right (dropping it makes the
residual 2.5× worse), and water KE is immaterial. The guard (the only qv limiter) changes nothing (exactly 0).

Dry thermals: microphysics off. A prescribed source, exp(−r²/(10 km)²)·sin(πz/12 km) per dry mass, for
8 h, applied E-consistently between EB points 3 and 4 (ΔE = q exactly). Moist species are zeroed at step 1 at fixed θ_m.

| run | heat input (J/m²) | dyn ΔE (J/m²) | ratio |
|---|---|---|---|
| th2_dry, 316 W/m² | 9.10e6 | −5.96e4 | −0.66 % |
| th2_dry_half, 158 W/m² | 4.55e6 | −2.56e4 | −0.56 % |
| th2_moist (vapour kept, passive) | 9.10e6 | −2.97e4 | −0.33 % |
| th3_hc: storm's gross heating 793 W/m² (0–12 km) + cooling 476 W/m² (0–5 km, Gaussian 12 km, 12 km downshear), 8 h | +2.28e7 / −1.37e7 | −2.45e5 | −1.07 % of gross heating |
| storm (f4h_lf), against net Lvap / gross Lvap+ | 9.13e6 / 2.28e7 | −3.81e5 | −4.2 % / −1.67 % |

Per step in the storm, the dyn residual regresses on the previous step's microphysics as follows:

| regressor | hourly correlation |
|---|---|
| gross condensation | −0.995 |
| Hpe | −0.986 |
| condensate mass | −0.966 |
| KE | −0.917 |
| net Lvap | −0.881 |

What the runs show:
- Most of the residual is a property of the dry dynamics responding to diabatic forcing: it is present without any
  water.
- The dry thermal with the storm's gross heating and cooling (th3_hc) reproduces 64 % of the storm's residual (2.45e5
  of 3.81e5 J/m²).
- The loss fraction grows mildly with forcing intensity: 0.56 % → 0.66 % for double the power, about P^0.24. The
  storm's forcing peaks at 2.45× the 8-h mean (hour 2). Scaling th3_hc by that gives about 1.33 % of 1.67 %. That is
  a two-point fit, not a test, and the classification does not rest on it.
- It is robust to dt, damping, diffusion and the advection order (table above). It tracks gross, not net,
  condensation. No single term moves it by more than 15 % (lagged diabatic forcing off: −14 %).

Per-term tally (research build `$E/tally2` = the 13 patches + `mk_etally.py` v2; meter on, no fixer; job 10153970,
runs `et2_storm`, `et2_hc`). The KE work of each explicit term is u·δ(ρu)·volume to first order, summed over owned
edges and cells:
- the explicit tendencies (computed on RK stage 1 and held) count × dt/3 per split step;
- divergence damping and w damping count on the final RK stage only, the only stage whose increments survive.

The remainder is dycore ΔE minus the tallied sum. With the tally on, closure.nc is bit-identical to `s12_lm` (storm)
and to the v1 tally runs over 20 and 9 variables (passive).

| term, 24 h (J/m²) | storm, layer coupling (`et2_storm`) | th3_hc forcing (`et2_hc`) |
|---|---|---|
| u del2 (2-D Smagorinsky) | −3.08e4 | −1.81e4 |
| u del4 | −1.37e5 | −6.46e4 |
| w diffusion | −3.11e4 | −2.17e3 |
| divergence damping | −8.36e3 | −2.70e3 |
| w damping (absorbing layer above 15 km) | −4.02e4 | −4.64e4 |
| u vertical diffusion, Rayleigh u (both off in this case) | 0 | 0 |
| θ_m diffusion (IE) | +35 | +2.4 |
| **sum of explicit terms** | **−2.48e5 (65 %)** | **−1.34e5 (55 %)** |
| remainder: advection, PGF, buoyancy, acoustic steps, tally truncation | −1.31e5 (35 %) | −1.11e5 (45 %) |
| dycore ΔE | −3.78e5 | −2.45e5 |

Correction to the v1 tally (jobs 10153199, 10153200; 88 %/79 %, withdrawn). It took the w and θ_m snapshots before
`w_dissipation_3d` and `scalar_dissipation_3d_les`, which zero their tendency first. So v1 counted w·(D_now − D_prev)
and θ·(D_now − D_prev) instead of w·D_now. Only those two rows change. v2 takes a zero snapshot.

Cross-check against the variants (stock coupling, base −3.67e5):
- w damping off raises dyn ΔE by 2.9e4 (tally 4.0e4);
- divergence damping off raises it by 1.0e4 (tally 8.4e3);
- del4 off raises it by only 6.1e4 (tally 1.37e5), because the other dissipation takes up the slack.

So the tally's scale is right to within ~30 %, and the 0014 heating returns each term as tallied (§10). The storm
exceeds th3_hc by 1.33e5 J/m². Of that, −1.14e5 is explicit dissipation of the storm's stronger flow, and the
remainder differs by −2.0e4. The remainder is similar with and without water, so it is not water-specific.

Classification: the explicit terms are **DESIGN**. MPAS removes KE by explicit diffusion and damping and returns no
heat. The remainder is **OPEN**. It is the net numerical energy error of the operators that conserve energy in the
continuum, and it includes the IE convexity of θ_m transport. Splitting it further needs exact per-operator accounting
inside the acoustic solver, which this tally does not attempt. The labelled fixer closes both. The opt-in 0014
returns the explicit terms as local heat (§10); the remainder stays with the fixer.

Method note: with microphysics off nothing resets rt_diabatic_tend, so the test heating resets it every step. Without
the reset (runs `th_*`, invalid) the heating accumulates in the lagged forcing and the dycore gains +40 % of the input.

## 5. Reproducible fixer (v4)

Fixed-point global sums (6 int64 digits of base 2^40, MOM6 reproducing_sum style) everywhere in the meter and fixer;
reference energy E0 and precipitation totals in the restart stream (diag ebud_eref, ebud_pall, ebud_pice, ebud_ppe).

| gate | result |
|---|---|
| closure.nc 16 vs 7 tasks (v4) | PASS bit-identical |
| closure.nc 16 vs 12 tasks (v4) | PASS bit-identical |
| restart.0000-01-02 straight vs 12 h + 12 h restart (249 variables) | PASS bit-identical |
| fixer reference after restart | E(24 h) identical in both (EB pt5) |
| switches off vs pre-meter tree (closure.nc) | PASS bit-identical (meter passive) |
| control: v3 (Neumaier sums) 16 vs 7 tasks | FAIL (as expected: the gate can fail) |

## 6. Option-B impact against noise

The control is stock coupling (`final_off`). The noise controls are fix2 vs fixth8 (a round-off water change) and
config_smdiv 0.1 → 0.1001 and 0.0999. Units:

| quantity | measure | unit |
|---|---|---|
| wpk | peak max w, 0–8 h | m/s |
| P | domain mean precipitation, 24 h | kg/m² |
| cold | min θ′, lowest layer, 0–8 h | K |
| cpa | area with θ′ < −4 K, mean 1–8 h | km² |
| w999 | 99.9th percentile of w, peak 1–8 h | m/s |
| uvol | volume with w > 10 m/s, mean 1–8 h | km³ |
| S | peak / mean (1–8 h) max supersaturation | fraction |

Values are differences from the control. **Bold** = outside the noise range.

| run | wpk | P | cold | cpa | w999 | uvol | S_liq pk / mean | S_ice pk / mean |
|---|---|---|---|---|---|---|---|---|
| control (absolute) | 42.1 | 4.449 | −8.21 | 867 | 20.6 | 333 | 0.0195 / 0.0170 | 0.75 / 0.51 |
| noise: fix2 | +1.00 | −0.066 | +0.20 | −16 | −0.67 | +5.8 | +0.006 / +0.0005 | +0.016 / −0.028 |
| noise: smdiv +0.1 % | +0.47 | −0.138 | −0.03 | −9 | −0.20 | +4.5 | +0.002 / −0.0002 | −0.071 / −0.040 |
| noise: smdiv −0.1 % | +0.24 | −0.077 | +0.08 | −4 | −0.49 | +0.9 | +0.012 / +0.0019 | −0.019 / +0.016 |
| option B (layer, no fixer) | **+4.05** | −0.020 | **−0.40** | **+169** | **+0.63** | **+40** | **+0.075** / **+0.009** | **+0.42** / **+0.079** |
| option B + fixer | **+4.04** | −0.108 | **−0.45** | **+49** | **+0.58** | **+20** | **+0.021** / **+0.005** | **+0.31** / **+0.072** |

Storm-total heating by process (J/m², 24 h):
- stock Thompson heating ΔIE: 9.15e6 (final_meter);
- E-consistent heating: 9.85e6, of which Hpe 6.3e5, Lfus 8.9e4, Hke 1.8e3.

Option B is a **PHYSICS CHANGE**. It gives a stronger storm (peak w +10 %, updraft volume +6 to +12 %), a colder and
larger cold pool, and higher peak supersaturation. Precipitation is unchanged within noise. Pointwise RMS
differences are not usable: the round-off control already gives an RMS 24 h rain difference of 2.6 kg/m².

Ash's decision: 0012 is offered opt-in (`config_mp_energy_coupling = 'layer'`), and the default stays stock
(option A). With the default, the series is bit-identical to the series without 0012 (§8). This table is the
justification for offering it.

## 7. Classification

| change (series patches) | class | effect, 24 h |
|---|---|---|
| Thompson 0001–0004, dynamics v2 0005–0007 | BUG FIX (water) | ΔW/W 1.3e-3 → 1e-9 |
| TH8/TH9 0008–0009 (in the MPAS series; held for UFS and other copies) | BUG FIX (water) | 1e-9 → 2e-15 |
| sedimentation export 0010, meter 0011 | INSTRUMENTATION | bit-identical when off |
| layer-local coupling 0012 (option B) | PHYSICS CHANGE (frictional heating of falling water, E's latent heats), opt-in | §6; default stays stock (option A), Ash's decision; §6 is the justification for offering it |
| global energy fixer 0013 | FIXER (labelled), not a fix | reproducible |
| dissipative heating 0014 | PHYSICS CHANGE (KE removed by explicit diffusion and damping returned as heat; option 1 local work, option 2 positive-definite), opt-in | §10; fixer −65 %; stronger updrafts |

Inactive defects logged, not fixed (inactive in this configuration): condensate zeroing above config_microphysics_top
deletes water and latent heat; vertical θ mixing not in flux form (v_theta_eddy_visc2 > 0); Kessler top-layer rdzk on
stretched grids; LBC operator precedence; precipw uses rho_p/(1+qv) on an already-dry density; odd
number_of_sub_steps; IAU/LBC density mismatch with rho_zz_int.

## 8. Deliverable: `proposal/patches/ports/MPAS-conservation/`

There are 14 patches for MPAS-Dev `develop` aa6d8cd69, applied with `git am`; each is labelled in the series README.
With the user's go-ahead, TH8 and TH9 are in this series; they remain held for UFS and every other copy. 0012 and
0014 are opt-in PHYSICS CHANGES whose defaults keep stock behaviour (Ash's decision for 0012).

| patches | content | class |
|---|---|---|
| 0001–0004 | Thompson water closure (= `MPAS-thompson/`) | BUG FIX |
| 0005–0007 | dynamics v2 (positive-definite upwind, config_positive_definite, column-local guard) | BUG FIX |
| 0008–0009 | TH8, TH9 | BUG FIX |
| 0010 | Thompson sedimentation export | INSTRUMENTATION |
| 0011 | energy meter, reproducing sums, restart totals, test heating/cooling (`config_energy_meter`) | INSTRUMENTATION |
| 0012 | layer coupling, option B (`config_mp_energy_coupling = 'layer'`; default `'stock'`) | PHYSICS CHANGE, opt-in |
| 0013 | reproducible global fixer (`config_energy_fixer`) | FIXER |
| 0014 | dissipative heating (`config_dissipative_heating` = 0 / 1 local / 2 positive-definite; default 0) | PHYSICS CHANGE, opt-in |

The generator is `$R/e24/mk_ebud5.py <in.F> <out.F> <Registry in> <out> <level 1|2|3>`; levels 1–3 are 0011–0013.
Each level only adds lines (+474/+151/+34 in the dynamics, +36/+5/+5 in the Registry). 0014 is
`$R/e24/mk_edis.py` (v3) on the 0013 sources (+401/−2 in the dynamics, +11 in the Registry), built as `am14v3` by
`git am` of the exported patch.

| gate | status |
|---|---|
| git am on a fresh aa6d8cd69 through 0011, 0012, 0013; builds | PASS (job 10152081) |
| 0011 / 0012 / 0013 with switches off vs 0001–0009 (24 h closure.nc) | PASS bit-identical, each (job 10152091) |
| 0013 with layer + fixer + meter vs the release candidate | PASS bit-identical (job 10152092) |
| 0012 with layer alone: microphysics + coupling ΔE, 24 h | 0 (−7.1832e5 + 7.1832e5 J/m²) |
| release candidate: meter on vs off with layer + fixer (rc_lf vs rc_lf_meter) | PASS bit-identical |
| release candidate vs the v4 run f4_lf_n16 | PASS bit-identical |
| default namelist, 0012 and 0014 each vs 0001–0011: closure.nc straight and at 7 tasks; 24 h restart file straight and after 12 h + 12 h (249 variables) | PASS bit-identical, all 8 (job 10153963) |
| known-bad for that gate: heating on vs off (closure.nc) | FAIL, as it must (qr max\|d\| 1.0e-2) |
| 0014 switch off with layer + fixer + meter vs 0013 (`dh2_off` vs `s13_lfm`, closure.nc) | PASS bit-identical (job 10153970) |
| 0014 on: 16 vs 7 tasks (closure.nc); straight vs 12 h + 12 h restart (restart file) | PASS bit-identical, both |
| 0014 v3 (options 1 and 2): the same default, off and option-2 gates | PASS (§10; jobs 10155425, 10155426) |

## 9. Closure statement (24 h supercell, 16 tasks; with the series and switches layer + fixer)

| quantity | 24 h change | nature |
|---|---|---|
| dry mass | 0 (exact) | genuine |
| water | −1.6e-16 relative | genuine (needs TH8/TH9) |
| energy, physics + coupling | 0 to 1e-7 J/m²; gate ≤ 9e-6 J/m² per column-step | genuine (option B) |
| energy, dycore: KE removed by explicit diffusion and damping (per-term, §4) | −2.48e5 J/m² (65 % of the dycore's −3.78e5) | DESIGN: dissipation without heating, closed by the labelled fixer; returned as heat with the opt-in 0014 (§10) |
| energy, dycore: remainder (advection, PGF, buoyancy, acoustic steps) | −1.31e5 J/m² (35 %) | **OPEN: not split further, closed by the fixer** |
| energy, total with the fixer | +1.9e-16 relative | by construction |

## 10. Dissipative heating (0014, opt-in)

`config_dissipative_heating` returns the KE that §4 tallies as heat (0 off, the default; 1 local work; 2
positive-definite). The FV3 analogue is d_con. Every tallied term is included: u del2, u del4 and vertical u
diffusion; w diffusion; divergence damping; and the w absorbing layer. θ_m diffusion changes IE, not KE, and Rayleigh u
is off. No term was impractical. The heat is summed over the dynamics substeps and applied once per step, after
microphysics and the coupling, at constant volume (ΔE = q). Nothing is carried across steps.

**Option 1** heats with each term's local work u·δ(ρu)·volume, as in §4. An edge's work goes half to each of its two
cells after a halo exchange; an interface's work goes half to each adjacent layer. The heating is **signed**:
diffusion moves KE as well as removing it, so cells that gain KE cool.

**Option 2** heats with positive dissipation rates in summation-by-parts form. Each inexact term is rescaled per step
so that its reproducing domain sum equals its option-1 work, so the domain heat, and hence the fixer, are option 1's.

| term | positive density | exact when | density / work, 24 h |
|---|---|---|---|
| u del2 (Smagorinsky) | ρν·A·D² at cells + ρν·A·ζ² at vertices (kite shares) | ρν constant (here ν varies) | 1.067 |
| u del4 (+ vertical u, 0 here) | ρν4·dc·dv·(f·(∇D)² + (∇ζ)²) per edge, half to each cell | ρ constant (TRiSK div∘curl = 0 removes the cross term) | 0.999 |
| w del2 | (dv/dc)·ρν·(Δw)² per edge | always (symmetric flux form); not rescaled | 1 |
| w del4 | ν4·A·L²/ρ at cells (L = delsq_w) | ρ constant | 1.001 |
| divergence damping | A·dc·coef·δ′²/(2·dts·ρ·θ_m²), δ′ the substep's ρθ change | proxy | 1.092 |
| w damping | A·g·(ρ·zz)·w² per interface, g = dts·dss/(1 + dts·dss) | the Rayleigh part of the increment | 0.908 |

Without the rescale, option 2 would leave +1.1e3 J/m² for the fixer over 24 h, 0.5 % of the heat. Per-column
rescaling was not adopted: on average 1,381 of 7,056 columns per step (up to 3,801) have a negative net option-1
heat, −1.37e4 J/m² over 24 h, so a per-column rescale would cool them.

Runs (layer + fixer + meter): `dh2_storm` (option 1, v2 build, job 10153970), `d1_storm` (option 1, v3 build),
`dp_storm` (option 2), jobs 10155425/10155426; control `s13_lfm` = the same without heating.

| 24 h, J/m² | option 1 | option 2 | heating off |
|---|---|---|---|
| dycore ΔE | −3.83e5 | −3.78e5 | −3.81e5 |
| heat returned: u diffusion / div damping / w diffusion / w damping | +1.70e5 / +8.5e3 / +3.11e4 / +4.07e4 | +1.67e5 / +8.3e3 / +3.07e4 / +4.06e4 | — |
| heat returned, total | +2.51e5 | +2.47e5 | — |
| fixer ΔE | +1.32e5 | +1.31e5 | +3.81e5 |
| heating closure, max \|ΔE − q\| per step | 1.4e-6 | 1.4e-6 | — |
| local rate, K/day: min / max | −114 / +1176 | 0 / +1102 | — |
| local rate, K/day: rms peak / 24 h mean | 5.6 / 0.52 | 4.9 / 0.42 | — |

The fixer falls by 65 % with either option, and what remains is the §4 remainder (−1.31e5). Each returned term
matches its tally row to within 2 %; the heated flow differs slightly.

Impact against the §6 noise (the same measures and units; control `s13_lfm`, absolute in the first row; the noise
ranges were measured around `final_off`):

| run | wpk | P | cold | cpa | w999 | uvol | S_liq pk / mean | S_ice pk / mean |
|---|---|---|---|---|---|---|---|---|
| control (absolute) | 45.8 | 4.435 | −8.41 | 874 | 21.1 | 361 | 0.037 / 0.020 | 1.05 / 0.55 |
| option 1 (`dh2_storm`) | **+1.12** | +0.007 | +0.07 | **+184** | **+1.15** | **−11** | **+1.00** / **+0.15** | **+2.07** / **+0.36** |
| option 1, v3 build (`d1_storm`) | **+1.12** | −0.001 | +0.07 | **+181** | **+1.15** | **−13** | **+1.00** / **+0.15** | **+2.07** / **+0.36** |
| option 2 (`dp_storm`) | **+1.03** | −0.026 | −0.16 | **+97** | **+1.19** | −4.1 | **+0.99** / **+0.13** | **+2.05** / **+0.29** |

- With either option, precipitation and the coldest cold-pool θ′ stay within noise, and peak w and w999 rise beyond it.
- Option 2 halves the cold-pool area increase (+11 % against +21 %), and its updraft-volume change is within noise.
- The supersaturation peaks are one overshooting-top cell at hour 1: 14.75 km, T 185 K, θ′ −59 K, qv 2.6e-6. The
  control's peak is a cell at 14.25 km and 189 K. At these temperatures S_ice rises about 18 % per kelvin of
  cooling, so the stronger, colder overshoot drives the peak. That is a dynamical response to the heating in the
  updrafts, not heating applied in that cell; option 2 has it too.
- The v3 build's option 1 is the same algorithm as v2. It is bit-identical through hour 3 and differs from step 938,
  starting in the last digit of the dynamics' KE sum. Within one binary, runs are bit-identical at 7 and 16 tasks, so
  this is a rare code-generation difference (the Intel build uses `-O3` with the default fp-model), not an
  algorithm change. Its d1 − dh2 differences are within noise.

0014 is a **PHYSICS CHANGE**: it moves the storm beyond noise and is offered opt-in with the default off. **Option 2
is the recommended form**: it heats everywhere the KE is dissipated and is exact per term per step. Option 1 is kept
for comparison, as the exact local KE work.

A cross-build bitwise claim would need both builds with FMA contraction off. Under ifort, FMA choices can change
when unrelated code in the file is edited.

| gate (0014 v3) | result |
|---|---|
| switch 0 vs 0001–0011: closure.nc straight and at 7 tasks; 24 h restart straight and after 12 h + 12 h | PASS bit-identical, all 4 (job 10155426) |
| switch 0 with layer + fixer + meter vs 0013 | PASS bit-identical |
| option 2: 16 vs 7 tasks (closure.nc); straight vs 12 h + 12 h (restart file) | PASS bit-identical, both (job 10155425) |
| known-bads: option 2 vs option 1; option 1 vs heating off | FAIL, as they must |
| option 1, v3 vs v2 build | not bit-identical from step 938 (above); within noise |
