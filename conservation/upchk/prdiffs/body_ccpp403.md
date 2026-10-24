## Description of Changes:

PR submitted on behalf of @JongilHan66 

1. The current GFS 1D scale-aware (SA) TTE-EDMF scheme is extended to the 3D-SA TTE-EDMF scheme by replacing 3D TKE with 3D TTE. The horizontal turbulent diffusion is modified: the horizontal mixing length is now scaled directly to the vertical mixing length, replacing the previous formulation based on horizontal grid size. In addition, horizontal turbulent eddy diffusion—previously restricted to momentum and TKE—now applies across all scalar prognostic variables, including temperature, moisture, hydrometeors, passive tracers, momentum, and TTE.

2. Properly representing cold pools (CPs; dense, cold air masses formed by the downdrafts of precipitating cumulus clouds) within numerical weather prediction models has long been a challenge. By spreading horizontally, the cold pool's leading edge, known as the gust front, acts as a local lifting mechanism, forcing warm, moist air upward to generate secondary convective cells and organize larger systems. Neglecting the thermodynamic and momentum effects of these features, particularly their interaction with the boundary layer structure and the free atmosphere, can lead to significant systematic biases in the simulation of organized mesoscale convection and the diurnal cycle of precipitation. We integrate the CP parameterization developed by Freitas et al. (2024) into the NCEP Global Forecast System (GFS) with a modification. This implementation is coupled with the GFS deep convection and PBL schemes. The CP depth far behind the leading edge (D), used to compute gust front horizontal speed, was reduced from 2 km to 500 m. Concurrently, the density current head depth used for calculating vertical velocity at the CP leading edge was increased to approximately 2D. The modified scheme restricts the CP influence strictly to enhanced convection triggering. It removes convection intensity enhancement, eliminating additional source terms for buoyancy, moisture, and updraft velocity. To eliminate competition between the Cellular Automata (CA) scheme and the CP parameterization—which both attempt to promote secondary cell generation and larger system organization—CA is automatically disabled when the CP scheme is active. Simultaneous activation of both schemes was found to degrade overall forecast skill, particularly for MJO and hurricane predictions.

3. A mixed subgrid-scale turbulent flux scheme is introduced into the GFS based on Moeng et al. (2010), incorporating an auxiliary subgrid vertical flux known as the "Leonard term" (Leonard 1974; Moeng et al. 2010). The Leonard term accounts for subgrid-scale turbulent fluxes originating from near-grid-scale unresolved eddies—the largest subgrid eddies with scales comparable to the model's horizontal grid resolution. Applied primarily to mitigate subgrid flux underestimation, this formulation is most effective at kilometer-scale, convection-permitting, or cloud-resolving resolutions (Moeng et al. 2010; Verrelle et al. 2017; Hanley et al. 2019). In the current implementation, the Leonard term calculation is embedded directly within the convection schemes rather than the Planetary Boundary Layer (PBL) scheme.


## Tests Conducted:
Regression test suite was run on Ursa. 

## Dependencies:


## Issue (optional):
Fixes issue: ufs-community/ufs-weather-model#3401
Fixes issue:  ufs-community/ccpp-physics#401


## Contributors (optional):
@JongilHan66 
