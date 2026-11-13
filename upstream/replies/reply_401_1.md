Thanks @JongilHan66. With `clamt` = `clam` the floor does keep `eta` ≤ 1: above 1 km, `xlamue` = `crtlame` = `xlamud`. But for `tkemean` > `tkcrt` the TKE scaling multiplies `clamt`, and with it `xlamud` = 0.001·`clamt`, by up to 15, and `crtlame` does not follow. Above 1 km, detrainment then exceeds entrainment, so `eta` grows downward. On develop this happens in 1 % of convective columns, and in all of them `tkemean` > 2. `eta` exceeds 10 in 5,311 columns, with a maximum of 102.

We ran your test, with 20 members each for 6 h:

| | develop | `eta`, `etad` ≤ 1 | no convective TKE source | A (CFL bound) |
|---|---|---|---|---|
| crashed of 20: develop / our 24 fixes | 0 / 3 | 0 / 0 | 0 / 0 | 0 / 0 |
| layer-steps heated > 4 K, per member | 257–351 | 5513–5935 | 0 | 0–1 |
| largest step | 52 K | 14.5 K | — | 4.8 K |
| columns with sub-cloud `eta` > 1.2, all members | 261,145 | 0 | 40 | — |
| mean precipitation, mm/day | 2.4370 | 2.2390 (−8.1 %) | 2.6497 (+8.7 %) | 2.4327 (−0.18 %) |

The crashes go away when sub-cloud `eta` stays at 1. The large TKE comes from SAMF's own source, `0.5·σ·w_u²` with `w_u` ∝ `eta`·`xmb`, so large `eta` and large TKE feed each other. Without that source, `tkemean` > 2 falls from 11 % to 2 % of convective columns. With `eta` capped, the closure raises `xmb` to `xmbmax` instead, and surface-based columns heat 4–14 K per step at CFL ≈ 1.

Since both your test and removing the source change precipitation by about 8 %, which would you prefer: scaling `crtlame` with `clamt` (not yet tested), bounding the TKE source, or the CFL bound? We can test any of them.
