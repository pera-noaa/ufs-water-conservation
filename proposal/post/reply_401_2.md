Thanks @JongilHan66. You are right about the floor, which our description left out: with `clamt` = `clam`, above 1 km `xlamue` = `crtlame` = `xlamud`, so `eta` stays at 1. What breaks it is the TKE scaling. For `tkemean` > `tkcrt` it multiplies `clamt`, and with it `xlamud` = 0.001·`clamt`, by up to `cmxfac` = 15, while `crtlame` stays at 1e-4. Above 1 km detrainment then exceeds entrainment and `eta` grows downward. In every column we checked, `eta` > 1.2 came with `tkemean` > 2. GFS v16 does not have this scaling; it came with #65.

We ran your test and a few others. `hafs_global_1nest_atm` is develop with print-only diagnostics; the `control_*` runs are `rt.sh` with the same diagnostics, and all 12 tests we checked match the baselines.

| | crashed | largest one-step heating | sub-cloud `eta` | precipitation |
|---|---|---|---|---|
| develop, 48 h, 10 members | **6** (at 19–40 h) | 49–96 K | up to ~100 | |
| develop, 6 h, 20 members | 0 | 23–52 K, CFL up to 25 | up to 102 | 2.4370 mm/day |
| your test, `eta`, `etad` ≤ 1 | 0 | 14.5 K, CFL up to 2.6 | ≤ 1 | −8.1 % |
| `crtlame` · max(1, `clamt`/`clam`) | 0 | none above 4 K | ≤ 1.2 | +0.02 % (member spread 0.04 %) |
| same, 48 h, 10 members | 0 | 5.0–7.6 K | ≤ 1 | |
| xmb CFL bound in every updraft layer (our option A), 48 h | 0 | 4.8–6.6 K | up to ~80 | −0.18 % |
| develop `control_c384` (GFS v17 P8, `dt` 300 s, 12 h) | 0 | 26 K, CFL 9 | up to 9.2 | |

So with your test the crash goes away: it is the sub-cloud `xm`, not `xmb`. The large TKE comes from SAMF itself. "Include TKE contribution from deep convection" adds `0.5·σ·w_u²` with `w_u` ∝ `eta`·`xmb` once per call, so large `eta` and large TKE feed each other. With that source removed, no layer heats by more than 4 K. Halving the source gives 3× fewer capped columns, quartering it 19× fewer. The `dt` dependence is just as strong: capped column-steps are 332k at `dt` 45 s, 62k at 90 s, 4.7k at 180 s and 264 at 360 s, and one 45 s member crashes within 6 h.

Scaling `crtlame` with `clamt` keeps `eta` ≤ 1 below cloud base at any TKE, as you describe, and leaves precipitation unchanged here. Would you take that? We have not yet tested it in GFS. It also raises the floor in cloud, which matters for elevated bases.

All of the above has `progsigma` = .false., as in the UFS RTs. With `progsigma` = .true., as in HAFS v2.1, none of it appears: across 40 members (develop and our fixes), no layer heats by more than 4 K, sub-cloud `eta` stays at or below 1.3, and nothing crashes. So this affects the `progsigma` = .false. configurations.
