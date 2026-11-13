# Meter prototypes A, B, C: measured results

Case `control_p8` (suite `FV3_GFS_v17_p8_ugwpv1`, C96 L127, 24 h, dt 720 s, Intel, `-D32BIT=ON`), Hercules, base `develop`
after ufsatm #1145 (capgen-v1). Two physics trees on the same base: **fix** = package 1 (SAMF/PBL fixes, ccpp-physics
`44defba3`), **dev** = unfixed (ccpp-physics `b7cb19b1`). Neither has the Thompson fixes (package 2). All three prototypes
are in one executable (`apply_meterproto.py`), switched by `&budget_nml budget_meter, budget_hook`. Units kg/m² per 6-h
window, global area-weighted means via `mpp_reproducing_sum`. Run dirs `/work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto/runs/`.

## Answer neutrality (G1)

| Comparison (atmf/sfcf, all variables, 6 tiles) | Differ |
|---|---|
| plain exe vs meter exe, meters off | 0 of 3402 |
| plain exe vs meter exe, meters on | 0 of 3402 |
| fix vs dev, meters on (control: the check can fail) | 916 of 1134 |
| plain 1 thread 3×8 vs plain 2 threads 3×4 | 0 of 2268 |
| plain 1 thread vs meters on, 2 threads 3×4 | 0 of 2268 |
| BUDGET lines, 1 thread 3×8 vs 2 threads 3×4 (fix and dev) | 0 lines differ (all digits) |

## Budget (windows 6–12, 12–18, 18–24 h)

| Quantity | fix | dev |
|---|---|---|
| A physics residual | −1.63e-3, −1.56e-3, −1.69e-3 | +1.77e-3, +1.74e-3, +1.68e-3 |
| A non-physics (dynamics) residual | ~1e-7 to 6e-7 | ~1e-7 to 9e-7 |
| A h2ophys source H | 1.24e-7 | 1.24e-7 |
| A total − offline history budget (independent) | 3e-8 to 4e-8 | 1e-9 to 2e-8 |
| B SAMF residual | ~1e-15 | +3.41e-3, +3.30e-3, +3.38e-3 (+0.78 % of P_conv) |
| B − C SAMF family | ~1e-16 | ~1e-16 |
| C sum over schemes − A dW | ~1e-17 | ~1e-16 |
| C family residuals: pbl / photochem / samf / mp / rest | 2e-14 / 1e-16 / 1e-15 / **−1.6e-3** / 0 | 3e-8 / 1e-16 / +3.4e-3 / **−1.6e-3** / 0 |
| mp residual as % of P_ls | −0.69, −0.61, −0.58 % | −0.70, −0.61, −0.58 % |

E ≈ 0.74–0.80, P_conv ≈ 0.42–0.44, P_ls ≈ 0.24–0.29 kg/m² per window.

**Microphysics known-good arm (`th`)** = fix + the Thompson series TH1–TH7 (`patches/git/ufs-dev/thompson/`, `git am`
clean on `44defba3`), meters on, 1 thread:

| Quantity | th |
|---|---|
| C mp family residual | −1.29e-7, −1.29e-7, −1.29e-7 (−0.0001 % of P_ls; fix tree −1.6e-3) |
| C pbl / photochem / samf / rest | 2e-14 / 1e-16 / 1e-15 / 0 (unchanged from fix) |
| A physics residual | −1.29e-7 per window = −5.2e-7 per 24 h (audit, same series without TH8: −5.50e-7 per 24 h) |
| A total − offline history budget | 2e-8 to 3e-8 |
| C sum − A dW; B − C SAMF | ~1e-17; ~1e-16 |
| vs fix, all variables (answers change, as expected) | 915 of 1134 differ |

The remaining −1.29e-7 is the sub-threshold surface sedimentation that TH8 (with TH9, round 2) counts.

## Findings

- The mp residual is the known Thompson leak (TH1–TH4, `../../proposals/water_conservation_audit.md`, ~0.67 % of P_ls); package 1 does
  not fix it. The Thompson series removes it (−1.6e-3 → −1.29e-7) and moves no other family: each family meter has a
  known-good and known-bad arm.
- **C attributes only to `_post` interstitials.** Since ufs-community/ccpp-physics#299 schemes return tendencies; the state
  changes in `GFS_PBL_generic_post`, `GFS_DCNV_generic_post`, `GFS_SCNV_generic_post`, `GFS_MP_generic_post`,
  `GFS_photochemistry_post`. Every physics scheme's own slot reads 0. C gives family, not scheme, attribution.
- SAMF must be metered from `GFS_suite_interstitial_3` to `_4` (condensate held in `clw` between them); per-call C
  numbers inside that span are not meaningful alone.
- C per-column slot counter: surface-loop schemes appear twice (two iterations) as separate slots.
- A non-physics max |column residual| is ~70 kg/m² (transport is not column-local); only the global mean is meaningful.
- Wall time (one sample each, 1 thread): plain 154 s, meters off 169 s, on 167 s (fix) / 173 s (dev); 2 threads plain
  181 s, on 199 / 196 s. Overhead is not resolved by one sample.
- Build: hook in caps = 27 calls in `phys_ps`, 17 in `phys_ts`, 8 in `radiation` (filtered out at run time). Caps at -O0.
- Staging gotcha: native cubed-sphere output with `output_file 'netcdf'` aborts if `zstandard_level > 0`.
