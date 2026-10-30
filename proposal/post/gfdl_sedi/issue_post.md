**Describe the bug**
`terminal_fall` passes `c_ice` to `sedi_heat` for every species ([gfdl_mp.F90 L2692](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/blob/8b94b9f3e54dbd04caff0ef28913d3c2ea5c1a70/model/gfdl_mp.F90#L2692)). In `sedi_heat` ([L5685–5720](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere/blob/8b94b9f3e54dbd04caff0ef28913d3c2ea5c1a70/model/gfdl_mp.F90#L5685-L5720)), `cw` is the heat capacity of the falling mass `m1`, which brings `cw·tz(k−1)` into the layer below. For rain and cloud water (`qflag` `"qr"`, `"ql"`) it should be `c_liq`. The 2019 version used `c_ice` only for falling ice, snow and graupel, and `c_liq` for rain (UFS copy, [L813](https://github.com/ufs-community/ccpp-physics/blob/9b65688ca82fad3f87801799f82d30ba7fe00007/physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90#L813) and [L1126](https://github.com/ufs-community/ccpp-physics/blob/9b65688ca82fad3f87801799f82d30ba7fe00007/physics/MP/GFDL/v1_2019/gfdl_cloud_microphys_mod.F90#L1126)).

**To Reproduce**
Any run with `do_sedi_heat = .true.` (the default) and rain. I measured it in UFS's copy of this code (ccpp-physics `gfdl_cloud_microphys_v3_mod.F90`, the same `terminal_fall` and `sedi_heat`) with an energy meter in GFDL MP's own constants, including the potential energy of the water: C96 `control_iovr4_gfdlmpv3`, 24 h, the microphysics energy residual is +0.20 W/m² before this change and −0.007 W/m² after it. In a standalone build of `gfdl_mp.F90` from `main`, one 300 s step of rain falling through a column creates energy equal to 6 × 10⁻⁵ of the column's, and with `c_liq` the energy is conserved to rounding (test in the PR). I have not run SHiELD.

**Expected behavior**
Rain and cloud water falling into a layer bring their heat at `c_liq`:
```fortran
        if (qflag .eq. "qr" .or. qflag .eq. "ql") then
            call sedi_heat (ks, ke, dp, m1, dz, tz, qv, ql, qr, qi, qs, qg, c_liq)
        else
            call sedi_heat (ks, ke, dp, m1, dz, tz, qv, ql, qr, qi, qs, qg, c_ice)
        endif
```
The same fix for UFS's copy is in ufs-community/ccpp-physics#413; the fix here is #431.

**System Environment**
- OS: Rocky Linux 9 (NOAA Hercules)
- Compiler: Intel Fortran Classic, oneAPI 2024.2.1 (spack-stack 1.9.2)
- MPI: Intel MPI 2021.13
- Configure options: UFS `compile.sh`, `-DAPP=ATM`, 64-bit dynamics
