<!-- POSTED 13 Nov 2026 as NCAR/TEMPO#63 (body = this file without this comment). NCAR/TEMPO PR, base tempo_v3.3.0 71588d1, head pera-noaa:entry-density-v330
     79fa6c6 (0182132 = db01901d cherry-picked, then a comments-only commit; runs measured 0182132). CI: 0182132 run
     43514870813 pass; 79fa6c6 run 43515547695 pass. Forecast impact: tp_port/fi_v330.py (md5 9a60d533). Strip this comment before posting.
     Numbers: PREREG_tempo_v330.md (Hercules build 10468464, runs 10468465). Replaces pr_tempo_c2c3.md.
     Title: "Sedimentation with the entry density" -->

@AndersJensen-NOAA Thanks for #61 and #62: they cover the fallback sign and the graupel re-close we had found. This
is the one water fix from ufs-community/ccpp-physics#406 that `tempo_v3.3.0` doesn't have yet.

After the tendencies, `rho` is recomputed from the heated temperature
([L518](https://github.com/NCAR/TEMPO/blob/71588d12d12270446af682c7618e082f27095032/src/module_mp_tempo_main.F90#L518),
[L611](https://github.com/NCAR/TEMPO/blob/71588d12d12270446af682c7618e082f27095032/src/module_mp_tempo_main.F90#L611),
[L639](https://github.com/NCAR/TEMPO/blob/71588d12d12270446af682c7618e082f27095032/src/module_mp_tempo_main.F90#L639)),
and sedimentation converts between mixing ratio and mass with it. `dz1d` doesn't change, so the new `rho` implies a
different layer mass, and water that falls is not the water that arrives. The fix keeps `rho` at the entry density
through sedimentation and gives the updated one (`rhon`) to `thermo_vars`, so fall speeds and ventilation still see
the heated column. Between the update and the recompute after sedimentation
([L834](https://github.com/NCAR/TEMPO/blob/71588d12d12270446af682c7618e082f27095032/src/module_mp_tempo_main.F90#L834),
unchanged), the other users of `rho` now take the entry density: the aerosol tendencies, the `*_check_and_update`
calls, `cloud_condensation`, `rain_evaporation` and `freeze_cloud_melt_ice`, a change of order ΔT/T in those terms.
This is what ufs-community/ccpp-physics#406 does in Thompson. Setting `dz1d` from the new `rho` instead would also
close.

The closure is exact where the entry `rho·dz1d` is the host's layer mass, as in UFS once #407 takes the layer depth
from the host's pressure. Where `dz1d` is geometric (WRF, MPAS), the fix removes the change within the step, not any
mismatch the host passes in.

Measured in UFS (C96 `control_p8_ugwpv1_tempo`, 24 h, with ufs-community/ccpp-physics#407) by an in-model water
meter. R is the water the scheme creates (+) or destroys (−), as a percentage of its grid-scale precipitation P:

| `tempo_v3.3.0` | R/P 0–6 h | R/P 6–24 h | P 6–24 h |
|---|---|---|---|
| as merged | −0.47 % | −0.34 % | 0.7684 kg/m² |
| with this PR | −0.31 % | −0.19 % | 0.7677 kg/m² |
| noise run | −0.47 % | −0.34 % | 0.7692 kg/m² |

The noise run is the first row's binary with `consv_te = 0.999`. The fix removes 0.15 % of P from the water the scheme
destroys; its precipitation change is smaller than the noise run's. Most of what remains was, on the older pin, cloud
water settling out of the lowest layer; how to count it is still open for Thompson too. At 24 h the rms
difference from `tempo_v3.3.0` is 0.95–1.04× the noise run's for temperature, humidity, winds, surface pressure, 2-m
temperature, precipitation, and cloud, rain, ice, snow and graupel mixing ratios. One case, one noise run; happy to
add a column water-conservation check to `test/tests.F90` if that's useful.

One more, not in this PR: below freezing the graupel check still sums the unscaled `prg_rcg`
([L1648](https://github.com/NCAR/TEMPO/blob/71588d12d12270446af682c7618e082f27095032/src/module_mp_tempo_main.F90#L1648))
after the rain check scaled `prr_rcg`
([L1621](https://github.com/NCAR/TEMPO/blob/71588d12d12270446af682c7618e082f27095032/src/module_mp_tempo_main.F90#L1621));
the reset comes later
([L1677–1680](https://github.com/NCAR/TEMPO/blob/71588d12d12270446af682c7618e082f27095032/src/module_mp_tempo_main.F90#L1677-L1680)).
Setting `prg_rcg = −prr_rcg` right after the rain check, the graupel counterpart of #62's `prs_rcs` cap, would
close it. Found by reading the code, not measured; happy to add it here or open it separately.

Environment: ufs-weather-model 517e02c9, IntelLLVM ifx 2025.3.0, spack-stack 2.1.1, Hercules.
TEMPO CI passes on the branch ([run](https://github.com/pera-noaa/TEMPO/actions/runs/43515547695)); `test/tests.F90`
runs the unit tests and the column test; it has no stored answers.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
