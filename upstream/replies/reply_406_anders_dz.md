<!-- POSTED 12 Nov 2026: https://github.com/ufs-community/ccpp-physics/pull/406#discussion_r4559017207. Reply in the #406 L720 thread (root 4554926173) to AndersJensen-NOAA 4557327444
     ("I'd keep dz and pass in a calculated version of dz from dm if dm is present"), 22:47Z; he APPROVED abd89364 at 23:02Z.
     done = withdraw our "I'll make dz optional" promise; no code change (would reset three approvals and need RT).
     His sentence reads as the status quo (module L1401-1406: dz1d = dm/rho when present(dm), else dz). If he meant
     "compute dz once in the driver and drop dm", the cost is from 0e22f8c2's message: C96 control_p8_ugwpv1,
     dt_inner = 150 (five inner steps), fixed width lost 7.1e-4 kg/m2 in 24 h = 0.026 % of precipitation. -->

Thanks. Then I'll leave it as it is, which keeps `dz`: when `dm` is present the module computes the width from it at each inner step (L1401–1406), and otherwise uses `dz`. Computing `dz` once here instead loses water when there are inner steps: 7.1e-4 kg/m² in 24 h with `dt_inner = 150` in C96 `control_p8_ugwpv1`, 0.026 % of precipitation.
