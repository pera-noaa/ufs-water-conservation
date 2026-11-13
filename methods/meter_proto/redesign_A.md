# Option A redesigned: a driver-level budget meter with owner-declared sources

Review of the host-meter prototype (`ufs/GFS_budget.F90`, `apply_meterproto.py`) against [`results.md`](results.md), and
a replacement design. Scope and gates are those of [`../meter_design.md`](../meter_design.md).

## Status

| | |
|---|---|
| **Verdict on A as built** | Correct where tested: equals C's per-call sum to 1e-17 kg/m², answer-neutral (0 of 3402), layout- and thread-invariant. Not mergeable as is: FV3-only call sites, a window rule that ignores `fhzero_array` and the IAU-centre reset, always-allocated arrays, a one-off photochemistry export, and the flux list in the meter |
| **Proposal (A2)** | Bracket in `CCPP_driver.F90` inside the threaded chunk loop; close windows at the call that zeroes the diagnostic buckets; read only the boundary terms every suite already books (E `dqsfci`, P `rain`); every other source is written by its owner into one cumulative, standard-named **declared-change counter** per quantity; add diag_table residual maps |
| **Main departure** | The meter holds no process knowledge beyond E and P; sources are counters written where they are applied, differenced like the state, so B and C reuse them unchanged |
| **First PR** | ufsatm: new `ccpp/driver/GFS_budget.F90` (~300 lines), ~12 lines in `CCPP_driver.F90`, ~30 in `GFS_typedefs.F90/.meta` and `GFS_diagnostics.F90`; ccpp-physics: one optional argument in `GFS_photochemistry`. No `atmos_model.F90` edit, no suite edit |
| **Cannot do** | Attribute below whole physics. That stays with B or C, which reuse A2's counters, reduction and line writer |

## 1. Option A as built

**What it gets right (measured, control_p8 C96, 24 h, 32-bit dycore).**
- Whole physics with no suite edit, and nothing is lost by bracketing at the host: C's sum over all calls − A's ΔW is
  1e-17 (fix) / 1e-16 (dev). Its own snapshots survive `qgrs` and `gq0` being rewritten outside the bracket.
- Detects: physics residual +1.77e-3/+1.74e-3/+1.68e-3 (dev) vs −1.63e-3/−1.56e-3/−1.69e-3 (fix) per 6 h; total vs an
  independent offline history budget 3e-8 to 4e-8 (fix).
- Passive and reproducible: 0 of 3402 variables differ on vs off; 0 `BUDGET` lines differ for 1 thread 3×8 vs 2 threads 3×4.

**What it cannot do.**
- **Attribute.** dev's +1.77e-3 is SAMF +3.4e-3 and Thompson −1.6e-3 cancelling; the whole-physics number understates
  the larger defect twofold. `sum|r|` cannot be relied on to unmask it, since both act in precipitating columns.
- **Go fatal on today's trees.** The fix tree carries the Thompson leak (−1.6e-3, ~0.6 % of P_ls), 1600× the design's
  1e-6 fatal threshold; the 32-bit `non_physics` residual (1e-7 to 9e-7 per window) sits at 0.9× of it.
- **Say anything per column outside physics.** `non_physics` max |column| is ~70 kg/m² (transport is not column-local).
- **Separate the stochastics step, IAU and the `cplchm` import** from the dycore: all are lumped into `non_physics`.

**What a maintainer would push back on.**

| Prototype | Push-back | A2 |
|---|---|---|
| 3 calls in `atmos_model.F90`, serial, outside the OpenMP region | FV3-host only; MPAS gets nothing; serial cost | calls in `CCPP_driver.F90`, per chunk, threaded |
| Window `mod(kdt, nwin)`, `nwin = nszero` frozen at init | buckets are zeroed at `mod(kdt−1, nszero) == 0` with the *current* `nszero` (changes at `fhzero_fhour` with `fhzero_array`) and at the IAU window centre (`CCPP_driver.F90` ~L135–146) | window closed at that same call |
| 5 `Intdiag` arrays always allocated (`apply_meterproto.py`), each a new standard name | memory in every run; names not shared with CAM-SIMA | allocated only when on; `optional` + `active` (capgen-v1 probe) |
| E = `dqsfci/hvap` in the meter | the applied flux for 5 PBL schemes only; satmedmfvdifq differs by ~4e-8 of E; MYNN books a clipped flux, unmeasured. 26 of 56 suites (MYNN) do not run `GFS_PBL_generic_post`; `mynnedmf_wrapper` books `dqsfci_diag` itself | kept as the declaration (it is the host contract every PBL fills); the gap is reported as a finding against the scheme, not compensated in the meter; MYNN suites report-only until measured |
| `GFS_photochemistry` gets a bespoke `budget_h2ophys` and a new `prsi` input | a one-off ccpp-physics edit for a 1.24e-7 term; `dp` is already an argument | adds to the generic counter using the existing `dp`: the pattern every later source follows |
| `dtf == dtp` is `FATAL` at init | switching on a diagnostic must not abort a run | line flagged `not covered: dtf/=dtp` |
| Two `mpp_reproducing_sum` per mean (~20 collectives per window), (i,j) packing via `Atm_block` | FV3-specific; the EFP sum is order-independent, so the (i,j) map buys nothing | pack (ncols,1); area sum once at init; one `mpp_efp_list_sum_across_PEs` per window |
| One fatal threshold, physics only, `mpp_error` inside the meter | `non_physics` needs a precision-aware threshold | per-segment thresholds; `errflg` through `CCPP_step`'s `ierr` (the Noah-MP precedent's path) |
| stdout only | each user writes a parser; no map to find a leak | stdout + diag_table maps (no cost unless requested) |

## 2. Proposed design (A2)

**Call sites, all in `ccpp/CCPP_driver.F90`** (shared by FV3 and MPAS; `atmos_model.F90` untouched):

| Where | Call | Effect |
|---|---|---|
| `physics_init`, after `ccpp_physics_init` | `budget_init(errmsg, errflg)` | read switches, allocate when on, area sum, print configuration and coverage |
| `timestep_init`, right after `GFS_Intdiag%phys_zero` | `budget_window_end(errmsg, errflg)` | snapshot W(`qgrs`); close `non_physics`; reduce, print, check; zero |
| chunk loop, before `phys_ps` (FV3) or `physics` (MPAS) / after `phys_ts` | `budget_begin(SEG_PHYS, lb, ub)` / `budget_end(SEG_PHYS, lb, ub)` | physics segment per chunk |
| chunk loop, `stochastics` group | `budget_begin/end(SEG_STOCH, lb, ub)` | SPPT/SHUM/CA measured, not labelled "not covered" |
| `physics_final` | `budget_final()` | report a partial last window, flagged |

- **Windows equal the history buckets by construction**, including `fhzero_array` and the IAU-centre reset, because they
  close at the same statement. The snapshot taken there and the next physics-begin snapshot read the same `qgrs`, so
  their difference must be exactly 0: a free per-step check that nothing writes `qgrs` between them.
- **Segments:** `physics`, `stochastics`, `non_physics` (dycore, state update, IAU, `cplchm` import, r4 storage).
- **Storage:** host-module arrays in `GFS_budget` (host code, not a scheme), per column, written only for `lb:ub` by
  the owning thread. Accumulators are not restarted; the first window after a restart is flagged `partial`.

**Interfaces.**

```fortran
module GFS_budget                                     ! ccpp/driver/GFS_budget.F90
  integer, parameter, public :: SEG_PHYS = 1, SEG_STOCH = 2
  public :: budget_init, budget_begin, budget_end, budget_window_end, budget_final
  ! quantity q: tracer index list + weight; water = indices from ntqv..nthl present (Zhao-Carr 2, NSSL+hail 7)
  subroutine colint(q, lb, ub, w)                     ! sum_k sum_m q(i,k,idx(m))*(prsi(i,k)-prsi(i,k+1))/g, real(8)
```

Switches go in `gfs_physics_nml` so the flag can carry a standard name for capgen's `active`: `budget_meter`,
`budget_tracers`, `budget_tol_report(3)`, `budget_tol_fatal(3)` (per segment, kg/m² per window).

**Declarations: who owns what.**

| Term | Source | Owner |
|---|---|---|
| E | `GFS_Intdiag%dqsfci/hvap·dtp` | the PBL scheme that books it: `GFS_PBL_generic_post` (28 of 56 suites) or `mynnedmf_wrapper` (`dqsfci_diag`; that it maps to `Intdiag%dqsfci` is to verify) |
| P | `GFS_Intdiag%rain` (m per step, `rainc + frain·rain1`) | `GFS_MP_generic_post` (55 of 56 suites; not `MPAS_RRFS`) |
| any other source or sink | **declared-change counter** `budget_decl_<quantity>(i)` | the scheme that applies it |

The counter is cumulative within the physics step, zeroed by `budget_begin` for `lb:ub`, and read by `budget_end`.
Because it is cumulative, any segment's declared term is a difference of two readings, exactly like the state. B's
check schemes and C's hook therefore read it without `prepare_flux` interstitials for these terms. Host metadata:

```
[budget_decl_water]
  standard_name = cumulative_declared_change_of_column_water_in_physics   ! proposed jointly with CAM-SIMA
  units = kg m-2
  dimensions = (horizontal_dimension)
  type = real | kind = kind_phys | active = (flag_for_budget_meter)
```

Scheme side: `intent = inout`, `optional = True`, one loop after every existing statement:
`if (present(budget_decl_water)) budget_decl_water(i) = budget_decl_water(i) + dtp*sum(ten_q(i,:,ntqv)*dp(i,:))*con_1ovg`.
Tracers use `budget_decl_tracer(i, ntrac)` with dimensions `(horizontal_dimension, number_of_tracers)`. Moving E and
P into the counter (each family writing its own) is a later decision taken with B, not part of PR 1.

**Generalisation.**

| Suites | Physics segment | Declared | Status in PR 1 |
|---|---|---|---|
| GFS v16/v17 (satmedmfvdif[q], SAMF, Thompson / GFDL MP) | yes | E, P, h2ophys counter (53 of 56 suites run `GFS_photochemistry`) | checked; satmedmfvdifq gap ~3e-8 per window is a reportable finding |
| HRRR / RAP / RRFS (MYNN, GF, smoke) | yes | E from `mynnedmf_wrapper` (clipped) | water report-only until G2 measures it; smoke/dust are tracers |
| TEMPO, NSSL, Zhao–Carr | yes | species from indices | checked |
| GFDL inline MP (`do_inline_mp`) | yes | its precipitation leaves inside the dycore | `non_physics` flagged `not covered: inline MP` |
| RRTMG / RRTMGP | no water change | energy later reads the host radiative-flux arrays both drivers fill | — |
| MPAS (`physics` group) | same calls in `CCPP_driver` | EFP over (ncols,1) is mesh-agnostic | expected; verify `prsi`, `area`, pelist |
| SCM | own host | the counter is in ccpp-physics, so an SCM meter is ~50 lines later | not covered |

- **Tracers:** one quantity per tracer; classes `passive` (declared 0; refuse `fscav > 0` at init), `emitted`,
  `scavenged` (owners write the counter: SAMF `wet_dep`, MYNN `mix_chem` deposition, smoke emission), `nopbl` (report).
- **Energy:** same machinery with a level-weighted integrand in CAM-SIMA's total-energy vocabulary; declared terms
  (radiative and turbulent fluxes, precipitation enthalpy, fixer, dissipative heating) are a later PR.

**Output.**
- **stdout:** `BUDGET v1 <qty> <fh_end> <segment> <change> <declared> <residual> <sum|r|> <max|r|> <hash> [flags]`;
  `non_physics` prints `-` for the per-column fields. No `rt.sh` keywords. Global means via one EFP collective.
- **diag_table:** `budget_res_<qty>_phys` and `budget_decl_<qty>_phys`, bucket-accumulated 2-D fields registered in
  `GFS_diagnostics.F90`. Written only when listed, so no baseline changes; this is how a developer finds the leak.
- **Fatal:** `errflg` from `budget_window_end` → `CCPP_step` `ierr` → the host's existing `mpp_error(FATAL)`.

**Thresholds** (per window): physics report 1e-10, fatal 1e-5, about 70× above the measured fixed-tree remainder (1.46e-7)
and 160× below the smallest measured defect (1.6e-3); `non_physics` and `stochastics` report-only in 32-bit builds.

**Regression tests.** PR 2 turns the meter on in `control_p8` report-only (stdout only, no baseline), with the PR text
showing dev against fix; physics fatal once the Thompson series merges. One MYNN test (`hrrr_control`) report-only.

**Cost.** Off: one logical test per chunk and no allocation. On: two column integrals per column per step
(2·levs·nwat flops) inside the threaded loop, one collective per window, ~10 real(8) per column per quantity. The
measured wall times are single samples (plain 154 s, off 169 s, on 167–173 s); off slower than on shows the noise is
≥10 %, so G6 needs ≥3 samples per arm.

## 3. Verification

| Claim | Must reproduce | Known-good | Known-bad that must fail |
|---|---|---|---|
| Relocation is exact | A2 physics `change` = prototype A's, all digits, fix and dev, 3 windows; = C sum to 1e-16 | both meters in one executable | bracket around `phys_ps` only: off by the `phys_ts` families (photochem, SAMF, MP) |
| Detection | dev +1.77/+1.74/+1.68e-3, fix −1.63/−1.56/−1.69e-3 | Thompson-fixed tree (TH1–TH7): −1.29e-7 per window, measured | fix tree + SA1 reverted: +3.4e-3 more |
| Counter | H = 1.24e-7; residual equal to the prototype's to round-off | `h2o_phys` on | counter write removed: residual shifts by exactly −H |
| Independent closure | total − offline history budget 3e-8 to 4e-8 (fix) | buckets = windows | window shifted one step: gap ≈ one step of E − P |
| Window alignment | per-bucket agreement with the offline budget | `FHZERO=6` | `fhzero_array=1,3` with the prototype's rule: misaligned after `fhzero_fhour` |
| No-gap check | window-end and next physics-begin snapshots differ by exactly 0 | every step | a test-only write to `qgrs` between them |
| Passive | 0 of 3402, plus GNU, 64-bit, FMA-on (WCOSS2 flags), with the photochemistry counter | meter on vs off | a meter that writes one state value |
| Layout, threads | 0 lines differ, 3×8×1 vs 3×4×2, with (ncols,1) packing | — | plain `MPI_SUM` |
| Stochastics | `control_p8` (`do_ca`) nonzero; deterministic exactly 0 | deterministic run | — |
| Restart | 24 h vs 12 + 12: identical second-window lines; first window flagged `partial` | `FHZERO=6`, restart at 12 h | accumulators carried as zero without the flag |
| Map | area-weighted mean of `budget_res_water_phys` = the stdout residual to r4 precision | — | map not reset with the buckets |

## 4. Risks

| Rank | Risk | What retires it |
|---|---|---|
| 1 | **E is not the applied flux in half the suites.** satmedmfvdifq ~4e-8 of E (measured); MYNN clips and is unmeasured across 26 suites. A false fatal or a masked leak | G2 on `hrrr_control`: booked `dqsfci_diag` vs Σ applied PBL water tendency; MYNN report-only until then; the two PBL PRs exporting the applied flux |
| 2 | **The counter write in ccpp-physics is not answer-neutral.** In-routine meter statements changed FMA contraction in release builds (METERS.md); the prototype's photochemistry edit was shown neutral on one Intel build only | G1/G1b on Intel and GNU, FMA on and off; keep the write a separate trailing loop; fallback: a separate declaration scheme (B pattern) |
| 3 | **A whole-physics number is not acted on, so the meter is not used.** dev's +1.77e-3 hid +3.4e-3/−1.6e-3, and `control_p8` cannot go fatal until the Thompson fixes merge. Also, the bucket-zero block A2 hooks into is marked for removal once the framework handles diagnostics (`CCPP_driver.F90` "DH* 20210104") | the residual map in PR 1; PR 2 report-only with dev-vs-fix evidence; C or B for attribution on the same counters; the window call moves with `phys_zero` (one line), stated in the PR |
