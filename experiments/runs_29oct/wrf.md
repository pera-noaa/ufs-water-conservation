# WRF ports: Thompson full series rerun (#62), W1/W2 restart and decomposition (#63)

**Status (29 October 2026).** WRF `release-v4.8.1` 315a8319, `em_quarter_ss` supercell (doubly periodic, no surface fluxes), 2 h. Criteria pre-registered in `r14_wrf/PREREGISTRATION.txt`, with addendum A for the dmpar builds.
- **#62 PASS.** The five-commit Thompson series closes to the same level as the four-commit build. That build had neither TH6's refill nor TH7's noreturn. Host meter / P: mp 8 +1.714e-6, mp 28 +1.694e-6, mp 38 +1.332e-6. The earlier values were +1.694e-6, +1.578e-6 and +1.382e-6; the original code gives +1.5e-2. The new code changes the run (output is not bit-identical to the four-commit build), and domain/P is unchanged to 3 digits.
- **#63 restart PASS.** On the serial build, a run restarted at 60 min is bit for bit identical to a straight run. This holds for base and fix, in case a (`diff_opt=2`, W1) and case d (no PBL, W2). It holds for every variable at 90 and 120 min and for the full 120-min restart file, by our comparator and by WRF's `diffwrf`.
- **#63 decomposition: PASS on every output variable, INCONCLUSIVE by the letter of the rule on the restart file.** On dmpar builds, 2x2 and 4x3 runs are bit for bit identical to 1x1 for base and fix in both cases. This holds for every wrfout variable at every time, by our comparator and by `diffwrf`, and also against the serial build. The 120-min restart files differ in one of 603 variables, `MIN_PTCHSZ`, a restart-only integer that records the smallest patch size (21 at 2x2, 32 at 4x3). It differs identically in base. A restart within the 2x2 layout is bit for bit.
- **A gate failed and was caught.** The earlier builds (`dynfix/src_ctl`, `src_fix`) are configure option 76, i.e. **serial** with `-DSTUBMPI`, not dmpar. My first decomposition pairs (job 10327884) therefore compared independent single-task copies. Gate D2 caught this (ntasks 1, no rsl files), so those pairs are void. The fix was new option-78 (dmpar) builds, under addendum A.
- **Scope.** One case per fix, one storm, 2 h. W3 is not tested (not asked). The Thompson tree used for #63 is the four-commit series both builds were made with.

## #62 WRF Thompson, five commits

Build `r14_wrf/th5`: 315a8319 plus `git apply` of `patches/ports/WRF-thompson/000[1-5]` (no commits), WBMP meter v2, option 76 as before (build job 10327882, runs 10327883). The runs repeat `verify/run.sbatch` exactly: serial, 600 microphysics calls, own tables.

| run | host/P | scheme/P | domain/P at 120 min | vs earlier run |
|---|---|---|---|---|
| b0 (original), mp 8, rerun | +1.512e-2 | +1.526e-2 | +1.406e-2 | bit-identical to `verify/runs/b0_mp8` |
| b4 (4 commits), mp 8, rerun | +1.694e-6 | +1.418e-4 | −1.068e-3 | bit-identical to `verify/runs/b4_mp8` |
| **th5, mp 8** | **+1.714e-6** | +1.418e-4 | −1.067e-3 | differs from b4 (21 variables) |
| **th5, mp 28** | **+1.694e-6** | +1.417e-4 | −1.036e-3 | differs from b4 (24) |
| **th5, mp 38** | **+1.332e-6** | +1.423e-4 | −1.250e-3 | differs from b4 (26) |

Criterion: \|host/P\| ≤ 3.0e-6 for each mp. All three pass.

Gates:
- **T0 (build).** Both executables were linked after the job started; 0 error lines.
- **T1 (content).** The `module_mp_thompson.F` md5 after compile (a22fda06) equals the md5 after apply. It also equals an independent sequential apply of the five patches to the extracted 315a8319 file. The th5 manifest checked against b4 **fails** (expected).
- **Markers.** The refill, noreturn and graupel-≤R1 markers are present once each in th5 and absent from b4.
- **b4 → th5 diff.** 12 hunks, +62/−10 lines: the refill replaces the 1e-10 vapour floor, the noreturn check, the graupel ≤R1 branch, and the reworked cloud-sedimentation substep. The lowest-layer threshold lines of M2 are withdrawn, as the series now holds M2. The meter-instrumented driver is byte-identical to b4's.
- **T2 / T3 (meter).** The known-bad b0 rerun reproduces +1.512e-2. The known-good b4 rerun reproduces +1.694e-6, bit for bit.

## #63 W1 and W2: restart and decomposition

Builds:
- **Serial (reused, read-only).** base = `dynfix/src_ctl`, fix = `dynfix/src_fix`.
- **dmpar (new, addendum A).** `r14_wrf/dm_base` and `dm_fix`: copies of the same trees, configure option 78.
- **Content (gate D0).** In the serial builds, `module_diffusion_em.F` and `module_big_step_utilities_em.F` are byte-equal to 315a8319 (base) and to 315a8319 + patches 0001 + 0002 (fix). Each build fails the other's manifest, neither equals +0003 (W3 absent), and `wrf.exe` is newer than both sources and objects.

Cases:
- **a:** `diff_opt=2`, `km_opt=2`.
- **d:** `diff_opt=1`, `km_opt=4`, no PBL.

Only `restart_interval` 60, `history_interval` 30 and `nproc_x/y` differ from the dynfix runs.

**Tolerance: bit for bit.** This is WRF's own standard. The `.sane/wrf` regression tests in 315a8319 (`restart.py`; `wrf_coop.py` serial vs MPI vs OpenMP) pass only when `diffwrf` writes no `fort.88`/`fort.98`. `em_quarter_ss` is not in that suite.

### Restart (serial build, straight 0–120 min vs restart from the 60-min `wrfrst`; job 10327884)

| build | case | wrfout 90, 120 min | `wrfrst` 120 min (603 vars) | `diffwrf` | verdict |
|---|---|---|---|---|---|
| base | a | identical | identical | bit for bit | PASS |
| base | d | identical | identical | bit for bit | PASS |
| fix | a | identical | identical | bit for bit | **PASS** |
| fix | d | identical | identical | bit for bit | **PASS** |

Gates:
- **D1 (reruns reproduce).** Each 1x1 straight run is bit-identical to the October dynfix run at 0/30/60/90/120 min.
- **D3 (comparator can fail).** The fix executable restarted from base's restart file differs (57 of 603 variables). A restart from its own file with one QVAPOR value moved by one float32 ulp also differs: 57 variables in the restart file, 42 in wrfout, and `diffwrf` writes `fort.88`. A file compared with itself is identical.

Closure on the 1x1 runs (res/P = domain W+P change over P; dyn = res − microphysics meter):

| build | case | res/P | mp/P | dyn/P |
|---|---|---|---|---|
| base | a | −1.068e-3 | +1.694e-6 | −1.069e-3 |
| fix | a | +1.156e-5 | +1.802e-6 | +9.76e-6 |
| base | d | +0.9296 | +6.818e-3 | +0.9228 |
| fix | d | +1.660e-2 | +1.661e-2 | −5.45e-6 |

These reproduce the README's dynfix numbers.

### Decomposition (dmpar builds; 1x1 vs 2x2 and 4x3)

dmpar builds `r14_wrf/dm_base` and `dm_fix` (job 10328230) and runs (job 10328231). Verdict rule (addendum A): fix PASS if bitwise; FAIL if base is bitwise and fix is not; INCONCLUSIVE if neither is.

| build | case | 1x1 vs 2x2, wrfout (167 vars × 5 times) | 1x1 vs 4x3, wrfout | `diffwrf` (both) | `wrfrst` 120 min (603 vars) | serial build vs dmpar 1x1 / 2x2 / 4x3 | 2x2 restart at 60 min |
|---|---|---|---|---|---|---|---|
| base | a | identical | identical | bit for bit | `MIN_PTCHSZ` only | identical | bit for bit |
| base | d | identical | identical | bit for bit | `MIN_PTCHSZ` only | identical | bit for bit |
| fix | a | identical | identical | bit for bit | `MIN_PTCHSZ` only | identical | bit for bit |
| fix | d | identical | identical | bit for bit | `MIN_PTCHSZ` only | identical | bit for bit |

**Verdicts for fix:**
- **wrfout decomposition:** PASS (a, d).
- **Serial vs MPI:** PASS. This is WRF's coop-test comparison.
- **Restart under MPI:** PASS.
- **Restart file across layouts:** INCONCLUSIVE by the letter of the rule. Neither base nor fix is bitwise, and the one differing variable is `MIN_PTCHSZ`. In the Registry it is `state integer min_ptchsz ... r` (restart only), it is passed to `module_first_rk_step_part1`, and its value is the layout's own minimum patch size. Its values (21, 32) are the same in base and fix. Every prognostic and diagnostic field in the restart file is identical.
- **Not tested:** restarting a file written in one layout on another layout.

Gates:
- **E2 (MPI is real): PASS.** Every 2x2 and 4x3 run has one rsl.error per rank and reports ntasks 2×2 or 4×3. Each run's WBMP lines number 600 × ranks, with per-tile column counts {400, 420, 441} and {130, 140, 143, 154}, against 1681 in 1x1. The same gate FAILED on the void first attempt (job 10327884: "Ntasks in X 1" in every copy, 1681 columns each), so it can fail.
- **E0 (build): FAIL by its letter, benign on inspection.** Each `compile.log` has one " error" line, `make[2]: [Makefile:441: submodules] Error 1 (ignored)`: the `git submodule` step could not fetch, and make ignored it.
  - Both builds are option 78 (dmpar) with no `-DSTUBMPI`, and both executables are newer than the job start.
  - `dyn_em` md5s: dm_base = 315a8319 and dm_fix = 315a8319 + W1 + W2. Each fails the other's manifest, and neither equals +W3.
  - Thompson and meter-driver md5s equal the serial builds'.
  - The submodule trees were not hashed.
- **Closure is unchanged by layout:** res/P is identical to the serial 1x1 values above for all three layouts. The WBMP mp/P column of the multi-rank runs is rank 0's tiles only, so it is not a closure number (declared in advance).

The void first attempt reported every serial-build 2x2 and 4x3 pair identical. Those pairs were a full-domain run against itself. `mpitest.10327986` reproduced this with `srun`, `srun --mpi=pmi2`, `srun --mpi=pmix` and `mpirun`, so the cause was the build.

Hercules: `/work2/noaa/co2/ash/ufs-chem-v1/upstream/r14_wrf/` (logs `build.10327882.log`, `run_th5.10327883.log`, `run_dyn.10327884.log`, `mpitest.10327986.log`, `dm_build.10328230.log`, `run_dm.10328231.log`). Reused read-only: `upstream/wrf/{orig,verify,dynfix}`. The `co2` project on /work2 is over its soft quota (684 T of 677 T, 6-day grace); r14_wrf adds about 20 GB (`dm/` 6.9 GB, `dyn/` 7.8 GB, two dmpar trees, `th5`, `runs/`).
