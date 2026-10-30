# NM12-EMC (20b): NOAA-EMC/noahmp `combine` melt-out fix in `datm_cdeps_lnd_gswp3` (triage row #65)

## Status

- **Verdict: PASS on all ten pre-registered criteria.** The patch builds and runs in the UFS land component. In the stock test the defect never fires, so the stock result is bitwise unchanged. In a seeded variant it fires 128 times. There the fix changes exactly the firing columns and removes the NM12 water term to 1.4e-12 mm. The latent-heat term changes as the meter predicts.
- **The stock RT cannot exercise NM12.** The IC has no snow, and no snow layer ever forms in 24 h (max weasd 0.7 mm), so firings = 0 and the fix run is bitwise identical to the unpatched run. Merged as-is, 20b will not move this RT's baseline.
- **Seeded variant (artificial).** Every land column was seeded with a 5.1–10.0 mm 2-layer pack at the skin temperature. 128 lsm firings, at hours 1–3. Per firing: water −2.8e-4 to +0.285 mm (109 of 128 are exactly 0), latent energy −0.07 to −3.34 MJ/m² (mean −1.63).
- **Glacier hunk:** compiled, but it never fired (0 glacier firings), so it is not exercised here.
- **Open (not NM12):** the output-file water budget fails to close (|R| > 1e-6 mm, p99 ≈ 0.10 mm) in about 30 % of column-hours, including snow-free columns of the stock run. The same residual is in both arms (R_Os − R_Fs equals the NM12 term to 1e-12), so the fix run's total budget is not zero in 67 % of firing columns. Cause not investigated.
- Code-read only, not tested: `lnd_comp_driver.F90` scales `snwdph` by 1000 under `where(mask > 1)`, and the mask is 0/1, so a custom-IC `snow_depth` in metres ends up divided by 1000 in `InitializeStates`. The seeding therefore used depth 0, which applies the 10:1 rule.

| Criterion (pre-registered, `$U/cons/r14_nm12/PREREG.txt`) | Measured | Pass |
|---|---|---|
| C1 builds: `compile.sh hercules "-DAPP=LND -DWARN_AS_ERROR=OFF"`, orig+meter / fix+meter | both BUILD_OK (jobs 10327797/8, 1:43, 1:40); fix has +1 `isnow < -1` per module | yes |
| C2 6 runs exit 0, 144 lnd.out each | all 0, all 144 (job 10327799, 4:49 total) | yes |
| C3 P0 (RT exe, rerun) == RT original | 0 / 19,152 (file,var) differ | yes |
| C3k comparator can fail | RT h1 vs h2: 70 vars differ; P0 vs Ps: 10,005 / 19,950 differ | yes |
| C4 meter write-only: O0 == P0, Os == Ps | 0 / 19,950 and 0 / 19,950 | yes |
| C5 stock: no firing, F0 == O0 | NFIRE 0 / 0; 0 / 19,950 differ | yes |
| C6 seeded fires | NFIRE Os 128, Fs 128 (lsm 128, glacier 0); hours 1/2/3: 65/61/2 | yes |
| C7 firing → output column | max map distance 9.2e-8 deg | yes |
| C8 Fs ≠ Os only in firing columns | 128 differing = 128 firing; 0 diff-not-fired, 0 fired-not-diff, 0 differ before first firing | yes |
| C9 water: \|(R_Os − R_Fs) − w_pred\| ≤ 1e-3 mm (≥95 %) | 100 %; max 1.37e-12, median 3.4e-13 mm | yes |
| C10 ice: \|(G_Os − G_Fs) − e_pred\| ≤ 0.2 mm (≥95 %) | 97.7 %; median 2.4e-15, max 0.296 mm (3 columns: e_pred 5.1–6.1 vs ΔG 4.8–5.8) | yes |

Water: w_pred = sneqv_entry − I − L. Ice: e_pred = sneqv_entry − I. Latent defect = −h_fus · ΔG, with h_fus = 0.3336 MJ/kg. Pre-registered background (Ps, non-firing, hours 1–3): median 5e-13 mm; 30–32 % of column-hours > 1e-6 mm; p99 0.10–0.12 mm. Stock P0 snow-free column-hours: 29.5 % > 1e-6 mm, p99 0.10 mm.

## Method

- **Source.** rt_sxs tree (`47dbddfb`, noahmp `2c7b3bc`, the same tree that built `rt_234783`), rsync-copied without `.git` to `$U/cons/r14_nm12/src_{orig,fix}`. `fix` = `patch -p1` of `20b_NM12-EMC_noahmp-emc_combine_melt_out.diff` (md5 5f09ef4e…).
- **Meter.** Inserted by `tools/apply_meter.py`, write-only (C4). It is a module counter in `combine` / `combine_glacier` at j = 0, firing when `isnow_old < -1 .and. isnow == -1`, the only case where the old and new tests differ. It records L = snliq(0), I = snice(0) and sneqv. The cap prints one `NM12FIRE` line per record with time, PET and lat/lon. Source diffs: `logs/src_{orig,fix}.diff`.
- **Runs.** Each run dir was copied from `rt_234783/datm_cdeps_lnd_gswp3_intel`: INPUT symlinked, `C96.initial.*` copied. The only config change is `restart_n` 1 → 24 (restart cadence). Run with `-A co2`. Seeded ICs come from `tools/seed_ic.py` (`ic_seeded/`).
- **Analysis.** `tools/compare.py` → `logs/compare.log`; per-firing rows in `logs/firing_rows.txt`; background checks in `tools/diag.py`, `diag2.py`. Exes: pristine ca0da536…, orig c32e0678…, fix e2f47256….
- **Disk.** `$U/cons/r14_nm12` = 13 GB (`runs/` 11 GB of hourly lnd.out). Small leftovers: `metertest{,2,3,4}/`, and `/tmp/nm12chk_547559` (716 KB) on a Hercules login node.
