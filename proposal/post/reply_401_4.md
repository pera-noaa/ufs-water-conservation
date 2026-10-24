Thanks @JongilHan66. You are right about the floor, which our description left out: with `clamt` = `clam`, `xlamue` = `crtlame` = `xlamud` above 1 km, so `eta` stays at 1, and `xmbmax` limits `xm` only at `kbcon`. TKE raises both rates, but above 1 km `xlamue` sits on the unscaled `crtlame`, so only `xlamud` grows: for `tkemean` > `tkcrt`, `clamt` grows up to `cmxfac` = 15 times and `eta` grows downward. We saw `eta` > 1.2 only where `tkemean` > 2. Operational GFS v16 has no `cmxfac`; on develop, `control_c384gdas` (FV3_GFS_v16) reaches `eta` 8.5.

`hafs_global_1nest_atm`, develop with print-only diagnostics (bitwise identical in the 12 RTs we ran), `progsigma` = .false. as in the RT:

| | crashed | layer-steps > 4 K, per member | largest one-step heating | sub-cloud `eta` |
|---|---|---|---|---|
| develop, 6 h, 20 members | 0 | 257–351 | 23–52 K, CFL ≤ 25 | ≤ 102 |
| develop, 48 h, 10 members | **6** (at 19–40 h) | ~9,000 | 49–96 K, CFL ≤ 47 | ≤ 264 |
| your test (`eta`, `etad` ≤ 1), 48 h | 0 | 48,000–50,000 | 15.2 K, CFL ≤ 3.6 | ≤ 1 |
| `xlamue` ≥ 0.001·`clamt`, 48 h | 0 | 16–28 | 5.5–7.6 K, CFL ≤ 2.6 | ≤ 1.2 |
| `xm` CFL bound in every updraft layer, 48 h | 0 | 10–20 | 4.8–6.6 K | ≤ 180 |

Your test prevents the crashes, so the trouble is the sub-cloud `xm`, not `xmb`. But it leaves many 4–15 K heatings per step at cloud base in surface-based columns, with `xmb` at `xmbmax`. They are the limit, not a physical rate: at `dt` 45, 90 and 180 s the heating per step is the same (median 6 K, 99th percentile 11 K, CFL median 1.0), so the rate scales as 1/`dt` (120–480 K/h). Your test also moves 6 h precipitation by −8 %; the floor below changes it by +0.02 %.

The large TKE does not come from the instability. With the `xm` bound there are no overshoots, yet `clamt` is capped as often (67k vs 62k column-steps). Without SAMF's "TKE contribution from deep convection" it never is. That term adds `0.5·σ·w_u²` with `w_u` ∝ `eta`·`xmb` once per call, so `eta` and TKE feed each other, more so at short `dt`: capped column-steps per member are 33k at 45 s, 3.1k at 90 s and 26 at 360 s.

With `progsigma` = .true. (HAFS v2.1, and the UFS GFS v17 coupled tests), none of this appears. Over 48 h (10 members) nothing crashes, no layer heats by more than 4 K, and `eta` stays ≤ 1.3, although TKE still reaches the cap about 180 times per member. We do not know why.

Would you accept flooring `xlamue` at 0.001·`clamt` (= `xlamud`)? It restores your floor at any TKE and `clam`. It changes answers wherever `tkemean` > 0.35 and raises the in-cloud entrainment floor for bases above 1 km. We have not tested it in GFS yet.
