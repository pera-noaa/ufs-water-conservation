# Option B redesigned: chained checkpoints at the tendency-application interstitials

Review of prototype B (CAM-SIMA-style check schemes) against [`results.md`](results.md) and
[`../meter_design.md`](../meter_design.md), and a design more likely to be merged and used. Suite facts are from the patched
tree on Hercules (`src_fix/UFSATM/ccpp/suites/`, 56 suite files).

## Status

| | |
|---|---|
| **Proposal** | Keep B's two good ideas (declaration next to the code that knows the flux; a CCPP-native check that also runs in the SCM). Replace its save/prepare/check triples with **one chain of checkpoints** whose segments tile the physics and sum exactly to A |
| **Main departure** | No suite edits, no per-family `*_prepare_flux_for_budget` schemes, no Diag arrays. Declarations and checkpoints are one-line calls added to the seven interstitials that apply tendencies since ccpp-physics#299; together they appear in 55 of 56 suites |
| **Depends on** | A (host meter, PR 1): it seeds the chain, closes the tail, reduces and prints |
| **Must reproduce** | B SAMF ~1e-15 (fix) / +3.4e-3 (dev); C families pbl / photochem / mp; Σ segments − A ≤ 1e-15 |
| **Open** | Whether maintainers accept meter calls inside shared interstitials (fallback below); answer neutrality of recompiled interstitials (G1b) |

## 1. Prototype B as built

**What it gets right**

- The flux declaration is a separate, reviewable piece of code with metadata (units `kg m-2`, dimensions) that capgen checks.
- It is ordinary CCPP: no framework change, so it also builds under `ccpp_prebuild` (the SCM), which C cannot.
- The integrand is the effective state `gq0 + dtp·dqdt`, so it is correct under every `tend_opt_*` chain.
- It reproduces the research convection meters: SAMF ~1e-15 (fix), +3.41e-3 / +3.30e-3 / +3.38e-3 (dev, 0.78 % of P_conv); B − C ~1e-16; lines identical across 1 and 2 threads; G1 0 of 3402.

**What it cannot do, and what a maintainer would push back on**

| Issue | Evidence | Consequence |
|---|---|---|
| One segment only | the four `budget_*` names are singular; a second family needs four more names and four more Diag arrays | names grow as families × quantities |
| Segments do not tile | save/check pairs bracket only interstitial_3→_4 | the Thompson leak (C fam_mp −1.6e-3) is invisible to B; no closure test against A is possible |
| The declaration is the meter author's, not the family's | `samf_prepare_flux_for_budget` reads Diag `rainc`, which `GFS_DCNV_generic_post` sets and `GFS_SCNV_generic_post` increments (`rainc = frain·rain1`, `rainc += frain·rain1`) | the name says SAMF but the code is generic: it is true of all 46 suites with `GFS_DCNV_generic_post` (SAMF, GF, C3, Tiedtke) |
| Span knowledge lives in the suite placement | condensate sits in `clw` between `GFS_suite_interstitial_3` and `_4` | nothing stops a later edit placing the check between them |
| Not switchable | the schemes always run; the Diag arrays are always allocated (`apply_meterproto.py` comment) | "meters off" is not off: the measured 169 s vs plain 154 s cannot be attributed |
| Suite clutter | 3 lines per family per suite | ~4 families × 55 suites ≈ 660 XML lines; CAM-SIMA carries this in one `suite_cam7.xml`, UFS has 56 suite files |
| Diag misuse | non-output accumulators in the output DDT, zeroed by the host's `zero_window`, not by Diag's own zeroing | split ownership of one array |
| Duplicated math | `ufs_budget_colwater` (scheme) and `colwater` (host) are two copies of one integral with a hard-wired 7-index species list | a fix to one copy misses the other; Zhao–Carr, NSSL hail and tracers need a third |
| Reporting lives only in the ufsatm host | `GFS_budget.F90` reduces and prints | the SCM gets no output |

## 2. Proposed design

**Principle.** The code that applies a tendency declares the boundary flux that goes with it; a checkpoint at each
point where the state is consistent closes the segment since the previous checkpoint. Since #299 these are the same
seven interstitials in every GFS-family suite, each shared by every scheme of its family.

**Chain.** Per column and quantity q, `w_last(i,q)` holds the column amount at the last checkpoint and `decl(i,q)`
the declarations since then. A checkpoint at site s computes `w = Σ_k Σ_n W(n,q)·(gq0 + dtp·dqdt)(i,k,n)·Δp_k/g`, adds
`w − w_last` to `seg_change(i,s,q)` and `decl` to `seg_decl(i,s,q)`, then sets `w_last = w`, `decl = 0`. The host
seeds `w_last` from A's start-of-physics snapshot and books `colwater(gq0_end) − w_last` as the segment `tail`.
Segments telescope, so **Σ segments + tail = A physics** to round-off, whatever the suite — a closure that fails only
on a meter bug. Adding a checkpoint refines a segment; it can never double-count or leave a gap.

**Sites** (named integer constants in the helper module; the segment index *is* the site, so no slot counter, no
run-time label registry, no thread race):

| Site (checkpoint at the end of) | Declares there | Suites | Segment it closes |
|---|---|---|---|
| `GFS_PBL_generic_post` | +E·dtp (`dqsfc1/hvap`; applied flux once satmedmfvdifq exports it) | 28 | start → PBL (surface, PBL) |
| `mynnedmf_wrapper_post` | +MYNN's clipped `qfx`·dtp (the flux it applies, once exported) | 26 more | start → PBL |
| `GFS_photochemistry_post` | +H = Σ `dtp·ten_q(:,:,ntqv)`·Δp/g (moved from A's prototype edit) | 53 | PBL → photochemistry (incl. GWD) |
| `GFS_DCNV_generic_post`, `GFS_SCNV_generic_post` | −ρ_w·frain·`rain1`, declare only | 46 / 23 | — |
| `GFS_suite_interstitial_4` | — | 50 | photochemistry → convection (the 3→4 span, for every scheme) |
| `GFS_MP_generic_post` | −ρ_w·frain·`rain1` (the MP's own) | 55 | convection → MP |
| host, after `CCPP_step("physics")` | — | all | MP → end (`tail`: pending `dqdt` never applied) |

A suite without a site merges that segment into the next one (NSSL/WoFS have no interstitial_4; they have no
convection). MPAS_RRFS gets nothing (another host). GFDL MP, TEMPO, Thompson, NSSL all end in `GFS_MP_generic_post`;
GFDL in-core MP changes water in the dycore and lands in A's `non_physics`.

**Where code lives**

| Repo | File | Content |
|---|---|---|
| ccpp-physics | `physics/tools/ufs_column_budget.F90` (new, no module state) | `column_amount` (the one copy of the integral, also used by the host), `budget_declare`, `budget_checkpoint`, site constants |
| ccpp-physics | seven interstitials above | per file: one `budget_declare` and/or one `budget_checkpoint` call under the flag, plus optional `active`-gated arguments in the `.meta` |
| ccpp-physics | `ufs_column_budget_checkpoint.F90/.meta` (new) | thin scheme wrapper, site `adhoc`, for a developer bisecting inside a family in a local suite; never committed in suites |
| ccpp-physics CI | `tools/check_budget_placement.py` | suite lint: no checkpoint between interstitial_3 and _4, between a scheme and its `_post`, or in `subcycle loop > 1` |
| ufsatm | `GFS_budget.F90` (A) + a new `GFS_budget_type` in `GFS_typedefs`, allocated only when on | arrays, `W(n,q)` from `nwat`/tracer indices/`budget_tracers`, chain seed, tail, window sums (EFP), `BUDGET` lines |
| CCPPStandardNames | 8 names, proposed jointly with CAM-SIMA | below |

**Standard names** (all new; checked absent from `GFS_typedefs.meta`; `flag_for_diagnostics` exists but means bucket
output). Their number does not grow with segments or quantities — the prototype's grows as 4 × segments × quantities.

| Name | Shape | Who writes |
|---|---|---|
| `flag_for_column_budget_checks` | logical | host namelist |
| `number_of_column_budget_quantities`, `number_of_column_budget_sites` | dims | host init |
| `column_budget_tracer_weights` | (number_of_tracers, nq) | host init |
| `column_budget_amount_at_last_checkpoint` | (horizontal, nq) | host seed, checkpoints |
| `column_budget_declared_change_since_last_checkpoint` | (horizontal, nq) | declarers |
| `column_budget_segment_change`, `column_budget_segment_declared_change` | (horizontal, nsites, nq) | checkpoints |

Existing names reused: `tracer_concentration`, `process_split_cumulative_tendency_of_tracers`, `air_pressure_at_interface`,
`timestep_for_physics`, `gravitational_acceleration`, `number_of_tracers`, and each family's existing `rain1` name.

**Generalisation**

- *Suites:* by construction — the sites are generic interstitials. MYNN needs its owners to add two calls in
  `mynnedmf_wrapper_post` and to export the applied `qfx`.
- *Tracers:* quantity q > 1 is a tracer selected by `W`; the same checkpoints meter it. Declarations come from the
  family that knows them: RRFS smoke emission, SAMF `wet_dep` (exported by the scheme, declared in DCNV_post), MYNN
  `mix_chem` deposition. Undeclared quantities are report-only and labelled so.
- *Energy:* the same chain with a second integrand in CAM-SIMA's total-energy vocabulary; declarations (radiative,
  sensible, precipitation enthalpy) go in the same interstitials. Phase 4.

**On/off and answers.** `&budget_nml budget_meter = .false.` by default: arrays unallocated, optional arguments
absent, declarer and checkpoint return at the flag. Only reads `gq0`/`dqdt`; writes only its own arrays.

**Output and tests.** Stdout only, A's format and EFP sums:
`BUDGET water <h> B:<site> <change> <declared> <residual> <sum|r|> <max|r|> <hash>` per site, then
`B:closure` (Σ − A). No baseline change. In `control_p8`: fatal on `B:closure > 1e-12` from day one (it can only be a
meter bug); per-site residuals report-only until fix packages 1–3 merge, then fatal at A's 1e-6 threshold.

**Cost.** Four checkpoints per suite × ncol × levs × nwat multiply-adds per step (≈ 4 × 127 × 6 per column), well below any
physics scheme; off, seven flag tests. G6 needs ≥ 5 timing samples per arm (one sample in `results.md` resolved nothing).

**Fallback** if maintainers reject calls inside interstitials: the same module and arrays, with the checkpoint as an
explicit scheme line after each site in the RT-tested suites only (1 line per site, not 3 per family). If capgen's
post-call hook (C) is accepted, it can call `budget_checkpoint` after each site instead. Declarations stay put in all three.

## 3. Verification

| Claim | Must reproduce | Known-good | Known-bad that must fail |
|---|---|---|---|
| Answer-neutral | G1: 0 of 3402 history fields, meter on vs off vs plain | same | a checkpoint that writes `w` back into `gq0(:,1,ntqv)` |
| Answer-neutral, recompiled interstitials | G1b: full RT, Intel + GNU, incl. a 2-thread test, meter off vs current baselines | — | — (gate on the full set) |
| Closure | `B:closure` ≤ 1e-15 (C sum − A was ~1e-17) | fix and dev | skip one `w_last` update; seed from `gq0` after interstitial_1 |
| Convection segment | fix ~1e-15; dev +3.41e-3, +3.30e-3, +3.38e-3 (= prototype B) | fix | fix + SA1 reverted (G2); a checkpoint inserted between DCNV_post and SCNV_post (lint must also reject it) |
| MP segment | −0.69/−0.61/−0.58 % of P_ls, = C fam_mp −1.6e-3, both trees | Thompson TH1–TH7 run: −1.29e-7 per window (measured) | drop the MP declaration: residual ≈ −P_ls |
| PBL segment | C fam_pbl 2e-14 (fix), 3e-8 (dev) | fix | drop the declaration: residual ≈ +E (0.74–0.80) |
| Photochemistry | 1e-16, H = 1.24e-7 | both | drop the declaration: residual = 1.24e-7 |
| Layout / threads | identical lines 3×8 vs 4×6, 1 vs 2 threads (G3, G4) | — | a plain `MPI_SUM`; a module-level accumulator |
| Restart | identical second-window lines, 24 h vs 12 + 12 (G5) | — | seed carried across restart from an uninitialised array |
| Generic across suites | closure ≤ 1e-15 in one MYNN/Thompson (HRRR), one TEMPO, one GFDL-MP (HAFS) RT | each | the same suites with the `mynnedmf_wrapper_post` checkpoint removed: closure still holds, PBL merges into the next site |
| Off is off | no budget allocation; timing within noise over ≥ 5 samples | — | prototype B build (schemes run unconditionally) |

## 4. Top three risks

| # | Risk | What retires it |
|---|---|---|
| 1 | Editing seven shared interstitials changes their code generation and therefore answers on some platform (FMA, vectorisation) | G1b on the full RT, Intel + GNU, 2-thread; precedent: A's prototype already edited `GFS_photochemistry` with 0 of 3402 differing. If it fails, the fallback (explicit scheme lines, interstitials untouched) |
| 2 | Maintainers reject meter calls inside interstitials, or the eight names | PR 0 issue with these numbers; the interstitials already book `dtend` and Diag buckets, so a declaration is the same kind of statement; names proposed jointly with CAM-SIMA. Fallback as in 1 |
| 3 | A per-segment residual is a booked-vs-applied difference, not a leak (MYNN's clipped, ρ·dz-weighted `qfx`; satmedmfvdifq's `dtdz1·evap`; tracer sinks not exported) | G2 per PBL scheme on its RT suite; two small PRs exporting the applied flux; per-site fatal only after the gap is measured below 1e-6 |
