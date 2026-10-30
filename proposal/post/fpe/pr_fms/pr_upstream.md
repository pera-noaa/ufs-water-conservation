## Description

On AVX-512 targets, gcc ≥ 12 vectorises FMS's masked diagnostic averaging loop as an unmasked FMA plus blend ([GCC Bug 128221](https://gcc.gnu.org/bugzilla/show_bug.cgi?id=128221)), so applications that trap floating-point exceptions intermittently stop in `diag_send_data` (NOAA-GFDL/FMS#1937). This adds `-fno-tree-loop-if-convert` for gcc. Already in JCSDA/spack-packages#103 for spack-stack 2.2.

## Testing

FMS 2024.02 with this flag, gcc 13.3.0 on Hercules (Ice Lake): UFS `cpld_debug_sfs_gnu` completed 15 of 15 runs (stock: 7 of 10), and `cpld_control_sfs_gnu` is bit-identical to its baseline.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
