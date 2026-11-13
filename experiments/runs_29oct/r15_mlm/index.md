# #404 index fix: `ntswx` / `ntincx` for `satmedmfvdifq` (PREREG item 4)

## Status

- The fix is done and tested: `Interstitial%ntswx` and `ntincx` are now in the vertical-diffusion order, and `satmedmfvdifq.meta` passes them. The generated caps pass `GFS_Interstitial(mythread)%ntswx/%ntincx` to `satmedmfvdifq_run`.
- With `mlm` off, the fix changes nothing: `control_p8` is bitwise identical to the plain baseline in all 44 `LIST_FILES`.
- **The premise is wrong for `control_p8`.** Its field table (`field_table_thompson_noaero_tke`) comments out `water_nc`. So ntrac = nvdiff = 10, and `GFS_PBL_generic_pre` copies `vdftra = qgrs`. The full `ntinc` is 7, not 8, and the defect does not occur there. With `mlm` on, the fixed and unfixed builds are bitwise identical, and both print `ntsw 5, ntinc 7`.
- No RT field table with a satmedmf suite triggers the defect either (list below). The defect is latent. It appears only when a tracer that is not diffused sits ahead of `snowwat`/`ice_nc` in the field table while nvdiff ≠ ntrac.
- **Defect reproduced in a constructed case:** a passive tracer `idxtest` at slot 7 of the P8 field table. The unfixed build prints `ntinc 8` (rain number in the vdiff array) and the fixed build prints `ntinc 7`. With `mlm` on, 38 of 44 files differ. With `mlm` off, the two builds are bitwise identical, so the change acts only through the MLM.
- Uncommenting `water_nc` (the case the premise describes) does not run: it segfaults in both arms in `GFS_suite_interstitial_4.F90:239`, where `nwfa` is unallocated when there is no aerosol. The field table itself says "not for non-aerosol runs".
- Not checked: whether MLM column water and energy stay closed with the fix (PREREG item 4, last clause), and the optional TEMPO / aerosol-aware run. In those configurations the indices coincide anyway (see below).

## Deliverables

- `index_fix_ufsatm.diff` (paths relative to ufsatm): `ccpp/data/CCPP_typedefs.F90` (declare, set to 0, set per MP) and `CCPP_typedefs.meta`.
- `index_fix_ccpp-physics.diff` (relative to ccpp-physics): `physics/PBL/SATMEDMF/satmedmfvdifq.meta`, which gives `ntsw` and `ntinc` the new names. Apply it on top of `fix_v2.diff`.
- New standard names: `index_for_snow_water_vertical_diffusion_tracer` and `index_for_mass_number_concentration_of_cloud_ice_vertical_diffusion_tracer`. ESCOMP CCPPStandardNames has no `*vertical_diffusion*` names at all, and the UFSATM tree has only the four existing `index_for_*_vertical_diffusion_tracer` names, so neither new name already existed. `snow_water` follows the existing `rain_water` name.
- One deliberate difference from `ntcwx`, `ntiwx` and `ntrwx`: the new values are set **after** the `cplchm` block, using the final nvdiff. That is the value `GFS_PBL_generic_pre` tests (`nvdiff == ntrac`). `ntcwx` and the others are set before `cplchm` changes nvdiff, which is a latent mismatch for MG with `cplchm`: there nvdiff equals ntrac before the block and not after it. Not fixed here.

## MP table (ccpp-physics 44defba3 `GFS_PBL_generic_pre.F90`; new code at `CCPP_typedefs.F90` L1348–1377)

| MP / option | vdftra order | ntswx | ntincx | source lines (PBL_pre) |
|---|---|---|---|---|
| any MP with final nvdiff == ntrac (Zhao-Carr; MG and GFDL without `cld_amt`; P8 as shipped) | `vdftra = qgrs` (full order) | `Model%ntsw` | `Model%ntinc` | L59–61 |
| Thompson, `ltaerosol` | qv qc qi qr **qs** qg nlc **inc** rnc oz wa ia | 5 | 8 | L98, L101 |
| Thompson, `mraerosol` | qv qc qi qr **qs** qg nlc **inc** rnc oz | 5 | 8 | L116, L119 |
| Thompson, neither | qv qc qi qr **qs** qg **inc** rnc oz | 5 | 7 | L132, L134 |
| TEMPO (any `ltaerosol`/`lthailaware`; `mraerosol` ignored) | qv qc qi qr **qs** qg **inc** rnc oz [nlc wa ia] [gnc gv] | 5 | 7 | L149, L151 (appends L159–177) |
| NSSL, hail | qv qc qi qr **qs** qg qh nlc **inc** rnc snc gnc hnc gv hv oz [ccn] [z×3] | 5 | 9 | L238, L242 |
| NSSL, no hail | qv qc qi qr **qs** qg nlc **inc** rnc snc gnc gv oz [ccn] [z×2] | 5 | 8 | L272, L275 |
| MG3 (`ntgl > 0`) | qv qc qi qr **qs** qg nlc **inc** rnc snc gnc oz | 5 | 8 | L187, L190 |
| MG2 | qv qc qi qr **qs** nlc **inc** rnc snc oz | 5 | 7 | L205, L207 |
| GFDL (with `cld_amt`, so nvdiff = ntrac − 1) | qv qc qi qr **qs** qg oz | 5 | 0 | L223 (no ice number) |
| WSM6 | qv qc qi oz | 0 | 0 | L67–70 (snow not diffused) |
| Ferrier-Aligo | qv qc qi qr rimef oz | 0 | 0 | L79–84 |
| `cplchm` (`trans_aero`) | MP block unchanged; chem tracers after `kk`, tke at `ntkev` | as MP row | as MP row | L299–326; affects only whether final nvdiff == ntrac |

In the satmedmf RT field tables, the full and vdiff indices coincide: `thompson_noaero_tke`, `_GOCART`, `aero_tke`, `aero_hail_tke`, `hafs_thompson` and both NSSL tables have nvdiff == ntrac. `_progsigma`, `aero_tke_smoke`, `fire`, `mr2` and `gfsv16` take the MP-order path, but `snowwat` and `ice_nc` sit at the same slot in both orders.

## Other `ntsw` / `ntinc` users (check 2)

All of them index `q1`/`rtg`, which are the vdiff arrays (`nvdiff` wide; `ntrac1 = nvdiff − 1` inside the MLM), so all are consistent after the change. Every `ntswx`/`ntincx` value is ≤ nvdiff − 1, and 0 is guarded at every use.

- `satmedmfvdifq.F` (line numbers as in `src_plain`): L659–660 (`qlx` ice term under `mlm`), L678–679 (`hx`), and the call at L2128 that passes `ntsw`, `ntinc → nqni`.
- `mfscuq_mlm.f`: L175–186 (`qsnow`, `qnice`), the `b` profile from `fix_v2`, and the `rtg(ntsw)` / `rtg(nqni)` tendencies (interior loop and the `mlmb−1` / `mlmt+1` rows).
- Outside the scope of this fix: `satmedmfvdifq.F` L653 and L1646 hard-code `q1(:,:,5)+q1(:,:,6)` (snow and graupel) for `sa3dtke`. That is correct only for the MP orders above with snow at 5 and graupel at 6.

## Tests (Hercules, C96 `control_p8`, 24 h, Intel, `-D32BIT=ON`, suites `FV3_GFS_v17_p8,_ugwpv1`)

Trees and runs are under `/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/r15_mlm/index/`:
- `src_i` = `src_plain` + `fix_v2.diff` + the index fix + the test print.
- `src_v2` = `src_plain` + `fix_v2.diff` + the test print.
- The test print (`print_test.diff`, not in the deliverables) writes `IDXPRINT` once per rank from `satmedmfvdifq_run`.

Jobs: setup 10450911, builds 10450912 (`src_i`) and 10450913 (`src_v2`). Runs are staged by `stage.sh`, which keeps the baseline's own output settings; the comparer is `cmp_runs.py`.

| run (job) | build | mlm | field table | IDXPRINT ntsw/ntinc | compared with | result |
|---|---|---|---|---|---|---|
| `runs/i_off` (10451007) | i | off | as baseline | 5 / 7 | baseline `rt_3544740/control_p8_intel` | **0/44 files differ** (bitwise) |
| `runs/i_on` (10451008) | i | on | as baseline | 5 / 7 | `runs/v2_on` | 0/44 differ (indices coincide) |
| `runs/v2_on` (10451009) | v2 | on | as baseline | 5 / 7 | — | — |
| `runs/i_on_x7` (10451062) | i | on | + `idxtest` at slot 7 | 5 / **7** | `runs/v2_on_x7` | **38/44 differ**: everything after 0 h; atmf024 rms(Δtmp) 0.14 K, rms(Δicmr) 4.2e-6 against rms 1.3e-5 |
| `runs/v2_on_x7` (10451063) | v2 | on | + `idxtest` | 5 / **8** | — | — |
| `runs/i_off_x7` (10451064) | i | off | + `idxtest` | 5 / 7 | `runs/v2_off_x7` (10451065, prints 8) | 0/44 differ: the index reaches only the MLM path |
| `runs/i_on_wnc` (10451010), `v2_on_wnc` (10451011) | i, v2 | on | `water_nc` uncommented | 7 / 8 | — | both SIGSEGV at `GFS_suite_interstitial_4.F90:239` (config not runnable) |

The comparer can fail: baseline vs `i_on` gives 42/44 files differing, and baseline vs itself gives 0/44. In the `i_on_x7` vs `v2_on_x7` comparison, the six identical files are the 0-h outputs, `coupler.res` and `fv_core.res.nc`. Full list: `logs/cmp_i_on_x7_v2_on_x7.txt`.

The cap check is in `src_*/tests/build_fv3_idx*/UFSATM/ccpp/ccpp/ccpp_FV3_GFS_v17_p8{,_ugwpv1}_phys_ps_cap.F90`, in the `call satmedmfvdifq_run` blocks at L2672 and L2637. `src_i` passes `ntsw=GFS_Interstitial(mythread)%ntswx` and `ntinc=GFS_Interstitial(mythread)%ntincx`; `src_v2` passes `GFS_Control%ntsw` and `GFS_Control%ntinc`.
