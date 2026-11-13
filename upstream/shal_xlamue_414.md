# Shallow SAMF sub-cloud mass flux (#414 follow-up)

**Status.** Jongil's #414 approval asked to "include this change in samfshalcnv.f" (deep: `xlamue >= 0.001*clamt`).
Copying it literally is wrong for shallow; the principled fix is to cap detrainment, not floor entrainment.
Deep: keep #414's floor. Seven sub-cloud fixes all stop the HAFS crash (0/10 each vs develop 6/10); on the #401 heating metric only the sub-cloud CFL bound beats the floor (alone it leaves eta growing; with the cap it is two changes), and Laura's lifetime intensity differs by ≤ 2 m/s and ≤ 3.6 hPa across all of them (see "Range of fixes"). The floor equals Han et al. (2024) Eq. 5 applied to the documented entrainment floor.
The earlier "6.6 m/s wind loss with the floor" is withdrawn: it was a whole-nest maximum at 48 h, when Laura is inland; tracked, the floor's storm is deeper at 36 h and decays faster after a landfall shifted by one to two grid cells.
Shallow: in control_p8 the cap binds in 14 % of convecting columns (sub-cloud eta up to 4.1×); no build shows a shallow heating above 4 K in HAFS or control_p8. The literal floor, cap, sub-cloud floor and doc all change 24 h fields by no more than a consv_te 0.999 perturbation does, and global precipitation by ≤ 0.2 %; the choice between the literal floor (Jongil's request) and the cap is structural, not measurable at 24 h: the floor stops shallow in-cloud mass flux from decreasing below cloud top.
**Resolved.** Jongil chose his own form, a floor at and below cloud base and a cap above (`max`/`min` with 0.001·`clamt`), and put it in #403 (62485fc1). #414 stays deep-only ([reply 6833781177](https://github.com/ufs-community/ccpp-physics/pull/414#issuecomment-6833781177)). The analysis below is kept for the record.

## Why the literal port is wrong

Shallow's in-cloud mass flux decreases only through `xlamue < xlamud = 0.001*clamt` (no organized detrainment term, unlike deep's `cxlamdt*frh`).
Flooring every level sets in-cloud eta to exactly 1.000 (standalone). Default `clam_shal` = 0.3, so the floor is ≥ 2·`crtlame` and binds above ~1 km in every column.

## What is actually wrong

The scheme's own documentation (samfshalcnv.f): detrainment "set constant and equal to the entrainment rate at cloud base"; eta "increases upward below the cloud base".
`xlamud = 0.001*clamt` (in the code since the 2018 ccpp import; the HWRF branch keeps `xlamue(kbcon)`) breaks the second when cloud base is above ~1 km: sub-cloud eta grows downward.

## Fix: cap detrainment at the layer entrainment below cloud base

Three lines, same per-layer value in eta, `hcko` and the heat tendency (`tem1`):
`ptem = max(ptem, 0)` in the sub-cloud eta loop; `if(k <= kbcon(i)) tem1 = min(tem1, 0.5*tem)` in the hcko loop; `if(k <= kbcon(i)) tem1 = min(tem1, tem)` in the tendency loop.
Detrained air carries updraft properties, so only the mass-flux profile changes; q, u, v and tracer updraft properties use entrainment only.

## Standalone evidence (scratchpad `xlam/`, pr1-samf shallow + e50fcc77)

| check | result |
|---|---|
| trade-cumulus sweep (T 293–308 K, RH 0.48–0.80, TKE 0.4–10, inversion 0.5–1.1 km above base) | 276 convecting columns, cloud base 0.1–1.5 km; cap binds in 156 |
| max sub-cloud eta, current code | 1.186 (cloud base 1.0–1.5 km) |
| in-cloud eta changed by cap | never |
| -O0 bitwise, cap not binding | 120/120 identical |
| heat budget Σ dellah·Δp / Σ\|dellah\|·Δp, cap binding | ≤ 2e-12; known-bad (cap in eta only) ≥ 3e-2 |
| rain change, max: cap / floor ≤ kbcon / floor everywhere | 2.8 % / 21 % / 75 % (cloud base 1.0–1.5 km) |
| convection removed: cap / floor ≤ kbcon / floor everywhere | 0 / 0 / 0 (sweep 4); floors removed 4 of 39 in sweep 1 |
| flag combos (po ps tk me hw, 13 combos) × blocks 6/3/1 | all run, block-independent; HWRF bitwise unchanged (cap never binds) |

`rhcrt` = 0.75 limits surface-based shallow cloud base to ~1.4 km, so the analytic 2.5–15× growth needs an elevated source level; realistic growth is ≤ ~20 %.
(Superseded by control_p8: cloud bases reach 3.1 km and growth reaches 4.1×; the synthetic sweep did not sample elevated sources.)

## Water and tracer budgets (package shallow = pr1-samf + #405 merge)

Same 276 columns; residual = Σ(Δq + Δice + Δliquid)·Δp/g + rain, over gross vapour change; tracer has a curved profile so the TVD limiter acts.

| build | water median / max | tracer median / max |
|---|---|---|
| package, current | 4e-15 / 5e-14 | 4e-16 / 7e-15 |
| package + cap (binds in 156) | 4e-15 / 6e-14 | 4e-16 / 5e-15 |
| pre-#405 (known-bad) | 1e-1 / 3e-1 | 1e-2 / 1e-2 |

## Red team: alternative sub-cloud rules (same 276 columns, package build)

All close water, tracer and heat to rounding and remove downward growth; they differ in what else moves.

| rule | in-cloud eta changed | T tendency chg med/max | mass flux chg med/max | verdict |
|---|---|---|---|---|
| cap (3 lines) | 0 | 2e-3 / 0.1 | 2e-3 / 0.2 | minimal |
| cap, per-layer array set once | 0 | bitwise = cap (276/276, 18/18 flag×block) | | preferred form: one place to keep consistent |
| lev: deep-style per-level array, capped ≤ kbcon | 156/156 | 3e-3 / 0.1 | 4e-3 / 0.2 | rain +5–15 % at high TKE via first in-cloud layer; reject |
| doc: sub-cloud λd = min(0.001·clamt, λe(kbcon)) | 0 | 2e-2 / 0.3 | 3e-2 / 0.3 | design-faithful but moves the whole sub-cloud, also below 1 km; second choice |
| none | — | — | — | defensible: growth ≤ 1.19, no failure shown |

Deep #414 has the same in-cloud side effect in milder form: with clamt raised by TKE (up to 1.5) the floor lifts base entrainment from clamt/z to clamt/1000 above 1 km (×5 at 5 km) before fent1. HAFS needs only the sub-cloud part to stop crashing (the deep cap alone gives 0/10), but that side effect is Eq. 5 of Han et al. (2024) applied as written: with `clam_deep` = 0.1, `crtlame` = 0.001·`clam`, so scaling entrainment by f gives max(`clamt`/z, 0.001·`clamt`).

## 3D tests (Hercules, `upstream/xcap`)

Counters (print-only; pA vs pA0 bitwise identical in all 181 fields) count convecting calls where λd > λe below cloud base ("would bind") and where sub-cloud eta exceeds eta(kbcon) ("grows").

HAFS `hafs_global_1nest_atm`, 48 h, 10 members per build (consv_te 1, 0.999 … 0.991); hP = develop f1d68949, hF = #414 floor, hC = deep cap.

| | hP | hF | hC |
|---|---|---|---|
| crashed (`compute_qs` table overflow) | 6/10 | 0/10 | 0/10 |
| deep would-bind / grows, per 48 h member | 9.1 M / 9.1 M | — | 8.9 M / 0 |
| sub-cloud eta growth, 99th pct of per-call max / max | 8.2× / 3253× | — | none |
| max cloud base where binding | 7.4 km | — | 7.4 km |
| nest max 10 m wind f048, m/s | 29.8 (4 survivors) | 22.7 | 29.3 |
| nest convective precip f048, mm/d | 2.88 | 3.03 | 2.91 |

Paired by consv_te at f048: hC − hF wind +6.6 ± 1.6 m/s (member sd 1.0), nest convective precip −0.12 (sd 0.002); hC − hP wind −1.4 ± 1.0 (n = 4, within member spread).
Growth occurs in every binding call because λe = clamt/z decreases with height, so the binding layers are contiguous below cloud base.
The ocean-masked minimum surface pressure (848.6 hPa, member sd 0.03) is not the storm centre and is not used.
(Superseded by "Range of fixes": the nest spans 139–33° W, 15° S–61° N at ~33 km, so the two wind rows above are whole-nest maxima, not Laura.)

control_p8, 24 h, package physics 44defba3 (#405, #408, #414 floor): pA0 pristine, pA = e50fcc77 shallow form + counters, pB = shallow cap, pC = shallow and deep caps.

| | pA | pB | pC |
|---|---|---|---|
| shallow would-bind / grows (of 2.59 M convecting) | 357 k / 357 k | 355 k / 0 | 356 k / 0 |
| shallow growth max, cloud base max | 4.09×, 3.1 km | none | none |
| deep would-bind / grows (of 2.33 M) | 0 / 0 (floor) | 0 / 0 | 87 k / 0 |
| global precip / convective precip, mm/d | 2.7486 / 1.7117 | 2.7472 / 1.7104 | 2.7481 / 1.7083 |

pA = pA0 bitwise confirms e50fcc77 is answer-neutral in 3D. pB and pC change 140/163 sfc fields at 24 h; without a perturbation baseline these field differences cannot be separated from chaotic growth, but global precip moves ≤ 0.2 %.

Heating, the #401 metric (print-only `dbg4` in hP/hF/hC; with it, all 361 fields at f024 are bitwise equal to the runs above). Per member over 48 h, 10 members; hP crashes the same 6 members as before.

| | hP | hF (floor) | hC (cap) |
|---|---|---|---|
| layer-steps with \|ΔT\| > 4 K | 3,591–9,011 | 17–34 | 75–126 |
| of those > 10 K | 514–1,236 | 0 | 0–2 |
| largest one-step heating, K | 44–96 | 4.9–8.0 | 6.1–12.8 |
| largest CFL | 17–47 | 1.8–2.9 | 2.1–2.9 |
| sub-cloud eta at events, max | 19–139 | 1.00 | 1.00 |
| column-steps with TKE at its cap | 23–61 k | 14–15 k | 3.0–3.2 k |
| global precip f024, mm/d | 2.673–2.676 | 2.659–2.661 | 2.659–2.661 |

hP and hF reproduce the #401 rows (develop ~9,000, 49–96 K, CFL ≤ 47; floor 16–28, 5.5–7.6 K, CFL ≤ 2.6). The cap's events are all below `kbcon`, 89 % with `xmb` at `xmbmax` and 88 % heating; with eta ≤ 1 there, CFL > 1 means the layer is thinner than the cloud-base layer that `xmbmax` is set from. The cap is far better than develop and than Jongil's `eta`, `etad` ≤ 1 test (48–50 k, 15.2 K), but worse than the floor; #401 option A (`xmbmax` also bounded below cloud base) removed all such events on develop and would close the gap, at the cost of a second change.

## Range of fixes (HAFS deep, control_p8 shallow)

Cause: λe = max(`clamt`/z, `crtlame`) and λd = 0.001·`clamt`; with `clam_deep` = 0.1 they are equal above 1 km until TKE scales `clamt` by f ≤ 15 (PR #65, 2023) while `crtlame` stays 1e-4. Shallow (`clam_shal` = 0.3, `crtlamd` = 3e-4) has had λd > λe above 1 km since fv3atm 06b956a (2018) replaced `xlamud = xlamue(kbcon)` (still in the code, commented out) with 0.001·`clamt`.

HAFS `hafs_global_1nest_atm`, develop + one fix + print-only counters and `dbg4`, 10 members × 48 h each. Storm: Laura tracked by the slp minimum (Gulf/Caribbean box at 3 h, then within 500 km; terrain > 500 m excluded), wind = max lowest-level |V| within 300 km, from the 3-hourly nest diagnostics.

| fix | what it restores | crash | steps > 4 K | max ΔT, K | max CFL | sub-cloud growth calls | lifetime max wind / min slp | vs cap, paired |
|---|---|---|---|---|---|---|---|---|
| none (develop) | — | 6/10 | 3,591–9,011 | 44–96 | 17–47 | 3.9–9.1 M | 44.6 / 965.9 (n = 4) | |
| F floor everywhere (#414) | Eq. 5 on the documented floor | 0/10 | 17–34 | 4.9–8.0 | 1.8–2.9 | 0 | 43.6 / 964.0 | −1.0 ± 1.0 m/s, −1.0 ± 1.3 hPa |
| S floor below cloud base | Eq. 5 below cloud base only | 0/10 | 287–418 | 7.0–8.3 | 2.1–2.7 | 0 | 43.1 / 966.3 | −1.5 ± 1.0, +1.3 ± 1.3 |
| C cap λd ≤ λe below cloud base | "eta increases upward" | 0/10 | 75–126 | 6.1–12.8 | 2.1–2.9 | 0 | 44.6 / 964.9 | — |
| D λd ≤ λe(kbcon) below cloud base | "λd equal to λe at cloud base" | 0/10 | 47–67 | 5.7–8.5 | 1.7–2.8 | 0 | 44.2 / 965.7 | −0.4 ± 1.1, +0.7 ± 1.6 |
| U λd ≤ `crtlamd` below cloud base | pre-2018 sub-cloud λd | 0/10 | 40–58 | 5.5–6.5 | 1.7–2.5 | 0 | 43.9 / 965.5 | −0.7 ± 0.9, +0.6 ± 1.2 |
| A CFL bound below cloud base only | stability only; eta still grows | 0/10 | 10–20 | 4.8–6.6 | 1.2–1.7 | 9.2–9.3 M | 42.7 / 967.6 | −1.9 ± 0.7, +2.6 ± 0.8 |
| CA cap + A | two changes | 0/10 | 2–12 | 4.3–6.1 | 1.0–1.9 | 0 | 42.6 / 967.5 | −2.0 ± 0.8, +2.5 ± 0.9 |

Member sd of lifetime max wind 0.5–0.9 m/s, of min slp 0.4–1.3 hPa. At 48 h Laura is inland: F 978.2 hPa / 26.0 m/s and A 977.4 / 30.1 against 972.7–976.5 / 33.9–35.6 for the rest; F is deepest at 36 h (965.7 / 43.0 vs 969.5–973.6 / 37.5–39.6) and its mean centre is 35–53 km (1–2 nest cells) from every other build's from 36 h on.
In the standalone screen (40 convecting columns) C, D and CA leave the in-cloud mass flux bitwise unchanged; S changes it by up to 30 % and T by up to 100 % (the floor at `kbcon` feeds the first in-cloud layer); U changes T by up to 30 % also in columns that never grow.

control_p8 (package physics with the deep floor; 24 h; `dbg4` in all):

| shallow | sub-cloud growth calls (max) | shallow steps > 4 K | precip / conv precip vs develop | field rel. rms diff vs develop, median / p90 |
|---|---|---|---|---|
| develop (pA) | 357 k (4.09×) | 0 | — | — |
| develop, consv_te 0.999 (noise) | 353 k (3.54×) | 0 | +0.02 % / +0.04 % | 0.026 / 0.30 |
| cap (pB) | 0 | 0 | −0.05 % / −0.08 % | 0.026 / 0.30 |
| floor below cloud base (pS) | 0 | 0 | −0.09 % / −0.20 % | 0.026 / 0.27 |
| doc (pD) | 0 | 0 | +0.03 % / −0.06 % | 0.025 / 0.30 |
| literal floor everywhere (pL, #414 in shallow) | 0 | 0 | +0.03 % / +0.11 % | 0.026 / 0.27 |

Deep steps > 4 K in control_p8 with the floor: 59–92 per 24 h in every build.

The earlier "53 % of rain" was the standalone build lacking #405, not the accounting. A uniform or linear tracer never triggers the limiter, so it passed the known-bad too; the curved profile is required.
