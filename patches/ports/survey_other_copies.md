# Other copies: SAMF (SA1), the prsl gas constant (FV1), Thompson (TH2–TH4, TH6, TH8, TH7)

Surveyed 14 October 2026 from source (read-only clones, nothing compiled, run or posted). Spot-checked by hand in this
session: the GEOS Thompson lines. The checker used for Thompson (`check_thompson.py`, in the survey scratch directory)
flags all six defects on ufs/dev c7dc705 and none after the ccpp-physics patches, so it can fail both ways.

## SA1: SAMF cloud-base double counting

The defect arrived with the TVD rewrite (ccpp-physics `ed3768b9`, 2021-10-05): every copy with `flxtvd` has it, older
copies do not.

| Copy | Commit | SA1 |
|---|---|---|
| ufs-community/ccpp-physics `production/GFS.v17`, `RRFS.v1`, `HAFS.v2.2`, `AQM.v7`, `release/srw-v3` | 8007f2c3, edd85a55, 14437d0e, 67d069ad, 2d8b1f20 | **present** (deep `samfdeepcnv.f` e.g. GFS.v17 L1534/2428/2433/2512/2517; shallow L1877/1933) |
| NCAR/ccpp-physics `main`, `scm/dev` | f601ce98, 72570a3f | present, double-precision form (the hand port in `git/ncar-main/` covers it) |
| NOAA-GSL/ccpp-physics `gsl/develop`, `RRFS_dev`, `rrfs_dev_merge` and HFIP branches (dormant since 2023-04) | 340b1777, 6b28c222, c29d9f54 | present |
| NOAA-GFDL/SHiELD_physics `main`, tag `FV3-202604-public`; pySHiELD | cb66dedd, d0ea7bdc; 7abb1b75 | absent (pre-TVD form) |
| older forks (GEPS, RAQMS, ai2cm/fv3gfs-fortran) | — | absent (pre-TVD) |

## FV1: prsl built with a single-precision gas constant

| Copy | Commit | FV1 |
|---|---|---|
| GFDL_atmos_cubed_sphere `production/GFS.v17`, `driver/UFS/atmosphere.F90` | af77d0f2 | **present**, as on `dev/emc` (L154, 348, 2288, 2296) |
| `main`, `driver/SHiELD/atmosphere.F90`; tag `FV3-202604-public` (pinned by SHiELD_build) | 8b94b9f3; 6f658bd0 | **present in SHiELD's default 32-bit build**: the dycore's `rdgas` is real(4) (287.04998779), the physics' `con_rd` 287.05 in double precision (relative 4.25e-8, as in UFS); a 64-bit build is unaffected |
| `dev/gfdl` SHiELD driver | 4bd9f120 | present in a 32-bit build (inferred from the build configuration) |
| `driver/GFDL`, NOAA-GFDL/atmos_drivers | — | n/a (do not build prsl) |

## Thompson

Y = present in the ufs/dev form (line numbers at the commit).

| Copy | Commit | TH2 | TH3 | TH4 | TH6 | TH8 | TH7 (entry / leftover rain / sedimentation floor) |
|---|---|---|---|---|---|---|---|
| ccpp-physics `production/RRFS.v1` | edd85a55 | Y 4074 | Y 3223 | Y | Y | Y (`R1*1000.`) | Y / Y / Y |
| ccpp-physics `production/GFS.v17` | 8007f2c3 | Y 4041 | Y 3190 | Y | Y | Y (`R1*rr_min`) | Y / Y / Y |
| ccpp-physics `production/HAFS.v2.2` | 14437d0e | Y | Y | Y | Y | Y (`R1*rr_min`) | Y / Y / Y |
| ccpp-physics `release/srw-v3`, `production/AQM.v7` | 2d8b1f20, 67d069ad | Y | Y | Y | Y | Y (`R1*1000.`) | Y / Y / Y |
| NOAA-GSL/ccpp-physics branches; NOAA-GSL/GSL_cloud_physics `main` | 340b1777 …; 046f4765 | Y | Y | Y | Y | Y | Y / Y / Y |
| **GEOS-ESM/GEOSgcm_GridComp `develop`**, `GEOSmoist_GridComp/module_mp_thompson.F90` (verified) | 23e58ba4 | Y 4017 | Y 3156 | Y 3348 | Y | Y 3961 | Y / Y / Y 6431 |
| NOAA-EMC/HRRR `develop` (WRF 3.9 HRRRv4) | 40ee6058 | Y | Y | Y | Y | Y (`R1*10.`) | Y / Y / n/a |
| Bramsmodel/brams `master` | e491dc63 | Y | Y | Y | Y | Y | Y / Y / n/a |
| DOI-USGS/COAWST, USEPA/UACM | 26e6fb73, e4ba1ee7 | byte-identical to WRF `develop`: the WRF port applies | | | | | |
| monanadmin/MONAN-Model `main` | cf4ac916 | byte-identical to MPAS-Dev `develop`: the MPAS port applies | | | | | |
| KuangLab SAM 6.11, gSAM | 0850e3ce, a0e1a023 | n/a | different form | absent | Y | Y | Y / Y / n/a |
| NCAR/MMM-physics, SHiELD_physics | — | no Thompson | | | | | |

## Gaps

- NOAA-GFDL/atmos_phys (AM4/AM5) was not checked (code-search rate limit); CM1 is not on GitHub; personal WRF forks
  were not examined.
- GitHub code search covers default branches only.
- FV1 on `dev/gfdl` is inferred from the build configuration; nothing here was compiled.
