## Description

Fixes JCSDA/spack-stack#2188 for `release/2.2`: on AVX-512 targets, gcc ≥ 12 vectorises FMS's masked diag averaging loop as an unmasked FMA plus blend ([GCC Bug 128221](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=128221)), so FPE-trapping (debug) applications intermittently stop in `diag_send_data`. This adds `-fno-tree-loop-if-convert` for gcc, alongside the existing oneAPI `-fp-speculation=safe`. Reported upstream as NOAA-GFDL/FMS#1937, where FMS could instead apply it to `diag_manager.F90` alone. Will cherry-pick for `develop` and send upstream to spack/spack-packages afterwards.

## Testing

FMS 2024.02 with the recipe's flags plus this one, gcc 13.3.0, Hercules: UFS `cpld_debug_sfs_gnu` completed 15 of 15 runs (stock: 7 of 10), and `cpld_control_sfs_gnu` is bit-identical to the 20261016 baseline. Timing, from a single run: `cpld_control_sfs_gnu` model time 16:59, against 17:45 in the upstream Hercules log, so no slowdown is visible beyond run-to-run noise.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
