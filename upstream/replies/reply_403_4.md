<!-- POSTED 12 Nov 2026: https://github.com/ufs-community/ccpp-physics/pull/403#issuecomment-6818866209 (body below, verbatim). Reply on ufs-community/ccpp-physics#403 to @JongilHan66's 30 Oct request ("Could you check if
     the leak from conservation is significantly reduced"), correcting our 29 Oct comment (reply_403_3).
     Evidence: experiments/runs_29oct/mlm_diff3d.md, section "#403 v4/v5"; Hercules $U/cons/r14_d3d runs d3d_v4_3d,
     d3d_v5_3d, d3d_v3_3d_b4 (gate: bitwise = d3d_v3_3d), logs/uc_v345.txt, logs/PREREG_v45.md.
     Line numbers: GFDL_atmos_cubed_sphere#429 @8460b55b dyn_core.F90; ccpp-physics#403 @5292bcfe satmedmfvdifq.F. -->

@JongilHan66 Sorry for the slow reply. We put your updated `diff3d` (NOAA-GFDL/GFDL_atmos_cubed_sphere#429 @8460b55b) through the same meter. It cuts the leak about 17-fold but does not close it, because it divides by FV3's `delp`, while the physics applies the tendency to a different mass: `delp` minus the condensates, its `del`. My 29 Oct comment should have said that.

C96 `control_p8`, 24 h, `sa3dtke` and `sa3dtke_dyco` on. Net horizontal-diffusion tendency as `satmedmfvdifq` applies it, mass-weighted with `del`, relative to its gross:

| | T | `sphum` | worst tracer | PBL water residual, 24 h (kg/m²) |
|---|---|---|---|---|
| original operator | −2.8e-2 | −9.8e-3 | 9.8e-3 | −1.3e-5 |
| your update (÷ FV3 `delp`) | +1.6e-3 | −5.7e-4 | 4.8e-3 | −8.2e-7 |
| your update, ÷ the physics' `del` | −1.5e-17 | +4.8e-18 | 7.5e-16 | −1.7e-16 |

So one change closes it. Drop the three divisions by `delp` in `diff3d` (`dyn_core.F90` L2565, L2640, L2703), and divide by `del` where `satmedmfvdifq` uses `def_3` and `def4q` (L2276 for TKE; L2946–L3062). For example, once before they are used:

```fortran
hdt(i,k)   = def_3(i,k)/del(i,k)
hdq(i,k,n) = def4q(i,k,n)/del(i,k)
```

then `hdt` and `hdq` in place of `def_3` and `def4q`.

A smaller point: your stencil differences `q·dx` across a face rather than `q`, so a uniform tracer still gets a tendency wherever the grid spacing varies, up to 3.7e-9 /s, the same as the original operator. It nets to zero, so it does not affect conservation. Differencing `q` itself gives exactly zero. The form we tested (then ÷ `del` in the physics):

```fortran
fx(i,j)  = 0.25*(dku3d_e(i-1,j,k)+dku3d_e(i,j,k))*(delp(i-1,j,k)+delp(i,j,k))*(q(i,j)-q(i-1,j))*dy(i,j)/dxc(i,j)
fy(i,j)  = 0.25*(dku3d_e(i,j-1,k)+dku3d_e(i,j,k))*(delp(i,j-1,k)+delp(i,j,k))*(q(i,j)-q(i,j-1))*dx(i,j)/dyc(i,j)
div(i,j) = rarea(i,j)*(fx(i+1,j)-fx(i,j)+fy(i,j+1)-fy(i,j))
```

These ran in our build (ufs-weather-model 3d2331e3 with #403 as of 23 Oct), with your `diff3d` copied in; we have not built your full updated branches.
