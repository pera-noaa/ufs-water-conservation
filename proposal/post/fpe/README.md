# `cpld_debug_sfs_gnu` SIGFPE: root cause and where to report it

## Status

| Item | Result |
|---|---|
| Trap site | FMS 2024.02 `diag_send_data`, masked averaging loop (`diag_manager.F90` L2529–2546), from MOM6 frazil `post_data` |
| Cause | gcc x86 backend: `cond_fma<mode>` (and `cond_fms`, `cond_fnma`, `cond_fnms`) expand the masked `.COND_FMA` as an **unmasked** `vfmadd` + `vblendmpd`, so masked-off lanes are computed and can raise FP exceptions despite the default `-ftrapping-math` |
| Middle end | correct: if-conversion emits `.COND_FMA (mask, w, field, buffer, missvalue)` (`gimple.sh`, `*.optimized`) |
| Expander | unchanged from gcc 13.3.0 to master (`gcc/config/i386/sse.md`) |
| `-ffp-contract=off` | `.COND_MUL`/`.COND_ADD` expand masked (`vmulpd …{%k1}{z}`, `vaddpd …{%k1}`): no spurious flag |
| Shipped library | spack-stack 1.9.2 `fms-2024.02-anubnpi`, gcc 13.3.0, Release, `-O3 -funroll-all-loops -finline-functions -fopenmp` + spack `-march=icelake-client`; `codegen.sh` rebuilds `diag_manager.F90` from the 2024.02 tag: 0 of 38,892 disassembly lines differ |
| Rerun loop 2 (job 10226396) | run 3 of 3 trapped, rank 308, `invalid` this time (stale NaN/Inf lane), at the same unmasked `vfmadd213pd 0x20(%r8,%rdx,2),%ymm9,%ymm13`; weight bits normal (`409C2…` = 1800, `40AC2…` = 3600; 1/1800, 1/3600); field finite and < 2¹⁰⁰ everywhere |
| Why intermittent | in FMS the field is a merge-masked load (`vmovupd …{%k}`), so masked-off lanes hold stale register/stack data; it traps only when that is ≳10³⁰⁵ |
| Why debug only | the GNU debug executable sets `-ffpe-trap=invalid,zero,overflow` process-wide but links the Release FMS; Hercules spack-stack has no debug FMS |
| Our PRs | not involved; develop links the same library |
| FMS main | the loop is unchanged (5 masked loops of this form) |

Standalone reproducer `condfma.c` (deterministic: the masked-off value is loaded unconditionally, so it is 1e307, not stale):

| gcc | flags | result |
|---|---|---|
| 13.3.0, 12.2.0 | `-O3 -march=icelake-client` | `FE_OVERFLOW RAISED`; SIGFPE with `feenableexcept` |
| 13.3.0 | `+ -fno-trapping-math` / `-mprefer-vector-width=512` | raised |
| 13.3.0 | `+ -ffp-contract=off` | clear |
| 13.3.0 | `-O3 -march=haswell`, `-O0` | clear (no AVX-512 masking / not vectorised) |
| 11.3.1 | `-O3 -march=icelake-client` | clear (not vectorised) |

Not yet run: gcc trunk on x86 (none on Hercules; Mac is arm64). Compiler Explorer would do it.

## Venues and what each needs

| Venue | Requirements | Have | Missing |
|---|---|---|---|
| **gcc Bugzilla** (root cause) | account; `gcc -v`; command line; self-contained testcase (or `.i`); actual vs expected; ideally confirmed on trunk | testcase, versions, flags, expander source, GIMPLE | trunk confirmation; Bugzilla account (Ash). Related: PR122103 (same class on SVE, middle end), PR96373 |
| **NOAA-GFDL/FMS issue** (bug template) | description; reproduce steps; expected; OS, compiler+version, MPI, netCDF C+Fortran, configure options; context | all fields (below) | nothing; but FMS has no bug, so an issue is a heads-up only |
| **FMS PR** (template: description, `Fixes #`, how tested, checklist incl. new check tests, `make distcheck`) | a source change + test | — | no justified change: any if-converted form hits the same expander. Possible but hacky: `!GCC$ novector` on the 5 loops |
| **ufs-weather-model / spack-stack** | issue | trap site, cause, rerun record | decision: debug FMS for GNU debug builds (as WCOSS2's `fms-D`), or FMS built with `-ffp-contract=off` |

FMS template fields: Rocky Linux 9.1; Intel Xeon Platinum 8380 (Ice Lake); GNU 13.3.0; OpenMPI 4.1.6; netCDF-C 4.9.2, netCDF-Fortran 4.6.1 (HDF5 1.14.3); CMake `-DGFS_PHYS=ON -DOPENMP=ON -DENABLE_QUAD_PRECISION=ON -DSHARED_LIBS=OFF -DWITH_YAML=OFF -DCONSTANTS=GFS -DLARGEFILE=OFF -DINTERNAL_FILE_NML=ON -D32BIT=ON -D64BIT=ON -DFPIC=ON -DUSE_DEPRECATED_IO=ON`, `CMAKE_BUILD_TYPE=Release`, spack target `icelake`.

Related FMS issue: NOAA-GFDL/FMS#1587 (intermittent gcc 13 FPE in `time_interp_external2` at `-O0`; different cause).

## Files

- `gcc/` — gcc Bugzilla reproducer: `condfma.c` (standalone, `./t.x trap` for SIGFPE), `pr-condfma.c` (testsuite form, `dg-do run`), `run.sh` (flag matrix, GIMPLE, asm), `bugzilla.md` (draft report, not filed).
- `condfma.c`, `run_condfma.sh` — earlier version of the reproducer.
- `codegen.sh` — rebuild FMS 2024.02 `diag_manager.F90` as spack did; count FMA/blend/masked loads per flag set; diff against the shipped object.
- `gimple.sh` — `-fdump-tree-{ifcvt,vect-details,optimized}` for the same build.
- Hercules: `/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/fms_codegen/` (builds, dumps, `gccrepro/`).

## Posting order

1. gcc Bugzilla: filed 27 Oct as GCC Bug 128221 (target, 17.0; text `gcc/bugzilla_description.txt`, attachment `gcc/condfma.i`); linked from ufs-community/ufs-weather-model#3406.
2. spack-stack issue: posted 27 Oct as JCSDA/spack-stack#2188 (`spack_stack_issue.md`).

## Develop and flag test (Hercules, 24 Oct; `fpe_dev/`, jobs 10229005/11/12)

| Check | Result |
|---|---|
| FMS rebuild gate | own build (spack args + PR 1559 patch) vs spack `libfms_r4/r8.a`: 0 of 110 objects differ in disassembly |
| Flag scope | `-fno-tree-loop-if-convert` changes 53 of 110 objects; `diag_manager` r8: vfmadd 256 → 128, vblendmpd 128 → 0 |
| Consumer | `fv3.exe` `diag_send_data`: stock 256 vfmadd / 128 blend; flagged (debug and release exes) 128 / 0 |
| Stock develop 5651397d, `cpld_debug_sfs_gnu` | **3 of 10 runs trapped** (overflow), same site |
| Develop + flagged FMS, `cpld_debug_sfs_gnu` | **0 of 15** (P = 0.7¹⁵ ≈ 0.005 if the rate were unchanged) |
| Develop + flagged FMS, `cpld_control_sfs_gnu` vs baseline 20261016 | PASS (bit-identical) |
| Stock develop, `cpld_control_sfs_gnu` | not run: rt.sh could not start ecFlow (both trees shared port 12168); infrastructure |
