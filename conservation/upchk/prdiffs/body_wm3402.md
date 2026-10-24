## Commit Queue Requirements:
- [X] This PR addresses a relevant WM issue (if not, create an issue). 
- [ ] All subcomponent pull requests (if any) have been reviewed by their code managers. (Developers should request reviews when they believe their development and testing are complete.)
- [X] Run the full Intel+GNU RT suite (compared to current baselines), preferably on Ursa (Hercules is also an acceptable alternative). **Exceptions:** documentation-only PRs, CI-only PRs, etc.
   - [X] Commit log file w/full results from RT suite run (if applicable).
   - [X] Verify that `test_changes.list` indicates which tests, if any, are changed by this PR. Commit `test_changes.list`, even if it is empty. Ensure that syncs w/develop do not overwrite this file. 
- [ ] All CI is passing. 
  - Note that any increase in compile warnings must be investigated and solved before a PR can be processed. 
- Transparency in the use of generative AI is required by NOAA policy. Was GenAI used in this work?
   - [X] No.
   - [ ] Yes. [Generative AI tool (insert name, if any)] was used to assist with developing this code. 
     - [ ] The code has been reviewed, edited, and validated by NWS staff. (Note: If the code has not yet been reviewed by NWS staff, leave unchecked, and OMD CMs will review as part of the PR review process.)
- [X] Fill out all sections of this template.

---

## Description:
PR submitted on behalf of @JongilHan66 

1. The current GFS 1D scale-aware (SA) TTE-EDMF scheme is extended to the 3D-SA TTE-EDMF scheme by replacing 3D TKE with 3D TTE. The horizontal turbulent diffusion is modified: the horizontal mixing length is now scaled directly to the vertical mixing length, replacing the previous formulation based on horizontal grid size. In addition, horizontal turbulent eddy diffusion—previously restricted to momentum and TKE—now applies across all scalar prognostic variables, including temperature, moisture, hydrometeors, passive tracers, momentum, and TTE.

2. Properly representing cold pools (CPs; dense, cold air masses formed by the downdrafts of precipitating cumulus clouds) within numerical weather prediction models has long been a challenge. By spreading horizontally, the cold pool's leading edge, known as the gust front, acts as a local lifting mechanism, forcing warm, moist air upward to generate secondary convective cells and organize larger systems. Neglecting the thermodynamic and momentum effects of these features, particularly their interaction with the boundary layer structure and the free atmosphere, can lead to significant systematic biases in the simulation of organized mesoscale convection and the diurnal cycle of precipitation. We integrate the CP parameterization developed by Freitas et al. (2024) into the NCEP Global Forecast System (GFS) with a modification. This implementation is coupled with the GFS deep convection and PBL schemes. The CP depth far behind the leading edge (D), used to compute gust front horizontal speed, was reduced from 2 km to 500 m. Concurrently, the density current head depth used for calculating vertical velocity at the CP leading edge was increased to approximately 2D. The modified scheme restricts the CP influence strictly to enhanced convection triggering. It removes convection intensity enhancement, eliminating additional source terms for buoyancy, moisture, and updraft velocity. To eliminate competition between the Cellular Automata (CA) scheme and the CP parameterization—which both attempt to promote secondary cell generation and larger system organization—CA is automatically disabled when the CP scheme is active. Simultaneous activation of both schemes was found to degrade overall forecast skill, particularly for MJO and hurricane predictions.

3. A mixed subgrid-scale turbulent flux scheme is introduced into the GFS based on Moeng et al. (2010), incorporating an auxiliary subgrid vertical flux known as the "Leonard term" (Leonard 1974; Moeng et al. 2010). The Leonard term accounts for subgrid-scale turbulent fluxes originating from near-grid-scale unresolved eddies—the largest subgrid eddies with scales comparable to the model's horizontal grid resolution. Applied primarily to mitigate subgrid flux underestimation, this formulation is most effective at kilometer-scale, convection-permitting, or cloud-resolving resolutions (Moeng et al. 2010; Verrelle et al. 2017; Hanley et al. 2019). In the current implementation, the Leonard term calculation is embedded directly within the convection schemes rather than the Planetary Boundary Layer (PBL) scheme.

### Commit Message:
<!--
Provide a concise commit message for the UFS WM and any subcomponents; delete unnecessary info.
-->
```
* UFSWM - Update submodule pointers and conducted regression tests on Ursa
  * UFSATM - Updated submodule pointers and added options and variables for 3D TTE-based EDMF Turbulent Mixing Scheme, Cold Pool Parameterization, and Leonard term
    * ccpp-physics - Introduced GFS PBL and Convection models with 3D TTE-based EDMF Turbulent Mixing Scheme, Cold Pool Parameterization, and Leonard term
    * atmos_cubed_sphere - Updated FV3 dycore for the 3D TTE-EDMF, Cold Pool Parameterization, and Leonard term
```

### Priority:
<!--
Indicate PR priority and include a justification for high/critical priority PRs; delete options that are not applicable. 
-->
- [ ] Critical Bugfix: Reason
- [ ] High: Reason
- [x] Normal

## Git Tracking
### UFSWM:
* Closes #3401

### Sub component Pull Requests:
* UFSATM - NOAA-EMC/UFSATM#1154
  * ccpp-physics - ufs-community/ccpp-physics#403
  * atmos_cubed_sphere - NOAA-GFDL/GFDL_atmos_cubed_sphere#429

### UFSWM Blocking Dependencies:
- [ ] Blocked by #
- [X] None

### Documentation:

- [ ] Documentation update required. 
   - [ ] Relevant updates are included with this PR. 
   - [ ] A WM issue has been opened to track the need for a documentation update; a person responsible for submitting the update has been assigned to the issue (link issue).
- [X] Documentation update NOT required. 

---
## Changes
### Regression Test Changes (Please commit test_changes.list):
- [ ] PR Adds New Tests/Baselines.
- [X] PR Updates/Changes Baselines.
- [ ] No Baseline Changes.

### Input data Changes:
- [X] None.
- [ ] PR adds input data.
- [ ] PR changes existing input data.

### Subcomponent Branch Changes
Does this PR change which subcomponent branch will be used in the UFS WM? 
- [ ] Yes --> Update `tests/ci/repo_check.sh` to point the CI to the new branch.
- [X] No

### Library Changes/Upgrades:
- [ ] Required
  * Library names w/versions:
  * Git Stack Issue (JCSDA/spack-stack#)
- [X] No Updates

---
<!-- STOP!!! THE FOLLOWING IS FOR CODE MANAGERS ONLY. PLEASE DO NOT FILL OUT -->
## What's Missing? 
CMs are waiting on the following items before this PR can be scheduled for the commit queue:
- [ ] Reviews for ALL subcomponent PRs (developer should request that subcomponent code managers review their subcomponent PRs)
- [ ] Updated Ursa logs (or Hercules)
- [ ] `test_changes.list` file reflecting changes in the developers PR (do not overwrite when sync'ing w/`develop`)
- [ ] Passing CI in WM and all subcomponent PRs (if CI is expected to fail, note the reason in the relevant (sub-)PR)
- [ ] Updated `.gitmodules` file points to developer's branch at every level
- [ ] Commit message (a short message for the WM and every affected subcomponent)
- [ ] Updated hashes? - It is the developer's responsibility to keep their PR up-to-date with WM `develop`.
- [ ] Other: 

If the developer is unable to complete any of these items, tag a WM CM (e.g., @gspetro-NOAA) for help. 

---
<!-- STOP!!! THE FOLLOWING IS FOR CODE MANAGERS ONLY. PLEASE DO NOT FILL OUT -->
## Testing Log:
- RDHPCS
  - [ ] Orion
  - [ ] Hercules
  - [ ] GaeaC6
  - [ ] Ursa
- WCOSS2
  - [ ] Dogwood/Cactus
- [ ] CI
- [ ] opnReqTest (complete task if unnecessary)

## Testing Remarks:
- 

