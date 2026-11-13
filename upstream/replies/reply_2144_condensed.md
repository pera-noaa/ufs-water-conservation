@climbfuji Sorry for the length! This was just a heads-up; the repo fixes (#2145, #2146) are already merged into `release/2.2`. What's left is in the installed Orion/Hercules envs, for EPIC:

1. 1.9.x/2.1.x meta-modules predate #2145, so `stack-gcc/13.3.0` and `stack-intel-oneapi-compilers/2025.3.1` need a `module use` first.
2. `intel-oneapi-compilers/2025.3.1.lua` sets `INTEL_ONEAPI_COMPILERS_ROOT` and `INTEL_PATH` to nonexistent paths.
3. Hercules OpenMPI 4.1.6 links to the removed `/opt/slurm-24-11.3`, so plain `srun` fails.
4. 1.9.x oneAPI `ufs-weather-model-env` needs `scotch/7.0.4`, found only in a gcc branch.
5. 1.9.3 `crtm-fix` and 1.9.1 `nofmsio` lack the install-time `stack-oneapi` edit, so loading loops.

Happy to close this or move it to an `[INSTALL]` issue.
