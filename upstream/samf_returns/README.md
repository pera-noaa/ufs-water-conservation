# SAMF deep early returns: block dependence, deletion, and a single-exit fallback

## Status (28 October 2026)

- **Question:** Lisa (#408) asked for one bypass flag covering progomega, the CA trigger and coldpool (#403).
- **Finding:** an early return is only safe if nothing after it still has work for a quiet column. Each feature adds such work:

| Feature | Work after the returns | In |
|---|---|---|
| CA trigger | turns columns back on (`ca_deep > nthresh`) | develop, #403 |
| progomega | updraft memory turns columns on (`ufs/dev` L1902–1904); with `dt_decay`, `progomega_calc` decays memory in every quiet column | develop; decay #403 only |
| coldpool | relaxes `buoyexcs` in every column | #403 |
| MG (`mp_phys_mg`) | `qlcn`/`qicn` become increments at the end; an early return leaves the full cloud water | develop (latent: no UFS suite pairs SAMF deep with MG) |

- **Proposed (posted to #408, [comment](https://github.com/ufs-community/ccpp-physics/pull/408#issuecomment-6485108259)):** delete the 10 early returns. Block-independent by construction, no flag. Fallback if the cost is unwanted: `pending(i)` (CA above threshold, or any updraft memory) and a single exit, each return becoming `if (.not. any(cnvflg .or. pending)) go to 900`, where 900 does the every-column work (`buoyexcs` relaxation, MG outputs) before the tendencies.
- **Block test:** standalone gfortran build, 6 synthetic columns, run as blocks of 6, 4, 2 and 1. Reference: the same source with every early return disabled (`noret`), itself block-independent in every case. Comparison is bit-for-bit over all outputs.

| Source | Combos × block sizes identical to the reference | Differs |
|---|---|---|
| #403 as posted (2a95266) | 6 of 11 | coldpool alone (`buoyexcs`), progomega alone (`omegaout`), coldpool + CA, MG (`qlcn`/`qicn`), CA + MYNN (convection lost in 2 columns, 25 fields) |
| #403 + `pending` | 11 of 11 | — |
| #403 + `pending` without progomega (known-bad) | — | progomega (`omegaout`) |
| #408 as posted (f5a9fc81) | 11 of 12 | MG only (from develop) |
| #408 + `pending` | 12 of 12 | — |

- **Cost of deleting them, standalone** (Hercules, ifort 2023.1 with the UFS release flags, one pinned core, 7 interleaved rounds; µs per column, minimum):

| Case | With returns | Without | Ratio |
|---|---|---|---|
| Quiet column, features off (#408 / #403) | 24.3 / 24.9 | 51.9 / 52.6 | 2.1× |
| Quiet column, all features on (#408) | 36.8 | 56.8 | 1.5× |
| Quiet column, all features on (#403; its guard already disables the returns) | 60.8 | 60.7 | 1.0× |
| Convecting column, or a block of 6 with one convecting column | equal | equal | 1.0× |

- **Cost in UFS:** WM develop 783f524a, `control_p8` (C96, `FV3_GFS_v17_p8_ugwpv1`, blocksize 32), 3 interleaved runs of each on Hercules. Outputs bit-identical (6 of 6 files in every pair).

| | develop | returns deleted |
|---|---|---|
| `GFS Physics` clock, PE 0 [s] | 37.12, 37.20, 37.32 | 37.70, 37.72, 37.72 |
| Total wall time [s] | 159.7, 158.6, 157.6 | 158.1, 153.4, 157.6 |

  Physics +0.50 s (+1.3 %), well outside its 0.2 s spread; total wall time within its noise. The FMS clock is PE 0's only.
- **Open:** in #408 the progomega term in `pending` couldn't be made to matter (a conservative superset there). Neither change is checked in a full UFS RT or a layout test yet. #403's guard (`.not.progomega .or. .not.coldpool`) keeps the returns unless both flags are on; #403 is 21 commits behind `ufs/dev` and lacks the memory re-enable.

## Files

`drv.f90` (#403 interface) and `drv408.f90`: driver, `drv <cp po ca mg my me> <block size> <out>`. `mkvariants.py`, `mkvariants408.py`: make `noret` and `proto`. `build.sh`, `build2.sh`: compile (`-fcheck=all -ffpe-trap=invalid,zero,overflow`). `cmp.py`, `cmp408.py`: compare. `proto_on_403.diff`, `proto_on_408.diff`: the `pending` fallback. `results_403.txt`, `results_408.txt`: block-test tables.

Timing: `tdrvh.f90`, `tdrvh408.f90` (driver, 64-bit clock; `drv <flags> <nb> <out> <nrep> [column]`), `samf_timing.sb` (standalone job), `timing_standalone.txt`; `rettime_setup.sh` (login node: WM tree) and `rettime_build.sb` (both builds, 3 + 3 `control_p8` runs), `timing_control_p8.txt`. Hercules: `/work2/noaa/co2/ash/ufs-chem-v1/samf_timing`, `/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/rettime` (`run_*` are the failed first attempt, built for the wrong suite; `run2_*` are the measured runs).

Flags: `cp` coldpool, `po` progomega, `ca` CA trigger, `mg` MG outputs, `my` MYNN `maxMF > 0` in the CA columns, `me` strong memory in columns 1, 3, 5.
