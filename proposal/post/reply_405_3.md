@JongilHan66 Thanks for going through it. I agree with your 1) and 2): `dellaq(kb)` and `dellaq(jmin+1)` must be zero, and the subtraction makes them zero. This PR keeps them zero.

The problem is in how terms (2) and (3) of your Eq. (9c) ([Office Note 506](https://doi.org/10.25923/5051-3r70); slide 8 of [TVD.pdf](https://github.com/NCAR/ccpp-physics/files/7290057/TVD.pdf) in NCAR/ccpp-physics#753) meet at cloud base. At the `kb` interface their fluxes cancel only if `φ̄` there equals `φu(kb)`. In the code `φu(kb) = qcko(kb) = qo(kb)`. Before TVD, term (2) also used `qo(kb)` at `kb` (`dv3q`), so they cancelled. With TVD, term (2) uses the limited value `tem1` from the `flxtvd` loop, while term (3) still starts from `qo(kb)`.

Taking your 1) one layer up, at `k = kb+1`:
- term (3) adds `eta(kb)*qcko(kb)*g/dp = eta(kb)*qo(kb)*g/dp`;
- term (2) subtracts `flxtvd(kb)*g/dp = eta(kb)*tem1*g/dp`.

By your 1), nothing at or below `kb` changes, so layer `kb+1` gains `eta*(qo(kb) - tem1) = eta*(1 - phkp)*(qo(kb) - q1(kb+1))` (times `xmb*g/dp`) with no source. The downdraft at `jmin`, your 2), works the same way. `dellah` closes because it has no TVD and uses `heo(kb)` in both terms.

Your slide-8 check, `∫ ∂φ/∂t dz = (−w'φ')top − (−w'φ')bot`, gives ~1e-17 for TKE with central differencing and 1e-5 to 1e-2 with TVD. That TVD residual is this term. I ran your check on the two tracers SAMF transports here, in `control_p8` (C96, 24 h), as the column residual over the gross transport `Σ|∂φ/∂t| dz`:

| | develop, deep | develop, shallow | this PR, deep | this PR, shallow |
|---|---|---|---|---|
| TKE | 6.4e-3 | 3.6e-3 | 1.2e-16 | 1.0e-16 |
| ozone | 2.5e-3 | 3.0e-4 | 5.5e-16 | 2.5e-15 |

On develop, the residual equals `eta*(ctro(kb) - tem1)` (deep: plus the `jmin` term) to 2e-14 of itself, summed over every column-step. With this PR, it drops to your central-differencing level.

The same check on water (change in column water plus rain):

| | deep | shallow |
|---|---|---|
| column-steps with rain | 337,149 | 1,791,709 |
| water created, % of convective rain | +0.56 % | +2.12 % |
| column-steps where it exceeds 0.1 % of their rain | 88 % | 99 % |
| residual minus the formula above, max | 4e-15 kg/m² | 2e-15 kg/m² |
| residual with this PR, max | 4e-15 kg/m² | 2e-15 kg/m² |

Together that is 0.8 % of convective rain, about 0.014 mm/day globally. With this PR the residual is at rounding level, as with central differencing. The limiter is unchanged everywhere else, and negative-vapour borrowing is needed as often as before (97 with it vs 104 without, of about 330,000 deep column-steps).

I can push the check to a branch if you want to run it.
