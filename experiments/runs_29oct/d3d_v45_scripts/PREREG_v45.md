# Pre-registration: #403 variants 4/5, Jongil's diff3d (written 2026-11-12, before the build)

Question (Jongil, #403, 30 Oct): does his updated mass-weighted diff3d (NOAA-GFDL/GFDL_atmos_cubed_sphere#429 @8460b55b,
dyn_core.F90 L2508-2703) remove the leak? His stencil = the original stencil with K_face x delp_face, divided by FV3 delp.
It is not our measured v1 (which differences q itself with dy/dxc), so v1's numbers do not answer him.

Variants in r14d3d4 (same build otherwise as r14d3d3): 4 = his stencil / FV3 delp in the dycore (his code);
5 = his stencil, no division in the dycore, / the physics' layer mass in the driver (as v3).

Estimator (unchanged): UCH Smass/Gmass, net of the horizontal-diffusion tendency as satmedmfvdifq applies it,
mass-weighted with the physics' del, / its gross, for T, sphum, o3mr; PBL water residual. Pass <= 1e-10.
Predictions: v4 fails at ~1e-3 (divisor mismatch, as v1); v5 passes (~1e-16, as v3).
Uniform tracer ('D3J', his stencil / delp on q = 1): predicted nonzero, about the original's 3.6e-9 /s max,
since his stencil still differences q*dx; its mass-weighted net ~0 (it telescopes).
Gates: v3 rerun with r14d3d4 bitwise = d3d_v3_3d (known-good: new switches leave old paths alone); v4 differs from v3
(known-bad: the switch reaches the code).
Scope: his dycore operator in our 3d2331e3-based build (t403m, #403 as of 23 Oct), not his whole updated branch.
