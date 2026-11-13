# TEMPO `tempo_v3.3.0` (with #59, #61, #62) and the entry-density fix: what is tested, before it runs

**Status (13 November 2026).** Registered before any build. NCAR merged the fallback sign (#61, = T1) and the graupel
re-close (#62, Anders's form of C2, also re-closing the graupel volume) into `tempo_v3.3.0` at 71588d1. The entry
density (C3) is not in it. Done = every gate passes and the table is filled; then the density-only PR quotes these runs.
**Done: G0–G4 pass** (build 10468464, runs 10468465); results below.

## Code under test

| Variant | TEMPO sources | `module_mp_tempo_main.F90` md5 | Fix |
|---|---|---|---|
| V3 | `tempo_v3.3.0` 71588d1 (`main`, `cfgs`, `utils`) | b40d4385df0d190dee724d4d899d4933 | — |
| V3C3 | V3 + C3 (db01901d cherry-picked: local branch `entry-density-v330` 0182132) | f2de1c0ba476e560ad16917d64b63bbd | entry density |
| V3n | V3's binary, `consv_te = 0.999` | as V3 | noise control |

`cfgs` 47e668eb, `utils` 26961f7d for all three. Driver: 1c664a4f + meter, as `PREREG_tempo_port.md`'s B (`mp_tempo.F90`
8b34e516, `.meta` 6f4dbcb4). Tree, template and scripts: `$U/cons/tp_port` (same tree as B; only TEMPO's three files
change).

## Gates (all must hold)

| | Gate | Fails if |
|---|---|---|
| G0 | pins | any source md5 ≠ the table; driver ≠ B's |
| G1 | one fix | V3C3 ≠ V3 + exactly db01901d's lines (checked locally: PASS; known-bad, the C2 + C3 lines, caught) |
| G2 | meter | any run lacks a `TPW` record (120 steps × 144 ranks), `rc ≠ 0` or no `atmf024` |
| G3 | code live | V3 equals c62699f's B (`PREREG_tempo_port.md`) in every window to 1e-4 |
| G4 | fix live | V3C3 equals V3 in every window to 1e-4 |

## Predictions (from the c62699f runs; reported against, not gates)

| | 0–6 h | 6–24 h | P 6–24 h |
|---|---|---|---|
| V3 (≈ c62699f's T1 run + C2's 0–6 h effect) | ≈ −0.41 | ≈ −0.32 (± 0.10) | ≈ 0.773 kg/m² (B − 4.3 %) |
| V3C3 − V3 (C3 removes a sink) | ≈ +0.07 | ≈ +0.07 | ≈ −0.37 % |
| V3n − V3 | — | — | the P noise; C3's P change is resolved only if larger |

#59 (snow moments) and #61's other two fixes (`precip` intent, bottom fall speed) also change answers, so V3 may miss
by more than T1 and C2 alone would; a miss is reported, not tuned. Same sign and within 2× is agreement.

## Runs

| Run | Build job | Run job | 0–6 h | 6–12 h | 12–18 h | 18–24 h | 6–24 h | Σ\|R\|/P 6–24 h | P 6–24 h (kg/m²) |
|---|---|---|---|---|---|---|---|---|---|
| V3 | 10468464 | 10468465 | −0.46583 | −0.34131 | −0.30733 | −0.35921 | −0.33669 | 0.33965 % | 0.7684 |
| V3C3 | 10468464 | 10468465 | −0.30949 | −0.20196 | −0.16680 | −0.19355 | −0.18725 | 0.18725 % | 0.7677 |
| V3n | 10468464 | 10468465 | −0.46538 | −0.33960 | −0.30861 | −0.36175 | −0.33758 | 0.34053 % | 0.7692 |

### Result

| Gate | Result |
|---|---|
| G0 pins | pass: `exe/manifest.txt` V3 = driver 8b34e516, main b40d4385, cfgs 47e668eb, utils 26961f7d; V3C3 main f2de1c0b; V3n runs V3's binary (`cmp` identical) with `consv_te = 0.999` |
| G1 one fix | pass (locally, before the build) |
| G2 meter | pass: 17280 `TPW` records, `rc=0` and `atmf024.nc` in all three runs |
| G3 code live | pass: V3 differs from B in every window (6–24 h −0.337 vs +0.432) |
| G4 fix live | pass: V3C3 differs from V3 in every window by 0.14–0.17, against a noise pair difference ≤ 0.003 |

Against the predictions (agreement = same sign and within 2×):

| | 0–6 h | 6–24 h | P 6–24 h | |
|---|---|---|---|---|
| V3 | −0.466 (pred −0.41) | −0.337 (pred −0.32 ± 0.10) | 0.7684 (pred 0.773) | agrees: v3.3.0 sits where c62699f's T1 run did (−0.325) |
| V3C3 − V3 | +0.156 (pred +0.07) | +0.149 (pred +0.07) | −0.09 % (pred −0.37 %) | same sign; 2.1× the prediction, just outside the rule; P not resolved |
| V3n − V3 | +0.0005 | −0.0009 | +0.10 % | the noise floor |

- **On `tempo_v3.3.0` the scheme now destroys water** (−0.34 % of its precipitation, 6–24 h), as c62699f did with only T1
  fixed. What remains are sinks: C3 (0.15) and C1, r1 (the rest).
- **C3 is twice as large here as at c62699f** (+0.149 against +0.072), so it removes 44 % of v3.3.0's residual
  (−0.337 → −0.187) and of its gross error Σ|R|/P (0.340 → 0.187 %). Why it grew is not tested; #62's bottom fall
  speed (`wi(nz+1) = vt(nz)`) changes the flux C3's density acts on and is the first candidate.
- **C3's precipitation change (−0.09 %) is inside the noise** (V3n − V3 = +0.10 %); one case, one start, so the PR
  claims the water, not a precipitation change.

**Forecast impact** (`tp_port/fi_v330.py`, not pre-registered; known-good V3 against itself gives 0): at 24 h, rms
(V3C3 − V3) / rms (V3n − V3) = 0.95–1.04 for 3-D T, q, u, v, cloud, rain, ice, snow, graupel, surface pressure,
2-m T, precipitable water and the 18–24 h precipitation rate (`fi_v330.py` md5 9a60d533): at noise, against one noise
run. Hail and number concentrations are not in the output, so not compared.

**Branch after the runs:** 79fa6c6 shortens the code comment only (`git diff 0182132..79fa6c6`: two comment lines);
the runs measured 0182132.

**Correction (red team, 13 Nov).** *Predictions* above names `precip` intent and the bottom fall speed as #61's; #61
(4874168) has the fallback sign and the `precip` intent, and the bottom fall speed `wi(nz+1) = vt(nz)` is in #62
(71588d1). The predictions are unchanged by this. The recompute after sedimentation (L834) is not touched by C3, so
code after it still sees the heated density.
