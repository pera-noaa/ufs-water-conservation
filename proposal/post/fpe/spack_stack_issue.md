**Title:** GNU FMS on AVX-512: intermittent SIGFPE in `diag_send_data` in UFS-WM debug runs

## Description

`cpld_debug_sfs_gnu` on Hercules intermittently stops with SIGFPE in FMS `diag_send_data`, called from MOM6 `post_surface_thermo_diags` (frazil). The fault is in the precompiled FMS, not in MOM6 or UFS (ufs-community/ufs-weather-model#3406). The effect is like #2075 and NOAA-GFDL/FMS#1898, where oneAPI's floating-point speculation raised spurious exceptions and `-fp-speculation=safe` fixed it; here the speculation is a gcc bug.

gcc vectorises the masked time-averaging loop in `diag_manager.F90` (`if (mask) buffer = buffer + field*weight; else buffer = missvalue`) with AVX-512 as an unmasked `vfmadd213pd` followed by `vblendmpd`, so the multiply-add also runs in masked-off lanes, which hold stale register contents. The debug executable traps invalid, zero and overflow process-wide, so a stale lane that is huge, NaN or Inf stops the run. The weight and field values passed in are normal.

The defect is in gcc's x86 `cond_fma` expanders, from gcc 12.2 to trunk: [GCC Bug 128221](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=128221), with a standalone reproducer.

## To Reproduce

- Run `cpld_debug_sfs_gnu` on Hercules (develop 5651397d) repeatedly: 3 of 10 runs trapped, all at the same instruction.
- Without UFS: FMS 2024.02 `diag_manager.F90` built with gcc 13.3.0 and the recipe's flags (`-O3 -funroll-all-loops -finline-functions -fopenmp -march=icelake-client`) disassembles identically to the installed `libfms_r8.a`, with the unmasked FMA + blend.

## Expected behavior

FMS from spack-stack does not raise floating-point exceptions in debug-built applications. As for oneAPI, a GNU flag in the FMS recipe may be appropriate. Tested: the recipe's FMS 2024.02 build plus `-fno-tree-loop-if-convert`, linked into develop 5651397d. `cpld_debug_sfs_gnu` completed 15 of 15 runs (stock: 7 of 10), and `cpld_control_sfs_gnu` is bit-identical to the 20261016 baseline. The flag changes 53 of 110 FMS objects.

| Option | Effect on answers |
|---|---|
| `-fno-tree-loop-if-convert` | none in `cpld_control_sfs_gnu` |
| `-ffp-contract=off` (untested in UFS) | changes answers wherever FMA contraction applies |
| FMS ≥ 2026.01, GNU `Release` `-O2` (untested) | changes answers |

## System, compiler, code, ...

- Hercules, Rocky Linux 9.1, Intel Xeon Platinum 8380.
- spack-stack 1.9.2 `ue-gcc-13.3.0`: `fms@2024.02` `build_type=Release`, target `icelake`; OpenMPI 4.1.6; netCDF-C 4.9.2, netCDF-Fortran 4.6.1.
- spack-stack 2.1 (`fms@2025.03`) uses the same GNU `-O3` flags and is expected to be affected on AVX-512 targets.

## Additional context

To check an installed library: `objdump -d libfms_r8.a`, and in `diag_send_data` look for `vfmadd213pd` without `{%k}` followed by `vblendmpd`.
