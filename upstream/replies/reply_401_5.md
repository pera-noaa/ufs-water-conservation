Thanks @JongilHan66. Yes, it resolves the unrealistic heating. We ran your floor in the 12 RTs we surveyed before (develop vs develop + floor, one run each):

| RT | sub-cloud `eta` > 1.2, column-steps (max) | largest one-step heating (CFL) |
|---|---|---|
| `control_c384` (GFS v17) | 43,924 (9.2) → 0 | 26.4 K (9.1) → 8.3 K (3.5) |
| `control_c384gdas` (GFS v16) | 36,289 (8.5) → 0 | 19.8 K (8.5) → 5.6 K (3.5) |
| `control_c192` | 2,647 (2.1) → 0 | 9.3 K (4.8) → 7.5 K (3.7) |
| `hafs_regional_atm` | 36,819 (9.3) → 0 | 17.3 K (9.6) → 7.9 K (4.8) |
| `hafs_regional_1nest_atm` | 17,544 (34.1) → 0 | 48.3 K (15.3) → 4.6 K (2.5) |
| `hafs_global_1nest_atm` | 13,012 (100) → 0 | 24.5 K (24.0) → none above 4 K |

The other six (`control_c48`, `control_c48.v2.sfc`, `control_stochy`, `control_p8`, `hafs_regional_atm_thompson_gfdlsf`, `hafs_global_storm_following_1nest_atm`) also go to 0. Steps above CFL 5 drop from up to 464 per RT to one in all 12. Precipitation changes by −0.09 % to +0.19 % in the seven RTs where our script reads it. In `hafs_global_1nest_atm` over 48 h (10 members), develop crashed in 6 and the floor in none. With `progsigma` = .true., the floor removes the remaining `eta` > 1.2 (1,225 → 0 over 48 h) and changes precipitation by +0.1 %.

What we ran is `xlamue(i,k) = max(xlamue(i,k), crtlame, 0.001_conv_wp * clamt(i))`. Keeping `crtlame` in the `max` leaves develop's answers unchanged where `tkemean` < 0.35 (`clamt` < `clam`). Replacing it would lower the floor there, to 7e-5 at `clamt` = `clam` − `clamd`, which nothing here needs. With `hwrf_samfdeep`, `xlamud` is `xlamx`, so 0.001·`clamt` is not `xlamud` in that branch.

Two notes outside this fix:
- `samfshalcnv` has the same code, but with `clam_shal` = 0.3, `xlamud` = 3e-4 is above `crtlame` at any TKE, so `eta` can exceed 1 below shallow cloud bases between 1 and 3 km. Shallow heating above 4 K appeared only twice (5.1 K, `control_c48.v2.sfc`, the same with and without the floor), and we did not measure shallow `eta`.
- With the floor, steps of 4–9 K at CFL 1–3.7 remain in the GFS and HAFS regional RTs, with `eta` ≤ 1.2. Develop has them too, unchanged in `control_c48.v2.sfc`, where `eta` never exceeds 1.2. We have not looked into them yet.
