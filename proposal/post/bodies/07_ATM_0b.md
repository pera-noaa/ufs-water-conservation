## Description
- `ccpp/CMakeLists.txt`: `-DSAMFCNV_32BIT=ON` (#1133) compiled 2 of SAMF's 5 files single precision: the filter searched the scheme files only, and `mo_conv_kind.F90`, `progsigma_calc.f90`, `progomega_calc.f90` are capgen dependencies, so `conv_wp` stayed 8-byte. Now all 5; configure stops if only some are found. @rhaesung
- Updates `ccpp/physics` for the track-0b fixes: SAMF + PBL, Noah-MP, GFDL MP v3.

Answers change: the physics fixes in the suites that use them, and SAMF is now really single precision in the `_conv32` tests.

### Issue(s) addressed
- ufs-community/ufs-weather-model#3404

## Testing
Intel + GNU, Hercules: full `rt.sh` in ufs-community/ufs-weather-model#TBD. Baselines change.

## Dependencies
ufs-community/ccpp-physics#TBD (SAMF + PBL), #TBD (Noah-MP), #TBD (GFDL MP v3)
