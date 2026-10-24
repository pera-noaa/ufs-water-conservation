# Conservation of ccpp-physics #403 (3D TTE-EDMF) and #390 (MLM)

**Status (23 Oct 2026).** Both PR stacks built at their head SHAs and ran C96 `control_p8` for 24 h, each new path on vs off in the same tree. Neither new path conserves. The candidate causes are read from the code, and no fix has been tested yet. Nothing is posted.

## Setup
- **Stacks:**
  - #403 = WM #3402 + ufsatm #1154 + GFDL_atmos_cubed_sphere #429.
  - #390 = WM #3355 + ufsatm #1138.
- **Meters:** our energy, water and tracer meters, ported in (`scripts/instrument_upchk.py`, `port_eb_phys2.py`, `add_pblw.py`).
- **Run list:** `data/runs.tsv`; per-run tables `data/*.txt` (`scripts/uc_table.py`).
- **Noise:** `consv_te` 0.999 vs 1 gives 1e-3 W/m². The off arms are at round-off.
- **Passivity gates:** metered vs plain runs are bitwise identical, except #390 with MLM on. There the two differ, but within noise in rms. The plain MLM-on run is itself reproducible, so the meter perturbs the MLM-on run (cause not found). The known-bad pair fails as intended.

## Result (new path on − off)

| C96, 24 h | #403 horizontal diffusion | #390 MLM |
|---|---|---|
| Water, new term | −1.31e-5 kg/m²/day | +4.39e-4 kg/m²/day |
| Energy, new term | −1.9e-3 W/m² | −1.28 W/m² |
| Passive tracer (ozone) | +6.8e-9 /day (off: 1e-17) | not touched |
| PBL energy residual | +1.43 → +2.51 W/m² | +1.43 → +0.38 W/m² |

## #403
- **Candidate bug:** FV3 `diff3d` (#429) builds T and tracer tendencies that cancel per unit area. `satmedmfvdifq` then applies them to mixing ratios, where only a mass-weighted sum cancels, so about 1–3 % of the gross diffusion leaks. Cube-edge halos are fine (the area-weighted sum is about 1e-17). Fix: mass-weighted fluxes.
- **Design question:** with sa3dtke on, the PBL heats more than the kinetic energy it removes (+1.08 W/m²). Most of this (+0.77) is already in develop with sa3dtke on. Hypothesis: double heating. The PBL dissipates TKE made from horizontal shear, and FV3's divergence damping, driven by the PBL's horizontal eddy diffusivity, also heats (`d_con` = 1). Confirming it needs a dycore meter.
- **Cold pool and Leonard:** no gap at C96. Leonard is inactive above 15 km.

## #390
- **Candidate bug, confirmed by reading the code:** the cloud-base smoothing at the end of `mfscuq_mlm.f` overwrites the k−1 tendencies of T, q and cloud water with the mean of their neighbours. This is not column-conserving: −0.88 W/m² and −6.0e-4 kg/m².
- **Candidate bug:** the remaining gap comes from `−ΔF/dz` applied without density, using the next layer's dz.
- **Latent defect:** `ntsw` and `ntinc` are tracer-array indices used as vertical-diffusion indices. They coincide only for Thompson.
- **Blocking:** with MLM on, single columns get a lowest layer 40–52 K colder than the layer above. This never happens with MLM off.

## #403 sa3dtke energy: the code path (read 23 Oct, at 2a95266 and FV3 e3af577) — hypothesis refuted by the result below
- **PBL** (`satmedmfvdifq.F` L2010–2012, L2072–2075): with `sa3dtke`, TKE shear production is `dku·def_1 + 2·dku_h·def_2`.
  - `def_2` (`dyn_core.F90` L2487) is the horizontal deformation, 2(u_x² + v_y²) + (u_y + v_x)² + w_x² + w_y² + cross term: the horizontal part of 2·S_ij·S_ij.
  - This TKE dissipates and, with `dspheat`, heats (L3331–3336). The PBL's momentum solve is vertical only, so no resolved KE pays for the horizontal part inside the PBL.
- **Dycore** (`sw_core.F90` L1461–1464, `dyn_core.F90` L937–953): `dku3d_h` = `dku_h` raises the del-2 divergence damping, `damp2 = max(damp2, dt·dku3d_h)`. With `d_con` = 1 (GFS RT default), the KE this damping removes becomes heat (`heat_source`, L1542–1572).
- **So, per part of the horizontal shear:**
  - Divergent part: the dycore removes the KE and heats it, and the PBL heats the same shear again through TKE. Heat counted twice.
  - Rotational and stretching parts: `dku_h` drives no resolved sink (vorticity damping uses `damp_vt`). The TKE, and so the heat, has no KE source.
  - Production factor: `2·dku_h·def_2` is twice the standard K·2S_ij·S_ij, while the vertical part `dku·def_1` uses the standard form. This may be intentional.
- **Measured:** PBL residual +1.43 → +2.51 W/m² in the same tree. The +0.77 "already in develop" compares two trees (develop+FX1 SG1 CP1 vs the #403 tree), so it is not a clean contrast.
- **Test:**
  - In the PBL, meter Σ m·2·dku_h·def_2 and Σ m·dku·def_1 against the +1.08.
  - In `d_sw`, meter the `heat_source` from the `dku3d_h` part of `damp2` (on vs off, same tree).
  - Double counting if the dycore heat ≈ the PBL's divergent-shear production; a source if the PBL's production exceeds every KE sink.

## #403 sa3dtke energy: result (23 Oct; build t403d, runs d403_off/3d/c999)

| C96, 24 h, global W/m² | OFF | ON | ON − OFF | noise |
|---|---|---|---|---|
| horizontal production as coded | 0 | +2.7e-4 (divergent 25 %) | +2.7e-4 | — |
| vertical production | +2.594 | +3.889 | **+1.295** | 1.3e-3 |
| dissipative heating | +3.685 | +4.821 | +1.137 | 1.1e-3 |
| KE the PBL removes | −2.253 | −2.310 | −0.057 | 1e-4 |
| PBL residual | +1.432 | +2.510 | +1.078 | 1.0e-3 |
| dycore damping heat | +0.767 | +0.756 | −0.011 | 9e-5 |

- **Gates:**
  - The meters are passive: bitwise, OFF and ON; the known-bad pair differs.
  - Dissipative heating + KE removed = the PBL residual, to 9e-13 (OFF). ON is off by −1.9e-3, which is the horizontal-diffusion heat.
- **Double count: no.** The dycore's heat does not rise; at C96, `dt·dku3d_h` rarely exceeds the default `damp2`. This may differ at convection-permitting resolution (not tested).
- **Horizontal shear: negligible** at C96. **Factor 2: absent.** `prod` averages interfaces k−1 and k, and only k carries the horizontal term, so the horizontal production enters as `dku_h·def_2`.
- **Source:** the vertical production. With sa3dtke the PBL uses the dycore's `def_1`, which differs from its own `shr2`:
  - it adds 2(∂w/∂z)² and w–u cross terms;
  - it comes from A-grid winds at the last acoustic step, on Lagrangian levels;
  - it has no `dw2min` floor.

  The PBL removes KE only through the u, v shear, so the extra +1.3 W/m² of TKE production has no KE sink; 88 % of it becomes heat. Not yet split: the (∂w/∂z)² term vs the level/timing difference.
- **Attribution:** `def_1` and `def_2` predate #403 (the original sa3dtke). The same-tree contrast is sa3dtke on vs off, so this is sa3dtke's, not #403's additions. Our D1 `dspheat_ke` (heat = the KE the momentum solve removes) would close it either way.
- **Files:** `scripts/add_dspm.py`, `scripts/dsp_table.py`, `data/dsp_d403_{off,3d,c999}.txt`.

## #403 sa3dtke vertical production: split (23 Oct; passive build s403b, runs s403_off, s403b_3d, s403b_3dc999)

| C96, 24 h, W/m² | OFF | ON | noise |
|---|---|---|---|
| vertical production (b) | 2.5943 | 3.8895 | 9e-4 |
| w part: 2(∂w/∂z)² + cross terms | 0 | +4.3e-5 | 3e-8 |
| u, v part of `def_1` | 0 | 3.8894 | 9e-4 |
| PBL's own `shr2` production (shadow) | 2.5943 | 3.4018 | 4e-4 |

- **Gates:**
  - bitwise passive ON and OFF; the known-bad pair differs;
  - the parts sum to (b) to 7e-16;
  - the shadow equals (b) OFF exactly.
  - The first split build was not passive (`-O3` reordered `deform_1`); fixed by `scripts/fix_split_passive.py`.
- **The w terms are not the cause** (0.003 % of the rise).
- **+0.49 (38 %):** in the same ON flow, the dycore's u, v shear exceeds the PBL's own. It is not `dw2min`, which only raises `shr2`, and the level alignment matches. Likely the dycore's winds at the last acoustic step on Lagrangian levels, before the remap (not measured).
- **+0.81 (62 %):** the PBL's own shear production rises with sa3dtke on (ck1 = ch1 = 0.17 instead of 0.15, mixing length, flow response). The KE the PBL removes moves only −0.057. So this is consistent with the D1 mechanism, production from the pre-step shear against what the implicit solve removes, growing with K (interpretation, not measured).
- **Both parts are dissipative heating computed from production, not from the KE the solve removes;** D1 `dspheat_ke` closes them.

## #403 sa3dtke with D1 `dspheat_ke` (23 Oct; build t403k = s403b + D1 ported, `scripts/port_D1.py`)

| C96, 24 h, W/m² | OFF | ON | OFF + D1 | ON + D1 | ON + D1, noise |
|---|---|---|---|---|---|
| PBL residual | +1.432 | +2.510 | **−1.6e-12** | **−1.832e-3** | −1.832e-3 |
| heating applied | 3.685 (ε) | 4.821 (ε) | 2.2542 (−dK) | 2.3101 (−dK) | 2.3100 |
| KE the PBL removes | −2.253 | −2.310 | −2.2542 | −2.3101 | −2.3100 |
| dycore heat | 0.767 | 0.756 | 0.765 | 0.753 | 0.753 |

- **Gates:**
  - D1 off is bitwise equal to p403_3d;
  - the meters are byte-identical to s403b_3d;
  - the known-bad pair differs;
  - OFF + D1 reproduces develop's D1 result;
  - `dspfac` = 1 (default).
- **D1 closes the whole sa3dtke PBL residual.** What remains, −1.832e-3, is the horizontal-diffusion leak posted on #403, to 7 digits: T −1.444e-3, vapour −3.87e-4, ice −1e-6.

## Open
- Why the meter perturbs the #390 MLM-on run.
- The source of the 40–52 K cold columns.
- Whether the +0.49 is the pre-remap state (dycore shear vs `u1`),.
- Test the candidate fixes (mass-weighted `diff3d` tendencies, conservative cloud-base smoothing, density in `−ΔF/dz`), each against a known-bad run.
