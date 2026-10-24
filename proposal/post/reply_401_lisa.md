@lisa-bengtsson Yes, on Hercules: `/work2/noaa/co2/ash/share/ccpp401` (`README.txt` first). All are `hafs_global_1nest_atm` as `rt.sh` sets it up (`progsigma` = .false.), with print-only blocks that leave the RT baselines bitwise identical.

- `develop_48h/`: develop f1d68949 with no changes of ours, run to 48 h. It stops at about 19 h with the `compute_qs` overflow.
- `develop/`: the same build, 6 h; it finishes.
- `crash_24fixes/`: plus our 24 fixes (diffs included); it stops within 6 h.

Each has `fv3.exe`, `INPUT/`, the namelists, `field_table`, `model_configure`, `job_card` (change `--account`), `out` and `err`. If you are not on Hercules, tell me which machine and I will copy it there.
