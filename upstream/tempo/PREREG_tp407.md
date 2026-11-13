# #407 update (merge ufs/dev + TH5): what is tested, before it runs

**Status (13 November 2026).** Registered before any build. Done = push `pr1-tempo` 1c664a4f to the fork if every gate
below passes; otherwise report and do not push.

**Result: all gates pass; pushed 13 Nov (fork `pr1-tempo` ca0fb920 → 1c664a4f, #407 mergeable; note 6848990859).**

| Gate | Result (job 10460986, 32 min, rt.sh rc 0) |
|---|---|
| G0, G1 | pass (setup script) |
| G2 | `atm_dyn32_oneapi` compiles |
| G3 | `control_p8_ugwpv1` PASS (44 files identical) |
| G4 | all three TEMPO tests reach the end-of-run wall-time line; every compared file NOT IDENTICAL against real baselines |

f000 already differs in `clwmr` (1e-33 level), `spfh`, `dpres`, `o3mr`, `tmp` (8783 pts), `pressfc` (3854 pts): physics runs
before the f000 write; not separately attributed to TH5 vs the mass basis (rt_mp2 per-file logs were overwritten).

## What is already covered

- Merge commit 04788c6e: `mp_tempo.F90` and `.meta` are byte-identical (md5) to 44cc136e, the #407 rebase that
  package 2 (`pr1-mp2` e52c75af) carried through the full RT `rt_mp2` (job 10327345 + rerun 10329068, WM develop
  560345cc, Intel + GNU): 151 baseline changes, 109 pass, 25 restart tests not started, 1 run failure
  (`cpld_debug_sfs_gnu`, fails on develop). ufs/dev b7cb19b1 → 7ab37e41 changes nothing under `physics/MP/`.
- TH5 in commit 1c664a4f is the D7T5 expression (`runs_29oct/tempo_v325.md`): at noise in the C96 forecast on
  TEMPO v3.2.5; ρ·dz equals the host mass to 4e-16 in the column test. Not yet through CCPP metadata or an RT.

## This test (`rt_tp407`)

- Tree: WM develop 517e02c9, UFSATM d0d6c3ff, ccpp-physics 1c664a4f (base 7ab37e41 = develop's pin), `tempo_v3`
  c62699f. Physics brought in by bundle from the local clone (not pushed).
- `rt.sh -a lpdm -e -k -l tp407.conf` vs `develop-20261104`: COMPILE `atm_dyn32` oneapi (Intel; the label in rt.conf), RUN
  `control_p8_ugwpv1_tempo`, `control_p8_ugwpv1_tempo_aerosol`, `regional_wofs_tempo`, `control_p8_ugwpv1`.

## Gates (all must hold)

| | Gate | Fails if |
|---|---|---|
| G0 | tree pins | WM ≠ 517e02c9, UFSATM ≠ d0d6c3ff, physics base ≠ 7ab37e41, `tempo_v3` ≠ c62699f |
| G1 | physics diff vs 7ab37e41 = #407's ± lines + TH5's ± lines, nothing else | any other line; known-bad: 04788c6e alone (no TH5) must differ |
| G2 | compile `atm_dyn32` succeeds (CCPP capgen accepts the `prsi` metadata) | compile fails |
| G3 | null: `control_p8_ugwpv1` (Thompson suite; nothing it runs is changed) IDENTICAL to baseline | NOT IDENTICAL: change leaks outside TEMPO, or the compare is off |
| G4 | the three TEMPO tests run to completion and are NOT IDENTICAL (#407 changes answers) | crash, or IDENTICAL (code not live) |

G3 is the can-fail check for the comparison; G4's "NOT IDENTICAL" is the can-fail check that the branch is in the build.
Run: job 10460986 (setup re-run 12 Nov 23:48 after its grep matched `intel`, not rt.conf's `oneapi`, and stopped
under `set -e` before writing the conf; gates unchanged). Not tested here: GNU (no TEMPO test is GNU), restart/decomposition reproducibility (package 2's full RT will).
