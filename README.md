# Water, energy and tracer conservation in UFS physics

Measured defects in the UFS physics (ccpp-physics, FV3 and its coupling, Noah-MP), the fixes we propose, and the
evidence behind each one. Written for the developers who own the code. Ash Pera (NOAA GML / CIRES).

**Start here:** find your scheme below, or scan [every defect](#all-defects), sorted by size. Each scheme page lists
every defect in that code, its measured size, the fix, where it stands upstream, and links to the evidence.

## Status (13 November 2026)

- **Water.** In `FV3_GFS_v17_p8_ugwpv1` the physics creates water: +0.25 % of precipitation on the first day at C96,
  +0.45 % at C384. The dynamical core conserves water; the physics and its coupling to the land model do not
  ([proposal](proposals/water_closure_proposal.md)).
- **Energy and tracers.** With every fix on (C96, 24 h), total energy closes to 1.6 × 10⁻¹² W/m² (from +2.08) and
  passive-tracer mass to ~3 × 10⁻¹⁵ per day ([proposal](proposals/conservation_proposal.md)).
- **Upstream.** 8 ccpp-physics PRs posted; 5 approved (#405, #406, #407, #408, #414); none merged. The fixes go in as
  three packages (SAMF/PBL, microphysics, Noah-MP), so regression baselines change three times, not eight
  ([roadmap](upstream/ROADMAP.md)). The plan is filed as
  [ufs-weather-model#3404](https://github.com/ufs-community/ufs-weather-model/issues/3404).
- **TEMPO upstream.** NCAR merged two of our TEMPO fixes into `tempo_v3.3.0` (T1 in NCAR/TEMPO#61, C2 in #62); the
  entry-density fix (C3) is posted as NCAR/TEMPO#63.

## By scheme

| Scheme | Page | Upstream items |
|---|---|---|
| SAMF convection | [samf](components/samf.md) | #401, #405, #408, #414; #403 (not ours) |
| PBL (satmedmfvdifq, MLM, shinhongvdif) | [pbl](components/pbl.md) | #404, NCAR/ccpp-physics#1251 |
| MYNN-EDMF | [mynn](components/mynn.md) | drafted |
| Grell–Freitas | [grell_freitas](components/grell_freitas.md) | drafted |
| Gravity-wave drag and tendency application (TOPT) | [gwd](components/gwd.md) | not posted |
| Thompson microphysics | [thompson](components/thompson.md) | #406 |
| TEMPO microphysics | [tempo](components/tempo.md) | #407; NCAR/TEMPO#61, #62 merged; #63 open |
| GFDL MP v3 | [gfdl_mp](components/gfdl_mp.md) | #413; NOAA-GFDL/GFDL_atmos_cubed_sphere#430, #431 |
| Noah-MP | [noahmp](components/noahmp.md) | #409, #410; NCAR/noahmp#274 |
| NSST and sea ice | [surface](components/surface.md) | not posted |
| FV3 dycore, its coupling to the physics, tracer transport | [fv3](components/fv3.md) | not posted |

Issue and PR numbers without a repository are ufs-community/ccpp-physics. Per-item state, with links:
[`upstream/POSTING.md`](upstream/POSTING.md).

## All defects

Every defect on the scheme pages, in one table. Groups run from crashes to water, energy, tracers, and defects that
change the forecast without breaking a budget. Within a group the largest measured effect comes first: first the
global numbers (share of precipitation, or W/m²), then local or per-event sizes, then defects that were not measured
or did not fire. Unless stated, the case is C96 `control_p8_ugwpv1`, 24 h. Microphysics percentages are of that
scheme's grid-scale precipitation (TEMPO: `control_p8_ugwpv1_tempo`). A row's ID links to its scheme page, which
gives the fix and the evidence. "Drafted" means the text exists but has not been posted; "not proposed" means the
owners have to decide whether the behaviour is wrong.

| Group | ID | Scheme | Defect | Measured effect | Upstream |
|---|---|---|---|---|---|
| Crash | [#401](components/samf.md) | SAMF deep | Once TKE raises `clamt`, the sub-cloud mass flux grows downward; the CFL number is bounded only at cloud base | HAFS global nest, 48 h: 6 of 10 members crash; one-step heating 49–96 K | PR #414 approved (package 1) |
| Crash | [#404 cause 3](components/pbl.md) | PBL (MLM) | `mlmb` can be 0 in an active column, so the scheme writes level −1 | NaN, segfaults, or bottom layers 40–52 K too cold (`mlm` on) | issue #404 open |
| Crash | [#404 cause 4](components/pbl.md) | PBL (MLM) | In inactive columns the mixed-layer means divide 0 by 0 | `control_debug_p8` with `mlm` on traps at step 3 | issue #404 open |
| Crash | [E1](components/surface.md) | NSST | Sea-spray fluxes are explicit and oscillate where the gain exceeds 2 | one 10-day C96 run blew up at day 6.4; 271 oscillating cells in 10 days on `develop` | not posted |
| Crash | [T1 (02b)](components/samf.md) | SAMF | Tracers are stepped explicitly at Courant numbers up to 5; the step is stable only to about 1 | a tracer piles up 184–236× in the lowest layers; ozone one-step error 18 % where C > 2; negative TKE | drafted (round-2 issue 1) |
| Crash | [NCAR#1251](components/pbl.md) | Shin–Hong PBL | The ozone diagnostic sits outside its loops and uses stale indices | bounds-checked builds trap (SCM; not run) | NCAR/ccpp-physics#1251 open |
| Water | [GF 03 (a)](components/grell_freitas.md) | Grell–Freitas | `raincv` includes shallow precipitation only when deep convection is active | shallow-only columns lose 0.281 kg/m²/day but report 0.126 (`rap_control`); the fix raises global precipitation 8.9 % | drafted (round-2 issue 4) |
| Water | [NM2](components/noahmp.md) | Noah-MP coupling | With `frac_grid`, coastal land is stepped twice every step | land gains 3–5 % of global precipitation | drafted (round-1 track 1d) |
| Water | [MLM negative condensate](components/pbl.md) | PBL (MLM) | The explicit update can remove more condensate than a layer holds | 0.14 kg/m²/day of negative water; Thompson turns it into a source of about 3 % of evaporation (`mlm` on) | asked in #404 |
| Water | [GF 03 (c)](components/grell_freitas.md) | Grell–Freitas | Shallow precipitation (Σ `pwo`) differs from the water the vapour tendency removes | −2.5 % (GF's own frame) | drafted (round-2 issue 4) |
| Water | [GFDL02](components/gfdl_mp.md) | GFDL MP wrapper | The wrapper keeps species on `mpdrv`'s updated layer mass; the host rebuilds them on the old one | −1.03 % of MP precipitation (`control_iovr4_gfdlmpv3`) | PR #413 open |
| Water | [C2](components/tempo.md) | TEMPO | Graupel gains are not re-closed after the limiters cut the matching losses | creates 0.86 % (0–6 h), 0.004 % (6–24 h) | fixed: NCAR/TEMPO#62, in `tempo_v3.3.0` |
| Water | [MYNN 01 (a)](components/mynn.md) | MYNN-EDMF | Surface fluxes are multiplied back by a surface density with a typo | +0.85 % of evaporation (`control_p8_mynn`) | drafted (round-2 issue 8) |
| Water | [SA1](components/samf.md) | SAMF | The cloud-base correction subtracts the limited value, not what the updraft took | creates 0.8 % of convective rain (0.97 % at C384); a convected tracer −2.0 % per day | PR #405 approved (package 1) |
| Water | [TH3](components/thompson.md) | Thompson | Graupel gains are not recomputed after the limiters cut the matching losses | creates 0.76 % in the first 6 h, 0.03 % after | PR #406 approved |
| Water | [MYNN 01 (b)](components/mynn.md) | MYNN-EDMF | The dew limiter is zero whenever there is vapour, so downward vapour fluxes are dropped | +0.67 % of evaporation (`control_p8_mynn`) | drafted (round-2 issue 8) |
| Water | [T1](components/tempo.md) | TEMPO | The semi-Lagrangian sedimentation fallback tests `qpi > 0` instead of `< 0` | creates 0.64 % (6–24 h), 0.72 % (0–6 h); the fix lowers grid-scale precipitation 4–5 % | fixed: NCAR/TEMPO#61, in `tempo_v3.3.0` |
| Water | [TH1](components/thompson.md) | Thompson driver | Species go to mixing ratio with the old vapour and back with the new | removes 0.4 % | PR #406 approved |
| Water | [TH1 (driver)](components/tempo.md) | TEMPO driver | The same round trip as Thompson's TH1 | hides TEMPO's own creation: gross error Σ\|R\|/P 1.85 → 0.93 % with the fix | PR #407 approved |
| Water | [C1](components/tempo.md) | TEMPO | Cloud water settling out of the lowest layer mostly leaves no precipitation | removes 0.20 % (0–6 h), 0.14 % (6–24 h) | not proposed (owners choose the form) |
| Water | [TH2](components/thompson.md) | Thompson | Cloud water settling out of the lowest layer is counted in no precipitation total | removes 0.15 % | drafted |
| Water | [C3](components/tempo.md) | TEMPO | Sedimentation uses a density recomputed after heating, with the old layer depth | removes 0.12 % | NCAR/TEMPO#63 open |
| Water | [TH4](components/thompson.md) | Thompson | The same density mismatch as TEMPO's C3 | removes 0.11 % | PR #406 approved |
| Water | [NM1](components/noahmp.md) | Noah-MP driver | Evaporation is handed over with the host's latent heat; Noah-MP removed it with its own | atmosphere gains 0.07–0.10 % of precipitation more than the land loses | PR #410 in review |
| Water | [TH5](components/thompson.md) | Thompson driver | Layer depth comes from `phii`, not the host's layer mass | removes 0.014 % | PR #406 approved |
| Water | [TH5 (driver)](components/tempo.md) | TEMPO driver | The same as Thompson's TH5 | removes 0.011 % | PR #407 approved |
| Water | [NM5](components/noahmp.md) | Noah-MP | Thin snow without layers is zeroed and its water goes nowhere | removes 0.009 % of precipitation from the land | not posted |
| Water | [TH6](components/thompson.md) | Thompson | Negative or tiny hydrometeors are deleted and vapour is floored from nothing | creates 0.002 % | drafted |
| Water | [commit 3](components/tempo.md) | TEMPO | Water below `r1` is deleted in the six check-and-update routines | creates 0.001 % (with T1 fixed) | not proposed (owners choose the form) |
| Water | [NM6](components/noahmp.md) | Noah-MP | `canwater` zeroes canopy water at or below 10⁻⁶ mm | removes 4 × 10⁻⁷ of land precipitation | not posted |
| Water | [TH8](components/thompson.md) | Thompson | Sedimentation out of the bottom counts as precipitation only above a threshold | removes 2 × 10⁻⁷ of precipitation | drafted (round-2 issue 2, with TH9) |
| Water | [FV1](components/fv3.md) | FV3 driver | `prsl` is built with the dycore's single-precision gas constant and inverted with the physics' | 4 × 10⁻⁸ of evaporation (32-bit build) | drafted (track 1c) |
| Water | [TH7](components/thompson.md) | Thompson | Water at or below `R1` is deleted on entry, in sedimentation and as leftover rain | removes 2 × 10⁻⁸ of precipitation | drafted |
| Water | [NM4](components/noahmp.md) | Noah-MP init | At a cold start the snow layers are built from the cell mean, not the land snow | 0.29 kg/m² of land snow lost on the first step | PR #409 in review |
| Water | [NM9](components/noahmp.md) | Noah-MP glacier | Glacier snow is reset to 600 mm every call; the water added or removed goes nowhere | a glacier column −860 mm in 120 days (single-column test) | drafted (round-2 issue 3b) |
| Water | [NM12](components/noahmp.md) | Noah-MP | `combine` tests the entry layer count, so a melting-out pack merges wrongly | per firing −0.10 to +0.16 mm water and −1.1 to −8.5 MJ/m²; fires on 5 × 10⁻⁶ of calls at 720 s, 1.7 × 10⁻² at 3600 s (single-column test) | PR #409 in review |
| Water | [NM3](components/noahmp.md) | Noah-MP coupling | With `frac_grid`, the land snow is overwritten with the cell mean every step | about 0.005 mm per land column per 6 h | PR #409 in review |
| Water | [#403 `diff3d`](components/pbl.md) | satmedmfvdifq | FV3's horizontal diffusion is applied on the PBL's layer mass, so its tendencies no longer cancel | net/gross −2.8 × 10⁻² (T); PBL water −1.3 × 10⁻⁵ kg/m² (`sa3dtke` on) | not ours: answered on #403 and NOAA-GFDL/GFDL_atmos_cubed_sphere#429 |
| Water | [MYNN 01 (c)](components/mynn.md) | MYNN-EDMF | `moisture_check` fills on MYNN's interpolated layer mass, not the solver's | +3.9 × 10⁻⁷ kg/m²/day (`control_p8_mynn`) | drafted (round-2 issue 8) |
| Water | [PBL05](components/pbl.md) | satmedmfvdifq | Surface sources are applied with a different density than the fluxes were made with | +2.6 × 10⁻⁸ kg/m²/day (GFDL v16 suite); zero in P8 | PR #408 approved (package 1) |
| Water | [MYNN 01 (d)](components/mynn.md) | MYNN-EDMF | The solver's density is ideal-gas, not the host's layer mass | rare events up to 5.6 × 10⁻¹³ kg/m² in one step | for #392's wrapper |
| Water | [GF 03 (b)](components/grell_freitas.md) | Grell–Freitas | Mixing-ratio conversions in and out do not match the host's | water and energy inconsistent at about 2r | drafted (round-2 issue 4) |
| Water | [GF 03 (d)](components/grell_freitas.md) | Grell–Freitas | Floors on vapour and condensate create water | small, not separated | drafted (round-2 issue 4) |
| Water | [`prg_rcg`](components/thompson.md) | Thompson | The graupel check counts the unscaled rain–graupel gain; graupel can end negative and be zeroed | not measured (found by reading the code) | drafted (issue owed on #406) |
| Water | [`prg_rcg`](components/tempo.md) | TEMPO | The same as Thompson's; still present in `tempo_v3.3.0` | not measured (found by reading the code) | not proposed |
| Energy | [TOPT](components/gwd.md) | tendency application (also [fv3](components/fv3.md)) | The process-split sum is applied only by a scheme with option 3, and nothing checks that one does | +110 to −142 W/m² in the broken option combinations; `FV3_HRRR_gf_nogwd` never applies radiation or PBL with defaults | drafted (round-2 issue 7) |
| Energy | [MYNN 01b](components/mynn.md) | MYNN-EDMF | The latent heat of filled condensate is counted twice | +8.0 W/m² (`control_p8_mynn`) | fixed in NCAR `main` (e447691); still in `ufs/dev` until #392 merges |
| Energy | [D1](components/pbl.md) | satmedmfvdifq | Dissipative heating is the last substep's TKE dissipation, not the KE the momentum solve removes | +1.43 W/m² | not proposed (owner decision) |
| Energy | [#404 cause 2](components/pbl.md) | PBL (MLM) | MLM tendencies omit density and use the wrong layer's thickness | −1.28 W/m² and +4.4 × 10⁻⁴ kg/m²/day of water (`mlm` on) | issue #404 open |
| Energy | [sa3dtke](components/pbl.md) | satmedmfvdifq | With `sa3dtke`, shear production uses the dycore's deformation, which exceeds the KE the PBL removes | +1.08 W/m² (PBL residual 1.43 → 2.51, `control_p8`) | not posted |
| Energy | [#404 cause 1](components/pbl.md) | PBL (MLM) | Cloud-base smoothing replaces the tendencies with their neighbours' mean | −0.88 W/m² and −6.0 × 10⁻⁴ kg/m² of water (`mlm` on) | issue #404 open |
| Energy | [MYNN 06](components/mynn.md) | MYNN-EDMF | MYNN mixes θ_l, not an energy | 0.47 W/m² | not proposed |
| Energy | [D3A](components/samf.md) | SAMF | Detrained condensate becomes ice with no heat of fusion | −0.44 W/m² (deep −0.42, shallow −0.02) | PR #408 approved (package 1) |
| Energy | [D4n](components/gwd.md) | UGWP-v1 | Non-orographic heating comes from a prescribed launch flux, not the resolved flow | net source +0.335 W/m² | not proposed (option 2 recommended) |
| Energy | [D4](components/gwd.md) | GSL drag | Drag removes KE with no heating | −0.32 W/m² | not proposed (owner decision) |
| Energy | [DY1](components/fv3.md) | FV3 dycore | `d_con` heat is added at fixed δz with c_v of dry air | +0.29 W/m² | drafted (round-2 issue 5) |
| Energy | [GF energy](components/grell_freitas.md) | Grell–Freitas | The driver re-partitions the deep updraft's frozen condensate without its heat | −0.26 W/m² | asked in round-2 issue 4 |
| Energy | [MYNN 04](components/mynn.md) | MYNN-EDMF | Surface sensible heat is applied as a θ flux without 1/Π and with c_pm | applied 16.72 vs reported 16.97 W/m² | not proposed |
| Energy | [S1, S1K](components/samf.md) | SAMF | Condensation is heated at a constant latent heat | deep −0.245, shallow +0.128 W/m² | not proposed |
| Energy | [GFDL07](components/gfdl_mp.md) | GFDL MP | Falling rain and cloud water exchange heat with the ice heat capacity | 0.21 W/m² (`control_iovr4_gfdlmpv3`) | PR #413 open |
| Energy | [D3B](components/samf.md) | SAMF | Momentum transport removes KE with no heating | −0.15 W/m² (deep −0.12, shallow −0.03) | not proposed (owner decision) |
| Energy | [D12](components/gwd.md) | GWD post | PBL and GWD wind increments from the same state are applied together | −0.066 W/m²; up to 47 K/day below 850 hPa | not proposed |
| Energy | [DY2](components/fv3.md) | FV3 dycore | `d_sw` takes the KE about the half-damped wind | −0.0195 W/m² | drafted (round-2 issue 5) |
| Energy | [CMC](components/noahmp.md) | Noah-MP | Canopy evaporation is capped after the energy solve charged it | 0.0148 W/m² | drafted (round-2 issue 3d) |
| Energy | [PL1](components/surface.md) | surfaces | Surfaces book step N's precipitation at step N+1's temperature | −0.0121 W/m² (only with the EP1 option) | not posted |
| Energy | [SI1](components/surface.md) | sea ice | NSST re-flags icy cells, so the ice is stepped twice | −0.010 W/m²; 1.9 % of ice column-steps stepped twice | drafted (round-1 track 1d) |
| Energy | [CP1](components/fv3.md) | FV3 coupling | The physics heats its own layer mass, but the tendency lands on the new δp | −8.6 × 10⁻³ W/m² | drafted (track 1c) |
| Energy | [FL1](components/surface.md) | sea ice | Flooded snow becomes ice at the layers' temperatures | −7.9 × 10⁻³ W/m² | drafted (track 1d) |
| Energy | [R1](components/fv3.md) | radiation (`dcyc2t3`) | Heating rates for the radiation-time layer mass are applied while δp changes | −7.7 × 10⁻³ W/m² | drafted (round-2 issue 6) |
| Energy | [PBF](components/pbl.md) | satmedmfvdifq | PBL condensate transport is treated as vapour by the coupling | −4.9 × 10⁻³ W/m² | not proposed |
| Energy | [DY3](components/fv3.md) | FV3 dycore | `Rayleigh_Super` heats the A-grid KE while total energy loses the D-grid KE | +6.4 × 10⁻⁴ W/m² | drafted (round-2 issue 5) |
| Energy | [FX1](components/fv3.md) | FV3 dycore | The `consv_te` fixer computes its increment with c_v of dry air but applies it at c_vm | −5.5 × 10⁻⁴ W/m² | drafted (track 1c) |
| Energy | [SL2](components/noahmp.md) | Noah-MP | Snow layer merges lose or misplace heat | with CS1, CB1: soil energy residual 3.9 × 10⁻⁴ W/m² | PR #410 and NCAR/noahmp#274 in review |
| Energy | [SG1](components/fv3.md) | FV3 dycore | `fv_subgrid_z` mixes total energy, then relaxes each variable separately | −1.6 × 10⁻⁴ W/m² | drafted (track 1c) |
| Energy | [PBK](components/pbl.md) | satmedmfvdifq | The condensate filler uses a constant latent heat | +4.8 × 10⁻⁵ W/m² | not proposed |
| Energy | [NM11](components/noahmp.md) | Noah-MP | Ground vapour is charged as liquid while the water is taken from snow ice | 0.13–0.61 W/m² over a snow season, up to 78 W/m² in one step (single-column test) | drafted (round-2 issue 3d) |
| Energy | [NM8](components/noahmp.md) | Noah-MP | Noah-MP charges its own latent heats; the vapour arrives with the host's | +0.131 W/m² per land column | not posted |
| Energy | [QR1](components/surface.md) | NSST | Rain per step is used as a rate | rain heat flux × 1000/720 at 720 s (inside NSST) | drafted (track 1d) |
| Energy | [NM7](components/noahmp.md) | Noah-MP | Negative transpiration is clipped, so condensation heats the canopy with no water | 0.024 W/m² per land column | drafted (round-2 issue 3a) |
| Energy | [CS1](components/noahmp.md) | Noah-MP | Snow heat capacity ignores liquid beyond the pore space | −57,043 of 175,101 J/m²/K (Noah-MP v5 test) | PR #410 and NCAR/noahmp#274 in review |
| Energy | [CB1](components/noahmp.md) | Noah-MP | `combo` multiplies per-m³ heat capacities by kg/m² masses | +1,393 and +542 J/m² per merge (Noah-MP v5 test) | PR #410 and NCAR/noahmp#274 in review |
| Energy | [GFDL07 (GFDL copy)](components/gfdl_mp.md) | GFDL MP (GFDL's copy) | The same as GFDL07, in GFDL's own `gfdl_mp.F90` | one 300 s step creates 6 × 10⁻⁵ of the column energy (standalone) | NOAA-GFDL/GFDL_atmos_cubed_sphere#430, #431 |
| Energy | [SI2](components/surface.md) | sea ice | `ice3lay` divides the excess heat by Δt twice | did not fire (thin ice near melting) | drafted (track 1d) |
| Energy | [NP1](components/noahmp.md) | Noah-MP | `phasechange` deletes the heat of a layer that melts out over sub-freezing snow | did not fire | not posted |
| Tracers | [DRY (03b)](components/samf.md) | SAMF; satmedmfvdifq ([pbl](components/pbl.md)) | Chemistry tracers move with moist-air fluxes while each layer keeps its dry mass | a uniform dry tracer drifts 1.1 × 10⁻³ rms in 24 h (SAMF deep 1.0 × 10⁻³, PBL 1.8 × 10⁻⁴) | not proposed |
| Tracers | [F3 (01a)](components/samf.md) | SAMF | Wet deposition is booked and removed with different mass fluxes | −7.4 × 10⁻⁴ per day (scavenged tracer + deposition) | PR #408 approved (package 1) |
| Tracers | [#403 stencil](components/pbl.md) | satmedmfvdifq | The `diff3d` stencil gives a uniform tracer a tendency where the grid stretches | up to 3.7 × 10⁻⁹ /s | not ours: in the #403 comment |
| Tracers | [`dry_tracer_ic`](components/fv3.md) | FV3 initialisation | The initial remap treats a chemistry tracer as a moist ratio | 3.4 × 10⁻⁴ (max) | not posted |
| Tracers | [`dry_tracer_adv`](components/fv3.md) | FV3 transport | The limiter and remap act on each water species separately, so a uniform dry tracer is not kept uniform | 1.8 × 10⁻⁴ per call | not posted |
| Tracers | [`dry_negadj`](components/fv3.md) | FV3 | `neg_adj` borrows water between layers at fixed δp, moving dry air with no tracer | 2.3 × 10⁻⁷ per call | not posted |
| Tracers | [INLQ](components/fv3.md) | FV3 (`inline_q`) | Tracer damping uses different δp on a PE's own cells and its halo | 1.0–1.9 × 10⁻⁹ per day (no RT uses `inline_q`) | drafted (track 1c) |
| Tracers | [FV2](components/fv3.md) | FV3 driver | Tracers go into the physics per `prsl` and come back per layer δp | +3.1 × 10⁻¹⁵ per day (64-bit dycore) | drafted (track 1c) |
| Tracers | [#404 index](components/pbl.md) | satmedmfvdifq | Full-tracer indices are used on the diffused arrays | a passive tracer at slot 7 changes 38 of 44 output files (`mlm` on) | offered in #404 |
| Tracers | [F3 (01b)](components/samf.md) | SAMF | Wet deposition is computed but never exported | budget cannot be closed; no forecast effect | drafted (round-2 issue 9) |
| Forecast | [SAMF08](components/samf.md) | SAMF | Early returns sit before the CA trigger, so a column depends on the others in its block | 90 of 126 output variables differ between 3×8 and 4×6 layouts (`control_p8_mynn`) | PR #408 approved (package 1) |
| Forecast | [SAMF early returns](components/samf.md) | SAMF | The other early returns skip per-column work done later | standalone test: 11 of 12 combinations identical | in PR #408 |
| Forecast | [E2](components/noahmp.md) | Noah-MP | The canopy wetted fraction comes from the ice alone whenever there is any ice | on 45–48 % of wet-canopy steps `fwet` is 0.09 instead of 0.58 | drafted (round-2 issue 2) |
| Forecast | [TH9](components/thompson.md) | Thompson | Ice and snow sedimentation moves an absent species' placeholder as if it were mass | with TH8: land canopy evaporation at 6 h −68 % → −2.9 % | drafted (with TH8) |
| Forecast | [#414 shallow](components/samf.md) | SAMF shallow | The shallow sub-cloud mass flux also grows downward | grows in 357 k of 2.59 M convecting calls, up to 4.09× | not ours: in PR #403 (approved) |
| Forecast | [SAMF32](components/samf.md) | SAMF build | `-DSAMFCNV_32BIT=ON` misses three capgen dependencies | 2 of 5 files single precision | not posted |
| Forecast | [NM10](components/noahmp.md) | Noah-MP | The grid-scale frozen fraction is applied to convective precipitation | turns convective rain on land into snow (phase only) | drafted (round-2 issue 3c) |

Option switches that are off by default (for example the `cpl_water_energy` bits and the Noah-MP energy options) and
the judgement calls are listed on each scheme page, not here.

## Reproduce

- **Patches:** [`patches/README.md`](patches/README.md): one diff per fix against ccpp-physics `ufs/dev`, `git
  format-patch` series, and ports to other copies of the code (NCAR, WRF, MPAS, NOAA-EMC/noahmp) in
  [`patches/ports/`](patches/ports/README.md).
- **Meters:** [`methods/METERS.md`](methods/METERS.md): the in-model budget meters behind every number, which one to
  use for which question, and how to read them. A design for maintained upstream meters:
  [`methods/meter_design.md`](methods/meter_design.md).
- **How we measured, and pitfalls:** water proposal §5 and §8; energy proposal *Method*.
- **Test plan per package** (regression tests, HAFS checks): [`upstream/ROADMAP.md`](upstream/ROADMAP.md).

## Layout

| Directory | What is in it |
|---|---|
| [`components/`](components/) | one page per scheme (start here) |
| [`proposals/`](proposals/) | the full write-ups: water, energy and tracers, round-1 PR set, round-2 issues, triage of what is not yet posted, code audit, literature |
| [`methods/`](methods/) | meters, meter design and prototypes, analysis scripts |
| [`experiments/`](experiments/) | run reports: `conservation/<topic>/report.md` (energy, tracer, surface, suites, red teams), `runs_29oct/` (re-measurements), `hafs_samf/` |
| [`patches/`](patches/) | diffs and patch series, ports to other copies |
| [`upstream/`](upstream/) | posting state, roadmap, PR and issue bodies as posted, replies, per-item test harnesses |

Long documents are split into a short head (`<name>.md`) and a dated archive (`<name>.history.md`); read the head.
Section numbers (`§N`) are stable.
