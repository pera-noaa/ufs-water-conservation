@JongilHan66 Thanks. I agree with your 1) and 2): `dellaq(kb)` and `dellaq(jmin+1)` must be zero, and the subtraction makes them zero. This PR keeps them zero. The problem shows up one layer higher, in `kb+1`.

Following your 1) one layer up (updraft only), at `k = kb+1`:
- the updraft term adds `eta(kb)*qcko(kb)*g/dp`, which is `eta(kb)*qo(kb)*g/dp` because `qcko(kb) = qo(kb)`;
- the TVD term subtracts `flxtvd(kb)*g/dp`, which is `eta(kb)*tem1*g/dp`, with `tem1` the limited face value from the `flxtvd` loop.

So the updraft takes `eta*qo(kb)` up through face `kb`, and the subsidence brings `eta*tem1` back down through it. Nothing below that face changes, so the difference, `eta*(qo(kb) - tem1) = eta*(1 - phkp)*(qo(kb) - q1(kb+1))`, is created. It vanishes only where `phkp = 1` or `qo(kb) = q1(kb+1)`. The downdraft at `jmin` is the same. `dellah` doesn't have this problem because its subsidence at `kb` uses `heo(kb)`, the value the updraft starts from; water used `qo(kb)` there too before #754. This PR puts `qo(kb)` back on that one face. The limiter is unchanged everywhere else, and negative-vapour borrowing is needed as often as before (about 0.03 % of deep-convecting column-steps, 97 with it and 104 without in 24 h at C96).

How did you check conservation? Globally this is about 0.014 mm/day, 0.8 % of convective rain, which is easy to miss in a global budget. Column by column it is clear. In `control_p8` (C96, 24 h) I added up the change in column water plus rain for every column-step with convective rain:

| | deep | shallow |
|---|---|---|
| column-steps | 337,149 | 1,791,709 |
| water created, % of convective rain | +0.56 % | +2.12 % |
| column-steps where it exceeds 0.1 % of their rain | 88 % | 99 % |
| created minus `xmb*dt*eta*(qo(kb) - tem1)` (deep: plus the `jmin` term), max | 4e-15 kg/m² | 2e-15 kg/m² |
| created with this PR, max | 4e-15 kg/m² | 2e-15 kg/m² |

I can push the diagnostic to a branch so you can run it. I'm also happy with a different fix, for example starting the updraft from `tem1`; what matters is that both sides of face `kb` use the same value.
