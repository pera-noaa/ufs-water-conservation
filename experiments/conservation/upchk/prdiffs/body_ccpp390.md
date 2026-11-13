## Description of Changes:
This PR introduces a Mixed-Layer Model (MLM) formulation for cloud-driven, top-down turbulent mixing in the TKE-EDMF PBL scheme. The MLM provides an alternative to the existing mass-flux treatment of stratocumulus-top-driven turbulence, which is based on a parameterization of surface-forced thermal plumes.

The formulation is based on Solomon et al. (2026), where it was evaluated against turbulence-resolving simulations of Arctic stratocumulus and shown to improve the representation of cloud-driven turbulent energy and water fluxes.

The MLM is implemented as an optional (mlm = .true.) component of TKE-EDMF and uses cloud-top radiative cooling and large-scale precipitation information from the physics suite to represent turbulent mixing driven from cloud top.

----------
In addition to the introduction of the MLM scheme, this PR also contains a bug-fix in shallow convection which initializes input fields from deep convection to 0. It also includes further refinements to the prognostic updraft velocity scheme.
----------


## Tests Conducted:
The full UFS regression test suite was run. With mlm = .false. no baselines are changed (default). Additional tests with mlm = .true. were conducted to test impact on Arctic mixed phase stratocumulus. 

## Issue (optional):
Fixes issue: https://github.com/ufs-community/ufs-weather-model/issues/3354 in ufs-weather-model

## Contributors:
@egrell
@AmySolomon

