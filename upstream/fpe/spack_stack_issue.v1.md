**Title:** GNU FMS (Release, `-O3`, AVX-512 target) raises intermittent SIGFPE in UFS-WM GNU debug runs (gcc cond_fma bug)

## Description

`cpld_debug_sfs_gnu` on Hercules intermittently stops with SIGFPE inside FMS `diag_send_data`, called from MOM6 `post_surface_thermo_diags` (frazil). The fault is in the precompiled FMS, not in MOM6 or UFS code. It is the GNU counterpart of #2075 and NOAA-GFDL/FMS#1898.

The masked time-averaging loop in `diag_manager.F90` (`if (mask) buffer = buffer + field*weight; else buffer = missvalue`) is vectorised by gcc with AVX-512 as an unmasked `vfmadd213pd` followed by `vblendmpd`. The multiply-add therefore runs in masked-off (land) lanes, which hold stale register contents. The UFS debug executable enables `-ffpe-trap=invalid,zero,overflow` process-wide, so when a stale lane is huge, NaN or Inf, the run stops with an overflow or invalid-operation trap. The weight and every field value passed in were checked and are normal.

The gcc defect is in the x86 `cond_fma` expanders (`config/i386/sse.md`). It is present in gcc 12.2 through trunk and reported as [GCC Bug 128221](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=128221), with a 50-line standalone reproducer.

## To Reproduce

- Run `cpld_debug_sfs_gnu` on Hercules (develop 5651397d) repeatedly: 3 of 10 runs trapped, all at the same instruction.
- Without UFS: build FMS 2024.02 `diag_manager.F90` with gcc 13.3.0 and the recipe's flags (`-O3 -funroll-all-loops -finline-functions -fopenmp -march=icelake-client`). The disassembly of `diag_send_data` is identical to the installed `libfms_r8.a` and contains the unmasked FMA + blend.
- The gcc reproducer fails with `-O3 -mavx512vl` and passes with `-O2`, `-ffp-contract=off` or `-march=haswell`.

## Expected behavior

FMS from spack-stack does not raise floating-point exceptions in debug-built applications. As for oneAPI, a GNU flag in the FMS recipe may be appropriate. `-fno-tree-loop-if-convert` was tested: FMS 2024.02 rebuilt as the recipe does (disassembly identical to the installed library) plus this flag, linked into develop 5651397d. `cpld_debug_sfs_gnu` then completed 15 of 15 runs (stock: 7 of 10), and `cpld_control_sfs_gnu` is bit-identical to the 20261016 baseline. The flag changes 53 of 110 FMS objects.

| Option | Effect on answers |
|---|---|
| `-fno-tree-loop-if-convert` | none in `cpld_control_sfs_gnu` (bit-identical to baseline) |
| `-ffp-contract=off` (untested in UFS) | changes answers wherever FMA contraction applies |
| FMS ≥ 2026.01, whose GNU `Release` is `-O2` (untested) | changes answers (`-O3` → `-O2`) |

## System, compiler, code, ...

- Hercules, Rocky Linux 9.1, Intel Xeon Platinum 8380.
- spack-stack 1.9.2 `ue-gcc-13.3.0`: `fms@2024.02` `build_type=Release`, target `icelake`; OpenMPI 4.1.6; netCDF-C 4.9.2, netCDF-Fortran 4.6.1.
- ufs-weather-model develop 5651397d.
- spack-stack 2.1 (`fms@2025.03`, `build_type=Release`) uses the same GNU `-O3` flags and is expected to be affected on AVX-512 targets.

## Additional context

FMS main changed the GNU `Release` flags to `-O2` in 2026.01, and at `-O2` this loop is not vectorised. The installed library can be checked with `objdump -d libfms_r8.a`: in `diag_send_data`, look for `vfmadd213pd` without `{%k}` followed by `vblendmpd`.
