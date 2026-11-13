# #404 MLM fix and #403 `diff3d` mass-weighted fix: C96 24 h runs (29 Oct 2026)

**Status (29 Oct).** Both fixes have now run in the model (C96 `control_p8`, 24 h, Hercules). Superseded for #404 by `r15_mlm/` (fix v3, posted 12 Nov as the rewritten #404); the #403 result was posted 12 Nov (`post/reply_403_4.md`).
- **#404, verdict: the draft diff crashes as written; with an index guard added it conserves.**
  - As drafted, the run hits a NaN at step 4.
  - The cause is an out-of-bounds index that is already in `mfscuq_mlm.f`: `mlmb` can be 0 while the MLM is active.
  - With a two-line guard added, the fix runs 24 h. The MLM's own column energy and water then close to 1e-19 of the gross (defect without the fix: −1.26 W/m², +4.61e-4 kg/m²/day).
  - A PBL water gap of 2.6e-9 kg/m²/day remains. It lies outside the MLM tendencies, so the pre-registered whole-PBL criterion (≤ 1e-12) fails.
  - The fix is bitwise inert with `mlm` off.
- **uc:12 is resolved.** Once the index is guarded, the metered and plain MLM-on runs are bitwise identical. The 40–52 K cold columns also disappear.
- **#403, verdict: closes only when the tendency is divided by the physics' own layer mass.**
  - The `reply_403_3` face flux, divided by the dycore's `delp` (the draft as written), leaves 1.8e-3 (T) and 5.8e-4 (`sphum`) of the gross.
  - Divided by the post-remap `delp`, it leaves 5.7e-6.
  - Divided by the layer mass the physics uses (`delp` minus condensates), the T and tracer terms close to 1e-16 of the gross or better. The PBL water residual goes from −1.3e-5 to 8e-16 kg/m².
  - A uniform tracer gets exactly zero from the new operator. The original operator gives it up to 3.6e-9 /s.
- **Both drafts need changes** (last section).

## Pre-registration (written before any run; unchanged)
- **#404**
  - **Estimators:** UCM `E`, `W` and Σm·du, the column integrals of the MLM tendencies inside the call; and the EMS PBL-segment water residual.
  - **Pass:** |E| and |W| ≤ 1e-9 of their gross; |PBL water| ≤ 1e-12 kg/m².
  - **Known-bad:** `m390c_mlm`.
  - **Gates:** fix with `mlm` off bitwise = `m390c_off`; no-fix rerun bitwise = `m390c_mlm`.
  - **Meter perturbation (uc:12):** handled by using only within-call identities, with the same meter in both arms.
- **#403**
  - **Estimator:** UCH Smass/Gmass, the net of the horizontal-diffusion tendency as `satmedmfvdifq` applies it, mass-weighted with the physics' `del`, divided by its gross.
  - **Pass:** ≤ 1e-10 for T, `sphum`, `o3mr`.
  - **Known-bad:** `m403_3d`.
  - **Gates:** v0 bitwise = `m403_3d`; feature off bitwise = `m403_off`.
  - **Uniform tracer:** the original operator applied to q ≡ 1.

## Gates (all bitwise comparisons: 50 files, 2398 variables: RESTART + 24 h history)

| comparison | expected | result |
|---|---|---|
| comparator known-bad: `m390c_mlm` vs `p390_mlm`; `m403_3d` vs `m403_c999` | DIFFER | DIFFER (1740; 1702 vars) |
| comparator known-good: `p390_mlm` vs `p390_mlm_r` | IDENTICAL | IDENTICAL |
| #404 fix, `mlm` off: `mlmfix_off` vs `m390c_off` | IDENTICAL | **IDENTICAL** |
| #404 no-fix rerun, 23 Oct output settings: `mlmnofix_on_fh` vs `m390c_mlm` | IDENTICAL | IDENTICAL |
| #403 v0 (switch + diagnostics present) vs `m403_3d`; v2 sa3dtke off vs `m403_off` | IDENTICAL | IDENTICAL; IDENTICAL |
| #403 rebuilt exes are passive: v2 vs v2 + telescoping meter; v2 vs v2 after the v3 rebuild | IDENTICAL | IDENTICAL; IDENTICAL |
| #403 copy of the original operator vs `diff3d` on `sphum` | ≤ 1e-12 rel. | 2.1e-25 / 1.8e-9 (1e-16) |
| source: copies differ from `upchk/t390m` / `t403m` in exactly 2 / 3 files | — | OK |
| source: the draft diff applies with zero fuzz to pristine 3d2331e3 | — | OK |

## #404 MLM: C96 24 h, `mlm` on (metered build; the UCM values are within-call column integrals)

| arm | completes | E W/m² | W kg/m²/day | Σm·du | PBL water residual kg/m² |
|---|---|---|---|---|---|
| `m390c_mlm` (23 Oct, no fix) = `mlmnofix_on_fh` | yes | −1.275 | +4.388e-4 | +3.0e13 | +4.388e-4 |
| `mlmnofix_on` (no fix; only `output_fh` changed) | SIGSEGV, step 8, `mfscuq_mlm.f` L497 | | | | |
| `mlmfix_on`, `mlmfix_on_fh` (draft diff) | NaN, step 4 | 3 steps: −6.7e-19 of gross | −5.5e-19 of gross | | 3 steps: +2.3e-16 |
| `g1_on` (draft + `b` defined at all levels) | NaN, step 4 | | | | |
| `h0_on` (no fix + guards) = `h0p_on` (plain build) | yes | **−1.261** | **+4.613e-4** | +3.0e13 | +4.613e-4 |
| `h1_on` (draft + guards) | yes | **+6.3e-18** | **−9.5e-20** | −3.4e-4 | **+2.6e-9** |
| `mlm` off (`m390c_off` = `mlmfix_off`) | yes | 0 | 0 | 0 | −1.8e-15 |

- **Gross terms in `h1_on`:** |E| 16.6 W/m², |W| 0.85 kg/m²/day.
- **Guards** (`bin/apply_hguard.py`):
  - define `b` at every level;
  - turn the MLM off when `mlmb ≤ 1` (currently only `mlmb = 1` is screened, at L271).
- **Debug build of the fix tree** (`-check`, `-ftrapuv`, `-fpe0`), in the order the traps were hit:
  1. L305: `levs = mlmt − mlmb + 1` is 0 in inactive columns.
  2. L381: uninitialised `b` (it is set only for k = 2..km−2).
  3. With `b` defined everywhere: subscript `b(i,0)`. So `mlmb` = 0 with `cnvflg` true, i.e. `mlmt = krad − 2 = 1` and `mlmb = mlmt − 1`.
  - From the code, not measured: the block at k = `mlmb − 1` = −1 then writes `du`, `dv`, `tdt` and `rtg` out of bounds. The fix also divides by `del(i,−1)` there.
- **Not separated:** whether the `b` guard is needed beyond the index guard. Both were applied together in h0/h1.
- **PBL energy residual** (contains the dissipative-heating term; reported, not a criterion):
  - `mlm` off: +1.433 W/m²;
  - h0: +0.381 W/m²;
  - h1: +1.649 W/m².
- **Lowest layer vs the layer above, min T(bottom) − T(bottom+1) at 24 h:**

| `m390c_off` | `m390c_mlm` | `p390_mlm` | `g0_on` | `h0_on` = `h0p_on` | `h1_on` |
|---|---|---|---|---|---|
| −3.91 K | −11.57 K | −51.83 K (1 column < −30 K) | −4.04 K | −3.62 K | −14.53 K |

## #403 `diff3d`: C96 24 h, sa3dtke + sa3dtke_dyco on (UCH Smass/Gmass)

| variant | T | `sphum` | `o3mr` | max over all 10 tracers | T W/m² | `sphum` kg/m² | PBL water residual kg/m² |
|---|---|---|---|---|---|---|---|
| v0 original (= `m403_3d`) | −2.75e-2 | −9.75e-3 | +9.47e-3 | 9.75e-3 | −1.48e-3 | −1.35e-5 | −1.31e-5 |
| v1 draft: ÷ dycore `delp` (pre-remap) | +1.82e-3 | −5.77e-4 | +1.34e-3 | 4.72e-3 | +8.2e-5 | −7.8e-7 | −8.1e-7 |
| v2: ÷ `delp` after remap | −5.69e-6 | +5.34e-6 | −6.78e-6 | 1.55e-4 | −2.6e-7 | +7.2e-9 | +1.4e-8 |
| **v3: ÷ the physics' layer mass** | **+2.9e-19** | **+1.4e-17** | **−1.5e-17** | **1.6e-16** | +1.3e-20 | +1.9e-20 | **+8.2e-16** |

- **Why v2 does not close:** the dycore side telescopes. Σa·div is 2.4e-17 (`sphum`) and 1.2e-17 (T) of the gross (`D3V`). But the physics builds `prsi` and `del` from `delp` minus the condensates (`atmosphere.F90` L2282–2292). v3 divides by that mass.
- **Uniform tracer, from `D3U`, identical in v0–v3 to 3 digits:**

| operator on q ≡ 1 | mean \|dq/dt\| | mass-weighted net | max \|dq/dt\| |
|---|---|---|---|
| original | 9.4e-12 /s | −1.25e-15 /s (−1.1e-10 /day) | 3.6e-9 /s (3.1e-4 per day) |
| new face flux | 0 exactly | 0 | 0 |

  - For scale: the original operator's mass-weighted |tendency| on `sphum` is 6.5e-10 /s of its mean.
- **PBL energy residual** (reported, not a criterion): 2.5099 (v0), 2.5106 (v1), 2.5116 (v2), 2.5116 W/m² (v3).

## Verdicts
- **#404:**
  - **As drafted:** not runnable. NaN at step 4 at C96, with or without the `b` guard.
  - **With the index guard:**
    - passes the in-call criterion (|E|, |W| ≈ 1e-19 of the gross; known-bad −1.275 W/m², +4.39e-4);
    - fails the whole-PBL water criterion (2.6e-9 vs ≤ 1e-12; the gap is outside the MLM tendencies, cause not traced);
    - inert with `mlm` off (bitwise).
- **#403:**
  - The draft as written (v1) fails: 1.8e-3 of the gross.
  - Dividing by the physics' layer mass (v3) passes: ≤ 1.6e-16 for every term.
  - A uniform tracer gets 0 from the new operator.

## Changes the drafts need
- **`post/issue_390_mlm_body.md` and `issue_390_mlm_fix.diff`:**
  - Replace "compiles, not yet run in the model" with the results above.
  - Add to the diff `if (mlmb(i).le.1) cnvflg(i) = .false.` (in place of `.eq.1`) and `b` at every level. Without these the fixed code goes NaN by step 4.
  - Add a 4th defect: `mlmb` = 0 with `cnvflg` true (trapped by bounds checking). Guarding it makes metered and plain runs bitwise identical and removes the cold columns (−51.8 K → −3.6 K).
  - The defect numbers barely move with the guard: −1.26 W/m² and +4.61e-4 kg/m²/day, vs −1.28 and +4.39e-4 in the draft.
  - State that 2.6e-9 kg/m²/day of water remains in `satmedmfvdifq` with the fix (not traced).
  - The "40–52 K cold columns, not traced" paragraph can now be explained.
- **`post/reply_403_3.md`:** "divide by `dp(i)`" must name the mass the physics applies the tendency to (in UFS, `delp` minus condensates), not FV3's `delp`. Measured with FV3's `delp`: 1.8e-3 before the remap, 5.7e-6 after it. Practical form: `diff3d` returns the flux divergence and `satmedmfvdifq` divides by its own `del`. "A uniform q still gets zero" is confirmed. "Σ q dp dx conserved exactly" holds in the dycore (2e-17) but is not what the physics conserves.
- **`triage_unposted.md` rows #71 and #72, and `experiments/conservation/upchk/report.md` uc:12, uc:32, uc:114:** no longer "NEEDS A RUN". Point them to this file.

## Files (Hercules, `U=/work2/noaa/co2/ash/ufs-chem-v1/upstream`)
- **#404:**
  - `$U/cons/r14_mlm/` — draft fix build, runs, `logs/{bitwise,analyze*}.txt|log`, `bin/`;
  - `$U/cons/r14_mlm_g{0,1}/` — `b` guard;
  - `$U/cons/r14_mlm_h{0,1,0p}/` — both guards; `h0p` is the plain build.
- **#403:** `$U/cons/r14_d3d/`.
  - Switch `UPCHK_D3D` = 0/1/2/3.
  - Source records: `logs/src.diff`, `logs/dyn_core.F90.r14a`, `logs/atmosphere.F90.r14b`.
  - Executables: `exe/r14d3d{,2,3}.exe`.
- **Jobs:** `$U/cons/r14_mlm/logs/jobs.txt`.

## #403 v4/v5: Jongil's updated `diff3d` (12 Nov)

Pre-registered (`$U/cons/r14_d3d/logs/PREREG_v45.md`, md5 e96dc466, before the build). His update
(GFDL_atmos_cubed_sphere#429 @8460b55b) keeps the original stencil (differences `q·dx`) with K_face × `delp`_face and
divides by FV3 `delp`: not our v1. Build `r14d3d4` (`bin/apply_d3d45.py`, `setup6.sh`); v4 = his code, v5 = his stencil
÷ the physics' layer mass (as v3). The old template (`cons/energy/runs/tmpl`) and its RT inputs are gone; inputs are
links into `meterproto/rt_plain` `control_p8_intel` (`bin/fill6.sh`).

| variant | T | `sphum` | max over 10 tracers | T W/m² | PBL water residual kg/m² |
|---|---|---|---|---|---|
| v4: his update ÷ FV3 `delp` | +1.62e-3 | −5.67e-4 | 4.75e-3 | +8.7e-5 | −8.2e-7 |
| v5: his update ÷ the physics' mass | −1.5e-17 | +4.8e-18 | 7.5e-16 | −8.3e-19 | −1.7e-16 |

- **Gates:** v3 rerun with `r14d3d4` bitwise = 29-Oct `d3d_v3_3d` (2398 variables, so the new inputs and the rebuild change
  nothing); v4 differs from it (the switch reaches the code). Tables: `logs/uc_v345.txt`.
- **Uniform tracer** (`D3J`, his stencil ÷ `delp` on q ≡ 1): max |dq/dt| 3.68e-9 /s, area-mean 1.1e-11 /s (original
  3.6e-9, 9.4e-12); mass-weighted net ~1e-17 of it. As predicted: it telescopes but still moves a uniform tracer.
- **Verdict (as predicted):** his update reduces the leak about 17-fold and does not close it; dividing by the physics' `del`
  closes it to round-off. Reply drafted: `post/reply_403_4.md`.
