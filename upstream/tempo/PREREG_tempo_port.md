# NCAR/TEMPO port (C2, C3, T1 on c62699f): what is tested, before it runs

**Status (13 November 2026).** Registered before any build. Branches built, gated and through TEMPO CI; the UFS meter
runs are **not launched**: Hercules was down (broker: last drop 13 Nov 01:57Z, master gone) and a Duo push was not
triggered. Done = every gate below passes and the table is filled; then the PR body and the T1 issue get the
c62699f numbers.

## Code under test

NCAR/TEMPO `main` c62699fb (`tempo_v3`, = ufs/dev 7ab37e41's pin). Fork `pera-noaa/TEMPO`, local clone
`/Users/pera/Documents/ash-code/TEMPO`.

| Variant | `module_mp_tempo_main.F90` from | md5 | Fix |
|---|---|---|---|
| B (base) | c62699fb | 6654feece617901b35cb780eb88d029d | — |
| C2 | `water-graupel-density~1` ca8252d5 | b664f004d6ebbc3ce845c7b7f2f08a0a | graupel re-close + snow-gain cap |
| C3 | `c3-only` 4f04f61d (db01901d cherry-picked onto c62699fb; local, not pushed) | e04a537f8c746e868a026d72e1a62fd7 | entry density |
| C23 | `water-graupel-density` db01901d | 2463fe8472d0d0e1ea604616296d64ba | C2 + C3 (the PR) |
| T1 | `fallback-sign` 10dc4577 | b9176df089cc470e1e1cc6e5b7da5ff7 | fallback sign |
| N5 | c62699fb, with physics 04788c6e (#407 mass basis, no TH5) | 6654feece617901b35cb780eb88d029d | TH5's before |

Physics for B, C2, C3, C23, T1: ccpp-physics 1c664a4f (`pera-noaa/ccpp-physics` `pr1-tempo`, #407 + TH5) plus the
`TPW` meter. N5: 04788c6e (1c664a4f's parent) plus the same meter. Tree as `rt_tp407` (WM 517e02c9, UFSATM d0d6c3ff).

## Runs

C96 `control_p8_ugwpv1_tempo`, 24 h, 720 s, `-D32BIT=ON`, 144 compute ranks, meter on (method as `results.md`).
Optional seventh run Bn: B's binary run again (null). Hercules `$U/cons/tp_port` (new; scripts copied from `tp_attr`,
meter sources from `tp389`; nothing in either edited).

## Gates (all must hold)

| | Gate | Fails if |
|---|---|---|
| G0 | pins | tree ≠ the hashes above; `tempo_v3` md5 ≠ the table's for any variant |
| G1 | each variant = B + exactly its fix | scheme: `git diff c62699fb..<branch>` ≠ the fix's hunks of `patches/ports/TEMPO-scheme/0001`/`0002` (checked locally, all PASS; known-bads caught: a stray `rho`→`rhon` at the entry `thermo_vars`, a stray `<=` in T1, C2 alone against the C2+C3 spec, the full 0001 against the branch). N5: `mp_tempo.F90` differs from B's only by TH5's lines (1c664a4f: +7/−5 `.F90`, +8 `.meta`), meter lines identical |
| G2 | meter | any step lacks a rank; meter lines differ between builds |
| G3 | reproduces `tp389` (same TEMPO, WM 560345cc) | N5 6–24 h outside +0.434 ± 0.03 % (D7) or B outside +0.450 ± 0.03 % (D7T5). Then stop: tree or meter differs, variants not interpreted |
| G4 | code live | any variant's R/P equals B's in every window to 1e-4 |
| G5 | null (if Bn runs) | Bn ≠ B; then |Bn − B| is the floor for G4 and the predictions |

`results.md`'s +0.38 % is the old pin's (2856696); at c62699f, B is expected at `tp389`'s +0.45 %.

## Predictions (old-pin add-one deltas from `results.md`; reported against, not gates)

| Run − B | 0–6 h | 6–24 h | P 6–24 h |
|---|---|---|---|
| C2 | ≈ −0.83 (removes most of the spin-up leak) | ≈ −0.005 | ≈ +0.1 % |
| C3 | ≈ +0.02 | ≈ +0.04 | ≈ −0.4 % |
| C23 | ≈ C2 + C3 (additive to 0.01 at 6–24 h) | ≈ +0.04 | ≈ −0.3 % |
| T1 | ≈ −0.72 | ≈ −0.64 (sign of R flips) | ≈ −5 % |
| B − N5 (TH5) | ≈ +0.01 | ≈ +0.016 | noise (`tp389` pair: P ±0.15 %) |

Same sign and within a factor 2 is agreement. The hail physics added since 2856696 (+529/−132) can move magnitudes;
a miss is reported as a finding, not tuned.

## Launch (when Hercules is live)

1. Copy `rt_tp407`'s tree to `$U/cons/tp_port`; install each `module_mp_tempo_main.F90` from the fork (git fetch of
   `pera-noaa/TEMPO`; C3 by `git cherry-pick db01901d` onto c62699fb); check md5s (G0).
2. Meter: B from `tp389`'s metered D7T5 `mp_tempo.F90`, N5 from its metered D7, after checking each equals
   1c664a4f / 04788c6e plus the meter lines (G1).
3. Build and run with `tp_attr`'s sbatch scripts (6 builds or one build per variant, 24 h runs); record job IDs here.
4. Tabulate each run dir with `tp_attr`'s `tp_budget.py` (same invocation as `tp_attr`'s run script), as
   `results.md`'s Runs table: R/P per 6-h window, 6–24 h, Σ|R|/P, P 6–24 h.

| Run | Build job | Run job | 0–6 h | 6–12 h | 12–18 h | 18–24 h | 6–24 h | Σ\|R\|/P 6–24 h | P 6–24 h (kg/m²) |
|---|---|---|---|---|---|---|---|---|---|
| B | | | | | | | | | |
| C2 | | | | | | | | | |
| C3 | | | | | | | | | |
| C23 | | | | | | | | | |
| T1 | | | | | | | | | |
| N5 | | | | | | | | | |

TEMPO CI on the fork (build, unit tests, MPAS 59-level column test; no stored answers, so it checks build and run
only): `water-graupel-density` run 43497234719, `fallback-sign` 43497239698, `main` 43497244608 (control), all pass.
