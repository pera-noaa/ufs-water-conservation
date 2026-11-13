Thanks @JongilHan66. You are right about the floor, and our description left it out: with `clamt` = `clam`, above 1 km `xlamue` = `crtlame` = `xlamud`, so `eta` stays at 1, and `xmbmax` limits `xm` only at `kbcon`. TKE raises both rates, but above 1 km `xlamue` sits on `crtlame`, which is not scaled, so only `xlamud` grows. For `tkemean` > `tkcrt`, `clamt` grows up to `cmxfac` = 15 times, and `eta` grows downward. We saw `eta` > 1.2 only where `tkemean` > 2. Operational GFS v16 has no `cmxfac`; on develop, `control_c384gdas` (FV3_GFS_v16) reaches `eta` 8.5.

`hafs_global_1nest_atm`, develop with print-only diagnostics (bitwise identical to the baselines in all 12 RTs we ran), `progsigma` = .false. as in the RT:

| | crashed | layer-steps > 4 K, per member | largest one-step heating | sub-cloud `eta` | precipitation |
|---|---|---|---|---|---|
| develop, 6 h, 20 members | 0 | 257–351 | 23–52 K, CFL ≤ 25 | ≤ 102 | 2.4370 mm/day |
| develop, 48 h, 10 members | **6** (at 19–40 h) | ~9,000 | 49–96 K, CFL ≤ 47 | ≤ 264 | |
| your test (`eta`, `etad` ≤ 1), 6 h | 0 | 5,500–5,900 | 14.5 K, CFL ≤ 2.6 | ≤ 1 | −8.1 % |
| your test, 48 h, 10 members | 0 | 48,000–50,000 | 15.2 K, CFL ≤ 3.6 | ≤ 1 | |
| `xlamue` ≥ 0.001·`clamt`, 6 h | 0 | 0 | below 4 K | none > 1.2 | +0.02 % |
| `xlamue` ≥ 0.001·`clamt`, 48 h | 0 | 16–28 | 5.5–7.6 K, CFL ≤ 2.6 | none > 1.2 | |
| `xm` CFL bound in every updraft layer, 48 h | 0 | 10–20 | 4.8–6.6 K | ≤ 180 | −0.18 % (6 h) |

Your test removes the overshoots, so the trouble is the sub-cloud `xm`, not `xmb`. It also prevents develop's 48 h crashes (0 of 10). It also makes many smaller heatings at cloud base in surface-based columns, with `xmb` at `xmbmax`.

On TKE: most columns have it at order 1 (`tkemean` > 2 in 11 % of convective column-steps), but where `eta` > 1.2 the median is 11 m²/s². It does not come from the instability. With the `xm` bound there are no overshoots, yet `clamt` is capped as often (67k vs 62k column-steps). Without SAMF's "TKE contribution from deep convection" it is never capped. That source adds `0.5·σ·w_u²` with `w_u` ∝ `eta`·`xmb`, once per call, so large `eta` and large TKE feed each other, more so at short `dt`: capped column-steps per member are 33k at 45 s, 3.1k at 90 s, 240 at 180 s and 26 at 360 s.

With `progsigma` = .true. (HAFS v2.1, and the UFS GFS v17 coupled tests) none of this appears: in 40 members over 6 h, no layer heated by more than 4 K, `eta` stayed ≤ 1.3 and nothing crashed. Over 48 h (10 members) there is still no crash and no layer above 4 K, and `eta` stays ≤ 1.3, although TKE reaches the cap in about 180 column-steps per member. We do not know why; its σ floor of 0.01 should make the TKE source larger.

Would you accept flooring `xlamue` at 0.001·`clamt`, i.e. at `xlamud`? It restores the floor you describe at any TKE and any `clam`; here (`clam_deep` = 0.1) it equals `crtlame`·max(1, `clamt`/`clam`). It changes answers wherever `tkemean` > 0.35 and raises the in-cloud entrainment floor for bases above 1 km, to 1.5e-3 at the cap. TKE is still capped in about 15k column-steps per member over 48 h. We have not tested it in GFS yet.
