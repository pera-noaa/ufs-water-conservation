Title: gcc ≥ 12 on AVX-512: spurious FPEs in `diag_send_data` with `ReleaseUFS` flags

Heads-up, not an FMS bug: a gcc defect ([GCC Bug 128221](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=128221)) vectorises the masked averaging loop in `diag_manager.F90` as an unmasked FMA plus blend, so masked-off lanes can trap in FPE-trapping (debug) applications. It shows up with `-O3 -funroll-all-loops -finline-functions` (now `ReleaseUFS`, and `Release` before 2026.01) on AVX-512 targets, and intermittently stops UFS debug runs (JCSDA/spack-stack#2188).

`-fno-tree-loop-if-convert` fixes it, with bit-identical UFS results in our test. We plan to add it to the spack recipe for gcc, like `-fp-speculation=safe` for oneAPI (#1898). Would you rather carry it in `compiler_flags_GNU_Fortran.cmake`?
