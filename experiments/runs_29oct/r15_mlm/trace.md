# #404 MLM: tracing the PBL water residual (PREREG.md §3)

**Status.** All runs: C96 `control_p8` (`FV3_GFS_v17_p8_ugwpv1`), 24 h, Intel, 1 thread, Hercules. kg/m² per day, global area mean.
- **The 2.6e-9 is not the MLM.** It comes from `dtdz1(i) = dt2 / (zi(i,2)-zi(i,1))` in `satmedmfvdifq.F`, the pre-package-1 surface-flux statement. That statement injects dt·evap·Δp₁/(g·Δz₁), while the declared flux is dt·ρa·evap.
  - The 29-Oct number reproduces from its own logs: the EMS PBL residual (+2.601069e-9) equals the in-scheme `uc_exit` residual (+2.601069e-9).
  - Reconstruction: today's tree with that statement restored and a 64-bit dycore (as on 29 Oct). The PBL residual is +1.7791e-9 with `mlm` on and −9.7e-14 with it off; the probe on that statement (P16) gives +1.7792e-9, i.e. 100.00 % (difference 9e-14, the background with `mlm` off).
  - Package 1 replaced the statement (`dt2*rho_a*g/del(1)`). On today's base with `fix_v2` the PBL family closes: −8.7e-14 (`mlm` on) vs −8.8e-14 (off). **No PBL code change is implied.**
- **Pre-registered hypothesis: right mechanism, wrong segment.**
  - Refuted for the PBL residual: no clip in the PBL family acts on MLM tendencies. The fixers act only on the solver state (P04 ≤ 1e-18).
  - Confirmed at a much larger size in microphysics:
    - The MLM leaves −0.136 kg/m²/day of negative water (98 % cloud water). By `mp_thompson` entry it is −0.1007 (qc −0.0979, qs −0.0021, qi −0.00065).
    - Thompson's entry branches set every q ≤ R1 to 0 (`module_mp_thompson.F90` L2267 `qc1d(k) = 0.0`; qs L2334, qi L2294), creating **+0.1007 kg/m²/day** of water, 3.3 % of surface evaporation.
    - This accounts for 100.9 % of the MLM-induced change in the MP-family residual (−0.0050 → +0.0948). The 0.9 % remainder is the change in Thompson's own leak.
  - The negatives are not caused by `fix_v2`: the guards-only arm has −0.141.
- **Implied change, not built here:** a positivity limiter on the MLM condensate fluxes in `mfscuq_mlm.f`. The interior flux divergence makes 74 % of the negative qc, the top boundary block 10 %, the bottom block 8 %, and cloud-base smoothing 7 %.
  - With the Thompson series (TH5/TH6 send negative/≤R1 condensate to vapour), the MP residual with `mlm` on equals `mlm` off to 5e-7 of the negatives.
  - So that series removes the water source, but the negative cloud water itself remains the MLM's.
- **Unverified:** why the old surface-flux mismatch appears only with `mlm` on (the layer-1 `q1 < qmin` probe P15 reads 0); an MLM-side limiter; energy consequences of the clip.

## Probes (passive; switch `&budget_nml budget_probe`, needs `budget_hook`, 1 thread)

Water = vdiff slots 1–6 (qv qc qi qr qs qg), mass weight del/g in `satmedmfvdifq`, the meter's `prsi`/g in the hook. Each probe is a per-column sum per step, accumulated per 6-h window and area-meaned with the meter's `mpp_reproducing_sum`. Probe code: `trace_scripts/apply_probe{,2,3}.py`.

| slot | statement measured |
|---|---|
| P01 | MLM water change, dt·W(rtg after `mfscuq_mlm` − before) |
| P02 / P03 | solver W(f2 − q1) after `tridin` / its surface source dtdz1·evap·del₁/g |
| P04 | negative-moisture fixers, W(f2 after fixers − f2 after `tridin`) |
| P05 / P06 | scheme total dt·W(rtg_end − rtg_entry) / declared E = dt·ρa·evap (= meter's `dqsfci`/hvap·dt) |
| P07 / P09 | negative water W(min(q,0)) at scheme exit / after the MLM tendency alone |
| P12 / P13 / P14 / P16 | P05−P06 (scheme residual) / P05−(P01+P02+P04) (split check) / P02−P03 / P03−P06 |
| P15 | layer-1 q1 < qmin flag (column-steps) |
| P17–P21 | negative qc after the MLM tendency by layer: k = mlmb−1, mlmt+1, cldbase−1 (smoothing target), interior, other |
| M01–M06 / M07–M12 | negatives entering / leaving `mp_thompson_run` (qv qc qr qi qs qg) |

## Gates (`mp_compare.py bitcmp`, atmf+sfcf, 6 tiles, fh 6–24)

| comparison | expected | result |
|---|---|---|
| probes on vs off, same build: `p_on`/`p_on_np`, `m_on`/`m_on_np`, `k_on`/`k_on_np` | identical | 0 of 4536 each |
| probe build with probes off vs build without probe code: `p_on_np`, `m_on_np`, `k_on_np` vs `z_on` | identical | 0 of 4536 each |
| `m_off` vs `p_off` (stage-2 code inert with `mlm` off) | identical | 0 of 1134 |
| comparator can fail: `p_on` vs `p_off`; `p_on` vs `g_on`; `t_on` vs `t_off` | differ | 916; 916; 915 of 1134 |
| probe known-bad: guards-only MLM (`g_on`), P01 vs PBL-family residual | equal, ≈ +5e-4 | +6.823451e-4 = +6.823451e-4 (P12 same) |
| probe known-good: `mlm` off, P01 / P09 / M02 | 0 / 0 / ~0 | 0 / 0 / −1.8e-19 |
| split check P13 | round-off | ≤ 9e-17 in all runs |

## PBL family (C:fam_pbl residual vs probes, 24-h sums)

| run | tree | `mlm` | fam_pbl res | P01 | P04 | P14 | P16 | P12 |
|---|---|---|---|---|---|---|---|---|
| `p_on` (= `m_on`, `k_on`) | `src_fix` + `fix_v2` | on | −8.75e-14 | +3.7e-20 | −1.3e-18 | −5.7e-16 | +6.2e-18 | −4.7e-16 |
| `p_off` | same | off | −8.79e-14 | 0 | +5.2e-18 | +1.2e-16 | +6.1e-18 | +2.2e-16 |
| `g_on` (known-bad) | `src_fix` + guards only | on | **+6.823e-4** | **+6.823e-4** | +3.6e-18 | −1.2e-16 | — | +6.823e-4 |
| `d_on` / `d_off` | + 29-Oct `dtdz1`, 32-bit dycore | on / off | +1.243e-7 / +1.259e-7 | ~1e-19 / 0 | ~1e-18 | ~1e-16 | +1.243e-7 / +1.259e-7 | = P16 |
| **`d64_on`** | + 29-Oct `dtdz1`, 64-bit dycore | on | **+1.779066e-9** | +7.4e-20 | +9.5e-19 | +1.1e-16 | **+1.779158e-9** | +1.779158e-9 |
| `d64_off` | same | off | −9.7e-14 | 0 | +4.7e-18 | −4.9e-16 | +6.8e-16 | +2.8e-16 |
| `t_on` / `t_off` | `src_th` + `fix_v2` | on / off | −8.7e-14 / −8.7e-14 | ~1e-20 / 0 | ~1e-18 | ~1e-16 | ~6e-18 | ~1e-16 |

Per-window `d64_on` fam_pbl residual: +2.81e-10, +2.08e-10, +7.18e-10, +5.72e-10, matched by P16 to 2e-14 in each window. With the 32-bit dycore, the same statement mismatches by ~4e-8 of E whether or not `mlm` is on. With the 64-bit dycore, it mismatches only with `mlm` on, which is the 29-Oct signature.

**The 29-Oct tree (r14, EMS + upchk meters)**, `trace_scripts/old_uc.py` on the kept `out` files:

| run | EMS PBL-segment water residual | in-scheme `uc_exit` (Σ rtg·del/g·dt − ρa·evap·dt) |
|---|---|---|
| `r14_mlm_h1/runs/h1_on` (draft + guards, `mlm` on) | +2.601069e-9 | +2.601069e-9 |
| `r14_mlm/runs/mlmfix_off` | −1.85e-15 | +3.2e-16 |

That tree's `satmedmfvdifq.F` differs from today's `src_0` only in the meter calls and the `dtdz1` line. Package 1 (`meterproto/pkg1_physics.diff`) touches `satmedmfvdifq.F` only at that line, and that tree's `GFS_PBL_generic_{pre,post}` differ only by `dqdt`→`ten_q` renames. Its build had no `-D32BIT` (`r14_mlm_h1/logs/build.10328734.log`). The old binary was not re-probed; the attribution of the original 2.6e-9 rests on the identity above and the `d64` reconstruction.

## Microphysics family: where the MLM's negative water becomes a source (24-h sums)

| quantity | `m_on` (`fix_v2`, `mlm` on) | `m_off` | `t_on` (TH series, on) | `t_off` |
|---|---|---|---|---|
| P09 negative water after the MLM tendency | −0.1361 | 0 | −0.1228 | 0 |
| P07 negative water at PBL exit | −0.1054 | −1.6e-19 | — | — |
| M02–M06 negative condensate entering `mp_thompson` | **−0.10066** (qc −0.09791, qs −0.00210, qi −0.00065, qr/qg ~1e-23) | −1.8e-19 | −0.09212 | −1.9e-19 |
| M01 negative vapour entering (first 12 h only) | −3.7e-6 | ~1e-25 | −3.2e-6 | ~1e-25 |
| M07–M12 negatives leaving `mp_thompson` | 0 | 0 | 0 | 0 |
| C:fam_mp residual | **+0.094801** | −0.005004 | −5.64e-7 | −5.18e-7 |
| fam_mp residual + M02–M06 (MP residual without the entry clip) | −0.005857 | −0.005004 | −0.0921 (clip is conservative here) | — |
| C:fam_samf / fam_pbl / fam_rest residual | ~1e-15 / −8.7e-14 / 0 | same | same | same |

Per window, `m_on` fam_mp: +0.02219, +0.02169, +0.02481, +0.02611. Entry negatives: −0.02243, −0.02352, −0.02663, −0.02808.

- **Attribution:** MLM-induced change in the MP-family residual = 0.094801 − (−0.005004) = 0.099805. Entry-clip creation = 0.100659 (+3.7e-6 vapour) → **100.86 %**.
  - The −8.5e-4 remainder is Thompson's own leak, larger with the MLM's extra cloud (−0.005857 vs −0.005004; same sign in every window).
  - Independent check (TH arm, where TH5/TH6 return clipped/≤R1 condensate to vapour): the same −0.092 of negatives changes the MP residual by −4.6e-8, i.e. 5e-7 of itself.
  - Hence the source is the entry deletion, not any other MLM-dependent path in Thompson.
- **Statement:** `module_mp_thompson.F90` (`src_fix`), subroutine `mp_thompson`, entry loop. When `qc1d(k) .le. R1`, the `else` branch sets `qc1d(k) = 0.0` (L2267; 97.3 % of the creation). The same branches for snow (L2334, 2.1 %) and ice (L2294, 0.65 %) make up the rest.
- **Size for scale:** +0.1007 kg/m²/day = 3.3 % of E (3.02), 20× Thompson's own leak, 1.5e2× the pre-fix MLM defect (+6.8e-4).

**Where the MLM makes the negative cloud water** (`k_on`, qc only, negative part of q1 + dt·MLM tendency, 24 h; sum −0.1333 = 98 % of P09):

| layer | k = mlmb−1 (bottom block) | k = mlmt+1 (top block) | k = cldbase−1 (smoothing target) | mlmb ≤ k ≤ mlmt (interior flux divergence) | other |
|---|---|---|---|---|---|
| negative qc | −0.01011 (7.6 %) | −0.01388 (10.4 %) | −0.00968 (7.3 %) | **−0.09903 (74.3 %)** | −0.00059 (0.4 %) |

The explicit flux-form update removes more cloud water from a layer than it holds. A one-step limit on `qcflux` (and `qiflux`/`qsflux`), or routing the MLM tendencies through `satmedmfvdifq`'s conservative negative-moisture borrowing, would remove the negatives at the source. Neither was built here.

## Trees, builds, runs (Hercules, `T=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/r15_mlm/trace`)

| tree | contents | exe (build job) |
|---|---|---|
| `src_p` | `meterproto/src_fix` + `fix_v2.diff` + stage-1 probes | `fv3_trp` (10450999) |
| `src_0` | `src_fix` + `fix_v2.diff`, no probe code | `fv3_tr0` (10451000) |
| `src_gp` | `src_fix` + `guards_only.diff` + stage-1 probes (known-bad) | `fv3_trg` (10451001) |
| `src_m` | `src_p` + stage-2 probes (MP entry/exit, P15–P16) | `fv3_trm` (10451140) |
| `src_d` | `src_m` + 29-Oct `dtdz1` | `fv3_trd` (10451141); `fv3_trd64` without `-D32BIT` (10451465) |
| `src_tm` | `meterproto/src_th` (TH1–TH6) + `fix_v2.diff` + stage-1/2 probes | `fv3_trt` (10451142) |
| `src_k` | `src_m` + stage-3 probes (P17–P21) | `fv3_trk` (10451484) |

- **Builds:** `-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1 -D32BIT=ON` (`bin/build.sb`), except `trd64` (`bin/build64.sb`).
- **Setup jobs:** 10450946, 10451139, 10451483. 10450946 exited 141 from a SIGPIPE in its final `awk | head`, after every step had completed. Source diffs: `logs/src_*.diff`.
- **Runs** (`runs/<name>`, staged by `bin/stage.sh` from `meterproto/rt_plain/.../rt_3544740/control_p8_intel`; native output every 6 h; meter + hook on):

| run | job | run | job | run | job |
|---|---|---|---|---|---|
| `p_on` | 10451067 | `z_on` | 10451096 | `d_off` | 10451383 |
| `p_on_np` | 10451068 | `m_on` | 10451379 | `t_on` | 10451384 |
| `p_off` | 10451069 | `m_on_np` | 10451380 | `t_off` | 10451385 |
| `g_on` | 10451071 | `m_off` | 10451381 | `d64_on` | 10451560 |
| `k_on` | 10451562 | `d_on` | 10451382 | `d64_off` | 10451561 |
| `k_on_np` | 10451563 | | | | |

- **Failed/cancelled:**
  - `z_on` first attempt (10451070) failed: `budget_probe` is not a namelist member in `tr0`. Kept as `runs/z_on.fail_nml`.
  - 10451093 was cancelled.
- **Tables:** `logs/table{1,2,3}.txt`, `logs/fam_lines.txt`, `logs/fam2.txt`, `logs/old_uc.txt`, `logs/bitcmp_*.txt`. Job list: `logs/jobs.txt`. Scripts: `bin/` (local copies in `trace_scripts/`).
- **Not touched:** `cons/r15_mlm/{src_f,src_g,rt,runs}` (the other session). Nothing was deleted, committed, pushed or posted.
