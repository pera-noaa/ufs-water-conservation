**Title:** `cpld_debug_sfs_gnu`: intermittent SIGFPE in FMS `diag_send_data`

## Description
On Hercules, `cpld_debug_sfs_gnu` stops with a floating-point exception in about a third of runs, always at the same instruction in FMS `diag_send_data`, called from MOM6 `post_surface_thermo_diags` (frazil). It passes on rerun. The cause is in spack-stack's precompiled FMS, not MOM6 or UFS.

gcc vectorises the masked time-averaging loop in `diag_manager.F90` (`if (mask) buffer = buffer + field*weight; else buffer = missvalue`) with AVX-512 as an unmasked `vfmadd213pd` followed by `vblendmpd`, so the multiply-add also runs in masked-off lanes, which hold stale register contents. The debug executable sets `-ffpe-trap=invalid,zero,overflow` for the whole process, so a stale lane holding a huge value, NaN or Inf traps. The weight and field values passed in are normal.

The defect is in gcc's x86 `cond_fma` expanders, from gcc 12.2 to trunk. Reported to gcc, with a 50-line standalone reproducer, as [GCC Bug 128221](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=128221). Expected: a debug run does not trap on arithmetic the source never performs.

### To Reproduce:
1. Hercules, spack-stack 1.9.2 `ue-gcc-13.3.0` (`fms@2024.02`, Release, target `icelake`), develop 5651397d.
2. Run `cpld_debug_sfs_gnu` repeatedly: 3 of 10 runs trapped, all at the same `vfmadd213pd`.
3. Without UFS: in `objdump -d libfms_r8.a`, `diag_send_data` has `vfmadd213pd` without `{%k}` followed by `vblendmpd`. `diag_manager.F90` from the 2024.02 tag, built with the recipe's flags (`-O3 -funroll-all-loops -finline-functions -fopenmp -march=icelake-client`), disassembles identically.

## Additional context
Workaround tested: the recipe's FMS 2024.02 build plus `-fno-tree-loop-if-convert`, linked into develop 5651397d. `cpld_debug_sfs_gnu` completed 15 of 15 runs, and `cpld_control_sfs_gnu` is bit-identical to the 20261016 baseline. `-ffp-contract=off`, or FMS ≥ 2026.01 (GNU Release `-O2`), would change answers. The fix belongs in the spack-stack FMS recipe: JCSDA/spack-stack#2188.

Related: JCSDA/spack-stack#2075 (oneAPI SCOTCH needing `-fp-speculation=safe`), NOAA-GFDL/FMS#1587 (a different gcc FPE in `time_interp_external2`).

## Output
```
218: Program received signal SIGFPE: Floating-point exception - erroneous arithmetic operation.
218: #1  0x5a37e1e in ???
218: #2  0x5a53c0c in ???
218: #3  0x5037b32 in __mom_diag_manager_infra_MOD_send_data_infra_2d at MOM_diag_manager_infra.F90:319
218: #4  0x4255b85 in post_data_2d_low at MOM_diag_mediator.F90:1601
218: #6  0x3fb468f in __mom_diagnostics_MOD_post_surface_thermo_diags at MOM_diagnostics.F90:1709
```
