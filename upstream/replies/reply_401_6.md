Thanks @JongilHan66. Yes, it resolves the unrealistic heating. We applied Christian's 2a95266 as is to develop and ran the 12 RTs we surveyed before (one run each):

| RT | sub-cloud `eta` > 1.2, column-steps (max) | largest one-step heating (CFL) |
|---|---|---|
| `control_c384` (GFS v17) | 43,924 (9.2) → 0 | 26.4 K (9.1) → 8.8 K (3.5) |
| `control_c384gdas` (GFS v16) | 36,289 (8.5) → 0 | 19.8 K (8.5) → 6.2 K (3.4) |
| `control_c192` | 2,647 (2.1) → 0 | 9.3 K (4.8) → 7.8 K (3.8) |
| `hafs_regional_atm` | 36,819 (9.3) → 0 | 17.3 K (9.6) → 8.3 K (5.0) |
| `hafs_regional_1nest_atm` | 17,544 (34.1) → 0 | 48.3 K (15.3) → 4.5 K (2.4) |
| `hafs_global_1nest_atm` | 13,012 (100) → 0 | 24.5 K (24.0) → none above 4 K |

The other six RTs also go to 0. Steps above CFL 5 drop from up to 464 per RT to at most 2. In `hafs_global_1nest_atm` over 48 h (10 members), develop crashed in 6 and 2a95266 in none. With `progsigma` = .true. there is no step above 4 K and no `eta` > 1.2.

Precipitation changes more than with the floor alone. We also ran `max(xlamue, crtlame, 0.001·clamt)` in deep convection only (global means at each RT's last output, 6–24 h):

| RT | floor alone | 2a95266 |
|---|---|---|
| GFS (7 RTs) | +0.03 to +0.25 % | +0.15 to +0.46 % |
| `hafs_global_1nest_atm`, `..._storm_following_...` | +0.04, +0.01 % | +0.34, +0.66 % |
| `hafs_regional_atm`, `..._thompson_gfdlsf` | +0.04, +0.10 % | +1.84, +1.71 % |
| `hafs_regional_1nest_atm` | +0.40 % | +0.51 % |

Both remove the instability equally. 2a95266 also (1) drops `crtlame`, which lowers the floor where `clamt` < `clam`; (2) applies the floor in `samfshalcnv`, where with `clam_shal` = 0.3 the floor (about 3e-4) exceeds `crtlame` in every column; and (3) caps `fent1` and `fent2` at 1 (previously 3 and 5.2). We have not separated which of these moves precipitation. Is (3) meant as part of this fix? If it helps, we can run each part alone.

With either version, steps of 4–11 K at CFL up to 5.4 remain in the GFS and HAFS regional RTs, with `eta` ≤ 1.2 (largest: 11.2 K with 2a95266, 8.8 K with the floor alone, both in `hafs_regional_atm_thompson_gfdlsf`). Develop has them too, unchanged in `control_c48.v2.sfc`, where `eta` never exceeds 1.2. We have not looked into them yet.
