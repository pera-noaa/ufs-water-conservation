# Canonical conservation patch series for `full13`

*Replay agent, 18 October 2026. Nothing has been posted. Local root `conservation/replay/`; Hercules root
`$U/cons/replay` (`$U` = `/work2/noaa/co2/ash/ufs-chem-v1/upstream`, `$E` = `$U/cons/energy`).*

## Status

| Check | Result |
|---|---|
| Base | `$E/base/ufs-weather-model` = `$U/p20rt_final/ufs-weather-model` (develop @112b1d46 + water diffs 01–19 + 09b). `diff -r` of the two: source identical; the only entries are p20rt's run artefacts `tests/fv3_conf`, `tests/logs`, `tests/run_dir` |
| Series | 55 proposed diffs (manifest rows 1–55, same numbers) + `56_NOFMA` (the `-no-fma` build setting, not proposed). Each applies with `patch -F0` on the state the diffs before it leave |
| Verbatim | 48 of the 55 are the delivered or accepted files, unchanged. Of these, 19 apply with line offsets and none needs fuzz |
| Rebased | 7 diffs are regenerated from the integrator's re-anchoring: 28, 30, 38, 42, 50, 51, 53. Their + and − lines equal the source diff's, except one merged line in 42 (below). Row 15 is the integrator's own rebased file `10r` |
| Extracted | none needed. Every script-applied change (FX1, SG1, CP1, R1, D7, energy round 4 06–12) is reproduced exactly by the delivered diff at -F0. The one change no diff produced is `-no-fma` (`nofma.py`), now `56_NOFMA` |
| Stage checks | the replay equals `$E/fx`, `$E/all_full`, `$E/full6`, `$E/full10`, `$E/full11`, `$E/full12` and `$E/full13` at each stage boundary, on all 60 files the series touches. The only exception is `cmake/IntelMixed.cmake`, which differs from full11/12 until 56 |
| **Gate** | fresh base + `apply_series.sh`, then `diff -r` against `$E/full13`: **empty** (`logs/gate_full.txt`). The known-bad case, with only `52_PBL05` (1 line) left out, **fails** on `satmedmfvdifq.F` (`logs/gate_skip52.txt`) |
| Meters | full13 has 0 meter-only identifiers out of 380, and no new `getenv`. The known-bad case, metered mq13, shows 21. Details are in [Meters](#meters) |
| Build/run | the replay tree, built 64-bit, ATM, p8_ugwpv1, `-no-fma`, reproduces full13's 24 h all-on run **byte for byte**. That covers every `atmf`/`sfcf` file f000–f024 and all 76 RESTART files at 12 h and 24 h |

## Apply

```
replay/apply_series.sh <ufs-weather-model tree>             # all 56 (the tested tree, -no-fma)
replay/apply_series.sh <ufs-weather-model tree> 56_NOFMA    # the 55 proposed diffs only
```

`patches/series.txt` holds one line per diff: the file, the directory it applies in (relative to the
`ufs-weather-model` root), the `-p` level, its origin, and its source path on Hercules. The script stops at the first
diff that does not apply at `-F0` and leaves no `.orig` or `.rej` files. The gate is `tools/gate.sh <name> [skip…]`:
it copies a fresh base, runs the series, and runs `diff -r` against full13.

**Excluded from `diff -r`:** `.git`, `tests/build_*`, `*.exe`, `tests/compile_*_time.log`, `tests/modules.fv3_*`, and
`*.orig`/`*.rej`. Without the exclusions, the 30 entries are full13's build artefacts plus 7 stray patch backups
(`*.orig`) that the integrator's `patch` calls left in full13: `atmosphere.F90`, `fv_mapz.F90`, `fv_arrays.F90`,
`satmedmfvdifq.meta`, `dcyc2t3.f`, `GFS_GWD_generic_post.F90` and `sfc_sice.f`
(`logs/gate_full_unexcluded.txt`).

## The series

Origin values:
- **V**: verbatim, applies clean.
- **V+o**: verbatim, applies with line offsets.
- **RB**: rebased, regenerated pre→post. Paths are `-p1` at the tree root.

Targets:
- **FV3**: NOAA-GFDL/GFDL_atmos_cubed_sphere at `UFSATM/fv3/atmos_cubed_sphere`.
- **phys**: ufs-community/ccpp-physics at `UFSATM/ccpp/physics`.
- **UFSATM**: ufs-community/UFSATM `ccpp/data`, `ccpp/driver` and `ccpp/CMakeLists.txt` at `UFSATM`.
- **noahmp**: NOAA-EMC/noahmp at `NOAHMP-interface/noahmp`.
- **uwm**: ufs-weather-model.

Classes: BF = bug fix, PC = physics change, NC = numerical consistency. In the switch column, "—" means unconditional.

| # | Diff (`patches/`) | Fix | Origin | Dir / -p | Targets | Class | Switch: default / all-on |
|---|---|---|---|---|---|---|---|
| 01 | `01_FX1.diff` | consv_te fixer weight | V | . / 1 | FV3 | BF | — |
| 02 | `02_SG1.diff` | fv_sg total energy | V | . / 1 | FV3 | BF | — |
| 03 | `03_CP1.diff` | state-update heating mass | V | . / 1 | FV3 (driver) | BF | — |
| 04 | `04_R1.diff` | dcyc2t3 current mass | V | . / 1 | phys, UFSATM | BF | — |
| 05 | `05_FV2.diff` | statein layer mass | V+o | `UFSATM/fv3/atmos_cubed_sphere` / 1 | FV3 (driver) | BF | — |
| 06 | `06_D1_dspheat_ke.diff` | PBL dissipative heating KE | V+o | . / 1 | phys, UFSATM | PC | `dspheat_ke` F / T |
| 07 | `07_D3A.diff` | SAMF ice fusion | V | . / 1 | phys | BF | — |
| 08 | `08_D7.diff` | A→D KE heating | V | . / 1 | FV3 | NC | `cpl_ke_heating` F / T |
| 09 | `09_D3B.diff` | SAMF CMT heating | V+o | . / 1 | phys, UFSATM | PC | `samf_cmt_heat` F / T |
| 10 | `10_D4.diff` | GWD KE heating (D4 + D12) | V+o | . / 1 | phys, UFSATM | PC | `gwd_ke_heat` F / T |
| 11 | `11_D4n.diff` | NGW heating | V+o | . / 1 | phys, UFSATM | PC | `ngw_heat_opt` 0 / 2 |
| 12 | `12_NM12.diff` | Noah-MP combine melt | V | `UFSATM/ccpp/physics` / 1 | phys | BF | — |
| 13 | `13_C1.diff` | coupling water energy | V+o | . / 1 | FV3 | PC | `cpl_water_energy` 0 / 15 |
| 14 | `14_K1.diff` | Thompson Kirchhoff | V+o | . / 1 | phys, UFSATM | PC | `thompson_kirchhoff` F / T |
| 15 | `15_S1_export.diff` | S1 + precipitation-flux export | V (= `accepted/10r`) | . / 1 | FV3, phys, UFSATM | PC | `samf_kirchhoff` F / T; export under `cpl_water_energy` 1, 4 |
| 16 | `16_TH8.diff` | Thompson sedimented precip | V | . / 1 | phys | BF (ship with 42 or 43) | — |
| 17 | `17_S1K.diff` | SAMF Kirchhoff ice, initial T | V | . / 1 | phys | PC | `samf_kirchhoff` |
| 18 | `18_TFH.diff` | Thompson frame-F heating | V | . / 1 | phys, UFSATM | PC | `thompson_frame_heat` F / T |
| 19 | `19_PBK.diff` | PBL filler Kirchhoff | V | . / 1 | phys, UFSATM | PC | `pbl_kirchhoff` F / T |
| 20 | `20_C8.diff` | water-mass KE | V | . / 1 | FV3 (driver) | PC | `cpl_water_energy` bit 8 |
| 21 | `21_D7S.diff` | smooth D7 | V | . / 1 | FV3 | NC | `cpl_ke_smooth` 0 / 32 |
| 22 | `22_PBF.diff` | PBL condensate flux export | V | . / 1 | FV3, phys, UFSATM | PC | under `cpl_water_energy` bit 4 |
| 23 | `23_F3_01a.diff` | SAMF scavenging booking | V+o | . / 1 | phys | BF | — |
| 24 | `24_F3_01b.diff` | wet-deposition export (`_on_all_full`) | V+o | . / 1 | phys, UFSATM | NC (diag) | — |
| 25 | `25_SAMF32.diff` | cmake filter dependencies | V | . / 1 | UFSATM (`ccpp/CMakeLists.txt`) | BF (build) | `-DSAMFCNV_32BIT=ON` |
| 26 | `26_TOPT.diff` | process-split sum once | V+o | . / 1 | phys | BF | — |
| 27 | `27_T1_02b.diff` | SAMF tracer substep | V+o | `UFSATM/ccpp/physics` / 1 | phys | BF | — |
| 28 | `28_DRY_03b.diff` | chem tracers dry mixing ratio | **RB** | . / 1 | phys | PC | none (chemistry tracers) |
| 29 | `29_INLQ_04.diff` | inline_q damping mass | V | . / 1 | FV3 | BF | — |
| 30 | `30_DYN_v6.diff` | dry tracer adv/remap/IC + dry_negadj | **RB** | . / 1 | FV3 | PC | `dry_tracer_adv` F / T; `dry_tracer_ic` F / F |
| 31 | `31_SI1.diff` | sea ice | V | . / 2 | phys | BF | — |
| 32 | `32_SI2.diff` | sea ice | V+o | . / 2 | phys | BF | — |
| 33 | `33_NP1.diff` | Noah-MP | V | . / 2 | phys | BF | — |
| 34 | `34_QR1.diff` | NSST | V | . / 2 | phys | BF | — |
| 35 | `35_CMC.diff` | Noah-MP | V+o | . / 2 | phys | BF | — |
| 36 | `36_FL1.diff` | sea ice | V+o | . / 2 | phys | BF | — |
| 37 | `37_sfc_options_r3.diff` | surface options r3 | V+o | . / 2 | phys, UFSATM | PC / NC | 7 switches (manifest row 37) |
| 38 | `38_SL2.diff` | snow layers | **RB** | . / 1 | phys | BF | — |
| 39 | `39_CS1.diff` | Noah-MP | V+o | . / 2 | phys | BF | — |
| 40 | `40_CB1.diff` | Noah-MP | V+o | . / 2 | phys | BF | — |
| 41 | `41_sfc_options_r4_16b.diff` | surface options r4 (16b, meta fixed) | V+o | . / 2 | phys, UFSATM | PC | `sfc_precip_enthalpy`, `lw_sfc_return`, `noahmp_pore_air` F / T |
| 42 | `42_E2.diff` | Noah-MP fwet option | **RB** | . / 1 | phys, UFSATM, **noahmp** | BF, switched | `noahmp_fwet_opt` 0 / 2 |
| 43 | `43_TH9.diff` | Thompson sedimentation actual | V | . / 1 | phys, UFSATM | BF | `thompson_sed_actual` F / T |
| 44 | `44_E1.diff` | NSST spray implicit | V+o | . / 1 | phys, UFSATM | PC | `nst_spray_opt` 0 / 1 |
| 45 | `45_dyn_te_exact_v2.diff` | FV3 TE tally exact | V | . / 1 | FV3 | bits 1–16 BF; 32, 64 PC | `dyn_te_exact` 0 / 31 |
| 46 | `46_PL1.diff` | precip T1 carry | V | . / 1 | phys, UFSATM | BF of EP1 | `sfc_precip_t1_carry` F / T |
| 47 | `47_MYNN01.diff` | MYNN surface flux density | V | . / 1 | phys | BF / NC | — |
| 48 | `48_MYNN01b.diff` | MYNN moisture check | V | . / 1 | phys | BF | — |
| 49 | `49_GFDL02.diff` | GFDL v3 mass basis | V | . / 1 | phys | BF | — |
| 50 | `50_GF03.diff` | GF water closure | **RB** | . / 1 | phys, UFSATM | BF + NC | `gf_closure` F / T |
| 51 | `51_MYNN04.diff` | MYNN surface heat flux θ | **RB** | . / 1 | phys, UFSATM | NC | `mynn_sfc_heat` F / T |
| 52 | `52_PBL05.diff` | satmedmfvdifq flux layer mass | V | . / 1 | phys | NC | — |
| 53 | `53_MYNN06.diff` | MYNN static energy mixing | **RB** | . / 1 | phys, UFSATM | PC | `mynn_mix_sl` F / T |
| 54 | `54_GFDL07.diff` | GFDL v3 rain sedimentation cp | V | . / 1 | phys | BF | — |
| 55 | `55_SAMF08.diff` | SAMF deep CA trigger return | V | . / 1 | phys | BF | — |
| 56 | `56_NOFMA.diff` | `-no-fma` in `cmake/IntelMixed.cmake` | script (`nofma.py`) | . / 1 | uwm | **build setting, not proposed** | — |

### Rebased diffs

Each one is `patch -F0` followed by the integrator's own re-anchoring stage, run on the replay tree. The diff is
regenerated from the files before and after, and `tools/check_pm.py` compares its + and − lines with the source.

| # | Source | Rejected hunks at -F0 | Re-anchor stage | + / − vs source |
|---|---|---|---|---|
| 28 | `accepted/17_trdyn_03b_…` | 1 (satmedmfvdifq declarations next to PBK/PBF) | `rebase_trdyn.py` | same |
| 30 | `accepted/18d_trdyn_01_DYN_…_v6` | 1 (fv_control namelist line next to D7/D7S) | `rebase_trdyn.py` | same |
| 38 | `accepted/24_ensfc2_13_sfc_SL2` | 1 (hunk 8, `hc1` next to ensfc2 11's `svn, hcpo, hcpn`) | `rebase_r11.py 13` | same |
| 42 | `accepted/28_canopy_01_E2_…` | 7 (next to 41's lines) | `rebase_r11.py E2` | same except **one merged line** (below) |
| 50 | `accepted/35_suites_03_…` | 2 (GFS_typedefs switch lines next to TH9) | `rebase_r11.py REJ` | same |
| 51 | `accepted/36_suites_04_…` | 2 | `rebase_r11.py REJ` | same |
| 53 | `accepted/38_suites_06_…` | 2 | `rebase_r11.py REJ` | same |

**Two lines that are true merges, not context changes.** In each case two diffs edit the same line, so the rebased
line carries both edits.
- **Row 42, `noahmpdrv.F90` argument list.** 41 turns `con_t0c                &` into `con_t0c,  &`, because it adds
  arguments on the next line. E2 adds `noahmp_fwet_opt` to that same line. The rebased − line is 41's version, and the
  + line is `hflx_evap_enth, con_cliq, con_cvap, con_t0c, noahmp_fwet_opt,              &`.
- **Row 15, `samfshalcnv.f` argument list** (in the integrator's `10r` rather than in this replay). As cut, encpl 06
  splits the `…cat_adj_shal,errmsg,errflg)` line into two to add `pflx, samf_kirchhoff`. After encnv 02–04 that line
  is `errmsg,errflg)` alone. 10r edits it into `pflx,samf_kirchhoff,errmsg,errflg)`. The arguments are the same, in
  the same order.

Every other rebased diff carries the source's + and − lines exactly.

**Other substitutions relative to the as-cut files**, all as the manifest records:
- 24 is `01b_…_on_all_full`. It has the same + and − lines as `01b_…export.diff`, which is cut on `fx`; checked.
- 41 is `16b`. It differs from `16_sfc_options_r4.diff` by one + line, the `[tgrs]` standard_name: `air_temperature` →
  `physics_timestep_initial_air_temperature`. This reproduces `mk11b.sh`'s sed exactly.
- 43 TH9 applies clean on the plain tree. Its re-anchoring was only ever needed in the metered tree.

### What the manifest's open questions turned out to be

- **`$E/accepted` numbers** (Hercules listing): 02 = enpbl 04, 04–06 = encnv 02–04, 08–10 = encpl 04–06, 10r = 06
  rebased, 13 = latent 01b `_on_all_full`, 19–22 = ensfc2 08–11. 11 does not exist. full9 took ensfc2 04–11 from
  `$U/cons/ensfc2/patches`; the files are byte-identical to accepted 19–22.
- **D7 (row 8)** went into all_full by anchors (`integrate_full.txt`: `FIX:D7`). `energy/patches/05_…` reproduces it
  exactly at -F0.
- **FX1, SG1, CP1, R1 and energy 06–12** were all applied by anchors. The delivered diffs reproduce `$E/fx`,
  `$E/all_full` and the round-4 part of `$E/full6` exactly, with no offset.
- **trdyn 02b → 03b → 04_INLQ → v6 on full6 in one pass:** it works and gives `$E/full10` exactly, with the same
  re-anchoring of 03b and v6 as v5 needed.
- **suites accepted 32–40 names:** `32_suites_01_E3_…` … `40_suites_08_SAMF_…`. The mapping is 32 → 01, 33 → 01b,
  34 → 02, 35 → 03, 36 → 04, 37 → 05, 38 → 06, 39 → 07, 40 → 08, and every file is byte-identical to `suites/patches/`.
- **D3A (row 7):** `accepted/03` and `encnv/patches/01_D3A.diff` differ only in their header timestamps.

## Per-repository combined diffs (`repo_diffs/`)

These run from base to full13, one diff per repository, with paths relative to the submodule root (`-p1`). Each was
checked to apply at `-F0` to the base's submodule and to reproduce full13's files.

| File | Repository | Apply in | Files | + / − |
|---|---|---|---|---|
| `GFDL_atmos_cubed_sphere.diff` | NOAA-GFDL/GFDL_atmos_cubed_sphere | `UFSATM/fv3/atmos_cubed_sphere` (`model/`, `driver/UFS/`) | 10 | +1199 / −36 |
| `ccpp-physics.diff` | ufs-community/ccpp-physics | `UFSATM/ccpp/physics` (`physics/`) | 41 | +2987 / −201 |
| `UFSATM.diff` | ufs-community/UFSATM | `UFSATM` (`ccpp/data/`, `ccpp/driver/`, `ccpp/CMakeLists.txt`) | 7 | +446 / −3 |
| `noahmp.diff` | NOAA-EMC/noahmp | `NOAHMP-interface/noahmp` (`src/module_sf_noahmplsm.F90`; row 42 only) | 1 | +28 / −0 |
| `ufs-weather-model_build_setting.diff` | ufs-weather-model | `.` (`cmake/IntelMixed.cmake`; row 56, not proposed) | 1 | +1 / −1 |

- **Nothing touches ccpp/framework**, and full13 adds no new files.
- **Base for all of these:** develop @112b1d46 + the water proposal's diffs. They sit on top of that proposal, not on
  bare develop.
- **For per-fix PRs,** split each `patches/NN_*.diff` by the target column above. Most diffs touch both ccpp-physics
  and UFSATM, because a switch needs both its scheme code and its `GFS_typedefs` plumbing.
- **MPAS (manifest rows 56–59)** is a separate `git am` series in another repository and is not part of this tree.

## Meters

`tools/meter_tokens.py` collects the identifiers on the + lines of every meter or test-hook diff in manifest part C:
- 26 diffs plus `fv_etally.F90`;
- the integrator's own `mq13` − `full13` difference, which also adds `em_p01`–`em_p05` as new files in mq13.

It keeps the identifiers that appear in none of the base's 60 touched files: 431. Of those, 51 are also on the
+ lines of the series. They are the fix switches and variables the meters read (`cpl_water_energy`, `samf_kirchhoff`,
`tprcp_t1`, …). The other 380 are meter-only.

**Result:**

| Tree | Meter-only identifiers present | New `getenv` | Explicit grep (`eb_state`, `eb_print`, `ebx`, `ebq`, `ebq_prc`, `em_pNN`, `fv_etally`, `etally`, `getenv`, `get_environment_variable`) |
|---|---|---|---|
| full13 | **0** | **0** | none |
| mq13 (known-bad) | 21 (`eb_state` ×15, `ebq_prc` ×8, `eb_print` ×5, `em_p01`…) | 0 | — |

full13 also has no file beyond the base's, while mq13 adds the `em_p*` scheme files. So **full13 carries no meter or
test-hook code**.

## Build and run check

**Build.** `$U/cons/replay/tree` is the replay tree, `diff -r`-identical to `gate/full`. It was built once by
`tools/build64.sbatch`: energy's script with the log path changed, `compile.sh hercules "-DAPP=ATM
-DCCPP_SUITES=FV3_GFS_v17_p8_ugwpv1"`, 64-bit dycore, with `-no-fma` coming from `56_NOFMA`. Job 10157729, rc 0; the
executable is `$U/cons/replay/exe/fv3_r_replay.exe`.

**Run.** `tools/mkrun.sh` made `$U/cons/replay/runs/rp13_S`:
- the run template `$E/runs/tmpl`, copied;
- `rs13_S`'s own `input.nml`, `model_configure`, `field_table` and `diag_table`, checked identical with `cmp`;
- its `job_card` with only the job name changed;
- this executable.

`rs13_S` is energy's full13 all-on 24 h run with a 12 h restart, the restart-gate run. Job 10157768 completed in
4 min 26 s.

**Comparison** (`tools/cmp_nc.py`, `logs/run_rp13_vs_rs13.txt`):

| Files | Count | Result |
|---|---|---|
| `atmf000`–`atmf024` (6 tiles × 5 times) | 30 | byte-identical |
| `sfcf000`–`sfcf024` | 30 | byte-identical |
| `RESTART/*`: fv_core, fv_tracer, fv_srf_wnd, phy_data, sfc_data, ca_data, coupler at 12 h and 24 h | 76 | byte-identical |

**Known-bad for the comparator:** rs13_S vs rs12_S (full12) gives `atmf024.tile1` and `fv_core.res.tile1` at 24 h
both DIFFERENT, with 8 of 15 fv_core variables differing.

So the replayed series rebuilds the tested model exactly, from source to executable output.
