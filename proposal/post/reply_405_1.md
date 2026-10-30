@JongilHan66 Thank you, I agree with both points: with the TVD flux, `dellaq(kb)` and `dellaq(jmin+1)` must be zero, and the subtraction makes them zero. This PR keeps them zero. The problem is what passes through the top face of layer `kb`.

**The column sum.** Summing `dellaq·dp/g` over a convecting column (per unit `xmb`), term by term:

1. The updraft and downdraft terms (`tem1 - tem2`, `ptem1 - ptem2`, layer 1, cloud top) telescope to `eta(kb)*qcko(kb) + edto*etad(jmin)*qcdo(jmin)` minus the condensate, with `qcko(kb) = qo(kb)` and `qcdo(jmin) = qo(jmin)`.
2. The TVD terms telescope to `flxtvd(ktcon) - flxtvd(0) = 0`.
3. The subtractions add `-eta(kb)*tem1(kb) - edto*etad(jmin)*tem1(jmin)`.

So for each column and step,

`(change in column water) + rain = xmb*dt*[eta(kb)*(qo(kb) - tem1(kb)) + edto*etad(jmin)*(qo(jmin) - tem1(jmin))]`

which is zero only where `phkp = 1`. Shallow has the `kb` term only.

The updraft carries `eta*qo(kb)` up through that face, and the subsidence brings `eta*tem1` back down through it. Layer `kb` does not change, so the difference has no source. Before #754 the subsidence there used `dv3q = qo(kb)`. `dellah` still does (`dv3h = heo(kb)`, `hcko(kb) = heo(kb)`), which is why moist static energy closes at cloud base and water does not. This PR makes water do the same at that one face; the limiter is unchanged elsewhere.

**Measured** in `control_p8` (develop 5651397d, Intel, C96, 24 h), with print-only code that evaluates both sides in every column-step with convective rain. Built with `-no-fma`, the instrumented model is bit-identical to develop and gives the same percentages to within 0.01; the table is from the standard build:

| | deep | shallow |
|---|---|---|
| column-steps with rain | 337,149 | 1,791,709 |
| net water created, % of convective rain | +0.56 % | +2.12 % |
| \|created\|, % of convective rain | 0.98 % | 2.26 % |
| column-steps with \|created\| > 0.1 % of their rain | 88 % | 99 % |
| \|created\|, max per column | 0.090 kg/m² | 0.019 kg/m² |
| \|created − formula\|, max per column | 4e-15 kg/m² | 2e-15 kg/m² |
| \|created\|, max per column, with this PR | 4e-15 kg/m² | 2e-15 kg/m² |

The formula matches the model to rounding in every column. One deep column: `phkp = 0` at `kb = 35`, so `tem1 = q1(kb+1) = 8.646e-3` against `qo(kb) = 8.904e-3`. It rains 0.436 kg/m² and creates 0.040 kg/m² (9 %), as the formula predicts; with this PR it creates 2e-16.

The error is `eta*(1 - phkp)*(qo(kb) - q1(kb+1))`, small where moisture is smooth across cloud base, so a check on smooth or well-mixed profiles can pass.

I can push the check to a branch if you want to try it. I'm also happy to fix it by starting the updraft from `tem1` instead; what matters is that both ends of the flux through that face carry the same value.
