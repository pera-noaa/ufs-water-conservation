# NCAR/TEMPO port (C2, C3, T1 on c62699f): what is tested, before it runs

**Status (13 November 2026).** Registered before any build. Branches built, gated and through TEMPO CI. Launched on
Hercules in `$U/cons/tp_port` (build 10468157, runs 10468158; deviations in *Launch, as run*). **Done: G0–G4 pass**
(G5 not run); results below; the PR body and the T1 issue carry the c62699f rows.

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

### Launch, as run (deviations from steps 1–3)

- **No `tp_attr` on Hercules.** Scripts are `tp389`'s (`tp_build5.sbatch`, `tp_mkrun.sh`, `tp_runs3.sbatch`, `tp_budget.py`), with paths changed
  only; runs use 160 tasks on 2 nodes, as the RT and `tp389` (not 144).
- **B is not `tp389`'s D7T5.** D7T5's TH5 is the 29 Oct form (no `prsi` argument; same `.meta` as D7), so it is not
  1c664a4f. B, C2, C3, C23, T1 take 1c664a4f's `mp_tempo.F90`/`.meta` plus the meter; N5 takes 04788c6e's plus the meter.
  The meter is `tp389_in/meter_port.py`, extended to sources that already take `prsi` (`tp_port_in/meter_port2.py`).
  Result: N5's metered `mp_tempo.F90` is byte-identical to `tp389`'s D7 (md5 e528eff1); every `.meta` is identical (6f4dbcb4).
- **G1 meter check** (`g1.py`): the lines the meter adds to B and to N5 are the same multiset apart from N5's `prsi`
  declaration and `[prsi]` block (41 and 50 lines): PASS; a copy of B with one meter coefficient changed: caught.
- **Tree:** a copy of `rt_tp407` (no `stmp/`, no executables), built per variant in one job; run template = the
  `rt_tp407` RT run dir of `control_p8_ugwpv1_tempo` (hard links; the same 122 names as `tp389/tmpl`, outputs left out,
  empty `RESTART/`), so the runs load that tree's spack-stack 2.1 modules.

| Run | Build job | Run job | 0–6 h | 6–12 h | 12–18 h | 18–24 h | 6–24 h | Σ\|R\|/P 6–24 h | P 6–24 h (kg/m²) |
|---|---|---|---|---|---|---|---|---|---|
| B | 10468157 | 10468158 | +1.24657 | +0.41891 | +0.44063 | +0.43361 | +0.43154 | 0.92922 % | 0.8079 |
| C2 | 10468157 | 10468158 | +0.49787 | +0.42904 | +0.43551 | +0.43587 | +0.43371 | 0.93130 % | 0.8073 |
| C3 | 10468157 | 10468158 | +1.32175 | +0.48041 | +0.50112 | +0.52476 | +0.50376 | 0.89015 % | 0.8049 |
| C23 | 10468157 | 10468158 | +0.55752 | +0.47981 | +0.49761 | +0.51715 | +0.49958 | 0.88383 % | 0.8051 |
| T1 | 10468157 | 10468158 | +0.33614 | −0.33876 | −0.30182 | −0.33450 | −0.32501 | 0.35015 % | 0.7734 |
| N5 | 10468157 | 10468158 | +1.24945 | +0.40579 | +0.43049 | +0.42507 | +0.42112 | 0.91950 % | 0.8074 |

### Result

| Gate | Result |
|---|---|
| G0 pins | pass: tree 517e02c9 / 1c664a4f / c62699f; every variant's sources as the table (`exe/manifest.txt`) |
| G1 one fix each | pass (scheme branches locally; meter multiset check above) |
| G2 meter | pass: 17280 `TPW` records = 120 steps × 144 ranks in every run; all `rc=0`, `atmf024` written |
| G3 reproduces `tp389` | pass: N5 +0.421 (target +0.434 ± 0.03), B +0.432 (target +0.450 ± 0.03) |
| G4 code live | pass: every variant differs from B in every window |

Against the predictions (Run − B; agreement = same sign and within 2×):

| Run − B | 0–6 h | 6–24 h | P 6–24 h | |
|---|---|---|---|---|
| C2 | −0.749 (pred −0.83) | +0.002 (pred −0.005) | −0.07 % (pred +0.1 %) | 0–6 h agrees; 6–24 h and P are below the `tp389` P noise (±0.15 %), sign not meaningful |
| C3 | +0.075 (pred +0.02) | +0.072 (pred +0.04) | −0.37 % (pred −0.4 %) | 6–24 h and P agree; 0–6 h 3.7× |
| C23 | −0.689 | +0.068 (pred +0.04) | −0.35 % (pred −0.3 %) | agrees; additive to 0.006 at 6–24 h (C2 + C3 = +0.074) |
| T1 | −0.910 (pred −0.72) | −0.757 (pred −0.64; R flips to −0.325) | −4.3 % (pred −5 %) | agrees |
| B − N5 (TH5) | −0.003 (pred +0.01) | +0.010 (pred +0.016) | +0.06 % (noise) | 6–24 h agrees; 0–6 h at noise |

- **On `main` the net residual is +0.43 % (6–24 h), and the PR raises it to +0.50 %:** C3 removes a 0.07 % sink that
  offsets part of T1's source. The gross error Σ|R|/P falls 0.929 → 0.884 %; C2 removes 0.75 of the 1.25 % created in
  the first 6 h.
- **T1 is the main source at c62699f too:** fixing it turns +0.43 % into −0.33 % (the sinks C1 and r1 left), cuts
  Σ|R|/P to 0.35 %, and lowers grid-scale precipitation 4.3 %.
- One case (C96, 24 h, one start), no null run (G5), so differences below ~0.01 % of R/P and 0.15 % of P are not resolved.

TEMPO CI on the fork (build, unit tests, MPAS 59-level column test; no stored answers, so it checks build and run
only): `water-graupel-density` run 43497234719, `fallback-sign` 43497239698, `main` 43497244608 (control), all pass.
