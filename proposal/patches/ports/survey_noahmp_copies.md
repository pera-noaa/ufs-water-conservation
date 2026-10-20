# Noah-MP copies: defects NM5, NM6, NM8, NM7 (and NM1, NM2)

Surveyed 14 October 2026 (read-only clones; nothing posted; a dated record: later fixes NM9 and NM10 were not surveyed). Line numbers at the commits listed. Verified by hand in
this session: the glacier gap in fix NM5 (below). The rest is the survey's record, each verdict from quoted lines.

## Commits examined

- **WRF** `release-v4.8.1` 315a8319 pins NCAR/noahmp **f301c728** (v5.2.2 line); `develop` 1086c862 and `master` (tag
  v4.8.0, 06d4240a) pin **5da0b241** (v5.2.0).
- **MPAS-Dev** `develop` aa6d8cd6 (`master` f34984b2 identical): in-tree Noah-MP v5.0, `src/core_atmosphere/physics/physics_noahmp`.
- **HRLDAS** `master` cd96df47, `develop`, `release-v5.2.1`: pin NCAR/noahmp **17751dcd** (v5.2.1).
- **NASA LISF** `master` 2f2c1cba: in-tree `noahmp.3.6`, `noahmp.4.0.1` (soil + glacier), `glacier/noahmp.3.9.1.1`;
  `noahmp.5.0/phys/noahmp` submodule at NCAR/noahmp **0cd33858** (`release-v5.0-LIS`).
- **NOAA-EMC/noahmp**: `develop` 2c7b3bc (ported, `noahmp-emc_develop_D_H_I_K_L/`), `master` f80b216 (2022, v4-era, not
  pinned by any UFS ref found).
- **ufs-weather-model `NOAHMP-interface` pins**: `develop`, GFS.v17, HAFS.v2.2 → 2c7b3bc; RRFS.v1 → **0cd3e23**;
  public-v3.0.0 → **1a2d2fc**. **land-DA_workflow** (ufs-community): `develop`, public-v3.0.0 → ufs-wm a758c88 → **8fe108a**;
  public-v2.0.0 → ufs-wm 2ccc549 → **3ac32f0**.
- **ccpp-physics production branches**: GFS.v17 8007f2c, RRFS.v1 edd85a5, HAFS.v2.2 14437d0.
- **Others**: WRF-Hydro/NWM (`NCAR/wrf_hydro_nwm_public` main 55ed71c8, in-tree v4-era); ERF (`erf-model/ERF`
  development e12a05d2, pins the erf-model/noahmp fork fbaa38f); CTSM (no Noah-MP).

## Results

**v5 copies.** WRF pins, HRLDAS and ERF are identical to NCAR/noahmp master 1a6225b in every NM5/NM6/NM8/NM7 file.

| Copy | NM5 | NM6 | NM8 | NM7 | NM1 analogue | NM2 |
|---|---|---|---|---|---|---|
| WRF 4.8.1 / develop, HRLDAS, ERF | `SnowWaterMainMod.F90:176`, `SnowpackHydrologyMod.F90:96`, glacier `:176`/`:106` | `CanopyHydrologyMod.F90:92`, `:101` | present | `:75`, `:81` | WRF/HRLDAS absent (QFX is the water flux); **ERF present** | n/a |
| MPAS-Dev develop (v5.0 in-tree) | `src/SnowWaterMainMod.F90:132`, `SnowpackHydrologyMod.F90:100`, glacier `:132`/`:110` | `:92`, `:101` | present | `:75`, `:81` | absent | n/a |
| LIS noahmp.5.0 (0cd33858) | 132/100/132/110 | 92/101 | present (offline) | 75/81 | — | n/a |

`HeatLatentCanTransp` is not clamped, so it can be negative (NM7).

**v4-era monolithic copies.** NM5 at two sites (end of sflx, snowh2o; the CCPP `energy` site is absent); glacier modules
have no canopy, so NM6 and NM7 do not apply there. `FCTR = TR` is unclamped (NM7).

| Copy | NM5 | NM6 | NM7 | NM8 (parameters) |
|---|---|---|---|---|
| LIS 4.0.1 `module_sf_noahmplsm_401.F90` | 861, 7516 | 6705, 6714 | 6687, 6693 | 165–167 |
| LIS 4.0.1 glacier | 294, 2913 | n/a | n/a | 14–16 |
| LIS 3.6 `module_sf_noahmplsm_36.F90` | 1066, 7967 | 7128, 7151 | 7110, 7116 | 53–55 |
| LIS glacier 3.9.1.1 | 290, 2912 | n/a | n/a | 14–16 |
| WRF-Hydro `module_sf_noahmplsm.F` | 849, 6768 | 5952, 5961 | 5934, 5940 | 167–169 |
| WRF-Hydro glacier | 288, 2910 | n/a | n/a | 14–16 |
| NOAA-EMC `master` `.F` | 1066, 7170 | 6345, 6354 | 6327, 6333 | 208–210 |
| NOAA-EMC `master` glacier | 285, 2901 | n/a | n/a | 14–16 |

**NOAA-EMC/noahmp pins used by UFS and land-DA (CCPP lineage).** NM5 at three sites (sflx, energy, snowh2o, 1e-6/1e-3);
glacier NM5 at 351 and 3307; NM8 at 186–188; NM1 is `evap = evap/density/con_hvap` in `drivers/ccpp/noahmpdrv.F90`; NM2 absent.

| Pin | NM5 | NM6 | NM7 | NM1 |
|---|---|---|---|---|
| 8fe108a (land-DA develop) | 945 / 2047 / 8164 | 7330 / 7339 | 7312 / 7318 | 1566 |
| 3ac32f0 (land-DA v2) | 945 / 2047 / 8164 | 7330 / 7339 | 7312 / 7318 | 1273 |
| 0cd3e23 (RRFS.v1) | 945 / 2045 / 8162 | 7328 / 7337 | 7310 / 7316 | 1254 |
| 1a2d2fc (public-v3.0.0) | 945 / 2047 / 8164 | 7330 / 7339 | 7312 / 7318 | 1566 |

The ccpp-physics production branches carry all of them as well (GFS.v17, HAFS.v2.2: lsm 947/2049/8182, canopy
7348/7357, etran 7330, NM2 at drv 1000, NM1 at drv 1573; RRFS.v1: 945/2045/8162, 7328/7337, 7310, drv 697/1254).

## Findings beyond the ports

- **Fix NM5 misses the glacier module (verified).** ccpp-physics `ufs/dev` c7dc705 `module_sf_noahmp_glacier.F90` zeroes
  thin snow at `noahmp_glacier` L357 (`snowh <= 1.e-6 .or. sneqv <= 1.e-3`, after the water-balance check, so `errwat`
  cannot see it) and `snowh2o_glacier` L3347 (`1.e-8` / `1.e-6`); diff 12 touches only `module_sf_noahmplsm.F90`.
  Every CCPP-lineage copy has the same two glacier sites. Metered in the parent session (C96, 24 h, all 144 ranks with
  glacier points; output byte-identical to the unmetered run): no deletions. **Since fixed by NM9** (UFS diff 16) in
  ufs/dev and every ported copy (production branches, NOAA-EMC `develop`), which books the truncated snow as runoff;
  the other copies above still carry it.
- **NM8 in every copy.** All use hvap 2.5104e6, hsub 2.844e6, hfus 0.3336e6; no host passes its own. WRF (XLV 2.5e6,
  XLS 2.85e6) and MPAS (xlv 2.5e6, xls 2.85e6) receive the vapour as QFX, so the land pays 0.4 % more latent energy
  than the vapour carries, and over ice 0.2 % less. HRLDAS, LIS and WRF-Hydro are offline: a constant difference only.
- **ERF has an NM1 analogue.** `Source/LandSurfaceModel/Noah-MP/ERF_NOAHMP_ResultPolicy.H:89` sets the moisture flux to
  `latent_heat_flux/(density*latent_heat)` with L_v = 2.5e6 (`ERF_NOAHMP_Advance.cpp:314–335`): about 0.4 % too much
  water over unfrozen land and about 14 % over frozen surfaces.
- **NUOPC land cap.** NM2 does not occur (one `noahmpdrv_run` per step, `flag_iter = .true.`). NM1 reaches the atmosphere in
  ATM–LND runs (`evap` exported as `Fall_lat`); the NM1 fix in `drivers/ccpp/noahmpdrv.F90` corrects it at the source.

## NM11: ground latent heat keyed on ground temperature only

Read-only, 15 October 2026. The ground's latent heat is hvap when the ground is above freezing (`latheag`; v5
`LatHeatVapGrd`), but the water step takes the ground vapour from the snow ice whenever there is snow (`qsnsub`/`qsnfro`;
v5 `SublimSnowSfcIce`/`FrostSnowSfcIce`) and, on frozen ground, from the soil ice, with any shortfall taken from the
liquid. UFS diff 18 adds the anchors below. Line numbers: the `latheag = hsub` line (v5: the ground-temperature test) and
the frozen-ground `sice(1)` update.

| Copy | Commit | energy | water | Form |
|---|---|---|---|---|
| ccpp-physics `ufs/dev` | c7dc705 | 2227 | 7190 | the reference (diff 18) |
| `production/GFS.v17`, `production/HAFS.v2.2` | 8007f2c3, 525174d8 | 2227 | 7190 | blocks identical to `ufs/dev` |
| `production/RRFS.v1` | edd85a55 | 2223 | 7170 | identical |
| `release/srw-v3` | 2d8b1f20 | 2225 | 7188 | identical |
| `production/AQM.v7` (`module_sf_noahmplsm.f90`) | 67d069ad | 2176 | 6771 | same logic; `0.622` for `ep_2` |
| NOAA-EMC/noahmp `develop` (GFS.v17, HAFS.v2.2) / 0cd3e23 (RRFS.v1) | 2c7b3bc / 0cd3e23 | 2225 / 2223 | 7170 / 7170 | identical |
| NOAA-EMC/noahmp 8fe108a, 3ac32f0 (land-DA), 1a2d2fc (public-v3.0.0) | | 2225 | 7172 | identical |
| NCAR/noahmp `master` (v5; also the WRF and HRLDAS pins f301c728, 5da0b241, 17751dcd; ERF's fork byte-identical) | 1a6225b | `PsychrometricVariableMod.F90:50` | `WaterMainMod.F90:139` | v5 names, same logic |
| NCAR/noahmp `release-v5.0-LIS` (LIS 5.0) | 0cd33858 | :50 | present (file differs only by the wetland option) | v5 |
| MPAS-Dev `develop` (in-tree v5.0) | f34984b2 | :50 | :133 | v5 |
| LIS `noahmp.3.6`, `noahmp.4.0.1`; WRF-Hydro | 2f2c1cba; 55ed71c8 | 1819, 1995; 1969 | 6856, 6532; 5793 | v4 anchors matched, logic not re-read |

Glacier modules always use hsub (no NM11). NOAA-EMC `master` f80b216 (`.F`, not pinned) was not checked. Nothing ported:
held until the UFS series' reproducibility run is back.
