# Canonical conservation patch series for `full14`

*Replay agent, 18 October 2026. Nothing has been posted. Local root `conservation/replay/`; Hercules root
`$U/cons/replay` (`$U` = `/work2/noaa/co2/ash/ufs-chem-v1/upstream`, `$E` = `$U/cons/energy`). The full13 version
of this file is [`SERIES.history.md`](SERIES.history.md), kept verbatim. Its `patches/` and `repo_diffs/` paths now
live in `patches_full13/` and `repo_diffs_full13/`.*

## Status

| Check | Result |
|---|---|
| Target | `$E/full14` = full13 + three decisions (`energy/patches/full14/delta_*.diff`, = `$E/stage14/delta_*.diff`, md5-identical) |
| Base | unchanged: `$E/base` = `$U/p20rt_final/ufs-weather-model` (develop @112b1d46 + water 01–19 + 09b) |
| Series | 55 proposed diffs + `56_NOFMA` (build setting), each applying at `patch -F0` on the state before it. **No renumbering:** row 16 is retired, rows 43 and 46 are replaced, row 57 is new |
| Origins | **50 verbatim**, 23 of them with line offsets and none with fuzz. **4 rebased**: 28, 30, 38 and 42, unchanged from full13. **1 composed**: 46. Rows 50, 51 and 53 are verbatim again, because removing TH9's switch lines also removes their clash |
| **Gate** | fresh base + `apply_series.sh`, then `diff -r` against `$E/full14`: **empty** (`logs/gate_f14_full.txt`). Known-bad: without `57_NM10r`, it **fails** on `GFS_typedefs.F90`, `module_sf_noahmplsm.F90` and `noahmpdrv.F90` (`logs/gate_f14_skip57.txt`) |
| Bug-fix arm | assembled from the series rows, it equals `$E/gB14` under `diff -r` (`logs/arm14_vs_gB14.txt`). Energy's default-off gate gA14_off vs gB14_off: 0 variables differ |
| Meters | full14 has 0 of 385 meter-only identifiers and no new `getenv`. The known-bad mq14 shows 24. The + lines of all 56 series diffs have 0 hits for the explicit meter names |
| Build/run | both runs were done, and the source tree is also byte-identical. The replay exe (job 10158558) is **byte-identical to full14** in its all-on 24 h run vs `rs14_S`: 30 atmf, 30 sfcf and 76 RESTART files. It is also byte-identical in its **default-off** run vs `gA14_off`: 30 + 30 + 38 files. Only the default-off run tells full14 from full13 (below) |
| Water 17r | `energy/patches/water_17r/17r_NM10r_noahmp_precip_phase.diff` applies at -F0 (0 offsets) on develop + water 01–16, and water 18 still applies after it at -F0 (3 offsets). Known-bad: 17r on top of 17 fails, 3 hunks |

## Changes from full13 (old → new)

| Row | full13 | full14 |
|---|---|---|
| 16 | `16_TH8.diff` (energy 06 = canopy 02) | **retired**. TH8 is now part of 43. The number stays reserved, nothing is renumbered |
| 43 | `43_TH9.diff` (canopy 03, switch `thompson_sed_actual`) | `43_TH8-TH9_unconditional.diff` = `energy/patches/13_ccpp-thompson_TH8-TH9_unconditional.diff`, verbatim (cut on fx: held TH8 + held TH9, `module_mp_thompson.F90` only). It applies at -F0 at row 43 with offsets. **Unconditional; in the bug-fix arm.** The `thompson_sed_actual` plumbing (GFS_typedefs, mp_thompson) is gone |
| 46 | `46_PL1.diff` (switch `sfc_precip_t1_carry`) | `46_PL1_under_EP1.diff`: old 46 composed with `delta_PL1_folded_into_EP1` at -F0 and regenerated. It is +94/−11 over 11 files (was +132/−11), and `sfc_precip_t1_carry` appears nowhere. It acts under `sfc_precip_enthalpy` and carries the restart field as before |
| 50, 51, 53 | rebased (REJ stage next to TH9's GFS_typedefs lines) | **verbatim** accepted 35, 36 and 38, with offsets. With no TH9 lines the -F0 clash is gone, and the result is still byte-identical to full14 |
| 57 | — | `57_NM10r.diff` = `delta_NM10r`, verbatim (+5/−4, 3 files). It drops the `precip_phase_host` gate on Noah-MP soil convective precipitation, so `precip_phase_host` now governs glaciers only |

Every other row is byte-identical to its full13 file. Unchanged rows are 01–15, 17–42, 44, 45, 47–49, 52 and 54–56.

## Apply

```
replay/apply_series.sh <ufs-weather-model tree>                 # all 56 (the tested full14 tree, -no-fma)
replay/apply_series.sh <ufs-weather-model tree> 56_NOFMA        # the 55 proposed diffs only
PATCHES=patches_full13 replay/apply_series.sh <tree>            # the old full13 series
ONLY="01_FX1 04_R1 …" replay/apply_series.sh <tree>             # a subset, in series order
```

`patches/series.txt` holds one line per diff: the file, the directory it applies in, the `-p` level, its origin and
its Hercules source. The gate is `FINAL=full14 tools/gate.sh <name> [skip…]`. The `diff -r` exclusions are as before
(`.git`, build dirs, `*.exe`, compile logs and modules, `*.orig`/`*.rej`).

## The series

Origin:
- **V**: verbatim, applies clean.
- **V+o**: verbatim, applies with offsets.
- **RB**: rebased; integrator re-anchor, regenerated pre→post.
- **CO**: composed, regenerated pre→post.

Targets:
- **FV3**: GFDL_atmos_cubed_sphere at `UFSATM/fv3/atmos_cubed_sphere`.
- **phys**: ccpp-physics at `UFSATM/ccpp/physics`.
- **UFSATM**: `ccpp/data`, `ccpp/driver` and `ccpp/CMakeLists.txt`.
- **noahmp**: NOAA-EMC/noahmp at `NOAHMP-interface/noahmp`.
- **uwm**: ufs-weather-model.

Classes: BF = bug fix, PC = physics change, NC = numerical consistency.

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
| 16 | — (retired) | energy 06 TH8 | merged into 43 | — | — | — | — |
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
| 43 | `43_TH8-TH9_unconditional.diff` | Thompson: count all sedimented precip (held TH8) + floored layers sediment their actual mass (held TH9); replaces energy 06, canopy 02, canopy 03 | V+o (= `energy/patches/13_…_TH8-TH9_unconditional.diff`, cut on fx) | . / 1 | phys (`module_mp_thompson.F90` only) | BF | — (`thompson_sed_actual` removed) |
| 44 | `44_E1.diff` | NSST spray implicit | V+o | . / 1 | phys, UFSATM | PC | `nst_spray_opt` 0 / 1 |
| 45 | `45_dyn_te_exact_v2.diff` | FV3 TE tally exact | V | . / 1 | FV3 | bits 1–16 BF; 32, 64 PC | `dyn_te_exact` 0 / 31 |
| 46 | `46_PL1_under_EP1.diff` | PL1 folded into EP1: precip T1 carry, acts under `sfc_precip_enthalpy` | **CO** (old 46 + `delta_PL1_folded_into_EP1`) | . / 1 | phys, UFSATM | BF of EP1 | under `sfc_precip_enthalpy` (`sfc_precip_t1_carry` removed) |
| 47 | `47_MYNN01.diff` | MYNN surface flux density | V | . / 1 | phys | BF / NC | — |
| 48 | `48_MYNN01b.diff` | MYNN moisture check | V | . / 1 | phys | BF | — |
| 49 | `49_GFDL02.diff` | GFDL v3 mass basis | V | . / 1 | phys | BF | — |
| 50 | `50_GF03.diff` | GF water closure | V+o | . / 1 | phys, UFSATM | BF + NC | `gf_closure` F / T |
| 51 | `51_MYNN04.diff` | MYNN surface heat flux θ | V+o | . / 1 | phys, UFSATM | NC | `mynn_sfc_heat` F / T |
| 52 | `52_PBL05.diff` | satmedmfvdifq flux layer mass | V | . / 1 | phys | NC | — |
| 53 | `53_MYNN06.diff` | MYNN static energy mixing | V+o | . / 1 | phys, UFSATM | PC | `mynn_mix_sl` F / T |
| 54 | `54_GFDL07.diff` | GFDL v3 rain sedimentation cp | V | . / 1 | phys | BF | — |
| 55 | `55_SAMF08.diff` | SAMF deep CA trigger return | V | . / 1 | phys | BF | — |
| 56 | `56_NOFMA.diff` | `-no-fma` in `cmake/IntelMixed.cmake` | script (`nofma.py`) | . / 1 | uwm | **build setting, not proposed** | — |
| 57 | `57_NM10r.diff` | NM10r: Noah-MP soil takes the host's convective phase unconditionally (`precip_phase_host` now gates glaciers only) | V (= `delta_NM10r`) | . / 1 | phys, UFSATM | PC (unconditional) | — |

### Rebased and composed diffs

| # | Source | Method | + / − vs source |
|---|---|---|---|
| 28 | `accepted/17_trdyn_03b_…` | -F0, 1 reject, `rebase_trdyn.py` | same |
| 30 | `accepted/18d_trdyn_01_DYN_…_v6` | -F0, 1 reject, `rebase_trdyn.py` | same |
| 38 | `accepted/24_ensfc2_13_sfc_SL2` | -F0, 1 reject, `rebase_r11.py 13` | same |
| 42 | `accepted/28_canopy_01_E2_…` | -F0, 7 rejects, `rebase_r11.py E2` | same except the merged `noahmpdrv.F90` argument-list line (41 and E2 edit the same line; see the history file) |
| 46 | `accepted/41_preclag_01_PL1_…` + `delta_PL1_folded_into_EP1.diff` | both at -F0, the delta with offsets, no fuzz | the composition. Lines PL1 adds and the delta removes cancel (the `sfc_precip_t1_carry` switch) |

## Bug-fix arm (default-off gate)

The bug-fix arm is fx plus the unconditional rows:

01 02 03 04 05 07 12 23 25 26 27 29 31–36 38 39 40 **43** 47 48 49 52 54 55 **57**, + 56 (`-no-fma`).

- **Changes from full13's arm:** 16 (TH8) leaves the arm, and **43** (TH8+TH9 unconditional) and **57** (NM10r)
  join it.
- **Row 38 is applied as cut** (`accepted/24_ensfc2_13_sfc_SL2.diff`, -p2). The rebased series form needs ensfc2 11's
  option lines, which the arm lacks.
- **Row 57 is applied as cut** (`ensfc2/patches/12_sfc_NM10r.diff`, -p2), for the same reason.
- **Assembled this way it equals `$E/gB14`** under `diff -r` (recipe `tools/recipe_arm14.txt`, `logs/arm14_vs_gB14.txt`).
- **Energy's gate** (`$E/logs/final14.txt`): full14 with every switch off vs gB14 has 0 differing variables in
  atmf000/024, sfcf024 and the restart files.

Switch-gated rows, all off by default: 06, 08, 09, 10, 11, 13, 14, 15, 17, 18, 19, 20, 21, 22, 30, 37, 41, 42, 44,
45, 46, 50, 51 and 53. Rows 24 (diagnostic) and 28 (chemistry tracers only) are not switched but are inert in p8.

## Build and run check

**Build.** `$U/cons/replay/tree14` was replayed with `tools/recipe_f14.txt`; it is `diff -r`-identical to
`gate/f14_full` and to `$E/full14`. Build: job 10158558, rc 0, 64-bit, ATM, p8_ugwpv1, `-no-fma`. Exe:
`exe/fv3_r_replay14.exe`.

**Runs.** Each run dir is energy's template, copied, with the reference run's own `input.nml`, `model_configure`,
`field_table` and `diag_table` (checked identical with `cmp`). Only the job name and the exe change. Comparison by
`tools/cmp_nc.py`:

| Run | Reference | Job | Result | Known-bad |
|---|---|---|---|---|
| all-on 24 h with 12 h restart, `runs/rp14_S` | `$E/runs/rs14_S` | 10158602 | atmf 30/30, sfcf 30/30, RESTART 76/76 **byte-identical** | rs14_S vs rs13_S is *also* identical (see below) |
| default-off 24 h, `runs/rp14_off` | `$E/runs/gA14_off` | 10158640 | atmf 30/30, sfcf 30/30, RESTART 38/38 **byte-identical** | gA13_off vs gA14_off: atmf024 **DIFFERENT** |

**The all-on run cannot tell full14 from full13.** Energy also finds rs13_S = rs14_S, 0 differing variables
(`allon-full13-vs-full14`). The three decisions make unconditional what the all-on switches already selected:
- TH8 + TH9, since `thompson_sed_actual` was T;
- PL1 under EP1, since `sfc_precip_t1_carry` and `sfc_precip_enthalpy` were both T;
- NM10r, since `precip_phase_host` was T.

So the default-off run is the check that discriminates, and it is byte-identical. Independent of both runs, the source
tree is byte-identical to full14.

## Water diff 17r (standalone, for the water proposal)

**Diff:** `energy/patches/water_17r/17r_NM10r_noahmp_precip_phase.diff`, md5 62a6ac11e802. It was already delivered,
so I verified it and did not regenerate it. Paths are ccpp-physics `physics/…`.

**Tree:** develop @112b1d46 from the pristine clone `$U/ufs-weather-model`. Its ccpp-physics is @242a2fc with a clean
`git status`; I copied it without `.git` (`tools/w17r.sh`, `logs/w17r.txt`).

| Step | Result |
|---|---|
| develop + water 01–16 (-p1 -F0) | all 16 apply |
| + 17r | **applies at -F0**, 0 offsets |
| + 18 after 17r | **applies at -F0**, 3 offsets (17r shifts line numbers, no fuzz) |
| reference: + 17, then 18 | both apply, 0 offsets |
| known-bad: 17r on top of 17 | **fails**, 3 hunks |
| note: 17r on bare develop | also applies (8 offsets). It does not depend on 01–16 text, so applying there is not a known-bad |

**17r vs 17:** 17 + the host-phase argument (`fpcv_host` / `fpcvh`).
- `module_sf_noahmplsm.F90`: +12 / −3 vs 17's 1 / 0.
- `noahmpdrv.F90`: +10 / −1.

Water 18 applies after 17r without re-anchoring. Its line numbers move by the 17r insertions.

## Per-repository combined diffs (`repo_diffs/`, base → full14)

Each was checked to apply at `-F0` to the base submodule and reproduce full14.

| File | Repository | Apply in | Files | + / − |
|---|---|---|---|---|
| `GFDL_atmos_cubed_sphere.diff` | NOAA-GFDL/GFDL_atmos_cubed_sphere | `UFSATM/fv3/atmos_cubed_sphere` | 10 | +1199 / −36 |
| `ccpp-physics.diff` | ufs-community/ccpp-physics | `UFSATM/ccpp/physics` | 41 | +2948 / −209 |
| `UFSATM.diff` | ufs-community/UFSATM | `UFSATM` | 7 | +424 / −3 |
| `noahmp.diff` | NOAA-EMC/noahmp | `NOAHMP-interface/noahmp` | 1 | +28 / −0 |
| `ufs-weather-model_build_setting.diff` | ufs-weather-model | `.` (row 56, not proposed) | 1 | +1 / −1 |

The same 60 files change base → full13 and base → full14. ccpp-physics and UFSATM shrink by the removed
`thompson_sed_actual` and `sfc_precip_t1_carry` plumbing.

## Meters

`tools/meter_tokens.py` was run as before:
- inputs: the 26 meter and test-hook diffs, `fv_etally.F90`, and energy's `mq14` − `full14`;
- mq14 adds `em_p01`–`em_p12` and `energy_meter_common.F90` as new files, plus the land meter from
  `instrument_land14.py`;
- identifiers new vs the base number 433; of these, 48 are fix switches and variables the meters read, and 385 are
  meter-only.

| Tree | Meter-only identifiers | New `getenv` |
|---|---|---|
| full14 | **0** | **0** |
| mq14 (known-bad) | 24 (`eb_state` ×15, `ebq_prc` ×8, `eb_print` ×5, `em_p01`, …) | 0 |

The + lines of all 56 series diffs give 0 matches for `eb_state`, `eb_print`, `ebx`, `ebq`, `ebq_prc`, `em_pNN`,
`fv_etally`, `etally`, `getenv`, `get_environment_variable`, `eb_land` and `instrument`.
