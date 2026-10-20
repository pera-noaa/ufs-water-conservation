# SAMF sub-cloud overshoot in `hafs_global_1nest_atm`: instrumentation and ensembles

Evidence for the SAMF issue (`../pr_round1_descriptions.md` §8) and for the *HAFS crash* section of `../pr_round1.md`.
Runs: Hercules, Intel, `hafs_global_1nest_atm` 6 h, 6 nodes, about 2.5 min each. Copied from
`/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/` (`hafs_exp/` and the tree scripts).

| File | What |
|---|---|
| `dbg4_deep.f`, `dbg4_shal.f` | print-only blocks inserted in `samfdeepcnv.f` / `samfshalcnv.f` before "Negative moisture is set to zero after borrowing": one `DBGSAMF`/`DBGSHAL` line per layer with a single-step heating above 4 K (column, layer, `kb`, `kbcon`, `jmin`, `ktcon`, dT, dq, `xmb`, `xmbmax`, CFL, `eta`, `del`, mean TKE, `clamt`); `DBGTKE` for columns with mean TKE > 28 (capped `clamt`); `DBGPRF` the sub-cloud profile when CFL > 10 |
| `dbgtke.F`, `dbgtk_i3.f90`, `dbgtk_mp.f90`, `tketrace4.py` | print-only TKE trace through the PBL, the interstitials and microphysics; the per-step TKE budget at the hotspot |
| `fixb.f` | option A: also bound `xmbmax` by `dp/(g·dt·eta)` for `kb ≤ k < kbcon` (the patch is `../pr_round1_patches/ccpp-physics_samfcfl/`) |
| `q_r37.sh`, `q_t1a.sh`, `q_ens.sh`, `q_ens3.sh`, `q_runs.sh` | build an instrumented tree from the pristine develop clone plus a set of fix branches, compile, launch members |
| `mkexp.sh` | one member: copy the RT run directory, install the executable, set `consv_te` (1, 0.999, …) |
| `q_stats.py` | per member: finished, crashed, events > 4 K, of those with CFL > 1 and > 5, > 10 K, largest dT and CFL, TKE, mean precipitation |
| `q_t1a_stats.txt`, `q_ens_stats.txt`, `q_ens_np_stats.txt`, `q_ens3_stats.txt` | the outputs (`q_ens3_stats.txt` has every member) |

Tree names in the statistics: `dev` develop (f1d68949); `r37` all 37 round-1 fixes; `t1a` SAMF + PBL, Noah-MP, sea
ice/NSST, GFDL MP v3, SAMF32 build; `t1ans` the same without sea ice/NSST; `t1anp` without PBL05; `t1ar` without the
NSST rain fix; `t1ai` without the three sea-ice fixes; `t1ac` `t1a` + FV3.
