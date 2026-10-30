# TEMPO on v3.2.5: #407 re-measured, TH5 noise pair

**Status (29 October 2026).** Measured after ccpp-physics#389 merged (`ufs/dev` b7cb19b1, TEMPO `tempo_v3.2.5` c62699f, WM develop 560345cc).
- **#407 still does its job on v3.2.5.** It halves the gross column error (Σ|R|/P 1.85 → 0.93 %). The net residual rises +0.18 → +0.43 % because develop's mismatched round trip removes about 0.25 % net, which hides TEMPO's own creation. #407's body already says this. TEMPO's own creation, +0.43 %, is close to October's +0.38 % on 2856696.
- **#407's body quotes +0.33 %.** On v3.2.5 that figure is +0.43 % (6–24 h); update it when the package-2 bodies are written.
- **TH5 (driver layer depth) is at noise in the forecast.** Its T and ps rms are 1.02× and 0.96× the `consv_te` 0.999 pair; its precipitation change, +0.028 %, is inside the pair's −0.039 %. The triage's F gap (row #60) is closed for one case and one member.
- **TH5's net water effect is not its closure.** Added to #407 it raises the net residual by +0.016 %; the noise pair moves it by −0.001 %. In October's leave-one-out (other leaks fixed) it removed 0.011 %. With the core leaks present, the net mixes TH5's term with their sedimentation. Its term closes exactly in the column test (ρ·dz vs host mass 4.7e-3 → 4e-16, ports/README.md). An in-model closure needs the `all` variant, and the October core fixes do not apply to v3.2.5 (≈660 changed lines).
- **#407 in the forecast:** T and ps rms at noise (1.03×, 1.01×); precipitation −0.12 % against develop, 3× the pair's change, in the direction of the water develop removes.

## Runs

C96 `control_p8_ugwpv1_tempo`, 24 h, 720 s steps, 144 ranks. Meter `TPW` (as `tempo_attr/`): Σ area·(host-frame column water change + the call's precipitation), per rank. Hercules `$U/cons/tp389`; builds 10327340, 10327522; runs 10327343, 10327523.

| Run | Code | 0–6 h | 6–12 h | 12–18 h | 18–24 h | 6–24 h | Σ\|R\|/P 6–24 h | P 6–24 h (kg/m²) |
|---|---|---|---|---|---|---|---|---|
| D0 | develop + meter | +0.871 | +0.091 | +0.183 | +0.255 | +0.183 | 1.851 | 0.8204 |
| D7 | + #407 (44cc136e) | +1.248 | +0.422 | +0.440 | +0.438 | +0.434 | 0.930 | 0.8156 |
| D7T5 | + TH5 (9fa47d2c) | +1.256 | +0.432 | +0.450 | +0.465 | +0.450 | 0.942 | 0.8158 |
| D7n | D7, `consv_te` 0.999 | +1.251 | +0.419 | +0.441 | +0.438 | +0.433 | 0.929 | 0.8168 |

The residual columns are R/P in %.

| f24 vs D7 | T rms (K) | ps rms (Pa) | global P |
|---|---|---|---|
| D7n (noise) | 0.1425 | 7.518 | −0.039 % |
| D7T5 | 0.1447 | 7.255 | +0.028 % |
| D0 | 0.1469 | 7.626 | +0.117 % |

## Gates

- **Rebase.** #407 onto b7cb19b1 had one conflict block (upstream's `merra2_aerosol_aware` condition, kept with #407's input-humidity basis). The rebased diff's ± lines equal #407's original; a known-bad resolution (new_spechum left in) differs.
- **Meter.** The meter adds the same 27 lines to D0, D7 and D7T5; the `prsi` argument is shared with TH5, so D7 and D7T5 differ only by TH5's code. The setup verified md5s of the pristine and #407 sources and that D0 ≠ D7 ≠ pristine. D0 against D7 is the meter's can-fail check: it separates #407's term (gross 1.85 vs 0.93 %).
- **TH5 patch.** One hunk (the argument list) was re-applied by hand because #389 changed its context; the code ± lines equal the port patch's.
- **Scope.** One start date, one member per arm. The noise pair is a single `consv_te` perturbation. Percentages are of TEMPO's grid-scale precipitation.

Local branches (scratchpad physics clone, not pushed): `pr1-tempo-on389` 44cc136e, `tp389-th5` 9fa47d2c, `pr1-mp2` e52c75af (#406 + #407 + #413 on b7cb19b1).
