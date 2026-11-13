We checked conservation of the new horizontal diffusion in a C96 `control_p8` run (24 h, `sa3dtke` and `sa3dtke_dyco` on), at this PR's head with NOAA-EMC/ufsatm#1154 and NOAA-GFDL/GFDL_atmos_cubed_sphere#429. The `diff3d` tendencies cancel exactly per unit area: the area-weighted global sum is about 1e-17 of the gross. But `satmedmfvdifq` adds them to temperature and mixing ratios, where only a mass-weighted sum cancels, and `delp` differs between neighbouring columns. So part of each tendency leaks:

| | mass-weighted net / gross | net over 24 h |
|---|---|---|
| T | −2.7 % | −1.5e-3 W/m² |
| `sphum` | −1.0 % | −1.3e-5 kg/m² |
| `o3mr` | +0.95 % | +6.8e-9 of its mass |
| other tracers | 0.05–0.9 % | |

The amounts are small, but a diffusion term should conserve exactly. Building the face fluxes from `q·delp` and dividing each cell's net flux by its own `delp` would make the sum telescope in mass. We can test that if useful.
