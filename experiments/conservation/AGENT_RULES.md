# Rules for every conservation agent (read first)

- Hercules ONLY via `broker run --timeout <S> hercules -- '<cmd>'` (`--timeout` before the host). `broker status` first.
  NEVER `ssh hercules`/`ssh orion`, NEVER `broker connect` (Duo push to Ash's phone). If hercules is not LIVE, stop and report.
- Keep each command's output small (head/tail/grep; logs to files). Big outputs hang the connection on this network.
- SLURM `-A co2 -p hercules -q batch` (debug QOS is shared, 2 jobs/user: don't use it). ≤ 2 of your own jobs queued at once.
  scancel only your own job IDs. Never build on the login node.
- Write ONLY inside your own Hercules dir and your own local folder. Everything else is read-only — in particular other
  agents' dirs under `$U/cons/`, `$U/p20rt_final`, `$U/patched*`, `$U/rt/*`, `variants/`. Copy files you edit as real
  files; never write through a symlink (an agent already corrupted a shared RT field_table that way once).
  `rm -rf` only with `"${var:?}"` guards and only on what you created.
- Python: scripts in files (no `python -c`), on Hercules `/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I`.
- No GitHub, email, or messages outside this session. Nothing is posted.
- Bar ("we only want to propose fixes that we are absolutely sure are improvements"): code-level explanation; a meter
  showing the fix closes exactly its term; a comparison against the unfixed run showing no change beyond the defect's own
  signal (use the consv_te=0.999 control `ctlc999` trick for threshold noise); a red-team pass (restart, decomposition,
  other suites/hosts sharing the code). Classify every change as BUG FIX (restores what the code intends) or PHYSICS
  CHANGE (adds a missing physical term / changes a design choice); for physics changes quantify the forecast impact.
- Meters are separate diffs from fixes. Fix diffs must apply on top of `$U/cons/energy/fx` (base + FX1 SG1 CP1, no meters).
- Keep `report.md` in your local folder updated AS YOU GO (status block at top). It is the hand-off if you run out of context.
- they/them for anyone whose pronouns you don't know.
- Release builds (-O3 -march=core-avx2) let ifort fuse multiply-adds, so editing ANY physics file can change round-off elsewhere. A claim that a meter is passive or a switch-off is bitwise inert needs `-no-fma` builds of both arms (`$U/cons/samfinit/tools/nofma.py` patches cmake/IntelMixed.cmake); otherwise judge differences against the ctlc999 noise control.
