# Round 2: issue drafts (not posted)

*Bugs held out of round 1 because the fix needs an owner's decision, plus three round-1 fixes moved here by the red
team (R1, TOPT, MYNN; `pr_round1.md`). Each issue asks one question, gives the options with our recommendation, and
offers a tested patch; the PR follows the owners' answer. Open after round-1 track 1a is in review, so owners see one
thing at a time. Measurements: C96 `control_p8_ugwpv1`, 24 h, in-model budget meters, unless stated. "Noise" is the 24-h
difference made by `consv_te` = 0.999 instead of 1 (T rms 0.149 K, ps 8.41 Pa). Patches: `conservation/replay/patches/`
and `proposal/patches/`.*

| # | Repository | Owners | Subject | Patch |
|---|---|---|---|---|
| 1 | ccpp-physics | @JongilHan66 @lisa-bengtsson | SAMF tracer transport at Courant numbers above 1 | 27 |
| 2 | ccpp-physics | Thompson + Noah-MP owners | Thompson surface sedimentation trace and the Noah-MP canopy wetted fraction | 43, 42 |
| 3 | ccpp-physics | @barlage @cenlinhe | Noah-MP: four water–energy decisions | W14, W16, 17r, W18 + 35 |
| 4 | ccpp-physics | @haiqinli | Grell–Freitas loses 30 % of its own precipitation | 50 |
| 5 | GFDL_atmos_cubed_sphere | `dev/emc` maintainers | Three energy bugs in the dycore's heating of dissipated KE | 45 |
| 6 | ccpp-physics (+ SCM, ufsatm) | code managers, DTC | Radiative heating applied to a stale layer mass | 04 |
| 7 | ccpp-physics | @dustinswales + code managers | Process-split tendencies dropped for some `tend_opt` combinations | 26 |
| 8 | NCAR/MYNN-EDMF | @joeolson42 @XiaSun-Atmos | Mass basis of surface fluxes and fills; fill heat counted twice | 47, 48 |
| 9 | ccpp-physics | SAMF owners | Feature: export SAMF's convective wet deposition | 24 |

---

## 1. SAMF tracer transport at Courant numbers above 1

**To:** ufs-community/ccpp-physics. @JongilHan66 @lisa-bengtsson

SAMF updates transported tracers (`ntr` loop, deep and shallow) with an explicit TVD step whose Courant number reaches
5. Stable only to about 1, it overshoots: a tracer that the PBL does not mix piles up 100–200× in the lowest layers
in 24 h. SAMF transports o3 and TKE this way too.

**Measured.** Sub-stepping to donor Courant ≤ 0.5 removes the o3 one-step increment error (median 19 % where the
Courant number exceeds 2) and cuts negative TKE from 13 % to 1.6 % of those columns; tracer mass is conserved to
3 × 10⁻¹⁵ per day. Weather impact: zonal-mean T ≤ 6 mK; 9–13 of 72 cells outside a 4-member spread (3.6 expected);
o3 global mean −1.2 × 10⁻⁶.

**Question.** Is sub-stepping the fix you want (tested, 426 lines in `samfdeepcnv.f`/`samfshalcnv.f`, no interface
change), or would you prefer an implicit or flux-limited update? Should o3 and TKE be sub-stepped too (we did)?

**Related.** The SAMF sub-cloud overshoot issue (`pr_round1_descriptions.md` §8): a CFL problem in T and q below
cloud base. Sub-stepping the tracer transport does not change it.

---

## 2. Thompson surface sedimentation trace and the Noah-MP canopy wetted fraction

**To:** ufs-community/ccpp-physics. @gthompsnWRF @RuiyuSun @AndersJensen-NOAA; @barlage @cenlinhe

Two Thompson bugs whose fix uncovers a Noah-MP one:
- **Thompson:** sedimentation out of the lowest layer counts as precipitation only above a threshold, although the
  mass has left (7.1 × 10⁻¹² kg/m²/s lost); and flux-form ice and snow sedimentation moves the R1 placeholder
  (10⁻¹²) of an absent species as if it were mass.
- **Noah-MP:** `fwet` picks the canopy phase by "any ice", and the ice capacity is ~50× the liquid's, so a trace of
  canopy ice hides the canopy's liquid and stops its evaporation.

**Measured.** Thompson's fix alone sends traces of snow to the land: canopy evaporation −68 % at 6 h, −47 % at 24 h.
With the placeholder fix as well, stock `fwet`: −2.9 % at 6 h. With a mixed-phase `fwet` (new
`noahmp_fwet_opt`, default 0 = stock): both Thompson fixes are at noise from 6 h. The option itself changes the land:

| `noahmp_fwet_opt` | Rule | Canopy evaporation | Land LH |
|---|---|---|---|
| 1 | mass-weighted | +32 % | +1.5 % |
| 2 | larger of the two fractions (monotone: adding water never lowers `fwet`) | +36 % | +1.2 % |
| 3 | dominant phase, as Noah-MP v5 (He et al. 2023) | within a few % of 2 | |

**Question (Noah-MP owners).** Which `fwet` rule should UFS use? We recommend 2; the switch defaults to stock.
**Question (Thompson owners).** OK to ship the two Thompson fixes together, unconditionally, once `fwet` is settled?

---

## 3. Noah-MP: four water–energy decisions

**To:** ufs-community/ccpp-physics. @barlage @cenlinhe

The round-1 Noah-MP PR (#TBD) fixes the bugs that only restore intent. These four each involve a choice; tested patches exist for
all four, and each can be answered separately.

| | Defect | Measured | Our fix | Question |
|---|---|---|---|---|
| a | `canwater` clips negative transpiration (`etran = max(fctr/hvap, 0)`): the condensation heat warms the canopy but no water condenses (13 % of land column-steps) | land latent energy exceeds its water's by 0.023 W/m² per land column | add the condensate to canopy dew (frost when frozen); energy solve unchanged | this, or suppress it in the energy solve (CTSM)? |
| b | glacier snow set by assignment: reset to 600 mm every call, floored at 0.1 mm, thin snow zeroed; the water goes nowhere | one glacier column −860 mm in 120 days (harness); all snowfall on land ice deleted | keep the assignments, book the water as runoff | is the reset intended? The ice part goes into `drain`, which the host reads as liquid: needs a frozen-runoff flux |
| c | `opt_snf = 4`: the microphysics' frozen fraction of grid-scale precipitation is applied to convective precipitation | a trace of grid-scale snow turns convective rain into snow | convective phase from the host's `srflag` (land and atmosphere agree to 1.2 × 10⁻¹⁰ of frozen mass; land means at noise) | adopt the host's criterion (skin T) for convective phase? |
| d | ground vapour charged at `hvap` when `tg` > 0 °C, but taken from snow ice whenever there is snow | creates the fusion heat of the ice sublimated: 0.13–0.61 W/m² over a snow season, up to 78 W/m² in one step | `hsub` with snow; return any remaining phase mismatch to the top soil layer (also used for three canopy charge mismatches) | OK to route the mismatch heat to soil layer 1? Land over snow changes beyond noise (snow cover +0.16 %) |

---

## 4. Grell–Freitas loses 30 % of its own precipitation

**To:** ufs-community/ccpp-physics. @haiqinli

In the GF driver:
- (a) shallow-only columns dry the air but report no precipitation;
- (b) the vapour increment is applied on a different mass basis;
- (c) GF shallow is inconsistent with itself (−2.5 %);
- (d) floors create or remove water.

**Measured** (GF suites, C96, 24 h): GF water residual −0.137 kg/m²/day (−30 % of GF precipitation) → 2.5 × 10⁻¹⁶.
Global precipitation +8.9 %, SH −0.10 W/m², T −0.011 K, rms 1.0–1.4× noise.

**Question.** (a) is a plain bug, but fixing it raises precipitation by 8.9 %. Ship it unconditionally, or behind a
switch (our patch: `gf_closure`, default off)? Separately, GF still leaves −0.26 W/m² of energy because the deep
updraft, the driver and shallow/mid convection partition ice differently; one shared partition would close it. Is
that worth doing?

---

## 5. Three energy bugs in the dycore's heating of dissipated KE

**To:** NOAA-GFDL/GFDL_atmos_cubed_sphere (`dev/emc`; the same code is in `main`). Maintainers.

The `consv_te` fixer removes 0.570 W/m² that FV3 creates. An in-dycore tally attributes it:

| Term | W/m² | Our label |
|---|---|---|
| `d_con` heat added as `dtmp/pkz` at fixed δz with 1/c_v,air: realised ΔT = dtmp/(1−κ), c_p/c_v × the KE returned | +0.2905 | bug (DY1) |
| KE estimate taken about the half-damped wind | −0.0195 | bug (DY2) |
| `Rayleigh_Super` heats A-grid KE at c_v,air with a stale `pkz` | +0.0006 | bug (DY3) |
| adiabatic dynamics + tracer transport | +0.4145 | discretization; no proposal |
| vertical remap; undamped sponge heat | −0.1160 | design |

Confirmed without our meter from FV3's own `ENG Deficit` print.

**Measured.** Fixing DY1–DY3 (plus two immaterial sponge items) moves the fixer from −0.570 to −0.304 W/m²; the
forecast is at noise (T 0.153 K).

**Question.** Our patch puts the fixes behind `dyn_te_exact` (bits 1–16, default 0), with bits 32/64 returning the
remap and sponge terms as a design option. Should the bug bits be unconditional?

---

## 6. Radiative heating applied to a stale layer mass

**To:** ufs-community/ccpp-physics; cc NCAR/ccpp-scm (DTC), NOAA-EMC/ufsatm. Code managers.

RRTMG's heating rates are per the layer mass at the radiation call; `dcyc2t3` applies the same K/s on later steps
while δp changes: −7.65 × 10⁻³ W/m² (Σ|r| 2.70 × 10⁻²) → −8.4 × 10⁻¹⁴ with the fix (store δp at the last SW and LW
calls, scale by δp_rad/δp_now). Forecast at noise.

**Question (sequencing).** The fix needs two new `Radtend` fields in every host. ccpp-physics CI runs capgen against
NCAR/ccpp-scm `main` and ufsatm `develop`, so the host fields must merge first: SCM, ufsatm, and the MPAS host
(#397). Which order do you want, and should we open the SCM PR?

---

## 7. Process-split tendencies dropped for some `tend_opt` combinations

**To:** ufs-community/ccpp-physics. @dustinswales; code managers

The process-split sum (radiation, PBL, GWD) is applied only by a scheme with `tend_opt` = 3, and nothing checks that a
3 follows a 2. Tendencies are dropped for (`tend_opt_pbl`, `tend_opt_gwd`) = (1,1), (1,2), (2,1), (2,2), (3,2);
option 4 discards silently; `FV3_HRRR_gf_nogwd` never applies radiation or PBL with the defaults. Energy residual
+110 to −142 W/m² in the broken combinations, 2.08–3.12 with our fix (apply a pending sum once, before
convection; default 2.09). Default
(2,3) is bitwise.

**Question.** #397 restructures the same cases. Fold the fix into #397, or a separate PR after it? Should option 4
be a CCPP error (our patch) or a warning?

---

## 8. MYNN-EDMF: mass basis of surface fluxes and fills; fill heat counted twice

**To:** NCAR/MYNN-EDMF. @joeolson42 @XiaSun-Atmos (after ufs-community/ccpp-physics#392)

Found in the CCPP copy (`module_bl_mynn.F90`), measured in `control_p8_mynn` and `rap_control`:
- surface fluxes made kinematic with ρ(k=1) are applied back with a separate surface density (+0.85 % of E);
- the vapour-flux limiter `max(qvflux, min(0.9*sqv - 1e-8, 0)/dtz)` is 0 whenever there is vapour, removing every
  negative flux (+0.67 % of E);
- `moisture_check` fills on MYNN's interpolated δp while the solver conserves ρ·dz;
- `moisture_check` adds the fill's latent heat to θ_l and `Dth` counts it again: +8.0 W/m².

Fixed: water +4.5 × 10⁻² → 5 × 10⁻¹⁵ kg/m²/day. The fill-heat fix alone: T −0.063 K, LH +3.1 W/m², ps rms 2.4×
noise.

**Question.** Since ebd5d2d MYNN-EDMF builds `Dth` from the input condensate, so the double count is gone there. Are
the other three still present in `main`, and would you take the fixes there, ahead of #392?

---

## 9. Feature: export SAMF's convective wet deposition

**To:** ufs-community/ccpp-physics. SAMF owners

SAMF computes `wet_dep` per scavenged tracer but never exports it (`Coupling%wetdpc_flux` is GF/`rrfs_sd` only;
GOCART exchanges no deposition), so a chemistry tracer's budget cannot close. Our patch adds a diagnostic bucket
`cnv_wetdep_<tracer>` (matches the in-model meter to 10⁻¹¹), with no effect on the forecast. Wanted?
