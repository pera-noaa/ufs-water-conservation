<!-- POSTED 12 Nov 2026, untagged: https://github.com/NCAR/ccpp-physics/issues/1251. Trimmed 12 Nov to the reachable bug; the latent-cases table is in git history (d45d7bb^). Re-checked 12 Nov line by line (after a field-table misread was caught): ccpp-physics ufs/dev
     7ab37e41 and NCAR main 2a669458; ccpp-scm 928aef9d (suites, physics namelists, scm/src/GFS_typedefs.F90, run_scm.py);
     ufs-weather-model 3d0703d2 (suites, RT tests, parm templates, field tables, read with comment lines excluded).
     This is the only one reachable in a shipped configuration, in the SCM: post it to NCAR/ccpp-physics. Not run (SCM not built). -->

**Title:** `shinhongvdif`: ozone PBL tendency diagnostic uses stale loop indices

# Description

In `shinhongvdif.F90` L1139–L1144 (NCAR `main` 2a669458; same in `ufs/dev`), the ozone tendency diagnostic is outside the loops:

```fortran
dtend(:,:,idtend) = dtend(:,:,idtend) + ten_q(i,k,ntoz)*dtstep
```

`i` and `k` are left at `ite+1` and `kts−1`, which is `ten_q(1,1,ntoz)` in column-major order: a release build adds that one value everywhere, and a bounds-checked build traps. The humidity diagnostic above uses `ten_q(:,:,ntqv)`; the fix is `ten_q(:,:,ntoz)`.

It is reached in the SCM with `SCM_GFS_v15p2_saYSU` (`_ps` suite only), whose namelist sets `shinhong`, `ldiag3d` and `qdiag3d`; no UFS suite uses `shinhongvdif`. Found by reading the code, not run.
