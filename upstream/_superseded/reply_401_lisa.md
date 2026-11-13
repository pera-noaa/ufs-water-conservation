@lisa-bengtsson Here it is, for both the floor alone (`xlamue` ≥ 0.001·`clamt`) and Christian's 2a95266 as is, against develop f1d68949. The runs are `hafs_global_1nest_atm` with members `consv_te` = 1, 0.999, …, and the fields are the run mean of `cprat_ave`. Every panel is 0–18 h with 10 members, for `progsigma` = .true. and .false. (the RT setting) alike. I stopped at 18 h because develop with `progsigma` = .false. crashes after 19 h in three of the ten.

[maps: develop; floor − develop; 2a95266 − develop. Global 1° and the 0.25° nest. Faded where |t| < 2.1 against the member spread.]

[zonal means with ±2 SE bands, and the global mean of each member]

Change in mean precipitation, as a % of develop:

| | convective, global | convective, nest | total, global | total, nest |
|---|---|---|---|---|
| `progsigma` = .true., floor | +0.41 | +0.76 | +0.16 | +0.24 |
| `progsigma` = .true., 2a95266 | +0.60 | +0.85 | +0.27 | +0.28 |
| `progsigma` = .false., floor | +0.70 | +3.2 | −0.22 | −0.19 |
| `progsigma` = .false., 2a95266 | +0.92 | +3.4 | −0.08 | −0.14 |

Each member's convective rain is within ±0.3 % of its set's mean (±0.06 % globally), so the convective changes are well outside that spread. With `progsigma` = .true., both versions add a little convective rain, mostly between 10°S and 40°N. The largest local changes are a north–south shift along the 35–40°N Atlantic band, plus changes in the east Pacific ITCZ and the western Pacific. The rms difference of the mean field is 0.14 mm/day for the floor and 0.19 for 2a95266. Splitting develop's members in half gives 0.05 mm/day for comparison.

With `progsigma` = .false., the change is larger and concentrated in the nest. Convective rain there rises 3 % and grid-scale rain falls by about as much, so total precipitation changes by −0.2 %.

The members only perturb `consv_te`, so this is a small ensemble from a single case and says nothing about forecast skill. In our runs, splitting develop's members in half gives |t| > 2.1 over 6–7 % of the area, which suggests the significance test is about right.
