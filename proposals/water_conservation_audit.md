# Is moisture conserved in UFS-Chem v1? Code audit and measured budget

Code: Jian He's `dev-am4` (ccpp-physics `f70b191`, fv3atm `a5c4305`, dycore `d4838c3`); suite `FV3_GFS_v17_p8_ugwpv1`
(Thompson, `satmedmfvdifq`, SAMF deep + shallow, Noah-MP, `h2ophys`); case `control_p8_ugwpv1` (24 h, C96 L127,
2021-03-22 06Z, dt 720 s). "Conserved" means total water Σq·Δp/g over the six species changes only by surface
evaporation, surface precipitation or a documented deliberate source. Line numbers below are in this snapshot; the
`ufs/dev` equivalents are in the proposal's Appendix B.

## Status (11 November 2026)

- **Dry air, the dynamical core and the physics → dynamics update conserve water**; **the unmodified physics does
  not** (sizes in *Measured budget*; every defect in *Where water is not conserved*).
- **Proposed set:** SA1, TH1–TH7, NM1–NM11, FV1 (`../patches/`, numbered in application order; 09b is NM2's
  NOAA-EMC/noahmp companion). **TH8 ships only with its placeholder fix TH9, as one unconditional diff in round 2** (`../patches/held/`; round-2 issue 2, with the Noah-MP `fwet` question). With the set the
  model closes water except TH8's sub-threshold term and passes its full regression suite (*Measured budget*).
- **Upstream:** SA1 and TH1, TH3–TH5 are in approved ccpp-physics PRs, NM1, NM3, NM4 in PRs under review; none
  merged; the other fixes are not posted (*Upstream state*).
  The proposal is [`water_closure_proposal.md`](water_closure_proposal.md); posting state
  [`../upstream/POSTING.md`](../upstream/POSTING.md).
- **Open:** TH8 + TH9 wait for Noah-MP's `fwet` rule (TH8 alone sends trace snow to the canopy); the PBL added − booked gap over 10 days and May's
  drift (deferred); whether UFS-Chem PBL-mixes its added tracers (`nvdiff`); the 32-bit tracer write-back bias (no
  minimal fix; 64-bit removes it). Issues 3–7 (NSST spray, Noah-MP canopy wetness, MYNN, GFDL MP v3, Grell–Freitas
  shallow precipitation) are drafted, not fixes.
- **Labels** were renamed by home on 15 Oct (was → now): A→SA1, B→TH1, C1–C3→TH2–TH4, M4→TH5, M1→TH6, M5→TH7, M2→TH8,
  13a→TH9, D–I→NM1–NM6, L→NM7, K→NM8, N→NM9, O→NM10, J→FV1. The history file and `water_closure_references.md` use
  the old letters, and the history's diff numbers are the old ones.

## Measured budget

| Quantity | Result | Runs |
|---|---|---|
| Meters around `fv_dynamics` (incl. `neg_adj3`), `fv_subgrid_z`, the update write (incl. `fill_gfs`), `fv_update_phys` | < 3 × 10⁻⁷ kg/m² per step (32-bit round-off; ~10⁻¹² in 64-bit); `fill_gfs`, `fv_update_phys` never fire | `wb_herc_wbfzcpd`, `wbfzcpd64`, `wbctlp` |
| R_dyn | 0 to 10⁻⁶ per window | same |
| Unmodified physics, total | +0.25–0.29 % of P per 6 h at C96; +0.45 % at C384 (current upstream) | |
| SAMF (SA1) | ~+0.8 % of convective rain | |
| Thompson (TH1–TH4) | ~−0.67 % of grid-scale P | |
| Final tree `patched19` / `patched19m`, total, dt_inner 720 / 150 | 0.00000 per window after the first | `wb_m19_di720`, `_di150` |
| same, metered physics R per 24 h | −5.50e-7 / −2.47e-7 kg/m², one-signed; max column 2.2e-4 / 3.0e-4 (TH8's sub-threshold surface sedimentation) | same |
| same, PBL added − booked | 1.5e-11 / 1.6e-16 of E | same |
| same, 10 d / C384 | 0.00000 days 2–10 / after the first window | `wb_d10_m19`, `wb_c384_m19` |
| same, vs develop | canopy evap +10 %, sublimation +5.7 %, precip −0.7 % (the per-fix signals) | |
| With TH8 as well (`patched18`), physics R per 24 h, dt_inner 720 / 150 | −9.68e-15 / −7.84e-15 kg/m² (max column 1.9e-13 / 2.2e-13); 10 d and C384 0.00000 | |
| Regression, final tree 01–19 + 09b (`$U/p20rt_final`) | 234/234 PASS (34 restart, 17 decomp, 14 threads, 1 MPI); no crash/NaN/FPE/FATAL/PT | jobs 10125027, 10127943, 10130763 |
| Passive tracers, physics with SA1 | 10⁻¹⁸ of M | `wb_herc_tr_*` |
| Passive tracers, SAMF deep without SA1 | −0.28 / +0.041 %/yr (profile trpa / 3-D trpb), persistent | same |
| Passive tracers, 32-bit physics → dycore write-back | −0.7e-3…−4.1e-3 %/yr, one-signed; ±5e-15 in 64-bit | same |

## Upstream state (11 November 2026)

| Fixes | Where |
|---|---|
| SA1 | ufs-community/ccpp-physics#405, approved; package 1 (NOAA-EMC/ufsatm#1156, ufs-community/ufs-weather-model#3408 draft) |
| TH1, TH3, TH4, TH5 | #406, approved; TH1's TEMPO twin #407, approved; package 2 |
| NM3, NM4 | #409, in review; package 3 |
| NM1 | #410 (stacked on #409), in review; package 3 |
| TH2, TH6, TH7 | not posted: round 1e, each with a second form ([`pr_round1.md`](pr_round1.md)) |
| NM2 (+ 09b) | not posted: round 1d, held on a HAFS crash |
| FV1 | not posted: round 1c (GFDL_atmos_cubed_sphere `dev/emc`) |
| NM5–NM11 | not posted: later rounds ([`round2_issues.md`](round2_issues.md), [`triage_unposted.md`](triage_unposted.md)) |
| TH8 + TH9 | one unconditional diff; round-2 issue 2, not posted |

## Where water is not conserved

Line numbers in the v1 snapshot (`ufs/dev` equivalents: proposal Appendix B). Sizes are without the fix.

| | Location (v1 snapshot) | Effect | Fix and result |
|---|---|---|---|
| SA1 | SAMF deep `samfdeepcnv.f:2378-2389` (kb, jmin), tracers `:2463-2472`; shallow `samfshalcnv.f:1818-1841` | cloud-base "double counting" correction subtracts the flux-limited `tem1` while the updraft took `qo(kb)` (`:1510`, `:2016`) | cloud-base face carries `qo` (SA1), subtraction uses it; convection +0.78 % → 0.00 % of convective rain, layer kb unchanged |
| TH1 | `mp_thompson.F90:574-581` (÷(1−q_v,old)), `:783-790` (÷(1+r_v,new)); host rebuilds mass as pre-physics (dry + vapour) thickness × q (`atmosphere.F90:1616`, basis `:2141-2180`) | each species scaled by (m_d+m_v,old)/(m_d+m_v,new) | convert back with the input `spechum`; Thompson −0.67 % → −0.30 % |
| TH2 | `module_mp_thompson.F90:4049` | cloud water settling out of the lowest layer not counted as precipitation; cloud sedimentation in one full DT (others substep) | count it, substep it; → −0.15 % |
| TH3 | `:3030`, `:3151-3197` | rain–ice and cold rain–snow collection rescaled without re-closing graupel (a source, mostly during spin-up) | re-close after the limiters, snow gain capped at the rain loss; with TH2 → −0.18 % (6–24 h); −0.76 % of P_grid in 0–6 h |
| TH4 | `:3388`, `:3664`, `:3747` | `rho` recomputed after latent heating; sedimentation then runs in a frame ~ΔT/T off the host's layer mass | keep the entry density for mass; → −0.07 % (split); total −0.003 % of P |
| TH5 | driver `mp_thompson.F90:600` | `dz` from `phii`, computed before convection heats the column | `dz` from `prsi` with Thompson's ρ: +0.014 % of P_grid → 0 |
| TH6 | `:4226-4294`; vapour floor `MAX(1e-10, …)` | end-of-step clips and floors (≤ 10⁻¹² → 0); vapour floored by creating water | exchange with vapour; refill the vapour floor from the layer's condensate, then column vapour: +0.002 % → 0 |
| TH7 | `:2248-2324` (entry), `:3341` (leftover rain), `:6273, 6457` (`semi_lagrange_sedim`) | water ≤ R1 deleted | to vapour; physics −6.2e-8 → −4.3e-15 kg/m² per 24 h |
| TH8 | `:3993, 4087, 4116, 4146` | lowest-layer sedimentation counted as precipitation only above `R1·rr_min` | count all: physics −1.46e-7 → −1.6e-8 kg/m² per 6 h; **on hold** (placeholder trace → Noah-MP snow) |
| NM1 | `noahmpdrv.F90:1254` evap = LH/2.5e6; land debits LH/2.5104e6 or LH/2.844e6 (`module_sf_noahmplsm.F90:186-187, 869, 2208-2226, 7310-7316`) | atmosphere gains 1.0042× the water unfrozen land loses, 1.138× over frozen ground or canopy | pass `ecan+etran+edir`; gap → 0.00 % |
| NM2 | `GFS_surface_loop_control_part2.F90:50`; `noahmpdrv.F90:697` | with frac_grid, coastal land stepped twice per step | land once per step: +3–5 % of global P → 0 |
| NM3 | `GFS_surface_composites_pre.F90:229` | land snow overwritten with the cell mean every step | keep `weasd_lnd` |
| NM4 | `GFS_phys_time_vary.fv3.F90:487, 599` | cold-start snow layers from cell-mean `weasd` | `weasdl`/`snodl`: −0.29 kg/m² → 0 |
| NM5 | `module_sf_noahmplsm.F90:945, 2045, 8162` | thin snow without layers deleted | to soil ice: errwat −15.6 mm → −0.014 mm |
| NM6 | `:7328, 7337` (`canwater`) | canopy water ≤ 1e-6 mm deleted | to the ground with rain/snow: → −1.2e-8 mm |
| NM7 | `:7312, 7320` (`canwater`) | negative transpiration heat with no water (energy) | dew/frost: −0.023 → +0.0012 W/m² (canopy cap left) |
| NM8 | `module_sf_noahmplsm.F90:193-195`; glacier `:23-25` | Noah-MP's own latent heats (energy) | host constants: +0.131 W/m² → 0 |
| NM9 | ufs/dev `module_sf_noahmp_glacier.F90:2653` (reset), `:357`, `:3347`; `noahmpdrv.F90:960` (floor) | glacier snow set by assignment | book as runoff: −860 mm/120 d → 2.4e-13 (harness); ice in `drain` (FIXME) |
| NM10 | ufs/dev `module_sf_noahmplsm.F90:1094-1104` | grid-scale fpice applied to convective precipitation | convective phase by temperature (phase, not water); `fwet` switch → issue 4 |
| FV1 | `fvGFS/atmosphere.F90:2241` | prsl with float32 `rdgas` | `con_rd`, `con_fvirt`: PBL gap 4.1e-8 → 5e-16 of E |
| — | `h2ophys.f:125-129` | deliberate relaxation to a zonal climatology above 100 hPa | by design; ≲ 10⁻⁴ of column water |

## Conservative (code)

- **Dry air:** the physics update rebuilds delp as old dry mass + new water mass (`atmosphere.F90:1625-1629`).
- **Physics → dycore:** every advected tracer is returned as mass and divided by the new delp, so a tracer the physics
  leaves alone keeps its mass (`:1616, 1629`). `fv_update_phys`'s delp branch is not executed (no `q_dt`).
- **Dycore:** flux-form horizontal transport; the `kord_tr=9` remap conserves q·delp; `fillz`, `neg_adj3` and
  `fill_gfs` conserve the column; `consv_te` changes temperature only. No dry-pressure transport switch exists.
- **PBL** (`satmedmfvdifq`): implicit diffusion, mass-flux updraft/downdraft and subsidence are flux-form; all six
  species are diffused; the only boundary exchange is surface vapour; negative fixes borrow within the column.
- **Interstitials:** copies and linear updates only.

## Relevance to the GHG work

- Measured with passive tracers (*Measured budget*): with fix SA1 the physics conserves tracer mass to 10⁻¹⁸; without
  it SAMF deep changes it by −0.28 or +0.04 %/yr depending on the profile, the size of May's +0.25–0.65 %/yr (different
  FV3 branch). v1's dycore ≤ 10⁻⁴ %/yr; the 32-bit write-back −0.001 to −0.004 %/yr, one-signed.
- Open for UFS-Chem's own configuration: the write-back bias and whether added tracers are PBL-mixed (`nvdiff`).

## Finding register

Each finding below is recorded in full, with its runs and scripts, in the history file's Status section.

| Finding | Answer | Status |
|---|---|---|
| Earlier stages (SA1 + TH1–TH4; + TH5, TH6, NM1) | −0.005 % of P at C96; < 10⁻⁶ kg/m² per 6 h with TH5, TH6, NM1 | superseded by the final set |
| TH5 first form (host gas constants for Thompson's ρ) | +1 × 10⁻⁵ residual | superseded: Thompson's constants; inner-loop depth from host `dm` |
| Output `dpres` = delp·(1 − condensate) | spurious "dynamics loss" −3…−6 × 10⁻⁵ kg/m² per 6 h; budgets re-run with W from dpres/(1 − condensate) | current |
| TH3 is mostly a spin-up fix | −0.76 % of P_grid in the first 6 h, ~−0.03 % after | current |
| Per-scheme split resolution | resolves build differences, not absolute levels below ~10⁻⁴ kg/m² per 6 h | current |
| Cold start (`coldstart_trace.py`) | IC on `orog_raw`, model on `orog_filt`: −0.0024 kg/m²; fix on the IC side or `USE_GFS_ZS` | current; not proposed |
| NM1 verified exactly | land–atmosphere gap +4.5…+6.9 × 10⁻⁴ kg/m² per 6 h → 0 | current |
| NM2–NM5 (land storage meter) | coastal re-step +3.3–5.3 % of P; snow overwrite; init −0.29 kg/m²; thin snow −15.6 mm → −0.014 mm | current |
| NM6 first form (via `ecan`) | left the latent heat unpaid (≤ 3.5e-3 W/m² at a point) | superseded by NM6 final (to rain/snow) |
| Physics in double precision; TH7, FV1 | TH8 93 % of the −1.46e-7 residual; TH7 → −4.3e-15 per 24 h; FV1 PBL gap 4.25e-8 predicted, → 1.6e-16 | current |
| NM8, NM7 (energy side) | +0.131 W/m² → 0; −0.0228 → +0.0012 W/m² (canopy cap left, documented only) | current |
| Negative hydrometeors at Thompson's exit | 2.21e-5 → 1.26e-8 kg/m² per 24 h, folded into diff 03 | current |
| NM9 glacier | reset deletes glacier snowfall; booked as runoff, ≤ 2.4e-13 mm (harness); v1 has no reset | current |
| Forecast impact (red team, 9 bit-perturbed IC pairs) | beyond noise: SA1 first form, NM1, NM2, NM3, NM4, TEMPO T1, TH8 | current |
| NM10 and TH8's placeholder fix | NM10 phase within noise; the `fwet` part is issue 4; TH8 held with TH9 (user, 15 Oct) | superseded: one unconditional diff for round 2 (conservation series row 43, 18 Oct) |
| Other red-team findings | sublimation at hvap above 0 °C, canopy cap, MYNN qfx from LH, glacier `waxy`, TH6/TH7 edge cases | documented, not fixed |
| Step-771 blow-up (v1, 10 d) | NSST sea-spray explicit instability in a TC eyewall; a cap is not proposed | current; issue 3 |
| Daily jump at kdt = 120n+1 | gcycle sea-ice `tisfc` reset → Courant ~1.8 cloud sedimentation → vapour floor; fixed by diff 03's substepping | current |
| Tracer write-back bias | round-to-nearest in `atmosphere_state_update`; no minimal fix, 64-bit removes it | current |
| "Open: final `patched18` runs and regression suite" | done as `patched19` and `p20rt_final` | superseded |

## Where things are

- Proposal: `water_closure_proposal.md`; diffs: `../patches/`; scripts: `../methods/scripts/`. Literature and upstream status: `water_closure_references.md`.
- Hercules runs: `/work2/noaa/co2/ash/ufs-chem-v1/rt/wb_herc_*` (v1 snapshot variants) and
  `/work2/noaa/co2/ash/ufs-chem-v1/upstream/rt/wb_*` (upstream, C96 and C384). Variant source trees:
  `/work2/noaa/co2/ash/ufs-chem-v1/variants/` (snapshot; `wbdev` = the fast dev tree, `wbtr*` tracers) and
  `…/upstream/patched*/` (upstream: `patched19` = develop + the final set (`patches/final19/`), `patched19m` metered;
  `patched18` the earlier final with TH8 (`patches/final18/`); older `patched17*` carry SA1's first form). Final runs
  `…/upstream/rt/wb_m19*`, `wb_d10_m19`, `wb_c384_m19`; regression `$U/p20rt_final`, triage `$U/triage_apera/`.
  SCM build: `/work2/noaa/co2/ash/ufs-chem-v1/scm/`.
- Private regression baselines `$U/p20rt_suite/stmp/apera/FV3_RT/REGRESSION_TEST` (564 GB): staged for deletion.

Full previous text, every dated finding with its runs and scripts:
[`water_conservation_audit.history.md`](water_conservation_audit.history.md).
