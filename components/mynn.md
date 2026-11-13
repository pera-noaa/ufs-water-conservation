# MYNN-EDMF (`module_bl_mynn.F90`, `mynnedmf_wrapper.F90` in ccpp-physics; `module_bl_mynnedmf.F90` in NCAR/MYNN-EDMF)

**Status (13 November 2026).** MYNN-EDMF creates water: its surface fluxes are applied with a different density than
they were made kinematic with, its dew limiter removes every downward vapour flux, and its filler uses the wrong layer
mass (2–3.5 % of precipitation in the MYNN suites). The ccpp-physics copy also counts its fill heat twice. Nothing is
posted. Round-2 issue 8 is drafted and must be retargeted to NCAR/MYNN-EDMF `main`, where the double count is already
fixed and (a)–(c) remain. [#392](https://github.com/ufs-community/ccpp-physics/pull/392) (open) replaces the vendored
copy with that submodule. Open: the energy options MYNN 04 and 06 (default off) and the TKE/KE accounting gap.

## Defects and fixes

| ID | Defect | Measured effect (case) | Fix | Upstream | Evidence |
|---|---|---|---|---|---|
| MYNN 01 (a) | Surface fluxes made kinematic with ρ(k=1) are multiplied back by a surface density `rhosfc` that has a typo. | +0.85 % of evaporation (C96 `control_p8_mynn`, 24 h) | `rhosfc = rho(kts)` (also makes heat and drag match the reported `dtsfc1`, `dusfc1`). 01 (a–d) together: water +4.53 × 10⁻² → −5.5 × 10⁻¹⁵ kg/m²/day; LH +0.56 W/m², T2m −0.021 K, ps rms 1.19× noise. | round-2 issue 8 drafted, not posted; present in NCAR `main` @11f6bc1 and `ufs/dev` | [conservation §10](../proposals/conservation_proposal.md#10-other-suites-mynn-edmf-gfdl-mp-v3-grellfreitas), [suites §3](../experiments/conservation/suites/report.md#3-e3-mynn-edmf-fv3_gfs_v17_p8_mynn-also-fv3_rap), [r2_8_mynn.md](../experiments/runs_29oct/r2_8_mynn.md) |
| MYNN 01 (b) | The dew limiter `max(qvflux, min(0.9*sqv-1e-8, 0)/dtz)` is 0 whenever there is vapour, so every downward vapour flux is removed while the surface books it. | +0.67 % of evaporation | `-max(0.9*sqv-1e-8, 0)/dtz`, the bound its comment describes. | as (a) | [suites §3](../experiments/conservation/suites/report.md#3-e3-mynn-edmf-fv3_gfs_v17_p8_mynn-also-fv3_rap), [mynnred](../experiments/conservation/mynnred/report.md) |
| MYNN 01 (c) | `moisture_check` fills on MYNN's interpolated δp while the solver conserves ρ·dz (in `main`: on the host δp). | +3.9 × 10⁻⁷ kg/m²/day (p8_mynn), −1.3 × 10⁻¹⁰ (rap) | Pass ρ·dz. | as (a); in `main` in a changed form, size there not measured | [r2_8_mynn.md](../experiments/runs_29oct/r2_8_mynn.md) |
| MYNN 01 (d) | The solver's ρ is ideal-gas, not Δp/(g·dz), with the host's non-hydrostatic dz. | rare events up to 5.6 × 10⁻¹³ kg/m² in one step | ρ = Δp/(g·dz) in the wrapper, for the solver only; at noise. | wrapper part, to go on #392's wrapper | [suites §10.4](../experiments/conservation/suites/report.md#104-mynnred-corrections) |
| MYNN 01b | `moisture_check` adds the latent heat of filled condensate to θ_l, then `Dth` counts it again. | +8.0 W/m² spurious heat (fill 0.28 kg/m²/day; p8_mynn) | v2: call `moisture_check` after `Dth` with a scratch θ, so liquid, ice and snow fills count once → 0; T −0.063 K, LH +3.12 W/m², ps rms 2.37× noise. | fixed in NCAR `main` by e447691 ([NCAR/MYNN-EDMF#84](https://github.com/NCAR/MYNN-EDMF/issues/84)); still in `ufs/dev`'s vendored copy until #392 merges | [mynnred](../experiments/conservation/mynnred/report.md), [r2_8_mynn.md](../experiments/runs_29oct/r2_8_mynn.md), [row 48](../experiments/conservation/replay/patches/48_MYNN01b.diff) |
| MYNN 04 | Surface sensible heat is applied as a θ flux without 1/Π and with c_pm. | applied 16.72 vs 16.97 W/m² reported (p8_mynn) | `mynn_sfc_heat` (default off): applied = reported; noise (0.9–1.2×). | not proposed (proposal only) | [suites §3](../experiments/conservation/suites/report.md#3-e3-mynn-edmf-fv3_gfs_v17_p8_mynn-also-fv3_rap), [row 51](../experiments/conservation/replay/patches/51_MYNN04.diff) |
| MYNN 06 | MYNN mixes θ_l, not an energy. | θ_l-equation gap 0.47 W/m² | `mynn_mix_sl` (default off, opt-in): → 2 × 10⁻⁹; SH −0.68, LH +1.75 W/m², T2m +0.068 K, rms 1.3–1.5× noise. | not proposed (proposal only) | [suites §10.2](../experiments/conservation/suites/report.md#102-design-energy-gaps), [row 53](../experiments/conservation/replay/patches/53_MYNN06.diff) |

## Not proposed, or a judgement call

- **TKE/KE accounting.** After 01 and 01b the remaining frame-P "gap" is TKE-dissipation heating (2.21 W/m²) against the
  mean-flow KE loss (−2.27): the same choice as satmedmfvdifq's D1 ([pbl.md](pbl.md),
  [conservation §13](../proposals/conservation_proposal.md#13-what-remains)). `dheat_opt = 1` is hard-wired.
- **Retargeting issue 8:** ask NCAR to take (a)–(c) in `main` (a three-line port, `git apply --check` passes, not compiled
  or run) so #392's submodule pointer carries them; propose the wrapper half (d) on #392. Drop the 01b ask and the
  "+8.0 W/m²" figure, which does not apply to `main` ([r2_8_mynn.md](../experiments/runs_29oct/r2_8_mynn.md)).
- **01b v1 is withdrawn:** a scratch copy before the call dropped the heat of a snow fill; v2 moves the call after `Dth`.
  v2 is correct for both the CCPP form and the NCAR `main` form.
- **Impacts are area- and mass-weighted.** The older unweighted 01b figures (T −0.049 K, LH +3.19 W/m², ps 2.42×) are
  superseded ([conservation §14](../proposals/conservation_proposal.md#14-corrections)).
- **MYNN 04 is a switch** because `flt` also feeds the surface-layer stability (`rmol`, `fltv`).
- **`sfcdif4`** (MYNN surface layer) still derives the moisture flux from latent heat, so water fix NM1 is incomplete
  there; no patch ([water §7](../proposals/water_closure_proposal.md#7-what-remains)).
- **Not measured:** `main`'s 68d1af7 (input condensate clipped at entry, `moisture_check2` removed) and the open
  MYNN-EDMF#85 (mass-flux cloud ice booked as vapour). MYNN smoke and chemistry mixing were not exercised; with
  `mix_chem` off MYNN never touches the passive test tracers.

## Reproduce

- Patches: rows 47, 48, 51, 53 of the [series](../experiments/conservation/replay/SERIES.md) (= `suites/patches/01_`,
  `01b_`, `04_`, `06_`); the port of 01 to NCAR `main` is inline in [r2_8_mynn.md](../experiments/runs_29oct/r2_8_mynn.md).
- Meter: the suites meter, `experiments/conservation/suites/meters/01_suites_meter.diff`
  ([`../methods/METERS.md`](../methods/METERS.md)); the offline `moisture_check` replay in `mynnred/tools/`.
- Runs to compare: [suites §3](../experiments/conservation/suites/report.md#3-e3-mynn-edmf-fv3_gfs_v17_p8_mynn-also-fv3_rap)
  gate table (`control_p8_mynn` and `rap_control`, C96, 24 h, `-no-fma`, each with its own `consv_te` 0.999 control).
- RT: none (in no posted package). Gates: meters passive, switches off inert, 3×8 = 4×6, restart 12 + 12 h, all bitwise
  ([suites §10.5](../experiments/conservation/suites/report.md#105-final-gates-x10m10--no-fma)).
