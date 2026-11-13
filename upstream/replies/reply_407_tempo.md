<!-- DRAFT 13 Nov 2026, not posted. Reply on ufs-community/ccpp-physics#407 to AndersJensen-NOAA 01:38Z ("are you
     willing to make a PR to NCAR/TEMPO with the same changes that are in Thompson?").
     done = he knows what goes where and in what order; plan in tempo_attr/PLAN_tempo_upstream.md.
     Numbers are from our UFS runs at the previous tempo_v3 pin 2856696 (../tempo/results.md), hence "previous pin". -->

@AndersJensen-NOAA Yes. They split by where the code lives:

- **Here, in `mp_tempo.F90`:** the mass basis, which this PR already fixes, and the layer depth from `prsi`. I'll add the layer depth to this PR in the form you suggested on #406: `mp_tempo` computes `dz` from the host's mass at each inner step, since TEMPO's inner loop is here. I'll also merge `ufs/dev` in, since this branch now conflicts with it.
- **NCAR/TEMPO, in `tempo_main`:** the graupel and density fixes, in one PR, retested on the current `main`.

TEMPO also has a larger leak that Thompson doesn't: v3.0.0 inverted the semi-Lagrangian fallback test ([L1911](https://github.com/NCAR/TEMPO/blob/c62699fb660ebbb14e4388f7b59a8b38decac1ab/src/module_mp_tempo_main.F90#L1911), `qpi(k) > 0` where v2 and Thompson test `< 0`), so negative edge values are raised to the floor. In our UFS runs with the previous TEMPO pin it created about 0.6 % of precipitation, and fixing it lowered precipitation about 5 %. Since it changes forecasts, and the v3 hail tuning was done with it, I'll open it as its own issue for you to decide.
