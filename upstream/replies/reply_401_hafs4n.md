Another case, from a full RT on Hercules (develop 783f524a, baselines 20261026): with #405, `hafs_global_multiple_4nests_atm` stops at step 131 of 360 with `compute_qs: saturation vapor pressure table overflow`. It's this instability, not #405. Five runs of that test each (`consv_te` = 1, 0.999, …, 0.996):

| | crashed |
|---|---|
| develop | 1 of 5 |
| #405 | 2 of 5 (one is the RT's own run) |
| develop + `xlamue` ≥ 0.001·`clamt` | 0 of 5 |
| #405 + the same floor | 0 of 5 |

Every crash is on the same rank with the same error, so develop passes this RT only because its one run happens to be a safe one. I'll open the floor as its own PR and pair it with #405 in the ufsatm/WM companions.
